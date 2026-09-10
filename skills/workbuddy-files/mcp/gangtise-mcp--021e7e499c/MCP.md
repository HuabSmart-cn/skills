{
  "mcpServers": {
    "gangtise-mcp": {
      "type": "streamableHttp",
      "url": "https://openapi.gangtise.com/application/open-mcp/",
      "headers": {
        "accessKey": "${GTS_ACCESS_KEY}",
        "secretKey": "***REDACTED***"
      },
      "timeout": 60000
    }
  }
}