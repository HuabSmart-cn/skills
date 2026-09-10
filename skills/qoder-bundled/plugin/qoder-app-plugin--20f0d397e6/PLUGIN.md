{
  "id": "qoder.find-extensions",
  "name": "find-extensions",
  "version": "0.1.0",
  "engines": {
    "qoder": ">=0.0.1"
  },
  "main": "dist/node/main.cjs",
  "activationEvents": [],
  "permissions": [],
  "contributes": {
    "qoderAgentSdk": {
      "plugins": [
        {
          "type": "local",
          "path": "cli/findExtensions"
        }
      ]
    }
  }
}