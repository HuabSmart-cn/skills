{
  "schemaVersion": 10,
  "id": "qoder.index-settings",
  "name": "Workspace Index Settings",
  "version": "0.1.0",
  "engines": {
    "qoder": ">=0.0.1"
  },
  "main": "dist/node/main.cjs",
  "activationEvents": [
    "onStartup",
    "onView:index-settings"
  ],
  "permissions": [
    "auth.readState",
    "node.callService",
    "workspace.readProjects"
  ],
  "contributes": {
    "views": [
      {
        "id": "index-settings",
        "title": {
          "default": "Workspace Index",
          "translations": {
            "zh-CN": "工作区索引"
          }
        },
        "location": "settings",
        "directoryId": "workspace-index",
        "icon": "assets/index-settings.svg",
        "entry": "dist/browser/view.cjs"
      }
    ]
  }
}