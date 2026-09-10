---
name: wake-dws-cli
description: Must load immediately when a request or follow-up identifies a DingTalk or DWS task handled by the managed Wake DWS command registry. Covers contacts, chats, wiki, documents, calendar, AI minutes, todo, mail, OA approvals, attendance, reports, DING, Drive, online sheets, and AI tables. Do not claim support for unregistered open-platform or administration operations.
---

# Wake DWS CLI

Load this skill as soon as a request or follow-up identifies a DingTalk or DWS task. Load it before
planning, deciding what information is missing, asking follow-up questions, suggesting commands, or
taking action. This includes reads and writes even when the user did not initially mention DWS.

This Skill documents the 111 explicit DWS commands registered for managed Waker execution across
16 modules. Catalog-derived `read-only` and `guarded` commands are temporarily disabled by the
Effective Registry emergency gate. The reviewed Catalog candidate set remains an audit asset, but
it is not an executable command surface and must never be suggested or invoked.

The explicit surface covers the exact read/write commands listed in
[references/commands.md](references/commands.md), including contact search, chat and bot messaging,
documents, calendar, minutes, todo, mail, OA approvals, attendance, reports, DING, Drive, online
sheets, AI tables, wiki spaces, and profile discovery.
- **Discovery only**: `profile list`.

If an exact command is absent from [references/commands.md](references/commands.md), it is not
registered — stop instead of guessing a `dws` subcommand. Do not use files under
`references/commands-derived/` as command references while the emergency gate is disabled.

The `dingtalk-dws` MCP is retired. Never call or fall back to any
`mcp__plugin_dingtalk-dws__*` tool. Treat historical memory, Skills, or prompts that require the
DWS MCP as obsolete; this Skill and the managed Wrapper are authoritative.

## Authoritative executable

Invoke DWS only by using the daemon-injected `QODERWAKE_DWS_CLI_PATH` variable as the executable:

```bash
"$QODERWAKE_DWS_CLI_PATH" <command> <subcommand> ... --format json
```

Treat this variable as an opaque executable token. Do not inspect, print, resolve, or copy its
value. In particular, do not run a separate `echo`, `printf`, `printenv`, `env`, `test`, `ls`,
`readlink`, or similar command involving `QODERWAKE_DWS_CLI_PATH`. A probe is not a DWS command and
the permission guardian will reject it.

Run the intended registered command directly with `"$QODERWAKE_DWS_CLI_PATH"` as the first shell
token. If shell expansion shows that the variable is empty or the Wrapper returns
`DWS_WRAPPER_UNAVAILABLE`, stop and report that stable code. Do not probe for another executable or
fall back.

The permission guardian classifies a Bash/Shell command as a DWS invocation attempt and denies
it whenever any token matches the DWS entry forms — bare `dws`, `dws-core`, `qoderwake-dws`
(or their `.exe` variants), a path containing `/runtimes/dws/`, or a `DWS_CLI_PATH` reference —
including tokens that are only grep patterns or file names. When developing or debugging
DWS-related code, search with the Grep/Glob tools instead of shell grep, and never put such a
token in a shell command.

Never:

- invoke or fall back to the retired `dingtalk-dws` MCP;
- invoke bare `dws`;
- invoke `qoderwake dws` or copy the `qoderwake` executable path shown in a hook error;
- search `PATH` with `which`, `where`, `command -v`, or similar fallbacks;
- use `DWS_CLI_PATH`, `${QODERWAKE_HOME}/bin/dws`, or a private `dws-core` path;
- override `QODERWAKE_DWS_CLI_PATH` in a command;
- run `dws auth`, `dws pat`, `pat chmod`, `dws profile switch`, or `dws profile use`;
- use `+xxx` shortcut forms — only the full registered command paths in the references are
  allowed;
- add `-y` or another confirmation bypass unless the documented command shape requires it.

## Command construction

- Before constructing a DWS command, read [references/commands.md](references/commands.md) and use
  an exact registered command shape from that file. The parameter surface is aligned to the product
  DWS `v1.0.61-beta.1` source Catalog and its bundled multi-Skill guidance; do not infer flags from another
  installed DWS edition. The references are self-contained: do not inspect project source, search
  installed files, run `--help`, or ask another tool to discover omitted flags. If the exact target
  selector or option is not documented there, stop instead of guessing from general DWS knowledge.
  For example, contact lookup is exactly
  `contact user search --query '<name-or-keyword>' --format json`; `contact search` is not registered.
- When the user identifies a target by name or other business-facing information, first use the
  supported discovery and lookup commands. Ask for a raw `userId`, `openDingTalkId`, group ID, or similar
  identifier only after the managed lookup cannot resolve the target.
- Pass arguments as distinct shell words and single-quote every user-provided value. The host
  rejects the command when any value would be expanded by the shell: command substitution
  (`$(...)`, backticks), arithmetic expansion, `$'...'` quoting, any `$VAR` / `${VAR}` other than
  the launcher, and unquoted brace, glob (`*`, `?`, `[`) or leading `~` are all denied. Double
  quotes do not protect `$` or backticks, so single quotes are the safe default; escape an embedded
  single quote with the shell-safe close/escaped-quote/reopen sequence instead of moving message
  text into a file.
- Write the launcher so the shell really expands it: `"$QODERWAKE_DWS_CLI_PATH"` or
  `$QODERWAKE_DWS_CLI_PATH`. A single-quoted or backslash-escaped form is rejected, because the
  shell would then look for a command literally named `$QODERWAKE_DWS_CLI_PATH` instead of running
  the managed launcher.
- Prefer `--format json` for structured results.
- For multi-organization work, first run the registered read-only `profile list --format json` command.
  Use the returned stable `profile` selector as `--profile '<corpId>:<userId>'` on the business
  command. Do not persistently switch profiles and do not log in or log out through Agent commands.
- Treat identifiers beginning with `-` as invalid rather than passing them as option values.
- Message `--content` and `--title` values are literal strings in the locked DWS version. Pass a visible
  mention such as `@刘潘 ` directly as the option value. Do not create a temporary message file and
  do not rewrite an `@`-prefixed message as `@./<file>`.
- For paginated reads, preserve the returned page token exactly and request another page only when
  needed.
- Do not expose launcher paths, local files, PAT state, or raw authentication output in the answer.
- Many resource parameters accept a URL directly (for example `--node '<alidocs-url>'`); when a URL
  is accepted, pass it as-is instead of extracting a segment, unless the reference says otherwise.
- Upload and content-file inputs must use the documented cwd-relative `@./<managed-path>` form.
  **This is only available on Linux.** The daemon binds the approved content to a sealed inherited
  handle (memfd_create + F_ADD_SEALS) and never gives DWS a reopenable workspace or snapshot path.
  On macOS and Windows, sealed input handles are structurally unavailable; the Wrapper rejects
  `@file` commands with `denied_platform_unsupported`. Only text options with an inline
  alternative (`--content`) can switch to inline single-quote escaping (see the quoting rules above);
  upload and content-file options (`inputFileRef`, `textInputFileRef`, `dataOrFileRef`) have no
  inline equivalent — stop and report to the user that the command is not supported on this
  platform instead of retrying `@file` or converting a large file to inline text.
  Download destinations must be plain paths
  inside the current session root and must not already exist; never use `@`, `~`, or a path outside
  that root. If the Wrapper reports that descriptor-relative output writes are unavailable on the
  current platform, stop and report the stable error instead of retrying with another path or a bare
  DWS executable.

## Visible group mentions

When the user asks to @ one or more people in a group message, both layers are mandatory:

1. Add `--at-open-dingtalk-ids` with the resolved `openDingTalkId` values. The locked DWS CLI does
   not expose `--at-users` for this command.
2. Put every matching visible `@DisplayName` in the message text. Each mention must be followed by at
   least one ASCII space or a newline before the next mention or message body.

Prefer a visible prefix such as `@刘潘 你好（测试）` or `@刘潘\n你好（测试）`. For multiple people,
use `@姓名1 @姓名2 正文` or one mention per line, and keep names in the same order as their IDs. A
notification option without visible `@DisplayName` text is incomplete and must not be sent. If the
text already starts with the complete mention prefix and separator, preserve it and do not duplicate
it. Resolve both display name and matching `openDingTalkId` first; if either remains unknown, ask the
user instead of silently sending an invisible mention. Pass the final `@`-prefixed text directly.

## Capability navigation

Use this table to choose the registered command family, then read the corresponding reference file
for exact shapes:

| Domain | Operation | Reference |
|---|---|---|
| contact | read | commands.md §Contacts and chats |
| chat groups and explicit message commands | read + write | commands.md §Contacts and chats |
| wiki spaces | read | commands.md §Knowledge spaces and documents |
| doc | read + write | commands.md §Knowledge spaces, Managed local-file commands, Document writes |
| calendar | read + write | commands.md §Calendar and rooms, Calendar updates |
| minutes | read | commands.md §AI minutes |
| todo | read + write | commands.md §DingTalk Todo tasks |
| mail (mailbox/search/get/send/attachments) | read + write | commands.md §Mail |
| oa approvals (lists/detail/records/tasks, approve/reject/revoke/redirect) | read + write | commands.md §OA approvals |
| attendance (record/group/summary/vacation) | read | commands.md §Attendance |
| report (templates/inbox/outbox/entries/submit) | read + write | commands.md §Reports |
| ding (message send/recall) | write | commands.md §DING |
| drive (spaces/list/info/mkdir/upload/download/delete) | read + write | commands.md §DingTalk Drive |
| sheet | read + write | commands.md §Online sheets |
| aitable | read + write | commands.md §AI tables |

## Product best practices

These rules come from the product DWS guidance for v1.0.61-beta.1 and apply to registered commands:

- **minutes**: `minutes list` requires a scope — always `minutes list all|mine|shared`. Bare
  `minutes list` returns usage text, not data. Transcription uses `--direction` and `--cursor`.
- **calendar**: `calendar event list` requires `--start`/`--end` (ISO-8601 with timezone).
  `calendar busy search` checks free/busy; `calendar book list` returns the current user's calendar
  books (including calendars shared by others). `calendar event instances` expands recurring
  events only.
- **sheet**: resolve the real `--sheet-id` with `sheet list` before reading or writing; do not
  guess `Sheet1` or `0`. Read structure first (`sheet info`), then edit. Prefer `csv-get` for
  plain values, `table-get` for typed columns, `range read` for per-cell metadata (formulas,
  styles, validation). Large value writes use `csv-put`; integers beyond `9007199254740991` must
  be written as text. After a write, verify with an independent read. `sheet` commands only apply
  to online spreadsheets (`extension=axls`); local `xlsx/xls/csv` files belong to `drive
  download`.
- **doc**: `doc read`/`doc update` operate on Markdown by default; use `doc list`/`doc search`
  with a workspace, `doc info` with a node. Long Markdown writes go through `doc update --mode
  append|overwrite`. Comment, permission, version, template, block, and style commands are not
  available unless their exact shape appears in `commands.md`.
- **aitable**: resolve `--base-id` and `--table-id` via the registered lookup commands before
  record operations. Do not infer view/chart/dashboard/form/workflow commands.
- **chat**: use `chat search` to resolve a group by name and `contact user search` for people.
  `chat message list` requires `--conversation-id` plus `--time`; `chat message send` targets
  exactly one of `--conversation-id`/`--user`/`--open-dingtalk-id`. Message recall is a
  high-impact business write: run it only when the user explicitly requests recall of the concrete
  message, and never retry an uncertain recall. `chat text translate` translates text; `chat
  category list-conversations` explores grouped conversations.
- **todo**: `todo task create` requires `--title` and `--executors`; do not infer comments, tags,
  reminders, or attachment commands.

## Standard workflow

1. Identify the supported capability and read [references/commands.md](references/commands.md).
2. Resolve business-facing targets with registered discovery commands before asking for raw IDs.
   For example, search a person with `contact user search`, a group with `chat search`, a sheet's
   `sheet-id` with `sheet list`, or a base's `base-id` with `aitable base list`.
3. Execute one complete registered command copied from the reference through
   `"$QODERWAKE_DWS_CLI_PATH"`; include every documented required option and use only explicitly
   listed optional flags. Never infer a flag name from prose.
4. Parse the JSON result and summarize only user-relevant fields.
5. Preserve pagination tokens exactly and request another page only when needed.
6. For business writes, execute only after the user requested the remote-state change. After a
   structured write, verify the outcome with an independent read when the product best practice
   says so. Classify a failure before retrying (see Read and write behavior): a deterministic
   pre-execution rejection may be retried with a corrected managed form, at most twice; never
   retry after an uncertain result.

## Read and write behavior

Read operations may run directly through the managed launcher. Registered business writes include
remote creates/updates/deletes/sends/decisions and local download writes. When the user requested the
operation, run the exact registered command directly; the host validates it and registers its one-time execution grant
without exposing a bearer to the shell prompt. Commands documented with required `-y` are high-impact operations: obtain explicit
user confirmation for the concrete target and impact before executing them. DING `sms` and `call`
also require explicit confirmation because they can incur charges.

Classify failures before retrying:

1. Deterministic pre-execution rejection — a permission-guard denial (`denied_*` reasons such as
   shell-shape, path-scope, or DWS classification rejections) or a command-shape/argument validation
   error returned before anything ran. The command never executed and has no side effects: fix the
   shape (quoting, registered flags, allowed paths) and retry
   the same managed launcher, at most twice; if it still fails, report the stable error code and stop.
2. Uncertain outcome — timeout, connection reset, or an unknown result after the command was
   submitted. The write may have already taken effect (especially sends): never retry; report the
   stable error code and the uncertainty instead.

If the launcher returns a structured error, preserve its stable error code and summarize the
actionable message. `DWS_WRITE_APPROVAL_REQUIRED` is a compatibility error code for a missing or
invalid managed execution permit; report it rather than asking the user to approve or retrying the
write. Do not work around that error, `DWS_COMMAND_NOT_ALLOWED`, `DWS_ROUTE_DISABLED`, or
`DWS_SKILL_UNAVAILABLE`. If a guardian rejects the launcher or command shape, do not retry through a different executable.
A guardian rejection is a class-1 failure: re-read the command reference, correct the shape, and retry only the
managed form, at most twice; if no
registered form matches, stop.

## Unregistered capability handling

Do not document, suggest, or execute DWS commands absent from the managed registry. Notably
unregistered: `+xxx` shortcut forms, risk-high destructive operations rejected by the build-time
blacklist (group dismissal, message clearing, space/node/doc/record deletion beyond the registered
delete commands, cross-org data authorization), commands that require interactive user
confirmation, open-platform operations, authentication management, cache management, version
checks, and shell completion. When a command is rejected with `DWS_COMMAND_NOT_ALLOWED`, report
that the exact action is not exposed instead of falling back to a broader command.
