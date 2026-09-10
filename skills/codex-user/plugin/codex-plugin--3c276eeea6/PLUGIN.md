{
  "name": "chrome",
  "hooks": {
    "hooks": {
      "Interrupt": [
        {
          "hooks": [
            {
              "type": "mcp_tool",
              "server": "node_repl",
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
              "server": "node_repl",
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
              "server": "node_repl",
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
  "description": "Chrome automation for tasks that depend on the user's existing Chrome state: tabs, logged-in sessions, cookies, extensions, and ChatGPT Chrome Extension setup. Prefer purpose-built connectors, APIs, or CLIs. If one fails due to missing or expired authentication, ask the user to reauthenticate or explicitly approve Chrome as a fallback.",
  "author": {
    "name": "OpenAI"
  },
  "homepage": "https://github.com/openai/openai/tree/master/lib/browser_use/plugin",
  "repository": "https://github.com/openai/openai/tree/master/lib/browser_use/plugin",
  "license": "Proprietary",
  "keywords": [
    "browser",
    "chrome"
  ],
  "skills": "./skills/",
  "interface": {
    "displayName": "Chrome",
    "shortDescription": "Control Chrome with ChatGPT",
    "longDescription": "Chrome lets ChatGPT use your Chrome browser for tasks that need your existing browser state, including open tabs, page content, and websites you're already signed into. It can navigate, view, click, type, and take screenshots while working. You stay in control: ChatGPT asks before interacting with new sites, you can stop actions at any time, and you can manage or remove Chrome access in settings. Browser content may include sensitive information from logged-in sites. Browser data from using this plugin may be used for training, subject to your OpenAI account data controls.",
    "developerName": "OpenAI",
    "category": "Productivity",
    "capabilities": [
      "Interactive",
      "Read"
    ],
    "websiteURL": "https://openai.com/",
    "privacyPolicyURL": "https://openai.com/policies/row-privacy-policy/",
    "termsOfServiceURL": "https://openai.com/policies/row-terms-of-use/",
    "defaultPrompt": [
      "file my expenses for me",
      "review my messages on social media",
      "put in a PTO request in Workday"
    ],
    "brandColor": "#10A37F",
    "composerIcon": "./assets/google-chrome-composer.png",
    "logo": "./assets/google-chrome.png",
    "screenshots": []
  }
}