# 画布交付

产物怎么落到 `.miora` 画布

## 一、调用顺序

```
第 1 件产物：
  miora_text_to_image / miora_edit_image ...   → 取 localPath
  miora_write_canvas(action: create)           → 取 file_path，记住它
  miora_open_canvas(file_path)

第 2..N 件产物（每拿到一件立刻做一遍）：
  miora_write_canvas(action: update, file_path: <同一张画布>)
```

## 二、写入时机：拿到一件写一件

判据：这件产物成功拿到本地文件了没有，拿到了就立刻写进画布。要出 5 张图就写 5 次画布（1 次 `create` + 4 次 `update`）。

多阶段流程（先出锚点、再以它派生物料）同样按件写：锚点确认后就写进画布。

## 三、一个对话默认只有一张画布

- 首次落盘用 `action: create`；此后**本对话内的所有写入**——无论同一交付的追加替换，还是后续轮次新生成的图片 / 视频——**一律 `action: update` 写进这张已有画布**。只有用户明确说了"另开一张 / 新建画布 / 分开交付"才允许第二次 `create`。
- 首次写完就把画布路径记住并全程复用；**路径记不清时先在会话工作目录找已有 `.miora`**（如 Glob `*.miora`），找到就复用，找不到才 `create`。
- 只有真正拿到本地素材的项才进画布。生成成功但没拿到本地副本（下载失败、只有会过期的远端 URL）时，如实说明该项没进画布。
