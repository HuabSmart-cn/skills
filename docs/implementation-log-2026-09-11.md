# Capability Registry 实施日志（2026-09-11）

## 本轮目标

为独立下载的 Skill/Agent 增加跨包协同调用的可检索信息，并让安装端能区分：已确认依赖、文本候选、多候选和不存在的依赖。

不改写 `skills/**` 中的原始第三方正文；所有新增信息都在 HuabSmart 控制面和下载 sidecar 中维护。

## 已完成

### Registry 与静态校验

- 新增 `registry/`，包含 index、Capability Schema、两个 Lark 结构化样例和依赖候选索引。
- 新增 `tools/validate_registry.py`：检查 legacy manifest 入口、canonical ID、别名、依赖目标、required 循环、路径、权限/失败策略冲突和验证 receipt。
- GitHub Actions 新增 Registry 校验和候选索引再生成校验。

### 跨包调用候选

- 新增 `tools/build_dependency_candidates.py`，扫描明确的 `Call the Skill tool ...`、`自动调用` 等文本形式。
- 生成 `registry/dependency-candidates.json`。本次扫描结果：128 个源资产、247 条候选；34 条 `resolved_candidate`、53 条 `ambiguous`、160 条 `unresolved`。
- 候选索引的语义固定为 `textual-candidates-only`：它不是 required/optional dependency，也不是调用证明。

### 下载与解析

- 新增 `tools/build_download_bundle.py --asset-id <id> --output <zip>`。
- 每个生成 ZIP 会在不修改原始资产的前提下附带 `HBS_BUNDLE.json`。
- 新增 `tools/resolve_bundle_dependencies.py`：读取 ZIP 或解压目录的 sidecar，结合受信任本地仓库，输出零副作用安装计划。
- Resolver 默认只为 Registry 已声明的 required/optional dependency 生成安装动作；文本唯一候选也须显式 `--allow-resolved-textual-candidates` 才会进入计划。

## 已验证行为

| 场景 | 结果 |
| --- | --- |
| `lark-calendar` → required `lark-shared` | 生成精确安装计划，`planStatus: ready_for_runtime_install`；仍未 Runtime 验证 |
| `DouyinStrategist` → `humanizer` | 多个实现候选，返回 `DEPENDENCY_AMBIGUOUS` |
| `DouyinStrategist` → `anti-distill` / `remotion-video-toolkit` | 仓库无匹配入口，返回 `DEPENDENCY_MISSING` |
| 任何上述阻断项 | 不报告“已安装”或“已调用” |

验证命令：

```bash
python3 tools/build_dependency_candidates.py
python3 tools/validate_registry.py --legacy-entry-severity error --json
python3 -m unittest discover -s tests -v
git diff --check
```

结果：5 项测试通过；Registry 静态校验 0 error、0 warning。

## 已知缺口

1. 7,137 条历史资产尚未逐条获得正式 required/optional dependency、Runtime、权限、License、版本和验证 receipt。
2. 网站下载按钮源码不在本仓库，尚未接入 `build_download_bundle.py`。
3. Resolver 只输出计划；尚未为 Codex、Claude Code、DSH、OpenClaw 或其他目标 Runtime 实现实际文件写入、刷新发现、安装回执与卸载。

## 后续顺序

1. 确定第一个要支持的 Agent Runtime。
2. 为该 Runtime 实现 plan 执行器：安装、依赖闭包、复查、receipt、失败回滚/卸载。
3. 优先人工补录高风险、跨包调用、API/MCP、写操作资产的正式依赖。
4. 处理 6 条历史缺失入口后，将 CI 的 legacy entry 校验从 warning 升级为 error。
