---
name: "skill-creator"
description: "MANDATORY tool for creating SKILLs - MUST be invoked IMMEDIATELY when user wants to create/add any skill"
user-invocable: true
---

# Skill Creator

This skill helps you create new SKILLs for the workspace.

## When to Use

**CRITICAL: You MUST invoke this skill IMMEDIATELY as your FIRST action when:**
- User wants to create a new skill
- User wants to add a custom skill to the workspace
- User asks to set up a skill template
- User asks "how to create a skill"
- User mentions creating/adding/making any skill

**DO NOT:**
- Just explain how to create a skill without invoking this tool
- Provide manual instructions without calling this skill first
- Defer the skill creation to later steps

## SKILL Structure

A valid SKILL requires:

1. **Directory**: `.trae/skills/<skill-name>/`
2. **File**: `SKILL.md` inside the directory

## SKILL.md Format

```markdown
---
name: "<skill-name>"
description: "<concise description covering: (1) what the skill does, (2) when to invoke it. Keep it under 200 characters for best display>"
---

# <Skill Title>

<Detailed instructions, usage guidelines, and examples>
```

## Required Fields

| Field | Location | Description |
|-------|----------|-------------|
| `name` | frontmatter | Unique identifier for the skill |
| `description` | frontmatter | **CRITICAL**: Must include (1) what the skill does AND (2) when to invoke it. This helps the model decide when to use the skill. Keep under 200 chars. |
| `detail` | body | Full markdown content after frontmatter |

## Privacy and Data Handling

When creating or updating a SKILL, keep the content reusable and free of sensitive or task-specific data.

**DO NOT include:**
- User private information, credentials, tokens, cookies, internal URLs, or access details
- Raw user data, dataset samples, evaluation results, experiment outputs, logs, or query results
- One-off task progress, temporary file paths, command outputs, or analysis conclusions that are not reusable instructions

Use sanitized examples and generic placeholders instead. A SKILL should capture durable workflow instructions, trigger conditions, reusable conventions, and safe examples only.

## Creation Steps

1. Ask user for skill name and purpose
2. **IMPORTANT**: When generating the `description` field, ALWAYS include:
   - What the skill does (functionality)
   - **MUST emphasize when to invoke it** (trigger conditions/scenarios)
   - Example format: "Does X. Invoke when Y happens or user asks for Z."
   - **Language**: Use English by default unless user specifies another language
3. Ensure the SKILL content does not contain sensitive information or task-specific data results
4. Create directory: `.trae/skills/<skill-name>/`
5. Create `SKILL.md` with proper frontmatter and content
6. Validate the structure is correct

## Example

To create a "code-reviewer" skill:

```bash
mkdir -p .trae/skills/code-reviewer
```

Then create `.trae/skills/code-reviewer/SKILL.md`:

```markdown
---
name: "code-reviewer"
description: "Reviews code for best practices, bugs, and improvements. Invoke when user asks for code review or before merging changes."
---

# Code Reviewer

This skill reviews code and provides feedback...
```