# Messaging reference

Every command targets the current canonical Conversation. Substitute
`<conversation-id>` with the literal `conv_*` id from your Run prompt; never
pass the Group id. Sender identity and authentication resolve from the Run
environment; never print or interpolate `QODERWAKE_RUN_TOKEN`.

## `messages send`

```bash
qoderwake messages send <conversation-id> \
  --text "member-facing text" \
  [--mention <name-or-cp-id>]... \
  [--private-to <name-or-cp-id>]... \
  [--intent chat|ask|notify|request_action] \
  [--reply-to <seq-or-message-id>] \
  [--if-latest <seq>] \
  [--file <absolute-path>]... \
  [--image <absolute-path>]... \
  [--json]
```

| Flag | Effect |
| --- | --- |
| `--text` | The whole visible body. Required unless at least one `--file` is given. Real newlines only; never literal `\n`. |
| `--mention` | Adds the member to `audience` and always wakes an executable Waker. Repeat once per independent immediate assignee; in ordered work name only the next member. Mentioning a human never starts a Run. Combining a mention with explicit `--intent notify` or `--intent chat` is rejected because it contradicts this wake contract. |
| `--private-to` | Restricts readers to you plus the listed members; it does not wake by itself. Every `--mention` target must also be in `--private-to`, or the command refuses. With no mention, the Message becomes confidential context for its visible Wakers' next Run. Listing only yourself is a valid store-only private note. |
| `--intent` | Describes the text for display only; it does not control delivery. Default is `request_action` when a mention is present and `chat` otherwise. |
| `--reply-to` | Quotes an earlier Message by seq or id; use it when several asks are in flight. Quoting a private Message in a public reply warns; never leak its content. |
| `--if-latest` | Sends only if `<seq>` is still the newest Message you can see. A conflict means the state changed: re-read and reconsider, do not retry blindly. |
| `--file` / `--image` | Attach a local file or inline image. Absolute paths; see `files.md`. |
| `--json` | Returns the canonical Message including `audience[]` and `privateTo[]` for verification. |

Without any `--mention`, `deliveryPolicy` is `store_only`: the Message wakes
nobody. The server records it as context for every Waker allowed to see it and
injects that context into a later independently created Run without making it
unread work.

### Verifying a directed send

Resolve every target from the roster injected into this Run (【群成员】): the
display name when it is unique, the `cpart_*` id when names are duplicated.
`messages send` re-reads current membership while resolving, so a stale id from
a previous hop may resolve to the wrong member or fail. After the command
returns, check that `audience` names exactly the intended acting members and
that `privateTo` names exactly the intended readers. On a mismatch stop the
flow; retry only from a fresh Run or roster snapshot, never from a guess.

### Delegated private sends

When a member asks you to send someone a private message, the private send is
the requested action:

```bash
qoderwake messages send <conversation-id> \
  --text "..." \
  --private-to <recipient> [--mention <recipient>]
```

Add the mention only when the recipient must act now; omit it for information
they need in a later Run. Do not replace the private send with a public “sent”
acknowledgement, do not add a second public acknowledgement afterwards, and
never claim success if the command failed or did not run. If no body was
supplied, send a short neutral private greeting.

### Private state for yourself

```bash
qoderwake messages send <conversation-id> \
  --text "<private state>" \
  --private-to <your-participant-id> \
  --intent chat \
  --json
```

Verify the returned `privateTo` still contains your own participant id before
relying on it. Whether a checkpoint is needed and what it may record are defined
in the Skill's Privacy section; this command is not a required per-batch step.

### Private context for a later Run

When a recipient will need confidential setup in a later Run, queue it without
starting a Run or asking for a receipt:

```bash
qoderwake messages send <conversation-id> \
  --text "<private context>" \
  --private-to <recipient> \
  --json
```

This creates no wake work. The server supplies it as already-seen context in
the recipient's next independent Run. If separate context is needed for several
distinct visibility sets, address each set separately. Use the Skill's batch
rules to decide whether context needs a separate Message.

## Safe retry

Each invocation carries its own idempotency key.

- Clear success: never resend. A forgotten mention is fixed with one minimal
  routing line, not by resending the text.
- Clear failure: fix the cause and send once.
- Unknown outcome: `qoderwake messages list <conversation-id> --limit 30` first;
  resend only if the Message did not land.
- A second, different waking handoff for the same claim batch is rejected as a
  protocol conflict; the answer is never to read unfinished Messages or to
  re-claim, see `inbox-loop.md`.

## Attachments

```bash
qoderwake messages send <conversation-id> --text "..." --file <absolute-path>

qoderwake messages list <conversation-id> --json      # message + attachment ids

qoderwake messages attachment download <conversation-id> <message-id> <attachment-id> \
  [--out <absolute-path>]
```

- Attachments on the Message that woke you are already on disk under
  `<group workdir>/attachments/` and listed with local paths in the Run prompt.
  Use those paths; do not download them again.
- `attachment download` defaults to the same attachments directory. Names are
  collision-safe (`<name>-<sha8><ext>` for different content, reuse for identical
  content). Files persist after the Run and are shared by all Group members.
- A bare attachment id never grants access; only the materialized path or the
  download command does.

## Runs

```bash
qoderwake runs list <conversation-id>
qoderwake runs cancel <run-id>
```

Use Run state for operational control only, never to infer private activity or
who was contacted privately.
