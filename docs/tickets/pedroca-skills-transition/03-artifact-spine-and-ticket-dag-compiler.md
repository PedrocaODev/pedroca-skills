---
id: ticket-03-artifact-spine-and-ticket-dag-compiler
title: "03 — Refactor domain-modeling, to-spec, to-tickets and Add Deterministic Ticket-to-DAG Compiler"
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
    target: ./02-setup-pedroca-skills-and-okf-bootstrapper.md
tags:
  - ticket
  - to-spec
  - to-tickets
  - domain-modeling
---

# 03 — Refactor domain-modeling, to-spec, to-tickets and Add Deterministic Ticket-to-DAG Compiler

**What to build:** Update `domain-modeling`, `grill-with-docs`, `to-spec`, and `to-tickets` to write OKF v0.2 artifacts into `docs/adr/`, `docs/specs/`, and `docs/tickets/<topic>/` using `okf_bootstrap.py` and `config/akashic.toml` (replacing all `setup-matt-pocock-skills` references), and build `to-tickets/scripts/compile_dag.py` to deterministically compile OKF Ticket `depends_on` edges into a phased `herdr-orchestration` DAG JSON file.

**Blocked by:** `02-setup-pedroca-skills-and-okf-bootstrapper`

**Allowed paths:** `domain-modeling/**`, `grill-with-docs/**`, `to-spec/**`, `to-tickets/**`, `tests/test_compile_dag.py`

**Status:** ready-for-agent

- [ ] `domain-modeling`, `grill-with-docs`, `to-spec`, and `to-tickets` reference `setup-pedroca-skills`, `config/akashic.toml`, `okf_bootstrap.py`, and `CONTEXT.md` terminology, with zero references to `setup-matt-pocock-skills` or `.scratch/` as the default tracker.
- [ ] `to-tickets/scripts/compile_dag.py` reads `docs/tickets/<topic>/*.md`, parses OKF `depends_on` edges, detects cycles or missing blockers, groups Tickets into topological execution phases, and outputs a valid `herdr-orchestration` DAG JSON file.
- [ ] Seam 2 test suite (`tests/test_compile_dag.py`) verifies topological wave compilation (including tested compatibility against ` docs/tickets/pedroca-skills-transition/*.md`) and cycle/missing-target error handling.
