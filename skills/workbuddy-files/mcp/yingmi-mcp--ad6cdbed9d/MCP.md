{
  "mcpServers": {
    "yingmi-mcp": {
      "type": "streamableHttp",
      "url": "https://stargate.yingmi.com/mcp/v2?apiKey=${YINGMI_API_KEY}",
      "env": {
        "YINGMI_API_KEY": "***REDACTED***"
      },
      "timeout": 30000
    }
  }
}