# 风格目录静默匹配工作流

整体流程：**收集缺失素材 → 获取轻量风格列表 → 静默匹配并校验 → 获取完整风格规则或进入兜底 → 合成 prompt → 渲染与交付**。

## 1. 收集缺失素材

只询问用户尚未提供、且无法从上下文可靠推断的信息。把**仍缺失**的项合并到**一次** `AskUserQuestion`（多题并列，每题独立选项列表）。

⛔ **本步必须在 `create_design` / ImageGen / 画布排版之前完成**。

### 必问字段与选项（字面量不可改）

| 字段 | 何时跳过 | 选项（必须原样出现） |
|------|----------|----------------------|
| 人物照片 | 当前轮已上传人物照，或用户明确「用这张当讲师/嘉宾照片」 | `我稍后上传` / `没有，用 AI 生成人物` / `没有，海报不放人物` |
| 品牌 Logo | 已上传 Logo，或用户明确不要 Logo | `我稍后上传` / `不需要 Logo` |
| 文案 | 用户给出完整可直接使用的文案 | `我稍后提供完整文案（一字不改直接用）` / `我提供关键信息、其余 AI 补` / `全部由 AI 创意生成` |
| 海报比例 | 用户已指定比例（如「竖版 9:16」） | `小红书配图 1080×1440 3:4` / `微信公众号首图 900×383 2.35:1` / `视频号/抖音封面 1080×1920 9:16` / `B站视频封面 1920×1080 16:9` / `微信公众号次条 200×200 1:1` / `自定义尺寸` |

本工作流**不询问视觉风格**：

- 用户已有风格文字时，把它作为 `$styleHint`
- 用户无风格偏好时，令 `$styleHint` 为空，只按直播主题和文案匹配

已明确提供的字段不得重复询问。选项使用自然语言，禁止向用户暴露 `.md`、文件路径、目录、脚本或工具语法。

### 标准问法示例（人物 + Logo 分两题）

```
AskUserQuestion({
  questions: [
    {
      header: "人物照片",
      question: "海报中的人物形象如何处理？",
      options: [
        { label: "我稍后上传", description: "上传讲师/嘉宾肖像，通过 AI 融合进底图，保证人物一致。" },
        { label: "没有，用 AI 生成人物", description: "不上传照片，由 AI 生成中性专业人物形象。" },
        { label: "没有，海报不放人物", description: "纯背景与排版，画面中不出现人物。" }
      ]
    },
    {
      header: "品牌 Logo",
      question: "是否需要加入品牌 Logo？",
      options: [
        { label: "我稍后上传", description: "上传 Logo 文件，在画布中单独排版。" },
        { label: "不需要 Logo", description: "海报不含品牌标识。" }
      ]
    }
  ]
})
```

### 禁止的反模式

- ❌ 合并人物与 Logo 为一题，或使用「AI 生成讲师肖像」「不放讲师肖像」等自造文案
- ❌ 因 prompt 含讲师姓名就默认 AI 生成或跳过人物题
- ❌ 省略「我稍后上传」
- ❌ 把目录中的风格选项展示给用户，或要求用户选择风格来源

任何字段选到「我稍后上传」或「我稍后提供完整文案」时，必须停在当前轮等待用户补齐；不要生图或操作画布。

## 2. 静默匹配视觉风格

先把当前 `livestream-poster` 技能目录的绝对路径记为 `$skillDir`。脚本始终使用该绝对路径调用。

### 2.1 获取轻量列表

运行：

```bash
node "$skillDir/scripts/fetch-operation-styles.mjs"
```

读取脚本输出，格式为：

```json
[{"id":"...","style":"..."}]
```

- `id`：后续获取完整风格规则时使用
- `style`：用于本轮语义匹配

命令失败、输出无法解析或列表为空时，直接进入 **步骤 3B 兜底路径**。

### 2.2 语义匹配与“不强制命中”门禁

根据以下信息，在列表中静默选择**一个**最匹配项：

1. `$styleHint`（有则优先）
2. 直播主题、行业和文案语气
3. 人物数量与目标画面方向
4. 条目的 `style` 描述

选中前必须通过合适性门禁：

- 用户有明确风格要求时，候选必须在主色、氛围和构图中的至少两个核心维度一致
- 候选与用户硬要求冲突（如明亮与暗黑、单人与双人、横竖方向完全不兼容）时不得命中
- 仅共享「直播」「海报」「人物」「科技」等泛词，不算合适
- 用户无风格偏好时，可按主题和人物场景命中；如果所有候选都明显偏离主题，也不得为了使用目录而强选

没有任何合适候选时，直接进入 **步骤 3B 兜底路径**。不要向用户展示候选或追问二次选择。

### 2.3 获取所选风格规则

匹配成功后，把候选 `id` 记为 `$styleId`，运行：

```bash
node "$skillDir/scripts/fetch-operation-design.mjs" "$styleId"
```

读取脚本输出作为所选风格的完整 Markdown，并按 [../references/style-guide-semantics.md](../references/style-guide-semantics.md) 解释。命令失败、输出为空，或无法识别 `imagePrompt` / `textLayout` 时，转入 **步骤 3B 兜底路径**。

对用户只说「已选定视觉风格」，不要暴露目录、id、URL、脚本或内部文件。

## 3A. 已匹配风格：提取规则

读取完整 Markdown 或足以覆盖所有语义角色的范围，不使用固定行数或章节字母截断。提取画布、生图、人物、文字排版、前景说明和矢量素材。

按 [../references/adaptive-sizing.md](../references/adaptive-sizing.md) 的映射设置尺寸，并按 `style-guide-semantics.md` 适配排版。

## 3B. 无合适匹配：兜底路径

加载：

1. [../references/fallback-prompt-rules.md](../references/fallback-prompt-rules.md)：根据用户风格文字或直播主题生成背景 prompt
2. [../references/dsl-md-format.md](../references/dsl-md-format.md)：生图后读图定框，以 MD DSL 自适应排版

兜底时不得假装取得了完整风格规则，也不使用 `adaptive-sizing.md` 的固定坐标表。

## 4. 合成 prompt

### 4.1 已匹配风格 + 有用户人物照片

按 `style-guide-semantics.md` 的人物归一化规则处理 `imagePrompt` 和 `personSpec`：替换虚拟人物的身份、外貌和衣物，保留姿势、位置、表情与光线。

```
<归一化后的 imagePrompt + personSpec>
No frames, no borders, no windows around the people - they stand directly on the background.

No text, no letters, no numbers anywhere in the image.
```

禁止添加原文没有的视觉元素或自由发挥姿势；目标比例不兼容时允许按尺寸归一化规则重写景别。示例见 [../references/prompt-examples.md](../references/prompt-examples.md)。

### 4.2 兜底路径 + 有用户人物照片

```
<fallback-prompt-rules 生成的背景 prompt>

Person (must look exactly like the character in image #1):
- IMPORTANT: The person must be rendered in CLEAN PHOTOREALISTIC style with studio lighting, regardless of background style.
- [衣物描述，来自用户照片；看不清则 professional attire]
- [位置/姿势，按目标比例的默认构图确定]

The background style and the person's rendering style are SEPARATE. No frames or borders around the person.

No text, no letters, no numbers anywhere in the image.
```

人物照片必须作为高保真参考图参与生图。

### AI 生成人物

- 已匹配风格：删除全部 image 引用，补充中性外貌与服装，保留人物姿势、位置和光线
- 兜底路径：根据直播主题生成中性、专业的人物描述，位置服从目标比例的默认构图
- 不得擅自推断真实人物身份或敏感属性

### 不放人物

删除全部人物、Mascot 和 IP 内容，并追加：

`No people, no persons, no human figures. No text, no letters, no numbers anywhere in the image.`

## 5. 渲染与交付

Prompt 合成后加载 [../references/render-and-compose.md](../references/render-and-compose.md)，执行建文件、生图、画布排版和最终验证：

- 已匹配风格：按 `style-guide-semantics.md` 排版
- 兜底路径：用 `dsl-md-format.md` 读图定框后排版
