{
  "name": "unified-computer-use",
  "hooks": {
    "hooks": {
      "Interrupt": [
        {
          "hooks": [
            {
              "type": "mcp_tool",
              "server": "cua_repl",
              "tool": "turn_ended",
              "input": {
                "hook_event_name": "${hook_event_name}",
                "session_id": "${session_id}",
                "turn_id": "${turn_id}"
              }
            }
          ]
        }
      ],
      "SubagentStop": [
        {
          "hooks": [
            {
              "type": "mcp_tool",
              "server": "cua_repl",
              "tool": "turn_ended",
              "input": {
                "hook_event_name": "${hook_event_name}",
                "session_id": "${agent_id}",
                "turn_id": "${turn_id}"
              }
            }
          ]
        }
      ],
      "Stop": [
        {
          "hooks": [
            {
              "type": "mcp_tool",
              "server": "cua_repl",
              "tool": "turn_ended",
              "input": {
                "hook_event_name": "${hook_event_name}",
                "session_id": "${session_id}",
                "turn_id": "${turn_id}"
              }
            }
          ]
        }
      ]
    }
  },
  "version": "26.903.61454",
  "description": "App-managed browser automation runtime.",
  "mcpServers": "./.mcp.json"
}