---
name: pptx
description: "Presentation creation, editing, and analysis. When you need to work with presentations (.pptx files) for: (1) Creating new presentations, (2) Modifying or editing content, (3) Working with layouts, (4) Adding comments or speaker notes, or any other presentation tasks"
license: Proprietary. LICENSE.txt has complete terms
supported_os:
  - macos
  - linux
---

# PPTX Skill

## ⚠️ Completion Checklist (MANDATORY)

Before declaring any PPTX task complete, **all** of the following must be done:

- [ ] **Content QA**: `python3 -m markitdown output.pptx` — check text content, order, typos
- [ ] **Post-generation fix**: `python3 scripts/fix_pptx.py output.pptx`
- [ ] **Layout QA**: `python3 scripts/validate_layout.py output.pptx` — fix all issues
- [ ] **Fix-and-verify cycle**: fix issues → re-run checks → repeat until clean
- [ ] **Background image text check**: Examine each background image yourself — does it contain any clearly readable text in the main content area? (Ignore small watermarks in corners/edges.) Regenerate any that do.
- [ ] **Hero/Card image text check**: Examine each Image-Hero and Image-Card — does it contain any clearly readable text? Regenerate any that do.

## Quick Reference

| Task | Guide |
|------|-------|
| Read/analyze content | `python3 -m markitdown presentation.pptx` |
| Edit or create from template | Read [editing.md](editing.md) — QA: `validate_layout.py` + `markitdown` |
| Create from scratch | 1. Plan content → 2. Pre-generate assets → 3. Read [pptxgenjs.md](pptxgenjs.md) |
| Prevent overflow by design | Read [pptxgenjs.md](pptxgenjs.md#layout-safety-prevent-overflow-before-qa) |
| Generate design system | `python3 skills/pptx/scripts/design/search.py "<topic>" --design-system` |
| **Post-generation fix** | `python3 scripts/fix_pptx.py output.pptx` |
| **Layout QA (critical first)** | `python3 scripts/validate_layout.py presentation.pptx` |

---

## Reading Content

```bash
# Text extraction
python3 -m markitdown presentation.pptx

# Raw XML
python3 scripts/unpack.py presentation.pptx unpacked/
```

---

## Editing Workflow

**Read [editing.md](editing.md) for full details.**

1. Analyze template with `markitdown`
2. **Classify slides** — identify usable layouts vs. design reference pages (font specs, color swatches, icon libraries). Skip design reference slides.
3. Unpack + style-layer check + Theme & Style alignment plan
4. **Measure text box constraints** — read the XML to get each text box's width, height, and font size. Calculate max content length before writing.
5. Manipulate slides → edit content → clean → pack
6. **⚠️ Layout QA (mandatory gate)**: `python3 scripts/fix_pptx.py output.pptx` → `python3 scripts/validate_layout.py output.pptx --slides <edited_slide_numbers>`
7. **⚠️ Content QA (mandatory)**: `python3 -m markitdown output.pptx`

---

## Creating from Scratch

**Read [pptxgenjs.md](pptxgenjs.md) for full details.**

Use when no template or reference presentation is available.

---

## Style Discovery

Before designing slides, ask the user what visual style they want. The style choice drives color palette, layout density, and — critically — how much imagery to use.

| Style | Character | Image Strategy |
|-------|-----------|----------------|
| **Minimalist** | Clean, spacious, typography-driven. Whitespace is the hero. | Rarely use images. Rely on shapes, icons, and whitespace. Only add an image when it directly illustrates a key point (1-2 per deck max). |
| **Tech / Futuristic** | Dark backgrounds, geometric accents, modern. | Generated abstract or digital backgrounds for title/section slides. Content slides use shapes and icons, not stock photos. |
| **Business / Corporate** | Professional, structured, credible. | Stock photos on key slides (title, section dividers) — roughly 30-40% of slides. Most content slides use clean layouts with icons. |
| **Creative / Bold** | Eye-catching, expressive, strong imagery. | Heavy use of full-bleed photos and illustrations. Most slides (60-80%) benefit from visual elements. Mix search and generation. |
| **Academic / Technical** | Data-focused, structured, understated. | Charts and diagrams only. Decorative stock photos are distracting — skip them. |

If the user doesn't specify a style, infer from context (startup pitch → Business or Creative, research report → Academic, product launch → Tech or Creative). When genuinely unclear, ask — a one-sentence question is enough: "What visual style are you after — minimalist, corporate, techy, something bold, or more academic?"

---

## ⚠️ REQUIRED: Pre-Generation Planning

**Before writing any code, you MUST complete these planning steps:**

### Step 1: Output Content Design Plan

Present a structured plan covering:

1. **Overall Theme & Style**
   - Color palette choice (reference "Design Ideas" section)
   - Typography pairing
   - Visual motif to carry across slides

2. **Slide-by-Slide Outline**
   ```
   Slide 1: Cover - Layout type, key elements
   Slide 2: Table of contents - Ordered section list
   Slide 3: [Section 1 from TOC] - Layout type, key elements, insight plan (if visual)
   ...
   Slide N: Closing / Thank You - Layout type, key elements
   ...
   ```

3. **Visual Elements Inventory**
   - List all images, icons, charts, and diagrams needed
   - Mark each as: `[Built-in]` (pptxgenjs shapes/charts) or `[External]` (needs pre-generation)

**Example planning output:**
```markdown
## Presentation Plan

**Theme:** Ocean Gradient palette (065A82, 1C7293, 21295C)
**Fonts:** Georgia (headings) + Calibri (body)
**Motif:** Rounded cards with left accent border

### Slides:
1. Cover Slide - Centered title, gradient background [Image: bg-cover]
2. Table of Contents - Overview / Architecture / Metrics / Timeline [No Image]
3. [Section 1 from TOC] - Layout type, key elements [Image: illustration of architecture]
...
n. Thank You - Closing statement + contact [Image: bg-closing]
```

### Step 2: Pre-Generate External Assets

For figures marked `[External]`, generate them BEFORE writing pptxgenjs code.

**⚠️ Minimum Image Count (mandatory)**

Generate at least **2 images per 3 content slides**. For a 12-slide deck (10 content slides), that means at least **7-8 images** minimum (cover/closing backgrounds + Image-Hero + Image-Card illustrations). Prefer embedding images inside cards (Image-Card) over standalone elements when the layout calls for it.

**⚠️ CRITICAL: Color Consistency**

All generated diagrams and charts MUST use the same color palette as the presentation. Define colors at the top of your generation script based on your chosen theme.

**Option A: Native Shapes/Charts First (REQUIRED default)**

ALL architecture diagrams, flowcharts, process diagrams, org charts, and relationship diagrams MUST be built with pptxgenjs native shapes. See [pptxgenjs.md — Building Diagrams with Native Shapes](pptxgenjs.md#building-diagrams-with-native-shapes) for patterns and examples.

Only fall back to matplotlib for complex statistical charts that pptxgenjs charts cannot handle.
Only fall back to Mermaid when the diagram is too complex for native shapes AND involves many cross-links.

**Option B: GenerateImage (preferred for illustrations/backgrounds)**

Use GenerateImage to generate slide images directly — do not use WebSearch to find images online (search results are unreliable and often low-quality).

- Write a detailed, specific prompt for each image describing the desired scene, style, color tones, and mood
- Choose the right `image_size` enum for the target aspect ratio:
  - `landscape_16_9` for 16:9 (full-slide backgrounds, wide layouts)
  - `landscape_4_3` for 4:3 (content area illustrations)
  - `square` for 1:1 (headshots, profile images, square icons)
  - `portrait_4_3` for 3:4 portrait orientation
  - `portrait_16_9` for 9:16 tall portrait orientation
- **⚠️ When embedding images in PPT, the target `w` and `h` MUST match the image's aspect ratio.** For example, a `landscape_4_3` image must be placed in a 4:3 target area (e.g., `w: 4, h: 3`), NOT a 1:1 area. See [pptxgenjs.md — How to Use Images](pptxgenjs.md#how-to-use-images-aspect-ratio-preserved) for the ratio mapping table.
- Include color guidance in prompts to match the slide palette
- **NEVER include text or letters in ANY generated image** — this applies to ALL image types (Image-BG, Image-Hero, Image-Card). Explicitly add "no text, no letters, no words, no numbers" to every image generation prompt. Use PptxGenJS text elements instead.
- **Filename MUST include ratio suffix** matching the `image_size` enum used:
  - `landscape_16_9` → `_16x9` suffix
  - `landscape_4_3` → `_4x3` suffix
  - `square` → `_1x1` suffix
  - `portrait_4_3` → `_3x4` suffix
  - `portrait_16_9` → `_9x16` suffix
- **Background images MUST use `bg-` filename prefix**: e.g. `bg-cover_16x9.png`, `bg-section_16x9.png`
- Save to `<output-dir>/images/` as `{descriptive-name}_{ratio}.png`, e.g. `bg-cover_16x9.png`, `image-solution_4x3.png`, `image-team_1x1.png`

**⚠️ Background image text verification (MANDATORY — DO NOT SKIP):**

After generating each background image, **examine the image yourself** and answer:
"Does this background image contain any clearly readable text in the main content area?"

- **Ignore** small watermarks in corners/edges — these do not count
- If text IS visible: regenerate with stronger negative prompt — add "absolutely no text, no letters, no words, no numbers, no characters, no writing, no typography, no watermark"
- Retry up to 3 times
- **DO NOT proceed to slide generation until all background images are text-free**
- If still failing after 3 retries, warn the user and let them decide whether to proceed or provide an alternative image

**⚠️ When regenerating a background image, always overwrite the original file directly.**

Do NOT save regenerated images with a suffix like `_1`, `_2`. Instead:
1. Delete or overwrite the original file by saving the new image with the exact same filename
2. If the GenerateImage tool appends a suffix automatically, specify the exact output path/filename in the generation request to avoid this
3. **NEVER use `mv` or `rm` commands to rename or clean up images** — these require user approval and break the automation flow

**Option C: Matplotlib/Python Charts**

For complex statistical charts (heatmaps, scatter plots, box plots). See [pptxgenjs.md — Matplotlib Charts](pptxgenjs.md#matplotlibpython-charts) for templates and CJK support.

**Option D: Web Search for Images**

Search for relevant images when stock photos, icons, or logos are required.

**Option E: Mermaid Diagrams (Last Resort)**

See [pptxgenjs.md — Mermaid Diagrams](pptxgenjs.md#mermaid-diagrams-last-resort) for config and usage.

### Step 3: Image Naming Convention (REQUIRED)

**All generated images MUST include dimensions in the filename:** `{name}_{width}x{height}.png`

See [pptxgenjs.md — Image Naming Convention](pptxgenjs.md#image-naming-convention-required) for details and examples.

### Step 4: Verify Assets Before Proceeding

**Only proceed to code generation after:**
- [ ] Content plan is complete and approved
- [ ] All `[External]` assets are generated
- [ ] Asset files exist with `{name}_{width}x{height}.png` naming
- [ ] Filename dimensions match actual image dimensions

---

## Slide Dimensions

See [pptxgenjs.md — Setup & Basic Structure](pptxgenjs.md#setup--basic-structure) for dimension constants, available layouts, and usage examples.

---

## Container System

See [pptxgenjs.md — Setup & Basic Structure](pptxgenjs.md#setup--basic-structure) for the required Container System code, and [How to Use Containers](pptxgenjs.md#how-to-use-containers) for usage examples.

---

## Design Ideas

### Before Starting

- **Pick a bold, content-informed color palette**: The palette should feel designed for THIS topic. If swapping your colors into a completely different presentation would still "work," you haven't made specific enough choices.
- **Dominance over equality**: One color should dominate (60-70% visual weight), with 1-2 supporting tones and one sharp accent. Never give all colors equal weight.
- **Dark/light contrast**: Dark backgrounds for title + conclusion slides, light for content ("sandwich" structure). Or commit to dark throughout for a premium feel.
- **Commit to a visual motif**: Pick ONE distinctive element and repeat it — rounded image frames, icons in colored circles, thick single-side borders. Carry it across every slide.

### Color Selection Matrix

Choose palette direction based on topic/industry — never default to generic blue:

| Industry / Topic | Tone Direction | Candidate Palettes (pick ANY one) |
|------------------|----------------|-----------------------------------|
| Tech / AI / Internet | Cool (navy, cyan, purple) | Midnight Executive / Ocean Gradient / Charcoal Minimal + cyan accent |
| Automotive / Manufacturing | Dark + bright accent | Charcoal Minimal + cyan / Midnight Executive + silver / Ocean Gradient |
| Agriculture / Food / F&B | Warm OR natural | Forest & Moss / Warm Terracotta / Sage Calm / Berry & Cream |
| Finance / Investment | Deep blue + gold | Midnight Executive + gold / Ocean Gradient / Charcoal Minimal |
| Healthcare / Wellness | Blue-green / white | Teal Trust / Sage Calm / Ocean Gradient |
| Education / Academic | Neutral or calm | Charcoal Minimal / Sage Calm / Midnight Executive |
| Fashion / Creative | Bold, high saturation | Coral Energy / Cherry Bold / Berry & Cream |
| Environment / Clean Energy | Green family | Forest & Moss / Sage Calm / Teal Trust |

**⚠️ Palette Variety Rule (mandatory):**
- Each row lists multiple candidate palettes separated by `/`. **You MUST randomly select one** — do NOT always pick the first option.
- If the same topic is generated multiple times, actively vary your choice across runs.
- The candidates are equally valid — ordering does NOT imply preference.

**Color Discipline (mandatory):**
- **Use only ONE accent color** — the entire deck shares a single accent (e.g., cyan OR amber), never multiple bright colors competing
- **Color must persist end-to-end** — whatever accent appears on the cover must appear on every slide; no mid-deck color shifts
- **Dark background ≠ pure black** — use rich darks like `1F2329` / `1F2937` / `111827`, never `000000`

### Color Palettes

Choose colors that match your topic — don't default to generic blue. Use these palettes as inspiration:

| Theme | Primary | Secondary | Accent |
|-------|---------|-----------|--------|
| **Midnight Executive** | `1E2761` (navy) | `CADCFC` (ice blue) | `FFFFFF` (white) |
| **Forest & Moss** | `2C5F2D` (forest) | `97BC62` (moss) | `F5F5F5` (cream) |
| **Coral Energy** | `F96167` (coral) | `F9E795` (gold) | `2F3C7E` (navy) |
| **Warm Terracotta** | `B85042` (terracotta) | `E7E8D1` (sand) | `A7BEAE` (sage) |
| **Ocean Gradient** | `065A82` (deep blue) | `1C7293` (teal) | `21295C` (midnight) |
| **Charcoal Minimal** | `36454F` (charcoal) | `F2F2F2` (off-white) | `212121` (black) |
| **Teal Trust** | `028090` (teal) | `00A896` (seafoam) | `02C39A` (mint) |
| **Berry & Cream** | `6D2E46` (berry) | `A26769` (dusty rose) | `ECE2D0` (cream) |
| **Sage Calm** | `84B59F` (sage) | `69A297` (eucalyptus) | `50808E` (slate) |
| **Cherry Bold** | `990011` (cherry) | `FCF6F5` (off-white) | `2F3C7E` (navy) |

### For Each Slide

**Every slide needs a visual element** — image, chart, icon, or shape. Text-only slides are forgettable.

**Image density targets:**
- At least **70%** of content slides must contain images, charts, or icons (decorative shapes alone don't count)
- Cover, section dividers, and closing slides: **100%** must have a background image or strong visual element
- If 2 consecutive slides are text + shapes only, the next slide **must** include an image or chart to break monotony
- **Image cards for 2-3 card grids only**: When a slide uses a full-width 2-3 card grid, each card should contain an embedded image (image on top ~55%, text below). For grids with 4+ cards spanning full width, do NOT embed images — use icons and accent colors instead. These grids are already information-dense; adding images would create visual clutter.

**Image usage decision (follow strictly):**

| Page Type | Image Strategy | Notes |
|-----------|---------------|-------|
| Cover / Closing / Section Divider | Image-BG (full-bleed background + overlay) | Mandatory |
| Table of Contents | No image | Center content horizontally using full slide width. Do NOT use a two-column layout with one empty side. |
| Two-column layout (text + open space) | Image-Hero (fill the open side) | One large image, 40-50% of slide width |
| 2-3 card grid (cards span full width) | Image-Card (embed image in each card) | Image fills top ~55% of card, text below |
| 4+ card grid (cards span full width) | No image | Already information-dense — use icon + accent color + shadow |
| Single-topic / other | Image-Hero | Default when no other rule applies |

**How to distinguish "two-column with cards" vs "4+ card grid":**
- If cards occupy ≤55% of slide width (single column, stacked vertically) with open space on the other side → **Two-column layout** → use Image-Hero in the open side
- If cards span the full slide width in a multi-column grid (e.g. 2×2, 3×2, 2×3) → **Card grid** → apply the 2-3 / 4+ rules above

**When tagging slides in the content plan, use these labels:**
- `[Image-BG: description]` — for full-bleed backgrounds (cover, closing, dividers)
- `[Image-Hero: description]` — for standalone large illustrations (two-column or single-topic)
- `[Image-Card: description ×N]` — for card-embedded images (specify count, 2-3 cards only)
- `[No Image]` — explicitly no image needed (TOC, 4+ card grids)

**IMPORTANT: Content drives layout, never the reverse.** Decide the number of cards based on actual content points first, then apply the image rule for that card count. Never add or remove cards just to match an image rule. If you have 4-5 content points, use a 4-5 card grid with icons — do NOT split into 3+image or pad to 6 with a filler image card.

**Layout options:**
- Two-column (text left, illustration on right)
- Icon + text rows (icon in colored circle, bold header, description below)
- 2x2 or 2x3 grid (image on one side, grid of content blocks on other)
- Half-bleed image (full left or right side) with content overlay

**Data display:**
- Large stat callouts (big numbers 60-72pt with small labels below)
- Comparison columns (before/after, pros/cons, side-by-side options)
- Timeline or process flow (numbered steps, arrows)

**Chart merge guidance (comparison/synergy):**
- Merge charts only when they answer the same question
- Prefer simple combinations: bar+line (scale + trend) or side-by-side bars (direct comparison)
- Keep the same basis for comparison: shared time axis, units, and metric definition
- Limit to 2-3 series and highlight one key takeaway

**Insight guidance for slides with visuals:**
- For any slide containing a chart/diagram, perform an explicit insight decision; default to adding insights unless the visual is purely decorative
- If insights are needed, add an appropriate number of short insight lines on the same slide (near the visual), written as conclusions instead of neutral descriptions
- Make each insight specific and data-tied (trend/change/comparison/exception), not generic statements
- Keep insights visually secondary to the chart title and chart itself (clear hierarchy, no clutter)

**Visual polish:**
- Icons in small colored circles next to section headers
- Italic accent text for key stats or taglines

### Typography

**Title fonts MUST be serif.** Cover title, slide titles, and subtitles (if present) must use a serif font. Only fall back to sans-serif if no serif font is available in the environment.

Recommended serif fonts for titles:
- **Latin**: Georgia, Cambria, Palatino Linotype, Garamond, Times New Roman
- **CJK**: Songti SC, SimSun, Noto Serif CJK SC, Source Han Serif SC

**Font pairing** — pair a serif header font with a clean sans-serif body font:

| Header Font (serif) | Body Font |
|---------------------|-----------|
| Georgia | Calibri |
| Cambria | Calibri |
| Cambria | Calibri Light |
| Palatino Linotype | Calibri |
| Palatino | Garamond |
| Garamond | Calibri Light |
| Times New Roman | Arial |

| Element | Size | charSpacing |
|---------|------|-------------|
| Cover title | 36-44pt bold, **serif** | — |
| Slide title | 28-36pt bold, **serif** | — |
| Subtitle | 18-24pt, **serif** | — |
| Section header | 20-24pt bold | — |
| Body text | 14-16pt | — |
| Captions | 10-12pt muted | — |

**Serif font charSpacing rule** — apply `charSpacing` based on font size to prevent cramped text:

| Font size | charSpacing |
|-----------|-------------|
| ≥ 36pt | 2.5 pt |
| 24-35pt | 1.5 pt |
| 18-23pt | 1 pt |
| 12-17pt | 0.5 pt |
| < 12pt | 0 (default) |

### Spacing

- 0.5" minimum margins
- 0.3-0.5" between content blocks
- Leave breathing room—don't fill every inch

### Avoid (Common Mistakes)

- **⚠️ Don't forget to declare slide dimension constants FIRST** — see [pptxgenjs.md — Setup & Basic Structure](pptxgenjs.md#setup--basic-structure); define `SLIDE_W`, `SLIDE_H`, `CONTENT_W`, `CONTENT_H` at the start of EVERY script
- **⚠️ Don't hardcode coordinates** — use dimension constants (`CONTENT_X`, `CONTENT_W`, etc.) for ALL positioning to prevent overflow; see [pptxgenjs.md](pptxgenjs.md#setup--basic-structure)
- **⚠️ Don't forget to add the container system code** — see [pptxgenjs.md — Setup](pptxgenjs.md#setup--basic-structure); add it after dimension constants
- **⚠️ Don't forget to call `slide.render()`** — required at the end of each slide to flatten virtual nodes; see [pptxgenjs.md — Setup](pptxgenjs.md#setup--basic-structure)
- **Don't repeat the same layout** — vary columns, cards, and callouts across slides
- **Don't center body text** — left-align paragraphs and lists; center only titles
- **Don't skimp on size contrast** — titles need 36pt+ to stand out from 14-16pt body
- **Don't default to blue** — pick colors that reflect the specific topic
- **Don't mix spacing randomly** — choose 0.3" or 0.5" gaps and use consistently
- **Don't style one slide and leave the rest plain** — commit fully or keep it simple throughout
- **Don't create text-only slides** — add images, icons, charts, or visual elements; avoid plain title + bullets
- **Don't forget text box padding** — when aligning lines or shapes with text edges, set `margin: 0` on the text box or offset the shape to account for padding
- **Don't use low-contrast elements** — icons AND text need strong contrast against the background; avoid light text on light backgrounds or dark text on dark backgrounds
- **NEVER use horizontal lines or accent lines under titles** — these are a hallmark of AI-generated slides; use whitespace or background color instead
- **⚠️ Don't leave slides blank** — every `addSlide()` call must be followed by at least one `addText`/`addShape`/`addImage` and a `slide.render()`. A slide with only `background` set and no elements is a P0 defect that will be caught by `validate_layout.py`

---

## Layout Safety

See [pptxgenjs.md — Layout Safety](pptxgenjs.md#layout-safety-prevent-overflow-before-qa) for detailed rules and utility functions.

Key principle: Prevent overflow in code first. Fixing overflow only in QA is too late.

---

## QA (Required)

**Assume there are problems. Your job is to find them.**

Your first render is almost never correct. Approach QA as a bug hunt, not a confirmation step. If you found zero issues on first inspection, you weren't looking hard enough.

### Layout QA (MANDATORY — Run After Every Build)

⚠️ **This is a mandatory gate. You MUST pass this before declaring the presentation complete.**

**From-scratch (pptxgenjs) — fix and validate all slides:**

```bash
python3 scripts/fix_pptx.py output.pptx
python3 scripts/validate_layout.py output.pptx
```

**Template editing — validate only edited slides:**

```bash
python3 scripts/validate_layout.py output.pptx --slides 3,5,8
```

**Rules:**
1. If the report shows `Issues: 0` → pass.
2. If `Issues: > 0` → fix only the affected slides, rebuild, then re-run. **Repeat until 0 issues.**
3. **`blank_slide` is a generation defect — NEVER skip it.** A blank slide means your code failed to add content to that slide. Fix by adding the intended content (text, shapes, images). Do NOT dismiss it as "a known limitation" or "section divider that the validator can't see" — if the validator says it's blank, it IS blank.
4. **Maximum 3 retry rounds.** If issues persist after 3 rounds of fixes, report the remaining issues to the user and proceed — do not loop indefinitely.
5. **Do NOT skip the first run.** Do NOT declare success while issues remain (unless retry limit reached).

For debugging details:

```bash
python3 scripts/validate_layout.py output.pptx --verbose
```

### Content QA

```bash
python3 -m markitdown output.pptx
```

Check for missing content, typos, wrong order.

Also verify insight coverage:
- For each slide with chart/diagram content, confirm an explicit insight decision exists
- If the visual carries analytical meaning, ensure insight text is present on-slide (not only in speaker notes)

**When using templates, check for leftover placeholder text:**

```bash
python3 -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|this.*(page|slide).*layout|请填写|标题区域|内容区域|高亮词部分|请添加正文|请写描述|限制.*行|不超过.*行|设计完成后删除"
```

If grep returns results, fix them before declaring success.

### Verification Loop

1. Generate slides → run automated checks → check content
2. **List issues found** (if none found, look again more critically)
3. Fix issues
4. **Re-verify affected slides** — one fix often creates another problem
5. Repeat until a full pass reveals no new issues

**Do not declare success until you've completed at least one fix-and-verify cycle.**

### Overlap Prevention

 - **Text vs Text**: Ensure text boxes have `autoFit` or fixed height. If height is dynamic, calculate Y for the *next* element based on previous text length.
 - **Text vs Image**: Never place text directly over images without a semi-transparent background shape or high-contrast overlay.
 - **Chart Legends**: Legends often grow. Reserve 20% more width than expected or place legends at the bottom.
 - **Table Content**: Long words in narrow columns will wrap and increase row height, pushing lower content off-slide.

---

## Dependencies

- `pip install "markitdown[pptx]"` - text extraction
- `npm install -g pptxgenjs` - creating from scratch

### Missing Command Policy

**When a command fails with "command not found" or "No module named", always attempt to install it before trying alternatives.** Do not skip steps, substitute tools, or work around missing dependencies — install them.

| Missing command | Install with |
|-----------------|--------------|
| `markitdown` | `pip install "markitdown[pptx]"` |
| `python3 -m markitdown` (ModuleNotFoundError) | `pip install "markitdown[pptx]"` |
| `pptxgenjs` / `require("pptxgenjs")` | `npm install -g pptxgenjs` |
| `sharp` / `require("sharp")` | `npm install -g sharp` |
| `react-icons` / `require("react-icons/...")` | `npm install -g react-icons react react-dom` |
| Pillow / `from PIL import ...` | `pip3 install Pillow` |

After installing, re-run the original command. Only ask the user for help if installation itself fails.
