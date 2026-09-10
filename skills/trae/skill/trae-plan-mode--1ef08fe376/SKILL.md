---
name: TRAE-plan-mode
description: >
  Research a bounded repository change, write one implementation plan, obtain
  approval, then execute it. Use when repository research or user clarification is
  needed to determine implementation steps and a single plan with one approval
  gate provides enough control. Do not use for complex work requiring persistent
  requirements, acceptance criteria, task queues, or independent review; use Spec
  Mode for the latter.
---

# Plan Mode

Use this preference task skill to plan a bounded change before implementing, then
execute the approved plan.

## Scope

Use Plan Mode when:

- repository research or user clarification is needed to determine implementation
  steps;
- a single implementation plan and one approval gate provide enough control;
- the desired outcome can be covered by one plan.

Use Spec Mode instead when the work needs durable requirement artifacts,
`rule`/`rubric` acceptance criteria, a managed task or remediation queue, or an
independent Review gate.

## Workflow

### 1. Understand

Read the relevant code and documentation to understand the request and current
implementation. Resolve material ambiguity with an available user-input tool
before planning.

For non-edit requests (explain, investigate, analyze, discuss), producing a plan
document and requesting approval are optional — respond directly when
appropriate.

### 2. Plan

Create one implementation plan at:

```text
$(cwd)/.trae/documents/{NAME}_plan.md
```

Use a short, descriptive name and write the plan in the same natural language as
the latest user request. Include:

- repository research conclusions;
- files and modules to change;
- dependency-ordered implementation steps;
- relevant dependencies and considerations;
- validation needed after implementation;
- risks and their handling.

Keep the plan proportional to the task. Do not include development time or
scheduling estimates.

### 3. Approve

After writing the plan, use `NotifyUser` when available to request review and
approval. When `NotifyUser` is unavailable, use another available interaction
mechanism.

Apart from the plan document itself, do not modify files or system state before
explicit approval.

### 4. Implement

After approval, execute the plan and perform its validation. Keep the plan
accurate when approved scope or implementation steps materially change; request
fresh approval before proceeding with a material scope change.

### 5. Respond

Summarize the completed work and validation results.

## Plan Template

```markdown
# [Change Name] Implementation Plan

## Repository Research
[Relevant current behavior, architecture, and constraints]

## Files and Modules
- `[path]`: [expected change]

## Implementation Steps
1. [Dependency-ordered step]

## Dependencies and Considerations
- [Dependency, compatibility concern, or important assumption]

## Validation
- [Test, check, or inspection]

## Risks
- [Risk]: [handling or fallback]
```

## Validation for the Plan Mode Workflow

- Exactly one plan is created before implementation.
- The plan contains research, affected areas, steps, considerations, validation,
  and risks.
- Approval occurs after plan creation and before implementation.
- No implementation state changes occur before approval.
- The workflow does not create Spec Mode artifacts or require an independent
  Review gate.

## Gotchas

- A plan document is an implementation aid, not a requirements specification.
- Do not expand Plan Mode into the Spec Mode artifact and review lifecycle.
