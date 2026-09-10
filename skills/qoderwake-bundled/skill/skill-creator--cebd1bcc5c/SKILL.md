---
name: skill-creator
description: "Guide for creating or updating skills for the current QoderWake waker/数字员工 or Group Conversation. Use when the user asks to 创建/新建/更新 a skill, Group Skill/群 Skill, teach a capability, or author SKILL.md content. The final skill MUST be persisted via `qoderwake skill manage` into the selected QoderWake SkillStore — never into the qodercli user-level skills directory."
---

# Skill Creator（QoderWake 数字员工版）

在 QoderWake 数字员工（waker）会话或 Conversation Run 中创建或更新技能时，使用本指引。

## 落点约束（最高优先级）

- 先确定技能归属，两个 owner 参数必须二选一：
  - 普通 Waker Skill 创建到**当前 waker 的 SkillStore**：`"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --waker-id <id> --action create --skill-name <name> --content-file <path> --summary <summary>`。
  - Conversation Run 中用户明确要求 Group Skill / 群 Skill 时，创建到**当前 Conversation 的 SkillStore**：`"${QODERWAKE_CLI_PATH:-qoderwake}" skill manage --conversation-id "$QODERWAKE_CONVERSATION_ID" --action create --skill-name <name> --content-file <path> --summary <summary>`；禁止改用执行 Waker 的 `--waker-id`。
- **禁止**把 `SKILL.md` 写入 qodercli 用户级技能目录（如 `~/.qoder/skills/`）当作创建结果——该目录不属于任何 waker：Console 技能列表不展示、不参与版本管理与 runtime 同步，创建后 waker 无法作为自身技能使用，还会泄漏到同机其他 waker 的会话。权限系统也会拦截对该目录的写入。
- 可以把当前工作区的临时目录当作**草稿**位置（先在临时文件里打磨 `SKILL.md` 内容），但最终创建必须走上面的 `skill manage --action create`；创建成功后删除草稿文件。
- Waker Skill 的 wakerId 取当前会话绑定的 wakerId（见"数字员工身份初始化"段落）或环境变量 `QODER_AGENT_ID`；Group Skill 的 conversationId 只取 `QODERWAKE_CONVERSATION_ID`。
- 创建成功后简短确认即可；该命令会完成版本化、Console 可见性与 runtime 同步，不要再用 `Read` 反复验证镜像文件。
- 如果 `skill manage` 返回未登录、daemon 未运行或 frontend access login 类错误：**停下来如实告诉用户**（例如"当前 daemon 需要完成访问登录后才能创建技能"），不要尝试自行修复认证、伪造会话、重启 daemon 或改用 HTTP API 绕过。

## 前台会话的更新/创建决策（必须）

- 用户明确要求"创建/新建一个 Skill"时才直接进入创建流程。"记到你的 Skill 里"、"以后按这个规则"、"把这次反馈沉淀下来"等表达属于 **update-or-create**，不是 create。
- 未明确要求新建时，起草前必须先确认已经枚举当前 owner 的可自进化 Skill，并根据 name/description、本轮实际加载或使用记录和紧邻对话上下文选择承载者。
- 如果用户是在纠正某个已有 Skill 刚刚产出的结果，且该 Skill 可自进化，必须通过 `Skill(<target-skill-name>)` 加载其完整正文，保留无关规则并把纠正规则融入语义匹配章节，然后用 `skill manage --action patch/edit` 更新。禁止把同一条规则泛化后创建职责重叠的新 Skill。
- 只有确认不存在语义匹配的可自进化 Skill 时，才允许创建。已选定目标但正文无法安全加载时必须停止写入，不得以 create 作为兜底，也不得直接读取或修改 runtime mirror。

## 后台 Skill Review 起草模式

仅当调用方明确说明当前任务是**后台 Skill Review**，并且隔离运行时只开放 `Skill` 工具时，使用本模式：

- 必须依据调用方提供的所需语言、用户核心目标、实际执行轨迹和最终完成结果起草 Skill；信息不足或不具备复用价值时返回调用方约定的 `action=none`，不得编造。
- 创建场景必须返回完整的新 `SKILL.md`；更新场景必须通过 `Skill` 工具加载本次 Review 选择的已有 Skill，保留 frontmatter `name` 和与本轮经验无关的既有规则，把新增或修正规则融合到语义匹配章节，并返回更新后的完整 `SKILL.md`。不得只返回追加片段或更新说明。
- 不读写草稿文件，不执行 `qoderwake skill manage`，不调用 Bash/MCP；严格按调用方给出的结构化输出契约返回最终草案。
- daemon 会在校验草案后负责最终持久化。本模式只复用 Waker `skill-creator` 的内容生成能力，不是本地模板或另一套 Skill 存储渠道，也不改变普通用户会话必须经 `skill manage` 受管链路落库的规则。

## 内容质量要求

- `SKILL.md` 必须包含 YAML frontmatter：`name`（小写字母/数字/连字符，与 `--skill-name` 一致）和 `description`（说明技能做什么、何时触发，包含具体场景关键词）。
- 内容要教给模型"它没有的知识"：具体工作流、团队规范、领域知识、脚本用法；不要写模型本来就会的常识。
- 保持精简：上下文窗口是公共资源，只写必要内容；长流程用编号步骤，易错点用低自由度精确指令。
- 需要脚本 / 参考文档 / 模板等支持文件时，创建技能后按用户需要再补充。

## 流程

1. 从对话中提炼技能用途、触发场景与关键知识；信息不足时先向用户澄清。
2. 判断是更新还是创建。未明确要求新建时先比对可自进化 Skill；命中候选则加载其完整正文并进入更新，确认无匹配候选才进入创建。
3. 在当前工作区的临时目录起草完整 `SKILL.md`（含合规 frontmatter）；更新时保留目标 Skill 的 `name` 和无关规则。
4. 更新时执行 `skill manage --action patch/edit`；创建时执行 `skill manage --action create`。
5. 删除草稿文件，向用户简短确认技能名称与用途。
