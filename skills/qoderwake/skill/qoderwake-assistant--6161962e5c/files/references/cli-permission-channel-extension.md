# Permission、Channel 与 Extension 命令

来源：`package/src/cli/index.ts`、`permission.ts`、`channel.ts`、`extension.ts`。

这些命令优先复用 Console 已有 daemon HTTP API；`extension list` 使用 CLI 专用只读 JSON route。配置型命令用 JSON 对象透传；如果需要原始 JSON 输出，用 `--format json`，避免和 `--json <object>` 输入冲突。

## permission

用于查看和更新 waker 级权限配置。

**变更类命令（update / patch）是高风险自我服务操作**：权限守卫是其他所有防护的根开关。仅在用户明确提出权限变更诉求、并确认将要修改的 section 与目标值后执行；在执行其他任务（代码评审、日志分析、定时巡检等）时，严禁以"加强防护"、"修复权限问题"等理由自行发起权限变更。用户抱怨权限现象时先 `permission get` 汇报现状，由用户决定是否变更。

```bash
qoderwake permission get --waker-id <waker-id>

# 以下两类命令仅限用户显式要求并确认后执行：
qoderwake permission update --waker-id <waker-id> \
  --json '{"toolGuard":{"enabled":true}}'
qoderwake permission update --waker-id <waker-id> \
  --json-file ./permissions.json

qoderwake permission patch tool-guard --waker-id <waker-id> --json '<object>'
qoderwake permission patch file-guard --waker-id <waker-id> --json '<object>'
qoderwake permission patch builtin-tools --waker-id <waker-id> --json '<object>'
qoderwake permission patch model-security --waker-id <waker-id> --json '<object>'

qoderwake permission builtin tool-guard-rules
qoderwake permission builtin tool-catalog
```

说明：

- `update` 对应 Console 的整体 `PUT /api/agents/:agentId/permissions`。
- `patch` 只更新一个 section，适合脚本化小改动。
- JSON 输入必须是对象，不能是数组或标量。

## channel

用于管理 IM channel、钉钉二维码注册、pairing 记录。

```bash
qoderwake channel settings
qoderwake channel list [--waker-id <waker-id>]
qoderwake channel get <channel-id>
qoderwake channel config <channel-id> --json '<object>'
qoderwake channel start <channel-id>
qoderwake channel stop <channel-id>
qoderwake channel restart <channel-id>
qoderwake channel delete <channel-id>
```

钉钉二维码：

```bash
qoderwake channel dingtalk qr-start
qoderwake channel dingtalk qr-poll --device-code <device-code>
```

Pairing：

```bash
qoderwake channel pairing generate-code --channel-id <channel-id>
qoderwake channel pairing list [--channel-id <channel-id>] [--robot-id <robot-id>]
qoderwake channel pairing pending [--channel-id <channel-id>] [--robot-id <robot-id>]
qoderwake channel pairing delete <pairing-id>
qoderwake channel pairing approve --channel-id <channel-id> --robot-id <robot-id> --binding-key <key>
qoderwake channel pairing ignore --channel-id <channel-id> --robot-id <robot-id> --binding-key <key>
```

破坏性命令：

- `channel delete`
- `channel pairing delete`
- `channel pairing ignore`

执行前应向用户复述命令并确认。

## extension

用于只读查看本地 extension runtime 状态，对齐 Console `/extensions` 页面。

```bash
qoderwake extension list
qoderwake extension ls
```

说明：

- 数据源是 daemon 暴露的 `GET /api/ext/v1/extensions`。
- `extension` 不接收 `--waker-id`；它查看本机 daemon 管理的 extension runtime 状态。
- 当前 CLI 不提供 install、enable、disable、reload；Console 也只读。
- 安装 extension 仍按产品约定：将扩展目录放入 `${QODERWAKE_HOME:-~/.qoderwake}/extensions/` 后重启 daemon。
