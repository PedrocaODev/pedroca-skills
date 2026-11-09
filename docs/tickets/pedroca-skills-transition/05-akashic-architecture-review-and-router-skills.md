---
id: ticket-05-akashic-architecture-review-and-router-skills
title: "05 — Create ask-pedroca Router, Integrate Akashic Graph in improve-codebase-architecture, and Align Remaining Skills"
type: Architecture
status: active
valid_from: 2026-11-09
artifact: ticket
scope:
  system: pedroca-skills
  env: production
relations:
  - type: supported_by
    target: ../../specs/pedroca-skills-transition.md
  - type: depends_on
    target: ./01-prune-lockfile-and-retired-skills.md
  - type: depends_on
    target: ./02-setup-pedroca-skills-and-okf-bootstrapper.md
tags:
  - ticket
  - ask-pedroca
  - improve-codebase-architecture
  - akashic
---

# 05 — Create ask-pedroca Router, Integrate Akashic Graph in improve-codebase-architecture, and Align Remaining Skills

**What to build:** Create `ask-pedroca/SKILL.md` as the workflow router for the `pedroca-skills` ecosystem, refactor `improve-codebase-architecture` to use `akashic` Code Graph tools (`graph_god_nodes`, `graph_get_community`, `graph_blast_radius`, `akashic graph surprising`) for deterministic Phase 1 discovery, update `code-review`, `triage`, `wayfinder`, and `diagnosing-bugs` to use `config/akashic.toml` and `docs/`, and ship the Seam 3 repository hygiene verification test suite.

**Blocked by:** `01-prune-lockfile-and-retired-skills`, `02-setup-pedroca-skills-and-okf-bootstrapper`

**Allowed paths:** `ask-pedroca/**`, `improve-codebase-architecture/**`, `code-review/**`, `triage/**`, `wayfinder/**`, `diagnosing-bugs/**`, `tests/test_repo_hygiene.py`

**Status:** ready-for-agent

- [ ] `ask-pedroca/SKILL.md` routes users across the canonical spine (`grill-with-docs` → `to-spec` → `to-tickets` → `herdr-orchestration` → `implement` → `code-review`), on-ramps (`triage`, `diagnosing-bugs`, `wayfinder`), upkeep (`improve-codebase-architecture`), and foundations (`setup-pedroca-skills`, `domain-modeling`, `codebase-design`, `akashic-cli`).
- [ ] `improve-codebase-architecture/SKILL.md` uses `akashic` Code Graph (`graph_god_nodes`, `graph_get_community`, `graph_blast_radius`, `akashic graph surprising`) as its primary deterministic discovery step before organic file exploration.
- [ ] `code-review`, `triage`, `wayfinder`, and `diagnosing-bugs` reference `setup-pedroca-skills`, `config/akashic.toml`, and `docs/` with zero remaining references to `setup-matt-pocock-skills` or `docs/agents/issue-tracker.md`.
- [ ] Seam 3 test suite (`tests/test_repo_hygiene.py`) asserts that `.skill-lock.json` has zero `mattpocock/skills` entries, all retired skills are absent, no `SKILL.md` references `setup-matt-pocock-skills`, and `akashic lint --strict --vault docs` exits `0`.
