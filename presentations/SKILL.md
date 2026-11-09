---
name: presentations
description: "Engineer presentation decks and slide systems using a 4-stage pipeline: SCQA storyboard, fixed 1920x1080 stage, vector diagrams, and closed-loop Playwright visual QA. Use when building, redesigning, auditing, or exporting presentations, slide decks, pitch decks, keynotes, or tech talks in single-file HTML (default), Slidev/Marp Markdown, or native .pptx."
---

# Presentations Skill

Engineer presentation decks and slide systems using a deterministic 4-stage pipeline.

A presentation deck is a fixed-ratio projection artifact (`1920x1080`), not a scrolling webpage. Every run executes four sequential stages: **Storyboard -> Visual Style and Stage Construction -> Diagram Injection -> Closed-Loop Visual QA**.

## Engine Routing

Select the engine based on user requirements:

- **Default — Fixed-Stage Single-File HTML**: Use when building standalone, zero-build-dependency web decks or upgrading existing HTML decks. Base the layout on [`templates/stage-1920x1080.html`](templates/stage-1920x1080.html).
- **Developer Markdown Decks (Slidev / Marp)**: When the user requests Markdown authoring, live code walkthroughs, or CLI multi-format compilation, read [`references/markdown-engines.md`](references/markdown-engines.md).
- **Stakeholder Editable PowerPoint (`.pptx`)**: When the user requests a native `.pptx` file for executive or client editing in PowerPoint or Google Slides, read [`references/pptx-pipeline.md`](references/pptx-pipeline.md).

---

## Stage 1: Narrative Spine and Storyboard

Ground every claim in verified repository facts, specifications, and disposition matrices before drafting slide copy.

Structure the deck using **SCQA** (Situation, Complication, Question, Answer) or the **Minto Pyramid**:

1. **Horizontal Logic (Action Titles)**: Write every slide title as a complete assertion sentence that states the takeaway. For example, use *"Deterministic Runner Gates Block Unverified Agent Diffs"* instead of *"Verification"*. Reading only the slide titles in sequence must convey the full strategic narrative.
2. **Vertical Logic and Cognitive Budget**: Every element on a slide proves its Action Title. Limit each slide to one core concept, at most 3 to 5 items (Miller's Law), and at least 35% open whitespace.
3. **Slide Archetype Selection**: Assign each slide an explicit layout archetype so the presentation maintains visual rhythm:
   - `hero-title`: Opening slide, big vision statement, bold typography
   - `section-divider`: Structural chapter break with kicker and takeaway
   - `split-comparison`: Two-column contrast (before vs after, problem vs solution)
   - `three-pillar-grid`: Three core capabilities, metrics, or pillars
   - `diagram-spotlight`: Large architectural, sequence, or workflow diagram
   - `metric-callout`: Huge numerical metrics with descriptive labels
   - `code-walkthrough`: Code snippet with line highlights and annotations
   - `quote-verdict`: Executive summary, conclusion, or customer quote
4. **Speaker Notes**: Draft concise speaker notes for every slide to guide the presenter.

### Completion criterion
A slide-by-slide storyboard exists (in a `slides-outline.md` file or approved plan) where every slide has an Action Title, a layout archetype, at most 5 data points, and speaker notes grounded in verified source files.

---

## Stage 2: Visual Style and Fixed-Stage HTML Construction (Default Engine)

Build the presentation using a fixed coordinate canvas.

1. **Visual Style Selection**:
   - Reference the [`awesome-design-md`](../awesome-design-md/SKILL.md) skill to select a concrete brand token palette (`cursor`, `linear.app`, `stripe`, `vercel`, or `apple`).
   - Follow [`design-taste-frontend`](../design-taste-frontend/SKILL.md) guidelines for clean typography, generous whitespace, and restrained accent colors.

2. **Fixed 1920x1080 Coordinate Stage**:
   - Start from [`templates/stage-1920x1080.html`](templates/stage-1920x1080.html).
   - Enforce these structural invariants:
     - **Virtual Canvas Math**: Lock the slide frame to `width: 1920px` and `height: 1080px` with `overflow: hidden`. Scale the active stage uniformly to the browser window using `Math.min(window.innerWidth / 1920, window.innerHeight / 1080)` via CSS custom property `--slide-scale`.
     - **Projection Typography Floors**: Set slide titles to `48px`–`72px`, section headers to `32px`–`40px`, body copy to `24px`–`28px`, and captions or badges to at least `16px`. Ensure high contrast for projector legibility from 15 feet away.
     - **Data-Driven Slide Array**: Store slide content in a structured data structure decoupled from the viewport shell.
     - **Presenter Runtime Controls**: Support keyboard navigation (`ArrowRight` or `Space` for next step or slide, `ArrowLeft` for previous), fragment step-throughs (`[data-fragment]`), toggleable Speaker Notes and Timer drawer (`N` key), Slide Overview Grid (`O` key), and Inline Text Editing (`E` key toggling `contenteditable="true"` on text nodes).
     - **Print and PDF Unrolling (`@media print`)**: Render all slides in the print DOM with standard page size rules (`1920px 1080px`, zero margin) and `break-after: page` so browser print (`Ctrl+P`) and `playwright-cli pdf` export every slide cleanly rather than printing only the first slide.

### Completion criterion
The presentation file renders a locked `1920x1080` scaled canvas, supports keyboard navigation, `N` notes drawer, `O` overview grid, `E` inline edit mode, and unrolls all slides under `@media print`.

---

## Stage 3: Declarative Vector Diagrams

Replace generic bullet card chains with true vector architecture, sequence, or workflow diagrams.

1. Reference the [`diagrams`](../diagrams/SKILL.md) skill to author and lint Mermaid definitions.
2. Validate Mermaid syntax with `mmdflux --lint`.
3. Export clean SVG using `mmdflux --format svg` or embed calibrated inline `<svg viewBox="...">` elements with explicit coordinate geometry and label sizes of at least `18px`.
4. Style diagram nodes with matching brand tokens (`--bg-card`, `--border`, `--accent`).

### Completion criterion
Every architectural flow, pipeline, or state model uses a validated SVG or Mermaid diagram that scales cleanly inside its `1920x1080` slide container.

---

## Stage 4: Closed-Loop Visual QA Gate (`playwright-cli` + `@runner`)

Validate rendered slides in headless Chromium at `1920x1080` using [`playwright-cli`](../playwright-cli/SKILL.md) or delegate verification to `@runner`:

1. Open the deck and lock the viewport:
   ```bash
   playwright-cli open file:///absolute/path/to/presentation.html
   playwright-cli resize 1920 1080
   ```

2. Run the programmatic DOM bounding-box audit across every slide (`0` to `SLIDES.length - 1`):
   ```bash
   playwright-cli eval "window.auditSlides()"
   ```
   Verify that no slide container or child card overflows (`element.scrollHeight <= element.clientHeight` and `element.scrollWidth <= element.clientWidth`) and zero console errors occurred.

3. Capture screenshots for each slide and inspect for layout defects:
   ```bash
   playwright-cli screenshot --filename=/tmp/slide-01.png
   ```
   Check for text clipping, element collisions, single-word orphan wraps, or low contrast.

4. Test PDF unrolling export:
   ```bash
   playwright-cli pdf --filename=/tmp/presentation.pdf
   ```
   Verify all slides unroll onto separate landscape pages.

5. When a slide fails overflow or visual inspection, adjust card padding, trim copy, or split the slide into two slides, then re-run the QA audit.

### Completion criterion
The verification runner confirms 0 overflowing slides across all indices at `1920x1080`, 0 console errors, verified visual balance on captured screenshots, and a working multi-page PDF export (`VERDICT: PASSED`).
