# 风格规则语义

按标题和内容判断用途，不依赖章节字母、顺序或 T 编号。

| 语义角色 | 识别与用途 |
|---|---|
| `canvas` | 画布尺寸、背景色和 ImageGen size |
| `imagePrompt` | Image/ImageGen Prompt；用于生图，可能已包含人物 |
| `personSpec` | Person/Mascot/IP Reference；人物外貌、姿势、位置和光线，可选 |
| `textLayout` | Text Layout；含 Purpose/Content 及坐标、字号、颜色等排版字段 |
| `layoutNotes` | Layout Notes/Self-Drawn UI Layers/Layer Order；画布前景容器和层级 |
| `vectorAssets` | Icon/Decorative SVG/Brand Assets；可编辑矢量素材 |

`imagePrompt` 和可解析的 `textLayout` 是完整风格规则的最低要求。缺少时不得按完整风格执行；目录匹配流程应进入兜底。

## 人物归一化

人物描述可能位于 `imagePrompt` 或独立 `personSpec`，处理时覆盖两处：

- 用户照片：删除虚拟人物的身份、外貌和衣物，改为对应 image #N；保留姿势、位置、表情和光线
- AI 生成人物：删除全部 image 引用，补充中性外貌与服装；保留姿势、位置和光线
- 不放人物：删除全部人物、Mascot、IP 描述，并追加 `No people, no persons, no human figures.`

## 画布归一化

- 覆盖尺寸时同步删除 `imagePrompt` 中原比例、方向、人物位置和冲突景别，改写为目标构图
- `abs(目标宽高比 / 原宽高比 - 1) ≤ 0.3`：`x/width` 按宽度缩放，`y/height` 按高度缩放，字号按较小缩放比调整
- 方向翻转或宽高比差超过 30%：原 `textLayout` 只保留语义，坐标交给 [dsl-md-format.md](dsl-md-format.md) 重排；`layoutNotes` / `vectorAssets` 同样按新 Zone 重定位
- `textLayout`：遍历所有行，按 Purpose/Content 语义填入用户文案；ID 只用于标识节点
- `layoutNotes`：只有带明确坐标且标记 `selfDrawn` / `on-canvas overlay` 的前景容器才执行；普通说明只作理解
- `vectorAssets`：只有明确要求画布叠加且提供有效素材与位置时执行；模板尺寸优先
- 背景图形、材质和氛围始终由 `imagePrompt` 生图，不在画布重复绘制
