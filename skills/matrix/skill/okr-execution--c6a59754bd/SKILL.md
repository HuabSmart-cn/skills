---
name: okr-execution
description: "Use to track and prove work you own: open a Task and set its done-criteria, attach proof and check it in, schedule a reminder / deadline / recurring check, or close an OKR loop (an active Objective with no first Key Result, or an active Key Result with no movable next Task). Trigger: \"I own this and it needs a durable owner, proof, and a next move.\" This is the persistent OKR Task system via mcp__okr__state (task.upsert / task.check_in) — NOT the session-scratch TaskCreate/TaskList/TodoWrite built-in tools, which vanish when the session ends. To hand work to another department or reply to one, use department-management instead."
category: coordination
symbolName: checkmark.seal
seedVersion: 39
---

# OKR Execution

Objective sets direction. Key Result makes progress observable. Task is the owned work. Criteria say what would count as done. Trigger wakes the work. Proof supports the Check-in. Check-in records status, judgment, next action, KR decision, and learning decision. Learning changes future behavior. Dashboard is a projection.

Resolve the right owner first; scaffold the Task under that owner.

## Two different "tasks" — do not confuse them

This skill governs the **OKR Task**: a durable, owned unit written through `mcp__okr__state` (`task.upsert` / `task.check_in`), persisted under the department's `tasks/`, carrying owner, Criteria, Proof, and Check-ins. It survives across sessions and is what the Dashboard and wakes are built from.

The built-in `TaskCreate` / `TaskGet` / `TaskUpdate` / `TaskList` / `TodoWrite` tools are a **session-scratch todo list** — in-memory, gone when the session ends, with no owner, proof, or Check-in. They are fine for organizing your own multi-step thinking inside one turn, but they are **not** OKR Tasks.

Rule: anything that must be owned, proven, tracked across sessions, or reflected on the Dashboard goes through `mcp__okr__state`. Never let a `TaskCreate` scratch item stand in for an OKR Task — that produces a "ghost task" that looks done but vanishes with the session.

## Concept Application
- Objective: direction, priority, tradeoff, ownership, or horizon.
- Key Result: a judgeable result — numeric, milestone, rubric, or state-based; its owner carries status, health, risk, proof, learning, and next action.
- Task: owned work. Link both `objectiveId` and `keyResultId` when it advances OKR progress; omit both for inbox work.
- Criteria: the smallest gates that would make completion truthful.
- Proof: concrete refs — files, URLs, screenshots, task outputs, tests, messages, reports.
- Check-in: a record written after proof, blocker, failure, cancellation, or meaningful progress; it states who judged what, based on what, and what happens next.
- KR/Learning decision: linked Task Check-ins accept/modify/reject the KR suggestion; learning-bearing Check-ins choose `ignore`, `proof-only`, `memory-card`, `skill-update`, or `next-task`.
- User-facing copy translates to direction, result, task, done check, proof, status, or owner unless the user asks how the system works.

## Use
Apply this skill whenever an operating loop needs an owner, criteria, trigger, proof, and Check-in: future work, follow-up, deadline, monitoring loop, department-message work, proof awaiting Check-in, active Objective without a first Key Result, or active Key Result without a movable next Task.

A one-off ask you can satisfy now and that leaves no follow-up does NOT need the Task loop — even when it takes several tool calls or a fanned-out worker run; just do the work and reply. The Task loop is for work worth tracking past this turn: a durable owner, proof awaiting a Check-in, or something you or the user will revisit or audit later. Match the mechanism to the work's shape — the Operating Action Model lays out the full ladder (do-it-now → worker → department → OKR); this skill is the OKR/Task rung. When work does earn a loop, size it to the real work.

## Rules

- Skill owns judgment. Workspace tools own storage, scheduling, derived views, and safety boundaries.
- A Task carries owner, next action, wake path, criteria, and proof expectation. When any are missing, fill them or keep the work in-session until they exist.
- Mark `completed` only when every criterion is `satisfied`.
- Two similar user actions in the same domain are enough to propose or create an owner when it removes repeated setup.
- Time triggers are deterministic wakeups for an existing Task; create the Task first, then attach the schedule.
- Objective page form edits are user confirmation: treat them as accepted direction, then create or adjust the smallest first Key Result and proof-bearing Task. Other Objective meaning changes still need explicit user confirmation.
- Tasks are owned by departments, not by Agents/subagents. Agents may produce proof; department Leads check in proof, learning, and linked Key Result state. Inbox Tasks may start without `objectiveId` or `keyResultId`; link both before they count as OKR progress.
- Any execution result tied to a Task lands as a proof ref (file path, URL, screenshot, task output, message, report) or as a blocker recorded in `nextAction`, Criteria notes, or Key Result blockers — that is what closes the loop.
- Placeholder values (`TBD`, bracketed text, empty owners, "pending partner input", draft-only assumptions) count as blockers, never proof, unless the Criteria explicitly asked for a blank template.
- Load-bearing business facts (caps, impacts, contract dates, approvals, owner names) come from the user, an attached source, a tool result, or a responsible department reply. When they are missing and Criteria need them, ask one brief factual question or mark the item blocked; bundle related facts in one ask.
- When an existing department owns the domain facts, ask that department before Check-in and attach the reply with outcome as proof.
- Before naming a department owner, verify it exists in the current workspace. Route the Task to the existing department whose responsibility covers it; if none does, form the new owner first and scaffold under it.
- For criteria with an external timing constraint, complete only the due slice; preparation for later slices is useful work but does not satisfy their Criteria. When no timing constraint exists, keep advancing until proof, Check-in, or blocker.
- Parallelism splits independent proof-bearing slices: department messages cross owners, Agents/subagents work inside one owner.
- Background task completion notifications with output files are proof refs; check in the linked Task against the output path, or create the smallest next Task when none exists.
- Department message replies with outcome and attachments are proof for the sender or owner to check in the related Task.
- Department-structure changes are Tasks: use a structure-change Task with storage kind `org_change` for creating, retiring, merging, renaming, or reshaping departments or skills.
- Use `mcp__okr__state` for Objective, Key Result, Task, Criteria, Proof, and Check-in facts; `mcp__matrix__department` is reserved for department messages, chat reads, and department CRUD.
- `task.upsert` creates or revises an open packet. `task.check_in` closes a packet to `blocked`, `completed`, `failed`, or `cancelled` with author, judgment, proof, and next action; blocked/failed Check-ins also carry `blockerCategory`.
- `blockerCategory` is one of: `user_input_missing`, `department_waiting`, `external_system_failure`, `permission_or_credential`, `business_blocker`.
- Linked Task Check-ins carry `keyResultDecision`: `accept` applies the automatic KR suggestion, `modify` requires `keyResultState`, `reject` requires a clear judgment. Learning-bearing Check-ins carry `learningDecision`: `ignore`, `proof-only`, `memory-card`, `skill-update`, or `next-task`. For `memory-card` and `skill-update`, write the destination file first and include the path in `learningRefs`.
- When this skill loads against an execution loop that still lacks Tasks, the next move changes or verifies state, or names a concrete blocker.

## State Shape

Operating loops live as state. Start with the smallest living loop: Objective, Key Result, owner, Task, trigger, Check-in, and learning. The primary entrypoint keeps workspace direction. The owning department keeps its Key Result direction. Supporting owner departments keep execution bounded with next action, context, proof, and learning destination.

When you record Objective or Key Result state, use `mcp__okr__state` and the required shape exactly. The derived dashboard and nudge logic read only this shape:

- Workspace `okr.json` contains Objectives only. Required Objective fields: `objectiveId`, `title`, `ownerDepartmentId`, `summary`, `status`, `timeHorizon`. Status: `draft | active | blocked | completed | cancelled`.
- A department `okr.json` contains only the Key Results owned by that department. Required Key Result fields: `keyResultId`, `objectiveId`, `ownerDepartmentId`, `title`, `targetState`, `status`, `priority`. Optional execution fields include `health`, `progress`, `confidence`, `blockers`, `nextAction`, `proofRefs`, and `learningRefs`. Status: `draft | active | at_risk | blocked | completed | cancelled`. Priority: `low | normal | high`.
- A Key Result's `ownerDepartmentId` matches the department store it is written to; child-owned Key Results live in the child's store, never the parent's. Workspace Objective records hold Objectives only.
- Use only the listed field names and states; malformed records are ignored.

## Task Packet

Tasks are recorded through `mcp__okr__state`; Task packets live under the owning department's `tasks/` directory:

```yaml
---
taskId: task-first-loop
kind: local
status: scheduled
title: Run the first operating loop
objectiveId: objective-operating-system
keyResultId: keyResult-first-loop
ownerDepartmentId: owner
priority: high
createdAt: 2026-04-30T00:00:00.000Z
updatedAt: 2026-04-30T00:00:00.000Z
---
```

OKR-linked Task packets carry both `objectiveId` and `keyResultId`. Inbox Task packets omit both until the owner links them. Use `taskId` as the durable Task identity.
Required body sections:
- `## Brief` - action and why it matters.
- `## Trigger` - JSON `manual`, `time`, or `department_message`.
- `## Criteria` - smallest checkable completion conditions.
- `## Context Refs` - only execution-relevant context.
- `## Next Action` - next concrete move.
- `## Proof Refs` and `## Learning Refs` - empty until real refs exist.
- `## Check-ins` - persisted by the state tool with author, judgment, status, proof, learning, next action, KR decision, and learning decision.

## Proof-Bearing Execution

Tools do work; Check-ins judge work. A Task closes when a Check-in records proof or a real blocker.

After execution tied to a Task, collect concrete refs — output paths, URLs, screenshots, message ids, worker activity ids, report paths — attach them to the Task and Criteria, then check in. On each satisfied Criteria item, set `proofRefs`, e.g. `{id, text, status: "satisfied", proofRefs: ["file://deliverables/report.md"]}`. When reality blocks completion, record the blocker in `nextAction`, Criteria notes, or Key Result blockers.

## Trigger Discipline

- `manual`: user or owning department explicitly starts the Task.
- `time`: work must wake at a specific date/time or cadence. For time wakeups, use cron only after a Task exists; bind it to the Task's `taskId`, optional `keyResultId`, `purpose`, and `sourceRefs`.
- `department_message`: department messages and cross-department work.

External events and dependencies are conditions; record them in context, next action, or `sourceRefs`. When they need execution, convert them into a `manual`, `time`, or `department_message` trigger on a real Task.

Schedule a wake only against an existing Task: select or create the Task, then attach the schedule.

## Criteria, Verification, Check-in

Criteria are the Codex-Key Result lesson absorbed into the Check-in loop: `objective -> requirements -> proof -> audit -> complete`, without adding a second Key Result system.

Use the smallest useful checklist:

```md
## Criteria

- [open] A1: Deliver the reminder to the user at or after the due time.
- [open] A2: Attach the delivered message as proof.
```
Statuses: `open`, `satisfied`, `blocked`, `not_applicable`.

Timing is Criteria only when reality makes it part of completion. A repeated Task is complete for the slice whose criteria can be truthfully proven now; preparation may create drafts or queues, but it does not complete future slices. When no external timing constraint exists, continuation should keep going.

If criteria have a verifier such as a test, script, checklist, visual diff, browser proof, metric, or reviewer reply, run the verifier loop: inspect the actual state, change the narrowest mutable surface, run or check the verifier, attach the result as proof, keep improving until satisfied, blocked, out of budget, or stopped by a real timing boundary.

When proof arrives:

1. Attach proof refs: files, messages, diffs, screenshots, reports, external URLs, or department messages replies.
2. Set `check_in_pending` if proof exists but no conclusion has been made.
3. Mark Criteria items `satisfied`, `blocked`, or `not_applicable`.
4. Write a Check-in with `authorDepartmentId`, one-line `judgment`, `status`, `nextAction`, `proofRefs`, and any learning refs.
5. If the Task is linked, the state tool creates a KR state suggestion. Choose `keyResultDecision: "accept"` to apply it, `"modify"` with `keyResultState` when the suggestion is wrong or incomplete, or `"reject"` with a clear judgment when the KR should not change.
6. If blocked, failed, cancelled, or directionally wrong, record proof and the smallest viable change: split, reroute, change owner, adjust criteria, or create an alternative Task.
7. Decide the next Task. An active Key Result without a movable Task is a Task gap.
8. Decide learning explicitly: `ignore`, `proof-only`, `memory-card`, `skill-update`, or `next-task`. If choosing `memory-card` or `skill-update`, write the destination file first and include that path in `learningRefs`.

## OKR, Dashboard, Nudge

- Key Result execution state can update from proof without asking when it reflects reality.
- Key Result title, target state, owner, deadline, or priority can change when the user asks or proof makes old wording false; explain the change.
- Dashboard is a projection; change source facts and let it refresh from them.
- After a Check-in changes user-facing measures, sharpen the source facts first; the dashboard follows.
- Dashboard Task list and periodic wake share the same operating ref order; treat listed refs as the wake reason.
- Each wake ref carries owner, route, and stop condition. Act through that route until the stop condition holds.
Reason order:

1. `due_time_trigger`: execute next action, attach proof, then update or propose the next Task.
2. `blocked_task`: remove, route, or report the smallest real blocker.
3. `proof_check_in_pending`: check proof against criteria, update linked Key Result state when present, decide learning.
4. `active_task`: keep advancing the next action until proof, Check-in, or blocker.
5. `active_key_result_missing_task`: create or restore the smallest movable proof-bearing Task.
6. `active_objective_missing_first_key_result`: create or propose the smallest first Key Result, then create or attach the smallest proof-bearing Task.
