# Skill Writing Guide

Best practices for authoring effective Cola skills. Read this for design principles, writing patterns, and common pitfalls.

## Core Principle: Progressive Disclosure

Skills use a three-level loading system:

1. **Metadata** (description) — always in context, ~100 words. This is all the AI sees when deciding whether to use the skill.
2. **SKILL.md body** — loaded when the skill triggers. Keep under 500 lines.
3. **Bundled resources** — loaded on demand from the body's instructions. No size limit.

Design with this hierarchy in mind. Don't front-load everything into the body — push reference material into `references/` and let the body point to it.

## Writing the Description

The description is the skill's advertisement. The AI reads it alongside dozens of other skill descriptions and picks the most relevant one. Write it like a search result snippet — informative, specific, and action-oriented.

### Pattern: "What + When"

```
[What the skill does in 1-2 sentences]. Use when [scenario 1], [scenario 2],
[scenario 3], or when the user mentions [keyword 1], [keyword 2], [keyword 3].
```

### Good descriptions

- Cover what the skill does AND when to trigger it
- Include specific keywords users would actually type
- Mix formal terms with casual phrasing ("spreadsheet" AND "CSV" AND "tabular data")
- Lean toward over-triggering — a skill that fires too often is tunable; one that never fires is invisible

### Bad descriptions

- Too vague: "Helps with data" — triggers on everything or nothing
- Too narrow: "Converts Q4-2024-sales.csv to JSON" — misses generalization
- Missing trigger cues: only describes what it does, not when to use it
- Keyword-stuffed: a wall of terms with no coherent sentence

## Writing the Body

### Voice and tone

- **Imperative**: "Read the input file" not "You should read the input file"
- **Explain why**: "Use streaming for large files — loading everything into memory will crash on files over 1GB" beats "ALWAYS use streaming for large files"
- **Concise**: challenge every sentence — does the AI actually need this information to do its job?

### Structure

1. **Overview** — one paragraph on what the skill does and the high-level approach
2. **Steps** — the main workflow, in order
3. **Reference pointers** — tell the AI when to read bundled resources
4. **Edge cases** — only the ones that actually come up

### What to avoid

- **Over-specification**: don't dictate every micro-step. The AI is smart — give it the strategy and let it execute.
- **Missing "why"**: if you find yourself writing MUST or NEVER in all caps, step back and explain the reasoning instead. The AI responds better to understanding than to commands.
- **Monolithic body**: if the body exceeds 500 lines, extract reference material into `references/` files and add "Read [file] when you need to [do X]" pointers.

## Bundled Resources

### When to bundle

- A script that multiple invocations would otherwise reinvent (data processing, file conversion)
- A reference document that's too large for the body (API spec, architecture guide)
- An output template that must be pixel-perfect (HTML email, report format)

### When NOT to bundle

- The skill is simple enough to fit in one SKILL.md
- The "resource" is just a few lines of example code (inline it)
- The resource changes frequently (point to an external URL instead)

### Organization

```
references/   → docs the AI reads into context on demand
scripts/      → code the AI executes (not read into context)
assets/       → files used in output (templates, images)
```

Reference files over 300 lines should include a table of contents at the top.

## Design Patterns

### Domain variants

When a skill supports multiple frameworks or platforms, organize by variant:

```
cloud-deploy/
├── SKILL.md          # Workflow + how to pick the right variant
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

The body explains how to choose; the AI reads only the relevant reference.

### Output format definition

When the skill must produce a specific format:

```markdown
## Report Structure

Use this template exactly:

# [Title]
## Executive Summary
[2-3 sentence overview]
## Key Findings
[Bulleted list]
## Recommendations
[Numbered action items]
```

### Example-driven skills

When showing the AI how to transform input to output:

```markdown
## Commit Message Format

**Example 1:**
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication

**Example 2:**
Input: Fixed crash when uploading files larger than 10MB
Output: fix(upload): handle large file uploads without OOM
```

## Common Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Wall of MUSTs | AI ignores or over-indexes on rigid rules | Explain the reasoning, let the AI generalize |
| Description says "helps with X" | Too vague to trigger reliably | Add specific scenarios and keywords |
| 800-line SKILL.md | Floods context, dilutes key instructions | Extract to references/, keep body focused |
| No examples | AI guesses at the expected format | Add 2-3 concrete input/output pairs |
| Hardcoded paths/names | Skill breaks in other environments | Use relative paths and placeholders |
