# Cola Skill Specification

Technical reference for Cola skill format. Read this when you need exact rules for frontmatter fields, directory structure, or validation behavior.

## Directory Structure

A skill is a directory containing a `SKILL.md` file:

```
skill-name/
├── SKILL.md          # Required — the skill definition
├── scripts/          # Optional — executable code
├── references/       # Optional — docs loaded on demand
└── assets/           # Optional — templates, icons, etc.
```

The directory name becomes the skill's identifier. Always use the subdirectory format (`skill-name/SKILL.md`). Root-level `.md` files placed directly in the skills directory are discovered, but their name falls back to the parent directory name (e.g., `skills`), not the filename — so you must set `name` explicitly in frontmatter for flat files.

## Frontmatter Fields

SKILL.md must begin with YAML frontmatter between `---` delimiters.

### description (required)

The skill's trigger text. The AI sees all skill descriptions in its context and decides which to load based on relevance. If this field is empty or missing, **the skill will not load at all**.

- Max recommended length: 1024 characters (exceeding produces a warning but still loads)
- Must not be empty or whitespace-only

### name (optional)

The skill's identifier. If omitted, derived from the parent directory name.

Validation rules:
- Lowercase letters, digits, and hyphens only: `[a-z0-9-]`
- Max 64 characters
- Cannot start or end with a hyphen
- Cannot contain consecutive hyphens (`--`)
- If provided, should match the parent directory name (mismatch produces a warning)

### disable-model-invocation (optional)

Set to `true` to prevent the AI from automatically invoking this skill. The skill can still be loaded explicitly by the user. Default: `false`.

### Other fields

Any additional YAML keys (e.g., `version`, `tags`, `metadata`) are accepted without error but are not consumed by the SDK. Use them for your own organization if desired.

## Skill Loading Priority

Skills are loaded from multiple sources. When names collide, the first-loaded wins:

1. **User skills** — `~/.cola/skills/`
2. **Global skills** — `~/.cola/resources/skills/`
3. **External skills** — from configured skill paths

This means a user skill with the same name as a global skill will override it.

## How Triggering Works

1. All loaded skills' `name + description` are injected into the AI's context as `<available_skills>` XML
2. When the AI decides a skill is relevant to the user's request, it reads the full SKILL.md body
3. The AI follows the skill's instructions to complete the task

The description is the **only** trigger mechanism. The body content is never seen unless the AI first decides to load the skill based on its description.

## Validation Summary

| Check | Severity | Effect |
|-------|----------|--------|
| description missing/empty | Hard block | Skill not loaded |
| description > 1024 chars | Warning | Still loads |
| name invalid format | Warning | Still loads (uses dir name as fallback) |
| name ≠ directory name | Warning | Still loads |

## Frontmatter Example

```yaml
---
name: data-transformer
description: >
  Transform and convert data between formats — CSV, JSON, SQLite, Excel.
  Handles column mapping, type coercion, filtering, and aggregation.
  Use when working with data migration, format conversion, ETL pipelines,
  or when the user mentions importing, exporting, or reshaping data.
---
```
