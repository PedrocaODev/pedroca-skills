---
id: ticket-02-setup-pedroca-skills-and-okf-bootstrapper
title: "02 — Build setup-pedroca-skills and Deterministic OKF Artifact Bootstrapper"
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
tags:
  - ticket
  - setup-pedroca-skills
  - akashic
---

# 02 — Build setup-pedroca-skills and Deterministic OKF Artifact Bootstrapper

**What to build:** Create the `/setup-pedroca-skills` skill and its deterministic Python OKF v0.2 artifact bootstrapper (`setup-pedroca-skills/scripts/okf_bootstrap.py`) so repositories can initialize `config/akashic.toml` (`vault.path = "docs"`), configure harness-native `akashic-mcp` enforcement (instructing on the *Why* and required invariants rather than hardcoded harness mechanics), and deterministically generate OKF-compliant ADR, Spec, and Ticket Markdown files that pass `akashic lint --strict`.

**Blocked by:** None — can start immediately.

**Allowed paths:** `setup-pedroca-skills/**`, `tests/test_okf_bootstrap.py`

**Status:** ready-for-agent

- [ ] `setup-pedroca-skills/SKILL.md` guides onboarding a repo with `config/akashic.toml` (`vault.path = "docs"`), `AGENTS.md` pointer rules, opt-in prompts for external trackers (GitHub Issues, Linear, Jira) and external docs (Notion, Confluence), and harness-agnostic instructions explaining *why* `akashic-mcp` must be enabled and verified at session start (via harness hooks or workspace rule + Git `pre-commit` fallback).
- [ ] `setup-pedroca-skills/scripts/okf_bootstrap.py` deterministically scaffolds OKF v0.2 frontmatter (`id`, `title`, `type`, `status`, `valid_from`, `artifact`, `scope`, forward-only `relations`, `tags`) for `adr`, `spec`, and `ticket` artifacts in `docs/{adr,specs,tickets}/`.
- [ ] Seam 1 test suite (`tests/test_okf_bootstrap.py`) verifies that bootstrapped ADR, Spec, and Ticket nodes with `depends_on`, `supported_by`, and `supersedes` edges pass `akashic lint --strict` (`exit 0`) and that broken targets (`L004`) or cycles (`L005`) are rejected.
