{
  "name": "messages",
  "version": "1.0.1000968",
  "description": "Read, search, and send messages from the native macOS Messages app",
  "author": {
    "name": "OpenAI",
    "email": "support@openai.com",
    "url": "https://openai.com/"
  },
  "homepage": "https://openai.com/",
  "license": "Proprietary",
  "keywords": [
    "messages",
    "imessage",
    "text messages",
    "texts",
    "texting",
    "sms",
    "rcs",
    "macos"
  ],
  "mcpServers": "./.mcp.json",
  "interface": {
    "displayName": "Messages",
    "shortDescription": "Read, search, and send with Messages on this Mac",
    "longDescription": "The Messages plugin lets ChatGPT find conversations, read or search message history, and send messages or local file attachments through the native Messages app on this Mac. By default, ChatGPT uses messages only from conversations you approve to answer your requests, and sends messages only after you approve the message and its recipients.",
    "developerName": "OpenAI",
    "category": "Productivity",
    "capabilities": [
      "Read",
      "Write"
    ],
    "websiteURL": "https://openai.com/",
    "privacyPolicyURL": "https://openai.com/policies/row-privacy-policy/",
    "termsOfServiceURL": "https://openai.com/policies/row-terms-of-use/",
    "logo": "./assets/app-icon.png",
    "defaultPrompt": [
      "Tell me about my most recent conversations",
      "Find recent messages about dinner plans",
      "Send a message"
    ],
    "brandColor": "#34C759"
  }
}