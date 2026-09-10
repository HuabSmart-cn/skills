{
  "id": "qoder.computer-control",
  "name": "computer-control",
  "version": "1.0.0",
  "engines": {
    "qoder": ">=0.0.1"
  },
  "main": "dist/node/main.cjs",
  "activationEvents": [
    "onStartup"
  ],
  "permissions": [
    "chat.observeTurn",
    "chat.continueSession"
  ],
  "contributes": {
    "configuration": [
      {
        "section": "settings.browserControl",
        "group": {
          "id": "computer-use",
          "title": {
            "default": "Computer Use",
            "translations": {
              "zh-CN": "电脑操控"
            }
          }
        },
        "properties": {
          "qoder.computer-control.computerUse.enabled": {
            "type": "boolean",
            "title": {
              "default": "Enable Computer Use",
              "translations": {
                "zh-CN": "启用电脑操控"
              }
            },
            "description": {
              "default": "Allow Qoder to inspect and operate desktop apps.",
              "translations": {
                "zh-CN": "允许 Qoder 查看并操作桌面应用。"
              }
            },
            "default": false,
            "enablement": {
              "type": "operatingSystem",
              "versions": {
                "darwin": ">=14.0",
                "win32": ">=10.0"
              }
            }
          }
        }
      },
      {
        "section": "settings.browserControl",
        "group": {
          "id": "record-and-replay",
          "title": {
            "default": "Record & Replay",
            "translations": {
              "zh-CN": "录制与回放"
            }
          }
        },
        "enablement": {
          "type": "operatingSystem",
          "versions": {
            "darwin": ">=0"
          }
        },
        "properties": {
          "qoder.computer-control.recordAndReplay.enabled": {
            "type": "boolean",
            "title": {
              "default": "Enable Record & Replay",
              "translations": {
                "zh-CN": "启用录制与回放"
              }
            },
            "description": {
              "default": "Allow Qoder to record a demonstrated workflow and turn it into a reusable skill.",
              "translations": {
                "zh-CN": "允许 Qoder 录制演示流程并将其转换为可复用的 Skill。"
              }
            },
            "default": false,
            "enablement": {
              "type": "operatingSystem",
              "versions": {
                "darwin": ">=14.0"
              }
            }
          }
        }
      }
    ],
    "qoderAgentSdk": {
      "plugins": [
        {
          "type": "local",
          "path": "dist/cli/computerUse",
          "mcpToolPresentations": [
            {
              "serverName": "computer-use",
              "tools": [
                {
                  "name": "list_apps",
                  "title": {
                    "default": "List desktop apps",
                    "translations": {
                      "zh-CN": "列出桌面应用"
                    }
                  }
                },
                {
                  "name": "list_windows",
                  "title": {
                    "default": "List app windows",
                    "translations": {
                      "zh-CN": "列出应用窗口"
                    }
                  }
                },
                {
                  "name": "get_window",
                  "title": {
                    "default": "Read window",
                    "translations": {
                      "zh-CN": "读取窗口"
                    }
                  }
                },
                {
                  "name": "launch_app",
                  "title": {
                    "default": "Launch app",
                    "translations": {
                      "zh-CN": "启动应用"
                    }
                  }
                },
                {
                  "name": "activate_window",
                  "title": {
                    "default": "Activate window",
                    "translations": {
                      "zh-CN": "激活窗口"
                    }
                  }
                },
                {
                  "name": "get_app_state",
                  "title": {
                    "default": "Read app state",
                    "translations": {
                      "zh-CN": "读取应用状态"
                    }
                  }
                },
                {
                  "name": "get_window_state",
                  "title": {
                    "default": "Read window state",
                    "translations": {
                      "zh-CN": "读取窗口状态"
                    }
                  }
                },
                {
                  "name": "click",
                  "title": {
                    "default": "Click UI element",
                    "translations": {
                      "zh-CN": "点击界面元素"
                    }
                  }
                },
                {
                  "name": "perform_secondary_action",
                  "title": {
                    "default": "Perform secondary action",
                    "translations": {
                      "zh-CN": "执行辅助操作"
                    }
                  }
                },
                {
                  "name": "set_value",
                  "title": {
                    "default": "Set element value",
                    "translations": {
                      "zh-CN": "设置元素值"
                    }
                  }
                },
                {
                  "name": "select_text",
                  "title": {
                    "default": "Select text",
                    "translations": {
                      "zh-CN": "选择文本"
                    }
                  }
                },
                {
                  "name": "scroll",
                  "title": {
                    "default": "Scroll interface",
                    "translations": {
                      "zh-CN": "滚动界面"
                    }
                  }
                },
                {
                  "name": "drag",
                  "title": {
                    "default": "Drag UI element",
                    "translations": {
                      "zh-CN": "拖动界面元素"
                    }
                  }
                },
                {
                  "name": "press_key",
                  "title": {
                    "default": "Press key",
                    "translations": {
                      "zh-CN": "按下按键"
                    }
                  }
                },
                {
                  "name": "type_text",
                  "title": {
                    "default": "Type text",
                    "translations": {
                      "zh-CN": "输入文本"
                    }
                  }
                },
                {
                  "name": "run_steps",
                  "title": {
                    "default": "Run action sequence",
                    "translations": {
                      "zh-CN": "执行操作序列"
                    }
                  }
                }
              ]
            }
          ],
          "enablement": {
            "allOf": [
              {
                "type": "configuration",
                "key": "qoder.computer-control.computerUse.enabled",
                "equals": true
              },
              {
                "type": "operatingSystem",
                "versions": {
                  "darwin": ">=14.0",
                  "win32": ">=10.0"
                }
              }
            ]
          }
        },
        {
          "type": "local",
          "path": "dist/cli/recordAndReplay",
          "mcpToolPresentations": [
            {
              "serverName": "event-stream",
              "tools": [
                {
                  "name": "event_stream_start",
                  "title": {
                    "default": "Start recording",
                    "translations": {
                      "zh-CN": "开始录制"
                    }
                  }
                },
                {
                  "name": "event_stream_status",
                  "title": {
                    "default": "View recording status",
                    "translations": {
                      "zh-CN": "查看录制状态"
                    }
                  }
                },
                {
                  "name": "event_stream_stop",
                  "title": {
                    "default": "Stop and save recording",
                    "translations": {
                      "zh-CN": "停止并保存录制"
                    }
                  }
                }
              ]
            }
          ],
          "enablement": {
            "allOf": [
              {
                "type": "configuration",
                "key": "qoder.computer-control.recordAndReplay.enabled",
                "equals": true
              },
              {
                "type": "operatingSystem",
                "versions": {
                  "darwin": ">=14.0"
                }
              }
            ]
          }
        }
      ]
    },
    "nativeModules": [
      {
        "id": "picture-in-picture-host",
        "resourceId": "qoder-computer-use-presentation-provider",
        "lifecycle": "plugin",
        "enablement": {
          "allOf": [
            {
              "type": "configuration",
              "key": "qoder.computer-control.computerUse.enabled",
              "equals": true
            },
            {
              "type": "operatingSystem",
              "versions": {
                "darwin": ">=14.0"
              }
            }
          ]
        }
      }
    ]
  }
}