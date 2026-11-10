"""Tests for Ticket Graph to Herdr DAG Compiler & LaneOrchestrator.

Seam 2: Verifies that to-tickets/scripts/compile_dag.py can:
1. Parse OKF Ticket dependencies and group them into topological execution phases.
2. Compile real-world tickets (docs/tickets/pedroca-skills-transition) into two phases.
3. Detect dependency cycles and raise CycleDetectedError.
4. Detect missing dependency targets and raise MissingDependencyError.
5. Round-trip compiled DAGs through Herdr LaneOrchestrator (brief, prompt, receipt).
6. Run successfully via CLI invocation producing valid DAG JSON matching schema.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Add scripts and orchestrator paths to sys.path
TO_TICKETS_SCRIPTS = REPO_ROOT / "skills" / "spine" / "to-tickets" / "scripts"
if str(TO_TICKETS_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(TO_TICKETS_SCRIPTS))

HERDR_DIR = REPO_ROOT / "skills" / "spine" / "herdr-orchestration"
if str(HERDR_DIR) not in sys.path:
    sys.path.insert(0, str(HERDR_DIR))

# Import LaneOrchestrator components
from subagent.orchestrator import LaneConfig, LaneOrchestrator, LaneType

# Target module under test
try:
    import compile_dag
    from compile_dag import (
        compile_dag,
        CycleDetectedError,
        MissingDependencyError,
    )
except ImportError:
    try:
        from to_tickets.scripts.compile_dag import (
            compile_dag,
            CycleDetectedError,
            MissingDependencyError,
        )
    except ImportError:
        _script_file = TO_TICKETS_SCRIPTS / "compile_dag.py"
        if _script_file.exists():
            import importlib.util
            _spec = importlib.util.spec_from_file_location("compile_dag", str(_script_file))
            _mod = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_mod)
            compile_dag = getattr(_mod, "compile_dag")
            CycleDetectedError = getattr(_mod, "CycleDetectedError")
            MissingDependencyError = getattr(_mod, "MissingDependencyError")
        else:
            compile_dag = None
            class CycleDetectedError(Exception):  # type: ignore[no-redef]
                pass
            class MissingDependencyError(Exception):  # type: ignore[no-redef]
                pass

try:
    from compile_dag import to_lane_configs  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    try:
        from to_tickets.scripts.compile_dag import to_lane_configs  # type: ignore[attr-defined]
    except (ImportError, AttributeError):
        to_lane_configs = None

CLI_SCRIPT = TO_TICKETS_SCRIPTS / "compile_dag.py"


def create_ticket_file(
    directory: Path,
    filename: str,
    title: str,
    depends_on: list[str] | None = None,
    allowed_paths: list[str] | None = None,
    description: str = "",
) -> Path:
    """Helper to create a well-formed OKF v0.2 ticket file."""
    if depends_on:
        relations_yaml = "relations:\n" + "\n".join(
            f"  - type: depends_on\n    target: {dep}" for dep in depends_on
        )
    else:
        relations_yaml = "relations: []"

    paths_str = ", ".join(f"`{p}`" for p in allowed_paths) if allowed_paths else "`src/**`"
    desc_str = description or f"Work item for {title}."

    content = f"""---
id: ticket-{Path(filename).stem}
title: "{title}"
type: Architecture
status: active
valid_from: 2026-11-09
artifact: ticket
scope:
  system: pedroca-skills
  env: production
{relations_yaml}
tags:
  - ticket
---

# {title}

**What to build:** {desc_str}

**Blocked by:** {"None" if not depends_on else ", ".join(depends_on)}

**Allowed paths:** {paths_str}

**Status:** ready-for-agent

- [ ] Task item 1
"""
    file_path = directory / filename
    file_path.write_text(content, encoding="utf-8")
    return file_path


def test_topological_phase_grouping_linear_and_branching(tmp_path: Path):
    """Test 4 OKF tickets compiled into 3 topological execution phases.

    - 01-unblocked.md (no depends_on)
    - 02-first-branch.md (depends on ./01-unblocked.md)
    - 03-second-branch.md (depends on ./01-unblocked.md)
    - 04-join.md (depends on ./02-first-branch.md and ./03-second-branch.md)

    Verifies 3 topological execution phases:
    - Phase 1: [01-unblocked]
    - Phase 2: [02-first-branch, 03-second-branch] (order independent)
    - Phase 3: [04-join]
    """
    if compile_dag is None:
        pytest.fail("to-tickets/scripts/compile_dag.py is not available")

    # Create 4 OKF tickets
    create_ticket_file(
        tmp_path,
        "01-unblocked.md",
        "01 — Unblocked Task",
        depends_on=[],
        allowed_paths=["src/core/**"],
        description="Unblocked base task",
    )
    create_ticket_file(
        tmp_path,
        "02-first-branch.md",
        "02 — First Branch Task",
        depends_on=["./01-unblocked.md"],
        allowed_paths=["src/branch1/**"],
        description="First branch task",
    )
    create_ticket_file(
        tmp_path,
        "03-second-branch.md",
        "03 — Second Branch Task",
        depends_on=["./01-unblocked.md"],
        allowed_paths=["src/branch2/**"],
        description="Second branch task",
    )
    create_ticket_file(
        tmp_path,
        "04-join.md",
        "04 — Join Task",
        depends_on=["./02-first-branch.md", "./03-second-branch.md"],
        allowed_paths=["src/join/**"],
        description="Join branch results",
    )

    dag = compile_dag(tmp_path)
    assert isinstance(dag, dict), "compile_dag must return a dictionary"
    assert "phases" in dag, "DAG output must contain 'phases'"

    phases = dag["phases"]
    assert len(phases) == 3, f"Expected 3 phases, got {len(phases)}"

    def extract_lane_names(phase_dict: dict) -> list[str]:
        return [l["name"] if isinstance(l, dict) else l.name for l in phase_dict["lanes"]]

    # Phase 1: [01-unblocked]
    p1_names = extract_lane_names(phases[0])
    assert len(p1_names) == 1, f"Expected 1 lane in Phase 1, got {p1_names}"
    assert any("01-unblocked" in n or "unblocked" in n for n in p1_names)

    # Phase 2: [02-first-branch, 03-second-branch] (order independent)
    p2_names = extract_lane_names(phases[1])
    assert len(p2_names) == 2, f"Expected 2 lanes in Phase 2, got {p2_names}"
    assert any("first-branch" in n for n in p2_names)
    assert any("second-branch" in n for n in p2_names)

    # Phase 3: [04-join]
    p3_names = extract_lane_names(phases[2])
    assert len(p3_names) == 1, f"Expected 1 lane in Phase 3, got {p3_names}"
    assert any("join" in n for n in p3_names)


def test_real_world_pedroca_skills_transition_tickets():
    """Run compile_dag against repo's own docs/tickets/pedroca-skills-transition.

    Verifies:
    - Topic is 'pedroca-skills-transition'
    - Has 2 phases
    - Phase 1 contains 'prune-lockfile-and-retired-skills' and 'setup-pedroca-skills-and-okf-bootstrapper'
    - Phase 2 contains 'artifact-spine-and-ticket-dag-compiler',
      'single-scope-implement-and-herdr-alignment', and 'akashic-architecture-review-and-router-skills'
    - Paths, description, dependencies are correctly extracted
    """
    if compile_dag is None:
        pytest.fail("to-tickets/scripts/compile_dag.py is not available")

    tickets_dir = REPO_ROOT / "docs" / "tickets" / "pedroca-skills-transition"
    assert tickets_dir.exists(), f"Tickets directory {tickets_dir} does not exist"

    dag = compile_dag(tickets_dir)
    assert isinstance(dag, dict)
    assert dag.get("topic") == "pedroca-skills-transition"
    assert "phases" in dag
    phases = dag["phases"]
    assert len(phases) == 2, f"Expected 2 phases, got {len(phases)}"

    def extract_lane_names(phase_dict: dict) -> list[str]:
        return [l["name"] if isinstance(l, dict) else l.name for l in phase_dict["lanes"]]

    # Phase 1 verification
    p1_names = extract_lane_names(phases[0])
    assert len(p1_names) == 2, f"Expected 2 lanes in Phase 1, got {p1_names}"
    assert any("prune-lockfile-and-retired-skills" in n for n in p1_names)
    assert any("setup-pedroca-skills-and-okf-bootstrapper" in n for n in p1_names)

    # Phase 2 verification
    p2_names = extract_lane_names(phases[1])
    assert len(p2_names) == 3, f"Expected 3 lanes in Phase 2, got {p2_names}"
    assert any("artifact-spine-and-ticket-dag-compiler" in n for n in p2_names)
    assert any("single-scope-implement-and-herdr-alignment" in n for n in p2_names)
    assert any("akashic-architecture-review-and-router-skills" in n for n in p2_names)

    # Verify extracted properties (paths, description, dependencies)
    p2_lanes = phases[1]["lanes"]
    lane_03 = next(
        l for l in p2_lanes
        if "artifact-spine-and-ticket-dag-compiler" in (l["name"] if isinstance(l, dict) else l.name)
    )
    lane_03_dict = lane_03 if isinstance(lane_03, dict) else lane_03.__dict__

    assert lane_03_dict.get("description"), "Lane 03 must have a non-empty description"
    paths = lane_03_dict.get("paths", [])
    assert len(paths) > 0, "Lane 03 must have paths extracted"
    assert any("to-tickets" in p for p in paths), f"Expected to-tickets in paths, got {paths}"

    deps = lane_03_dict.get("dependencies", [])
    assert len(deps) > 0, "Lane 03 must have dependencies extracted"
    assert any(
        "setup-pedroca-skills-and-okf-bootstrapper" in d for d in deps
    ), f"Expected setup-pedroca-skills in dependencies, got {deps}"

    # Verify lane 04 dependencies (depends on 01)
    lane_04 = next(
        l for l in p2_lanes
        if "single-scope-implement-and-herdr-alignment" in (l["name"] if isinstance(l, dict) else l.name)
    )
    lane_04_dict = lane_04 if isinstance(lane_04, dict) else lane_04.__dict__
    deps_04 = lane_04_dict.get("dependencies", [])
    assert any("prune-lockfile-and-retired-skills" in d for d in deps_04)

    # Verify lane 05 dependencies (depends on 01 and 02)
    lane_05 = next(
        l for l in p2_lanes
        if "akashic-architecture-review-and-router-skills" in (l["name"] if isinstance(l, dict) else l.name)
    )
    lane_05_dict = lane_05 if isinstance(lane_05, dict) else lane_05.__dict__
    deps_05 = lane_05_dict.get("dependencies", [])
    assert any("prune-lockfile-and-retired-skills" in d for d in deps_05)
    assert any("setup-pedroca-skills-and-okf-bootstrapper" in d for d in deps_05)


def test_cycle_detection(tmp_path: Path):
    """Create tickets with a dependency cycle (A -> B -> C -> A) and verify CycleDetectedError."""
    if compile_dag is None:
        pytest.fail("to-tickets/scripts/compile_dag.py is not available")

    create_ticket_file(
        tmp_path,
        "01-task-a.md",
        "01 — Task A",
        depends_on=["./03-task-c.md"],
    )
    create_ticket_file(
        tmp_path,
        "02-task-b.md",
        "02 — Task B",
        depends_on=["./01-task-a.md"],
    )
    create_ticket_file(
        tmp_path,
        "03-task-c.md",
        "03 — Task C",
        depends_on=["./02-task-b.md"],
    )

    with pytest.raises(CycleDetectedError):
        compile_dag(tmp_path)


def test_missing_target_detection(tmp_path: Path):
    """Create a ticket that depends on a non-existent file and verify MissingDependencyError."""
    if compile_dag is None:
        pytest.fail("to-tickets/scripts/compile_dag.py is not available")

    create_ticket_file(
        tmp_path,
        "01-orphan.md",
        "01 — Orphan Task",
        depends_on=["./non-existent.md"],
    )

    with pytest.raises(MissingDependencyError):
        compile_dag(tmp_path)


def test_round_trip_with_lane_orchestrator():
    """Convert compiled DAG output into LaneConfig objects and round-trip through LaneOrchestrator:
    - build_lane_brief
    - build_lane_prompt
    - verify_lane_receipt (validates VERDICT: PASSED and WORKFLOW: /implement returns (True, ...))
    """
    if compile_dag is None:
        pytest.fail("to-tickets/scripts/compile_dag.py is not available")

    tickets_dir = REPO_ROOT / "docs" / "tickets" / "pedroca-skills-transition"
    dag = compile_dag(tickets_dir)

    lane_configs: list[LaneConfig] = []
    if to_lane_configs is not None:
        res = to_lane_configs(dag)
        if isinstance(res, dict):
            for phase_lanes in res.values():
                lane_configs.extend(phase_lanes)
        else:
            lane_configs = list(res)
    else:
        for phase in dag["phases"]:
            for lane_data in phase["lanes"]:
                raw_type = lane_data.get("type", "implementation")
                try:
                    lane_type = LaneType(raw_type)
                except ValueError:
                    lane_type = LaneType.IMPLEMENTATION
                lane_configs.append(
                    LaneConfig(
                        name=lane_data["name"],
                        lane_type=lane_type,
                        description=lane_data.get("description", "Test lane description"),
                        paths=lane_data.get("paths", []),
                        stage1_test=lane_data.get("stage1_test", ""),
                        dependencies=lane_data.get("dependencies", []),
                        required_skills=lane_data.get("required_skills", ["implement", "tdd"]),
                    )
                )

    assert len(lane_configs) > 0, "Must have at least one LaneConfig to round-trip"

    session_id = "test-session-roundtrip"
    topic = dag.get("topic", "test-topic")

    for lane in lane_configs:
        branch = f"lane/{topic}-{lane.name}"

        # 1. Test build_lane_brief
        brief = LaneOrchestrator.build_lane_brief(
            lane=lane,
            session_id=session_id,
            topic=topic,
            worktree_dir=f"/tmp/worktrees/{topic}/{lane.name}",
            branch=branch,
            base_branch="main",
            predecessor_receipts=None,
        )
        assert isinstance(brief, str)
        assert f"# Lane Kickoff Brief: {lane.name}" in brief
        assert lane.description in brief
        assert f"- **Session**: {session_id}" in brief
        assert f"- **Branch**: {branch}" in brief
        if lane.paths:
            for p in lane.paths:
                assert p in brief

        # 2. Test build_lane_prompt
        prompt = LaneOrchestrator.build_lane_prompt(
            lane=lane,
            session_id=session_id,
            branch=branch,
        )
        assert isinstance(prompt, str)
        assert f"/tmp/handoff-{session_id}-{lane.name}.md" in prompt
        assert f"/tmp/handoff-{session_id}-{lane.name}-result.md" in prompt
        if LaneOrchestrator.is_implementation_lane(lane):
            assert prompt.startswith("/implement")

        # 3. Test verify_lane_receipt with valid receipt
        valid_receipt = f"""# Lane Completion Receipt: {lane.name}

**VERDICT**: PASSED
**WORKFLOW**: /implement executed successfully with TDD slices.
**COMMITS**: 7cc8103
**FILES_MODIFIED**: {", ".join(lane.paths) if lane.paths else "None"}
**STAGE_1_VERIFICATION**: pytest tests/ - exit 0
**EXPORTED_CONTRACTS**: None
"""
        passed, msg = LaneOrchestrator.verify_lane_receipt(lane, valid_receipt)
        assert passed is True, f"Valid receipt was rejected: {msg}"
        assert "passed" in msg.lower()

        # 4. Test verify_lane_receipt with FAILED receipt
        failed_receipt = f"""# Lane Completion Receipt: {lane.name}

**VERDICT**: FAILED
**WORKFLOW**: /implement executed with errors.
"""
        passed, msg = LaneOrchestrator.verify_lane_receipt(lane, failed_receipt)
        assert passed is False
        assert "failed" in msg.lower()

        # 5. Test verify_lane_receipt with missing /implement on implementation lane
        if LaneOrchestrator.is_implementation_lane(lane):
            invalid_workflow_receipt = f"""# Lane Completion Receipt: {lane.name}

**VERDICT**: PASSED
**WORKFLOW**: manual edits without implement
"""
            passed, msg = LaneOrchestrator.verify_lane_receipt(lane, invalid_workflow_receipt)
            assert passed is False
            assert "rejected" in msg.lower()


def test_cli_compilation(tmp_path: Path):
    """Execute python3 to-tickets/scripts/compile_dag.py via subprocess CLI.

    - Test --tickets-dir docs/tickets/pedroca-skills-transition --output <tmp_json>
    - Assert exit code 0 and valid JSON produced matching schema.
    """
    tickets_dir = REPO_ROOT / "docs" / "tickets" / "pedroca-skills-transition"
    out_file = tmp_path / "compiled_dag.json"

    cmd = [
        sys.executable,
        str(CLI_SCRIPT),
        "--tickets-dir",
        str(tickets_dir),
        "--output",
        str(out_file),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"CLI exited with {proc.returncode}.\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    assert out_file.exists(), f"Expected output JSON file {out_file} was not created"

    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "Output JSON must parse to a dict"
    assert data.get("topic") == "pedroca-skills-transition"
    assert "phases" in data
    assert len(data["phases"]) == 2

    # Verify phases schema matches herdr-orchestration DAG schema
    for phase in data["phases"]:
        assert "phase" in phase
        assert isinstance(phase["phase"], int)
        assert "lanes" in phase
        assert isinstance(phase["lanes"], list)
        for lane in phase["lanes"]:
            assert "name" in lane
            assert "type" in lane
            assert "description" in lane
            assert "paths" in lane
            assert isinstance(lane["paths"], list)
