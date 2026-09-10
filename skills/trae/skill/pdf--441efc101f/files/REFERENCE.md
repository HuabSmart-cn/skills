# PDF Processing Advanced Reference

This document contains **only** advanced features and additional libraries that are **not** in SKILL.md.

> **Lookup guide — which file to read:**
>
> | Topic | Where |
> |-------|-------|
> | reportlab basics, page geometry, `normalize_text()`, `safe_image()` / `add_figure()` | **SKILL.md** |
> | PlantUML render, theme, examples (sequence / flowchart / Gantt) | **SKILL.md § PlantUML** |
> | Graphviz render, examples (flowchart / architecture / flywheel), tips | **SKILL.md § Graphviz** |
> | Image Overflow Protection 12-rule checklist | **SKILL.md § Image Overflow Protection** |
> | CJK font registration (`pick_font`), matplotlib CJK setup | **SKILL.md** |
> | Command-line tools (pdftotext / qpdf / pdftk) | **SKILL.md § Command-Line Tools** |
> | Common tasks (OCR, watermark, image extraction, password) | **this file** |
> | pypdfium2, pdf-lib, pdfjs-dist | **this file** |
> | pdfplumber advanced (coordinates, custom table settings) | **this file** |
> | reportlab advanced pagination, LongTable, CJK Word Wrap | **this file** |
> | Complex workflows (batch, cropping, figure extraction) | **this file** |
> | Performance tips, troubleshooting | **this file** |
>
> **Rule**: If a topic exists in SKILL.md, SKILL.md is the single source of truth. This file never duplicates it.

## pypdfium2 Library (Apache/BSD License)

### Overview
pypdfium2 is a Python binding for PDFium (Chromium's PDF library). It's excellent for fast PDF rendering, image generation, and serves as a PyMuPDF replacement.

### Render PDF to Images
```python
import pypdfium2 as pdfium
from PIL import Image

# Load PDF
pdf = pdfium.PdfDocument("document.pdf")

# Render page to image
page = pdf[0]  # First page
bitmap = page.render(
    scale=2.0,  # Higher resolution
    rotation=0  # No rotation
)

# Convert to PIL Image
img = bitmap.to_pil()
img.save("page_1.png", "PNG")

# Process multiple pages
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.5)
    img = bitmap.to_pil()
    img.save(f"page_{i+1}.jpg", "JPEG", quality=90)
```

### Extract Text with pypdfium2
```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("document.pdf")
for i, page in enumerate(pdf):
    text = page.get_text()
    print(f"Page {i+1} text length: {len(text)} chars")
```

## JavaScript Libraries

### pdf-lib (MIT License)

pdf-lib is a powerful JavaScript library for creating and modifying PDF documents in any JavaScript environment.

#### Load and Manipulate Existing PDF
```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

async function manipulatePDF() {
    // Load existing PDF
    const existingPdfBytes = fs.readFileSync('input.pdf');
    const pdfDoc = await PDFDocument.load(existingPdfBytes);

    // Get page count
    const pageCount = pdfDoc.getPageCount();
    console.log(`Document has ${pageCount} pages`);

    // Add new page
    const newPage = pdfDoc.addPage([600, 400]);
    newPage.drawText('Added by pdf-lib', {
        x: 100,
        y: 300,
        size: 16
    });

    // Save modified PDF
    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('modified.pdf', pdfBytes);
}
```

#### Create Complex PDFs from Scratch
```javascript
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import fs from 'fs';

async function createPDF() {
    const pdfDoc = await PDFDocument.create();

    // Add fonts
    const helveticaFont = await pdfDoc.embedFont(StandardFonts.Helvetica);
    const helveticaBold = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

    // Add page
    const page = pdfDoc.addPage([595, 842]); // A4 size
    const { width, height } = page.getSize();

    // Add text with styling
    page.drawText('Invoice #12345', {
        x: 50,
        y: height - 50,
        size: 18,
        font: helveticaBold,
        color: rgb(0.2, 0.2, 0.8)
    });

    // Add rectangle (header background)
    page.drawRectangle({
        x: 40,
        y: height - 100,
        width: width - 80,
        height: 30,
        color: rgb(0.9, 0.9, 0.9)
    });

    // Add table-like content
    const items = [
        ['Item', 'Qty', 'Price', 'Total'],
        ['Widget', '2', '$50', '$100'],
        ['Gadget', '1', '$75', '$75']
    ];

    let yPos = height - 150;
    items.forEach(row => {
        let xPos = 50;
        row.forEach(cell => {
            page.drawText(cell, {
                x: xPos,
                y: yPos,
                size: 12,
                font: helveticaFont
            });
            xPos += 120;
        });
        yPos -= 25;
    });

    const pdfBytes = await pdfDoc.save();
    fs.writeFileSync('created.pdf', pdfBytes);
}
```

#### Advanced Merge and Split Operations
```javascript
import { PDFDocument } from 'pdf-lib';
import fs from 'fs';

async function mergePDFs() {
    // Create new document
    const mergedPdf = await PDFDocument.create();

    // Load source PDFs
    const pdf1Bytes = fs.readFileSync('doc1.pdf');
    const pdf2Bytes = fs.readFileSync('doc2.pdf');

    const pdf1 = await PDFDocument.load(pdf1Bytes);
    const pdf2 = await PDFDocument.load(pdf2Bytes);

    // Copy pages from first PDF
    const pdf1Pages = await mergedPdf.copyPages(pdf1, pdf1.getPageIndices());
    pdf1Pages.forEach(page => mergedPdf.addPage(page));

    // Copy specific pages from second PDF (pages 0, 2, 4)
    const pdf2Pages = await mergedPdf.copyPages(pdf2, [0, 2, 4]);
    pdf2Pages.forEach(page => mergedPdf.addPage(page));

    const mergedPdfBytes = await mergedPdf.save();
    fs.writeFileSync('merged.pdf', mergedPdfBytes);
}
```

### pdfjs-dist (Apache License)

PDF.js is Mozilla's JavaScript library for rendering PDFs in the browser.

#### Basic PDF Loading and Rendering
```javascript
import * as pdfjsLib from 'pdfjs-dist';

// Configure worker (important for performance)
pdfjsLib.GlobalWorkerOptions.workerSrc = './pdf.worker.js';

async function renderPDF() {
    // Load PDF
    const loadingTask = pdfjsLib.getDocument('document.pdf');
    const pdf = await loadingTask.promise;

    console.log(`Loaded PDF with ${pdf.numPages} pages`);

    // Get first page
    const page = await pdf.getPage(1);
    const viewport = page.getViewport({ scale: 1.5 });

    // Render to canvas
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    const renderContext = {
        canvasContext: context,
        viewport: viewport
    };

    await page.render(renderContext).promise;
    document.body.appendChild(canvas);
}
```

#### Extract Text with Coordinates
```javascript
import * as pdfjsLib from 'pdfjs-dist';

async function extractText() {
    const loadingTask = pdfjsLib.getDocument('document.pdf');
    const pdf = await loadingTask.promise;

    let fullText = '';

    // Extract text from all pages
    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();

        const pageText = textContent.items
            .map(item => item.str)
            .join(' ');

        fullText += `\n--- Page ${i} ---\n${pageText}`;

        // Get text with coordinates for advanced processing
        const textWithCoords = textContent.items.map(item => ({
            text: item.str,
            x: item.transform[4],
            y: item.transform[5],
            width: item.width,
            height: item.height
        }));
    }

    console.log(fullText);
    return fullText;
}
```

#### Extract Annotations and Forms
```javascript
import * as pdfjsLib from 'pdfjs-dist';

async function extractAnnotations() {
    const loadingTask = pdfjsLib.getDocument('annotated.pdf');
    const pdf = await loadingTask.promise;

    for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const annotations = await page.getAnnotations();

        annotations.forEach(annotation => {
            console.log(`Annotation type: ${annotation.subtype}`);
            console.log(`Content: ${annotation.contents}`);
            console.log(`Coordinates: ${JSON.stringify(annotation.rect)}`);
        });
    }
}
```

## Advanced Command-Line Operations

### poppler-utils Advanced Features

#### Extract Text with Bounding Box Coordinates
```bash
# Extract text with bounding box coordinates (essential for structured data)
pdftotext -bbox-layout document.pdf output.xml

# The XML output contains precise coordinates for each text element
```

#### Advanced Image Conversion
```bash
# Convert to PNG images with specific resolution
pdftoppm -png -r 300 document.pdf output_prefix

# Convert specific page range with high resolution
pdftoppm -png -r 600 -f 1 -l 3 document.pdf high_res_pages

# Convert to JPEG with quality setting
pdftoppm -jpeg -jpegopt quality=85 -r 200 document.pdf jpeg_output
```

#### Extract Embedded Images
```bash
# Extract all embedded images with metadata
pdfimages -j -p document.pdf page_images

# List image info without extracting
pdfimages -list document.pdf

# Extract images in their original format
pdfimages -all document.pdf images/img
```

### qpdf Advanced Features

#### Complex Page Manipulation
```bash
# Split PDF into groups of pages
qpdf --split-pages=3 input.pdf output_group_%02d.pdf

# Extract specific pages with complex ranges
qpdf input.pdf --pages input.pdf 1,3-5,8,10-end -- extracted.pdf

# Merge specific pages from multiple PDFs
qpdf --empty --pages doc1.pdf 1-3 doc2.pdf 5-7 doc3.pdf 2,4 -- combined.pdf
```

#### PDF Optimization and Repair
```bash
# Optimize PDF for web (linearize for streaming)
qpdf --linearize input.pdf optimized.pdf

# Remove unused objects and compress
qpdf --optimize-level=all input.pdf compressed.pdf

# Attempt to repair corrupted PDF structure
qpdf --check input.pdf
qpdf --fix-qdf damaged.pdf repaired.pdf

# Show detailed PDF structure for debugging
qpdf --show-all-pages input.pdf > structure.txt
```

#### Advanced Encryption
```bash
# Add password protection with specific permissions
qpdf --encrypt user_pass owner_pass 256 --print=none --modify=none -- input.pdf encrypted.pdf

# Check encryption status
qpdf --show-encryption encrypted.pdf

# Remove password protection (requires password)
qpdf --password=***REDACTED***
```

## Advanced Python Techniques

### pdfplumber Advanced Features

#### Extract Text with Precise Coordinates
```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]

    # Extract all text with coordinates
    chars = page.chars
    for char in chars[:10]:  # First 10 characters
        print(f"Char: '{char['text']}' at x:{char['x0']:.1f} y:{char['y0']:.1f}")

    # Extract text by bounding box (left, top, right, bottom)
    bbox_text = page.within_bbox((100, 100, 400, 200)).extract_text()
```

#### Advanced Table Extraction with Custom Settings
```python
import pdfplumber
import pandas as pd

with pdfplumber.open("complex_table.pdf") as pdf:
    page = pdf.pages[0]

    # Extract tables with custom settings for complex layouts
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
        "snap_tolerance": 3,
        "intersection_tolerance": 15
    }
    tables = page.extract_tables(table_settings)

    # Visual debugging for table extraction
    img = page.to_image(resolution=150)
    img.save("debug_layout.png")
```

### reportlab Advanced Features

#### Advanced Pagination Control

When creating multi-page documents, proper pagination prevents excessive blank space:

```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, LongTable, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

PAGE_WIDTH, PAGE_HEIGHT = letter
MARGIN = 0.75 * inch

doc = SimpleDocTemplate(
    "document.pdf",
    pagesize=letter,
    leftMargin=MARGIN,
    rightMargin=MARGIN,
    topMargin=MARGIN,
    bottomMargin=MARGIN
)

styles = getSampleStyleSheet()
story = []

# --- Cover Page (standalone) ---
cover_title_style = ParagraphStyle(
    'CoverTitle',
    parent=styles['Title'],
    fontSize=36,
    spaceAfter=30,
)
story.append(Spacer(1, 2 * inch))
story.append(Paragraph("Document Title", cover_title_style))
story.append(Paragraph("Subtitle or Author", styles['Normal']))
story.append(PageBreak())

# --- Body Content (flows naturally, can split across pages) ---
heading_style = ParagraphStyle(
    'Heading',
    parent=styles['Heading1'],
    spaceBefore=12,
    spaceAfter=6,
)
body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontSize=11,
    leading=14,
    spaceBefore=6,
    spaceAfter=6,
    wordWrap='CJK',
)

story.append(Paragraph("Chapter 1: Introduction", heading_style))
story.append(Paragraph("This is body text that can flow naturally across pages. "
                       "Long paragraphs will automatically split at page boundaries. "
                       "This maximizes page utilization and avoids blank space.", body_style))

# --- Image with Caption (KeepTogether decided by height heuristic) ---
KEEP_TOGETHER_THRESHOLD = CONTENT_HEIGHT * 0.6

def add_figure(story, image_path, caption, width=4*inch):
    caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, alignment=1)
    img = Image(image_path, width=width, height=width*0.75)
    block_h = img.drawHeight + 6 + 14
    if block_h <= KEEP_TOGETHER_THRESHOLD:
        story.append(KeepTogether([
            img,
            Spacer(1, 6),
            Paragraph(caption, caption_style)
        ]))
    else:
        img.keepWithNext = True
        story.append(img)
        story.append(Spacer(1, 6))
        story.append(Paragraph(caption, caption_style))

# add_figure(story, "chart.png", "Figure 1: Sales Chart")

# --- Small Table (kept together) ---
def add_small_table(story, data, col_widths):
    wrapped_data = _wrap_cells(data)
    table = Table(wrapped_data, colWidths=col_widths)
    table.setStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
        ('BACKGROUND', (0, 0), (-1, 0), '#CCCCCC'),
    ])
    story.append(KeepTogether([table]))

# --- Large Table (splits by rows, repeats header) ---
def add_large_table(story, data, col_widths):
    wrapped_data = _wrap_cells(data)
    table = LongTable(wrapped_data, colWidths=col_widths, repeatRows=1)
    table.splitByRow = True
    table.setStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, 'black'),
        ('BACKGROUND', (0, 0), (-1, 0), '#CCCCCC'),
    ])
    story.append(table)

doc.build(story)
```

#### Create Professional Reports with Tables (with CJK Support)
```python
import os
import platform
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register CJK font for non-ASCII text support
def register_cjk_font():
    system = platform.system()
    if system == "Darwin":
        paths = ["/Library/Fonts/Arial Unicode.ttf", "/System/Library/Fonts/STHeiti Medium.ttc"]
    elif system == "Windows":
        paths = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simsun.ttc"]
    else:
        paths = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"]
    for p in paths:
        if os.path.exists(p):
            pdfmetrics.registerFont(TTFont("CJKFont", p, subfontIndex=0))
            return "CJKFont"
    return "Helvetica"

cjk_font = register_cjk_font()

# Sample data with Chinese
data = [
    ['产品 Product', '第一季度 Q1', '第二季度 Q2', '第三季度 Q3', '第四季度 Q4'],
    ['部件 Widgets', '120', '135', '142', '158'],
    ['设备 Gadgets', '85', '92', '98', '105']
]

# Create PDF with table
doc = SimpleDocTemplate("report.pdf")
elements = []

# Add title with CJK support
styles = getSampleStyleSheet()
cjk_title_style = ParagraphStyle('CJKTitle', parent=styles['Title'], fontName=cjk_font)
title = Paragraph("季度销售报告 Quarterly Sales Report", cjk_title_style)
elements.append(title)

# Add table with advanced styling (use CJK font)
cell_style = ParagraphStyle('CellStyle', fontName=cjk_font, fontSize=10, leading=13, wordWrap='CJK', splitLongWords=1)
header_style = ParagraphStyle('HeaderStyle', fontName=cjk_font, fontSize=14, leading=17, textColor=colors.whitesmoke, wordWrap='CJK', splitLongWords=1)
wrapped_data = [[Paragraph(str(c), header_style) for c in data[0]]] + [[Paragraph(str(c), cell_style) for c in row] for row in data[1:]]
table = Table(wrapped_data)
table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
    ('GRID', (0, 0), (-1, -1), 1, colors.black)
]))
elements.append(table)

doc.build(elements)
```

#### matplotlib + seaborn Charts with CJK Support

When creating charts with matplotlib + seaborn for embedding in PDFs:

```python
import os, platform
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

def setup_matplotlib_cjk():
    system = platform.system()
    if system == "Darwin":
        font_names = ['Arial Unicode MS', 'PingFang SC', 'Heiti SC', 'STHeiti']
    elif system == "Windows":
        font_names = ['Microsoft YaHei', 'SimHei', 'SimSun']
    else:
        font_names = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'Droid Sans Fallback']
    available_fonts = [f.name for f in matplotlib.font_manager.fontManager.ttflist]
    for font_name in font_names:
        if font_name in available_fonts:
            plt.rcParams['font.sans-serif'] = [font_name] + plt.rcParams['font.sans-serif']
            plt.rcParams['axes.unicode_minus'] = False
            return font_name
    return None

setup_matplotlib_cjk()
sns.set_theme(style="whitegrid")

MAX_FIG_WIDTH = CONTENT_WIDTH / 72

fig, ax = plt.subplots(figsize=(MAX_FIG_WIDTH, 5))
labels = ['研发 R&D', '市场 Marketing', '运营 Operations', '销售 Sales']
sizes = [30, 25, 20, 25]
colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
ax.set_title('部门预算分配 Budget Allocation', fontsize=16)
ax.axis('equal')
fig.tight_layout()
fig.savefig('pie_chart.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

**Seaborn chart examples:**
```python
import pandas as pd

data = pd.DataFrame({
    '季度': ['Q1', 'Q2', 'Q3', 'Q4'] * 2,
    '销售额': [120, 135, 142, 158, 85, 92, 98, 105],
    '产品': ['部件'] * 4 + ['设备'] * 4
})

fig, ax = plt.subplots(figsize=(MAX_FIG_WIDTH, 4))
sns.barplot(data=data, x='季度', y='销售额', hue='产品', ax=ax, palette='Set2')
ax.set_title('产品季度对比')
fig.tight_layout()
fig.savefig('grouped_bar.png', dpi=150, bbox_inches='tight')
plt.close(fig)

fig, ax = plt.subplots(figsize=(MAX_FIG_WIDTH, 4))
sns.lineplot(data=data, x='季度', y='销售额', hue='产品', ax=ax, marker='o')
ax.set_title('销售趋势')
fig.tight_layout()
fig.savefig('line_chart.png', dpi=150, bbox_inches='tight')
plt.close(fig)
```

#### PlantUML Structural Diagrams (Advanced)

For render setup, theme, sequence/flowchart/Gantt examples → See **SKILL.md § PlantUML**.

This section only covers diagram types **not** in SKILL.md:

##### State Diagram Example

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from render_plantuml import render_plantuml, PlantUMLSyntaxError, PlantUMLError, PLANTUML_THEME

state_diagram = f"""
@startuml
{PLANTUML_THEME}
[*] --> 待审核
待审核 --> 审核中 : 提交
审核中 --> 已通过 : 批准
审核中 --> 已驳回 : 驳回
已驳回 --> 待审核 : 重新提交
已通过 --> [*]
@enduml
"""
try:
    render_plantuml(state_diagram, 'state.png')
except PlantUMLSyntaxError as e:
    print(f"Syntax error — fix puml source:\\n{e}")
```

#### Graphviz Flowcharts & Architecture Diagrams (Advanced)

For render setup, flowchart / architecture / flywheel examples, multi-row layout rules, and Graphviz tips → See **SKILL.md § Graphviz**.

#### Overflow-Safe Image Embedding

For `safe_image()`, `add_figure()`, and the full 12-rule Image Overflow Protection checklist → See **SKILL.md § Image Overflow Protection**.

#### Long Text with CJK Word Wrap

For long Chinese text that needs proper line breaking:

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle

# IMPORTANT: Set wordWrap='CJK' for proper Chinese line breaking
cjk_paragraph_style = ParagraphStyle(
    'CJKParagraph',
    fontName='CJKFont',
    fontSize=12,
    leading=18,
    wordWrap='CJK',  # Critical for Chinese text wrapping
)

doc = SimpleDocTemplate("long_text.pdf")
story = []

long_chinese_text = """
这是一段很长的中文文本，用于演示中文换行功能。在没有设置 wordWrap='CJK' 的情况下，
reportlab 默认使用英文换行规则，只在空格处换行。但中文句子通常没有空格，
因此需要特别设置 CJK 换行模式，才能让文本在适当的位置自动换行。
"""
story.append(Paragraph(long_chinese_text, cjk_paragraph_style))

doc.build(story)
```

## Common Tasks

### Extract Text from Scanned PDFs
```python
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path('scanned.pdf')

text = ""
for i, image in enumerate(images):
    text += f"Page {i+1}:\n"
    text += pytesseract.image_to_string(image)
    text += "\n\n"

print(text)
```

### Add Watermark
```python
from pypdf import PdfReader, PdfWriter

watermark = PdfReader("watermark.pdf").pages[0]

reader = PdfReader("document.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark)
    writer.add_page(page)

with open("watermarked.pdf", "wb") as output:
    writer.write(output)
```

### Extract Images
```bash
pdfimages -j input.pdf output_prefix
```

### Password Protection
```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("input.pdf")
writer = PdfWriter()

for page in reader.pages:
    writer.add_page(page)

writer.encrypt("userpassword", "ownerpassword")

with open("encrypted.pdf", "wb") as output:
    writer.write(output)
```

## Complex Workflows

### Extract Figures/Images from PDF

#### Method 1: Using pdfimages (fastest)
```bash
# Extract all images with original quality
pdfimages -all document.pdf images/img
```

#### Method 2: Using pypdfium2 + Image Processing
```python
import pypdfium2 as pdfium
from PIL import Image
import numpy as np

def extract_figures(pdf_path, output_dir):
    pdf = pdfium.PdfDocument(pdf_path)

    for page_num, page in enumerate(pdf):
        # Render high-resolution page
        bitmap = page.render(scale=3.0)
        img = bitmap.to_pil()

        # Convert to numpy for processing
        img_array = np.array(img)

        # Simple figure detection (non-white regions)
        mask = np.any(img_array != [255, 255, 255], axis=2)

        # Find contours and extract bounding boxes
        # (This is simplified - real implementation would need more sophisticated detection)

        # Save detected figures
        # ... implementation depends on specific needs
```

### Batch PDF Processing with Error Handling
```python
import os
import glob
from pypdf import PdfReader, PdfWriter
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_process_pdfs(input_dir, operation='merge'):
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))

    if operation == 'merge':
        writer = PdfWriter()
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                for page in reader.pages:
                    writer.add_page(page)
                logger.info(f"Processed: {pdf_file}")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                continue

        with open("batch_merged.pdf", "wb") as output:
            writer.write(output)

    elif operation == 'extract_text':
        for pdf_file in pdf_files:
            try:
                reader = PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()

                output_file = pdf_file.replace('.pdf', '.txt')
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                logger.info(f"Extracted text from: {pdf_file}")

            except Exception as e:
                logger.error(f"Failed to extract text from {pdf_file}: {e}")
                continue
```

### Advanced PDF Cropping
```python
from pypdf import PdfWriter, PdfReader

reader = PdfReader("input.pdf")
writer = PdfWriter()

# Crop page (left, bottom, right, top in points)
page = reader.pages[0]
page.mediabox.left = 50
page.mediabox.bottom = 50
page.mediabox.right = 550
page.mediabox.top = 750

writer.add_page(page)
with open("cropped.pdf", "wb") as output:
    writer.write(output)
```

## Performance Optimization Tips

### 1. For Large PDFs
- Use streaming approaches instead of loading enti

... [Content truncated, total 27,188 chars] ...