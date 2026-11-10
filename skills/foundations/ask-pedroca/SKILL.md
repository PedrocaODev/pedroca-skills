---
name: ask-pedroca
description: Ask which skill or flow fits your situation. A workflow router over the pedroca-skills ecosystem.
disable-model-invocation: true
---

# Ask Pedroca

You do not need to memorize every skill — ask which workflow fits your current situation.

The `pedroca-skills` framework structures agentic engineering across a two-tier execution topology:
- **Tier 1 (Cross-Session / Multiplexer)**: Independent, concurrent workspaces or long-running workstreams coordinated via Herdr worktrees (`herdr-orchestration`) across isolated Git worktrees (`Lane`).
- **Tier 2 (In-Session Specialist Subagents)**: Bounded task delegation within a single workspace session using a `Specialist Subagent` (`fixer`, `craftsman`, `runner`, `integrator`, `librarian`, `evaluator`, `oracle`, `council`).

The core development lifecycle flows through the **Canonical Spine**, supported by entry **On-ramps**, ongoing **Upkeep**, architectural **Foundations**, and focused **Standalone / Utility** workflows.

---

## The Canonical Spine: Idea → Ship

The standard pipeline for designing, ticketing, implementing, and verifying features:

```text
grill-with-docs ──► to-spec ──► to-tickets ──► herdr-orchestration ──► implement ──► code-review
```

1. **`grill-with-docs`** — Requirements discovery and interview.
   Sharpen raw ideas into clear requirements through Socratic questioning within a repository working directory. Persists domain concepts into `CONTEXT.md` and records architectural decisions in `docs/adr/`.
2. **`to-spec`** — Specification synthesis.
   Synthesize the grilled conversation and domain models into a canonical `Spec` document (`docs/specs/<topic>.md`) registered in the repository's Akashic `Vault` using Open Knowledge Format (OKF v0.2).
3. **`to-tickets`** — Work breakdown and DAG compilation.
   Decompose the `Spec` into vertical tracer-bullet `Ticket` artifacts in `docs/tickets/<topic>/`. Each `Ticket` defines explicit acceptance criteria and `depends_on` blocking edges. Compiles the dependency graph into an execution DAG for orchestrating parallel work.
4. **`herdr-orchestration`** — Multi-lane coordination across isolated worktrees.
   The `Orchestrator` provisions an isolated Git worktree and Herdr workspace (`Lane`) for each independent workstream. For each `Lane`, the `Orchestrator` generates a `Kickoff Brief` (`/tmp/handoff-<session>-<lane>.md`) specifying scope, allowed paths, upstream dependencies, and Stage 1 verification commands.
5. **`implement`** — Workstream execution within a Lane.
   Executes a `Ticket` within its designated `Lane` using test-driven development (TDD). Employs in-session `Specialist Subagent` delegation (`fixer` for code modifications, `runner` for Stage 1 verification). Once Stage 1 verification passes (`VERDICT: PASSED`), the `Lane` emits a structured `Completion Receipt` (`/tmp/handoff-<session>-<lane>-result.md`).
6. **`code-review`** — Three-axis verification gate.
   Audits the diff against a fixed point across three independent axes: **Standards** (repository conventions and Fowler smell baseline), **Spec** (implementation fidelity against the originating `Spec` and `Ticket`), and **Complexity** (algorithmic time/space Big-O analysis). Ensures changes are verified before integration.

---

## On-ramps

Starting workflows that process raw inputs and merge onto the Canonical Spine:

- **Bugs, feature requests, or external contributions arriving** → **`triage`**.
  Moves raw issues and external PRs through a state machine of triage roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). Consults `config/akashic.toml` and `docs/tickets/` to produce durable, agent-ready briefs that feed into `implement`.
- **Hard bugs, regressions, or intermittent flakes** → **`diagnosing-bugs`**.
  A disciplined root-cause investigation flow. Refuses to theorize without first building a tight, deterministic, red-capable feedback loop that reproduces the exact symptom. Minimizes the reproduction scenario, instruments falsifiable predictions, and locks in regression tests respecting `docs/adr/` and `config/akashic.toml`. If missing architectural test seams prevent testing, it hands off to `improve-codebase-architecture`.
- **Large, foggy, or ambiguous initiatives** → **`wayfinder`**.
  Designed for greenfield efforts or massive epics too large for a single session. Charts a shared map of decision tickets in `docs/tickets/` within the `Vault`. Works decisions one at a time — producing decisions rather than code deliverables — pushing back the fog of war until the route is clear, then hands off to `to-spec`.

---

## Upkeep

Ongoing architectural hygiene and code health:

- **`improve-codebase-architecture`** — Codebase deepening and friction reduction.
  Scans the repository for shallow modules, coupling leaks, and architectural friction to improve testability and AI-navigability. Uses deterministic Akashic Code Graph tools (`graph_god_nodes`, `graph_get_community`, `graph_blast_radius`, `akashic graph surprising`) as its primary discovery step before organic file exploration. Generates an interactive visual HTML report with before/after diagrams and walks through candidate refactors via structured grilling.

---

## Foundations

Core configuration, domain modeling, and knowledge graph infrastructure:

- **`setup-pedroca-skills`** — Repository bootstrapping.
  Configures `config/akashic.toml`, bootstraps the OKF v0.2 `Vault` (`docs/adr/`, `docs/specs/`, `docs/tickets/`), installs required agent configs, and sets up project-level tracker bindings.
- **`domain-modeling`** — Ubiquitous language definition.
  Extracts and sharpens project domain terminology into `CONTEXT.md` and records architectural decision records in `docs/adr/`.
- **`codebase-design`** — Architectural vocabulary and principles.
  Provides a shared vocabulary (**module**, **interface**, **depth**, **seam**, **adapter**, **leverage**, **locality**) and design principles (the deletion test, interface as test surface, dual adapter rule) for creating deep modules with small interfaces.
- **`akashic-cli`** — Vault and code graph management.
  CLI and MCP toolkit for querying multi-language code graphs, validating `Vault` OKF v0.2 frontmatter via `akashic lint`, running root cause analysis (RCA), and managing embeddings.

---

## Standalone / Utility

Specialized tools and procedures that operate outside the main linear flow:

- **`grill-me`** — Stateless Socratic interview for refining plans, designs, or prose without modifying local files or creating `CONTEXT.md`.
- **`grilling`** — The underlying interview primitive driving `grill-with-docs`, `triage`, `wayfinder`, and `improve-codebase-architecture`.
- **`prototype`** — Fast, throwaway implementation to resolve state model or UI questions. Prototypes are retained on `prototype/<name>` branches as primary source artifacts.
- **`research`** — Background research agent that queries authoritative external docs and APIs, capturing findings in a cited Markdown report.
- **`resolving-merge-conflicts`** — Intent-based Git merge and rebase conflict resolution, reconciling conflicting hunks against their original commits.
- **`handoff`** — Creates a portable session-transition document (`/tmp/handoff-*.md`) for transferring state across sessions, harnesses, or directories.
- **`pr`** — Environment-agnostic review submission and evidence formatting.
  Prepares coordinated delivery packages decoupling code review hosting (Gerrit changes, GitHub PRs, GitLab MRs, local Vault) from project management and verification tracking (Jira, Linear, GitHub Issues, Vault). Formats commit messages with Change-Ids, visual diff sketches, risk assessments, and test execution evidence packages.
- **`wizard`** — Interactive terminal assistant for tasks that require human authorization or manual execution (provisioning cloud secrets, third-party auth, one-off migrations).

---

## Context Hygiene & Phase Boundaries

### The Smart Zone
Large language models reason with peak sharpness within a context budget known as the **smart zone** (~150k tokens on modern frontier models). As context approaches or exceeds this window, reasoning fidelity declines and edge-case hallucination increases.

Keep linear discovery phases (`grill-with-docs` → `to-spec` → `to-tickets`) in a single unbroken context when possible, but observe the smart zone limit. Once tickets are generated, clear the session or delegate execution to isolated Lanes.

### Phase Boundary Operations
When reaching the end of a phase or approaching the ~150k token limit, transition using one of five deliberate operations:

1. **Continue**: Maintain the current session window. Use when the smart zone has ample headroom and the subsequent step directly builds on conversational context.
2. **Clear** (`/clear`): Completely reset the session context window. Use when moving from planning to implementation (`to-tickets` → `implement`); the tickets in the `Vault` are self-contained and prior conversational tokens are disposable.
3. **Handoff** (`/handoff`): Write a structured transition document (`/tmp/handoff-*.md`). Use when moving work to a different repository worktree, passing context across CLI harnesses, or when the `Orchestrator` produces a `Kickoff Brief` for a `Lane`.
4. **Compact** (`/compact`): Condense conversational state to reclaim token headroom when a long-running design session exceeds ~150k tokens but cannot yet be fully written into a `Spec` or `Ticket`.
5. **Specialist Subagent** (`invoke_subagent`): Delegate a self-contained, bounded task to an in-session `Specialist Subagent` (`fixer`, `craftsman`, `runner`, `integrator`, `librarian`, `evaluator`, `oracle`, `council`). This preserves the `Orchestrator` context while running specialized implementation, verification, or research tasks.

---

## Domain Glossary Reference (`CONTEXT.md`)

When authoring documents or communicating within this ecosystem, strictly follow canonical terms:
- **`Orchestrator`**: The coordinating agent session managing plans, interviews, and DAG execution without directly editing application code.
- **`Lane`**: A Tier-1 isolated Git worktree and Herdr workspace (`lane/<topic>-<lane>`) executing a bounded workstream.
- **`Specialist Subagent`**: A Tier-2 role-bounded in-session agent (`fixer`, `craftsman`, `runner`, `integrator`, `librarian`, `evaluator`, `oracle`, `council`).
- **`Vault`**: The repository's documentation store governed by Akashic, holding OKF v0.2 Markdown nodes with typed frontmatter and relational edges.
- **`Spec`**: A canonical design artifact (`docs/specs/<topic>.md`) defining requirements, user stories, and technical decisions.
- **`Ticket`**: A tracer-bullet work item (`docs/tickets/<topic>/`) with explicit dependencies and acceptance criteria.
- **`Kickoff Brief`**: The input contract (`/tmp/handoff-<session>-<lane>.md`) defining a `Lane`'s scope, allowed files, and verification criteria.
- **`Completion Receipt`**: The output contract (`/tmp/handoff-<session>-<lane>-result.md`) certifying completion, commit hashes, modified files, and Stage 1 test verdicts.
