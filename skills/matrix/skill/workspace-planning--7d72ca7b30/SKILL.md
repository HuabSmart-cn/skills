---
name: workspace-planning
description: "Use at the start of a broad, vague, or multi-part request, before any execution, to decide its shape: what the Objective is, which departments own which parts, and what to fan out to owners vs keep for yourself. Triggers: ongoing-help language (manage / watch / improve / keep track of / take care of), a goal with no clear owner yet, or work spanning several owners. This skill decides the plan only — once owners are clear, use department-management to create owners and dispatch via message.send, and okr-execution to track each owned piece with proof."
category: workspace
symbolName: point.3.connected.trianglepath.dotted
seedVersion: 14
---

# Workspace Planning

A working aid for the primary department: turn loose intent into a shape the workspace can run today and continue tomorrow.

## Two Layers

- Workspace shape: Objectives, departments, routing, shared resources, handoffs.
- Department execution: Key Results, Tasks, Criteria, Proof, Check-ins, learning, memory, artifacts.

Change the workspace map when the work falls outside every existing department's responsibility; otherwise route to the responsible owner. Use `department-management`, `okr-execution`, and `mcp__okr__state` for the mechanics.

## Decision Order

1. Read the intent in the user's language: what they said, what repetition or ambition implies, what outcome would help.
2. Resolve ownership: route to the existing department whose responsibility covers it, or form the new owner the work needs.
3. Move first: take the concrete step, write the OKR fact, or send the handoff in this turn.
4. Close the loop: leave proof, a movable next action, or a real blocker.

If one part of the ask is clear and another part is vague, move the clear part now and ask one precise question for the vague part.

Continuity language ("manage", "watch", "improve", "keep track of", "take care of") usually signals ongoing ownership, not a one-off answer.

## State Discipline

Operating structure lives as state through `mcp__okr__state`:

- Workspace Objectives carry `objectiveId`, `title`, `ownerDepartmentId`, `summary`, `status`, `timeHorizon`.
- Department Key Results carry `keyResultId`, `objectiveId`, `ownerDepartmentId`, `title`, `targetState`, `status`, `priority`, and live in the owning department's store.
- Key Result statuses: `draft`, `active`, `at_risk`, `blocked`, `completed`, `cancelled`. Priorities: `low`, `normal`, `high`.
- Narrative belongs in Objective summaries, dashboard prose, or workspace/department memory, not in a separate root markdown file.
- Every operating loop ends with at least one proof-bearing Task or a real blocker.

The Objective page form is user-confirmed direction. Objective meaning changes and recurring user-facing triggers need explicit user confirmation; drafting the first Objective for an ask that has none is not a meaning change.

## Human Output

Speak in the user's words. Describe the lived effect — what will be watched, remembered, handed off, or continued — and the immediate move you took.

For broad intent, reply with a plain read, the first concrete move, and at most one question.

When you have just created structure, name it briefly so the user can confirm direction. Mention an owner only when ownership matters; mention trigger, proof, or learning only when relevant.

## Receipts

After applying changes, the reply names what changed, what remains pending, and what will wake or continue next.
