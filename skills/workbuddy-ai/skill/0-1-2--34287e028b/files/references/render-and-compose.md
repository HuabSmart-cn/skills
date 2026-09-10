# 直播海报通用渲染与画布流程

任一工作流完成 prompt 合成后加载本文件。文件门禁、工具调用和验证仍以 `ardot-design-core` 为准。

> ⛔⛔⛔ **第零条铁律（贯穿全文件所有步骤）**：所有 array 类型参数写成纯数组 `[...]`，绝对不能套 `{item:[...]}` 外壳。错例：`"image":{"item":["a.jpg"]}` → 正例：`"image":["a.jpg"]`。适用于 ImageGen `image`、upload_images `items`、capture_screenshot `nodeIds` 等一切 `type:"array"` 字段。

## 1. 建文件 + 生图

⛔ **时序约束（最高优先级）**：打开画布后**第一步必须调用 ImageGen 生图**，用 `image` 参数把人物照片与背景风格 prompt 融合成**一张完整底图**；**严禁把人物照片作为独立图层贴到 Ardot 背景底图上**（两种渲染风格会脱节）。ImageGen 未完成前不做任何画布排版、文字、speaker card、SVG icon 等操作。

先按 `ardot-design-core` 处理 `<ardot_file_directive>`，完成文件门禁并等待 ready context update，再调用 ImageGen。

### ImageGen 调用

```
ToolSearch({ tool_names: ["ImageGen"] })
DeferExecuteTool({
  toolName: "ImageGen",
  params: {
    prompt: "<合成后的完整 prompt>",
    image: ["<人物照片绝对路径1>", "<人物照片绝对路径2>"],
    input_fidelity: "high",
    size: "<确定的 ImageGen size>",
    quality: "high",
    output_dir: "<工作目录>/.workbuddy/generated-images"
  }
})
```

规则：

- `image` 只传人物照片，使用绝对路径，最多 3 张
- 有人物照片时必须使用 `input_fidelity: "high"`
- 无人物照片时省略 `image` 和 `input_fidelity`
- `image` 必须是**原生单层字符串数组** `["/abs/1.jpg", "/abs/2.jpg"]`：每个元素是一条纯路径字符串。以下形态都会报 `must be array`：
  - ❌ 嵌套数组 `[["/abs/1.jpg", "/abs/2.jpg"]]`（多套一层 `[]`）
  - ❌ 整体一条字符串 `"['/abs/1.jpg','/abs/2.jpg']"`（被 `JSON.stringify` 或拼引号包成字符串）
  - ❌ 单字符串合并 `["/abs/1.jpg, /abs/2.jpg"]`（两条路径挤进同一个字符串）
  - 校验器对以上形态统一报 `/image: must be array`，含义是「没收到合法字符串数组」，而非「值不存在」
- 多人照片按 prompt 中 image #1 / #2 / #3 的顺序传入

### ⛔ 不要对 `params` 做任何 JSON.stringify

```jsonc
// ❌ 错误 1：对整个 params 调了 JSON.stringify（最常见的踩法）
DeferExecuteTool({
  toolName: "ImageGen",
  params: JSON.stringify({                            // ← 这一步就把数组变成字符串了
    prompt: "...",
    image: ["/abs/photo1.jpg", "/abs/photo2.jpg"]
  })
})

// ❌ 错误 2：把数组再包一层（嵌套）
image: [["/abs/photo1.jpg", "/abs/photo2.jpg"]]      // ← 多套了 []

// ❌ 错误 3：把数组手工拼成字符串
image: "['/abs/photo1.jpg', '/abs/photo2.jpg']"      // ← 不是 JSON 数组

// ❌ 错误 4：用 bash / Python 包装后注入（heredoc / env var / cat | xargs）
"image=[\"photo1\",\"photo2\"]"                      // ← shell 解析后变成字符串

// ❌ 错误 5：把 image 写成 object，把 schema 的 items 关键字当成字段名（两种变种都会失败）
image: { "item": "/abs/photo1.jpg" }                            // 变种 A：单图——item 值是字符串
image: { "item": ["/abs/photo1.jpg", "/abs/photo2.jpg"] }        // 变种 B：多图——item 值是数组，外层还是 object
//  schema 写 "items": { "type": "string" } 表示「数组每一项必须是 string」，
//  **items 是 schema 元语言（类型约束），不是数据字段名**。
//  AI 看到错误 5 变种 A 失败时常常误以为「修复方法是把数组塞进 item 下」——
//  于是改写成变种 B，但外层那层 object 壳没拆掉，schema validator 看 type 不是 array 直接拒绝（result 返回 {}）。
//  正确修法只有一种：**拆掉外层 object 壳，直接传数组** `image: ["..."]` 或 `image: ["...", "..."]`
```

**验证手段**：调用成功时返回 `"status": "completed"` 且 `images[0].localPath` 指向一个真实 PNG；调用失败时返回 `must be array` 错误或 `"result": {}` 空对象，说明 `image` 字段被破坏。**不要在 `must be array` 错误时改 prompt / 改 size / 改 input_fidelity，这些不是问题源；问题一定在 `image` 字段的形态上**。

排查清单（按出现频率排序）：

1. **（最高频！）** `image` 是否写成 `{ "item": "..." }` 或 `{ "item": [...] }` 对象？→ **拆掉外层 object 壳，直接传纯数组** `["/path1", "/path2"]`（schema 的 `items` 是类型约束不是字段名！）
2. 是否对 `params` 调过 `JSON.stringify`？（删除 stringify，直接传对象字面量）
3. `image` 是不是嵌套数组 `[[...]]`？（去掉外层多余的 `[]`）
4. `image` 是不是被拼成了字符串？（去掉外层引号）
5. 是否用了 bash / Python 包装过？（去掉包装层，直接用 `DeferExecuteTool` 调用）

## 2. 生图检查

用文件读取工具读取生成图，仅在以下严重问题出现时重生：

| 需要重生 | 可以接受 |
|----------|----------|
| 人物过大，叠字后会严重遮挡 | 人物大小合理，文字区留白充足 |
| 人物偏到文字区 | 人物在预期区域 |
| 明显白色面板、窗口或边框 | 背景干净 |

最多重生 1 次；第二次无论结果直接使用。小瑕疵不重生。重生时保持相同 `image` 与 `size`，只修改 prompt 的构图描述。

## 3. 搭画布

有风格文件时，使用 Part C 排版表；无风格文件时，使用 [adaptive-sizing.md](adaptive-sizing.md) 的对应方向排版。每次调用 `batch_edit` 前加载 `ardot-design-core/tool-usage/batch-edit.md`，DSL 和 schema 均以核心技能为唯一真源。

### 文案映射（有 Part C 时）

| 风格表节点 | 填入内容 |
|------------|----------|
| T01 brand | 用户品牌名；没有则跳过 |
| T02 main title | 直播标题前半段（逗号/顿号前） |
| T03 sub title | 直播标题后半段 |
| T04 english decor | 课程看点英文关键词；没有则 `LIVE` |
| T05 window title | 「课程要点」或用户栏目标题 |
| T06–T09 list items | 用户给几条填几条 |
| T10 speech bubble | 讲师姓名 + 头衔（`｜` 连接） |
| T11 promo band | 直播时间 |
| T12 bottom header | 课程看点/副标题 |
| T13 contact | 用户提供的电话；没有则跳过 |
| T14 contact addr | 用户提供的底部地址；没有则跳过 |

- 用户给出的文案一字不改
- 标题按第一个逗号/顿号拆分；无分隔符则全放 T02
- 文本超宽时优先缩字号或扩宽度，不改文字

### batch_edit

每次不超过 25 ops，按以下顺序创建：

1. 顶层 Frame：`layout: "none"`、画布尺寸、`clipsContent: true`
2. 底图 rectangle：`x:0, y:0, width:画布宽, height:画布高+100`
3. Logo rectangle（如有）
4. 文字节点
5. 风格文件 `## Icons` 指定的 icon Frame（如有）

字体优先中文 `Noto Sans SC`、英文 `Inter`。创建文字前调用 `get_available_fonts` 确认精确 family/style，不得猜测字体样式名称。

### 图片上传（三段式，顺序不能乱）

把 ImageGen 生成的本地图片传到 Ardot 画布，必须按以下三步执行，缺一不可：

1. **`register_assets`（申请通道）**：调用一次，拿到临时 `uploadUrl` + `downloadUrl`。`contentType` 传真实 MIME（`image/png` / `image/jpeg` / `image/webp`）。URL 有过期时间，过期需重新申请。
2. **`curl PUT` 上传（真正把文件传上去）**：
   ```bash
   curl -s -X PUT "<uploadUrl>" -H "Content-Type: image/png" --data-binary "@/absolute/path/to/image.png" -w "HTTP_STATUS:%{http_code}\n"
   ```
   - **`--data-binary` 的文件路径前必须带 `@` 前缀**。不带 `@` 会把「路径字符串本身」当作数据上传，Ardot 端拿到的是几十字节的文本，imageHash 仍会生成，但图片永远渲染不出来——这是最隐蔽的坑。
   - 必须显式检查返回的 `HTTP_STATUS`，**不是 200 就不要进入下一步**（先查 URL 是否过期、Content-Type 是否匹配）。
   - `Content-Type` 必须与第 1 步 `register_assets` 传的 `contentType` **完全一致**（png 写成 jpeg 会解析失败）。
3. **`upload_images`（绑定 downloadUrl 为 fill）**：`filePath` 只能传第 1 步返回的 `downloadUrl`，**不能传本机文件路径**——传本地路径会静默失败或报错，图片不显示但很难定位原因。`nodeId` 为目标节点（底图 rectangle / Logo rectangle）。

跳过第 2 步直接把本地路径丢给 `upload_images` 是最常见的错法。不能用 batch_edit U() 替代。

`upload_images` 调用格式（2026-08-18 实测成功）：

```jsonc
// ✅ 正确写法 — items 是纯一维数组
DeferExecuteTool({
  toolName: "mcp__ardot__upload_images",
  params: {
    fileUrl: "https://ardot.tencent.com/file/<fileId>",
    items: [
      { nodeId: "3:2", filePath: "<register_assets 返回的 downloadUrl>" }
    ]
  }
})
```

- `items` 必须是**纯一维对象数组** `[{nodeId, filePath}]`
- `filePath` 传 `downloadUrl`（COS 地址），**不能传本机路径**
- 如果 wrapper 报 `items must be array`：检查是否把 items 套成了 `{item: [{...}]}` 对象外壳（与 ImageGen 的 `image` 数组 bug 同源）

#### ❌ 错误思路：用 batch_edit U() 写 IMAGE fill 来「替代」upload_images

### SVG icon

风格文件 `## Icons` 提供 SVG 源码 + 尺寸表时，用独立 `batch_edit` 插入功能性 icon；无 Icons、仅色块占位或 `no icons` 时跳过。禁止 ImageGen 生 icon、Write `.svg` 文件、或把 Part A / prompt 背景描述画成 SVG/rectangle。

```
iconCal=I("<canvasFrameId>",{type:"frame",name:"iconCalendar",x:<X>,y:<Y>,width:<W>,height:<H>,svg:"<svg viewBox='0 0 24 24' ...>...</svg>"})
```

- SVG `width` / `height` 必须等于 Ardot 帧宽高
- icon 尺寸约为承载色块的 50–60%，并居中
- 不给 icon Frame 添加 `fills`

## 4. 验证与交付

按 `ardot-design-core` 执行最终 `capture_screenshot`，并完成以下直播海报专项检查：

- 文字是否被裁切
- 人物与文字是否重叠
- Logo 是否变形
- 水印是否确实位于裁切区外

发现问题最多进行 2 轮集中修复。验证通过后再交付。

## 5. 错误处理

| 场景 | 处理 |
|------|------|
| ImageGen 报 `image must be array` | `image` 数组形态错了：改成单层字符串数组 `["p1","p2"]`（去掉多套的一层 `[]`，也不要把数组拼成字符串），修正后按相同参数重试 1 次 |
| 有人物参考图时 ImageGen 仍失败 | 不得静默去掉 `image`；告知用户无法保证人物一致性 |
| 无人物参考图时 ImageGen 失败 | 按相同参数重试 1 次；再失败告知用户 |
| 字体不可用 | 用 `get_available_fonts` 选择可用的中英文回退字体 |
| `Skipped unparseable line` | 按 `ardot-design-core/tool-usage/batch-edit.md` 修正 DSL |
| 底图 / Logo 上传成功但画布不显示图片 | 检查 curl 的 `--data-binary` 是否带 `@` 前缀（不带会传成路径字符串）；确认 `upload_images` 的 `filePath` 传的是 `downloadUrl` 而非本地路径；确认 curl 返回 HTTP 200；确认 Content-Type 与 `register_assets` 一致 |
