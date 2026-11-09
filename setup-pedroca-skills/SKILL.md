---
name: setup-pedroca-skills
description: Onboard a repository to the Pedroca Skills framework — configure config/akashic.toml (vault.path = "docs"), establish harness-native akashic-mcp verification, and set up the OKF v0.2 artifact spine and AGENTS.md rules. Run once before first use of the framework.
---

# Setup Pedroca Skills

Onboard this repository to the Pedroca Skills framework and scaffold the per-repository configuration:

1. **Akashic OKF v0.2 Vault Configuration** (`config/akashic.toml`) — establishes `docs/` as the default local artifact store (`vault.path = "docs"`), creates `docs/adr/`, `docs/specs/`, and `docs/tickets/`, and configures OKF v0.2 lint rules (`L001`-`L012`).
2. **Akashic MCP Server Verification & Invariants** — explains why `akashic-mcp` must be enabled and verified, guiding the active harness to enforce it via native lifecycle hooks or fallback workspace rules (`AGENTS.md` / `GEMINI.md`) and Git `pre-commit` hooks.
3. **External Tracker & Docs Adapters (Opt-in)** — defaults to the local Akashic Vault (`docs/`); offers opt-in adapters for external issue trackers (GitHub Issues, GitLab, Linear, Jira) and documentation tools (Notion, Confluence) only when explicitly requested.
4. **Agent Guidelines Integration** — records the workflow spine and artifact pointers in `AGENTS.md` or `CLAUDE.md`.

---

## Process

### 1. Initialize Akashic Vault & Config

Run the deterministic OKF bootstrapper script:

```bash
python3 setup-pedroca-skills/scripts/okf_bootstrap.py init-config --repo-root . --vault-path docs
```

This creates `config/akashic.toml`:

```toml
[vault]
path = "docs"
db_path = ".akashic/vault_index.db"
okf_version = "0.2"

[lint]
enabled_rules = ["L001", "L002", "L003", "L004", "L005", "L006", "L007", "L008", "L009", "L010", "L011", "L012"]
strict_forward_only = true

[lint.custom_fields.artifact]
required = false
type = "string"
allowed_values = ["adr", "spec", "ticket"]
applies_to = ["decision", "architecture", "guide"]

[workflow]
default_spine = ["grill-with-docs", "to-spec", "to-tickets", "herdr-orchestration", "code-review"]

[workflow.tracker]
adapter = "vault"
tickets_dir = "docs/tickets"

[workflow.docs]
adapter = "vault"
specs_dir = "docs/specs"
adr_dir = "docs/adr"
```

And ensures `docs/adr/`, `docs/specs/`, and `docs/tickets/` exist.

---

### 2. Akashic MCP Invariant & Harness Configuration

#### The "Why"
The Pedroca Skills workflow spine relies on deterministic, machine-readable code and knowledge graphs:
- **Code Graph (`akashic graph`)**: High-speed symbol resolution, blast-radius analysis before refactoring, and dependency-tree exploration without dumping thousands of lines into LLM contexts.
- **Knowledge Vault (`akashic vault` / `akashic lint`)**: Canonical OKF v0.2 decision and architecture storage with strict forward-only typed edges (`depends_on`, `supported_by`, `supersedes`) validated by `akashic lint --strict`.

#### Harness Integration
Rather than injecting ad-hoc checks into individual skills, configure enforcement natively in your coding harness:
- **Harnesses with MCP configuration (Antigravity CLI, Claude Code, Cursor)**: Ensure the `akashic` MCP server is registered in your harness settings:
  ```json
  {
    "mcpServers": {
      "akashic": {
        "command": "akashic",
        "args": ["mcp"]
      }
    }
  }
  ```
- **Harnesses with session hooks**: Add a session startup check verifying `which akashic` and `akashic lint --strict`.
- **Workspace Rule Fallback (`AGENTS.md` / `GEMINI.md`)**: Document the requirement in your root agent instructions so any agent working in the repository queries `akashic graph` and validates artifacts with `akashic lint --strict`.
- **Git Pre-commit Hook**: Add `akashic lint --strict` to verify artifact integrity on commit.

---

### 3. Artifact Bootstrapper CLI Reference

The deterministic helper `setup-pedroca-skills/scripts/okf_bootstrap.py` is available for both agents and humans to scaffold artifacts that adhere strictly to OKF v0.2:

#### Bootstrap an ADR
```bash
python3 setup-pedroca-skills/scripts/okf_bootstrap.py adr \
  --slug init \
  --title "Initialize Architecture" \
  --number 1 \
  --status active \
  --supersedes "../adr/0000-old.md"
```
Generates `docs/adr/0001-init.md` with:
- `id: adr-0001-init`
- `type: Decision`
- `artifact: adr`

#### Bootstrap a Specification
```bash
python3 setup-pedroca-skills/scripts/okf_bootstrap.py spec \
  --topic user-auth \
  --title "User Authentication Specification" \
  --status active \
  --depends-on "../adr/0001-init.md"
```
Generates `docs/specs/user-auth.md` with:
- `id: spec-user-auth`
- `type: Architecture`
- `artifact: spec`

#### Bootstrap a Ticket
```bash
python3 setup-pedroca-skills/scripts/okf_bootstrap.py ticket \
  --topic user-auth \
  --slug jwt-tokens \
  --ticket-num 1 \
  --title "Implement JWT Token Generation" \
  --status active \
  --supported-by "../../specs/user-auth.md" \
  --depends-on "./00-setup.md"
```
Generates `docs/tickets/user-auth/01-jwt-tokens.md` with:
- `id: ticket-01-jwt-tokens`
- `type: Architecture`
- `artifact: ticket`

---

### 4. External Tracker and Docs Adapters (Opt-in)

The framework defaults to the local vault (`adapter = "vault"`). If your team explicitly requests external issue tracking or document management:

- **GitHub Issues**: Set `[workflow.tracker] adapter = "github"`. Skills will use the `gh` CLI for ticket creation and triage.
- **GitLab Issues**: Set `[workflow.tracker] adapter = "gitlab"`. Skills will use the `glab` CLI.
- **Linear / Jira**: Set `[workflow.tracker] adapter = "linear"` or `"jira"`. Specify team IDs and ticket prefix mapping.
- **Notion / Confluence**: Set `[workflow.docs] adapter = "notion"` or `"confluence"`.

---

### 5. Update Agent Guidelines

Add the Pedroca Skills section to `AGENTS.md` (or `CLAUDE.md` / `GEMINI.md`):

```markdown
## Pedroca Skills & Akashic Spine

This repository uses the Pedroca Skills framework:
- **Default Spine**: `grill-with-docs` -> `to-spec` -> `to-tickets` -> `herdr-orchestration` -> `implement` -> `code-review`.
- **Artifact Store**: OKF v0.2 in `docs/` (`docs/adr/`, `docs/specs/`, `docs/tickets/<topic>/`).
- **Scaffolding**: Deterministic scaffolding via `python3 setup-pedroca-skills/scripts/okf_bootstrap.py {adr,spec,ticket}`.
- **Integrity Gate**: Validate artifact changes with `akashic lint --strict`.
- **Architecture & Symbol Queries**: Query `.akashic/code_graph.db` using `akashic graph` and MCP tools before wide codebase reads.
```
