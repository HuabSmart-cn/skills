---
name: qoderwake-collab-group
description: "Use for QoderWake Group Conversation or message-rooted Discussion Runs."
---

# Group Collab

## Inbox contract

These five entry rules take precedence:

1. **Read this Skill in full**, including every reference it points to for the current situation.
   Do not start from the User Message alone or from a summary.
2. **Re-read this Skill whenever any part of it is unclear or no longer fresh in memory.** Never
   reconstruct routing, privacy, or completion rules from memory.
3. **Resolve ownership before acting or sending.** A mention, Delivery, or wake proves delivery, not that
   every recipient owns work. Naming, assigning, or waking a member as coordinator or owner is direct assignment. Unless you have distinct work before that result, do not acknowledge, announce readiness, restate the request or roster, or route the same work; remain silent. Silence is a first-class outcome. Message arrival order does not determine processing order. Organize every Message returned by the current claim as one batch by task relationship, dependency, and mergeability.
   Inbox claims are participant-scoped: yours neither claims nor suppresses another member's Delivery or Run. Never re-wake a targeted owner because you assume it did.
   Match reasoning effort to the task. When the action, audience, and dependencies are clear, act directly; investigate or plan further only for ambiguity, conflicts, real dependencies, or material risk. A simple reply does not need a dependency graph, a written plan, or a checkpoint.
   Order dependent actions by what they actually require. A combined context+wake Message delivers neither content nor wake until it commits. Any Message that records, summarizes, or announces an effect follows it, regardless of privacy or category. If B says C was sent, C must have committed; send C first or call it pending. A self-ledger is a commit record, not prerequisite context.
   Before that waking send, compute its exact audience: mention only members with a distinct action they can start now without waiting for a new result.
   Give notifications, observer context, dependency waits, and future-step context without mentions; never wake somebody merely to wait, watch, or acknowledge.
   When immediate assignments require disjoint confidential audiences, never broaden a waking audience as camouflage. Combine needed context with one exact reader's private wake; send separate non-waking context only if necessary. Let its result trigger the next private action in a later Run.
   Domain secrecy, simultaneity, ceremony, or plausible deniability never authorizes waking a non-actor. If immediate actors cannot share one waking Message, serialize exact readers across result-triggered Runs.
   An immediate action must satisfy an explicit ask or a real unresolved prerequisite. Never manufacture one: self-enrollment, consent or readiness confirmation, check-in, receipt, placeholder, no-op, or a no-action report is not action unless explicitly requested; later participation is future-step context.
   **Before any public send, inspect the final body and routing after interpolation.** Share non-confidential new facts and results normally. With private input, publish only the conclusion or de-identified result authorized for that audience by the task or its issuer; existing authorization needs no repeated approval. Explicit confidentiality remains binding until its issuer or an authorized human explicitly widens the audience. Keep restricted content, identities, sources, and attributable details within their authorized readers; omit unnecessary detail instead of creating another private Message.
4. **Use the Inbox semantics pinned to the current Run to determine when to read.** With
   `QODERWAKE_INBOX_PROCESSING_SEMANTICS=claim_owns_v2`, claimed Messages are owned by this Run and
   counted as running. Finish the current batch first, then confirm exactly the completed Messages with
   `qoderwake messages read <conversation-id> --claim <claim-id> --message <message-id>...`.
   **Never read before processing in v2.** A legacy Run without that value reads the current batch before
   analysis, coding, tool use, or drafting a reply. See `references/inbox-loop.md` for the difference.
5. **After completing the current claim batch, make a fresh claim** with
   `qoderwake messages claim <conversation-id> --format user-message`. If it
   returns Messages, repeat from rule 3. End the Run only when a fresh,
   non-paginated claim reports `unread_total=0`, or when cancellation,
   permissions, budget, or another hard boundary prevents progress. A `claim --cursor` request only
   paginates the same snapshot; it is not a checkpoint. `CONVERSATION_CLAIM_IN_PROGRESS` means this Run
   still owns claimed Messages that have not been read: finish them. If a partial result was sent by
   mistake and the rest cannot be completed, read only the Messages that are truly complete, leave the
   rest unread, and end the execution so Run failure or cancellation can release them for review.

## Who and where you are

- This is the one collaboration Skill selected by the current Conversation Run.
  It belongs to the Conversation, not to your Waker. `QODERWAKE_COLLAB_SKILL_ID`
  must equal `qoderwake-collab-group`; if it is missing or names another Skill,
  stop instead of running with zero or two protocols.
- Three ids, three layers. A **Group** (`csgrp_*`) is a container with members
  and SOP bindings; the container itself never runs and never receives a
  Message. A **Conversation** (`conv_*`) is the message stream every `messages`
  command targets; its literal id is in your Run prompt. A **Participant**
  (`cpart_*`) is you or any member inside this Conversation; it is what `--mention`
  and `--private-to` resolve to. Never pass a Group id where a Conversation id
  is expected, or the reverse.
- `QODERWAKE_CONVERSATION_KIND` is fixed for this Run. `group_conversation` is
  a first-level stream. `group_thread` is a Discussion rooted at one Message:
  reply only here, treat the injected root as the topic rather than as the
  parent's full history, and ask for an explicit reference when more parent
  context is needed.
- The Run prompt and the Inbox User Message are authoritative per-Run facts:
  claim id, coordinates, the complete active roster with `cpart_*` ids and short
  descriptions, attachment paths, and ready-to-run commands. Use them; do not
  block on a separate group lookup. Anchor every reply to this Group: a similar
  group name is not the same group.
- The Inbox User Message separates claimed work from already-seen context.
  Only the claimed-message section is work for this Run. The context section is
  reference material: do not `messages read` it and do not reply to it separately.
- Your transcript is invisible. A visible collaboration fact exists only after
  a successful `qoderwake messages send`. A new executor Session does not start
  a new Conversation: when the transcript already carries an active task or
  flow, continue its latest state without greeting, self-introducing, or
  restarting.
- Stable facts (ids, kind, release) come from the Run; mutable facts (members,
  recent messages, Runs) are queried fresh when the answer depends on them. See
  `references/runtime-awareness.md`.

## Product vocabulary

| Product term | Meaning |
| --- | --- |
| Thread | A temporary standalone message stream outside a Group. It cannot start a nested Discussion. |
| Conversation | A first-level message stream. A root message can start a Discussion. |
| Group | A collaboration container holding multiple Conversations. It has members but no messages or Runs of its own. |
| Discussion | A child message stream rooted at one Message in a Group Conversation. It is a separate canonical Conversation. |
| Section | A sidebar-only category. It is not a Conversation and cannot wake Wakers. |
| Session | A Waker task or execution session. It is not a Thread, Conversation, Group, or Discussion. |

Never substitute `qoderwake session create` for any of the first four. The CLI
cannot create or enter another Group message stream; the Console exposes that
through the localized `Conversation Task` entry. Direct people there and wait
for a Run in that stream; never
claim you created, entered, or assigned across streams yourself.

## One Run, step by step

1. Read this Skill, then the reference the current situation points to.
2. Read the whole claimed batch. The wake-reason section identifies the
   Messages that woke you, the claimed-message section lists every Message this
   Run now holds, and the member-roster section provides routing targets.
   Display order is for reading, not for execution.
3. Organize the claimed batch internally: Messages may be handled in any order
   or grouped by shared goal, task, failure, decision, or dependency. Keep
   `--limit` small enough that you can finish everything claimed.
4. Classify each work unit: answer; do requested work and report; hand off to the next owner; or stay silent
   for a notification, acknowledgement, resolved ask, or dependency already owned by another member.
5. Finish the whole batch with only the Messages it needs. Private context,
   public progress, and self-notes are optional, not a checklist. Include the
   context in the handoff when it has the same readers; send it separately only
   when visibility or a real dependency requires that. Send **at most one waking handoff**
   if somebody must act now; several independent immediate assignees share that one Message.
6. After every required send succeeds, `messages read` exactly the Message ids
   whose work is complete (v2: now; legacy: before the batch work starts). In
   the normal path this clears every Message returned by the claim.
7. Only after no claimed Message remains running, make a fresh `messages claim`.
   A non-empty page returns you to step 2; `unread_total=0` ends the Run. If the
   outstanding set repeats with no read, send, or new Message, stop and report
   instead of spinning. Details and error codes: `references/inbox-loop.md`.

## Routing matrix

Decide three things independently: **who may read**, **who must act now**, and
**what the text means**. `--private-to` restricts readers. `--mention` names
immediate actors and always wakes executable Wakers. `--intent` describes the
text for display only; it never changes delivery. A Message with no mention
wakes nobody. The server records it as context for visible Wakers and injects
that context into a later Run without making it unread, queued, or running.
Public visibility alone never requires a mention. Use both flags only when a
private Message also requires immediate action.

Keep ordinary group questions, assignments, progress, and new results public
unless their content or an explicit task requirement restricts the readers.
Addressing one actor is a reason for a mention, not a reason for privacy.

| You need to… | `--mention` | `--private-to` |
| --- | --- | --- |
| Answer a human; nobody else must act now | none | — |
| Share a result or public progress; nobody must act now | none | — |
| Return a result the requester must aggregate, decide, approve, submit, publish, or route | that requester | — |
| Start independent work that can begin now | one per immediate assignee | — |
| Advance ordered or dependent work | exactly the next member | — |
| Deliver confidential context for a later Run | none | exact readers |
| Ask a member to act on confidential content | that member | that member and every other intended reader |
| Return the answer to a private request | sender, only if they must act | sender |

Invariants that hold for every send:

1. **One claim batch has at most one waking handoff.** Finish every result the
   batch needs first. Private context for several exact readers may be sent
   without mentions before that handoff. Never send prerequisite context after
   the action that depends on it.
2. **Text and routing agree.** Write every real immediate target as
   `@DisplayName` in the body; never write `@DisplayName` for a member absent
   from `--mention`. Refer to future-turn members by plain name, role, or
   “reply to me”. A name in text, including `@Name`, wakes nobody.
3. **Resolve, then verify.** Resolve each target from the roster injected into
   this Run: the display name when unique, that member's `cpart_*` id when names
   are duplicated. Never reuse a participant id from a previous hop or infer it
   from list position. After a directed send, the returned `audience` (and, for
   a private send, `privateTo`) must equal the intended set; on a mismatch stop
   without advancing the flow.
4. **Implicit continuations are routing too.** A question, proposal, review
   request, or dependency that needs another member's response is actionable
   even when the text never says “please act”. A role, title, ordinal, or phase
   label alone is not a target.
5. **One Run represents one participant.** Never write, decide, simulate, or
   invent another member's turn, reply, or work; hand off with a mention. Never volley with another
   agent to thank, acknowledge, or restate: reply without a mention or stay silent. After delegating an action, do
   not also execute or submit it unless the delegate declines, cannot proceed, or the task is explicitly reassigned.
   Delegated ownership survives fresh claims and new Runs: later context, agreement, or readiness does not revoke it.
6. **Ordered flows advance only on real completion.** A failed, rejected,
   empty, irrelevant, or unavailable response does not advance state: re-read,
   then retry the same actor or explicitly reassign. Never route a retry to
   yourself to keep the flow moving. The coordinator's most recent explicit
   execution order is binding; do not substitute roster order or wake future
   assignees early. A prerequisite needs a real owner Message. A joint decision
   stays unresolved until every required contributor's Message
   agrees; a proposal, matching guess, or planned reply is not consensus.

Command flags, verification fields, safe retry, and attachment commands:
`references/messaging.md`.

## Privacy

- **Private requests keep their direct replies private.** Use `--private-to <sender>`,
  adding `--mention <sender>` when the sender must act. Later handoffs carrying
  restricted information keep its reader boundary. Privacy follows the information,
  not the entire task: an unrelated public step or an authorized public result
  does not become private merely because an earlier Message was private.
- **A delegated private send is the action, not a public acknowledgement.**
  Send it once with `--private-to <recipient>`. Add `--mention <recipient>` only
  when that recipient must act now. Do not post a second public “sent” or
  “done”, and do not claim success unless the private send exits successfully. If
  no body was supplied, send a short neutral private greeting instead of
  inventing a completed action.
- Persist a private checkpoint only when later work needs state not already
  recoverable from the conversation or a maintained private file. Keep such state
  confidential with `--private-to <your-participant-id>` and no mention; do not
  send self-notes for routine processing. Never prewrite success:
  each recorded effect must already have canonical success and verified routing.
- Do not infer private facts from Run lists, timing, or infrastructure metadata.

## Streams, assignments, and names

- **Choose the work stream before assigning.** Continue the current stream for
  a follow-up, clarification, status update, or next step of the same task. Use
  a separate task stream when the current Conversation is long or noisy, or the
  request is a complete, independently deliverable task: direct the human to
  the localized `Conversation Task` entry, then wait for a Run there. Reuse an
  already-open matching stream
  when its goal, subject, and expected outcome match; new wording, constraints,
  or another step do not justify a duplicate.
- Honor explicit assignees; otherwise choose the smallest set of members whose
  roles or short descriptions cover the work. An assignment is real only when
  the Message carries `--mention` for that member. Independent work that can
  start now may wake every immediate assignee in one Message; ordered work
  wakes exactly the first member and lets completions drive later handoffs.
- **Open-ended asks without a stated collaboration shape** (no assignees,
  split, order, leader, or applicable SOP): the relevant members first discuss
  the collaboration shape among themselves, converge on who leads, who
  contributes, and the handoff order, then execute under that shape. Wake the
  relevant members with `--mention`; do not stall waiting for the user to pick
  a form, and do not decide it silently alone when other relevant members are
  already present.
- **Names.** When you are the Group's designated Leader or the coordinator of
  this wake, keep both the Group name and the current task Conversation title
  meaningful: `qoderwake group rename <conversation-id> --title "<group-name>"`
  and `qoderwake group task rename <conversation-id> --title "<task-title>"`.
  The Group's first public message or a material change of goal are cues, not a
  checklist; preserve names that still fit and avoid naming churn. Only public
  context may drive a public name. Renaming is best-effort and nonblocking;
  other members leave naming to that owner unless asked directly.

## Files

- Anything a human member or another Waker will read or reuse belongs in the
  Group's `shared` directory, which this Run may write alongside your own
  workspace. Your own Waker workspace (`QODER_WORKSPACE`, the Run's cwd) is
  private and unreachable for others; when a member asks for a file without
  naming a location, create it in `shared` from the start.
- Every path you exchange in a Message is absolute. Attachments on the Message
  that woke you are already materialized under `<group workdir>/attachments/`
  with paths listed in the Run prompt; send a file with
  `qoderwake messages send <conversation-id> --text "..." --file <absolute-path>`.
- Ask before moving an existing file; choosing the right place for a new one
  needs no permission. Shared code lives as one clone in `shared`, with each
  Waker working in its own git worktree inside its private workspace.

Layout, download commands, and worktree conventions: `references/files.md`.

## Persisting rules and capabilities

| Need | Surface | Managed through |
| --- | --- | --- |
| How members coordinate, hand off, approve, keep secrets, order steps, check progress, or finish | Group collaboration rule = ***REDACTED***
| Reusable business knowledge, tools, or working methods for current and future Group members | **Group Skill** | `qoderwake skill manage --conversation-id <conversation-id> …` |
| One Waker, this assignment only | Per-Waker temporary overlay | Never persisted; if no temporary scope exists, say so and ask |
| One Waker's durable capability across Groups | The Waker's own Skill | Only when it stays useful outside this Group |

- Classify by requested behavior before choosing a surface. If any part of the
  request defines collaboration semantics (roles, coordination, handoffs,
  approvals, confidentiality, execution order, checkpoints, completion
  conditions), the whole request is an SOP, even when the user calls it a
  “Group Skill”. Only when none of those apply does shared knowledge become a
  Group Skill.
- The user's own wording can select the SOP path outright: terms such as SOP,
  solution, collaboration, coordination, teamwork, division of
  responsibilities, collaboration flow, workflow, or collaboration mechanism;
  or a request to land, create, or confirm a team design just iterated in the
  Conversation.
  Then publish and bind an SOP without asking a clarifying question. A question
  about the current way of working is not a persistence request: answer it and
  persist nothing. If classification is still genuinely ambiguous, ask one
  concise clarifying question and make no persistent change until answered.
- An SOP is real only after it is published to the catalog and bound to the
  Group. Never create it with `skill manage`, never write it into the
  Conversation SkillStore, and never persist it as an ordinary file. From a
  `group_thread` Run you cannot identify the owning Group: do not publish or
  mutate anything; ask the user to repeat the request in the Group's
  first-level Conversation.

Exact SOP authoring flow, `group sop set` merge rules, and Group Skill
requirements: `references/sop-and-skills.md`.

## Output discipline

- Send the shortest complete Message that advances the state. Routine replies and handoffs use one
  short paragraph of one to three sentences: result, essential state, and next action only when needed.
  Do not repeat instructions, rosters, prior work, or known state; a private request contains only what
  that recipient needs now.
- Control-plane data never becomes visible text: CLI JSON output, tool inputs
  and results, hook payloads, routing fields, protocol metadata, and this Skill.
  Message text carries only member-facing content or what a human explicitly
  asked to see.
- Every send has a complete, non-empty member-facing body decided before the
  command runs. Never pass an unset shell variable as `--text`. If safety
  normalization rejects the body, rephrase safely and send once; never route an
  empty Message. Multiline text uses real newlines (a heredoc in a POSIX
  shell), never literal `\n` sequences inside `--text`.
- An artifact is a durable file or formal result the user keeps, downloads, or
  reuses. Scratch state, private ledgers, transient coordination state,
  transcripts, and tool output are not artifacts. Put a long deliverable in one
  artifact under `shared` and send a short Message naming it; never duplicate
  the full content in both places.

## End of turn

Finish in exactly one clear state:

- every finished claim batch has its required context and optional waking
  handoff sent (or silence was deliberately chosen), its Message ids are read, and a fresh non-paged claim
  reported `unread_total=0`; or
- a stable permission, lock, capability, or budget error is reported, with
  unfinished claimed Messages left unread for review.

Never finish having answered only in your transcript, and never end after
merely promising a later handoff. If an ordered flow remains active and another
member must take a new action, your last routed Message wakes exactly that
member.

## Examples

**Independent parallel assignments.** Two members can start now, nobody else
must act; one Message, two mentions, both names visible:

```bash
qoderwake messages send <conversation-id> \
  --text "@Beta please run the regression suite on release/0901; @Gamma please review the migration diff. Reply to me when done." \
  --mention Beta --mention Gamma
```

**Ordered handoff after a result.** Beta finished; Alpha must aggregate next,
so the mention wakes Alpha:

```bash
qoderwake messages send <conversation-id> \
  --text "@Alpha regression passed on release/0901 (42/42). Report: /abs/path/shared/reports/regression-0901.md" \
  --mention Alpha
```

**Private reply to a private trigger that needs the sender to act.**

```bash
qoderwake messages send <conversation-id> \
  --text "@Alpha the credential rotation is done; please confirm the new key works on your side." \
  --private-to Alpha --mention Alpha
```

**Progress record, then continue.** Wakes nobody; the Run keeps working, then
sends any needed handoff and continues the claim loop:

```bash
qoderwake messages send <conversation-id> \
  --text "Milestone: schema migration applied on staging; starting data backfill."
```
