# 控制角色 / 人物画面占比

当需要重新约束 IP 角色或人物尺寸时使用。风格文件已写好较好 prompt 时直接照抄。

## 无效约束（不要用）

| 手段 | 为什么无效 |
|---|---|
| 百分比约束 `"mascot occupies 55% of canvas height"` | 模型忽略，角色仍填满 |
| 像素坐标 `"top at y=280, bottom at y=770"` | ImageGen 输出尺寸桶固定，坐标对不上 |
| Bounding box / zone / frame 语言 | 模型会把 box 渲染成可见矩形容器 |
| 威胁语气 `"IMAGE FAILS IF ..."` | 无效 |

## 唯一有效方式：摄影语言

用相机 / 拍摄距离 / 场景比喻，让模型进入正确构图范式：

- `"Camera pulled FAR back / shot from 3 meters away with a wide-angle lens"`
- `"A small toy figurine on a large empty backdrop"`
- `"The figurine appears SMALL in the frame with enormous empty backdrop above the ears, below the pedestal, and across most of the left side"`

⛔ 不要在同一段 prompt 里混合摄影语言 + 像素/百分比/box 约束——后者会覆盖前者。

## Ardot 端后处理（角色仍略大时）

- 裁切只能重新取景，不能缩小人物；不得用裁切掩盖人物过大或截头
- 人物明显过大时，按渲染流程允许的次数重生，并改用更远的摄影语言
- 人物大小合格时才可保持原比例、移动底图并用 `clipsContent: true` 裁边；绝不拉伸
