# Design Project Validation Flow

This document describes all design project validation flows and script usage within the solo-design skill.

## Validation Responsibilities

| Level | Executor | Script | Trigger Timing | Purpose |
|------|--------|------|---------|------|
| **HTML self-check** | **Page Sub-Agent** | Does not run design project validation scripts | After HTML write is complete | Executes `delivery-quality/page-rendering-quality-gate.md`, then reports artifact path, nodeId, component reads, and quality gate status to Main Agent |
| **Full validation** | **Main Agent** | `validate-design-workspace.mjs` | After all sub-tasks complete, before presenting results to user | Confirms all artifacts (directory structure, HTML, assets, theme infrastructure, .design) are correct |

> **Page Sub-Agents must not run design project validation scripts**: `validate-design-workspace.mjs` traverses the entire design directory. When executed concurrently, other pages' HTML has not yet been generated, which triggers numerous false positives. `validate-design-file-format.mjs` validates shared `.design` metadata owned by the Main Agent. After completing HTML generation, Page Sub-Agents perform local HTML style integrity self-checks and report directly to the Main Agent.

> **Concurrent write deadlock note**: When multiple Sub-Agents run in parallel, if each attempts to fix the same .design file, concurrent write conflicts (deadlocks) occur. Therefore, .design file repair responsibility is unified under the Main Agent; Sub-Agents only fix their own HTML output files.

## Sub-Agent: Report Directly After Completion

After writing HTML, the Page Sub-Agent **does not run design project validation scripts** and reports the following information directly to the Main Agent:

```json
{
  "nodeId": "<nodeId assigned during pre-registration>",
  "page": "pages/<page-name>.html",
  "title": "<page title>",
  "domIds": ["<data-dom-id values added in HTML>"],
  "componentsRead": ["<component slugs read from componentPlan>"],
  "extraComponentsRead": ["<bounded supplement component slugs>"],
  "aestheticsRead": ["index.md"],
  "aestheticsSkipped": [],
  "nestingDepthCheck": { "status": "pass", "maxLayersFound": 2, "samplePaths": ["section > card > content"] },
  "qualityGate": "passed"
}
```

The Main Agent collects all Sub-Agent reports (including `domIds` for wiring checklist construction) and then performs unified full validation. If the Main Agent finds HTML errors, it dispatches repair tasks to the corresponding Sub-Agent.

## Generation Intermediate State (Step 2 → Step 3)

**Definition**: After Step 2 (Main Agent pre-registers page skeleton nodes) completes, until Step 3 (all Sub-Agents finish HTML generation) ends, the `.design` file is in an intermediate state:

- `.design` already contains skeleton nodes for all pages (nodeId, htmlSrc, title, etc. are pre-allocated)
- HTML files in the `pages/` directory have not yet been generated

**Validation restrictions during this period:**

| Script | Allowed to Run | Notes |
|------|------------|------|
| `validate-design-workspace.mjs` | **Forbidden** | HTML file existence checks will batch-report expected intermediate errors, producing heavy noise and making it impossible to distinguish expected intermediate state from real errors |
| `validate-design-file-format.mjs` | **Forbidden** | This script is an internal dependency of `validate-design-workspace.mjs`; running it directly creates a second validation path and can trigger incorrect repair actions during partial generation |

During intermediate state, the Main Agent may only perform lightweight inspection: read the `.design` JSON, confirm skeleton node IDs / `htmlSrc` / `canvasData.group` values, and avoid running any Skill validation script.

> Missing HTML during intermediate state is **expected behavior** and does not indicate `.design` pre-registration failure. Only after Step 3 is entirely complete and all HTML has been generated should full validation pass.

**Typical error scenario**: If `validate-design-workspace.mjs` is run during intermediate state, the script will report all page HTML as missing. The Agent may incorrectly judge Step 2 as failed and rewrite `.design`, causing pre-registered skeleton nodes to be overwritten. **Running any scan-result-based repair actions during intermediate state is forbidden.**

## Main Agent: Full Validation (validate-design-workspace.mjs)

After all sub-tasks complete, the Main Agent must execute a one-time complete validation:

```bash
node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-design-workspace.mjs <design-directory-path> [--expected-pages=<N>] [--require-interactions=domId1:file1.html,domId2:file2.html,...] [--report-json=<path>]
```

For create/add-page HTML workflows, use the fixed completion command shape below. `--report-json` is not optional for completion:

```bash
node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-design-workspace.mjs <design-project-path> \
  --expected-pages=<N> \
  --require-interactions=<domId1>:<pageFile1>,<domId2>:<pageFile2> \
  --report-json=<design-project-path>/validation-report.json
```

If there is no planned wiring, omit `--require-interactions` and record that no visible/hidden interaction checklist exists. Do not fabricate placeholder domIds.

**Parameter description:**
- `<design-directory-path>`: Design project root directory path (required)
- `--expected-pages=<N>`: Expected total number of pages (optional; if provided, automatically passed to `.design` file validation)
- `--require-interactions=domId:file.html,...`: Expected wiring checklist (optional; forwarded to `validate-design-file-format.mjs` to verify each domId exists in the owning HTML file and is registered in `.design` interactions)
- `--report-json=<path>`: Machine-readable validation evidence file. The final response may claim completion only when this report exists and has `success: true`.

**Functionality:**
- Checks directory structure (assets/, pages/)
- Discovers and validates all .design files (internally auto-invokes validate-design-file-format.mjs and forwards `--expected-pages` / `--require-interactions`)
- Validates HTML file completeness in the pages/ directory
- Validates HTML infrastructure (`theme-vars`, `@theme inline`, Tailwind, Lucide, theme class)
- Blocks forbidden HTML quality issues: hardcoded colors outside `theme-vars`, Tailwind named color utilities, external/base64 images, missing `../assets/` image paths, missing image files, and brand CSS `<link>` usage
- Optionally validates .theme files if theme/ directory exists (non-blocking)
- Checks asset directory status
- Generates a complete validation report on stdout and, when `--report-json` is passed, writes `{ success, skillProvenance, operatingMode, renderBlockingErrorCount, softWarningCount, renderBlockingErrors, softWarnings, repairPlanHints, repairActionTable, errorCount, warningCount, errors, warnings, projectFileHashes, designDir, expectedPages, requireInteractions, checkedAt }` to that JSON file. `projectFileHashes` is produced by `validate-design-workspace.mjs` and is the baseline used by `validate-finish-readiness.mjs` to detect post-validation artifact mutations; the Agent must not recalculate or hand-copy it. `skillProvenance` is copied from `runtime-orchestration-summary.json.skillProvenance` when available; otherwise the report falls back to `skill-release-manifest.json` and records the fallback reason. `repairPlanHints` and `repairActionTable` are the first source for post-validation repair strategy; if they tell the Main Agent to run a deterministic script once or return to a preflight gate, do not replace that with manual Grep/SearchReplace.

**Mode-specific repair semantics:**
- Free-explore fast path repairs only render-blocking errors (`renderBlockingErrorCount > 0`). Soft warnings are recorded but must not trigger visual/token repair loops.
- Library-bound strict path keeps token, component, UI Kit, and Library identity violations blocking. Do not downgrade these to free-mode soft warnings.

**Validation decision table:**

| Condition | Next action |
| --- | --- |
| `success === true` and `renderBlockingErrorCount === 0` | Enter the finish gate |
| `success === true`, `renderBlockingErrorCount === 0`, and `softWarningCount > 0` in free-explore/layout-static mode | Record the warnings and stop repairing |
| `success === false` or `renderBlockingErrorCount > 0` | Read the repair workflow declared by the selected `INTENT_WORKFLOW.md`, repair by owner, and re-run the final scan once |
| Any project file changed after the report was written | Re-run the final scan before final response |

This table must not trigger extra scans by itself; it only decides what to do with the validation result already produced.

## Validation Run Discipline

HTML/page workflows must write `runtime-orchestration-summary.json.project.validationRunDiscipline` before final validation:

```json
{
  "maxFullValidationRuns": 2,
  "softWarningsTriggerRepair": false,
  "blockingRepairMode": "targeted-once",
  "forbiddenRepairTriggers": ["soft-warning-only", "provenance-warning-only", "style-warning-only"]
}
```

Rules:
- One full validation is allowed after generation.
- If blocking errors exist, one owner-scoped targeted repair and one revalidation are allowed.
- Soft warnings alone must not trigger LLM repair.
- `validate-design-workspace.mjs` reports `validationRunDisciplineStatus`; discipline violations are blocking.
- If revalidation still fails, stop and report the remaining blocking errors or reduced-scope decision.

`build-page-dispatch-manifest.mjs` enforces `validationRunDiscipline` at preflight. If preflight reports a missing validation run discipline, write the object into `runtime-orchestration-summary.json.project.validationRunDiscipline` and re-run preflight.

**Exit codes:**
- `0`: Validation passed
- `1`: Validation failed; must fix based on error information and re-validate

Before any repair after exit code `1`, the Main Agent must read the selected lane's declared repair workflow if it has not already done so in this repair phase. The next action after a failed validation must not be Grep/Read against validator source, full HTML, or `apply-html-head-contract.mjs` source.

When `validation-report.json.repairPlanHints[]` is present, repair must follow the matching hint before any source exploration. For `mobile-navigation-consistency`, the expected strategy is `run_repair_mobile_navigation_once`; if it has already been attempted or still fails after the final scan, stop and report blocking errors.

When `validation-report.json.repairActionTable[]` is present, use it before reading source files. The table maps each blocking error to one `errorClass`, required action, owner, and source-read policy:

| `errorClass` | Required action | Forbidden action |
| --- | --- | --- |
| `head-infrastructure` | Run `apply-html-head-contract.mjs --replace-head` once on affected files | Reading validator source or hand-writing `<head>` infrastructure |
| `dispatch-preflight-or-ownership` | Return to dispatch preflight and rebuild packet / manifest evidence | Patching `dispatchPreflightManifest` after generation |
| `restore-source-authority-or-checkpoint` | Repair only the affected source authority or checkpoint evidence | Reinterpreting visual authority from browser/URL after lock |
| `repair-ledger` | Append repair entry evidence and revalidation report path | Continuing validation without repair ledger |
| `artifact-readiness` | Repair `.design`, file references, asset registration, or interaction target only | Editing visual page content after validation passed |
| `visual-checkpoint` | Repair only the failed checkpoint | Subjective broad polishing |

If `repairPlanHints[]` and `repairActionTable[]` both exist, choose the narrower deterministic action. If the action table says to return to preflight, stop page repair and rerun the owning preflight phase.

### Validation Repair State Machine

After a failed full validation, follow this fixed sequence:

1. Run `record-validation-repair-entry.mjs --phase=start` on the failed `validation-report.json`.
2. Read the selected lane's declared repair workflow.
3. For each owner-scoped repair action, run `record-validation-repair-entry.mjs --phase=action` using the matching `repairActionTable[].errorClass`, pre/post file hashes, and repair-owned field list.
4. Apply one owner-scoped batch repair. Main Agent repairs `.design`, summary, and `<head>` infrastructure; Sub-Agents repair only assigned HTML body issues.
5. Re-run full validation once with `--report-json`.
6. Run `record-validation-repair-entry.mjs --phase=revalidate` with the new validation report. If revalidation still fails because of non-ledger artifact/render/schema errors, pass `--blocked-reason=<reason>` and stop. If the report contains only `repair-ledger` errors, treat it as ledger diagnostic evidence: run the script once with `--blocked-reason=repair-ledger-diagnostic`, then run `validate-finish-readiness.mjs <design-project-path> --check=repair-ledger`. Do not start another full validation, do not read validator source, and do not hand-edit `validationHistory[]`, `validationRepairLedger[]`, or `repairEntryEvidence[]`.

Before step 1 is recorded, these actions are forbidden: editing files, reading full HTML files, reading validator source, reading deterministic script source, starting browser preview, creating helper scripts, or launching additional Sub-Agents.

After every validation run with `--report-json`, append a compact record to `runtime-orchestration-summary.json.project.validationHistory[]`:

```json
{
  "reportPath": "validation-report.json",
  "checkedAt": "2026-07-08T00:00:00.000Z",
  "success": false,
  "exitCode": 1,
  "renderBlockingErrorCount": 2,
  "repairPlanHints": ["mobile-navigation-consistency"]
}
```

If a validation record has `success=false` or `exitCode=1`, run this command before making any repair:

```bash
node {SKILL_DIR}/shared-runtime/deterministic-tooling/record-validation-repair-entry.mjs \
  <design-project-path> \
  --phase=start \
  --failed-report=<design-project-path>/validation-report.json
```

Record the selected action before editing:

```bash
node {SKILL_DIR}/shared-runtime/deterministic-tooling/record-validation-repair-entry.mjs \
  <design-project-path> \
  --phase=action \
  --failed-report=<design-project-path>/validation-report.json \
  --owner=main-agent \
  --error-class=<repairActionTable.errorClass> \
  --action=<deterministic-action-name> \
  --affected-files=<comma-separated-relative-paths>
```

After the batch repair and one revalidation run, record the revalidation report:

```bash
node {SKILL_DIR}/shared-runtime/deterministic-tooling/record-validation-repair-entry.mjs \
  <design-project-path> \
  --phase=revalidate \
  --revalidation-report=<design-project-path>/validation-report.json
```

The script appends lightweight `project.validationRepairLedger[]`, `project.repairEntryEvidence[]`, `repairActions[]`, script-owned file hash evidence, `revalidationReportPath`, `revalidationReportHash`, and `revalidationSuccess`. Do not hand-edit these fields and do not calculate hashes manually.

```json
{
  "failedReportPath": "validation-report.json",
  "repairWorkflowReadPath": "intent-workflows/intent-project-mutation/main-agent-repair-workflow.md",
  "repairPlanHints": ["mobile-navigation-consistency"],
  "ownerTriage": [
    {"owner": "main-agent", "errorClass": "head-infrastructure", "affectedFiles": ["pages/index.html"]}
  ],
  "repairActions": [
    {"owner": "main-agent", "action": "run apply-html-head-contract", "status": "done"}
  ],
  "revalidationReportPath": "validation-report.json",
  "revalidationReportHash": "sha256",
  "revalidationSuccess": true
}
```

`validate-finish-readiness.mjs` fails when `validationHistory[]` contains a failed validation and the matching repair ledger is missing or incomplete. A complete ledger has non-empty `repairActions[]`, `revalidationReportPath`, `failedReportHash`, and `revalidationReportHash`, and the hashes must match the report files on disk. It also verifies Design artifact readiness: page/image registration, page/asset file existence, interaction target integrity, validation success, and post-validation mutation. It does not validate the assistant's final natural-language response format.

If validation would require more than 3 repair ledger entries, do not continue open-ended repair. Either stop as blocked, or use the controlled incomplete path:

```json
{
  "repairStopConditionMet": true,
  "repairStopReason": "short reason based on the last validation report",
  "remainingBlockingIssues": ["blocking issue still present"],
  "lastValidationReportPath": "validation-report.json"
}
```

The controlled incomplete path is accepted only when the evidence above is recorded in `runtime-orchestration-summary.json.project`.

**Validation evidence contract:**

```json
{
  "validationEvidence": {
    "command": "node {SKILL_DIR}/shared-runtime/deterministic-tooling/validate-design-workspace.mjs <design-directory-path> --report-json=<designProjectPath>/validation-report.json",
    "reportJsonPath": "{designProjectPath}/validation-report.json",
    "exitCode": 0,
    "skillProvenance": {
      "name": "solo-design",
      "version": "2026.07.06.8",
      "version_source": "skill-release-manifest.json",
      "read_status": "ok"
    },
    "stdoutSummary": "Validation Passed / All checks passed",
    "renderBlockingErrorCount": 0,
    "softWarningCount": 0,
    "errorCount": 0,
    "warningCount": 0,
    "repairRounds": 0
  }
}
```

If validation evidence or the report JSON is missing, the task is incomplete even if all files exist.

### Validation Is Non-Substitutable

`validate-design-workspace.mjs --report-json=<designProjectPath>/validation-report.json` cannot be replaced by:

- Grep/Read checks
- browser screenshots or manual visual preview
- `apply-html-head-contract.mjs` stdout
- a natural-language claim that validation passed
- checking only `.design` JSON manually

For create/add-page HTML workflows, completion requires both command evidence and a report JSON whose latest contents record `success: true`.

### Post-validation Mutation Rule

After a successful validation report is produced, do not modify project files before final response. If any HTML, asset, `.design`, CSS, summary, or interaction file is changed after validation, run the full final scan again and update `validation-report.json`.

### Restore 1:1 Evidence Gate

Before full validation in `intentProfile.caseFamily === "restore_1to1"`, the Main Agent must have persisted restore evidence in `runtime-orchestration-summary.json`:

- `project.referenceCaptureEvidence` exists.
- `project.restoreVisualCheckpoints` contains at least 8 rows and at least 5 high priority rows.
- URL-only restore has non-empty `referenceCaptureEvidence.fullPageScreenshotEvidence`.
- High/medium `sourceRegionCoverage` rows are `mapped` or `intentionally-deviated`; none may remain `unmapped`.
- Every restored page has `pages[].restoreEvidence.visualCheckpointResults`.
- `pages[].restoreEvidence.dominantReferenceImageUsedAsBody === false`.
- `project.restoreEvidenceReview` exists before final delivery and records `allHighPriorityCheckpointsAcceptable === true`.
- `project.restoreEvidenceReview.highPriorityMissingCount === 0`.
- `project.restoreEvidenceReview.highPriorityPartialWithoutDeviationCount === 0`.
- `project.visualDiffReview` exists before final delivery and records `blockingMismatchCount === 0` and `allBlockingMismatchesResolved === true`.

Legacy `replicationEvidence` may appear in older completion reports, but new restore dispatches use `RestorePagePacket` and `restoreEvidence`. If capture evidence or checkpoint evidence is missing, stop as blocked instead of continuing as free-explore, same-domain redesign, or image-only graphic delivery. Do not take additional screenshots only to satisfy this gate; use the mandatory capture already performed by `delivery-quality/reference-material-ingestion-rules.md`.

If these conditions fail, repair the evidence or page before running final validation; `validate-design-workspace.mjs` proves renderability plus restore evidence completeness, not pixel similarity. High-fidelity similarity is reviewed through `project.restoreEvidenceReview`, which inspects the persisted checkpoint results and allowed deviations. It must not trigger screenshot or browser preview by default; preview follows the selected lane's declared repair workflow only.

## Repair Flow

When validation fails, the Main Agent must **triage errors by owner** before dispatching any repair:

### Error Triage Table

| Error Category | Example Errors | Owner | Repair Method |
|---------------|----------------|-------|---------------|
| **`<head>` infrastructure** | Missing Tailwind CDN, missing `<style id="theme-vars">`, missing `@theme inline`, missing `@layer base`, missing `<html class="light/dark">` | **Main Agent** | Run `apply-html-head-contract.mjs <css-path> <html-file> --replace-head` — this regenerates the entire `<head>` without touching `<main>` content |
| **`<body>` script** | Missing `lucide.createIcons()` | **Sub-Agent** | Dispatch targeted repair: add `<script>lucide.createIcons();</script>` before `</body>` |
| **Custom `<style>` in `<head>`** | Custom style blocks detected in `<head>` | **Main Agent** | Run `apply-html-head-contract.mjs --replace-head` — it automatically relocates custom styles to `<body>` end |
| **Hardcoded colors** | `#f5a623`, `rgb(246, 81, 89)` found outside `theme-vars` | **Sub-Agent** | Dispatch targeted repair: replace hardcoded values with `var(--prefix-*)` tokens using Edit tool |
| **Tailwind named colors** | `bg-blue-500`, `text-red-600` | **Sub-Agent** | Dispatch targeted repair: replace with brand semantic classes |
| **`.design` metadata** | Missing nodes, wrong nodeId, interaction errors | **Main Agent** | Fix `.design` JSON directly |
| **Missing HTML files** | `pages/about.html` not found | **Sub-Agent** | Re-dispatch page generation Sub-Agent |
| **CSS semantic aliases** | `apply-html-head-contract.mjs` reports missing mappings such as `foreground`, `card`, `primary`, or `muted` | **Main Agent** | Add the required `--{brandPrefix}-*` semantic aliases to `colors_and_type.css` before retrying the head command |

### Repair Procedure

1. **Triage**: Classify each error using the table above
2. **Main Agent fixes first**: Execute `apply-html-head-contract.mjs --replace-head` for all HTML files with `<head>` infrastructure errors — this is a single batch command that fixes multiple files at once:
   ```bash
   node {SKILL_DIR}/shared-runtime/deterministic-tooling/apply-html-head-contract.mjs <css-path> page1.html page2.html ... --replace-head
   ```
3. **Then dispatch Sub-Agent repairs**: For `<main>` content issues (hardcoded colors, Tailwind named colors, missing lucide init), dispatch Sub-Agent(s) with targeted Edit instructions — **not full-file rewrites**
4. **Re-validate**: Run `validate-design-workspace.mjs` again
5. Repeat steps 2–4 until validation passes

**[FORBIDDEN]** Delegating `<head>` infrastructure repair to Sub-Agents — this causes Sub-Agents to rewrite entire HTML files, destroying content and creating a cycle of re-validation failures.

## Common Omission Patterns

| Omission Pattern | Consequence | Prevention |
|-----------------|-------------|------------|
| Generated HTML but `.design` nodes missing | Canvas blank | Main Agent must pre-register page skeleton nodes before dispatching Sub-Agents |
| `data` is empty array `[]` | Canvas blank | Validation script will catch |
| `.design` registered a file but file was not created | White screen / SDK error | Validation script will catch |
| Used `metadata` instead of `devMetadata` | SDK cannot recognize | Validation script will catch |
| Parallel Sub-Agent writes causing overwrites | Page loss | Only Main Agent writes `.design`; pass `--expected-pages` during gate validation to detect |
| Skipped image pre-generation, page Sub-Agent generates images on its own | Slow, inconsistent image style | Must complete image pre-generation phase before page generation; page Sub-Agents are forbidden from calling image generation tools on their own |
| Sub-Agent fills interactions on its own | Wiring points to wrong page or is missing | Sub-Agent keeps `interactions` as empty array `[]`; Main Agent registers wiring in atomic Step 3.5b |
