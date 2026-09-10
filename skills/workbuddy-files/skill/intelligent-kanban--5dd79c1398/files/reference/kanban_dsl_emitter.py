"""
看板 DSL Emitter —— spec + runner 编译产物 → DSL JSON。

设计原则
========
1. **零重复计算**：emitter 不重新解析 spec / 不重新编译 SQL / 不重新生成数据。
   所有数据都来自 runner build_kanban() 编译循环里**已经计算好**的产物：
       - cfg（ECharts options dict） → Chart.Option（只保留样式与 dataBinding 字段映射，不内联业务数据）
       - kpi_config                  → KPI（DSL 称作 indexCard）的 Option 字段映射
       - slot_data                   → Dataset.data（首行 header 的二维数组 JSON 字符串，仅写入 SqlSlots）
       - 编译期 SQL                  → Dataset.sql

2. **DSL / Dataset 同源**：emitter 在 build_kanban() 末尾、PREVIEW 同步之前调用，
   保证本地 kanban_dsl.json 与写入平台的 lowerCamelCase Dataset 数组同源同步。
   入库时 HtmlContent 只承载页面/组件 DSL（不含 Datasets），SqlSlots 是唯一 Dataset 源。
   任何修改都通过改 spec 重跑 build_kanban，入库参数原子级一起更新。

3. **30 栅格映射**：DSL 约定 Cols=30，与 spec.grid_columns（默认 4）按比例映射：
       step = 30 // grid_columns
       w = span × step
       KPI 行 N 张卡走"等分 30"特殊映射：w = 30 // N（保证 N 张卡占满整行不留空隙）

4. **Dataset 1:1 绑定 widget**：每个 chart/kpi widget 对应一个独立 dataset，
   key/sql/data 一一对应，便于面板编辑回显与按需走 Sql 实时查询。
   纯文本 widget（page_title / page_subtitle）不绑定 dataset。

5. **SqlSlots 是唯一数据源**：Dataset.data 只是预览态初始快照，可能因体积阈值被整体剥离。
   前端必须通过 Widget.DatasetName 匹配 SqlSlots.key，优先使用 data，缺失或刷新时调用批量查询接口拉取最新 rows。

6. **不引入新 LLM API**：spec 形态零变化（LLM 仍只写 kanban_spec.py），
   emitter 完全是 runner 内部细节，遵循 SKILL P0-1 / P0-2。

入口
====
    emit_dsl(spec, widget_records, slot_data, sql_map, output_dir, slot_meta_map=None, save_meta=None) -> Dict
"""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from kanban_dsl import Spec, Source, Chart, Compare, Metric, Dim


DSL_VERSION = '1.0.0'
GRID_COLS = 30                  # DSL 约定（30 列，5 张 KPI 卡可整除）
ROW_HEIGHT_PX = 20              # widget.h × 20px = 实际高度
UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES = 64 * 1024
UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO = 0.20
MAX_DEFAULT_RENDER_DATA_BYTES = 128 * 1024
MAX_UNCOMPRESSED_CONTENT_BYTES = 16 * 1024 * 1024
LEGACY_DATASET_FIELDS = frozenset({
    'Key', 'Sql', 'Metrics', 'Dimensions', 'Data', 'Columns',
    'RefreshInterval', 'SqlType', 'DataSourceId', 'ConnectionType',
})


def _encode_update_payload(text: str, field_name: str = '') -> str:
    """将 UpdateAiKanBan 大字段编码为 base64；超过阈值时优先使用 gzip+base64。"""
    raw = text.encode('utf-8')
    label = field_name or 'UpdateAiKanBan payload'
    if len(raw) > MAX_UNCOMPRESSED_CONTENT_BYTES:
        raise ValueError(
            f'{label} 解码后内容超过服务端上限: raw={len(raw)}B, '
            f'threshold={MAX_UNCOMPRESSED_CONTENT_BYTES}B'
        )

    raw_b64 = base64.b64encode(raw).decode('ascii')
    if len(raw) < UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES:
        return raw_b64

    gz = gzip.compress(raw, compresslevel=6)
    gz_b64 = base64.b64encode(gz).decode('ascii')
    saving_ratio = 1 - (len(gz_b64) / len(raw_b64)) if raw_b64 else 0
    if saving_ratio >= UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO:
        print(f'📦 {label} 已启用 gzip+base64: raw={len(raw)}B, base64={len(raw_b64)}B, '
              f'gzipBase64={len(gz_b64)}B, saving={saving_ratio:.1%}')
        return gz_b64
    return raw_b64


def _validate_lower_camel_datasets(datasets: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """校验入库 Dataset 数组只使用当前 lowerCamelCase 字段协议。"""
    for index, dataset in enumerate(datasets):
        if not isinstance(dataset, dict):
            return False, f'DSL Dataset 协议错误：Datasets[{index}] 不是对象'
        legacy_fields = sorted(LEGACY_DATASET_FIELDS.intersection(dataset.keys()))
        if legacy_fields:
            key = dataset.get('key') or dataset.get('Key') or f'#{index}'
            return False, (
                'DSL Dataset 协议错误：检测到旧 PascalCase 字段 '
                f'{legacy_fields}，dataset={key}；请重跑当前 emitter 生成 lowerCamelCase 字段'
            )
    return True, ''


def _default_render_data_bytes(datasets: List[Dict[str, Any]]) -> int:
    """统计整组 Datasets 的默认渲染 data 字节数；结构不明确时返回 -1。"""
    total = 0
    for dataset in datasets:
        if not isinstance(dataset, dict):
            return -1
        if 'data' not in dataset or dataset.get('data') is None:
            continue
        data = dataset.get('data')
        data_text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
        total += len(data_text.encode('utf-8'))
        if total > MAX_DEFAULT_RENDER_DATA_BYTES:
            return total
    return total


def _strip_default_render_data_if_needed(datasets: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], bool, int]:
    """生成端与服务端保持同口径：整组默认渲染 data 超过阈值时删除所有 dataset.data。

    Dataset.data 只是可选预览快照；缺失时前端必须按 Widget.DatasetName 动态查询。
    """
    data_bytes = _default_render_data_bytes(datasets)
    if data_bytes < 0 or data_bytes <= MAX_DEFAULT_RENDER_DATA_BYTES:
        return datasets, False, data_bytes

    next_datasets: List[Dict[str, Any]] = []
    stripped = False
    for dataset in datasets:
        if not isinstance(dataset, dict):
            next_datasets.append(dataset)
            continue
        next_dataset = dict(dataset)
        if 'data' in next_dataset:
            next_dataset.pop('data', None)
            stripped = True
        next_datasets.append(next_dataset)
    return next_datasets, stripped, data_bytes


def _dsl_without_internal_fields(dsl: Dict[str, Any]) -> Dict[str, Any]:
    """移除 emitter/runner 内部诊断字段，保证入库 DSL 协议稳定。"""
    return {k: v for k, v in dsl.items() if not str(k).startswith('_')}


def _dsl_without_datasets(dsl: Dict[str, Any]) -> Dict[str, Any]:
    """HtmlContent 只承载页面/组件 DSL；Datasets 仅通过 SqlSlots 入库，避免重复存储。"""
    html_dsl = _dsl_without_internal_fields(dsl)
    html_dsl.pop('Datasets', None)
    return html_dsl


# 各 kind 推荐的 widget 高度（行数；× 20px = 像素高度）
# KPI 卡只有「数值 + 标签」两行内容，6 行 = 120px 留白过多；
# 4 行 = 80px 紧凑且足以容纳 24px 数值 + 标签 + 内边距，视觉上更协调。
HEIGHT_BY_KIND: Dict[str, int] = {
    'kpi':         4,
    'indexCard':   4,
    'text':        2,
    'line':        14,
    'bar':         14,
    'pie':         14,
    'scatter':     14,
    'radar':       14,
    'funnel':      14,
    'gauge':       14,
    'heatmap':     14,
    'candlestick': 14,
    'treemap':     14,
    'sunburst':    14,
    'sankey':      16,
    'graph':       16,
    'boxplot':     14,
    'parallel':    16,
    'table':       18,
    'compare':     14,
}

# 看板 DSL 默认视觉色板 / 圆角 / 阴影常量
ACCENT = '#FF6B35'  # 橙色 —— KPI 数值 / gauge 指针 / trend 强调
PRIMARY = '#0EA5E9'  # 青蓝 —— line/bar/pie 主色
KANBAN_COLORS = [
    '#4C84FF', '#36CBCB', '#F2637B', '#FAD337', '#975FE4',
    '#3AA1FF', '#4ECB73', '#FBD44A', '#F97B7B', '#6DD47E',
]
CARD_BORDER = '#eef2f7'
CARD_RADIUS = 14
TITLE_COLOR = '#0f172a'
KPI_LABEL_COLOR = '#64748b'

# 指标卡数值色板：5 张 KPI 常见于一行，避免整排"清一色橙"造成视觉疲劳。
# 首位保留 ACCENT（#FF6B35 橙）延续既有主视觉，后 4 位与 KANBAN_COLORS 主色系呼应，
# 且饱和度接近、明度接近，确保整排 KPI 在同一视觉权重上（不出现某张"过淡/过亮"）。
# 依赖前端契约：IndexCardWidget 的 valueColor 直接作用于数字字色（css color）。
KPI_VALUE_COLORS = [
    '#FF6B35',  # 橙 —— 主 KPI（承接 ACCENT）
    '#0EA5E9',  # 天蓝
    '#22C55E',  # 翠绿
    '#8B5CF6',  # 紫
    '#F59E0B',  # 琥珀
]


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _now_iso8601() -> str:
    """返回带 +08:00 时区的 ISO 8601 时间字符串。"""
    tz_cn = timezone(timedelta(hours=8))
    return datetime.now(tz_cn).strftime('%Y-%m-%dT%H:%M:%S+08:00')


def _expr_to_field_name(expr: str) -> str:
    """从 SQL 表达式提取主字段名（用于 KPI valueField / 兜底字段名）。

    简单启发式：
      - SUM(sales) → 'sales'
      - COUNT(*) → '*'
      - SUM(a)/SUM(b) → 'a'（取第一个字段）
      - 裸列名 → 原样
    """
    if not expr:
        return ''
    s = expr.strip()
    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', s):
        return s
    m = re.match(
        r'^(?:SUM|AVG|COUNT|MIN|MAX|FIRST|LAST|MEDIAN)\s*\(\s*'
        r'(?:DISTINCT\s+)?(?P<c>[^),]+?)\s*[,)]',
        s, flags=re.IGNORECASE,
    )
    if m:
        c = m.group('c').strip().strip('`').strip('"')
        if c == '*':
            return '*'
        return c
    return s


def _normalize_unit(unit: Optional[str]) -> str:
    """统一单位文本，兼容全角百分号和空白。"""
    value = str(unit or '').strip()
    return '%' if value in ('%', '％') else value


def _is_percent_suffix(suffix: Optional[str]) -> bool:
    return _normalize_unit(suffix) == '%'


def _format_decimal_places(fmt: Optional[str], *, default: int = 0,
                           max_decimals: Optional[int] = None) -> int:
    """从 spec format 中提取小数位，并可统一封顶。"""
    fmt_s = (fmt or '').strip()
    decimal_match = re.search(r'\.(\d+)', fmt_s)
    decimals = int(decimal_match.group(1)) if decimal_match else default
    decimals = max(0, decimals)
    if max_decimals is not None:
        decimals = min(max_decimals, decimals)
    return decimals


def _format_to_numeral(fmt: Optional[str], prefix: str = '', suffix: str = '', *,
                       include_affixes: bool = True,
                       max_decimals: Optional[int] = None) -> str:
    """spec 风格 format → numeral.js 风格字符串（纯数字格式，不承担单位）。

    协议约定（前端渲染器统一消费 valuePrefix / valueSuffix 作为单位真源）：
      - valueFormat 只描述**纯数字**格式（千分位、小数位），不含 ¥ / % / 件 / 万 等单位；
      - 单位一律通过 chart 顶层的 valuePrefix / valueSuffix 字段下发，前端在渲染时拼装
        `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}`。

    format → numeral 转换示例：
      ',.0f'  → '0,0'
      ',.2f'  → '0,0.00'
      '.1f' + suffix='%' → '0.0'（% 走 valueSuffix，绝不拼进 numeral 格式串）
      ','     → '0,0'

    关于百分比：SQL 端已把百分比 × 100（例如 25.30 表示 25.30%），因此这里的 numeral
    表达式绝不能用 numeral 的百分比触发符 `%`（会二次 ×100 → 2530%）。本函数**始终不**
    在返回值中包含 `%` / `¥` 等单位字符，避免任何双单位拼接风险。

    参数说明：
      include_affixes: 保留形参用于向后兼容 emitter 内其他调用点，实际语义已收敛为
                       "永远剥离单位"。传 True 也不会把单位塞回 numeral 格式串——
                       调用方必须通过 valuePrefix / valueSuffix 显式下发单位。
    """
    del prefix, suffix, include_affixes  # 单位真源改由 valuePrefix / valueSuffix 承载
    fmt = (fmt or ',').strip()
    has_thousand = ',' in fmt
    decimal_match = re.search(r'\.(\d+)', fmt)
    decimals = int(decimal_match.group(1)) if decimal_match else 0
    decimals = max(0, decimals)
    if max_decimals is not None:
        decimals = min(decimals, max_decimals)

    base = '0,0' if has_thousand else '0'
    if decimals > 0:
        base += '.' + ('0' * decimals)
    return base


def _column_type_lower(col_type: str) -> str:
    """spec source.columns 的 type → Dataset columns[].columnType（小写枚举）。

    DSL 约定：string / int / bigint / double / decimal / date / timestamp / boolean
    """
    if not col_type:
        return 'string'
    t = col_type.strip().lower()
    mapping = {
        'string': 'string', 'varchar': 'string', 'char': 'string', 'text': 'string',
        'date': 'date',
        'timestamp': 'timestamp', 'datetime': 'timestamp',
        'unix': 'bigint',
        'int': 'int', 'integer': 'int', 'tinyint': 'int', 'smallint': 'int',
        'bigint': 'bigint', 'long': 'bigint',
        'double': 'double', 'float': 'double', 'real': 'double',
        'decimal': 'decimal', 'numeric': 'decimal',
        'boolean': 'boolean', 'bool': 'boolean',
    }
    return mapping.get(t, 'string')


def _column_type_upper(col_type_lower: str) -> str:
    """columnType（小写）→ table 列定义用的 DataType（大写，前端 table 渲染用）。"""

    return col_type_lower.upper()


def _is_numeric_lower(col_type_lower: str) -> bool:
    return col_type_lower in ('int', 'bigint', 'double', 'decimal')


def _metric_alias(m: Metric) -> str:
    """与 runner._metric_alias 同语义，用于查找列名。"""
    if m.alias:
        return m.alias
    s = (m.expr or '').strip()
    mm = re.match(
        r'^(?P<f>SUM|AVG|COUNT|MIN|MAX|FIRST|LAST)\s*\(\s*(?:DISTINCT\s+)?(?P<c>[^)]+?)\s*\)$',
        s, flags=re.IGNORECASE,
    )
    if mm:
        f = mm.group('f').lower()
        c = mm.group('c').strip().strip('`').strip('"')
        if c == '*':
            return f'{f}_count'
        if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', c):
            distinct = bool(re.search(r'DISTINCT', s, re.IGNORECASE))
            return f'{f}_distinct_{c}' if distinct else f'{f}_{c}'
    return _expr_to_field_name(s) or 'metric'


def _dim_alias(d: Dim) -> str:
    """与 runner._dim_sql 输出列名对齐。"""
    if d.alias:
        return d.alias
    if d.is_time:
        return f'{d.expr.strip()}_{d.granularity}'
    return _expr_to_field_name(d.expr)


# ---------------------------------------------------------------------------
# UI Settings 主题派生（保留主题色，但圆角/阴影对齐 mock 视觉）
# ---------------------------------------------------------------------------

_THEME_PRESETS: Dict[str, Dict[str, str]] = {
    'retail':    {'PrimaryColor': PRIMARY, 'BackgroundColor': '#F5F7FA', 'Mode': 'light'},
    'business':  {'PrimaryColor': '#1E40AF', 'BackgroundColor': '#F1F5F9', 'Mode': 'light'},
    'finance':   {'PrimaryColor': '#15803D', 'BackgroundColor': '#F0FDF4', 'Mode': 'light'},
    'monitor':   {'PrimaryColor': '#0891B2', 'BackgroundColor': '#0F172A', 'Mode': 'dark'},
    'dark':      {'PrimaryColor': '#3B82F6', 'BackgroundColor': '#0F172A', 'Mode': 'dark'},
}


def _build_ui_settings(theme: str) -> Dict[str, Any]:
    preset = _THEME_PRESETS.get((theme or '').lower(), _THEME_PRESETS['retail'])
    is_dark = preset['Mode'] == 'dark'
    return {
        'Theme': {
            'Mode': preset['Mode'],
            'PrimaryColor': preset['PrimaryColor'],
            'FontColor': '#E5E7EB' if is_dark else TITLE_COLOR,
            'BackgroundColor': preset['BackgroundColor'],
            'Padding': {'X': 24, 'Y': 24},
            'FontFamily': 'PingFang SC, Helvetica, Arial, sans-serif',
            'FontSize': 14,
            'FontWeight': '400',
            'EnableEdit': True,
            'EnableHoverHighlight': True,
            'HoverBorderStyle': 'dashed',
            'HoverBorderColor': preset['PrimaryColor'],
            'SelectedBorderStyle': 'solid',
            'SelectedBorderColor': preset['PrimaryColor'],
            'SelectedBorderWidth': 2,
            'BorderRadius': CARD_RADIUS,
            'BoxShadow': 30,
            'TitleAlign': 'left',
        },
        'Grid': {
            'Cols': GRID_COLS,
            'RowHeight': ROW_HEIGHT_PX,
            'Gutter': [12, 12],
        },
        'Locale': 'zh-CN',
        'Filters': [],
        'Variables': [],
    }


# ---------------------------------------------------------------------------
# Card / Title 默认样式（与 mock 视觉对齐）
# ---------------------------------------------------------------------------

def _default_card(*, transparent: bool = False) -> Dict[str, Any]:
    """DSL Card 默认样式（无 Size/Margin，Padding 用 {X,Y}，Border 含 Radius）。

    transparent=True 时用于纯文本 widget（page-title / note），
    去掉边框 / 阴影 / 背景。
    """
    if transparent:
        return {
            'Padding': {'X': 0, 'Y': 0},
            'Background': {'Color': 'transparent', 'Opacity': 100},
            'Border': {'Color': 'transparent', 'Width': 0, 'Style': 'none', 'Radius': 0},
        }
    return {
        'Padding': {'X': 16, 'Y': 16},
        'Background': {'Color': '#ffffff', 'Opacity': 100},
        'Border': {'Color': CARD_BORDER, 'Width': 1, 'Style': 'solid', 'Radius': CARD_RADIUS},
    }


def _default_title(text: str, *, kind: str = 'card') -> Dict[str, Any]:
    """生成 Title。

    kind:
      'page'       → 页面大标题（22px / 700 / Layout=vertical）
      'card'       → 卡片标题（14px / 600 / Layout=auto / Bottom margin=8）
      'kpi-label'  → KPI 卡 label（12px / 500 / 灰色 / 不加粗）
      'section'    → 分组段落标题（15px / 600）
    """
    # 说明：DSL 已用 Font.StrokeColor / Font.StrokeWidth（CSS `-webkit-text-stroke`
    # 作用在标题文字本身）取代原 Title.BorderBottom（作用在标题底部下划线）。默认不描边，
    # 与历史 BorderBottom={Color:null, Width:0, Style:'none'} 的"无边框"语义一致。
    base = {
        'Show': True,
        'Text': text,
        'Description': {'Show': False, 'Text': ''},
        'Margin': {'X': 0, 'Y': 0},
        'Padding': {'X': 0, 'Y': 0},
        'Font': {'Family': None, 'Size': 14, 'Weight': 600,
                 'Color': TITLE_COLOR, 'LetterSpacing': 0,
                 'StrokeColor': None, 'StrokeWidth': 0},
        'Decoration': {'Align': 'left', 'Bold': True, 'Italic': False,
                       'Underline': False, 'LineThrough': False},
    }
    if kind == 'page':
        base['Font'] = {'Family': None, 'Size': 22, 'Weight': 700,
                        'Color': TITLE_COLOR, 'LetterSpacing': 0,
                        'StrokeColor': None, 'StrokeWidth': 0}
        base['Margin'] = {'X': 0, 'Y': 0}
        base['Padding'] = {'X': 18, 'Y': 0}
    elif kind == 'kpi-label':
        # KPI 标签：符合现代 Dashboard 审美（Linear / Stripe / Vercel 风格）。
        # 12px / 500 / 浅灰（#94A3B8）+ 字距 0.4，与 32px 深黑数字形成"label—value"两级层次。
        # 浅灰 label 主动"退后"，让数字成为正负空间的唯一视觉中心。
        base['Padding'] = {'X': 0, 'Y': 4}
        base['Margin'] = {'X': 0, 'Y': 0}
        base['Font'] = {'Family': None, 'Size': 12, 'Weight': 500,
                        'Color': '#94A3B8', 'LetterSpacing': 0.4,
                        'StrokeColor': None, 'StrokeWidth': 0}
        base['Decoration'] = {'Align': 'left', 'Bold': False, 'Italic': False,
                              'Underline': False, 'LineThrough': False}
    elif kind == 'section':
        base['Font'] = {'Family': None, 'Size': 15, 'Weight': 600,
                        'Color': TITLE_COLOR, 'LetterSpacing': 0,
                        'StrokeColor': None, 'StrokeWidth': 0}
    elif kind == 'card':
        base['Margin'] = {'X': 0, 'Y': 8}
    return base


def _default_chart_block() -> Dict[str, Any]:
    """除 Option 之外的 Chart 通用配置块（前端兜底字段）。

    全部走 null 回退到主题默认，避免硬编码污染主题。
    """
    return {
        'Padding': {'X': 0, 'Y': 0},
        'Background': {'Color': None, 'Opacity': 100},
        'Legend': {'Show': True, 'Position': 'top', 'Orient': 'horizontal', 'Color': None},
        'Tooltip': {'Show': True, 'BackgroundColor': None, 'BorderColor': None, 'FontColor': None},
        'Axis': {
            'X': {'Name': '', 'LabelRotate': 0},
            'Y': {'Name': ''},
        },
    }


# ---------------------------------------------------------------------------
# Chart.Option 派发（按 widget_type）
# ---------------------------------------------------------------------------

def _build_indexcard_option(kpi_metric: Metric,
                            *,
                            value_field: Optional[str] = None,
                            color: str = ACCENT) -> str:
    """KPI Metric → Chart.Option（顶层 key=indexCard）字符串。

    DSL 渲染契约：indexCard 的 valueField 指向 dataset.columns[].columnName，
    valueFormat 仅表达**纯数字**的 numeral 格式串（千分位 / 小数位），
    单位一律通过顶层 valuePrefix / valueSuffix 下发；前端渲染器统一按
    `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}` 拼装。

    历史上曾把单位内联进 valueFormat 做"旧协议兜底"，但 numeral.js 对字面 `%`
    的语义在部分前端实现下会触发 ×100，与 SQL 端已 ×100 的百分比字段叠加导致
    二次放大（例如 25.30 → 2530%）。因此这里 valueFormat 绝不再承载单位。

    数值色由调用方按 KPI_VALUE_COLORS 轮换传入（默认 ACCENT 兼容旧行为）：
    整排 KPI 各取一色，与 KPI 标题（TITLE_COLOR 深灰）拉开对比，
    避免"一片橙色"或"一片黑白灰"的视觉疲劳。

    单位视觉分隔：
      - 非百分号后缀（如 '元' / 'K' / '万'）自动在前面补 U+2009 窄空格，
        改善 `12,345 元` 的可读性；`%` 保持紧贴数字（`50.1%`）符合中文排版习惯。
      - 前缀（如 `¥` / `$`）保持紧贴数字，符合货币符号排版习惯。
    """
    val_field = value_field or _metric_alias(kpi_metric) or _expr_to_field_name(kpi_metric.expr)
    prefix = _normalize_unit(kpi_metric.prefix)
    suffix = _normalize_unit(kpi_metric.suffix)
    is_percent = _is_percent_suffix(suffix)
    # 非 % 的文字后缀（元/万/K/件…）加窄空格分隔；% 保持紧贴。
    if suffix and not is_percent and not suffix.startswith(('\u2009', ' ')):
        suffix = '\u2009' + suffix
    decimals = _format_decimal_places(kpi_metric.format, default=2 if is_percent else 0,
                                      max_decimals=2 if is_percent else None)
    # valueFormat 只表达纯数字格式（千分位/小数位）；单位由 valuePrefix / valueSuffix 承载，
    # 前端渲染器拼装 `${valuePrefix}${numeral(v).format(valueFormat)}${valueSuffix}`。
    val_format = _format_to_numeral(
        kpi_metric.format,
        max_decimals=2 if is_percent else None,
    )
    index_card = {
        'dataBinding': _build_data_binding('indexCard', {'value': val_field}),
        'valueField': val_field,
        'valueFormat': val_format,
        # valueFontSize 走存量兼容：前端契约优先 Chart.Text.Font.Size（emitter 已在
        # KPI 分支写入 24），存量 DSL 走这里的 24 兜底。
        # 字号选型：一行 5~6 张 KPI 时，单卡内宽通常 <180px，长金额数字（10~12 位含千分位）
        # 用 32/36 会溢出被截断（例如 135,702,970 显示为 135,702,97）。降到 24 既保证
        # 长数字完整可读，也与 12px 标题保持 2x 层次比（Linear / Notion / Vercel 通用尺度）。
        'valueFontSize': 24,
        'valueColor': color,
        'showTrend': False,
        # 单位真源：valuePrefix / valueSuffix，前端渲染器统一消费。
        'valuePrefix': prefix,
        'valueSuffix': suffix,
        'decimalPlaces': decimals,
    }
    return json.dumps({'indexCard': index_card}, ensure_ascii=False)


# 依赖笛卡尔坐标系（必须显式声明 xAxis + yAxis 才能 setOption 渲染）的图表族。
# 与 frontend/packages/dashboard-aidash/src/widgets/EChartsWidget.tsx 的 CARTESIAN_TYPES 保持一致。
_CARTESIAN_KINDS = frozenset({'line', 'bar', 'scatter', 'boxplot', 'candlestick', 'heatmap'})


def _ensure_cartesian_axes(kind: str, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """笛卡尔族 cfg 缺 xAxis / yAxis 时补一个最小可工作声明，不覆盖已声明字段。

    动机：ECharts 在 series 落到笛卡尔坐标系（line/bar/scatter/...）时，
    必须能找到 xAxisIndex/yAxisIndex 指向的轴对象，否则会抛
    `xAxis "0" not found` / `yAxis "0" not found`。DSL 自身就该是
    "取出即可 setOption" 的，前端兜底只是安全网。
    """
    # 也兼容 series[].type 是笛卡尔但顶层 kind 不是的情形
    series = cfg.get('series')
    series_has_cartesian = isinstance(series, list) and any(
        isinstance(s, dict) and s.get('type') in _CARTESIAN_KINDS for s in series
    )
    if kind not in _CARTESIAN_KINDS and not series_has_cartesian:
        return cfg

    next_cfg = dict(cfg)  # 浅拷贝即可，xAxis/yAxis 是顶层字段
    if next_cfg.get('xAxis') is None:
        next_cfg['xAxis'] = {'type': 'category'}
    if next_cfg.get('yAxis') is None:
        next_cfg['yAxis'] = {'type': 'value'}
    return next_cfg


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    """历史渲染协议里的 _hexToRgba Python 等价实现。"""
    if not hex_color or not isinstance(hex_color, str):
        return f'rgba(76,132,255,{alpha})'
    if hex_color.startswith('rgb'):
        return hex_color
    h = hex_color.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(ch * 2 for ch in h)
    if len(h) != 6:
        return f'rgba(76,132,255,{alpha})'
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return f'rgba(76,132,255,{alpha})'
    return f'rgba({r},{g},{b},{alpha})'


def _linear_gradient(x: int, y: int, x2: int, y2: int, stops: List[Tuple[float, str]]) -> Dict[str, Any]:
    """ECharts JSON 形式线性渐变，等价于运行态的 echarts.graphic.LinearGradient。"""
    return {
        'type': 'linear',
        'x': x,
        'y': y,
        'x2': x2,
        'y2': y2,
        'colorStops': [{'offset': offset, 'color': color} for offset, color in stops],
        'global': False,
    }


def _as_dict_list(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _ensure_axis_style(axis: Any) -> None:
    """补齐旧协议 axisLabel/axisLine/axisTick/splitLine/nameTextStyle。"""
    if isinstance(axis, list):
        for item in axis:
            _ensure_axis_style(item)
        return
    if not isinstance(axis, dict):
        return
    axis_label = axis.setdefault('axisLabel', {})
    if isinstance(axis_label, dict):
        axis_label.setdefault('color', KPI_LABEL_COLOR)
        axis_label.setdefault('fontSize', 11)
        axis_label.setdefault('margin', 12)
        if axis.get('type') == 'category':
            axis_label.setdefault('overflow', 'truncate')
            axis_label.setdefault('width', 80)
    axis_line = axis.setdefault('axisLine', {})
    if isinstance(axis_line, dict):
        axis_line.setdefault('lineStyle', {'color': '#e2e8f0'})
        if axis.get('type') == 'value':
            axis_line.setdefault('show', False)
    axis_tick = axis.setdefault('axisTick', {})
    if isinstance(axis_tick, dict):
        axis_tick.setdefault('show', False)
    axis.setdefault('splitLine', {'lineStyle': {'type': 'dashed', 'color': 'rgba(15,23,42,0.06)'}})
    if axis.get('name') and not axis.get('nameTextStyle'):
        axis['nameTextStyle'] = {'color': '#94a3b8', 'fontSize': 11}


def _polish_data_zoom(data_zoom: Any, primary: str) -> None:
    """补齐旧协议缩放滑块样式。"""
    for dz in _as_dict_list(data_zoom):
        if dz.get('type') != 'slider':
            continue
        dz.setdefault('borderColor', 'transparent')
        dz.setdefault('backgroundColor', 'rgba(15,23,42,0.02)')
        dz.setdefault('fillerColor', _hex_to_rgba(primary, 0.18))
        dz.setdefault('handleStyle', {
            'color': primary,
            'borderColor': '#fff',
            'borderWidth': 2,
            'shadowColor': 'rgba(15,23,42,0.15)',
            'shadowBlur': 6,
        })
        dz.setdefaul

... [Content truncated, total 163,814 chars] ...