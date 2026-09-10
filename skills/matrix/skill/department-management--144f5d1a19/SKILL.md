---
name: department-management
description: Use for department CRUD and cross-department coordination: create/update/retire/merge/delete owners, inspect department ownership, route work to an existing owner, send or reply to department messages, or read another department's prior chat context.
category: coordination
symbolName: building.2.crop.circle
seedVersion: 19
---

# Department Management

A decision policy for ownership and cross-department coordination. `mcp__matrix__department` carries the execution; this skill chooses what to call.

## First Principles

- A department is an owner with its own context, responsibilities, and backlog.
- Tasks belong to departments. Agents/subagents are same-owner execution seats inside one department.
- Cross-owner work goes through department messages: ask clearly, let the recipient resolve it, continue from the reply with outcome.
- Department CRUD lives with the primary entrypoint; non-primary departments propose structure changes via `message.send`.
- The workspace topology is already in the prompt; reach for `department.list` or `department.get` when the prompt context is insufficient.
- File structure follows ownership: workspace-level shape and the primary department's own root sit at workspace level; each non-primary department owns its own root; tool-managed state stays behind tools.

## Decision Ladder

One question decides ownership: does the work fall within an existing department's responsibility?

1. If yes, route with `message.send` to that owner.
2. If no, create the smallest set of owners now; one clear ask is enough.
3. Vague ambition becomes a Task under whichever owner is responsible.

Owners retire via `department.update` lifecycle `retired` once their work ends — project complete, pattern faded, or another owner now covers the domain. Retirement is a cleanup move on past work, not a precondition for creating an owner today.

Each structural change leaves an execution fact: create or update a structure-change Task with storage kind `org_change`, owned by the primary entrypoint, recording why the change is justified, what proof supports it, and what routing memory or initial brief closes the loop.

## After Creating

Routing memory is a primary-entrypoint belief card at `memory/knowledge/routing-*.md` with `tag: self` and `confidence: H`. Write or update it before or immediately after the initial `message.send`; the body must state the routing condition, target department, what the primary entrypoint keeps local, and what context to include.

Name departments for user workflows and responsibilities, not tools, file formats, or implementation details.

## Tool Interface

Use `mcp__matrix__department` for all department operations.

All departments may use:

- `department.list` and `department.get` to inspect departments and their metadata.
- `chat.read_recent` and `chat.search` to read another department's prior conversation.
- `message.send` to dispatch new work — request, review, answer, or workflow continuation. Use the message body and attachments; the action itself opens the work, so it carries no `outcome`.
- `message.queue` and `message.thread` to inspect pending or historical department messages.
- `message.reply` `kind: "reply"` with `outcome` (`completed | failed | cancelled`) to close work received via `message.send`.
- `message.reply` `kind: "note"` to add silent context to an existing thread; for action, use `message.send`.

The primary entrypoint department may also use:

- `department.create` when the decision ladder calls for a new owner.
- `department.update` to change name, description, parent, or posture.
- `department.update` lifecycle `retired` or `merged` when an owner's work has ended and its history still matters.
- `department.delete` for hard deletion after explicit confirmation; ordinary endings use the `retired` or `merged` lifecycle.

Non-primary departments propose structure changes through `message.send` to the primary entrypoint with the reason, proposed boundary, and expected ownership.

When user instructions to multiple departments conflict on the same artifact, customer promise, or decision, surface the exact conflict to the primary entrypoint. Keep local work to cheap reversible inspection until the decision lands, then continue with the smallest aligned proof step or name the blocker.

## Common Moves

When the user asks another department to act:

1. Identify the target department from the workspace topology or `department.list`.
2. When the ask depends on prior conversation, use `chat.read_recent` or `chat.search` first.
3. `message.send` carries a concrete message, the expected deliverable, and any relevant context (file paths in `attachments` when they matter).
4. Receiving a message: trust the delivery, inspect context if needed, then do the work.
5. `message.reply` `kind: "reply"` with `outcome` closes the work; keep the body short.

When the user asks about something they discussed with another department:

1. `chat.read_recent` reads that department's recent context.
2. `chat.search` reaches further back by meaning, title, or topic.
3. Answer from the retrieved context, separating retrieved facts from inference.

When the user asks to create a department:

1. Apply the decision ladder.
2. The primary entrypoint calls `department.create` with the minimal owner boundary: name, description, optional parent, optional profile.
3. Other departments send the proposal to the primary entrypoint with `message.send`.

## Taste Rules

- One precise tool call beats a long explanation of internals.
- User-facing output stays in operating language: who owns the work, what context was read, what was requested, what happens next.
- Internal layout, message routing, lifecycle state, and scaffolding stay implementation details unless the user explicitly asks.
- Seed a new department only with what the user gave you or what the boundary actually needs; placeholder Key Results, memory, or process text obscure real ownership.

## Reference

Read [reference.md](reference.md) for conceptual boundary checks; it is a model description, not an execution recipe.
