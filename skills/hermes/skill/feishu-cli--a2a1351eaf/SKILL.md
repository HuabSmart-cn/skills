---
name: feishu-cli
description: "Install, isolate, authenticate, and operate the official Feishu/Lark CLI for Hermes without disturbing a user's existing global account or CLI configuration."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [feishu, lark, cli, oauth, mcp, productivity, isolation]
    related_skills: [chinese-productivity-doc-scrape]
---

# Official Feishu/Lark CLI

Use this skill when the user wants Hermes to operate Feishu/Lark directly, especially when they already have a globally installed CLI or an account logged in elsewhere and require a separate Hermes-only identity/configuration.

## Important distinction

Do not conflate these three products:

- **Official Feishu CLI**: package `@larksuite/cli`, executable `lark-cli`; it can initialize an app through a browser link/QR flow and supports user authorization with `lark-cli auth login`.
- **Official local OpenAPI MCP**: package `@larksuiteoapi/lark-mcp`; requires an App ID/App Secret and is a different integration path.
- **Feishu remote MCP configuration platform**: creates a temporary remote MCP server URL/JSON, currently documented as expiring after seven days for newly created services.

If the user remembers “the CLI gives me a link/QR code to create it”, that is the official `lark-cli config init --new` flow, not the local MCP package.

## Official installation

The upstream documentation currently gives:

```bash
npx @larksuite/cli@latest install
```

For Hermes-only isolation, prefer a private npm prefix rather than a global install:

```bash
mkdir -p "$HOME/.hermes/tools/lark-cli"
npm install --prefix "$HOME/.hermes/tools/lark-cli" @larksuite/cli@latest
LARK="$HOME/.hermes/tools/lark-cli/node_modules/.bin/lark-cli"
"$LARK" --version
```

Do not use `npm install -g` when the user explicitly asks not to affect their global CLI/account.

## Isolated state

Keep the executable and profile state under Hermes-owned paths. Use a named profile so the Hermes app is visibly separate from the user's existing default profile:

```bash
export HERMES_HOME="$HOME/.hermes"
export LARK_CLI_HOME="$HOME/.hermes/lark-cli"
LARK="$HOME/.hermes/tools/lark-cli/node_modules/.bin/lark-cli"
```

Before changing anything, record the global CLI path and status if present; after setup, verify that the global path and its status/configuration are unchanged. Never copy or overwrite the global credential store.

### Verify the CLI's actual state directory

Do not assume `LARK_CLI_HOME` relocates the official CLI's state. In the tested macOS CLI, app/profile state was written to `~/.lark-cli/`, with named-profile data in `~/.lark-cli/<profile>/config.json`; secrets are stored in macOS Keychain and referenced by ID. `HERMES_HOME` is relevant to Hermes, but is not proof that the third-party CLI has moved its own state. After setup, inspect the real files with read-only commands:

***REDACTED***
find "$HOME/.lark-cli" -maxdepth 3 -type f -print
"$LARK" config show
"$LARK" profile list
"$LARK" auth status --profile hermes-feishu
```

If the user asked for strict filesystem isolation, report this distinction clearly and do not claim full isolation merely because the executable is under `~/.hermes/tools/`. The reliable isolation achieved in this session was a private executable plus a separate named/profile config; the CLI's global default store remained separately observable at `~/.lark-cli/config.json`.

## Browser-link / QR initialization

The official CLI supports creating a new application through a browser-assisted flow:

```bash
"$LARK" config init --new --name hermes-feishu
```

The command may print a QR code plus a URL like:

```text
https://open.feishu.cn/page/cli?user_code=XXXX-XXXX&...
```

Run it in a tracked background process when the user needs time to open the link. Return the exact URL and verification code from real process output; never invent or paraphrase them. The process normally waits for the user to complete setup in the browser, then receives the app configuration.

Hermes contexts may cause the CLI to refuse initialization to avoid parallel apps. The help text explicitly recommends `config bind` for binding an existing app, and requires `--force-init` only when the user explicitly wants a separate app inside the Hermes workspace:

```bash
"$LARK" config init --new --name hermes-feishu --force-init --lang zh_cn
```

Use `--force-init` only after confirming the user's intent to create a separate app; do not silently choose it for an existing account.

## User authorization

After app initialization, authorize access as the user when personal calendar, messages, documents, mail, or other user-scoped data is needed:

```bash
"$LARK" auth login
"$LARK" auth status
"$LARK" auth check
```

The login command may open or print an authorization link. Tell the user which Feishu account will be authorized and wait for explicit completion before claiming success. For missing permissions, use the CLI's suggested scope/application-permission flow rather than guessing scopes.

Useful commands from the official guide:

```bash
"$LARK" config init
"$LARK" config bind
"$LARK" profile list
"$LARK" profile use <name>
"$LARK" --profile <name> <command>
"$LARK" auth logout
```

## User-authorization interaction details

`auth login` is an interactive TTY flow, not just a single browser launch. In a tracked PTY/background process it may first ask for business domains and then permission type. To select all displayed domains, use the UI's documented `ctrl+a` select-all shortcut, then Enter; typing `a` is not equivalent. Choose the permission tier explicitly (for example, 常用权限 vs 全部权限), confirm, and only then will the CLI print the device-verification URL and user code.

A generated device-verification URL is separate from the app-registration URL. Treat app creation and user OAuth as two checkpoints:

1. `config init --new` → browser app setup → App ID/config result.
2. `auth login` → select domains/scopes → browser device verification → token saved.

Use a PTY for both interactive commands and keep the process alive while the user opens the link. Poll/wait for the real completion output; do not report authorization success merely because a URL was printed.



```bash
"$LARK" config init --new --name bot-reader
"$LARK" profile list
"$LARK" profile use bot-reader
"$LARK" --profile bot-reader im send-message ...
```

For non-interactive App Secret input, use stdin rather than putting secrets in command arguments or process listings:

***REDACTED***
printf '%s' "$APP_SECRET" | "$LARK" profile add \
  --name bot-reader --app-id cli_xxx --app-secret-stdin
```

## Verification checklist

Before reporting completion:

1. `lark-cli --version` succeeds from the Hermes-private path.
2. The browser URL/QR was obtained from actual CLI output.
3. The user confirms the browser setup/authorization completed.
4. `auth status` and/or `profile list` show the Hermes profile as valid.
5. The global `lark-cli` path and status remain unchanged.
6. Explain what account identity is active and which data scopes are available.

## Inspecting a bitable (multi-dimensional table)

Feishu bitables are accessed via `lark-cli base`. The wiki URL token is NOT a valid `base_token` — it must be unwrapped first. Real session-tested recipe:

***REDACTED***
LARK="$HOME/.hermes/tools/lark-cli/node_modules/.bin/lark-cli"

# 1) Resolve a wiki/doc URL to the underlying real token + type
"$LARK" drive +inspect --url "<FEISHU_URL>"
#   -> returns { token, type:***REDACTED***

# 2) Get the base metadata with the UNWRAPPED token
"$LARK" base +base-get --base-token "<obj_token>"

# 3) List its tables
"$LARK" base +table-list --base-token "<obj_token>"

# 4) List a table's fields and records
"$LARK" base +field-list --base-token "<obj_token>" --table-id "<tblXXX>"
"$LARK" base +record-list --base-token "<obj_token>" --table-id "<tblXXX>" --limit 100
```

Flag name is `--base-token`, NOT `--app-token` (using `--app-token` returns "unknown flag"). The wiki token from the original URL will be rejected as `param baseToken is invalid` (code 800004006) by `base +base-get` / `+table-list` — always run `drive +inspect` first when the input is a URL or a wiki token.

## Copying / exporting a bitable

`base +base-copy` is the obvious shortcut but has two real failure modes worth knowing before promising a copy to the user:

1. It only copies the **structure** (tables, fields, views, dashboards); it does NOT copy records.
2. It can return `forbidden (code 800004011)` even when the user has full read access — the user identity needs a separate base-copy scope that `auth login` does not always grant.

When the user asks to "copy" a populated bitable, do not just run `+base-copy` — surface the three real options and ask which they want:

1. **Structure-only copy** — `lark-cli base +base-copy --base-token <base_token> --name "<copy-name>" --time-zone Asia/Shanghai`. Fast, no records. Source: ***REDACTED***
2. **XLSX export to Drive** — `lark-cli drive +export --url "<FEISHU_URL>" --file-extension xlsx` then `drive +upload` to a chosen folder. Preserves all rows/columns in spreadsheet form; loses bitable-specific things (formulas, automations, view filters, attachments). Good for backups.
3. **Full record-by-record replay** — create a new base, copy field schemas, then `+record-list` on each source table and `+record-batch-create` on the target. Slow (rate-limited) and can drop attachment/link fields. Use only when the user needs an editable copy with all rows. **The full recipe is in `references/bitable-read-copy-export.md`** (Step 0 → Step 6), covering: probing source data, the `+base-create` / `+table-create` / `+field-create` / `+field-delete` quirks, the field-name intersection trick, source-value coercion, 50-rows-per-batch rate-limit handling, and post-write verification.

Run the chosen command with `--dry-run` first and show the user the would-be request before any actual write.

## Pre-action confirmation for side-effecting operations

This skill's user is sensitive to anything that touches their real Feishu account. Default behavior for write/copy/move/delete/publish commands:

- Show the user a `--dry-run` of the exact command first.
- Print the diff (what would change, where, on which scope).
- Wait for explicit confirmation before re-running without `--dry-run`.
- High-risk writes (delete, move between accounts, publish) require the CLI's own `--yes` flag AND a second user confirmation.

This applies to: `base +base-copy`, `base +base-create`, `base +record-create/update/delete`, `drive +create-folder`, `drive +move`, `drive +delete`, `drive +upload`, anything in `im`/`mail` that sends or modifies.

## Plain-language re-explanation on confusion

When the user signals they don't understand ("听不懂", "什么意思", "我没明白", etc.), do NOT reply with a longer technical explanation. The signal means the previous response was over-jargonized. Re-do it in short, analogy-style Chinese with minimal Latin terms, then end with one concrete next-step question. Save the technical detail for after they confirm the analogy made sense.

## Pitfalls

- Do not answer a request for the official CLI with only an App ID/App Secret MCP JSON configuration.
- Do not claim that Hermes can create or authorize a Feishu app without the user opening the generated link and confirming in Feishu.
- Do not expose App Secrets or tokens in chat, shell history, process arguments, logs, or skill files.
- In interactive domain selection, use the CLI's documented `ctrl+a` select-all shortcut; sending the literal letter `a` may leave the selection empty or behave differently.
- App registration and user authorization are separate checkpoints and may generate different kinds of links: ***REDACTED***
- Keep exact URLs and codes from process output, but do not put App Secrets or access tokens in chat or persistent skill content.
- The base domain flag is `--base-token`, never `--app-token`. The wiki URL token is not a valid base token; always `drive +inspect` first.
- `base +base-copy` is structure-only. Do not let "copy" requests run it on populated bitables without confirming the user is okay losing records.
- `base +base-copy` may also return `forbidden (code 800004011)` even when the user has full read access — the user identity needs a separate base-copy scope that `auth login` does not always grant. When this fires, do not retry: pivot to Option 2 (XLSX export) or Option 3 (record-by-record replay). Full replay recipe is in `references/bitable-read-copy-export.md`.
- `+record-batch-create` is the ONLY record-write verb. There is no `+record-create` (singular). Use it with a one-row batch for "create one" operations.
- `+field-create` takes `--json` (single object), NOT `--field`. The wrong flag returns empty stdout without a useful error in some CLI versions — always confirm `"ok": true` in the response.
- When a target bitable is created via `+base-create`, the auto-shipped first table comes with 4 extra default columns (`日期/单选/附件/文本` in CN locale). When replaying records, ONLY pass source field names that exist in BOTH source and target. Including the defaults causes `code 800030201 not_found`.
- Source `select` cells in the wild often contain long free-text strings that are NOT in the declared `options` list. Detect this BEFORE replay (Step 0 in the recipe) and surface the count to the user — they will choose between keeping `select` (loses data) and re-creating the field as `text` (preserves data, type changes).
- Source values for `select` cells come back as either strings, dicts (`{"name":"x","hue":"Blue"}`), or arrays of dicts/strings. `+record-batch-create` rejects arrays and dicts on `text` fields with `code 800010407 "Provide a string value"`. Coerce to a single string in user code before batching.
- The documented `+record-batch-create` limit is 200 rows/call but the API frequently returns `code 800004135 "OpenAPIBatchAddRecords limited"` after 2-3 batches at that size. 50 rows/batch with a 2s sleep on limit errors is the practical sweet spot.
- LARK_CLI_HOME is NOT honored by the official CLI in the version tested; real state is in `~/.lark-cli/`. Setting it is harmless but misleading — verify with `find ~/.lark-cli -maxdepth 3 -type f` before claiming isolation is "complete".
- A backgrounded `config init --new` process may print the URL once and the process can exit or stall. If the user does not act in time, the registration times out with `token_expired`; the fix is to re-run the command and have the user open the new link immediately (link/codes are single-use).


## Authoritative references

See `references/official-feishu-cli.md` for the verified official documentation links and condensed command notes. For investigating an existing local Feishu bot without modifying it, use `references/read-only-bot-forensics.md`. For inspecting, reading, copying, or exporting a bitable (多维表格), see `references/bitable-read-copy-export.md` (token-type confusion, the `--base-token` vs `--app-token` flag trap, structure-only vs xlsx vs record-replay options, `--dry-run` confirmation pattern).
