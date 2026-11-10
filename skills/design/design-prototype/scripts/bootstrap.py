#!/usr/bin/env python3
"""
bootstrap.py - Initialize a living visual contract prototype in a target project.

Copies prototype_template.html and serve_prototype.py into docs/design/.
"""

import argparse
import os
import shutil
import stat
import sys
from pathlib import Path


def find_template_dir() -> Path:
    """Resolve the directory containing templates."""
    # Check sibling templates folder relative to scripts/
    script_dir = Path(__file__).resolve().parent
    candidates = [
        script_dir.parent / "templates",
        script_dir / "templates",
        Path.home() / ".agents" / "skills" / "design-prototype" / "templates",
        Path.home() / "projects" / "design-prototype" / "templates",
    ]
    for c in candidates:
        if (c / "prototype_template.html").is_file() and (c / "serve_prototype.py").is_file():
            return c.resolve()

    raise FileNotFoundError("Could not locate design-prototype template directory.")


def bootstrap(target_project_dir: Path, force: bool = False) -> int:
    template_dir = find_template_dir()
    src_html = template_dir / "prototype_template.html"
    src_server = template_dir / "serve_prototype.py"

    design_dir = target_project_dir / "docs" / "design"
    design_dir.mkdir(parents=True, exist_ok=True)

    dest_html = design_dir / "prototype.html"
    dest_server = design_dir / "serve_prototype.py"

    # Copy prototype.html
    if dest_html.exists() and not force:
        print(f"[SKIP] {dest_html} already exists (use --force to overwrite)")
    else:
        shutil.copy2(src_html, dest_html)
        print(f"[CREATE] Initialized prototype at {dest_html}")

    # Copy serve_prototype.py
    if dest_server.exists() and not force:
        print(f"[SKIP] {dest_server} already exists (use --force to overwrite)")
    else:
        shutil.copy2(src_server, dest_server)
        # Make executable
        st = os.stat(dest_server)
        os.chmod(dest_server, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[CREATE] Initialized runner at {dest_server}")

    print("\nVisual Contract Prototype successfully bootstrapped!")
    print("\nNext steps:")
    print("  1. Verify the prototype contract:")
    print(f"     python3 {dest_server} --check")
    print("  2. Start the interactive state simulator:")
    print(f"     python3 {dest_server} --open\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap a living design prototype in docs/design/."
    )
    parser.add_argument(
        "--target-dir",
        default=".",
        help="Target project directory (default: current directory)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing prototype files in target",
    )

    args = parser.parse_args()
    target_dir = Path(args.target_dir).resolve()

    return bootstrap(target_dir, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
