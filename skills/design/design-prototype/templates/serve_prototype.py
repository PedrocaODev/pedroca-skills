#!/usr/bin/env python3
"""
serve_prototype.py - Zero-dependency HTTP server and contract verification suite
for living HTML/CSS/JS design prototypes.
"""

import argparse
import http.server
import os
import re
import shutil
import socket
import socketserver
import sys
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Required section markers according to the design-prototype contract
REQUIRED_SECTION_MARKERS = [
    "/* === SECTION: TOKENS: PRIMITIVES === */",
    "/* === SECTION: TOKENS: SEMANTIC === */",
    "/* === SECTION: BASE & RESET === */",
    "/* === SECTION: HARNESS: STATE SIMULATOR === */",
    "/* === SECTION: COMPONENTS: FOUNDATIONAL === */",
    "/* === SECTION: COMPONENTS: DOMAIN === */",
    "/* === SECTION: SCREENS === */",
    "/* === SECTION: JAVASCRIPT: LOGIC & HARNESS === */",
]

REQUIRED_STATES = ["populated", "loading", "empty", "error"]
REQUIRED_THEMES = ["warm_dark", "light", "dark", "sepia"]


def find_prototype_file(target: Path) -> Path:
    """Locate prototype.html (or prototype_template.html) in the specified or standard search paths."""
    if target.is_file():
        return target.resolve()
    script_dir = Path(__file__).resolve().parent
    candidates = [
        target / "prototype.html",
        target / "prototype_template.html",
        target / "docs" / "design" / "prototype.html",
        script_dir / "prototype.html",
        script_dir / "prototype_template.html",
        script_dir.parent / "templates" / "prototype_template.html",
        Path.cwd() / "docs" / "design" / "prototype.html",
        Path.cwd() / "prototype.html",
    ]
    for c in candidates:
        if c.is_file():
            return c.resolve()
    return (target / "prototype.html").resolve()


def verify_prototype_contract(prototype_path: Path) -> Tuple[bool, List[str]]:
    """
    Automated contract verification suite for design prototypes:
    1. Checks file existence and non-zero size.
    2. Validates rigid ASCII section markers.
    3. Validates 2-tier semantic token pairs across declared themes.
    4. Validates presence and wiring of declarative data-state harness.
    """
    errors: List[str] = []
    log: List[str] = []

    # 1. File existence
    if not prototype_path.exists():
        errors.append(f"File not found: {prototype_path}")
        return False, errors

    try:
        content = prototype_path.read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"Failed to read {prototype_path}: {e}")
        return False, errors

    if len(content.strip()) == 0:
        errors.append(f"Prototype file is empty: {prototype_path}")
        return False, errors

    log.append(f"[PASS] File check: {prototype_path} exists ({len(content)} bytes)")

    # 2. Section markers
    missing_sections = []
    for marker in REQUIRED_SECTION_MARKERS:
        if marker not in content:
            missing_sections.append(marker)

    if missing_sections:
        errors.append(f"Missing {len(missing_sections)} required section marker(s):\n  " + "\n  ".join(missing_sections))
    else:
        log.append(f"[PASS] Section delimitation: All {len(REQUIRED_SECTION_MARKERS)} rigid markers verified")

    # 3. 2-Tier Token Hierarchy & Semantic token parity across themes
    # Find all theme blocks: [data-theme="..."] or :root
    theme_pattern = re.compile(r'(\:root|\[data-theme=["\']?([a-zA-Z0-9_\-]+)["\']?\])\s*\{([^}]+)\}', re.MULTILINE)
    matches = theme_pattern.findall(content)

    theme_tokens: Dict[str, Set[str]] = {}
    for selector, theme_name, block in matches:
        key = theme_name.lower().replace("-", "_") if theme_name else ":root"
        # Extract CSS variables (--foo: ...)
        var_names = set(re.findall(r'(--[a-zA-Z0-9_\-]+)\s*:', block))
        if key not in theme_tokens:
            theme_tokens[key] = set()
        theme_tokens[key].update(var_names)

    # Validate declared themes
    detected_themes = [t for t in theme_tokens.keys() if t != ":root"]
    log.append(f"[INFO] Detected theme blocks: {', '.join(detected_themes) if detected_themes else 'none'}")

    # Check that required themes exist
    missing_themes = [req for req in REQUIRED_THEMES if req not in detected_themes]
    if missing_themes:
        errors.append(f"Missing declared themes in CSS [data-theme=...]: {', '.join(missing_themes)}")
    else:
        log.append(f"[PASS] Themes verified: {', '.join(REQUIRED_THEMES)}")

    # Check semantic token consistency across themes
    # Required core semantic tokens
    core_semantic_tokens = ["--bg", "--surface", "--on-surface", "--primary"]
    for theme in REQUIRED_THEMES:
        tokens_in_theme = theme_tokens.get(theme, set())
        # check against root + theme
        available_tokens = tokens_in_theme | theme_tokens.get(":root", set())
        missing_semantic = [tok for tok in core_semantic_tokens if tok not in available_tokens]
        if missing_semantic:
            errors.append(f"Theme '{theme}' missing semantic tokens: {', '.join(missing_semantic)}")

    if not any(f"Theme '{theme}' missing semantic tokens" in e for e in errors):
        log.append(f"[PASS] Semantic token pairs verified across themes ({', '.join(core_semantic_tokens)})")

    # 4. Declarative State Harness validation
    # Look for [data-state="..."] in CSS or HTML, and data-set-state or controls
    missing_states = []
    for state in REQUIRED_STATES:
        state_css_pattern = re.compile(rf'\[data-state=["\']?{state}["\']?\]')
        state_html_pattern = re.compile(rf'data-state=["\']{state}["\']|data-set-state=["\']{state}["\']')
        if not (state_css_pattern.search(content) or state_html_pattern.search(content)):
            missing_states.append(state)

    if missing_states:
        errors.append(f"Missing data-state wiring for states: {', '.join(missing_states)}")
    else:
        log.append(f"[PASS] Declarative State Harness: All states verified ({', '.join(REQUIRED_STATES)})")

    # Summary
    if errors:
        for err in errors:
            print(f"[FAIL] {err}", file=sys.stderr)
        return False, errors

    for msg in log:
        print(msg)
    print("\n[VERDICT: PASSED] Prototype visual contract is 100% compliant.")
    return True, []


class NoCachePrototypeHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler that enforces no-cache headers and rewrites / to prototype.html."""

    prototype_filename: str = "prototype.html"

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self) -> None:
        # Rewrite root path to prototype.html if requesting /
        if self.path in ("/", ""):
            if os.path.exists(os.path.join(self.directory, self.prototype_filename)):
                self.path = f"/{self.prototype_filename}"
        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        # Clean logging
        sys.stdout.write(f"[{self.log_date_time_string()}] {self.address_string()} - {format % args}\n")
        sys.stdout.flush()


def find_available_port(host: str, start_port: int, max_attempts: int = 50) -> int:
    """Probe for an available port starting at start_port up to max_attempts."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    raise OSError(f"Could not find an open port in range {start_port}..{start_port + max_attempts - 1}")


def get_candidates_dirs(base_dir: Path) -> List[Path]:
    """Return prioritized candidate search directories."""
    dirs = [
        base_dir / "candidates",
        Path.cwd() / "docs" / "design" / "candidates",
        Path.cwd() / "candidates",
    ]
    seen: Set[Path] = set()
    result: List[Path] = []
    for d in dirs:
        res = d.resolve()
        if res not in seen:
            seen.add(res)
            result.append(res)
    return result


def list_candidates(base_dir: Path) -> int:
    """List available candidate prototypes in design directory."""
    candidate_dirs = get_candidates_dirs(base_dir)
    found_files: List[Tuple[str, Path]] = []

    for c_dir in candidate_dirs:
        if c_dir.is_dir():
            for f in sorted(c_dir.glob("*.html")):
                cand_name = f.stem
                if cand_name.startswith("prototype-"):
                    cand_name = cand_name.replace("prototype-", "")
                elif cand_name.startswith("prototype_"):
                    cand_name = cand_name.replace("prototype_", "")
                found_files.append((cand_name, f))

    print("==================================================")
    print("  DESIGN PROTOTYPE CANDIDATES")
    print("==================================================")
    if found_files:
        print(f"Discovered {len(found_files)} candidate prototype file(s):")
        for name, path in found_files:
            print(f"  • {name:14} -> {path}")
    else:
        print("No standalone candidate files found in docs/design/candidates/.")
        print("Multi-skill candidates available in unified prototype harness:")
        print("  • awesome       Candidate A: awesome-design-md (Industry Benchmark)")
        print("  • frontend      Candidate B: frontend-design (Bespoke Studio)")
        print("  • taste         Candidate C: design-taste-frontend (Anti-Slop Modern)")

    print("--------------------------------------------------")
    print("To promote a candidate to the canonical MVP Contract:")
    print("  python3 docs/design/serve_prototype.py --promote <candidate_name>")
    print("==================================================")
    return 0


def promote_candidate(base_dir: Path, candidate_name: str) -> int:
    """
    Promote candidate prototype to canonical docs/design/prototype.html.
    Copies docs/design/candidates/prototype-<name>.html to docs/design/prototype.html.
    """
    clean_name = candidate_name.strip().lower()
    cand_key = clean_name
    if cand_key.startswith("prototype-"):
        cand_key = cand_key.replace("prototype-", "")
    elif cand_key.startswith("prototype_"):
        cand_key = cand_key.replace("prototype_", "")

    dest_path = (Path.cwd() / "docs" / "design" / "prototype.html").resolve()
    if not (Path.cwd() / "docs" / "design").is_dir() and (base_dir / "prototype.html").parent.is_dir():
        dest_path = (base_dir / "prototype.html").resolve()

    candidate_dirs = get_candidates_dirs(base_dir)
    target_candidate_file: Optional[Path] = None

    for c_dir in candidate_dirs:
        possible = [
            c_dir / f"prototype-{cand_key}.html",
            c_dir / f"prototype_{cand_key}.html",
            c_dir / f"{cand_key}.html",
        ]
        for p in possible:
            if p.is_file():
                target_candidate_file = p.resolve()
                break
        if target_candidate_file:
            break

    if target_candidate_file:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target_candidate_file, dest_path)
        print("==================================================")
        print("  MVP CANDIDATE PROMOTION SUCCESSFUL")
        print("==================================================")
        print(f"  Source Candidate : {target_candidate_file}")
        print(f"  Canonical MVP    : {dest_path}")
        print(f"  Candidate Name   : {cand_key}")
        print("--------------------------------------------------")
        print(f"[PROMOTED] Candidate '{cand_key}' successfully promoted to Canonical MVP Contract at:")
        print(f"  -> {dest_path}")
        print("==================================================")
        return 0

    prototype_file = find_prototype_file(base_dir)
    if prototype_file.is_file():
        content = prototype_file.read_text(encoding="utf-8")
        if f'data-candidate-btn="{cand_key}"' in content or f'data-candidate="{cand_key}"' in content or f'"{cand_key}":' in content:
            updated = re.sub(r'data-candidate="[^"]*"', f'data-candidate="{cand_key}"', content)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(updated, encoding="utf-8")
            print("==================================================")
            print("  MVP CANDIDATE PROMOTION SUCCESSFUL")
            print("==================================================")
            print(f"  Source Embedded  : {prototype_file}")
            print(f"  Canonical MVP    : {dest_path}")
            print(f"  Candidate Name   : {cand_key}")
            print("--------------------------------------------------")
            print(f"[PROMOTED] Embedded candidate '{cand_key}' successfully promoted to Canonical MVP Contract at:")
            print(f"  -> {dest_path}")
            print("==================================================")
            return 0

    print(f"Error: Candidate prototype not found for '{candidate_name}'.", file=sys.stderr)
    print(f"Looked for: prototype-{cand_key}.html in:", file=sys.stderr)
    for c_dir in candidate_dirs:
        print(f"  - {c_dir}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Zero-dependency HTTP server and contract checker for design prototypes."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port to serve on (default: 8765)")
    parser.add_argument("--strict-port", action="store_true", help="Fail immediately if the requested port is busy")
    parser.add_argument("--dir", dest="directory", default=None, help="Directory containing prototype.html")
    parser.add_argument("--open", dest="open_browser", action="store_true", help="Open prototype in default browser")
    parser.add_argument("--check", action="store_true", help="Run contract verification suite and exit")
    parser.add_argument("--candidates", action="store_true", help="List available candidate prototypes in design directory")
    parser.add_argument("--promote", type=str, metavar="CANDIDATE", help="Promote candidate to canonical prototype.html")

    args = parser.parse_args()

    # Determine base directory
    script_dir = Path(__file__).resolve().parent
    if args.directory:
        base_dir = Path(args.directory).resolve()
    elif (script_dir / "prototype.html").is_file():
        base_dir = script_dir
    elif (Path.cwd() / "docs" / "design" / "prototype.html").is_file():
        base_dir = (Path.cwd() / "docs" / "design").resolve()
    elif (Path.cwd() / "prototype.html").is_file():
        base_dir = Path.cwd().resolve()
    else:
        base_dir = script_dir

    # Handle --candidates
    if args.candidates:
        return list_candidates(base_dir)

    # Handle --promote
    if args.promote:
        return promote_candidate(base_dir, args.promote)

    prototype_file = find_prototype_file(base_dir)

    # Handle --check
    if args.check:
        print(f"=== Verifying Visual Contract for: {prototype_file} ===\n")
        passed, _ = verify_prototype_contract(prototype_file)
        return 0 if passed else 1

    # Ensure prototype directory exists for serving
    serve_dir = prototype_file.parent if prototype_file.is_file() else base_dir
    if not serve_dir.exists():
        print(f"Error: Directory does not exist: {serve_dir}", file=sys.stderr)
        return 1

    # Select port
    if args.strict_port:
        port = args.port
    else:
        try:
            port = find_available_port(args.host, args.port)
        except OSError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    class CustomHandler(NoCachePrototypeHandler):
        def __init__(self, *handler_args, **handler_kwargs):
            super().__init__(*handler_args, directory=str(serve_dir), **handler_kwargs)

    try:
        with socketserver.TCPServer((args.host, port), CustomHandler) as httpd:
            url = f"http://{args.host}:{port}/"
            if prototype_file.is_file():
                url += prototype_file.name

            print("==================================================")
            print("  DESIGN PROTOTYPE SERVER (Zero-Dependency Runner)")
            print("==================================================")
            print(f"  Serving Directory : {serve_dir}")
            print(f"  Target File       : {prototype_file.name}")
            print(f"  URL               : {url}")
            print(f"  Cache-Control     : no-store, no-cache, must-revalidate")
            print("--------------------------------------------------")
            print("  Press Ctrl+C to stop the server.")
            print("==================================================")

            if args.open_browser:
                webbrowser.open(url)

            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nPrototype server stopped.")
        return 0
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
