# Dashboard Reference

Exhaustive technical reference for Mixpanel dashboard creation, layout, content actions, text card formatting, time filters, and known gotchas. Consult this when you need exact parameter names, field types, API behaviors, or formatting rules.

All code examples use the `mixpanel_headless` Python library.

```python
import mixpanel_headless as mp
from mixpanel_headless.types import (
    CreateDashboardParams,
    UpdateDashboardParams,
    UpdateTextCardParams,
    UpdateReportLinkParams,
    Dashboard,
)

ws = mp.Workspace()
```

---

## 1. API Reference

### 1.1 Types

#### CreateDashboardParams

Import: `from mixpanel_headless.types import CreateDashboardParams`

| Field | Type | Default | Constraints |
|---|---|---|---|
| `title` | `str` | **required** | Max 255 chars |
| `description` | `str \| None` | `None` | Max 400 chars |
| `is_private` | `bool \| None` | `None` (False) | |
| `is_restricted` | `bool \| None` | `None` (False) | |
| `filters` | `list[Any] \| None` | `None` | Dashboard-level filters |
| `breakdowns` | `list[Any] \| None` | `None` | Dashboard-level breakdowns |
| `time_filter` | `Any \| None` | `None` | Dashboard-level time filter (see Section 5) |
| `duplicate` | `int \| None` | `None` | ID of dashboard to duplicate |

```python
params = CreateDashboardParams(
    title="Product Health Dashboard",
    description="Key metrics for monitoring product health.",
)
```

#### UpdateDashboardParams

Import: `from mixpanel_headless.types import UpdateDashboardParams`

All fields are optional. Only provided fields are sent to the API.

| Field | Type | Default | Constraints |
|---|---|---|---|
| `title` | `str \| None` | `None` | Max 255 chars |
| `description` | `str \| None` | `None` | Max 400 chars |
| `is_private` | `bool \| None` | `None` | |
| `is_restricted` | `bool \| None` | `None` | |
| `filters` | `list[Any] \| None` | `None` | Dashboard-level filters |
| `breakdowns` | `list[Any] \| None` | `None` | Dashboard-level breakdowns |
| `time_filter` | `Any \| None` | `None` | Dashboard-level time filter |
| `layout` | `Any \| None` | `None` | Layout patch (see Section 3) |
| `content` | `Any \| None` | `None` | Content action (see Section 2) |

```python
params = UpdateDashboardParams(title="Q1 Metrics v2")
data = params.model_dump(exclude_none=True)
# {"title": "Q1 Metrics v2"}
```

#### UpdateTextCardParams

Import: `from mixpanel_headless.types import UpdateTextCardParams`

| Field | Type | Default | Notes |
|---|---|---|---|
| `markdown` | `str \| None` | `None` | HTML content for the text card (see Section 4) |

Model config: `extra="allow"` -- additional fields are preserved.

```python
params = UpdateTextCardParams(markdown="<h2>Section Title</h2><p>Description.</p>")
```

#### UpdateReportLinkParams

Import: `from mixpanel_headless.types import UpdateReportLinkParams`

| Field | Type | Default | Notes |
|---|---|---|---|
| `link_type` | `str` | **required** | Serialized as `"type"` via alias. Example: `"embedded"` |

Model config: `populate_by_name=True, extra="allow"`.

```python
params = UpdateReportLinkParams(link_type="embedded")
data = params.model_dump(by_alias=True, exclude_none=True)
# {"type": "embedded"}
```

#### Dashboard (response model)

Import: `from mixpanel_headless.types import Dashboard`

The `Dashboard` model uses `extra="allow"` so new API fields are preserved automatically. Key fields:

| Field | Type | Description |
|---|---|---|
| `id` | `int` | Unique dashboard identifier |
| `title` | `str` | Dashboard title |
| `description` | `str \| None` | Dashboard description |
| `is_private` | `bool` | Whether dashboard is private |
| `is_restricted` | `bool` | Whether access is restricted |
| `creator_id` | `int \| None` | Creator's user ID |
| `creator_name` | `str \| None` | Creator's name |
| `creator_email` | `str \| None` | Creator's email |
| `created` | `datetime \| str \| None` | Creation timestamp |
| `modified` | `datetime \| str \| None` | Last modification timestamp |
| `is_favorited` | `bool \| None` | Whether current user favorited it |
| `pinned_date` | `str \| None` | Date pinned, if any |
| `layout_version` | `str \| None` | Layout version metadata |
| `unique_view_count` | `int \| None` | Number of unique viewers |
| `total_view_count` | `int \| None` | Total view count |

The `layout` field (from `get_dashboard`) contains the full layout structure described in Section 3.

### 1.2 Workspace Methods

#### List dashboards

```python
def list_dashboards(self, *, ids: list[int] | None = None) -> list[Dashboard]
```

Retrieves all dashboards visible to the authenticated user, optionally filtered by specific IDs.

```python
dashboards = ws.list_dashboards()
dashboards = ws.list_dashboards(ids=[101, 102, 103])
```

#### Create dashboard

```python
def create_dashboard(self, params: CreateDashboardParams) -> Dashboard
```

Creates a new dashboard. Returns the newly created `Dashboard`.

```python
dashboard = ws.create_dashboard(CreateDashboardParams(title="Q1 Metrics"))
print(dashboard.id)  # Use this ID for all subsequent operations
```

#### Get dashboard

```python
def get_dashboard(self, dashboard_id: int) -> Dashboard
```

Retrieves a single dashboard by ID. The response includes the full `layout` structure with row IDs, cell IDs, and content IDs needed for layout patching.

```python
dash = ws.get_dashboard(dashboard_id)
# Access layout: dash.layout["order"], dash.layout["rows"]
```

#### Update dashboard

```python
def update_dashboard(self, dashboard_id: int, params: UpdateDashboardParams) -> Dashboard
```

Updates an existing dashboard. Only provided fields are modified. Returns the updated `Dashboard`.

Used for three distinct operations:
1. **Metadata updates** -- title, description, privacy, time filter
2. **Content actions** -- add/remove/update reports and text cards (via `content` field)
3. **Layout patches** -- rearrange rows, resize cells (via `layout` field)

```python
# Metadata update
ws.update_dashboard(dashboard_id, UpdateDashboardParams(title="New Title"))

# Content action (see Section 2)
ws.update_dashboard(dashboard_id, UpdateDashboardParams(content={...}))

# Layout patch (see Section 3)
ws.update_dashboard(dashboard_id, UpdateDashboardParams(layout={...}))
```

#### Delete dashboard

```python
def delete_dashboard(self, dashboard_id: int) -> None
```

Permanently deletes a dashboard. No return value.

#### Bulk delete dashboards

```python
def bulk_delete_dashboards(self, ids: list[int]) -> None
```

Deletes multiple dashboards in a single API call.

```python
ws.bulk_delete_dashboards([101, 102, 103])
```

#### Favorite / unfavorite dashboard

```python
def favorite_dashboard(self, dashboard_id: int) -> None
def unfavorite_dashboard(self, dashboard_id: int) -> None
```

Toggles the current user's favorite status on a dashboard. Favorited dashboards appear in the user's favorites list in the Mixpanel UI.

#### Pin / unpin dashboard

```python
def pin_dashboard(self, dashboard_id: int) -> None
def unpin_dashboard(self, dashboard_id: int) -> None
```

Pinned dashboards appear at the top of the dashboard list for all project members.

#### Add report to dashboard

```python
def add_report_to_dashboard(self, dashboard_id: int, bookmark_id: int) -> Dashboard
```

**CLONES** the specified bookmark onto the dashboard. The original bookmark is unchanged. The cloned report gets a new content ID and appears with a "Duplicate of ..." name prefix. Returns the updated `Dashboard`.

**Prefer inline content actions (Section 2) over this method** to avoid cloning behavior.

```python
updated_dash = ws.add_report_to_dashboard(dashboard_id, bookmark_id)
```

#### Remove report from dashboard

```python
def remove_report_from_dashboard(self, dashboard_id: int, bookmark_id: int) -> Dashboard
```

Removes a report from a dashboard by its bookmark/report ID. Returns the updated `Dashboard`.

```python
ws.remove_report_from_dashboard(dashboard_id, report_id)
```

#### Update text card

```python
def update_text_card(self, dashboard_id: int, text_card_id: int, params: UpdateTextCardParams) -> None
```

Updates a text card's content. The `text_card_id` is the content ID from the layout.

```python
ws.update_text_card(dashboard_id, text_card_id, UpdateTextCardParams(
    markdown="<h2>Updated Title</h2><p>New description.</p>"
))
```

#### Update report link

```python
def update_report_link(self, dashboard_id: int, report_link_id: int, params: UpdateReportLinkParams) -> None
```

Updates a report link on a dashboard.

```python
ws.update_report_link(dashboard_id, report_link_id, UpdateReportLinkParams(link_type="embedded"))
```

---

## 2. Content Actions

Content actions add, remove, and modify items on a dashboard via the `content` field of `UpdateDashboardParams`. Each action is a dictionary with `action`, `content_type`, and action-specific fields.

### Content types

| Type | Description |
|---|---|
| `report` | A report card (insights, funnels, retention, flows) |
| `text` | A text/markdown card |

### Actions

| Action | Description |
|---|---|
| `create` | Add new content to the dashboard |
| `delete` | Remove content from the dashboard |
| `update` | Modify existing content in place |
| `move` | Move content to a different position (prefer layout PATCH — Section 3 — instead) |
| `duplicate` | Duplicate content within the dashboard |
| `undelete` | Restore previously deleted content |

### 2.1 Create text card

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "create",
        "content_type": "text",
        "content_params": {
            "markdown": "<h2>Section Title</h2><p>Brief description of this section.</p>"
        },
    }
))
```

The new text card is appended to the bottom of the dashboard. Rearrange via layout patch (Section 3) afterward.

### 2.2 Create report from existing bookmark (clones it)

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "create",
        "content_type": "report",
        "content_params": {
            "source_bookmark_id": bookmark_id
        },
    }
))
```

This clones the bookmark onto the dashboard. The original bookmark is unchanged. The clone gets a new content ID.

### 2.3 Create report inline (preferred)

```python
import json

ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "create",
        "content_type": "report",
        "content_params": {
            "bookmark": {
                "name": "Daily Active Users",
                "type": "insights",
                "params": json.dumps(result.params),
                "description": "DAU trend over the last 90 days.",
            }
        },
    }
))
```

**This is the preferred method.** It creates the report directly on the dashboard without cloning, without creating a separate bookmark entity, and without the "Duplicate of ..." name prefix.

Supported `type` values: `"insights"`, `"funnels"`, `"retention"`, `"flows"`

The `params` field must be a JSON string (use `json.dumps()`), not a dict.

### 2.4 Delete content

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "delete",
        "content_type": "report",  # or "text"
        "content_id": content_id,
    }
))
```

The `content_id` is the numeric ID from the layout cells.

### 2.5 Update text card content

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "update",
        "content_type": "text",
        "content_id": text_card_id,
        "content_params": {
            "markdown": "<h2>Updated Title</h2><p>New description.</p>"
        },
    }
))
```

### 2.6 Duplicate content

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "duplicate",
        "content_type": "report",
        "content_id": content_id,
    }
))
```

### 2.7 Undelete content

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "undelete",
        "content_type": "report",
        "content_id": content_id,
    }
))
```

---

## 3. Layout System

### 3.1 Grid Fundamentals

- **12 columns** per row (`ROW_TOTAL_WIDTH = 12`)
- **Max 4 items** per row
- **Max 30 rows** per dashboard
- **Layout version:** `"2.0.0"`
- **Standard widths:** 3 (quarter), 4 (third), 6 (half), 12 (full)
- Cell widths in a row must sum to exactly 12

### 3.2 Layout Structure from GET

When you call `ws.get_dashboard(id)`, the layout is returned in this structure:

```json
{
  "version": "2.0.0",
  "order": ["row-abc-123", "row-def-456"],
  "rows": {
    "row-abc-123": {
      "height": 0,
      "cells": [
        {
          "id": "cell-aaa-111",
          "width": 12,
          "content_id": 90001,
          "content_type": "text"
        }
      ]
    },
    "row-def-456": {
      "height": 336,
      "cells": [
        {
          "id": "cell-bbb-222",
          "width": 4,
          "content_id": 90002,
          "content_type": "report"
        },
        {
          "id": "cell-ccc-333",
          "width": 4,
          "content_id": 90003,
          "content_type": "report"
        },
        {
          "id": "cell-ddd-444",
          "width": 4,
          "content_id": 90004,
          "content_type": "report"
        }
      ]
    }
  }
}
```

Key fields:

| Field | Description |
|---|---|
| `version` | Always `"2.0.0"`. **Never include in PATCH.** |
| `order` | Ordered list of row IDs. **Called `order` in GET response.** |
| `rows` | Dict mapping row ID to `{height, cells}`. |
| `rows[].height` | Row height in pixels. `0` means auto (text-only rows). |
| `rows[].cells` | Ordered list of cells in the row. |
| `cells[].id` | Cell identifier (UUID string). |
| `cells[].width` | Cell width (1-12). Sum of all cells in a row must equal 12. |
| `cells[].content_id` | Numeric ID of the content item. |
| `cells[].content_type` | One of: `"text"`, `"report"`. |

### 3.3 Layout PATCH Format

When patching layout via `UpdateDashboardParams(layout=...)`, use this format. **Critical: `rows` must be a list (not a dict).** The GET response returns rows as a dict keyed by row ID, but the PATCH expects a list with `id` on each row object.

```json
{
  "rows_order": ["row-abc-123", "row-def-456"],
  "rows": [
    {
      "id": "row-abc-123",
      "height": 0,
      "cells": [
        {
          "id": "cell-aaa-111",
          "width": 12,
          "content_id": 90001,
          "content_type": "text"
        }
      ]
    },
    {
      "id": "row-def-456",
      "height": 418,
      "cells": [
        {
          "id": "cell-bbb-222",
          "width": 6,
          "content_id": 90002,
          "content_type": "report"
        },
        {
          "id": "cell-ccc-333",
          "width": 6,
          "content_id": 90003,
          "content_type": "report"
        }
      ]
    }
  ]
}
```

**Critical differences from GET:**

| GET response | PATCH payload |
|---|---|
| `"order"` | `"rows_order"` |
| `"rows"` is a **dict** keyed by row ID | `"rows"` is a **list** with `"id"` on each row |
| Includes `"version"` | **Never include `"version"`** |

### 3.4 Complete Layout Patch Example

```python
# 1. Get current layout to discover IDs
dash = ws.get_dashboard(dashboard_id)
layout = dash.layout  # dict with version, order, rows

# 2. Extract existing row/cell IDs and content IDs
# (IDs are auto-generated UUIDs; you must read them, not invent them)

# 3. Build the patch — rows_order (not order), rows as LIST (not dict)
row_ids = list(layout["order"])  # preserve current order, or rearrange
rows_list = []
for row_id in row_ids:
    row = layout["rows"][row_id]
    rows_list.append({
        "id": row_id,
        "height": row.get("height", 0),
        "cells": row.get("cells", []),
    })

ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    layout={"rows_order": row_ids, "rows": rows_list}
))
```

### 3.5 Width Assignment Table

| Content | Width | Rationale |
|---|---|---|
| Text card (section header) | 12 | Always full width |
| KPI metric card | 3 or 4 | Pack 3-4 per row |
| Line/bar chart (paired) | 6 | Side-by-side comparison |
| Line/bar chart (solo) | 12 | Full width for detail |
| Table | 12 | Needs full width for columns |
| Funnel (3+ steps) | 12 | Complex funnels need space |
| Retention curve | 12 | Full width for cohort grid |
| Sankey/flow | 12 | Always full width |

### 3.6 Height Guidelines

| Row Configuration | Height (px) | Notes |
|---|---|---|
| Text-only row | 0 | Auto height, expands to fit content |
| KPI row (3-4 metric cards) | 336 | Compact number display |
| Two charts side-by-side (6+6) | 418 | Standard chart height |
| Single full-width chart | 500 | More vertical space for detail |
| Full-width funnel or table | 588 | Extra space for steps/rows |

Heights are guidelines. The Mixpanel UI allows manual resizing. Use `0` for text-only rows to let them auto-size.

---

## 4. Text Card Formatting

Text cards use a restricted subset of HTML. Mixpanel's frontend renders them through a TipTap editor which sanitizes input and only supports specific tags.

### 4.1 Allowed HTML Tags

| Category | Tags | Notes |
|---|---|---|
| Headings | `<h1>`, `<h2>`, `<h3>` | Prefer `<h2>` and `<h3>`. Avoid `<h1>` (too large for dashboard cards). |
| Text | `<p>`, `<strong>`, `<em>`, `<u>`, `<s>`, `<mark>`, `<code>` | Use `<strong>` not `<b>`. Use `<em>` not `<i>`. |
| Structure | `<blockquote>`, `<hr>`, `<br>` | `<blockquote>` renders as indented block with left border. |
| Lists | `<ul>`, `<ol>`, `<li>` | Nested lists are supported. |
| Links | `<a href="...">` | External links open in new tab. |

### 4.2 Tags That Will Be STRIPPED

These tags are silently removed by the sanitizer. Your content will render without them, potentially breaking layout:

| Tag | Reason | Use Instead |
|---|---|---|
| `<div>` | Stripped by sanitizer | `<p>` |
| `<span>` | Stripped by sanitizer | Inline formatting tags (`<strong>`, `<em>`, etc.) |
| `<b>` | Non-semantic | `<strong>` |
| `<i>` | Non-semantic | `<em>` |
| `<img>` | Not supported | — |
| `<table>`, `<tr>`, `<td>`, `<th>` | Not supported | Use a report card with table chart type |
| Any inline `style` attributes | Stripped | Use semantic tags |
| Any `class` attributes | Stripped | Use semantic tags |

### 4.3 Formatting Rules

1. **Strip all `\n` newlines and collapse whitespace before sending.** Mixpanel's TipTap editor takes a markdown-it code path that mangles HTML when newlines are present. Always call `.replace("\n", "").strip()` on the markdown string. Multiple spaces or tabs can also cause rendering issues.

2. **Each HTML element renders as a new line** in the card. A `<p>` tag produces one visual line. Two consecutive `<p>` tags produce two lines. Do not try to use `\n` for line breaks.

3. **Character limit:** Practical limit is 2,000 characters. Keep text cards under 500 characters for readability. Dashboard cards have limited vertical space.

4. **No Markdown syntax.** Despite the field being called `markdown`, it accepts only HTML. Do not send `# Heading` or `**bold**` -- use `<h2>Heading</h2>` and `<strong>bold</strong>`.

5. **Section header pattern:** `<h2>Section Title</h2><p>One sentence description.</p>` -- keep section titles to 2-4 words.

6. **Explainer pattern:** `<p>^ Brief data-driven insight about the chart above.</p>` -- the `^` caret is a visual convention indicating this card explains the chart directly above it.

### 4.4 Text Card Templates

#### Dashboard intro

```python
markdown = (
    "<h2>Product Health Dashboard</h2>"
    "<p>Core metrics for monitoring product health. Updated daily.</p>"
)
```

#### Section header

```python
markdown = (
    "<h2>Growth Trends</h2>"
    "<p>User acquisition and activation metrics over time.</p>"
)
```

#### Explainer card (data-driven)

```python
markdown = (
    f"<p>^ DAU is <strong>{latest_dau:,.0f}</strong>, "
    f"{'up' if trend > 0 else 'down'} "
    f"<strong>{abs(trend):.1f}%</strong> vs. last week.</p>"
).replace("\n", "")
```

#### Methodology note

```python
markdown = (
    "<p><em>Methodology:</em> DAU counts unique users who triggered "
    "any event in a calendar day. Excludes bot traffic.</p>"
)
```

#### Key takeaway

```python
markdown = (
    "<h3>Key Takeaway</h3>"
    "<p>Mobile conversion is <strong>2.3x higher</strong> than desktop. "
    "Prioritize mobile onboarding improvements.</p>"
)
```

#### Warning / caveat

```python
markdown = (
    "<p><strong>Note:</strong> Data prior to Jan 15 reflects the old "
    "tracking schema. Direct comparison across that boundary is unreliable.</p>"
)
```

#### Bullet list summary

```python
markdown = (
    "<h3>Q1 Highlights</h3>"
    "<ul>"
    "<li>DAU grew <strong>18%</strong> quarter-over-quarter</li>"
    "<li>Signup funnel conversion improved from 12% to 15%</li>"
    "<li>7-day retention stable at <strong>42%</strong></li>"
    "</ul>"
)
```

#### Blockquote callout

```python
markdown = (
    "<blockquote>This dashboard covers the core product loop: "
    "acquisition, activation, retention. For revenue metrics, "
    "see the Revenue Dashboard.</blockquote>"
)
```

### 4.5 Sending Text Card Content

Always strip newlines before sending:

```python
# Build multi-line for readability in code
markdown = (
    "<h2>Section Title</h2>"
    "<p>Description paragraph one.</p>"
    "<p>Description paragraph two.</p>"
)

# Strip newlines (critical -- TipTap mangles HTML with newlines)
clean_markdown = markdown.replace("\n", "")

# Send via content action
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    content={
        "action": "create",
        "content_type": "text",
        "content_params": {"markdown": clean_markdown},
    }
))

# Or update existing text card directly
ws.update_text_card(dashboard_id, text_card_id, UpdateTextCardParams(
    markdown=clean_markdown
))
```

---

## 5. Dashboard Time Filters

Dashboard-level time filters override individual report time ranges. Set them at creation time or via update.

### 5.1 "Last N days" (rolling window)

```python
time_filter = {
    "dateRange": {
        "type": "in the last",
        "window": {"unit": "day", "value": 30}
    },
    "displayText": "Last 30 days"
}

dashboard = ws.create_dashboard(CreateDashboardParams(
    title="Rolling 30-Day Metrics",
    time_filter=time_filter,
))
```

Window units: `"day"`, `"week"`, `"month"`

### 5.2 "Since date" (open-ended)

```python
time_filter = {
    "dateRange": {
        "type": "since",
        "from_date": "2025-01-01"
    },
    "displayText": "Since Jan 1, 2025"
}

dashboard = ws.create_dashboard(CreateDashboardParams(
    title="2025 Metrics",
    time_filter=time_filter,
))
```

### 5.3 "Between dates" (fixed range)

```python
time_filter = {
    "dateRange": {
        "type": "between",
        "from_date": "2025-01-01",
        "to": "2025-03-31"
    },
    "displayText": "Jan 1 - Mar 31, 2025"
}

dashboard = ws.create_dashboard(CreateDashboardParams(
    title="Q1 2025 Metrics",
    time_filter=time_filter,
))
```

### 5.4 Updating time filter on existing dashboard

```python
ws.update_dashboard(dashboard_id, UpdateDashboardParams(
    time_filter={
        "dateRange": {
            "type": "in the last",
            "window": {"unit": "week", "value": 4}
        },
        "displayText": "Last 4 weeks"
    }
))
```

### 5.5 Removing time filter

```python
# Set to empty dict or None to remove dashboard-level time filter
ws.update_dashboard(dashboard_id, UpdateDashboardParams(time_filter={}))
```

### 5.6 Dashboard-Level Filters and Breakdowns

`CreateDashboardParams` accepts `filters` and `breakdowns` fields. These apply globally across all reports on the dashboard. In practice, dashboard-level filters are primarily configured through the Mixpanel UI. The API fields are useful for:

- **Preserving existing filters** when updating a dashboard programmatically
- **Reading filters** from `get_dashboard()` to understand the dashboard's scope

```python
# Read existing dashboard-level filters
dash = ws.get_dashboard(dashboard_id)
print(dash.filters)     # list of filter dicts, or None
print(dash.breakdowns)  # list of breakdown dicts, or None
```

---

## 6. Critical Gotchas

### 6.1 CreateBookmarkParams(dashboard_id=X) does NOT add to layout

The `dashboard_id` field on `CreateBookmarkParams` exists but only sets internal metadata. It does **not** place the report on the dashboard layout. You must use one of:
- `ws.add_report_to_dashboard(dashboard_id, bookmark_id)` (clones the bookmark)
- Inline content action via `UpdateDashboardParams(content=...)` (preferred)

### 6.2 add_report_to_dashboard() CLONES the bookmark

This method creates a "Duplicate of ..." copy of the bookmark. The original bookmark is unchanged. The cloned report gets a new `content_id` on the dashboard. To avoid this:
- 

... [Content truncated, total 37,982 chars] ...