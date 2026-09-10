# 完整风格文件工作流

仅适用于用户引用了包含生图描述和文字排版的完整直播海报风格文件，或上下文已经提供同等完整的风格规则。

只有风格文字、视觉大类或主题不算完整风格规则；这类输入和无风格偏好都应改走 [style-matching.md](style-matching.md)，不要在本工作流内补造或搜索风格文件。

## 1. 收集缺失素材

只询问用户尚未提供、且无法从上下文可靠推断的信息。把**仍缺失**的项合并到**一次** `AskUserQuestion`（多题并列，每题独立选项列表）。

⛔ **本步必须在 `create_design` / ImageGen / 画布排版之前完成**。

### 必问字段与选项（字面量不可改）

| 字段 | 何时跳过 | 选项（必须原样出现） |
|------|----------|----------------------|
| 人物照片 | 当前轮已上传人物照，或用户明确「用这张当讲师/嘉宾照片」 | `我稍后上传` / `没有，用 AI 生成人物` / `没有，海报不放人物` |
| 品牌 Logo | 已上传 Logo，或用户明确不要 Logo | `我稍后上传` / `不需要 Logo` |
| 文案 | 用户给出完整可直接使用的文案 | `我稍后提供完整文案（一字不改直接用）` / `我提供关键信息、其余 AI 补` / `全部由 AI 创意生成` |
| 海报比例 | 用户已指定比例（如「竖版 9:16」） | `小红书配图 1080×1440 3:4` / `微信公众号首图 900×383 2.35:1` / `视频号/抖音封面 1080×1920 9:16` / `B站视频封面 1920×1080 16:9` / `微信公众号次条 200×200 1:1` / `自定义尺寸` / `沿用视觉风格原比例` |

已明确提供的字段不得重复询问。选项使用自然语言，禁止向用户暴露 `.md`、文件路径或工具语法。

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
- ❌ 省略「我稍后上传」（AskUserQuestion 无法代用户传文件，但必须保留该选项以触发等待上传流程）

任何字段选到「我稍后上传」或「我稍后提供完整文案」时，告知用户补充素材并停止当前轮；不要生图或操作画布。

## 2. 确认风格规则

使用用户明确引用的风格文件或上下文中已经给出的完整风格规则，并加载 [../references/style-guide-semantics.md](../references/style-guide-semantics.md)。至少应能识别 `imagePrompt` 和 `textLayout`；人物描述、前景说明和矢量素材按语义角色选用。

若只有名称、短风格词或不完整描述，说明路由条件不成立，应改走 `style-matching.md`；禁止无边界扫描用户磁盘，也不得假装已经取得完整风格文件。

对话中只说「已选定 XX 风格」，不暴露内部文件名或路径。

## 3. 获取风格规则

读取完整文件或足以覆盖所有语义角色的范围，不使用固定行数或章节字母截断。按 `style-guide-semantics.md` 提取画布、生图、人物、文字排版、前景说明和矢量素材。

选择「沿用视觉风格原比例」时使用 `canvas` 原尺寸；用户指定其他比例或自定义尺寸时，按 [../references/adaptive-sizing.md](../references/adaptive-sizing.md) 选择生图尺寸，并按 `style-guide-semantics.md` 适配排版。

## 4. 合成 prompt

### 有用户人物照片

按 `style-guide-semantics.md` 的人物归一化规则处理 `imagePrompt` 和 `personSpec`：替换虚拟人物的身份、外貌和衣物，保留姿势、位置、表情与光线。

```
<归一化后的 imagePrompt + personSpec>
No frames, no borders, no windows around the people - they stand directly on the background.

No text, no letters, no numbers anywhere in the image.
```

禁止添加原文没有的视觉元素或自由发挥姿势；目标比例不兼容时允许按尺寸归一化规则重写景别。示例见 [../references/prompt-examples.md](../references/prompt-examples.md)。

### AI 生成人物

- 删除全部 image 引用，补充中性外貌与服装，保留人物姿势、位置和光线；生图不带人物参考图
- 不得擅自推断真实人物身份或敏感属性

### 不放人物

删除生图描述中的全部人物、Mascot 和 IP 内容，并追加：

`No people, no persons, no human figures. No text, no letters, no numbers anywhere in the image.`

## 5. 渲染与交付

Prompt 合成后加载 [../references/render-and-compose.md](../references/render-and-compose.md)，执行建文件、生图、画布排版和最终验证。
