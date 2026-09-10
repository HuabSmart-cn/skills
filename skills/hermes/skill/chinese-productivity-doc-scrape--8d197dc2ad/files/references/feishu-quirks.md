# Feishu / Lark Wiki Scraping — Specific Quirks

Session notes from scraping https://yunyinghui.feishu.cn/wiki/HnlhwXv9JiebrDkJ9occDNARnPO (the WAIC 2026 aggregator page) on 2026-07-22. These observations inform the main skill.

## Aggregator pages are very thin on text

The top-level "目录" page had only **1117 chars** of `innerText`. The rest was the sidebar (child-doc titles) + chrome (login button, breadcrumbs, view counts). **The actual content is in the children.** If your scraped Markdown for an aggregator page looks short, that's correct — don't keep retrying.

## What worked

- `document.body.innerText` for ordinary text content (paragraphs, headings, lists, the "使用说明" callout)
- Direct `browser_navigate(url)` to a child doc whose URL was in an `<a>` link on the aggregator page (worked for 6 of 6 children tested)
- Sidebar showed *different* sibling docs on each child page (Feishu surfaces context-aware recommendations)

## What did NOT work

### 1. Sidebar button clicks in unauthenticated mode

Clicked 3 sidebar buttons via `browser_click(ref="@eN")`. **None navigated.** URL stayed at the aggregator page. Hooked `history.pushState` to verify — `__lastPush` was `null` after every click. The Feishu SPA simply does not bind navigation handlers in unauth mode.

### 2. React event inspection

`document.querySelectorAll('button').onclick` returned `function ln(){}` (no-op stub). React's synthetic event delegation means real handlers live on root-level listeners, not on individual buttons. **You cannot extract URLs by reading DOM event handlers** — use `<a href>` scraping or Performance API XHR inspection instead.

### 3. Performance API for XHR URLs

`performance.getEntriesByType('resource')` returns only JS/CSS bundle URLs, not the API XHRs that fetch child-doc metadata. Feishu uses `fetch()` not `XMLHttpRequest`, and the Performance API doesn't include those entries by default.

### 4. IndexedDB stores (`moirae-forage-v2-...`, `sophon-forage:...`, `larkw-storage`)

These were present but **empty** in unauth mode. Feishu doesn't preload sidebar data without auth.

### 5. `fetch('https://yunyinghui.feishu.cn/space/api/wiki/v2/tree/getNode?token=...')`

`Failed to fetch` — CORS-blocked from page-script context. Need to run from a proxy or use the page's own cookies (which means auth).

## Bitable (multi-dim table) specifics

URL pattern: `https://<tenant>.feishu.cn/wiki/<token>?table=<tblId>&view=<viewId>`

- Page chrome: tabs, "添加记录", "字段配置", "视图配置", "筛选", "分组", "排序", "行高", "填色", "智能提醒"
- View tabs (left sidebar): "全部汇总", "世博展览馆", "世博中心", "西岸国际会展中心", "张江科学会堂", "其他", "行业统计"
- Column headers rendered as DOM but data cells rendered via canvas
- `innerText` only captures chrome, not data rows
- `browser_vision` (screenshot) DOES capture the visible rows — useful for top-of-table samples

Sample captured from a Bitable with 966 rows:

```
总计: 963 家参展商 | 6 大展馆 | 18 大行业 | 信息已全量填充
1 | 上海稀宇极智科技有限公司 / MiniMax | 世博展览馆 | H1-A801 | ...
2 | 商汤科技 / SenseTime | 世博展览馆 | H1-B807 | ...
3 | 上海阶跃星辰智能科技有限公司 / Shanghai StepFun Intelligence | 世博展览馆 | H1-C107 | ...
```

To get all 966 rows you need one of:
1. User logs in and uses UI "..." → "导出 CSV/Excel"
2. Feishu Bitable Open API call with auth token
3. Programmatic scroll-and-screenshot loop (slow + imperfect)

## Cookie/session observations

- Cookie present in unauth mode: ***REDACTED***
- `localStorage` had `__garr_preload_editable_data__` (Feishu's editable-data preload key) but contents were just JS chunk references, not doc content
- No `passport_token` or `sessionid` cookie — confirming unauthenticated

## Useful DOM probes

```js
// Are there any real <a> links to other wiki pages?
Array.from(document.querySelectorAll('a[href*="wiki/"]'))
  .map(a => ({text: a.innerText.trim().slice(0,80), href: a.href}))

// Is the current view a Bitable?
location.href.match(/table=[^&]+/) ? 'Bitable' : 'Doc'

// Roughly how much text is on the page?
document.body.innerText.length

// Hook pushState to verify sidebar clicks actually navigate
const orig = history.pushState;
history.pushState = function(...a){ window.__lastPush = a; return orig.apply(this, a); };

// Look for Feishu storage DBs (usually empty in unauth mode)
await indexedDB.databases().then(dbs => dbs.map(d => d.name))
```

## Recommended next-step UX

When you hit the "6 out of 16 reachable" wall, the cleanest path is usually:
1. Deliver the 6 you have (don't pretend the others exist)
2. Tell the user explicitly: "to get the rest, I need either (a) the URLs, (b) you paste your feishu.cn cookies, or (c) you click each child doc in your browser and paste the URLs back to me"
3. Don't burn more tool calls clicking sidebar items that demonstrably don't work