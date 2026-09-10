"""
看板 DSL —— L3 颗粒度声明式 Spec。

LLM 唯一编写文件 kanban_spec_*.py，只构造一个 Spec 实例。
runner 接收 Spec 编译为 SQL/SLOT_DATA/sqlSlots/DSL widgets，调用 builder 落盘 kanban_save_params.json，
随后 kanban_dsl_emitter 覆盖 HtmlContent(DSL)/SqlSlots(Datasets)，三端统一入库。

设计原则：
1. **统一抽象**：dim/x/y/path/source_dim/target_dim/nodes/group → 全部统一为 Dim
                metric/value/o/c/l/h/indicators → 全部统一为 Metric（带可选 role）
2. **三态数据形态**：series（一维）/matrix（二维交叉）/hierarchy（多层路径）自动识别
3. **逃生口**：复杂 SQL 走 raw_sql=，仍走 builder 全 lint
4. **类型安全**：dataclass + 必填校验，构造期就拦截大部分错误
5. **extras 兜底**：任何超出抽象的 echarts 原生配置走 extras=，零妥协灵活性
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union
import sys as _sys
import re as _re


# ===== SQL 字符串字面量自动归一化（治本：从 DSL 构造期消除双引号字面量误用） =====
#
# 背景（SKILL.md P0-10 ④）：Spark/DuckDB 中双引号是**列引用**，不是字符串。
# LLM 用 Python 双引号包 SQL 时极易把内层字符串也写成双引号：
#   SUM(CASE WHEN status = "delivered" THEN 1 ELSE 0 END)
# DuckDB Binder 找不到列 "delivered" → CASE 静默退化为 NULL → SUM=0（KPI 假 0）。
#
# 本工具用字符串感知扫描（与 runner._strip_string_literals 同款思路），
# 把所有**双引号包裹的字面量**改写为单引号，并 stderr 打软告警。
# - 跳过单引号已包字符串内部（避免误伤 'I love "quoted"'）
# - 跳过反引号包裹标识符（`col_name`，那是真列引用）
# - "" 双双引号是 Spark 内部转义 → 转为单引号内 \" 不需要（直接拼为含 " 的内容用 '' 转义不可行，
#   但 Spark 的 ""→" 与 DuckDB 的 ''→' 行为一致，这里我们按"内容里允许出现 \""保守处理：
#   遇到 "" 视为字符串内部的字面量 "，输出时用 \"（DuckDB/Spark 都接受 \" 转义）
#
# 该函数对**已正确使用单引号**或**不含双引号字面量**的 SQL 完全幂等无副作用。

def _normalize_sql_string_literals(expr: str, *, ctx: str = '') -> str:
    """把 SQL 表达式里的双引号字符串字面量改写为单引号字面量。

    Args:
        expr: 原始 SQL 表达式（dim/metric/raw_sql 等）
        ctx:  上下文标识（如 'Metric.expr@KPI 总额'），仅用于软告警显示

    Returns:
        归一化后的 SQL 表达式；若未触发改写则原样返回。

    设计原则：
    - 字符串感知扫描：跳过单引号字符串内部 + 反引号标识符内部
    - 双引号包裹的内容视为字面量误用，整体替换为单引号字面量
    - 内容含单引号 → 用 '' 转义；内容含 "" → 视为字符串内 "，转为 \"
    - 触发改写时 stderr 打一行软告警（不 raise，避免为单一 SQL 纠偏触发整轮重跑）
    """
    if not expr or '"' not in expr:
        return expr

    out: List[str] = []
    i = 0
    n = len(expr)
    in_single = False   # 在 '...' 内
    in_backtick = False # 在 `...` 内
    changed_segments: List[str] = []

    while i < n:
        ch = expr[i]
        if in_single:
            out.append(ch)
            if ch == "'":
                # 处理 '' 转义
                if i + 1 < n and expr[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue
        if in_backtick:
            out.append(ch)
            if ch == '`':
                in_backtick = False
            i += 1
            continue
        if ch == "'":
            in_single = True
            out.append(ch)
            i += 1
            continue
        if ch == '`':
            in_backtick = True
            out.append(ch)
            i += 1
            continue
        if ch == '"':
            # 抓取整段 "...."（含 "" 转义）
            j = i + 1
            buf: List[str] = []
            closed = False
            while j < n:
                c2 = expr[j]
                if c2 == '"':
                    if j + 1 < n and expr[j + 1] == '"':
                        # "" → 字面量内的 "
                        buf.append('"')
                        j += 2
                        continue
                    closed = True
                    j += 1
                    break
                buf.append(c2)
                j += 1
            if not closed:
                # 未闭合双引号：保守原样输出，不动
                out.append(expr[i:])
                break
            content = ''.join(buf)
            # 改写为单引号字面量：内容中的 ' 需用 '' 转义；内容中的 " 用 \" 转义
            escaped = content.replace("'", "''").replace('"', '\\"')
            out.append("'" + escaped + "'")
            changed_segments.append(f'"{content}"→\'{escaped}\'')
            i = j
            continue
        out.append(ch)
        i += 1

    new_expr = ''.join(out)
    if changed_segments:
        try:
            tag = f'[{ctx}] ' if ctx else ''
            print(
                f'⚠️  [DSL 软告警] {tag}SQL 字面量双引号已自动改写为单引号 '
                f'（Spark/DuckDB 双引号=列引用，单引号=字符串）：'
                + ' | '.join(changed_segments[:3])
                + (f' …(+{len(changed_segments)-3})' if len(changed_segments) > 3 else ''),
                file=_sys.stderr,
            )
        except Exception:
            pass
    return new_expr


# ===== raw_sql 标识符引号纠偏（FROM/JOIN 后单/双引号包标识符 → 反引号） =====
#
# 背景：远端 Spark PARSE_SYNTAX_ERROR Top1 来源是 raw_sql 里 `FROM 'tbl'` / `JOIN 'tbl'`：
#   - LLM 习惯按 ANSI SQL 写 `JOIN "tbl"` 包标识符 → 后续 _normalize_sql_string_literals
#     无差别把所有 `"..."` 治成 `'...'` → Spark 把 'tbl' 当字符串字面量 → PARSE_SYNTAX_ERROR；
#   - 或 LLM 直接写 `JOIN 'tbl'`（误解为 ANSI）；
#   本地 DuckDB 对 `FROM 'tbl'` 行为更宽松（甚至当 csv 路径），无法暴露问题，
#   导致"本地预览成功 / 远端入库失败"的失真陷阱。
#
# 治理策略（必须**先于** _normalize_sql_string_literals 执行）：
#   FROM/JOIN/逗号（FROM 列表分隔）/USING 后紧跟 'X' 或 "X"，且 X 形似标识符
#   （满足 `^[\w.\-]+$` 且非数字字面量）→ 改写为 `` `X` ``（反引号包裹）。
#   字符串字面量内部 / 反引号内部 / CTE 别名不命中。

# 标识符形态：英文字母/数字/下划线/点/连字符；至少含一个字母；禁纯数字
_RAW_SQL_IDENT_RE = _re.compile(r'^[A-Za-z_][\w.\-]*$')

# FROM/JOIN 关键字上下文（紧邻空白后的引号位置才算）。
# 注意：故意**不**包含 `,`（无法区分 FROM 多表 / SELECT 列表 / 函数参数）和
#       `USING`（USING 后紧跟的是列名列表非表名）。漏检由用户改用 JOIN 兜底。
_RAW_SQL_TABLE_CTX_RE = _re.compile(
    r'\b(?:FROM|JOIN)\b\s*$', _re.IGNORECASE
)


def _normalize_raw_sql_identifiers(sql: str, *, ctx: str = '') -> str:
    """把 raw_sql 中 FROM/JOIN/USING/, 后紧跟的 'X' 或 "X" 改写为 `X`（反引号）。

    仅当 X 形似标识符（含点的三段式 / 含连字符的 hive 表名等）时才改写；
    否则保持原样（普通字符串字面量、子查询别名 AS 'name' 不命中）。

    与 _normalize_sql_string_literals 配合：
      raw_sql ─┬─ _normalize_raw_sql_identifiers  # 第一步：标识符场景的引号纠偏
               └─ _normalize_sql_string_literals  # 第二步：剩余双引号字面量改单引号
    """
    if not sql or ('"' not in sql and "'" not in sql):
        return sql

    out: List[str] = []
    i = 0
    n = len(sql)
    in_single = False
    in_backtick = False
    in_dquote_literal = False  # 仅在不处于 FROM/JOIN 上下文时才视为字面量
    rewrites: List[str] = []

    def _is_table_ctx() -> bool:
        # 用已收集的 out 字符串末尾判断（含空白）；keyword 必须是独立词
        tail = ''.join(out[-32:]) if out else ''
        return bool(_RAW_SQL_TABLE_CTX_RE.search(tail))

    while i < n:
        ch = sql[i]
        # 已在单引号字符串内：仅处理闭合 + '' 转义
        if in_single:
            out.append(ch)
            if ch == "'":
                if i + 1 < n and sql[i + 1] == "'":
                    out.append("'")
                    i += 2
                    continue
                in_single = False
            i += 1
            continue
        # 已在反引号内：透传
        if in_backtick:
            out.append(ch)
            if ch == '`':
                in_backtick = False
            i += 1
            continue
        if ch == '`':
            in_backtick = True
            out.append(ch)
            i += 1
            continue
        # 双引号或单引号开头：先看上下文是否是 FROM/JOIN/USING/,
        if ch == '"' or ch == "'":
            quote = ch
            # 抓取整段（含转义）
            j = i + 1
            buf: List[str] = []
            closed = False
            while j < n:
                c2 = sql[j]
                if c2 == quote:
                    # 转义：双双引号 / 双单引号
                    if j + 1 < n and sql[j + 1] == quote:
                        buf.append(quote)
                        j += 2
                        continue
                    closed = True
                    j += 1
                    break
                buf.append(c2)
                j += 1
            content = ''.join(buf)
            if closed and _is_table_ctx() and _RAW_SQL_IDENT_RE.match(content):
                # 改写为反引号
                out.append('`' + content + '`')
                rewrites.append(f'{quote}{content}{quote}→`{content}`')
                i = j
                continue
            # 否则保持原样进入字面量分支
            if not closed:
                out.append(sql[i:])
                break
            if quote == "'":
                # 仍按字面量原样输出
                out.append(quote)
                # 内部内容（含原始 '' 转义）原样回填
                k = i + 1
                while k < j:
                    out.append(sql[k])
                    k += 1
                i = j
                continue
            else:
                # 双引号未识别为标识符：原样回吐让 _normalize_sql_string_literals 处理
                out.append(quote)
                k = i + 1
                while k < j:
                    out.append(sql[k])
                    k += 1
                i = j
                continue
        out.append(ch)
        i += 1

    new_sql = ''.join(out)
    if rewrites:
        try:
            tag = f'[{ctx}] ' if ctx else ''
            print(
                f'⚠️  [DSL 软告警] {tag}raw_sql 中 FROM/JOIN 后引号包裹的标识符已自动改为反引号 '
                f'（Spark 单/双引号=字符串字面量，反引号=标识符）：'
                + ' | '.join(rewrites[:3])
                + (f' …(+{len(rewrites)-3})' if len(rewrites) > 3 else ''),
                file=_sys.stderr,
            )
        except Exception:
            pass
    return new_sql


# ===== Dim：统一维度抽象 =====

@dataclass(frozen=True)
class Dim:
    """统一维度抽象。覆盖：裸列名 / SQL 表达式 / 时间分桶。

    Args:
        expr:        SQL 表达式或裸列名（必填）
        alias:       SQL/SLOT 列别名（默认从 expr 派生）
        label:       显示名（入库 dimensions[].name，如 '月份' / '品类'；缺省回退 alias/expr）
        granularity: 维度粒度。
                     - 时间粒度：day/week/month/quarter/year（runner 走时间分桶）
                     - 业务粒度：category/product/region/channel/... 任意非空字符串
                     - None：runner 视为非时间维度（裸列名/SQL 表达式）
        description: 业务说明（入库 dimensions[].description）
        col_type:    string/date/timestamp/unix（时间维度需要；date/timestamp 走裸列，Unix 秒/毫秒分桶请用 raw_sql 显式 FROM_UNIXTIME）

    示例：
        Dim('product_type', label='品类', granularity='category')
        Dim('time', label='月份', granularity='month')
        Dim("CASE WHEN p<20 THEN 'L' ELSE 'H' END", label='价格段')
    """
    expr: str
    alias: Optional[str] = None
    label: Optional[str] = None
    granularity: Optional[str] = None
    description: Optional[str] = None
    col_type: str = 'string'

    _TIME_GRAN = ('day', 'week', 'month', 'quarter', 'year')
    _TYPES = ('string', 'date', 'timestamp', 'unix')

    def __post_init__(self):
        if not self.expr or not str(self.expr).strip():
            raise ValueError('[DSL] Dim.expr 不能为空')
        if self.granularity is not None and not str(self.granularity).strip():
            raise ValueError('[DSL] Dim.granularity 不能为空字符串（None 表示非时间维度）')
        if self.col_type not in self._TYPES:
            raise ValueError(f'[DSL] Dim.col_type 必须 ∈ {self._TYPES}，得到: {self.col_type!r}')
        # SQL 字面量归一化（双引号→单引号），治理 LLM 高频误用
        normalized = _normalize_sql_string_literals(
            self.expr, ctx=f'Dim.expr alias={self.alias!r}'
        )
        if normalized != self.expr:
            object.__setattr__(self, 'expr', normalized)

    @property
    def is_time(self) -> bool:
        return self.granularity in self._TIME_GRAN


def dim(expr: str, alias: Optional[str] = None, **kw) -> Dim:
    """便捷工厂：dim('product_type') / dim('time', granularity='month')。"""
    return Dim(expr=expr, alias=alias, **kw)


def time_dim(col: str, granularity: str = 'month', col_type: str = 'string', **kw) -> Dim:
    """时间维度便捷工厂：time_dim('time','month', label='月份')。

    **kw 透传给 Dim（支持 alias/label/description 等所有 Dim 字段）。

    🛡️ label 兜底（消除「前端轴名永远是 'time'」的软陷阱）：
        若调用方未显式传 label，自动注入 `f'{col}({granularity})'`，
        例如 time_dim('order_purchase_timestamp','month') →
        label='order_purchase_timestamp(month)'。用户传了 label='月份' 则尊重原值。
        反例 9（time_dim 无 label）由此默认避免；如需保持纯净 col 输出可显式 label=''。
    """
    if 'label' not in kw or kw.get('label') is None:
        kw['label'] = f'{col}({granularity})'
    return Dim(expr=col, granularity=granularity, col_type=col_type, **kw)


# ===== Metric：统一度量抽象 =====

@dataclass(frozen=True)
class Metric:
    """统一度量抽象。覆盖：聚合指标 / 派生比率 / 角色化字段（K线OCLH、雷达轴）。

    Args:
        expr:      聚合 SQL 表达式（如 'SUM(sales)' 或 'SUM(a)/NULLIF(SUM(b),0)*100'）
        alias:     SLOT 列别名（默认从 expr 派生）
        label:     显示标签（KPI / 雷达轴名）
        role:      角色标签（candlestick: open/close/low/high；boxplot: value）
        format:    数字格式（用于 KPI/gauge formatter，如 ',.0f' / '.1f'）
        prefix:    数值前缀（如 '¥'）
        suffix:    数值后缀（如 '%'）
        normalize: 'max-norm' 时按最大值归一化到 100（雷达图常用）
        target:    目标值（gauge 专用，用于设置 max）

    示例：
        Metric('SUM(sales)')                                     # 普通聚合
        Metric('SUM(sales)', label='销售额', format=',.0f')       # KPI
        Metric('MIN(price)', role='low')                          # K线
        Metric('SUM(sales)', normalize='max-norm', label='销售')  # 雷达
    """
    expr: str
    alias: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None  # 入库 metrics[].description
    role: Optional[str] = None
    format: str = ','
    prefix: str = ''
    suffix: str = ''
    normalize: Optional[str] = None
    target: Optional[float] = None
    # KPI 专用：自定义 FROM 子句（表名 / 子查询 / JOIN 串），覆盖 spec.source.table。
    # 取值示例：
    #   - 'cat.db.order_items'                                      → 跨主表的另一张表聚合
    #   - 'cat.db.orders o JOIN cat.db.order_items oi ON o.id=oi.id'→ JOIN 后聚合
    #   - '(SELECT price FROM cat.db.items WHERE status="paid") t' → 子查询聚合
    # 仅当 role='kpi' 时生效；非 KPI 角色（K线/雷达/箱线）仍受 spec.source.table 约束。
    # runner 把 KPI 编译为 `SELECT {expr} AS alias FROM {from_sql or spec.source.table}`，
    # 所以 expr 仍必须是聚合表达式（SUM/COUNT/AVG/...），from_sql 只决定数据来源。
    from_sql: Optional[str] = None

    _ROLES = (None, 'open', 'close', 'low', 'high', 'value', 'kpi')
    _NORMS = (None, 'max-norm')

    def __post_init__(self):
        if not self.expr or not str(self.expr).strip():
            raise ValueError('[DSL] Metric.expr 不能为空')
        if self.role not in self._ROLES:
            raise ValueError(f'[DSL] Metric.role 必须 ∈ {self._ROLES}，得到: {self.role!r}')
        if self.normalize not in self._NORMS:
            raise ValueError(f'[DSL] Metric.normalize 必须 ∈ {self._NORMS}，得到: {self.normalize!r}')
        # SQL 字面量归一化（双引号→单引号），治理 LLM 高频误用
        normalized = _normalize_sql_string_literals(
            self.expr, ctx=f'Metric.expr label={self.label!r}'
        )
        if normalized != self.expr:
            object.__setattr__(self, 'expr', normalized)


def metric(expr: str, **kw) -> Metric:
    """便捷工厂：metric('SUM(sales)', label='销售额')。"""
    return Metric(expr=expr, **kw)


def kpi(expr: str, label: str, **kw) -> Metric:
    """KPI 便捷工厂：自动设置 role='kpi'，label 必填。

    兼容性吞噬：`emoji=` 在 KPI 中无效（KPI 卡片由 Spec.kpis 整体承载图标），
    若误传则**静默丢弃**（不再打软告警，避免 LLM 误用 chart() 风格写 kpi() 时
    在控制台刷屏；KPI 卡片头会用 spec.title 的 emoji 自动填充）。
    同样吞噬 `span=` / `slot_key=` 等仅 Chart 适用的字段。

    🛑 expr 必须是**聚合表达式**或常量（runner 编译为
    `SELECT {expr} AS alias FROM {from_sql or 主表}`，expr 必须能在 SELECT 上求值）。
    LLM 高频踩坑：把派生指标名（如 'total_gmv' / 'gmv_total'）当 expr 写进来 →
    编译产物 `SELECT total_gmv FROM olist_orders` 永远报 `Column not found` → 平台
    周期刷新一直 0。

    ✅ 跨表/JOIN 聚合：传 `from_sql=` 指定数据源（覆盖 spec.source.table），
       仍在主表所在 KPI batch 中以**标量子查询**形式合并执行，渲染真实数据：
         kpi('SUM(oi.price)', '订单商品总额',
             from_sql='cat.db.olist_orders o JOIN cat.db.order_items oi ON o.order_id=oi.order_id',
             prefix='¥', format=',.0f')
       runner 编译为：
         (SELECT SUM(oi.price) FROM <from_sql>) AS `订单商品总额`
       多张 KPI 可各自带不同 from_sql，仍拼成一条 SQL 一次性下发。
    """
    _CHART_ONLY = ('emoji', 'span', 'slot_key', 'order_by', 'limit', 'stacked',
                   'dual_axis', 'smooth', 'extras', 'kind', 'title', 'dims', 'metrics')
    for k in [k for k in list(kw.keys()) if k in _CHART_ONLY]:
        kw.pop(k, None)

    # —— KPI expr 形态契约（防"裸列名"静默失败 P0 陷阱）——
    # 合法形态：① 含聚合函数  ② 纯常量  ③ 传了 from_sql 的标量子查询语义（由 from_sql 兜底语义）
    # 非法形态：裸列名 / 派生标识符 / 含运算符但无聚合 且 没传 from_sql →
    #          runner 编译出 `SELECT <expr> FROM 主表`，主表无该列时永远 0/报错。
    _expr_norm = (expr or '').strip()
    _from_sql = (kw.get('from_sql') or '').strip()
    if _expr_norm and not _from_sql:
        _agg_re = _re.compile(
            r'\b(SUM|AVG|COUNT|MIN|MAX|PERCENTILE|PERCENTILE_APPROX|STDDEV|STDDEV_POP|STDDEV_SAMP|'
            r'VARIANCE|VAR_POP|VAR_SAMP|FIRST|LAST|FIRST_VALUE|LAST_VALUE|COLLECT_LIST|COLLECT_SET|'
            r'BIT_AND|BIT_OR|BIT_XOR|BOOL_AND|BOOL_OR|APPROX_COUNT_DISTINCT|APPROX_QUANTILE)\s*\(',
            _re.I,
        )
        # 常量字面量：纯数字 / 'xxx' / NULL / TRUE / FALSE
        _const_re = _re.compile(
            r"""^\s*(
                -?\d+(\.\d+)?            # 数字
                | '([^']|'')*'           # 单引号字符串
                | NULL | TRUE | FALSE    # 关键字常量
            )\s*$""",
            _re.I | _re.X,
        )
        if not _agg_re.search(_expr_norm) and not _const_re.match(_expr_norm):
            raise ValueError(
                f'[DSL] kpi("{_expr_norm}", "{label}") expr 不含聚合函数且非常量、且未指定 from_sql。\n'
                f'  原因：runner 把 KPI 编译为 `SELECT {_expr_norm} AS alias FROM {{主表}}`，\n'
                f'        expr 必须能在主表 SELECT 上求值；裸列名/派生标识符在主表不存在时\n'
                f'        会让 SQL 报 `Column not found`，平台周期刷新永远 0。\n'
                f'  ✅ 修法 A（主表内可聚合）：\n'
                f'      kpi("SUM(amount)", "{label}", prefix="¥", format=",.0f")\n'
                f'  ✅ 修法 B（跨表/JOIN 聚合，最常用）：\n'
                f'      kpi("SUM(oi.price)", "{label}",\n'
                f'          from_sql="cat.db.olist_orders o JOIN cat.db.order_items oi ON o.order_id=oi.order_id",\n'
                f'          prefix="¥", format=",.0f")\n'
                f'  ✅ 修法 C（子查询聚合）：\n'
                f'      kpi("SUM(price)", "{label}",\n'
                f'          from_sql="(SELECT price FROM cat.db.items WHERE status=\\"paid\\") t")'
            )

    return Metric(expr=expr, label=label, role='kpi', **kw)


# ===== Source：数据源 =====

@dataclass
class Source:
    """看板数据源。

    runner 自动按物理表拼"全量取数 SQL"（`SELECT * FROM table LIMIT N`），
    走 wedatacli query-sql 取数拿 csv，本地 DuckDB 按 columns 投影视图喂所有图表。

    Args:
        table: 表名（schema.table 形式）
        columns: 列名列表（字符串或 {name,type,is_partition} dict 都接受）
        time_col: 主时间列（用于 string 时间解析嗅探）
        time_type: string / date / timestamp / unix（datetime 按 timestamp 填；Unix 分桶需 raw_sql 显式 FROM_UNIXTIME）
        limit: 全量取数上限
        where: 可选全局 where 子句
    """
    table: str
    columns: Sequence[Union[str, Dict[str, Any]]]
    time_col: Optional[str] = None
    time_type: str = 'string'
    limit: int = 10_000
    where: Optional[str] = None

    def __post_init__(self):
        # 自动把自己注入模块级上下文，让后续构造的 Chart 在 __post_init__ 里
        # 能查到当前 Source 的 columns 类型，避免 double 裸列被启发式误判为分类列。
        # 利用 Python "先求实参 → 再调 Spec.__init__" 的求值顺序：
        # spec 文件里 source 永远比 chart 早实例化，因此此处注入时机正确。
        global _LATEST_SOURCE
        _LATEST_SOURCE = self

        # ── C3 软告警：columns 缺 type 字段时，scatter/数值列豁免将退化 ──
        # 设计动机（与 SKILL.md 反例 13 对齐）：
        #   _is_numeric_column 仅在 columns 元素是 {name,type,...} dict 时才能命中数值类型
        #   并撤销"裸列名→分类列"的保守误判。如果 LLM 只写 columns=['a','b','c']（纯 str），
        #   ⑪ scatter 形态硬契约会强制要求 `* 1.0`/CASE 包装，报错文案易被误读为
        #   "dim 表达式写错了"，引导 LLM 去改 dim 而不是补 type。
        #   此处构造期打一行 stderr 软告警（不 raise，避免为单一 columns 缺 type 触发整轮重跑），
        #   让根因（column 缺 type）直接出现在控制台首行。
        try:
            has_any_dict_with_type = any(
                isinstance(c, dict) and 'name' in c and 'type' in c
                for c in self.columns
            )
            if self.columns and not has_any_dict_with_type:
                print(
                    f'⚠️  [DSL 软告警] Source.columns 全部为纯字符串（缺 type 字段），'
                    f'scatter/数值列豁免将退化为文本启发式：裸数值列（如 double/decimal）'
                    f'会被误判为分类列，触发 ⑪ scatter 硬契约误报。\n'
                    f'  ✅ 建议改为 dict 形态：columns=[{{"name":"col","type":"double"}}, ...]'
                    f'（type 取自 SKILL.md 表 schema 的真实类型，整列抄全）',
                    file=_sys.stderr,
                )
        except Exception:
            pass

    def column_names(self) -> List[str]:
        out: List[str] = []
        for c in self.columns:
            if isinstance(c, str):
                out.append(c)
            elif isinstance(c, dict) and 'name' in c:
                out.append(c['name'])
            else:
                raise ValueError(f'[DSL] Source.columns 元素必须是 str 或 {{name,...}} dict，得到: {c!r}')
        return out

    def column_types(self) -> Dict[str, str]:
        """返回 {列名: 类型小写串}，仅对 dict 形态的元素有效。

        runner 真正读取 csv 时会做更精确的类型推断；这里仅用于 DSL 构造期
        的"裸列名→数值列"豁免（消除 `* 1.0` 咒语）。
        """
        out: Dict[str, str] = {}
        for c in self.columns:
            if isinstance(c, dict) and 'name' in c and 'type' in c:
                out[c['name']] = str(c['type']).lower().strip()
        return out


# 模块级"最近构造的 Source"上下文。
# 设计动机：Chart.__post_init__ 单独构造时拿不到 Source，只能用文本启发式，
#   把 double 裸列名误判为分类列，逼用户写 `col * 1.0` 这种"咒语"。
#   利用 Python 求值顺序"先构造 Source 实参 → 再构造 Chart 实参 → 最后调 Spec.__init__"，
#   让 Source.__post_init__ 自动把自己注入此 context，Chart 启发式即可在裁定
#   "裸列是否分类"时先查 columns 类型，命中数值类型直接放行。
#   多 Spec 共存时以"最近构造的 Source"为准（实际场景一个进程只跑一个 spec）。
_LATEST_SOURCE: Optional['Source'] = None


def _current_source() -> Optional['Source']:
    return _LATEST_SOURCE


# 视为"数值列"的类型集合（覆盖 Spark/Hive/Presto/MySQL/PG/Iceberg 常见命名）。
# 命中即可在 scatter 启发式中豁免（撤销"裸列名 → 分类列"的保守误判）。
_NUMERIC_TYPE_PREFIXES = (
    'tinyint', 'smallint', 'int', 'integer', 'bigint',
    'float', 'double', 'real', 'decimal', 'numeric',
    'long', 'short', 'byte',
)


def _is_numeric_column(col: str) -> bool:
    """查询当前 _LATEST_SOURCE 内 column 类型，命中数值类型返回 True；
    若没有 source 上下文 / column 类型未声明，返回 False（保守降级到文本启发式）。
    """
    s = _current_source()
    if s is None:
        return False
    types = s.column_types()
    t = types.get(col, '')
    if not t:
        return False
    return any(t.startswith(p) for p in _NUMERIC_TYPE_PREFIXES)


# ────────────────────────────────────────────────────────────────────────
# 类型规范化：把 source.columns 各种方言的类型名 → Dim.col_type 枚举值
# ────────────────────────────────────────────────────────────────────────
# 支持的真实方言（Iceberg / Delta / Spark / Hive / ClickHouse / Presto / MySQL / PG）：
#   - date / date32                                     → 'date'
#   - timestamp / timestamp(N) / timestamp_tz(N)
#     timestamp_ntz / timestamp_ltz / datetime / datetime(N) → 'timestamp'
#   - 其它                                              → ''（不回填，沿用默认 string）
# 注意：数值型 Unix 秒/毫秒不会按列名启发式自动归一，需在 raw_sql 中显式 FROM_UNIXTIME。
_TIMESTAMP_TYPE_PREFIXES = (
    'timestamp', 'datetime',  # spark/iceberg/hive 主流
)
_DATE_TYPE_PREFIXES = ('date',)
def _normalize_col_type(raw_type: str) -> str:
    """把 source.columns 的真实类型字符串映射到 Dim.col_type 四值之一。

    返回 '' 表示无法归一（保持调用方原默认值，不污染）。
    """
    if not raw_type:
        return ''
    t = str(raw_type).lower().strip()
    # 去掉精度后缀：timestamp(6) → timestamp，varchar(255) → varchar
    import re as _re_n
    t_base = _re_n.sub(r'\s*\(.*?\)\s*', '', t).strip()
    # timestamp 系列：timestamp / timestamp_tz / timestamp_ntz / timestamp_ltz / datetime
    if any(t_base.startswith(p) for p in _TIMESTAMP_TYPE_PREFIXES):
        return 'timestamp'
    # date 系列：date / date32
    if any(t_base.startswith(p) for p in _DATE_TYPE_PREFIXES):
        return 'date'
    return ''


def source(table: str, columns: Sequence[Union[str, Dict[str, Any]]], **kw) -> Source:
    return Source(table=table, columns=list(columns), **kw)


# ===== Chart：统一图表抽象（L3 核心） =====

@dataclass
class Chart:
    """单个图表组件（L3 统一抽象）。

    必填：
        kind:    图表类型，∈ SUPPORTED_KINDS
        title:   卡片标题

    数据描述（统一为 dims + metrics）：
        dims:    维度列表（List[Dim] 或 List[str] 自动包装）
        metrics: 度量列表（List[Metric] 或 List[str] 自动包装）

    数据形态自动识别（runner 内部按 kind 派发）：
        - series   ：单 dim + n metrics（line/bar/pie/funnel/radar）
        - point    ：散点 scatter，dims[0]→x，metrics[0]→y，dims[1?]→group
        - matrix   ：双 dim + 1 metric（heatmap/sankey/graph）
        - hierarchy：多 dim path + 1 metric（treemap/sunburst）
        - kpi_like ：单 metric（gauge）
        - role     ：角色化 metrics（candlestick: o/c/l/h；boxplot: value+group）
        - table    ：列出 dims（直接展示）

    渲染控制：
        span:        占用列数（1~grid_columns）；None=由 runner 按形状偏好自动决定（推荐）
        emoji:       标题前的 emoji
        order_by:    排序键（'-SUM(sales)' 倒序，'name' 升序，None 默认）
        limit:       结果行数上限（自动 TopN+Others 防偏态）
        stacked:     堆叠（bar/line）
        dual_axis:   双轴 metric 索引数组（[1] 表示第 2 个 metric 走右轴）
        smooth:      折线平滑

    高级：
        extras:      透传给前端 echarts 的额外配置（任意 dict）
        slot_key:    SLOT 键，默认从 title 派生
        raw_sql:     ⚠️ 逃生口
        slot_columns: raw_sql 模式下显式列序
        escape_hatch: True 时允许 raw_sql
    """
    kind: str
    title: str

    # —— 统一数据描述 ——
    dims: List[Union[Dim, str]] = field(default_factory=list)
    metrics: List[Union[Metric, str]] = field(default_factory=list)

    # —— 渲染控制 ——
    span: Optional[int] = None  # None=runner 按

... [Content truncated, total 94,296 chars] ...