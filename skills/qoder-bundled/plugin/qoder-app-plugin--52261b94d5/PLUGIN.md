{
  "id": "qoder.knowledge.center",
  "name": "knowledge-center",
  "version": "0.1.1",
  "engines": {
    "qoder": ">=0.0.1"
  },
  "main": "dist/node/main.cjs",
  "activationEvents": [
    "onStartup",
    "onView:knowledge-center-workbench"
  ],
  "permissions": [
    "auth.readState",
    "auth.readUserToken",
    "chat.createSession",
    "chat.readSessionResult",
    "chat.revealSession",
    "node.callService",
    "files.stageLocal",
    "workspace.read",
    "workspace.readProjects"
  ],
  "contributes": {
    "views": [
      {
        "id": "knowledge-center-workbench",
        "title": {
          "default": "Knowledge Center",
          "translations": {
            "zh-CN": "知识中心"
          }
        },
        "location": "workbench",
        "hostHeader": "hidden",
        "entry": "dist/browser/view.cjs"
      }
    ],
    "sidebarNavItems": [
      {
        "id": "knowledge-center-sidebar",
        "title": {
          "default": "Knowledge Center",
          "translations": {
            "zh-CN": "知识中心"
          }
        },
        "icon": "assets/knowledge-center.svg",
        "viewId": "knowledge-center-workbench",
        "slot": "workbench.sidebar.secondary"
      }
    ],
    "qoderAgentSdk": {
      "plugins": [
        {
          "type": "local",
          "path": "cli/qoder-qmind"
        }
      ]
    }
  }
}