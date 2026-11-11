---
name: retro
description: Conduct a retrospective on a coding session, suggesting environment, guardrail, and steering improvements.
disable-model-invocation: true
---

# Retro

`retro` is a user-invoked retrospective for a single coding session or specific lane. It analyzes agent session logs and workspace history, identifies friction points, and recommends high-leverage improvements to the agent's environment to make future runs faster, safer, and more reliable.

Unlike `reflect` (which synthesizes patterns across many sessions), `retro` conducts a deep post-mortem on one target session.

## Steps

### 1. Style Reference

Follow the guidelines in `writing-for-agents` for concise phrasing, progressive disclosure, leading words, and completion criteria.

### 2. Inspect Primary Sources

Locate and read the primary logs for the target session. If the user does not specify a session ID, lane, or commit range, evaluate the current active session.

- **Harness Session Transcripts & Logs**:
  - Conversation transcripts, execution traces, or session logs in the active coding harness environment (e.g. `<appDataDir>/brain/<conversation-id>/.system_generated/logs/transcript.jsonl`, `~/.agents/history/`, or harness session directories).
- **Herdr Worktrees / Lanes**:
  - Lane kickoff briefs at `/tmp/handoff-<session>-<lane>.md`.
  - Lane completion receipts at `/tmp/handoff-<session>-<lane>-result.md`.
  - Multiplexer pane scrollback or lane git commits (`git log -p`).
- **Git Workspace Evidence**:
  - Commits and diffs via `git log -n 5 --stat` and `git diff`.
  - Test run execution outputs, compiler errors, and linter receipts.

### 3. Analyze Improvement Candidates

Evaluate session friction across these six categories:

1. **Navigation & Pointers**:
   - How easily did the agent locate relevant files?
   - Were there hidden cross-module dependencies or unexpected coupling?
   - Would intentional navigation pointers in `AGENTS.md` (or workspace instructions) eliminate exploratory searches?
   - Would deterministic Akashic Code Graph queries (`akashic graph query "<question>"`, `akashic graph path "<A>" "<B>"`) reduce directory traversal round-trips?

2. **Automated Checks & Guardrails**:
   - Did the agent make errors that an automated check could prevent?
   - Inspect existing repository check commands first (`pytest`, `npm test`, `cargo check`, `gradlew check`, `akashic lint --strict`). Check if an existing check was unwired or ignored.
   - An un-linted repository is a finding. Recommend deterministic pre-commit hooks (`setup-pre-commit`) or CI gates instead of relying on agent memory or prompt reminders.

3. **Coding Standards vs Mechanical Linters**:
   - Did the reviewer agent (`code-review`) miss a violation, or does a new rule need enforcement?
   - Classify the issue strictly:
     - **Mechanical violations** (fixed syntactic patterns, banned APIs, import shapes, file organization rules) must become deterministic checks: linter rules, AST checks, or pre-commit hooks.
     - **Judgement calls** (cross-file architectural consistency, public API design, semantic clarity) belong in `CODING_STANDARDS.md` or architectural decision records in `docs/adr/`.
   - Never write a prose rule for a mechanical violation that a linter can enforce.

4. **Steering Hygiene (`AGENTS.md` / Workspace Rules)**:
   - Are instructions in `AGENTS.md` or workspace rules bloated, redundant, or acting as no-ops?
   - Does an instruction fail to alter agent behavior compared to the default?
   - Can oversized instructions be moved down the information hierarchy into specialized skills or automated scripts?

5. **Topology & Tool Economy**:
   - Did the primary orchestrator session maintain role separation (coordinating, researching, and planning without editing application code directly)?
   - Were code changes correctly delegated to `fixer` or `designer`?
   - Were subagent invocations explicitly tiered according to generic capability tiers:
     - Routine Execution tier (`runner`/`librarian`)
     - Balanced Workhorse tier (`fixer`/`integrator`)
     - Frontier Reasoning tier (`evaluator`/`craftsman`/`oracle`)
     rather than wasting tokens or running inappropriate models?
   - Were tool calls efficient, or did the agent make repetitive, token-heavy calls?

6. **Information Access & Architectural Seams**:
   - Was critical runtime information unavailable (swallowed stderr/stdout, hidden crashes, missing dev server logs)?
   - Did missing test seams prevent fast, deterministic reproduction of defects?
   - If shallow modules, coupling leaks, or missing test boundaries blocked progress, recommend `improve-codebase-architecture`.

### 4. Present Findings

Output candidate findings ranked by severity and return on investment (ROI). For each finding, provide:

1. **Category**: One of the six evaluation categories.
2. **Observation**: Concrete evidence from the session logs (tool call, error output, or wasted turn).
3. **Root Cause**: Why the friction occurred (missing pointer, absent linter, bloated steering, or missing seam).
4. **Actionable Fix**: Concrete diff, configuration change, or shell command to implement the fix immediately.

---

## Reference

### Implementation vs Review Context Pressure

Engineering tasks split into two distinct phases with asymmetric context constraints:

- **Implementation Phase (`fixer`, `craftsman`)**:
  - Highest context pressure.
  - The agent must explore files, read error traces, write code, and debug test failures.
  - Keep implementation context clean. Do not load comprehensive coding standards into the implementation prompt.
- **Review Phase (`code-review`)**:
  - Lowest context pressure.
  - The reviewer receives a bounded diff and does not explore or debug.
  - The review agent enforces repository standards and architectural consistency.

Delegate rule enforcement to review gates or mechanical linters, not implementation prompts.

### File Roles and Information Hierarchy

Place guidance in the correct tier of the information hierarchy:

| File / Location | Primary Role | Scope & Guidance |
|---|---|---|
| `AGENTS.md` / Workspace Rules | Context steering & navigation | Loaded on every turn. Use sparingly. Limit to navigation pointers, essential tool routing, and non-negotiable project boundaries. |
| `CODING_STANDARDS.md` | Reviewer standards | Read during review (`code-review`), not implementation. Keep focused on human judgement calls. If it exceeds 1,000 lines, split into topic docs with pointers. |
| `docs/adr/`, `docs/specs/` | Architectural decisions & contracts | Canonical records of design choices and domain boundaries. Point to from `AGENTS.md` rather than inlining. |
| `skills/` | On-demand procedural workflows | Disclosed workflows loaded only when invoked or when trigger keywords match. Pushes operational load out of global steering. |
