# Stakeholder PowerPoint Pipeline (.pptx)

This guide documents the creation of native, editable PowerPoint (`.pptx`) decks using structured specifications and deterministic compilation scripts.

## Core Architecture

Direct text generation of coordinate values leads to misalignment and clipped copy. Avoid writing raw geometry directly in conversational turns.

Use a two-step compilation model:
1. Generate an intermediate slide specification file (`slides-spec.json`).
2. Run a deterministic Python builder script with `python-pptx` to generate `presentation.pptx`.

## 16:9 Widescreen Setup

Configure the presentation canvas to true 16:9 widescreen dimensions (`13.333 x 7.5` inches):

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]
```

## Deterministic Builder Implementation

Save this script as `build_deck.py`:

```python
import json
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

BG_COLOR = RGBColor(9, 10, 15)
SURFACE_COLOR = RGBColor(18, 20, 28)
TEXT_PRIMARY = RGBColor(241, 245, 249)
TEXT_MUTED = RGBColor(148, 163, 184)
ACCENT_COLOR = RGBColor(56, 189, 248)

def build_presentation(spec_path, output_path):
    with open(spec_path, 'r', encoding='utf-8') as f:
        deck_spec = json.load(f)

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    for slide_data in deck_spec.get('slides', []):
        slide = prs.slides.add_slide(blank_layout)

        # Background fill
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = BG_COLOR

        # Kicker and Action Title
        kicker_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.6), Inches(11.7), Inches(0.4))
        ktf = kicker_box.text_frame
        ktf.word_wrap = True
        kp = ktf.paragraphs[0]
        kp.text = slide_data.get('kicker', '').upper()
        kp.font.size = Pt(14)
        kp.font.bold = True
        kp.font.color.rgb = ACCENT_COLOR

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.0), Inches(11.7), Inches(1.1))
        ttf = title_box.text_frame
        ttf.word_wrap = True
        tp = ttf.paragraphs[0]
        tp.text = slide_data.get('title', '')
        tp.font.size = Pt(36)
        tp.font.bold = True
        tp.font.color.rgb = TEXT_PRIMARY

        # Archetype rendering
        archetype = slide_data.get('archetype', 'three-pillar')
        cards = slide_data.get('cards', [])

        if archetype == 'three-pillar' and len(cards) >= 3:
            card_width = Inches(3.64)
            card_gap = Inches(0.39)
            top_pos = Inches(2.4)
            card_height = Inches(4.3)

            for idx, card in enumerate(cards[:3]):
                left_pos = Inches(0.8) + idx * (card_width + card_gap)
                shape = slide.shapes.add_shape(1, left_pos, top_pos, card_width, card_height) # msoShapeRectangle = 1
                shape.fill.solid()
                shape.fill.fore_color.rgb = SURFACE_COLOR
                shape.line.color.rgb = RGBColor(36, 41, 56)

                ctf = shape.text_frame
                ctf.word_wrap = True
                ctf.margin_left = Inches(0.3)
                ctf.margin_right = Inches(0.3)
                ctf.margin_top = Inches(0.3)

                p1 = ctf.paragraphs[0]
                p1.text = card.get('title', '')
                p1.font.size = Pt(20)
                p1.font.bold = True
                p1.font.color.rgb = TEXT_PRIMARY

                p2 = ctf.add_paragraph()
                p2.text = card.get('body', '')
                p2.font.size = Pt(16)
                p2.font.color.rgb = TEXT_MUTED

        # Speaker notes injection
        notes_text = slide_data.get('notes', '')
        if notes_text:
            notes_slide = slide.notes_slide
            notes_tf = notes_slide.notes_text_frame
            notes_tf.text = notes_text

    prs.save(output_path)

if __name__ == '__main__':
    spec_file = sys.argv[1] if len(sys.argv) > 1 else 'slides-spec.json'
    out_file = sys.argv[2] if len(sys.argv) > 2 else 'presentation.pptx'
    build_presentation(spec_file, out_file)
```

## Specification File Format (`slides-spec.json`)

Define slide content in a clean JSON structure:

```json
{
  "title": "Deterministic Engineering Workflows",
  "slides": [
    {
      "id": "intro",
      "archetype": "three-pillar",
      "kicker": "Strategy Alignment",
      "title": "Verified Automation Increases Engineering Throughput",
      "cards": [
        {
          "title": "Continuous Scoping",
          "body": "Bound agent edits to specific files with automated diff auditing."
        },
        {
          "title": "Closed-Loop Gates",
          "body": "Execute test suites and browser audits before task sign-off."
        },
        {
          "title": "Modular Templates",
          "body": "Standardize presentation layouts across engineering and executive reviews."
        }
      ],
      "notes": "Stress the business value of closed-loop verification gates across departments."
    }
  ]
}
```

## Closed-Loop Visual QA Gate for PPTX

Always inspect generated `.pptx` slides visually before delivering them to users.

Convert the `.pptx` file to images and review the rendering:

```bash
# Convert presentation to PDF using headless LibreOffice
soffice --headless --convert-to pdf presentation.pptx

# Render PDF pages to high-resolution PNG images
pdftoppm -png -r 150 presentation.pdf /tmp/pptx-slide

# Verify individual slides for text clipping or overlapping boxes
ls -l /tmp/pptx-slide-*.png
```

Check the rendered PNG files for:
- Text wrapping past shape boundaries
- Unintended line breaks in card titles
- High-contrast readability across slide backgrounds
- Correct placement of speaker notes in the presentation file
