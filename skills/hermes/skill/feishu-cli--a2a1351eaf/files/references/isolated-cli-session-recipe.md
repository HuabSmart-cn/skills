# Session-specific interaction recipe

## App creation

Use a private npm prefix and a Hermes-owned state directory:

```bash
mkdir -p "$HOME/.hermes/tools/lark-cli"
npm install --prefix "$HOME/.hermes/tools/lark-cli" @larksuite/cli@1.0.74
export HERMES_HOME="$HOME/.hermes"
export LARK_CLI_HOME="$HOME/.hermes/lark-cli"
LARK="$HOME/.hermes/tools/lark-cli/node_modules/.bin/lark-cli"
"$LARK" config init --new --name hermes-feishu --force-init --lang zh_cn
```

The CLI printed a QR and an app-setup URL, then returned an App ID after browser completion. The first generated URL expired when not completed quickly; rerunning `config init --new` produced a fresh code and succeeded.

## OAuth authorization

Run in a PTY/background process:

```bash
"$LARK" auth login --profile hermes-feishu
```

The live flow displayed a selector for 21 business domains and then a permission-tier selector. For all domains, use the UI's `ctrl+a` select-all shortcut and Enter. Select the desired permission tier and press Enter again. The CLI then printed a device verification URL under `accounts.feishu.cn/oauth/v1/device/verify` and waited for browser authorization.

Do not treat the authorization as complete until the process exits successfully and `auth status`/`auth check` confirm it. The app-setup URL and OAuth device URL are distinct and have separate expiration/confirmation steps.
