# Figma Token Generation Sub-Task Template

> ⚠️ ROUTE: Figma (EXTRACT ONLY). Rules from scratch-token-gen do NOT apply here.

> Sub-agent reads design-tokens.jsonl (which includes merged design language overview) to generate complete design token CSS.
> Writes 1 file. Writes compact report to `ReturnReportFileAbs` (≤ 4KB).
> Main Agent runs `css-to-json.mjs` after this sub-agent returns.

---

## Sub-Agent Execution Constraints

- Tool bans: per SKILL.md invariant #16 (`TodoWrite`, `Skill`, `Grep`, `RunCommand`, `SearchCodebase`); this template additionally forbids `LS`, `Glob` (no discovery needed — all input paths are explicit).
- The variables-raw data may be split across multiple part files (e.g. variables-raw.md, variables-raw-part1.md ... part7.md) — read ALL parts to ensure complete coverage.
- SILENT: Do NOT output intermediate reasoning between tool calls. After Write, write the report file and final-respond only `已完成 Token 生成。`.
- WRITE-FIRST (anti-overthinking): Do NOT compose the complete token structure in your
  reasoning before writing. After the READ SEQUENCE, go STRAIGHT to the Write call and
  think WHILE writing — the CSS file itself is your working draft. Correctness is
  enforced by the read-back REVIEW step afterwards, not by upfront mental rehearsal.
  Pre-drafting the full CSS in reasoning wastes tokens and adds no accuracy.
- COMPLETION CAP: per SKILL.md invariant #23. Machine data goes to `ReturnReportFileAbs`; final response is only `已完成 Token 生成。`.
- ⚠️ DISPATCH PARAMETER: `subagent_type` MUST be `"general_purpose_task"` (not "Explore", not "search"). Sub-agents WRITE files to disk.

---

## Task Template

```
Task: Generate complete token system from Figma design data for brand "{brandName}" ({productType}).
Output (write 1 file):
  1. {output_dir}/colors_and_type.css

⛔ HARD PROHIBITION — You MUST write EXACTLY 1 file: {output_dir}/colors_and_type.css
css.json is derived by deterministic scripts from your CSS output.
Writing it yourself will produce INCORRECT format and break the frontend
(TypeError: Cannot read properties of undefined (reading 'hex')).
Do NOT write css.json. ONE file only.

⛔ NO CSS IN REASONING (HARD — this is a budget rule, same severity as the file prohibition above):
NEVER draft, rehearse, or revise CSS content inside your thinking/reasoning.
Any CSS composed in reasoning must be typed AGAIN in the Write call — it is 100% wasted
tokens and adds zero accuracy. Concretely:
  ***REDACTED***
    (theme mode, group list, priority order) — never token-by-token content.
  - The FIRST place any `--token: ***REDACTED***
    Compose the CSS inside the Write argument, deciding values as you type.
  - If during REVIEW you find problems, fix them with Edit calls on the FILE.
    Do NOT re-plan or re-draft the corrected CSS in reasoning and rewrite the whole file.
All token categories with source data MUST be present (colors, spacing, radius, shadow, typography).

NOTE: The output contract (group comments, ordering, @primary, @group-priority, category
naming, aliases, self-review) is the route-independent css-tokens.md § Shared Token
Contract — this route is its reference standard. Rules below spell it out together with
this route's Figma-specific source-fidelity requirements.

⚠️ HARD RULES (embedded — do NOT skip):

  READ SEQUENCE (mandatory, in this order):
  R1. Read constraint specs FIRST: {SKILL_DIR}/file-specs/css-tokens.md
  R2. Read design tokens: ***REDACTED***
      — First: attempt to read the full file (no offset/limit).
      — If Read returns "exceeds the limit of 64KB" error: this is a large token file. Re-read in chunks using offset/limit. Since JSONL has few lines (typically 10-20, one per variable set), use small limits:
        Read offset=1 limit=5 → Read offset=6 limit=5 → Read offset=11 limit=5 → ... until no more content.
        Accumulate ALL `_type` sections across chunks. Do NOT start writing CSS until every line has been consumed.
      — Edge case: if even a single line (limit=1) exceeds 64KB, extract what you can and note missing data in warnings.
  R2b. Read raw Figma variables: {bundle_path}/context/variables-raw*.md (CRITICAL for color completeness)
       — This file contains ALL Figma variables with their original designer-defined names and values.
       — design-tokens.jsonl only includes variables with numeric suffixes (e.g. /500, -6) in stepsMap.
       — Variables with semantic names (e.g. brand/hover, text/secondary, fill/active) are MISSING from design-tokens.jsonl.
       — When generating theme color tokens, cross-reference variables-raw to ensure NO semantic colors are lost.
       — If a color exists in variables-raw but not in design-tokens.jsonl variableSets, you MUST still include it.
       — ⚠️ Data may be split across multiple files: variables-raw.md (header), variables-raw-part1.md, part2.md, ... up to part7.md. Read ALL parts.
       — ⚠️ PALETTE COMPLETENESS MANDATE (CRITICAL):
         After reading all variables-raw parts, actively identify ALL distinct
         color palette families (hue scales with ≥ 2 stops). Compare against
         what design-tokens.jsonl already captured. For EACH palette family in
         variables-raw that is MISSING or INCOMPLETE in design-tokens.jsonl,
         extract it and include it in your CSS output.
         Common signs of missed palettes:
           - Variable paths like "颜色/碧涛青/*" or "Color/Cyan/*"
           - Collection names containing hue words in any language
           - Sets with ≥ 3 color variables sharing a common path prefix
         Do NOT rely solely on design-tokens.jsonl for color completeness.
         variables-raw IS the authoritative complete source.
  R3. (Optional) Read designer notes summary: {bundle_path}/generated/annotations-summary.jsonl first (only if design-tokens.jsonl designerNotes is empty or insufficient). Fallback to {bundle_path}/annotations/index.md only if the summary is missing or insufficient

  CSS GENERATION RULES:
  4. CSS blocks depend on your theme decision (see Rule 4b below). Include @import for Google Fonts, all token scales.
  4b. THEME DECISION (YOUR responsibility — not pre-determined):
     Read `themeSignals` in design-tokens.jsonl:
     ***REDACTED***
     - `luminanceProfile.darkValueRatio`: ratio of color values with luminance < 0.3
     - `sampleIdentical` / `sampleDifferent`: concrete examples

     Decision logic:
     - identicalRatio > 0.9 AND darkValueRatio > 0.8 → @dark-only
       → :root contains dark values directly. Omit .dark {} block. Add /* @dark-only */ at top.
     - identicalRatio > 0.9 AND darkValueRatio < 0.2 → @light-only
       → :root contains light values directly. Omit .dark {} block. Add /* @light-only */ at top.
     - Otherwise → dual-theme
       → :root (light values) + .dark {} (dark overrides)

     These signals are ADVISORY. You have final say — factor in designerNotes,
     specAnnotations, and overall color context.
  4c. DESIGN LANGUAGE CONTEXT (from `_type: "designLanguage"` line in design-tokens.jsonl — informs but does NOT override source data):
     The designLanguage line provides high-level design language signals to guide your decisions:
     - `style` ("flat"/"material"/"neumorphic"/etc.) — informs shadow depth, border usage
     - `density` ("compact"/"normal"/"spacious") — validates spacing choices
     - `mood` — emotional direction (e.g., "professional", "playful")
     - `brand.hasDarkMode` — quick confirmation for Rule 4b dark mode decision
     - `contrastIssues[]` — accessibility warnings; if present, add CSS comment noting
       low-contrast pairs for downstream review
     - `namingConvention` — cross-validate naming style choices

     These signals are ADVISORY context. The other lines in design-tokens.jsonl (themeSignals,
     colors, typography, etc.) remain the authoritative source for all token VALUES.
     designLanguage helps you make better decisions about organization, naming, and theme structure.
  5. SOURCE FIDELITY (applies to all Figma-route output):
     Goal: output ONLY what exists in source data.
     - Every hex value must trace to design-tokens.jsonl (Variables, resolvedSemanticColors, or scaleGroups).
     - Scales: if source has N stops, output N stops. Never fill to 10.
     - Missing roles: omit (output nothing), never fabricate.
     - Provenance: `/* Variable: {name} */` for semantic Variables; `/* Source: {set name} */` for scale groups.
  6. NO INTERPOLATION: If source data has only one color shade (e.g., primary-500), output ONLY
     that single value. Do NOT generate a full scale by lightening/darkening. Output exactly what
     exists in the source — never fabricate colors that the designer did not provide.
  7. Color Data Navigation:
     design-tokens.jsonl `colors.variableSets` is an array of Variable Sets from Figma.
     Each Set has:
       - `name`: the Figma Variable Set name
       - `isSemantic`: true if >50% variables have semantic paths (bg/, text/, border/, etc.)
       - `variables` (for semantic Sets): compact variable list, each entry is one of:
         - `{ name, light, dark }` — dual-theme variable
         - `{ name, value }` — same value in both themes or single-mode variable
         - `light`/`dark` are normalized semantic labels; original Figma modes may be non-standard names such as Day/Night
       - `scaleGroups` (for primitive Sets): color scale summaries with prefix + sample value

     ⚠️ VARIABLE-FIRST PRIORITY (CRITICAL):
     Figma Variables represent the designer's INTENTIONAL token system. When semantic
     Variable Sets exist (isSemantic=true), they are the PRIMARY source for theme tokens:

     Priority order (highest → lowest):
       P0. `authoritativePrimary` (Rule 7.2) — if present, skip all other primary logic
       P1. Semantic Variables (`isSemantic=true`, has `variables[]` with `{name, light, dark}`)
           — These ARE the designer's token definitions. Use their names for CSS variable
             naming and their light/dark values directly for :root / .dark blocks.
           — Variable name paths define roles: `bg/color-bg-1` → background token,
             `text/color-text-1` → foreground token, `Brand Color/常规 @primary-6` → primary
           — When a variable name contains `@token-name` (e.g., `@primary-6`, `@color-bg-1`),
             that suffix IS the canonical token reference. Preserve it in CSS comments.
       P2. `resolvedSemanticColors` with `confidence >= 0.7` — computed semantic mappings
       P3. Primitive scale groups (`scaleGroups` with `stepsMap`) — raw color palettes
       P4. `fromVisualAnnotations` — last resort, visual layer only
       P5. Never invent values that don't exist in any source

     When P1 (semantic Variables) and P2 (resolvedSemanticColors) conflict:
       - For the SAME role: prefer P1 if the Variable has an explicit semantic path
         (e.g., `bg/color-bg-1` for background is more reliable than a computed
         `bg.default` with confidence 0.5-0.7)
       - For PRIMARY color: P0 > P1 Variables with `brand`/`primary` in path > P2
       - `resolvedSemanticColors` with confidence < 0.7 CANNOT override an explicit
         semantic Variable. It may only create derived variables marked `/* Derived */`.

     DARK MODE FROM VARIABLES:
     When semantic Variables have `{ name, light, dark }` entries:
       - Use `light` value in `:root {}` block
       - Use `dark` value in `.dark {}` block
       - This is MORE authoritative than inferring dark values from scale inversion
         or separate "Dark/*" primitive sets
       - Variables with `{ name, value }` (single value) use the same value in both themes

     Role mapping from Variable name paths (ALIAS LAYER ONLY — applies only when
     generating Layer 2/3 portable aliases; source definition-layer token names are NEVER renamed):
       ***REDACTED***
       - `text/*` or `Text/*` → --foreground, --color-text-* aliases
       - `fill/*` or `Fill/*` → --color-fill-* aliases (surface/container tokens)
       - `border/*` or `line/*` → --border, --color-border-* aliases
       - `brand/*` or `Brand Color/*` or `primary/*` → --primary scale aliases
       - `status/*` or `danger/*` / `success/*` / `warning/*` → semantic status aliases
       - `interactive/*` or `action/*` → --color-link, --color-focus aliases (NOT --primary)
     ⚠️ These mappings produce ALIASES (var(--source-token)) only. The original token
     declarations MUST keep their source names verbatim — never translate or rename them.

     CSS COMMENT PROVENANCE for Variables:
       - When a token value comes from a Figma Variable, add:
         ***REDACTED***
       - When a variable name contains `@ref` suffix, note it:
         `/* Variable: Brand Color/常规 @primary-6 */`

     RESOLVED SEMANTIC COLORS (P2 — supplementary, NOT primary):
     If `resolvedSemanticColors` exists, use it to SUPPLEMENT Variable-derived tokens:
     ***REDACTED***
       with confidence >= 0.7 for core aliases: --primary, --primary-foreground,
       --background, --foreground, --border, --ring, --color-primary,
       --color-surface, --color-border.
     - `confidence < 0.7` cannot drive Layer 2 core aliases; it may only create
       optional derived variables marked `/* Derived */`.
     - If `themeSignals.quality.status` is `fail`, continue in degraded-token mode.
       Use semantic Variables first, then available resolved semantic colors,
       then primitive/spec annotation fallbacks. Mark unresolved critical roles in warnings;
       do not stop token generation only because semantic coverage is incomplete.
     - Role hints (for entries NOT overridden by P1 Variables):
       `brand.primary` → --primary / --color-primary;
       `bg.default` → --background / --color-surface;
       `text.default` → --foreground;
       `border.default` → --border / --color-border;
       `bg.brand`, `text.brand`, `icon.brand`, `border.brand` are exact brand
       semantic slots and must not be overwritten by status/primary.

     Fallback mapping strategy (P3/P4 — when Variables and resolvedSemanticColors are absent or incomplete):
     a. Start with semantic Sets (isSemantic=true) — these contain your bg, text, border, status tokens.
        Use variable name paths to identify CSS roles:
        - `bg/*` or `background/*` → --color-bg-* variables
        - `text/*` or `foreground/*` → --color-text-* variables
        - `border/*` or `outline/*` → --color-border-* variables
        - `brand/*` or `primary/*` → --primary scale
        - `status/*` → success/warning/error semantic colors
        - `interactive/*` or `action/*` → --color-link, --color-focus (NOT --primary)
     b. fromVisualAnnotations: Use description + name to identify role. If description is present, it is authoritative. If brandHints has no primaryScale/primarySample, use names like Primary/* or Brand/* as primary fallback. Convert 8-digit hex (#rrggbbaa) to rgba(r,g,b,a).
     c. themeSignals.unresolvedSummary: Note unresolved count/bySet/sample names — do not invent values for unresolved tokens
     d. For primitive color scales: if `scaleGroups[].stepsMap` exists, use exact values from `stepsMap`; otherwise output ONLY the `sample500` value as a single token. Do NOT generate additional scale stops from a single sample. If a repeated scale has `seeSet`, reuse the referenced Set scale.
  7.1 Brand Primary Color Identification (CRITICAL — overrides colorPalette.primary hint):
     When determining which color is the TRUE brand primary from colors.variableSets:
     a. AUTHORITATIVE brand signals (highest priority):
        - Variables with path containing `bg/brand`, `bg-brand`, `background-brand` → brand fill
        - Variables with path containing `text/brand`, `text-brand` → brand text
        - Variable SCALE named `brand/{hue}/*` (e.g., brand/green/600) → brand hue scale
        If these exist with a saturated chromatic color (saturation > 45%), that IS the brand primary.
     b. INTERACTIVE/STATE signals (NOT brand identity):
        - Variables in `status/primary-*`, `interactive/primary-*`, `action/primary-*` paths
          are UI interaction colors (links, focus rings, selected states) — use for --color-link or
          interactive semantic slots, NOT for --primary brand identity.
     c. FALLBACK: If no explicit brand signals exist, then `*/primary-default` or `*/primary/500` may serve as primary.
     d. Resolution: If colorPalette.primaryHint from brand-input.jsonl conflicts with (a) signals,
        always prefer (a). Add CSS comment: /* brand identity from bg-brand variable */
     e. The `status/primary-*` colors should map to semantic slots like:
        --color-link, --color-interactive, --color-focus (NOT --primary)
     f. SCALE CONFLICT RESOLUTION (when multiple Sets have same-named scales with different hex values):
        - Resolution priority:
          1. Prefer the Variable Set marked `isSemantic: true`
          2. If multiple semantic Sets exist, prefer the one whose name suggests a design system
             (e.g., 'Semantic', 'Theme', 'Token') or that contains bg-brand/text-brand variables
          3. If neither Set has semantic tokens, prefer the one whose 500-step matches
             `themeSignals.brandHints.primaryScale` or `themeSignals.brandHints.primarySample` (exact hex match). If brandHints is empty or only has accentCount, fallback to fromVisualAnnotations names containing Primary/Brand, then brand-input.colorPalette.primaryHint. Do not choose accent over explicit brand-base/brand paths merely because accent appears more often.
          4. Mark chosen scale with CSS comment: /* from Set: "{setName}" */
  7.2 authoritativePrimary (HIGHEST PRIORITY — if present, skip 7.1 entirely):
     If a `_type: "authoritativePrimary"` line exists in design-tokens.jsonl, use it directly:
     - `keyColor` → --primary (the definitive brand primary color)
     - `fullScale` → all --primary-{step} scale stops (output every key-value pair as-is)
     - Do NOT re-derive primary from variableSets, semanticColors, or brandHints.
     - Do NOT second-guess or override this value. It has been pre-computed with scale-aware
       confidence scoring and represents the authoritative brand color decision.
  8. Primary scale: output ALL stops that exist in source data. Do NOT enforce a minimum count —
     if source has only 2 stops, output 2. Never interpolate to fill gaps.
     NOTE: the post-processor caps each color group at 10 tokens (evenly sampled) for the
     Theme panel. The CSS itself still carries ALL source stops. ONLY if the user explicitly
     asked to keep longer scales in the Theme panel, declare `/* @max-group-size: N */` at
     the top of the CSS file to raise the cap.
  9. Neutral scale: output ALL stops that exist in source data. No minimum count requirement.
  10. Semantic colors: success, warning, error, info — output ONLY if present in
     design-tokens.jsonl. If source data has NO status colors, output NONE. Do NOT use
     "standard defaults" or invent colors for missing status roles.
  11. Typography: Use fonts from design-tokens.jsonl typography.fonts. Include @import URL for Google Fonts at top of CSS.
     Use typeScale entries directly for .brand-* utility classes.
     FONT FAMILY FIDELITY (HARD): the number of DISTINCT font families in output MUST equal
     the number of distinct families in typography.fonts. If source has exactly 1 family,
     ALL font-family tokens (--font-heading, --font-body, etc.) MUST reference that single
     family — do NOT invent a serif/display/mono pairing that the designer did not use.
     Never copy multi-font examples from spec files when source has fewer families.
     If `typography.fontsByUsage` exists (keys: heading/body/mono/display), use it to assign font families
     to CSS font-family tokens (e.g., `--font-heading`, `--font-body`, `--font-mono`).
     typeScale entries include fontWeight, lineHeight, and letterSpacing — for EACH typeScale entry, emit
     corresponding CSS custom properties in :root {}:
       `--font-size-{role}: {fontSize}px;`
       `--font-weight-{role}: {fontWeight};`
       `--line-height-{role}: {lineHeight};`
     where {role} is the normalized scale name (e.g., h1, h2, body, caption, display).
     The .brand-* typography utility classes should reference these variables:
       font-weight: var(--font-weight-{role});
       line-height: var(--line-height-{role});
  12. Spacing (NAMING CRITICAL):
    a. Use design-tokens.jsonl spacing.observedValues or commonPaddings/commonGaps as source data.
    b. CSS variable names MUST use `--space-{N}` pattern (e.g., --space-1, --space-2, --space-3).
       NEVER name SPACING tokens --spacing-*, --size-*, or --gap-* — those patterns are NOT
       parsed as spacing. (`--size-*` is reserved for component SIZING tokens — see Rule 14b.)
    c. Map source values to ascending --space-{N} scale (smallest value = --space-1).
       If source has named entries (e.g., "sm", "md"), you may also add semantic aliases
       like `--space-sm: var(--space-1)` but the base --space-N tokens MUST exist.
    d. If source has NO spacing data (observedValues empty AND commonPaddings/commonGaps empty),
       output NOTHING for spacing — do NOT invent a default scale.
    e. COMPLETENESS (HARD): output EVERY deduplicated source value — including half-step /
       "off-grid" values (e.g., 2px, 10px, 14px, 18px for a 4px base = 0.5x/2.5x/3.5x/4.5x).
       Do NOT drop values because they don't fit a clean 4px/8px rhythm. The --space-{N}
       suffix is just an ascending index, NOT a multiplier — N does not need to equal value/4.
       After writing, verify: count of --space-* tokens == count of deduplicated source values.
  13. Radius (STRICT MAPPING — no interpolation allowed):
    a. Read radius.observedValues from design-tokens.jsonl — these are the ONLY source-of-truth values
    b. Map each observedValue to the NEAREST alias slot:
       - If an entry has `isKey: true`, assign it to --radius-md (it is the designer's primary radius)
       - If 1 value exists → assign to --radius-md (medium is default)
       - If 2 values exist → assign smaller to --radius-sm, larger to --radius-xl
       - If 3+ values exist → map by ascending size to sm/md/lg/xl; prefer isKey entry for --radius-md
    c. For unmapped alias slots, leave them empty — do NOT fill with default fallback values.
       Only output radius values that trace directly to source data.
    d. NEVER invent radius values — every non-default value MUST trace to an observedValue entry.
       This includes 0: NEVER add a `--radius-none: 0px` (or any 0 value) unless 0 is
       literally present in radius.observedValues or specAnnotations. Do NOT add
       "convenience" slots (none/full/circle) that the designer did not define.
    e. NEVER round or "improve" source values (if source says 4px, output 4px — not 6px)
    f. If specAnnotations has a "radius" category section, use its named values as PRIMARY (Rule 20c applies)
    g. Use `description` field (when present) for naming context and CSS comments
    h. COMPLETENESS (HARD): output EVERY deduplicated observedValue. If source has more
       values than the sm/md/lg/xl alias slots (e.g., 8 values), use ascending numeric
       names (--radius-1 ... --radius-8) for the full set and add sm/md/lg/xl as aliases
       referencing them. After writing, verify:
       count of distinct radius values output == count of deduplicated observedValues
       (no more — nothing fabricated; no fewer — nothing dropped).
  14. Shadows: Each design-tokens.jsonl shadow has `{ name, x, y, blur, spread, color }`.
    a. Generate CSS as `{x}px {y}px {blur}px {spread}px {color}`.
    b. If a shadow entry has `layers` array (length > 1), each layer is a sub-shadow
       `{ x, y, blur, spread, color }`. Join all layers with comma to form a single
       composite CSS box-shadow value (e.g., `0 2px 4px rgba(...), 0 1px 2px rgba(...)`).
    c. Name shadow variables with numeric suffixes ordered by blur ascending: `--shadow-1`, `--shadow-2`, etc.
    d. Use `description` or `usageHint` field (when present) as an inline CSS comment after the semicolon
       (e.g., `--shadow-2: 0 4px 8px ...; /* Card Hover */`). If neither field exists, infer a short
       usage label from the blur level (e.g., "Subtle", "Card", "Float", "Dialog", "Overlay").
       The `css-to-json.mjs` script uses these comments to produce display keys like `shadow-2·Card Hover`.
    e. COMPLETENESS (HARD): output ONE --shadow-N variable for EVERY entry in shadows[].
       If source has 9 shadows, output exactly 9 — do NOT merge "similar" shadows, do NOT
       trim to a 5-level elevation scale to match spec-file examples (those illustrate
       format, not count). Only true duplicates (identical x/y/blur/spread/color across
       all layers) may be deduplicated.
       After writing, verify

... [Content truncated, total 50,707 chars] ...