---
name: setup-pre-commit
description: Set up git pre-commit hooks that run the repo's code-quality tooling (formatters, linters, static analysis, type checks, tests) for any language or framework. Use when the user wants pre-commit hooks, commit-time quality gates, or to configure the pre-commit framework, Husky, lint-staged, or lefthook.
---

# Setup Pre-Commit Hooks

Wire the repo's **quality gates** — format, lint, static analysis, typecheck/compile, test — into git hooks, for every language the repo contains. The repo's own commands are the source of truth: CI workflows, `Makefile` / `justfile` / `Taskfile` targets, build-tool tasks (`./gradlew check`, `mvn verify`, `cargo clippy`), and package scripts. Wire what the repo already runs before adding anything new.

## Steps

### 1. Inventory the stack

Detect every ecosystem from its manifests and build files (`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle(.kts)`, `CMakeLists.txt`, `*.csproj`, `Package.swift`, `Gemfile`, `composer.json`, `pubspec.yaml`, `mix.exs`, `*.tf`, …). Include sub-projects in monorepos and note each one's root directory.

**Done when:** every ecosystem and its root directory is listed.

### 2. Inventory the existing quality gates

For each ecosystem, find the command the repo already uses for each gate. Read, in order: CI workflow files, task-runner targets, build-tool plugins and their config (Spotless, Checkstyle, detekt, clippy, ESLint, Ruff, clang-format, …), and package scripts. Also detect an existing hook manager (see [HOOK-MANAGERS.md](HOOK-MANAGERS.md)).

**Done when:** you have a gate matrix with one row per ecosystem and one cell per gate. Each cell holds a runnable command or `gap`.

### 3. Fill gaps with the user

For each `gap`, propose the ecosystem's conventional tool from [ECOSYSTEMS.md](ECOSYSTEMS.md). Present the gate matrix with the proposals and get the user's approval before you add any new tool: a new formatter or linter rewrites or flags code across the whole codebase. Use the tool's default style. Create a config file only when the tool needs one to run.

**Done when:** each cell holds an existing command, an approved new tool, or `skipped` (user declined, or the ecosystem has no such gate).

### 4. Choose the hook manager

1. If a hook manager already exists, extend it.
2. Else, if the repo is Node-only, use **Husky + lint-staged**.
3. Else, use the **pre-commit framework**. It runs any language through `language: system` hooks.
4. If the user cannot install Python tooling, use **lefthook**.

Read the matching section of [HOOK-MANAGERS.md](HOOK-MANAGERS.md).

### 5. Assign each gate a stage

The pre-commit hook must stay **tight**: it runs on every commit, so it must be fast and must check only the staged files where the tool allows that.

- **pre-commit**: format and lint on staged files; repo hygiene and secret scanning (see [ECOSYSTEMS.md](ECOSYSTEMS.md#cross-cutting-hygiene)); typecheck/compile when it runs fast.
- **pre-push**: whole-project compile, full test suites, and any check that is too slow for every commit.
- **CI only**: integration, end-to-end, and platform-specific suites.

Time each command on the whole repo. Move a command to pre-push when it takes more than about 10 seconds, and tell the user.

**Done when:** every non-`skipped` cell in the matrix has a stage.

### 6. Write the hook config

Write the config for the chosen manager. Use the repo's own commands from step 2 verbatim, and run each one from its ecosystem's root directory. For each formatter, use the mode that writes changes (`--write`, `-a`, `fmt`), and configure the manager to re-stage the fixed files, or tell the user that they must re-stage them.

### 7. Verify

- Install the hooks (`pre-commit install`, `npx husky init`, `lefthook install`, …), including the pre-push hook if any gate uses it.
- Run every hook on all files (`pre-commit run --all-files`, `npx lint-staged` on staged changes, `lefthook run pre-commit --all-files`).
- Make each gate go **red** once: stage a deliberate violation (a mis-formatted line, a lint error), confirm the hook blocks the commit, then revert the violation.

**Done when:** all hooks pass on a clean tree, and each wired gate has blocked one deliberate violation. If a gate fails on existing code, report the failing files to the user and fix them only with the user's approval.

### 8. Commit

Commit through the `pr` skill and `integrator`. Stage only the hook config, the tool configs, and the manifest or lockfile changes. Message: `chore: add pre-commit hooks`. The commit runs the new hook, which is a final smoke test.

Report the final gate matrix to the user, with the stage of each gate and each `skipped` gap.
