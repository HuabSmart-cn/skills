thread_id: 019fee95-a389-7190-990a-9555d14efca5
updated_at: 2026-08-11T02:41:48+00:00
rollout_path: <LOCAL_PATH>
cwd: <LOCAL_PATH>

# 在飞书知识库中创建并调整 Seedance 2.0 提示词资料

Rollout context: 工作目录为 `<LOCAL_PATH>`。用户希望把 GitHub 仓库 `Emily2040/seedance-2.0` 整理成中文、适合飞书的视频提示词文档，并先确认路径；随后确认应建立可扩展的提示词目录，并在用户修改正文后要求标题后的额外换行。

## Task 1: 核对并确认知识库路径

Outcome: success

Preference signals:
- 用户要求“先告诉我确认路径没问题再写”，并进一步询问“后面还有很多类似这种各种各样提示词的话，也是放着？还是新建一个目录？” -> 类似任务应先只读核对层级，不直接写入；面对可扩展内容应主动设计独立目录而不是把资料堆在现有分类下。
- 用户同意建立“AI提示词与创作工具库”后才允许写入 -> 飞书知识库的目录和正文写入都应等待明确确认。

Key steps:
- 使用项目专用 `./bin/lark-cli`、独立 `.lark-cli` 配置和显式 `--as user`，确认目标空间为“华彬智融 知识数据库”，space_id 为 `7447214332972187650`。
- 只读递归核对后确定路径：`华彬智融 知识数据库 / 未来视界丨时代先锋领航者 / 创新科技观察室`；该分类已有 DeepSeek、Manus、豆包、Claude Code、Codex 等 AI 专栏。
- 用户接受扩展方案：在“创新科技观察室”下新建“AI提示词与创作工具库”，再把 Seedance 作为第一个子文档。

Failures and how to do differently:
- 初次创建目录因用户身份缺少 `wiki:node:create` 和 `wiki:node:read` 失败；应申请最小 scope，不要改用 bot 绕过用户知识库，也不要重复使用失效设备授权流程。
- 第一次设备码流程失效；重新发起新的授权流程后成功。未来设备授权必须使用新生成的流程，完成授权后再由 agent 执行设备码登录。

Reusable knowledge:
- 项目 wrapper `<LOCAL_PATH>` 会绑定 `feishu-hukee-knowledge` profile 和项目 `.lark-cli`；不要使用裸 `lark-cli` 或其他项目 profile。
- 目标父节点“创新科技观察室”的 node token 为 `XHovwFTViiXJ8OkBx7OcQAOGn9g`；新建目录节点为 `DXF4wJN43iwT2rkus7ncBOSzn6b`，其子文档节点为 `Q3IhwhT3liwaWekLDQ5cpRqsnXg`。

References:
- [1] `./bin/lark-cli wiki +space-list --as user --page-all --page-limit 0 --format json`：确认目标 space。
- [2] `./bin/lark-cli wiki +node-list --space-id 7447214332972187650 --parent-node-token XHovwFTViiXJ8OkBx7OcQAOGn9g --as user --page-all --page-limit 0 --format json`：确认父目录已有 AI 专栏。
- [3] 最终路径：`华彬智融 知识数据库 / 未来视界丨时代先锋领航者 / 创新科技观察室 / AI提示词与创作工具库 / Seedance 2.0：AI视频生成与提示词`。

## Task 2: 整理 GitHub 仓库并写入飞书文档

Outcome: success

Preference signals:
- 用户希望“提示词可以搬过去，文档格式可以更视频飞书的 markdown 文档” -> 类似任务应提取可复制提示词、模板和工作流，使用飞书 Markdown，并保留来源、版本和安全边界；不要机械搬运整个仓库。
- 用户后来直接修改正文，要求只调整格式而不要覆盖修改 -> 对已有用户编辑的飞书文档，应先回读当前版本，做最小定向修改，保留同步引用、callout、图片和其他资源块。

Key steps:
- 读取仓库 README、中文指南、`seedance-prompt`、中文示例、quick reference、reference workflow、首尾帧指南、sequence、continuation、api-status、LICENSE 和 CHANGELOG。
- 整理为 13 个章节，覆盖：定位、核心思路、路径选择、工作流、T2V/I2V/V2V/R2V/FLF2V/Edit/Extend、参考素材角色、中文提示词模板、首尾帧、连续剧情、检查清单、安全版权、来源与版本边界。
- 创建并写入目录页及 Seedance 子文档；回读确认目录层级、子文档层级和 13 个正文章节均正确。
- 用户编辑后，回读发现标题后没有独立空白段；尝试 `<p></p>` 和错误锚点 `page_id` 均无效。读取 XML 结构确认页面标题块 ID 是文档 token 本身，最终使用 `block_insert_after --block-id W4IzdWsw2oz6CixlcpgccZVSnXf --content '<p><br/></p>'` 成功插入一个空白换行段。
- 最终回读验证顺序为：标题 → 空白段 `<p><br/></p>` → 用户新增的 synced reference → callout → 正文；用户修改内容仍保留。

Failures and how to do differently:
- `docs +update --doc-format markdown --command overwrite --content @file` 返回 `partial_success` / “Instruction produced no document changes”，但回读显示内容实际已写入；应以回读结果而不是单独的 warning 判断最终状态。
- `docs +fetch --doc-format markdown --detail with-ids` 会提示 detail 仅支持 XML；需要 block ID 时改用 `--doc-format xml --detail full`。
- 纯 `<p></p>` 不会产生可见空段；使用 `<p><br/></p>`。插入页面标题后的正文时，`page_id` 未命中，使用文档真实标题块 ID（文档 token）成功。
- 最终一次普通沙盒回读遇到 `keychain Get failed: keychain not initialized`，通过同一 wrapper 请求提升权限后回读成功。类似情况应区分写入成功与本地 Keychain 读取失败，不要宣称未验证。

Reusable knowledge:
- GitHub 仓库是 MIT 授权的 Seedance 2.0 Agent Skill OS，不是官方客户端；README 标注 v6.7.0，提示词 Skill 元数据更新时间为 2026-08-01。
- 核心可复用原则：主体和动作先写；每个参考素材分配明确角色；一镜一个主要动作和终点；续写必须以已接受视频的真实结尾为准；删除“电影感/高级感”等空泛质量词；最终字幕和法务文案放在后期处理；涉及 IP、真人、品牌、歌曲和声音时做授权检查或安全改写。
- 用户编辑后的文档包含同步引用和 📍 callout；后续修改必须先 `docs +fetch --doc ... --doc-format xml --detail full` 检查真实 block，再做局部 block 操作，避免 overwrite 覆盖用户内容。

References:
- [1] GitHub source: `https://github.com/Emily2040/seedance-2.0`
- [2] Chinese guide: `https://github.com/Emily2040/seedance-2.0/blob/main/docs/README.zh.md`
- [3] Prompt skill: `https://github.com/Emily2040/seedance-2.0/blob/main/skills/seedance-prompt/SKILL.md`
- [4] Final document: `https://bl7rsz9526.feishu.cn/wiki/Q3IhwhT3liwaWekLDQ5cpRqsnXg`
- [5] Successful spacing command: `./bin/lark-cli docs +update --doc W4IzdWsw2oz6CixlcpgccZVSnXf --as user --doc-format xml --command block_insert_after --block-id W4IzdWsw2oz6CixlcpgccZVSnXf --content '<p><br/></p>' --format json`
- [6] Final XML evidence begins: `<title id="W4IzdWsw2oz6CixlcpgccZVSnXf">... </title><p id="..."><br/></p><synced_reference ...></synced_reference><callout ...>`。
