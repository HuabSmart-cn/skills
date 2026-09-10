# Himalaya 2 configuration

This package targets Himalaya `2.0.0` at revision `923414155f4281d681f4ea8631954f406acf51ee`.

## Active configuration

For normal operations, run the executable resolved in `SKILL.md` and pass no `--config`. On macOS and Windows that is always the bundled copy, never a `himalaya` from `PATH`; on platforms this package does not ship a build for, it is the validated `v2.0.0` from `PATH` that `SKILL.md` permits. It may already have an active configuration selected; confirm what it sees with:

```bash
himalaya --json account list
```

Do not choose a configuration by scanning files, and do not replace the active configuration just because another TOML file exists.

When the native executable has not been given an active configuration, Himalaya searches:

1. `$XDG_CONFIG_HOME/himalaya/config.toml`
2. `$HOME/.config/himalaya/config.toml`

On Windows the equivalent location is `%APPDATA%\himalaya\config.toml`. Write configuration only to these paths: a file placed anywhere else looks saved while `account list` keeps reporting no account.

The global `--config <path>` option explicitly selects another profile. Use it only when the user requests a separate profile; do not use it for ordinary account discovery, validation, or mailbox operations.

## Store the mailbox secret

IMAP/SMTP secrets (Gmail app password, QQ authorization code, iCloud app-specific password, NetEase 客户端授权码, or another provider secret) are entered through the bundled helper. The user never uses a terminal.

Never run the bare `himalaya` setup wizard. That wizard needs a real terminal this chat does not have and dumps implementation details to the user.

Use the `cola-credential-helper` command Cola put on `PATH`. If the command is missing, the mailbox is not ready — do not fall back to a wizard, chat, or `password.raw`. When writing Himalaya `password.command`, store the absolute path from `command -v cola-credential-helper` (Windows: ***REDACTED***

1. After the user has generated the provider secret, run:

***REDACTED***
cola-credential-helper prompt \
  --account universal-email/<key> \
  --title-en "<title>" \
  --title-zh "<title>" \
  --secret-label-en "<label>" \
  --secret-label-zh "<label>"
```

**Prefer running `prompt` with `run_in_background: true`.** You will be notified with the result when the dialog settles — do not poll `bash_output` while waiting. Every path is bounded (the dialog waits 180 seconds, the local page 300), and a foreground call that hits the bash timeout is not killed — it converts to a background session and notifies the same way — but starting in the background keeps the conversation responsive from the first second. This works on Windows too.

The helper shows a Cola-styled dialog window (a system WebView) and brings it to the front. **A window that appears settles the flow — no second prompt opens behind it.** Saving returns `ok`; cancel or closing the window returns `用户取消了`; 180 seconds without a save returns `输入超时，未收到密钥`; the local page's own timeout returns `Configuration timed out`. Cancel and either timeout are safe to retry. Any *other* message means the save itself failed — tell the user saving did not go through, in your own words, and stop instead of prompting again.

**Fallbacks are for a window that did not work**, not for one the user ignored: the system password dialog (macOS `display dialog`, Windows a small password window) when the WebView cannot be created, then a local HTML page when that dialog cannot run either. Those hops happen silently inside the same call — you cannot announce them in advance; a returned `"ui": "html"`, or a `Configuration timed out`, is how you learn afterwards that the local page was used. That page has no cancel button: it fails 300 seconds after opening (requests to it do not extend that). On the system dialog an empty save reopens the window — it has no inline error area — but the 180-second budget keeps running, so that path ends on time too.

Secrets go to Cola's owner-only `~/.cola/credentials/secrets.json` with account `universal-email/<key>`; only `cola-credential-helper read` retrieves them, and it hands them to Himalaya to authenticate against the provider. Storage is local — the secret still travels to the mail server on every connection, so never tell the user it never leaves their machine.

**对用户表达的要点与示例。** 下面的句子用于说明必须传达的信息，措辞可结合上下文自然调整。聊天只收邮箱地址。生成密钥的具体链接和菜单在各 provider 指南里。收密钥时必须先说明窗口即将出现，并在同一轮立刻跑 `prompt`，不要再等一句聊天。

- 问地址：「把要连接的邮箱地址发我。应用专用密码或授权码不要发到聊天里。」
- 弹窗前（同一轮启动 `prompt`）：「屏幕上马上会弹出一个系统窗口。把刚生成的应用专用密码或授权码填进去，点保存。不要粘贴到聊天里。」
- `prompt` 成功：「已经收下了，我继续连。」（回落路径上系统还会闪一个"已保存"提示框，macOS 几秒后自动消失，Windows 要用户点一下确定）
- 上一轮走了本机页面、需要重来：「上次窗口没能弹出来，走的是浏览器里那个本机页面。我再来一次。」
- 用户点了取消：「窗口取消了。要继续连的话跟我说一声，我会再弹一次。」
- 窗口超时：「窗口等太久关掉了。跟我说一声，我会再弹一次。」
- 本机页面超时：「浏览器里那个页面等太久失效了，别再往里填。跟我说一声，我重新开一次。」
- 用户把密钥发到聊天：「不要发在聊天里。先去作废这一串，重新生成一串。生成后跟我说，我会弹出窗口让你填。」

Never say only “我会在本机安全输入框中接收它”.

2. Write the Himalaya 2 account into the active configuration using the templates below. Point both IMAP and SMTP `password.command` at the helper `read` and the same `--account`. Use a TOML literal string for a Windows path so `\Users` is not parsed as an escape (`\U`). Forward slashes also work on Windows. Never `password.raw`. Never put the secret in a command argument or in the TOML file.

| Provider | `--account` | Himalaya account name |
| --- | --- | --- |
| Gmail (personal or Workspace) | `universal-email/gmail` | `gmail` |
| QQ Mail | `universal-email/qq` | `qq` |
| iCloud Mail | `universal-email/icloud` | `icloud` |
| NetEase `@163.com` | `universal-email/163` | `163` |
| NetEase `@126.com` | `universal-email/126` | `126` |
| NetEase `@yeah.net` | `universal-email/yeah` | `yeah` |
| Other IMAP/SMTP | `universal-email/<name>` | `<name>` — `name` may contain only ASCII letters, digits, `-`, and `_` |

Provider guides supply the title and secret-label values. Do not show `--account`, the helper path, or credential-storage details to the user.

If `prompt` does not return `ok`, do not write TOML. For a cancel or a timeout, tell the user the input did not finish and that they can try again. For any other failure the save itself broke — say so plainly and stop; do not re-prompt and do not paste the raw message. If they paste a secret in chat anyway, do not store it: ***REDACTED***

## Minimal IMAP and SMTP account

```toml
[accounts.personal]
email = "user@example.com"
display-name = "User"
default = true

mailbox.alias.inbox = "INBOX"
mailbox.alias.sent = "Sent"
mailbox.alias.drafts = "Drafts"
mailbox.alias.trash = "Trash"

imap.server = "imaps://imap.example.com:993"
imap.sasl.plain.username = "user@example.com"
imap.sasl.plain.password.command = ***REDACTED***

smtp.server = "smtps://smtp.example.com:465"
smtp.sasl.plain.username = "user@example.com"
smtp.sasl.plain.password.command = ***REDACTED***
```

For STARTTLS, use the cleartext scheme and opt in explicitly:

```toml
smtp.server = "smtp://smtp.example.com:587"
smtp.starttls = true
```

Use `imap://...` plus `imap.starttls = true` for IMAP STARTTLS. Do not combine an implicit-TLS scheme such as `imaps://` or `smtps://` with `starttls = true`.

`password.command` must be the bundled helper `read`. Himalaya prints that command's stdout as the secret; `read` writes only the secret.

## Gmail IMAP/SMTP

```toml
[accounts.gmail]
email = "you@gmail.com"
display-name = "Your Name"
default = true

mailbox.alias.inbox = "INBOX"
mailbox.alias.sent = "[Gmail]/Sent Mail"
mailbox.alias.drafts = "[Gmail]/Drafts"
mailbox.alias.trash = "[Gmail]/Trash"
mailbox.alias.archive = "[Gmail]/All Mail"

imap.server = "imaps://imap.googlemail.com:993"
imap.sasl.plain.username = "you@gmail.com"
imap.sasl.plain.password.command = ***REDACTED***

smtp.server = "smtps://smtp.gmail.com:465"
smtp.sasl.plain.username = "you@gmail.com"
smtp.sasl.plain.password.command = ***REDACTED***
```

Use a Google app password, not the normal account password. The helper strips display spaces from the 16-character app password.

## QQ Mail IMAP/SMTP

```toml
[accounts.qq]
email = "you@qq.com"
display-name = "Your Name"
default = true

mailbox.alias.inbox = "INBOX"

imap.server = "imaps://imap.qq.com:993"
imap.sasl.plain.username = "you@qq.com"
imap.sasl.plain.password.command = ***REDACTED***
imap.id.auto = true

smtp.server = "smtps://smtp.qq.com:465"
smtp.sasl.plain.username = "you@qq.com"
smtp.sasl.plain.password.command = ***REDACTED***
```

QQ requires `imap.id.auto = true`. Use the client authorization code, not the QQ login password.

## iCloud IMAP/SMTP

```toml
[accounts.icloud]
email = "you@icloud.com"
display-name = "Your Name"

mailbox.alias.inbox = "INBOX"

imap.server = "imaps://imap.mail.me.com:993"
imap.sasl.plain.username = "you@icloud.com"
imap.sasl.plain.password.command = ***REDACTED***

smtp.server = "smtp://smtp.mail.me.com:587"
smtp.starttls = true
smtp.sasl.plain.username = "you@icloud.com"
smtp.sasl.plain.password.command = ***REDACTED***
```

Discover the actual mailbox names with `mailbox list` before adding Sent, Drafts, or Trash aliases.

## NetEase Mail IMAP/SMTP

Use the host that matches the address. Replace `163` below with `126` or `yeah` for those domains (`imap.126.com` / `smtp.126.com`, `imap.yeah.net` / `smtp.yeah.net`).

```toml
[accounts.163]
email = "you@163.com"
display-name = "Your Name"
default = true

mailbox.alias.inbox = "INBOX"

imap.server = "imaps://imap.163.com:993"
imap.sasl.plain.username = "you@163.com"
imap.sasl.plain.password.command = ***REDACTED***

smtp.server = "smtps://smtp.163.com:465"
smtp.sasl.plain.username = "you@163.com"
smtp.sasl.plain.password.command = ***REDACTED***
```

Use the 客户端授权码, not the NetEase login password. Guide the user with the official FAQ in `netease.md`.

## Provider compatibility options

Some providers require extra IMAP behavior:

```toml
# Coremail providers that reject SASL initial response
imap.sasl-ir = false

# Providers that require an RFC 2971 ID exchange
imap.id.auto = true
```

Only enable these when the provider guide requires them.

## Validate

Configuration-only parse check using the active configuration:

```bash
himalaya --json account list
```

Connection and authentication check, on the first wrap from `proxy.md`:

```bash
himalaya --account <name> --log-level debug --json account check
```

The list command proves only that the TOML matches Himalaya 2. The check exercises configured backends. If it times out, follow Route fallback in `proxy.md` — next wrap, do not stop. Split `--backend imap` / `--backend smtp` only when debug shows they failed at different stages.
