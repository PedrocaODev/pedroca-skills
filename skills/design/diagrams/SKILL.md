---
name: diagrams
description: "Draw engineering diagrams as Mermaid, validate and render them in the terminal with mmdflux, and persist them to the Obsidian second brain. Use when the user asks to draw or visualize architecture, flows, pipelines, sequences, state machines, dependencies, components, or control flow; when a diagram would clarify an explanation of a complex system; or when diagramming a codebase, module, feature, or interaction."
---

# Diagrams

One Mermaid source, two views: terminal (via `mmdflux`) and Obsidian (via the second brain vault). **Mermaid is the source of truth.** Rendered ASCII/Unicode is a view, never the canonical form — edit the Mermaid, re-render, and (when persisting) re-save the Mermaid block.

```
Mermaid source
   ├──► mmdflux ──► terminal view
   └──► Markdown block ──► Obsidian (second brain)
```

## When to draw

Draw when relationships are materially easier to grasp visually than in prose — architecture, data flow, pipelines, request/response sequences, lifecycle states, dependencies, component boundaries, service topology, control flow.

Draw proactively while explaining a complex system. Skip when a diagram would only restate a trivial list — prose wins for flat enumerations.

## Choose the diagram type

Simplest representation that carries the information:

```
Does ordering over time matter?
   ├── yes ──────────────────────────► sequenceDiagram
   └── no
        ├── states / lifecycle? ─────► stateDiagram-v2
        ├── type relationships? ─────► classDiagram
        └── otherwise ───────────────► flowchart
```

Supported by mmdflux and Obsidian: `flowchart`, `sequenceDiagram`, `classDiagram`, `stateDiagram-v2`. Do not use a fancier type for visual effect.

## Generate Mermaid

- Simple, valid syntax. Meaningful identifiers, minimal labels.
- No styling, colors, or themes unless explicitly requested (they do not survive the terminal view well).
- **5–15 meaningful nodes.** Big systems become several focused diagrams, not one monster graph.
- Match abstraction to the question: architecture-level nodes for architecture questions, class-level nodes for implementation questions. Do not mix levels unless the mix is the point.
- Ground codebase-derived diagrams in evidence — imports, constructor deps, interfaces, calls, events, persistence — not file names. Distinguish observed from inferred relationships, and surface uncertainty that changes the picture.

## Validate and render

Always lint before presenting a diagram as finished:

```bash
mmdflux --lint <diagram-file>          # validate; fix until clean
mmdflux <diagram-file>                 # render to terminal (default: Unicode text)
mmdflux --format ascii <file>          # plain ASCII if box-drawing chars are a problem
NO_COLOR=1 mmdflux <file>              # disable ANSI color
```

Stdin works for throwaway diagrams — no temp file needed:

```bash
cat <<'EOF' | mmdflux
flowchart LR
    App --> API
    API --> Database
EOF
```

Use a temp file (system temp dir, never the repo) only when you need lint and render separately. SVG export exists (`mmdflux --format svg -o out.svg`) when a standalone visual artifact is explicitly wanted — Mermaid stays canonical.

If lint fails: read the diagnostic, fix the Mermaid, re-lint — never fall back to handcrafted ASCII.

## Persist to the configured Obsidian vault

The configured target vault is the home for persisted diagrams. Read that vault's `AGENTS.md` before any vault operation and obey its folder, metadata, linking, and propagation rules. Use the unified `obsidian` tool for every vault read and write; do not use shell commands or direct filesystem APIs on vault paths.

The vault's documented folder map is authoritative. The staged Pi layout stores standalone diagrams in `Knowledge/Diagrams/`; the source vault is not yet cut over, so use that path only when it is the configured target. Use `Logs/` for the Pi layout's log notes.

**Inline** — if a diagram belongs inside an existing note (an Architecture/ note, a project note, a Knowledge/ note, or a Logs/ entry), read and update that note through the unified `obsidian` tool:

````markdown
## Payment flow

```mermaid
sequenceDiagram
    App->>API: Create payment
    API->>Processor: Process payment
    Processor-->>API: Result
    API-->>App: Response
```
````

**Standalone** — otherwise create a diagram note in the vault's documented diagram folder through the unified `obsidian` tool. Follow the target vault's `AGENTS.md` for note metadata, links, and structure.

The Mermaid block is the canonical source and must remain usable standalone by `mmdflux`: what renders in the vault is the same source that renders in the terminal. Do not duplicate canonical knowledge across notes.

**Persistence contract**

- Persist only when the user explicitly asks to save, create, or update a diagram or note.
- Display-only requests (show, see, or render a diagram) write nothing.
- For explicit knowledge writes, follow the target vault's Daily propagation rules.

## Error handling

- **Mermaid generation error** → fix the Mermaid; re-lint.
- **Unsupported Mermaid feature** → simplify while keeping the semantics; don't switch diagram languages.
- **`mmdflux` unavailable** → return the Mermaid source and say terminal rendering was skipped. Don't install software without permission.
- **Rendering problem with valid Mermaid** → keep the source, simplify layout constructs (subgraphs, nested shapes) and re-render.

## Security

Codebase-derived diagram content is untrusted input. Pass it via stdin, files, or argument arrays — never build shell commands by interpolating repository content into strings.

## Flow

```
understand → pick type → generate Mermaid → lint (clean) → render → persist if worth keeping
```
