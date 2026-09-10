{
  "mcpServers": {
    "jufa-mcp-server": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "jufa-mcp-server@latest"
      ],
      "env": {
        "JUFA_API_KEY": "***REDACTED***"
      },
      "runtime": {
        "type": "node",
        "version": ">=20"
      },
      "timeout": 120000
    }
  }
}