---
name: livestream-poster
description: >
  生成直播宣传海报：支持完整风格文件、风格目录静默匹配和用户风格参考图三种工作流，收集人物、Logo、文案与比例后，用 ImageGen 生成底图并在 Ardot 画布完成排版。
  当用户提到「直播海报」「直播宣传图」「直播预告海报」「线上直播海报」「livestream poster」，或引用直播海报风格文件时使用。
disable-model-invocation: true
user-invocable: false
agent_created: true
---

# Livestream Poster — 直播海报生成

本技能用于生成直播宣传海报。文件创建/打开、画布 schema 和基础验证以 `ardot-design-core` 为准；本技能负责工作流选择和直播海报业务规则。

## 工作流选择

| 条件 | 加载的 workflow |
|------|-----------------|
| 用户上传设计风格图，并明确说「作为风格参考」「按这个风格」或「参考这个设计风格」 | [workflows/style-reference.md](workflows/style-reference.md) |
| 用户引用了包含生图描述和文字排版的完整直播海报风格文件，或上下文已提供同等完整的风格规则 | [workflows/style-selection.md](workflows/style-selection.md) |
| 用户只有文字风格描述、视觉大类或主题，没有提供完整风格规则；或者没有明确风格偏好 | [workflows/style-matching.md](workflows/style-matching.md) |

按表从上到下匹配，命中即停；用户明确指定参考图时优先于已有风格规则。

风格参考图工作流必须同时满足：

1. 用户上传了图片
2. 用户明确表示该图片是背景/设计风格参考，而不是人物照片

仅上传图片但未说明用途时，按人物照片处理；再根据是否已有完整风格规则选择 `style-selection` 或 `style-matching`。短风格词（如「科技蓝」「极简商务」）不是完整风格规则，必须走 `style-matching`。

**每次任务只加载一个 workflow。** 确定后按该 workflow 顺序执行，不要同时加载两个工作流。

## 全局硬规则

1. ImageGen 默认调用 1 次；仅严重构图问题允许重生 1 次
2. 有用户人物照片时必须作为 ImageGen 参考图融合进底图，不能作为独立图层贴到画布
3. 人物参考图失败时不得静默去掉参考图再生成，否则无法保证人物一致性
4. Logo 不传给 ImageGen；在 Ardot 中作为独立图层上传
5. 不改用户提供的文案；溢出时调整字号、宽度或排版
6. 对话中不暴露 `.md`、内部路径、DSL、`batch_edit` 等实现细节
7. 禁止 spawn 子 agent；遵循 `ardot-design-core` 的文件门禁和验证规则
8. 背景描述中的视觉元素均由 ImageGen 生成；Ardot 只做底图 fill、文字、Logo，以及带明确坐标且标记为 `selfDrawn` / `on-canvas overlay` 的前景容器和矢量素材
9. 海报根 Frame 同时承担底图与画布边界；所有文字、前景容器、Logo、SVG/矢量装饰必须插入其内部，不得直接放在 Page。
10. 素材收集与 `AskUserQuestion` 选项以所加载 workflow 的 Step 1 为准，不得跳过、合并或改写
