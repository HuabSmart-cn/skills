# iCloud Mail

iCloud Mail uses IMAP/SMTP and an Apple app-specific password.

## What the user needs

- the complete iCloud Mail address;
- an app-specific password generated for this mail client.

Do not ask for the Apple Account password.

## 对用户表达的要点与示例

保留下列事实、安全提醒、官方链接和下一步；措辞可结合上下文自然调整。

1. 「把用来收信的 iCloud 邮箱地址发我。应用专用密码不要发到聊天里。」
2. Use these official URLs directly; do not search for replacements:
   - Apple Account: <https://account.apple.com/>
   - Apple 官方操作说明: <https://support.apple.com/en-us/102654>

Give this as the user-facing guide:

「如果还没生成 App 专用密码：

先打开 Apple 账户：<https://account.apple.com/>

登录后进入“登录与安全”→“App 专用密码”，生成一组新密码，名称填 Cola。如果没有“App 专用密码”选项，先开启双重认证。

官方操作说明：<https://support.apple.com/en-us/102654>

生成后告诉我一声，不要把密码发到聊天里；我会弹出系统窗口让你填写，并继续完成刚才的邮件操作。」
3. When they have generated it: communicate the relevant 弹窗前 / 成功 / 取消 / 超时 guidance in `configuration.md`, then run `prompt` in the same turn.
4. After `account check` succeeds: 「iCloud 邮箱已经连好了。以后直接说『看看今天的邮件』就行。」
5. If authentication fails: 「这个应用专用密码好像不对。打开 Apple 账户重新生成一组：<https://account.apple.com/>。官方操作说明：<https://support.apple.com/en-us/102654>。生成后告诉我，我会再弹出窗口。」

This mail flow is separate from iCloud Calendar. Do not send the user to the calendar helper.

## How to connect

1. Confirm the complete iCloud Mail address used to receive mail.
2. Guide two-factor authentication and the app-specific password using the guidance above. Apple Account (user-facing): ***REDACTED***
3. Collect the app-specific password with the bundled helper as described in `configuration.md`. Use `--account universal-email/icloud`, title `Connect iCloud Mail` / `连接 iCloud 邮箱`, secret label `App-specific password` / `应用专用密码`. Never run the Himalaya wizard. Never open a terminal for the user.
4. Write the iCloud IMAP/SMTP account from `configuration.md`. Then run `himalaya --account icloud --json account check`.

## Validate and troubleshoot

If authentication fails, confirm the mailbox address rather than an Apple Account alias, confirm two-factor authentication, and generate a new app-specific password. Apple revokes app-specific passwords after some account password or security changes.

Discover mailboxes before saving a sent copy. Do not assume iCloud exposes `Sent` or `Sent Messages`. If mailbox discovery returns only `Inbox`, send without `--save`; do not create a folder automatically. Delivery and sender-side archiving are separate outcomes.
