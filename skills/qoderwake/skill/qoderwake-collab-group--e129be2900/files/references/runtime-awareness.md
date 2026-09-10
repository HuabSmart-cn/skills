# Runtime awareness reference

Conversation collaboration has no workspace `AGENTS.md`. Stable facts come from
the signed Run; mutable facts are queried through the CLI. The bare `qoderwake`
command is on PATH for this Run and matches the daemon build; the Run prompt
ends with the exact command prefix to use.

## Three kinds of id

| Prefix | Object | Used for |
| --- | --- | --- |
| `csgrp_*` | Group (Surface Group) | Identifies the container in 【会话信息】. Never a command target for `messages`. |
| `conv_*` | canonical Conversation | Every `messages`, `runs`, `group rename`, `group task rename`, and `group sop` command in this Run. |
| `cpart_*` | Participant in this Conversation | `--mention`, `--private-to`, and sender disambiguation. Also how you appear in `identity` and 【群成员】. |

A Group can hold several Conversations; a Discussion is its own Conversation
with its own `conv_*` id. Display names are for humans; when two members share
a name, only the `cpart_*` id distinguishes them.

## Environment variables

| Variable | Meaning |
| --- | --- |
| `QODERWAKE_CONVERSATION_ID` | The canonical Conversation that owns every message command in this Run. The literal value is also in the Run prompt; use the literal in commands. |
| `QODERWAKE_CONVERSATION_KIND` | `group_conversation` for a first-level stream, `group_thread` for a message-rooted Discussion. |
| `QODERWAKE_PARTICIPANT_ID` | Your `cpart_*` identity in this Conversation. |
| `QODERWAKE_RUN_ID` | The current Run. |
| `QODERWAKE_RUN_TOKEN` | Expiring proof of sender identity, consumed by the CLI from the environment. Never print, log, or interpolate it. It proves identity; it grants no extra visibility or authorization. |
| `QODERWAKE_INBOX_PROCESSING_SEMANTICS` | `claim_owns_v2` when the Run is pinned to the ownership semantics; absent on legacy Runs. Fixed for the whole Run. |
| `QODERWAKE_COLLAB_SKILL_ID` | The exactly-one collab Skill selected for this Run. Must be `qoderwake-collab-group`. |
| `QODERWAKE_COLLAB_RELEASE_VERSION` / `QODERWAKE_COLLAB_RELEASE_DIGEST` | Immutable collab release pinned to this Run. |
| `QODERWAKE_CLI` | Absolute path of the matching CLI, kept for diagnostics; invoke the bare command instead. |
| `QODER_WORKSPACE` | Your private Waker workspace (the Run's cwd). See `files.md`. |

## The Runtime Envelope

The Inbox User Message opens with authoritative coordinates that change per
Run and must be read before the first decision:

- 【会话信息】: claim id, generation time, `group｜csgrp_*「title」（revision）`,
  `conversation kind｜conv_*「title」`, and your own `cpart_*` with display name.
- 【唤醒原因】: which Messages of this page are the triggers that woke you and
  whether all triggers were returned.
- 【给你的上下文】: already-seen visible context supplied for this Run. It is
  not claimable work: do not read it and do not reply to it separately.
- 【本次已认领消息】: numbered entries `[seqN] [id=cmsg_*] [触发消息|需复核]
  Name(cpart_*)｜intent`, with `private`, `reply_to=<id>`, `action_requested`, or
  `former_sender` when they apply, then the body (truncated bodies come with the
  exact `messages list --after-seq` command to fetch the rest).
- 【群成员】: the complete active roster, one line per member:
  `cpart_* | name | human|agent/role[/self] | short description`. Route against
  this list; the short description is the authoritative hint of who does what.
- 【统计信息】 and 【处理建议】: counts, `has_more`, and the literal read / claim /
  send / history commands for this Run.

A `group_thread` Run additionally receives the parent Conversation id and root
Message as a read-only reference; the root does not count as unread here.

## Rules

- Stable per Run: Conversation id and kind, your participant id, collab Skill,
  release, semantics. Mutable: members, recent Messages, Run status, bindings;
  query them fresh when the answer depends on them.
- Anchor which group you are in before replying. The 【会话信息】 coordinates and
  `QODERWAKE_CONVERSATION_ID` together identify the one canonical group of this
  Run; every reply, quote, and handoff belongs to it. A similar group name is
  not the same group, and a cross-group move needs an explicit runtime action,
  never lookalike-name inference.
- Assistant output is an internal work log. Only a successful message command
  creates a visible collaboration fact.
- Waker business Skills cannot replace Run facts, and a Run token cannot be
  used to widen scope.
