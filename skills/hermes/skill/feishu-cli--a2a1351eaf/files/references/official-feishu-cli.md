# Official Feishu CLI — verified references

## Official CLI guide

- Guide: https://open.feishu.cn/document/mcp_open_tools/feishu-cli-let-ai-actually-do-your-work-in-feishu
- Source repository: https://github.com/larksuite/cli
- npm package: `@larksuite/cli`
- Verified package metadata during this session: version `1.0.74`, executable `lark-cli`.

## Verified official workflow

The official guide documents:

```bash
npx @larksuite/cli@latest install
lark-cli config init --new
lark-cli auth login
lark-cli auth status
lark-cli auth check
```

`config init --new` is the browser-assisted application setup flow. The CLI can print a QR code and a URL under `https://open.feishu.cn/page/cli?...`; the user completes setup in the browser while the CLI waits for the result.

The guide also documents named profiles:

```bash
lark-cli config init --new --name bot-reader
lark-cli profile list
lark-cli profile use bot-reader
lark-cli --profile bot-reader <command>
```

## Hermes-specific observation

The installed CLI's live help reported that inside an `HERMES_HOME`/agent context, `config init` refuses by default to create a parallel app and recommends `config bind`. If the user explicitly wants a separate app inside Hermes, the help exposes `--force-init`; only use this after confirming that intent.

Observed help wording in version 1.0.74:

- `config init --new` creates a new app directly and blocks until browser setup is complete.
- `config bind` is the recommended route for binding an existing app.
- `--force-init` allows a separate app inside an agent workspace.

## Separate but related products

- Local OpenAPI MCP: https://github.com/larksuite/lark-openapi-mcp and npm `@larksuiteoapi/lark-mcp`; this is not the official `lark-cli` package.
- Remote MCP personal configuration: https://open.feishu.cn/document/mcp_open_tools/end-user-call-remote-mcp-server; this generates a remote MCP URL/JSON and is a separate flow. The page states newly created services expire after seven days unless reauthorized.
