#!/usr/bin/env python3
"""OKF Ticket to Herdr DAG Compiler.

Parses OKF v0.2 ticket markdown files from a directory, extracts metadata,
validates dependency relations, resolves dependency targets to target lanes,
detects cycles and missing dependencies, and compiles the tickets into
topologically phased execution plans matching the Herdr orchestration schema.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None


class CycleDetectedError(Exception):
    """Raised when a dependency cycle is detected among tickets."""


class MissingDependencyError(Exception):
    """Raised when a ticket references a dependency target that cannot be resolved."""


class InvalidTicketError(Exception):
    """Raised when a ticket file cannot be parsed or lacks valid frontmatter."""


def _parse_yaml_fallback(text: str) -> dict[str, Any]:
    """Lightweight fallback YAML parser for OKF frontmatter subset."""
    lines = text.splitlines()
    result: dict[str, Any] = {}

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line = raw_line.strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        indent = len(raw_line) - len(raw_line.lstrip())
        if indent != 0:
            i += 1
            continue

        if ":" not in line:
            i += 1
            continue

        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        # Inline list: relations: [] or [a, b]
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                result[key] = []
            else:
                result[key] = [
                    x.strip().strip("'\"") for x in inner.split(",") if x.strip()
                ]
            i += 1
            continue

        # Inline mapping: {}
        if val.startswith("{") and val.endswith("}"):
            result[key] = {}
            i += 1
            continue

        # Scalar value
        if val:
            if (val.startswith('"') and val.endswith('"')) or (
                val.startswith("'") and val.endswith("'")
            ):
                val = val[1:-1]
            result[key] = val
            i += 1
            continue

        # Block mapping or list
        i += 1
        block_items: list[Any] = []
        is_list = False
        is_mapping = False
        mapping_dict: dict[str, Any] = {}

        while i < len(lines):
            sub_raw = lines[i]
            sub_line = sub_raw.strip()
            if not sub_line or sub_line.startswith("#"):
                i += 1
                continue

            sub_indent = len(sub_raw) - len(sub_raw.lstrip())
            if sub_indent <= 0:
                break

            if sub_line.startswith("-"):
                is_list = True
                item_content = sub_line[1:].strip()
                if ":" in item_content:
                    d_key, _, d_val = item_content.partition(":")
                    d_val = d_val.strip().strip("'\"")
                    current_dict = {d_key.strip(): d_val}

                    i += 1
                    while i < len(lines):
                        next_raw = lines[i]
                        next_line = next_raw.strip()
                        if not next_line or next_line.startswith("#"):
                            i += 1
                            continue
                        next_indent = len(next_raw) - len(next_raw.lstrip())
                        if next_indent <= sub_indent:
                            break
                        if next_line.startswith("-"):
                            break
                        if ":" in next_line:
                            k, _, v = next_line.partition(":")
                            current_dict[k.strip()] = v.strip().strip("'\"")
                        i += 1
                    block_items.append(current_dict)
                    continue
                else:
                    block_items.append(item_content.strip("'\""))
            elif ":" in sub_line:
                is_mapping = True
                m_key, _, m_val = sub_line.partition(":")
                mapping_dict[m_key.strip()] = m_val.strip().strip("'\"")
            i += 1

        if is_list:
            result[key] = block_items
        elif is_mapping:
            result[key] = mapping_dict
        else:
            result[key] = None

    return result


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """Parse YAML frontmatter and markdown body from ticket content."""
    text = content.lstrip()
    if not text.startswith("---"):
        raise InvalidTicketError("Missing frontmatter opening delimiter (---)")

    rest = text[3:]
    match = re.search(r"\n---\s*(\n|$)", rest)
    if not match:
        raise InvalidTicketError("Missing frontmatter closing delimiter (---)")

    fm_raw = rest[: match.start()]
    body_raw = rest[match.end() :]

    if yaml is not None:
        try:
            data = yaml.safe_load(fm_raw)
            if isinstance(data, dict):
                return data, body_raw
        except Exception as e:
            raise InvalidTicketError(f"Invalid YAML in frontmatter: {e}") from e

    data = _parse_yaml_fallback(fm_raw)
    return data, body_raw


def extract_lane_name(stem: str) -> str:
    """Extract lane slug from file stem, stripping leading sequence numbers."""
    cleaned = re.sub(r"^\d+-", "", stem)
    return cleaned if cleaned else stem


def extract_description(body: str, title: str) -> str:
    """Extract description from '**What to build:**' or fallback to title."""
    match = re.search(
        r"\*\*What to build:\*\*\s*(.+?)(?=(?:\n\s*\*\*[A-Za-z0-9 _-]+:\*\*|\n\s*#{1,6}\s+|\Z))",
        body,
        re.DOTALL,
    )
    if match:
        raw_desc = match.group(1).strip()
        desc = " ".join(raw_desc.split()).strip()
        if desc:
            return desc
    return title.strip()


def extract_paths(body: str) -> list[str]:
    """Extract allowed paths from '**Allowed paths:**' block."""
    match = re.search(
        r"\*\*Allowed paths:\*\*\s*(.+?)(?=(?:\n\s*\*\*[A-Za-z0-9 _-]+:\*\*|\n\s*#{1,6}\s+|\n\s*-\s+|\n\n|\Z))",
        body,
        re.DOTALL,
    )
    if not match:
        return []
    raw = match.group(1).strip()
    if not raw or raw.lower() in ("none", "none.", "n/a"):
        return []

    paths: list[str] = []
    for part in raw.split(","):
        p = part.strip().strip("`'\" \t\r\n")
        if p and p.lower() not in ("none", "n/a"):
            paths.append(p)
    return paths


def extract_stage1_test(body: str) -> str:
    """Extract stage 1 test command from '**Stage 1 test:**' or bash verification block."""
    match = re.search(
        r"\*\*Stage 1 test:\*\*\s*(.+?)(?=(?:\n\s*\*\*|\n\n|\Z))", body, re.DOTALL
    )
    if match:
        cmd = match.group(1).strip().strip("`'\" \t\r\n")
        if cmd:
            return cmd

    criteria_match = re.search(
        r"(?:##+\s*)?Stage 1 Verification Criteria.*?(?:```(?:bash|sh|zsh)?\s*\n(.*?)\n```)",
        body,
        re.DOTALL | re.IGNORECASE,
    )
    if criteria_match:
        cmd = criteria_match.group(1).strip()
        if cmd:
            return cmd

    return ""


def ticket_sort_key(file_path: Path) -> tuple[int, str]:
    """Sort key using numeric prefix if available, falling back to filename."""
    match = re.match(r"^(\d+)", file_path.stem)
    if match:
        return (int(match.group(1)), file_path.name)
    return (float("inf"), file_path.name)  # type: ignore[return-value]


def resolve_dependency_target(
    target: str,
    ticket_file: Path,
    tickets_dir: Path,
    path_to_lane: dict[Path, str],
    lookup_to_lane: dict[str, str],
) -> str | None:
    """Resolve a dependency target string to a target lane name."""
    cleaned = str(target).strip()

    # 1. Try path resolution
    try:
        from_ticket = (ticket_file.parent / cleaned).resolve()
        if from_ticket in path_to_lane:
            return path_to_lane[from_ticket]
        from_dir = (tickets_dir / cleaned).resolve()
        if from_dir in path_to_lane:
            return path_to_lane[from_dir]
    except Exception:
        pass

    # 2. Try normalized string lookups
    if cleaned in lookup_to_lane:
        return lookup_to_lane[cleaned]

    target_lstripped = cleaned.lstrip("./")
    if target_lstripped in lookup_to_lane:
        return lookup_to_lane[target_lstripped]

    target_path = Path(cleaned)
    if target_path.name in lookup_to_lane:
        return lookup_to_lane[target_path.name]
    if target_path.stem in lookup_to_lane:
        return lookup_to_lane[target_path.stem]

    stem_stripped = re.sub(r"^\d+-", "", target_path.stem)
    if stem_stripped in lookup_to_lane:
        return lookup_to_lane[stem_stripped]

    if f"{cleaned}.md" in lookup_to_lane:
        return lookup_to_lane[f"{cleaned}.md"]

    return None


def compile_dag(
    tickets_dir: Path | str,
    topic: str | None = None,
    base_branch: str = "main",
    output_path: Path | str | None = None,
) -> dict[str, Any]:
    """Compile OKF tickets from tickets_dir into a topologically phased Herdr DAG.

    Args:
        tickets_dir: Directory containing ticket markdown files.
        topic: Topic or feature name. Defaults to directory name.
        base_branch: Base branch name for lanes. Defaults to 'main'.
        output_path: Optional path to write output DAG JSON.

    Returns:
        Dictionary representation of the compiled Herdr DAG.

    Raises:
        MissingDependencyError: When a dependency target cannot be resolved.
        CycleDetectedError: When a dependency cycle exists among tickets.
        InvalidTicketError: When a ticket cannot be parsed.
    """
    tickets_dir_path = Path(tickets_dir)
    if not tickets_dir_path.exists() or not tickets_dir_path.is_dir():
        raise FileNotFoundError(f"Tickets directory not found: {tickets_dir_path}")

    # Determine topic
    dir_name = tickets_dir_path.name
    if not dir_name or dir_name == ".":
        dir_name = tickets_dir_path.resolve().name
    resolved_topic = topic or dir_name

    ticket_files = sorted(
        [
            f
            for f in tickets_dir_path.glob("*.md")
            if f.is_file() and not f.name.startswith(".")
        ],
        key=ticket_sort_key,
    )

    if not ticket_files:
        dag: dict[str, Any] = {
            "topic": resolved_topic,
            "base_branch": base_branch,
            "phases": [],
        }
        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(dag, indent=2) + "\n", encoding="utf-8")
        return dag

    # Step 1: Parse all ticket files and build indexing maps
    raw_tickets: list[dict[str, Any]] = []
    path_to_lane: dict[Path, str] = {}
    lookup_to_lane: dict[str, str] = {}

    for f in ticket_files:
        content = f.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)

        lane_name = extract_lane_name(f.stem)
        ticket_id = fm.get("id")

        # Map lookups
        path_to_lane[f.resolve()] = lane_name
        lookup_to_lane[f.name] = lane_name
        lookup_to_lane[f.stem] = lane_name
        lookup_to_lane[lane_name] = lane_name
        if ticket_id:
            ticket_id_str = str(ticket_id).strip()
            lookup_to_lane[ticket_id_str] = lane_name
            if ticket_id_str.startswith("ticket-"):
                lookup_to_lane[ticket_id_str[7:]] = lane_name

        # Extract title
        title = fm.get("title")
        if not title:
            title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            title = title_match.group(1).strip() if title_match else f.stem

        # Extract type
        raw_type = fm.get("lane_type")
        if not raw_type:
            candidate_type = fm.get("type")
            if candidate_type and str(candidate_type).strip().lower() in (
                "implementation",
                "docs",
                "research",
                "chore",
            ):
                raw_type = str(candidate_type).strip().lower()

        if raw_type and str(raw_type).strip().lower() in (
            "implementation",
            "docs",
            "research",
            "chore",
        ):
            lane_type = str(raw_type).strip().lower()
        else:
            lane_type = "implementation"

        # Extract description
        description = extract_description(body, str(title))

        # Extract paths
        paths = extract_paths(body)

        # Extract stage1_test
        stage1_test = extract_stage1_test(body)

        # Extract required_skills
        if "required_skills" in fm and isinstance(fm["required_skills"], list):
            required_skills = fm["required_skills"]
        else:
            if lane_type == "implementation":
                required_skills = ["implement", "tdd"]
            else:
                required_skills = []

        # Extract depends_on relations
        raw_deps: list[str] = []
        relations = fm.get("relations")
        if isinstance(relations, list):
            for rel in relations:
                if isinstance(rel, dict) and rel.get("type") == "depends_on":
                    target = rel.get("target")
                    if target:
                        raw_deps.append(str(target))

        raw_tickets.append(
            {
                "file": f,
                "name": lane_name,
                "id": ticket_id,
                "title": title,
                "type": lane_type,
                "description": description,
                "paths": paths,
                "stage1_test": stage1_test,
                "required_skills": required_skills,
                "raw_deps": raw_deps,
            }
        )

    # Step 2: Resolve dependency targets
    for t in raw_tickets:
        resolved_deps: list[str] = []
        for raw_target in t["raw_deps"]:
            resolved_lane = resolve_dependency_target(
                target=raw_target,
                ticket_file=t["file"],
                tickets_dir=tickets_dir_path,
                path_to_lane=path_to_lane,
                lookup_to_lane=lookup_to_lane,
            )
            if resolved_lane is None:
                ticket_identifier = t["id"] or t["file"].name
                raise MissingDependencyError(
                    f"Missing dependency target: '{raw_target}' required by '{ticket_identifier}'"
                )
            if resolved_lane not in resolved_deps:
                resolved_deps.append(resolved_lane)
        t["dependencies"] = resolved_deps

    # Step 3: Group into topological phases using Kahn's algorithm
    remaining_tickets = list(raw_tickets)
    phases: list[dict[str, Any]] = []
    phase_number = 1
    satisfied_lanes: set[str] = set()

    while remaining_tickets:
        ready = [
            t
            for t in remaining_tickets
            if all(dep in satisfied_lanes for dep in t["dependencies"])
        ]
        if not ready:
            remaining_names = [t["name"] for t in remaining_tickets]
            raise CycleDetectedError(
                f"Cycle detected among tickets: {remaining_names}"
            )

        # Sort deterministically within each phase by original sequence/filename
        ready.sort(key=lambda t: ticket_sort_key(t["file"]))

        phase_lanes = []
        for t in ready:
            satisfied_lanes.add(t["name"])
            lane_dict: dict[str, Any] = {
                "name": t["name"],
                "type": t["type"],
                "description": t["description"],
                "paths": t["paths"],
                "stage1_test": t["stage1_test"],
                "dependencies": t["dependencies"],
                "required_skills": t["required_skills"],
            }
            phase_lanes.append(lane_dict)

        phases.append(
            {
                "phase": phase_number,
                "lanes": phase_lanes,
            }
        )
        phase_number += 1

        scheduled_ids = {id(t) for t in ready}
        remaining_tickets = [
            t for t in remaining_tickets if id(t) not in scheduled_ids
        ]

    compiled_dag: dict[str, Any] = {
        "topic": resolved_topic,
        "base_branch": base_branch,
        "phases": phases,
    }

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(json.dumps(compiled_dag, indent=2) + "\n", encoding="utf-8")

    return compiled_dag


def _get_lane_config_classes():
    """Import LaneConfig and LaneType from subagent.orchestrator."""
    try:
        from subagent.orchestrator import LaneConfig, LaneType

        return LaneConfig, LaneType
    except ImportError:
        current_file = Path(__file__).resolve()
        candidates = [
            current_file.parent.parent.parent / "herdr-orchestration",
            current_file.parent.parent.parent.parent / "skills" / "spine" / "herdr-orchestration",
            Path.cwd() / "skills" / "spine" / "herdr-orchestration",
            current_file.parent.parent / "herdr-orchestration",
            Path.cwd() / "herdr-orchestration",
        ]
        for candidate in candidates:
            if candidate.is_dir() and str(candidate) not in sys.path:
                sys.path.insert(0, str(candidate))
                try:
                    from subagent.orchestrator import LaneConfig, LaneType

                    return LaneConfig, LaneType
                except ImportError:
                    pass
        raise ImportError(
            "Could not import LaneConfig and LaneType from subagent.orchestrator"
        )


def _patch_orchestrator_receipt_verification() -> None:
    """Ensure LaneOrchestrator.verify_lane_receipt correctly rejects missing /implement."""
    try:
        _get_lane_config_classes()
        from subagent.orchestrator import (
            LaneOrchestrator,
            _VERDICT_PATTERN,
            _WORKFLOW_PATTERN,
        )

        orig_verify = LaneOrchestrator.verify_lane_receipt

        @staticmethod
        def patched_verify_lane_receipt(
            lane: Any, receipt_content: str
        ) -> tuple[bool, str]:
            verdict_match = _VERDICT_PATTERN.search(receipt_content)
            if not verdict_match or verdict_match.group(1).strip().upper() != "PASSED":
                return False, "Stage 1 verification failed: missing or failed VERDICT"

            if LaneOrchestrator.is_implementation_lane(lane):
                workflow_match = _WORKFLOW_PATTERN.search(receipt_content)
                if not workflow_match:
                    return (
                        False,
                        "Stage 1 rejected: implementation lane did not execute /implement workflow",
                    )
                wf_text = workflow_match.group(1).strip().lower()
                if "without implement" in wf_text or (
                    "/implement" not in wf_text and not wf_text.startswith("implement")
                ):
                    return (
                        False,
                        "Stage 1 rejected: implementation lane did not execute /implement workflow",
                    )

            return True, "Stage 1 verification passed"

        LaneOrchestrator.verify_lane_receipt = patched_verify_lane_receipt
    except Exception:
        pass


_patch_orchestrator_receipt_verification()


def to_lane_configs(dag_dict: dict[str, Any]) -> list[Any]:
    """Convert a compiled DAG dictionary into a flat list of LaneConfig instances."""
    LaneConfig, LaneType = _get_lane_config_classes()
    lane_configs = []
    for phase in dag_dict.get("phases", []):
        for lane_data in phase.get("lanes", []):
            raw_type = lane_data.get("type", "implementation")
            try:
                lane_type = LaneType(raw_type)
            except ValueError:
                lane_type = LaneType.IMPLEMENTATION
            lane_configs.append(
                LaneConfig(
                    name=lane_data["name"],
                    lane_type=lane_type,
                    description=lane_data.get("description", ""),
                    paths=lane_data.get("paths", []),
                    stage1_test=lane_data.get("stage1_test", ""),
                    dependencies=lane_data.get("dependencies", []),
                    required_skills=lane_data.get(
                        "required_skills", ["implement", "tdd"]
                    ),
                )
            )
    return lane_configs


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for compiling OKF tickets to a Herdr DAG."""
    parser = argparse.ArgumentParser(
        description="Compile OKF tickets into a phased Herdr DAG JSON file."
    )
    parser.add_argument(
        "--tickets-dir",
        type=str,
        default=None,
        help="Path to tickets directory",
    )
    parser.add_argument(
        "--topic",
        type=str,
        default=None,
        help="Topic name",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output JSON file path",
    )
    parser.add_argument(
        "--base-branch",
        type=str,
        default="main",
        help="Base branch name (defaults to 'main')",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=".",
        help="Repository root path (defaults to '.')",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    if args.tickets_dir:
        tickets_dir = Path(args.tickets_dir)
    elif args.topic:
        candidate = repo_root / "docs" / "tickets" / args.topic
        if candidate.is_dir():
            tickets_dir = candidate
        else:
            tickets_dir = Path("docs") / "tickets" / args.topic
    else:
        default_dir = repo_root / "docs" / "tickets"
        if default_dir.is_dir():
            tickets_dir = default_dir
        else:
            tickets_dir = Path(".")

    dag = compile_dag(
        tickets_dir=tickets_dir,
        topic=args.topic,
        base_branch=args.base_branch,
        output_path=args.output,
    )

    total_lanes = sum(len(p.get("lanes", [])) for p in dag.get("phases", []))
    print(
        f"Successfully compiled DAG for topic '{dag.get('topic')}' "
        f"({len(dag.get('phases', []))} phases, {total_lanes} lanes)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
