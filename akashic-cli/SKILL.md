---
name: akashic-cli
description: Manage and verify Akashic knowledge graph vaults, index and query multi-language code graphs, execute root cause analysis (RCA), and control background daemons. Use when running akashic vault, lint, graph, rca, daemon, embedding, or sanitize subcommands, or invoking vault, graph, and rca MCP tools.
---

# Akashic Records CLI (`akashic`)

Workflows and instructions to manage knowledge vaults, verify graph integrity, conduct root cause analysis, and control background services with the unified `akashic` CLI.

## 1. Overview and Architecture

The `akashic` binary provides domain subcommands for knowledge management and automated investigation.

- **Storage Isolation**: Physical SQLite databases reside in `.akashic/`:
  - `vault_index.db`: Full-text search and vault node metadata.
  - `rca_state.db`: Durable RCA Conductor workflow states and checkpoints.
  - `code_graph.db`: Multi-language code symbols, AST relations, and embeddings.
- **Canonical Source of Truth**: Markdown documents in Git hold canonical content following Google Open Knowledge Format (OKF) v0.2.
- **MCP Integration**: An embedded Model Context Protocol server exposes vault and RCA tools over standard I/O.

---

## 2. Vault Operations (`akashic vault`)

Manage vault lifecycle, author notes, inspect frontmatter, and execute migration plans.

### Canonical Node Template

Write notes with standard YAML frontmatter:

```markdown
---
id: <kebab-case-slug>
title: "<Human-Readable Title>"
type: Concept | Decision | Architecture | Incident | Evidence | Resolution | Runbook | Guide
status: draft | proposed | active | stable | superseded | deprecated | resolved
valid_from: YYYY-MM-DD
valid_until: YYYY-MM-DD   # Optional
scope:
  system: <system-name>
  env: production | staging | dev
relations:
  - type: supersedes | depends_on | supported_by | caused_by | relates_to | contradicts
    target: ./<relative-path-to-target>.md
    evidence: ./<relative-path-to-evidence>.md   # Optional
    scope:                                       # Optional
      env: production
tags:
  - <tag-name>
---

# Document Title

Document body text in GitHub Flavored Markdown (GFM).
```

### Directed Relation Rules

1. **Assert forward relations only**: Use `supersedes`, `depends_on`, `supported_by`, `caused_by`, `relates_to`, or `contradicts`.
2. **Do not assert inverse relations**: Do not write `superseded_by` or `depended_on_by`. The engine derives inverses automatically during graph traversal.
3. **Use relative paths**: Reference target notes with `./<filename>.md` or relative subpaths.

### Subcommands

#### `akashic vault init`
Initialize an empty vault directory:
```bash
akashic vault init [--path <dir>]
```
- Creates the specified directory (defaults to `vault`).

#### `akashic vault query`
Query active guidance, lineage, impact, or historical state:
```bash
akashic vault query [--mode <current|lineage|impact|historical>] [--note-id <id>] [--scope <key=val>]
```
- Modes:
  - `current` (default): Resolves active guidance. Navigates supersession edges to authoritative successors.
  - `lineage`: Traces chronological evolution from root predecessor to active node.
  - `impact`: Computes downstream dependency blast radius.
  - `historical`: Reconstructs graph guidance at a specified historical timestamp.
- **Conflict Handling**: Returns exit code 2 and outputs `[UNRESOLVED_CONFLICT]` when competing successors or cycles exist. Never guess a winner. Surface the conflict for human decision.

#### `akashic vault inspect`
Inspect frontmatter metadata and edge connections for a specific note:
```bash
akashic vault inspect <note_id>
```

#### `akashic vault plan`
Generate an idempotent migration diff to normalize metadata and links:
```bash
akashic vault plan [--path <dir>] [--out <output-file.json>]
```

#### `akashic vault apply`
Apply planned mutations with pre-image SHA-256 verification:
```bash
akashic vault apply [--path <dir>] [--plan <plan-file.json>]
```
- Halts execution if pre-image hashes do not match.

#### `akashic vault reindex`
Rebuild the local SQLite index in `.akashic/vault_index.db`:
```bash
akashic vault reindex [--path <dir>]
```

---

## 3. Vault Linting and Custom Fields (`akashic lint`)

Verify vault graph schema rules and custom metadata constraints.

### Execution

```bash
# Standard lint
akashic lint [--vault <dir>]

# Strict mode (enforces strict forward-only rules)
akashic lint [--vault <dir>] --strict

# Machine-readable JSON output
akashic lint [--vault <dir>] --json
```

Exit codes:
- `0`: Vault is valid.
- `1`: Rule violations detected.

### Core Lint Rules

| Rule Code | Description | Remediation |
|---|---|---|
| `L001` | Missing or invalid YAML frontmatter. | Ensure the document begins with valid `---` YAML boundaries. |
| `L002` | Missing required fields (`id`, `type`, `status`). | Add mandatory fields to frontmatter. |
| `L003` | Duplicate vault node ID. | Assign unique `id` values to each document. |
| `L004` | Broken relation target or evidence link. | Fix relative target path or create the missing note. |
| `L005` | Directed cycle detected in `supersedes` or `depends_on`. | Remove the loop-closing edge. Cycles are prohibited. |
| `L006` | Node marked `superseded` without incoming `supersedes` edge. | Link the successor note to the predecessor with a `supersedes` relation. |
| `L007` | Competing active successors across overlapping scopes. | Order successors explicitly or narrow scopes to disjoint domains. |
| `L008` | Unscoped contradiction between active nodes. | Narrow scopes to disjoint environments or resolve with supersession. |
| `L009` | Missing `valid_from` date on active guidance. | Add ISO date (`YYYY-MM-DD`) to `valid_from`. |
| `L010` | High-impact supersession missing empirical evidence. | Add `evidence:` path linking to an empirical validation node. |
| `L011` | Prohibited inverse relation asserted in frontmatter. | Replace inverse relation (`superseded_by`) with forward edge (`supersedes`). |
| `L012` | Custom field schema validation failure. | Comply with types and allowed values defined in configuration. |

### Custom Fields Validation (`[lint.custom_fields]` / `L012`)

Define custom field schemas in `.akashic.toml` or `akashic.toml`:

```toml
[lint.custom_fields.component]
required = true
type = "string"
allowed_values = ["radio", "modem", "telephony", "bluetooth"]
applies_to = ["incident", "resolution"]

[lint.custom_fields.severity_level]
required = false
type = "integer"
allowed_values = ["1", "2", "3"]
applies_to = ["incident"]
```

Supported property types: `string`, `list`, `boolean`, `integer`, `float`, `date`, `object`.
When frontmatter omits required custom fields or uses invalid values, rule `L012` emits an error.

---

## 4. Code Graph Operations (`akashic graph`)

Execute graph extraction, analysis, and queries from the command line.

### `akashic graph index`
Index a repository from source files and commit references:
```bash
akashic graph index [--repo-path <dir>] [--repo-name <name>] [--commit <rev>]
```
- Parses source files with Tree-sitter.
- Extracts symbols (classes, functions, interfaces, methods) and call edges.
- Generates vector embeddings through `akashic-embedding`.
- Writes symbols and relations to `.akashic/code_graph.db`.

### `akashic graph reconcile`
Incrementally reconcile graph state between two git revisions:
```bash
akashic graph reconcile [--repo-path <dir>] [--repo-name <name>] [--old-rev <rev>] [--new-rev <rev>]
```
- Computes git diff between revisions.
- Upserts modified symbols and removes deleted symbols.
- Preserves unchanged nodes and edge weights.

### `akashic graph query`
Search symbols using full-text search (FTS5) and vector similarity:
```bash
akashic graph query "<search-text>" [--repo-name <name>] [--limit <n>]
```

### `akashic graph symbol`
Look up a specific symbol across indexed repositories:
```bash
akashic graph symbol "<symbol-name>"
```

### `akashic graph path`
Find the shortest directed dependency path between two symbols:
```bash
akashic graph path "<source-symbol>" "<target-symbol>" [--repo-name <name>] [--max-hops <n>]
```
- Returns step-by-step edges with relation types and confidence scores.

### `akashic graph explain`
Inspect symbol details, definition locations, and connected callers:
```bash
akashic graph explain "<symbol-name>" [--repo-name <name>]
```

### `akashic graph communities`
Detect architectural modules and subgraphs using the Louvain algorithm:
```bash
akashic graph communities [--repo-name <name>]
```
- Computes modularity partitions across code symbol clusters.

### `akashic graph god-nodes`
Identify central hub symbols with high degree centrality:
```bash
akashic graph god-nodes [--repo-name <name>] [--top-n <n>]
```
- Reports in-degree, out-degree, and total degree metrics.
- Surfaces architectural bottlenecks and high-risk modification points.

### `akashic graph surprising`
Identify surprising cross-community connections and coupling anomalies:
```bash
akashic graph surprising [--repo-name <name>] [--top-n <n>]
```

### `akashic graph blast-radius`
Compute upstream callers and downstream dependencies for a target symbol:
```bash
akashic graph blast-radius "<symbol-name>" [--repo-name <name>] [--max-depth <n>]
```
- Traces transitive call hierarchies.
- Identifies impacted communities and caller files.

### `akashic graph report`
Generate an architectural markdown summary report:
```bash
akashic graph report [--repo-name <name>] [--format md]
```

### `akashic graph wiki`
Generate agent-crawlable documentation partitioned by community:
```bash
akashic graph wiki [--repo-name <name>] [--out-dir <dir>]
```

### `akashic graph discover`
Scan the workspace for git repositories and register Android package mappings:
```bash
akashic graph discover [--path <dir>]
```

---

## 5. Root Cause Analysis (`akashic rca`)

Investigate crashes, symbolicate stack traces, and crystallize findings into vault resolutions.

### Pipeline Subcommands

#### `akashic rca run`
Execute the host-native 6-stage RCA Conductor pipeline:
```bash
akashic rca run --app-id <app-id> --log-file <crash-log-path> [--jira-key <key>]
# Or with raw log text:
akashic rca run --app-id <app-id> --raw-log "<log-content>" [--jira-key <key>]
```
- Performs log parsing, symbolication, Soak Storm deduplication check, evidence gathering, and resolution drafting.

#### `akashic rca start`
Initiate a new RCA investigation:
```bash
akashic rca start <trigger_id>
```

#### `akashic rca resume`
Resume an investigation from durable state in `.akashic/rca_state.db`:
```bash
akashic rca resume <investigation_id>
```

#### `akashic rca status`
Print investigation details and current stage status:
```bash
akashic rca status <investigation_id>
```

#### `akashic rca symbolicate`
Symbolicate raw stack traces against code graphs and symbol mappings:
```bash
akashic rca symbolicate --app-id <app-id> --log-file <crash-log-path>
```

#### `akashic rca crystallize`
Write verified investigation findings to canonical vault notes under `resolutions/`:
```bash
akashic rca crystallize --run-id <run-id> [--summary "<summary-text>"]
```

#### `akashic rca supersede`
Supersede an obsolete resolution with an updated resolution node:
```bash
akashic rca supersede --old-id <old-resolution-id> --new-id <new-resolution-id> [--reason "<reason>"]
```

#### `akashic rca triage`
List all open RCA investigations stored in `.akashic/rca_state.db`:
```bash
akashic rca triage
```

---

## 6. Background Services and Sidecars (`akashic daemon` & `akashic embedding`)

Control background event streaming, discovery, and embedding sidecars.

### Daemon Service (`akashic daemon`)

- `akashic daemon start`: Launch background Gerrit stream ingestion and auto-reconciliation.
- `akashic daemon run`: Run daemon process in foreground.
- `akashic daemon stop`: Terminate running background daemon.
- `akashic daemon status`: Inspect stream connection health and lag.
- `akashic daemon catchup [--stream <name>]`: Replay missed stream events.
- `akashic daemon discover [--workspace <dir>]`: Discover Android repositories and index package-to-repo mappings.

### Embedding Sidecar (`akashic embedding`)

- `akashic embedding start` / `start-sidecar`: Launch local vector embedding sidecar.
- `akashic embedding stop`: Stop embedding sidecar.
- `akashic embedding status`: Check sidecar process health and model availability.
- `akashic embedding benchmark [--count <n>]`: Benchmark vector generation throughput and latency.

---

## 7. Sanitization Testing (`akashic sanitize`)

Validate log and source code redaction filters to prevent credential or PII leaks:

```bash
# Test code sanitization
akashic sanitize test-code -i <file-path>

# Test log sanitization
akashic sanitize test-log -i <file-path>

# Profile-based invocation
akashic sanitize --profile code -i <file-path>
akashic sanitize --profile log -i <file-path>
```

---

## 8. Model Context Protocol Server Tools

Start the unified stdio MCP server:
```bash
akashic mcp [--vault <vault-dir>] [--workspace <workspace-dir>]
```

The MCP server provides the following tools for agents:

### Vault MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `vault_query` | `mode` (string: current, lineage, impact, historical), `scope` (optional string), `note_id` (optional string) | Query vault notes by traversal mode and optional scope filter. |
| `vault_inspect` | `note_id` (string) | Inspect note frontmatter, metadata, incoming edges, and outgoing edges. |
| `vault_lint` | `path` (optional string), `strict` (optional bool) | Lint target vault directory against OKF v0.2 and custom rules. |
| `vault_read` | `note_id` (string) | Read full Markdown content of a vault note. |
| `vault_write_canonical` | `note_id` (string), `title` (string), `node_type` (string), `content` (string), `tags` (optional list of strings) | Write or update a canonical OKF v0.2 note in the vault. |

### Code Graph MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `graph_query` | `query` (string), `repo_name` (optional string), `limit` (optional usize) | Search code symbols using full-text search against `.akashic/code_graph.db`. |
| `graph_get_node` | `node_id` (string) | Retrieve symbol details, signature, and file location by symbol ID. |
| `graph_get_neighbors` | `node_id` (string), `direction` (optional string: `incoming`, `outgoing`, `both`) | Retrieve incoming callers and outgoing dependency edges for a node. |
| `graph_get_community` | `community_id` (optional u32) | Retrieve Louvain community clusters or filter by a specific community ID. |
| `graph_god_nodes` | `repo_name` (optional string), `top_n` (optional usize) | Identify architectural hub symbols with high degree centrality. |
| `graph_stats` | `repo_name` (optional string) | Get summary counts of symbols, edges, and communities. |
| `graph_shortest_path` | `source` (string), `target` (string) | Find the shortest dependency path between two symbols. |
| `graph_blast_radius` | `target` (string), `max_depth` (optional usize) | Compute transitive upstream callers, downstream dependencies, and impacted communities. |

### RCA MCP Tools

| Tool Name | Parameters | Description |
|---|---|---|
| `rca_status` | `investigation_id` (string) | Check progress and findings of an RCA investigation. |
| `rca_trigger` | `app_id` (string), `raw_log` (string) | Execute end-to-end RCA conductor pipeline for a crash log. |
| `rca_symbolicate` | `app_id` (string), `raw_log` (string) | Parse and symbolicate stack traces against code graph mappings. |
| `rca_crystallize` | `run_id` (string), `summary` (string) | Crystallize RCA findings into a canonical vault resolution note. |
