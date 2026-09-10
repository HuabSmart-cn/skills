---
name: docx
description: "Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When you need to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks"
license: Proprietary. LICENSE.txt has complete terms
supported_os:
  - macos
  - linux
---

# DOCX creation, editing, and analysis

## Overview

A .docx file is a ZIP archive containing XML files.

## Quick Reference

| Task | Approach |
|------|----------|
| Read/analyze content | `pandoc` or unpack for raw XML |
| Create new document | **⚠️ MUST use JavaScript `docx-js`** - see Creating New Documents below |
| Edit existing document | Unpack → edit XML → repack - see Editing Existing Documents below |

### Converting .doc to .docx

Legacy `.doc` files must be converted before editing:

```bash
soffice --headless --convert-to docx document.doc
```

### Reading Content

```bash
# Text extraction with tracked changes
pandoc --track-changes=all document.docx -o output.md

# Raw XML access
python scripts/unpack.py document.docx unpacked/
```

### Converting to Images

```bash
soffice --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

### Accepting Tracked Changes

To produce a clean document with all tracked changes accepted (requires LibreOffice):

```bash
python scripts/accept_changes.py input.docx output.docx
```

---

## Creating New Documents

**⚠️ MANDATORY: Creating new .docx files from scratch MUST use the JavaScript `docx-js` library. Do NOT use Python, XML templates, or any other approach. The JavaScript solution provides the most reliable and maintainable way to generate documents programmatically.**

Generate .docx files with JavaScript using the pre-installed `docx` package.

**⚠️ CRITICAL: In docx-js, use JavaScript escapes (`\"`) for quotes. NEVER use XML entities (`&#x201C;`) - they will appear as literal garbage text.**

After generating a new docx, always run:

```bash
python scripts/sanitize.py input.docx
```

### Setup
```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ExternalHyperlink,
        HeadingLevel, BorderStyle, WidthType, ShadingType,
        VerticalAlign, PageNumber, PageBreak } = require('docx');

// CRITICAL: Use exactly ONE section - multiple sections create blank pages
const doc = new Document({ sections: [{ children: [/* ALL content here */] }] });
Packer.toBuffer(doc).then(buffer => fs.writeFileSync("doc.docx", buffer));
```

### Page Size

```javascript
// CRITICAL: docx-js defaults to A4, not US Letter
// Always set page size explicitly for consistent results
sections: [{
  properties: {
    page: {
      size: {
        width: 12240,   // 8.5 inches in DXA
        height: 15840   // 11 inches in DXA
      },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } // 1 inch margins
    }
  },
  children: [/* ALL content goes here in this single section */]
}]
```

**Common page sizes (DXA units, 1440 DXA = 1 inch):**

| Paper | Width | Height | Content Width (1" margins) |
|-------|-------|--------|---------------------------|
| US Letter | 12,240 | 15,840 | 9,360 |
| A4 (default) | 11,906 | 16,838 | 9,026 |

### Fonts and CJK Support

**CRITICAL: For documents containing Chinese/Japanese/Korean text, you MUST configure fonts for both ASCII and East Asian characters.** Using only ASCII fonts (like Arial) will cause CJK characters to display incorrectly or as boxes.

#### Font Configuration by Character Type

Word documents use different font slots for different character types:
- `ascii` / `hAnsi`: Latin characters (A-Z, a-z, numbers)
- `eastAsia`: CJK characters (Chinese, Japanese, Korean)
- `cs`: Complex scripts (Arabic, Hebrew, etc.)

#### Recommended Font Combinations

| Platform | ASCII/Latin | East Asian (CJK) |
|----------|-------------|------------------|
| Cross-platform | Arial | Microsoft YaHei |
| macOS | Arial | PingFang SC |
| Windows | Arial | SimSun or SimHei |
| Linux | DejaVu Sans | Noto Sans CJK SC |

**Best practice**: Use `Microsoft YaHei` for CJK as it's available on most platforms and renders well.

#### Basic Font Setup (ASCII only - English documents)

```javascript
const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } }
  }
});
```

#### CJK Font Setup (Documents with Chinese/Japanese/Korean)

```javascript
const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: {
            ascii: "Arial",
            hAnsi: "Arial",
            eastAsia: "Microsoft YaHei"
          },
          size: 24
        }
      }
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: {
          size: 32, bold: true,
          font: { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" }
        },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0, keepNext: false, keepLines: false } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: {
          size: 28, bold: true,
          font: { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" }
        },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1, keepNext: false, keepLines: false } },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("标题 Title")] }),
    ]
  }]
});
```

#### Platform-Adaptive Font Selection

For maximum compatibility across different operating systems:

```javascript
const os = require('os');

function getCJKFont() {
  const platform = os.platform();
  if (platform === 'darwin') {
    return 'PingFang SC';  // macOS
  } else if (platform === 'win32') {
    return 'Microsoft YaHei';  // Windows
  } else {
    return 'Noto Sans CJK SC';  // Linux
  }
}

const cjkFont = getCJKFont();
const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: { ascii: "Arial", hAnsi: "Arial", eastAsia: cjkFont },
          size: 24
        }
      }
    }
  }
});
```

### Styles (Override Built-in Headings)

Keep titles black for readability. Set `keepNext: false` and `keepLines: false` to allow natural page flow.

```javascript
const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" },
          size: 24
        }
      }
    },
    paragraphStyles: [
      // IMPORTANT: Use exact IDs to override built-in styles
      // IMPORTANT: Set keepNext/keepLines to false to allow natural page flow
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" } },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0, keepNext: false, keepLines: false } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" } },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1, keepNext: false, keepLines: false } },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("标题 Title")] }),
    ]
  }]
});
```

### Special Characters in docx-js

**⚠️ CRITICAL: Use JavaScript escapes, NOT XML entities.**

| Need to write | ✅ Correct (JavaScript) | ❌ Wrong (XML entity) |
|---------------|------------------------|----------------------|
| Double quote `"` | `\"` | `&#x201C;` `&#x201D;` `&#34;` |
| Single quote `'` | `\'` | `&#x2018;` `&#x2019;` `&#39;` |
| Ampersand `&` | `&` (no escape needed) | `&amp;` |
| Less than `<` | `<` (no escape needed) | `&lt;` |

```javascript
// ✅ CORRECT - use JavaScript backslash escapes
new TextRun("这是中文内容")
new TextRun("He said \"Hello\" and replied \"你好\"")
new TextRun("包含\"双引号\"的内容")

// ❌ WRONG - XML entities will display as garbage text in the document
new TextRun("&#x201C;Hello&#x201D;")  // Shows literal: &#x201C;Hello&#x201D;
new TextRun("Tom&#x2019;s book")  // Shows literal: Tom&#x2019;s book

// ❌ WRONG - do NOT convert characters to \uXXXX escapes
new TextRun("\u8fd9\u662f\u4e2d\u6587")  // Makes code unreadable
```

**Remember:**
- docx-js handles XML internally - you write JavaScript strings, not XML
- XML entities are ONLY for the "Editing Existing Documents" workflow (raw XML editing)
- When in doubt, use `\"` for quotes

### Lists (NEVER use unicode bullets)

```javascript
// ❌ WRONG - never manually insert bullet characters
new Paragraph({ children: [new TextRun("• Item")] })  // BAD
new Paragraph({ children: [new TextRun("\u2022 Item")] })  // BAD

// ✅ CORRECT - use numbering config with LevelFormat.BULLET
const doc = new Document({
  numbering: {
    config: [
      { reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbers",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ]
  },
  sections: [{
    children: [
      new Paragraph({ numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Bullet item")] }),
      new Paragraph({ numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("Numbered item")] }),
    ]
  }]
});

// ⚠️ Each reference creates INDEPENDENT numbering
// Same reference = continues (1,2,3 then 4,5,6)
// Different reference = restarts (1,2,3 then 1,2,3)
```

### Tables

**CRITICAL: Tables need dual widths** - set both `columnWidths` on the table AND `width` on each cell. Without both, tables render incorrectly on some platforms.

**CRITICAL: Tables should not split across pages** - use `cantSplit: true` on TableRow to keep each row intact.

```javascript
// CRITICAL: Always set table width for consistent rendering
// CRITICAL: Use ShadingType.CLEAR (not SOLID) to prevent black backgrounds
// CRITICAL: Use cantSplit: true to prevent rows from breaking across pages
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 100, type: WidthType.PERCENTAGE }, // Always set table width
  columnWidths: [4680, 4680], // Set at table level (DXA: 1440 = 1 inch)
  rows: [
    new TableRow({
      cantSplit: true, // Prevent row from splitting across pages
      children: [
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA }, // Also set on each cell
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR }, // CLEAR not SOLID
          margins: { top: 80, bottom: 80, left: 120, right: 120 }, // Cell padding (internal, not added to width)
          children: [new Paragraph({ children: [new TextRun("Cell")] })]
        })
      ]
    })
  ]
})
```

**Table width calculation:**

Use `WidthType.PERCENTAGE` for simplicity, or `WidthType.DXA` for precise control:

```javascript
// Option 1: Percentage (recommended - automatically fits content area)
width: { size: 100, type: WidthType.PERCENTAGE }

// Option 2: DXA (precise control)
// Table width = sum of columnWidths = content width
// US Letter with 1" margins: 12240 - 2880 = 9360 DXA
width: { size: 9360, type: WidthType.DXA },
columnWidths: [7000, 2360]  // Must sum to table width
```

**Width rules:**
- Table width must equal the sum of `columnWidths`
- Cell `width` must match corresponding `columnWidth`
- Cell `margins` are internal padding - they reduce content area, not add to cell width
- For full-width tables: use content width (page width minus left and right margins)

### Images

```javascript
// CRITICAL: type parameter is REQUIRED
new Paragraph({
  children: [new ImageRun({
    type: "png", // Required: png, jpg, jpeg, gif, bmp, svg
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150 },
    altText: { title: "Title", description: "Desc", name: "Name" } // All three required
  })]
})
```

### Charts & Diagrams (Image Insertion)

Use `matplotlib` + `seaborn` (Python) for data charts, `PlantUML` (`plantuml.jar`) for UML diagrams, and `Graphviz` (`dot`) for flowcharts and architecture diagrams. Generate PNG images first, then embed via `ImageRun`.

**Tool selection:**

| Scenario | Tool | When to Use |
|----------|------|-------------|
| Data charts (bar, line, pie, scatter, heatmap) | `matplotlib` + `seaborn` (Python) | Quantitative data visualization with axes, legends, and labels |
| Sequence / State / Gantt / Class diagram | `PlantUML` (`plantuml.jar`) | UML-style diagrams with rich semantics (participants, messages, timelines) |
| Flowchart / Architecture / Network topology | `Graphviz` (`dot`) | Directed/undirected graphs with nodes and edges; system architecture, dependency graphs |

**Decision guide:**
- 有**数值数据**要展示 → `matplotlib` + `seaborn`
- 有**时序交互**或**甘特图/类图** → `PlantUML`
- 有**节点-边关系**（流程图、架构图、依赖图、网络拓扑） → `Graphviz`

#### Generate Charts with matplotlib + seaborn

**⚠️ CRITICAL: NEVER call `sns.set_theme()` or `sns.set_style()` directly in your code.** Both reset `matplotlib.rcParams` including font settings, which causes CJK text (Chinese/Japanese/Korean) to render as empty boxes. Always use the provided `setup_matplotlib.py` script instead:

```python
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from setup_matplotlib import init_plot_env
init_plot_env()

import matplotlib.pyplot as plt

CONTENT_WIDTH_INCHES = 6.5

fig, ax = plt.subplots(figsize=(CONTENT_WIDTH_INCHES, 4))
import seaborn as sns
sns.barplot(x=['Q1', 'Q2', 'Q3', 'Q4'], y=[120, 135, 142, 158], ax=ax, palette="Blues_d")
ax.set_title('Quarterly Sales')
fig.tight_layout()
fig.savefig('chart.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

`init_plot_env()` handles both seaborn theme setup and CJK font configuration in the correct order. Do NOT manually set `plt.rcParams['font.sans-serif']` or call `sns.set_theme()` / `sns.set_style()` — `init_plot_env()` does both.

If you need to change seaborn style/theme **after** `init_plot_env()`, use the safe wrappers:

```python
from setup_matplotlib import safe_set_style, safe_set_theme
safe_set_style("darkgrid")       # instead of sns.set_style("darkgrid")
safe_set_theme(style="white")    # instead of sns.set_theme(style="white")
```

#### Seaborn API Safety Guide

| Status | Function | Notes |
|--------|----------|-------|
| ❌ FORBIDDEN | `sns.set_theme()` | Resets font.sans-serif → CJK broken. Use `init_plot_env()` or `safe_set_theme()` |
| ❌ FORBIDDEN | `sns.set_style()` | Resets font.sans-serif → CJK broken. Use `safe_set_style()` |
| ❌ FORBIDDEN | `sns.set()` | Alias for set_theme. Use `init_plot_env()` or `safe_set_theme()` |
| ❌ FORBIDDEN | `sns.reset_defaults()` | Resets all rcParams → CJK broken |
| ❌ FORBIDDEN | `sns.reset_orig()` | Resets all rcParams → CJK broken |
| ✅ Safe | `sns.set_context()` | Only changes font sizes, not font family |
| ✅ Safe | `sns.set_palette()` | Only changes colors |
| ✅ Safe | `sns.barplot()`, `sns.heatmap()`, etc. | All plotting functions are safe |

#### Generate Diagrams with PlantUML

Use the standalone script at `scripts/render_plantuml.py` which provides `returncode` checking, syntax error parsing with line numbers, retry on transient failures, and Gantt-safe DPI handling:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from render_plantuml import render_plantuml, PlantUMLSyntaxError, PlantUMLError, PLANTUML_THEME

try:
    render_plantuml(f"@startuml\n{PLANTUML_THEME}\nleft to right direction\nrectangle A\nrectangle B\nrectangle C\nA --> B\nB --> C\n@enduml", 'flow.png')
except PlantUMLSyntaxError as e:
    print(f"Syntax error in PlantUML code, fix the puml source and retry:\\n{e}")
except PlantUMLError as e:
    print(f"PlantUML rendering failed:\\n{e}")
```

**⚠️ PlantUML Tips:**
- **Always inject `PLANTUML_THEME`**: Every diagram must include `{PLANTUML_THEME}` after `@startuml`
- Use `participant` for services, `actor` for users, `database` for storage — each maps to distinct colors
- Use `left to right direction` for horizontal layout to reduce vertical space

#### Generate Flowcharts/Architecture Diagrams with Graphviz

Use the standalone script at `scripts/render_graphviz.py` which provides `returncode` checking, syntax error parsing with line numbers, and auto size injection:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from render_graphviz import render_graphviz, GraphvizSyntaxError, GraphvizError, GRAPHVIZ_DPI

GRAPHVIZ_MAX_WIDTH_IN = 6.5
GRAPHVIZ_MAX_HEIGHT_IN = GRAPHVIZ_MAX_WIDTH_IN * 1.3 * 0.6

try:
    render_graphviz("digraph { rankdir=LR; nodesep=0.65; ranksep=0.85; node [fontsize=16 margin=\"0.40,0.28\"]; edge [fontsize=14 penwidth=1.5]; A -> B -> C }", 'flow.png',
                    max_width_in=GRAPHVIZ_MAX_WIDTH_IN, max_height_in=GRAPHVIZ_MAX_HEIGHT_IN)
except GraphvizSyntaxError as e:
    print(f"Syntax error in Graphviz code, fix the dot source and retry:\\n{e}")
except GraphvizError as e:
    print(f"Graphviz rendering failed:\\n{e}")
```

**⚠️ Graphviz Readability Rules:**
- **Node fontsize MUST be 16–20** — fontsize < 16 缩放到文档后难以辨认
- **联动放大**：放大字号时必须同步放大 `margin`（如 `"0.40,0.28"`）和调整 `nodesep`/`ranksep`（如 `0.65`/`0.85`）
- **多行布局（MUST for 4+ nodes）**：4 个以上同层节点**必须**用 `{rank=same}` 分成 2-3 行网格，配合 `style=invis` 不可见边引导换行；飞轮/循环回路边用 `constraint=false`。目标宽高比 4:3 ~ 16:9（如 6 节点 → 3+3, 8 节点 → 4+4）
- **cluster 标题 fontsize** 与节点保持一致（≥16）

#### Embed Chart/Diagram in DOCX (Overflow-Safe)

Read actual image dimensions and scale to fit the content area:

```javascript
const fs = require('fs');
const sizeOf = require('image-size');

const PAGE_CONTENT_WIDTH_PX = 624; // US Letter 9360 DXA ≈ 624px at 96 DPI
const MAX_IMAGE_WIDTH = Math.floor(PAGE_CONTENT_WIDTH_PX * 0.9);
const MIN_IMAGE_WIDTH = Math.floor(PAGE_CONTENT_WIDTH_PX * 0.3);
const MAX_IMAGE_HEIGHT = Math.floor(PAGE_CONTENT_WIDTH_PX * 1.3 * 0.6); // ~60% of content height

function safeImageRun(imagePath) {
  const data = fs.readFileSync(imagePath);
  const dims = sizeOf(data);
  let width = dims.width;
  let height = dims.height;
  if (width > MAX_IMAGE_WIDTH) {
    const scale = MAX_IMAGE_WIDTH / width;
    width = MAX_IMAGE_WIDTH;
    height = Math.round(height * scale);
  } else if (width < MIN_IMAGE_WIDTH) {
    const scale = MIN_IMAGE_WIDTH / width;
    width = MIN_IMAGE_WIDTH;
    height = Math.round(height * scale);
  }
  if (height > MAX_IMAGE_HEIGHT) {
    const scale = MAX_IMAGE_HEIGHT / height;
    height = MAX_IMAGE_HEIGHT;
    width = Math.round(width * scale);
  }
  return new ImageRun({
    type: imagePath.endsWith('.png') ? 'png' : 'jpg',
    data,
    transformation: { width, height },
    altText: { title: "Chart", description: "Chart", name: "chart" }
  });
}

// Usage: center-aligned image with caption
new Paragraph({ alignment: AlignmentType.CENTER, children: [safeImageRun('chart.png')] }),
new Paragraph({
  alignment: AlignmentType.CENTER,
  children: [new TextRun({ text: "Figure 1: Quarterly Sales", size: 18, color: "666666" })]
}),
```

**⚠️ Image Overflow Protection Rules:**
- Always use `safeImageRun()` — it reads actual dimensions via `image-size`, enforces width AND height limits
- `MAX_IMAGE_WIDTH` = 90% of content width; `MIN_IMAGE_WIDTH` = 30% (prevents tiny images)
- `MAX_IMAGE_HEIGHT` = 60% of content height (prevents tall images from triggering page breaks)
- For very tall images (e.g., long sequence diagrams), prefer splitting at the diagram source into multiple smaller diagrams
- Always center-align image paragraphs with `AlignmentType.CENTER`
- Constrain matplotlib `figsize` width to `6.5` inches; use `dpi=150` on `savefig()`
- PlantUML: use `-Sdpi=150` (except `@startgantt` — omit `-Sdpi` for Gantt charts); Graphviz: use `-Gdpi=150`
- **NEVER** use `keepNext: true` or `keepLines: true` on heading or body paragraph styles — these cause large blank areas when content doesn't fit on the current page

### Page Breaks and Pagination

**Pagination strategy:**
- **Cover page**: Use explicit PageBreak after cover content
- **Images/Tables**: Keep intact, do not split across pages
- **Headings/Paragraphs**: Allow natural flow, no forced page breaks

```javascript
// CRITICAL: PageBreak must be inside a Paragraph
new Paragraph({ children: [new PageBreak()] })

// Or use pageBreakBefore (use sparingly - only for cover pages or major sections)
new Paragraph({ pageBreakBefore: true, children: [new TextRun("New page")] })
```

**IMPORTANT: Avoid excessive whitespace** - Word's default heading styles set `keepNext: true` which forces headings to stay with the following paragraph. This causes pages with only a heading at the bottom and large blank areas. Always set `keepNext: false` and `keepLines: false` on heading styles (see Styles section above).

**⚠️ CRITICAL: Each section generates at least one page. If you create an empty section (e.g., with page properties only and `children: []`) followed by a content section, the empty section will render as a blank first page. Use `PageBreak` within a single section instead.

### Headers/Footers

```javascript
sections: [{
  properties: {
    page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } // 1440 = 1 inch
  },
  headers: {
    default: new Header({ children: [new Paragraph({ children: [new TextRun("Header")] })] })
  },
  footers: {
    default: new Footer({ children: [new Paragraph({
      children: [new TextRun("Page "), new TextRun({ children: [PageNumber.CURRENT] })]
    })] })
  },
  children: [/* content */]
}]
```

### Critical Rules for docx-js

- **Use exactly ONE section** - put ALL content in a single section's `children` array. Multiple sections cause blank pages (each empty section renders as a blank page). Never create an empty section followed by a content section
- **Set page size explicitly** - docx-js defaults to A4; use US Letter (12240 x 15840 DXA) for US documents
- **Configure CJK fonts for Chinese/Japanese/Korean** - use `font: { ascii: "Arial", hAnsi: "Arial", eastAsia: "Microsoft YaHei" }` to prevent garbled text
- **Use JavaScript escapes for quotes** - use `\"` not XML entities; `&#x201C;` will show as garbage text
- **Never use `\n`** - use separate Paragraph elements
- **Never use unicode bullets** - use `LevelFormat.BULLET` with numbering config
- **PageBreak must be in Paragraph** - standalone creates invalid XML
- **ImageRun requires `type`** - always specify png/jpg/etc
- **Always set table `width`** - use `{ size: 100, type: WidthType.PERCENTAGE }` for full width
- **Tables need dual widths** - `columnWidths` array AND cell `width`, both must match
- **Table width = sum of columnWidths** - for DXA, ensure they add up exactly
- **Always add cell margins** - use `margins: { top: 80, bottom: 80, left: 120, right: 120 }` for readable padding
- **Use `ShadingType.CLEAR`** - never SOLID for table shading
- **Override built-in styles** - use exact IDs: "Heading1", "Heading2", etc.
- **Include `outlineLevel`** - required in heading styles (0 for H1, 1 for H2, etc.)
- **Set `keepNext: false` on headings** - prevents excessive whitespace from headings being pushed to next page
- **Set `cantSplit: true` on table rows** - keeps tables intact across page boundaries
- **No table of contents** - do not generate any TOC or directory page; start directly with document content
- **Always run sanitize.py after creation** - it checks for and removes text-only TOC blocks and redundant blank pages

---

## Editing Existing Documents

**⚠️ This section is for editing RAW XML files (unpack/pack workflow). XML entities (`&#x201C;`) are ONLY valid here, NOT in docx-js code above.**

**Follow all 3 steps in order.**

### Step 1: Unpack
```bash
python scripts/unpack.py document.docx unpacked/
```
Extracts XML, pretty-prints, merges adjacent runs, and converts smart quotes to XML entities (`&#x201C;` etc.) so they survive editing. Use `--merge-runs false` to skip run merging.

### Step 2: Edit XML

Edit files in `unpacked/word/`. See XML Reference below for patterns.

**Use "AI Assistant" as the author** for tracked changes and comments, unless the user explicitly requests use of a different name.

**Use the Edit tool directly for string replacement. Do not write Python scripts.** Scripts introduce unnecessary complexity. The Edit tool shows exactly what is being replaced.

**CRITICAL: Use smart quotes for new content.** When adding text with apostrophes or quotes, use XML entities to produce smart quotes:
```xml
<!-- Use these entities for professional typography -->
<w:t>Here&#x2019;s a quote: &#x201C;Hello&#x201D;</w:t>
```
| Entity | Character |
|--------|-----------|
| `&#x2018;` | ‘ (left single) |
| `&#x2019;` | ’ (right single / apostrophe) |
| `&#x201C;` | “ (left double) |
| `&#x201D;` | ” (right double) |

**Adding comments:** Use `comment.py` to handle boilerplate across multiple XML files (text must be pre-escaped XML):
```bash
python scripts/comment.py unpacked/ 0 "Comment text with &amp; and &#x2019;"
python scripts/comment.py unpacked/ 1 "Reply text" --parent 0  # reply to comment 0
python scripts/comment.py unpacked/ 0 "Text" --author "Custom Author"  # custom author name
```
Then add markers to document.xml (see Comments in XML Reference).

### Step 3: Pack
```bash
python scripts/pack.py unpacked/ output.docx --original document.docx
```
Validates with auto-repair, condenses XML, and creates DOCX. Use `--validate false` to skip.

**Auto-repair will fix:**
- `durableId` >= 0x7FFFFFFF (regenerates valid ID)
- Missing `xml:space="preserve"` on `<w:t>` with whitespace

**Auto-repair won't fix:**
- Malformed XML, invalid element nesting, missing relationships, schema violations

### Common Pitfalls

- **Replace entire `<w:r>` elements**: When adding tracked changes, replace the whole `<w:r>...</w:r>` block with `<w:del>...<w:ins>...` as siblings. Don't inject tracked change tags inside a run.
- **Preserve `<w:rPr>` formatting**: Copy the original run's `<w:rPr>` block into your tracked change runs to maintain bold, font size, etc.

---

## XML Reference

### Schema Compliance

- **Element order in `<w:pPr>`**: `<w:pStyle>`, `<w:numPr>`, `<w:spacing>`, `<w:ind>`, `<w:jc>`, `<w:rPr>` last
- **Whitespace**: Add `xml:space="preserve"` to `<w:t>` with leading/trailing spaces
- **RSIDs**: Must be 8-digit hex (e.g., `00AB1234`)

### Tracked Changes

**Insertion:**
```xml
<w:ins w:id="1" w:author="AI Assistant" w:date="2025-01-01T00:00:00Z">
  <w:r><w:t>inserted text</w:t></w:r>
</w:ins>
```

**Deletion:**
```xml
<w:del w:id="2" w:author="AI Assistant" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
```

**Inside `<w:del>`**: Use `<w:delText>` instead of `<w:t>`, and `<w:delInstrText>` instead of `<w:instrText>`.

**Minimal edits** - only mark what changes:
```xml
<!-- Change "30 days" to "60 days" -->
<w:r><w:t>The term is </w:t></w:r>
<w:del w:id="1" w:author="AI Assistant" w:date="...">
  <w:r><w:delText>30</w:delText></w:r>
</w:del>
<w:ins w:id="2" w:author="AI Assistant" w:date="...">
  <w:r><w:t>60</w:t></w:r>
</w:ins>
<w:r><w:t> days.</w:t></w:r>
```

**Deleting entire paragraphs/list items** - when removing ALL content from a paragraph, also mark the paragraph mark as deleted so it merges with the next paragraph. Add `<w:del/>` inside `<w:pPr><w:rPr>`:
```xml
<w:p>
  <w:pPr>
    <w:numPr>...</w:numPr>  <!-- list numbering if present -->
    <w:rPr>
      <w:del w:id="1" w:author="AI Assistant" w:date="2025-01-01T00:00:00Z"/>
    </w:rPr>
  </w:pPr>
  <w:del w:id="2" w:author="AI Assistant" w:date="2025-01-01T00:00:00Z">
    <w:r><w:delText>Entire paragraph content being deleted...</w:delText></w:r>
  </w:del>
</w:p>
```
Without the `<w:del/>` in `<w:pPr><w:rPr>`, accepting changes leaves an empty paragraph/list item.

**Rejecting another author's insertion** - nest deletion inside their insertion:
```xml
<w:ins w:author="Jane" w:id="5">
  <w:del w:author="AI Assistant" w:id="10">
    <w:r><w:delText>their inserted text</w:delText></w:r>
  </w:del>
</w:ins>
```

**Restoring another author's deletion** - add insertion after (don't modify their deletion):
```xml
<w:del w:author="Jane" w:id="5">
  <w:r><w:delText>deleted text</w:delText></w:r>
</w:del>
<w:ins w:author="AI Assistant" w:id="10">
  <w:r><w:t>deleted text</w:t></w:r>
</w:ins>
```

### Comments

After running `comment.py` (see Step 2), add markers to document.xml. For replies, use `--parent` flag and nest markers inside the parent's.

**CRITICAL: `<w:commentRangeStart>` and `<w:commentRangeEnd>` are siblings of `<w:r>`, never inside `<w:r>`.**

```xml
<!-- Comment markers are direct children of w:p, never inside w:r -->
<w:commentRangeStart w:id="0"/>
<w:del w:id="1" w:author="AI Assistant" w:date="2025-01-01T00:00:00Z">
  <w:r><w:delText>deleted</w:delText></w:r>
</w:del>
<w:r><w:t> more text</w:t></w:r>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>

<!-- Comment 0 with reply 1 nested inside -->
<w:commentRangeStart w:id="0"/>
  <w:commentRangeStart w:id="1"/>
  <w:r><w:t>text</w:t></w:r>
  <w:commentRangeEnd w:id="1"/>
<w:commentRangeEnd w:id="0"/>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="0"/></w:r>
<w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:commentReference w:id="1"/></w:r>
```

### Images

1. Add image file to `word/media/`
2. Add relationship to `word/_rels/document.xml.rels`:
```xml
<Relationship Id="rId5" Type=".../image" Target="media/image1.png"/>
```
3. Add content type to `[Content_Types].xml`:
```xml
<Default Extension="png" ContentType="image/png"/>
```
4. Reference in document.xml:
```xml
<w:drawing>
  <wp:inline>
    <wp:extent cx="914400" cy="914400"/>  <!-- EMUs: 914400 = 1 inch -->
    <a:graphic>
      <a:graphicData uri=".../picture">
        <pic:pic>
          <pic:blipFill><a:blip r:embed="rId5"/></pic:blipFill>
        </pic:pic>
      </a:graphicData>
    </a:graphic>
  </wp:inline>
</w:drawing>
```

---

## Dependencies

> **All dependencies mentioned below are pre-installed, use them directly. **

- **pandoc**: Text extraction
- **docx**: JavaScript library for new documents
- **image-size**: JavaScript library for reading image dimensions
- **matplotlib** + **seaborn**: Python libraries for data chart generation
- **plantuml**: Pre-installed CLI for rendering PlantUML diagrams to PNG
- **graphviz** (`dot`): Graph layout tool for flowcharts and architecture diagrams
- **LibreOffice**: PDF conversion
- **Poppler**: `pdftoppm` for images
