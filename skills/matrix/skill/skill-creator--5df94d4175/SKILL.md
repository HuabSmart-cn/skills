---
name: skill-creator
description: Create, edit, and improve workspace skills. Use when the user wants to capture a repeatable workflow, add a new skill, refine an existing skill, or turn an in-conversation procedure into a reusable skill.
category: development
symbolName: hammer.fill
seedVersion: 3
---

# Skill Creator

Skills are reusable workflows the agent can invoke for recurring tasks.
Each skill lives at `skills/<name>/SKILL.md` (workspace-level) or
`departments/<id>/skills/<name>/SKILL.md` (department-level).

## When to Make a Skill

Convert work into a skill when **all** of these hold:

- The same procedure is likely to recur many times across sessions
- It has a clear trigger (the situation that should make the agent invoke it)
- It has a clear output (what "done" looks like)
- The procedure is too involved to expect the agent to rediscover each time

If any of those is missing, prefer a one-off task or a memory note.

## Anatomy of a Skill

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter (name + description required)
│   └── Markdown body — instructions, rules, examples
└── (optional)
    ├── scripts/    — executable helpers
    ├── references/ — documentation loaded on demand
    └── assets/     — templates, fixtures
```

## Required Frontmatter

```yaml
---
name: my-skill                # kebab-case, matches directory name
description: One sentence saying WHAT it does and WHEN to use it.
                              # This is the only thing the agent sees
                              # when deciding whether to invoke the skill.
                              # Be concrete, mention trigger phrases.
category: coordination | development | automation | analysis | ...
symbolName: hammer.fill       # SF Symbol name, used by the app UI
seedVersion: 1                # bump when the body changes meaningfully
---
```

The **description** field is the load-bearing part — it determines
whether the agent invokes the skill at all. Include both:
- WHAT the skill does (verb + object)
- WHEN to trigger (concrete user phrases or contexts)

Example: `Translate Figma designs into production-ready code with 1:1
visual fidelity. Use when implementing UI from Figma files, when the
user mentions "implement design", or provides Figma URLs.`

## Body Style

- **Imperative voice** ("Read the file", not "the file should be read")
- **Explain the WHY** — give the agent enough context to handle edge
  cases, rather than only enumerating steps
- **Concrete examples** beat abstract descriptions; show input/output
  pairs where possible
- **Keep it under ~500 lines**; if longer, split bundled material into
  `references/` and load only when needed
- **Avoid heavy-handed `MUST`/`NEVER`** unless safety-critical — the
  agent reads instructions better when given reasoning

## Workflow for Creating a New Skill

1. **Capture intent** — confirm with the user: what should the skill do?
   When should it trigger? What's the expected output?
2. **Pick the scope** — workspace-level (used across departments) vs
   department-level (specific to one team's domain).
3. **Draft `SKILL.md`** with frontmatter + body following the patterns above.
4. **Try it on a real example** — the user gives a representative task,
   the agent invokes the skill, you both inspect the output.
5. **Refine based on what went wrong** — was the trigger right? Did the
   body's instructions cover the edge case? Was the output format
   useful?
6. **Iterate 1-3 rounds** until the skill produces what the user wants.

## Workflow for Improving an Existing Skill

1. **Identify the symptom** — does the skill under-trigger, over-trigger,
   produce wrong output, or take too long?
2. **For under-trigger / over-trigger** → fix the description's wording
   and example phrases.
3. **For wrong output** → fix the body's instructions, especially the
   "Why" / context that helps the agent generalize.
4. **For too long** → look for repeated work the skill could pre-script
   or pre-bundle in `scripts/`.
5. **Bump `seedVersion`** in frontmatter so any consuming systems know
   the body has materially changed.

## Common Pitfalls

- **Description too vague**: "Help with documents" → triggers at random.
  Concrete: "Convert markdown notes into formatted .docx with consistent
  heading styles."
- **Body too prescriptive**: 50 numbered steps the agent must follow.
  Better: 3 phases with reasoning, leaving the agent room to handle edge
  cases.
- **Skill that competes with itself**: two skills with overlapping
  triggers confuse the routing. Either merge them or make their
  descriptions explicitly distinct.
- **Bundled scripts that don't exist**: if the SKILL.md tells the agent
  to run `python -m scripts.foo`, make sure `scripts/foo.py` is in the
  skill directory.

## Reference Slot

If the skill involves a domain with multiple variants (e.g.,
`cloud-deploy/` for AWS / GCP / Azure), put the per-variant detail in
`references/<variant>.md` and have `SKILL.md` route to the right one.
The agent reads only the relevant reference, keeping context lean.

## Criteria

A skill is ready when:

- The description triggers it on the right kinds of prompts (and not on
  unrelated ones)
- The body produces the expected output without the user having to
  steer it mid-flight
- The user runs it on 2-3 fresh real tasks and is satisfied with each
- The frontmatter is complete and `seedVersion` is set

That's the whole loop. Heavy quantitative evaluation infrastructure
(automated A/B benchmarking, eval viewers, optimization loops) is
available in the standalone Anthropic skill-creator project, not part
of this Neo workspace seed — most workspace skills do not need it. Add
it only if a skill turns out to need quantitative tuning over many
runs.
