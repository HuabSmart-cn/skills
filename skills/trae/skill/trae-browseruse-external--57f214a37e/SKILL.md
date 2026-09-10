---
name: "TRAE-browseruse-external"
description: "Automate tasks in the user's own browser (Chrome on their machine). Invoke when the user says things like 'use my browser', 'open in my Chrome', 'use the browser on my computer', or wants to browse/interact/test web pages in their local Chrome.When the complete content of this skill cannot be found in the current context, load this skill before using browser tools such as `await tools.external_browser_navigate(...)`, `await tools.external_browser_click(...)`, or `await tools.external_browser_evaluate(...)`"
user-invocable: false
---

# External Browser Use Guide

Browser tools that operate the user's **external Chrome browser** via the TRAE Chrome extension. All tools below are aliases of the standard browseruse tools, automatically routed to the external Chrome browser (native mode).

Most browser operations are executed through the Exec tool (V8 sandbox), but some tools **must** be called as standalone toolcalls. See [Tool Calling Mode Reference](#tool-calling-mode-reference) for the complete classification.

---

## Tool Calling Mode Reference

### Tools callable via Exec (`await tools.*`)

These tools **MUST** be called inside Exec using `await tools.<name>(args)`:

| Category | Tools |
|----------|-------|
| Navigation | `external_browser_navigate`, `external_browser_navigate_back`, `external_browser_tabs` |
| Observation | `external_browser_snapshot`, `external_browser_take_screenshot`, `external_browser_get_attribute`, `external_browser_console_messages`, `external_browser_network_requests` |
| Interaction | `external_browser_click`, `external_browser_type`, `external_browser_fill`, `external_browser_fill_form`, `external_browser_hover`, `external_browser_scroll`, `external_browser_press_key`, `external_browser_select_option`, `external_browser_drag`, `external_browser_upload_file`, `external_browser_handle_dialog` |
| Advanced | `external_browser_evaluate`, `external_browser_wait_for` |

### Tools that MUST be called alone (one per turn)

| Tool | Reason |
|------|--------|
| `browser_connect_plugin` | Connectivity check. Must run before any other browser tools in a session. You need its result to decide the next step. |
| `browser_setup_plugin` | Requires user interaction (confirm/skip). You need its result to decide whether to use external or built-in browser. |

> **Rule**: These tools MUST be the **only** tool call in that turn. Do NOT combine them with other tool calls in the same response. These tools do NOT use the `external_` prefix.

---

## CRITICAL - Tool Naming Convention

When operating the user's **external Chrome browser**, you MUST always use the `external_browser_*` prefix for ALL operational browseruse tool calls (e.g., `external_browser_navigate`, `external_browser_click`, `external_browser_snapshot`).

- **DO NOT** use `browser_navigate`, `browser_click`, or any unprefixed `browser_*` form for operational tools — those may target the built-in browser, NOT the user's external Chrome.
- Even if error messages or tool descriptions mention `browser_xxx` without the prefix, you must still use `external_browser_xxx` for operational tools to route the call to the external browser.
- The `external_` prefix is the **sole routing signal** that distinguishes external Chrome operations from built-in browser operations.

---

## CRITICAL - First-time Connection Check

Before using any external browser tools for the first time in a session, you MUST:

1. Call `browser_connect_plugin` to verify the Chrome extension is reachable.
2. If `browser_connect_plugin` returns `connected: false`, immediately call `browser_setup_plugin` to guide the user through setup.
3. Only proceed with browser operations after `browser_connect_plugin` succeeds or `browser_setup_plugin` completes.

If `browser_setup_plugin` returns that the user chose the built-in browser, stop using `external_*` tools and follow the `TRAE-browseruse` skill for standard browser usage.

> **CRITICAL**: `browser_connect_plugin` and `browser_setup_plugin` MUST each be called **alone** in a single turn — do NOT combine them with any other tool calls in the same response. Mixing them with other tools causes judgment issues because the AI cannot properly evaluate the connection/initialization result before deciding the next step.

> **NEVER** call `browser_waiting_for_user_interaction` when `connected: false`. That tool is for handing browser control to the user during an active session — it cannot fix a missing extension. The ONLY correct response to `connected: false` is `browser_setup_plugin`.

---

## CRITICAL - Before interacting with any page

1. Use `external_browser_tabs` with action `"list"` to see open tabs and their URLs.
2. Use `external_browser_snapshot` to get the page structure and element refs before any interaction (click, type, hover, etc.).

## IMPORTANT - Waiting strategy

When waiting for page changes (navigation, content loading, animations, etc.), prefer short incremental waits (1-3 seconds) with `external_browser_snapshot` checks in between rather than a single long wait. For example, instead of waiting 10 seconds, do: wait 2s → snapshot → check if ready → if not, wait 2s more → snapshot again. This allows you to proceed as soon as the page is ready rather than always waiting the maximum time.

## Notes

- If two browser actions need to be performed sequentially, they should not be called in parallel.
- Iframe content is not accessible — only elements outside iframes can be interacted with.
- For nested scroll containers, use `external_browser_scroll` with `scrollIntoView: true` before clicking elements that may be obscured.

---

## Code Execution Tool

You have access to a code execution tool that runs JavaScript in an isolated V8 sandbox.

### CRITICAL: Always prefer Exec when the available tools can accomplish the task.

- ANY tool listed below MUST be called via `await tools.<name>(args)` inside Exec, NOT as a direct tool call.
- Use direct tool calls ONLY for tools that are NOT available inside Exec.
- Even for a single-step task, use Exec if that step involves an available tool.
- For multi-step tasks that share a clear linear flow (e.g., navigate → wait → snapshot → click → type), use a single Exec call.
- **However**, do NOT pack an entire long-running automation (polling loops, multi-minute waits, conditional branching across many pages) into one giant Exec block. Instead, split into multiple Exec calls so the LLM can inspect intermediate results and decide the next action.
- Exec gives you programmatic control: conditionals, error handling, sequential calls — use it for **short, focused sequences** (generally ≤ 20 lines). Do NOT use loops for polling or retrying.

### Call format

```
run_mcp(server_name="integrated_code_mode", tool_name="Exec", args={"code": "<your_js_code>"})
```

- `args` MUST be a JSON object, not a string. The only accepted field is `code`. Using any other field name (e.g., `script`, `command`, `program`) results in "code is empty" error — all such fields are silently ignored.
- `code` is required and must contain non-empty JavaScript.

### Runtime environment

- Pure ECMAScript sandbox. Available globals: standard built-ins (Array, Object, Math, JSON, Promise, RegExp, Date, etc.) plus `tools`, `text`, `exit`.
- Use `text(value)` to output results. Use `await tools.<name>(args)` to invoke other tools.
- Code runs as a top-level script, NOT inside a function. `return` at the top level is a SyntaxError — use `text(value)` to output final results.
- **NOT available**: `require`, `import`, `module`, `exports`, `process`, `Buffer`, `__dirname`, `__filename` (no Node.js/CommonJS), `document`, `window`, `navigator`, `location`, `localStorage` (no browser DOM), `fetch`, `XMLHttpRequest`, `WebSocket` (no network). Using any of these throws `ReferenceError: <name> is not defined`.

### Instructions

- Use `await tools.<tool_name>(args)` to call tools — multiple calls in sequence are encouraged.
- Use `Promise.all([tools.a(x), tools.b(y)])` for concurrent tool calls.
- Use `text(value)` to output results to LLM (value will be stringified via JSON.stringify if not a string).
- Use `exit()` to stop execution early (already-produced text output is preserved).

### Error handling

- Tool call errors cause the Promise to reject — use `try/catch` to handle them gracefully.
- Unhandled exceptions terminate the script and return the error message as the result.
- If the script exceeds the execution time limit, it is forcibly terminated and an error is returned.
- `text()` output produced before an unhandled error is preserved in the response.

### Tool response structure

All browser tools return the same structure:

```typescript
interface BrowserToolResult {
  /** Array of content items */
  content: Array<{ type: "text"; text: string }>;
  /** 0 = success, non-zero = error */
  status: number;
}
```

- Most tools return a single `content` item with `type: "text"` containing the snapshot or result text.
- When `status !== 0`, the `text` field contains the error message.
- Access the text output: `result.content[0].text`

### PTC Output Boundary

Nested tool results are **not automatically visible to the model**.

- `await tools.<name>(...)` returns a JavaScript value inside Exec.
- `JSON.stringify(...)` only converts a value to a string. It does **not** display it.
- Use `text(...)` to expose a result to the model.

```javascript
const snap = await tools.external_browser_snapshot();
text(snap);
```

- If the next action requires **branching logic** (choosing between different paths based on page content), end the current Exec immediately after `text(...)`. The model cannot inspect `text(...)` output while the same Exec is still running.
- However, if the next action is **deterministic** (you already know what to do regardless of snapshot content), you MAY continue in the same Exec without outputting intermediate snapshots.

---

## Available Browser Functions

### Page Navigation

#### `external_browser_navigate` — Navigate to a URL and return a snapshot

```typescript
interface ExternalBrowserNavigateParams {
  /** Target URL (MUST be http:// or https:// — about:, file:, chrome:, javascript: URLs are blocked by security policy*/
  url: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
  /** Whether to open in a new tab */
  newTab?: boolean;
  /** Tab position: "active" (replace current) | "side" (open beside) */
  position?: "active" | "side";
  /** Custom HTTP headers for all requests in this tab (pass empty {} to clear) */
  extraHeaders?: Record<string, string>;
}
```
** Constraints **

`external_browser_navigate` will return ERR_ACCESS_DENIED for any non-http(s) URL. file:// is permanently blocked by security policy.

#### `external_browser_navigate_back` — Go back in browser history, return a snapshot

```typescript
interface ExternalBrowserNavigateBackParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_tabs` — Manage browser tabs (list/new/close/select/activate)

```typescript
interface ExternalBrowserTabsParams {
  /** Action type: "list" | "new" | "close" | "select" | "activate" */
  action: "list" | "new" | "close" | "select" | "activate";
  /** Tab index (required for close/select/activate). NOTE: this is the positional index, NOT tabId */
  index?: number;
}
```

> **`activate` vs `select`**: `select` switches to a tab but does NOT steal user focus. `activate` = select + bring the tab to foreground focus. Some pages only execute certain logic (e.g., timers, animations, event listeners) when they are the focused/active tab. If you notice a page not responding as expected after `select`, try `activate` instead.

### Page Observation (prefer snapshot over screenshot)

#### `external_browser_snapshot` — Get page accessibility snapshot

```typescript
interface ExternalBrowserSnapshotParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
  /** Snapshot strategy: "dom" (DOM mode) | "cdp" (Chrome AX Tree mode, default) */
  strategy?: "dom" | "cdp";
  /** Maximum traversal depth */
  maxDepth?: number;
  /** Maximum number of nodes */
  maxNodes?: number;
  /** Whether to include ignored nodes */
  includeIgnored?: boolean;
  /** Whether to return only interactive elements */
  interactive?: boolean;
  /** Whether to use compact output format */
  compact?: boolean;
  /** CSS selector to snapshot only the matching subtree */
  selector?: string;
}
```

#### `external_browser_take_screenshot` — Take a screenshot (use only when snapshot is insufficient, e.g. canvas, complex CSS, images)

```typescript
interface ExternalBrowserTakeScreenshotParams {
  /** Output filename */
  filename?: string;
  /** Whether to capture the full page (not just the viewport) */
  fullPage?: boolean;
  /** Capture only the element matching this ref */
  ref?: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_get_attribute` — Get an element attribute value

```typescript
interface ExternalBrowserGetAttributeParams {
  /** Element reference ID (from snapshot's [ref=eN]) */
  ref: string;
  /** Attribute name to read (e.g. "href", "src", "class") */
  name: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_console_messages` — Get browser console log messages

```typescript
interface ExternalBrowserConsoleMessagesParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_network_requests` — Get captured network requests

```typescript
interface ExternalBrowserNetworkRequestsParams {
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

### Element Interaction

#### `external_browser_click` — **Preferred click method.** Click an element by ref (supports double-click, mouse buttons, modifiers), returns snapshot
```typescript
interface ExternalBrowserClickParams {
  /** Element reference ID (from snapshot's [ref=eN]) */
  ref: string;
  /** Whether to double-click */
  doubleClick?: boolean;
  /** Mouse button: "left" (default) | "right" | "middle" */
  button?: "left" | "right" | "middle";
  /** Modifier keys, e.g. ["Alt", "Control", "Meta", "Shift"] */
  modifiers?: string[];
  /** Horizontal offset from element's top-left corner in pixels. If omitted, clicks the horizontal center. */
  offsetX?: number;
  /** Vertical offset from element's top-left corner in pixels. If omitted, clicks the vertical center. */
  offsetY?: number;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_type` — Type text into an input element by ref, returns snapshot

```typescript
interface ExternalBrowserTypeParams {
  /** Element reference ID */
  ref: string;
  /** Text to type */
  text: string;
  /** Whether to clear existing content before typing. Use this to replace the current value instead of appending to it. Defaults to false. */
  clear?: boolean;
  /** Whether to press Enter after typing (submit form) */
  submit?: boolean;
  /** Whether to type character-by-character (simulates real typing for per-char event triggers) */
  slowly?: boolean;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_fill` — Clear and fill a value into an input element atomically

Unlike `external_browser_type` which appends text, this clears the existing value first and sets the new value atomically. Use this when you want to replace the entire content of an input field.

```typescript
interface ExternalBrowserFillParams {
  /** Human-readable element description used to obtain permission to interact with the element */
  element: string;
  /** Exact target element reference from the page snapshot */
  ref: string;
  /** Value to fill into the element (replaces any existing content) */
  value: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_fill_form` — Fill multiple form fields at once

Each field uses ref + value. By default, each field is cleared before setting the new value.

```typescript
interface ExternalBrowserFillFormParams {
  /** Array of form fields to fill */
  fields: Array<{
    /** Human-readable element description used to obtain permission to interact with the element */
    element: string;
    /** Exact target element reference from the page snapshot */
    ref: string;
    /** Value to fill into the field */
    value: string;
    /** Whether to clear existing content before filling. Defaults to true. */
    clear?: boolean;
  }>;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
  /** When true, takes a screenshot after the fill completes. Defaults to false. */
  take_screenshot_afterwards?: boolean;
}
```

#### `external_browser_hover` —  Hover over an element (triggers mouseenter/mouseover/mousemove), returns snapshot

```typescript
interface ExternalBrowserHoverParams {
  /** Element reference ID */
  ref: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_scroll` —  Scroll the page or a specific element by direction/amount, returns snapshot

```typescript
interface ExternalBrowserScrollParams {
  /** Element reference to scroll (omit to scroll the page) */
  ref?: string;
  /** Scroll direction: "up" | "down" (default) | "left" | "right" */
  direction?: "up" | "down" | "left" | "right";
  /** Scroll amount in pixels */
  amount?: number;
  /** Horizontal scroll delta */
  deltaX?: number;
  /** Vertical scroll delta */
  deltaY?: number;
  /** Whether to scroll the ref element into the visible area */
  scrollIntoView?: boolean;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_press_key` — Dispatch a keyboard event to the currently focused 

```typescript
interface ExternalBrowserPressKeyParams {
  /** Key name. Common: "Enter", "Tab", "Escape", "Backspace", "ArrowDown", "ArrowUp", "ArrowLeft", "ArrowRight" */
  key: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_select_option` — Select option(s) in a select dropdown by value, returns snapshot

```typescript
interface ExternalBrowserSelectOptionParams {
  /** Select element reference ID */
  ref: string;
  /** Option value(s) to select (supports multi-select) */
  values: string[];
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_drag` — Drag from one element to another element or coordinate
```typescript
interface ExternalBrowserDragParams {
  /** Source element reference ID */
  sourceRef: string;
  /** Target element reference ID (mutually exclusive with targetX/targetY) */
  targetRef?: string;
  /** Target absolute X coordinate */
  targetX?: number;
  /** Target absolute Y coordinate */
  targetY?: number;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_upload_file` — Upload a file to a file input element

```typescript
interface ExternalBrowserUploadFileParams {
  /** File input element reference ID (REQUIRED — from snapshot [ref=eN]) */
  ref: string;
  /** Element selector (alternative locator) */
  element?: string;
  /** File path to upload (REQUIRED — must be a valid local path)  */
  filePath: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

#### `external_browser_handle_dialog` — Handle a browser dialog (alert/confirm/prompt)


```typescript
interface ExternalBrowserHandleDialogParams {
  /** Action: "accept" | "dismiss" */
  action?: "accept" | "dismiss";
  /** Text to enter in a prompt dialog */
  promptText?: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

### Advanced

#### `external_browser_evaluate` — Execute JavaScript in the page context

```typescript
interface ExternalBrowserEvaluateParams {
  /** JavaScript code to execute (use JSON.stringify for structured data extraction) */
  script: string;
  /** Target browser tab ID. If omitted, uses the last interacted tab. NOTE: field name is "script", NOT "expression" or "code" */
  viewId?: string;
}
```

** Constraints **

- The `script` parameter is the ONLY field for code. Any other field name will fail with "missing field `script`". `script` must be a string. Passing an object (e.g., `{ script: {...} }`) causes "[object Object]" parse errors.
- NEVER wrap script in IIFE (`(function(){})()` or `(async()=>{})()`). The engine auto-wraps — hand-written IIFE causes double-wrapping and returns `undefined`.
- Guard all DOM access with `?.` or explicit null checks — elements may not exist.
- Do NOT call `fetch()` or `XMLHttpRequest` inside script — use `browser_navigate` for API URLs.
- Do NOT `JSON.stringify` DOM elements directly — extract needed primitive values first.
- Do NOT serialize `document.body.innerHTML` or large subtrees — causes 30s timeout.
- Use standard CSS selectors and guard optional elements with `?.` or `??`.
- Use `JSON.stringify(...)` for structured data (on plain objects only, never on DOM nodes).
- Read-Only Only: All page mutations (click, type, submit, navigate) must use native browser tools. Keep `external_browser_evaluate` for data extraction only.

#### `external_browser_wait_for` — Wait for a condition (time/text appear/text disappear/selector appear)

```typescript
interface ExternalBrowserWaitForParams {
  /** Seconds (not ms) to sleep. Range: 1–60. For longer waits, use a loop. */
  time?: number;
  /** Wait for this text to appear on the page */
  text?: string;
  /** Wait for this text to disappear from the page */
  textGone?: string;
  /** Wait for a CSS selector to match an element */
  selector?: string;
  /** Element state: "visible" | "hidden" | "attached" | "detached" */
  state?: string;
  /** Maximum timeout in milliseconds */
  timeout?: number;
  /** Target browser tab ID. If omitted, uses the last interacted tab. */
  viewId?: string;
}
```

Usage patterns:
- Sleep 3 seconds: `{ time: 3 }`
- Wait for text: `{ text: "Loading complete", timeout: 30 }`
- Wait for element: `{ selector: ".content", timeout: 10 }`

---

## Workflow Best Practices

### Exec Batching & Interaction Patterns

#### Rule — Maximize Actions Per Exec

Never issue back-to-back single-tool Exec calls if the workflow can be combined into a single Exec block. **Pack 3–8 predictable sequential browser operations into ONE Exec call.**

- **Target density**: 3–5 tools per Exec = good; 5–8 = optimal for form-filling; 8+ = split for readability.
- **Split point**: End the Exec ONLY when you need to **branch** (choose a different path based on page content). Pure verification (read-only evaluate) does NOT require splitting.
- **Key insight**: If you already know what actions to perform next (e.g., fill 3 more fields, then click submit), do them all in one Exec — don't stop to observe between each one.

#### Ref Invalidation Risk Levels

Not all operations invalidate refs equally. Use this guide to decide when re-snapshot is needed:

| Risk Level | Operations | Refs still valid? | Action |
|------------|-----------|-------------------|--------|
| **HIGH** — must re-snapshot | `external_browser_navigate`, `external_browser_click` that triggers page navigation, `external_browser_evaluate` that modifies DOM | ❌ All refs invalidated | End Exec with `text(snap)` |
| **MEDIUM** — re-snapshot recommended | `external_browser_click` on buttons/links (may trigger AJAX), `external_browser_select_option` on dynamic forms | ⚠️ May partially invalidate | Re-snapshot if next action targets a different page region |
| **LOW** — safe to continue | `external_browser_type`, `external_browser_fill`, `external_browser_fill_form`, `external_browser_press_key` (Tab/Enter on same form), `external_browser_select_option` on static forms, `external_browser_scroll` | ✅ Refs remain valid | Continue using same refs without re-snapshot |

**Critical change from prior guidance**: `type → type → type` on adjacent form fields is SAFE (95%+ success rate). You do NOT need to snapshot between each type operation on the same form. The same applies to `external_browser_fill` and `external_browser_fill_form` — they are atomic per-field operations that do not invalidate refs.

#### Proven Patterns (use as default templates)

```javascript
// Pattern A: click → wait → snapshot (98.6% success, N=423)
// Use when click triggers page change or async loading
await tools.external_browser_click({ ref: "e42" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern B: click → snapshot (100% success, N=107)
// Use when target page is fast / no async loading
await tools.external_browser_click({ ref: "e42" });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern C: navigate → wait → snapshot (100% success, N=40)
await tools.external_browser_navigate({ url: "https://example.com" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern D: Form Fill — multiple fields in one Exec (96% success, N=180)
// Use when filling 2+ fields on the same form
await tools.external_browser_click({ ref: "e10" });
await tools.external_browser_type({ ref: "e10", text: "John Doe", clear: true });
await tools.external_browser_type({ ref: "e12", text: "john@example.com", clear: true });
await tools.external_browser_type({ ref: "e14", text: "Hello world", clear: true });
await tools.external_browser_click({ ref: "e20" }); // submit button
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern D2: Form Fill via external_browser_fill_form — PREFERRED for multi-field forms (atomic, single call)
// Fills all fields in one operation, each field is cleared by default
await tools.external_browser_fill_form({
  fields: [
    { element: "Name input", ref: "e10", value: "John Doe" },
    { element: "Email input", ref: "e12", value: "john@example.com" },
    { element: "Message textarea", ref: "e14", value: "Hello world" }
  ]
});
await tools.external_browser_click({ ref: "e20" }); // submit button
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern D3: Single field fill via external_browser_fill — atomic clear + set
// Use when replacing a single input's value (simpler than external_browser_type with clear: true)
await tools.external_browser_fill({ element: "Search box", ref: "e5", value: "new search query" });
await tools.external_browser_press_key({ key: "Enter" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern E: scroll → wait → snapshot (100% success, N=96)
await tools.external_browser_scroll({ ref: "e10", direction: "down", amount: 300 });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

```javascript
// Pattern F: Batch Verify — extract multiple values in one evaluate (99% success)
// Use when checking 2+ data points on the same page
const data = await tools.external_browser_evaluate({
  script: `JSON.stringify({
    title: document.querySelector('h1')?.textContent?.trim() ?? '',
    status: document.querySelector('.status')?.textContent?.trim() ?? '',
    count: document.querySelector('.count')?.textContent?.trim() ?? '',
    items: Array.from(document.querySelectorAll('.item')).map(el => el.textContent.trim()).slice(0, 10)
  })`
});
text(data);
```

#### Anti-Patterns (NEVER use)

| Pattern | Success | Root Cause |
|---------|---------|------------|
| `click → wait → click` (no re-snapshot) | 0% | Refs stale after first click |
| `navigate → navigate → snapshot` | 20% | Race condition between navigations |

**Multi-click recovery** — re-snapshot only when the page actually changes:
```javascript
// ✅ Correct: refresh refs after page-changing click
await tools.external_browser_click({ ref: "e5" }); // this triggers navigation
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

### Snapshot Strategy — When to Observe

**Snapshot is needed when:**
1. You've never seen the page before (first interaction)
2. After navigation or page-changing click (HIGH risk operations)
3. When you need to discover unknown element refs
4. After an action whose outcome is uncertain

**Snapshot can be SKIPPED when:**
1. You're typing into form fields whose refs you already have
2. You're using `external_browser_fill` or `external_browser_fill_form` on known refs
3. You're pressing Tab/Enter to move between known fields
4. You're selecting options in a static dropdown
5. You're scrolling to bring a known element into view
6. The previous action was LOW risk (see Ref Invalidation table)

**Key principle**: Don't snapshot to "verify" actions whose outcomes are deterministic. If you typed "hello" into a text field, it now contains "hello" — you don't need a snapshot to confirm this.

### Cost Hierarchy (prefer top)

| Method | Cost | Use for |
|--------|------|---------|
| `external_browser_snapshot()` | Very low | Page understanding, finding elements |
| `external_browser_click`/`external_browser_type`/`external_browser_fill`/`external_browser_fill_form`/`external_browser_press_key` | Low | Interaction |
| `external_browser_evaluate()` | Low | Data extraction, DOM queries |
| `external_browser_take_screenshot()` | High | Visual-only info, canvas, layouts |

### Form Fill Pattern (HIGH PRIORITY)

When filling multiple form fields, use `external_browser_fill_form` for the most efficient approach — it fills all fields atomically in a single call. Alternatively, batch individual `external_browser_type` or `external_browser_fill` operations into a single Exec. Do NOT snapshot between each field.

### Text Input Pattern
```javascript
// ✅ BEST: Use external_browser_fill_form for multi-field forms (single atomic call)
const snap = await tools.external_browser_snapshot();
text(snap);
```

After reading refs from the snapshot, fill all fields in one Exec:

```javascript
// Option 1: external_browser_fill_form (preferred — one call fills everything)
await tools.external_browser_fill_form({
  fields: [
    { element: "Email field", ref: "e3", value: "user@example.com" },
    { element: "Password field", ref: "e5", value: "password123" },
    { element: "Full name field", ref: "e7", value: "John Doe" }
  ]
});
await tools.external_browser_select_option({ ref: "e9", values: ["admin"] });
await tools.external_browser_click({ ref: "e15" }); // submit
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_snapshot();
text(result);
```

```javascript
// Option 2: Sequential external_browser_fill calls (when you need per-field control)
await tools.external_browser_fill({ element: "Email field", ref: "e3", value: "user@example.com" });
await tools.external_browser_fill({ element: "Password field", ref: "e5", value: "password123" });
await tools.external_browser_fill({ element: "Full name field", ref: "e7", value: "John Doe" });
await tools.external_browser_select_option({ ref: "e9", values: ["admin"] });
await tools.external_browser_click({ ref: "e15" }); // submit
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_snapshot();
text(result);
```

```javascript
// Option 3: external_browser_type with clear (legacy approach, still valid)
await tools.external_browser_click({ ref: "e3" });
await tools.external_browser_type({ ref: "e3", text: "user@example.com", clear: true });
await tools.external_browser_press_key({ key: "Tab" });
await tools.external_browser_type({ ref: "e5", text: "password123", clear: true });
await tools.external_browser_press_key({ key: "Tab" });
await tools.external_browser_type({ ref: "e7", text: "John Doe", clear: true });
await tools.external_browser_select_option({ ref: "e9", values: ["admin"] });
await tools.external_browser_click({ ref: "e15" }); // submit
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_snapshot();
text(result);
```

**Why `external_browser_fill_form` is preferred**: It reduces tool calls from N (one per field) to 1, eliminates the need for intermediate Tab/click focus management, and atomically clears + sets each field. This directly addresses the P5 form fragmentation bottleneck.

**Why this works**: `fill`, `fill_form`, `type`, `press_key(Tab)`, and `select_option` on static forms do NOT invalidate other refs on the page. The form fields remain in the same positions.

**When to break this pattern**: Only if a field triggers dynamic page changes (e.g., selecting a country reloads the city dropdown). In that case, split after the triggering action.

### Batch Verification Pattern (HIGH PRIORITY)

When you need to verify multiple data points on a page, use a SINGLE evaluate call that extracts all values at once. Do NOT use multiple separate evaluate calls.

```javascript
// ❌ BAD: 5 separate evaluates (5 rounds)
const v1 = await tools.external_browser_evaluate({ script: `document.querySelector('#name').textContent` });
text(v1);
// ... next turn ...
const v2 = await tools.external_browser_evaluate({ script: `document.querySelector('#email').textContent` });
text(v2);
// ... 3 more turns ...

// ✅ GOOD: 1 evaluate extracts everything (1 round)
const allData = await tools.external_browser_evaluate({
  script: `JSON.stringify({
    name: document.querySelector('#name')?.textContent?.trim() ?? '',
    email: document.querySelector('#email')?.textContent?.trim() ?? '',
    phone: document.querySelector('#phone')?.textContent?.trim() ?? '',
    status: document.querySelector('#status')?.textContent?.trim() ?? '',
    result: document.querySelector('#result')?.textContent?.trim() ?? ''
  })`
});
text(allData);
```

**Rule**: If you need to check N values on the same page, always use 1 evaluate with `JSON.stringify({...})` to extract all N values in a single call.

### Combined Action + Verify Pattern

You can combine interaction and verification in a single Exec when the verification is read-only:

```javascript
// Fill form AND verify result in 1 Exec (no intermediate snapshot needed)
await tools.external_browser_fill_form({
  fields: [
    { element: "Input field", ref: "e3", value: "test input" }
  ]
});
await tools.external_browser_click({ ref: "e10" }); // submit
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_evaluate({
  script: `JSON.stringify({
    success: !!document.querySelector('.success-msg'),
    output: document.querySelector('.output')?.textContent?.trim() ?? ''
  })`
});
text(result);
```
### Image Input Pattern
If you have to use the `external_browser_take_screenshot` tool, it is recommended to invoke the automatic image‑reading function image() after calling `external_browser_take_screenshot`. 
Bear in mind that image() exclusively accepts the raw tool‑response object carrying the __images property; string inputs are unsupported：

```javascript
const shot = await tools.external_browser_take_screenshot({}); 
image(shot);
```

### Debugging White/Blank Pages
If a page appears blank (white screen) after navigation, use `tools.external_browser_console_messages()` to check for JavaScript errors or failed resource loads that explain why the page didn't render.

### After Navigation
Always wait after navigating before interacting:
```javascript
await tools.external_browser_navigate({ url: "https://example.com" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

### Multi-Step Orchestration
```javascript
await tools.external_browser_navigate({ url: "https://example.com" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

After reading the snapshot output, continue in the next Exec:

```javascript
await tools.external_browser_click({ ref: "e3" });
await tools.external_browser_type({ ref: "e3", text: "search query", submit: true });
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_snapshot();
text(result);
```

### Tab Activation Pattern
When a page requires foreground focus to function properly (e.g., timers, animations, event listeners), use `activate` instead of `select`:
```javascript
// 1. List all tabs to find the target
const tabs = await tools.external_browser_tabs({ action: "list" });
// tabs output example:
//   [0] https://example.com/dashboard
//   [1] https://example.com/settings  <-- we want this one

// 2. Activate by index (positional index from the list, NOT tabId)
await tools.external_browser_tabs({ action: "activate", index: 1 });

// 3. Snapshot to verify and get fresh refs
const snap = await tools.external_browser_snapshot();
text(snap);
```

### Data Extraction with external_browser_evaluate()
```javascript
// Get all links
const links = await tools.external_browser_evaluate({
  script: `JSON.stringify(Array.from(document.querySelectorAll('a[href]')).map(a => ({text: a.textContent.trim(), href: a.href})).filter(a => a.text).slice(0, 20))`
});
text(links);

// Get form values
const formData = await tools.external_browser_evaluate({
  script: `JSON.stringify({ email: document.querySelector('#email')?.value, name: document.querySelector('#name')?.value })`
});
text(formData);
```

### Multi-Step Orchestration
```javascript
await tools.external_browser_navigate({ url: "https://example.com" });
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

After reading the snapshot output, continue in the next Exec:

```javascript
// Fill search and get results — all in one Exec
await tools.external_browser_fill({ element: "Search input", ref: "e3", value: "search query" });
await tools.external_browser_press_key({ key: "Enter" });
await tools.external_browser_wait_for({ time: 2 });
const result = await tools.external_browser_snapshot();
text(result);
```

---

## Ref Lifecycle & Invalidation

Element refs (`[ref=eN]`) are temporary identifiers generated at snapshot time. They become invalid after DOM changes that affect the relevant page region.

### Invalidation Rules (Tiered)

| Tier | Triggering Operation | Effect on Refs | Required Action |
|------|---------------------|----------------|-----------------|
| **Full invalidation** | `external_browser_navigate`, `external_browser_navigate_back`, page-changing `external_browser_click` | ALL refs invalid | Must re-snapshot |
| **Partial invalidation** | `external_browser_click` (AJAX-triggering), `external_browser_evaluate` (DOM-modifying) | Refs in affected region invalid | Re-snapshot if next target is in the changed region |
| **No invalidation** | `external_browser_type`, `external_browser_fill`, `external_browser_fill_form`, `external_browser_press_key`, `external_browser_select_option` (static), `external_browser_scroll`, `external_browser_hover` | All refs remain valid | Continue using existing refs |

### Key Principle

**Ask: "Does this operation change the page structure?"**
- YES (navigation, submit, AJAX button) → re-snapshot before next action
- NO (typing, filling, selecting, scrolling, tabbing) → continue with existing refs

### Recommended Patterns

**Compact mode (preferred)** — use a ref selected from the latest model-visible snapshot. No DOM mutation may have occurred since that snapshot:
```javascript
// This ref was selected from the snapshot output of the previous Exec.
await tools.external_browser_click({ ref: "<ref-from-latest-snapshot>" });
const result = await tools.external_browser_snapshot();
text(result);
```

**Form-fill mode** — use `external_browser_fill_form` for maximum efficiency:
```javascript
// All refs from the same snapshot — safe because fill_form doesn't invalidate
await tools.external_browser_fill_form({
  fields: [
    { element: "Field 1", ref: "e10", value: "value1" },
    { element: "Field 2", ref: "e12", value: "value2" },
    { element: "Field 3", ref: "e16", value: "value3" }
  ]
});
await tools.external_browser_select_option({ ref: "e14", values: ["opt1"] });
await tools.external_browser_click({ ref: "e20" }); // submit — this IS invalidating
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

**Form-fill mode (alternative)** — chain multiple LOW-risk operations without intermediate snapshots:
```javascript
// All refs from the same snapshot — safe because type/select/fill don't invalidate
await tools.external_browser_fill({ element: "Field 1", ref: "e10", value: "value1" });
await tools.external_browser_fill({ element: "Field 2", ref: "e12", value: "value2" });
await tools.external_browser_select_option({ ref: "e14", values: ["opt1"] });
await tools.external_browser_fill({ element: "Field 3", ref: "e16", value: "value3" });
await tools.external_browser_click({ ref: "e20" }); // submit — this IS invalidating
await tools.external_browser_wait_for({ time: 2 });
const snap = await tools.external_browser_snapshot();
text(snap);
```

**Wait-and-refresh pattern**:
```javascript
await tools.external_browser_wait_for({ text: "Loading complete" });
const snap = await tools.external_browser_snapshot();
text(snap);
```

If refs become stale, re-snapshot and retry with native external browser tools. Do not use `external_browser_evaluate` to mutate the page.
---

## Error Handling
- If a tool call fails, snapshot the page to understand current state before retrying.
- If an element ref is not found, the element may have been removed from DOM — re-snapshot to get fresh refs (see [Ref Lifecycle & Invalidation](#ref-lifecycle--invalidation)).
- After navigation that takes long, use `external_browser_wait_for({ selector })` to confirm page readiness instead of a fixed delay.
- If snapshot returns very few elements, the page may still be loading — wait and retry.

---

## Safety Rules
- Never submit forms with sensitive data without user approval.
- Never bypass security prompts (CAPTCHAs, "site not secure" warnings).
- Never delete or modify user data without explicit approval.

