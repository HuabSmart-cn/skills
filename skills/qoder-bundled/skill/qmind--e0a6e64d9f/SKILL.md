---
name: qmind
description: 在 QMind 知识库里检索证据、浏览 Notebook 与 Source，或把文本、HTTPS 链接、本地文件加入知识库。当用户提到 QMind、知识库检索、Notebook、知识源导入时使用。
---

# QMind 知识库

`qoder-qmind` MCP Server 暴露 QMind Agent Contract v3 的七个工具，工具名在会话里是
`plugin:qoder-qmind:qoder-qmind` 命名空间下的 `search`、`retrieve`、`list_notebooks`、
`list_sources`、`get_source`、`read_source`、`add_source`。

## 使用顺序

1. 不确定范围时先 `list_notebooks`，它返回当前 QMind 账号可见的 Notebook。
2. 跨 Notebook 找证据用 `search`；要在**一个** Notebook 里做 chunk 级检索（拿到带 score 的
   原文片段、按 `sourceIds` 限定范围、或用 `topK`/`scoreThreshold`/`maxResults` 调参）用
   `retrieve`；要看某个 Notebook 的内容清单用 `list_sources`。
3. `get_source` 读元数据与状态，`read_source` 读正文切片。Source 状态是 `pending` 或
   `processing` 时正文还没准备好，不要重试到超时，如实告知用户当前状态。
4. `add_source` 支持文本、HTTPS URL 与本地文件三种形态。本地文件使用用户提供或明确确认的
   路径；只要 MCP 进程可读，就交给 QMind 接口处理。路径不存在或不可读时返回 `invalid_input`，
   格式、大小、配额与账号权限以 QMind Client/API 响应为准。

## 边界

- 工具参数里不指定 Notebook 时，只会使用配置里的默认 Notebook；没有默认值时返回
  `selection_required`，此时应向用户确认要用哪个 Notebook，而不是自己挑一个。
- `unauthenticated` 表示 QMind 登录态缺失，`permission_denied` 表示当前账号没有接口要求的权限；
  这两种都不是原样重试能解决的问题，应把处置方式告诉用户。
- 工具结果本身就是有界的：列表分页、正文按切片返回。不要为了凑完整内容反复翻页。
