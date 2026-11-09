"""Repository hygiene and skill contract test suite (Seam 3).

Verifies:
1. Lockfile hygiene: ~/.agents/.skill-lock.json contains zero entries pointing to mattpocock/skills.
2. Retired skills elimination: No retired skills or nested duplicates exist in repo root.
3. Lane skills hygiene: No stale references to setup-matt-pocock-skills or docs/agents/issue-tracker.md.
4. Repo-wide skill hygiene: No skills reference setup-matt-pocock-skills (skipping unmerged parallel lane skills).
5. Vault hygiene: `akashic lint --strict --vault docs` returns zero issues.
6. ask-pedroca contract: Valid frontmatter, spine skills, on-ramps, upkeep, foundations, and OKF CONTEXT terminology.
7. improve-codebase-architecture contract: Deterministic Akashic Code Graph tools referenced.
"""

import json
import re
import subprocess
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_LOCK_PATH = Path("/home/pedrogoncalves/.agents/.skill-lock.json")

RETIRED_SKILL_PATHS = [
    "setup-matt-pocock-skills",
    "ask-matt",
    "writing-beats",
    "writing-fragments",
    "writing-shape",
    "issue-workflow",
    "deepwork",
    "codemap",
    "loop-me",
    "loop-engineering",
    "implement/implement",
]

LANE_SKILLS = [
    "ask-pedroca",
    "improve-codebase-architecture",
    "code-review",
    "triage",
    "wayfinder",
    "diagnosing-bugs",
]

PARALLEL_LANE_SKILLS = {
    "to-spec",
    "to-tickets",
}

CANONICAL_SPINE_SKILLS = [
    "grill-with-docs",
    "to-spec",
    "to-tickets",
    "herdr-orchestration",
    "implement",
    "code-review",
]

ON_RAMP_SKILLS = [
    "triage",
    "diagnosing-bugs",
    "wayfinder",
]

UPKEEP_SKILLS = [
    "improve-codebase-architecture",
]

FOUNDATION_SKILLS = [
    "setup-pedroca-skills",
    "domain-modeling",
    "codebase-design",
    "akashic-cli",
]

CONTEXT_TERMINOLOGY = [
    "Orchestrator",
    "Lane",
    "Specialist Subagent",
    "Vault",
    "Spec",
    "Ticket",
    "Kickoff Brief",
    "Completion Receipt",
]

DETERMINISTIC_AKASHIC_TOOLS = [
    "graph_god_nodes",
    "graph_get_community",
    "graph_blast_radius",
    "akashic graph surprising",
]


def parse_frontmatter(content: str) -> dict:
    """Extract and parse YAML frontmatter from markdown content."""
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Missing leading '---' in frontmatter")

    end_idx = -1
    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = idx
            break

    if end_idx == -1:
        raise ValueError("Missing closing '---' in frontmatter")

    fm_raw = "\n".join(lines[1:end_idx])

    try:
        import yaml

        return yaml.safe_load(fm_raw) or {}
    except ImportError:
        pass

    # Fallback YAML parser for basic key-value pairs
    data = {}
    for line in fm_raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" in stripped:
            k, v = stripped.split(":", 1)
            k = k.strip()
            v = v.strip()
            if v.lower() == "true":
                data[k] = True
            elif v.lower() == "false":
                data[k] = False
            elif (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                data[k] = v[1:-1]
            else:
                data[k] = v
    return data


def test_skill_lock_no_mattpocock():
    """Verify ~/.agents/.skill-lock.json has zero mattpocock/skills entries and is non-empty."""
    assert SKILL_LOCK_PATH.is_file(), f"Lockfile does not exist at {SKILL_LOCK_PATH}"

    with open(SKILL_LOCK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    skills = data.get("skills", {})
    assert isinstance(skills, dict), f"Expected 'skills' mapping in lockfile, got {type(skills)}"
    assert len(skills) > 0, "Expected non-empty skills dictionary in lockfile"

    mattpocock_entries = [
        name
        for name, meta in skills.items()
        if isinstance(meta, dict) and meta.get("source") == "mattpocock/skills"
    ]
    assert not mattpocock_entries, (
        f"Found entries in skill-lock.json with source 'mattpocock/skills': {mattpocock_entries}"
    )


def test_retired_skills_absent():
    """Verify none of the retired skills or nested duplicates exist under repo root."""
    present = []
    for rel_path in RETIRED_SKILL_PATHS:
        target = REPO_ROOT / rel_path
        if target.exists():
            present.append(rel_path)

    assert not present, f"Retired skill directories or nested duplicates found under repo root: {present}"


def test_lane_skills_no_stale_references():
    """Verify lane skills contain no stale references to setup-matt-pocock-skills or docs/agents/issue-tracker.md."""
    stale_findings = []
    stale_patterns = ["setup-matt-pocock-skills", "docs/agents/issue-tracker.md"]

    for skill_name in LANE_SKILLS:
        skill_dir = REPO_ROOT / skill_name
        assert skill_dir.is_dir(), f"Expected lane skill directory to exist: {skill_dir}"
        for md_file in skill_dir.rglob("*.md"):
            content = md_file.read_text(encoding="utf-8", errors="ignore")
            for pattern in stale_patterns:
                if pattern in content:
                    stale_findings.append(f"{md_file.relative_to(REPO_ROOT)}: contains '{pattern}'")

    assert not stale_findings, (
        "Stale references found in lane skills:\n" + "\n".join(stale_findings)
    )


def test_all_skills_no_setup_matt_pocock_references():
    """Verify all skills across the repository have 0 occurrences of setup-matt-pocock-skills.

    Skips parallel lane skills (to-spec, to-tickets) pending Stage 2 integration merge.
    """
    skill_files = list(REPO_ROOT.glob("*/SKILL.md"))
    assert skill_files, "No SKILL.md files found in repository"

    non_parallel_violations = []
    parallel_lane_has_stale = False

    for skill_file in skill_files:
        skill_name = skill_file.parent.name
        content = skill_file.read_text(encoding="utf-8", errors="ignore")
        if "setup-matt-pocock-skills" in content:
            if skill_name in PARALLEL_LANE_SKILLS:
                parallel_lane_has_stale = True
            else:
                non_parallel_violations.append(str(skill_file.relative_to(REPO_ROOT)))

    assert not non_parallel_violations, (
        f"Found 'setup-matt-pocock-skills' in skills outside parallel lane: {non_parallel_violations}"
    )

    if parallel_lane_has_stale:
        pytest.skip(
            "Skills in parallel lane (to-spec, to-tickets) still contain 'setup-matt-pocock-skills' "
            "before Stage 2 integration merge"
        )


def test_akashic_lint_strict_vault():
    """Verify `akashic lint --strict --vault docs` runs cleanly with 0 issues."""
    proc = subprocess.run(
        ["akashic", "lint", "--strict", "--vault", "docs"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert proc.returncode == 0, (
        f"`akashic lint --strict --vault docs` failed with exit code {proc.returncode}:\n{output}"
    )
    assert re.search(r"issues\s*=\s*0", proc.stdout) or "issues = 0" in proc.stdout, (
        f"Expected 'issues = 0' in output:\n{output}"
    )


def test_ask_pedroca_skill_contract():
    """Verify ask-pedroca/SKILL.md exists and satisfies router contract and terminology."""
    skill_path = REPO_ROOT / "ask-pedroca" / "SKILL.md"
    assert skill_path.is_file(), f"Expected skill file to exist at {skill_path}"

    content = skill_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)

    assert fm.get("name") == "ask-pedroca", f"Expected frontmatter name 'ask-pedroca', got {fm.get('name')}"
    assert fm.get("disable-model-invocation") is True, (
        f"Expected disable-model-invocation to be True, got {fm.get('disable-model-invocation')}"
    )

    missing_spine = [skill for skill in CANONICAL_SPINE_SKILLS if skill not in content]
    assert not missing_spine, f"Missing canonical spine skill references in ask-pedroca: {missing_spine}"

    missing_on_ramps = [skill for skill in ON_RAMP_SKILLS if skill not in content]
    assert not missing_on_ramps, f"Missing on-ramp skill references in ask-pedroca: {missing_on_ramps}"

    missing_upkeep = [skill for skill in UPKEEP_SKILLS if skill not in content]
    assert not missing_upkeep, f"Missing upkeep skill references in ask-pedroca: {missing_upkeep}"

    missing_foundations = [skill for skill in FOUNDATION_SKILLS if skill not in content]
    assert not missing_foundations, f"Missing foundation skill references in ask-pedroca: {missing_foundations}"

    missing_terms = [term for term in CONTEXT_TERMINOLOGY if term not in content]
    assert not missing_terms, f"Missing OKF CONTEXT terminology in ask-pedroca: {missing_terms}"


def test_improve_codebase_architecture_akashic_tools():
    """Verify improve-codebase-architecture/SKILL.md exists and references deterministic Akashic Code Graph tools."""
    skill_path = REPO_ROOT / "improve-codebase-architecture" / "SKILL.md"
    assert skill_path.is_file(), f"Expected skill file to exist at {skill_path}"

    content = skill_path.read_text(encoding="utf-8")
    missing_tools = [tool for tool in DETERMINISTIC_AKASHIC_TOOLS if tool not in content]
    assert not missing_tools, (
        f"Missing deterministic Akashic Code Graph tools in improve-codebase-architecture: {missing_tools}"
    )
