{
  "mcpServers": {
    "cua_repl": {
      "command": "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node",
      "args": [
        "<LOCAL_PATH>"
      ],
      "enabled": true,
      "enabled_tools": [
        "js",
        "js_reset",
        "turn_ended"
      ],
      "omit_tools_from": [
        "code_mode",
        "deferred"
      ],
      "startup_timeout_sec": 120,
      "tools": {
        "js": {
          "output_token_limit": "***REDACTED***"
        }
      },
      "env_vars": [],
      "env": {
        "NODE_REPL_NATIVE_PIPE_CONNECT_TIMEOUT_MS": "1000",
        "NODE_REPL_NODE_MODULE_DIRS": "/Applications/ChatGPT.app/Contents/Resources/cua_node/lib/node_modules",
        "NODE_REPL_NODE_PATH": "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node",
        "NODE_REPL_TRUSTED_CODE_PATHS": "<LOCAL_PATH>",
        "CODEX_HOME": "<LOCAL_PATH>",
        "BROWSER_USE_AVAILABLE_BACKENDS": "chrome,iab",
        "BROWSER_USE_TINYSKY_ENABLED": "1",
        "NODE_REPL_INSTRUCTIONS_USE_CASE_BROWSER": "Control the in-app browser in conjunction with the Browser Plugin.",
        "NODE_REPL_INSTRUCTIONS_USE_CASE_CHROME": "Control the Chrome browser in conjunction with the Chrome Plugin. Prefer this method of controlling Chrome over alternatives (such as Computer Use) unless the user explicitly mentions an alternative.",
        "NODE_REPL_INSTRUCTIONS_USE_CASE_COMPUTER_USE": "Control desktop apps on macOS through Computer Use.",
        "BROWSER_USE_CODEX_APP_BUILD_FLAVOR": "prod",
        "BROWSER_USE_CODEX_APP_VERSION": "26.903.61454",
        "NODE_REPL_TRUSTED_SERVICES": "{\"browser\":\"<LOCAL_PATH>\",\"sky\":\"@oai/sky/service\"}",
        "SKY_CUA_SERVICE_PATH": "<LOCAL_PATH> Computer Use.app",
        "CODEX_CLI_PATH": "/Applications/ChatGPT.app/Contents/Resources/codex",
        "CUA_REPL_NODE_REPL_PATH": "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node_repl",
        "CUA_REPL_ENABLED_SURFACES": "browser,computer"
      }
    }
  }
}