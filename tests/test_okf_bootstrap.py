"""Tests for OKF v0.2 artifact bootstrapper and Akashic integration.

Seam 1: Verifies that setup-pedroca-skills/scripts/okf_bootstrap.py can:
1. Initialize config/akashic.toml with vault.path = 'docs' and OKF v0.2 rules.
2. Bootstrap ADRs, Specs, and Tickets with valid OKF v0.2 YAML frontmatter.
3. Validate generated artifacts against `akashic lint --strict` (L001-L012).
4. Reject broken targets (L004) and directed cycles (L005).
5. Run successfully via CLI invocation.
"""

import os
import subprocess
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "foundations" / "setup-pedroca-skills" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Target module under test
from okf_bootstrap import (
    init_config,
    bootstrap_adr,
    bootstrap_spec,
    bootstrap_ticket,
)

CLI_SCRIPT = SCRIPTS_DIR / "okf_bootstrap.py"

REQUIRED_OKF_FIELDS = [
    "id",
    "title",
    "type",
    "status",
    "valid_from",
    "artifact",
    "scope",
    "relations",
    "tags",
]


def parse_frontmatter(content: str) -> dict:
    """Extract and parse YAML frontmatter from markdown content."""
    try:
        import yaml

        lines = content.splitlines()
        if lines and lines[0].strip() == "---":
            end_idx = -1
            for idx, line in enumerate(lines[1:], start=1):
                if line.strip() == "---":
                    end_idx = idx
                    break
            if end_idx != -1:
                return yaml.safe_load("\n".join(lines[1:end_idx])) or {}
    except ImportError:
        pass

    # Lightweight fallback YAML frontmatter parser (stdlib only)
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("Missing leading '---' in frontmatter")
    fm_lines = []
    found_end = False
    for line in lines[1:]:
        if line.strip() == "---":
            found_end = True
            break
        fm_lines.append(line)
    if not found_end:
        raise ValueError("Missing closing '---' in frontmatter")

    data = {}
    current_key = None

    for line in fm_lines:
        raw_line = line
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())

        if indent == 0 and ":" in stripped:
            key, val = stripped.split(":", 1)
            key = key.strip()
            val = val.strip()
            if val == "":
                current_key = key
            elif val.startswith("[") and val.endswith("]"):
                inner = val[1:-1].strip()
                data[key] = [x.strip() for x in inner.split(",") if x.strip()] if inner else []
                current_key = None
            else:
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                data[key] = val
                current_key = None
        elif current_key and indent > 0:
            if stripped.startswith("- "):
                if current_key not in data or not isinstance(data[current_key], list):
                    data[current_key] = []
                item_content = stripped[2:].strip()
                if ":" in item_content:
                    sub_k, sub_v = item_content.split(":", 1)
                    sub_v = sub_v.strip()
                    if (sub_v.startswith('"') and sub_v.endswith('"')) or (sub_v.startswith("'") and sub_v.endswith("'")):
                        sub_v = sub_v[1:-1]
                    item_dict = {sub_k.strip(): sub_v}
                    data[current_key].append(item_dict)
                else:
                    if (item_content.startswith('"') and item_content.endswith('"')) or (item_content.startswith("'") and item_content.endswith("'")):
                        item_content = item_content[1:-1]
                    data[current_key].append(item_content)
            elif ":" in stripped:
                sub_k, sub_v = stripped.split(":", 1)
                sub_k = sub_k.strip()
                sub_v = sub_v.strip()
                if (sub_v.startswith('"') and sub_v.endswith('"')) or (sub_v.startswith("'") and sub_v.endswith("'")):
                    sub_v = sub_v[1:-1]

                if current_key in data and isinstance(data[current_key], list) and data[current_key] and isinstance(data[current_key][-1], dict):
                    data[current_key][-1][sub_k] = sub_v
                else:
                    if current_key not in data or not isinstance(data[current_key], dict):
                        data[current_key] = {}
                    data[current_key][sub_k] = sub_v

    return data


def test_init_config(tmp_path: Path):
    """Test generating config/akashic.toml in a repository root."""
    config_file = init_config(tmp_path, vault_path="docs")
    assert config_file.exists()
    assert config_file == tmp_path / "config" / "akashic.toml"

    content = config_file.read_text(encoding="utf-8")
    assert '[vault]' in content
    assert 'path = "docs"' in content
    assert 'okf_version = "0.2"' in content
    assert '[lint]' in content
    assert 'strict_forward_only = true' in content
    assert '[lint.custom_fields.artifact]' in content
    assert '[workflow]' in content


def test_bootstrap_adr(tmp_path: Path):
    """Test generating an ADR under docs/adr/NNNN-<slug>.md."""
    init_config(tmp_path)
    adr_file = bootstrap_adr(
        repo_root=tmp_path,
        slug="init",
        title="Initialize Architecture",
        number=1,
    )
    assert adr_file.exists()
    assert adr_file == tmp_path / "docs" / "adr" / "0001-init.md"

    fm = parse_frontmatter(adr_file.read_text(encoding="utf-8"))
    assert fm["id"] == "adr-0001-init"
    assert fm["title"] == "Initialize Architecture"
    assert fm["type"] == "Decision"
    assert fm["status"] == "active"
    assert fm["artifact"] == "adr"
    assert "valid_from" in fm
    assert fm["scope"]["system"]
    assert fm["scope"]["env"]
    assert isinstance(fm["relations"], list)
    assert "adr" in fm["tags"]


def test_bootstrap_spec(tmp_path: Path):
    """Test generating a Spec under docs/specs/<topic>.md."""
    init_config(tmp_path)
    spec_file = bootstrap_spec(
        repo_root=tmp_path,
        topic="user-auth",
        title="User Authentication Specification",
        relations=[{"type": "depends_on", "target": "../adr/0001-init.md"}],
    )
    assert spec_file.exists()
    assert spec_file == tmp_path / "docs" / "specs" / "user-auth.md"

    fm = parse_frontmatter(spec_file.read_text(encoding="utf-8"))
    assert fm["id"] == "spec-user-auth"
    assert fm["title"] == "User Authentication Specification"
    assert fm["type"] == "Architecture"
    assert fm["status"] == "active"
    assert fm["artifact"] == "spec"
    assert "valid_from" in fm
    assert fm["scope"]["system"]
    assert fm["scope"]["env"]
    assert len(fm["relations"]) == 1
    assert fm["relations"][0]["type"] == "depends_on"
    assert fm["relations"][0]["target"] == "../adr/0001-init.md"
    assert "spec" in fm["tags"]


def test_bootstrap_ticket(tmp_path: Path):
    """Test generating a Ticket under docs/tickets/<topic>/<NN>-<slug>.md."""
    init_config(tmp_path)
    ticket_file = bootstrap_ticket(
        repo_root=tmp_path,
        topic="user-auth",
        slug="jwt-tokens",
        ticket_num=1,
        title="Implement JWT Token Generation",
        relations=[{"type": "supported_by", "target": "../../specs/user-auth.md"}],
    )
    assert ticket_file.exists()
    assert ticket_file == tmp_path / "docs" / "tickets" / "user-auth" / "01-jwt-tokens.md"

    fm = parse_frontmatter(ticket_file.read_text(encoding="utf-8"))
    assert fm["id"] == "ticket-01-jwt-tokens"
    assert fm["title"] == "Implement JWT Token Generation"
    assert fm["type"] == "Architecture"
    assert fm["status"] == "active"
    assert fm["artifact"] == "ticket"
    assert "valid_from" in fm
    assert fm["scope"]["system"]
    assert fm["scope"]["env"]
    assert len(fm["relations"]) == 1
    assert fm["relations"][0]["type"] == "supported_by"
    assert fm["relations"][0]["target"] == "../../specs/user-auth.md"
    assert "ticket" in fm["tags"]


def test_okf_v02_required_frontmatter_fields(tmp_path: Path):
    """Test that all bootstrapped artifacts contain the required OKF v0.2 frontmatter fields."""
    init_config(tmp_path)
    adr = bootstrap_adr(tmp_path, slug="db-choice", title="Database Choice", number=1)
    spec = bootstrap_spec(tmp_path, topic="data-layer", title="Data Layer Spec")
    ticket = bootstrap_ticket(tmp_path, topic="data-layer", slug="schema", ticket_num=1, title="Define Schema")

    for path in [adr, spec, ticket]:
        content = path.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        for field in REQUIRED_OKF_FIELDS:
            assert field in fm, f"Missing required OKF v0.2 field '{field}' in {path.name}"
            assert fm[field] is not None, f"Field '{field}' in {path.name} cannot be None"

        assert isinstance(fm["scope"], dict), f"'scope' must be a dict in {path.name}"
        assert "system" in fm["scope"], f"'scope.system' missing in {path.name}"
        assert "env" in fm["scope"], f"'scope.env' missing in {path.name}"
        assert isinstance(fm["relations"], list), f"'relations' must be a list in {path.name}"
        assert isinstance(fm["tags"], list), f"'tags' must be a list in {path.name}"


def test_integration_akashic_lint_strict_success(tmp_path: Path):
    """Integration test verifying that bootstrapped ADR, Spec, and Tickets pass `akashic lint --strict`."""
    init_config(tmp_path)

    # 1. ADR: 0001-init.md
    bootstrap_adr(
        repo_root=tmp_path,
        slug="init",
        title="Initialize Architecture",
        number=1,
    )

    # 2. Spec: my-feature.md with depends_on: ../adr/0001-init.md
    bootstrap_spec(
        repo_root=tmp_path,
        topic="my-feature",
        title="My Feature Spec",
        relations=[{"type": "depends_on", "target": "../adr/0001-init.md"}],
    )

    # 3. Ticket 1: 01-base.md with supported_by: ../../specs/my-feature.md
    bootstrap_ticket(
        repo_root=tmp_path,
        topic="my-feature",
        slug="base",
        ticket_num=1,
        title="Base Feature Setup",
        relations=[{"type": "supported_by", "target": "../../specs/my-feature.md"}],
    )

    # 4. Ticket 2: 02-ext.md with supported_by and depends_on: ./01-base.md
    bootstrap_ticket(
        repo_root=tmp_path,
        topic="my-feature",
        slug="ext",
        ticket_num=2,
        title="Extension Feature",
        relations=[
            {"type": "supported_by", "target": "../../specs/my-feature.md"},
            {"type": "depends_on", "target": "./01-base.md"},
        ],
    )

    # Run akashic lint --strict in tmp_path
    proc = subprocess.run(
        ["akashic", "lint", "--strict"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    assert proc.returncode == 0, f"`akashic lint --strict` failed with exit {proc.returncode}:\n{output}"
    assert "valid = true" in proc.stdout, f"Expected valid = true in output:\n{output}"
    assert "issues = 0" in proc.stdout, f"Expected issues = 0 in output:\n{output}"


def test_negative_akashic_lint_broken_target_l004(tmp_path: Path):
    """Negative test verifying that broken relation targets trigger L004 failure in `akashic lint --strict`."""
    init_config(tmp_path)

    # Create Spec targeting non-existent ADR
    bootstrap_spec(
        repo_root=tmp_path,
        topic="broken-spec",
        title="Broken Spec",
        relations=[{"type": "depends_on", "target": "../adr/0001-nonexistent.md"}],
    )

    proc = subprocess.run(
        ["akashic", "lint", "--strict"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{proc.stdout}\n{proc.stderr}"
    assert "valid = false" in output or proc.returncode != 0, f"Expected invalid lint report or non-zero exit code, got rc={proc.returncode}:\n{output}"
    assert "L004" in output, f"Expected L004 error code in output:\n{output}"


def test_negative_akashic_lint_cycle_l005(tmp_path: Path):
    """Negative test verifying that dependency cycles trigger L005 failure in `akashic lint --strict`."""
    init_config(tmp_path)

    # Ticket A depends on Ticket B, Ticket B depends on Ticket A
    bootstrap_ticket(
        repo_root=tmp_path,
        topic="cycle-topic",
        slug="a",
        ticket_num=1,
        title="Ticket A",
        relations=[{"type": "depends_on", "target": "./02-b.md"}],
    )
    bootstrap_ticket(
        repo_root=tmp_path,
        topic="cycle-topic",
        slug="b",
        ticket_num=2,
        title="Ticket B",
        relations=[{"type": "depends_on", "target": "./01-a.md"}],
    )

    proc = subprocess.run(
        ["akashic", "lint", "--strict"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output = f"{proc.stdout}\n{proc.stderr}"
    assert "valid = false" in output or proc.returncode != 0, f"Expected invalid lint report or non-zero exit code, got rc={proc.returncode}:\n{output}"
    assert "L005" in output, f"Expected L005 error code in output:\n{output}"


def test_cli_invocation(tmp_path: Path):
    """Test invoking setup-pedroca-skills/scripts/okf_bootstrap.py via subprocess CLI."""
    assert CLI_SCRIPT.exists(), f"CLI script {CLI_SCRIPT} should exist"

    # 1. init-config
    res_init = subprocess.run(
        [sys.executable, str(CLI_SCRIPT), "init-config", "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert res_init.returncode == 0, f"CLI init-config failed:\n{res_init.stderr}"
    assert (tmp_path / "config" / "akashic.toml").exists()

    # 2. bootstrap adr
    res_adr = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "adr",
            "--repo-root",
            str(tmp_path),
            "--slug",
            "init",
            "--title",
            "Initial Architecture",
            "--number",
            "1",
        ],
        capture_output=True,
        text=True,
    )
    assert res_adr.returncode == 0, f"CLI adr failed:\n{res_adr.stderr}"
    assert (tmp_path / "docs" / "adr" / "0001-init.md").exists()

    # 3. bootstrap spec
    res_spec = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "spec",
            "--repo-root",
            str(tmp_path),
            "--topic",
            "my-feature",
            "--title",
            "My Feature Spec",
            "--depends-on",
            "../adr/0001-init.md",
        ],
        capture_output=True,
        text=True,
    )
    assert res_spec.returncode == 0, f"CLI spec failed:\n{res_spec.stderr}"
    assert (tmp_path / "docs" / "specs" / "my-feature.md").exists()

    # 4. bootstrap ticket
    res_ticket = subprocess.run(
        [
            sys.executable,
            str(CLI_SCRIPT),
            "ticket",
            "--repo-root",
            str(tmp_path),
            "--topic",
            "my-feature",
            "--slug",
            "base",
            "--ticket-num",
            "1",
            "--title",
            "Base Ticket",
            "--supported-by",
            "../../specs/my-feature.md",
        ],
        capture_output=True,
        text=True,
    )
    assert res_ticket.returncode == 0, f"CLI ticket failed:\n{res_ticket.stderr}"
    assert (tmp_path / "docs" / "tickets" / "my-feature" / "01-base.md").exists()

    # Validate with akashic lint --strict
    proc = subprocess.run(
        ["akashic", "lint", "--strict"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"akashic lint failed on CLI-generated files:\n{proc.stdout}\n{proc.stderr}"
