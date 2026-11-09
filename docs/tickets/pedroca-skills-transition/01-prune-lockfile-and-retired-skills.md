---
id: ticket-01-prune-lockfile-and-retired-skills
title: "01 — Sever mattpocock/skills Lockfile Coupling and Prune Retired Skills"
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
  - pedroca-skills
  - cleanup
---

# 01 — Sever mattpocock/skills Lockfile Coupling and Prune Retired Skills

**What to build:** Decouple this repository from `mattpocock/skills` in `/home/pedrogoncalves/.agents/.skill-lock.json` while preserving third-party utility entries, and remove all 10 retired skill directories plus the duplicate nested `implement/implement/` directory so the repository contains zero competing or obsolete skill definitions.

**Blocked by:** None — can start immediately.

**Allowed paths:** `../.skill-lock.json`, `setup-matt-pocock-skills/**`, `ask-matt/**`, `writing-beats/**`, `writing-fragments/**`, `writing-shape/**`, `issue-workflow/**`, `deepwork/**`, `codemap/**`, `loop-me/**`, `loop-engineering/**`, `implement/implement/**`

**Status:** ready-for-agent

- [ ] All entries with `"source": "mattpocock/skills"` are removed from `/home/pedrogoncalves/.agents/.skill-lock.json`, while non-`mattpocock/skills` entries remain valid JSON.
- [ ] The 10 retired skill folders (`setup-matt-pocock-skills`, `ask-matt`, `writing-beats`, `writing-fragments`, `writing-shape`, `issue-workflow`, `deepwork`, `codemap`, `loop-me`, `loop-engineering`) are deleted from `/home/pedrogoncalves/.agents/skills/`.
- [ ] The duplicate nested `/home/pedrogoncalves/.agents/skills/implement/implement/` directory is deleted while preserving `/home/pedrogoncalves/.agents/skills/implement/SKILL.md`.
