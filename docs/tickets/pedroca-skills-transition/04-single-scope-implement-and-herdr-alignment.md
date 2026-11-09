---
id: ticket-04-single-scope-implement-and-herdr-alignment
title: "04 — Refactor Single-Scope /implement and Align herdr-orchestration"
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
tags:
  - ticket
  - implement
  - herdr-orchestration
---

# 04 — Refactor Single-Scope /implement and Align herdr-orchestration

**What to build:** Rewrite `implement/SKILL.md` so it owns single-scope implementation (retiring `implement-spec`'s multi-worktree orchestration responsibility) while strictly following `GEMINI.md`'s Tier-2 Specialist Subagent delegation rules (`fixer`/`craftsman` → `runner` → `evaluator` → `oracle` → `integrator`) and Herdr Completion Receipt generation (`WORKFLOW: /implement`), and align `herdr-orchestration` with the `CONTEXT.md` glossary (`Lane`, `Specialist Subagent`, `Kickoff Brief`, `Completion Receipt`) and Ticket DAG loading.

**Blocked by:** `01-prune-lockfile-and-retired-skills`

**Allowed paths:** `implement/**`, `herdr-orchestration/**`, `tests/test_herdr_orchestrator.py`

**Status:** ready-for-agent

- [ ] `implement/SKILL.md` has `disable-model-invocation` removed (and `implement/agents/openai.yaml` updated to `allow_implicit_invocation: true`), defines single-scope execution for a Spec, Ticket, or Kickoff Brief, enforces branch base verification, `/tdd` slices via `GEMINI.md` Tier-2 Specialist Subagents, `/code-review`, `integrator` commit delivery, and writes `/tmp/handoff-<session>-<lane>-result.md` with `WORKFLOW: /implement` when invoked in a Lane.
- [ ] `herdr-orchestration/SKILL.md` and `herdr-orchestration/subagent/orchestrator.py` use canonical `CONTEXT.md` terminology (`Lane`, `Specialist Subagent`, `Kickoff Brief`, `Completion Receipt`) and document consuming the compiled Ticket DAG from `/to-tickets`.
- [ ] Seam 2 test suite (`tests/test_herdr_orchestrator.py`) verifies `LaneOrchestrator.is_implementation_lane`, `build_lane_prompt`, `build_lane_brief`, and `verify_lane_receipt` (including rejection when `WORKFLOW: /implement` is missing).
