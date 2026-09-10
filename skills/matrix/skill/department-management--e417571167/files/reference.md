# Department Management Reference

A conceptual model of departments. `mcp__matrix__department` carries the execution.

## Department Boundary

A department is an owner with a recognizable domain, its own context, decisions, and backlog. Create one when the work falls outside every existing department's responsibility.

Route with `message.send` when an existing department already owns the domain. Use an inbox Task or same-owner worker when the work falls within an existing department's responsibility and only needs a movable next step.

Tasks belong to departments. Workers and subagents are same-owner execution seats inside one department.

## Tool Surface

The Matrix department tool covers every department operation:

- `department.list` and `department.get` for structure inspection.
- `chat.read_recent` and `chat.search` for another department's prior conversation.
- `message.send`, `message.queue`, `message.thread`, and `message.reply` for collaboration loops.
- `department.create`, `department.update`, and `department.delete` from the primary entrypoint.

Other departments propose structural changes via `message.send` to the primary entrypoint. Ordinary retirement or merge uses `department.update` lifecycle plus a structure-change Task; `department.delete` is reserved for explicit physical removal.

## Collaboration Loop

A good cross-department loop has four properties:

- The source department states the desired outcome and relevant context.
- The target department confirms ownership before doing longer work.
- The target department replies with a concrete result, blocker, or refusal.
- The source department continues from that reply instead of leaving the handoff implicit.

## Reading Another Department

When the user refers to a conversation in another department, read before answering. Prefer `chat.read_recent` for fresh context and `chat.search` for older or topic-specific context. Summarize only what is relevant to the user's current ask.

## Structural Taste

- Existing departments stay when ownership is already clear.
- Department messages handle pure collaboration with an existing owner.
- Inbox Tasks handle follow-up under a clear owner; same-owner workers handle parallel execution within one department.
- New owners form when the work falls outside every existing department's responsibility.
