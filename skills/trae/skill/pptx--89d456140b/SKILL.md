---
name: pptx
description: Create and edit presentation slide decks (`.pptx`) with PptxGenJS, bundled layout helpers, and render/validation utilities. Use when tasks involve building a new PowerPoint deck, recreating slides from screenshots/PDFs/reference decks, modifying slide content while preserving editable output, adding charts/diagrams/visuals, or diagnosing layout issues such as overflow, overlaps, and font substitution.
supported_os:
  - macos
  - linux
---

# PPTX

## Overview

Use PptxGenJS for slide authoring. Do not use `python-pptx` for deck generation unless the task is inspection-only; keep editable output in JavaScript and deliver the `.pptx`.

Keep work in a task-local directory. Only copy final artifacts to the requested destination after rendering and validation pass.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python3 -m markitdown presentation.pptx` |
| Edit or create from template | Must Read [editing.md](editing.md) |
| Generate design system | Plan content first, then `python3 skills/pptx/scripts/design/search.py "<content-derived keywords>" --design-system` |
| Recreate slides from screenshots/PDFs | Render source → Match aspect ratio → Rebuild with PptxGenJS → Validate |
| Visual assets (charts, diagrams, illustrations, etc.) | Read [image-generation.md](image-generation.md) |
| Render & validate | `python3 scripts/render_slides.py deck.pptx` + `python3 scripts/slides_test.py deck.pptx` |
| Build montage for quick scan | `python3 scripts/create_montage.py --input_dir rendered --output_file montage.png` |

## Visual & Image Work (MANDATORY)

**Any task involving charts, diagrams, illustrations, or other visual assets — whether pre-generated or created inline — MUST follow the guidelines in [image-generation.md](image-generation.md).** For illustrations, backgrounds, and hero images, prefer **GenerateImage** (Option B in that guide). Always consult that document for color consistency, naming conventions, rendering workflows, and tool selection.

## Bundled Resources

- `assets/pptxgenjs_helpers/`: Copy this folder into the deck workspace and import it locally instead of reimplementing helper logic.
- `scripts/render_slides.py`: Rasterize a `.pptx` or `.pdf` to per-slide PNGs.
- `scripts/slides_test.py`: Detect content that overflows the slide canvas.
- `scripts/create_montage.py`: Build a contact-sheet style montage of rendered slides.
- `scripts/detect_font.py`: Report missing or substituted fonts as LibreOffice resolves them.
- `scripts/ensure_raster_image.py`: Convert SVG/EMF/HEIC/PDF-like assets into PNGs for quick inspection.
- `scripts/render_plantuml.py`: Render PlantUML diagrams to PNG with syntax error parsing and Gantt-safe DPI handling.
- `scripts/render_graphviz.py`: Render Graphviz diagrams to PNG with syntax error parsing and auto size injection.
- `scripts/unpack.py`: Extract and pretty-print PPTX for template-based editing.
- `scripts/add_slide.py`: Duplicate a slide or create from layout.
- `scripts/clean.py`: Remove orphaned slides, media, and rels from unpacked directory.
- `scripts/pack.py`: Repack unpacked directory into PPTX with validation and auto-repair.
- `scripts/thumbnail.py`: Create visual grid of slide thumbnails for template analysis.
- `references/pptxgenjs-helpers.md`: Load only when you need API details or dependency notes.

## Workflow

Inspect the request and determine which path to follow:

| Situation | Go to |
|-----------|-------|
| No template or reference deck | [Creating from Scratch](#creating-from-scratch) |
| Editing an existing `.pptx` using it as a template | [editing.md](editing.md) (Template-Based Workflow) |
| Recreating from screenshots/PDFs/reference decks | [Recreate Existing Slides](#recreate-existing-slides) |

---

## Creating from Scratch

Use when no template or reference presentation is available.

### Required Slide Structure

You MUST follow this structure:

1. Slide 1: Cover page
2. Slide 2: Table of contents (agenda)
3. Slide 3 onward: Content sections in the exact order listed on Slide 2
4. Final slide: Closing/thank-you page

Do not skip the table of contents slide. Do not place content slides before the table of contents.

### Steps
1. **Set slide size**: Default to 16:9 (`LAYOUT_WIDE`) unless the source material clearly uses another aspect ratio.
2. **Plan content first**: Complete [Step 1: Draft the Content Plan](#step-1-draft-the-content-plan) in the [Pre-Generation Planning](#pre-generation-planning-required) section below — define the narrative arc, per-slide content summaries, and visual element inventory. Write the result to a `plan.md` file.
3. **Match design to content**: With the content plan in hand, complete [Step 2: Match Design System to Content](#step-2-match-design-system-to-content) — run `search.py --design-system` using content-derived keywords, then enrich `plan.md` with the color palette, typography, and style tokens.
4. **Pre-generate assets**: For figures marked `[External]` or `[GenerateImage]` in the plan, generate them BEFORE writing PptxGenJS code. Read [image-generation.md](image-generation.md) for full details. ⚠️ **Ignore watermarks on images.** Watermarks in images do NOT need to be removed or addressed.
5. **Copy helpers**: Copy `assets/pptxgenjs_helpers/` into the working directory and import the helpers from there.
6. **Build the deck**: Write the deck in JavaScript with an explicit theme font and stable spacing. Don't create boring slides. Plain bullets on a white background won't impress anyone.
7. **Render & review**: Run `render_slides.py`, review the PNGs, and run `slides_test.py` for overflow checks. Fix all issues before delivery. See [Validation Commands](#validation-commands).
8. **Deliver**: Deliver the `.pptx`.

---

### Pre-Generation Planning (Required)

**Before writing any code, you MUST complete these planning steps and write the result to a `plan.md` file in the working directory.**

⛔ **NEVER ask the user how many slides they want.** Slide count is determined by content, not by an upfront number. Derive it during planning using the density rules below.

#### Slide Count Rules

Good slides breathe. The number of slides follows from the content — not the other way around. Apply this principle when building the slide-by-slide outline:

**One core message per slide.** If you cannot summarize a slide's point in one sentence, split it. Prefer more slides with focused content over fewer slides crammed with text.

**Fixed overhead:** Cover (1) + Table of Contents (1) + Closing (1) = 3 slides minimum before any content.

**If the user explicitly requests a specific slide count**, respect it but flag in plan.md which content is compressed and at risk of overflow. Prefer splitting over cramming.

#### Step 1: Draft the Content Plan

**Content comes first. Design follows content.** Draft the full narrative and per-slide content before choosing any visual style. This ensures the design system is matched to what the slides actually say, not to a generic topic keyword.

The plan.md must begin with these content sections:

##### 1. Narrative Arc (Title Sequence)

A numbered table of every slide. Each row contains the slide's **title** (the actual text shown on the slide), its **role** in the storyline, a brief **content summary** (key points, data, or message on this slide), and the **visual** element planned for it (e.g. GenerateImage background, chart, diagram, shapes-only, or none).

```
| # | Title | Role | Content Summary | Visual |
|---|-------|------|-----------------|--------|
| 1 | ...   | Cover | ...            | ...    |
| 2 | ...   | TOC   | ...            | ...    |
| 3 | ...   | ...   | ...            | ...    |
| … | ...   | ...   | ...            | ...    |
```

End with: *"Reading only the titles, you can follow the whole story."* — if you cannot, revise the titles.

The **Content Summary** column is critical — it will be used in the next step to derive the best design keywords for the design system search.

##### 2. Visual Elements Inventory

List all images, icons, charts, and diagrams needed. Mark each with a source tag:

- `[Built-in]` — PptxGenJS shapes or native charts
- `[GenerateImage]` — AI-generated via GenerateImage (illustrations, backgrounds, hero images, conceptual visuals)
- `[External]` — Pre-generated with Matplotlib, PlantUML, Graphviz, or downloaded via web search

```
| Element | Type | Source |
|---------|------|--------|
| ...     | ...  | ...    |
```

##### 3. Content-Derived Design Keywords

Before calling the design system, extract **English keywords** from the content plan that capture:
- The **domain/industry** (e.g. "fintech", "healthcare", "developer tools")
- The **mood/tone** (e.g. "professional", "playful", "technical")
- The **dominant content types** (e.g. "data-heavy", "storytelling", "comparison")

These keywords will be used as the search query in Step 2.

#### Step 2: Match Design System to Content

Now that you know what every slide contains, use the content-derived keywords to find the best design system.

Run: `python3 skills/pptx/scripts/design/search.py "<content-derived keywords>" --design-system`

⚠️ IMPORTANT: Always use **English keywords** for search queries. The design system database contains English keywords only. Using non-English queries will result in poor matches and default/boring designs.

The command outputs a complete design system including:

- **PATTERN** — page layout archetype and section order (Hero → Features → CTA, etc.)
- **STYLE** — visual language (e.g. *Exaggerated Minimalism*, *Glass Morphism*)
- **COLORS** — Primary, Secondary, CTA, Background, Text tokens with hex values
- **TYPOGRAPHY** — a font pairing with mood tags and a Google Fonts share link
- **KEY EFFECTS** — signature CSS/layout techniques to carry the style
- **AVOID** — anti-patterns to steer clear of
- **PRE-DELIVERY CHECKLIST** — accessibility and interaction quality gates

Keep overrides minimal — the tool's recommendations are pre-validated for contrast and harmony.

**Optionally**, if slides have very different content types (e.g. a data-heavy analytics slide vs. a storytelling narrative slide), run additional searches with `--page` for per-page style overrides:

```bash
python3 skills/pptx/scripts/design/search.py "<page-specific keywords>" --design-system --persist --page "<page-name>"
```

Now enrich plan.md with the design system output:

##### 4. Overall Theme & Style

Summarize the design system's PATTERN, STYLE, and KEY EFFECTS into a concise description of the deck's visual identity: layout archetype, visual language, and the motif to carry across slides.

##### 5. Color Palette

Transcribe the design system's COLORS into **named tokens**. Include the token name, hex value, and where it is used. After the table, briefly explain the relationship between accent colors (e.g. shared chroma, complementary hues) so the palette feels intentional.

⚠️ NEVER use `#` prefix with hex colors in PptxGenJS code — causes file corruption. Strip the `#` when transcribing: use `"1E1B4B"` not `"#1E1B4B"`.

```
| Token | Value | Usage |
|-------|-------|-------|
| ...   | ...   | ...   |
```

##### 6. Type Scale

Transcribe the design system's TYPOGRAPHY into a font hierarchy. Use serif for authority/warmth and sans-serif for legibility.

```
| Name | Font | Usage |
|------|------|-------|
| ...  | ...  | ...   |
```

#### Step 3: Pre-Generate External Assets

For figures marked `[External]` or `[GenerateImage]`, generate them BEFORE writing PptxGenJS code. Read [image-generation.md](image-generation.md) for detailed guidance on GenerateImage, Matplotlib charts, web search images, PlantUML diagrams, and Graphviz diagrams.

⚠️ **CRITICAL: Color Consistency** — All generated assets MUST use the same color palette defined in the design system.

---

## Authoring Rules

- Set theme fonts explicitly. Do not rely on PowerPoint defaults if typography matters.
- Use `autoFontSize`, `calcTextBox`, and related helpers to size text boxes; do not use PptxGenJS `fit` or `autoFit`.
- Use bullet options, not literal `•` characters (creates double bullets).
- Use `imageSizingCrop` or `imageSizingContain` instead of PptxGenJS built-in image sizing.
- Use `latexToSvgDataUri()` for equations and `codeToRuns()` for syntax-highlighted code blocks.
- Prefer native PowerPoint charts for simple bar/line/pie/histogram style visuals so reviewers can edit them later.
- For charts or diagrams that PptxGenJS cannot express well, render SVG externally and place the SVG in the slide.
- Include both `warnIfSlideHasOverlaps(slide, pptx)` and `warnIfSlideElementsOutOfBounds(slide, pptx)` in the submitted JavaScript whenever you generate or substantially edit slides.
- Fix all unintentional overlap and out-of-bounds warnings before delivering. If an overlap is intentional, leave a short code comment near the relevant element.
- NEVER use `#` prefix with hex colors — causes file corruption. Use `"FF0000"` not `"#FF0000"`.
- Use `breakLine: true` between array items in rich text; without it, runs merge onto one line.
- Avoid `lineSpacing` with bullets — causes excessive gaps; use `paraSpaceAfter` instead.
- Each presentation needs a fresh `pptxgen()` instance — do not reuse across decks.
- NEVER hard-code `fontSize` for variable-length text without overflow protection — use `autoFontSize(..., { mode: "shrink" })`.
- Text boxes have internal margin by default. Set `margin: 0` when you need text to align precisely with shapes, lines, or icons at the same x-position.

---

## Recreate Existing Slides

Use when recreating from screenshots/PDFs/reference decks using PptxGenJS.

1. **Render the source**: Rasterize the source deck or reference PDF with `render_slides.py` so you can compare slide geometry visually.
2. **Match aspect ratio**: Set the slide size to match the original before rebuilding layout.
3. **Copy helpers**: Copy `assets/pptxgenjs_helpers/` into the working directory and import the helpers from there.
4. **Rebuild / edit**: Preserve editability where possible — text should stay text, and simple charts should stay native charts. If a reference slide uses raster artwork, use `ensure_raster_image.py` to generate debug PNGs from vector or odd image formats before placing them.
5. **Render & review**: Run `render_slides.py`, review the PNGs, and run `slides_test.py` for overflow checks. Fix all issues before delivery. See [Validation Commands](#validation-commands).
6. **Deliver**: Deliver the `.pptx`.

## Validation Commands

Examples below assume you copied the needed scripts into the working directory. If not, invoke the same script paths relative to this skill folder.

```bash
# Render slides to PNGs for review
python3 scripts/render_slides.py deck.pptx --output_dir rendered

# Build a montage for quick scanning
python3 scripts/create_montage.py --input_dir rendered --output_file montage.png

# Check for overflow beyond the original slide canvas
python3 scripts/slides_test.py deck.pptx

# Detect missing or substituted fonts
python3 scripts/detect_font.py deck.pptx --json
```

Load `references/pptxgenjs-helpers.md` if you need the helper API summary or dependency details.

---

## Dependencies

> All dependencies mentioned below are pre-installed, use them directly.

- `markitdown[pptx]` - text extraction (used in editing workflow for content QA)
- `Pillow` - thumbnail grids
- `pptxgenjs` - creating from scratch
- LibreOffice (`soffice`) - PDF conversion
- Poppler (`pdftoppm`) - PDF to images
- `pdf2image` - used by render scripts
- `python-pptx` - used by validation scripts (inspection only)
- `skia-canvas`, `linebreak`, `fontkit` - text measurement helpers
- `prismjs` - syntax highlighting
- `mathjax-full` - LaTeX rendering
- `defusedxml` - safe XML parsing (used by editing scripts)
