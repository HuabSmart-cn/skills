# QoderWake CLI 命令完整目录

## 用户 session 作用域安全

用户在当前数字员工会话里触发本 skill 时，默认只修改当前数字员工的配置。所有员工级写命令都应使用当前 session 的 `wakerId` 作为 `--waker-id`；不要自行选择其它员工。

需要二次确认的范围：

| 场景 | 示例命令 | 执行前必须确认 |
|---|---|---|
| 跨员工修改 | `qoderwake skill add --waker-id <other-waker>` | 告知目标员工 ID、要安装/修改的对象，并确认用户确实要改其它员工。 |
| 跨员工 MCP/automation/memory/permission 修改 | `qoderwake mcp update --waker-id <other-waker>` | 告知目标员工 ID 和影响范围。 |
| 无目标员工管理写 | `qoderwake waker create --template-id <id> --name <name>` / `qoderwake session create` | 告知该命令没有 `--waker-id` / `--worker-id`，确认目标范围；创建员工时还要确认新员工名称、模板来源和影响范围。 |
| 公共项目修改 | `qoderwake project create --public` / `update --public` / `delete --public` | 告知该命令没有目标员工参数，且会修改账号级公共项目，不是当前员工私有 project。 |

只读命令（如 `project list --public`、`skill search`）不需要二次确认。运行时权限系统会对上述写命令发起审批，不要绕过 CLI 调 HTTP API。

## 数字员工命令（waker）

### qoderwake waker list
列出所有 waker。
```
选项：
  --format <format>    输出格式：table（默认）/ json
  --json               输出原始 JSON
```

### qoderwake waker template list
列出可用的 waker 创建模板。

### qoderwake waker get
查看 waker 详情。
```
选项：
  --waker-id <id>    必需，Waker ID
  --json             输出 JSON
```

### qoderwake waker create
创建新 waker。

用户 session 内执行前必须二次确认：`waker create` 没有 `--waker-id` / `--worker-id`，会创建当前 session 员工之外的独立新数字员工，不是修改当前员工配置。确认内容至少包括新员工名称、模板来源（`--template-id` / `--template-json` / `--template-zip`）和工作区路径（如有）。

```
选项：
  --template-id <id>          使用服务端模板（三选一）
  --template-json <path>      使用本地 JSON 模板（三选一）
  --template-zip <path>       使用 zip 包（三选一）
  --name <name>               名称（模板未提供时必需）
  --description <desc>        描述
  --workspace <path>          工作区路径
  --session-timeout <sec>     会话超时时间（秒）
  --json                      输出 JSON
```

### qoderwake waker update \<field\>
更新 waker 的指定字段。
```
用法：qoderwake waker update <field> [value] --waker-id <id> [options]

字段类型：
  标量字段：name / description / avatar
  JSON 字段：coreCapabilities / workStyles / deliveryCommitments / skill / mcp
  文本字段：identity / persona / bible

选项：
  --waker-id <id>    必需
  --file <path>      从文件读取值
  --append           追加模式（仅 JSON/文本字段）
  --json             输出 JSON
```

### qoderwake waker export
导出 waker 为 zip 包。
```
选项：
  --waker-id <id>    必需
  --out <path>       必需，输出路径
```

### qoderwake waker delete
删除 waker。
```
选项：
  --waker-id <id>    必需
  --json             输出 JSON
```

---

## 项目命令（project）

### qoderwake project list
列出 waker 下的所有项目。
```
选项：
  --waker-id <id>    必需
  --format / --json  输出格式
```

### qoderwake project create
为 waker 创建新项目。
```
选项：
  --waker-id <id>                  必需
  --name <name>                    必需
  --description <desc>             描述
  --path <path>                    文件系统源（与 --git-url 互斥）
  --git-url <url>                  Git 仓库 URL
  --local-path <path>              Git 本地克隆路径
  --label <label>                  上下文源标签
  --initializer-command <cmd>      Shell 初始化命令
  --initializer-timeout <sec>      初始化超时
  --json                           输出 JSON
```

参数决策表：

| 参数 | 是否可默认 | 何时需要用户确认或手动提供 |
|---|---|---|
| `--waker-id` | 不可默认 | 当前会话上下文已有 waker id 时直接使用；否则先 `qoderwake waker list` 让用户选择。 |
| `--name` | 不可默认 | 可从仓库名或本地目录名推导；无法推导时让用户提供。 |
| `--path` | 与 `--git-url` 二选一 | 用户要绑定本地已有仓库或工作目录时必须提供。除非用户已明确给出本地路径，否则通过 Other 让用户输入；不要把当前工作目录作为默认选项。 |
| `--git-url` | 与 `--path` 二选一 | 用户要从远程 Git 仓库初始化时必须提供。需要用户输入时，在问题中提示选择 Other 并输入一个或多个 Git URL；不要设置"当前仓库"或"指定其他仓库"这种选项。 |
| `--local-path` | 可省略 | 仅 `--git-url` 模式下用户要求指定本地克隆位置时使用；否则由系统默认。 |
| `--description` / `--label` | 可省略 | 用户给出用途、环境或标签时传入；否则不问。 |
| `--initializer-command` | 可省略 | 只有用户要求初始化依赖、构建索引或运行脚本时才确认。 |
| `--initializer-timeout` | 可默认 | 只有设置了 initializer 且用户要求超时时间时才传。 |

AskUserQuestion 规则：project 的路径/URL 采集必须走自动 `Other` 输入框；问题文案写清楚"请选择 Other 并输入一个或多个 Git URL，或一个本地路径"。不要提供"当前仓库"、"指定其他仓库"这类选项；如果允许跳过，只能提供"暂不绑定 project"这种可直接执行项。

### qoderwake project get
查看项目详情。
```
选项：
  --waker-id <id>      必需
  --project-id <id>    必需
  --json               输出 JSON
```

### qoderwake project update
更新项目配置（PATCH 语义）。
```
选项：
  --waker-id <id>      必需
  --project-id <id>    必需
  --name / --description / --path / --git-url / --local-path / --label
  --initializer-command / --initializer-timeout
  --json               输出 JSON
```

### qoderwake project delete
删除项目。
```
选项：
  --waker-id <id>      必需
  --project-id <id>    必需
```

### qoderwake project onboard
触发项目 onboarding 初始化。
```
选项：
  --waker-id <id>      必需
  --project-id <id>    必需
```

---

## 自动化命令（automation）

### qoderwake automation list
列出 waker 下的自动化任务。
```
选项：
  --waker-id <id>    必需
```

### qoderwake automation detail
查看任务详情、近期 run 和 task。
```
选项：
  --waker-id <id>          必需
  --automation-id <id>     必需
  --run-id <id>            查看指定 run 的 task
  --runs-limit <n>         近期 run 数量（1-50，默认 10）
  --tasks-limit <n>        近期 task 数量（1-50，默认 10）
```

### qoderwake automation create
创建自动化任务。当前仅支持 `schedule` 子命令（定时触发），运行 `qoderwake automation create --help` 以查阅实际可用子命令。

#### qoderwake automation create schedule
创建定时触发的自动化任务（按 cron 表达式或一次性时间戳执行）。

如果用户没有明确给出调度类型、具体时间/cron、时区、prompt 或是否立即启用，先用 `AskUserQuestion` 澄清，再执行本命令；不要自行猜默认值后直接创建。
```
选项：
  --waker-id <id>             必需
  --name <name>               必需，任务名称
  --schedule-type <type>      必需，取值 "cron" 或 "one-time"
  --cron <expression>         cron 表达式（仅 schedule-type=cron 需要）
  --cron-preset <preset>      cron 预设：hourly / daily / weekly / monthly / custom（默认）
  --run-at <timestamp>        ISO 8601 时间戳（仅 schedule-type=one-time 需要）
  --timezone <tz>             IANA 时区，不传时取系统时区
  --project-id <id>           可选，本地 qoderwake 项目绑定
  --prompt <text>             任务提示词（与 --prompt-file 二选一）
  --prompt-file <path>        从文件读取 prompt
  --model <model>             qodercli 模型，默认 auto
  --enabled <bool>            是否启用（默认 true）
  --idempotency-key <key>     可选，跨重试复用的创建操作键
```

参数决策表：

| 参数 | 是否可默认 | 何时需要用户确认或手动提供 |
|---|---|---|
| `--waker-id` | 不可默认 | 若当前会话上下文有当前 waker id，可直接使用；否则先 `qoderwake waker list` 让用户选择。 |
| `--name` | 不可默认 | 用户未给任务名称时，用 `AskUserQuestion` 给出 2-4 个可读名称选项，或让用户在 Other 中填写。 |
| `--schedule-type` | 不可默认 | 用户只说"定时/周期性/跑一下"但没说明周期时，必须问：每天、每周、一次性、自定义 cron。 |
| `--cron` | 不可默认 | `--schedule-type cron` 时必需；用户只说"每天/每周"但没给具体时间时，必须问具体时间和时区。 |
| `--run-at` | 不可默认 | `--schedule-type one-time` 时必需；必须让用户提供明确 ISO 8601 时间或可解析的日期时间，并确认时区。 |
| `--cron-preset` | 可默认 `custom` | 能从用户话术确定 daily/weekly/monthly 时应显式传入；自定义 cron 或无法判断时用默认 `custom`。 |
| `--timezone` | CLI 可默认 | 如果用户给的是本地自然语言时间，优先确认时区；中国用户/上下文明确时可建议 `Asia/Shanghai` 作为推荐项。 |
| `--project-id` | 可省略 | 只有用户要求绑定项目、prompt 依赖项目上下文，或当前会话已有明确 project 时才传；多个项目时先列表让用户选择。 |
| `--prompt` / `--prompt-file` | 不可默认 | 必须由用户目标转写或用户提供；长 prompt、包含多行步骤或敏感上下文时写文件并用 `--prompt-file`。 |
| `--model` | 可默认 `auto` | 用户未指定模型时不需要确认；只有用户要求特定模型时才传。 |
| `--enabled` | CLI 默认 `true` | 创建后是否立即生效会产生后台执行，用户没明确时应确认；推荐项可为"立即启用"。 |
| `--idempotency-key` | Agent 会话可自动派生 | 同一次用户创建操作需要跨会话/跨进程重试时显式复用；同键异参会返回冲突，不能换参数继续复用。 |
| 输出格式 | 不适用 | `automation create schedule` 不支持 `--format` / `--json`；成功后默认输出带 `[qoderwake]` 前缀的 JSON 摘要，按默认输出解析。 |

澄清优先级：先补齐 `schedule-type`、时间/cron、prompt、enabled；其次确认 `timezone` 和 `project-id`；`model`、`cron-preset` 只有影响结果或用户提到时再问。

注意：
- 创建 automation 必须使用完整子命令 `qoderwake automation create schedule ...`。
- `qoderwake automation create` 父命令只用于查看帮助；不要把 `--waker-id`、`--project-id`、`--format` 等创建参数传给父命令。
- `automation create schedule` 不支持 `--format` / `--json`，不要追加输出格式参数。

Aone/A1 workitem 类 prompt 的额外要求：Aone 项目空间、需求池或迭代必须由用户提供明确 ID、名称或 URL。AskUserQuestion 的选项只能放已知且可直接使用的项目；如果需要用户输入，必须在问题中提示选择 Other 并填写项目 ID/URL 或需求池/迭代 ID/URL，不要使用"指定项目 ID"、"指定需求池/迭代"这类假选项。

示例：
```
qoderwake automation create schedule \
  --waker-id agent_123 \
  --name "每日评审" \
  --schedule-type cron \
  --cron "0 9 * * *" \
  --timezone Asia/Shanghai \
  --prompt-file ./review.md

qoderwake automation create schedule \
  --waker-id agent_123 \
  --name "发版提醒" \
  --schedule-type one-time \
  --run-at 2026-06-01T09:00:00+08:00 \
  --prompt "提醒发版群"
```

### qoderwake automation test-pull
测试拉取配置。
```
选项：
  --waker-id <id>          必需
  --automation-id <id>     必需
```

### qoderwake automation run-now
立即触发一次执行。
```
选项：
  --waker-id <id>          必需
  --automation-id <id>     必需
```

### qoderwake automation update
更新自动化任务配置。
```
选项：
  --waker-id <id>              必需
  --automation-id <id>         必需
  --name <name>                任务名称
  --enabled <bool>             启用/禁用
  --prompt <text>              任务提示词（与 --prompt-file 互斥）
  --prompt-file <path>         从文件读取提示词
  --pull-config-json <json>    pullConfig JSON
  --pull-config-file <path>    从文件读取 pullConfig
  --permissions-json <json>    权限 JSON
  --file-system <perm>         文件系统权限：read / read-write / none
  --network <bool>             网络权限
  --run-commands <bool>        命令执行权限
  --command-allow-list <cmds>  允许的命令列表
  --schedule-type <type>       cron / one-time
  --cron <expression>          cron 表达式
  --cron-preset <preset>       hourly / daily / weekly / monthly / custom
  --run-at <timestamp>         一次性任务 ISO 8601 时间
  --timezone <tz>              IANA 时区
```

修改名称或定时配置必须使用 `automation update` 原地更新，不要通过再创建一条任务来代替。
涉及定时参数时 CLI 会读取当前配置并合并未指定字段；从 cron 切换为 one-time 时必须提供
`--run-at`，从 one-time 切换为 cron 时必须提供 `--cron`。

### qoderwake automation delete
删除自动化任务。
```
选项：
  --waker-id <id>          必需
  --automation-id <id>     必需
```

### qoderwake automation inspect run
诊断 run 数据。
```
选项：
  --worker-id <id>         必需
  --run-id <id>            必需
  --format <fmt>           输出格式：table / json / timeline
  --include-prompt         包含 prompt 文本
  --events-limit <n>       事件最大行数（1-200）
  --comments-limit <n>     评论最大行数（1-200）
  --outbox-limit <n>       outbox 最大行数（1-200）
```

---

## 会话命令（session）

### qoderwake session list
列出会话。
```
选项：
  --waker-id <id>      按 Waker 过滤
  --status <status>    按状态过滤
  --format / --json    输出格式
```

### qoderwake session create
创建新会话。
```
选项：
  --waker-id <id>              必需
  --title <title>              必需
  --message <msg>              初始消息（与 events 互斥）
  --cwd <path>                 临时工作目录（与 --project-id 互斥）
  --project-id <id>            项目绑定
  --events-json <json>         初始事件 JSON 数组
  --events-json-file <path>    从文件读取事件
  --json                       输出 JSON
```

### qoderwake session detail
查看会话详情。
```
选项：
  --session-id <id>    必需
  --format <fmt>       输出格式：text（默认）/ json
  --json               输出 JSON
```

### qoderwake session send
向会话发送消息/事件。
```
选项：
  --session-id <id>            必需
  --message <msg>              文字消息（与 events 互斥）
  --events-json <json>         事件 JSON 数组
  --events-json-file <path>    从文件读取事件
  --json                       输出 JSON
```

### qoderwake session events
获取会话事件历史。
```
选项：
  --session-id <id>              必需
  --after-sequence-num <n>       获取此序列号之后的事件
  --limit <n>                    最大获取数
  --json                         输出 JSON
```

### qoderwake session stream
实时流式监听会话事件（SSE 输出到 stdout）。
```
选项：
  --session-id <id>            必需
  --from-sequence-num <n>      从指定序列号开始
```

### qoderwake session trajectory
生成会话轨迹摘要。
```
选项：
  --session-id <id>            必需
  --format <fmt>               输出格式：markdown（默认）/ json
  --scope <scope>              memory scope：agent / project
  --project-id / --project-name / --project-root
  --out <path>                 写入文件
  --no-write-memory            不写入 sessions/redacted/
  --force                      覆盖已有
  --max-step-chars <n>         每步最大字符数
```

### qoderwake session artifacts
查看产出物和文件变更。
```
选项：
  --session-id <id>              必需
  --include-file-changes         包含文件变更详情
  --file-changes-limit <n>       文件变更最大数
  --file-changes-cursor <cur>    分页游标
  --format / --json              输出格式
```

---

## 技能命令（skill）

### qoderwake skill list
列出 waker 的技能。
```
选项：
  --waker-id <id>    必需
```

### qoderwake skill add
注册技能。
```
选项：
  --waker-id <id>          必需
  --skill-id <id>          必需
  --name <name>            展示名称（默认为 skillId）
  --description <desc>     描述
  --skill-version <ver>    版本号
  --install-url <url>      安装包 URL
  --format <format>        输出格式：json（可选；默认也输出 JSON）
```

### qoderwake skill search
搜索技能市场，返回可以送给 `skill add --install-url` 的 `SKILL_ID` 和 `DOWNLOAD_URL`。
```
选项：
  --keyword <keyword>      全文关键词过滤
  --category <category>    分类过滤
  --tag <tags>             标签过滤（逗号分隔多个）
  --page <page>            页码（从 1 开始）
  --page-size <pageSize>   每页条数
  --order-by <field>       排序字段，如 install_count / updated_at / skill_name
  --order <0|1>            排序方向：0 升序，1 降序
  --format <format>        输出格式：table 或 json（默认 table）
  --json                   等效于 --format json，输出原始 JSON 代替表格
```
注意：`skill search` 查询全局技能市场，不接收 `--waker-id`。拿到 `SKILL_ID` 和 `DOWNLOAD_URL` 后，再用 `skill add --waker-id <id> ...` 安装到指定员工。

示例：
```
qoderwake skill search --keyword code-review --page 1 --page-size 20
qoderwake skill search --keyword qoderwork-ppt --format json
# 从表格拿到 SKILL_ID 和 DOWNLOAD_URL 后：
qoderwake skill add --waker-id <id> --skill-id <SKILL_ID> --install-url <DOWNLOAD_URL>
```

### qoderwake skill upload \<zipPath\>
上传 zip 包创建/更新技能版本。
```
位置参数：<zipPath>    本地 zip 包路径
选项：
  --waker-id <id>    必需
```

### qoderwake skill versions
列出技能版本。
```
选项：
  --waker-id <id>      必需
  --skill-id <id>      必需
```

### qoderwake skill diff
对比版本差异。
```
选项：
  --waker-id <id>      必需
  --skill-id <id>      必需
  --version <ver>      与前一版本对比（与 --from/--to 互斥）
  --from <ver>         起始版本（与 --to 同时使用）
  --to <ver>           结束版本（与 --from 同时使用）
  --json               输出 JSON
```

### qoderwake skill rollback
回滚到指定版本。
```
选项：
  --waker-id <id>      必需
  --skill-id <id>      必需
  --to <versionId>     必需，目标版本
  --reason <reason>    回滚原因
```

### qoderwake skill toggle
启用/禁用技能。
```
选项：
  --waker-id <id>         必需
  --skill-id <id>         必需
  --enabled <true|false>  必需
```

### qoderwake skill delete
删除技能及所有版本。
```
选项：
  --waker-id <id>      必需
  --skill-id <id>      必需
```

### qoderwake skill install
安装技能到本地内置目录。
```
选项：
  --waker-id <id>      必需
  --skill-id <id>      必需
```

---

## MCP 命令（mcp）

### qoderwake mcp list
列出 waker 的 MCP 服务器。
```
选项：
  --waker-id <id>    必需
```

### qoderwake mcp get
查看 MCP 配置。
```
选项：
  --waker-id <id>    必需
  --mcp-id <id>      必需
```

### qoderwake mcp add
新增 MCP 服务器。

stdio、HTTP、SSE 都会创建不可变配置提案并等待用户确认：确认窗口 90 秒，CLI 总等待上限 120 秒。等待期间不会探测远端、写入 MCP 配置、同步 extension 或重启 session；不要因为命令暂未返回而重试。

stdio 与 HTTP/SSE 使用同一提案确认边界，没有额外的风险勾选步骤；但 POSIX/Windows shell、显式 `shell`、`npx -c/--call` 会直接返回 `MCP_STDIO_SHELL_EXECUTION_DENIED`，不进入确认；不得自动改写成等价形式或重试。
```
JSON 模式：
  --waker-id <id>         必需
  --json <json>           MCP JSON 对象
  --json-file <path>      从文件读取 MCP JSON

字段化模式：
  --waker-id <id>         必需
  --name <name>           必需
  --description <desc>    描述
  --command <cmd>         stdio 启动命令（与 --http-url 择一）
  --args <args>           逗号分隔的命令参数
  --env <json>            JSON 环境变量
  --http-url <url>        HTTP/SSE URL（与 --command 择一）
  --transport <type>      传输类型：stdio / http / sse
  --headers <json>        JSON HTTP headers
  --header <KEY=VALUE>    HTTP 头（可多次）
  --oauth-client-metadata-url / --oauth-client-id / --oauth-client-secret
  --oauth-token-auth-method / --oauth-scope / --oauth-resource-metadata-url
```

### qoderwake mcp update
更新 MCP 配置（字段化，与 add 相同选项，至少提供一个更新字段）。

所有 transport 都与 add 一样先等待用户批准；批准对象是 daemon 已冻结的最终 payload，批准后不能由客户端替换参数。等待期间目标 MCP 被其它操作修改时返回 `mcp_config_proposal_stale`，不会覆盖新状态。
```
选项：
  --waker-id <id>    必需
  --mcp-id <id>      必需
  （同 add 的字段化选项，但不支持 --json/--json-file）
```

### qoderwake mcp toggle
启用/禁用 MCP。

toggle 会在创建提案时固化成明确的 enable 或 disable，并等待用户确认；批准前状态变化会返回 stale，不会重新读取后反转另一个状态。

enable 会按当前冻结的 stdio 配置重新分类；历史上已经添加或确认过的 Connector 不会继承风险豁免。
```
选项：
  --waker-id <id>         必需
  --mcp-id <id>           必需
  --enabled <true|false>  必需
```

### qoderwake mcp delete
删除 MCP。

delete 会展示目标 Connector、transport、当前启用状态和工具不可用影响，并在批准前保持 store、runtime 与 auth 状态不变。
```
选项：
  --waker-id <id>    必需
  --mcp-id <id>      必需
```

`mcp list` / `mcp get` / `mcp auth start` / `mcp refresh-tools` 不修改 Connector desired config，不进入本确认流程。cancel / timeout / supersede / stale 后禁止自动重试、换参数格式、直接调 REST 或改本地 JSON；只有用户再次明确要求时才重新执行。

### qoderwake mcp auth start
启动 OAuth 授权流。
```
选项：
  --waker-id <id>    必需
  --mcp-id <id>      必需
```

### qoderwake mcp refresh-tools
刷新工具列表缓存。
```
选项：
  --waker-id <id>    必需
  --mcp-id <id>      必需
```

---

## 记忆命令（memory）

所有 memory 命令支持 `--waker-id`（或废弃别名 `--agent-id`），scope 相关：`--scope agent|project`、`--project-id`、`--project-name`、`--project-root`。

### qoderwake memory show
查看记忆内容。
```
选项：
  --waker-id <id>        必需
  --scope <scope>        agent（默认）/ project
  --view <view>          long_term / daily / index / topics / sessions / all
  --project-id <id>      scope=project 时必需
  --session-id <id>      过滤到单个 session
```

### qoderwake memory dream
触发 dream 流程。
```
选项：
  --waker-id <id>            必需
  --scope <scope>            agent / project
  --mode <mode>              preview（默认）/ apply
  --project-id <id>          scope=project 时必需
  --session-id <id>          诊断用
  --preview-run-id <id>      apply 时复用 preview
  --timeout-ms <ms>          超时（默认 120000）
```

### qoderwake memory lifecycle inspect
查看生命周期统计。
```
选项：
  --waker-id <id>        必需
  --scope / --project-id / --project-name / --project-root
```

### qoderwake memory update
更新记忆文本片段。
```
选项：
  --waker-id <id>            必需
  --path <path>              必需，memory 文件路径
  --old-text <text>          必需，待替换文本
  --content <text>           必需，新内容
  --scope / --project-id
  --expected-hash <hash>     守卫哈希
  --reason <reason>          更新原因
  --dry-run                  仅预览
```

### qoderwake memory remove
删除记忆文本片段。
```
选项：
  --waker-id <id>            必需
  --path <path>              必需
  --old-text <text>          必需，待删除文本
  --scope / --project-id
  --expected-hash <hash>     守卫哈希
  --reason <reason>          删除原因
  --dry-run                  仅预览
```

### qoderwake memory snapshot
创建手动快照。
```
选项：
  --waker-id <id>            必需
  --scope / --project-id
  --include-sessions         包含脱敏 session 文件
  --operation <op>           快照标签（默认 manual_snapshot）
```

### qoderwake memory versions
列出快照。别名：`memory list` / `memory ls`。
```
选项：
  --waker-id <id>        必需
  --scope / --project-id
```

### qoderwake memory diff
对比两个快照差异。
```
选项：
  --waker-id <id>        必需
  --from <snapshotId>    必需，起始快照
  --to <snapshotId>      必需，目标快照
  --scope / --project-id
```

### qoderwake memory rollback
回滚记忆文件到指定快照。
```
选项：
  --waker-id <id>            必需
  --snapshot-id <id>         必需
  --path <path>              必需
  --scope / --project-id
  --apply                    实际写入（默认 dry-run）
```

### qoderwake memory export
导出记忆为 tar.gz。
```
选项：
  --waker-id <id>            必需
  --out-path <path>          必需，输出路径
  --scope / --project-id
  --include-sessions         包含脱敏 session
  --include-versions         包含历史 manifests 和 git bundle
```

### qoderwake memory import
从 tar.gz 导入记忆（replace 模式）。
```
选项：
  --waker-id <id>            必需
  --package-path <path>      必需，tar.gz 路径
  --scope / --project-id
  --apply                    实际写入（默认 dry-run）
```

---

## 权限命令（permission）

配置型命令的 `--json` 是输入对象；如需原始 JSON 输出，使用 `--format json`。

**变更类命令（update / patch）约束**：仅在用户明确提出权限变更诉求并确认目标值后执行；执行其他任务时不得以"加强防护"等理由自行发起权限变更。详见 SKILL.md 权限章节。

### qoderwake permission get
查看 waker 级权限配置。
```
选项：
  --waker-id <id>    必需
  --format <fmt>     table（默认）/ json
```

### qoderwake permission update
整体更新 waker 级权限配置。**仅限用户显式要求并确认后执行**。
```
选项：
  --waker-id <id>       必需
  --json <object>       权限 JSON 对象
  --json-file <path>    从文件读取权限 JSON 对象
  --format <fmt>        table（默认）/ json
```

### qoderwake permission patch
更新单个权限 section。**仅限用户显式要求并确认后执行**。
```
子命令：
  tool-guard
  file-guard
  builtin-tools
  model-security

选项：
  --waker-id <id>       必需
  --json <object>       section JSON 对象
  --json-file <path>    从文件读取 section JSON 对象
  --format <fmt>        table（默认）/ json
```

### qoderwake permission builtin
查看内置权限参考数据。
```
子命令：
  tool-guard-rules
  tool-catalog
```

---

## IM Channel 命令（channel）

### qoderwake channel settings
查看 channel 全局设置。

### qoderwake channel list
列出 IM channel。
```
选项：
  --waker-id <id>    按 waker 过滤
  --format <fmt>     table（默认）/ json
```

### qoderwake channel get \<channel-id\>
查看 channel 详情。

### qoderwake channel config \<channel-id\>
更新 channel 配置。
```
选项：
  --json <object>       配置 JSON 对象
  --json-file <path>    从文件读取配置 JSON 对象
  --format <fmt>        table（默认）/ json
```

### qoderwake channel start|stop|restart|delete \<channel-id\>
启动、停止、重启或删除 channel。`delete` 执行前需要用户确认。

### qoderwake channel dingtalk qr-start
开始钉钉二维码注册。

### qoderwake channel dingtalk qr-poll
轮询钉钉二维码注册结果。
```
选项：
  --device-code <code>    必需
```

### qoderwake channel pairing generate-code
生成 pairing code。
```
选项：
  --channel-id <id>    必需
```

### qoderwake channel pairing list
列出 pairing 记录。
```
选项：
  --channel-id <id>    按 channel 过滤
  --robot-id <id>      按 robot 过滤
  --format <fmt>       table（默认）/ json
```

### qoderwake channel pairing pending
列出 pending pairing 记录。
```
选项：
  --channel-id <id>    按 channel 过滤
  --robot-id <id>      按 robot 过滤
  --format <fmt>       table（默认）/ json
```

### qoderwake channel pairing delete \<pairing-id\>
删除 pairing 记录。执行前需要用户确认。

### qoderwake channel pairing approve|ignore
审批或忽略 pairing 请求。`ignore` 执行前需要用户确认。
```
选项：
  --channel-id <id>      必需
  --robot-id <id>        必需
  --binding-key <key>    必需
```

---

## Extension 命令（extension）

### qoderwake extension list
只读查看本地 extension runtime 状态。

### qoderwake extension ls
`extension list` 的别名。

---

## 插件命令（plugin）

### qoderwake plugin list
列出已安装插件（表格输出）。

### qoderwake plugin info \<name\>
查看插件详情（JSON 输出）。

### qoderwake plugin install \<dir-or-zip\>
安装插件。
```
选项：
  --enable       安装后启用
  --no-enable    安装后不启用
  --replace      允许替换同版本
```

### qoderwake plugin enable \<name\>
启用插件。
```
选项：
  --version <ver>    指定版本
```

### qoderwake plugin disable \<name\>
禁用插件。

### qoderwake plugin uninstall \<name\>
卸载插件。
```
选项：
  --version <ver>    仅卸载该版本
```

### qoderwake plugin reload \<name\>
热重载插件的 events capability。

### qoderwake plugin events
列出事件目录与订阅插件。
```
选项：
  --format <fmt>     table（默认）/ json
  --json             输出 JSON
```

### qoderwake plugin scheduled-task list
列出调度任务。
```
选项：
  --plugin <name>    按插件过滤
  --format / --json  输出格式
```

### qoderwake plugin scheduled-task register
注册调度任务。
```
选项：
  --plugin <name>      必需
  --task-id <id>       必需
  --cron <expr>        必需
  --payload <json>     JSON payload
  --json               输出 JSON
```

### qoderwake plugin scheduled-task unregister
反注册调度任务。
```
选项：
  --plugin <name>      必需
  --task-id <id>       必需
  --json               输出 JSON
```
