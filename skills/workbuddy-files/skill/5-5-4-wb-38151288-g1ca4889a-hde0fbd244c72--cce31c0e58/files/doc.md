# doc（本地 Word 类）编辑接口

上级：[SKILL.md](./SKILL.md)。工具名带 `doc_` 前缀。

```bash
python3 edsdk.py list doc
python3 edsdk.py schema <doc_tool>
python3 edsdk.py call <doc_tool> file_id=<id> ...
```

完整工具清单和参数以服务端 `tools/list` / `schema` 实时返回为准；本文只记录 doc 特有的操作约定。

> 调用任何 `doc_*` 工具前，必须先执行 `python3 edsdk.py schema <工具名>`，确认必填参数、UTF-16 偏移和区间语义；下面的接口列表只用于选工具。
> 对参数拿不准时一律先查 schema，绝不凭记忆或下表摘要猜参数。复杂参数用 `--json '{...}'`。

批量插入或一次插入大量内容时，优先使用 `doc_insert_markdown`，把多段文本、标题、列表、表格等内容组织成一段 Markdown 一次写入；不要拆成大量 `doc_insert_text` / `doc_insert_paragraph` 调用。

## 位置规则

- `idx` / `begin` / `end` 都是全文 UTF-16 code unit 偏移，不是字节 / 行列号 / 段落序号 / 肉眼字符数；底层含段落结束符、表格、图片、字段等结构占位，一个汉字或字母通常算 1，emoji / 结构占位可能不同。
- `paragraph_index` 是「第几段」序号，禁止传给 `idx` / `begin` / `end`。
- 字符范围统一左闭右开 `[begin, end)`，长度 `end - begin`。
- `doc_insert_comment` 的 `range_begin==range_end` 表示点锚批注。
- **位置一律靠查、不靠猜**：用 `doc_find` / `doc_resolve_document_structure` / `doc_get_outline` / `doc_get_table_info` 等查询工具查出来的坐标可直接回填，无需换算。
- 链式追加取「下一个插入点」：`doc_insert_text` 用 `last_edit_index`，`doc_insert_paragraph_with_text` 用 `next_index`，直接当下一次 `idx`。
- 插入图片 / 公式后必须补一次 `doc_insert_paragraph`（段落分隔符）：`doc_insert_image` / `doc_insert_math` 落点同属一个段落，不补段落分隔符会让后续文本与图片/公式挤在同一段，导致定位、样式和后续编辑全部串位；

## 编辑后索引

插入、删除、替换都会让后续内容偏移，编辑前拿到的 `idx` / `begin` / `end` 在写操作后立即失效。

- 连续多处编辑：每改完一处就重新查询，或沿用本次写接口返回的最新坐标继续追加，不沿用旧缓存。
- 多处替换优先 `doc_find_and_replace`，不要手算多个范围连续调 `doc_replace_text`；必须按旧索引批量改时从文档后部往前处理。

## 接口列表

| 工具 | 说明 |
|---|---|
| **查询 / 定位** | |
| `doc_find` | 查找文本所在位置，返回所有匹配位置的 begin/end 索引、上下文及定位锚点 |
| `doc_get_outline` | 获取文档大纲树（标题层级 Heading 1-9） |
| `doc_get_last_operable_pos` | 获取正文最后一个可操作位置的索引及其前最多 10 个字符 |
| `doc_get_images` | 获取文档中所有图片的信息 |
| `doc_resolve_document_structure` | 获取文档结构树（扁平节点列表），用于写类工具前定位位置 |
| `doc_get_text_property` | 读取指定位置 idx 处生效的文本属性 |
| `doc_get_paragraph_property` | 读取指定位置 idx 所在「段落」的属性 |
| `doc_get_section_property` | 读取指定节的页面属性、范围及总节数 |
| `doc_get_comments` | 获取文档中所有批注 |
| `doc_get_word_art_info` | 读取指定位置艺术字的属性 |
| **文本编辑** | |
| `doc_insert_text` | 在指定位置插入文本 |
| `doc_replace_text` | 替换 range 范围内的文本为指定文本 |
| `doc_find_and_replace` | 查找并替换文本，可通过 scope 限定范围 |
| `doc_find_and_set` | 按文本内容 + 文本属性组合查找，对匹配项批量替换/改属性/删除 |
| `doc_update_text_property` | 更新指定字符范围内的文本属性（仅改样式，不改长度） |
| `doc_copy_format` | 格式刷：将源范围的段落属性和文本属性复制到目标范围 |
| `doc_clear_format` | 一键清除指定范围内所有直设格式，重置为继承样式 |
| **段落 / 块** | |
| `doc_insert_paragraph` | 在 idx 处插入「段落分隔符」并给前面文本套段落样式，**不写文本**；写文本优先用 `doc_insert_paragraph_with_text` |
| `doc_insert_paragraph_with_text` | 一步插入「带文本的段落」，可带富文本 Run 和段落属性 |
| `doc_delete_paragraph` | 删除 idx 所在的整个段落及其段落结束符 |
| `doc_modify_paragraph` | 修改已有段落的属性（对齐/间距/缩进/样式/分页/制表位/引用与编号） |
| `doc_apply_named_style` | 把命名样式应用到已有段落（paragraph_ids 或 ranges 定位） |
| `doc_set_highlight_block` | 把已有段落设置为一个高亮块 |
| `doc_set_block_quote` | 设置或取消段落引用 |
| `doc_insert_page_break` | 在指定位置插入分页符 |
| `doc_insert_border` | 在指定位置插入水平分隔线（段落底边框实现） |
| **内容插入** | |
| `doc_insert_markdown` | 在指定位置插入 Markdown 格式内容（标题/列表/表格/链接/加粗斜体等） |
| `doc_insert_html_content` | 在指定 idx 处插入一段 HTML 富文本 |
| `doc_insert_math` | 在指定位置插入数学公式（LaTeX → OMML） |
| `doc_insert_image` | 在指定位置插入图片 |
| `doc_replace_image` | 替换文档中已有图片为新图片 |
| `doc_insert_normal_link` | 插入普通链接 |
| `doc_insert_word_art` | 在指定位置插入一段艺术字（带变形样式的文本） |
| `doc_insert_footnote` | 在指定位置插入脚注或尾注 |
| `doc_insert_toc` | 在指定位置插入目录（自动收集 Heading 1-9） |
| **批注** | |
| `doc_insert_comment` | 插入批注 |
| `doc_delete_comment` | 删除单条批注；最后一条删除后同时清理对应锚点，不删除被批注正文 |
| **样式 / 页面 / 节** | |
| `doc_update_named_style` | 修改命名样式定义，一次调用影响所有使用该样式的段落 |
| `doc_set_document_style` | 设置文档级默认样式（默认文本/段落/页面布局） |
| `doc_insert_section_break` | 在指定位置插入分节符，完整继承原节属性（下一页/下一栏/连续/偶数页/奇数页） |
| `doc_modify_section` | 修改指定节的页面尺寸、页边距、起始类型等属性 |
| `doc_insert_header` | 覆盖式设置页眉文本（可带 text_format / 对齐；单 section） |
| `doc_insert_footer` | 覆盖式设置页脚文本（可带 text_format / 对齐；与 set_page_number 互斥） |
| `doc_set_page_number` | 设置页码（在页脚中插入 PAGE 字段） |
| **历史 / 对比** | |
| `doc_compare_documents` | 对比两个已打开的 DOC 文档的内容和格式差异 |
| `doc_list_recent_ai_edits` | 列出文档最近通过 MCP 写工具产生的 AI 编辑记录 |
| `doc_undo_ai_edit` | 根据最近 AI 编辑记录中的 version 撤销指定编辑 |

### Table 相关工具

> 操作表格前建议先读 [table.md](./doc/table.md)：选型决策树 + 铁律 + 字段语义，最少调用次数、最低 token 消耗。
>
> 操作表格前优先用 `doc_list_tables` / `doc_get_table_info` 拿到 `table_id`，后续操作用 `table_id` 定位最稳；`table_id` 拿不到再退回 `idx`。

| 工具 | 说明 |
|---|---|
| **查询** | |
| `doc_list_tables` | 列出文档所有表格摘要（拿 table_id） |
| `doc_get_table_info` | 查询单张表格完整信息（含 cells） |
| **插入** | |
| `doc_insert_table` | 插入空表格，返回 table_id |
| `doc_insert_table_row` | 插入单行（可同时填内容） |
| `doc_insert_table_rows` | 批量多位置插入多行 |
| `doc_insert_table_column` | 插入单列（可同时填内容） |
| `doc_insert_table_cols` | 批量多位置插入多列 |
| **删除** | |
| `doc_delete_table_row` | 删除一行 |
| `doc_delete_table_column` | 删除一列 |
| `doc_delete_table` | 删除整张表格 |
| **合并 / 拆分** | |
| `doc_merge_table_cells` | 合并单元格 |
| `doc_unmerge_table_cells` | 拆分单元格 |
| **设置内容 / 属性** | |
| `doc_set_table_cells` | 批量设置单元格内容与样式（文本/格式/链接/图片） |
| `doc_set_table_properties` | 修改表格属性与布局（边框/对齐/宽度/内边距/行高列宽） |


> 参数 schema 以服务端 `tools/list` 实时返回为准；上表为一句话摘要。
