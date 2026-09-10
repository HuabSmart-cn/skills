{
  "mcpServers": {
    "wake_memory": {
      "type": "sse",
      "url": "http://127.0.0.1:19820/api/internal/builtin-mcp/qoderwake_memory/sse?agentId=0eb416f9f53d&workspace=%2FUsers%2Fhukee%2F.qoderwake%2Fdata%2Fworkers%2F0eb416f9f53d&sessionId=%24%7BQODER_SESSION_ID%7D",
      "headers": {
        "x-qw-product": "QoderWake",
        "x-qoderwake-builtin-mcp-token": "***REDACTED***"
      }
    },
    "wake_im_channel": {
      "type": "sse",
      "url": "http://127.0.0.1:19820/api/internal/builtin-mcp/qoderwake_im_channel/sse?sessionId=${QODERWAKE_SESSION_ID}&agentId=0eb416f9f53d",
      "headers": {
        "x-qw-product": "QoderWake",
        "x-qoderwake-im-channel-send-mcp-token": "***REDACTED***"
      }
    },
    "knowledge": {
      "type": "sse",
      "url": "http://127.0.0.1:19820/api/internal/builtin-mcp/knowledge/sse?sessionId=${QODERWAKE_SESSION_ID}",
      "headers": {
        "x-qw-product": "QoderWake",
        "x-qoderwake-qmind-mcp-token": "***REDACTED***",
        "x-qoderwake-waker-id": "0eb416f9f53d"
      }
    }
  }
}