<!-- ═══════════════════════════════════════════════════════════════════
     DISPATCH DIRECTIVE (for Main Agent orchestrator):
     The sub-agent reads this ENTIRE template directly as its first step.
     The Task query only contains parameters and this file path.
     Do NOT summarize. Do NOT omit rules. Do NOT compress.
     The sub-agent has NO other way to learn these rules.
     Missing rules → lower first-pass quality. Do not rely on post-write validation or regeneration.
     ═══════════════════════════════════════════════════════════════════ -->
# Phase 4: UI Kit Sub-Task Template

## Main Kit

```
Task: Generate interactive Design System Showcase (type: {kitType}).
Output:
  - ui_kits/{kitType}/index.html
  - ui_kits/{kitType}/quality-report.json
OutputDir: {output_dir}
OutputFileRel:
  - ui_kits/{kitType}/index.html
  - ui_kits/{kitType}/quality-report.json
OutputFileAbs:
  - {output_dir}/ui_kits/{kitType}/index.html
  - {output_dir}/ui_kits/{kitType}/quality-report.json

⚠️ HARD RULES (embedded — do NOT skip):
  1. MUST be standalone React 18 app (CDN imports, no build step)
  2. Prefer 3 distinct primary views with navigation between them, but do not optimize for validator-specific screen markers.
  2b. SHOWCASE NARRATIVE (MANDATORY — design first, components serve the design):
      UIKit is the INTERACTIVE SHOWCASE of the completed design library.
      It is NOT a raw component grid and NOT a disconnected component dump.
      It IS a curated, brand-immersive product scene that proves the design system works.
      (a) Read SKILL.md first. Extract Essentials as hard constraints.
      (b) Read README.md second. Extract Visual Foundations + Content Fundamentals as the design story.
      (c) Design the page experience first: brand scenario, screen flow, hierarchy, density, rhythm.
      (d) Then choose components from `components.css` that naturally serve that design.
      (e) Every screen must combine real brand/product context with strict component fidelity.
      (f) Anti-pattern: tiling components just to maximize count.
  2c. COMPONENT CONSUMPTION HIERARCHY (MANDATORY — strict priority order):
      (a) `{output_dir}/components.css` is the SOLE ground truth for component CSS + DOM anatomy.
          It contains all component class definitions AND `/* @anatomy */` comments showing representative DOM structure.
      (b) Read UIKitPlanFile for whitelist/blueprint only; do NOT use it as a styling source.
      (c) Read `{output_dir}/components.css` ONCE to obtain:
          - All component CSS class definitions (rules, pseudo-states, size/variant modifiers)
          - `/* @anatomy ... */` comments per component showing representative DOM structure
          - Component slug sections (separated by `/* ── {Name} ─── */` headers)
      (d) For variant/state details beyond what CSS provides, Read `{output_dir}/components/{slug}.json` (intent JSON) which provides `controlMatrix` (class combinations + CSS values) and `patterns` (structural models).
      (e) Directly reuse component class names from `components.css`. Do NOT redefine, rename, or override component CSS in UIKit `<style>`.
      (e2) UIKit `<style>` block is ONLY for page-level layout classes (.uikit-shell, .app-shell, .sidebar, etc.).
          - FORBIDDEN: redefining any selector that exists in `components.css`
          - FORBIDDEN: using !important to override component styles
          - ALLOWED: wrapper classes that position/arrange components without changing their internals
      (f) Read components/{slug}.json only as auxiliary context for variants/states when needed.
      (g) If a whitelisted slug is NOT present in `components.css`, Read `components/_evidence/{slug}.json` as fallback structure evidence.
      (h) Evidence fallback MUST be marked with warning `rendered-from-evidence:{slug}` and must not invent structure absent from evidence.
      (h2) If components/{slug}.json or evidence renderFacts contains `patterns.componentAnatomy`, preserve at least one `componentAnatomy.scenarios[*].root` slot hierarchy for that component instance. If it contains `patterns.listModel.itemStates`, preserve active/default/disabled text style differences; do not express state only through icon or container color.
      (h3) Child component binding: when composing complex showcases (Card with action buttons, Table with inline controls, List with trailing badges), read `componentRef` from `componentAnatomy` slots or `listModel.itemSlots[*].structure.componentRef` in the intent JSON to determine which variant/size class to apply to nested child components. Apply the exact class combination from `components.css` matching `componentRef.slug` + `componentRef.variant` + `componentRef.size` (e.g., `.btn.primary.size-sm`, `.tag.success.size-xs`). Do NOT default to a generic variant when `componentRef` specifies a different one.
      (i) **FORBIDDEN**: Reading `preview/component-*.html` files. `components.css` is the SOLE component styling and anatomy source.
  3. MUST use ONLY CSS variables that exist in colors_and_type.css, plus page-level custom properties you declare yourself in this HTML.
     Step 1: Read {CSSFile}; extract every declared custom property with regex `--([A-Za-z0-9_\-\u4e00-\u9fff]+)\s*:` (variable names may contain CJK characters).
     Step 2: Allowed variable names = that extracted set + custom properties declared inside this HTML (inline style or <style>, e.g. `--uikit-sidebar-w` from Rule 22b).
     FORBIDDEN: var(--any-name, #hex-fallback) for token variables — if a token variable doesn't exist, don't use it. EXCEPTION: the Rule 22b skeleton's `var(--uikit-sidebar-w, 220px)` fallback is required as-is.
  4. MUST use <link rel="stylesheet" href="{CSSLink}"> for tokens AND <link rel="stylesheet" href="../../components.css"> for component classes.
     SOURCE: Use these exact paths. Do NOT read uikit-plan.json just to obtain these links.
     ⚠️ SELF-CHECK: Before calling Write, search your generated HTML for BOTH EXACT strings:
     `<link rel="stylesheet" href="{CSSLink}">` and `<link rel="stylesheet" href="../../components.css">`.
     If EITHER is NOT found → your output is INVALID → insert them as FIRST children of <head> before writing.
  5. Phone frame wrapper required for app type; adapt wrapper semantics for non-app kit types from {kitType}.
  6. Read ONLY the simplified core inputs listed below: SKILL.md, README.md, colors_and_type.css, components.css, optional components/{slug}.json, optional uikit-plan.json, optional components/_evidence/*.json fallback, icons, aesthetics, and constraint files. Do NOT read phase2-brand-analyst.json, css.json, preview-css-extracted.json, or preview/component-*.html for UIKit generation.
   7. Write files to disk, then write the compact report to `ReturnReportFileAbs`. Final response: `已完成 UI Kit。` No verification, no read-back, no extra prose.
     CRITICAL OUTPUT PATH CONTRACT:
     - The physical Write targets MUST be the OutputFileAbs paths exactly:
       `{output_dir}/ui_kits/{kitType}/index.html`
       `{output_dir}/ui_kits/{kitType}/quality-report.json`
     - NEVER write to `ui_kits/{kitType}/index.html` or `ui_kits/{kitType}/quality-report.json` as relative paths.
     - OutputFileRel is only for the returned contract; it is not a filesystem write target.
     - If the Write tool requires file paths, pass the absolute OutputFileAbs path.
  8. CONTENT DENSITY & MOCK DATA (MANDATORY):
     (a) About 5 component instances per view; tables/lists MUST have ≥6 mock data rows; charts MUST have ≥12 data points with realistic units and a plausible trend (no empty charts, no all-equal bars).
     (b) SCOPE CLARIFICATION: the evidence-side `contentPolicy.forbiddenModes: ["invented-product-data"]` applies to component PREVIEW reproduction only. At the UIKit scenario layer you MUST generate realistic mock product data (names, amounts, dates, statuses) consistent with the plan's screenBlueprints / productNarrative scenario. Generic Figma placeholders ("Button text", "Cell text here") are FORBIDDEN as visible UIKit content.
     (c) Mock data must tell one coherent story per screen (same product domain, consistent entities across table/cards/charts).
  8b. SINGLE PRIMARY ACTION (MANDATORY): each view has EXACTLY ONE primary-variant button instance (the screen's main CTA, from screenBlueprints[*].primaryAction when present). All other actions on that view MUST use secondary/ghost/text variants. Table row actions are never primary.
  8c. INTERACTIVE STATES (MANDATORY): each view MUST render evidence-backed interactive states:
      (a) at least 1 hover pseudo-class rule group applied to a core component (use controlMatrix.states colors when present);
      (b) at least 1 disabled component instance;
      (c) at least 1 selected/active state (nav item, tab, or list row).
      Every non-default state present in a core component's `controlMatrix.states` MUST be expressed as a pseudo-class rule or a rendered state instance. Never fake states with filter:brightness or generic opacity when state colors exist.
  9. Prefer CSS classes in a <style> block for styling. Keep generated HTML simple and readable.
     ⚠️ DYNAMIC VALUES (chart bar heights, progress bars, conditional widths):
     Use finite CSS classes only. Define classes such as .barH20/.barH40/.barH60/.barH80 and .progress25/.progress50/.progress75 in <style>, then select those class names in JSX.
     Prefer class names for repeated dynamic values.
     For icon sizing: define .icon-sm / .icon-md / .icon-lg classes.
  10. ICON STRATEGY (3-TIER):
      (a) Use <img src="../../assets/icons/{name}.svg" width="N" height="N"> for ALL icons that exist in AvailableIcons.
      (b) If icon is NOT in AvailableIcons, use Lucide JS: <i data-lucide="{name}" style="width:Npx;height:Npx;display:inline-block"></i> (requires lucide.min.js script in head + lucide.createIcons() before </body>)
      (c) If no Lucide equivalent exists but evidence proves an icon slot, preserve that slot's exact width/height and render the contract fallback icon (`renderFacts.icons.unknownFallback`, default `circle-help`). Do not substitute Unicode glyphs, text arrows, CSS pseudo-icons, dots, or invented fallback icons.
      (d) Define ZERO <symbol> blocks — all icons use <img> tags exclusively.
      (e) NEVER define icon helper functions that construct paths dynamically.
          Every icon MUST appear as a literal <img src="../../assets/icons/{name}.svg"> tag with a static string src.
          BAD:  function icon(n) { return <img src={`../../assets/icons/${n}.svg`} /> }
          GOOD: <img src="../../assets/icons/icon16add.svg" width="16" height="16" alt="add" />
      (f) If preview/evidence semantics indicate an icon slot, render a real icon when local SVG or semantic Lucide exists; otherwise render the contract fallback icon at the evidenced slot size. Do NOT replace sidebar/nav/button/search/table-action/status icons with decorative CSS circles, bordered glyph boxes, initials, dots, or text-only placeholders. Use local SVG first, then Lucide CDN.
      (g) RUNTIME SAFETY: Follow `file-specs/ui-kit.md` → `Runtime Safety Contract (HARD)`.
          `MutationObserver` is forbidden in generated UIKit.
          Lucide initialization must remain one-shot; never watch DOM changes to re-run `lucide.createIcons()`.
      This eliminates ~1500 tokens of SVG path definitions entirely.
  11. Each screen = 1 structural wrapper + ≤3 content blocks. Dashboard "Settings" = ONE tab content only, not all tabs rendered.
  12. Output token budget ≤ 8000. If approaching limit: ***REDACTED***
  12b. Reasoning budget: choose one coherent UIKit concept, run required self-checks, then write. Do not explore multiple full alternatives in hidden reasoning. This MUST NOT reduce fidelity, density, aesthetics, mock data richness, interactive states, quality-report checks, or validators.
  13. SVG REUSE: Not applicable — all icons use <img> tags (see RULE 10). No <symbol> blocks needed.
  14. ZERO hardcoded color hex/rgb in <style> — the ONLY allowed exceptions are: #ffffff (on-primary text) and rgba() for state-layer opacity values. Everything else MUST use a CSS variable from colors_and_type.css.
  15. Before Write, self-scan the generated HTML string for every `var(--name)` and replace any name not in the extracted CSS variable set.
  16. Do NOT use `--color-danger` unless it exists in colors_and_type.css. Prefer `--color-destructive` or `--color-error` for destructive states when present.
  17. COLOR PRIORITY HIERARCHY:
      CSS files may contain many token categories. UI Kit MUST follow this usage hierarchy:
      ***REDACTED***
        Variable families: --background, --foreground, --card, --primary, --secondary,
        --border, --muted, --accent, --destructive, --popover, --input, --ring
      - CONTEXTUAL (only inside their designated container):
        --sidebar-* → only inside sidebar/nav panels
      - DATA-VIZ (only inside chart/visualization elements):
        --chart-* → only inside chart containers (bars, lines, areas, legends)
      - FORBIDDEN: Using sidebar/chart/data-viz tokens as page-level backgrounds,
        main navigation bars, card surfaces, or button fills outside their designated context.
      - SELF-CHECK: Before Write, scan generated HTML. If any --sidebar-* or --chart-*
        appears in a non-sidebar/non-chart context, replace with core system equivalent.
  18. CSS THREE-LAYER MODEL (CRITICAL):
      UIKit has three CSS layers (loaded in order):
      (a) TOKEN LAYER — `colors_and_type.css` (loaded via <link>).
          Provides all CSS custom properties (--color-*, --space-*, --radius-*, etc.).
      (b) COMPONENT LAYER — `components.css` (loaded via <link>).
          Provides all component class definitions (.btn, .card, .tbl, etc.) + DOM anatomy comments.
          These are auto-extracted from preview HTML by a deterministic script.
          UIKit MUST NOT redefine, override, or duplicate any selector from this layer.
      (c) PAGE LAYER — UIKit's own <style> block.
          UIKit may create semantic layout classes such as .app-shell, .sidebar, .page-header, .metric-grid.
          These classes control composition, spacing, layout, and narrative surfaces.
          Every value must use allowed var(--xxx) tokens from colors_and_type.css.
      (d) Page-level CSS may wrap and arrange components, but must not override component internals in a way that changes their visual identity.
      (e) When page design and component fidelity conflict, preserve component fidelity and adjust the page layout.
  19. COMPONENT WHITELIST:
      (a) Allowed component families = union of UIKitPlanFile.allowedComponents and slugs discovered from `components.css` section headers (`/* ── {Name} ── */`).
      (a2) When UIKitPlanFile.selectionPolicy is `fixed-slots-first`, corePreviewComponents are already the deterministic fixed-slot result. Do NOT re-rank, replace, or expand core components. Use slotAssignments and missingFixedSlots only as explanation/diagnostics.
      (b) Slug derivation: `/* ── Button ── */` section in components.css → `button`.
      (c) Main visual components should prefer components.css-derived slugs; uikit-plan support slugs may be rendered from evidence when preview is insufficient.
      (d) components/{slug}.json can explain variants/states; components/_evidence/{slug}.json can authorize fallback rendering only when slug is whitelisted.
      (e) Add data-component="{slug}" on every major component wrapper.
      (f) Do not invent component families absent from preview/, UIKitPlanFile.allowedComponents, or components/_evidence/index.json.
      (g) Every major design-system component wrapper MUST include `data-component="{allowed slug}"` so deterministic gates can verify whitelist usage.
  20. AESTHETIC SYSTEM (mandatory — governs page-level design decisions):
      Read `{SKILL_DIR}/aesthetics/index.md` in full BEFORE composing screens.
      This file is the design-thinking framework. It governs:
      - §0 North Star: the 5 criteria every page must meet
      - §2 Layout: rhythm patterns, whitespace discipline, composition
      - §4 Color & Surface: palette direction by business tone
      - §8 Anti-AI-Slop Blacklist: hard-fail patterns (any one = unqualified)
      - §11 Showcase Patterns: when kit is app/mobile type, prefer P-5 Phone Stage or P-1 Deep Stage
      THEN read `{SKILL_DIR}/aesthetics/screen-craft.md` — screen-level layout discipline
      (zero-tolerance rules, density laws, and the per-kit-type section matching {kitType}:
      §2 app phone-screen discipline / §3 dashboard density / §4 website narrative).
      Run its §5 Post-Write Screen Check on every screen before Write.

      PRIORITY HIERARCHY (resolves conflicts):
      (a) SKILL.md Essentials → hard numeric constraints and brand decisions.
      (b) README.md Visual Foundations → design philosophy and voice.
      (c) colors_and_type.css → executable CSS variable allowlist and semantic token source.
      (d) preview/component-{slug}.html → exact component DOM + styling.
      (e) components/_evidence/{slug}.json → fallback structure/composition evidence when preview is missing or insufficient. Consume final-state `renderFacts` only in this order: `identity` → `controlMatrix` → `patterns` → `contentPolicy` → `geometry`/`renderObligations` → `iconSlots`/`icons` → `unknowns`/`riskNotes`. Do not expect raw `renderPlan`, `visualSpecs`, `instanceComplexity`, or `evidenceQuality`.
      (f) Aesthetics → page-level composition, rhythm, spacing between components, visual tone, anti-patterns.

      Aesthetics defines HOW components are composed on the page. Preview HTML defines what each component looks like internally. Evidence fills gaps only; it never overrides existing preview CSS.

      Dark theme: if SKILL.md/README.md indicates dark theme or colors_and_type.css uses dark backgrounds, also read `{SKILL_DIR}/aesthetics/dark-mode.md`.
      Navigation/footer patterns: if kit includes nav, also read `{SKILL_DIR}/aesthetics/navigation-footer.md`.
  21. DOCUMENTATION CONSUMPTION (MANDATORY):
      (a) Read {output_dir}/SKILL.md BEFORE composing. Extract:
          - Essentials: primary color, radius, spacing, font, voice, shadow, brand quirk
          - These are HARD CONSTRAINTS for every visual decision in the Kit
      (b) Read {output_dir}/README.md BEFORE composing. Extract:
          - Visual Foundations: color, type, spacing, radius, shadow philosophy
          - Content Fundamentals: voice/tone rules and copy examples
          - Caveats: known substitutions or gaps to avoid repeating
      (c) VERIFICATION before Write:
          - Primary color from Essentials appears as dominant accent
          - Radius values match Essentials exactly where specified
          - Font-family declarations match README Typography section
          - Copy tone follows Content Fundamentals
      (d) README.md is the brand bible for narrative and voice. SKILL.md Essentials win for exact numeric constraints.
  22. CJK TEXT SAFETY (MANDATORY for Chinese/Japanese/Korean content):
      - All text in constrained-width containers (sidebar nav items, table cells, card titles, tags) MUST have `overflow: hidden; text-overflow: ellipsis; white-space: nowrap` or `-webkit-line-clamp`.
      - Flex children containing text MUST have `min-width: 0` (or `min-w-0`), otherwise text-overflow is ineffective.
      - Chinese headings: `word-break: keep-all; overflow-wrap: break-word`.
      - Tags/badges with Chinese > 4 chars: use `rounded-lg` not `rounded-full`; always `white-space: nowrap`.
      - Table th: `white-space: nowrap`; td with CJK text: `word-break: break-all` or `-webkit-line-clamp: 2`.
      - NEVER rely on container width alone to control CJK text flow — always declare explicit overflow behavior.
  22b. LAYOUT OVERFLOW GUARD (MANDATORY):
      - This guard is a deterministic failure gate, not advisory guidance. Any missing required class, missing responsive breakpoint, page-level scaling, or 1184px overflow-risk rule violation blocks validation.
      - The HTML `<head>` MUST include `<meta name="viewport" content="width=device-width, initial-scale=1.0">` before stylesheet links.
      - The root shell MUST include `data-layout-guard="uikit-v1"`.
      - Define and use these page-level classes exactly: `.uikit-shell`, `.uikit-sidebar`, `.uikit-main`, `.uikit-toolbar`, `.uikit-responsive-grid`, `.uikit-table-wrap`, `.uikit-truncate`, `.uikit-nowrap`, `.uikit-action-cell`, `.uikit-action`.
      - App kits ({kitType} = app): desktop-grid guards are advisory (validator reports warnings, not failures). HARD requirements remain: viewport meta, `data-layout-guard="uikit-v1"`, `.uikit-shell` (width:100%; max-width:1184px; margin:0 auto; overflow:hidden), `.uikit-truncate`, `@media (max-width: 640px)` stack guard, and no transform/zoom page scaling. Define `.uikit-sidebar`/`.uikit-responsive-grid`/`.uikit-table-wrap`/`.uikit-action-cell`/`.uikit-action` only where the phone screen actually uses those patterns; do not emit dead boilerplate just to satisfy the validator.
      - Target viewport is 1184px, matching the frontend Component tab iframe canvas (`componentList` max 1184px, full width with no preview padding). `.uikit-shell` MUST use `width: 100%`, `max-width: 1184px`, `margin: 0 auto`, and `overflow: hidden`.
      - Do NOT solve width problems by designing a wider virtual canvas and applying `transform: scale(...)`, `zoom`, or iframe/page scaling. The UIKit must fit natively at 1184px.
      - Responsive behavior is mandatory: 1184px is the desktop baseline, not a fixed-only canvas. At `max-width: 900px`, multi-column shells MUST collapse to one content column or a compact rail + content layout. At `max-width: 640px`, cards/toolbars MUST stack, optional sidebars MUST collapse above content, and dense tables MUST use horizontal scroll or card rows.
      - `.uikit-main`, `.uikit-toolbar`, cards, panels, table/list wrappers, and every flex/grid child that can contain text MUST include `min-width: 0`.
      - Multi-column grids MUST use `minmax(0, 1fr)` for flexible columns. Never use bare `1fr` next to fixed columns for content that can contain text.
      - `.uikit-responsive-grid` MUST define desktop columns with `minmax(0,1fr)` and include media queries that reduce columns before overflow occurs.
      - `.uikit-table-wrap` MUST contain `max-width:100%; overflow-x:auto; overscroll-behavior-x:contain`; dense data tables inside it may use an evidenced `min-width` so columns scroll instead of squeezing text into unreadable cells.
      - `.uikit-truncate` MUST contain `min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap`.
      - `.uikit-nowrap` MUST contain `white-space: nowrap; flex-shrink: 0`.
      - `.uikit-action-cell` MUST contain `display:flex; align-items:center; gap:8px; min-width:0; max-width:160px; overflow:hidden`.
      - `.uikit-action` MUST contain `min-width:0; max-width:120px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap`.
      - Search bars, filter buttons, timestamps, badges, sidebar titles, nav labels, table cells, and audit metadata MUST use `.uikit-truncate` or `.uikit-nowrap` according to their role.
      - Table/list action cells MUST render at most one visible text button per row plus one compact icon/overflow action. Never stack multiple full-width buttons in a single table cell.
      - Button groups and segmented controls MUST be rendered as one shared group; do not duplicate arrows/icons across every segment unless `renderFacts.patterns.segmentedGroups[*].segments[*].hasIcon` or `renderFacts.iconSlots` proves that segment has the icon.
      - Avatar or leading media slots in list/sidebar/table rows MUST render a real local icon/image or Lucide fallback (`circle-user-round`, `user`, or the evidenced semantic name). Do not use empty CSS circles as avatar/icon placeholders.
      - PLACEHOLDER SUBSTITUTION (MANDATORY): Evidence-derived `sampleValues` may contain Figma master-component placeholders that MUST NOT appear verbatim in UIKit HTML. Known placeholders (case-insensitive): `Button text`, `Badge text`, `Label`, `Placeholder text`, `Text`, `Input text`, `Helper text`, `Link text`. When rendering table cells, button labels, or badge text that match a known placeholder, substitute a contextually appropriate word based on column `role` and `productContext`: action→"View"/"Edit"/"Delete"; status→"Active"/"Pending"/"Completed"/"Failed"; badge→"New"/"Pro"/"Beta"; button→"Submit"/"Save"/"Cancel". Substitutions replace UI-chrome labels only and do NOT violate `contentPolicy.forbiddenModes: ["invented-product-data"]`.
      - FORBIDDEN: vertical CJK button text caused by narrow controls. Controls with 2+ CJK characters MUST have enough width or use ellipsis, never stacked glyphs.
      - FORBIDDEN: fixed `left/t

... [Content truncated, total 39,810 chars] ...