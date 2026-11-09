"""Command builder for Herdr terminal multiplexing and Antigravity agent CLI operations."""

import os

from .resolver import RoleConfig


class CommandBuilder:
    """Builds CLI command arrays for Herdr pane and agent operations."""

    @classmethod
    def build_agent_start_command(
        cls,
        role_config: RoleConfig,
        pane_id: str,
        extra_args: list[str] | None = None,
        skip_permissions: bool = True,
    ) -> list[str]:
        """Build the command to launch an isolated Antigravity CLI subagent process in a Herdr pane.

        Args:
            role_config: Subagent role configuration with model and effort settings.
            pane_id: Herdr pane ID where the agent process will run.
            extra_args: Optional extra arguments to pass to the agy process after '--'.
            skip_permissions: Whether to append '--dangerously-skip-permissions'.

        Returns:
            Command argument list suitable for subprocess execution.
        """
        cmd = [
            "herdr",
            "agent",
            "start",
            role_config.name,
            "--kind",
            "agy",
            "--pane",
            pane_id,
            "--",
            "--model",
            role_config.model,
            "--effort",
            role_config.effort,
        ]
        if skip_permissions:
            cmd.append("--dangerously-skip-permissions")
        if extra_args:
            cmd.extend(extra_args)
        return cmd

    @classmethod
    def build_pane_split_command(
        cls,
        cwd: str | None = None,
        direction: str = "right",
    ) -> list[str]:
        """Build the command to split and allocate a new terminal pane.

        Args:
            cwd: Optional working directory for the new pane. Defaults to os.getcwd().
            direction: Split direction (default: 'right').

        Returns:
            Command argument list.
        """
        resolved_cwd = cwd if cwd is not None else os.getcwd()
        return [
            "herdr",
            "pane",
            "split",
            "--current",
            "--direction",
            direction,
            "--cwd",
            resolved_cwd,
            "--no-focus",
        ]

    @classmethod
    def build_prompt_command(
        cls,
        role_name: str,
        prompt: str,
        wait: bool = True,
        timeout_ms: int | None = None,
    ) -> list[str]:
        """Build the command to dispatch a prompt to a running Herdr agent.

        Args:
            role_name: Target agent identifier.
            prompt: Text prompt to dispatch.
            wait: Whether to block waiting for completion.
            timeout_ms: Optional timeout in milliseconds.

        Returns:
            Command argument list.
        """
        cmd = ["herdr", "agent", "prompt", role_name, prompt]
        if wait:
            cmd.append("--wait")
        if timeout_ms is not None:
            cmd.extend(["--timeout", str(timeout_ms)])
        return cmd

    @classmethod
    def build_pane_close_command(cls, pane_id: str) -> list[str]:
        """Build the command to cleanly close a Herdr terminal pane.

        Args:
            pane_id: Identifier of the pane to terminate.

        Returns:
            Command argument list.
        """
        return ["herdr", "pane", "close", pane_id]
