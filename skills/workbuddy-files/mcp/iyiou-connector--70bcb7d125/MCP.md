{
  "mcpServers": {
    "iyiou-connector": {
      "type": "streamableHttp",
      "url": "https://mcp.iyiou.com/data",
      "headers": {
        "X-Client-Id": "${CLIENT_ID}",
        "X-Client-Secret": "***REDACTED***"
      },
      "timeout": 60000
    }
  }
}