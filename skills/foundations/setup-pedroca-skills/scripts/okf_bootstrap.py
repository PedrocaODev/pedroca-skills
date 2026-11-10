#!/usr/bin/env python3
"""Deterministic OKF v0.2 artifact bootstrapper and Akashic integration."""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path
import sys
import tomllib


def _get_vault_path(repo_root: Path) -> Path:
    """Resolve vault path from config/akashic.toml or fallback to docs/."""
    config_file = repo_root / "config" / "akashic.toml"
    if config_file.exists():
        try:
            with open(config_file, "rb") as f:
                data = tomllib.load(f)
                vault_rel = data.get("vault", {}).get("path", "docs")
                return repo_root / vault_rel
        except Exception:
            pass
    return repo_root / "docs"


def _extract_body(content: str) -> str | None:
    """Extract markdown body below the YAML frontmatter delimiter."""
    lines = content.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                return "".join(lines[idx + 1:])
    return None


def _render_frontmatter(
    doc_id: str,
    title: str,
    doc_type: str,
    status: str,
    valid_from: str,
    artifact: str,
    system: str,
    env: str,
    relations: list[dict],
    tags: list[str],
) -> str:
    """Render YAML frontmatter with strict OKF v0.2 structure."""
    lines = [
        "---",
        f"id: {doc_id}",
        f'title: "{title}"',
        f"type: {doc_type}",
        f"status: {status}",
        f"valid_from: {valid_from}",
        f"artifact: {artifact}",
        "scope:",
        f"  system: {system}",
        f"  env: {env}",
    ]

    if not relations:
        lines.append("relations: []")
    else:
        lines.append("relations:")
        for rel in relations:
            first = True
            for k, v in rel.items():
                if first:
                    lines.append(f"  - {k}: {v}")
                    first = False
                else:
                    lines.append(f"    {k}: {v}")

    if not tags:
        lines.append("tags: []")
    else:
        lines.append("tags:")
        for tag in tags:
            lines.append(f"  - {tag}")

    lines.append("---")
    return "\n".join(lines) + "\n"


def init_config(repo_root: Path | str = ".", vault_path: str = "docs") -> Path:
    """Initialize config/akashic.toml and canonical vault directories."""
    root = Path(repo_root).resolve()
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "akashic.toml"

    config_content = f"""# Unified Akashic & Pedroca Skills Configuration

[vault]
path = "{vault_path}"
db_path = ".akashic/vault_index.db"
okf_version = "0.2"

[lint]
enabled_rules = ["L001", "L002", "L003", "L004", "L005", "L006", "L007", "L008", "L009", "L010", "L011", "L012"]
strict_forward_only = true

[lint.custom_fields.artifact]
required = false
type = "string"
allowed_values = ["adr", "spec", "ticket"]
applies_to = ["decision", "architecture", "guide"]

[workflow]
default_spine = ["grill-with-docs", "to-spec", "to-tickets", "herdr-orchestration", "code-review"]

[workflow.tracker]
adapter = "vault"
tickets_dir = "{vault_path}/tickets"

[workflow.docs]
adapter = "vault"
specs_dir = "{vault_path}/specs"
adr_dir = "{vault_path}/adr"
"""

    config_file.write_text(config_content, encoding="utf-8")

    vault_dir = root / vault_path
    (vault_dir / "adr").mkdir(parents=True, exist_ok=True)
    (vault_dir / "specs").mkdir(parents=True, exist_ok=True)
    (vault_dir / "tickets").mkdir(parents=True, exist_ok=True)

    return config_file


def bootstrap_adr(
    repo_root: Path | str = ".",
    slug: str = "init",
    title: str = "Architecture Decision",
    number: int = 1,
    status: str = "active",
    system: str | None = None,
    env: str = "production",
    relations: list[dict] | None = None,
    tags: list[str] | None = None,
    body: str | None = None,
) -> Path:
    """Bootstrap an Architecture Decision Record (ADR) under <vault>/adr/NNNN-<slug>.md."""
    root = Path(repo_root).resolve()
    vault_dir = _get_vault_path(root)
    adr_dir = vault_dir / "adr"
    adr_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{number:04d}-{slug}.md"
    target_path = adr_dir / filename

    existing_body = None
    if target_path.exists():
        existing_body = _extract_body(target_path.read_text(encoding="utf-8"))

    if existing_body is not None and existing_body.strip():
        final_body = existing_body if existing_body.startswith("\n") else f"\n{existing_body}"
    elif body is not None:
        final_body = f"\n\n{body.lstrip()}"
    else:
        final_body = f"\n\n# {title}\n"

    fm_str = _render_frontmatter(
        doc_id=f"adr-{number:04d}-{slug}",
        title=title,
        doc_type="Decision",
        status=status,
        valid_from=datetime.date.today().isoformat(),
        artifact="adr",
        system=system or "pedroca-skills",
        env=env,
        relations=relations or [],
        tags=tags if tags is not None else ["architecture", "adr"],
    )

    target_path.write_text(fm_str + final_body.lstrip("\n"), encoding="utf-8")
    return target_path


def bootstrap_spec(
    repo_root: Path | str = ".",
    topic: str = "feature",
    title: str = "Feature Specification",
    status: str = "active",
    system: str | None = None,
    env: str = "production",
    relations: list[dict] | None = None,
    tags: list[str] | None = None,
    body: str | None = None,
) -> Path:
    """Bootstrap a Specification under <vault>/specs/<topic>.md."""
    root = Path(repo_root).resolve()
    vault_dir = _get_vault_path(root)
    specs_dir = vault_dir / "specs"
    specs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{topic}.md"
    target_path = specs_dir / filename

    existing_body = None
    if target_path.exists():
        existing_body = _extract_body(target_path.read_text(encoding="utf-8"))

    if existing_body is not None and existing_body.strip():
        final_body = existing_body if existing_body.startswith("\n") else f"\n{existing_body}"
    elif body is not None:
        final_body = f"\n\n{body.lstrip()}"
    else:
        final_body = f"\n\n# {title}\n"

    fm_str = _render_frontmatter(
        doc_id=f"spec-{topic}",
        title=title,
        doc_type="Architecture",
        status=status,
        valid_from=datetime.date.today().isoformat(),
        artifact="spec",
        system=system or "pedroca-skills",
        env=env,
        relations=relations or [],
        tags=tags if tags is not None else ["spec", topic],
    )

    target_path.write_text(fm_str + final_body.lstrip("\n"), encoding="utf-8")
    return target_path


def bootstrap_ticket(
    repo_root: Path | str = ".",
    topic: str = "feature",
    slug: str = "task",
    ticket_num: int = 1,
    title: str = "Task Title",
    status: str = "active",
    system: str | None = None,
    env: str = "production",
    relations: list[dict] | None = None,
    tags: list[str] | None = None,
    body: str | None = None,
) -> Path:
    """Bootstrap a Ticket under <vault>/tickets/<topic>/<NN>-<slug>.md."""
    root = Path(repo_root).resolve()
    vault_dir = _get_vault_path(root)
    tickets_dir = vault_dir / "tickets" / topic
    tickets_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{ticket_num:02d}-{slug}.md"
    target_path = tickets_dir / filename

    existing_body = None
    if target_path.exists():
        existing_body = _extract_body(target_path.read_text(encoding="utf-8"))

    if existing_body is not None and existing_body.strip():
        final_body = existing_body if existing_body.startswith("\n") else f"\n{existing_body}"
    elif body is not None:
        final_body = f"\n\n{body.lstrip()}"
    else:
        final_body = f"\n\n# {title}\n"

    fm_str = _render_frontmatter(
        doc_id=f"ticket-{ticket_num:02d}-{slug}",
        title=title,
        doc_type="Architecture",
        status=status,
        valid_from=datetime.date.today().isoformat(),
        artifact="ticket",
        system=system or "pedroca-skills",
        env=env,
        relations=relations or [],
        tags=tags if tags is not None else ["ticket", topic],
    )

    target_path.write_text(fm_str + final_body.lstrip("\n"), encoding="utf-8")
    return target_path


def main() -> None:
    """CLI entrypoint for okf_bootstrap."""
    parser = argparse.ArgumentParser(description="Deterministic OKF v0.2 artifact bootstrapper.")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # init-config
    p_init = subparsers.add_parser("init-config", help="Initialize config/akashic.toml")
    p_init.add_argument("--repo-root", default=".", help="Repository root path")
    p_init.add_argument("--vault-path", default="docs", help="Vault directory relative to repo root")

    # adr
    p_adr = subparsers.add_parser("adr", help="Bootstrap an ADR artifact")
    p_adr.add_argument("--repo-root", default=".", help="Repository root path")
    p_adr.add_argument("--slug", default="init", help="ADR slug")
    p_adr.add_argument("--title", default="Architecture Decision", help="ADR title")
    p_adr.add_argument("--number", type=int, default=1, help="ADR sequence number")
    p_adr.add_argument("--status", default="active", help="ADR status")
    p_adr.add_argument("--system", default=None, help="Scope system identifier")
    p_adr.add_argument("--env", default="production", help="Scope environment identifier")
    p_adr.add_argument("--supersedes", default=None, help="Target path of superseded ADR")
    p_adr.add_argument("--tag", action="append", default=None, help="Tags to assign (repeatable)")

    # spec
    p_spec = subparsers.add_parser("spec", help="Bootstrap a Spec artifact")
    p_spec.add_argument("--repo-root", default=".", help="Repository root path")
    p_spec.add_argument("--topic", default="feature", help="Spec topic identifier")
    p_spec.add_argument("--title", default="Feature Specification", help="Spec title")
    p_spec.add_argument("--status", default="active", help="Spec status")
    p_spec.add_argument("--system", default=None, help="Scope system identifier")
    p_spec.add_argument("--env", default="production", help="Scope environment identifier")
    p_spec.add_argument("--depends-on", action="append", default=None, help="Dependency target path (repeatable)")
    p_spec.add_argument("--tag", action="append", default=None, help="Tags to assign (repeatable)")

    # ticket
    p_ticket = subparsers.add_parser("ticket", help="Bootstrap a Ticket artifact")
    p_ticket.add_argument("--repo-root", default=".", help="Repository root path")
    p_ticket.add_argument("--topic", default="feature", help="Ticket topic identifier")
    p_ticket.add_argument("--slug", default="task", help="Ticket slug")
    p_ticket.add_argument("--ticket-num", type=int, default=1, help="Ticket sequence number")
    p_ticket.add_argument("--title", default="Task Title", help="Ticket title")
    p_ticket.add_argument("--status", default="active", help="Ticket status")
    p_ticket.add_argument("--system", default=None, help="Scope system identifier")
    p_ticket.add_argument("--env", default="production", help="Scope environment identifier")
    p_ticket.add_argument("--supported-by", default=None, help="Spec target path supporting this ticket")
    p_ticket.add_argument("--depends-on", action="append", default=None, help="Dependency target path (repeatable)")
    p_ticket.add_argument("--tag", action="append", default=None, help="Tags to assign (repeatable)")

    args = parser.parse_args()

    if args.subcommand == "init-config":
        path = init_config(repo_root=args.repo_root, vault_path=args.vault_path)
        print(f"Initialized configuration: {path}")
    elif args.subcommand == "adr":
        relations = []
        if args.supersedes:
            relations.append({"type": "supersedes", "target": args.supersedes})
        path = bootstrap_adr(
            repo_root=args.repo_root,
            slug=args.slug,
            title=args.title,
            number=args.number,
            status=args.status,
            system=args.system,
            env=args.env,
            relations=relations,
            tags=args.tag,
        )
        print(f"Bootstrapped ADR: {path}")
    elif args.subcommand == "spec":
        relations = []
        if args.depends_on:
            for dep in args.depends_on:
                relations.append({"type": "depends_on", "target": dep})
        path = bootstrap_spec(
            repo_root=args.repo_root,
            topic=args.topic,
            title=args.title,
            status=args.status,
            system=args.system,
            env=args.env,
            relations=relations,
            tags=args.tag,
        )
        print(f"Bootstrapped Spec: {path}")
    elif args.subcommand == "ticket":
        relations = []
        if args.supported_by:
            relations.append({"type": "supported_by", "target": args.supported_by})
        if args.depends_on:
            for dep in args.depends_on:
                relations.append({"type": "depends_on", "target": dep})
        path = bootstrap_ticket(
            repo_root=args.repo_root,
            topic=args.topic,
            slug=args.slug,
            ticket_num=args.ticket_num,
            title=args.title,
            status=args.status,
            system=args.system,
            env=args.env,
            relations=relations,
            tags=args.tag,
        )
        print(f"Bootstrapped Ticket: {path}")


if __name__ == "__main__":
    main()
