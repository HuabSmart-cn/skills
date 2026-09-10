---
name: feishu-knowledge-writer
description: "Route article, research, tutorial, and other content requests into a Feishu Wiki or docx target with source synthesis, safe read-before-write handling, and read-back verification. Use when the user asks to write, save, or organize content in a Feishu knowledge base or Wiki document."
---

# 飞书知识库写入编排

这个 Skill 是写入前置编排层。它不替代具体写作或飞书操作 Skill，而是根据任务顺序调用 `human-writing`、`lark-wiki` 和 `lark-doc`，把“整理内容并写进指定飞书知识库”变成一条可核验的流程。

## 何时触发

用户明确提出“写进飞书知识库”“存到 Wiki”“整理到这个飞书文档”“把这批资料放进去”等请求时触发。只要求聊天草稿、总结或改稿而没有写入意图时，不执行远程写入。

以下对象不由本 Skill 直接处理正文，按类型切换到对应 Skill：

- 多维表格或 Base 记录使用 `lark-base`
- 电子表格内部数据使用 `lark-sheets`
- 幻灯片使用 `lark-slides`
- 口播模板与临时稿/正式稿路由使用 `feishu-koubo`

## 协同路由

按当前任务读取相关 Skill，不要把所有规则重复写进本 Skill。

1. 内容来自外部材料、需要汇总或洗稿时，调用 `human-writing`。先区分可核验事实、来源自述、作者判断和未知项；吸收观点与结构，不照搬原文故事、顺序和措辞，不补造用户经历。
2. 目标是 Wiki URL、Wiki 节点或知识空间时，调用 `lark-wiki` 解析真实 `space_id`、`node_token`、`obj_token` 和父子关系。
3. 目标是 docx/Wiki 文档正文时，调用 `lark-doc`。读取正文前遵循 `lark-doc-fetch`，写入前遵循 `lark-doc-xml`、`lark-doc-style`、`lark-doc-update` 和 `lark-doc-update-workflow`。
4. `lark-wiki` 或 `lark-doc` 要求认证、权限或身份处理时，先遵循 `lark-shared`。

## 本项目身份边界

在 `<LOCAL_PATH>` 内，所有飞书 CLI 使用项目 wrapper `./bin/lark-cli`，显式传 `--as user`。不要在该项目里改用全局裸命令 `lark-cli`，不要切换到其他 profile，也不要把 Bot 视角当成用户知识库的替代路径。

如果任务发生在其他项目，先检查该项目是否有自己的 wrapper、配置目录和 profile，使用其项目约定；不能静默跨项目复用身份。

执行实际操作前先检查用户身份和 token 状态。认证失败、scope 不足或目标不可访问时停止在诊断阶段，不用另一个身份绕过问题。

## 写前检查

拿到目标 URL 后，先做只读解析。

1. 用 `wiki +node-get` 取得目标节点的 `space_id`、`node_token`、`obj_token`、`obj_type`、标题、父节点和 `has_child`。
2. 对 docx/Wiki 目标用 `docs +fetch --detail full --doc-format xml` 读取当前正文，确认标题块、正文块和资源块。
3. 判断目标属于空白页、用户已有内容、模板页还是目录节点。目标是目录节点时，不要直接把正文写到目录；先定位其下的具体文档或按用户意图创建子文档。
4. 如果需要新建节点，先列出目标父节点下的子节点，检查标题重复。重复时停止并报告，不自动加后缀制造重复文档。

## 内容组织

默认写成可独立阅读的知识文章，不把源材料的标题数量直接变成正文目录。

- 先给读者一个明确问题、判断或使用场景，再组织材料。
- 事实、版本、数字、产品能力和评测结果保留时间与适用边界；没有证据的案例和亲历不写成事实。
- 叙述和分析使用连续段落，真正的对比数据用表格，命令和配置用代码块，组件保持克制。
- 普通知识文章默认使用 XML 写入。只有用户明确要求 Markdown，或目标就是原生 Markdown 文件时，才切换 Markdown 路径。
- 公开材料支撑的文章可在文末列少量关键来源。来源列表服务核验，不替代正文解释。
- 不在正文末尾追加“已写入”“验证完成”等助手状态说明。

## 写入决策

### 空白目标

目标正文只有空标题或无正文、无资源块时，用户已经明确要求写入，可以用 `docs +update --command overwrite --doc-format xml` 写入完整标题和正文。写入前先用 `--dry-run` 检查目标 document、格式和内容；写入后必须回读。

### 已有内容的目标

已有正文、图片、附件、画板、表格、引用或用户编辑痕迹时，禁止默认 `overwrite`。保留以下资源和引用块原样，不把它们改成纯文本或占位符：

`<cite>`、`<img>`、`<source>`、`<whiteboard>`、`<sheet>`、`<bitable>`、`<synced_reference>`、`<synced_source>`。

根据用户意图选择 `block_insert_after`、`block_replace`、`block_delete` 或 `append`。用户只说“写进去”但没有说明追加、替换哪个章节时，先报告当前结构并询问；不要猜测覆盖范围。

### 新建文档

需要创建新页面时，使用 `wiki +node-create` 放到明确的 `space_id` 和父节点下，再用 `docs +update --command overwrite --doc-format xml` 写入。不要先用 `docs +create` 创建孤立文档后再猜测归属。

## 回读验收

任何写操作都必须以远端回读为准，不以 CLI 的成功提示单独结论。

至少核对：

- 目标 Wiki 标题、文档标题和 canonical URL
- revision 是否更新
- 目标父节点是否正确
- 文章标题、主要章节和关键内容是否存在
- 表格、代码块、链接和资源块是否仍可读取
- 原有用户内容和资源是否被保留

如果写入结果是 `partial_success`、出现 warning 或状态不确定，先回读目标文档和节点，再决定是否继续。不要重复创建同名节点。

## 对话交付

完成后只报告真实状态，说明写入的文档标题、链接、写入方式和是否完成回读核验。明确区分“生成草稿”“追加到已有文档”“覆盖空白页”“新建文档”。不要把未验证的内容说成已入库。
