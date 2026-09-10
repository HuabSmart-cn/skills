# Gmail

Gmail uses IMAP/SMTP and a Google app password. Personal Gmail and Google Workspace Gmail use the same connection method. They differ only in whether Google will issue an app password.

## What the user needs

- the full Gmail or Workspace address;
- a newly generated 16-character app password.

Do not ask for the normal Google password or any Google OAuth client credential.

## Personal Gmail vs Google Workspace

| Account | How to tell | What changes |
| --- | --- | --- |
| Personal Gmail | `@gmail.com` or `@googlemail.com` | The user turns on 2-Step Verification, then creates an app password. |
| Google Workspace | Company or school domain hosted by Google | Same IMAP/SMTP hosts and the same app password, **if** the organization allows app passwords. If the admin disabled them, or the account uses Advanced Protection or security-key-only 2-Step Verification, this skill cannot connect. |

Ask once only when the domain does not make it obvious. Do not invent a Google mail OAuth flow.

## 对用户表达的要点与示例

保留下列事实、安全提醒、官方链接和下一步；措辞可结合上下文自然调整。

1. 「把要连接的 Gmail 地址发我。应用专用密码不要发到聊天里。」
2. If they do not yet have an app password, use these exact official URLs directly; do not search for replacements. Give this as the user-facing guide:

***REDACTED***

先完成 Google 两步验证：https://myaccount.google.com/signinoptions/two-step-verification

再打开官方应用专用密码页面：https://myaccount.google.com/apppasswords

创建一组新的 16 位应用专用密码，名称填 Cola。生成后告诉我一声，不要把密码发到聊天里；我会弹出系统窗口让你填写，并继续完成刚才的邮件操作。」

3. If https://myaccount.google.com/apppasswords shows 「您的账号不支持您正在尝试的设置」:

「这是 Google 的页面，不是 Cola 连不上。个人 Gmail 一般是还没开两步验证：先去 https://myaccount.google.com/signinoptions/two-step-verification 做完，再回应用专用密码页。公司邮箱如果还是打不开，需要管理员开放应用专用密码，这个邮箱技能连不上。」

4. When they have generated the password: ***REDACTED***

5. After `account check` succeeds on a wrap: 「Gmail 已经连好了。以后直接说『看看今天的邮件』就行。」
6. After the fallback chain, IMAP works and SMTP does not: 「收信已经连上，发信这条路现在过不去。先看邮件可以。密码不用重新生成。」
7. After the fallback chain, SMTP works and IMAP does not: 「发信通道是通的，收信现在过不去。密码不用重新生成。」
8. After the whole chain, neither works: 「现在到邮箱服务的路都不通，不是密码错。邮箱配置还在，网络恢复后直接继续。」
9. If authentication fails after they filled the window (server responded, then rejected the secret): ***REDACTED***

A timeout with empty output is not authentication failure. Do not use line 9. Take the next wrap in `references/proxy.md`. Do not stop after one attempt.

## How to connect

1. Confirm the full address in chat using the guidance above.
2. Walk through 2-Step Verification and app password. Official help (user-facing): ***REDACTED***
3. Collect the app password with the bundled helper as described in `configuration.md`. Use `--account universal-email/gmail`, title `Connect Gmail` / `连接 Gmail`, secret label `App password` / `应用专用密码`. Never run the Himalaya wizard. Never open a terminal for the user.
4. Write the Gmail IMAP/SMTP account from `configuration.md`. Then run `himalaya --account gmail --log-level debug --json account check` on the first explicit wrap from `references/proxy.md`. If it fails at the network stage, continue the chain until one wrap succeeds, then reuse that wrap. Communicate the matching outcome above in natural language. This validation is for a newly connected or repaired account; an existing account's ordinary read task runs the requested IMAP operation directly and must not wait for SMTP validation.

## Validate and troubleshoot

If the server **rejects the secret after responding**, confirm the address, confirm they entered the new app password in the window (display spaces are stripped), and generate a new one if needed. Timeouts, TLS hangs, and empty wrapper kills are not that case — keep the stored secret and take the next wrap. A Workspace account that cannot create app passwords cannot be connected with this skill.

Reuse the wrap that succeeded for later commands in this session. If a later send fails while reads still work, retry that send on the next wrap only.
