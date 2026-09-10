---
name: chinese-productivity-doc-scrape
description: "Scrape/crawl Chinese productivity-tool wiki pages (Feishu/Lark, DingTalk docs, WeChat Work docs, Notion-China) into Markdown. Handles aggregator-style pages that link to permissioned child docs, multi-dim tables (Bitable), embedded images, and unauthenticated-view limits."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [scrape, crawl, feishu, lark, dingtalk, wechat-work, productivity, wiki, chinese]
    related_skills: [dogfood]
---

# Scrape Chinese Productivity Wiki Pages into Markdown

## Overview

This skill guides you through scraping Chinese productivity-tool wiki pages (Feishu/Lark, DingTalk docs, WeChat Work docs, Notion-China) — specifically the kind of pages where the top-level page is a **目录/aggregator page** linking to many private/permissioned child documents. These tools share common quirks that bite naive scrapers: sidebar buttons may not respond to clicks in unauthenticated mode, child-doc URLs aren't exposed in public HTML, Bitable (multi-dim tables) uses canvas rendering, and embedded PDFs/images have no text content.

The deliverable is always **one consolidated Markdown file** plus **per-child-doc Markdown files** in an output directory.

## When to use

Trigger this skill when the user asks any of:
- "把这个飞书/钉钉/企微文档爬下来"
- "把这个 wiki 页面的内容都抓出来"
- "I need to extract all content from this Chinese team wiki"
- "把 [feishu/lark/dingtalk URL] 的内容导出成 Markdown"

Don't use this skill for:
- Public marketing websites (just use `browser_navigate` + `browser_snapshot` directly)
- PDFs (use `pdf` or `ocr-and-documents` skills)
- Word/Excel/PPT files (use `docx`/`xlsx`/`powerpoint` skills)
- A single well-formed article (this skill is overkill)

## Inputs

The user provides:
1. **Target URL** — the wiki/doc page to scrape
2. **Tenant domain** — e.g. `yunyinghui.feishu.cn` (inferred from URL)
3. **Output directory** (optional, default `./<doc-title>/`)

## Workflow

### Phase 1: Reconnaissance — confirm the page type

Before scraping anything, navigate to the page and check what kind of page it is. **Most Chinese productivity wiki pages fall into one of three categories**, and the workflow diverges for each:

| Type | Indicator | Scrape strategy |
|---|---|---|
| **Aggregator/目录页** | Body is short (~1KB text), sidebar shows many child doc titles, body has callout/使用说明 box | Page itself is mostly a link list; each child must be scraped separately |
| **Long-form article** | Body is large (>5KB), single H1, paragraphs/headings | Single pass: snapshot → scroll → extract |
| **Bitable (multi-dim table)** | URL contains `?table=...&view=...`, body shows table view tabs | DOM scrape gives only chrome; need screenshot, scroll-load, or ask user to export CSV |

```bash
browser_navigate(url="<target_url>")
browser_console(expression="document.body.innerText.length")  # rough size check
```

If the page is an aggregator, **STOP** and run Phase 2 before promising the user you can scrape everything.

### Phase 2: Diagnose auth + discover child URLs

For Chinese productivity tools, **child-document URLs are NOT in the public HTML**. They live behind authenticated API calls. Before scraping, verify what you can actually reach:

```js
// Find all real <a> links (these are accessible without auth)
Array.from(document.querySelectorAll('a[href*="wiki/"]')).map(a => ({
  text: a.innerText.trim().slice(0,80),
  href: a.href
}))
```

If this returns fewer than the sidebar implies, **most child docs are gated**. Tell the user upfront — don't waste tool calls clicking through sidebar buttons that won't navigate.

Quick test: click a sidebar button via `browser_click(ref="@eN")`. If the URL doesn't change and `history.pushState` was never called (hook `history.pushState` first to verify), then **the page is unauthenticated and sidebar navigation is dead**.

```js
// Hook pushState BEFORE clicking
if (!window.__hooked) {
  const orig = history.pushState;
  history.pushState = function(...args) { window.__lastPush = args; return orig.apply(this, args); };
  window.__hooked = true;
}
// Now click sidebar items, then check window.__lastPush
```

### Phase 3: Choose a delivery path

Based on Phase 2 results, present the user with honest options. Don't promise more than you can deliver:

| What you can do | What you can't do |
|---|---|
| ✅ Scrape the top-level aggregator page (full text + sidebar structure) | ❌ Reach child docs without the URL or auth |
| ✅ Scrape any child doc whose URL appears in `<a>` links | ❌ Trigger sidebar navigation in unauth mode |
| ✅ Screenshot Bitable view + extract visible rows | ❌ Extract full table contents from canvas-rendered grids |

Then offer 2-4 specific options via `clarify`:
- Just save what I can reach (N child docs)
- You provide URLs for the rest, I scrape them
- You paste cookies for login, I retry
- Give up on the gated child docs

### Phase 4: Scrape each reachable page

For each accessible URL:

1. **Navigate** with `browser_navigate(url=...)`
2. **Wait** for content to load (Chinese SPAs are slow): `browser_console(expression="new Promise(r=>setTimeout(()=>r(document.body.innerText.length),3000))")`
3. **Extract text** with `browser_console(expression="document.body.innerText")` — note: this DOES NOT capture canvas-rendered content (Bitable, embedded charts)
4. **Detect images/PDFs** that are the actual content: look for short body text + large image elements → use `browser_vision` to capture
5. **Save per-page Markdown** to `output_dir/NN_<title>.md`

### Phase 5: Consolidate

Build a single `output_dir/README.md` (or `index.md`) with:
- Frontmatter: source URL, scrape time, total child docs reached / total child docs referenced
- Table of contents linking to each per-doc file
- A **clear "未能爬取" section** listing child docs that exist in the sidebar but were unreachable, with reasons

### Phase 6: Deliver

Final message to user must include:
1. Brief summary: "N out of M docs scraped"
2. **Honest gap report**: which docs are missing and why
3. Next-step offer: "If you want me to reach the missing ones, send me their URLs / your cookie / a screenshot showing the URLs"
4. **Path to the output directory** so the user knows where to look

## Critical pitfalls

### Pitfall #1: Don't promise "I'll scrape all 16 child docs" before checking auth

I lost iterations in this session promising to crawl all 16 children when only 6 had reachable URLs. Always run Phase 2 first, then make a delivery plan. **It's not lazy to ask the user for help reaching private content — it's honest.**

### Pitfall #2: Unauthenticated sidebar clicks do NOT navigate

Feishu (and likely DingTalk, WeChat Work) sidebar buttons in unauthenticated mode register clicks but the React handler does nothing — URL stays the same, no `pushState` fires, no XHR fires. **Don't burn tool calls clicking sidebar items hoping they'll work.** Verify with one click + URL check first.

### Pitfall #3: Bitable (multi-dim tables) renders via canvas, not DOM

`document.body.innerText` on a Bitable view returns only the chrome (titles, tab labels, "添加记录" buttons) — actual cell contents are NOT in the DOM. Use:
- `browser_vision` to screenshot what's visible
- Ask user to use the "..." → "导出 CSV/Excel" UI control
- Or call Feishu Bitable Open API directly if you have credentials

### Pitfall #4: Embedded PDFs and images = no text

Documents whose body is one giant PDF (e.g. "WAIC展品信息.pdf", "WAIC2026汇报.pdf") or one big image (e.g. "WAIC2026世界人工智能大会高清展位图") have ~zero text content even though they're "documents". Note this in the per-doc Markdown and tell the user — don't pretend you scraped the PDF.

### Pitfall #5: Sidebar contents change per page

Each child page in a Feishu wiki shows a DIFFERENT set of sibling docs in the sidebar (Feishu surfaces "related" docs based on navigation context). Don't assume the sidebar from page A applies to page B. After each navigation, re-collect sidebar contents if relevant.

### Pitfall #6: React events aren't on `onclick` attributes

In Feishu's modern SPA, buttons have `function ln(){}` as `onclick` but real handlers are attached via React's synthetic event delegation. `document.querySelectorAll('[onclick]')` and `el.onclick` both return empty. **You can't extract URLs by reading DOM event handlers.** Use `<a href>` scraping instead, or `Performance.getEntriesByType('resource')` to find XHR URLs.

### Pitfall #7: Tool-call budgets are real

A naive scrape of an aggregator + 16 children can easily blow through 50+ tool calls. Set a `todo` list early, batch `browser_console` calls when possible, and **stop and ask the user** if you find more gated docs than reachable ones — don't grind through the whole sidebar blindly.

## Output structure template

```
<output_dir>/
├── README.md                  # Index + gap report
├── 00_overview.md             # Top-level aggregator page
├── 01_<child-doc-title>.md
├── 02_<child-doc-title>.md
└── ...
```

Each per-doc Markdown should include:
- Source URL
- Type (article / bitable / image-only / pdf-only)
- Last-modified date + read/visitor counts (visible in page header)
- Body text (verbatim from `innerText`)
- For bitable: visible columns + sample rows + note about canvas limitation
- Sidebar structure (as TOC)

## Reference material

See `references/feishu-quirks.md` for the specific observations from the WAIC2026 scrape session that motivated this skill (sidebar non-responsiveness, Bitable canvas rendering, etc.).

See `templates/per-doc-template.md` for a copy-paste starter for each child doc's Markdown file.