---
name: universal-email
description: Use the bundled Himalaya 2 CLI to connect IMAP/SMTP or Microsoft Graph mailboxes and list, search, read, compose, reply, forward, move, delete, flag, and download email. Use when the user asks to connect or operate Gmail, QQ Mail, iCloud Mail, Outlook, NetEase Mail (163/126/yeah), or another standard mailbox, or says "连接邮箱"、"绑定邮箱"、"看看我的邮件"、"查邮箱"、"发邮件"、"回复邮件"、"连网易邮箱"、"连163邮箱".
metadata:
  version: 1.2.32
  category: integration
  requires:
    bins: ["himalaya"]
---

# Email (universal-email)

## Serve the user the Cola way

These rules govern what you communicate to the user. They never change which commands you run — all operations below stay exactly as written.

### 连接引导

如果用户指定的邮箱尚未连接，连接该邮箱就是完成原请求的必要前置步骤。

首次配置时，主动告诉用户：「首次配置会多花一点时间，但只需要完成一次。配置好后，就可以直接用 Cola 查看和处理邮件啦。」同一次连接流程只说一次。

使用上下文中已有的邮箱地址、服务商和连接所需信息，不重复询问已经明确的信息。

确定连接方式后，先简要列出完整的连接流程，让用户了解后续步骤；再根据当前进度，详细引导用户完成当前一步。

如果服务商同时提供官方操作文档和可直接打开的官方授权或设置入口，两者都提供给用户，方便用户快速操作。

连接并验证成功后，立即继续用户最初要求的查看、搜索、回复或发送操作。

- **Adapt the phrasing to the conversation.** User-facing sentences in `references/` wrapped in 「」 are examples, not scripts. Preserve their required facts, safety boundaries, official URLs, current action, and next step, but phrase them naturally for the user's language and context. Do not repeat information the user already supplied.
- **Product words are fine.** 配置、授权、连接、账号、授权码、应用专用密码 — the user should always know which step they are in.
- **Implementation details never reach the user.** `himalaya`, CLI, config files, TOML, PATH, keychain service names — say “你的邮箱” instead.
- **Use provider protocol names only when actionable.** You may say IMAP, SMTP, or POP3 when the user must select that named option in the provider's settings, when explaining a supported connection choice, or when the user asks about protocols. Otherwise say “收信” or “发信”.
- **Ask for the minimum, once.** Chat only takes the email address (and, if the domain is not Gmail/QQ/iCloud/Outlook/NetEase 163/126/yeah, which service hosts it). Then follow the communication guidance in that provider guide. Workspace vs personal Gmail: `references/gmail.md`. NetEase: `references/netease.md` — always give the official FAQ URL in that guide; do not treat 163/126/yeah as generic IMAP.
- **Credentials never enter the conversation.** Never ask them to paste an app password or authorization code in chat. When collecting the secret, follow the communication guidance in `references/configuration.md`: ***REDACTED***
- **Translate errors into next steps.** Never paste raw command output. Preserve the relevant diagnosis and next action from the provider guide while adapting the wording.
- **Confirm in user terms.** Confirm the outcome described in the provider guide in natural language.

Use the bundled `himalaya` executable. This Skill targets exactly Himalaya `2.0.0` at revision `923414155f4281d681f4ea8631954f406acf51ee`; do not use Himalaya 1.x configuration fields or command examples.

## Locate the executable

Cola exposes `himalaya`, `cola-credential-helper`, and `cola-outlook-mail-auth` on `PATH` at startup (wrappers over this skill's bundled binaries). Run those bare command names. Do not search `scripts/bin`, and do not use another copy from the user's machine.

If `himalaya` is missing, report that the mailbox is not ready yet — never describe it as an account problem or a broken connector. This skill ships on macOS and Windows only. Confirm `himalaya --version` reports `v2.0.0` before configuring an account.

You run `cola-credential-helper prompt` for IMAP/SMTP secrets (Gmail, QQ Mail, iCloud Mail, NetEase Mail, other IMAP), preferably as a background command. It shows a Cola-styled dialog window, falling back to a system password dialog and then a local HTML page only when a window cannot be shown. Himalaya later reads the secret with `cola-credential-helper read`. Never ask the user to run it, and never paste its path into chat. See `references/configuration.md`.

You run `cola-outlook-mail-auth` for Outlook / Microsoft 365 Graph mail. Never ask the user to run it, and never paste its path into chat. See `references/outlook.md`. Do not use the Himalaya setup wizard for any provider.

Treat the active configuration of the executable you invoke as the source of truth: do not inspect candidate config files to choose one, or add `--config` merely because a file exists. Use `--config` only when the user explicitly requests a separate profile.

## 使用场景

- 绑定邮箱:"帮我连一下 QQ 邮箱""绑定我的 Gmail""连一下网易邮箱""绑定163邮箱"
- 日常收发:"看看今天有什么新邮件""把这封转发给 Alice""回复他说我明天到"
- 整理与查找:"找一下上周报销相关的邮件""把这封标成已读""删掉这封"

## Choose the account

1. Confirm `himalaya --version` reports `himalaya v2.0.0`.
2. Run `himalaya --json account list`.
3. If the intended account exists, select it with the global `--account <name>` option.
4. If it does not exist, read the matching provider guide before asking the user for anything:
   - Gmail: `references/gmail.md`
   - QQ Mail: `references/qq.md`
   - iCloud Mail: `references/icloud.md`
   - NetEase Mail (`@163.com`, `@126.com`, `@yeah.net`, or the user says 网易邮箱): `references/netease.md`. Give the official FAQ URL in that guide; do not use `standard-imap-smtp.md`.
   - Outlook/Microsoft 365: `references/outlook.md` (Graph OAuth via the bundled helper; never the Himalaya wizard). Do not send an app-password or IMAP help link; this path does not collect a code.
   - Other IMAP/SMTP: `references/standard-imap-smtp.md`
5. If configuration is missing, use `references/configuration.md` for secret collection (system dialog, HTML fallback) and the Himalaya 2 TOML format.
6. If the account already exists, perform the user's requested operation immediately with the normal `himalaya` command and a 25-second tool timeout. If it succeeds, continue the task without inspecting or changing routing. Do not run `account check` before an ordinary read task; it also tests SMTP and can delay a working IMAP read.
7. Read `references/proxy.md` only when the requested operation fails at the network stage, the user explicitly asks to use or diagnose a proxy, or the current task otherwise requires a specific route. Then retry the same operation on distinct explicit wraps from that guide. Stop at the first success and reuse that wrap for the rest of the session. Use `account check` only after creating or repairing an account, or when the requested operation does not reveal the failing backend. Outlook Graph follows `references/outlook.md`.

Do not ask for a normal account password when the provider requires an app password, authorization code, or OAuth. Never echo a secret, put it in command arguments, or store it as `password.raw`. Never run the Himalaya wizard or any other terminal UI.

## Read operations

Prefer global `--json` for machine-readable output.

```bash
himalaya --account <name> --json mailbox list
himalaya --account <name> --json envelope list --mailbox inbox --page 1 --page-size 20
himalaya --account <name> --json envelope search --mailbox inbox from alice@example.com and subject report
himalaya --account <name> --json message read --mailbox inbox <message-id>
himalaya --account <name> --json attachment list --mailbox inbox <message-id>
himalaya --account <name> attachment download --mailbox inbox --dir <directory> <message-id> <attachment-id>
```

IDs are scoped to their mailbox. Re-list after switching mailboxes or after move/delete operations. Do not repeatedly fetch the same message when one `message read --json` result already contains the needed fields.

## Write operations

Show the final recipients, subject, and body to the user and obtain confirmation immediately before sending, replying, forwarding, moving, or deleting.

**Check the backend before writing.** `message compose|reply|forward --send` routes through SMTP or JMAP only, so an account on the Microsoft Graph backend cannot send with it. Read the account's backend from `account list` first; for a Graph account, send through `himalaya msgraph message send` with raw MIME and read `references/outlook.md` before composing.

**`--from` is required on every compose, reply, and forward.** Do not omit it. Himalaya 2 does not copy `email` from the account config into `From:`; without the flag the message has no sender. `--send` still opens IMAP/SMTP, then fails with `No From: header` — on a slow connection that looks like a timeout, not a missing flag.

- Use the connected mailbox address from this conversation (the address used to connect). `account list` returns only name and backends, not the email. Do not use the example placeholder. Do not invent another address.
- This `--from` is the sender address. `message move --from` / `message copy --from` is a mailbox name. They are not the same flag.
- If send times out, hangs, or returns no result: inspect the command you ran. If `--from` is missing, add the connected address and retry that one send. Do not treat it as a proxy or network failure yet.

```bash
himalaya --account <name> message compose \
  --from <connected-mailbox-address> \
  --to recipient@example.com \
  --subject "Subject" \
  --body "Body" \
  --send

himalaya --account <name> message reply --mailbox inbox \
  --from <connected-mailbox-address> \
  --body "Reply body" --send <message-id>

himalaya --account <name> message forward --mailbox inbox \
  --from <connected-mailbox-address> \
  --to recipient@example.com --body "Forward note" --send <message-id>
```

For attachments and raw RFC 5322 messages, read `references/message-composition.md`.

Never retry a send automatically after an ambiguous error. SMTP delivery can succeed before saving a copy to the Sent mailbox fails; verify delivery before any retry.

## Organize mail

```bash
himalaya --account <name> message move --from inbox --to archive <message-id>
himalaya --account <name> message copy --from inbox --to important <message-id>
himalaya --account <name> flag add --mailbox inbox --flag seen <message-id>
himalaya --account <name> flag remove --mailbox inbox --flag seen <message-id>
himalaya --account <name> message delete --mailbox inbox <message-id>
```

`message delete` is trash-first, but permanently removes messages already in trash. State this consequence and get explicit confirmation.

## Network and troubleshooting

Himalaya 2 supports SOCKS5 and HTTP CONNECT, and takes its route **only** from the environment of each invocation. Operating-system proxy settings are a discovery source, not a route: a proxy configured in macOS or Windows settings but absent from the process environment is not used, so reading it and then running the command unchanged tests the direct route while appearing to test the proxy. To exercise a discovered setting, pass it explicitly in that invocation's environment, and preserve the protocol exactly as reported — never infer one from a port number.

Himalaya has no proxy configuration field or CLI flag: the route comes only from the environment of each invocation, and this build reads exactly two variables — `all_proxy` first, then `https_proxy`. **`http_proxy` is not consulted at all**, so a proxy supplied only through it is silently ignored and the command runs direct; carry such a value over into `https_proxy` for the invocation. This environment is the one lever for per-command route isolation. To force a single command onto the direct route, clear the proxy variables for that invocation only, without touching the user's global proxy. Unset **both** letter cases: Cola writes `ALL_PROXY` / `HTTPS_PROXY`; a shell may write `all_proxy` / `https_proxy`. If `ALL_PROXY` remains, Himalaya is still on the proxy. On macOS:

```bash
env -u all_proxy -u ALL_PROXY -u https_proxy -u HTTPS_PROXY -u http_proxy -u HTTP_PROXY \
  himalaya --account <name> ...
```

In PowerShell, `env` does not exist, so scope the change to the process instead:

```powershell
# A child process, so the user's proxy stays intact in this session.
powershell -NoProfile -Command @'
Remove-Item Env:all_proxy,Env:ALL_PROXY,Env:https_proxy,Env:HTTPS_PROXY,Env:http_proxy,Env:HTTP_PROXY -ErrorAction SilentlyContinue
& '<himalaya>' --account <name> ...
'@
```

Never assign `$env:` values directly in the working session: they persist, and every later command would silently run without the user's proxy. Confirm the route actually used from Himalaya's own `dial <host>:<port> ... (source: direct|all_proxy|https_proxy)` debug line rather than assuming it.

The first ordinary mailbox operation may use bare `himalaya`: if the device's normal route works, no proxy diagnosis is needed. After a network failure, or when a specific route is required, read `references/proxy.md`. In that recovery flow, a mixed SOCKS + HTTP environment must use explicit per-command wraps so the higher-priority `all_proxy` value does not silently defeat the intended route. Some networks require the proxy and some require direct access; the ordered fallback decides from observed results instead of hard-coding one route for every user.

Outlook Graph setup (`cola-outlook-mail-auth connect` / `doctor` / `token`) is HTTPS to Microsoft, not IMAP/SMTP. Wrap those helper invocations the same way when a proxy is required; leave `status` and `configure` unwrapped; keep loopback off the proxy so the OAuth callback can return. See `references/outlook.md` (Network).

Read `references/proxy.md` before proxy-specific recovery or diagnosis when any of these conditions applies:

- the provider may require a proxy on the user's current network;
- proxy variables or an operating-system proxy are present;
- the failure mentions proxy, timeout, DNS/connect, TLS, unreachable service, or an incomplete SOCKS handshake;
- IMAP works but SMTP fails, or the reverse;
- changing between direct and proxied routing changes the result.

That guide defines the routing defaults for Gmail, QQ Mail, iCloud Mail, NetEase Mail, Outlook, and custom IMAP/SMTP; macOS and Windows proxy discovery; per-command route isolation; and error-specific recovery. Do not ask the user to edit global proxy settings.

Use its error mapping as recovery guidance. When an observed error matches a known case, move the diagnosis in the stated direction using the current device's available controls. Do not merely restate the protocol, port, or timeout to the user and stop, and do not assume that every device exposes proxy controls in the same way.

Use the actual CLI path on the current wrap:

```bash
himalaya --account <name> --log-level debug --json account check
```

Verify the selected route from Himalaya's own debug line before interpreting the result. Do not use `nc`, `telnet`, or a direct socket probe as proof of Himalaya connectivity because those checks bypass its proxy selection. Read `references/troubleshooting.md` for non-network failures and the staged diagnostic flow.

Do not discard the diagnostic stages before interpreting a timeout. Inspect the bounded command output first, then retain and report only safe route and stage information.
