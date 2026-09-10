{
  "name": "lark",
  "version": "1.0.5",
  "description": "Feishu/Lark workflows for messaging, documents, spreadsheets, calendar, tasks, meetings, and enterprise collaboration.",
  "i18n": {
    "display_name": {
      "en": "Feishu",
      "zh-cn": "飞书",
      "ja": "Feishu"
    },
    "description": {
      "en": "Connect your Feishu account to let TRAE manage docs, bases, calendars, messages and more",
      "zh-cn": "连接你的飞书账号，让 TRAE 操作云文档、多维表格、日历、消息等飞书功能",
      "ja": "Feishu アカウントを接続して、TRAE ドキュメント・テーブル・カレンダー・メッセージなどを操作"
    }
  },
  "author": {
    "name": "Lark",
    "url": "https://www.larksuite.com"
  },
  "homepage": "https://www.larksuite.com",
  "repository": "https://github.com/openai/plugins",
  "license": "MIT",
  "keywords": [
    "lark",
    "feishu",
    "collaboration",
    "documents",
    "spreadsheets",
    "calendar",
    "messaging",
    "tasks",
    "meetings"
  ],
  "binaries": [
    {
      "name": "lark-cli",
      "path": "bin/lark-cli",
      "required": true,
      "executable": true,
      "platforms": {
        "linux-arm64": {
          "sha256": "267b5d493f947ef7d0bf4dac771d4b7682b8cca6a9b47a6a41a160587f7b7edc",
          "file_size": 13139124,
          "urls": [
            {
              "source_group": "cn",
              "url": "https://p11-market.byteimg.com/tos-cn-i-17oceyzymr/binaries/lark-cli/1.0.94/linux-arm64-1788835698658016542.zip"
            },
            {
              "source_group": "sg",
              "url": "https://p16-market-sg.ibyteimg.com/tos-alisg-i-qmhakdvxf5-sg/binaries/lark-cli/1.0.94/linux-arm64-1788836630983637561.zip"
            }
          ]
        },
        "darwin-x64": {
          "sha256": "1ede1a41de9deb49442590928fb046a7c623642905ed0249d644c7d012b5f89a",
          "file_size": 14787942,
          "urls": [
            {
              "source_group": "cn",
              "url": "https://p11-market.byteimg.com/tos-cn-i-17oceyzymr/binaries/lark-cli/1.0.94/darwin-x64-1788835680107290854.zip"
            },
            {
              "source_group": "sg",
              "url": "https://p16-market-sg.ibyteimg.com/tos-alisg-i-qmhakdvxf5-sg/binaries/lark-cli/1.0.94/darwin-x64-1788836642519452009.zip"
            }
          ]
        },
        "linux-x64": {
          "sha256": "924ccf860a58336c410743fb0fc98142768e4ffd8b14fe8c8cb9c3b289281461",
          "file_size": 14269563,
          "urls": [
            {
              "source_group": "cn",
              "url": "https://p11-market.byteimg.com/tos-cn-i-17oceyzymr/binaries/lark-cli/1.0.94/linux-x64-1788835942090516517.zip"
            },
            {
              "source_group": "sg",
              "url": "https://p16-market-sg.ibyteimg.com/tos-alisg-i-qmhakdvxf5-sg/binaries/lark-cli/1.0.94/linux-x64-1788836593750314041.zip"
            }
          ]
        },
        "darwin-arm64": {
          "sha256": "ed20e804a63467f35afe3b98e52efb51caf9480be90b3490d49173265fbf4465",
          "file_size": 13541749,
          "urls": [
            {
              "source_group": "cn",
              "url": "https://p11-market.byteimg.com/tos-cn-i-17oceyzymr/binaries/lark-cli/1.0.94/darwin-arm64-1788835706540858632.zip"
            },
            {
              "source_group": "sg",
              "url": "https://p16-market-sg.ibyteimg.com/tos-alisg-i-qmhakdvxf5-sg/binaries/lark-cli/1.0.94/darwin-arm64-1788836620682898386.zip"
            }
          ]
        },
        "win32-x64": {
          "sha256": "c7230aa8ad164f6a1de9ea724cb4cd47bd612c7b8c6a2c110e291df029a395d3",
          "file_size": 14716202,
          "urls": [
            {
              "source_group": "cn",
              "url": "https://p11-market.byteimg.com/tos-cn-i-17oceyzymr/binaries/lark-cli/1.0.94/windows-x64-1788835719148526947.zip"
            },
            {
              "source_group": "sg",
              "url": "https://p16-market-sg.ibyteimg.com/tos-alisg-i-qmhakdvxf5-sg/binaries/lark-cli/1.0.94/windows-x64-1788836609884425201.zip"
            }
          ]
        }
      }
    }
  ],
  "env": {
    "LARKSUITE_CLI_USER_ACCESS_TOKEN": "***REDACTED***",
    "LARKSUITE_CLI_BRAND": [
      "${connector.feishu.Provider}",
      "${connector.lark.Provider}"
    ],
    "LARKSUITE_CLI_APP_ID": [
      "${connector.feishu.CLIENT_ID}",
      "${connector.lark.CLIENT_ID}"
    ]
  },
  "skills": "./skills/",
  "apps": "./.app.json",
  "connector": "./connector.json",
  "interface": {
    "displayName": "Lark",
    "shortDescription": "Enterprise collaboration powered by Feishu/Lark",
    "longDescription": "Feishu/Lark workflows for sending messages, managing documents, spreadsheets, calendars, tasks, meetings, OKRs, approvals, and more. Integrates with Lark Base, Drive, Wiki, Slides, Mail, and video conferencing.",
    "developerName": "Lark",
    "category": "Productivity",
    "capabilities": [
      "Interactive",
      "Read",
      "Write"
    ],
    "websiteURL": "https://www.larksuite.com",
    "privacyPolicyURL": "https://www.larksuite.com/en_us/privacy-policy",
    "termsOfServiceURL": "https://www.larksuite.com/en_us/terms-of-service",
    "defaultPrompt": [
      "Send a message to a Lark chat",
      "Create a document in Lark Docs",
      "Schedule a meeting on Lark Calendar"
    ],
    "brandColor": "#3370FF",
    "composerIcon": "./assets/app-icon.svg",
    "logo": "./assets/app-icon.svg",
    "screenshots": []
  }
}