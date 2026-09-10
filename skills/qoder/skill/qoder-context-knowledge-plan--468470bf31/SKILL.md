---
name: qoder-context-knowledge-plan
description: Create or update the pre-flight config (.qoder/repowiki/wiki_plan.yaml) that steers wiki and knowledge-card generation — authoring notes, page whitelist, per-page templates and preset wiki templates. Use when the user wants to customize or constrain the wiki / knowledge build, mentions knowledge-plan or wiki_plan.yaml, or asks to pin canonical facts or module boundaries. 用户提到知识规划、定制 wiki 结构、生成或修改 wiki_plan.yaml、干预知识卡生成时使用。
---

# Pre-flight intervention via wiki_plan.yaml

`wiki_plan.yaml` (lives at `<project_root>/.qoder/repowiki/wiki_plan.yaml`) lets
the project author steer the future wiki / knowledge build BEFORE it runs — via
authoring notes, a page whitelist, and per-page templates.

> Path note: `<project_root>` is a placeholder for the absolute path of the
> current project. The path separator inside concrete file operations must
> follow the host OS convention (`/` on macOS/Linux, `\` on Windows). When
> reading or writing the file via native tools, always join the path using the
> platform's native separator. Forward slashes inside the YAML file itself
> (e.g. relative globs in `scope.include`) are fine — YAML consumers normalise
> them across platforms.

## Workflow when activated

1. **Inspect briefly with native file tools (Read/Glob — NOT
   SearchWorkspace/SearchKnowledge)**: list the project root + read README /
   package.json / go.mod / pom.xml / etc. (whichever exist). Run reads in
   parallel. Always build paths with the OS-native separator.

2. **Read existing config first** — read the file at
   `<project_root>/.qoder/repowiki/wiki_plan.yaml` (join with the native path
   separator on the current OS):
   - Not found → create from scratch.
   - Exists & additive intent → preserve all existing fields, append /
     merge only the new entry; prefer surgical edits over full rewrites.
   - Exists & restructure intent → state changes explicitly, then overwrite.
   Never silently drop fields the user did not mention.

3. **Map intent → field**:
   - version pin / canonical fact / forbidden pattern → `repowiki.notes`
     (and usually `knowledgecard.notes` too for cross-pipeline consistency)
   - module split / merge / boundaries → `knowledgecard.notes`
   - required page outline → `repowiki.documents` (whitelist mode)
   - per-page section format → `repowiki.documents[*].template`
   - **preset wiki template (global)** → `repowiki.template` (see below)
   - file range control → **not supported yet**; say so instead of writing a
     `scope` block that would have no effect

4. **Write & summarise** — write (or edit) the file at
   `<project_root>/.qoder/repowiki/wiki_plan.yaml`, again using the OS-native
   path separator. Then tell the user (in their language) which intents map
   to which fields, what changed, and that the file only takes effect after
   the wiki / knowledge build is re-run.

## Schema reference (top-level keys, all optional except version)

```yaml
version: 1                     # always 1
repowiki:
  template: ""                 # OPTIONAL preset template name; one of:
                               #   architecture          — code/architecture analysis
                               #   product_requirement   — product PRD
                               # Empty = no preset (LLM organises freely).
                               # Priority: documents[*].template > repowiki.template
  notes: [{text, author?}]     # strong priors fed into the wiki planner and page bodies
  documents: [{title, goal, parent?, hints?, template?}]
                               # whitelist; sets strict-shape mode for the wiki build
                               # parent=="" = top-level; 1 nesting level only
                               # template = mandatory H2-section skeleton (markdown)
knowledgecard:
  notes: [{text, author?}]     # strong priors fed into knowledge planner
```

Hard caps: repowiki.notes & knowledgecard.notes ≤ 50 entries each;
single note.text ≤ 10000 chars; repowiki.documents ≤ 50 total /
≤ 12 top-level / ≤ 8 children per parent. Anything past a cap is silently
truncated, and an illegal field is dropped — a flawed file degrades, it never
fails the build.

## Not supported yet: `scope`

File-range filtering (`scope.include` / `scope.exclude`) is **not implemented**.
A `scope` block is parsed, reported as a warning, and then ignored. Do not write
one: tell the user file-range control is unavailable in this version instead of
leaving them a config that looks effective but changes nothing.

## Preset template recognition (`repowiki.template`)

When the user references one of these presets (any language, loose wording),
set `repowiki.template` accordingly. Only two values are accepted; matching
notes & section skeletons will be automatically applied in the build's output
language — do NOT duplicate them into `repowiki.notes`.

| Preset | Triggers (zh / en) |
|--------|-------------------|
| `architecture` | 架构 / 架构设计 / 代码架构 / 技术架构 / architecture / code architecture / design doc |
| `product_requirement` | 产品需求 / 需求文档 / 产品文档 / PRD / product requirement / product spec |

Priority: `documents[*].template` > `repowiki.template`. Unknown values are
ignored — if intent is ambiguous, ask instead of guess.

## Authoring rules (concise)

- Notes: 1–2 short sentences each, written as instructions to the LLM.
  Pin facts the LLM cannot infer from code (versions, ownership, canonical
  conventions, forbidden patterns). Skip vague compliments and obvious facts.
- Pages: use sparingly — empty = LLM auto-plans (right default for most
  projects). Each title must map to a real coherent code/doc area.
- Titles & note text in the project's documentation language
  (zh-CN / en-US / …); keys / category ids stay ASCII.

## Guardrails

- Never reference paths you have not verified exist.
- Never put real secrets / tokens / PII into note text.
- Never invent a non-version-1 schema.
- Never write a `scope` block — it has no effect in this version.
- When modifying existing yaml, never silently drop unrelated fields.
- When constructing absolute file paths for read/write operations, always use
  the host OS's native path separator; do not hardcode `/` on Windows.
