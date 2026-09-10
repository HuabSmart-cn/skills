{
  "mcpServers": {
    "qoder-context": {
      "command": "${QODER_NODE_RUNTIME}",
      "args": [
        "${QODER_PLUGIN_ROOT}/runtime/qoder-search.bundle.mjs",
        "mcp-bridge"
      ],
      "env_vars": [
        "QODER_HOME",
        "QODER_ENV",
        "QODER_BIG_MODEL_ENDPOINT",
        "QODER_OPENAPI_ENDPOINT"
      ],
      "env": {
        "QODER_PRODUCT_ID": "qoder",
        "QODER_SEARCH_PRODUCT_FORM": "qoder",
        "QODER_MTREE_NATIVE": "${QODER_PLUGIN_ROOT}/runtime/native/mtree/index.cjs",
        "QODER_SEARCH_RIPGREP_PATH": "${QODER_PLUGIN_ROOT}/runtime/ripgrep/rg",
        "QODER_SEARCH_BUILD_ID": "1.0.36.52b05a7-darwin-arm64"
      },
      "qoderAuthState": true,
      "startup": "application",
      "timeout": 600000,
      "alwaysAllow": [
        "SearchWorkspace",
        "SearchKnowledge"
      ],
      "toolOverrides": {
        "SearchWorkspace": {
          "exposedName": "SearchWorkspace",
          "alwaysLoad": true
        },
        "SearchKnowledge": {
          "exposedName": "SearchKnowledge",
          "alwaysLoad": true
        }
      }
    }
  }
}