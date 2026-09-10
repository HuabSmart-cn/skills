---
name: channel-plugins
description: Manage Cola's WeChat channel plugin — enable, disable, check status, and guide login. Use when the user wants to set up or manage WeChat messaging integration.
metadata:
  category: development
  icon: wechat
---

# WeChat Channel Plugin

Cola has a built-in WeChat plugin that lets users chat with the agent through WeChat. Use the `cola channel` CLI to manage it.

**CRITICAL: Never run `cola server stop`, `cola server start`, or `cola server restart`. This kills the running server and breaks the user's session. All operations below work without restarting.**

## Commands

All commands run via bash. The server must be running.

### Check status

```bash
cola channel list
```

Shows WeChat plugin status: connected / disconnected / not configured.

### Enable / Disable

```bash
cola channel enable wechat
cola channel disable wechat
```

Takes effect immediately for disable (stops the gateway). Enable takes effect on next server restart — tell the user.

### Login (automated with QR image)

Login triggers a QR code flow. After successful login, the gateway hot-reloads automatically — no restart needed.

Steps:

1. Run the login command **in the background** with `--qr-file` to save the QR as a PNG:
   ```bash
   cola channel login wechat --qr-file /tmp/cola-wechat-qr.png &
   ```
2. Wait for the QR to be generated:
   ```bash
   sleep 3 && ls -la /tmp/cola-wechat-qr.png
   ```
3. Send the QR image to the user via `desktop_tool`:
   - action: `send_file`
   - file_path: `/tmp/cola-wechat-qr.png`
   - caption: `请用微信扫描此二维码登录`
4. Tell the user to scan the QR code with their WeChat app.
5. The background command completes once the user scans and confirms. Check on it to report success or failure.

**Important:** The QR code expires after ~2 minutes. If the user doesn't scan in time, run the login command again to get a fresh QR code.

## Common workflows

### "帮我安装微信" / "Set up WeChat"

WeChat is built-in, no installation needed. Check status first:

```bash
cola channel list
```

- If **connected**: tell the user WeChat is already set up and working.
- If **disconnected** or **not configured**: start the login flow above.

### "关闭微信" / "Disable WeChat"

```bash
cola channel disable wechat
```

This stops the WeChat gateway immediately.

## Config

Plugin configuration is stored in `~/.cola/channels.json`.
