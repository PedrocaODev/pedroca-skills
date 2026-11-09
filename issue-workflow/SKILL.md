---
name: issue-workflow
description: Refine an issue with a grilling session, then plan, implement, and verify the change. Use when the user is working on an issue — mentions an issue, pastes an issue URL or number, or wants to refine, scope, implement, or close an issue.
---

# Issue Workflow: grill → plan → implement → verify

Two-phase workflow for taking an issue from raw idea to shipped change. Phase 1 is an interview; Phase 2 is implementation and verification. Never skip Phase 1's confirmation.

## Phase 1 — Refine (grill-me)

1. **Read the issue.** If it is a GitHub URL or `#N`/`owner/repo#N` reference and `gh` is available, run `gh issue view <ref>` and read the body and comments. Otherwise use the conversation context. Never ask the user for anything you can look up yourself.
2. **Run a grilling session** (per the `grilling` skill): interview the user relentlessly in rounds, mapping a design tree. Each round asks the whole current frontier — numbered questions, each with your recommended answer — then waits for the user's answers. Settled decisions push the frontier outward; recompute and ask the next round.
3. **Find facts yourself.** When a frontier question needs a fact from the environment (repo layout, architecture docs, similar past changes, code seams), look it up — never hand the user a question you could answer by reading. Don't block the rest of the frontier on it.
4. **Stop when the frontier is empty** — every branch of the design tree visited, nothing silently assumed. Present the shared understanding and get explicit user confirmation. **Do NOT start Phase 2 until the user confirms.**

   *Trivial, clear issue?* Grilling is for meaningful decisions. If the issue is small and the decision is clear, skip the interview — ceremony scales with risk.

## Phase 2 — Plan, Implement, and Verify

Only after the user confirms the refined understanding (or the issue was trivial):

1. **Plan** — define ordered implementation tasks, test-first slices, review checkpoints, and verification checks.
2. **Review plan** — present the plan; the user reviews before code is written.
3. **Implement** — implement through test-first slices, running review at checkpoints.
4. **Verify** — run planned checks and project verification commands. Ensure every check passes.
5. **Summarize** — summarize completed changes and verification evidence.

## Hard rules

- The grilling phase authorizes nothing beyond shared understanding. Do not start implementation until the user confirms.
- When implementation reveals a design issue, pause and suggest updating the plan, not silently deviating.
- A non-passing check never advances the workflow — fix and re-run.
