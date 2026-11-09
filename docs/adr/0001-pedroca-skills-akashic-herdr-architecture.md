---
id: adr-0001-pedroca-skills-akashic-herdr-architecture
title: "Transition from matt-pocock/skills to Pedroca Skills with Akashic Vault and Herdr Spine"
type: Decision
status: active
valid_from: 2026-11-09
scope:
  system: pedroca-skills
  env: production
tags:
  - architecture
  - akashic
  - herdr
  - workflow
---

# Transition from matt-pocock/skills to Pedroca Skills with Akashic Vault and Herdr Spine

We are severing upstream coupling to `mattpocock/skills` in `.skill-lock.json` and establishing this repository as the canonical source of truth for the `pedroca-skills` framework, governed by two core architectural contracts:

1. **Akashic OKF v0.2 Vault (`docs/`) as Default Artifact Store**: Configured once per repository via `/setup-pedroca-skills` in `config/akashic.toml` (`vault.path = "docs"`), all Specs (`docs/specs/`), Tickets (`docs/tickets/<topic>/`), and ADRs (`docs/adr/`) are written as canonical OKF v0.2 nodes with deterministic YAML frontmatter and forward-only typed edges (`depends_on` for Ticket blocking edges, `supported_by` for Ticket-to-Spec links, `supersedes` for ADR lineage) validated by `akashic lint --strict`. External issue trackers (GitHub Issues, Linear, Jira) and external documentation tools (Notion, Confluence) are opt-in adapters configured only when requested.
2. **Separation of Multi-Lane Orchestration (`herdr-orchestration`) from Single-Scope Execution (`implement`)**: Upstream `implement-spec` conflated multi-ticket worktree orchestration with per-ticket implementation. In `pedroca-skills`, `herdr-orchestration` exclusively owns Tier-1 Git worktree provisioning, DAG phase scheduling, Kickoff Briefs, and Stage 2 integration merges, while `/implement` exclusively owns executing a single bounded Spec, Ticket, or Lane via Tier-2 specialist subagents (`fixer`/`craftsman`, `runner`, `integrator`, `evaluator`, `oracle`), `/tdd`, and `/code-review`.
