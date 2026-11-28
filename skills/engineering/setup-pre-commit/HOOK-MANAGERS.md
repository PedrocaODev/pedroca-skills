# Hook managers

## Detect an existing manager

| Evidence | Manager |
|---|---|
| `.pre-commit-config.yaml` | pre-commit framework |
| `.husky/` dir, or `husky` in `package.json` | Husky |
| `lefthook.yml` / `.lefthook.yml` | lefthook |
| `.overcommit.yml` | Overcommit (Ruby) |
| `captainhook.json` | CaptainHook (PHP) |
| `[package.metadata.husky]` or `cargo-husky` in `Cargo.toml` | cargo-husky |
| a git-hooks plugin in `build.gradle(.kts)` / `pom.xml` | build-tool hook plugin |
| `git config core.hooksPath` is set | versioned hook scripts |

If you find one, add the gates to it in its own format. Keep the manager the repo already uses.

## pre-commit framework

Install: `pipx install pre-commit` (or `uv tool install pre-commit`, or `brew install pre-commit`). Then run `pre-commit install`, and also `pre-commit install --hook-type pre-push` if any gate runs at pre-push.

`.pre-commit-config.yaml`. Wire the repo's own commands as `repo: local` hooks with `language: system`, so the hooks use the same tool versions as the build:

```yaml
default_install_hook_types: [pre-commit, pre-push]
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-added-large-files
      - id: check-case-conflict
      - id: check-yaml
      - id: check-json
      - id: check-toml
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.0
    hooks:
      - id: gitleaks
  - repo: local
    hooks:
      # Staged-file gate: the framework passes the staged files that match `types`/`files`.
      - id: rustfmt
        name: cargo fmt
        entry: cargo fmt --
        language: system
        types: [rust]
      # Whole-project gate: no filenames, one run per commit.
      - id: clippy
        name: cargo clippy
        entry: cargo clippy --all-targets -- -D warnings
        language: system
        pass_filenames: false
        types: [rust]
      # Slow gate: moved to pre-push.
      - id: cargo-test
        name: cargo test
        entry: cargo test
        language: system
        pass_filenames: false
        stages: [pre-push]
```

- After you write the file, run `pre-commit autoupdate`. This pins the current `rev` of each remote repo, because the revs above can be out of date.
- To run a gate in a monorepo sub-project, use `entry: bash -c 'cd services/api && ./gradlew spotlessCheck'` and `files: ^services/api/`.
- When a hook modifies files, the commit fails and the fixes stay unstaged. Tell the user to re-stage them and commit again.
- Verify: `pre-commit run --all-files` and `pre-commit run --all-files --hook-stage pre-push`.

## Husky + lint-staged (Node-only repos)

1. Detect the package manager from the lockfile: `package-lock.json` (npm), `pnpm-lock.yaml` (pnpm), `yarn.lock` (yarn), `bun.lock` / `bun.lockb` (bun). Default to npm.
2. Install `husky` and `lint-staged` as devDependencies, together with any formatter or linter approved in step 3.
3. Run `npx husky init`. This creates `.husky/` and adds `"prepare": "husky"` to `package.json`.
4. Write `.husky/pre-commit`. Husky v9+ needs no shebang. Use the detected package manager and keep only the scripts that exist:

   ```
   npx lint-staged
   npm run typecheck
   ```

5. Write `.lintstagedrc` with the repo's format and lint commands. lint-staged re-stages the files that the commands fix:

   ```json
   {
     "*.{js,jsx,ts,tsx}": ["eslint --fix", "prettier --write"],
     "*": "prettier --ignore-unknown --write"
   }
   ```

6. Put the pre-push gates (for example, `npm run test`) in `.husky/pre-push`.
7. Verify: `.husky/pre-commit` is executable, `prepare` is `"husky"`, and `npx lint-staged` passes on a staged change.

## lefthook

Install it through the ecosystem's package manager (`npm i -D lefthook`, `go install github.com/evilmartians/lefthook@latest`, `brew install lefthook`, `pip install lefthook`, or `gem install lefthook`). Then run `lefthook install`.

`lefthook.yml`:

```yaml
pre-commit:
  parallel: true
  commands:
    format:
      glob: "*.{kt,kts}"
      run: ktlint --format {staged_files}
      stage_fixed: true
    lint:
      run: ./gradlew detekt
pre-push:
  commands:
    test:
      run: ./gradlew test
```

- `{staged_files}` passes only the staged files. `stage_fixed: true` re-stages the fixed files.
- In a monorepo, set `root: services/api/` on a command to run it in that sub-project.
- Verify: `lefthook run pre-commit --all-files` and `lefthook run pre-push`.
