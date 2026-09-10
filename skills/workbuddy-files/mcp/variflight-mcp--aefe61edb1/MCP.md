{
  "mcpServers": {
    "variflight-mcp": {
      "type": "streamableHttp",
      "url": "https://c-gw.variflight.com/chat_message/mcp/api",
      "headers": {
        "Authorization": "***REDACTED***"
      },
      "timeout": 120000,
      "disabledTools": [
        "getUserInfo",
        "queryUserTripStatsInner"
      ]
    }
  }
}