---
name: cola-skill-creator
description: >
  Create new skills from scratch and improve existing skills. Use when users
  want to create a skill, build a custom workflow, write a SKILL.md, design
  a new capability, or say "turn this into a skill". Also triggers on
  questions about skill structure, format, or how to write a good skill.
metadata:
  category: development
---

# Skill Creator

Guide users through creating new skills and iteratively improving them.

## Core Loop

1. Decide what the skill should do and roughly how
2. Write a draft of the skill
3. Test with realistic prompts
4. Improve based on feedback
5. Repeat until satisfied

Figure out where the user is in this process and help them progress. Maybe they want to create from scratch, or they already have a draft and want to iterate.

## Creating a Skill

### Capture Intent

Start by understanding the user's intent. The conversation might already contain a workflow to capture (e.g., "turn this into a skill"). If so, extract answers from context first — tools used, sequence of steps, corrections made, input/output formats observed. The user should confirm before proceeding.

1. What should this skill enable the agent to do?
2. When should this skill trigger? (what user phrases/contexts)
3. What's the expected output format?

### Interview and Research

Proactively ask about edge cases, input/output formats, example files, success criteria, and dependencies.

### Make the skill a project

A skill is something the user maintains over time — they often keep iterating on it and may push it to GitHub. So treat it as a project from the start, rather than scattering files into a scratch path:

1. Decide where the skill's directory will live as a real, maintainable folder — e.g. `~/code/<skill-name>/`, somewhere the user could later turn into a git repo. Ask the user if the location isn't obvious.
2. `project_create` a project named after the skill, with its `workspaceDir` set to that directory. (Run `project_list` first in case one already fits.)
3. Draft and iterate on `SKILL.md` (and any `references/`, `scripts/`) inside that directory — everything written there is owned by this project because it lives under its `workspaceDir`. Keep decisions and progress in the project's `memory.md`.

This keeps the whole skill tracked as one project the user can find and maintain, instead of loose files no project owns.

### Write the SKILL.md

Read [writing-guide.md](./references/writing-guide.md) for design principles and patterns.
Read [skill-spec.md](./references/skill-spec.md) for the full frontmatter specification.

Based on the interview, fill in:

- **name**: Skill identifier (kebab-case, must match directory name)
- **description** (required): The primary triggering mechanism — include both what the skill does AND specific contexts for when to use it. All "when to use" info goes here, not in the body. Lean toward over-triggering; it's easier to narrow later than to debug why a skill never fires.
- **the body**: Imperative instructions, concise, explain why things matter

#### Portability Rule

**Skills must not depend on platform-specific tools.** A well-designed skill should work with any AI agent, not just a particular platform. If a skill requires a tool that only exists in one agent platform (e.g., a proprietary file-upload tool, a platform-specific browser API, a vendor-locked MCP server), it becomes useless everywhere else.

Instead:
- Use standard tools that most agents provide: file read/write, web search/fetch, bash/shell execution
- If a specialized tool is needed, describe the *capability* needed (e.g., "requires web browsing") rather than a specific tool name
- Bundle deterministic logic as scripts in `scripts/` rather than relying on platform-provided tools
- If a skill truly requires a platform-specific capability, document this clearly in the `description` field so users know upfront

#### Description Writing Tips

The description field determines whether the agent ever loads the skill. A poor description means the skill is invisible.

- Start with a one-sentence summary of what the skill does
- Add "Use when..." followed by specific scenarios and keywords
- Cover the user's vocabulary: formal terms, casual phrasing, abbreviations
- Think about what the user would *type*, not just what the skill *does*
- Make descriptions a bit "pushy" — agents tend to under-trigger rather than over-trigger

**Good**: "Extract and transform data from CSV files — handles column mapping, data cleaning, type conversion, and export to JSON or SQLite. Use when working with spreadsheets, tabular data, CSV parsing, data migration, or when the user mentions importing, exporting, or converting data files."

**Bad**: "Helps with CSV files"

#### Skill Structure

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name, description required)
│   └── Markdown instructions
└── Bundled Resources (optional)
    ├── scripts/    - Executable code for deterministic/repetitive tasks
    ├── references/ - Docs loaded into context as needed
    └── assets/     - Files used in output (templates, icons, fonts)
```

#### Progressive Disclosure

Skills use a three-level loading system:
1. **Metadata** (name + description) — always in context (~100 words)
2. **SKILL.md body** — loaded when skill triggers (<500 lines ideal)
3. **Bundled resources** — loaded on demand (unlimited, scripts execute without loading)

Keep SKILL.md under 500 lines; if approaching this limit, extract to references/.

#### Writing Style

Explain *why* things matter rather than piling on rigid MUSTs. Use imperative sentences, keep it concise. If you find yourself writing ALWAYS or NEVER in all caps, step back and explain the reasoning — that's more effective.

### Save Location

Save the skill to the user's skill directory:

```
~/.cola/skills/<skill-name>/SKILL.md
```

If you developed the skill in its own project directory (e.g. `~/code/<skill-name>/`), keep that directory as the source of truth and **symlink** it into the path above so the project stays the place the user maintains and pushes to GitHub:

```
ln -s ~/code/<skill-name> ~/.cola/skills/<skill-name>
```

The SkillWatcher detects changes automatically — the skill will be available in the next conversation turn.

### Validate

- [ ] `name` matches directory name, lowercase `[a-z0-9-]`, max 64 chars
- [ ] `description` is non-empty (required — skill won't load without it), under 1024 chars
- [ ] No dependencies on platform-specific tools
- [ ] All relative path references point to files that exist
- [ ] Body is under 500 lines

---

## Improving a Skill

1. **Generalize from feedback.** Don't overfit to specific examples — if there's a stubborn issue, try different approaches rather than fiddly changes.
2. **Keep the prompt lean.** Remove things that aren't pulling their weight.
3. **Explain the why.** If you find yourself writing ALWAYS or NEVER in all caps, reframe and explain the reasoning.
4. **Look for repeated work.** If the agent keeps writing similar helper scripts, bundle that script in `scripts/`.
5. **Verify portability.** After each revision, check that the skill doesn't introduce dependencies on platform-specific tools.

---

## Reference Files

- `references/skill-spec.md` — Frontmatter specification and validation rules
- `references/writing-guide.md` — Design principles and writing patterns
