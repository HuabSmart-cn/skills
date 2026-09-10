# 修复结果与企业现场支持卡片

## 结果收敛

启动 `runtime` 或 `directx` 只代表启动请求已发出，不代表修复完成。等待用户完成工具界面内的
修复并重新启动原报错程序；只有原错误不再出现才报告已解决。错误变化时按新证据重新匹配，
不得把启动成功、下载成功或结果文件生成直接写成 DLL 已恢复。

## 旧 SOP 企业卡片映射

旧 SOP 已验证本 Skill 的固定映射为：

```text
skill_id=system-dll-repair
resource_key=general_on_site_service
```

每次最终报告前固定尝试一次该资源，包括修复成功、修复失败、信息不足、未匹配、非 DLL 问题和
工具失败。先完成独立自洽的正文，再调用 `mcp_wintools_action_search`，并确认候选精确包含
`win.org_support.get_company_resource_card`。不得用 `win.org_support.resolve_context`、相似 action、
模糊候选或 ambiguous 候选替代。

精确命中后调用 `mcp_wintools_action_execute`，只传 `skill_id` 和 `resource_key`。不得显式传
`is_ioa`、`env_vendor`、`company_id`、`company_name` 或 `mock_scenario`；组织信号由框架注入。

只有业务载荷 `org_support_resource_card.available=true`、存在语义匹配的有效入口，并且同一次
`action_execute` 返回真实 `tool_call_id` 时，才在正文末尾输出一次：

```<yyb-tool-call>
<本次 action_execute 返回的 tool_call_id>
```

`available=false`、IOA=false、IOA=unknown、action 不匹配、资源不可用或工具失败时静默省略卡片。
不得猜测或复用 search ID、历史 execute ID、其他 action ID 或后处理器 ID。卡片已有按钮，正文
不写“点击下方”，不重复固定人工链接；删除最终卡片代码块后正文仍完整。
