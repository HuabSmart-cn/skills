# PPTD Format Specification

PPTD (PPT-DSL) is a YAML abstraction layer for PowerPoint presentations, used to describe, generate, and edit slides in an AI-friendly way, with lossless bidirectional conversion to and from PPTX

---

## Conventions in This Document
- Uses **TS interfaces** to describe structures, with **field tables** and **minimal YAML examples** to aid understanding
- **Default values** are annotated in TS end-of-line comments as `// default: X`. X may be a literal (`1` / `"top"` / `[0, 0]`) or a descriptive phrase (`not applied` / `not shown` / `falls back along the inheritance chain` / `auto-adapts to chart size`, etc.)
- **Constraints** are annotated in TS end-of-line comments or below the TS block as `// constraint: ...`, uniformly using interval or inequality notation (`[0, 1]` / `> 0`) or textual descriptions
---

## 1. Global Conventions

### Syntax
- Uses **YAML 1.2** syntax
- For special characters such as `:`, `#`, `{`, `}`, the value must be wrapped in quotes or written with a block scalar instead
- For fields with many special characters such as `content.text`, a block scalar (`|`) should be used as its own block, to prevent content like `style="..."` from being parsed incorrectly

### Coordinate System and Units
- All geometry and size units are **px**; the origin `(0, 0)` is the top-left corner of the page
- Recommended sizes: 16:9 → `[960, 540]`; 4:3 → `[720, 540]`
- This specification defines 1px = 1pt (i.e., `fontSize: 18` is 18pt in PPTX)
- Element stacking order is determined by the order of the `Page.elements` array; the later an element, the higher its layer

### Style Priority and Default Values

For property values that conflict, the first source with a value is found by searching the following priorities from top to bottom; when none of the levels is set, fall back to the default values at the end of that section.

> The following rule applies to all subsections of this section: `lineHeight` (a multiple) and `lineHeightPx` (fixed px) are mutually exclusive; when both are set, `lineHeightPx` takes precedence.

#### 1. Text Styles Inside a Text Box

**Priority chain:**
1. Rich-text semantic tags such as `<u>`, `<sup>`, `<strong>` in [Text.content.text](#textcontent)
2. Inline properties set in `<span style="...">`
3. Paragraph properties set in `<p style="...">`
4. **Style fields set directly on [Text.content](#textcontent)** (distinct from the theme style referenced by `style`; including `color`, `fontSize`, `fontFamily`, `bold`, `italic`, `backgroundColor`, `lineHeight`, `lineHeightPx`, `letterSpacing`, `marginTop`)
5. The [TextStyleConfig](#textstyleconfig) theme style referenced by [Text.content.style](#textcontent)
6. Default values:

| Property | Default value |
|---|---|
| color | `#000000` |
| backgroundColor | Not applied |
| fontSize | `18` |
| fontFamily | `"MiSans"` |
| bold | `false` |
| italic | `false` |
| lineHeight | `1` |
| lineHeightPx | Not applied |
| letterSpacing | `0` |
| marginTop | `0` |

#### 2. Table Cell Styles

**Priority chain:**
1. Rich-text semantic tags such as `<u>`, `<sup>`, `<strong>` in [Cell.text](#cell)
2. Inline properties set in `<span style="...">`
3. Paragraph properties set in `<p style="...">`
4. [Cell](#cell) inline fields
5. The [TextStyleConfig](#textstyleconfig) referenced by [Cell.textStyle](#cell) (**applies only to text fields**; does not include `fill` / `border` / `align`)
6. Position-category styles of [TableStyleConfig](#tablestyleconfig)
   - On row vs column conflicts, [TableStyleConfig.rowOverColumn](#tablestyleconfig) decides the winner; default `true` = row wins
   - Row categories: `TableStyleConfig.firstRowStyle` / `TableStyleConfig.lastRowStyle`
   - Column categories: `TableStyleConfig.firstColumnStyle` / `TableStyleConfig.lastColumnStyle`
7. [TableStyleConfig.bodyStyles](#tablestyleconfig): applies to data rows other than the first and last rows, cycled by data-row index
8. [TableStyleConfig.cellStyle](#tablestyleconfig): the baseline cell style for the whole table
9. Default values

| Property | Default value |
|---|---|
| color | `#000000` |
| backgroundColor | Not applied |
| fontSize | Auto-adapts based on cell height |
| fontFamily | `"MiSans"` |
| bold | `false` |
| italic | `false` |
| lineHeight | `1` |
| lineHeightPx | Not applied |
| letterSpacing | `0` |
| marginTop | `0` |
| fill | Not applied (transparent) |
| border | `{style: solid, width: 1, color: "#000000"}` |
| align | `["center", "middle"]` |

#### 3. Chart Styles

Charts involve multiple kinds of styles (series body colors, fonts, data labels, axis/legend visibility, etc.), each with its own independent priority chain, explained below.

**3.1 Series body color priority chain:**
1. A series' explicit `fill` / `lineColor` / `areaColor` (field names differ per type; see [Color Mechanism](#52-color-mechanism))
2. The same-named field for the corresponding type in [Chart.seriesDefaults](#seriesdefaults)
3. The [Theme.colors](#theme) theme color cycle (colors are picked in the order the series appear in the array)

> [scatter](#scatter) is an exception: marker color resolves as `marker.fill > series.fill > theme color cycle`; marker.border likewise takes precedence over series.border.
>
> For each type's specific color fields, derivation rules, and role mappings, see [§5.2 Color Mechanism](#52-color-mechanism).

**3.2 Font priority chain:**
1. Sub-component `fontFamily` ([TitleConfig](#titleconfig) / [LegendConfig](#legendconfig) / [DataLabelConfig](#datalabelconfig) / [AxisConfig.label](#axisconfig) / [SpokeAxisConfig.label](#spokeaxisconfig))
2. [Chart.fontFamily](#chart)
3. Theme default ([Theme](#theme) or the PPTX master font)

**3.3 dataLabels priority chain:**
1. `series[i].dataLabels`
2. [Chart.dataLabels](#chart) (global default)
3. Not shown (equivalent to `show: false`)

> Sub-fields follow a **one-level shallow merge**: `series.dataLabels` only overrides the sub-fields it explicitly provides; unprovided ones fall back from [Chart.dataLabels](#chart); if neither provides them, the per-type default applies (see [dataLabels.content value quick reference](#55-datalabelscontent-value-quick-reference)).

**3.4 `seriesDefaults` merge rules:**

[Chart.seriesDefaults](#seriesdefaults)`[type]` provides common defaults for all series of that type, merged with each series via a **one-level deep merge**:
- **Scalar fields** (string / number / boolean): the series' explicit value overrides defaults
- **Object fields** (`marker` / `dataLabels` / `border` / `upBars` / `downBars` / `totalBars` / gradient `fill` objects, etc.): recursive one-level shallow merge — same-named fields of defaults and series are spread respectively, with sub-fields overridden by the nearest source
- **Array fields** (`fill: []` / `colorScheme: []`): the series replaces defaults as a whole, with no element-level merging
- `type` and `encode` are not allowed inside seriesDefaults
- Only multi-series types support seriesDefaults: `bar / line / area / scatter / bubble / candlestick / radar`

Counterintuitive example:
```yaml
seriesDefaults:
  bar: {marker: {shape: circle, size: 8}}
series:
  - type: bar
    marker: {size: 12}     # after merge: {shape: circle, size: 12}, not {size: 12}
```

**3.5 `boolean | Config` field convention:**

Fields of the form `boolean | XxxConfig` (`marker` / `legend` / `AxisConfig.label / axisLine / gridLine` / `SpokeAxisConfig.label / axisLine / gridLine` / `colorbar`) uniformly follow:
- `false` = off
- `true` = on with default configuration
- Object `{...}` = on + custom configuration

> **The only exception**: [scatter.marker](#scatter) cannot be `false` (a scatter plot without a marker has nothing to render).

---

### Multi-File Structure
A PPTD project consists of a main entry file and individual page files:
```
project/
  slides_name.pptd     # main entry (size/theme/title + page reference list)
  media/               # media resources such as images and videos
  pages/               # page file directory
    1_cover.page       # one .page file per page
    2_intro.page
```
**Path rules:**
1. **Fully self-contained**: all referenced files must be located inside the folder containing the `.pptd` file; **referencing files outside the directory is not allowed**
2. **Only relative paths are supported** (relative to the directory containing the `.pptd` file):
   - The `pages` list in `.pptd`: `pages/1_cover.page`
   - Image paths in `.page`: `media/image1.jpg`
3. **Media supports URLs**: `Image.src`, and the [ImageFill](#fill).src of `background` / `fill`, may be `https://...` (only jpg/jpeg/png/gif supported)

**Main entry is required:** everything must be loaded through the `.pptd` main entry file; a `.page` cannot be passed alone to the `convert`/`check` commands

---

## 2. Shared Types
The following types are reused in multiple places and are defined together up front. Element sections reference them by type name without repeating the expansion

### Color
```ts
type Color = string;
```
> Supports opaque **HEX6** (`#RRGGBB`), alpha **HEX8** (`#RRGGBBAA`), and [Theme.colors](#theme) theme color references (e.g. `$primary`)

### FontFamily
```ts
type FontFamily = string | { latin: string; ea: string };
```
| Form | Example | Description |
|------|------|------|
| String | `"MiSans"` | Chinese and English use the same font uniformly |
| Object | `{latin: "Arial", ea: "MiSans"}` | Explicitly specify Latin (latin) and East Asian (ea) fonts separately |

See [fonts.md](./fonts.md) for the list of available fonts

### Alignment
```ts
type HorizontalAlign = "left" | "center" | "right" | "justify" | "distributed";
type VerticalAlign   = "top"  | "middle" | "bottom";
type Alignment       = [HorizontalAlign, VerticalAlign];
```
| Value | Description |
|----|------|
| `left` / `center` / `right` | Horizontal left / center / right alignment |
| `justify` | Justified (last line not stretched) |
| `distributed` | Distributed (last line stretched) |
| `top` / `middle` / `bottom` | Vertical top / middle / bottom alignment |

### LineStyle
```ts
type LineStyle = "solid" | "dash" | "dot";
```

### Border
```ts
interface Border {
  style?: LineStyle;  // default: "solid"
  width?: number;     // default: 1
  color?: Color;      // default: "#000000"
}
```

#### BorderSpec
[Cell](#cell) and [CellStyle](#cellstyle) support an array form of `Border` to set the four side borders separately

```ts
type BorderSpec = null
                | Border
                | [Border | null, Border | null]
                | [Border | null, Border | null, Border | null, Border | null];
```

| Form | Meaning |
|------|------|
| `null` | Explicit clear: no border on any of the four sides (used to override a border set higher up the inheritance chain)|
| `Border` | Same on all four sides |
| Two-element array `[Border\|null, Border\|null]` | `[top-bottom, left-right]` |
| Four-element array `[Border\|null, Border\|null, Border\|null, Border\|null]` | `[top, right, bottom, left]` (clockwise) |

> A `null` inside the array means no border at the corresponding position; a top-level `null` clears everything.

### Shadow

```ts
interface Shadow {
  blur: number;                // blur radius
  color: Color;
  offset?: [number, number];   // default: [0, 0]; [x, y] offset
}
```

### ColorStop

```ts
interface ColorStop {
  position: number;  // constraint: [0, 1]
  color: Color;
}
```

### ImageFit / ImageCrop

```ts
interface ImageFit {
  mode: "fill" | "contain" | "cover";
}

interface ImageCrop {
  left?: number;
  top?: number;
  right?: number;
  bottom?: number;
}
```

> **Constraint:** the four fields of `ImageCrop` are analogous, default 0. A positive value crops inward from the corresponding edge proportionally (inset); a negative value expands outward toward the corresponding edge proportionally and pads with transparent pixels (outset). Must ensure `left + right < 1` and `top + bottom < 1`, otherwise the source rectangle degenerates.

| ImageFit.mode | Description |
|---|---|
| `cover` | Fills the container, keeps aspect ratio, may crop |
| `contain` | Shows the image completely, keeps aspect ratio, may leave blank space |
| `fill` | Stretches to fill, may distort |

### Fill

```ts
type Fill = SolidFill | GradientFill | ImageFill;

interface SolidFill {
  type: "solid";
  color: Color;
}

interface GradientFill {
  type: "gradient";
  gradientType: "linear" | "radial";
  stops: ColorStop[];                // constraint: at least 2
  angle?: number;                    // default: 0; only effective for linear
}

interface ImageFill {
  type: "image";
  src: string;                       // URL or relative path
  fit?: ImageFit;                    // default: {mode: "cover"}
  crop?: ImageCrop;                  // always applied; see the rendering order with fit below
  opacity?: number;                  // default: 1; constraint: [0, 1]
}
```

> `GradientFill.angle` takes values in `[0, 360)`; `0` means left to right, increasing clockwise. Examples: `90` = top→bottom, `180` = right→left.

> **ImageFill rendering order:** `crop` (adjust the source rectangle proportionally: positive values crop inward, negative values expand outward and pad with transparent pixels) → `fit` (adapt to the fill container per mode). The specific semantics of each `fit.mode` value are consistent with the "rendering logic" discussion in the [Image](#image-image) section.

**Examples:**

```yaml
# Solid
fill:
  type: solid
  color: "$primary"

# Gradient
fill:
  type: gradient
  gradientType: linear
  angle: 90
  stops:
    - {position: 0, color: "$primary"}
    - {position: 1, color: "$accent"}

# Image
fill:
  type: image
  src: "media/bg.jpg"
  fit: {mode: cover}
  opacity: 0.9
```

---

## 3. Main Entry File (.pptd)

### Presentation

```ts
interface Presentation {
  version: "v2";                // required, fixed to "v2" (version identifier)
  title?: string;              // default: no title
  size: [number, number];      // [width, height]; 16:9 recommended [960, 540], 4:3 recommended [720, 540]
  theme?: Theme;
  pages: string[];             // list of relative paths to page files, e.g. "pages/cover.page"
}
```

**Example:**

```yaml
version: v2
title: Annual Work Summary
size: [960, 540]
theme:
  colors:
    primary: "#2563EB"
    accent: "#F59E0B"
    text: "#1F2937"
  textStyles:
    title:
      fontSize: 40
      color: "$primary"
    body:
      fontSize: 18
      color: "$text"
      lineHeight: 1.6
  tableStyles:
    default:
      firstRowStyle:
        fill: {type: solid, color: "$primary"}
        color: "#ffffff"
        bold: true
      bodyStyles:
        - {fill: {type: solid, color: "#f8fafc"}}
        - {fill: {type: solid, color: "#ffffff"}}
pages:
  - pages/1_cover.page
  - pages/2_content.page
```

### Theme

The theme centrally manages colors, text styles, and table styles. Use `$<key>` in relevant fields to reference the theme:

| Theme type | Referencing field | Example |
|---|---|---|
| `colors` | Any [Color](#color) field | `$primary` |
| `textStyles` | [TextContent.style](#textcontent) / [Cell.textStyle](#cell) | `$title` |
| `tableStyles` | [Table.style](#table-table) | `$default` |

```ts
interface Theme {
  colors?: Record<string, Color>;
  textStyles?: Record<string, TextStyleConfig>;
  tableStyles?: Record<string, TableStyleConfig>;
}
```

#### TextStyleConfig

```ts
interface TextStyleConfig {
  color?: Color;
  fontSize?: number;
  fontFamily?: FontFamily;
  bold?: boolean;                    // bold
  italic?: boolean;                  // italic
  backgroundColor?: Color;           // text background color (e.g., text highlight)
  lineHeight?: number;               // line-height multiple
  lineHeightPx?: number;             // fixed line height (px); when it conflicts with lineHeight, lineHeightPx prevails
  letterSpacing?: number;
  marginTop?: number;
}
```

> Unset fields fall back along the inheritance chain (see [Style Priority and Default Values](#style-priority-and-default-values) for details)

#### CellStyle

```ts
interface CellStyle extends TextStyleConfig {
  // —— Inherits all properties of TextStyleConfig ——
  //   color / fontSize / fontFamily / bold / italic / backgroundColor / lineHeight / lineHeightPx / letterSpacing / marginTop

  // —— CellStyle-specific ——
  fill?: Fill;                              // background fill
  border?: BorderSpec;                      // border
  align?: Alignment;                        // text alignment
}
```

> Unset fields fall back along the inheritance chain (see [Style Priority and Default Values](#style-priority-and-default-values) for details)

#### TableStyleConfig

```ts
interface TableStyleConfig {
  // —— Cell style: applied to every cell ——
  cellStyle?: CellStyle;

  // —— Row category overrides ——
  firstRowStyle?: CellStyle;  // first-row style
  lastRowStyle?: CellStyle;  // last-row style

  // —— Column category overrides ——
  firstColumnStyle?: CellStyle;
  lastColumnStyle?: CellStyle;

  // —— Alternating row styles ——
  bodyStyles?: CellStyle[];  // data rows other than the first/last row apply these cyclically by data-row index

  // —— Cross-category rule ——
  rowOverColumn?: boolean;            // default: true; whether the row style wins when a cell is covered by both row and column rules
}
```
> **Row/column style rules**: category styles such as `firstRowStyle` / `lastRowStyle` / `firstColumnStyle` / `lastColumnStyle` mean **apply the style independently to every matching cell**, not apply the style to the first row/last column as a whole
> - Writing `firstRowStyle.border: {style: solid, width: 2}` → **every cell of the first row** gets a border on all four sides
> - To add an outer frame to the first row as a whole, use per-side BorderSpec: `border: [<top line>, null, <bottom line>, null]`, then set borders separately on the first-column and last-column cells of the first row


> For fallback rules, see [Style Priority and Default Values](#style-priority-and-default-values)

## 4. Page Files (.page)

### Page

```ts
interface Page {
  pageType?: "cover" | "table_of_contents" | "chapter" | "content" | "final" | string;  // default: none; category label (does not affect rendering); preset values are recognized as the corresponding page type, arbitrary custom strings are also allowed
  background?: Fill;               // default: {type: solid, color: "#FFFFFF"} (white solid fill)
  notes?: string;                  // default: none; speaker notes; plain text
  elements: Element[];             // the later an element, the higher its layer
}
```

**Example:**

```yaml
pageType: cover
background:
  type: solid
  color: "$primary"
notes: Speaker notes
elements:
  - elementId: title1
    elementType: text
    bounds: [100, 200, 760, 80]
    content:
      style: "$title"
      align: [center, middle]
      text: Hello World
```

---

## 5. Elements

### ElementBase

Common properties of all elements.

```ts
interface ElementBase {
  elementId: string;                                                      // constraint: unique within the same page; unique element ID
  elementType: "text" | "shape" | "line" | "image" | "icon" | "table" | "chart";  // element type
  bounds: [number, number, number, number];                               // element size and position, [x, y, width, height]
}

type Element = Text | Shape | Line | Image | Icon | Table | Chart;
```

---

### Text (text box)

```ts
interface Text extends ElementBase {
  elementType: "text";
  rotation?: number;                  // default: 0; degrees, clockwise rotation
  opacity?: number;                   // default: 1; constraint: [0, 1]
  flip?: [boolean, boolean];          // default: [false, false]; [horizontal flip, vertical flip]
  content: TextContent;
}
```

#### TextContent

```ts
interface TextContent {
  text: string;                                // rich text string (block scalar)
  style?: string;                              // references theme.textStyles, written as "$key" (e.g. "$title")

  // —— Style fields (when unset, fall back along the inheritance chain) ——
  color?: Color;
  fontSize?: number;
  fontFamily?: FontFamily;
  bold?: boolean;                              // bold: true=on, false/unset=off
  italic?: boolean;                            // italic: true=on, false/unset=off
  backgroundColor?: Color;                     // text background color (e.g., text highlight)
  lineHeight?: number;                         // line-height multiple
  lineHeightPx?: number;                       // fixed line height (px)
  letterSpacing?: number;
  marginTop?: number;

  // —— Layout fields ——
  textDirection?: "horizontal" | "vertical";   // default: "horizontal"
  wrap?: boolean;                              // default: true; when false, no wrapping, and the part beyond bounds.width overflows the element boundary; explicitly setting false is recommended for single-line text
  align?: Alignment;                           // default: ["left", "top"]

  // —— Visual decoration (unset = not applied) ——
  gradient?: GradientFill;                     // text gradient (applied to the text itself)
  shadow?: Shadow;                             // text shadow
}
```

**Examples:**

```yaml
# Basic: theme style + plain text
- elementId: title-1
  elementType: text
  bounds: [100, 50, 760, 80]
  content:
    style: "$title"
    align: [center, middle]
    text: Annual Work Summary

# Rich text + inline property overrides
- elementId: body-1
  elementType: text
  bounds: [100, 200, 600, 200]
  content:
    fontSize: 20
    color: "$text"
    lineHeight: 1.6
    align: [left, top]
    text: |
      <p><strong>Key achievement</strong>: completed <span style="color:$primary;">3</span> key projects</p>
      <p style="text-align:right"><span style="font-size:14px; color:#6b7280;">—— FY2024</span></p>

# Text gradient + shadow
- elementId: hero-text
  elementType: text
  bounds: [100, 100, 760, 120]
  content:
    align: [center, middle]
    gradient:
      type: gradient
      gradientType: linear
      angle: 90
      stops:
        - {position: 0, color: "$primary"}
        - {position: 1, color: "$accent"}
    shadow:
      blur: 6
      color: "#00000040"
      offset: [0, 3]
    text: |
      <p><span style="font-size:64px;">FUTURE</span></p>
```

#### Rich Text Rules

`TextContent.text` and `Cell.text` follow the rich text rules below for paragraph splitting and for setting paragraph or inline styles.

**Supported tags**

| Tag | Description | Example |
|------|------|------|
| `<p>` | Paragraph; may carry paragraph styles | `<p>paragraph</p>` |
| `<span>` | Inline style; use this tag to set inline styles | `<span style="color:#f00">red</span>` |
| `<strong>` | Bold | `<strong>important</strong>` |
| `<em>` | Italic | `<em>emphasis</em>` |
| `<u>` | Underline | `<u>underline</u>` |
| `<s>` | Strikethrough | `<s>deleted</s>` |
| `<sup>` | Superscript | `E=mc<sup>2</sup>` |
| `<sub>` | Subscript | `H<sub>2</sub>O` |
| `<a>` | Hyperlink; supports `https://`, `http://`, `mailto:`; once set, the hyperlink text style (blue with underline) is applied automatically | `<a href="https://x.com">link</a>` |
| `<ul>` | Unordered list | `<ul><li>item</li></ul>` |
| `<ol>` | Ordered list | `<ol><li>first item</li></ol>` |
| `<li>` | List item; must be used together with `<ul>` or `<ol>` | — |

**style attribute mapping**

`<p>`, `<li>`, and `<span>` may use `style="..."`. Color-type values may all use theme references (e.g. `$primary`), resolved per the [Color](#color) rules.

1. **Paragraph styles (only `<p>` supports them)**

| Property | Description | Values | Example |
| --- | --- | --- | --- |
| `text-align` | Paragraph horizontal alignment | `left` / `center` / `right` / `justify` / `distributed` | `<p style="text-align:center">…</p>` |
| `line-height` | Line height; **unitless** is treated as a `lineHeight` multiple, **with `px`** as a `lineHeightPx` fixed value | number (e.g. `1.5`) or px string (e.g. `24px`) | `<p style="line-height:1.6">…</p>` |
| `margin-top` | Spacing before the paragraph | px string (e.g. `8px`) | `<p style="margin-top:8px">…</p>` |
| `margin-left` | Left margin | px string (e.g. `12px`) | `<p style="margin-left:12px">…</p>` |
| `margin-right` | Right margin | px string (e.g. `12px`) | `<p style="margin-right:12px">…</p>` |

> Do not set `letter-spacing` on `<p>`; to set letter spacing uniformly, use `content.letterSpacing` or `Cell.letterSpacing`.

2. **List-item styles (only `<li>` supports them)**

| Property | Description |
| --- | --- |
| `text-align` | List-item horizontal alignment |
| `line-height` | Line height; value rules same as `<p>` |
| `letter-spacing` | Letter spacing |
| `margin-top` | Spacing before the paragraph |
| `margin-left` | Left margin |
| `list-style` | List style shorthand |
| `list-style-type` | List marker type |
| `list-style-position` | List marker position |
| `list-style-image` |

... [Content truncated, total 80,830 chars] ...