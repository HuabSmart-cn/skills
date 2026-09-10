# CLI 使用指南

## 前置条件

豆包沙箱已预装静态 `meegle-cli` 二进制，不依赖 Node.js/npm。所有命令通过 `meegle-cli` 执行。

禁止搜索或切换到任何其他二进制。豆包版本不提供 `auth`、`config` 命令或 `--profile`，也不读取本地配置、profile、keychain 或 TokenStore。

运行时必须注入 `DOUBAO_OFFICE_EDITION=internal|public`、`DOUBAO_OFFICE_MARKET=cn|overseas` 和非空的 `DOUBAO_OFFICE_USER_ACCESS_TOKEN`。CLI 按以下规则自动选择 host：

| Edition | Market | Host |
|---------|--------|------|
| `internal` | `cn` 或 `overseas` | `meego.larkoffice.com` |
| `public` | `cn` | `project.feishu.cn` |
| `public` | `overseas` | `meegle.com` |

豆包代理劫持请求后注入真实 token。遇到 `AUTH_REQUIRED`、`AUTH_REJECTED`、token rejected 或其他鉴权错误时，立即停止并报告豆包环境变量或代理注入异常；禁止执行授权命令、读取配置、改用浏览器或要求用户登录。

## 命令结构

```bash
meegle-cli <resource> <method> [flags] --format json
```

命令采用 `resource method` 两级结构。所有输出推荐使用 `--format json` 获取结构化数据。

## 全局 Flag

| Flag | 说明 |
|------|------|
| `--format json\|table\|ndjson` | 输出格式，默认 json |
| `--select <props>` | 选取输出属性，逗号分隔（支持 dot path，如 `name,owner.name`） |
| `--verbose` | 显示详细日志 |
| `--refresh` | 从服务端刷新本地命令缓存（旁路 24h cache） |

## 参数传递

几种方式，优先级从高到低：

1. **Flag 模式**（推荐）：`--project-key PROJ --work-item-type story`
2. **--fields 模式**（写工作项字段，可重复）：`--fields '{"field_key":"name","field_value":"任务标题"}' --fields '{"field_key":"priority","field_value":"1"}'`；`field_value` 支持任意 JSON 值（数组/对象原样传）
3. **--params 模式**（完整 JSON 兜底）：`--params '{"fields":[{"field_key":"name","field_value":"任务标题"}]}'`
4. **--set 模式**（仅顶层参数快捷写法，不支持 fields[]）：`--set page_num=1` 等价于 `--page-num 1`，支持 dot-path 嵌套；不要用它写工作项字段

Flag 覆盖 `--params`；`--set` 只影响顶层参数，**不会**写到 `fields[]`。

## 命令发现

CLI 的命令和参数会随版本更新。遇到不确定的命令或参数时，使用 `inspect` 获取最新信息：

```bash
meegle-cli inspect                    # 列出所有可用命令
meegle-cli inspect workitem.create    # 查看具体命令的参数 schema
```

> 命令清单本地缓存 24 小时。如果 `inspect` 输出的参数与服务端实际不符，或服务端有新命令但 CLI 报 `unknown command`，加上 `--refresh` 强制从服务端重新拉取最新清单：
> ```bash
> meegle-cli --refresh inspect workitem.create
> ```

## 输出处理

- 始终使用 `--format json` 获取结构化输出，方便解析
- 使用 `--select` 精简返回字段，如 `--select id,name,current_nodes.name`
- 命令返回错误时，JSON 中包含 `error` 和 `message` 字段
