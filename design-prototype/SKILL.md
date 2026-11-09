---
name: design-prototype
description: Convert written specifications, design briefs, or design tokens into a living, code-agnostic 1:1 visual reference, interactive state simulation, and multi-skill candidate exploration in HTML/CSS/JS. Use after /to-spec or when validating UI layouts, themes, responsive behavior, and edge-case states before native framework implementation.
---

# Design Prototype: Living Visual Contract & Design System

Convert written specifications, design briefs, or design tokens into a single-file, code-agnostic 1:1 visual reference, interactive state simulation, living multi-skill candidate review harness, and formal design system catalog in vanilla HTML/CSS/JS.

Use this workflow to parallel-explore design philosophies across loaded skills (`awesome-design-md`, `frontend-design`, `design-taste-frontend`, `web-design-guidelines`), compare live candidate prototypes side-by-side, promote an approved candidate to the canonical MVP Contract, and generate the formal 1:1 Design System Specification (`docs/specs/design-system.md`) before writing production UI code in native frameworks (e.g., Jetpack Compose, React, Flutter, SwiftUI).

---

## Ubiquitous Language

- **Living Visual Contract**: The single source of visual truth embodied in `docs/design/prototype.html`. It serves as the immutable UI specification and acceptance criteria for downstream engineering.
- **Multi-Skill Candidate Exploration**: The parallel exploration workflow where all relevant design skills (`awesome-design-md`, `frontend-design`, `design-taste-frontend`, `web-design-guidelines`) are loaded simultaneously, generating distinct design prototype candidates for user evaluation.
- **Candidate Prototype**: A living visual contract reflecting the distinct visual philosophy, tokens, typography, and component styling of a specific design skill:
  - **Candidate A (`awesome-design-md`)**: Curated industry benchmark aesthetic mapped to the product domain (e.g., Linear, Apple, Stripe, Raycast).
  - **Candidate B (`frontend-design`)**: Distinctive studio visual identity (bespoke typography pairing, custom 4-6 color palette, and 1 intentional aesthetic signature).
  - **Candidate C (`design-taste-frontend`)**: Anti-slop modern utility design system (audit-verified density, crisp surface elevation, ergonomic components).
- **Candidate Review & Promotion Harness**: The dual-pane viewer and server allowing live switching and side-by-side comparison between candidates across all screens, states, and the 4-card design system catalog.
- **MVP Promotion Gate**: The explicit decision where the user selects their preferred candidate, promoting it to the canonical `docs/design/prototype.html` and locking in the 1:1 Design System Specification (`docs/specs/design-system.md`).
- **Living Design System Catalog (4-Card Inspector)**: The inspector panel embedded alongside the device simulator (`Live Color Tokens`, `WCAG 2.1 Contrast Inspector`, `Typography, Shape & Spacing Tokens`, `Component Inventory & Variants Matrix`).
- **Interactive Component Preview**: Actions (`previewComponent(screen, state)`) in the Component Inventory that automatically navigate the simulator to that screen and state.
- **1:1 Design System Specification (`docs/specs/design-system.md`)**: The formal document detailing problem statements, solution architecture, design system user stories, design token definitions across 4 themes, foundational primitives, domain components, and testing seams.
- **Design System Topology**: The architectural ownership of UI tokens and components—either **Consolidated** (shared component library / design system module like `:core:designsystem` or `@org/ui`) or **Self-Contained** (project-local styling).
- **Input Modality**: The origin source driving prototype generation:
  - `Spec-Driven`: Originates from `docs/specs/*.md` and project context.
  - `Brief-Driven`: Originates from user prompts, problem statements, or sketches.
  - `Design-Driven`: Originates from Figma specs, design tokens, or brand assets.
- **2-Tier Token Hierarchy**: Strict decoupling between primitive design values (`--color-*`, `--space-*`, `--radius-*`) and semantic design intent (`--bg`, `--surface`, `--on-surface`, `--primary`).
- **Declarative State Harness**: CSS attribute selector-driven simulation (`[data-state="populated|loading|empty|error"]`) paired with a persistent docked simulator bar and external simulator controls.
- **Section Delimitation**: Rigid ASCII comment markers separating tokens, reset rules, simulator harness, components, screens, and JavaScript logic.
- **Zero-Dependency Runner**: The bundled Python 3 script (`serve_prototype.py`) providing instantaneous local hosting with no-cache headers, candidate listing, candidate promotion, and an automated contract verification suite.

---

## Process

### Step 1: Ingest Input & Clarify Topology

Determine the input modality and project topology before authoring prototype candidates:

1. **Identify the Input Modality**:
   - **Spec-Driven**: Read the active specification in `docs/specs/*.md` and `CONTEXT.md` to extract screens, interactions, and domain models.
   - **Brief-Driven**: Extract user stories, core workflows, and visual tone from conversation or design briefs.
   - **Design-Driven**: Ingest Figma node references, exported color palettes, or token dictionaries.
2. **Clarify Design System Topology**:
   - Inspect the codebase to detect if a consolidated design system module exists (e.g., `:core:designsystem`, `packages/ui`, `src/components/common`).
   - If a consolidated library exists: Note existing components and theme conventions to reuse or map downstream.
   - If self-contained: Plan to author full semantic tokens and foundational components locally.
3. **Inventory Screens & States**:
   - List the primary screens (e.g., Overview, Detail, Settings/Editor) and ensure each will support the 4 required states: `populated`, `loading`, `empty`, and `error`.

**Completion Criterion**: Input source identified, screen inventory listed, and design system topology classified as either `Consolidated` or `Self-Contained`.

---

### Step 2: Load All Design Skills (Auto-Install Absent)

Ensure all design skills are loaded in the environment so parallel candidate generation has 100% coverage:

1. **Inspect Environment for Required Design Skills**:
   - Check availability of:
     - `awesome-design-md`: Industry benchmark design styles (Linear, Apple, Stripe, Vercel, Raycast, Cursor, etc.).
     - `frontend-design`: Distinctive visual identity guidelines (bespoke typography pairing, 4-6 color palettes, 1 intentional aesthetic signature).
     - `design-taste-frontend`: Anti-slop frontend principles and audit-first preflight checks.
     - `web-design-guidelines`: Web interface guidelines, touch targets, accessibility standards, and contrast compliance.
2. **Auto-Install Any Absent Skills**:
   - If ANY of these skills are absent, install or add them immediately before proceeding:
     - Use the `find-skills` skill or run `npx skills add <skill-name>` / install from the agent skills ecosystem.
     - Ensure the skill instructions and references are loaded into context.
     - Do not proceed with generic single-aesthetic fallback code when all 4 design skills can be loaded.

**Completion Criterion**: All 4 design skills verified loaded in the environment and ready for multi-candidate generation.

---

### Step 3: Generate Multi-Skill Prototype Candidates

Scaffold and generate 3 distinct candidate design directions corresponding to the loaded design skills:

1. **Scaffold the Dual-Pane Workspace & Runner**:
   - If missing, bootstrap the prototype structure into `docs/design/`:
     ```bash
     python3 /home/pedrogoncalves/.agents/skills/design-prototype/scripts/bootstrap.py --target-dir .
     ```
   - Ensure `docs/design/prototype.html` and `docs/design/serve_prototype.py` exist with executable permissions (`chmod +x docs/design/serve_prototype.py`).
2. **Produce 3 Distinct Candidate Design Directions**:
   - **Candidate A (`awesome-design-md`)**: Industry-leading benchmark aesthetic mapped to the product domain (e.g. Linear dark tech, Apple minimalist warmth, Stripe precision, or Raycast command center).
   - **Candidate B (`frontend-design`)**: Bespoke studio identity with custom typography pairings (e.g. Plus Jakarta Sans / Newsreader), handcrafted 4-6 color palettes (terracotta, sage, warm paper), and 1 intentional aesthetic signature.
   - **Candidate C (`design-taste-frontend`)**: Anti-slop modern utility design system with audit-verified density, crisp surface elevation, and electric indigo/cyan accents.
3. **Candidate Structure**:
   - Candidates can be authored either:
     - **Option 1 (Unified Interactive Harness)**: Embedded within `docs/design/prototype.html` switchable via `data-candidate="awesome|frontend|taste"`, complete with candidate CSS variables and JavaScript token sets.
     - **Option 2 (Standalone Candidate Files)**: Under `docs/design/candidates/prototype-awesome.html`, `docs/design/candidates/prototype-frontend.html`, and `docs/design/candidates/prototype-taste.html`.
4. **Architectural Invariants Across All Candidates**:
   - **2-Tier Token Hierarchy**: Under `/* === SECTION: TOKENS: PRIMITIVES === */` and `/* === SECTION: TOKENS: SEMANTIC === */`, provide complete coverage for all 4 required themes (`warm_dark`, `light`, `dark`, `sepia`) with mandatory core tokens `--bg`, `--surface`, `--on-surface`, `--primary`.
   - **Living Design System Catalog (4-Card Inspector)**: Live Color Tokens, WCAG 2.1 Contrast Inspector, Typography/Shape/Spacing Tokens, and Component Inventory with `previewComponent(screen, state)` triggers.
   - **Interactive Device Simulator**: Mobile/desktop hardware frame with status bar, top app bar, viewport with screen navigation, and declarative state toggling.
   - **Declarative State Harness**: Attribute-driven branches (`.state-view-populated`, `.state-view-loading`, `.state-view-empty`, `.state-view-error`).

**Completion Criterion**: 3 distinct candidate prototypes generated and integrated into the review harness.

---

### Step 4: Serve Multi-Candidate Review Harness

Launch the review harness to allow dynamic switching and inspection across all candidates:

1. **Launch the Server**:
   ```bash
   python3 docs/design/serve_prototype.py --open
   ```
2. **Review Harness Capabilities**:
   - Header provides the **Candidate Switcher Pill Group**:
     - `[★ Candidate A: awesome-design-md (Industry Benchmark)]`
     - `[Candidate B: frontend-design (Bespoke Studio)]`
     - `[Candidate C: design-taste-frontend (Anti-Slop Modern)]`
   - Switching candidates dynamically updates:
     - Device simulator styling, typography, corner radii, and color accents.
     - 4-Card Design System Catalog: Live Color Tokens swatches and WCAG 2.1 Contrast validation table.
   - Theme Switcher allows testing all candidates across all 4 themes (`warm_dark`, `light`, `dark`, `sepia`).
   - State Simulator allows validating populated, loading shimmer, empty illustration, and error retry states.

**Completion Criterion**: Prototype served locally, allowing fluid real-time candidate switching and inspection.

---

### Step 5: User Candidate Evaluation & MVP Decision

Facilitate the candidate evaluation with the user:

1. **Present the Multi-Skill Candidates**:
   - Summarize the 3 candidates with their visual philosophy, typography pairing, aesthetic signature, and contrast scores:
     - **Candidate A (`awesome-design-md`)**: Industry benchmark alignment, domain ergonomics.
     - **Candidate B (`frontend-design`)**: Studio identity, distinctive palette, bespoke personality.
     - **Candidate C (`design-taste-frontend`)**: High-density utility, crisp elevation, modern precision.
2. **Gather Feedback & Selection**:
   - Allow user to toggle candidates in-browser or ask via conversational response / `ask_question`.
   - Guide the user to confirm their preferred candidate for the Minimum Viable Product (MVP).

**Completion Criterion**: User evaluates candidates and selects the winning design for the MVP.

---

### Step 6: Promote Selected Candidate to MVP Contract

Lock in the winning candidate as the canonical MVP visual contract:

1. **Promote the Candidate**:
   - **In-Browser**: Click the `[★ Set as MVP]` button in the prototype header. This marks the candidate as MVP, updates the header badge, saves the preference to `localStorage`, and displays a confirmation toast.
   - **Or via CLI**:
     ```bash
     python3 docs/design/serve_prototype.py --promote <candidate_name>
     ```
     (e.g., `python3 docs/design/serve_prototype.py --promote frontend` or `awesome` or `taste`). This copies/locks the selected candidate into `docs/design/prototype.html`.
2. **Generate / Update 1:1 Design System Specification (`docs/specs/design-system.md`)**:
   - Author or synchronize `docs/specs/design-system.md` with the selected MVP candidate:
     - **1. Problem Statement**: Deficiencies of fragmented UI, theme parity gaps, or visual inconsistency.
     - **2. Solution & Architecture**: 2-tier token system, 4 theme palettes, foundational primitives, domain components, and the living prototype contract.
     - **3. Design System User Stories**: Stories covering theme switching, accessibility contrast, navigation, and state feedback.
     - **4. Design Token System Definitions**:
       - Selected candidate's palette definitions across `Warm Dark`, `Light`, `Dark`, and `Sepia`.
       - Semantic token mapping table (`--bg`, `--surface`, `--on-surface`, `--primary`, etc.).
       - Typography scale, spacing tokens, and corner radius hierarchy.
     - **5. Foundational Primitives Catalog (10+ Components)**: Top app bar, bottom nav, action buttons, badges, chips, tabs, search pills, state feedback views, surface cards, bottom sheets/dialogs.
     - **6. Domain Components Catalog**: Specification of composed domain patterns with variants and states.
     - **7. Testing Seams**: UI semantics, test tags (`Modifier.testTag` or `data-testid`), and ViewModel state derivation contracts.

**Completion Criterion**: Canonical MVP contract confirmed at `docs/design/prototype.html` and 1:1 Design System Specification authored at `docs/specs/design-system.md`.

---

### Step 7: Verify MVP Contract (`serve_prototype.py --check`)

Validate that the canonical MVP contract satisfies all architectural invariants:

1. Run the contract verification suite:
   ```bash
   python3 docs/design/serve_prototype.py --check
   ```
2. Verify all verification checks pass:
   - `[PASS] File check`: File exists and has non-zero size.
   - `[PASS] Section delimitation`: All 8 rigid ASCII section markers present.
   - `[PASS] Themes verified`: All 4 themes (`warm_dark`, `light`, `dark`, `sepia`) detected.
   - `[PASS] Semantic token pairs verified`: Core tokens (`--bg`, `--surface`, `--on-surface`, `--primary`) complete across all themes.
   - `[PASS] Declarative State Harness`: All 4 states (`populated`, `loading`, `empty`, `error`) wired and verified.
   - Output terminates with `[VERDICT: PASSED]`.

**Completion Criterion**: `serve_prototype.py --check` exits with return code 0 and outputs `[VERDICT: PASSED]`.

---

### Step 8: Downstream Handoff (`/to-tickets`)

Prepare the canonical visual contract and design system specification for implementation:

1. **Topology Alignment**:
   - If **Self-Contained**: Ensure feature specs (`docs/specs/*.md`) and implementation tasks cite exact prototype DOM IDs, token names, and CSS classes.
   - If **Consolidated Library**: Map prototype components to existing design system primitives in `:core:designsystem` or `@org/ui`, noting any new tokens or components needed.
2. **Anchor for Implementation Tickets (`/to-tickets`)**:
   - Cross-link specific screen anchors (e.g., `#screen-overview`, `#screen-detail`) and component preview triggers directly into engineering tasks.
   - Reference `docs/design/prototype.html` and `docs/specs/design-system.md` as the authoritative visual acceptance criteria.

**Completion Criterion**: Feature specification and engineering backlog contain direct references and anchors to `docs/design/prototype.html` and `docs/specs/design-system.md`.
