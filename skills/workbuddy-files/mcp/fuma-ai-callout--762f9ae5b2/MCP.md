{
  "mcpServers": {
    "fuma-ai-callout": {
      "type": "streamableHttp",
      "url": "https://services.vcrm.vip:60610/mcp",
      "headers": {
        "access-token": "***REDACTED***",
        "orgCode": "${ORG_CODE}",
        "loginName": "${LOGIN_NAME}"
      },
      "timeout": 30000
    }
  }
}