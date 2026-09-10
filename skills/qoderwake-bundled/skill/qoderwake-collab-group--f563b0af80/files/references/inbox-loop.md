# Inbox loop reference

Read this when you need the exact claim / read state machine, the difference
between `claim_owns_v2` and legacy Runs, the error codes, or the stop
conditions. The five-rule contract at the top of `SKILL.md` is the summary;
this file is the detail.

## Commands

```bash
qoderwake messages claim <conversation-id> [--limit <n>] [--cursor <cursor>] \
  [--format user-message|json] [--json]

qoderwake messages read <conversation-id> --claim <claim-id> \
  --message <message-id> [--message <message-id> ...] [--json]

qoderwake messages list <conversation-id> --after-seq <seq> --limit <n> --json
```

- `claim` without `--cursor` creates a fresh snapshot of what is queued for you
  right now. Default `--limit` is 3, maximum 50; it is a hard cap on how many
  Messages this call may return and (in v2) claim. Trigger Messages sort first
  but never exceed the limit.
- `claim --cursor <cursor>` pages the same snapshot. In v2 each newly returned
  page also enters “running”. Paging never counts as a checkpoint and never
  proves the inbox is empty.
- `--format user-message` (default) prints the same Inbox document the Run
  started with. It separates already-seen context from claimed work. `--json`
  adds the machine fields (`claim_id`, `context[]`, `messages[]`, `stats`,
  `next_cursor`, `user_message`).
- A fresh empty claim prints one line containing `unread_total=0`; that line is
  the normal completion boundary of the Run.
- `read` takes 1..N explicit Message ids from one claim. There is no range or
  “through seq” form; whatever you do not list stays unread. The batch is
  all-or-nothing and safe to retry on a network timeout. Default output:
  `Marked 3 message(s) read; 0 already read; 7 unread remain.`
- `list --after-seq` is strictly greater-than, ascending by seq. Use it to fetch
  a truncated body (the User Message prints the exact command per item) or
  history that determines the answer; do not read the whole group history to
  “empty the inbox”.

## What a Message can be, for you

| Relation to you | How it reaches you | Counts as unread? |
| --- | --- | --- |
| You are mentioned | starts a Run for you, or queues as wake work for the active Run's next claim | yes |
| Visible to you, not mentioned | appears in the context section of a later Run; never starts one | no |
| Not visible to you | never appears in your Inbox or transcript | no |

Only waking Messages are claimable work. Context is already seen when injected:
do not `read` it and do not reply to it separately. Your own sends are never
unread for you.

## Per-message states (v2)

```text
queued (unread | needs_review)
  --claim returns it-->  claimed_unread   (counted as “running” for this Run)
claimed_unread
  --read succeeds-->     finalized_read   (leaves running; never shown again)
  --Run fails/cancels--> needs_review     (back to queued for a later Run)
```

- The Console counts queued wake work separately from `claimed_unread` owned by
  the active Run. Pending context is never shown as queued, running, or a note.
  Without an active Run, wake work causes the scheduler to create one. Claiming
  K wake Messages moves exactly those K from queued to running atomically;
  reading M moves M out of running. That is why you claim only what you can
  finish and read only what you have finished.
- `stats.unread_total` in a claim is the candidate total fixed when that claim
  snapshot was created; only a fresh, non-paged claim can report the inbox as
  empty.
- Messages you never claimed stay queued; a Run ending on a hard boundary leaves
  them for the next Run. Messages you claimed but did not read are released to
  `needs_review` when the Run fails or is cancelled; they are never silently
  consumed.

## Context lifecycle

```text
context_pending --included in a Run--> context_in_run
context_in_run  --Run succeeds-------> context_seen
context_in_run  --Run fails/cancels--> context_pending
```

Context never creates a Run and never enters `messages[]`. The server injects a
bounded recent context window into the next independently created Run. A
successful Run acknowledges that window; a failed or cancelled Run makes it
eligible for a later Run again.

## `claim_owns_v2` versus legacy

| | `claim_owns_v2` (`QODERWAKE_INBOX_PROCESSING_SEMANTICS` is set) | legacy (variable absent) |
| --- | --- | --- |
| Meaning of claim | ownership: returned Messages are already “running” | a stable view of unread candidates |
| When to `read` | after the current claim batch and its merged result are complete | before you start analysing, coding, calling tools, or composing a reply for the current claim batch |
| Fresh claim while you still hold unread claimed Messages | rejected with `CONVERSATION_CLAIM_IN_PROGRESS` | not applicable: a legacy claim takes no ownership, read is the checkpoint |
| Normal end | fresh claim with `unread_total=0` and nothing still running | fresh claim with `unread_total=0` |

The semantics are pinned when the Run is created and never change mid-Run. Read
the value once from the Run prompt (it states it explicitly) and follow one
column only.

## The loop, with failure paths

```text
initial implicit claim  ->  K Messages running
        |
        v
organize and finish all K  ->  0..n context sends  ->  <=1 waking handoff
        |
        v
read the exact completed ids              (v2: now; legacy: before the work)
        |
        v
still holding claimed Messages?  -- yes -->  finish them, or fail/cancel at a hard boundary
        | no
        v
fresh claim (no cursor)
   |-- non-empty -----------------------------> organize and finish the new batch
   |-- unread_total=0 -------------------------> end the Run
   |-- CONVERSATION_CLAIM_IN_PROGRESS ---------> you still hold unread ids: finish them
   |-- same outstanding set twice, no progress -> stop and report; do not spin
```

- If a waking handoff was already sent and the batch's remaining work is
  rejected, do not read the unfinished Messages and do not retry the fresh claim
  through `CONVERSATION_CLAIM_IN_PROGRESS`. Read only what really completed,
  leave the rest unread, and end the execution; Run failure or cancellation
  releases them for review.
- Batch too large to finish? Do not read ahead to shrink it. Finish what you
  can, read those, and use a smaller `--limit` on the next claim.
- Cancel, permission failure, wake budget, wall-clock, or token limits are hard
  boundaries: unclaimed Messages stay queued, claimed-unread Messages go to
  review, and the runtime derives a continuation. Report the boundary; do not
  fake completion.

## Error codes

| Code | Meaning | Do |
| --- | --- | --- |
| `CONVERSATION_CLAIM_IN_PROGRESS` | this Run still holds unread claimed Messages | finish and read them, then claim again |
| `CONVERSATION_CLAIM_EXPIRED` | the claim or cursor belongs to a closed generation | fresh claim; never read from the stale id |
| `CONVERSATION_CLAIM_STALE` | a paged candidate was withdrawn or invalidated | fresh claim |
| `CONVERSATION_CLAIM_MESSAGE_MISMATCH` | a `--message` id was not returned by that claim | fix the id list; the whole read batch was rolled back |
| `CONVERSATION_INBOX_INCOMPLETE` / `CONVERSATION_RUNTIME_ENVELOPE_INCOMPLETE` | the runtime could not build an authoritative page or roster | the Run fails explicitly; do not guess from history |

Errors are stable codes; a handle or permission error is never a signal to
switch Conversation, Group, or storage surface.
