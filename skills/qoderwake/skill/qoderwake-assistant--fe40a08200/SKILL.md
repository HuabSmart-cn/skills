---
name: qoderwake-assistant
description: "MUST use first for current QoderWake waker/数字员工 management: automation/定时任务, skills (含创建新技能/create skill), MCP/connectors, permissions, IM channels, extensions, projects, sessions, memory, plugins, or wakers."
---

# QoderWake 助手

## 运行模式

检测环境变量 `QODERWAKE_SKILL_PROFILE`：

- 若值为 `im-control`：你正在 IM 控制台中运行。严格遵守 `references/im-control-profile.md` 中的约束，只使用其中列出的命令。对话、自动任务的管理操作必须通过 `qoderwake_im` MCP 工具完成。
- 否则（包括未设置）：你在 Console 普通对话中运行。遵守当前全部规则，所有 8 个域的命令均可使用。

## 定位

本 Skill 帮助用户**通过对话的方式**操作 QoderWake：当用户在与某个 QoderWake 数字员工（waker）交流时，提出"帮我配置 / 安装 / 创建 / 修改 …"这类需要落到 QoderWake 平台能力上的诉求，本 Skill 指导你（agent）把对话意图翻译成对应的 `qoderwake` CLI 命令，替用户完成操作。

**必须使用本 Skill 的路由规则**：

- 用户提到"当前员工"、"当前数字员工"、"这个员工"、"这个 waker"并要求查看或管理 skill、MCP、permission、channel、extension、session、project、memory、automation、plugin、waker 时，先加载本 Skill。
- 不要在未加载本 Skill 的情况下直接用 Bash 试探 `qoderwake` 命令，也不要从源码入口 `node ./package/src/cli/index.ts` 运行 CLI。
- 加载本 Skill 后，优先使用 PATH 中的 `qoderwake`；如果本地开发环境明确要求使用构建产物，才使用 `./dist/qoderwake`。

典型对话场景（以下话术任意命中即应使用本 Skill）：

- "帮我给这个数字员工**创建一个自动化任务** / 定时跑一下 / 周期性触发…"
- "帮我**安装 / 启用 / 升级 / 卸载**这个**插件**（plugin）"
- "帮我**创建一个新技能** / **安装 / 注册 / 上传 / 回滚**这个**技能**（skill）"
- "帮我**配置一个 MCP** / **加一个连接器** / 接入 GitHub MCP / 接入某某外部工具…"
- "帮我**新建一个项目**绑定到这个员工 / 让员工**理解这个仓库**（onboarding）"
- "帮我**新建会话**并发一条消息 / 实时**看一下**它现在在干什么"
- "帮我**查一下 / 整理一下**它的**记忆**，dream 一下，回滚到上一个版本…"
- "帮我**调整权限** / 看看 tool guard / 文件访问 / 内置工具权限"
- "帮我配置**钉钉 / IM channel** / 处理 pairing / 生成绑定码"
- "帮我看看本地有哪些 **extension** 在运行"
- "帮我**导出**这个员工 / 把它**复制**一份"

## 硬约束

- 所有操作通过 `qoderwake` CLI 命令执行，**不要**直接调用 HTTP API。
- 程序化解析返回值时，只有在对应命令 help 或本 Skill reference 明确列出 `--json` / `--format json` 时才能追加输出格式参数；展示给用户看时使用默认 table。`automation create schedule` 不支持 `--json` / `--format`，不要追加。
- 所有需要的 ID（`--waker-id` / `--project-id` / `--session-id` / `--mcp-id` 等）必须显式传入；如果用户没给，先用 `qoderwake xxx list` 让用户选择，**不要凭空猜 ID**。
- 配置不完整或有多个合理选项时，优先调用 qodercli 内置 `AskUserQuestion` 工具向用户澄清，拿到回答后再执行 CLI；不要为了完成任务自行猜默认值。
- 涉及破坏性操作（`delete` / `rollback --apply` / `memory import --apply` / `mcp delete` / `plugin uninstall` 等），先复述将执行的命令并请用户确认，再执行。
- 用户 session 触发的管理操作默认只允许修改**当前数字员工**：`project/mcp/skill/permission/automation/memory` 等员工级命令使用当前 session 的 `wakerId` 作为 `--waker-id`。如果用户要求修改其它数字员工，或执行无法用 `--waker-id` / `--worker-id` 判定目标员工的管理写命令（例如 `qoderwake waker create`、`qoderwake project create --public`），必须先二次确认目标范围，再执行 CLI。
- 敏感信息（token、secret、PAT）在 JSON 输出中会被自动脱敏；你也**不得**把用户提供的 token 回显到对话或日志里。
- 使用前需保证 daemon 已启动且已登录；命令报"未登录"或"daemon 未运行"时，引导用户先 `qoderwake login` / 启动 daemon，而不是反复重试。
- **不要**在当前会话内执行 `qoderwake stop` / `qoderwake restart`：当前会话由 daemon 托管，停 daemon 会立即中断自己的会话（stream truncated）。确需重启时必须先向用户说明风险并获得明确确认。
- 命令返回 HTTP 401 `FRONTEND_AUTH_REQUIRED`（Frontend access login is required for externally exposed daemon）时，不代表登录态损坏——这是 expose 模式的前端访问登录门禁，重启 daemon 不能消除该 401，不要靠 `qoderwake restart` 自救。
- `extension` 当前只读，对齐 Console 的只读 Extension 页面；安装 extension 仍是文件系统投放后重启 daemon。
- CLI 已覆盖 Console 核心对象管理，但不是完整 Console 无头版；GitHub auth/trigger 高级配置、memory timeline/document 精细编辑、session stop/delete/binding 切换等仍需 Console 或后续 CLI 扩展。Skill 内容更新 / 自进化已经由 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage` 承接。
- 用户要求修改、更新、优化、进化 Skill 内容时，唯一推荐入口是 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage`。不要通过 `qoderwake skill add`、`qoderwake skill upload`、`qoderwake skill install` 或这些命令的 help 探索来替代内容更新；`add` 是安装市场/URL skill，`upload` 是用户明确提供 zip 时重新上传版本，二者不是对话内细粒度更新 Skill 内容的方式。
- 只有用户明确要求"创建一个新技能 / 新 Skill"，或经现有可自进化 Skill 比对确认没有匹配承载者时，才允许 create。普通员工 Skill 用 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --waker-id <id> --action create` 落入当前员工；Conversation Run 中用户明确要求 Group Skill / 群 Skill 时，必须用 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --conversation-id "$QODERWAKE_CONVERSATION_ID" --action create` 落入当前 Conversation。两个 owner 参数必须二选一，禁止把 Group Skill 建到执行 Waker。也禁止按通用 `skill-creator` 技能的默认约定把 `SKILL.md` 写入 `~/.qoder/skills/<name>`。必须先用 `Skill(skill-creator)` 起草内容，但最终落点必须是 `skill manage --action create`。
- 当调用方明确标记为后台 Skill Review，且只开放 `Skill` 工具时，必须调用 Waker 运行时中的 `skill-creator` 起草内容；Review 先根据全部可自进化 Skill 的 name/description 判断更新、创建或不沉淀。创建场景返回完整的新 `SKILL.md`；更新场景必须再调用 `Skill` 工具加载所选已有 Skill，并返回融合后的完整更新稿，不得只返回追加片段。该隔离进程不写文件、不执行 `skill manage`，只按调用方契约返回草案，由 daemon 校验后完成最终持久化。这是上述 Waker `skill-creator` 路由的后台模式，不是本地模板或另一套 Skill 存储渠道。

### 会话作用域安全

- 当前 session 能提供 `wakerId` 时，除非用户明确指定其它员工，所有员工级命令都必须传当前 `wakerId`。
- 不要为了完成任务自行 `waker list` 后挑选另一个员工；只有在当前 session 缺少 `wakerId` 或用户明确要求跨员工操作时，才让用户选择目标员工。
- `qoderwake waker create` 没有 `--waker-id`，会创建一个独立的新数字员工，属于当前 session 员工之外的新增资源；即使用户说"新建一个数字员工"，也要先确认新员工名称、模板来源和影响范围，再执行。
- 跨员工修改示例：`qoderwake skill add --waker-id <other-waker>`、`qoderwake mcp update --waker-id <other-waker>`、`qoderwake automation delete --waker-id <other-waker>`。这类命令执行前先明确告诉用户目标员工 ID 和将修改的对象，等待确认。
- 无目标员工管理写示例：`qoderwake waker create`、`qoderwake session create`、`qoderwake project create --public`、`qoderwake project update --public`、`qoderwake project delete --public`。这类命令没有 `--waker-id` / `--worker-id`，执行前必须让用户确认目标范围；公共项目还要明确“这是公共项目，不是当前员工私有 project”。
- 运行时权限系统会对上述命令触发二次审批；不要通过改写命令、直接调 HTTP API 或修改本地文件绕过审批。

## 对话澄清：AskUserQuestion

当用户只给出自然语言目标，但缺少必需配置，或存在多个安全做法时，先调用 `AskUserQuestion` 让用户选择。典型例子：

- "帮我给当前员工创建一个定时任务"：缺少任务名称、调度类型、时间/cron、prompt、是否立即启用。
- "每天跑一下"：缺少具体时间、时区、任务内容。
- "给这个员工接一个 MCP"：缺少 transport、URL/command、鉴权方式。
- "调整权限严格一点"：缺少具体权限域和允许/拒绝策略。

使用规则：

- `AskUserQuestion` 是 qodercli 内置工具，不是 `qoderwake` CLI 子命令；当前 session 暴露该工具时才调用。
- 每次问 1-4 个问题；每个问题 2-4 个选项；不要手写 `Other` 选项，UI 会自动提供。
- 如果有推荐方案，把它放在第一个选项，并在 label 后追加 `(Recommended)`。
- 选项文案必须直接对应后续 CLI flags，避免用户选完后仍无法落命令。
- 选项必须是"选中即可执行"的具体值或具体动作；不要设置"指定其他仓库"、"指定项目 ID"、"指定需求池/迭代"这类选中后仍缺少路径、URL 或 ID 的假选项。
- 需要用户输入路径、URL、ID、cron、关键词等自由文本时，在 question 中明确提示"如果不是上述具体选项，请选择 Other 并输入 ..."；不要把自由文本需求伪装成一个普通选项。
- 对 Git project 这类输入，推荐问题文案是："请提供要关联为 project 的 Git 仓库信息：选择 Other 并输入一个或多个 Git URL，或一个本地路径。" 不要提供"当前仓库"或"指定其他仓库"选项；除非用户已经在同一句里明确给出路径/URL，否则不要替用户猜当前仓库。
- 对 Aone 项目空间，推荐问题文案是："请提供 Aone 项目 ID 或项目 URL；如果要暂不配置，请选择对应选项。" 不要给"指定项目 ID"这种无法承载 ID 的选项。
- 拿到 `answers` 后，把答案映射成 `qoderwake` CLI 参数并继续执行；不要再要求用户重复输入同一信息。
- 如果 `AskUserQuestion` 被禁用或当前通道不能回传用户回答，只说明缺少哪些配置，并给出可复制的最小命令模板。

创建定时 automation 时，推荐一次性问清这些问题：

```json
{
  "questions": [
    {
      "header": "Schedule",
      "question": "这个自动化任务按什么规则触发？",
      "multiSelect": false,
      "options": [
        { "label": "每天固定时间 (Recommended)", "description": "生成 --schedule-type cron 和 daily cron 表达式，适合日常巡检、日报、提醒。" },
        { "label": "每周固定时间", "description": "生成 weekly cron 表达式，适合周报、周例行检查。" },
        { "label": "一次性时间", "description": "生成 --schedule-type one-time 和 --run-at，只运行一次。" },
        { "label": "自定义 cron", "description": "用户会在 Other 中补充 cron 或规则，适合复杂周期。" }
      ]
    },
    {
      "header": "Enable",
      "question": "创建后要立即启用吗？",
      "multiSelect": false,
      "options": [
        { "label": "立即启用 (Recommended)", "description": "创建后 enabled=true，到点自动运行。" },
        { "label": "先停用", "description": "创建为 enabled=false，用户检查后再手动启用。" }
      ]
    }
  ]
}
```

## 对话翻译指南

下面给出"用户说的话 → 你应该跑的 CLI"映射。详细参数见 [references/cli-commands.md](./references/cli-commands.md)。权限、IM channel 和 extension 的配置型命令见 [references/cli-permission-channel-extension.md](./references/cli-permission-channel-extension.md)。

### 1. 自动化任务（automation）

用户意图：让数字员工**自己定时 / 按事件触发**执行某类工作。

> 🚨 **执行态约束（优先级高于下方创建规则）**：如果当前消息包含
> `[QODERWAKE_AUTOMATION_EXECUTION]`，说明这是一条**已经存在**的自动任务正在执行。
> 消息中的“定时 / 每小时 / 每天 / 周期性”等文字默认只是任务背景，**本身不构成创建或修改请求**；
> 仅当任务提示词**显式要求**排程、创建、更新或删除其它自动任务（如任务 A 排程一次性任务 B 的元任务场景）时，
> 才执行对应的 `qoderwake automation` / `qoderwake trigger` 管理命令。

> 🚨 **强制约束（定时任务必须落到 QoderWake 平台，禁止本地操作系统级定时）**：
> 当用户要求"定时 / 每天 / 每周 / 周期性 / 到点自动跑"时，**只能**用 `qoderwake automation create schedule ...` 在 QoderWake 平台侧创建自动化任务。**严禁**用任何操作系统级定时机制替代，包括但不限于：macOS `launchd`（`launchctl load` / `~/Library/LaunchAgents/*.plist`）、`crontab` / `cron`、Linux `systemd` timer、`at`、Windows 任务计划程序（`schtasks`）。
> 原因：QoderWake 右侧"自动任务"列表查询的是**平台侧**记录（`origins=scheduled_task`），本地 launchd/crontab 任务**永远不会**出现在该列表里，到点也不会通过平台触发 waker 会话，用户会看到"暂无自动任务"并认为"定时未生效"。
> 即使本地确实能起一个定时器，也**不是**用户要的效果——必须改用 `qoderwake automation create schedule`，让任务在平台可见、可管理、可触发。若环境缺少 `qoderwake` CLI 或 daemon 未运行，应引导用户先解决 CLI/daemon，而不是退而求其次写本地定时任务。

| 用户说 | 推荐命令 |
|---|---|
| "看看现在配了哪些自动化任务" | `qoderwake automation list --waker-id <id>` |
| "看看这个任务最近跑得怎么样" | `qoderwake automation detail --waker-id <id> --automation-id <id>` |
| "现在手动触发一次" | `qoderwake automation run-now --waker-id <id> --automation-id <id>` |
| "改一下名称 / 提示词 / 频率 / 暂停掉" | `qoderwake automation update …`（`--name` / `--prompt-file` / `--cron` / `--run-at` / `--enabled false` 等），不要创建新任务代替更新。 |
| "这个任务不要了" | `qoderwake automation delete --waker-id <id> --automation-id <id>` |
| "排查一下这次为什么失败" | `qoderwake automation inspect run --worker-id <id> --run-id <id> --format timeline` |

创建新任务时，**当前 CLI 仅支持定时（schedule）触发器**——按 cron 表达式或一次性时间戳触发，不再支持 a1-workitem 等队列拉取触发器。先用 `qoderwake automation create --help` 查看子命令；如果用户描述明显是事件驱动/队列拉取（如 "有新 Aone 工单时触发"），请先告知当前 CLI 只能创建定时任务，并提议改用插件 + `qoderwake plugin scheduled-task register` 或后续扩展。

创建 automation 时必须使用完整子命令 `qoderwake automation create schedule ...`。不要生成 `qoderwake automation create --waker-id ...` 这种父命令带参数的形式；父命令只用于 `--help`，不会接收 `--waker-id` 等创建参数。

**创建定时自动化任务**：

| 用户说 | 推荐命令 |
|---|---|
| "每天早上 9 点跑一次代码评审" | `qoderwake automation create schedule --waker-id <id> --name "daily review" --schedule-type cron --cron "0 9 * * *" --timezone Asia/Shanghai --prompt-file ./review.md` |
| "每周一上午 10 点提醒一下" | `qoderwake automation create schedule --waker-id <id> --name weekly-ping --schedule-type cron --cron "0 10 * * 1" --cron-preset weekly --prompt "发周报提醒"` |
| "2026-06-01 上午 9 点跑一次发版前检查" | `qoderwake automation create schedule --waker-id <id> --name release-check --schedule-type one-time --run-at 2026-06-01T09:00:00+08:00 --prompt-file ./release.md` |

参数要点：
- `--schedule-type` 必传，取值 `cron` 或 `one-time`。
- `--cron` 与 `--schedule-type cron` 搭配；`--run-at` 与 `--schedule-type one-time` 搭配，时间戳需 ISO 8601。
- `--cron-preset` 可选 `hourly` / `daily` / `weekly` / `monthly` / `custom`（默认），仅用于元数据标注。
- `--timezone` 不传时取系统时区；展示给用户的预设要明确时区。
- `--idempotency-key` 可显式复用同一次创建操作的键；Agent 会话不传时 CLI 也会按会话和请求自动派生稳定键，重试同一创建命令不会新增第二条任务。
- `--prompt` / `--prompt-file` 二选一；长 prompt 一律走 `--prompt-file`。
- `--enabled false` 可先创建为停用状态，让用户检查后再启用。
- `automation create schedule` 不支持 `--format` / `--json`；成功后默认会输出带 `[qoderwake]` 前缀的 JSON 摘要，直接从该输出读取 `automationId` / `triggerId`。

### 2. 插件（plugin）

用户意图：给数字员工**装 / 卸 / 启停**一个插件包，或注册插件提供的调度任务。

| 用户说 | 推荐命令 |
|---|---|
| "看看装了哪些插件" | `qoderwake plugin list` |
| "看一下这个插件具体什么情况" | `qoderwake plugin info <name>` |
| "把这个插件装上"（用户给了路径或 zip） | `qoderwake plugin install <dir-or-zip> [--enable]` |
| "启用 / 停用这个插件" | `qoderwake plugin enable <name>` / `qoderwake plugin disable <name>` |
| "卸了它" | `qoderwake plugin uninstall <name>` |
| "热更新一下事件订阅" | `qoderwake plugin reload <name>` |
| "看看现在订阅了哪些事件" | `qoderwake plugin events` |
| "给它注册一个定时任务" | `qoderwake plugin scheduled-task register --plugin <name> --task-id <id> --cron <expr>` |

### 3. 技能（skill）

用户意图：给数字员工**装一个能力包**（如 code-review、test-writing），管理版本与回滚。

| 用户说 | 推荐命令 |
|---|---|
| "看一下这个员工有哪些技能" | `qoderwake skill list --waker-id <id>` |
| "创建一个新技能" | 先起草 `SKILL.md` 内容（大段内容先写入临时文件），再用 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --waker-id <id> --action create --skill-name <name> --content-file <path> --summary <summary>` 创建到当前员工；不要写到 `~/.qoder/skills/` 下 |
| "给当前群创建一个 Group Skill / 群 Skill" | 先起草 `SKILL.md`，再用 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --conversation-id "$QODERWAKE_CONVERSATION_ID" --action create --skill-name <name> --content-file <path> --summary <summary>` 创建到当前 Conversation；不要使用 `--waker-id` |
| "从技能市场搜一个 code review / 测试相关的 skill" | `qoderwake skill search --keyword <关键词> [--category <分类>] [--tag <tag1,tag2>] [--page 1 --page-size 20] [--format table|json]` |
| "刚才搜到的那个 skill 给我装上" | 用 `skill search` 结果中的 `SKILL_ID` 和 `DOWNLOAD_URL` 调 `qoderwake skill add --waker-id <id> --skill-id <SKILL_ID> --install-url <DOWNLOAD_URL>` |
| "注册一个技能"（已知 install URL） | `qoderwake skill add --waker-id <id> --skill-id <id> --name <name> [--install-url <url>]` |
| "把这个 zip 上传当作新版本" | `qoderwake skill upload <zipPath> --waker-id <id>` |
| "看版本历史" | `qoderwake skill versions --waker-id <id> --skill-id <id>` |
| "对比两个版本" | `qoderwake skill diff --waker-id <id> --skill-id <id> --from <v1> --to <v2>` |
| "新版本不行，回滚到旧版本" | `qoderwake skill rollback --waker-id <id> --skill-id <id> --to <ver> --reason <reason>` |
| "启用 / 禁用这个技能" | `qoderwake skill toggle --waker-id <id> --skill-id <id> --enabled <true\|false>` |
| "把它装到本地立刻生效" | `qoderwake skill install --waker-id <id> --skill-id <id>` |
| "删了这个技能" | `qoderwake skill delete --waker-id <id> --skill-id <id>` |

`skill search` 查询全局技能市场，不接收 owner 参数。`skill manage` 必须且只能传一个 owner：员工 Skill 用 `--waker-id`，Group Skill 用 `--conversation-id`；其它员工级命令仍使用 `--waker-id`。

#### 前台对话的更新/创建决策（必须）

- 用户说“记到你的 Skill 里”、“以后按这个规则”、“把这次反馈沉淀下来”时，这是 **update-or-create** 意图，不是 create 意图。用户未明确说“创建/新建一个 Skill”时，不得直接执行 `--action create`。
- 必须先执行 `qoderwake skill list --waker-id <id>`，只把 `source='agent-created'` 以及 `source='user-uploaded' && mutableByAgent=true` 作为可更新候选，并根据 name/description、本轮实际加载/使用记录和紧邻对话上下文选择承载者。
- 如果用户正在纠正某个已有 Skill 刚刚产出的结果，且该 Skill 可自进化，必须更新它；禁止把同一条纠偏规则泛化后另建一个职责重叠的 Skill。
- 选定现有 Skill 后，必须调用 `Skill(<target-skill-name>)` 加载完整 `SKILL.md`，再调用 `Skill(skill-creator)` 保留无关规则并把新规则融入语义匹配位置，最后使用 `skill manage --action patch/edit` 持久化。不要读取或修改 runtime mirror。
- 只有候选比对确认没有语义匹配的可自进化 Skill 时，才能调用 `Skill(skill-creator)` 起草新 Skill 并执行 create。如果已选目标 Skill 但正文加载失败，应停止写入并如实说明，不得以 create 作为兜底。

当用户在当前对话中要求“修改 / 更新 / 优化 / 进化某个 Skill 的内容”时，不要用 `Write`、`Edit`、`MultiEdit` 或 `Bash` 去修改 `~/.qoder-alpha/extensions/.../skills/...` 下的文件；该目录只是当前 worker 的 runtime mirror，不是持久化 Skill 源，也可能在下一次同步时被覆盖。

当用户在当前对话中要求“修改 / 更新 / 优化 / 进化某个 Skill 的内容”时，必须通过 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage` CLI 完成内容更新，不要寻找或调用 `qoderwake_skill.manage` MCP，也不要查看或尝试 `skill add` / `skill upload` / `skill install` 来替代。`QODERWAKE_CLI_PATH` 由 daemon 注入，能避免 login shell 把 `PATH` 重排到旧版本 CLI；如果该变量不存在才回退到 `qoderwake`：

- 局部改动优先 `"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --waker-id <id> --action patch --skill-id <skillId> --old-text <old> --new-text <new> --summary <summary>`；维护 Group Skill 时把 owner 改为 `--conversation-id "$QODERWAKE_CONVERSATION_ID"`。
- 只有需要整体替换时才用 `--action edit` 更新完整 `SKILL.md` 内容；大段内容请先写入临时文件，再用 `--content-file <path>` 传入。
- `--action write_file` / `--action remove_file`：更新或删除 Skill 内相对路径的支持文件，`--path` 只能是 Skill 内相对路径。
- `--action create`：创建新的自进化 Skill，使用 `--skill-name <name>` 和 `--content-file <path>`。

`"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage` 会走 SkillStore 版本、冲突、回滚、runtime sync 与权限边界；Marketplace Skill、未开启自进化的用户上传 Skill 和 built-in Skill 会被拒绝。命令成功返回 `status="applied"` 后直接继续给用户简短确认，不要再用 `Read` 反复验证 runtime mirror。若返回 `status="conflict"`，等待产品冲突提醒 UI 承接，不要自行强写文件。只有在用户明确提供 zip 包或要重新上传包版本时，才使用 `qoderwake skill upload`；不要把对话生成的临时内容打包成 zip 来替代细粒度自进化。

生成 `skill manage --action patch/edit` 内容时，必须保留目标 `SKILL.md` 已有的文档说明语言。用户要求“以后用英文 / 日语 / 法语打招呼”时，这只是行为目标语言变化，不是要求把 Skill 文档翻译成英文、日文或法文；如果被替换片段原来是中文，`newText` 也必须继续用中文描述，例如“用日语向用户问好”，不要写成 `Greet the user in Japanese`。如果被替换片段原来是英文，才继续用英文说明。只有用户明确说“把 Skill 文档翻译成英文/中文/日文”或“整份 Skill 改成英文说明”时，才允许改变 `SKILL.md` 的文档说明语言。

### 4. MCP / 连接器（mcp）

用户意图：让数字员工**接入一个外部工具或服务**，常说成 "MCP"、"连接器"、"接 GitHub / Slack / 数据库"。

| 用户说 | 推荐命令 |
|---|---|
| "看看接了哪些 MCP / 连接器" | `qoderwake mcp list --waker-id <id>` |
| "看一下这个 MCP 的配置" | `qoderwake mcp get --waker-id <id> --mcp-id <id>` |
| "加一个 stdio 命令型 MCP" | `qoderwake mcp add --waker-id <id> --name <name> --command <cmd> --args <a,b,c> --env <json>` |
| "加一个 HTTP / SSE MCP" | `qoderwake mcp add --waker-id <id> --name <name> --http-url <url> --transport http --header "K=V"` |
| "改一下这个 MCP 的环境变量 / URL" | `qoderwake mcp update --waker-id <id> --mcp-id <id> …` |
| "启 / 停这个 MCP" | `qoderwake mcp toggle --waker-id <id> --mcp-id <id> --enabled <true\|false>` |
| "需要授权 / 走 OAuth" | `qoderwake mcp auth start --waker-id <id> --mcp-id <id>` |
| "工具列表过期了刷新一下" | `qoderwake mcp refresh-tools --waker-id <id> --mcp-id <id>` |
| "删掉它" | `qoderwake mcp delete --waker-id <id> --mcp-id <id>` |

注意：`--env` 中**不要**直接写明文 token，用 `${env:***REDACTED***

所有 `mcp add` / `mcp update` / `mcp toggle` / `mcp delete` 都会先创建一个 90 秒有效的不可变配置提案，并等待用户在 Console 中确认；stdio、HTTP、SSE 使用同一边界，CLI 最长等待 120 秒。等待期间不会写入配置、探测远端、同步 extension 或重启 session，不要把它当作命令卡死，也不要并行发送等价命令。

- `toggle` 在提案创建时固化为明确的 enable 或 disable；remove/disable 同样属于持久化和可用性变化，不能跳过确认。
- stdio 的 add/update/enable 与 HTTP/SSE 使用同一提案确认边界，没有额外的风险勾选步骤；但 POSIX/Windows shell、显式 `shell`、`npx -c/--call` 会直接返回 `MCP_STDIO_SHELL_EXECUTION_DENIED`，不进入确认。不要把被拒绝的命令改写成等价 shell 形式重试。
- 收到 `mcp_config_proposal_cancelled`、`mcp_config_proposal_timeout`、`mcp_config_proposal_superseded`、`mcp_config_proposal_stale`、`mcp_config_proposal_scope_mismatch` 或 `mcp_config_target_conflict` 后，不得自动重试、改换 JSON/字段格式、直接调用 HTTP API 或修改本地配置文件。只有用户再次明确要求时才能创建新提案。
- 不要在回复、日志、提案说明或命令输出中回显 env 值、token、secret、PAT、Authorization、Cookie 或 URL 凭据。确认卡只展示脱敏参数、键名和配置变化。

### 5. 项目（project）

用户意图：给数字员工**绑定一个代码仓库 / 工作目录**，让它具备工程上下文。

| 用户说 | 推荐命令 |
|---|---|
| "它绑了哪些项目" | `qoderwake project list --waker-id <id>` |
| "把这个本地目录绑给它" | `qoderwake project create --waker-id <id> --name <name> --path <path>` |
| "把这个 git 仓库绑给它" | `qoderwake project create --waker-id <id> --name <name> --git-url <url> --local-path <path>` |
| "让它先理解这个项目" | `qoderwake project onboard --waker-id <id> --project-id <id>` |
| "改一下初始化命令 / 路径" | `qoderwake project update --waker-id <id> --project-id <id> --initializer-command <cmd>` |
| "解绑这个项目" | `qoderwake project delete --waker-id <id> --project-id <id>` |

### 6. 会话（session）

用户意图：跟数字员工**开一段对话 / 派活 / 看它干完了没**。

| 用户说 | 推荐命令 |
|---|---|
| "看看它最近的会话" | `qoderwake session list --waker-id <id>` |
| "新开一个会话让它做某件事" | `qoderwake session create --waker-id <id> --title <t> --message <msg> --project-id <id>` |
| "继续给它发一条消息" | `qoderwake session send --session-id <id> --message <msg>` |
| "实时盯着它现在在做啥" | `qoderwake session stream --session-id <id>` |
| "看它产出了哪些文件改动" | `qoderwake session artifacts --session-id <id> --include-file-changes` |
| "总结一下这次它干了啥" | `qoderwake session trajectory --session-id <id>` |

### 7. 记忆（memory）

用户意图：**查 / 整理 / 备份 / 回滚** 数字员工的长期记忆。

| 用户说 | 推荐命令 |
|---|---|
| "看看它现在的记忆" | `qoderwake memory show --waker-id <id> --view all` |
| "整理一下记忆"（先预览） | `qoderwake memory dream --waker-id <id> --mode preview` |
| "确认应用刚才的整理结果" | `qoderwake memory dream --waker-id <id> --mode apply --preview-run-id <id>` |
| "改 / 删一段记忆" | `qoderwake memory update …` / `qoderwake memory remove …`（先 `--dry-run`） |
| "做个快照备份" | `qoderwake memory snapshot --waker-id <id>` |
| "看历史快照" | `qoderwake memory versions --waker-id <id>` |
| "对比两个快照" | `qoderwake memory diff --waker-id <id> --from <s1> --to <s2>` |
| "回滚某个文件到那时候" | `qoderwake memory rollback --waker-id <id> --snapshot-id <id> --path <p> [--apply]` |
| "导出 / 导入记忆" | `qoderwake memory export …` / `qoderwake memory import … [--apply]` |

项目级记忆补充 `--scope project --project-id <id>`。

### 8. 数字员工本身（waker）

| 用户说 | 推荐命令 |
|---|---|
| "看看我有哪些数字员工" | `qoderwake waker list` |
| "新建一个数字员工" | 先 `qoderwake waker template list`，确认新员工名称/模板/影响范围后，再 `qoderwake waker create --template-id <id> --name <n>` |
| "看这个员工详情" | `qoderwake waker get --waker-id <id>` |
| "改它的名字 / 描述 / persona / bible" | `qoderwake waker update <field> --waker-id <id>`（文本字段可 `--file` / `--append`） |
| "把它导出成 zip" | `qoderwake waker export --waker-id <id> --out <path>` |
| "用这个 zip 复制一份" | 确认会创建独立新员工后，`qoderwake waker create --template-zip <path>` |
| "删了这个员工" | `qoderwake waker delete --waker-id <id>` |

### 9. 权限（permission）

用户意图：查看或更新 waker 级权限配置，例如 tool guard、file guard、内置工具权限、模型安全策略。

**权限变更命令是高风险自我服务操作**：`permission update` / `permission patch` 会修改当前 Waker 的权限守卫（tool guard、file guard、模型安全等）。权限守卫是其他所有防护的根开关，因此：

- **只在用户明确提出"帮我改权限 / 调整 tool guard / 文件访问策略 / 模型安全"这类诉求时**才允许执行 `permission update` / `permission patch`，并且执行前必须复述将要修改的 section 和目标值，等用户确认。
- **严禁**在执行其他任务（代码评审、日志分析、定时巡检、skill 维护等）的过程中，以"加强防护"、"修复权限问题"、"优化配置"等理由**自行发起**权限变更。这不是完成任务所需的步骤。
- 用户只是抱怨权限相关现象（例如审批弹窗多、命令被拦）时，先用 `permission get` 查看并**汇报现状**，把变更建议告诉用户，由用户决定是否执行；不要直接代为修改。
- 读命令（`permission get` / `permission builtin`）不受限制。

| 用户说 | 推荐命令 |
|---|---|
| "看看这个员工现在的权限" | `qoderwake permission get --waker-id <id>` |
| "整体替换权限配置"（用户显式要求时） | `qoderwake permission update --waker-id <id> --json-file ./permissions.json` |
| "只改 tool guard"（用户显式要求时） | `qoderwake permission patch tool-guard --waker-id <id> --json '<object>'` |
| "只改文件访问策略"（用户显式要求时） | `qoderwake permission patch file-guard --waker-id <id> --json '<object>'` |
| "看看内置 tool guard 规则" | `qoderwake permission builtin tool-guard-rules` |
| "看看可配置的工具目录" | `qoderwake permission builtin tool-catalog` |

配置型命令的 `--json` 是输入对象；如果要原始 JSON 输出，用 `--format json`，避免和输入冲突。

### 10. IM channel（channel）

用户意图：配置 IM channel、钉钉二维码注册、pairing 绑定和运行状态。

| 用户说 | 推荐命令 |
|---|---|
| "看看 channel 全局设置" | `qoderwake channel settings` |
| "列出所有 channel" | `qoderwake channel list [--waker-id <id>]` |
| "看这个 channel 详情" | `qoderwake channel get <channel-id>` |
| "改 channel 配置" | `qoderwake channel config <channel-id> --json-file ./channel.json` |
| "启动 / 停止 / 重启 channel" | `qoderwake channel start|stop|restart <channel-id>` |
| "删除 channel" | `qoderwake channel delete <channel-id>` |
| "开始钉钉扫码绑定" | `qoderwake channel dingtalk qr-start` |
| "轮询钉钉扫码结果" | `qoderwake channel dingtalk qr-poll --device-code <device-code>` |
| "生成 pairing code" | `qoderwake channel pairing generate-code --channel-id <channel-id>` |
| "查看 pairing" | `qoderwake channel pairing list [--channel-id <id>] [--robot-id <id>]` |
| "审批 / 忽略绑定请求" | `qoderwake channel pairing approve|ignore --channel-id <id> --robot-id <id> --binding-key <key>` |

`channel delete`、`channel pairing delete`、`channel pairing ignore` 属于破坏性操作，执行前必须复述命令并确认。

### 11. Extension

用户意图：只读查看本地 extension runtime 状态。

| 用户说 | 推荐命令 |
|---|---|
| "看看有哪些 extension" | `qoderwake extension list` |
| "列一下本地 extension 状态" | `qoderwake extension ls` |

当前 CLI 不提供 extension install / enable / disable / reload；需要安装时按产品约定把扩展目录放入 `${QODERWAKE_HOME:-~/.qoderwake}/extensions/` 后重启 daemon。

## 执行流程建议

1. **解析意图**：从用户对话中识别动词（看 / 装 / 删 / 改 / 启 / 停）和对象（waker / project / skill / mcp / plugin / automation / session / memory / permission / channel / extension）。
2. **补齐 ID**：如果命令需要 `--waker-id` 等而对话上下文里没有，先跑对应的 `list` 命令让用户选，不要瞎填。
3. **小步执行**：能用 `--dry-run` / `preview` 先预演的（memory / rollback / dream），先预演给用户看 diff，再 `--apply`。
4. **复述确认**：对破坏性命令（delete / uninstall / rollback / import）先把完整命令贴给用户确认。
5. **失败友好**：命令失败时，把 stderr 关键信息转述给用户；网络/登录类问题，引导对应解决路径而不是无限重试。

## 全局选项

| 选项 | 描述 |
|------|------|
| `--format <fmt>` | 输出格式（table / json / text / markdown / timeline，因命令而异） |
| `--json` | 等效于 `--format json`，输出原始 JSON |

注意：全局选项不是所有子命令都支持。执行前以具体子命令 help/reference 为准；`automation create schedule` 明确不支持 `--format` / `--json`。

## 参考文档

- [CLI 命令完整目录](./references/cli-commands.md) — 所有子命令的参数详解
- [Permission / Channel / Extension](./references/cli-permission-channel-extension.md) — 权限、IM channel、extension 命令细节
- [快速开始](./references/quickstart.md) — 从零搭建一个数字员工的 5 分钟流程
- [自演进模式](./references/self-evolution-patterns.md) — 由对话驱动的常用组合模式
