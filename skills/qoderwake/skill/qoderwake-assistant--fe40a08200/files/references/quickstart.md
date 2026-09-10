# QoderWake CLI 快速开始

5 分钟上手指南：从零开始创建数字员工并执行第一个任务。

## 前置条件

- 已安装 qoderwake CLI
- 有可用的网络连接
- 使用前请确保 daemon 已启动且已登录

## 第 1 步：创建数字员工

如果这段流程是在已有数字员工的用户 session 中由 agent 代为执行，`waker create` 没有 `--waker-id` / `--worker-id`，会创建一个独立的新数字员工；执行前必须让用户确认新员工名称、模板来源和影响范围。CLI 终端手动执行时按下面命令直接运行。

```bash
# 查看可用模板
qoderwake waker template list --json

# 使用默认模板创建
qoderwake waker create --template-id default --name "my-first-waker" --json
```

记住输出中的 `agentId`（如 `ag_abc123`），后续步骤需要使用。

## 第 2 步：创建项目

将代码仓库绑定到数字员工：

```bash
# 绑定本地目录
qoderwake project create \
  --waker-id ag_abc123 \
  --name "my-project" \
  --path /path/to/your/code \
  --json
```

记住输出中的 `projectId`。

触发 onboarding 让 waker 理解项目代码：

```bash
qoderwake project onboard --waker-id ag_abc123 --project-id <projectId>
```

## 第 3 步：创建会话并交互

```bash
# 创建会话并发送第一条消息
qoderwake session create \
  --waker-id ag_abc123 \
  --title "Hello World" \
  --message "请帮我查看项目结构" \
  --project-id <projectId> \
  --json
```

记住输出中的 `sessionId`。

实时监听 waker 的执行过程：

```bash
qoderwake session stream --session-id <sessionId>
```

查看执行结果：

```bash
# 查看产出物
qoderwake session artifacts --session-id <sessionId>

# 查看轨迹
qoderwake session trajectory --session-id <sessionId>
```

## 后续操作

### 添加技能

```bash
qoderwake skill add --waker-id ag_abc123 \
  --skill-id code-review --name "Code Review" \
  --description "代码审查"
```

### 添加 MCP 工具

```bash
# 添加 GitHub MCP
qoderwake mcp add --waker-id ag_abc123 \
  --name github-mcp \
  --command npx \
  --args "-y,@modelcontextprotocol/server-github" \
  --env '{"GITHUB_TOKEN":***REDACTED***
```

### 查看记忆

```bash
qoderwake memory show --waker-id ag_abc123 --view all
```

## 常用排查命令

```bash
# 查看所有会话
qoderwake session list --waker-id ag_abc123

# 查看该数字员工的自动化任务
qoderwake automation list --waker-id ag_abc123
```
