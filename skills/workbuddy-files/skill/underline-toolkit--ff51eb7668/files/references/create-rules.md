# DOCX 下划线创建规则

## 核心原则

### ⚠️ 绝对禁止

**永远不要**使用 `________`（连续下划线字符）来制作填空下划线！

```python
# ❌ 错误！用户在 Word 中填写后下划线会消失
run = p.add_run("甲方：________________")
```

**原因**：下划线字符本身就是文本内容，用户在 Word/WPS 中点击填写时会删除这些字符，导致下划线消失。

### ✅ 正确方案：字符下划线

统一使用 **字符下划线**（Run 的 underline 属性）实现所有填空下划线，适用于所有场景。

---

## 原理

在段落中添加一个带有 **`underline` 属性**的 Run（内容为空格或实际文本）。

- 空白模板：Run 的 text 为空格，用户看到一段下划线
- 带值时：Run 的 text 为实际内容，underline 属性保留

### XML 结构

```xml
<!-- 带下划线的 Run -->
<w:r>
  <w:rPr>
    <w:rFonts w:eastAsia="仿宋"/>
    <w:u w:val="single"/>
  </w:rPr>
  <w:t xml:space="preserve">深圳市南山区</w:t>
</w:r>
```

---

## 核心 API

- **`add_underline_run(paragraph, ...)`** — 添加带字符下划线的 Run（空格或实际文本），返回 `run`
  > 📍 深入参考：`src/skills/underline-toolkit/toolkit.py` → `add_underline_run()`

- **`add_normal_run(paragraph, text, ...)`** — 添加普通文字 Run（无下划线），用于拼接正文，返回 `run`
  > 📍 深入参考：`src/skills/underline-toolkit/toolkit.py` → `add_normal_run()`

---

## blank_spaces 取值经验（14pt 仿宋 / A4 页面）

> A4 可用宽度 ≈ 15.92cm（左右页边距各 2.54cm），14pt 中文字宽 ≈ 0.49cm，1 个 NBSP ≈ 0.25cm。
> **核心原则：先算文字占宽，再用剩余空间反推 NBSP 数量，宁短勿溢。**

| 场景 | 推荐值 | 说明 |
|------|--------|------|
| 独占一行（如合同编号） | 10-12 | 前面文字短，可适当拉长 |
| 同行两段（如姓名+身份证） | 6-8 | 两段下划线+两段标签，空间紧张 |
| 同行两段（如电话+地址） | 8 | 标签较短时可稍多 |
| 行内嵌入（如年/月/日） | 2-4 | 仅容纳几个数字 |
| 行内短填空（如金额） | 5-6 | 4-5 位数字+少量留白 |

**避坑：**
- 同一行放两个填空时，**每段不超过 8**，否则容易溢出换行
- 能合并到同一行的字段（如姓名+身份证）尽量合并，减少行数、排版更紧凑

---

## 通用辅助函数

以下辅助函数在 `src/skills/underline-toolkit/toolkit.py` 中提供，生成脚本中常用：

- **`add_paragraph_text(doc, text, ...)`** — 添加纯文本段落（不含下划线填空），返回 `Paragraph`
  > 📍 深入参考：`src/skills/underline-toolkit/toolkit.py` → `add_paragraph_text()`

- **`setup_a4_page(doc, ...)`** — 设置 A4 页面尺寸和页边距
  > 📍 深入参考：`src/skills/underline-toolkit/toolkit.py` → `setup_a4_page()`

---

## 注意事项与常见陷阱

### 必须注意

1. **中文字体必须同时设置 `font.name` 和 `eastAsia`**：
   ```python
   run.font.name = "仿宋"
   run._element.rPr.rFonts.set(qn('w:eastAsia'), "仿宋")
   ```
   只设 `font.name` 在 Word 中中文可能显示为宋体。

2. **空白下划线需要空格占位**：`blank_spaces` 不能太小，否则下划线不可见。

### 常见错误
| 错误 | 原因 | 修复 |
|------|------|------|
| 回填后下划线消失 | 用了 `________` 字符方式 | 改用 `add_underline_run()` |
| 中文显示为宋体 | 没设置 `eastAsia` | 同时设置 `font.name` 和 `eastAsia`（见上方第1条） |

