{
  "mcpServers": {
    "cua_repl": {
      "command": "node",
      "args": [
        "scripts/launch.mjs"
      ],
      "enabled": false,
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
      }
    }
  }
}