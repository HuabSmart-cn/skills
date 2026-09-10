# Prompt 示例：人物替换与多人场景

## 单人：人物替换

**风格规则中的人物原文（虚拟人物）**：

```
The person: a cute silver metallic cat-eared robot, round head with two
pointed cat-like ears, wearing black over-ear headphones, face is a black
display showing cyan geometric eyes, sleek silver metallic body, raised
left hand making a peace sign. Half-body portrait from waist up, positioned
on the LEFT side as a medium-sized subject. Photorealistic, studio lighting.
```

**用户给了照片后合成的 prompt**：

```
The person (must look exactly like the character in image #1): wearing a
navy blue business suit with a white shirt, raised left hand making a peace
sign. A medium-sized half-body portrait from waist up, positioned on the
LEFT with balanced surrounding margins. Photorealistic, studio lighting.
```

对照：外貌整段丢弃；保留姿势、位置和渲染风格，数字占比改写为摄影语言。

---

## 多人（2 人+）

### 核心原则

- 必须使用高保真人物参考
- 严格保留人物规范中的姿势/站位描述
- 禁止添加原文中不存在的视觉元素（window / frame / border / oval shape）
- 人物直接站在背景上，无任何框/窗口/容器包裹

### Prompt 模板

```
<imagePrompt 完整原文>

<personSpec；若人物嵌在 imagePrompt 中则处理对应段落>:
- 每个人物前加 "(must look exactly like the character in image #N)"
- 衣物描述改为用户照片实际穿着
- 姿势/手势/站位/表情/渲染风格 → 保留；数字占比改写为摄影语言
- 末尾追加："No frames, no borders, no windows around the people - they stand directly on the background."

No text, no letters, no numbers anywhere in the image.
```

### 参考图

人物照片顺序与 prompt 中 image #1 / #2 / #3 对齐。

### Ardot 端取景调整

裁切不能缩小人物。人物大小合格时才可通过底图位置和 `clipsContent: true` 调整取景；明显过大时重生一次。详细规则见 [person-size-control.md](person-size-control.md)。
