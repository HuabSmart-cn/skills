# 风格目录无合适匹配时的 Prompt 规则

> 仅供 `style-matching.md` 在目录为空、获取失败、风格规则残缺或没有语义合适候选时使用。一旦取得完整的生图描述和文字排版，本文件不参与。
>
> 背景 prompt 与人物段拼成一个完整 prompt，只通过一次 ImageGen 生成含人物与背景的底图。

## 1. 风格来源

| 用户输入 | 处理方式 |
|---|---|
| 通用风格词（科技感、极简、暗黑、活力、渐变、包豪斯等） | 直接映射为背景 prompt，不联网 |
| 特定品牌、平台或商家风格 | AI 已知其稳定视觉体系时直接概括；不确定时按 §2 联网学习 |
| 未描述任何风格，只给主题或文案 | 按主题关键词推导 |

### 无风格偏好时按主题推导

| 主题关键词 | 推导方向 |
|---|---|
| AI / 技术 / 产品发布 / 开发者 | 深色渐变 + 微光粒子，科技感 |
| 教育 / 公开课 / 分享 / 知识 | 明亮渐变或浅色调，干净专业 |
| 营销 / 电商 / 促销 | 饱和渐变 + 活力色调 |
| 设计 / 创意 / 艺术 | 柔和渐变或抽象几何，克制质感 |
| 金融 / 商务 / 企业 | 深蓝或深灰调，稳重简约 |

用户上传了明确的风格参考图时不走本文件，应在最初路由阶段选择 `style-reference.md`。

## 2. 特定品牌风格的联网学习

只有用户点名具体品牌、平台或商家，且无法凭稳定知识准确还原其视觉风格时，才执行一次联网学习：

1. 搜索「`{品牌名} 发布会海报 视觉风格`」或「`{品牌名} brand visual identity poster`」
2. 优先采用官方或权威来源，最多分析 2–3 个有效结果
3. 提取主色/辅色、背景材质、纹理和整体氛围
4. 不复制商标、受保护图形、文字或具体版式，按 §3 生成抽象化背景 prompt

通用风格词和 AI 已知的稳定品牌视觉体系不联网。搜索失败时不要重试，直接用用户文字与主题推导。

## 3. 背景 Prompt 结构

最终背景 prompt 必须包含以下结构：

```text
[色彩渐变描述], [氛围关键词] atmosphere, clean minimalist composition.

Background:
- [材质/纹理/微装饰，最多 2-3 种元素]
- ABSOLUTELY NO white panels, NO frosted glass windows, NO card shapes anywhere.

MANDATORY CONSTRAINTS:
1. Background must be CLEAN and UNCLUTTERED — no prominent 3D objects, no large foreground elements, no complex scenes competing with the person for visual attention.
2. All decorative elements must be SUBTLE: small particles, gentle gradients, thin geometric lines, soft bokeh. Never dominant.
3. The requested subject must be the CLEAR visual focal point; when there is no person, keep a strong quiet area for the later title.
4. Maximum 2-3 colors in the background palette. No rainbow gradients, no chaotic multi-color schemes.
5. Background complexity ≤ 3/10 — think premium product launch, not music festival.
6. Color tone must be UNIFORM across the canvas. The entire background should flow as one continuous tone, never patchy.

No text, no letters, no numbers, no logos, no watermarks anywhere.
```

## 4. 文字区域保护

确定人物与文字的空间分布后，在约束末尾追加：

```text
7. The [LEFT/TOP/对应方位] portion of the image where text will be placed later must remain visually quiet: no sharp color blocks, complex geometric patterns, or high-contrast edges. Use smooth gradients, uniform tones, or subtle textures only.
```

| 人物位置 | 文字区域 | prompt 中写 |
|---|---|---|
| 人物在右 | 左侧 | `left 60-65%` |
| 人物在左 | 右侧 | `right 60-65%` |
| 人物在下 | 上部 | `top 40-50%` |
| 人物在上 | 下部 | `bottom 30-40%` |

## 5. 拦截与降级

| 用户风格描述 | 风险 | 静默降级策略 |
|---|---|---|
| 城市街头、室内、海滩、森林等具体场景 | 实景抢注意力 | 改为该场景色调的虚化散焦背景，不画具体环境细节 |
| 二次元、水墨、像素、波普等非写实背景 | 污染写实人物 | 只把该风格用于背景配色、纹理和抽象装饰；人物始终写实 |
| 元素密度高 | 背景太杂 | 只取前 2 个主色和氛围词，丢弃具体元素 |
| 赛博朋克、蒸汽波等强风格 | 装饰喧宾夺主 | 改为对应色系渐变 + 极简几何微光，不画招牌等具象物 |

## 6. 出口

Prompt 合成完成后，加载 [dsl-md-format.md](dsl-md-format.md) 走「读图定框 + MD DSL」排版，不套 `adaptive-sizing.md` 的固定坐标表。
