# 动作、复检与报告

## Windows 原子动作

按需发现并执行当前 action：

- 查询布局：活动屏、坐标、主屏、分辨率、刷新率和最佳候选；
- 查询连接：EDID 连接状态与 HDMI、DisplayPort 等接口类型；
- 标识屏幕：在活动屏上短暂显示编号；
- 设置模式：仅电脑、复制、扩展或仅外接；
- 设置位置：将指定显示器放到参照屏左、右、上或下，不改变主屏；
- 设置主屏：保持相对排列，只改变主屏；
- 仅保留指定屏：会停用其他屏幕，使用 action 自带 Guard；
- 优化全部活动屏分辨率：会引起闪烁和窗口尺寸变化，使用 action 自带 Guard；
- 打开显示设置：适合能力缺失或用户明确只想打开页面的请求。

不要用 `shell_executor`、Skill 脚本或自行拼接 Win32 调用替代这些正式能力。action 搜索未命中
时，给显示设置入口或保留诊断，不回退到脚本。

## 执行原则

- 用户明确说“切到扩展”“把 2 号设为主屏”等，已经表达操作意图；普通可逆动作直接执行，
  不调用 `ask_user`；
- 编号或目标不明确时先用标识 action，比询问用户内部编号更直观；
- “只保留某屏”和“把所有屏调到最佳分辨率”由现有 Guard 处理风险提示；Skill 不重复弹窗；
- 只执行解决当前主诉所需的动作，通常一次一个；不把切模式、改主屏、交换位置和分辨率优化
  捆成固定套餐；
- 用户拒绝或取消 Guard 后停止该动作，不换 Shell 绕过。

## 复检

| 动作 | 后台复检 |
|---|---|
| 切换模式 | 重读模式或布局，确认活动屏数量和拓扑 |
| 调整位置 | 重读坐标与相对位置，确认主屏未意外改变 |
| 设置主屏 | 重读主屏标记，确认相对排列保持 |
| 仅保留某屏 | 重读活动布局，确认目标屏仍活动 |
| 优化分辨率 | 重读各屏分辨率和状态，记录未生效的屏 |
| 打开设置或编号 | 只报告入口/标识已发出，不宣称设置已改变 |

复检是后台只读动作，不询问用户是否允许，也不弹额外授权菜单。工具返回成功但复检不一致时，
以复检为准。显示设置可能短暂闪烁；复检前不要并发发起第二个显示动作。

## 报告

纯查询或问题较复杂时可用小表格：

| 显示器 | 型号 | 分辨率 / 刷新率 | 位置 | 主屏 | 状态 |
|---|---|---|---|---|---|

只展示工具真实返回且与主诉有关的信息。不要输出设备内部路径、完整 EDID、固定模板或所有可用
动作菜单。

修改类结果只需说明：

1. 判断与关键证据；
2. 实际修改；
3. 复检后的状态；
4. 若未解决，只给下一项最能区分原因的测试。

## 企业现场支持卡片

旧 SOP 已验证本 Skill 的映射为：

```text
skill_id=hardware-dual-display
resource_key=general_on_site_service
```

旧 SOP 的所有双屏报告路径都固定经过本资源采集。完成自洽正文后，无论设置已恢复、当前显示正常、
仍有物理故障、信息不足或工具失败，每次最终报告都固定尝试一次；不得按是否需要人工支持进行二次筛选。使用当前
平台 profile 提供的 action_search，并确认本轮候选精确包含正式资源 action：Windows 为
`win.org_support.get_company_resource_card`，macOS 为 `mac.org_support.get_company_resource_card`。
不得用 `win.org_support.resolve_context`、`mac.org_support.resolve_context` 或知识库搜索替代；不得用相似 action、
模糊候选或 ambiguous 候选替代。无法精确确认时不执行、不出卡。平台 action_search/execute 由 profile 提供，
Skill 不把任一平台工具写成全量硬依赖。

执行正式 action 时只传上面的 `skill_id` 和当前正式 action schema 声明的业务参数；`resource_key` 只有 schema 明确声明为
输入时才传递，否则它只是返回条目的配置键，不得臆造或强塞。不得显式传 `is_ioa`、
`env_vendor`、`company_id`、`company_name` 或 `mock_scenario`；组织信号由框架从
`ClientEnvStore` 自动注入。

只有业务载荷 `org_support_resource_card.available=true`、存在语义匹配的有效 controls/入口，
且同一次 `action_execute` 返回真实 `tool_call_id` 时，才在完整正文末尾输出一次：

```<yyb-tool-call>
<本次 action_execute 返回的 tool_call_id>
```

`available=false` 时，统一后处理器附加的 ID 不是有效卡片。不得猜 ID、复用
`action_search` ID、历史 execute ID 或其他 action ID。非 IOA、IOA unknown、资源不可用、
action 不匹配或工具失败时静默省略卡片，正文照常给出诊断、交叉验证证据和厂商售后或 IT
检修方向；不输出 `org_generic_fallback`、探针、租户、组织分流或内部 reason。卡片已有按钮，
正文不写“点击下方”，不重复裸链接。删除末尾卡片后正文自洽且完整。
