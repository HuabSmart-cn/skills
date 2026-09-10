---
name: skill-cleanup
description: >
  Trim the user's enabled skills down to the ones they actually use, or turn a
  specific skill off or back on. Use when the user asks to clean up / trim /
  reduce their skills, says they have too many skills enabled, asks which skills
  they never use, or names one and asks to close, disable, hide, enable, or
  restore it ("关掉 xx skill", "精简一下技能", "把 xx 打开"). Also use when the
  user takes up the "Trim for me" prompt, whether it appeared over the installed
  skills list or in chat.
metadata:
  category: system
---

# Skill Cleanup

## Tools

`inspect_skill_cleanup` and `apply_skill_cleanup` are deferred. Retrieve them
first, then call `inspect_skill_cleanup`; both carry their own reporting and
apply guidelines.

```
tool_search("select:inspect_skill_cleanup,apply_skill_cleanup")
```

`apply_skill_cleanup` is the only supported way to close a skill. Never rename,
move or delete anything under the skill directories, and never edit
`skills.json` by hand.

## Judging

Usage numbers come from the tool. Never guess them.

**Zero use is the close case.** Keeping a never-invoked skill costs a concrete
reason about that skill — a task in this user's recent work it would have
served, or a capability nothing else covers. "They are an engineer, so this
engineering skill is core" is not a reason to keep; it restates who they are and
matches half the catalogue. Profile belongs to step two below — choosing among
skills the usage cut already shortlisted — never to get one in. On its own it is
a reason to ask, which is what ② is for.

An invocation is the floor, not the test. Core is reached in three steps:

1. **Cut by usage** — take the head of the distribution, not every skill with a
   count above zero.
2. **Narrow by profile** — of those, which are actually this user's working set.
3. **Pull in what pairs** — skills from that same shortlist that belong to the
   same suite as one you kept, or carry the other half of its workflow.

Everything invoked that does not survive the three steps goes to ①: a few
scattered calls that never became a workflow is exactly what this cleanup is
for. Only the handful you are genuinely torn about go to ②, along with
low-frequency but critical work you can name (release, hotfix, recovery).

## Boundaries

- Before writing a single line, count what you put in ② and ③. **If the total is
  above 50, you kept too much**: go back, take the lowest-usage entries, move
  them into ① and count again. Repeat until ②+③ is 50 or fewer; 30–50 is where
  a real cleanup lands. This is not optional and it is not a judgement call.
- Do all of that silently. The count, the range, and the fact that you adjusted
  anything never appear in your answer — do not cite them, do not mention
  working to a size.
- Present the list, then **stop**. Do not apply until the user confirms.
- Turning a skill back on is not a cleanup and needs no confirmation.
