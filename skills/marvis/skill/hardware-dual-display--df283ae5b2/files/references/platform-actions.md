# 平台动作路由

两个平台都先调用 `action_search`，再将本轮候选交给 `action_execute`；不得复用历史 action ID。

## Windows

由 computer-agent 的 Windows profile 提供 wintools MCP。运行时先用 action_search 搜索本轮可用的显示布局、连接、模式、编号和分辨率 action，再用 action_execute 按返回 schema 执行；不要把历史 action ID 写进 Skill。

## macOS

由 computer-agent 的 macOS profile 提供 mactools MCP。使用本轮搜索到的 macOS 显示查询、设置入口和可逆布局 action；若精确坐标或拓扑写入能力不存在，打开系统显示设置并把未自动修改的边界告诉用户。不得安装 displayplacer、调用 ioreg/AppleScript 或用 Windows 命令代替。

平台 MCP 是 profile 级依赖，Skill 不声明 wintools 或 mactools 为全量硬依赖。
