{
  "mcpServers": {
    "qoder-qmind": {
      "command": "${QODER_NODE_RUNTIME}",
      "args": [
        "${QODER_PLUGIN_ROOT}/dist/qoder-qmind-mcp-server.cjs"
      ],
      "env_vars": [
        "QMIND_HOME",
        "QMIND_ENV"
      ]
    }
  }
}