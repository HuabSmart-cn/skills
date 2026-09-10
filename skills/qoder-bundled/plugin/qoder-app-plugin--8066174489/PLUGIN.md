{
  "id": "qoder.security",
  "name": "security",
  "version": "0.3.0",
  "engines": {
    "qoder": ">=0.0.1"
  },
  "main": "dist/node/main.cjs",
  "activationEvents": [
    "onView:security-settings"
  ],
  "permissions": [
    "node.callService",
    "configuration.write"
  ],
  "contributes": {
    "views": [
      {
        "id": "security-settings",
        "title": {
          "default": "Security",
          "translations": {
            "zh-CN": "安全"
          }
        },
        "location": "settings",
        "directoryId": "security",
        "entry": "dist/browser/view.cjs",
        "keywords": [
          {
            "default": "Security scanning",
            "translations": {
              "zh-CN": "安全扫描"
            }
          },
          {
            "default": "Scanning tiers",
            "translations": {
              "zh-CN": "扫描层级"
            }
          },
          {
            "default": "Static check lightweight scan deep scan",
            "translations": {
              "zh-CN": "静态检查 轻量扫描 深度扫描"
            }
          }
        ],
        "icon": "assets/security.svg"
      }
    ],
    "configuration": {
      "properties": {
        "qoder.security.l1StaticCheck": {
          "type": "boolean",
          "default": false
        },
        "qoder.security.l2LightweightScan": {
          "type": "boolean",
          "default": false
        },
        "qoder.security.l3DeepScan": {
          "type": "boolean",
          "default": false
        }
      }
    },
    "qoderAgentSdk": {
      "options": {
        "securityScan": {
          "l1StaticCheck": {
            "$configuration": "qoder.security.l1StaticCheck"
          },
          "l2LightweightScan": {
            "$configuration": "qoder.security.l2LightweightScan"
          },
          "l3DeepScan": {
            "$configuration": "qoder.security.l3DeepScan"
          }
        }
      }
    }
  }
}