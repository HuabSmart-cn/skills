# DOCX 下划线回填规则 (Underline Fill-in Rules)

## 回填核心思路

所有下划线函数（见 `src/skills/underline-toolkit/toolkit.py`）统一支持 `value` 参数：

- **不传 / `value=""`** → 空白下划线（模板模式）
- **`value="实际内容"`** → 内容 + 下划线保留（回填模式）

回填 = 在原有创建代码的调用处**加上 `value` 参数**，其他参数完全不变。

涉及函数：
`add_underline_run`。


## 注意事项
- 回填时 `blank_spaces` **不影响显示**，但建议保留不变，去掉 `value` 即可回退到空白模板
- 下划线不会消失：下划线是 Run 的 underline 属性，与文字内容解耦
