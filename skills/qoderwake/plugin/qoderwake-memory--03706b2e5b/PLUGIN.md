{
  "name": "qoderwake_memory",
  "version": "0.1.0",
  "description": "Persistent memory, persona, and cross-session context.",
  "author": {
    "name": "Qoder Team"
  },
  "keywords": [
    "memory",
    "persona",
    "context",
    "qoder",
    "qoderwake_memory"
  ],
  "userConfig": {
    "agent_id": {
      "title": "Agent ID",
      "description": "Digital employee identifier used to isolate qoderwake_memory data. Defaults to default.",
      "type": "string",
      "sensitive": false
    },
    "qoderwake_memory_root": {
      "title": "Memory Root",
      "description": "Explicit memory root for this agent. If omitted, it is derived from the base directory and agent ID.",
      "type": "directory",
      "sensitive": false
    },
    "qoderwake_memory_base_dir": {
      "title": "Memory Base Directory",
      "description": "Base directory that stores per-agent qoderwake_memory roots.",
      "type": "directory",
      "sensitive": false
    }
  }
}