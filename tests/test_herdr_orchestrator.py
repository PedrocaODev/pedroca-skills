"""Tests for Herdr LaneOrchestrator conforming to Spec Seam 2."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest

# Ensure herdr-orchestration is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
HERDR_DIR = REPO_ROOT / "skills" / "spine" / "herdr-orchestration"
if str(HERDR_DIR) not in sys.path:
    sys.path.insert(0, str(HERDR_DIR))

from subagent.orchestrator import LaneConfig, LaneOrchestrator, LaneType


class TestIsImplementationLane:
    """Verifies LaneOrchestrator.is_implementation_lane classification."""

    def test_implementation_lane_type(self) -> None:
        lane = LaneConfig(
            name="core-backend",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core logic",
        )
        assert LaneOrchestrator.is_implementation_lane(lane) is True

    def test_chore_with_implement_skill(self) -> None:
        lane = LaneConfig(
            name="refactor-seam",
            lane_type=LaneType.CHORE,
            description="Refactoring",
            required_skills=["implement", "tdd"],
        )
        assert LaneOrchestrator.is_implementation_lane(lane) is True

    def test_docs_with_implement_skill_case_insensitive(self) -> None:
        lane = LaneConfig(
            name="specs",
            lane_type=LaneType.DOCS,
            description="Docs",
            required_skills=["IMPLEMENT"],
        )
        assert LaneOrchestrator.is_implementation_lane(lane) is True

    def test_non_implementation_lane_docs(self) -> None:
        lane = LaneConfig(
            name="api-docs",
            lane_type=LaneType.DOCS,
            description="API Documentation",
            required_skills=["writing-for-agents"],
        )
        assert LaneOrchestrator.is_implementation_lane(lane) is False

    def test_non_implementation_lane_research(self) -> None:
        lane = LaneConfig(
            name="perf-eval",
            lane_type=LaneType.RESEARCH,
            description="Performance benchmark",
        )
        assert LaneOrchestrator.is_implementation_lane(lane) is False


class TestBuildLanePrompt:
    """Verifies LaneOrchestrator.build_lane_prompt construction."""

    def test_implementation_lane_prompt_structure(self) -> None:
        lane = LaneConfig(
            name="auth-api",
            lane_type=LaneType.IMPLEMENTATION,
            description="Auth endpoints",
            paths=["src/api/auth/**"],
            stage1_test="pytest tests/test_auth.py",
            required_skills=["implement", "tdd"],
        )
        prompt = LaneOrchestrator.build_lane_prompt(
            lane=lane, session_id="123456", branch="lane/auth-api"
        )
        assert prompt.startswith("/implement Execute the task specified in /tmp/handoff-123456-auth-api.md.")
        assert "Read the kickoff brief" in prompt
        assert "strictly adhere to the /implement workflow" in prompt
        assert "TDD slices, regular typechecking/tests, and pre-commit self-review with /code-review" in prompt
        assert "commit work to branch lane/auth-api" in prompt
        assert "write the completion receipt to /tmp/handoff-123456-auth-api-result.md" in prompt
        assert prompt.endswith("Reply when complete.")

    def test_non_implementation_lane_prompt_structure(self) -> None:
        lane = LaneConfig(
            name="api-docs",
            lane_type=LaneType.DOCS,
            description="API docs",
            paths=["docs/**"],
        )
        prompt = LaneOrchestrator.build_lane_prompt(
            lane=lane, session_id="123456", branch="lane/api-docs"
        )
        assert not prompt.startswith("/implement")
        assert prompt.startswith("Execute the task specified in /tmp/handoff-123456-api-docs.md.")
        assert "commit work to branch lane/api-docs" in prompt
        assert "write the completion receipt to /tmp/handoff-123456-api-docs-result.md" in prompt
        assert prompt.endswith("Reply when complete.")


class TestBuildLaneBrief:
    """Verifies LaneOrchestrator.build_lane_brief kickoff brief markdown generation."""

    def test_implementation_lane_brief_with_dependencies(self) -> None:
        lane = LaneConfig(
            name="auth-api",
            lane_type=LaneType.IMPLEMENTATION,
            description="Authentication API endpoints and JWT middleware.",
            paths=["src/api/auth/**", "src/middleware/**"],
            stage1_test="pytest tests/test_auth.py",
            dependencies=["core-schema"],
            required_skills=["implement", "tdd", "code-review"],
        )
        brief = LaneOrchestrator.build_lane_brief(
            lane=lane,
            session_id="999",
            topic="auth-system",
            worktree_dir="/home/user/.herdr/worktrees/repo/lane-auth-api",
            branch="lane/auth-system-auth-api",
            base_branch="main",
            predecessor_receipts=["/tmp/handoff-999-core-schema-result.md"],
        )
        assert "# Lane Kickoff Brief: auth-api" in brief
        assert "- **Session**: 999" in brief
        assert "- **Topic**: auth-system" in brief
        assert "- **Lane**: auth-api" in brief
        assert "- **Worktree**: /home/user/.herdr/worktrees/repo/lane-auth-api" in brief
        assert "- **Branch**: lane/auth-system-auth-api" in brief
        assert "- **Base**: main" in brief
        assert "## Objective\nAuthentication API endpoints and JWT middleware." in brief
        assert "- src/api/auth/**" in brief
        assert "- src/middleware/**" in brief
        assert "- Predecessor receipt: /tmp/handoff-999-core-schema-result.md" in brief
        assert "## Required Skills & Workflow" in brief
        assert "Mandatory workflow: You MUST execute `/implement` for this implementation lane" in brief
        assert "You MUST declare `WORKFLOW: /implement` in your completion receipt." in brief
        assert "pytest tests/test_auth.py" in brief
        assert "1. Commit all completed work to branch `lane/auth-system-auth-api`." in brief
        assert "`WORKFLOW`: `/implement` (must declare implement workflow)" in brief

    def test_non_implementation_lane_brief_root_phase(self) -> None:
        lane = LaneConfig(
            name="research-perf",
            lane_type=LaneType.RESEARCH,
            description="Investigate memory footprint",
            required_skills=["research"],
        )
        brief = LaneOrchestrator.build_lane_brief(
            lane=lane,
            session_id="111",
            topic="perf-audit",
            worktree_dir="/tmp/wt",
            branch="lane/perf-audit-research-perf",
            base_branch="main",
        )
        assert "# Lane Kickoff Brief: research-perf" in brief
        assert "- (Unrestricted or root scope)" in brief
        assert "None (Root Phase Lane)" in brief
        assert "Apply skills appropriate for research: research." in brief
        assert "# No stage 1 test specified" in brief
        assert "- `WORKFLOW`: Description of executed workflow" in brief


class TestVerifyLaneReceipt:
    """Verifies LaneOrchestrator.verify_lane_receipt validation gates."""

    def test_implementation_lane_passed_with_workflow(self) -> None:
        lane = LaneConfig(
            name="core",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core implementation",
        )
        receipt = """# Lane Completion Receipt: core
- **VERDICT**: PASSED
- **WORKFLOW**: /implement
- **COMMITS**: abc1234
"""
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is True
        assert msg == "Stage 1 verification passed"

    def test_implementation_lane_passed_case_variations(self) -> None:
        lane = LaneConfig(
            name="core",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core implementation",
        )
        receipt = """# Lane Completion Receipt: core
VERDICT: passed
WORKFLOW: implement
"""
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is True
        assert msg == "Stage 1 verification passed"

    def test_non_implementation_lane_does_not_require_workflow(self) -> None:
        lane = LaneConfig(
            name="docs",
            lane_type=LaneType.DOCS,
            description="Docs writing",
        )
        receipt = """# Lane Completion Receipt: docs
- **VERDICT**: PASSED
- **COMMITS**: abc1234
"""
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is True
        assert msg == "Stage 1 verification passed"

    def test_missing_verdict_fails(self) -> None:
        lane = LaneConfig(
            name="core",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core implementation",
        )
        receipt = "Some notes but no verdict"
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is False
        assert "missing or failed VERDICT" in msg

    def test_failed_verdict_fails(self) -> None:
        lane = LaneConfig(
            name="core",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core implementation",
        )
        receipt = "VERDICT: FAILED\nWORKFLOW: /implement"
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is False
        assert "missing or failed VERDICT" in msg

    def test_implementation_lane_missing_workflow_fails(self) -> None:
        lane = LaneConfig(
            name="core",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core implementation",
        )
        receipt = "VERDICT: PASSED\nCOMMITS: 1234"
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is False
        assert msg == "Stage 1 rejected: implementation lane did not execute /implement workflow"

    def test_implementation_lane_wrong_workflow_fails(self) -> None:
        lane = LaneConfig(
            name="core",
            lane_type=LaneType.IMPLEMENTATION,
            description="Core implementation",
        )
        receipt = "VERDICT: PASSED\nWORKFLOW: ad-hoc-manual-coding"
        ok, msg = LaneOrchestrator.verify_lane_receipt(lane, receipt)
        assert ok is False
        assert msg == "Stage 1 rejected: implementation lane did not execute /implement workflow"


class TestTicketDAGLoading:
    """Verifies consuming compiled Ticket DAG from /to-tickets and round-tripping."""

    @pytest.fixture
    def sample_dag_dict(self) -> dict:
        return {
            "topic": "feature-auth",
            "base_branch": "main",
            "phases": [
                {
                    "phase": 1,
                    "lanes": [
                        {
                            "name": "core-schema",
                            "type": "implementation",
                            "description": "Database migrations and token schemas",
                            "paths": ["src/db/**", "src/models/**"],
                            "stage1_test": "pytest tests/test_models.py",
                            "required_skills": ["implement", "tdd"],
                        }
                    ],
                },
                {
                    "phase": 2,
                    "lanes": [
                        {
                            "name": "auth-api",
                            "type": "implementation",
                            "description": "Authentication endpoints and JWT middleware",
                            "paths": ["src/api/auth/**", "src/middleware/**"],
                            "dependencies": ["core-schema"],
                            "stage1_test": "pytest tests/test_auth.py",
                            "required_skills": ["implement", "tdd"],
                        },
                        {
                            "name": "api-docs",
                            "type": "docs",
                            "description": "API documentation and schema reference",
                            "paths": ["docs/api/**"],
                            "dependencies": ["auth-api"],
                            "stage1_test": "",
                            "required_skills": ["writing-for-agents"],
                        },
                    ],
                },
            ],
        }

    def test_load_dag_from_dict(self, sample_dag_dict: dict) -> None:
        dag = LaneOrchestrator.load_dag(sample_dag_dict)
        assert dag["topic"] == "feature-auth"
        assert dag["base_branch"] == "main"
        assert len(dag["phases"]) == 2

        phase1_lanes = dag["phases"][0]["lanes"]
        assert len(phase1_lanes) == 1
        lane0 = phase1_lanes[0]
        assert isinstance(lane0, LaneConfig)
        assert lane0.name == "core-schema"
        assert lane0.lane_type == LaneType.IMPLEMENTATION
        assert lane0.paths == ["src/db/**", "src/models/**"]
        assert lane0.stage1_test == "pytest tests/test_models.py"

        phase2_lanes = dag["phases"][1]["lanes"]
        assert len(phase2_lanes) == 2
        assert phase2_lanes[0].name == "auth-api"
        assert phase2_lanes[0].dependencies == ["core-schema"]
        assert phase2_lanes[1].name == "api-docs"
        assert phase2_lanes[1].lane_type == LaneType.DOCS

    def test_load_dag_from_json_file(self, tmp_path: Path, sample_dag_dict: dict) -> None:
        dag_file = tmp_path / "dag-test.json"
        dag_file.write_text(json.dumps(sample_dag_dict), encoding="utf-8")

        dag = LaneOrchestrator.load_dag(dag_file)
        assert dag["topic"] == "feature-auth"
        assert len(dag["phases"]) == 2
        assert isinstance(dag["phases"][0]["lanes"][0], LaneConfig)

    def test_load_dag_invalid_inputs(self) -> None:
        with pytest.raises(ValueError, match="must be a dict or valid path"):
            LaneOrchestrator.load_dag(12345)  # type: ignore

        with pytest.raises(ValueError, match="missing required 'topic' or 'phases'"):
            LaneOrchestrator.load_dag({"base_branch": "main"})

        with pytest.raises(ValueError, match="'phases' must be a list"):
            LaneOrchestrator.load_dag({"topic": "t", "phases": "not-a-list"})

    def test_load_dag_roundtrip_execution(self, sample_dag_dict: dict) -> None:
        dag = LaneOrchestrator.load_dag(sample_dag_dict)
        for phase_info in dag["phases"]:
            for lane in phase_info["lanes"]:
                prompt = LaneOrchestrator.build_lane_prompt(
                    lane=lane, session_id="test-session", branch=f"lane/{dag['topic']}-{lane.name}"
                )
                assert f"handoff-test-session-{lane.name}.md" in prompt

                brief = LaneOrchestrator.build_lane_brief(
                    lane=lane,
                    session_id="test-session",
                    topic=dag["topic"],
                    worktree_dir=f"/tmp/wt/{lane.name}",
                    branch=f"lane/{dag['topic']}-{lane.name}",
                    base_branch=dag["base_branch"],
                )
                assert f"# Lane Kickoff Brief: {lane.name}" in brief

                workflow_line = "- **WORKFLOW**: /implement\n" if LaneOrchestrator.is_implementation_lane(lane) else ""
                simulated_receipt = f"- **VERDICT**: PASSED\n{workflow_line}"
                ok, msg = LaneOrchestrator.verify_lane_receipt(lane, simulated_receipt)
                assert ok is True
                assert msg == "Stage 1 verification passed"
