"""Lane orchestration module for Herdr multi-lane workflows.

Enforces lane classification, prompt construction, brief generation,
and completion receipt verification for two-stage gates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import re

_VERDICT_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:\*\*)?VERDICT(?:\*\*)?:\s*([A-Za-z_-]+)"
)
_WORKFLOW_PATTERN = re.compile(
    r"(?:^|\n)\s*(?:\*\*)?WORKFLOW(?:\*\*)?:\s*(.+)"
)


class LaneType(str, Enum):
    """Classification of workstream lanes in Herdr orchestration."""

    IMPLEMENTATION = "implementation"
    DOCS = "docs"
    RESEARCH = "research"
    CHORE = "chore"


@dataclass
class LaneConfig:
    """Configuration and bounded scope for an orchestration lane."""

    name: str
    lane_type: LaneType
    description: str
    paths: list[str] = field(default_factory=list)
    stage1_test: str = ""
    dependencies: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)


class LaneOrchestrator:
    """Orchestrator enforcing lane prompts, kickoff briefs, and verification receipts."""

    @staticmethod
    def is_implementation_lane(lane: LaneConfig) -> bool:
        """Determine if a lane requires implementation workflows."""
        return (
            lane.lane_type == LaneType.IMPLEMENTATION
            or any(s.strip().lower() == "implement" for s in lane.required_skills)
        )

    @staticmethod
    def build_lane_prompt(lane: LaneConfig, session_id: str, branch: str) -> str:
        """Construct the prompt sent to a lane agent."""
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
        """Generate the markdown kickoff brief for a lane agent."""
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
        """Verify the completion receipt from a lane agent against verification gates."""
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
