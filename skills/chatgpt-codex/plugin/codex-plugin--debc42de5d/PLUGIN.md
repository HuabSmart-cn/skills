{
  "name": "user-writing",
  "version": "0.1.2",
  "description": "Find relevant examples of your writing through connected apps before composing substantive prose.",
  "author": {
    "name": "OpenAI"
  },
  "repository": "https://github.com/openai/openai/tree/master/chatgpt/oai-maintained-plugins/plugins/user-writing",
  "license": "Proprietary",
  "publicationPolicy": "INTERNAL_ONLY",
  "keywords": [
    "writing",
    "style",
    "connected apps"
  ],
  "skills": "./skills/",
  "interface": {
    "displayName": "Write like me",
    "composerIcon": "./assets/icon.svg",
    "logo": "./assets/icon.svg",
    "shortDescription": "Write with context from your own writing",
    "longDescription": "Search your enabled, connected apps for relevant examples of your writing, keep the reference handoff to titles and source links, and compose using the bundled writing guidance. No writing bank is maintained.",
    "developerName": "OpenAI",
    "category": "Productivity",
    "capabilities": [
      "Read"
    ],
    "defaultPrompt": [
      "Draft a team update in my writing style."
    ]
  }
}