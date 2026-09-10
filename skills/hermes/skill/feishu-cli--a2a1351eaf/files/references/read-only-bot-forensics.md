# Feishu CLI and local bot forensics (read-only)

## What to inspect

The official `@larksuite/cli` executable can be installed privately, but on macOS its state may still live under:

- `~/.lark-cli/config.json`: default app/profile
- `~/.lark-cli/<profile>/config.json`: named profile (for example `hermes/config.json`)
- macOS Keychain: App Secrets and token material, referenced from JSON by keychain IDs
- `~/.lark-cli/events/<app-id>/`: event-bus/runtime traces, useful evidence that a bot process used that app

Hermes itself may contain bundled Feishu tools/plugins, but their presence does not prove that a Feishu bot gateway is enabled. Check `hermes plugins list`, Hermes gateway/platform config, and running processes separately.

## Safe read-only inventory

```bash
find "$HOME/.lark-cli" -maxdepth 3 -type f -print
find "$HOME/.openclaw" -maxdepth 4 -type f -print 2>/dev/null
hermes plugins list
hermes tools list
pgrep -af 'lark|feishu|openclaw|hermes'
```

Search configuration text for `feishu`, `lark`, `appId`, `app_id`, and bot/gateway keys, but exclude logs, caches, node_modules, and session/request dumps when drawing conclusions. Never print App Secrets, access tokens, or keychain contents.

## How to report findings

Separate the evidence into:

1. **Known app identities**: App IDs and profile paths found in local JSON.
2. **Runtime evidence**: event directories, process IDs, gateway service records.
3. **Attribution**: which software likely used the app. Treat this as an inference unless an explicit config or process record names the software.
4. **Unknowns**: what cannot be established from local files alone; a Feishu developer console may be needed to inspect app name, owner, and published versions.

Finding an old app config proves that a CLI or local integration knew about the app; it does not by itself prove whether the app was used by Hermes, OpenClaw, Cursor, Claude Code, or another agent.
