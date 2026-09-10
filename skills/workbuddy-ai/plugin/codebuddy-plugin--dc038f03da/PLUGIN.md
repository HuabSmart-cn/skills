{
  "name": "mcp-ardot-mcp-app",
  "version": "0.1.0",
  "description": "WorkBuddy bundled MCP app resource: ardot-mcp-app.",
  "author": {
    "name": "WorkBuddy"
  },
  "category": "mcp-app",
  "keywords": [
    "workbuddy",
    "builtin-mcp-app",
    "ardot-mcp-app"
  ],
  "workbuddy": {
    "kind": "builtin-mcp-app",
    "legacyResourceName": "ardot-mcp-app",
    "bundleSegments": [
      "plugins",
      "workbuddy-builtin",
      "mcps",
      "ardot-mcp-app"
    ],
    "runtimeSupportSegments": [
      [
        "plugins",
        "workbuddy-builtin",
        "mcps",
        "ardot-mcp-app",
        "_workbuddy-runtime",
        "mcp-app-bootstrap.cjs"
      ]
    ],
    "loadsCapabilities": false
  }
}