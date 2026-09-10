{
  "name": "record-and-replay",
  "version": "1.0.1000968",
  "description": "Record what I'm doing on my Mac",
  "author": {
    "name": "OpenAI",
    "email": "support@openai.com",
    "url": "https://openai.com/"
  },
  "homepage": "https://openai.com/",
  "license": "Proprietary",
  "keywords": [
    "record-and-replay",
    "macos",
    "accessibility",
    "recording",
    "replay",
    "skills",
    "automation",
    "record"
  ],
  "mcpServers": "./.mcp.json",
  "skills": "./skills/",
  "interface": {
    "displayName": "Record & Replay",
    "shortDescription": "Record what I'm doing on my Mac and turn it into a Skill",
    "longDescription": "Record & Replay lets ChatGPT record your actions on your Mac to create skills for more automated workflows. When you choose to start a recording, ChatGPT will record your mouse clicks, text you type, and the content in windows you interact with until you stop it (up to 30 minutes). You can stop or cancel recording at any time, and cancelling will discard any existing recording. Avoid recording sensitive workflows.",
    "developerName": "OpenAI",
    "category": "Productivity",
    "websiteURL": "https://openai.com/",
    "privacyPolicyURL": "https://openai.com/policies/row-privacy-policy/",
    "termsOfServiceURL": "https://openai.com/policies/row-terms-of-use/",
    "logo": "./assets/app-icon.png",
    "defaultPrompt": [
      "Record my workflow and turn it into a reusable skill",
      "Watch me do this task and create a skill from it",
      "Record what I'm doing and make a skill called 'File Expense'"
    ],
    "brandColor": "#0F172A",
    "screenshots": []
  }
}