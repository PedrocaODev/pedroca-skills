"""Lane orchestration module for Herdr multi-lane workflows.

Enforces canonical CONTEXT.md terminology (Lane, Specialist Subagent, Kickoff Brief,
Completion Receipt, Verification Gate), prompt construction, Kickoff Brief generation,
Ticket DAG loading from /to-tickets, and Completion Receipt verification for two-stage gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
import re
from typing import Any

# Match VERDICT with optional markdown list bullet (- or *) and bold formatting
_VERDICT_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:[-*]\s+)?(?:\*\*)?VERDICT(?:\*\*)?:\s*([A-Za-z_-]+)"
)
# Match WORKFLOW with optional markdown list bullet (- or *) and bold formatting
_WORKFLOW_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:[-*]\s+)?(?:\*\*)?WORKFLOW(?:\*\*)?:\s*(.+)"
)


class LaneType(str, Enum):
    """Classification of workstream lanes in Herdr orchestration."""

    IMPLEMENTATION = "implementation"
    DOCS = "docs"
    RESEARCH = "research"
    CHORE = "chore"


@dataclass
class LaneConfig:
    """Configuration and bounded scope for an orchestration Lane."""

    name: str
    lane_type: LaneType
    description: str
    paths: list[str] = field(default_factory=list)
    stage1_test: str = ""
    dependencies: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)


class LaneOrchestrator:
    """Orchestrator enforcing Lane prompts, Kickoff Briefs, and Completion Receipt verification."""

    @staticmethod
    def is_implementation_lane(lane: LaneConfig) -> bool:
        """Determine if a Lane requires implementation workflows (/implement, /tdd, /code-review)."""
        return (
            lane.lane_type == LaneType.IMPLEMENTATION
            or any(
                s.strip().lower() in ("implement", "/implement")
                for s in lane.required_skills
            )
        )

    @staticmethod
    def build_lane_prompt(lane: LaneConfig, session_id: str, branch: str) -> str:
        """Construct the prompt dispatched to a Lane session."""
        handoff_file = f"/tmp/handoff-{session_id}-{lane.name}.md"
        result_file = f"/tmp/handoff-{session_id}-{lane.name}-result.md"
        is_impl = LaneOrchestrator.is_implementation_lane(lane)

        if is_impl:
            return (
                f"/implement Execute the task specified in {handoff_file}. "
                f"Read the kickoff brief, strictly adhere to the /implement workflow "
                f"(TDD slices, regular typechecking/tests, and pre-commit self-review with /code-review), "
                f"implement changes within assigned file boundaries, "
                f"execute Stage 1 self-verification, commit work to branch {branch}, "
                f"and write the completion receipt to {result_file}. Reply when complete."
            )
        else:
            return (
                f"Execute the task specified in {handoff_file}. "
                f"Read the kickoff brief, execute changes within assigned file boundaries, "
                f"execute Stage 1 self-verification, commit work to branch {branch}, "
                f"and write the completion receipt to {result_file}. Reply when complete."
            )

    @staticmethod
    def build_lane_brief(
        lane: LaneConfig,
        session_id: str,
        topic: str,
        worktree_dir: str,
        branch: str,
        base_branch: str,
        predecessor_receipts: list[str] | None = None,
    ) -> str:
        """Generate the markdown Kickoff Brief for a Lane."""
        lines = [
            f"# Lane Kickoff Brief: {lane.name}",
            "",
            f"- **Session**: {session_id}",
            f"- **Topic**: {topic}",
            f"- **Lane**: {lane.name}",
            f"- **Worktree**: {worktree_dir}",
            f"- **Branch**: {branch}",
            f"- **Base**: {base_branch}",
            "",
            "## Objective",
            lane.description,
            "",
            "## Scope & File Boundaries",
            "Strictly restrict file additions, edits, and deletions to:",
        ]

        if lane.paths:
            for p in lane.paths:
                lines.append(f"- {p}")
        else:
            lines.append("- (Unrestricted or root scope)")
        lines.extend([
            "Do not modify files outside this designated scope.",
            "",
            "## Upstream Contracts & Dependencies",
        ])

        if predecessor_receipts:
            lines.append("Read outputs from prerequisite lanes:")
            for receipt in predecessor_receipts:
                lines.append(f"- Predecessor receipt: {receipt}")
        elif lane.dependencies:
            lines.append(f"Dependencies: {', '.join(lane.dependencies)}")
        else:
            lines.append("None (Root Phase Lane)")

        lines.append("")

        is_impl = LaneOrchestrator.is_implementation_lane(lane)
        if is_impl:
            skills_str = (
                ", ".join(lane.required_skills)
                if lane.required_skills
                else "implement, tdd, code-review"
            )
            lines.extend([
                "## Required Skills & Workflow",
                f"- Mandatory workflow: You MUST execute `/implement` for this implementation lane (skills: {skills_str}).",
                "- Enforce test-driven development (TDD), verification planning, and code review.",
                "- You MUST declare `WORKFLOW: /implement` in your completion receipt.",
                "",
            ])
        else:
            if lane.required_skills:
                skills_str = ", ".join(lane.required_skills)
                lines.extend([
                    "## Required Skills",
                    f"- Apply skills appropriate for {lane.lane_type.value}: {skills_str}.",
                    "",
                ])
            else:
                lines.extend([
                    "## Required Skills",
                    f"- Apply skills appropriate for {lane.lane_type.value}.",
                    "",
                ])

        lines.extend([
            "## Stage 1 Verification Criteria",
            "Before declaring completion, run and pass within this worktree:",
            "```bash",
            lane.stage1_test if lane.stage1_test else "# No stage 1 test specified",
            "```",
            "",
            "## Completion Protocol",
            f"1. Commit all completed work to branch `{branch}`.",
            f"2. Write a completion receipt to `/tmp/handoff-{session_id}-{lane.name}-result.md` adhering to the required schema:",
            "   - `VERDICT`: `PASSED` or `FAILED`",
        ])
        if is_impl:
            lines.append("   - `WORKFLOW`: `/implement` (must declare implement workflow)")
        else:
            lines.append("   - `WORKFLOW`: Description of executed workflow")
        lines.extend([
            "   - `COMMITS`: List of commit hashes created",
            "   - `FILES_MODIFIED`: List of modified file paths",
            "   - `STAGE_1_VERIFICATION`: Exact test commands executed and output summary",
            "   - `EXPORTED_CONTRACTS`: APIs, types, or interfaces produced for downstream lanes",
            "3. Reply to notify completion.",
            "",
        ])

        return "\n".join(lines)

    @staticmethod
    def verify_lane_receipt(lane: LaneConfig, receipt_content: str) -> tuple[bool, str]:
        """Verify the Completion Receipt from a Lane against Verification Gates."""
        verdict_match = _VERDICT_PATTERN.search(receipt_content)
        if not verdict_match or verdict_match.group(1).strip().upper() != "PASSED":
            return False, "Stage 1 verification failed: missing or failed VERDICT"

        if LaneOrchestrator.is_implementation_lane(lane):
            workflow_match = _WORKFLOW_PATTERN.search(receipt_content)
            if not workflow_match or "implement" not in workflow_match.group(1).lower():
                return (
                    False,
                    "Stage 1 rejected: implementation lane did not execute /implement workflow",
                )

        return True, "Stage 1 verification passed"

    @staticmethod
    def load_dag(dag_input: str | Path | dict[str, Any]) -> dict[str, Any]:
        """Load and validate a compiled Ticket DAG produced by /to-tickets.

        Args:
            dag_input: Path to a DAG JSON file or a dictionary containing the DAG schema.

        Returns:
            Dictionary with topic, base_branch, and parsed LaneConfig objects per phase.

        Raises:
            ValueError: If input format or DAG schema is invalid.
        """
        data: Any = None
        if isinstance(dag_input, dict):
            data = dag_input
        elif isinstance(dag_input, (str, Path)):
            path = Path(dag_input)
            if path.is_file():
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                except Exception as e:
                    raise ValueError(f"Failed to parse DAG JSON from {path}: {e}") from e
            elif isinstance(dag_input, str):
                try:
                    data = json.loads(dag_input)
                except Exception:
                    raise ValueError(f"dag_input must be a dict or valid path to a JSON file: {dag_input}")
            else:
                raise ValueError(f"dag_input must be a dict or valid path to a JSON file: {dag_input}")
        else:
            raise ValueError(f"dag_input must be a dict or valid path to a JSON file: {type(dag_input)}")

        if not isinstance(data, dict):
            raise ValueError("Invalid DAG: root must be a JSON object / dict")

        if "topic" not in data or "phases" not in data:
            raise ValueError("Invalid DAG schema: missing required 'topic' or 'phases'")

        phases_raw = data.get("phases")
        if not isinstance(phases_raw, list):
            raise ValueError("Invalid DAG schema: 'phases' must be a list")

        parsed_phases: list[dict[str, Any]] = []
        for phase_obj in phases_raw:
            if not isinstance(phase_obj, dict):
                raise ValueError("Invalid DAG schema: phase entry must be a dict")
            phase_num = phase_obj.get("phase", 0)
            lanes_raw = phase_obj.get("lanes", [])
            if not isinstance(lanes_raw, list):
                raise ValueError("Invalid DAG schema: 'lanes' must be a list")

            parsed_lanes: list[LaneConfig] = []
            for lane_dict in lanes_raw:
                if not isinstance(lane_dict, dict) or "name" not in lane_dict:
                    raise ValueError("Invalid DAG schema: lane must be a dict with 'name'")
                raw_type = str(lane_dict.get("type", "implementation")).lower()
                try:
                    lane_type = LaneType(raw_type)
                except ValueError:
                    lane_type = LaneType.IMPLEMENTATION

                parsed_lanes.append(
                    LaneConfig(
                        name=lane_dict["name"],
                        lane_type=lane_type,
                        description=lane_dict.get("description", ""),
                        paths=list(lane_dict.get("paths", [])),
                        stage1_test=lane_dict.get("stage1_test", ""),
                        dependencies=list(lane_dict.get("dependencies", [])),
                        required_skills=list(lane_dict.get("required_skills", [])),
                    )
                )
            parsed_phases.append({"phase": phase_num, "lanes": parsed_lanes})

        return {
            "topic": str(data.get("topic", "")),
            "base_branch": str(data.get("base_branch", "main")),
            "phases": parsed_phases,
        }
