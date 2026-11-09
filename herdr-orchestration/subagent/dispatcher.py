"""Subagent lifecycle dispatcher and receipt protocol manager."""

import json
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

from .builder import CommandBuilder
from .guard import EscalationGuard
from .resolver import RoleConfig, RoleResolver


@dataclass
class DispatchResult:
    """Outcome of a subagent dispatch execution."""

    role: RoleConfig
    pane_id: str | None
    session_id: str
    receipt_path: Path | None
    receipt_content: str
    source: Literal["receipt_file", "fallback_buffer", "dry_run"]
    exit_code: int
    planned_commands: list[list[str]] = field(default_factory=list)


@runtime_checkable
class CommandExecutor(Protocol):
    """Interface for command execution backends."""

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        """Execute command and return (returncode, stdout, stderr)."""
        ...


class SubprocessExecutor:
    """Default command executor using subprocess.run."""

    def run(self, cmd: list[str]) -> tuple[int, str, str]:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr


class SubagentDispatcher:
    """Manages the full lifecycle of out-of-process subagents in Herdr panes."""

    def __init__(
        self,
        executor: CommandExecutor | None = None,
        receipt_dir: str | Path | None = None,
    ) -> None:
        self.executor = executor or SubprocessExecutor()
        self.receipt_dir = Path(receipt_dir) if receipt_dir else Path("/tmp")

    def _run_command(self, cmd: list[str]) -> tuple[int, str, str]:
        return self.executor.run(cmd)

    def _extract_pane_id(self, stdout: str) -> str:
        stripped = stdout.strip()
        if "{" in stripped:
            try:
                # Find outermost JSON object
                start = stripped.find("{")
                end = stripped.rfind("}") + 1
                data = json.loads(stripped[start:end])
                if isinstance(data, dict):
                    result_obj = data.get("result", {})
                    if isinstance(result_obj, dict) and "pane_id" in result_obj:
                        return str(result_obj["pane_id"])
                    if "pane_id" in data:
                        return str(data["pane_id"])
            except Exception:
                pass
        # Fallback: extract first line or token
        lines = stripped.splitlines()
        first_line = lines[0].strip() if lines else "pane-unknown"
        if first_line.lower().startswith("pane"):
            return first_line.split()[-1] if " " in first_line else first_line
        return first_line

    def dispatch(
        self,
        role: str,
        prompt: str,
        *,
        session_id: str | None = None,
        escalation_receipt: str | Path | None = None,
        timeout_seconds: int = 300,
        cleanup: bool = True,
        cwd: str | None = None,
        dry_run: bool = False,
        extra_args: list[str] | None = None,
        receipt_path: str | Path | None = None,
    ) -> DispatchResult:
        """Dispatch a task to a specialized subagent.

        Args:
            role: Functional role name (e.g., 'runner', 'fixer', 'craftsman', 'oracle').
            prompt: Task instructions for the agent.
            session_id: Optional unique identifier for this dispatch session.
            escalation_receipt: Path to evaluator receipt approving frontier escalation.
            timeout_seconds: Prompt timeout in seconds (default: 300).
            cleanup: Whether to close the worker pane on completion (default: True).
            cwd: Working directory for the worker pane.
            dry_run: If True, plans commands without executing them.
            extra_args: Extra arguments to pass to the agent process after '--'.
            receipt_path: Explicit override path for the output receipt file.

        Returns:
            DispatchResult containing execution outcome and output.
        """
        role_config = RoleResolver.resolve(role)
        EscalationGuard.check(role_config, escalation_receipt)

        resolved_session_id = session_id or f"{int(time.time())}-{uuid.uuid4().hex[:8]}"

        if receipt_path is not None:
            resolved_receipt_path = Path(receipt_path)
        else:
            resolved_receipt_path = (
                self.receipt_dir / f"herdr-subagent-{role_config.name}-{resolved_session_id}.md"
            )

        split_cmd = CommandBuilder.build_pane_split_command(cwd=cwd)

        if dry_run:
            dry_pane_id = "pane-dry-run"
            start_cmd = CommandBuilder.build_agent_start_command(
                role_config=role_config,
                pane_id=dry_pane_id,
                extra_args=extra_args,
            )
            prompt_cmd = CommandBuilder.build_prompt_command(
                role_name=role_config.name,
                prompt=prompt,
                wait=True,
                timeout_ms=timeout_seconds * 1000,
            )
            planned = [split_cmd, start_cmd, prompt_cmd]
            if cleanup:
                close_cmd = CommandBuilder.build_pane_close_command(dry_pane_id)
                planned.append(close_cmd)

            return DispatchResult(
                role=role_config,
                pane_id=dry_pane_id,
                session_id=resolved_session_id,
                receipt_path=resolved_receipt_path,
                receipt_content="",
                source="dry_run",
                exit_code=0,
                planned_commands=planned,
            )

        # 1. Split terminal pane
        _, split_stdout, _ = self._run_command(split_cmd)
        pane_id = self._extract_pane_id(split_stdout)

        executed_commands: list[list[str]] = [split_cmd]

        # 2. Launch agent process in pane
        start_cmd = CommandBuilder.build_agent_start_command(
            role_config=role_config,
            pane_id=pane_id,
            extra_args=extra_args,
        )
        self._run_command(start_cmd)
        executed_commands.append(start_cmd)

        # 3. Dispatch prompt
        prompt_cmd = CommandBuilder.build_prompt_command(
            role_name=role_config.name,
            prompt=prompt,
            wait=True,
            timeout_ms=timeout_seconds * 1000,
        )
        prompt_code, _, _ = self._run_command(prompt_cmd)
        executed_commands.append(prompt_cmd)

        # 4. Ingest output receipt or fall back to terminal buffer
        source: Literal["receipt_file", "fallback_buffer"]
        if resolved_receipt_path.is_file():
            content = resolved_receipt_path.read_text(encoding="utf-8")
            source = "receipt_file"
            if cleanup:
                try:
                    resolved_receipt_path.unlink()
                except OSError:
                    pass
        else:
            read_cmd = ["herdr", "agent", "read", role_config.name, "--source", "recent-unwrapped"]
            _, read_stdout, _ = self._run_command(read_cmd)
            executed_commands.append(read_cmd)
            content = read_stdout
            source = "fallback_buffer"

        # 5. Clean up pane if requested
        if cleanup and pane_id:
            close_cmd = CommandBuilder.build_pane_close_command(pane_id)
            self._run_command(close_cmd)
            executed_commands.append(close_cmd)

        return DispatchResult(
            role=role_config,
            pane_id=pane_id,
            session_id=resolved_session_id,
            receipt_path=resolved_receipt_path,
            receipt_content=content,
            source=source,
            exit_code=prompt_code,
            planned_commands=executed_commands,
        )
