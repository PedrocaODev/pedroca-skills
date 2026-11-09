# Developer Markdown Decks: Slidev and Marp

This guide details authoring rules, configuration templates, and compilation pipelines for developer presentations using Slidev and Marp CLI.

## Engine Selection Matrix

| Criterion | Slidev (`sli.dev`) | Marp CLI (`@marp-team/marp-cli`) |
|---|---|---|
| Primary Strength | Interactive Vue components, live demos, Monaco editor | Strict CommonMark simplicity, fast single-binary pipeline |
| Code Presentations | Shiki Magic Move animations with line-by-line transitions | Syntax-highlighted code blocks with custom CSS styling |
| Output Formats | Interactive SPA web app, PDF, PPTX | PDF, PPTX, HTML, PNG, JPEG |
| Build Pipeline | Node.js and Vite dev server | Standalone CLI or zero-config NPX runner |
| Best For | Deep technical workshops, interactive tech talks | Fast slide generation, CI/CD automated reports, documentation decks |

## Slidev Configuration and Authoring

### Frontmatter Setup

Place this configuration at the top of `slides.md`:

```yaml
---
theme: seriph
aspectRatio: '16/9'
canvasWidth: 1920
transition: slide-left
title: System Architecture Deep Dive
lineNumbers: true
drawings:
  persist: false
---
```

### Authoring Rules for Slidev

1. Separate slides with triple dashes (`---`) on an isolated line.
2. Hide speaker notes inside standard HTML comments at the bottom of the slide.
3. Use `v-click` directives for progressive element disclosure.
4. Animate code state transitions using Shiki Magic Move blocks:

````markdown
# Architecture Evolution

We transition from direct polling to event-driven updates.

<!-- slide notes: Explain latency reductions -->

---

# Implementation Detail

```ts {all|2|4-6}
// Step 1: Initial listener setup
const connection = await establishConnection()

// Step 2: Subscribe to topic
const channel = connection.subscribe('telemetry', (payload) => {
  processPayload(payload)
})
```
````

### Slidev Export Commands

Run these commands to export slides to distribution formats:

```bash
# Export presentation deck to PDF
npx @slidev/cli export --format pdf --output /tmp/presentation.pdf

# Export presentation deck to PowerPoint
npx @slidev/cli export --format pptx --output /tmp/presentation.pptx

# Build static production Single Page Application
npx @slidev/cli build --base /deck/
```

## Marp CLI Configuration and Authoring

### Frontmatter Setup

Place this configuration at the top of `marp-slides.md`:

```yaml
---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  section {
    font-family: 'Geist', sans-serif;
    background-color: #090a0f;
    color: #f1f5f9;
  }
  h1 {
    color: #38bdf8;
  }
---
```

### Authoring Rules for Marp

1. Separate slides with triple dashes (`---`) on an isolated line.
2. Use `<!-- fit -->` in header tags to scale titles to slide bounds automatically.
3. Use list item asterisks with parentheses (`* [ ]`) or `*` prefixes for incremental lists.
4. Record speaker notes inside `<!-- note ... -->` comments.

```markdown
<!-- _class: lead -->

# <!-- fit --> High-Throughput Stream Processing

Actionable telemetry architecture for distributed agents

---

# Verification Strategy

- Automated static analysis of pull requests
- Headless browser visual regression validation
- Deterministic sandbox execution environments

<!-- note: Emphasize that all verification steps run before code review -->
```

### Marp Export Commands

Compile Markdown slides into final formats using Marp CLI:

```bash
# Export presentation deck to PDF
npx @marp-team/marp-cli marp-slides.md --pdf --output /tmp/marp-deck.pdf

# Export presentation deck to PowerPoint
npx @marp-team/marp-cli marp-slides.md --pptx --output /tmp/marp-deck.pptx

# Export standalone HTML presentation
npx @marp-team/marp-cli marp-slides.md --html --output /tmp/marp-deck.html
```

## Playwright Overflow Gate for Markdown Engines

When previewing local dev servers from Slidev (`http://localhost:3030`) or Marp (`http://localhost:8080`), execute programmatic boundary audits:

```bash
playwright-cli open http://localhost:3030
playwright-cli resize 1920 1080
playwright-cli eval "() => { const slides = document.querySelectorAll('.slidev-page, section'); return Array.from(slides).map((s, idx) => ({ slide: idx, overflow: s.scrollHeight > s.clientHeight })); }"
```
