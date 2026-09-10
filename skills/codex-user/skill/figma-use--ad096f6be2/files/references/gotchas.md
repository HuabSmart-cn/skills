# Gotchas & Common Mistakes

> Part of the [use_figma skill](../SKILL.md). Every known pitfall with WRONG/CORRECT code examples.

## Contents

- Component properties and variant creation pitfalls
- Paint, color, and variable binding pitfalls
- Page context and plugin lifecycle pitfalls (set current page once per `use_figma` call; split multi-page work across calls)
- Auto Layout and sizing order pitfalls (including HUG/FILL interactions, and TEXT nodes that ignore FILL and collapse to a zero-width thread)
- Variant layout and geometry pitfalls
- Canonical text-edit recipe + font loading and text/typography pitfalls
- Sequential awaits — batch independent async calls with `Promise.all` (including `import*ByKeyAsync` families)
- Prefer indexed lookups (`getNodeByIdAsync`, `findAllWithCriteria`, `node.query`) over `findAll`/`findOne` full-tree scans
- Scope traversal to the smallest known ancestor (never `figma.root.findAll`; prefer `someFrame.findAllWithCriteria` over `figma.currentPage.findAllWithCriteria`)
- Variable scopes and mode pitfalls
- Node cleanup and empty-fill pitfalls
- "no such property" errors — reading or calling members not defined on the node type
- Non-existent property writes and "object is not extensible"
- width/height are read-only — use resize()
- detachInstance() and node ID invalidation
- Icons — import the SVG, never reconstruct from rotated line primitives


## New nodes default to (0,0) and overlap existing content

Every `figma.create*()` call places the node at position (0,0). If you append multiple nodes directly to the page, they all stack on top of each other and on top of any existing content.

**This only matters for nodes appended directly to the page** (i.e., top-level nodes). Nodes appended as children of other frames, components, or auto-layout containers are positioned by their parent — don't scan for overlaps when nesting nodes.

```js
// WRONG — top-level node lands at (0,0), overlapping existing page content
const frame = figma.createFrame()
frame.name = "My New Frame"
frame.resize(400, 300)
figma.currentPage.appendChild(frame)

// CORRECT — find existing content bounds and place the new top-level node to the right
const page = figma.currentPage
let maxX = 0
for (const child of page.children) {
  const right = child.x + child.width
  if (right > maxX) maxX = right
}
const frame = figma.createFrame()
frame.name = "My New Frame"
frame.resize(400, 300)
figma.currentPage.appendChild(frame)
frame.x = maxX + 100  // 100px gap from rightmost existing content
frame.y = 0

// NOT NEEDED — child nodes inside a parent don't need overlap scanning
const card = figma.createAutoLayout('VERTICAL')
const label = figma.createText()
card.appendChild(label)  // positioned by auto-layout, no x/y needed
```

## `addComponentProperty` returns a string key, not an object — never hardcode or guess it

Figma generates the property key dynamically (e.g. `"label#4:0"`). The suffix is unpredictable. Always capture and use the return value directly.

```js
// WRONG — guessing / hardcoding the key
comp.addComponentProperty('label', 'TEXT', 'Button')
labelNode.componentPropertyReferences = { characters: 'label#0:1' }  // Error: key not found

// WRONG — treating the return value as an object
const result = comp.addComponentProperty('Label', 'TEXT', 'Button')
const propKey = Object.keys(result)[0]  // BUG: returns '0' (first char index of string!)
labelNode.componentPropertyReferences = { characters: propKey }  // Error: property '0' not found

// CORRECT — the return value IS the key string, use it directly
const propKey = comp.addComponentProperty('Label', 'TEXT', 'Button')
// propKey === "label#4:0" (exact value varies; never assume it)
labelNode.componentPropertyReferences = { characters: propKey }
```

The same applies to `COMPONENT_SET` nodes — `addComponentProperty` always returns the property key as a string.

## MUST return ALL created/mutated node IDs

Every script that creates or mutates nodes on the canvas must track and return all affected node IDs in the return value. Without these IDs, subsequent calls cannot reference, validate, or clean up those nodes.

```js
// WRONG — only returns the parent frame ID, loses track of children
const frame = figma.createFrame()
const rect = figma.createRectangle()
const text = figma.createText()
frame.appendChild(rect)
frame.appendChild(text)
return { nodeId: frame.id }

// CORRECT — returns all created node IDs in a structured response
const frame = figma.createFrame()
const rect = figma.createRectangle()
const text = figma.createText()
frame.appendChild(rect)
frame.appendChild(text)
return {
  createdNodeIds: [frame.id, rect.id, text.id],
  rootNodeId: frame.id
}

// CORRECT — when mutating existing nodes, return those IDs too
const nodes = figma.currentPage.findAll(n => n.name === 'Card')
for (const n of nodes) {
  n.fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
}
return {
  mutatedNodeIds: nodes.map(n => n.id),
  count: nodes.length
}
```

## Colors are 0–1 range

```js
// WRONG — will throw validation error (ZeroToOne enforced)
node.fills = [{ type: 'SOLID', color: { r: 255, g: 0, b: 0 } }]

// CORRECT
node.fills = [{ type: 'SOLID', color: { r: 1, g: 0, b: 0 } }]
```

## Fills/strokes are immutable arrays

```js
// WRONG — modifying in place does nothing
node.fills[0].color = { r: 1, g: 0, b: 0 }

// CORRECT — clone, modify, reassign
const fills = JSON.parse(JSON.stringify(node.fills))
fills[0].color = { r: 1, g: 0, b: 0 }
node.fills = fills
```

## setBoundVariableForPaint returns a NEW paint

```js
// WRONG — ignoring return value
figma.variables.setBoundVariableForPaint(paint, "color", colorVar)
node.fills = [paint]  // paint is unchanged!

// CORRECT — capture the returned new paint
const boundPaint = figma.variables.setBoundVariableForPaint(paint, "color", colorVar)
node.fills = [boundPaint]
```

## Variable collection starts with 1 mode

```js
// A new collection already has one mode — rename it, don't try to add first
const collection = figma.variables.createVariableCollection("Colors")
// collection.modes = [{ modeId: "...", name: "Mode 1" }]
collection.renameMode(collection.modes[0].modeId, "Light")
const darkModeId = collection.addMode("Dark")
```

## combineAsVariants requires ComponentNodes

```js
// WRONG — passing frames
const f1 = figma.createFrame()
figma.combineAsVariants([f1], figma.currentPage) // Error!

// CORRECT — passing components
const c1 = figma.createComponent()
c1.name = "variant=primary, size=md"
const c2 = figma.createComponent()
c2.name = "variant=secondary, size=md"
figma.combineAsVariants([c1, c2], figma.currentPage)
```

## Page switching: sync setter does NOT work

The sync setter `figma.currentPage = page` does **NOT work** in `use_figma` — it throws `"Setting figma.currentPage is not supported"`. You **must** use `await figma.setCurrentPageAsync(page)` instead, which switches the page and loads its content.

Note: **reading** `figma.currentPage` is fine — it's only the **assignment** (`figma.currentPage = ...`) that throws.

```js
// WRONG — throws "Setting figma.currentPage is not supported"
figma.currentPage = targetPage

// CORRECT — async method switches and loads content
await figma.setCurrentPageAsync(targetPage)

// ALSO CORRECT — reading currentPage is fine
const page = figma.currentPage  // works
```

## Set current page once per `use_figma` call — split multi-page work into parallel calls

**A `use_figma` script must call `setCurrentPageAsync` at most once.** Never loop over `figma.root.children` and switch pages inside one script.

**The rule is the same for reads and writes:** if work spans multiple pages, split it into **multiple `use_figma` tool calls, one per target page, and YOU MUST issue them in parallel**.

> **Explicit instruction to the agent:** emit all N `use_figma` calls in a **single assistant message**, as N parallel tool-use blocks. Do not send them in separate turns. Do not await one before issuing the next. Each call sets `currentPage` exactly once; the harness runs them concurrently. Sequential per-page calls defeat the entire point of splitting and are slower than the in-loop pattern this rule replaces.

```js
// WRONG — one script switches pages on every iteration; reloads the file N times sequentially
const componentsByPage = {}
for (const page of figma.root.children) {
  await figma.setCurrentPageAsync(page)
  componentsByPage[page.name] = page.findAllWithCriteria({ types: ['COMPONENT'] }).map(n => n.id)
}
return componentsByPage
```

Instead, do it in two steps and parallelize step 2:

```js
// CORRECT — step 1: cheap, no page switch. Return the page IDs you'll fan out over.
return figma.root.children.map(p => ({ id: p.id, name: p.name }))
```

Then in the **next assistant turn**, emit **N parallel `use_figma` tool-use blocks in one message** — one per page. Each script runs this:

```js
// CORRECT — step 2: one call per page, currentPage set exactly once.
// The assistant issues N of these in parallel — do NOT loop pages inside the script.
const page = await figma.getNodeByIdAsync(PAGE_ID)  // PAGE_ID supplied by caller
await figma.setCurrentPageAsync(page)
// ... read or mutate this page ...
return { pageId: page.id, components: page.findAllWithCriteria({ types: ['COMPONENT'] }).map(n => n.id) }
```

This applies to discovery, mutation, component-set creation, and audits — reads and writes alike. **The only acceptable reason to switch pages multiple times in one script is when splitting would break a transactional/atomicity guarantee** (i.e., the operation must succeed across all pages or none, and a partial failure between calls would corrupt state). "It's read-only" and "I want a consistent snapshot" are *not* exceptions — fan out in parallel.

The same rule generalizes to *any* traversal: scope it to the smallest known ancestor — see [Scope traversal to the smallest known ancestor](#scope-traversal-to-the-smallest-known-ancestor).

## `get_metadata` operates on one subtree — discover pages explicitly

A Figma file can have multiple pages (canvas nodes). `get_metadata` only returns the subtree of whichever node you pass it. To get a usable index of every page:

- Call `get_metadata` with **no nodeId** — it returns the document's top-level pages as `{guid, name}` entries (no XML dump). This is the cheapest way to discover pages.
- For more detail per page (e.g. child counts, top-level node types), fall back to `use_figma`:

```js
const pages = figma.root.children.map(p => `${p.name} id=${p.id} children=${p.children.length}`);
return pages.join('\n');
```

Icons, variables, and components may live on pages other than the first. Always enumerate all pages before concluding that the file has no existing assets.

## Never use figma.notify()

```js
// WRONG — throws "not implemented" error
figma.notify("Done!")

// CORRECT — return a value to send data back to the agent
return "Done!"
```

## `getPluginData()` / `setPluginData()` are not supported

These APIs are not available in `use_figma`. Use `getSharedPluginData()` / `setSharedPluginData()` instead (these ARE supported), or track nodes by returning IDs.

```js
// WRONG — not supported in use_figma
node.setPluginData('my_key', 'my_value')
const val = node.getPluginData('my_key')

// CORRECT — use shared plugin data (requires a namespace)
node.setSharedPluginData('my_namespace', 'my_key', 'my_value')
const val = node.getSharedPluginData('my_namespace', 'my_key')

// ALSO CORRECT — return node IDs and track them across calls
const rect = figma.createRectangle()
return { nodeId: rect.id }
// Then pass nodeId as a string literal in the next use_figma call
```

## Script must always return a value

```js
// WRONG — no return, caller gets no useful response
figma.createRectangle()

// CORRECT — return a result (objects are auto-serialized, errors are auto-captured)
const rect = figma.createRectangle()
return { nodeId: rect.id }
```

## setBoundVariable for paint fields only works on SOLID paints

```js
// Only SOLID paint type supports color variable binding
// Gradient paints, image paints, etc. will throw
const solidPaint = { type: 'SOLID', color: { r: 0, g: 0, b: 0 } }
const bound = figma.variables.setBoundVariableForPaint(solidPaint, "color", colorVar)
```

## Explicit variable modes must be set per component

```js
// WRONG — all variants render with the default (first) mode
const colorCollection = figma.variables.createVariableCollection("Colors")
// ... create variables and modes ...
// Components all show the first mode's values by default!

// CORRECT — set explicit mode on each component to get variant-specific values
component.setExplicitVariableModeForCollection(colorCollection, targetModeId)
```

## `lineHeight` and `letterSpacing` must be objects, not bare numbers

```js
// WRONG — throws or silently does nothing
style.lineHeight = 1.5
style.lineHeight = 24
style.letterSpacing = 0

// CORRECT
style.lineHeight = { unit: "AUTO" }                    // auto/intrinsic
style.lineHeight = { value: 24, unit: "PIXELS" }       // fixed pixel height
style.lineHeight = { value: 150, unit: "PERCENT" }     // percentage of font size

style.letterSpacing = { value: 0, unit: "PIXELS" }     // no tracking
style.letterSpacing = { value: -0.5, unit: "PIXELS" }  // tight
style.letterSpacing = { value: 5, unit: "PERCENT" }    // percent-based
```

This applies to both `TextStyle` and `TextNode` properties. The same rule applies inside `use_figma`, interactive plugins, and any other plugin API context.

## Canonical text-edit recipe (font load → await → mutate → return IDs)

Writing to any text property on a node whose font is not yet loaded throws `Cannot write to node with unloaded font "<family> <style>"`. The fix is always the same four-step recipe — use it verbatim every time you touch text:

```js
// WRONG — font not loaded; throws Cannot write to node with unloaded font "Inter Regular"
const node = figma.createText()
node.characters = "Hello"

// CORRECT — load font, await, mutate, return affected IDs
await figma.loadFontAsync({ family: "Inter", style: "Regular" })  // any font, not just Inter — see note
const node = figma.createText()
node.characters = "Hello"
return { createdNodeIds: [node.id] }
```

**This applies to every font, not just Inter.** Inter is preloaded in most environments so the missing-`loadFontAsync` bug often only surfaces with other families (`Roboto Mono`, `Merriweather`, `Figma Hand`, library fonts, etc.). Examples in these docs use `Inter` because it's available everywhere, but the recipe is identical for any family/style pair.

**The same recipe also applies when mutating existing text** — the font already on the node, not a hardcoded default, must be loaded:

```js
// CORRECT — load the node's own current font(s), then mutate
const segments = textNode.getStyledTextSegments(['fontName'])
await Promise.all(segments.map(s => figma.loadFontAsync(s.fontName)))
textNode.characters = "Updated"
return { mutatedNodeIds: [textNode.id] }
```

Font loading is also required for **any** operation on nodes that contain unloaded fonts — `appendChild`, `insertChild`, `setBoundVariable`, `setExplicitVariableModeForCollection`, `setValueForMode`, and even `findAll` callbacks that touch text properties. If the document has existing text nodes you'll traverse, preload their fonts at the start of the script.

## Sequential awaits — batch independent async calls with `Promise.all`

Awaiting an independent async call inside a `for`/`for…of` loop — or sequentially in a straight-line block — serializes one IPC round-trip per call. Each call to `getNodeByIdAsync`, `getVariableByIdAsync`, `loadFontAsync`, `setTextStyleIdAsync`, **`importComponentByKeyAsync`, `importComponentSetByKeyAsync`, `importStyleByKeyAsync`, `importVariableByKeyAsync`**, etc. is independent — batch them with `Promise.all`. The only awaits that *must* stay sequential are `setCurrentPageAsync` (changes global page context) and explicit per-iteration dependencies.

Sequential `import*ByKeyAsync` calls at the top of a `use_figma` script are a particularly common offender — design-system scripts often import a component set plus several variables plus an effect style in a row. **Always batch the imports:**

```js
// WRONG — four sequential round-trips at the start of every section build
const buttonSet   = await figma.importComponentSetByKeyAsync("BUTTON_SET_KEY")
const bgVar       = await figma.variables.importVariableByKeyAsync("BG_COLOR_VAR_KEY")
const spacingVar  = await figma.variables.importVariableByKeyAsync("SPACING_VAR_KEY")
const shadowStyle = await figma.importStyleByKeyAsync("SHADOW_STYLE_KEY")

// CORRECT — one round-trip
const [buttonSet, bgVar, spacingVar, shadowStyle] = await Promise.all([
  figma.importComponentSetByKeyAsync("BUTTON_SET_KEY"),
  figma.variables.importVariableByKeyAsync("BG_COLOR_VAR_KEY"),
  figma.variables.importVariableByKeyAsync("SPACING_VAR_KEY"),
  figma.importStyleByKeyAsync("SHADOW_STYLE_KEY"),
])
```

```js
// WRONG — N sequential round-trips, scales linearly with list length
const vars = {}
for (const id of collection.variableIds) {
  vars[id] = await figma.variables.getVariableByIdAsync(id)
}

// CORRECT — one round-trip
const fetched = await Promise.all(
  collection.variableIds.map(id => figma.variables.getVariableByIdAsync(id))
)
const vars = {}
collection.variableIds.forEach((id, i) => { vars[id] = fetched[i] })
```

When the loop only needs the *same* font for every iteration, load it once before the loop instead of inside it. (For freshly-created `TextNode`s this is the platform default — typically Inter Regular in design files; for FigJam sticky/shape sublayers it's Inter Medium. Either way, read `node.fontName` rather than hardcoding.)

```js
// WRONG — loads the same default font on every iteration
for (const label of labels) {
  const t = figma.createText()
  await figma.loadFontAsync(t.fontName)
  t.characters = label
}

// CORRECT — load once, then mutate synchronously
const probe = figma.createText()
await figma.loadFontAsync(probe.fontName)
probe.remove()
for (const label of labels) {
  const t = figma.createText()
  t.characters = label
}
```

If you do need different fonts per node, dedupe and `Promise.all` them up-front:

```js
const uniqueFonts = [...new Map(
  textNodes.map(t => [JSON.stringify(t.fontName), t.fontName])
).values()]
await Promise.all(uniqueFonts.map(f => figma.loadFontAsync(f)))
```

## Prefer indexed lookups over `findAll` / `findOne` full-tree scans

**Rule: use `findAllWithCriteria({ types: [...] })` for type-based searches. Reserve `findOne` / `findAll(predicate)` for cases the criteria API can't express** — name patterns, regex, capability checks (`'fills' in n`), or any predicate that touches properties the engine doesn't index.

`findAll` and `findOne` walk the entire subtree node-by-node and run a JS predicate on each one. For anything the Figma engine already indexes (type, pluginData, sharedPluginData), there is a much faster API. Use this table:

| You want… | DON'T | DO |
|---|---|---|
| One specific node, you have its ID | `page.findOne(n => n.id === id)` | `await figma.getNodeByIdAsync(id)` |
| All nodes of a given type | `page.findAll(n => n.type === 'TEXT')` | `page.findAllWithCriteria({ types: ['TEXT'] })` |
| Type + a few cheap attributes (`name`, `visible`, etc.) | `page.findAll(n => n.type === 'TEXT' && n.name === 'Title')` | `page.query('TEXT[name=Title]')` (see [SKILL.md → node.query](../SKILL.md#nodequeryselector--css-like-node-search)) |
| Nodes with plugin data | `page.findAll(n => n.getPluginData('key'))` | `page.findAllWithCriteria({ pluginData: { keys: ['key'] } })` |
| Nodes with shared plugin data | `page.findAll(n => n.getSharedPluginData('ns', 'key'))` | `page.findAllWithCriteria({ sharedPluginData: { namespace: 'ns', keys: ['key'] } })` |

**`types` and `pluginData.keys` are arrays — pass multiple values in a single call instead of issuing N separate ones.** A union over `types` is OR'd; multiple `pluginData.keys` match nodes that carry *any* of the given keys.

```js
// Multiple types in one call — returns COMPONENT ∪ COMPONENT_SET in one indexed pass
page.findAllWithCriteria({ types: ['COMPONENT', 'COMPONENT_SET'] })

// Multiple pluginData keys in one call — matches nodes that have any of them
page.findAllWithCriteria({ pluginData: { keys: ['dsb_key', 'dsb_run_id'] } })

// Multiple sharedPluginData keys (under the same namespace)
page.findAllWithCriteria({ sharedPluginData: { namespace: 'dsb', keys: ['key', 'run_id'] } })
```

One more rule applies to any traversal — see also the dedicated [Scope traversal to the smallest known ancestor](#scope-traversal-to-the-smallest-known-ancestor) gotcha below:

1. **Narrow the scope.** `frame.findAll(...)` is much cheaper than `figma.currentPage.findAll(...)`. Hold onto the smallest known subtree.

```js
// WRONG — full-tree scan for a single node you already have an ID for
const button = figma.currentPage.findOne(n => n.id === BUTTON_ID)

// CORRECT — indexed lookup
const button = await figma.getNodeByIdAsync(BUTTON_ID)

// WRONG — type filter via predicate (walks every node)
const textNodes = figma.currentPage.findAll(n => n.type === 'TEXT')

// CORRECT — type filter via criteria (indexed, hundreds of times faster on large docs)
const textNodes = figma.currentPage.findAllWithCriteria({ types: ['TEXT'] })

// WRONG — full traversal when you only need a couple of types
frame.findAll(() => true).forEach(node => { /* only touches TEXT and INSTANCE */ })

// CORRECT — restrict to the types you actually care about
const candidates = frame.findAllWithCriteria({ types: ['TEXT', 'INSTANCE'] })
for (const node of candidates) { /* ... */ }
```

**Caveat — don't enumerate every scene type just to use criteria.** If you'd need to list ~10+ types (e.g., "any node that can carry `boundVariables` or `effectStyleId`"), the type list is no longer narrowing — it's enumerating. `findAll(() => true)` is shorter, equivalently fast on real screen-sized subtrees, and saves a lot of script tokens. Reserve `findAllWithCriteria` for genuine narrowing (one to a handful of types).

**When the predicate combines type + name (or another non-indexed attribute), use criteria for the type and a `.filter`/`.find` for the rest** — the criteria stage already narrows the candidate set to the matching type using the index:

```js
// WRONG — predicate walks every node
const slot = instance.findOne(n => n.type === 'SLOT' && n.name === 'Content')

// CORRECT — type-indexed criteria + name filter
const slot = instance
  .findAllWithCriteria({ types: ['SLOT'] })
  .find(n => n.name === 'Content')
```

Name-only lookups (`findOne(n => n.name === 'X')`) cannot use criteria — they remain the right tool when you only have a name. But if you can capture the node's ID once and re-fetch with `getNodeByIdAsync` on subsequent calls, prefer that over searching by name again.

## Scope traversal to the smallest known ancestor

Every `findAll` / `findOne` / `findAllWithCriteria` walks the entire subtree of the receiver. Picking the right receiver is the single biggest performance lever you have — bigger than the type index. Cheapest to most expensive:

| Receiver | Walks… |
|---|---|
| `someFrame.findAllWithCriteria(...)` | one frame's subtree |
| `figma.currentPage.findAllWithCriteria(...)` | one page (every loaded node on it) |
| `figma.root.findAllWithCriteria(...)` | **every loaded page in the document** — only safe on tiny files |

**Rule: scope traversal to the smallest known ancestor.** If you have a specific frame's ID, search inside that frame. If you have a section, search inside that section. Drop back to `figma.currentPage` only when the work is genuinely page-wide.

```js
// WRONG — walks every loaded page in the document
const all = figma.root.findAllWithCriteria({ types: ['INSTANCE'] })

// BETTER — one page only
const onPage = figma.currentPage.findAllWithCriteria({ types: ['INSTANCE'] })

// BEST — when you have the parent frame's ID, search just that subtree
const frame = await figma.getNodeByIdAsync(FRAME_ID)
const inFrame = frame.findAllWithCriteria({ types: ['INSTANCE'] })
```

**Never use `figma.root.findAll(...)` in a `use_figma` script.** It walks every page that has been loaded into memory and forces every other page to load if not already in memory — the worst-case traversal. There is no legitimate use of it in this codebase.

**Never loop `figma.root.children` calling `setCurrentPageAsync(page)` and then `page.findAll(...)`** — that's the same antipattern in slow motion: one whole-page scan per page, plus the cost of switching pages. If work spans multiple pages, **fan out** instead: emit one `use_figma` per page in parallel (see [Set current page once per `use_figma` call](#set-current-page-once-per-use_figma-call--split-multi-page-work-into-parallel-calls)).

When you don't have a frame ID handy, capture one from a parent call a

... [Content truncated, total 53,768 chars] ...