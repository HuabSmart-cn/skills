# Humanizer 人性化优化编排

> 本文档定义 Humanizer 在创作流水线中的**编排规范**——语言判定、Skill 选择、执行约束与产物契约。
> Skill 本体实现见同目录 `SKILL.md`（英文/其他语言）与 `../humanizer-zh/SKILL.md`（中文）。
> 调用方：`src/agents/doc-writer.md`（Stage 1 创作子 Agent），在 Critic 通过后**强制**调用。

---

## 1. 定位

- **角色**：文档创作流水线中位于 Critic 之后的**表达优化环节**，去除 AI 生成痕迹、提升文字自然度。
- **触发时机**：Critic 编排产出 `PASS` 或 `DEGRADED` 决策后立即触发；`skip` 模式下仍需触发（Critic 跳过 ≠ Humanizer 跳过）。
- **不可跳过**：无论文档长度、体裁、Expert 类型，Humanizer 一律强制执行，不接受"文档已足够好"为由的省略。

---

## 2. 语言判定与 Skill 选择

```
Critic 通过的终稿
    │
    ├─ 判定文档主体语言
    │   ├─ 中文（含中英混合但以中文为主） → 加载 skills/humanizer-zh/SKILL.md
    │   └─ 其他语言（英文、日文等）       → 加载 skills/humanizer/SKILL.md
    │
    └─ 执行 Humanizer 工作流 → 产出人性化优化后的终稿
```

**语言判定规则**：

- 正文中中文字符占比 > 50% → 判定为中文
- 否则 → 判定为其他语言
- 中英双语文档（如含英文摘要的中文研报）→ 按中文处理

---

## 3. 执行约束

| 约束 | 说明 |
|------|------|
| **不可跳过** | 无论文档长度、体裁、Expert 类型，Humanizer 步骤一律强制执行 |
| **保持结构不变** | 只优化表达，不改变文档结构、章节编排、数据内容 |
| **保持 Markdown 格式** | 输入为 Markdown，输出必须仍为标准 Markdown |
| **不改变专业术语** | 行业术语、公司名称、数据指标等专有名词不做修改 |
| **不改变语义** | 核心论点、结论、数据引用的含义必须保持一致 |

---

## 4. 输入 / 输出契约

### 4.1 输入

- **来源**：Critic 编排通过后的终稿（Markdown 格式）
- **要求**：已通过 §5.2.1 Markdown 格式门禁的标准 Markdown

### 4.2 输出

- **产物**：人性化优化后的终稿（Markdown 格式）
- **去向**：作为 doc-writer §3.1 步骤 5 写入 `output/<request_id>/stage1/final_draft.md` 的最终内容
- **格式**：标准 Markdown，与输入保持相同的结构与元信息

---

## 5. 与 doc-writer 的对接点

在 `src/agents/doc-writer.md` 的 6 步强制序列中，Humanizer 位于**步骤 4.5**（Critic 之后、写入最终稿之前）：

```
步骤 1 加载 Expert
   → 步骤 2 驱动创作
   → 步骤 3 Markdown 格式门禁
   → 步骤 4 Critic 编排
   → 步骤 4.5 Humanizer 人性化优化（本文档定义）
   → 步骤 5 写入 final_draft.md
   → 步骤 6 返回 Orchestrator
```

调用方（doc-writer）职责：

1. 根据 §2 语言判定规则选择加载 `humanizer` 或 `humanizer-zh` 的 `SKILL.md`
2. 将 Critic 通过的终稿作为输入传入
3. 按 §3 执行约束驱动 Skill
4. 将产物作为最终稿写入 §4.2 指定路径

Humanizer Skill 本身职责边界：**只做表达优化**，不介入 Critic 循环、不改结构、不动数据。
