---
name: pdf
description: Comprehensive PDF manipulation toolkit for extracting text and tables,
  merging/splitting documents, and handling forms. Use ONLY when the user
  explicitly requests PDF as the output format (e.g., "generate a PDF",
  "export as .pdf", "I need a PDF file") or when programmatically processing
  existing PDF documents. Do NOT use for general report writing — the default
  artifact format for reports, research documents, PRDs, and other structured
  written deliverables is the `html-report` skill (HTML). Only route here when
  the user's intent unambiguously requires a .pdf file.
license: Proprietary. LICENSE.txt has complete terms
supported_os:
  - macos
  - linux
---

# PDF Processing Guide

## Overview

This guide covers essential PDF processing operations using Python libraries and command-line tools. For advanced features, JavaScript libraries, and detailed examples, see REFERENCE.md. If you need to fill out a PDF form, read FORMS.md and follow its instructions.

## Quick Start

```python
from pypdf import PdfReader, PdfWriter

# Read a PDF
reader = PdfReader("document.pdf")
print(f"Pages: {len(reader.pages)}")

# Extract text
text = ""
for page in reader.pages:
    text += page.extract_text()
```

## Python Libraries

### pypdf - Basic Operations

#### Merge PDFs
```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        writer.add_page(page)

with open("merged.pdf", "wb") as output:
    writer.write(output)
```

#### Split PDF
```python
reader = PdfReader("input.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    with open(f"page_{i+1}.pdf", "wb") as output:
        writer.write(output)
```

#### Extract Metadata
```python
reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Subject: {meta.subject}")
print(f"Creator: {meta.creator}")
```

#### Rotate Pages
```python
reader = PdfReader("input.pdf")
writer = PdfWriter()

page = reader.pages[0]
page.rotate(90)  # Rotate 90 degrees clockwise
writer.add_page(page)

with open("rotated.pdf", "wb") as output:
    writer.write(output)
```

### pdfplumber - Text and Table Extraction

#### Extract Text with Layout
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

#### Extract Tables
```python
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for j, table in enumerate(tables):
            print(f"Table {j+1} on page {i+1}:")
            for row in table:
                print(row)
```

#### Advanced Table Extraction
```python
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    all_tables = []
    for page in pdf.pages:
        tables = page.extract_tables()
        for table in tables:
            if table:  # Check if table is not empty
                df = pd.DataFrame(table[1:], columns=table[0])
                all_tables.append(df)

# Combine all tables
if all_tables:
    combined_df = pd.concat(all_tables, ignore_index=True)
    combined_df.to_excel("extracted_tables.xlsx", index=False)
```

### reportlab - Create PDFs

#### Text Normalization (IMPORTANT)

Before writing any text to PDF, you MUST normalize special Unicode characters to avoid rendering issues.

```python
DASH_REPLACEMENTS = {
    '\u2010': '-',  # HYPHEN
    '\u2011': '-',  # NON-BREAKING HYPHEN
    '\u2012': '-',  # FIGURE DASH
    '\u2013': '-',  # EN DASH (e.g., "2020–2024")
    '\u2014': '-',  # EM DASH (e.g., "Hello—World")
    '\u2015': '-',  # HORIZONTAL BAR
    '\u2212': '-',  # MINUS SIGN
    '\u00ad': '-',  # SOFT HYPHEN
}

def normalize_text(text):
    """Normalize special characters to ASCII equivalents for PDF compatibility"""
    for old, new in DASH_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text

# Usage: ALWAYS call normalize_text() before writing to PDF
text = normalize_text(user_input)
story.append(Paragraph(text, styles['body']))
```

#### CJK Font Support (Chinese/Japanese/Korean)

When creating PDFs with non-ASCII text (e.g., Chinese, Japanese, Korean), you MUST register a CJK-capable font first:

```python
import os
import platform
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_cjk_font():
    """Register a CJK-capable font based on the operating system"""
    system = platform.system()

    if system == "Darwin":  # macOS
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",
            "/Library/Fonts/Arial Unicode.ttf",
            "/System/Library/Fonts/STHeiti Medium.ttc",
        ]
    elif system == "Windows":
        font_paths = [
            "C:/Windows/Fonts/msyh.ttc",  # Microsoft YaHei
            "C:/Windows/Fonts/simsun.ttc",  # SimSun
        ]
    else:  # Linux
        font_paths = [
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("CJKFont", font_path, subfontIndex=0))
            return "CJKFont"
    return None

# Register CJK font before creating PDF
cjk_font = register_cjk_font()
```

#### Professional Styles (MUST USE)

Always use these well-designed styles for professional-looking PDFs:

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor

PRIMARY_COLOR = HexColor('#1a365d')
ACCENT_COLOR = HexColor('#2b6cb0')

def get_professional_styles(cjk_font='CJKFont'):
    """Return a dict of professional styles for PDF generation"""
    return {
        'title': ParagraphStyle(
            'Title', fontName=cjk_font, fontSize=28, leading=34,
            textColor=PRIMARY_COLOR, spaceAfter=20, alignment=1, wordWrap='CJK'
        ),
        'subtitle': ParagraphStyle(
            'Subtitle', fontName=cjk_font, fontSize=14, leading=18,
            textColor=HexColor('#4a5568'), spaceAfter=30, alignment=1, wordWrap='CJK'
        ),
        'h1': ParagraphStyle(
            'H1', fontName=cjk_font, fontSize=20, leading=26,
            textColor=PRIMARY_COLOR, spaceBefore=24, spaceAfter=12, wordWrap='CJK'
        ),
        'h2': ParagraphStyle(
            'H2', fontName=cjk_font, fontSize=16, leading=22,
            textColor=ACCENT_COLOR, spaceBefore=18, spaceAfter=8, wordWrap='CJK'
        ),
        'body': ParagraphStyle(
            'Body', fontName=cjk_font, fontSize=11, leading=18,
            textColor=HexColor('#2d3748'), spaceBefore=0, spaceAfter=10,
            firstLineIndent=0, wordWrap='CJK'
        ),
        'caption': ParagraphStyle(
            'Caption', fontName=cjk_font, fontSize=9, leading=12,
            textColor=HexColor('#718096'), alignment=1, spaceBefore=6, spaceAfter=12, wordWrap='CJK'
        ),
    }

# Usage
styles = get_professional_styles('CJKFont')
story.append(Paragraph("标题 Title", styles['title']))
story.append(Paragraph("第一章 Chapter 1", styles['h1']))
story.append(Paragraph("正文内容...", styles['body']))
```

#### Professional Table Styles

```python
from reportlab.lib.colors import HexColor
from reportlab.platypus import Table, LongTable, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

def _wrap_cells(data, cjk_font='CJKFont'):
    """Wrap every cell in a Paragraph so text auto-wraps inside cells"""
    header_style = ParagraphStyle(
        'TableHeader', fontName=cjk_font, fontSize=11, leading=14,
        textColor=colors.white, wordWrap='CJK', splitLongWords=1,
    )
    body_style = ParagraphStyle(
        'TableBody', fontName=cjk_font, fontSize=10, leading=13,
        wordWrap='CJK', splitLongWords=1,
    )
    wrapped = []
    for i, row in enumerate(data):
        style = header_style if i == 0 else body_style
        wrapped.append([Paragraph(str(cell), style) for cell in row])
    return wrapped

def create_styled_table(data, col_widths=None, is_large=False):
    """Create a professionally styled table with auto-wrapping cells"""
    wrapped_data = _wrap_cells(data)
    TableClass = LongTable if is_large else Table
    table = TableClass(wrapped_data, colWidths=col_widths, repeatRows=1 if is_large else 0)

    table.setStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#2b6cb0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BACKGROUND', (0, 1), (-1, -1), HexColor('#f7fafc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#f7fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#e2e8f0')),
    ])
    return table
```

#### Inline Text Formatting

Use HTML-like tags inside Paragraph for rich text:

```python
from reportlab.platypus import Paragraph

text = """
<b>粗体 Bold</b>, <i>斜体 Italic</i>, <u>下划线 Underline</u>
<font color="#2b6cb0">蓝色文字 Blue text</font>
<font size="14">大字号 Larger</font>, <font size="9">小字号 Smaller</font>
化学式: H<sub>2</sub>O, 数学: E=mc<sup>2</sup>
<br/>换行 Line break
"""
story.append(Paragraph(text, styles['body']))
```

| Tag | Effect |
|-----|--------|
| `<b>` | **粗体** |
| `<i>` | *斜体* |
| `<u>` | 下划线 |
| `<font color="...">` | 颜色 |
| `<font size="...">` | 字号 |
| `<sub>` | 下标 |
| `<sup>` | 上标 |
| `<br/>` | 换行 |

#### Text Alignment

```python
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle

left_style = ParagraphStyle('Left', alignment=TA_LEFT)
center_style = ParagraphStyle('Center', alignment=TA_CENTER)
right_style = ParagraphStyle('Right', alignment=TA_RIGHT)
justify_style = ParagraphStyle('Justify', alignment=TA_JUSTIFY)
```

#### Page Geometry Constants (MUST DEFINE)

All layout decisions (divider widths, image sizing, table widths) derive from these constants. Define them once at the top of your script:

```python
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch

PAGE_SIZE = letter
PAGE_WIDTH, PAGE_HEIGHT = PAGE_SIZE

TOP_MARGIN = 0.75 * inch
BOTTOM_MARGIN = 0.75 * inch
LEFT_MARGIN = 0.75 * inch
RIGHT_MARGIN = 0.75 * inch

CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
CONTENT_HEIGHT = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN

IMAGE_MAX_WIDTH = CONTENT_WIDTH * 0.95
IMAGE_MIN_WIDTH = CONTENT_WIDTH * 0.3
IMAGE_MAX_HEIGHT = CONTENT_HEIGHT * 0.6
```

#### Colored Divider Lines

Add decorative divider lines under titles and headings for visual hierarchy:

```python
from reportlab.platypus import Flowable
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch

class ColoredDivider(Flowable):
    """A colored horizontal divider line"""
    def __init__(self, width, height=2, color=HexColor('#2b6cb0'), space_before=6, space_after=12):
        Flowable.__init__(self)
        self.width = width
        self.height = height
        self.color = color
        self.spaceAfter = space_after
        self.spaceBefore = space_before

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=0)

def title_divider():
    """Wide accent divider for document title"""
    return ColoredDivider(CONTENT_WIDTH, height=3, color=HexColor('#2b6cb0'), space_after=20)

def h1_divider():
    """Medium divider for H1 headings"""
    return ColoredDivider(CONTENT_WIDTH * 0.3, height=2, color=HexColor('#2b6cb0'), space_after=12)

def subtle_divider():
    """Thin gray divider for sections"""
    return ColoredDivider(CONTENT_WIDTH, height=1, color=HexColor('#e2e8f0'), space_after=10)

# Usage in story
story.append(Paragraph("报告标题 Report Title", styles['title']))
story.append(title_divider())  # Accent line under title

story.append(Paragraph("第一章 Chapter 1", styles['h1']))
story.append(h1_divider())  # Short accent line under H1

story.append(Paragraph("正文内容...", styles['body']))
story.append(subtle_divider())  # Subtle section separator
```

#### Document Setup with Proper Margins

```python
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate

doc = SimpleDocTemplate(
    "report.pdf",
    pagesize=letter,
    leftMargin=0.75*inch,
    rightMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch,
)
```

#### Pagination Best Practices (IMPORTANT)

**Core Principle**: Let content flow naturally. Minimize `PageBreak` and `KeepTogether` usage. **NEVER** use `KeepTogether` directly in business code — use `add_figure()` or `add_small_table()` exclusively.

| Content | How to Add | KeepTogether? | PageBreak? |
|---------|-----------|---------------|------------|
| Cover page | `story.append()` + `PageBreak()` after | No | **Only after cover** |
| **Headings** | `story.append()` directly | **NO** | **NO** |
| **Paragraphs** | `story.append()` directly | **NO** | **NO** |
| Images + captions | `add_figure(story, path, caption, styles)` | Internal | No |
| Small tables (≤5 rows) | `add_small_table(story, table)` | Internal | No |
| Large tables | `LongTable(..., repeatRows=1)` | No | No |

**⚠️ COMMON MISTAKE #1 - Too many PageBreaks:**
```python
# WRONG: Do NOT add PageBreak before chapters/sections!
story.append(PageBreak())  # Creates wasted blank space!
story.append(Paragraph("Chapter 2", heading_style))

# CORRECT: Just add heading directly, content flows naturally
story.append(Paragraph("Chapter 2", heading_style))
```
**Rule: Use PageBreak ONLY once after cover page. Never use PageBreak anywhere else!**

**⚠️ COMMON MISTAKE #2 - KeepTogether on headings/paragraphs:**
```python
# WRONG: Creates half-page blank spaces!
story.append(KeepTogether([
    Paragraph("Chapter 2", heading_style),
    Paragraph("Long content...", body_style),
]))

# CORRECT: Add directly, let content flow and split naturally
story.append(Paragraph("Chapter 2", heading_style))
story.append(Paragraph("Long content...", body_style))
```

**Complete Example:**
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, KeepTogether

# 1. Define normalize_text() for special character handling (use DASH_REPLACEMENTS from above)
def normalize_text(text):
    for old, new in DASH_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text

# 2. Register CJK font first (use register_cjk_font() from above)
register_cjk_font()

# 3. Setup document with proper margins
doc = SimpleDocTemplate("report.pdf", pagesize=letter,
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    topMargin=0.75*inch, bottomMargin=0.75*inch)

# 4. Use professional styles (use get_professional_styles() from above)
styles = get_professional_styles('CJKFont')

# --- KeepTogether encapsulation (ONLY place allowed to use KeepTogether) ---
KEEP_TOGETHER_THRESHOLD = CONTENT_HEIGHT * 0.6

def add_figure(story, image_path, caption_text, styles):
    img = safe_image(image_path)
    caption = Paragraph(normalize_text(caption_text), styles['caption'])
    block_h = img.drawHeight + 20
    if block_h <= KEEP_TOGETHER_THRESHOLD:
        story.append(KeepTogether([img, caption]))
    else:
        img.keepWithNext = True
        story.append(img)
        story.append(caption)

def add_small_table(story, table_flowable):
    story.append(KeepTogether([table_flowable]))

story = []

# Cover - use PageBreak ONLY here
story.append(Spacer(1, 2*inch))
story.append(Paragraph(normalize_text("报告标题 Report Title"), styles['title']))
story.append(Paragraph(normalize_text("副标题 Subtitle"), styles['subtitle']))
story.append(PageBreak())

# Headings & Paragraphs - add directly (NO KeepTogether, NO PageBreak)
story.append(Paragraph(normalize_text("第一章 Introduction"), styles['h1']))
story.append(Paragraph(normalize_text("正文内容自然流动，可跨页分割..."), styles['body']))
story.append(Paragraph(normalize_text("1.1 背景 Background"), styles['h2']))
story.append(Paragraph(normalize_text("更多内容..."), styles['body']))

# Images - use add_figure() (KeepTogether decided internally)
add_figure(story, "fig.png", "图 1: 说明文字", styles)

# Small tables - use add_small_table()
add_small_table(story, create_styled_table(small_data))

doc.build(story)
```

### Charts & Diagrams (Image Insertion)

**Tool selection:**

| Scenario | Tool | When to Use |
|----------|------|-------------|
| Data charts (bar, line, pie, scatter, heatmap) | `matplotlib` + `seaborn` | Quantitative data visualization with axes, legends, and labels |
| Sequence / State / Gantt / Class diagram | `PlantUML` | UML-style diagrams with rich semantics (participants, messages, timelines) |
| Flowchart / Architecture / Network topology | `Graphviz` (`dot`) | Directed/undirected graphs with nodes and edges; system architecture, dependency graphs |

**Decision guide:**
- 有**数值数据**要展示 → `matplotlib` + `seaborn`
- 有**时序交互**或**甘特图/类图** → `PlantUML`
- 有**节点-边关系**（流程图、架构图、依赖图、网络拓扑） → `Graphviz`

### matplotlib + seaborn - Data Charts

**⚠️ CRITICAL: NEVER call `sns.set_theme()` or `sns.set_style()` directly in your code.** Both reset `matplotlib.rcParams` including font settings, which causes CJK text (Chinese/Japanese/Korean) to render as empty boxes. Always use the provided `setup_matplotlib.py` script instead:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from setup_matplotlib import init_plot_env
init_plot_env()

import matplotlib.pyplot as plt
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

#### Chart Creation (OO API)

Always use the object-oriented API (`fig, ax`) and constrain `figsize` to fit the PDF content area:

```python
MAX_FIG_WIDTH = CONTENT_WIDTH / 72

fig, ax = plt.subplots(figsize=(MAX_FIG_WIDTH, 4))
sns.barplot(x=['Q1', 'Q2', 'Q3', 'Q4'], y=[120, 135, 142, 158], ax=ax, palette="Blues_d")
ax.set_title('季度销售 Quarterly Sales')
ax.set_xlabel('季度')
ax.set_ylabel('销售额')
fig.tight_layout()
fig.savefig('chart.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

#### Embed Chart in PDF (Overflow-Safe)

```python
from PIL import Image as PILImage
from reportlab.platypus import Image, KeepTogether, Paragraph
from reportlab.lib.units import inch
import os

def safe_image(path):
    pil_img = PILImage.open(path)
    orig_w_px, orig_h_px = pil_img.size
    dpi_x, dpi_y = pil_img.info.get('dpi', (72, 72))
    orig_w_pt = orig_w_px / dpi_x * 72
    orig_h_pt = orig_h_px / dpi_y * 72

    display_w = max(min(orig_w_pt, IMAGE_MAX_WIDTH), IMAGE_MIN_WIDTH)
    scale = display_w / orig_w_pt
    display_h = orig_h_pt * scale

    if display_h > IMAGE_MAX_HEIGHT:
        display_h = IMAGE_MAX_HEIGHT
        display_w = display_w * (IMAGE_MAX_HEIGHT / (orig_h_pt * scale))

    img = Image(path, width=display_w, height=display_h)
    img.hAlign = 'CENTER'
    return img

KEEP_TOGETHER_THRESHOLD = CONTENT_HEIGHT * 0.6

def add_figure(story, image_path, caption_text, styles):
    img = safe_image(image_path)
    caption = Paragraph(caption_text, styles['caption'])
    block_h = img.drawHeight + 20
    if block_h <= KEEP_TOGETHER_THRESHOLD:
        story.append(KeepTogether([img, caption]))
    else:
        img.keepWithNext = True
        story.append(img)
        story.append(caption)

def safe_image_or_split(path, styles):
    pil_img = PILImage.open(path)
    orig_w_px, orig_h_px = pil_img.size
    dpi_x, dpi_y = pil_img.info.get('dpi', (72, 72))
    orig_h_pt = orig_h_px / dpi_y * 72
    if orig_h_pt <= CONTENT_HEIGHT:
        return [safe_image(path)]
    num_chunks = int(orig_h_pt / IMAGE_MAX_HEIGHT) + 1
    chunk_h_px = orig_h_px // num_chunks
    parts = []
    for i in range(num_chunks):
        top = i * chunk_h_px
        bottom = min(top + chunk_h_px, orig_h_px)
        chunk = pil_img.crop((0, top, orig_w_px, bottom))
        chunk_path = f"{os.path.splitext(path)[0]}_part{i+1}.png"
        chunk.save(chunk_path, dpi=(dpi_x, dpi_y))
        parts.append(safe_image(chunk_path))
    return parts

add_figure(story, 'chart.png', "图 1: 季度销售趋势", styles)
```

**Long image handling:** If a diagram (e.g., a complex sequence diagram) is taller than one page, use `safe_image_or_split()` which auto-crops the image into page-friendly chunks:
```python
for part in safe_image_or_split('long_sequence.png', styles):
    story.append(part)
```
Prefer splitting at the **source** (e.g., breaking one PlantUML diagram into multiple smaller diagrams) over auto-cropping, as source-level splitting preserves logical boundaries.

### PlantUML - Structural Diagrams

Use PlantUML for flowcharts, sequence diagrams, state diagrams, class diagrams, Gantt charts, etc. The `plantuml` command is pre-installed and available in PATH.

#### Render PlantUML to PNG

Use the standalone script at `scripts/render_plantuml.py` which provides:
- **`returncode` checking**: non-zero exit codes are always caught
- **Syntax error parsing**: `PlantUMLSyntaxError` with line numbers extracted from stderr
- **Retry on missing output**: configurable `retries` for transient failures
- **Gantt-safe DPI**: auto-skips `-Sdpi` for `@startgantt` diagrams

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from render_plantuml import render_plantuml, PlantUMLSyntaxError, PlantUMLError, PLANTUML_THEME

puml_code = f"""
@startuml
{PLANTUML_THEME}
left to right direction
rectangle "开始" as A
rectangle "条件判断" as B
rectangle "处理A" as C
rectangle "处理B" as D
rectangle "结束" as E
A --> B
B --> C : 是
B --> D : 否
C --> E
D --> E
@enduml
"""
try:
    render_plantuml(puml_code, 'flowchart.png')
except PlantUMLSyntaxError as e:
    print(f"Syntax error in PlantUML code, fix the puml source and retry:\\n{e}")
except PlantUMLError as e:
    print(f"PlantUML rendering failed:\\n{e}")
```

#### Embed PlantUML Image in PDF

Use the same `add_figure()` helper above to embed the output PNG:

```python
add_figure(story, 'flowchart.png', "图 2: 业务流程图", styles)
```

#### PlantUML Diagram Types

| Type | Syntax | Use Case |
|------|--------|----------|
| 时序图 | `@startuml` + `A -> B : msg` | API 调用、交互流程 |
| 流程图 | `@startuml` + `start` / `if` / `endif` | 业务流程、决策树 |
| 状态图 | `@startuml` + `[*] --> State` | 状态机、生命周期 |
| 类图 | `@startuml` + `class Foo` | 类结构、数据模型 |
| 甘特图 | `@startgantt` / `@endgantt` | 项目计划、时间线 |

#### Sequence Diagram Example

```python
seq_code = f"""
@startuml
{PLANTUML_THEME}
participant "客户端" as C
participant "服务器" as S
database "数据库" as D
C -> S : POST /api/login
S -> D : 查询用户
D --> S : 用户数据
S --> C : JWT Token
@enduml
"""
try:
    render_plantuml(seq_code, 'sequence.png')
except PlantUMLSyntaxError as e:
    print(f"Syntax error — fix puml source:\\n{e}")
```

#### Gantt Chart Example

```python
gantt_code = """
@startgantt
title 项目计划
project starts 2025-01-01
[需求分析] lasts 10 days
[系统设计] lasts 15 days
[系统设计] starts at [需求分析]'s end
[开发实现] lasts 30 days
[开发实现] starts at [系统设计]'s end
[测试验收] lasts 10 days
[测试验收] starts at [开发实现]'s end
@endgantt
"""
try:
    render_plantuml(gantt_code, 'gantt.png')
except PlantUMLSyntaxError as e:
    print(f"Syntax error — fix puml source:\\n{e}")
```

**⚠️ PlantUML Tips:**
- **Always inject `PLANTUML_THEME`** after `@startuml` — it defines fonts, colors, and skinparam for all element types
- **Semantic stereotypes**: `participant` (services), `actor` (users), `database` (storage), `collections` (middleware) — colors auto-applied via PLANTUML_THEME
- Use `left to right direction` for horizontal layout to reduce vertical space
- Keep node text concise to avoid diagram overflow
- **Avoid `-Sdpi` for `@startgantt`** (PlantUML ≤1.2020 returns non-zero exit code); other diagram types can use `-Sdpi=150` for higher quality

### Graphviz - Flowcharts & Architecture Diagrams

Use Graphviz (`dot`) for directed/undirected graphs: flowcharts, architecture diagrams, dependency graphs, network topologies. Graphviz excels at automatic layout and handles complex node-edge relationships well. `dot` is pre-installed in the environment.

#### Render Graphviz to PNG

Use the standalone script at `scripts/render_graphviz.py` which provides:
- **`returncode` checking**: non-zero exit codes are always caught
- **Syntax error parsing**: `GraphvizSyntaxError` with line numbers extracted from stderr
- **Auto size injection**: pass `max_width_in` / `max_height_in` to constrain output dimensions

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from render_graphviz import render_graphviz, GraphvizSyntaxError, GraphvizError, GRAPHVIZ_DPI

GRAPHVIZ_MAX_WIDTH_IN = IMAGE_MAX_WIDTH / 72          # ≈6.65" for letter
GRAPHVIZ_MAX_HEIGHT_IN = IMAGE_MAX_HEIGHT / 72         # ≈5.6" for letter
```

#### Flowchart Example

```python
flowchart = """
digraph {
    rankdir=LR
    nodesep=0.65
    ranksep=0.85
    node [shape=box style="rounded,filled" fillcolor="#E8F4FD" fontname="Noto Sans CJK SC" fontsize=16 margin="0.40,0.28"]
    edge [fontname="Noto Sans CJK SC" fontsize=14 penwidth=1.5]

    start [label="开始" shape=ellipse fillcolor="#C8E6C9"]
    cond [label="条件判断" shape=diamond fillcolor="#FFF9C4"]
    procA [label="处理A"]
    procB [label="处理B"]
    end_ [label="结束" shape=ellipse fillcolor="#FFCDD2"]

    start -> cond
    cond -> procA [label="是"]
    cond -> procB [label="否"]
    procA -> end_
    procB -> end_
}
"""
try:
    render_graphviz(flowchart, 'flowchart.png',
                    max_width_in=GRAPHVIZ_MAX_WIDTH_IN, max_height_in=GRAPHVIZ_MAX_HEIGHT_IN)
except GraphvizSyntaxError as e:
    print(f"Syntax error — fix dot source:\\n{e}")
except GraphvizError as e:
    print(f"Graphviz rendering failed:\\n{e}")
```

#### Architecture Diagram Pattern

Architecture diagrams follow the same syntax — use `subgraph cluster_xxx` for layered grouping (e.g., frontend / backend / data layers), `compound=true` for cross-cluster edges, and `margin=20` inside clusters. See the flowchart example above for node/edge styling conventions.

#### Multi-Row Layout Example (Flywheel / Grid)

When a diagram has 4+ nodes in a flat structure (e.g., flywheel, module overview, value chain), **always** arrange them in a 2-3 row grid using `{rank=same}` and invisible edges. This prevents the graph from becoming a single wide row or a single tall column, both of which get shrunk to fit the page.
**Target aspect ratio 4:3 ~ 16:9**: Distribute nodes evenly across rows (e.g., 6 nodes → 3+3, 8 nodes → 3+3+2 or 4+4)

```python
flywheel = """
digraph {
    rankdir=TB
    nodesep=0.65
    ranksep=0.85
    node [shape=box style="rounded,filled" fillcolor="#E8F4FD" fontname="Noto Sans CJK SC" fontsize=16 margin="0.40,0.28"]
    edge [fontname="Noto Sans CJK SC" fontsize=14 penwidth=1.5]

    a [label="用户增长" fillcolor="#BBDEFB"]
    b [label="内容生产" fillcolor="#C8E6C9"]
    c [label="算法推荐" fillcolor="#FFE0B2"]
    d [label="商业变现" fillcolor="#E1BEE7"]
    e [label="数据反馈" fillcolor="#FFF9C4"]
    f [label="体验优化" fillcolor="#FFCDD2"]

    {rank=same; a; b; c}
    {rank=same; d; e; f}

    a -> b -> c
    c -> d [style=invis]
    d -> e -> f
    f -> a [label="飞轮循环" constraint=false]
}
"""
try:
    render_graphviz(flywheel, 'flywheel.png',
                    max_width_in=GRAPHVIZ_MAX_WIDTH_IN, max_height_in=GRAPHVIZ_MAX_HEIGHT_IN)
except GraphvizSyntaxError as e:
    print(f"Syntax error — fix dot source:\\n{e}")
```

**⚠️ Graphviz Tips:**
- **Node fontsize 16–20**: < 16 becomes illegible after PDF scaling; sync `margin` (`"0.40,0.28"`) and `nodesep`/`ranksep` (`0.65`/`0.85`) when increasing font size
- **4+ flat nodes → MUST multi-row grid**: `{rank=same; ...}` to force 2-3 per row; `style=invis` edges for row transitions; `constraint=false` for back-edges
- **Target aspect ratio 4:3 ~ 16:9**: distribute nodes evenly (6 → 3+3, 8 → 4+4 or 3+3+2)
- **Size auto-injected**: `render_graphviz()` injects `size` + `ratio="compress"` so `safe_image()` needs no extra scaling
- **`penwidth=1.5`**: default 1.0 is too thin at high DPI
- **Cluster styling**: `margin=20` inside subgraphs; cluster title `fontsize` ≥ 16
- **Layout engines**: `dot` (hierarchical, default), `neato` (force-directed), `fdp` (large graphs)
- **CJK**: set `fontname="Noto Sans CJK SC"` on both nodes and edges

### ⚠️ Image Overflow Protection (MANDATORY)

All chart and diagram images MUST follow these rules to avoid overflowing the page:

1. **Use `safe_image()`**: Always use the DPI-aware `safe_image()` function (defined above) instead of hardcoding Image dimensions
2. **Use `add_figure()`**: Always insert images via `add_figure(story, path, caption, styles)` — it decides KeepTogether internally based on block height
3. **NEVER use `KeepTogether` directly**: All KeepTogether usage is encapsulated inside `add_figure()` and `add_small_table()`. Business code must not contain bare `KeepTogether([...])`
4. **Height-aware KeepTogether**: `add_figure()` only uses KeepTogether when block height ≤ `CONTENT_HEIGHT * 0.6`; taller blocks use `keepWithNext` soft-binding instead
5. **Page geometry constants**: All sizing derives from `IMAGE_MAX_WIDTH`, `IMAGE_MIN_WIDTH`, `IMAGE_MAX_HEIGHT` (see Page Geometry Constants above)
6. **DPI handling**: `safe_image()` reads actual DPI from image metadata (defaults to 72 if absent) and computes physical size in points — no hardcoded `72.0/150` ratios
7. **Height constraint**: Images taller than `IMAGE_MAX_HEIGHT` (60% of content height) are shrunk proportionally
8. **Long images**: Images taller than `CONTENT_HEIGHT` should use `safe_image_or_split()` or, preferably, be split at the diagram source
9. **Center alignment**: `safe_image()` sets `img.hAlign = 'CENTER'` automatically
10. **matplotlib figsize**: Constrain width to `CONTENT_WIDTH / 72` inches (≈6.5" for letter), e.g. `figsize=(CONTENT_WIDTH / 72, 4)`
11. **PlantUML**: Use `-Sdpi=150` for higher quality (except `@startgantt` — omit `-Sdpi` for Gantt charts); use `left to right direction` to reduce vertical space
12. **Graphviz**: Use `-Gdpi=150` for consistent resolution with other tools

## Command-Line Tools

### pdftotext (poppler-utils)
```bash
# Extract text
pdftotext input.pdf output.txt

# Extract text preserving layout
pdftotext -layout input.pdf output.txt

# Extract specific pages
pdftotext -f 1 -l 5 input.pdf output.txt  # Pages 1-5
```

### qpdf
```bash
# Merge PDFs
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf

# Split pages
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf --pages . 6-10 -- pages6-10.pdf

# Rotate pages
qpdf input.pdf output.pdf --rotate=+90:1  # Rotate page 1 by 90 degrees

# Remove password
qpdf --password=***REDACTED***
```

### pdftk (if available)
```bash
# Merge
pdftk file1.pdf file2.pdf cat output merged.pdf

# Split
pdftk input.pdf burst

# Rotate
pdftk input.pdf rotate 1east output rotated.pdf
```

## Common Tasks

For OCR (pytesseract), watermarking, image extraction, and password protection → See **REFERENCE.md § Common Tasks**.

## Critical Rules for PDF Generation

- **NEVER call `sns.set_theme()`, `sns.set_style()`, `sns.set()`, `sns.reset_defaults()`, or `sns.reset_orig()` directly** — all of these reset `matplotlib.rcParams` and destroy CJK font settings, causing Chinese/Japanese/Korean text to render as empty boxes. Always use `setup_matplotlib.py`: call `init_plot_env()` at the start, and `safe_set_style()` / `safe_set_theme()` for later changes
- **Register CJK font before any text rendering** — use `register_cjk_font()` for reportlab; use `init_plot_env()` for matplotlib
- **Normalize special Unicode characters** — call text normalization before writing to PDF to avoid rendering issues with dashes, quotes, etc.
- **Use `add_figure()` / `add_small_table()` for images** — NEVER use `KeepTogether` directly in business code
- **Define page geometry constants once** — all layout decisions derive from `PAGE_WIDTH`, `CONTENT_WIDTH`, `IMAGE_MAX_WIDTH`, etc.
- **Validate image dimensions** — always use `safe_image()` with overflow protection to prevent images exceeding page bounds

## Quick Reference

| Task | Best Tool | Command/Code |
|------|-----------|--------------|
| Merge PDFs | pypdf | `writer.add_page(page)` |
| Split PDFs | pypdf | One page per file |
| Extract text | pdfplumber | `page.extract_text()` |
| Extract tables | pdfplumber | `page.extract_tables()` |
| Create PDFs | reportlab | Canvas or Platypus |
| Data charts | matplotlib + seaborn | `sns.barplot()` / `fig.savefig()` |
| Sequence/State/Gantt | PlantUML (`plantuml`) | `render_plantuml()` → PNG |
| Flowcharts/Architecture | Graphviz (`dot`) | `render_graphviz()` → PNG |
| Command line merge | qpdf | `qpdf --empty --pages ...` |
| OCR scanned PDFs | pytesseract | Convert to image first |
| Fill PDF forms | pdf-lib or pypdf (see FORMS.md) | See FORMS.md |

## Next Steps

- For advanced pypdfium2 usage, see REFERENCE.md
- For JavaScript libraries (pdf-lib), see REFERENCE.md
- If you need to fill out a PDF form, follow the instructions in FORMS.md
- For troubleshooting guides, see REFERENCE.md
