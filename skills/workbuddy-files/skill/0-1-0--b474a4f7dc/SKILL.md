---
name: recommend-experts
description: |
  当任务需要专业判断、深度研究、专业角色或多角色协作，且当前会话尚未选择 Expert 时，搜索并用内联卡片推荐真实专家或专家团。
allowed-tools: search_plugins suggest_plugin_install
license: Internal
disable: false
---

# Recommend Experts

只在专业角色或多角色工作流会明显提升当前任务质量，且当前会话没有 Expert 时使用。

## Workflow

1. 先确认当前会话未选择 Expert；已有 Expert 时立即停止，不得搜索、推荐或替换。
2. 调用 `search_plugins`，`type` 必须是 `expert`；把用户请求放进 `userIntent`，必要时补充 `keywords`。
3. 根据精选场景和候选描述匹配当前任务。候选可能是单专家 `expert`，也可能是专家团 `expert_team`，二者合计最多选择 3 个。
4. `pluginId` 必须逐字来自本次 `search_plugins` 返回结果。
5. 调用一次 `suggest_plugin_install` 渲染 Expert 卡片：

```json
{
  "type": "expert",
  "contextLabel": "用于这次深度研究",
  "plugins": [
    { "pluginId": "DeepResearchExpert" },
    { "pluginId": "GPTResearcherTeam" }
  ]
}
```

## Rules

- 用户只能启用一个专家或专家团；不得静默启用、替换当前 Expert。
- 不得用文字列表代替 `suggest_plugin_install` 卡片。
- 搜索返回 `expertAlreadySelected: true` 时立即继续原任务，不得再次推荐。
- 搜索无相关结果时静默继续原任务。
- 用户跳过、超时或取消后，同一轮不得重复推荐相同候选。
- 不得使用网页搜索寻找 Plugin；`search_plugins` 是候选的唯一来源。
