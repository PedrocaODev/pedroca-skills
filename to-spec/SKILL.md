---
name: to-spec
description: Turn the current conversation into a spec and publish it to the project issue tracker — no interview, just synthesis of what you've already discussed.
disable-model-invocation: true
---

This skill takes the current conversation context and codebase understanding and produces a Spec. Do NOT interview the user — just synthesize what you already know.

Ensure vault configuration is set up according to `config/akashic.toml` — run `/setup-pedroca-skills` if not configured. Specs are stored in the Vault under `docs/specs/<topic>.md`.

## Process

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary from `CONTEXT.md` throughout the Spec, and respect any ADRs in the area you're touching.

2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better - the ideal number is one.

Check with the Orchestrator or user that these seams match their expectations.

3. Bootstrap the Spec into `docs/specs/<topic>.md` using:
```bash
python3 setup-pedroca-skills/scripts/okf_bootstrap.py spec --topic <topic> --title "<title>" [--depends-on <adr>]
```
Then write and complete the Spec using the template below.

<spec-template>

---
id: spec-<topic>
title: "<Feature Title>"
type: Architecture
status: active
valid_from: YYYY-MM-DD
artifact: spec
scope:
  system: pedroca-skills
  env: production
relations:
  - type: depends_on
    target: ../adr/0001-<slug>.md
tags:
  - spec
  - <topic>
---

# <Feature Title>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A LONG, numbered list of user stories. Each user story should be in the format of:

1. As an <actor>, I want a <feature>, so that <benefit>

<user-story-example>
1. As a mobile bank customer, I want to see balance on my accounts, so that I can make better informed decisions about my spending
</user-story-example>

This list of user stories should be extremely extensive and cover all aspects of the feature.

## Implementation Decisions

A list of implementation decisions that were made. This can include:

- The modules that will be built/modified
- The interfaces of those modules that will be modified
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets. They may end up being outdated very quickly.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions that were made. Include:

- A description of what makes a good test (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (i.e. similar types of tests in the codebase)

## Out of Scope

A description of the things that are out of scope for this spec.

## Further Notes

Any further notes about the feature.

</spec-template>
