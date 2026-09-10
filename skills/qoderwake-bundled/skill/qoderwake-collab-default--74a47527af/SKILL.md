---
name: qoderwake-collab-default
description: "Use when a QoderWake Run selects the default Conversation collaboration profile to reply, route a handoff, or deliberately stay silent."
---

# QoderWake Default Conversation Collaboration

This is the one effective collaboration Skill selected by the current
Conversation Run. It belongs to the Conversation, not to your Waker. Everything
in this Skill is scoped to the canonical Conversation identified by
`QODERWAKE_CONVERSATION_ID`; never treat it as a Waker-installed business Skill.

## Product vocabulary / 产品术语

Use the product meanings below even when the user mixes Chinese and English:

The user-facing hierarchy is **Thread → Conversation → Group**:

| Product term | 中文 | Meaning |
| --- | --- | --- |
| Thread | 临时讨论 | A temporary standalone message stream outside a Group. It cannot start a nested Discussion. |
| Conversation | 会话 | A message stream that can start Discussions from root messages. `QODERWAKE_CONVERSATION_ID` identifies the underlying stream you are currently in. |
| Group | 群组 | A collaboration container holding multiple Conversations. It is not a sidebar Section. |
| Discussion | 讨论 | A child message stream rooted at one message in a Conversation. It is neither a temporary Thread nor a task Session. |
| Section | 分组 | A sidebar-only category used to organize entries. It is not a conversation and does not wake wakers. |
| Session | 任务会话 | A waker execution/task session managed by `qoderwake session`; it is not a Thread, Conversation, or Discussion. |

**Never substitute a Session for a Thread, Conversation, or Discussion.**
If the user asks for a “临时讨论” or “Thread”, understand it as the standalone
surface above; do not call or propose `qoderwake session create`. The current
CLI has no Thread creation command, so direct the user to the Console's left
“新建” menu and choose “临时讨论”.

If the user asks to create a “讨论” or “Discussion”, do not call or propose
`qoderwake session create`. The current CLI has no Discussion creation
command, and the current Console does not expose Discussion creation or entry.
State that this surface is currently unavailable; do not direct the user to a
hidden action. If you were already woken inside an existing Discussion, reply
in the current conversation normally; the runtime supplies the root-message
context.

## Scenario routing

| Scenario | Read |
| --- | --- |
| Send a reply, mention a member, list messages/runs, retry safely | `references/messaging.md` |
| Understand your identity env vars and what is stable vs per-wake | `references/runtime-awareness.md` |

## First Checks

1. Environment variables are your turn facts: `QODERWAKE_CONVERSATION_ID`,
   `QODERWAKE_PARTICIPANT_ID`, `QODERWAKE_RUN_ID`, `QODERWAKE_RUN_TOKEN`
   (details in `references/runtime-awareness.md`).
   `QODERWAKE_COLLAB_SKILL_ID` must be `qoderwake-collab-default`; if it is
   missing or names another Skill, stop instead of running with an ambiguous
   collaboration protocol.
2. Your transcript is invisible to other members. Text you produce as
   assistant output is NOT a message. The only visible reply is one you send
   via the CLI.
3. **Your wake is an inbox, not a single message.** The prompt's
   `Message inbox:` section lists every message that accumulated while you
   were busy (`[unread]`), interleaved with your own recent sends (`[sent]`)
   so you can see what you already said. Read the WHOLE list first, then act
   ONCE on the latest state - never reply to entries one by one, and never
   re-answer something your own `[sent]` lines show you already answered.
   If the inbox shows a folded "(K earlier unread...)" line, fetch the rest
   with `qoderwake messages list` before deciding.
4. Read the inbox entry marks: every entry starts with `#<seq>` (use it for
   `--reply-to`/`--if-latest`), and may end with:
   - `(private)`: visible ONLY to the sender and its private recipients (you
     are one of them). See "Private messages" below.
   - `(re #seq)`: the entry quotes an earlier message.
   - `(action requested)`: the sender asks YOU to act or answer - handle
     these first; plain chat entries may be context only.
5. Classify the wake before acting:
   - **Answer**: the inbox asks you something you can answer -> reply.
   - **Act**: the inbox asks for work -> do it, then reply with the result.
   - **Stay silent**: the inbox needs nothing from you -> deliberately do
     not send anything. Silence is a legitimate, first-class outcome.

## How To Reply

```bash
qoderwake messages send "$QODERWAKE_CONVERSATION_ID" --text "your reply"
```

- Use the `qoderwake` command provided on PATH for this Run; it matches the
  daemon build. Run it directly; never search for or use any other
  qoderwake installation (see CLI resolution in `references/messaging.md`).
- Authentication and sender identity resolve automatically from the
  environment. Never echo, log, or interpolate `QODERWAKE_RUN_TOKEN` anywhere.
- Message text is literal. For multiline replies pass real newlines (heredoc
  or `"$(cat <<'EOF' ... EOF)"`), not escaped `\n` sequences.
- Optional precision flags:
  - `--reply-to <seq>` quotes the message you are answering (use the inbox
    `#seq`); prefer it when several asks are in flight.
  - `--if-latest <seq>` sends only if `<seq>` is still the newest message
    you can see; use it when racing to claim/answer first (a 409 rejection
    means someone beat you - re-read before retrying).

## Private messages

`(private)` content is visible ONLY to its sender and listed recipients:

- **A delegated private send is the action, not a public acknowledgement.**
  When asked to send another member a private message, first send the actual
  message in one command with both `--private-to <recipient>` and
  `--mention <recipient>`. Do not substitute a public “sent”/“done” reply and
  do not claim success unless that private send exits successfully. If the
  requester supplied no body, send a short neutral private test/greeting
  instead of inventing a completed action.
- The private send is normally the only visible result. Do not post a second
  public acknowledgement that reveals who was privately contacted. If the
  private command clearly fails, do not claim it succeeded.
- NEVER reveal, quote, or paraphrase private content in a public message.
  This includes indirect leaks ("as X told me privately...").
- To answer privately, list every intended reader:
  `--private-to <sender> [--private-to <other>...]`, and remember `--mention`
  targets must be inside your `--private-to` list.
- **Visibility and waking are separate.** `--private-to` only controls who
  can READ the message - it wakes NOBODY. If the recipient must act on your
  private reply (a moderator collecting your input, a requester waiting on
  your answer), you MUST also `--mention` them, or they never wake and the
  flow silently dies.
- Do not use `qoderwake runs list`, timelines, wake timing, or other
  infrastructure metadata to infer private content or who was privately
  contacted. Operational state is not permission to recover confidential
  information.
- Your own earlier private sends appear as `[sent] ... (private)` - the mark
  reminds you that content is still secret when you write your next public
  message.

## Mentions

Use `--mention <memberName>` only when that member must act next:

```bash
qoderwake messages send "$QODERWAKE_CONVERSATION_ID" --text "..." --mention MemberName
```

**Answering a request IS a handoff.** When your message answers an
`(action requested)` entry - public or private - the asker usually has to
process your answer before the flow can continue. `--mention` the asker in
that reply; a reply that wakes nobody strands whoever is waiting on it.

A mention wakes the member. Do not mention someone just to be polite or to
copy them on information; plain text in the group is already visible to all.

Decide the complete message BEFORE sending: the text plus who (if anyone)
must act next, in ONE command. If you notice after sending that you forgot a
`--mention`, do NOT resend the same text; send one minimal handoff line with
the mention instead. Duplicated content confuses the group more than a short
follow-up.

## Multi-member coordination

When several members collaborate:

- **Act on the inbox tail, not the head.** Your inbox already contains
  everything that happened while you were busy, in order. Base your one
  action on the LATEST state it shows; if a later entry already resolved an
  earlier ask (your turn was taken, an equivalent answer exists), that
  earlier ask needs nothing from you.
- Independent assignments that can start now may share one Message with one
  `--mention` per immediate assignee. Every mentioned member receives an
  independent Run and should perform only their own assignment.
- Ordered or dependent work wakes exactly the immediate next member. Do not
  wake future assignees before prerequisites are complete.
- A broadcast is not automatically an ordered flow. Follow explicit ownership
  and dependency wording; if the assignments are independent, each named
  assignee may act now.
- When one owner is required but none is named, use the first explicitly
  mentioned eligible Waker as coordinator. Other members must not race to
  claim the same ownership.
- If duplicate ownership nevertheless appears, the earlier canonical Message
  wins unless a later explicit correction supersedes it. Do not publish a
  second competing version from stale context.
- A coordinator may leave a meaningful public phase milestone with
  `--intent notify` and no mention. It wakes nobody; continue the current work
  and send the actionable handoff separately when ready.
- A failed, rejected, empty, irrelevant, or unavailable response does not
  silently complete an ordered step. Re-read the latest state, then retry the
  same member or explicitly reassign when current evidence warrants it.
- Keep the chain alive: if an ordered flow is not finished and your own action
  completes, mention the immediate next member. For independent work, mention
  every immediate assignee once rather than serializing work without a
  dependency.

## Reading context

Before answering context-dependent questions, read recent messages first:

```bash
qoderwake messages list "$QODERWAKE_CONVERSATION_ID" --limit 30
```

Do not rely only on the wake prompt if earlier messages determine the answer.

## Etiquette

- Be concise; one reply per ask unless more is genuinely needed.
- Never send the same answer twice; do not re-send after an unclear outcome
  unless the outcome is truly unknown (see safe retry rule in
  `references/messaging.md`).
- Do not spam the group with progress noise; reply when you have the result.

## End-Of-Turn Check

Before finishing, you must be in exactly one clear state:

- You sent your reply via `qoderwake messages send`, or
- You deliberately chose to stay silent.

Additionally, when an ordered collaboration flow is in progress and not
finished, your final sent Message must mention the immediate next member.
When independent work can begin now, mention every immediate assignee. Re-read
your own last send before finishing and add one minimal routing line if the
required handoff is missing.

Never end having "answered" only in your transcript - that reply does not
exist for anyone else.
