# Capability Registry v1（迁移中的控制面）

## 目的与边界

`skills/` 是原始公开资产快照，保持原路径和原内容；`manifest.json` 是现有站点的兼容目录。它们都不等于一个安装器或执行 Runtime。

`registry/` 是 HuabSmart 维护的机器可读控制面。它解决“资产是什么、需要什么、可否组合、风险何在、是否被真实验证过”，但**不会**仅凭文件存在就声称一个 Skill 已安装、已调用或可运行。

## 目录与唯一事实源

```text
registry/
├── index.json                         # 轻量发现索引；可按未来需要分片
├── schemas/                           # Schema 契约
└── capabilities/<capability-id>.json  # 单条结构化详情，唯一的出边事实源
```

每个 capability 有稳定、全小写的 `cap.<kind>.<namespace>.<name>.vN` ID。展示名、目录名、旧 `manifest.id`、`agentName` 都只能是元数据或别名，不能充当依赖引用。

依赖只写在被依赖者之外的 `dependencies.required` / `dependencies.optional`。反向 `dependents`、组合推荐和 Capability Graph 必须由构建器生成，禁止人工双写。

## 状态、运行时与验证不是一回事

| 层 | 能回答什么 | 不能据此推断什么 |
| --- | --- | --- |
| 收录 | 仓库中有此资产与入口 | 已安装、已执行 |
| 声明 | 需要的 Runtime、工具、服务、权限 | 当前环境真的具备它们 |
| 可用状态 | 静态依赖和声明是否完整 | 外部 API 成功、数据真实 |
| 验证 | 是否有带时间和环境的真实 receipt | receipt 之外的环境也可运行 |

合法状态为 `available`、`incomplete`、`dependency_missing`、`runtime_unsupported`、`deprecated`、`unverified`、`archived`。历史资产默认 `unverified`；只有 Runtime 实际探测并留下 receipt 后，才允许 `verification.status: verified`。普通 CI 不持有密钥，不可以把外部 API 或宿主兼容性推断为已验证。

## 依赖、错误与禁止模拟

- `required` 缺失：阻断执行，返回 `dependency_missing` / `DEPENDENCY_REQUIRED_MISSING`。
- `optional` 缺失：可有限降级，但结果必须列出被跳过的能力，不能伪称完整执行。
- `must_execute`：搜索、数据库、API、创建、更新、删除、发布等必须产生真实调用 evidence；失败返回 `execution_failed`、`authorization_denied` 或 `runtime_unsupported`，绝不能生成“已成功”的模拟结果。
- `no_fallback`：不可用时停止并报告机器可读错误。
- `llm_fallback_allowed`：只可用于元数据明确允许、且不冒充外部事实的纯推理/文本类能力。结果需要标明 `derived_without_tool`。

每个组合 Runtime 都应把实际子调用作为 receipt 返回；“Prompt 里写自动调用”只是声明，不构成调用证明。

## 最小详情模型

`capabilities/*.json` 要包含：身份与别名、原始资产入口、来源和 License 状态、required/optional 依赖、Runtime（宿主/工具/环境变量名/外部服务）、权限与风险、输入输出契约、失败策略、生命周期、验证收据。

环境变量只记录名称、是否必需、是否秘密；禁止写入值。许可不明必须显式 `unknown` 或 `unverified`，不得留空或猜测 SPDX。原始文件与 HuabSmart 添加的结构化字段通过 `artifact.contentLayer`、`origin.metadataAuthority` 分开。

## CI 与迁移

运行：

```bash
python3 tools/validate_registry.py --legacy-entry-severity error --json
python3 -m unittest discover -s tests
```

校验器使用 Python 标准库，且不执行第三方 Skill。它检查 legacy manifest 的 ID/分类/平台/入口路径，以及新 Registry 的 canonical ID、别名冲突、入口、依赖存在性、required 环、权限与失败策略、Runtime 形状和 verified receipt。

历史 `manifest.json` 中已移除 6 条“索引存在但入口不存在”的公开资产。CI 现在以 error 阻断任何新的缺失入口；若未来需要保留仅元数据资产，必须建立单独的 `withheld` 资产模型，不能伪造一个可下载入口。

迁移不能从自然语言自动推断依赖、兼容性、权限或真实可运行性。第一阶段只无损转写现有可证实字段，未知值写为 `unknown` / `unverified`；第二阶段从高风险、外部服务和组合能力开始人工补录并增加受保护的真实 probe。未来可从 `registry/` 生成分片搜索索引、关系图和兼容的 `manifest.json`，不再让单个 14MB 文件承担完整 Registry 职责。

## 跨包调用与下载包 sidecar

原始 Skill 可能在正文中写“调用某个 Skill”，但被点名的 Skill 是另一个独立资产包。不能把这类自然语言承诺当成已安装或已调用。

`python3 tools/build_dependency_candidates.py` 会扫描明确的 `Call the Skill tool with ...`、`自动调用` 等调用句式，生成 `registry/dependency-candidates.json`。其记录只有三种状态：

- `resolved_candidate`：文本名只匹配到一个现有资产；仍是候选，不会自动升级成 required。
- `ambiguous`：存在多个候选；安装端必须按 Runtime/来源/用户策略选择，不能静默挑一个。
- `unresolved`：仓库没有对应资产；安装端必须报告 `dependency_missing`，不能模拟调用成功。

下载服务可调用：

```bash
python3 tools/build_download_bundle.py --asset-id <manifest asset id> --output ./asset.zip
```

它会复制原始资产目录并附带 `HBS_BUNDLE.json` 与 `README_HUABSMART.md`。sidecar 包含精确资产 ID、源码 revision、受信任 GitHub 搜索目录地址和上述文本候选；README 提供相同的协同 Skill 检索规则。原始 `SKILL.md` / `AGENT.md` 完全不改。`HBS_BUNDLE.json` 替代旧的泛称 `MANIFEST.json`，避免它与仓库 catalog 混淆。网站前端源码不在此仓库，下载按钮需要在其后端或构建步骤接入这条命令。

安装端可先生成零副作用计划：

```bash
python3 tools/resolve_bundle_dependencies.py \
  --bundle ./asset.zip \
  --repository-root /path/to/trusted/skills-clone
```

它只从指定的受信任 Registry 解析，不做网页搜索或文件写入。Registry 明确声明的 required/optional 依赖会生成安装动作；从原文抽出的唯一候选默认仍需显式 `--allow-resolved-textual-candidates`，多候选和未解析候选会阻断并返回机器可读错误。真正写入不同 Agent Runtime 的安装器应消费这个 plan，而不是重复自己的模糊匹配逻辑。
