# reference/html.md —— 数据产出 HTML 产物工程约束（单一来源）

> 本文件是 `report-composer` 生成 **HTML 一体化产物**时的**全部工程约束单一来源**：适用范围、CDN 白名单、
> 浅色主题与 CSS 变量、移动端、组件样式、打印、图表（下钻 / 排版 / 序列化）、写盘前自检、内容组装骨架、design_brief。
> **产 html 时整份读本文**（组件 §d、图表 §f/g/h 已并入，不再拆分多文件）。可选的 `.docx` 导出在 `html-docx.md`（§L）。
>
> ## 自包含原则
>
> HTML 的全部工程约束都在本 skill 内（**不读取任何其它 skill 的 reference / scripts**）。配套图表工具在本 skill `scripts/chart_utils.py`。
> **形态 / 载体怎么定**（出单图还是满配报告、出 md/html/两者）见 `SKILL.md` §三；本文只管「决定要出 html 后，html 怎么工程化生成」。
>
> ⚠️ 本场景图表库**仅使用 ECharts**。基础语法底线：单文件直出（`<!DOCTYPE html>` → `</html>`，无 Markdown 代码块包裹 / HTML 注释）、JS **仅 ES5**、全 HTTPS、响应式。

## 目录

| 节 | 主题 | 何时读 |
|---|---|---|
| §a | 适用范围 | 确认场景 |
| §b | CDN 白名单（默认 1 / docx 3） | 写 `<head>` 前 |
| §c | 浅色主题 + CSS 变量 | 写 `<style>` |
| §c.5 | 移动端适配 | 写响应式（**强制**，另见开头「移动端红线速查」） |
| §d | 通用 UI 组件样式（KPI / section / SQL toggle / toast） | 组装 KPI/章节组件 |
| §e | 打印样式 | 收尾样式 |
| §f | 下钻交互骨架 | 有多维下钻 |
| §g | ECharts 排版规范 | 写图表 option |
| §h | `df_to_echarts_option` | 序列化图表 |
| §i | 生成前自检清单 | **写盘前必过** |
| §j | 内容组装（数据从上文识别） | 识别数据 + 搭骨架 |
| §k | `design_brief` 范例 | 按业务定制版面 |
| §L | DOCX 导出 | 见 `html-docx.md`，`export_docx` 时 |

> 与 md 版的一致性：html 与 md 由 report-composer 在**同一次调用**里组装，用**同一个时间戳** `report_<ts>.{md,html}`；两者的 KPI、核心发现、结论、行动建议、SQL 编号 **必须一一对应**，不允许 md 与 html 数据/结论打架（骨架对齐规则见 `SKILL.md` §三.4）。

---

## 🛑 移动端红线速查（先看这块，再往下读）

报告在手机端打开是**高频场景**，而移动端约束**分散在 §c.5 / §d / §g / §i 四处**，历史上多次因"只读了图表段就开写"而漏掉，导致手机端图表标题与轴标签重叠、数据标签糊成一片（复盘见 `../../../docs/mobile-adaptation-regression.md`）。

下面 7 条是**全部**移动端强制项，先建立整体印象，细节回各节看：

| # | 红线 | 原文位置 | 漏了会怎样 |
|---|---|---|---|
| 1 | `<head>` 有 `viewport` meta | §c.5.1 | iframe 按 980px 缩放，**所有响应式 CSS 全废** |
| 2 | 断点只用 `768` / `480` 两道线 | §c.5.2 | 自创断点导致各组件降级不同步 |
| 3 | 长 token（表全名 / URL）能断行 | §c.5.4 | 撑破容器 → 整页横向溢出、标题被挤偏 |
| 4 | `.kpi-grid` 有 `≤768 → 2 列` / `≤480 → 1 列` | §d | KPI 卡在手机上挤成一条 |
| 5 | `<table>` 外层包 `.table-wrap` | §d | 宽表撑破页面 |
| 6 | 每个图表容器 `class="chart-container"` + `≤768 → 320px` / `≤480 → 260px` | §g | 图表按桌面高度渲染，内容被压扁重叠 |
| 7 | 每个 `setOption` 用 `{baseOption, media:[768,480]}` + 挂 `resize` 监听 | §g | **标题/轴标签/数据标签互相重叠**（最典型的手机端翻车现场） |

> ⚠️ 第 6、7 条是**最易漏**的两条——它们在 §g（本文中后段），且只在 §i 自检里被复述一次。走 `df_to_echarts_option()` 的图表自动带 `media`；**手写 option 的必须自己加**。
>
> 这 7 条对**所有 shape 一致强制**（含 `chart` 单图 / `dashboard` 看板），不因产物轻量而豁免（见 §j.4）。

---

## a. 适用范围

适用于一切**数据驱动**的单文件 HTML 产物（分析报告 / 问数 / 看板等）； §三、§j.4。**§b~§i 工程底线对所有形态一致强制**。

## b. WeData 可信 CDN 白名单（强制 · 默认 1 个 / 导出 docx 时 3 个）

WeData 启用严格 CSP，非白名单 `<script>` 会被浏览器拦截（图表空白）；To B 客户内网也会屏蔽外网 CDN。因此**只允许** `wedata.cdn.tencent.com/w3_workspace/` 域下的脚本，按是否导出 docx 分两档：

**默认(仅渲染交互 HTML)——只放 1 个**：

```
https://wedata.cdn.tencent.com/w3_workspace/echarts.min.js
```

**`export_docx=true` 时——额外放 2 个**(仅此场景才引,见 `html-docx.md` §L)：

```
https://wedata.cdn.tencent.com/w3_workspace/html2canvas.min.js
https://wedata.cdn.tencent.com/w3_workspace/html-docx.min.js
```

| JS 库 | 文件 | 用途 | 何时引 |
| --- | --- | --- | --- |
| ECharts | `echarts.min.js` | 图表渲染（主力 & 唯一图表库） | 总是 |
| html2canvas | `html2canvas.min.js` | DOCX 导出时截非图表区(KPI 卡 / 表格)为位图 | 仅 `export_docx` |
| html-docx | `html-docx.min.js` | 把组装好的 HTML 转为 `.docx` 二进制 | 仅 `export_docx` |

**禁止项**（写入 HTML 前自检必过）：

- ❌ `cdn.jsdelivr.net`、`unpkg.com`、`cdnjs.cloudflare.com`、`bootcdn.net`、`cdn.plot.ly` 等任何公共 CDN
- ❌ Bootstrap / Ant Design / Google Fonts / FontAwesome / jQuery / D3 / Chart.js / jsPDF / docxjs 等白名单外第三方库（导出 docx 用 `html-docx`，**不是** docxjs/jsPDF）
- ❌ `import` 从外部 URL 加载 ES Modules

> 自检动作：生成 HTML 后全文搜 `src="https://`，所有命中域名必须是 `wedata.cdn.tencent.com`；未开 docx 时**不应**出现 html2canvas / html-docx。

## c. 浅色主题 + 全局 CSS 变量（强制）

所有产物必须使用**浅色主题**，禁止深色 / 暗黑背景。本场景需兼顾屏幕阅读与打印，浅色主题天然满足。

`<style>` 开头必须包含以下完整 CSS 变量定义并通篇引用：

```css
:root {
  --color-primary: #636efa; /* 主色：KPI 数值、标题左边框 */
  --color-secondary: #00cc96; /* 辅色：正向指标、toast、建议区块边框 */
  --color-warning: #d4880f; /* 警示色：需关注的指标 */
  --color-danger: #ef553b; /* 危险色：负向指标、差评 */
  --bg-page: #f0f2f5; /* 页面背景 */
  --bg-card: #ffffff; /* 卡片/区块背景 */
  --bg-hover: #f8f9fa; /* 行 hover 背景 */
  --bg-header: #f0f2f5; /* 表头背景 */
  --bg-insight: #f0f7ff; /* 分析洞察区块背景 */
  --bg-suggest: #e8f5e9; /* 建议区块背景 */
  --text-primary: #333333; /* 正文文字 */
  --text-secondary: #666666; /* 次要文字 */
  --text-muted: #888888; /* 辅助文字（标签、注释） */
  --border-light: #e8e8e8; /* 浅色边框 */
  --border-medium: #d0d5dd; /* 中等边框 */
  --shadow-card: 0 2px 8px rgba(0, 0, 0, 0.06); /* 卡片投影 */
  --radius-card: 12px; /* 卡片圆角 */
  --radius-btn: 6px; /* 按钮圆角 */
  --font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}
body {
  font-family: var(--font-family);
  background: var(--bg-page);
  color: var(--text-primary);
  line-height: 1.6;
  padding: 20px;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
}
h1 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 8px;
  color: var(--text-primary);
  overflow-wrap: break-word;
}
.subtitle {
  text-align: center;
  color: var(--text-muted);
  margin-bottom: 24px;
  font-size: 14px;
  /* 数据源常是表全名（catalog.schema.table，无空格长 token）→ 必须允许断行，
     否则窄屏下该 token 不折行会撑破容器、触发整页横向溢出（标题也被挤偏） */
  overflow-wrap: break-word;
  word-break: break-word;
}
```

> ⚠️ **禁止**将 `--bg-page` 改为深色（如 `#0f0c29`、`#1a1a2e`）。深色背景下 ECharts 默认文字颜色会不可读，同时不适合打印。
>
> 📌 **样式框架口径**：本场景使用**纯 CSS 变量 + 手写 class**（如上 `:root` + 下文 §d 各组件），**不引入** Tailwind / Bootstrap / Ant Design 等任何 CSS 框架（CDN 白名单只放 ECharts，框架 CSS 也会被 CSP 拦）。

## c.5 移动端适配硬约束（强制）

产物在前端 iframe 沙箱里渲染，可用宽度区间 ~300px ~ ~1920px。按**宽度**（不是 UA）判定排版。

### 1. viewport meta（必须，所有产物）

`<head>` 顶部第一行必须出现：

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

缺失会导致 iframe 在 srcdoc 模式（移动端降级）下按默认 980px 缩放渲染，所有响应式 CSS 失效。

### 2. 断点规范（统一三档）

```css
/* 默认样式 = 桌面排版（≥ 768px），无前缀 */

@media (max-width: 768px) {
  /* 平板 / 窄 sidebar：KPI 2 列、图表降高、表格仍保持完整列 */
}
@media (max-width: 480px) {
  /* 手机：KPI 1 列、字号下调 */
}
```

**只用** 768 / 480 两道线，**不要**自创 600 / 640 / 720 等中间断点。

### 3. 容器与字号

```css
@media (max-width: 480px) {
  body { padding: 12px; }
  .container { max-width: 100%; }
  .section { padding: 16px; }  /* 卡片内边距窄屏收窄，给图表/表格让出宽度 */
}
```

字号保留 px 硬编码（不引入 rem），每个组件在 ≤480px 下显式定义降级字号（见 §d 各组件）。

### 4. 长 token 强制断行（防整页横滚）

副标题/正文里出现 `catalog.schema.table` 表全名、长 URL、长 ID 等**无空格长 token** 时，承载它们的元素必须能断行，否则窄屏下该 token 不折行会撑破容器、触发**整页横向溢出**（标题也被一起挤偏）。

- 标题 `h1`、副标题 `.subtitle` 已在 §c 基础 CSS 内置 `overflow-wrap: break-word`（必须保留）。
- 任何**自定义**的 Hero / 页头 / 数据源行，凡可能放长表名的，都要带 `overflow-wrap: break-word;`（必要时再加 `word-break: break-word;`）。
- 数据源若特别长，优先只放表名（去掉 catalog 前缀），或用 `<code>` 包裹——`<code>` 在 §d 已带等宽样式但**也要确认**有 `overflow-wrap`。

## d. 通用 UI 组件样式（KPI / section / SQL toggle / toast）

与图表库无关，**所有数据产出 HTML 必须原样引用**（裸单图 `chart` 形态可只取用到的部分）：

### KPI 指标卡片

```css
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.kpi-card {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 20px 16px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-light);
}
.kpi-label {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 6px;
}
.kpi-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--color-primary);
  white-space: nowrap;
}
.kpi-value.green {
  color: var(--color-secondary);
}
.kpi-value.warning {
  color: var(--color-warning);
}
.kpi-value.danger {
  color: var(--color-danger);
}

@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  .kpi-value {
    font-size: 22px;
  }
}
@media (max-width: 480px) {
  .kpi-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .kpi-card {
    padding: 14px 12px;
    min-height: 80px;
  }
  .kpi-value {
    font-size: 20px;
  }
  .kpi-label {
    font-size: 12px;
  }
}
```

**KPI 布局规则**：

1. 固定列数 `repeat(3, 1fr)`，不要用 `auto-fit + minmax`（会导致卡片宽度不一致）。
2. HTML 结构必须是 `<div class="kpi-label">标签</div><div class="kpi-value">数值</div>`，顺序不能反。
3. `.kpi-value` 必须设置 `white-space: nowrap`，防止长数字（如 `R$ 13,541,512`）被挤压换行。
4. 窄屏降级遵循 §c.5 统一断点：`≤768px → 2 列`、`≤480px → 1 列`

### Section 区块 / 洞察 / 建议 / 表格

```css
.section {
  background: var(--bg-card);
  border-radius: var(--radius-card);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--border-light);
}
.section h2 {
  font-size: 18px;
  margin-bottom: 16px;
  color: var(--text-primary);
  padding-left: 12px;
  border-left: 4px solid var(--color-primary);
}
.section h3 {
  font-size: 15px;
  margin: 12px 0 8px;
  color: var(--text-primary);
}

.insight {
  background: var(--bg-insight);
  border-left: 3px solid var(--color-primary);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  margin: 12px 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}
.suggest {
  background: var(--bg-suggest);
  border-left: 3px solid var(--color-secondary);
  padding: 12px 16px;
  border-radius: 0 8px 8px 0;
  margin: 12px 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
}

/* 表格外层 wrapper 强制横滚（移动端列多必备）*/
.table-wrap {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  margin: 12px 0;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}
th {
  background: var(--bg-header);
  padding: 10px;
  text-align: left;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--border-medium);
  white-space: nowrap;
}
td {
  padding: 8px 10px;
  border-bottom: 1px solid var(--border-light);
  color: var(--text-secondary);
}
tr:hover td {
  background: var(--bg-hover);
}
@media (max-width: 480px) {
  table {
    font-size: 12px;
  }
  th, td {
    padding: 6px 8px;
  }
}
```

**表格使用规则**：所有 `<table>` 必须包一层 `<div class="table-wrap">`，否则窄屏下列多的表格会触发整页横滚（而非表格内局部横滚）。

```html
<div class="table-wrap">
  <table id="table-top10">
    <thead>...</thead>
    <tbody>...</tbody>
  </table>
</div>
```

### 查看 SQL 按钮（toggle）

```css
.sql-toggle {
  background: var(--bg-header);
  color: var(--color-primary);
  border: 1px solid var(--border-medium);
  padding: 6px 14px;
  border-radius: var(--radius-btn);
  cursor: pointer;
  font-size: 12px;
  margin: 8px 0;
  position: relative;
  z-index: 10;
}
.sql-toggle:hover {
  background: #e4e7ec;
}
.sql-block {
  display: none;
  background: var(--bg-hover);
  padding: 12px;
  border-radius: 8px;
  font-size: 12px;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  white-space: pre;
  color: var(--text-secondary);
  border: 1px solid var(--border-light);
  position: relative;
  z-index: 10;
}
@media (max-width: 480px) {
  .sql-block {
    font-size: 11px;
    padding: 10px;
  }
  .sql-toggle {
    font-size: 11px;
    padding: 5px 12px;
  }
}
```

```html
<div class="chart-section">
  <div id="chart-1" style="height:450px;"></div>
  <button class="sql-toggle" onclick="toggleSQL('sql-1')">📋 查看 SQL</button>
  <pre class="sql-block" id="sql-1"><code>SELECT ...</code></pre>
</div>

<script>
  function toggleSQL(id) {
    var el = document.getElementById(id);
    el.style.display = el.style.display === "none" ? "block" : "none";
  }
</script>
```

> **z-index 规则**：`.sql-toggle` 和 `.sql-block` 必须 `position:relative; z-index:10`，否则会被 ECharts Canvas 遮挡导致点击无效。

### Toast 通知（异步反馈）

任何异步操作（如刷新数据）完成后必须给用户明确反馈：

```html
<div class="toast" id="toast"></div>
<style>
  .toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--color-secondary);
    color: white;
    padding: 12px 24px;
    border-radius: 8px;
    font-weight: 600;
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s;
  }
  .toast.show {
    opacity: 1;
  }
</style>
<script>
  function showToast(msg, d) {
    var t = document.getElementById("toast");
    t.textContent = msg;
    t.classList.add("show");
    setTimeout(function () {
      t.classList.remove("show");
    }, d || 3000);
  }
</script>
```

## e. 打印样式（`@media print`，强制）

```css
@media print {
  .sql-toggle,
  .sql-block,
  .toast {
    display: none !important;
  }
  body {
    background: white !important;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .container {
    max-width: 100%;
    padding: 0;
  }
  .card,
  .section,
  .kpi-card {
    box-shadow: none;
    border: 1px solid #eee;
    break-inside: avoid;
  }
  /* ECharts 渲染为 canvas，避免跨页被截断 */
  .chart-container {
    break-inside: avoid;
  }
}
```

## f. 下钻交互 HTML 骨架 + ECharts JS 模板（强制）

所有包含**多维度数据**的产物，当数据存在可下钻维度（品类 → 各州、州 → 各品类、月份 → 各品类等）时，**必须实现点击下钻交互**，而非静态图表。

### 下钻实现原理

1. **取数阶段**额外查询交叉维度数据（如 `品类 × 州` 的 GMV 交叉表）。
2. 将交叉数据以 **JSON 嵌入到 HTML 前端**（`var crossData = [...]`）。
3. 通过 **ECharts `chart.on('click', ...)`** 事件监听图表点击。
4. 前端 JS **过滤交叉数据** + `drilldownChart.setOption(newOption)` 动态渲染下钻图表。
5. **纯前端过滤+渲染，不发起额外后端请求**。

### 适用场景判断

| 场景                                   | 是否需要下钻 | 下钻方式                               |
| -------------------------------------- | ------------ | -------------------------------------- |
| 柱状图展示品类 / 地区 / 渠道等分类维度 | ✅ 必须      | 点击柱子 → 展示该分类的子维度分布      |
| 趋势图展示时间序列                     | ✅ 建议      | 点击某月/某天 → 展示该时段的分维度明细 |
| 散点图展示多指标交叉                   | ⚠️ 可选      | 点击数据点 → 展示该实体的详细指标      |
| 饼图展示占比                           | ✅ 建议      | 点击扇区 → 展示该分类的子维度          |
| KPI 卡片                               | ❌ 不需要    | —                                      |

### HTML 骨架

```html
<!-- 主图表（可点击） -->
<div class="section">
  <h2>
    品类 GMV 排行
    <span style="font-size:11px;color:var(--text-muted)">👆 点击柱子下钻</span>
  </h2>
  <div id="chart-category" style="height:450px;"></div>
</div>

<!-- 下钻面板（默认隐藏） -->
<div class="section" id="drilldown-panel" style="display:none;">
  <div
    style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;"
  >
    <h2 id="drilldown-title">下钻详情</h2>
    <button
      class="sql-toggle"
      onclick="closeDrilldown()"
      style="background:#999;color:#fff;font-size:12px;padding:4px 10px;border:none;"
    >
      ✕ 关闭
    </button>
  </div>
  <div id="drilldown-chart" style="height:400px;"></div>
</div>
```

### 关键规则（与图表库解耦的业务规则）

1. **提示用户可点击**：在可下钻图表的标题旁加 `👆 点击柱子下钻` 提示文字。
2. **下钻面板可关闭**：必须有 `✕ 关闭` 按钮，关闭时调用 `dispose()` 释放实例。
3. **平滑滚动**：下钻面板展开时 `scrollIntoView({ behavior: 'smooth' })`。
4. **交叉数据取数阶段获取**：SQL 侧 `GROUP BY state, category`，Python 侧通过 `df_to_echarts_option` 之外的独立序列化（`df.to_dict('records')` + NaN 转 None）嵌入到 HTML `<script>` 中。
5. **纯前端过滤渲染，不额外请求后端**。
6. **所有 JS 必须 ES5 语法**（`var`、`function`，不要箭头函数、`let` / `const`、模板字符串、解构、`class`）。

## g. 图表排版规范（ECharts option 表达）

解决双 Y 轴组合图 / 短时间序列 / 带数值标签柱图 / 饼图 / 折线图常见的标题-legend 重叠、X 轴时间插值错位、柱顶数值被压、容器坍塌等问题。

### 通用 option 规则

| 问题                       | 强制修复（ECharts option）                                                                                                                                  |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 标题与 legend 重叠         | `title: { top: 8 }` + `legend: { top: 36, left: 'center', orient: 'horizontal' }` + `grid.top >= 80`                                                        |
| 柱顶数值被压               | `series[i].label = { show: true, position: 'top', color: '#333' }` + `grid.top` 预留空间                                                                    |
| 折线点标签遮柱值           | 折线 series 用 `label: { show: true, position: 'top' }`，柱状 series 用 `label.position: 'insideTop'` 或留白足够                                            |
| 同类 series 数值标签互相叠字   | 每个 series 加 `labelLayout: { hideOverlap: true }` + `label.minMargin: 4`（放大碰撞盒更早触发隐藏）；折线要"尽量都显示"改 `labelLayout: { moveOverlap: 'shiftY', hideOverlap: true }` |
| 柱顶数值压住 y 轴刻度          | `hideOverlap` **管不到跨组件冲突**，必须换手段：柱值改 `position:'insideTop'` / `yAxis.axisLabel.formatter` 缩短刻度（6000万→0.6亿）/ `yAxis.max` 上浮 15% |
| 轴 name 压住居中标题           | `yAxis: [{ nameLocation: 'end', nameGap: 8 }, ...]`；480 档 media 里直接 `name: ''`                                                                        |
| 月份/季度 X 轴出现日期插值 | `xAxis.type = 'category'`（离散枚举）；时间序列才用 `xAxis.type = 'time'`                                                                                   |
| 组合图柱子贴边             | `series[i].barGap = '20%'` + `series[i].barCategoryGap = '30%'`                                                                                             |
| 容器高度坍塌               | 容器 DOM 显式设 `style="height:450px"`（普通）/ `height:520px`（组合图、时间序列多系列）；**禁用 `height:100%` 或 `height:auto`**，ECharts 依赖容器初始高度；移动端按下文「图表容器移动端降级」规则覆盖 |
| 大数值展示                 | `yAxis.axisLabel.formatter` 自定义千分位；过大改单位 K/M                                                                                                    |
| 大数据量（> 1 万点）       | `series[i].progressive = 2000` + `series[i].large = true` + `largeThreshold = 2000`                                                                         |
| visualMap 误用于"区段染色"      | ❌ **禁止**在 option 顶层加 `visualMap` 调用以实现"预测期阴影 / 不同段颜色"。visualMap 是**会作用到所有 line series 的**：一旦 `pieces` 的范围与实际 y 轴值不重叠，所有曲线会被映射成默认透明色→"曲线全空"。区段背景染色统一走下面「区段阴影」模板的 `markArea` |
| `markArea` 写在 option 顶层        | `markArea` **必须挂载到某个 `series` 上**（推荐主线的 series），写在 option 顶层与 xAxis/series 同级会被**静默忽略**→ 阴影不出现                                                  |
| `stack` 误用于置信区间带          | ❌ **禁止**让 lower 和 upper 两条线同时 `stack: 'X'`——`stack` 是**值相加**，会得到 lower+upper 的总高度，y 轴被拉到 ~2×，其他曲线被压扁。正确写法 lower + (upper-lower) 差值两条 stack（下面「置信带」模板）                                                |

### 图表容器移动端降级（强制）

所有 ECharts 容器必须带 `chart-container` 类，按下面 CSS 在窄屏覆盖 inline `height`：

```html
<div class="chart-container" id="chart-1" style="height:450px;"></div>
```

```css
.chart-container { width: 100%; }
@media (max-width: 768px) { .chart-container { height: 320px !important; } }
@media (max-width: 480px) { .chart-container { height: 260px !important; } }
```

ECharts 不会自动响应 window resize，**必须挂监听**：

```javascript
window.addEventListener('resize', function () {
  for (var id in CHART_INSTANCES) {
    if (CHART_INSTANCES[id] && CHART_INSTANCES[id].resize) CHART_INSTANCES[id].resize();
  }
});
```

### ECharts 移动端 media query 规范（强制）

**所有 ECharts option 必须用 `{baseOption, media}` 结构**。走 `df_to_echarts_option()` 的图表已自动包含 `media`；手写 option 的按下面模板加：

```js
chart.setOption({
  baseOption: { /* title, legend, grid, xAxis, yAxis, series */ },
  media: [
    { query: { maxWidth: 768 }, option: {
      title: { textStyle: { fontSize: 14 } },
      legend: { top: 32, textStyle: { fontSize: 11 }, itemGap: 8 },
      grid: { top: 70, bottom: 50, left: 8, right: 12, containLabel: true },
      xAxis: { axisLabel: { fontSize: 11 } },
      yAxis: { axisLabel: { fontSize: 11 } }
    }},
    { query: { maxWidth: 480 }, option: {
      title: { textStyle: { fontSize: 13 } },
      legend: { bottom: 5, top: 'auto', left: 'center', textStyle: { fontSize: 10 }, itemGap: 6, itemWidth: 14, itemHeight: 8 },
      grid: { top: 50, bottom: 60, left: 8, right: 8, containLabel: true },
      xAxis: { axisLabel: { fontSize: 10, rotate: 30 } },
      yAxis: { axisLabel: { fontSize: 10 } }
    }}
  ]
});
```

**约束**：
- 768 写在 media 数组前、480 在后（ECharts 后写覆盖先写）
- media 里**不要改 series**，只改 title/legend/grid/axisLabel。**三个受控例外**：pie / heatmap（单 series），以及**双 Y 轴组合图**——组合图允许在 media 里改 `series[i].label`，但 `series` 数组**必须与 baseOption 下标一一对齐**（ECharts 按数组下标 merge，顺序错位会把 label 关到错误的系列上；不需要改的系列留空对象 `{}` 占位）
- **双 Y 轴组合图 480 档整体降级（对窄屏最有效）**：柱值 + 折线标签全关、轴 name 清空，数值靠 tooltip 与下方明细表读取：

```js
{ query: { maxWidth: 480 }, option: {
  // series 下标必须与 baseOption 严格对齐：[0]=bar, [1]=line
  series: [{ label: { show: false } }, { label: { show: false } }],
  yAxis: [{ name: '' }, { name: '' }]
}}
```
- pie 的 media 里**不要写** xAxis/yAxis（pie 无轴）
- **`grid.left/right` 取小值（8~16）**：`containLabel: true` 时 ECharts 已自动给轴标签留位，`left/right` 只是标签框外侧的留白，设 40-60 会在短轴标签左边硬塞一大段空白（移动端尤其明显）。短标签场景 `left: 8` 即可，ECharts 自动贴合
- pie 480：`series:[{radius:['28%','58%'], center:['50%','42%'], label:{show:false}}]`；768：`series:[{label:{formatter:'{d}%', fontSize:10}}]`
- **饼图图例统一放底部**（baseOption + 各档 media 的 `legend` 都用 `bottom`，`center` 上移到 `['50%','46%']` 留位），并给 series 加 `avoidLabelOverlap:true` + `labelLayout:{hideOverlap:true}`：外侧引导线标签集中在圆的上半圈，顶部图例会与标签打架（小扇区尤甚）
- heatmap 480：`xAxis.axisLabel.rotate:45` + `visualMap:{orient:'horizontal', bottom:0}`

### 双 Y 轴组合图最小 option 模板

```js
{
  title: { text: '销售额 & 订单数', left: 'center', top: 8, textStyle: { fontSize: 16 } },
  legend: { top: 36, left: 'center', orient: 'horizontal' },
  grid: { top: 90, bottom: 60, left: 8, right: 16, containLabel: true },
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  xAxis: { type: 'category', data: ['Jan', 'Feb', 'Mar', 'Apr'], axisLabel: { hideOverlap: true } },
  yAxis: [
    // nameLocation:'end' + 小 nameGap：轴 name 贴住轴顶，不会顶到居中标题
    // axisLabel.formatter 缩短刻度文本（6000万 → 0.6亿），避免长刻度被柱顶数值压住
    { type: 'value', name: '销售额', position: 'left', nameLocation: 'end', nameGap: 8,
      axisLabel: { formatter: function (v) { return v >= 1e8 ? (v / 1e8) + '亿' : (v >= 1e4 ? (v / 1e4) + '万' : v); } } },
    { type: 'value', name: '订单数', position: 'right', nameLocation: 'end', nameGap: 8,
      splitLine: { show: false } }
  ],
  series: [
    {
      name: '销售额', type: 'bar', yAxisIndex: 0,
      data: [1200, 1500, 900, 2100],
      itemStyle: { color: '#636EFA' },
      // 柱值放柱内顶部：避免柱顶数值向上压住折线标签与 y 轴刻度（见规则表「折线点标签遮柱值」）
      label: { show: true, position: 'insideTop', color: '#fff', formatter: '{c}', minMargin: 4 },
      labelLayout: { hideOverlap: true }
    },
    {
      name: '订单数', type: 'line', yAxisIndex: 1,
      data: [30, 45, 28, 62],
      itemStyle: { color: '#00CC96' },
      label: { show: true, position: 'top', color: '#333', minMargin: 4 },
      // 折线希望"尽量都显示"：先竖向错位让位，实在放不下才隐藏
      labelLayout: { moveOverlap: 'shiftY', hideOverlap: true },
      lineStyle: { width: 2 }, symbolSize: 8
    }
  ]
}
```

**组合图 label 的三类冲突与对应解法**（`hideOverlap` 只能解第一类，另两类必须换手段）：

| 冲突类型 | 典型现象 | 解法 |
| --- | --- | --- |
| 同类 series label 互压（同一碰撞组） | 折线相邻点标签 `21.55%` / `31.47%` 叠字 | `labelLayout: { hideOverlap: true }` + `label.minMargin: 4` 放大碰撞盒 |
| series label 压 y 轴刻度（跨组件，`hideOverlap` 管不到） | 柱顶 `5411.5万` 压住刻度 `6000万` | 柱值改 `position: 'insideTop'`；或 `yAxis.axisLabel.formatter` 缩短刻度；或 `yAxis.max` 上浮 15% 留头部空间 |
| 轴 name 压居中标题 | `销售额（万元）` 顶到主标题 | `yAxis.nameLocation: 'end'` + `nameGap: 8`；480 档直接 `name: ''` |

> **组合图分类数 > 4 时**：柱值一律改 `insideTop`，或直接 `label.show: false` 靠 tooltip + 明细表补数值，不要硬挤在柱顶。

### 时间序列的两种选择

- **短时间序列（月份 / 季度 / 周）** → `xAxis.type: 'category'`，`data: ['2025-01', '2025-02', ...]`（字符串数组），避免 ECharts 自动做日期插值。
- **长时间序列 / 不等间隔** → `xAxis.type: 'time'`，`series.data: [[timestamp, value], ...]` 或 `[[isoString, value], ...]`。**绝不传 `datetime64[ns]`**，Python 侧必须转 ISO 字符串或毫秒时间戳（详见 §h）。

### 历史 + 预测 + 置信带 图表骨架要点（趋势预测场景）

历史线、预测线、置信区间三组数据共用一个 `xAxis.data`，常见踩坑已收录在上方通用规则表（visualMap / markArea / stack 三行）。除此之外的骨架要点：

- **数据对齐**：三组 series（历史、预测、置信带）都要按 `historyMonths.concat(forecastMonths)` 的全长数组构造，非本段填 `null`；预测线**首点 = 历史末点**（避免折线断裂）
- **X 轴**：用 `xAxis.type: 'category'` + 字符串数组（月/周枚举），**不要**用 `'time'` + 原始 `Timestamp`
- **置信带实现**：两条 `type: 'line'` 同 `stack: 'confidence-band'`——下边界 series 数据 = `lower`、`lineStyle.opacity: 0`、**不加** `areaStyle`；上边界 series 数据 = `upper - lower` 差值、`lineStyle.opacity: 0`、**加** `areaStyle` 填淡色。两条都 `silent: true` + `tooltip.show: false`
- **预测区背景阴影**：用 `markArea` 挂在主历史 series 上（顶层 markArea 会被忽略），范围 `[{xAxis: forecastMonths[0]}, {xAxis: forecastMonths.last}]`
- **图例**：补一个空 `data: []` 的 series 用于在 legend 里显示"80% 置信区间"色块（隐藏 series 不占图例位）
- **不要**给下边界加 `areaStyle: rgba(255,255,255,1)` 试图"擦除填充"，会盖住上面的置信带让视觉上消失

## h. `df_to_echarts_option()` 工具函数规范

Python 侧从 DataFrame 生成 ECharts option 的统一入口。完整可运行实现见本 skill `scripts/chart_utils.py`，生成取数/绘图脚本时**必须调用此函数**，不得手写 option dict（手写易漏 NaN 处理、日期转换、主题色注入）。

### 函数签名

```python
def df_to_echarts_option(
    df: pd.DataFrame,
    chart_type: Literal['line', 'bar', 'pie', 'scatter', 'heatmap'],
    x: str,
    y: str | list[str],
    color: str | None = None,
    **kwargs,
) -> dict:
    """从 DataFrame 生成 ECharts option（dict），内嵌到 HTML 后可直接 setOption()"""
```

### 覆盖的图表类型

| chart_type | 必传列                                | 可选列 / kwargs                       | 场景             |
| ---------- | ------------------------------------- | ------------------------------------- | ---------------- |
| `line`     | `x`、`y`（单列或多列列表）            | `color` 分组列、`smooth`、`stack`     | 时间序列、趋势图 |
| `bar`      | `x`、`y`（单列或多列列表）            | `color` 分组列、`horizontal`、`stack` | 分类对比、排行   |
| `pie`      | `x`（类别列）、`y`（单个数值列）      | `ring` 环形、`top_n`                  | 占比             |
| `scatter`  | `x`、`y`（数值列）                    | `size`、`color

... [Content truncated, total 34,236 chars] ...