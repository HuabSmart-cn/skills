# Registered DWS commands

Source DWS version: `v1.0.61-beta.1`

Registry revision: `dws-effective-v2:e268e2bcf76c2ff7e0d6b550a8a5b7766e58abe79afa8a4bc1a48462dc77ef04`

Use only the command shapes in this reference. Catalog-derived `read-only` and `guarded` commands
are temporarily disabled and are not registered for Waker Agent execution. Every invocation is one
simple shell command whose
first token is exactly `"$QODERWAKE_DWS_CLI_PATH"`. Single-quote user-provided values. Do not add
pipes, redirections, environment assignments, wrapper shells, or unlisted options.

The host rejects the command when any value would be expanded by the shell. `$QODERWAKE_DWS_CLI_PATH`
is the only expansion allowed, and it must be written so the shell really expands it:
`"$QODERWAKE_DWS_CLI_PATH"` or `$QODERWAKE_DWS_CLI_PATH`. A single-quoted or backslash-escaped
launcher is rejected, because the shell would then look for a command literally named
`$QODERWAKE_DWS_CLI_PATH` instead of running the managed launcher. Command substitution (`$(...)`,
backticks), arithmetic expansion, `$'...'` quoting and every other `$VAR` / `${VAR}` reference are
denied, including inside double quotes, because the shell expands them before the launcher runs.
Unquoted brace expansion, globbing (`*`, `?`, `[`) and a leading `~` are denied as well, because
they change the argv that was validated. Values that may contain `$`, backticks or glob characters
— reply titles, message bodies, anything copied from a chat — must be single-quoted. Escape embedded
single quotes with the shell-safe close/escaped-quote/reopen sequence; message content stays inline.

This file is aligned with `package/src/daemon/modules/DwsCommandRegistry.ts`. If a DWS module,
subcommand, option, or write operation is not listed here, it is not registered for Waker Agent
execution. Stop instead of guessing from general DWS CLI knowledge.

The examples use descriptive placeholders such as `<query>` and `<group-id>`. Replace each complete
placeholder with one shell-quoted value; do not retain angle brackets in the executed command.

## Profile discovery

```bash
"$QODERWAKE_DWS_CLI_PATH" profile list --format json
```

This is the only registered profile-management command. Use each returned `profile` selector with
`--profile '<corpId>:<userId>'` on a business command. Never invoke `profile switch`, `profile use`,
`auth login`, or `auth logout`.

## Shared argument rules

- Every command below is complete and uses the only supported launcher. Do not remove required
  options or invent aliases for listed options.
- `--format json` is the only documented output form. Keep it in every invocation.
- `--profile '<corpId>:<userId>'` is an optional global selector on every business command below.
  It selects one DWS identity for this invocation and does not change the default profile. Obtain the
  exact selector from `profile list`; do not guess names or IDs.
- Profile switching, login, logout, and per-session data authorization are not registered for
  Agent execution; the global `--profile` selector covers multi-organization work.
- `identifier` values must be non-empty and must not start with `-`.
- `csv-identifiers` means one or more identifiers joined by commas with no empty item. Pass the
  complete list as one quoted shell argument.
- `group-id` is a DingTalk group/conversation ID returned by `chat search`.
- `user-id` and `staff-id` refer to the DingTalk staff/user ID returned by managed lookup results.
- `open-dingtalk-id` is an `openDingTalkId`, not a staff/user ID. Use only the flag matching the ID
  type actually returned by lookup or message data.
- Time ranges should use explicit ISO-8601 date-times with timezone when possible, for example
  `2026-08-07T09:00:00+08:00`. Preserve an API-returned time or token exactly when continuing a read.
- Options marked `business_write` change remote state. Never retry them after an uncertain result.
- Message titles are limited to 100 Unicode code points; literal message text is limited to 8192
  Unicode code points.
- Options documented as `literalText` are always sent literally, including values beginning with
  `@`; they never read local files. Options documented as `inputFileRef` or `textInputFileRef`
  require an `@<managed-path>` value.
  The path must be inside the current session root; the host snapshots it and removes `@` internally
  only for DWS options that expect a plain file path. `dataOrFileRef` keeps `@` for DWS-native file
  loading. Uploads are limited to 50 MiB and managed UTF-8 data files to 10 MiB.
  **Platform restriction**: file-backed commands (`@file`) are only available on Linux. On macOS
  and Windows, sealed memfd input handles are structurally unavailable and the Wrapper rejects
  such commands with `denied_platform_unsupported`. For `--text` values, switch to inline
  single-quote escaping (replace `'` with `'\''`) instead of retrying `@file`. Upload and
  content-file options (`inputFileRef`, `textInputFileRef`, `dataOrFileRef`) have no inline
  alternative: stop and report to the user that the command is not supported on this platform.
- `outputPath` values are plain relative or absolute paths inside the current session root. Do not
  prefix them with `@`, use `~`, target an existing path, or write through a parent directory that
  does not already exist. The Wrapper stages the core download privately and commits it through a
  verified directory handle; platforms without that primitive reject the command. Download commands
  are classified as `business_write` because they write locally and must never be replayed after an
  uncertain result.
- A command whose required list includes `-y` is high impact. Obtain explicit confirmation for its
  concrete target and impact before running it; do not treat the host execution grant as that
  business confirmation.

## Registry scopes

| Capability | Operation | PAT scope | Registered commands |
|---|---|---|---|
| `contact.user.read` | read | `contact.user:read` | `contact user search` |
| `chat.group.read` | read | `chat.group:read` | `chat search`, `chat group members` |
| `chat.message.read` | read | `chat.message:list` | `chat message list`, `chat message list-direct` |
| `chat.user.send` | business write | `chat.message:send` | `chat message send` |
| `chat.bot.send` | business write | `chat.message:send-by-bot` | `chat message send-by-bot` |
| `chat.message.recall` | business write | `chat.message:send` | `chat message recall` |
| `chat.bot.recall` | business write | `chat.message:send-by-bot` | `chat message recall-by-bot` |
| `wiki.space.read` | read | `wiki.space:read` | `wiki space search/get/list` |
| `doc.document.read` | read | `doc.document:read` | `doc list/search/info/read` |
| `calendar.event.read` | read | `calendar.event:read` | `calendar event list/get` |
| `calendar.event.write` | business write | `calendar.event:write` | `calendar event create` |
| `calendar.room.read` | read | `calendar.room:read` | `calendar room search` |
| `calendar.room.write` | business write | `calendar.room:write` | `calendar room add` |
| `minutes.read` | read | `minutes` | `minutes list`, `minutes get info/summary/transcription/todos` |
| `todo.task.read` | read | `todo` | `todo task list/get` |
| `todo.task.write` | business write | `todo` | `todo task create/update/done` |
| `mail.message.read` | read | `mail.message:read` | mailbox list, message search/get, attachment list |
| `mail.message.write` | business write | `mail.message:write` | message send |
| `oa.approval.read` | read | `oa.approval:read` | approval lists/detail/records/tasks |
| `oa.approval.write` | business write | `oa.approval:write` | approve/reject/revoke/redirect-task |
| `attendance.read` | read | `attendance.record:read` | record/group/summary/vacation reads |
| `report.read` | read | `report.entry:read` | templates, inbox/outbox, entry get/stats |
| `report.write` | business write | `report.entry:write` | entry submit |
| `ding.message.write` | business write | `ding.message:write` | message send/recall |
| `drive.file.read` | read or local write | `drive.file:read` | spaces/list/info/download |
| `drive.file.write` | business write | `drive.file:write` | mkdir/upload/delete |
| `sheet.read` | read | `sheet.document:read` | list/info/range read |
| `sheet.write` | business write | `sheet.document:write` | create/new/range update/append/csv-put/delete-sheet |
| `aitable.read` | read | `aitable.record:read` | Base/table/field/record/view reads |
| `aitable.write` | business write | `aitable.record:write` | Base/table/field/record writes |
| `doc.document.write` | business write | `doc.document:write` | create/update/upload |
| `calendar.participant.read` | read | `calendar.event:read` | participant list |
| `calendar.participant.write` | business write | `calendar.event:write` | participant add/delete |

## Contacts and chats

### Search for a person

Required: `--query`, `--format json`. Use `--query`, not `--keyword`.

```bash
"$QODERWAKE_DWS_CLI_PATH" contact user search --query '<name-or-keyword>' --format json
```

### Search for a group

Required: `--query`, `--format json`. Optional: `--limit`, `--cursor`, and `--exclude-muted`.
Preserve the returned cursor exactly when another page is needed.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat search --query '<group-name-or-keyword>' --format json
```

### List group members

Required: `--id`, `--format json`. Optional: `--cursor`; preserve a returned cursor exactly.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat group members --id '<group-id>' --format json
```

### List group messages

Required: `--conversation-id`, `--time`, `--format json`. Optional: `--limit` in `1..100` and
`--direction newer|older`.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message list --conversation-id '<group-id>' --time '<iso-time>' --limit 50 --format json
```

### List direct messages

Required: `--time`, `--format json`, plus exactly one identity selector:

- `--user "<user-id>"`; or
- `--open-dingtalk-id "<open-dingtalk-id>"`.

Optional: `--limit` in `1..100` and `--direction newer|older`. Do not pass both identity selectors.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message list-direct --user '<user-id>' --time '<iso-time>' --limit 50 --format json
```

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message list-direct --open-dingtalk-id "<open-dingtalk-id>" --time "<iso-time>" --limit 50 --format json
```

### Send a user or group message

This is `business_write`.

Required:

- exactly one target selector: `--conversation-id`, `--user`, or `--open-dingtalk-id`;
- at least one content selector: `--content` for text/Markdown or `--msg-type` for a registered rich-media form;
- `--format json` in the managed command shape.

`--title` is optional in DWS 1.0.61-beta.1. Optional delivery controls include `--idempotency-key`, `--at-all`, and
`--at-open-dingtalk-ids`. Rich media uses the registered `--msg-type`, `--file`, `--media-id`,
location, or contact-card options; local files must use a managed `@./...` reference.

The locked DWS CLI version does not expose `--at-users` for this command. Resolve staff/user IDs to
`openDingTalkId` before sending a notification mention. Never guess `--mention`, `--mentions`, or
`--at`. The mention option is for `--conversation-id`; omit it for direct messages.

A group mention is complete only when the notification option and visible message text agree:

- `--at-open-dingtalk-ids "openId1,openId2"` selects who receives the DingTalk mention notification;
- the message body must visibly contain the matching names in the same order, for example
  `@刘潘 你好（测试）` or `@刘潘 @张三 你好（测试）`;
- every visible `@DisplayName` must be followed by at least one ASCII space or a newline;
- never send a mention option with plain text such as `你好（测试）`, because the recipient is not
  visibly identified in the message;
- if the exact visible mention prefix already exists, do not add it again;
- resolve display names and IDs before sending. If a display name cannot be resolved, ask the user.

`--content` and `--title` are literal strings in the locked DWS version. Pass visible mentions such as
`--content "@刘潘 你好（测试）"` directly; do not create a temporary message file or use an
`@./<file>` indirection.

Direct message by staff/user ID:

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message send -y --user '<user-id>' --title '<title>' --content '<message>' --format json
```

Direct message by `openDingTalkId`:

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message send -y --open-dingtalk-id '<open-dingtalk-id>' --title '<title>' --content '<message>' --format json
```

Group message mentioning `openDingTalkId` values. Keep the visible names in the same order as the ID
list and pass the complete text inline:

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message send -y --conversation-id "<group-id>" --title "<title>" --content "@<display-name> <message>" --at-open-dingtalk-ids "<open-dingtalk-id-list>" --format json
```

### Send with a bot

This is `business_write`.

Required: `--robot-code`, `--title`, `--text`, and `--format json` in the managed command shape. Use
exactly one target form:

- `--group "<group-id>"` for a group;
- `--users "<staff-id-list>"` for comma-separated direct recipients; or
- `--open-dingtalk-ids "<open-dingtalk-id-list>"` for direct recipients identified by open ID.

Optional group mention controls are `--at-all`, `--at-user-ids`, and `--at-open-dingtalk-ids`.

Bot group message:

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message send-by-bot -y --robot-code '<robot-code>' --group '<group-id>' --title '<title>' --text '<message>' --format json
```

Bot direct message:

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message send-by-bot -y --robot-code '<robot-code>' --users '<staff-id-list>' --title '<title>' --text '<message>' --format json
```

### Recall a message

Recall is a high-impact `business_write`. Run it only after the user explicitly identifies or asks
to recall the concrete message. A successful or uncertain recall must never be retried.

For a regular message, use the `message-id` and `conversation-id` returned by a managed message
operation. The locked DWS command uses `--message-id`; do not substitute the legacy `--msg-id` flag.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message recall -y --conversation-id '<conversation-id>' --message-id '<message-id>' --format json
```

For a bot group message, use the `processQueryKey` returned by the send result as `--keys`. The
locked Catalog accepts exactly one conversation selector (`--group` or `--conversation-id`); prefer
`--group` for a known group. For a bot direct message, omit both conversation selectors. Multiple
keys are comma-separated identifiers.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message recall-by-bot -y --robot-code '<robot-code>' --group '<group-id>' --keys '<process-query-key-list>' --format json
```

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message recall-by-bot -y --robot-code '<robot-code>' --keys '<process-query-key-list>' --format json
```

### Download a message media file

This is `business_write` (it writes a local file and must never be replayed after an uncertain
result).

Required: `--message-id`, `--open-conversation-id`, `--resource-id`, `--type`, `--output`, and
`--format json`. `--output` is an `outputPath` value: a plain relative path inside the current
session root that does not yet exist.

```bash
"$QODERWAKE_DWS_CLI_PATH" chat message download-media --message-id '<message-id>' --open-conversation-id '<conversation-id>' --resource-id '<resource-id>' --type '<type>' --output './<file>' --format json
```

## Managed local-file commands

Local file arguments are only available on the commands documented here (plus `doc upload`,
`doc download`, `doc read`, `doc create`, `doc update`, `chat message send`, and `chat message
download-media` above). Input options (`inputFileRef`/`textInputFileRef`) require a managed
`@./<path>` reference inside the session root; `outputPath` options require a plain relative path
inside the session root that does not yet exist. All of these are `business_write` and must never
be replayed. Platform restriction: file-backed commands are only available on Linux.

```bash
"$QODERWAKE_DWS_CLI_PATH" todo task add-attachment --task-id '<task-id>' --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" doc media insert --node '<node-id>' --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" doc style cover set --node '<node-id>' --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" aitable record upsert --base-id '<base-id>' --table-id '<table-id>' --records-file '@./<records.json>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet import create --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet media-upload --node '<node-id>' --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet write-image --node '<node-id>' --sheet-id '<sheet-id>' --range '<range>' --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet create-float-image --node '<node-id>' --sheet-id '<sheet-id>' --range '<range>' --width 400 --height 300 --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet update-float-image --node '<node-id>' --sheet-id '<sheet-id>' --float-image-id '<image-id>' --file '@./<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet export --node '<node-id>' --output './<file>' --format json
```
```bash
"$QODERWAKE_DWS_CLI_PATH" sheet export-csv --node '<node-id>' --output './<file>.csv' --format json
```

## Knowledge spaces and documents

Search knowledge spaces. Required: `--format json` and at least one of `--query` or
`--type myWikiSpace`. Optional: `--limit` in `1..20`.

```bash
"$QODERWAKE_DWS_CLI_PATH" wiki space search --query '<space-keyword>' --format json
```

Get one knowledge space. Required: `--workspace`, `--format json`. `--workspace` accepts the ID or URL.

```bash
"$QODERWAKE_DWS_CLI_PATH" wiki space get --workspace '<workspace-id-or-url>' --format json
```

List knowledge spaces. Required: `--format json`. Optional: `--type` with exactly
`myWikiSpace` or `orgWikiSpace`, `--limit` in `1..50`, and `--cursor`. Preserve a returned cursor
exactly.

```bash
"$QODERWAKE_DWS_CLI_PATH" wiki space list --format json
```

List documents in a workspace. Required: `--workspace`, `--format json`. Resolve the workspace
first. Optional: `--folder`, `--limit` in `1..50`, and `--cursor`. Preserve a returned cursor exactly.

```bash
"$QODERWAKE_DWS_CLI_PATH" doc list --workspace '<workspace-id-or-url>' --format json
```

Search documents. Only `--format json` is required; the registry permits a search without filters.
Optional filters are:

- `--query "<text>"`;
- comma-separated lists: `--workspace-ids`, `--extensions`, `--creator-uids`, `--editor-uids`,
  `--mentioned-uids`;
- `--limit` in `1..30` and `--cursor`;
- non-negative integer values: `--created-from`, `--created-to`, `--visited-from`, `--visited-to`.

Do not invent singular aliases for plural options.

```bash
"$QODERWAKE_DWS_CLI_PATH" doc search --query '<document-keyword>' --format json
```

Get document metadata. Required: `--node`, `--format json`.

```bash
"$QODERWAKE_DWS_CLI_PATH" doc info --node '<node-id-or-url>' --format json
```

Read document content. Required: `--node`, `--format json`. Optional: `--content-format
markdown|jsonml`; JSONML reads may use `--scope outline|range|section|tags`, block boundaries,
`--max-depth`, `--tags`, and a managed plain `--output` path.

```bash
"$QODERWAKE_DWS_CLI_PATH" doc read --node '<node-id-or-url>' --format json
```

For knowledge-space browsing, first resolve the workspace, then list its documents, then read the
selected node. Do not use a space name as `doc search --query` unless the user explicitly wants a
document-content search.

## Calendar and rooms

### List events

Required: `--format json`. Optional: `--calendar-id`, `--start`, `--end`, `--limit`, and `--cursor`.
Prefer an explicit ISO-8601 range with timezone and preserve a returned cursor exactly.

```bash
"$QODERWAKE_DWS_CLI_PATH" calendar event list --start "<iso-start>" --end "<iso-end>" --format json
```

### Get one event

Get one event. Required: `--id`, `--format json`. Optional: `--calendar-id` for a non-primary
calendar.

```bash
"$QODERWAKE_DWS_CLI_PATH" calendar event get --id '<event-id>' --format json
```

### Create an event

This is `business_write`.

Required: `--title`, `--start`, `--end`, `--format json`. DWS 1.0.61-beta.1 additionally supports
`--calendar-id`, descriptions, timezone, attendees/open IDs, `--location`, `--free-busy`, reminders,
rooms, and a complete `--recurrence-*` pattern/range set. Once any recurrence option is used,
`--recurrence-type`, `--recurrence-interval`, and `--recurrence-range-type` must be supplied together.

```bash
"$QODERWAKE_DWS_CLI_PATH" calendar event create --title '<title>' --start '<iso-start>' --end '<iso-end>' --desc '<description>' --timezone 'Asia/Shanghai' --attendees '<staff-id-list>' --format json
```

### Search available rooms

Required: `--format json`. Optional: `--start`, `--end`, `--group-id`, `--room-name`, `--page`,
and `--limit`. Omitting the time range uses DWS defaults.

```bash
"$QODERWAKE_DWS_CLI_PATH" calendar room search --start '<iso-start>' --end '<iso-end>' --group-id '<room-group-id>' --format json
```

### Add rooms to an event

This is `business_write`. Required: `--event`, `--rooms`, `--format json`. Optional:
`--calendar-id`. `--rooms` is one quoted, comma-separated room-ID list.

```bash
"$QODERWAKE_DWS_CLI_PATH" calendar room add --event '<event-id>' --rooms '<room-id-list>' --format json
```

Create the event first and add rooms second. Do not create a duplicate event merely to change room
bookings.

## AI minutes

### List minutes

Required: exactly one positional scope (`all`, `mine`, or `shared`) and `--format json`. Optional:
`--query`, `--start`, `--end`, `--limit` in `1..100`, and `--cursor`. Prefer `all` unless the user
requests a narrower scope. Preserve `--cursor` exactly.

```bash
"$QODERWAKE_DWS_CLI_PATH" minutes list all --query "<keyword>" --start "<start-time>" --end "<end-time>" --limit 50 --format json
```

### Get minutes metadata

Required: `--id`, `--format json`.

```bash
"$QODERWAKE_DWS_CLI_PATH" minutes get info --id '<task-id>' --format json
```

### Get the summary

Required: `--id`, `--format json`.

```bash
"$QODERWAKE_DWS_CLI_PATH" minutes get summary --id '<task-id>' --format json
```

### Get a transcription page

Required: `--id`, `--direction`, `--format json`. `--direction` must be `0` for forward order or `1`
for reverse order. Optional: `--cursor`; preserve it exactly.

```bash
"$QODERWAKE_DWS_CLI_PATH" minutes get transcription --id '<task-id>' --direction 0 --format json
```

### Get extracted todos

Required: `--id`, `--format json`. This command only reads todos extracted from minutes; it does not
create or modify DingTalk Todo tasks.

```bash
"$QODERWAKE_DWS_CLI_PATH" minutes get todos --id '<task-id>' --format json
```

## DingTalk Todo tasks

### Create a todo

This is `business_write`. Required: `--title`, `--executors`, `--format json`. Optional: `--due`,
`--priority` (`10`, `20`, `30`, or `40`), and `--recurrence`; recurrence requires a due time.

```bash
"$QODERWAKE_DWS_CLI_PATH" todo task create --title '<title>' --executors '<staff-id-list>' --format json
```

### List todos

Required: `--format json`. Optional: `--page`, `--size` in `1..20`, boolean `--status`,
`--role-types creator,executor,participant`, `--priority 10|20|30|40`, ISO-8601 planned-finish range,
and `--query-all` when the request explicitly spans all organizations.

```bash
"$QODERWAKE_DWS_CLI_PATH" todo task list --format json
```

### Get a todo

Required: `--task-id`, `--format json`.

```bash
"$QODERWAKE_DWS_CLI_PATH" todo task get --task-id '<task-id>' --format json
```

### Update a todo

This is `business_write`. Required: `--task-id`, `--format json`, and at least one of `--title`,
`--due`, `--priority`, or `--done`.

```bash
"$QODERWAKE_DWS_CLI_PATH" todo task update --task-id '<task-id>' --title '<title>' --format json
```

### Set todo completion

This is `business_write`. Required: `--task-id`, `--status` (`true` or `false`), `--format json`.

```bash
"$QODERWAKE_DWS_CLI_PATH" todo task done --task-id '<task-id>' --status true --format json
```

## Mail

Use `mailbox list` to resolve the current user's mailbox instead of guessing an address. Search
requires `--email`, `--query`; optional `--cursor`, `--limit` (`1..100`). Get and attachment list
require `--email` plus the returned message ID. Send is `business_write` and requires `--from`,
comma-separated `--to`, `--subject`, and `--content`; optional `--cc`, repeatable managed
`--attachment @./...`, and repeatable managed `--inline-attachment @./...`. Attachment download
and other mail management operations (move

... [Content truncated, total 43,242 chars] ...