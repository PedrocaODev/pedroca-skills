---
name: to-tickets
description: Break a plan, spec, or the current conversation into a set of tracer-bullet tickets, each declaring its blocking edges, published to the configured tracker — edges as text in one file per ticket locally, or native blocking links on a real tracker.
disable-model-invocation: true
---

# To Tickets

Break a plan, Spec, or conversation into a set of **Tickets** — tracer-bullet vertical slices, each declaring the Tickets that **block** it.

Ensure vault configuration is set up according to `config/akashic.toml` — run `/setup-pedroca-skills` if not configured. Tickets are stored in the Vault under `docs/tickets/<topic>/<NN>-<slug>.md`.

## Process

### 1. Gather context

Work from whatever is already in the conversation context. If the Orchestrator or user passes a reference (a Spec path, an issue number or URL) as an argument, fetch it and read its full body and comments.

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code. Ticket titles and descriptions should use the project's domain glossary vocabulary from `CONTEXT.md`, and respect ADRs in the area you're touching.

Look for opportunities to prefactor the code to make the implementation easier. "Make the change easy, then make the easy change."

### 3. Draft vertical slices

Break the work into **tracer bullet** Tickets.

<vertical-slice-rules>

- Each slice cuts a narrow but COMPLETE path through every layer (schema, API, UI, tests) — vertical, NOT a horizontal slice of one layer
- A completed slice is demoable or verifiable on its own
- Each slice is sized to fit in a single fresh context window
- Any prefactoring should be done first

</vertical-slice-rules>

Give each Ticket its **blocking edges** — the other Tickets that must complete before it can start. A Ticket with no blockers can start immediately.

**Wide refactors are the exception to vertical slicing.** A **wide refactor** is one mechanical change — rename a column, retype a shared symbol — whose **blast radius** fans across the whole codebase, so a single edit breaks thousands of call sites at once and no vertical slice can land green. Don't force it into a tracer bullet; sequence it as **expand–contract**. First expand: add the new form beside the old so nothing breaks. Then migrate the call sites over in batches sized by blast radius (per package, per directory), each batch its own Ticket blocked by the expand, keeping CI green batch to batch because the old form still exists. Finally contract: delete the old form once no caller remains, in a Ticket blocked by every migrate batch. When even the batches can't stay green alone, keep the sequence but let them share an integration branch that all block a final integrate-and-verify Ticket — green is promised only there.

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each Ticket, show:

- **Title**: short descriptive name
- **Blocked by**: which other Tickets (if any) must complete first
- **What it delivers**: the end-to-end behaviour this Ticket makes work

Ask the Orchestrator or user:

- Does the granularity feel right? (too coarse / too fine)
- Are the blocking edges correct — does each Ticket only depend on Tickets that genuinely gate it?
- Should any Tickets be merged or split further?

Iterate until the breakdown is approved.

### 5. Publish the tickets to the configured tracker

Publish the approved tickets. **How** depends on the tracker configuration (see `config/akashic.toml` via `/setup-pedroca-skills`) — the tickets are the same either way, only the shape of the blocking edges changes:

- **Local files** → write one file per Ticket under `docs/tickets/<topic>/<NN>-<slug>.md`, numbered from `01` in dependency order (blockers first). Bootstrap each ticket with:
  ```bash
  python3 setup-pedroca-skills/scripts/okf_bootstrap.py ticket --topic <topic> --slug <slug> --ticket-num <N> --title "<title>" [--supported-by ../../specs/<topic>.md] [--depends-on ./<prerequisite>.md]
  ```
  Each file's "Blocked by" lists the relative ticket path or prerequisite it depends on. Use the per-ticket file template below — one Ticket per file, never a single combined file.
- **A real issue tracker (GitHub, Linear, …)** → publish one issue per Ticket in dependency order (blockers first) so each Ticket's blocking edges can reference real identifiers. Use the platform's native blocking / sub-issue relationship where it has one; otherwise set each Ticket's "Blocked by" to the blocking issues. Apply the `ready-for-agent` triage label unless instructed otherwise — the Tickets are agent-grabbable by construction.

### 6. Compile tickets into an execution DAG

Compile tickets into an execution DAG for `herdr-orchestration`:
```bash
python3 to-tickets/scripts/compile_dag.py --topic <topic> --output /tmp/dag-<session>.json
```
This parses the Ticket dependencies, checks for cycles, and assigns execution phases and Lanes for the Orchestrator.

Work the **frontier**: any Ticket whose blockers are all done. For a purely linear chain that means top to bottom.

Do NOT close or modify any parent issue.

<local-ticket-template>

---
id: ticket-<NN>-<slug>
title: "<NN> — <Ticket title>"
type: Architecture
status: active
valid_from: YYYY-MM-DD
artifact: ticket
scope:
  system: pedroca-skills
  env: production
relations:
  - type: supported_by
    target: ../../specs/<topic>.md
  - type: depends_on
    target: ./<blocking-ticket>.md
tags:
  - ticket
  - <topic>
---

# <NN> — <Ticket title>

**What to build:** the end-to-end behaviour this ticket makes work, from the user's perspective — not a layer-by-layer implementation list.

**Blocked by:** `./<blocking-ticket>.md` (or "None — can start immediately")

**Allowed paths:** `<path1>`, `<path2>`

**Status:** ready-for-agent

- [ ] Acceptance criterion 1
- [ ] Acceptance criterion 2

</local-ticket-template>

<issue-template>

## Parent

A reference to the parent issue on the tracker (if the source was an existing issue, otherwise omit this section).

## What to build

The end-to-end behaviour this ticket makes work, from the user's perspective — not layer-by-layer implementation.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- A reference to each blocking ticket, or "None — can start immediately".

</issue-template>

In either form, avoid specific file paths or code snippets — they go stale fast. Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.
