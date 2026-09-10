---
name: solo-design
description: Design website pages, UI screens, prototypes, page-level visual systems, and existing `.design` project mutations. Use for websites, landing pages, UI prototypes, redesigns, theme changes, 1:1 restoration, editable static layouts, and complex canvas projects. Route bitmap image edits to solo-image-edit, bitmap-first poster/banner/KV/cover generation to solo-graphic-generation, and reusable Design Library / Design System / token architecture creation to design-library-creator.
---

# Solo Design

This Skill uses a **decision -> load -> preflight -> dispatch -> validate -> readiness** routing chain. `SKILL.md` only classifies the request, writes the resolved lane into working notes / summary when a project exists, and loads exactly one `intent-workflows/<selected>/INTENT_WORKFLOW.md`.

Do not scan all workflow folders. After a lane is selected, read only that lane's `INTENT_WORKFLOW.md` and the files declared in its `Context Requirements`. Before any dispatch, the selected lane's declared context files must be recorded with body-read evidence in `runtime-orchestration-summary.json.project.contextRequirementsLoaded[]`.

## Top-Level Skill Handoffs

Evaluate these handoffs in order before `Route Priority` and before reading any intent workflow.

Immediately invoke the `Skill` tool with `name: "solo-image-edit"` and stop applying this Skill when either condition matches:

1. Current-turn context contains an image-region annotation whose parsed payload type is `design-image-annotation`. Match this semantically across available envelopes such as a `web-element` record or a `selected_browser_item`; do not require one exact wrapper or field layout.
2. The user explicitly asks to edit, retouch, remove, replace, recolor, restyle, extend, or otherwise change pixels in an existing bitmap image, and an original image is available as a local file or current-turn attachment.

The structured `design-image-annotation` marker is authoritative even when the visible user text is only a short instruction such as "按评论改一下" or only names the selected `image-region`. Do not route ordinary HTML/DOM/CSS/page-component edits merely because the page contains images. Do not route text-to-image creation without an original bitmap; keep those requests in the graphic lanes below.

After the image-edit handoff does not match, immediately invoke the `Skill` tool with `name: "solo-graphic-generation"` and stop applying this Skill when the generated bitmap itself is the deliverable: poster, banner, KV/key visual, cover, invitation, social card, illustration, portrait, product image, transparent-background asset, cutout, or an image batch without editable HTML requirements.

The graphic-generation handoff also applies when the user asks to generate and append a new image asset to an existing canvas. `solo-graphic-generation` owns the required pre-generation size confirmation, image generation, canvas registration, and image-only validation. Keep text-critical static layouts in this Skill when exact readable/editable copy, DOM typography, tables, schedules, prices, legal copy, PPT, one-pager, or manual/document structure is required.

## Global Invariants

- Output is canvas-first: every produced page or kept image asset must be represented in the `.design` file.
- `.design` validity is blocking: valid JSON, non-empty `data`, existing `devMetadata.htmlSrc` / `imageSrc`, unique node ids, and registered image assets.
- Explicit user instructions win for design direction and optional process choices, but cannot override canvas validity, rendering correctness, safety, or required validation gates.
- Existing page/project changes create a new comparison page by default. In-place edit is allowed only when the user explicitly asks to overwrite, replace, or modify in place.
- New dispatches must never target `shared-runtime/blocked-legacy-entrypoints/blocked-legacy-page-template.md`.
- `shared-runtime/agent-dispatch-runtime/shared-page-rendering-kernel.md` is a Declared Load only; it is not an Always Load file.
- `visual-experience/` and `delivery-quality/` are loaded only when the selected `INTENT_WORKFLOW.md` declares them.
- Flow-control rules are model-agnostic. Do not add model-specific branches, model names, or per-model instructions to this Skill.
- Production visual stability is a generation-time gate for layout-risk pages. Page Sub-Agents must build layout-critical structure with responsive-safe static CSS in the page, not rely only on Tailwind browser runtime compilation, late validation, or repair passes. If first-screen frame, density, overflow, or overlap checks cannot pass during generation, return `qualityGate: "failed|blocked"` instead of producing a low-fidelity page for later repair.

## Route Priority

After no top-level handoff matches, evaluate from P1 to P9 and stop at the first match.

| Priority | Condition | `resolvedLane` | Load |
| --- | --- | --- | --- |
| P1 | Existing project/page/selection edit, add state, add comparison page, navigation add, delete/adopt/refresh operation | `existing_edit_add_comparison` | `intent-workflows/intent-project-mutation/INTENT_WORKFLOW.md` |
| P2 | Redesign duplicate project or convert an existing project to another device/view | `redesign_duplicate_project` | `intent-workflows/intent-project-mutation/INTENT_WORKFLOW.md` |
| P3 | Generate variants, alternatives, multi-scheme comparison for existing pages | `variants_multi_scheme` | `intent-workflows/intent-project-mutation/INTENT_WORKFLOW.md` |
| P4 | Project-wide theme, token, color, typography, or head refresh customization | `theme_customize` | `intent-workflows/intent-project-mutation/INTENT_WORKFLOW.md` |
| P5 | Explicit 1:1, clone, replicate, pixel-perfect, exact restoration, or restore eval metadata | `restore_1to1` | `intent-workflows/intent-page-restore-1to1/INTENT_WORKFLOW.md` |
| P6 | Active Design Library identity, Library path, `componentPlan`, or `actualTokenNameReference` | `library_bound` | `intent-workflows/intent-page-library-bound/INTENT_WORKFLOW.md` |
| P7 | `graphicStrategyGate = "layout-static"`: long copy, PPT/one-pager/manual, exact editable text, table/schedule/legal/brand copy | `graphic_layout_static` | `intent-workflows/intent-project-complex-build/INTENT_WORKFLOW.md` |
| P8 | Long PRD, multi-page or multi-device project, generation tree, complex interaction/state expansion, fragment mode | `complex_html_page` | `intent-workflows/intent-project-complex-build/INTENT_WORKFLOW.md` |
| P9 | No Library, no restore target, open-ended page/UI/site/app creation | `free_exploration` | `intent-workflows/intent-page-free-exploration/INTENT_WORKFLOW.md` |

Conflict rule: earlier priorities win. Example: explicit restore wins over active Library; existing project mutation wins over new-project creation unless the user explicitly asks for a separate new project.

## Dispatch Discipline

- Main Agent owns routing, `.design` writes, image-node registration, interaction registration, and validation.
- Before any dispatch, Main Agent must record a Step 0 lane gate in `runtime-orchestration-summary.json.project`: `resolvedLane`, `selectedIntentWorkflowRead: true`, `contextRequirementsLoaded[]`, `contextReadScope`, `validationRunDiscipline`, and `lowValueCallWatchdog`. Each `contextRequirementsLoaded[]` row must include `{ path, readStatus: "loaded", bodyRead: true }`. If this evidence cannot be written, do not dispatch.
- Page Sub-Agents consume only the selected lane page runtime guide, the selected lane dispatch contract, and the packet fields provided by Main Agent.
- Page Sub-Agents do not write `.design`, run project validators, start preview servers, create helper scripts, or generate images.
- Page Sub-Agent packets must include `allowedWritePaths[]`; completions must report `changedFiles[]`. The Main Agent owns `.design`, `runtime-orchestration-summary.json`, validation reports, readiness evidence, and final delivery text.
- Cross-lane collaboration uses `runtime-orchestration-summary.json`, `dispatchPreflightManifest[]`, and `sourceProjectLaneHeritage`; do not make one intent workflow read another intent workflow's runbook.
- `supplementaryReads[]` entries must be explicit `{ path, reason, ownerLane }`. Free lane may keep `implementationEscalationReason` only as a compatibility alias.
- Restore dispatches must lock `project.sourceAuthorityLock` before page generation. Screenshot/user-provided imagery is visual authority when present; URL/browser evidence may supplement content but must not override the locked visual authority.
- Static graphic / layout-heavy page dispatches must write `project.visualQualityCheckpoints[]` before generation. These checkpoints lock visual anchor, information hierarchy, composition structure, and implementation strategy without adding open-ended exploration.
- Layout-risk page dispatches must include a compact production stability target: target device/frame, viewport mode, first-screen content regions, responsive breakpoints, and high-risk compression/overlap risks. Page Sub-Agents must report `staticRenderingEvidence` and `viewportIntegrityEvidence`; missing evidence blocks that layout-risk dispatch before project validation.
- Long reasoning without tool calls, artifact diffs, or structured decisions must follow `project.lowValueCallWatchdog.noProgressNextAction` and move to readiness or a minimal blocked summary; do not continue thinking loops.

## Allowed Scripts

Only Skill-provided deterministic scripts below are allowed during execution or maintenance:

| Script | Caller | When |
| --- | --- | --- |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/apply-html-head-contract.mjs` | Page Sub-Agent / Main Agent fallback | Generate or replace approved HTML `<head>` |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-restore-contract.mjs` | Main Agent | Restore-only pre-dispatch contract gate; validates source identity, page state, measured facts, region groups, CSS aliases, and packet readiness |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-design-workspace.mjs` | Main Agent | Final validation for HTML/page projects |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/record-validation-repair-entry.mjs` | Main Agent | Required first action after a failed `validate-design-workspace.mjs` report; records lightweight script-owned repair evidence. Do not hand-write hashes or validation history |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/record-dispatch-completion.mjs` | Main Agent | Records Page Sub-Agent completion evidence into `expectedDispatches[]` and main-agent mutation evidence. Do not hand-edit dispatch completion JSON |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-finish-readiness.mjs` | Main Agent | Design artifact readiness gate after `validation-report.json success=true`; run `--check=all` for final delivery; checks validation report integrity, `.design` registration, page/image paths, interactions, post-validation mutation, and restore final-response text policy when provided |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-design-file-format.mjs` | Internal only | Called by workspace validation |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-lane-runtime-contract.mjs` | Main Agent / maintainer | Lane contract preflight and audit |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/build-page-dispatch-manifest.mjs` | Main Agent | Build page dispatch preflight manifest for page-dispatch lanes |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/repair-mobile-navigation-flow.mjs` | Main Agent | One-time repair after mobile navigation validation issue |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/check-intent-workflow-boundaries.mjs` | Maintainer | Validate lane isolation and declared visual-quality loading |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/check-skill-runtime-read-scope.mjs` | Maintainer | Validate agent-readable runbook file-size and read-scope limits |
| `node {SKILL_DIR}/shared-runtime/deterministic-tooling/check-solo-design-contract-regressions.mjs` | Maintainer | Run fixture-based regressions for dispatch, repair ledger, version, and readiness contract failures |

## Out-Of-Scope Routing

- Pixel-level edits of an existing bitmap, including structured Design image comments, go to `solo-image-edit`.
- Bitmap-first poster/banner/KV/cover/card/illustration/image-batch generation goes to `solo-graphic-generation`.
- Professional reusable Design Library / Design System / token architecture creation goes to `design-library-creator`.
- Legacy runtime templates are blocked. If any dispatch packet or task query names `blocked-legacy-page-template.md`, stop and re-route to the lane-owned page runtime guide.
- `create-design-system` style requests inside page creation are treated as page styling requirements only; they must not self-create a reusable Design Library.

## Completion Gate

Before final delivery, run the validation required by the selected `INTENT_WORKFLOW.md`. For **restore_1to1 workflows**, skip `validate-design-workspace.mjs` entirely and proceed directly to `validate-finish-readiness.mjs <designProjectPath> --check=all --final-response-file=<draft.md>`; ensure the draft is link-free and path-free. For **other HTML/page workflows**, after `validate-design-workspace.mjs --report-json=<designProjectPath>/validation-report.json` succeeds, run `validate-finish-readiness.mjs <designProjectPath> --check=all` as the Design artifact readiness gate. Do not claim completion while validation has blocking errors, artifact readiness fails, validation report integrity fails, or restore final-response text policy fails.

If `validate-design-workspace.mjs` reports only repair-ledger metadata warnings, do not rerun full validation or inspect validator source. Repair-ledger metadata is diagnostic; continue only when `validation-report.json success=true` and `validate-finish-readiness.mjs <designProjectPath> --check=all` passes. If `validation-report.json.terminalState` is present, stop and report the blocking summary instead of starting another repair loop.
