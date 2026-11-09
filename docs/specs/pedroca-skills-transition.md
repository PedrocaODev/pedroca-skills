---
id: spec-pedroca-skills-transition
title: "Transition Repository to Pedroca Skills Framework with Akashic Vault and Herdr Spine"
type: Architecture
status: active
valid_from: 2026-11-09
artifact: spec
scope:
  system: pedroca-skills
  env: production
relations:
  - type: depends_on
    target: ../adr/0001-pedroca-skills-akashic-herdr-architecture.md
tags:
  - spec
  - pedroca-skills
  - akashic
  - herdr-orchestration
---

# Transition Repository to Pedroca Skills Framework with Akashic Vault and Herdr Spine

## Problem Statement

The skills repository was originally populated using `mattpocock/skills` via `npx skills`, creating upstream lockfile coupling and workflow friction:

1. **Upstream Drift & Collisions**: Upstream changes (such as renaming `implement` to `implement-spec` with built-in worktree orchestration, or adding `disable-model-invocation: true`) conflict with `herdr-orchestration` (which owns Tier-1 multi-lane Git worktree orchestration and requires `/implement` for Stage 1 Lane execution) and `GEMINI.md` (which mandates Tier-2 Specialist Subagent delegation).
2. **Boilerplate Tracker Setup & Non-Validated Artifacts**: Multiple upstream skills require `setup-matt-pocock-skills` and prose configuration files under `docs/agents/`, producing unvalidated Markdown files instead of leveraging the Akashic Knowledge Graph and Open Knowledge Format (OKF v0.2) with CI-enforced typed edges.
3. **Redundant & Overlapping Skills**: The repository contains 10 redundant or conflicting skills (`setup-matt-pocock-skills`, `ask-matt`, `writing-beats`, `writing-fragments`, `writing-shape`, `issue-workflow`, `deepwork`, `codemap`, `loop-me`, `loop-engineering`) and an accidental nested duplicate (`implement/implement/`), while architecture discovery skills (`improve-codebase-architecture`) ignore deterministic `akashic graph` analysis.

## Solution

Transition the repository into a standalone, shareable `pedroca-skills` framework governed by `CONTEXT.md` and `ADR-0001`:

1. Sever `mattpocock/skills` from `.skill-lock.json` and prune all 10 retired skills plus the nested `implement/implement/` duplicate.
2. Introduce `setup-pedroca-skills` (configuring `config/akashic.toml` with `vault.path = "docs"`, instructing harnesses on the "Why" of `akashic` MCP + lifecycle hook/fallback enforcement, and providing a deterministic Python OKF frontmatter bootstrapper) and `ask-pedroca` (the workflow router).
3. Standardize the default engineering spine (`grill-with-docs` → `to-spec` → `to-tickets` → `herdr-orchestration` → `implement` → `code-review`) around Akashic OKF v0.2 Vault artifacts (`docs/adr/`, `docs/specs/`, `docs/tickets/<topic>/`) with deterministic Python scripts bridging Ticket `depends_on` edges into `herdr-orchestration` DAG phases.
4. Refactor `/implement` to own single-scope execution (retiring `implement-spec`'s orchestration responsibility) aligned with `GEMINI.md`'s Tier-2 Specialist Subagent topology (`fixer`, `craftsman`, `runner`, `integrator`, `evaluator`, `oracle`) and Herdr Completion Receipts (`WORKFLOW: /implement`).
5. Refactor `improve-codebase-architecture` and remaining workflow skills (`domain-modeling`, `to-spec`, `to-tickets`, `code-review`, `triage`, `wayfinder`, `diagnosing-bugs`) to use the Akashic Vault, Akashic Code Graph, and canonical `CONTEXT.md` terminology.

## User Stories

1. As a framework maintainer, I want all `mattpocock/skills` entries removed from `.skill-lock.json`, so that upstream `npx skills` updates never overwrite or rename my first-party workflow skills.
2. As a framework maintainer, I want `writing-beats`, `writing-fragments`, `writing-shape`, `issue-workflow`, `deepwork`, `codemap`, `loop-me`, `loop-engineering`, `setup-matt-pocock-skills`, `ask-matt`, and the nested `implement/implement` folder deleted, so that the repository contains zero redundant or competing orchestration pipelines.
3. As a developer onboarding a repository with `/setup-pedroca-skills`, I want `config/akashic.toml` initialized with `vault.path = "docs"` and OKF custom field rules (`artifact = "adr" | "spec" | "ticket"`), so that `akashic vault`, `akashic lint --strict`, and `akashic mcp` work out of the box without extra flags.
4. As a developer running `/setup-pedroca-skills` in any coding harness, I want the skill to explain *why* `akashic-mcp` must be enabled and verified at session start (via harness lifecycle hooks where supported, or `AGENTS.md` workspace rules and Git `pre-commit` hooks where not), so that the active harness configures enforcement using its own native capabilities without polluting every other skill with MCP check boilerplate.
5. As a developer using external project management (Linear, Jira, GitHub Issues) or external documentation (Notion, Confluence), I want `/setup-pedroca-skills` to default to the local Akashic Vault (`docs/`) and only configure external adapters when I explicitly opt in.
6. As an agent generating an ADR, Spec, or Ticket, I want a deterministic Python CLI helper that scaffolds OKF v0.2 YAML frontmatter (`id`, `title`, `type`, `status`, `valid_from`, `artifact`, `scope`, `relations`, `tags`) and writes the file into `docs/adr/`, `docs/specs/`, or `docs/tickets/<topic>/`, so that every artifact passes `akashic lint --strict` without hand-rolled YAML errors.
7. As a developer asking how to navigate the framework, I want `/ask-pedroca` to route me across the canonical spine (`grill-with-docs` → `to-spec` → `to-tickets` → `herdr-orchestration` → `implement` → `code-review`) and standalone skills using the `CONTEXT.md` vocabulary.
8. As a developer running `/domain-modeling` (via `/grill-with-docs`), I want resolved terms captured in `CONTEXT.md` and architectural decisions bootstrapped into `docs/adr/NNNN-<slug>.md` as OKF v0.2 `Decision` nodes with `supersedes` edges when applicable.
9. As a developer running `/to-spec`, I want my conversation synthesized into `docs/specs/<topic>.md` with OKF v0.2 `Architecture` (`artifact: spec`) frontmatter and `depends_on` edges pointing to governing ADRs, without being prompted to run `setup-matt-pocock-skills`.
10. As a developer running `/to-tickets`, I want a Spec decomposed into vertical tracer-bullet Tickets under `docs/tickets/<topic>/<NN>-<slug>.md` where each Ticket links to its Spec via `supported_by` and declares blocking Tickets via forward-only OKF `depends_on` edges, so `akashic lint --strict` validates missing targets (`L004`) and dependency cycles (`L005`) at CI level.
11. As an Orchestrator transitioning from `/to-tickets` to `/herdr-orchestration`, I want a deterministic Python compiler that parses `docs/tickets/<topic>/*.md`, resolves `depends_on` topological waves, and emits the `herdr-orchestration` DAG JSON (`/tmp/dag-<session>.json`), so Lane scheduling is 100% deterministic.
12. As an Orchestrator or Lane executing `/implement`, I want `/implement` to be model-invocable (`disable-model-invocation` removed) and scoped strictly to single-ticket/single-spec/single-lane implementation—confirming branch alignment, driving `/tdd` slices through `GEMINI.md` Tier-2 Specialist Subagents (`fixer`/`craftsman`, `runner` `VERDICT: PASSED`, 2-attempt `evaluator` → `oracle` escalation, `integrator`), running `/code-review`, and writing the Completion Receipt (`/tmp/handoff-<session>-<lane>-result.md` with `WORKFLOW: /implement`) when invoked from a Kickoff Brief.
13. As a developer running `/improve-codebase-architecture`, I want Phase 1 exploration to query the Akashic Code Graph (`graph_god_nodes`, `graph_get_community`, `graph_blast_radius`, and `akashic graph surprising`) before organic file browsing, so deepening candidates are grounded in deterministic AST centrality and coupling metrics.
14. As a developer running `/code-review`, `/triage`, `/wayfinder`, or `/diagnosing-bugs`, I want all references to `setup-matt-pocock-skills` and `docs/agents/issue-tracker.md` replaced with `setup-pedroca-skills`, `config/akashic.toml`, and `docs/` Vault conventions.

## Implementation Decisions

1. **Unified Configuration Schema (`config/akashic.toml`)**:
   - Uses `akashic-core`'s native default path `config/akashic.toml` with `[vault] path = "docs"`, `[lint]` (`L001`–`L012`, `strict_forward_only = true`), `[lint.custom_fields.artifact]` (`allowed_values = ["adr", "spec", "ticket"]`), and `[workflow]` (`default_spine`, `[workflow.tracker]`, `[workflow.docs]`).
   - Because `AkashicConfig` uses `#[serde(default)]` without `deny_unknown_fields`, `[workflow]` coexists natively in `config/akashic.toml`.
2. **Harness-Agnostic Enforcement in `setup-pedroca-skills`**:
   - Only `setup-pedroca-skills` carries instructions regarding `akashic` MCP activation and verification.
   - It instructs the agent on the **Why** and required invariants (1. `akashic` MCP server registered for Vault and Code Graph access; 2. session-start verification via native harness hooks when supported, or fallback via workspace rules in `AGENTS.md`/`GEMINI.md` and Git `pre-commit` running `akashic lint --strict`), leaving the **How** to the active coding harness.
3. **Deterministic OKF Frontmatter Bootstrapper**:
   - A standalone Python 3.11+ stdlib script (`tomllib`, `argparse`, `pathlib`, `datetime`) that reads `config/akashic.toml` and generates or updates canonical OKF v0.2 frontmatter for `adr` (`type: Decision`), `spec` (`type: Architecture`, `artifact: spec`), and `ticket` (`type: Architecture`, `artifact: ticket`), enforcing forward-only `relations` (`depends_on`, `supported_by`, `supersedes`).
4. **Deterministic Ticket-to-DAG Compiler**:
   - A Python 3.11+ stdlib script that parses OKF Ticket frontmatter from `docs/tickets/<topic>/*.md`, validates `depends_on` edges (detecting missing targets or cycles via Kahn's topological sort), groups Tickets into concurrent execution phases, and serializes a `herdr-orchestration`-compatible DAG JSON payload (`/tmp/dag-<session>.json`).
5. **Single-Scope `/implement` Contract**:
   - Retires multi-ticket worktree orchestration from `implement-spec` (owned by `herdr-orchestration`).
   - `/implement` executes a single bounded Spec, Ticket, or Kickoff Brief by: (a) verifying worktree/branch base alignment, (b) agreeing seams and executing `/tdd` vertical slices via `GEMINI.md` Tier-2 Specialist Subagents (`fixer`/`craftsman` → `runner` `VERDICT: PASSED` with 2-strike `evaluator` → `oracle` escalation), (c) running `/code-review`, (d) committing via `integrator`, and (e) emitting `/tmp/handoff-<session>-<lane>-result.md` with `VERDICT: PASSED` and `WORKFLOW: /implement` when a Kickoff Brief is provided.
6. **Vocabulary & Cross-Skill Alignment**:
   - All skills use the canonical vocabulary in `CONTEXT.md` (`Orchestrator`, `Lane`, `Specialist Subagent`, `Skill`, `Vault`, `Spec`, `Ticket`, `Kickoff Brief`, `Completion Receipt`, `Handoff`, `Verification Gate`).

## Testing Decisions

Good tests verify observable behavior through public CLI and module seams without coupling to internal helper implementation details:

1. **Seam 1 — OKF Artifact Bootstrapper & `akashic lint --strict`**:
   - Unit/integration tests invoking the OKF bootstrapper CLI/module in a temporary repo fixture to generate ADR, Spec, and Ticket files with `depends_on`, `supported_by`, and `supersedes` edges, followed by running `akashic lint --strict` (verifying exit code `0` on valid graphs and non-zero on `L004` broken targets or `L005` cycles).
2. **Seam 2 — Ticket Graph to Herdr DAG Compiler & `LaneOrchestrator`**:
   - Tests feeding a multi-ticket OKF directory (`01` unblocked, `02` and `03` depending on `01`, `04` depending on `02` and `03`) into the DAG compiler, asserting topological phase grouping (`Phase 1: [01]`, `Phase 2: [02, 03]`, `Phase 3: [04]`) and round-tripping the resulting `LaneConfig` objects through `LaneOrchestrator.build_lane_brief`, `build_lane_prompt`, and `verify_lane_receipt`.
   - Prior art: existing `herdr-orchestration/subagent/` modules (`orchestrator.py`, `resolver.py`, `guard.py`).
3. **Seam 3 — Repository Hygiene & Vault Compliance Suite**:
   - Automated verification test checking `.skill-lock.json` (zero `mattpocock/skills` keys), verifying deletion of all 10 retired skills + nested `implement/implement`, verifying zero stale references to `setup-matt-pocock-skills` or `docs/agents/issue-tracker.md` across `*/SKILL.md`, and running `akashic lint --strict` against this repository's `docs/` Vault.

## Out of Scope

- Modifying third-party Android, Compose, or frontend design skills (`adaptive`, `android-*`, `camerax`, `wear-compose-m3`, `frontend-design`, `design-taste-frontend`, `awesome-design-md`, etc.).
- Modifying the Rust source code of the `akashic` binary in `/home/pedrogoncalves/projects/akashic`.
- Building custom API clients for Linear, Jira, Notion, or Confluence (external integrations remain prompt/MCP-driven when opted into via `setup-pedroca-skills`).

## Further Notes

- The repository's own `docs/` directory (`docs/adr/`, `docs/specs/`, `docs/tickets/`) serves as the first live dogfooding instance of the `pedroca-skills` Akashic Vault.
