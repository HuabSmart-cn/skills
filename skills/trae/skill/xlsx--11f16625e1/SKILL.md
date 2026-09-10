---
name: xlsx
description: "Use this skill any time a spreadsheet file is the primary input or output. This means any task where the user wants to: open, read, edit, or fix an existing .xlsx, .xlsm, .csv, or .tsv file (e.g., adding columns, computing formulas, formatting, charting, cleaning messy data); create a new spreadsheet from scratch or from other data sources; or convert between tabular file formats. Trigger especially when the user references a spreadsheet file by name or path — even casually (like \"the xlsx in my downloads\") — and wants something done to it or produced from it. Also trigger for cleaning or restructuring messy tabular data files (malformed rows, misplaced headers, junk data) into proper spreadsheets. The deliverable must be a spreadsheet file. Do NOT trigger when the primary deliverable is a Word document, HTML report, standalone Python script, database pipeline, or Google Sheets API integration, even if tabular data is involved."
license: Proprietary. LICENSE.txt has complete terms
supported_os:
  - macos
  - linux
---

# Requirements for Outputs

## All Excel files

> **All dependencies are pre-installed** (pandas, openpyxl, LibreOffice), use them directly.
### Professional Font
- Use a consistent, professional font (e.g., Arial, Times New Roman) for all deliverables unless otherwise instructed by the user

### Zero Formula Errors
- Every Excel model MUST be delivered with ZERO formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?)

### Preserve Existing Templates (when updating templates)
- Study and EXACTLY match existing format, style, and conventions when modifying files
- Never impose standardized formatting on files with established patterns
- Existing template conventions ALWAYS override these guidelines

### Visual Table Design (MUST for new tables unless user/template says otherwise)
- Apply zebra striping in data regions (not headers or totals), using low-contrast alternating fills (for example `#FFFFFF` and `#F7F9FC`)
- Apply thin, light borders for structure (for example `#D9DEE7`), favoring outer border + row separators over heavy full-grid borders
- For subtotal/total emphasis, use hierarchy cues (bold text and/or top border emphasis) instead of thick borders around every cell

### KPI Visual Hierarchy (MUST when KPI-like metrics exist)
- Highlight an appropriate number of key metrics based on content complexity, prioritizing summary rows, current-period critical values, and exceptions
- Keep highlight treatment consistent (prefer bold + light fill) and avoid overusing saturated colors
- Keep color semantics consistent across the workbook (for example green=positive, red=risk)
- Add short labels near highlighted metrics when helpful (for example "Core KPI", "Exception")

### Style Migration (MANDATORY when merging/consolidating from source files)
- When copying data from source or template files, MUST migrate cell styles (font, fill, border, alignment, number_format) to the target
- ⚠️ Capture styles from reference rows BEFORE any row deletion/insertion operations — openpyxl merge-cell bugs corrupt styles after structural changes
- For template-based workflows, capture the data-row style first, then apply to all new rows:
  ```python
  from copy import copy
  ref = {c: {k: copy(getattr(ws.cell(3, c), k)) if k != "number_format" else ws.cell(3, c).number_format
             for k in ("font", "fill", "border", "alignment", "number_format")}
         for c in range(1, ws.max_column + 1)}
  ```
- Preserve hierarchical grouping (merged cells for categories). If infeasible, use indentation as fallback and inform the user.

### Column Width & Text Wrapping (MANDATORY)
- After populating data, MUST auto-fit column widths based on content length:
  ```python
  from openpyxl.utils import get_column_letter
  for col_idx in range(1, ws.max_column + 1):
      max_len = max(
          (len(str(ws.cell(row=r, column=col_idx).value or "")) for r in range(1, ws.max_row + 1)),
          default=0,
      )
      ws.column_dimensions[get_column_letter(col_idx)].width = min(max(max_len + 2, 8), 60)
  ```
- For columns containing long text (descriptions, notes, specs — typically > 30 chars), MUST set `wrap_text=True` and a reasonable width (30-60 chars):
  ```python
  from openpyxl.styles import Alignment
  for r in range(1, ws.max_row + 1):
      cell = ws.cell(row=r, column=col_idx)
      cell.alignment = Alignment(wrap_text=True, vertical="top")
  ```
- When loading from a template, preserve the template's existing column widths. Only auto-fit columns where new data significantly exceeds the original width.

## Financial models

### Color Coding Standards
Unless otherwise stated by the user or existing template

#### Industry-Standard Color Conventions
- **Blue text (RGB: 0,0,255)**: Hardcoded inputs, and numbers users will change for scenarios
- **Black text (RGB: 0,0,0)**: ALL formulas and calculations
- **Green text (RGB: 0,128,0)**: Links pulling from other worksheets within same workbook
- **Red text (RGB: 255,0,0)**: External links to other files
- **Yellow background (RGB: 255,255,0)**: Key assumptions needing attention or cells that need to be updated

### Number Formatting Standards

#### General Number Formatting Rules (ALL scenarios)
- **Preserve source formats**: When copying data from source files, MUST detect and migrate each cell's `number_format` to the target.
- **Units MUST be visible**: Every numeric column MUST have its unit clearly displayed:
  1. **Header with unit** (preferred): Append unit to column header — e.g., "单价(元)", "金额(万元)", "Revenue ($mm)"
  2. **number_format with symbol**: For currency, embed in `number_format` — e.g., `¥#,##0.00`, `$#,##0`
  3. **Dedicated unit row/column**: ONLY as last resort when headers are locked/unmodifiable
  - ⚠️ NEVER leave numeric columns without visible unit indication
- **Infer units from context**: Scan source headers and cell formats. Common mappings:
  - "元"/"¥"/"人民币" → `¥#,##0.00` + header "(元)" | "万元"/"亿元" → `#,##0.00` + header "(万元)"
  - "%"/"率"/"比例" → `0.0%` | "台"/"套"/"个"/"件" → `#,##0` + header with unit
- **Decimal precision**: Match source. Default: 2 decimals for currency, 0 for counts.
- **Thousands separator**: ALWAYS apply for numbers ≥ 1000

#### Financial Model Format Rules
- **Years**: Format as text strings (e.g., "2024" not "2,024")
- **Currency**: Use $#,##0 format; ALWAYS specify units in headers ("Revenue ($mm)")
- **Zeros**: Use number formatting to make all zeros "-", including percentages (e.g., "$#,##0;($#,##0);-")
- **Percentages**: Default to 0.0% format (one decimal)
- **Multiples**: Format as 0.0x for valuation multiples (EV/EBITDA, P/E)
- **Negative numbers**: Use parentheses (123) not minus -123

### Formula Construction Rules

#### Assumptions Placement
- Place ALL assumptions (growth rates, margins, multiples, etc.) in separate assumption cells
- Use cell references instead of hardcoded values in formulas
- Example: Use =B5*(1+$B$6) instead of =B5*1.05

#### Formula Error Prevention
- Verify all cell references are correct
- Check for off-by-one errors in ranges
- Ensure consistent formulas across all projection periods
- Test with edge cases (zero values, negative numbers)
- Verify no unintended circular references

#### Documentation Requirements for Hardcodes
- Comment or in cells beside (if end of table). Format: "Source: [System/Document], [Date], [Specific Reference], [URL if applicable]"
- Examples:
  - "Source: Company 10-K, FY2024, Page 45, Revenue Note, [SEC EDGAR URL]"
  - "Source: Company 10-Q, Q2 2025, Exhibit 99.1, [SEC EDGAR URL]"
  - "Source: Bloomberg Terminal, 8/15/2025, AAPL US Equity"
  - "Source: FactSet, 8/20/2025, Consensus Estimates Screen"

# XLSX creation, editing, and analysis

## Overview

A user may ask you to create, edit, or analyze the contents of an .xlsx file. You have different tools and workflows available for different tasks.

## Important Requirements

**LibreOffice Required for Formula Recalculation**: You can assume LibreOffice is installed for recalculating formula values using the `scripts/recalc.py` script. The script automatically configures LibreOffice on first run, including in sandboxed environments where Unix sockets are restricted (handled by `scripts/office/soffice.py`)

## Reading and analyzing data

### Data analysis with pandas
For data analysis, visualization, and basic operations, use **pandas** which provides powerful data manipulation capabilities:

```python
import pandas as pd

# Read Excel
df = pd.read_excel('file.xlsx')  # Default: first sheet
all_sheets = pd.read_excel('file.xlsx', sheet_name=None)  # All sheets as dict

# Analyze
df.head()      # Preview data
df.info()      # Column info
df.describe()  # Statistics

# Write Excel
df.to_excel('output.xlsx', index=False)
```

## Excel File Workflows

## CRITICAL: Use Formulas, Not Hardcoded Values

**Always use Excel formulas instead of calculating values in Python and hardcoding them.** This ensures the spreadsheet remains dynamic and updateable.

### ❌ WRONG - Hardcoding Calculated Values
```python
# Bad: Calculating in Python and hardcoding result
total = df['Sales'].sum()
sheet['B10'] = total  # Hardcodes 5000

# Bad: Computing growth rate in Python
growth = (df.iloc[-1]['Revenue'] - df.iloc[0]['Revenue']) / df.iloc[0]['Revenue']
sheet['C5'] = growth  # Hardcodes 0.15

# Bad: Python calculation for average
avg = sum(values) / len(values)
sheet['D20'] = avg  # Hardcodes 42.5
```

### ✅ CORRECT - Using Excel Formulas
```python
# Good: Let Excel calculate the sum
sheet['B10'] = '=SUM(B2:B9)'

# Good: Growth rate as Excel formula
sheet['C5'] = '=(C4-C2)/C2'

# Good: Average using Excel function
sheet['D20'] = '=AVERAGE(D2:D19)'
```

This applies to ALL calculations - totals, percentages, ratios, differences, etc. The spreadsheet should be able to recalculate when source data changes.

## ⚠️ REQUIRED: Pre-Build Planning

Before writing ANY code, complete these two steps:

### Step 1: Problem Review
- Read ALL source and template files
- Combine file findings with the user query and restate the task intent in concrete terms

### Step 2: Output Detailed Workbook Plan
Present a structured plan covering:

1. **Sheet Plan**
   - Total number of sheets
   - Each sheet name
   - Purpose of each sheet

2. **Schema Plan (per sheet)**
   - Row fields (if row-oriented)
   - Column fields (if column-oriented)
   - Value source/calculation for each field (raw source / lookup / formula / aggregation)

3. **Style Plan (per sheet)**
   - Header style (fill, font color, emphasis)
   - Number format per column (currency, percentage, integer, etc.) — specify `number_format` strings
   - Units per numeric column — specify where each unit is displayed (header text, number_format symbol, or unit row)
   - Column widths strategy (auto-fit vs fixed, which columns need wrap_text)
   - Style migration plan (if sourcing from template: which reference row to capture styles from)
   - Zebra striping design
   - KPI visual hierarchy design

**Required planning output format:**
```markdown
## Problem Review
- Files read: ...
- Task understanding: ...

## Detailed Plan
### Sheet Plan
1. Sheet: <name> — Purpose: <purpose>

### Schema Plan
1. Sheet: <name>
- Row fields: ...
- Column fields: ...
- Value source/calculation: ...

### Style Plan
1. Sheet: <name>
- Header: ...
- Number formats: Col A = #,##0, Col B = ¥#,##0.00, ...
- Units: Col B header = "单价(元)", Col C header = "金额(万元)", ...
- Column widths: Col A = 12, Col B = auto-fit, Col J = 50 (wrap_text)
- Style migration: capture from template row 3
- Zebra striping: ...
- KPI hierarchy: ...
```

If inputs are incomplete, still output this plan with explicit assumptions first.

**Only proceed to implementation after:**
- [ ] Problem Review is complete
- [ ] Detailed Workbook Plan is output

⚠️ Do NOT ask the user to confirm the plan. Output the plan and immediately proceed to implementation in the same response.

## Common Workflow
1. **Output plan first (MANDATORY)**: Complete Pre-Build Planning above
2. **Create/Load**: Create new workbook or load existing file
3. **Modify**: Add/edit data, formulas, and formatting
4. **Save**: Write to file
5. **Recalculate formulas (MANDATORY IF USING FORMULAS)**: Use the scripts/recalc.py script
   ```bash
   python scripts/recalc.py output.xlsx
   ```
6. **Verify and fix any errors**:
   - The script returns JSON with error details
   - If `status` is `errors_found`, check `error_summary` for specific error types and locations
   - Fix the identified errors and recalculate again
   - Common errors to fix:
     - `#REF!`: Invalid cell references
     - `#DIV/0!`: Division by zero
     - `#VALUE!`: Wrong data type in formula
     - `#NAME?`: Unrecognized formula name

### Creating new Excel files

```python
# Using openpyxl for formulas and formatting
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

wb = Workbook()
sheet = wb.active

# Add data
sheet['A1'] = 'Hello'
sheet['B1'] = 'World'
sheet.append(['Row', 'of', 'data'])

# Add formula
sheet['B2'] = '=SUM(A1:A10)'

# Formatting
sheet['A1'].font = Font(bold=True, color='FF0000')
sheet['A1'].fill = PatternFill('solid', start_color='FFFF00')
sheet['A1'].alignment = Alignment(horizontal='center')

# Column width
sheet.column_dimensions['A'].width = 20

wb.save('output.xlsx')
```

### Editing existing Excel files

```python
# Using openpyxl to preserve formulas and formatting
from openpyxl import load_workbook

# Load existing file
wb = load_workbook('existing.xlsx')
sheet = wb.active  # or wb['SheetName'] for specific sheet

# Working with multiple sheets
for sheet_name in wb.sheetnames:
    sheet = wb[sheet_name]
    print(f"Sheet: {sheet_name}")

# Modify cells
sheet['A1'] = 'New Value'
sheet.insert_rows(2)  # Insert row at position 2
sheet.delete_cols(3)  # Delete column 3

# Add new sheet
new_sheet = wb.create_sheet('NewSheet')
new_sheet['A1'] = 'Data'

wb.save('modified.xlsx')
```

## Recalculating formulas

Excel files created or modified by openpyxl contain formulas as strings but not calculated values. Use the provided `scripts/recalc.py` script to recalculate formulas:

```bash
python scripts/recalc.py <excel_file> [timeout_seconds]
```

Example:
```bash
python scripts/recalc.py output.xlsx 30
```

The script:
- Automatically sets up LibreOffice macro on first run
- Recalculates all formulas in all sheets
- Scans ALL cells for Excel errors (#REF!, #DIV/0!, etc.)
- Returns JSON with detailed error locations and counts
- Works on both Linux and macOS

## Formula Verification Checklist

Quick checks to ensure formulas work correctly:

### Essential Verification
- [ ] **Test 2-3 sample references**: Verify they pull correct values before building full model
- [ ] **Column mapping**: Confirm Excel columns match (e.g., column 64 = BL, not BK)
- [ ] **Row offset**: Remember Excel rows are 1-indexed (DataFrame row 5 = Excel row 6)

### Common Pitfalls
- [ ] **NaN handling**: Check for null values with `pd.notna()`
- [ ] **Far-right columns**: FY data often in columns 50+
- [ ] **Multiple matches**: Search all occurrences, not just first
- [ ] **Division by zero**: Check denominators before using `/` in formulas (#DIV/0!)
- [ ] **Wrong references**: Verify all cell references point to intended cells (#REF!)
- [ ] **Cross-sheet references**: Use correct format (Sheet1!A1) for linking sheets

### Formula Testing Strategy
- [ ] **Start small**: Test formulas on 2-3 cells before applying broadly
- [ ] **Verify dependencies**: Check all cells referenced in formulas exist
- [ ] **Test edge cases**: Include zero, negative, and very large values

### Interpreting scripts/recalc.py Output
The script returns JSON with error details:
```json
{
  "status": "success",           // or "errors_found"
  "total_errors": 0,              // Total error count
  "total_formulas": 42,           // Number of formulas in file
  "error_summary": {              // Only present if errors found
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

## Best Practices

### Library Selection
- **pandas**: Best for data analysis, bulk operations, and simple data export
- **openpyxl**: Best for complex formatting, formulas, and Excel-specific features

### Working with openpyxl
- Cell indices are 1-based (row=1, column=1 refers to cell A1)
- Use `data_only=True` to read calculated values: `load_workbook('file.xlsx', data_only=True)`
- **Warning**: If opened with `data_only=True` and saved, formulas are replaced with values and permanently lost
- For large files: Use `read_only=True` for reading or `write_only=True` for writing
- Formulas are preserved but not evaluated - use scripts/recalc.py to update values

### Working with pandas
- Specify data types to avoid inference issues: `pd.read_excel('file.xlsx', dtype={'id': str})`
- For large files, read specific columns: `pd.read_excel('file.xlsx', usecols=['A', 'C', 'E'])`
- Handle dates properly: `pd.read_excel('file.xlsx', parse_dates=['date_column'])`

### Reusable Styling Helpers (openpyxl)
Use helper functions so visual rules are applied consistently instead of ad-hoc cell formatting:

```python
from openpyxl.styles import PatternFill, Border, Side, Font

ZEBRA_FILL_1 = PatternFill(fill_type="solid", fgColor="FFFFFF")
ZEBRA_FILL_2 = PatternFill(fill_type="solid", fgColor="F7F9FC")
KPI_FILL = PatternFill(fill_type="solid", fgColor="EAF2FF")
THIN_BORDER = Border(
    left=Side(style="thin", color="D9DEE7"),
    right=Side(style="thin", color="D9DEE7"),
    top=Side(style="thin", color="D9DEE7"),
    bottom=Side(style="thin", color="D9DEE7"),
)
TOP_EMPHASIS_BORDER = Border(
    left=Side(style="thin", color="D9DEE7"),
    right=Side(style="thin", color="D9DEE7"),
    top=Side(style="medium", color="AAB4C5"),
    bottom=Side(style="thin", color="D9DEE7"),
)

def apply_zebra_style(ws, min_row, max_row, min_col, max_col):
    for r in range(min_row, max_row + 1):
        fill = ZEBRA_FILL_1 if (r - min_row) % 2 == 0 else ZEBRA_FILL_2
        for c in range(min_col, max_col + 1):
            ws.cell(r, c).fill = fill

def apply_light_borders(ws, min_row, max_row, min_col, max_col):
    for r in range(min_row, max_row + 1):
        for c in range(min_col, max_col + 1):
            ws.cell(r, c).border = THIN_BORDER

def highlight_kpis(ws, cells, label_col=None, label_text=None):
    # cells example: ["F5", "F12", "F20"]
    for ref in cells:
        cell = ws[ref]
        cell.fill = KPI_FILL
        cell.font = Font(bold=True, color="1F2937")
    if label_col and label_text and cells:
        ws[f"{label_col}{ws[cells[0]].row}"] = label_text

# Example usage:
# apply_zebra_style(ws, min_row=2, max_row=30, min_col=1, max_col=8)
# apply_light_borders(ws, min_row=1, max_row=30, min_col=1, max_col=8)
# highlight_kpis(ws, cells=["F5", "F12"], label_col="G", label_text="Core KPI")
# ws["A31"].border = TOP_EMPHASIS_BORDER  # subtotal/total row emphasis
```

## Code Style Guidelines
**IMPORTANT**: When generating Python code for Excel operations:
- Write minimal, concise Python code without unnecessary comments
- Avoid verbose variable names and redundant operations
- Avoid unnecessary print statements

**For Excel files themselves**:
- Add comments to cells with complex formulas or important assumptions
- Document data sources for hardcoded values
- Include notes for key calculations and model sections

## Chart Best Practices (openpyxl Native Charts)

### Chart Type Selection

| Data Pattern | Chart Type |
|---|---|
| Category comparison (≤12 categories) | `BarChart` (vertical) |
| >12 categories or long labels | `BarChart` with `type="bar"` (horizontal) |
| Trend over time | `LineChart` |
| Part-of-whole (≤6 slices) | `PieChart` |
| Part-of-whole (>6 slices) | Aggregate smallest into "Other", or use horizontal `BarChart` |
| Two metrics with different scales | `LineChart` + secondary y-axis |

### Anti-Overlap Rules (MANDATORY)

1. **Sizing**: Always set `chart.width = 20`, `chart.height = 12` as baseline. Add ~1.5 width per category beyond 8.
2. **Tick label position**: Always set `chart.x_axis.tickLblPos = 'low'` and `chart.y_axis.tickLblPos = 'low'` to force axis labels outside the plot area. Default position renders labels inside, causing overlap with bars/lines.
3. **Data labels**: Only enable when `series_count × category_count ≤ 20`. Use `dLblPos='outEnd'`. Otherwise disable.
4. **X-axis rotation**: Labels > 8 chars → rotate -45° (`rot=-2700000`); > 15 chars → rotate -90° or switch to horizontal bar.
5. **Bar spacing**: Set `chart.gapWidth = 100`, `chart.overlap = -10` for grouped bars.
6. **Legend**: Single series → `chart.legend = None`. Multi-series → keep default `'r'` position.
7. **Pie charts**: Always show `showPercent=True` + `showCatName=True`. Max 6 slices.

### X-Axis Rotation Reference

```python
from openpyxl.chart.text import RichText
from openpyxl.drawing.text import Paragraph, ParagraphProperties, CharacterProperties, RichTextProperties

chart.x_axis.txPr = RichText(
    bodyPr=RichTextProperties(rot=-2700000),  # -45°; use -5400000 for -90°
    p=[Paragraph(pPr=ParagraphProperties(defRPr=CharacterProperties(sz=900)),
                 endParaRPr=CharacterProperties(sz=900))]
)
```

### Style

```python
chart.style = 10  # Recommended built-in styles: 10, 26, 42
CHART_COLORS = ["4472C4", "ED7D31", "A5A5A5", "FFC000", "5B9BD5", "70AD47"]
for i, s in enumerate(chart.series):
    s.graphicalProperties.solidFill = CHART_COLORS[i % len(CHART_COLORS)]
```

### Placement
- Place chart below data table with 2-row gap: `ws.add_chart(chart, f"A{ws.max_row + 3}")`
- Multiple charts: stagger at columns A and J, rows spaced by 18

### Data Preparation
- Aggregate categories to ≤12 for bar/column, ≤6 for pie
- Sort data meaningfully (by value or chronological)
- Ensure no blank rows/columns in data range
- Numeric columns must contain numbers, not string representations
