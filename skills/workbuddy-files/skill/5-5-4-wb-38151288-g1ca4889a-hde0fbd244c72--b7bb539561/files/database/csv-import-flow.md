# database · CSV 导入流程

> 📎 字段类型语义与配置结构见 `params-reference.md` §PropertyConfig；写入值结构见 §PropertyValue。

---

## 1. CSV 检查与字段分析

### 1.1 基础检查

- 文件必须存在、为 `.csv` 后缀且非空；
- CSV 必须有单行表头，字段名非空且不重复；解析失败、列数不一致或无有效数据行时停止该 CSV 的处理并返回错误；
- 记录文件大小，供 §2 决策使用。

### 1.2 字段类型推断

读取 CSV **表头 + 前 N 行样本**（建议 N=20~50），结合字段名语义和样本中的非空值推断类型；类型语义与 config 结构以 `params-reference.md` §PropertyConfig 各类型说明为准，本文不重复定义。

- 低基数单值列可推断为 `select`，多值列可推断为 `multi_select`；
- 推断不确定、同列类型冲突或格式混合时，统一降级为 `text`。

**必须先输出逐列判定表，再进入 §2 决策，不可跳过**：

| 列名 | 样本值 | 判定类型 |
| --- | --- | --- |
| （逐列填写） | | |

---

## 2. 路径决策

用户明确指定导入方式或字段 schema 时以用户要求为准；否则以 §1.2 的判定表为唯一依据，未输出判定表前不得进入任一路径。

| 判据（自上而下，首个命中即生效） | 选择 | 理由 |
| --- | --- | --- |
| CSV 超过 50 MiB | **路径 B（§4）或先拆分 CSV** | `import_csv` 单文件上限为 50 MiB |
| 任一列判定为 `text` / `number` / `date` **之外**的类型 | **路径 B（§4）** | 精确指定 schema，避免后端推断丢类型 |
| 全部列均为 `text` / `number` / `date` | **路径 A（§3）** | 一次导入，字段类型交后端推断 |

> 行数多不构成回退路径 A 的理由。

---

## 3. 路径 A · import_csv 直接导入

将当前 CSV 交给 `import_csv.py` 直接导入；标题由脚本取文件名（去扩展名）。鉴权与命令形态按 `SKILL.md` §调用方式与运行模式处理，`--token-stdin` 仅客户端模式使用。

```bash
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/library/database/import_csv.py" "<path-to-local.csv>"
# 覆盖已有 Database
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/library/database/import_csv.py" "<path-to-local.csv>" --database-id "<existing_database_id>"
# 指定目标位置
python3 "${CODEBUDDY_PLUGIN_ROOT}/skills/library/database/import_csv.py" "<path-to-local.csv>" --space-id "<target_space_id>" --parent-id "<target_parent_node_id>"
```

---

## 4. 路径 B · create_database + 分批 batch_add

本路径内部按顺序执行，必须先取得建表结果，再写入记录。

### 4.1 确定 schema

按 §1.2 的判定表构造 schema。

- `select` / `multi_select` 的 options 应基于完整 CSV 去重值生成，不能只使用样本值；
- person 列在 schema 最终确定前，按 `entry.md` §Person 写入前置解析，将姓名解析为 uid；无法唯一解析时须确认，或在建表前将整列降级为 `text`。

### 4.2 创建 database

通过 `create_database` 能力创建 database，调用方式参考 `entry.md` §1；以成功响应中的 `database_id`、最终字段 id 和选项 id 为准。

### 4.3 分批写入

把 CSV 数据行映射为 `records`，通过 `batch_add_database_records` 能力循环写入，调用方式参考 `entry.md` §3。

- 每批最多 100 条，各批次串行执行；
- `select` / `multi_select` 可按 schema 使用选项文本；
- 逐条失败保留在 `results` 中，继续处理其余有效记录并汇总失败明细。

---

## 5. 结果契约

每个 CSV 返回一个结构化结果，供直接回执或上游流程汇总：

- 路径 A 成功：`{file_name, path:"A", node_block_id, url, publish_url}`；
- 路径 B 成功：`{file_name, path:"B", database_id, url, total_count, success_count, failed_count, failures}`；
- 失败：`{file_name, error}`。

**交付给用户的必须是在线数据表的 url 或 id，不得给本地 CSV 路径或临时目录**。url 一律取自脚本返回，不自行拼接。

---

## 6. 失败与幂等约束

- 路径 A 重试时复用已返回的 `database_id` / `node_block_id` 覆盖同一节点，避免重复建表；
- 路径 B 建表成功但写入中断时，复用已创建的 `database_id`，只补写尚未成功的行，不重新建表；
- 重试前保留已成功批次及逐条结果，禁止整表盲目重放造成重复记录。