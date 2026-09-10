# 直播海报通用渲染与画布流程

任一工作流完成 prompt 合成后加载本文件。文件门禁、画布 schema、DSL 和验证以 `ardot-design-core` 为准。

## 1. 建文件 + 生图

⛔ **时序约束（最高优先级）**：打开画布后**第一步必须生图**，把人物照片与背景风格 prompt 融合成**一张完整底图**；**严禁把人物照片作为独立图层贴到 Ardot 背景底图上**（两种渲染风格会脱节）。生图未完成前不做任何画布排版、文字、speaker card、SVG icon 等操作。

先按 `ardot-design-core` 处理 `<ardot_file_directive>`，完成文件门禁并等待 ready context update，再调用 ImageGen。

### 生图规则

- 有人物照片：作为参考图传给 ImageGen，顺序与 prompt 中 image #1 / #2 / #3 一致，使用高保真参考
- 无人物照片：不要传参考图
- Logo 不参与生图
- 生图尺寸按当前 workflow 的比例表选择；完整风格规则已写 `ImageGen size` 且用户未改比例时，用规则中的值
- 生成服务使用有限尺寸桶，画布尺寸不代表生图会原样输出；目标与返回比例相差超过 20% 时，先重写构图 prompt，不得直接依赖 Fill 裁切
- 目标比例大于 2.0 时，prompt 必须明确超宽横幅、人物与视觉重心集中在一侧、另一侧保留连续文字安全区，且上下裁切边界不得放关键内容
- 900×383 使用 `1536x768` 的 2:1 生图桶；Fill 后会裁去约 15% 的上下区域，因此人物头部、手势和关键装饰必须位于中间 70% 安全带
- 重写后返回比例仍无法安全适配时停止，说明当前服务无法保证该极端比例

调用成功后用文件读取工具核对生成图。失败时不要靠去掉参考图或改 prompt 绕过。

## 2. 生图检查

用文件读取工具读取生成图，仅在以下严重问题出现时重生：

| 需要重生 | 可以接受 |
|----------|----------|
| 人物过大，叠字后会严重遮挡 | 人物大小合理，文字区留白充足 |
| 人物偏到文字区 | 人物在预期区域 |
| 明显白色面板、窗口或边框 | 背景干净 |

最多重生 1 次；第二次无论结果直接使用。小瑕疵不重生。重生时保持相同参考图与尺寸，只修改 prompt 的构图描述。

## 3. 搭画布

排版路径由当前 workflow 决定：

- 完整风格文件或目录成功匹配：按 `style-guide-semantics.md` 排版；其判定需要重排时转 `dsl-md-format.md`
- 用户上传风格参考图：使用 [adaptive-sizing.md](adaptive-sizing.md) 的对应方向排版
- 风格目录无合适匹配：先读取生成图，再使用 [dsl-md-format.md](dsl-md-format.md) 的 Zone 与 MD DSL 自适应排版

每次 `batch_edit` 前加载 `ardot-design-core/tool-usage/batch-edit.md`，DSL 和 schema 均以核心技能为唯一真源。

### 文案映射

遍历 `textLayout` 全部行，按 Purpose/Content 的语义映射品牌、标题、副标题、讲师、时间、地点、要点和 CTA；T 编号只标识节点，不代表固定用途。用户未提供的可选内容跳过，用户文案一字不改；溢出时调整字号、宽度或换行。

### 画布节点顺序

按 `batch_edit` 的操作上限拆批，顺序如下：

1. 顶层 Frame：无自动布局、画布尺寸、裁切溢出
2. 底图 rectangle：铺满画布（高度可略超出以便裁切）
3. `layoutNotes` 中通过语义门禁的前景容器
4. Logo、文字节点
5. `vectorAssets` 中通过语义门禁的矢量素材

字体优先中文 `Noto Sans SC`、英文 `Inter`。创建文字前用 `get_available_fonts` 确认精确 family/style，不得猜测字体样式名称。

### 图片上传

把 ImageGen 生成的本地图片、以及用户 Logo，铺到对应节点上：申请上传通道 → 上传本地文件 → 绑定为节点 fill。

- 底图和 Logo 都走这条上传链路，不要用 `batch_edit` 写 IMAGE fill 代替
- 绑定目标：底图 rectangle / Logo rectangle

### SVG icon

`vectorAssets` 明确要求画布叠加并提供有效 SVG 时，用独立 `batch_edit` 插入；仅有普通说明、占位或声明无图标时跳过。禁止 ImageGen 生 icon、Write `.svg` 文件，或把背景生图描述画成 SVG/rectangle。

插入方式见 `ardot-design-core/tool-usage/batch-edit.md`。额外约束：

- 模板明确提供的坐标和尺寸优先
- 未提供尺寸时，icon 才按承载色块的 50–60% 居中
- SVG 宽高必须等于最终 Ardot 帧宽高
- 不给 icon Frame 添加 `fills`

## 4. 验证与交付

按 `ardot-design-core` 执行最终 `capture_screenshot`，并完成以下直播海报专项检查：

- 文字是否被裁切
- 人物与文字是否重叠
- Logo 是否变形
- 水印是否确实位于裁切区外
- 900×383 的人物头部、手势和关键装饰是否被上下裁切

发现问题最多进行 2 轮集中修复。验证通过后再交付。

## 5. 错误处理

| 场景 | 处理 |
|------|------|
| ImageGen 失败 | 有人物参考图时不得静默去掉参考图再生成，告知用户无法保证人物一致性；无参考图时按相同意图重试 1 次，再失败告知用户 |
| 字体不可用 | 用 `get_available_fonts` 选择可用的中英文回退字体 |
| `Skipped unparseable line` | 按 `ardot-design-core/tool-usage/batch-edit.md` 修正 DSL |
| 底图 / Logo 上传后画布不显示 | 检查上传通道是否过期、文件是否真正传上去，不要跳过中间步骤 |
