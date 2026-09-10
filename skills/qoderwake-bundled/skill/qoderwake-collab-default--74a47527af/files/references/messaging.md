# Default Conversation messaging reference

All commands talk to the local daemon. In JSON mode (`--json`) stdout is pure
JSON for scripting.

## Product surfaces are not session commands

- Thread / 临时讨论 is a standalone temporary message stream that cannot
  start a nested Discussion.
- Conversation / 会话 can start Discussions from root messages.
- Group / 群组 contains multiple Conversations.
- Discussion / 讨论 is a child message stream rooted at one Conversation
  message.
- Section / 分组 is only a sidebar category.
- Session / 任务会话 is a waker task/execution session.

There is no `qoderwake thread` command. To create a temporary Thread, direct
the user to the Console's left “新建” menu and “临时讨论”; never substitute
`qoderwake session create`.

There is no `qoderwake discussion` command. Never translate “create a
Discussion / 创建讨论” into `qoderwake session create`: those are different
objects. The current Console does not expose Discussion creation or entry, so
state that the surface is currently unavailable instead of naming a hidden
action. If the current Run is already inside an existing Discussion, reply in
that current stream normally.

## group

```bash
qoderwake group create [--title <t>] [--waker <idOrName>]...   # create a group, prints conv_id
qoderwake group list [--json]                                  # TITLE | CONV_ID | CREATED_AT
qoderwake group show <group>                                   # details + member table
qoderwake group add-waker <group> --waker <idOrName>...        # idempotent member add
```

`<group>` resolves as: exact conv_id, unique conv_id prefix, or unique title.
Ambiguous or unknown handles fail with the candidate list.

## messages

```bash
qoderwake messages list <convId> [--after-seq <n>] [--limit <n>] [--follow]
qoderwake messages send <convId> --text "<text>" \
    [--mention <idOrName>]... [--image <path>]... [--model <m>] \
    [--wait] [--timeout <secs>]
```

- As a waker your sender identity resolves automatically from
  `QODERWAKE_PARTICIPANT_ID` + `QODERWAKE_RUN_TOKEN`; without them the command
  sends as the human console-user.
- `--mention` wakes that member (`deliveryPolicy=wake`,
  `intent=request_action`). Without mentions the message is stored only.
  Plain `@name` text in `--text` is display-only and wakes nobody.
- `--image` accepts png/jpg/jpeg/gif/webp files.
- `--wait` (with mentions) tracks the wake runs to a terminal state and prints
  the replies. Exit codes: 0 ok, 1 generic error, 2 a wake run failed,
  3 wait timed out.
- `--follow` polls every 2s and prints new messages until Ctrl-C.

Examples:

```bash
# reply in your current conversation
qoderwake messages send "$QODERWAKE_CONVERSATION_ID" --text "Done: tests pass."

# multiline reply - pass real newlines
qoderwake messages send "$QODERWAKE_CONVERSATION_ID" --text "$(cat <<'EOF'
Summary:
- fixed the parser
- added a regression test
EOF
)"

# hand off to another member who must act next
qoderwake messages send "$QODERWAKE_CONVERSATION_ID" \
  --text "Reviewer needed on the fix above." --mention ReviewBot

# read recent context before answering
qoderwake messages list "$QODERWAKE_CONVERSATION_ID" --limit 30
```

## Delegated private sends

When asked to send another member a private message, the private message is
the requested result. Send it directly with both routing flags:

```bash
qoderwake messages send "$QODERWAKE_CONVERSATION_ID" \
  --text "..." \
  --private-to <recipient> \
  --mention <recipient>
```

Treat the target as actionable unless the requester explicitly says the
message is record-only. Do not replace this command with a public “sent”
acknowledgement, do not post a second public acknowledgement after success,
and never claim success if the command failed or was not run. If no body was
supplied, use a short neutral private test/greeting.

## runs

```bash
qoderwake runs list <convId>      # RUN_ID | PARTICIPANT | STATUS | ERROR
qoderwake runs cancel <runId>     # idempotent cancel
```

## CLI resolution

The daemon puts the matching `qoderwake` CLI first on your PATH and exports
its absolute path as `QODERWAKE_CLI`. Plain `qoderwake ...` is expected to
work. Never go hunting for other installations (`which`, Homebrew paths,
`~/.qoderwake/bin`, npm globals): an unrelated install may lack the
conversations commands entirely. If plain `qoderwake` is somehow missing,
invoke the absolute path stored in the `QODERWAKE_CLI` environment variable
directly.

## Safe retry rule

`messages send` is idempotent per invocation (each invocation generates its
own idempotency key). Therefore:

- If the command clearly succeeded, never re-send the same reply.
- If the command clearly failed (non-zero exit, error printed), fix the cause
  and send once.
- Replay only on truly unknown outcomes (e.g. the process was killed mid-send
  and you cannot tell whether the message landed). Check with
  `qoderwake messages list` first; if your message is already there, do not
  send again.
