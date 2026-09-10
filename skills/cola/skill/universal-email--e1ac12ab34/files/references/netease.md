# NetEase Mail (163 / 126 / yeah)

Use this guide when the mailbox is NetEase personal mail. That includes:

- the user says 网易邮箱、163 邮箱、126 邮箱、yeah 邮箱;
- the address ends in `@163.com`, `@126.com`, or `@yeah.net`.

Do **not** fall through to `standard-imap-smtp.md` for those addresses. NetEase personal mail supports IMAP/SMTP and POP3/SMTP with a 客户端授权码. This skill's bundled client connects through IMAP/SMTP; it has no POP3 backend. Do not ask for the webmail login password.

网易企业邮箱 (qiye.163.com / a company domain hosted by NetEase) is a different product. Do not use this guide or this FAQ for it; use `standard-imap-smtp.md` and that organization's own setup page.

## Official entry and operation document

- 网易邮箱登录入口: <https://email.163.com/>
- 网易官方 IMAP/POP3 开启教程 **「如何开启客户端协议？」**: <https://help.mail.163.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b8f4f8e49998b374173cfe9171305fa1ce630d7f67ac2a5feb28b66796d3b>

The tutorial shows how to enable either incoming protocol and obtain the 16-letter 客户端授权码. Always include it when guiding; do not invent another tutorial or send only a menu path.

The same FAQ covers @163.com, @126.com, and @yeah.net (the help center lists all three). Server hostnames change with the domain; the 授权码 steps do not.

## What the user needs

- the full `@163.com`, `@126.com`, or `@yeah.net` address;
- the 客户端授权码 generated on that official page.

The username is the full email address.

## 对用户表达的要点与示例

保留下列事实、安全提醒、官方链接和下一步；措辞可结合上下文自然调整。

1. 「把要连接的网易邮箱地址发我，完整的 @163.com、@126.com 或 @yeah.net。授权码不要发到聊天里。」
2. When connecting Cola, recommend IMAP because it synchronizes mailbox folders and state with webmail. Do not ask the user to choose a protocol unless they already mentioned POP3. Give this as the user-facing guide:

「建议使用 IMAP，它能与网页版同步邮件和文件夹。

先登录网易邮箱：<https://email.163.com/>

再按官方 IMAP 教程开启 IMAP/SMTP 并生成客户端授权码：<https://help.mail.163.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b8f4f8e49998b374173cfe9171305fa1ce630d7f67ac2a5feb28b66796d3b>

生成后告诉我一声，不要把授权码发到聊天里；我会弹出系统窗口让你填写，并继续完成刚才的邮件操作。」

3. If the user explicitly asks to connect Cola through POP3, state immediately that Cola currently cannot receive mail through POP3. Do not guide them to enable POP3 or collect a code for that path. Offer the supported IMAP connection and continue only after they accept it. If they are configuring a different mail client instead, guide them to the same official tutorial and the “POP/SMTP/IMAP” settings, where they can enable POP3/SMTP. Never write a POP3 server into an IMAP configuration.

4. When they have generated it: communicate the relevant 弹窗前 / 成功 / 取消 / 超时 guidance in `configuration.md`, then run `prompt` in the same turn. In that window they enter the 客户端授权码, not the NetEase login password.
5. After `account check` succeeds: 「网易邮箱已经连好了。以后直接说『看看今天的邮件』就行。」
6. If authentication fails: 「这个授权码好像不对。按网易官方教程重新生成一组：<https://help.mail.163.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b8f4f8e49998b374173cfe9171305fa1ce630d7f67ac2a5feb28b66796d3b>。生成后告诉我，我会再弹出窗口。」

Do not stop after “去生成授权码” without saying the next action. Connecting saves the account on this device and does not change mail stored by NetEase.

## How to connect

1. Confirm the full address. Choose the Himalaya account name from the domain: `163`, `126`, or `yeah`.
2. Guide IMAP + 客户端授权码 using the guidance above. Always include the official mailbox entry and IMAP tutorial URL. If the user asks to connect Cola through POP3, stop before provider setup and follow the POP3 boundary above.
3. Collect the authorization code with the bundled helper as described in `configuration.md`. Use `--account universal-email/<name>` (`163` / `126` / `yeah`), title `Connect NetEase Mail` / `连接网易邮箱`, secret label `Authorization code` / `授权码`. Never run the Himalaya wizard. Never open a terminal for the user.
4. Write the matching IMAP/SMTP account from `configuration.md`. Then run `himalaya --account <name> --json account check`.

## Validate and troubleshoot

| Address | IMAP | SMTP |
| --- | --- | --- |
| `@163.com` | `imap.163.com:993` TLS | `smtp.163.com:465` TLS |
| `@126.com` | `imap.126.com:993` TLS | `smtp.126.com:465` TLS |
| `@yeah.net` | `imap.yeah.net:993` TLS | `smtp.yeah.net:465` TLS |

Use the host that matches the address. Do not point a 126 mailbox at `imap.163.com`.
