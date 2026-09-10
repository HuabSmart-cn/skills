{
  "id": "qoder.desktop-pet-skill",
  "name": "desktop-pet-skill",
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
          "path": "cli/desktopPetSkill"
        }
      ]
    }
  }
}