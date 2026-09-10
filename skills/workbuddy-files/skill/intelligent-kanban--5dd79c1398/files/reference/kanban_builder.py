"""
看板构建器 — 单一入口文件（合并原 kanban_utils.py + kanban_builder.py）

🛑🛑🛑 P0 强制：本文件为只读模板，禁止任何修改 🛑🛑🛑
本文件是 generate_kanban.py 的公共构建器，通过 exec() 加载使用。
所有 UI 呈现由平台侧读取 DSL（HtmlContent）+ Datasets（SqlSlots）渲染，
所有数据/指标变动通过修改 Spec 后重跑 runner 生成 DSL/Datasets 实现。
绝不允许为了实现某个看板的个性化需求而修改本文件。

解决的核心问题：
1. Python f-string 与 HTML/CSS/JS 花括号冲突 → 使用 string.Template（$variable 占位符）
2. 两个文件分散加载易遗漏 → 合并为单文件，一次 exec 即可

三端统一入库权威链路：
    1. write_kanban_outputs      → 完成 lint 并准备基础 save_meta（主链路不写空 params）
    2. kanban_dsl_emitter.emit_dsl → 一次性写入 kanban_save_params.json（HtmlContent = DSL / SqlSlots = Datasets）
    3. update_to_kanban_list     → UpdateAiKanBan/PREVIEW（读最终 params，PC/H5/embed 三端共用）
       save_to_kanban_list       → SaveAiKanBan（发布态；只带 WorkspaceId + AccessKey）

使用方式（在 Step D 脚本中，沙箱兼容）：
    # 由 kanban_runner 内部解析并 exec 加载 kanban_builder.py；spec 侧无需直接引用本文件。
    # 若需手动定位，参考 _resolve_builder_dir 的多级降级策略：
    #   1) KANBAN_REFERENCE_DIR 显式指定
    #   2) 通过 __file__ 相对定位（reference/ 目录自身）
    #   3) CODEBUDDY_PLUGIN_ROOT 下按新→旧及 WorkBuddy 布局探测
    #   4) os.getcwd()/reference/ 兜底
"""

import os
import sys
import time
import json
import re
import glob
import base64
import gzip
import math
from string import Template
from datetime import datetime, date, time as dt_time


# ===== 沙箱兼容：确定本文件所在目录（用于路径解析） =====
# 通过 exec() 加载时 __file__ 未定义，需要多级降级
def _resolve_builder_dir():
    """确定 kanban_builder.py 所在目录的绝对路径（即 reference/ 目录）。

    优先级（first-wins，兼容 WorkBuddy 与多种 DataBuddy 部署布局）：
    1. KANBAN_REFERENCE_DIR 环境变量（显式指定）
    2. __file__ 所在目录（直接 import / runner exec 加载）
    3. CODEBUDDY_PLUGIN_ROOT 下依次探测新版、旧版和 WorkBuddy connector 布局
    4. os.getcwd()/reference/ 兜底（本地开发）
    """
    ref_dir = os.environ.get('KANBAN_REFERENCE_DIR', '').strip()
    if ref_dir and os.path.isdir(ref_dir):
        return ref_dir

    try:
        here = os.path.dirname(os.path.abspath(__file__))
        if os.path.isdir(here):
            return here
    except NameError:
        pass

    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '').strip()
    if plugin_root:
        for sub in (
            ('scenarios', 'data-analysis', 'skills', 'intelligent-kanban', 'reference'),
            ('l3-skill-scenario', 'intelligent-kanban', 'reference'),
            ('intelligent-kanban', 'reference'),
        ):
            candidate = os.path.join(plugin_root, *sub)
            if os.path.isdir(candidate):
                return candidate

    candidate = os.path.join(os.getcwd(), 'reference')
    if os.path.isdir(candidate):
        return candidate
    return os.getcwd()

_BUILDER_DIR = _resolve_builder_dir()


# ============================================================
# 通用工具函数（原 kanban_utils.py）
# ============================================================

# ===== 安全 JSON 编码器（兼容 Pandas/NumPy 特殊类型） =====

class _SafeJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，自动处理 Pandas/NumPy 等常见不可序列化类型。
    
    覆盖场景：
    - pandas.Timestamp / NaT → ISO 字符串 / null
    - numpy.int64/float64 → Python int/float
    - numpy.ndarray → list
    - numpy.bool_ → Python bool
    - numpy.nan / inf → null
    - datetime.date/datetime → ISO 字符串
    - pandas.NA / NaT → null
    - set → list
    """
    def default(self, obj):
        # 尝试处理 pandas 类型（不强制 import pandas）
        obj_type = type(obj).__name__
        obj_module = type(obj).__module__ or ''
        
        # pandas.NaT / NA 必须在 datetime 之前检测（因为 NaT 是 datetime 子类）
        if obj_type in ('NaTType', 'NAType') or str(obj) in ('NaT', '<NA>'):
            return None
        
        # pandas.Timestamp（也是 datetime 子类，但需要特殊处理）
        if obj_type == 'Timestamp':
            try:
                return obj.isoformat()
            except Exception:
                return str(obj)
        
        # datetime 系列
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, dt_time):
            return obj.isoformat()
        
        # numpy 整数类型
        if 'numpy' in obj_module or obj_type in ('int64', 'int32', 'int16', 'int8', 'uint64', 'uint32', 'uint16', 'uint8'):
            try:
                if hasattr(obj, 'item'):
                    val = obj.item()
                    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                        return None
                    return val
            except (ValueError, OverflowError, TypeError):
                pass
        
        # numpy 浮点类型
        if obj_type in ('float64', 'float32', 'float16'):
            try:
                val = obj.item() if hasattr(obj, 'item') else float(obj)
                if math.isnan(val) or math.isinf(val):
                    return None
                return val
            except (ValueError, OverflowError, TypeError):
                return None
        
        # numpy bool
        if obj_type == 'bool_':
            return bool(obj)
        
        # numpy ndarray
        if obj_type == 'ndarray':
            return obj.tolist()
        
        # pandas Series / DataFrame（极端兜底）
        if obj_type in ('Series', 'DataFrame'):
            return obj.to_dict()
        
        # set → list
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        
        # bytes → base64
        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode('ascii')
        
        # 最终兜底：尝试 str()
        try:
            return str(obj)
        except Exception:
            return None


def _safe_json_dumps(obj, **kwargs):
    """安全的 json.dumps 封装，自动使用 _SafeJSONEncoder 处理特殊类型。
    
    额外处理：
    - float NaN/Inf → null（json.dumps 默认会输出 NaN/Infinity 导致 JS 解析失败）
    """
    kwargs.setdefault('ensure_ascii', False)
    kwargs['cls'] = _SafeJSONEncoder
    result = json.dumps(obj, **kwargs)
    # 后处理：替换 JSON 中的 NaN/Infinity（Python json 模块默认允许这些非标准值）
    result = re.sub(r'\bNaN\b', 'null', result)
    result = re.sub(r'-Infinity\b', 'null', result)
    result = re.sub(r'\bInfinity\b', 'null', result)
    return result


_UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES = 64 * 1024
_UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO = 0.20


def _encode_update_payload(text: str, field_name: str = '') -> str:
    """将 UpdateAiKanBan 大字段编码为 base64；超过阈值时优先使用 gzip+base64。

    服务端仅接受 base64 或 gzip+base64，并在入库前统一还原为明文。
    本地落盘的 dsl/json 文件不受影响，仅请求参数使用压缩后的传输形态。
    """
    raw = text.encode('utf-8')
    raw_b64 = base64.b64encode(raw).decode('ascii')
    if len(raw) < _UPDATE_PAYLOAD_GZIP_THRESHOLD_BYTES:
        return raw_b64

    gz = gzip.compress(raw, compresslevel=6)
    gz_b64 = base64.b64encode(gz).decode('ascii')
    saving_ratio = 1 - (len(gz_b64) / len(raw_b64)) if raw_b64 else 0
    if saving_ratio >= _UPDATE_PAYLOAD_GZIP_MIN_SAVING_RATIO:
        label = field_name or 'UpdateAiKanBan payload'
        print(f'📦 {label} 已启用 gzip+base64: raw={len(raw)}B, base64={len(raw_b64)}B, '
              f'gzipBase64={len(gz_b64)}B, saving={saving_ratio:.1%}')
        return gz_b64
    return raw_b64


# ===== 产物目录 =====

def get_kanban_output_dir():
    """确定看板产物目录，按优先级降级，最终路径必须为 base_dir/.kanban_output。
    
    优先级（选择基础目录）：
    1. 显式环境变量 KANBAN_OUTPUT_DIR（最高优先级，由 plugin-env 注入）
    2. 显式环境变量 WEDATA_WORKSPACE_FOLDER（WorkBuddy session 场景注入）
    3. /workspace（沙箱固定挂载点）
    4. cwd（兜底，本地开发兼容）
    
    无论基础目录是哪个，看板产物都必须放在 base_dir/.kanban_output 下。
    """
    # 1. 显式环境变量（最高优先级，由 plugin-env 注入）
    env_dir = os.environ.get('KANBAN_OUTPUT_DIR')
    if env_dir:
        # 🛡️ 防嵌套：如果环境变量已经以 .kanban_output 结尾，直接使用（不再追加）
        if env_dir.rstrip('/').endswith('.kanban_output'):
            output_dir = env_dir
            os.makedirs(output_dir, exist_ok=True)
            return output_dir
        base_dir = env_dir
    # 2. WEDATA_WORKSPACE_FOLDER（WorkBuddy connector 场景 session 目录）
    elif os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip() and os.path.isdir(os.environ['WEDATA_WORKSPACE_FOLDER'].strip()):
        base_dir = os.environ['WEDATA_WORKSPACE_FOLDER'].strip()
    # 3. /workspace（沙箱固定挂载点）
    elif os.path.isdir('/workspace'):
        base_dir = '/workspace'
    # 4. 兜底：cwd（本地开发兼容）
    else:
        base_dir = os.getcwd()

    # 🛡️ 防嵌套（cwd / base_dir 已位于 .kanban_output 内）：
    # 当 LLM 按 SKILL.md 新模板执行 `python3 ./.kanban_output/kanban_spec.py` 时，
    # spec 本身位于 `<case_sandbox>/.kanban_output/kanban_spec.py`，进程 cwd 仍是
    # case_sandbox（os.getcwd()），此时拼接 base_dir/.kanban_output 是正确的。
    # 但若用户/脚本 cd 进了 .kanban_output 再执行 spec（base_dir 末尾就是
    # .kanban_output），需要直接返回该目录而不是再嵌一层 .kanban_output/.kanban_output。
    if os.path.basename(os.path.normpath(base_dir)) == '.kanban_output':
        output_dir = base_dir
    else:
        # 所有看板产物必须放在 .kanban_output 子目录下
        output_dir = os.path.join(base_dir, '.kanban_output')
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


# ===== DataFrame → SLOT_DATA 安全转换 =====

def df_to_slot_data(df, columns=None):
    """将 Pandas DataFrame 安全转换为 SLOT_DATA 格式（二维列表：[header_row, data_row1, ...]）。
    
    自动处理：
    - Timestamp → ISO 字符串
    - numpy int64/float64 → Python int/float
    - NaN/NaT → None
    - 其他不可序列化类型 → str()
    
    参数:
        df: Pandas DataFrame
        columns: 可选，指定输出的列名列表（默认使用 df.columns）
    
    返回:
        [[col1, col2, ...], [val1, val2, ...], ...]
    
    示例:
        daily_trend = df.groupby('date').agg({'sales': 'sum'}).reset_index()
        SLOT_DATA['daily_trend'] = df_to_slot_data(daily_trend)
    """
    if columns:
        df = df[columns]
    
    header = df.columns.tolist()
    
    # 🔧 记录原始整数列集合，修复 iterrows() 混合 dtype 提升问题
    # 背景：pandas iterrows() 在 DataFrame 包含 int + float 列时，
    # 会将整行 Series 统一提升为 float64，导致整数列丢失精度（如 1 → 1.0）。
    # 解决方案：遍历后对原始整数列做类型恢复。
    _int_dtypes = ('int8', 'int16', 'int32', 'int64',
                   'uint8', 'uint16', 'uint32', 'uint64')
    int_col_set = set(df.select_dtypes(include=list(_int_dtypes)).columns)
    
    # 逐行转换，确保所有值都是 JSON 可序列化的基本类型
    rows = []
    for _, row in df.iterrows():
        converted_row = []
        for col_name, val in row.items():
            converted = _convert_value(val)
            # 恢复被 iterrows dtype 提升破坏的整数列
            if col_name in int_col_set and isinstance(converted, float):
                # 仅当值确实是整数时恢复（NaN 已在 _convert_value 中处理为 None）
                if converted == int(converted):
                    converted = int(converted)
            converted_row.append(converted)
        rows.append(converted_row)
    
    return [header] + rows


def _convert_value(val):
    """将单个值转换为 JSON 安全的 Python 基本类型。"""
    if val is None:
        return None
    
    # 检查 NaN 和 Inf（float NaN/Inf 和 numpy NaN/Inf）
    try:
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
    except (TypeError, ValueError):
        pass
    
    # 检查 pandas NaT / NA
    val_type = type(val).__name__
    if val_type in ('NaTType', 'NAType') or str(val) in ('NaT', '<NA>'):
        return None
    
    # Timestamp → ISO 字符串
    if val_type == 'Timestamp':
        try:
            return val.isoformat()
        except Exception:
            return str(val)
    
    # datetime/date → ISO 字符串
    if isinstance(val, (datetime, date)):
        return val.isoformat()
    
    # numpy 数值类型 → Python 原生类型
    if hasattr(val, 'item'):
        try:
            native = val.item()
            if isinstance(native, float) and (math.isnan(native) or math.isinf(native)):
                return None
            return native
        except (ValueError, OverflowError, TypeError):
            pass
    
    # 基本类型直接返回
    if isinstance(val, (str, int, float, bool)):
        return val
    
    # 兜底：转字符串
    return str(val)


# ===== CSV 路径获取 =====

def find_latest_csv():
    """降级方案：从 /tmp/ 目录查找最新的 wedata_result CSV 文件。"""
    csv_files = glob.glob('/tmp/wedata_result_*.csv')
    if not csv_files:
        raise FileNotFoundError('未找到 CSV 数据文件（目录: /tmp/），请确认取数步骤已执行且 --save_dir 为 /tmp')
    return max(csv_files, key=os.path.getmtime)


class _TimeParseResult:
    """parse_time_column 的防误用代理返回值。

    设计目的：
        parse_time_column 返回布尔值表示"是否解析成功"，但 Agent 生成代码时
        极易写出 `df = parse_time_column(df, col)` 导致 df 被覆盖为 True/False。

    本类让返回值同时满足：
        1. 布尔上下文正常工作：`if parse_time_column(df, col):` → True/False
        2. 误赋值场景安全降级：`df = parse_time_column(df, col)` → df 仍是原 DataFrame
           （代理对象转发所有 DataFrame 属性/方法访问到原始 df）
        3. 比较运算正常：`result == True` / `result is True` 的替代 `bool(result)`

    兼容性保证：
        - `bool(result)` → True/False（与原行为一致）
        - `result.columns` → df.columns（透传 DataFrame 属性）
        - `result.groupby(...)` → df.groupby(...)（透传 DataFrame 方法）
        - `result[col]` → df[col]（透传索引）
        - `result[col] = val` → df[col] = val（透传赋值）
        - `len(result)` → len(df)
        - `iter(result)` → iter(df)
    """

    __slots__ = ('_df', '_is_datetime')

    def __init__(self, df, is_datetime):
        object.__setattr__(self, '_df', df)
        object.__setattr__(self, '_is_datetime', bool(is_datetime))

    # ===== 布尔语义（核心：保持原有 bool 返回值行为） =====
    def __bool__(self):
        return object.__getattribute__(self, '_is_datetime')

    def __eq__(self, other):
        if isinstance(other, bool):
            return object.__getattribute__(self, '_is_datetime') == other
        # 非 bool 比较时转发给 df（如 df == other_df）
        return object.__getattribute__(self, '_df').__eq__(other)

    def __ne__(self, other):
        if isinstance(other, bool):
            return object.__getattribute__(self, '_is_datetime') != other
        return object.__getattribute__(self, '_df').__ne__(other)

    def __hash__(self):
        return hash(object.__getattribute__(self, '_is_datetime'))

    # ===== DataFrame 透传（误赋值场景的安全降级） =====
    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, '_df'), name)

    def __setattr__(self, name, value):
        if name in ('_df', '_is_datetime'):
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, '_df'), name, value)

    def __getitem__(self, key):
        return object.__getattribute__(self, '_df')[key]

    def __setitem__(self, key, value):
        object.__getattribute__(self, '_df')[key] = value

    def __len__(self):
        return len(object.__getattribute__(self, '_df'))

    def __iter__(self):
        return iter(object.__getattribute__(self, '_df'))

    def __contains__(self, item):
        return item in object.__getattribute__(self, '_df')

    def __repr__(self):
        is_dt = object.__getattribute__(self, '_is_datetime')
        return f'_TimeParseResult(is_datetime={is_dt}, df=<DataFrame {len(self)} rows>)'

    def __str__(self):
        return str(object.__getattribute__(self, '_is_datetime'))

    # ===== 支持 int() 转换（兼容 True→1, False→0） =====
    def __int__(self):
        return int(object.__getattribute__(self, '_is_datetime'))

    def __float__(self):
        return float(object.__getattribute__(self, '_is_datetime'))


def parse_time_column(df, col, keep_str_copy=True, min_success_ratio=0.5):
    """安全解析 DataFrame 中的时间字段（B4 P0 强制完整模板）。

    解析策略（按顺序尝试，命中即返回）：
        1. 已是 datetime 类型 → 直接返回
        2. 数值类型（int/float） → 优先按 Unix 秒/毫秒识别（10/13 位数量级判断），避免被自动推断当年份解析
        3. 字符串类型 → pd.to_datetime 自动推断（覆盖 yyyy-MM-dd / yyyy/M/d / MM/dd/yyyy / ISO 8601 / 含时间部分）
        4. 字符串解析覆盖率不足 → 尝试截断时间部分后重试（针对 '2017/10/2 10:56' 等带时间字符串）
        5. 全部失败 → 保留原始 dtype，返回 is_datetime=False

    判定逻辑（关键）：
        以"非空值中成功解析为 datetime 的比例 ≥ min_success_ratio"为成功标准（默认 50%）。
        避免被仅 1 行有效就返回 True 的情况误导（如 99% NaN 字段、混合格式只成功 1 个）。

    副作用（仅当 keep_str_copy=True）：
        在 df 中写入 `<col>_str` 列，保存原始字符串副本（用于兜底从字符串中提取年月）。

    参数:
        df: Pandas DataFrame（原地修改 df[col]）
        col: 时间字段列名
        keep_str_copy: 是否保留 `<col>_str` 原始字符串副本（默认 True）
        min_success_ratio: 解析成功率阈值（0~1，默认 0.5），低于此值视为解析失败

    返回:
        _TimeParseResult: 解析后 df[col] 是否为 datetime 类型（兼容 bool 和 DataFrame 双重语义）
              - bool(result) == True：可使用 .dt 访问器（如 df[col].dt.strftime('%Y-%m')）
              - bool(result) == False：仍为字符串/数值类型，需走兜底分支
              - 误用 `df = parse_time_column(df, col)` 时：df 仍可正常使用（代理透传所有 DataFrame 操作）

    示例:
        # ✅ 正确用法（推荐）
        is_dt = parse_time_column(df, 'dt')
        if is_dt:
            df['month'] = df['dt'].dt.strftime('%Y-%m')
        else:
            df['month'] = df['dt_str'].str.extract(r'(\\d{4}[/-]\\d{1,2})')[0]

        # ✅ 误用也安全（df 不会被破坏）
        df = parse_time_column(df, 'dt')  # df 仍是 DataFrame（代理对象透传）
        if df:  # 等价于 if is_datetime
    """
    try:
        import pandas as pd
    except ImportError:
        return _TimeParseResult(df, False)

    # 已是 datetime 类型，直接返回
    if pd.api.types.is_datetime64_any_dtype(df[col]):
        if keep_str_copy and f'{col}_str' not in df.columns:
            df[f'{col}_str'] = df[col].astype(str)
        return _TimeParseResult(df, True)

    # 保留原始字符串副本（防止覆盖后丢失，B4 关键约束）
    str_col = f'{col}_str'
    if keep_str_copy:
        df[str_col] = df[col].astype(str)
    src = df[str_col] if keep_str_copy else df[col].astype(str)

    # 计算非空数量（覆盖率分母）
    # ⚠️ pandas 3.0+ 中 astype(str) 后 NaN 仍保留为 NaN（不是字符串 'nan'），需先 dropna
    src_nonnull = src.dropna()
    src_clean = src_nonnull[~src_nonnull.astype(str).isin(['nan', 'None', 'NaT', '<NA>', ''])]
    non_null = len(src_clean)
    if non_null == 0:
        # 全空：直接判失败（保持 object dtype，下游可走兜底分支）
        return _TimeParseResult(df, False)

    def _accept(parsed):
        """判定解析结果是否可接受（覆盖率 ≥ min_success_ratio）。"""
        # 仅在原本非空的位置上计算覆盖率，避免被 NULL 拖低
        valid = parsed.loc[src_clean.index].notna().sum()
        return valid >= max(1, int(non_null * min_success_ratio))

    # 策略 1（数值类型优先）：Unix 时间戳（先于自动推断，避免被当作年份解析）
    # is_numeric_dtype 不识别 object 中的纯数字串，所以仅适用于真正的数值列
    if pd.api.types.is_numeric_dtype(df[col]):
        numeric = df[col].astype('float64')
        # 以数量级粗判：10^9 ≤ 秒级 < 10^12；10^12 ≤ 毫秒级 < 10^15
        sample = numeric.dropna().abs()
        if not sample.empty:
            mag = sample.iloc[0]
            unit = 'ms' if mag >= 1e12 else 's'
            ts = pd.to_datetime(numeric, unit=unit, errors='coerce')
            if _accept(ts):
                df[col] = ts
                return _TimeParseResult(df, True)

    # 策略 2：字符串自动推断（covers yyyy-MM-dd / yyyy/M/d / MM/dd/yyyy / 含时间部分 等）
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        parsed = pd.to_datetime(src, errors='coerce')
    if _accept(parsed):
        df[col] = parsed
        return _TimeParseResult(df, True)

    # 策略 3：字符串覆盖率不足 → 截断时间部分（' '/'T' 之前）后重试（针对 '2017/10/2 10:56'）
    # 强制转换为 string 后再用 .str 访问器（防止 src 为数值/混合类型时报错）
    truncated = src.astype(str).str.split(r'[ T]', n=1, regex=True).str[0]
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        parsed2 = pd.to_datetime(truncated, errors='coerce')
    if _accept(parsed2):
        df[col] = parsed2
        return _TimeParseResult(df, True)

    # 策略 4：字符串中可能是纯数字串的 Unix 时间戳
    numeric_str = pd.to_numeric(src, errors='coerce')
    if numeric_str.notna().any():
        sample = numeric_str.dropna().abs()
        if not sample.empty:
            mag = sample.iloc[0]
            unit = 'ms' if mag >= 1e12 else 's'
            ts2 = pd.to_datetime(numeric_str, unit=unit, errors='coerce')
            if _accept(ts2):
                df[col] = ts2
                return _TimeParseResult(df, True)

    # 全部失败：保留原 dtype
    return _TimeParseResult(df, False)


def safe_time_groupby(df, col, granularity='month'):
    """安全的时间字段分组键提取（兼容 datetime / 已是目标粒度的字符串）。

    参数:
        df: Pandas DataFrame
        col: 时间字段列名
        granularity: 'day' | 'month' | 'year'

    返回:
        Series：可直接用作 groupby 键（name 属性已设置为 col，reset_index 后列名正确）
            - 已是目标粒度的字符串（如 'YYYY-MM' 长度 7）→ 原样返回
            - datetime 类型 → strftime 提取
            - object 字符串 → 先 to_datetime 再 strftime

    正确用法:
        # ✅ 作为 groupby 键（推荐）
        df.groupby(safe_time_groupby(df, 'dt', 'month')).agg({'sales': 'sum'})

        # ✅ 赋值给新列后再 groupby
        df['month'] = safe_time_groupby(df, 'dt', 'month')
        monthly = df.groupby('month').agg({'sales': 'sum'}).reset_index()

    常见误用（已防护）:
        # ⚠️ 不要将返回值当作 DataFrame 使用
        # result = safe_time_groupby(df, 'dt', 'month')
        # result.agg(...)  ← 这是 Series，不是 DataFrame，但 .agg() 仍可用于 Series
    """
    try:
        import pandas as pd
    except ImportError:
        return df[col]

    fmt_map = {'day': '%Y-%m-%d', 'month': '%Y-%m', 'year': '%Y'}
    fmt = fmt_map.get(granularity, '%Y-%m-%d')
    expected_len = {'day': 10, 'month': 7, 'year': 4}.get(granularity, 10)

    def _named(series):
        """确保返回的 Series.name = col，使 groupby + reset_index 后列名正确。"""
        series.name = col
        return series

    if pd.api.types.is_datetime64_any_dtype(df[col]):
        return _named(df[col].dt.strftime(fmt))

    if df[col].dtype == 'object':
        # 检查是否已是目标粒度
        sample = df[col].dropna()
        if not sample.empty:
            s = str(sample.iloc[0])
            if len(s) == expected_len:
                return _named(df[col].copy())
        # 转换后提取
        dt = pd.to_datetime(df[col], errors='coerce')
        return _named(dt.dt.strftime(fmt))

    # 数值类型（可能是 Unix 时间戳）
    dt = pd.to_datetime(df[col], unit='s', errors='coerce')
    if dt.notna().any():
        return _named(dt.dt.strftime(fmt))
    return _named(df[col].astype(str))


# ===== SQL 安全日期/时间提取（Spark 3.4+，实测平台 Spark 3.5.3 全部 PASS） =====
#
# 🛑 设计目的：专为 sqlSlots SQL（写入 kanban_save_params.json 的 SqlSlots 字段，
#    看板保存后平台周期性自动刷新执行）设计。Spark 3.0+ 严格 DateTimeParser 对裸 TO_DATE/TO_TIMESTAMP
#    在以下场景抛 INCONSISTENT_BEHAVIOR_CROSS_VERSION.PARSE_DATETIME_BY_NEW_PARSER：
#       - 字段实际值含时间尾巴而 format 只到日期 ❌
#       - format 比字段值更长 ❌
#       - CAST string AS DATE 仅支持 yyyy-MM-dd 标准格式 ❌
#
# ✅ 实现方案（依赖 Spark 3.4+ 的 try_to_timestamp + regexp_replace）：
#       表达式 = try_to_timestamp(regexp_replace(col, '[./]', '-'))
#    一次性覆盖所有主流格式（已在生产平台 Spark 3.5.3 实测 PASS）：
#       yyyy-MM-dd / yyyy/M/d / yyyy.M.d，可补零/不补零，
#       可含 ' ' 或 'T' 分隔的时间部分（HH:mm / HH:mm:ss）
#    'null' / 'NULL' / '' / 'garbage' / 无效月日 → 返回 NULL（不抛异常）
#    与 pandas.to_datetime(errors='coerce') 行为对齐
#
# ⚠️ 平台版本前置：try_to_timestamp 自 Spark 3.4.0 引入。如果目标 Spark 集群 < 3.4，
#    helper 生成的 SQL 会抛 UNRESOLVED_ROUTINE / ROUTINE_NOT_FOUND。
#    建议 Step B0 用 `SELECT version()` 探测确认（腾讯 Wedata 当前为 3.5.3）。
#
# ⚠️ 适用范围：仅当字段类型为 string 时使用。物理类型为 date/timestamp 时不需要这些 helper。
# 🛑 物理类型为 long/bigint/integer（Unix 时间戳数字字段）时**禁止套主入口 helper** ——
#    会静默返回全 NULL 不报错（看板"无数据"）。改用 CAST(FROM_UNIXTIME(col) AS TIMESTAMP)（秒）
#    或 CAST(FROM_UNIXTIME(col/1000) AS TIMESTAMP)（毫秒）。详见 sql_syntax_rules.md 铁律 3。
# ⚠️ B3 取数 SQL（一次性，wedatacli query-sql 跑一次即丢）也不需要 helper —— 失败可立即手工重试。
#    详见 sql_syntax_rules.md 顶部「sqlSlots SQL 生成铁律」。
#
# 🛑 helper 严格单参签名（仅接收列名），不接受 format/time_format 参数 ——
#    try_to_timestamp 默认 format 已自动识别 ISO 系格式，无需 Agent 探测/传参。
#    **唯一例外**：spark_safe_date_format(col, output_format='yyyy-MM') 的第二个参数
#    是输出聚合粒度（'yyyy-MM' 按月 / 'yyyy' 按年 / 'yyyy-MM-dd' 按日），允许且必要。
# =====


def spark_safe_to_timestamp(col):
    """单表达式安全解析 string 时间字段为 timestamp（主入口）。

    核心实现：try_to_timestamp(regexp_replace(col, '[./]', '-')) + 低粒度兜底
        1. regexp_replace([./], -) 把 '/' 和 '.' 一次性规范化为 '-'（→ ISO 8601 形态）
        2. try_to_timestamp 默认 format 兼容 ISO：
              yyyy-MM-dd[ HH:mm[:ss[.SSS]]] / yyyy-MM-ddTHH:mm:ss
              支持补零/不补零（M/d、MM/dd 均可）
           解析失败 → 返回 NULL（不抛异常）
        3. 低粒度兜底（2026-06 增强）：数仓 ADS 层 year_month='2017-01' /
           stat_month='201701' / dt='2017' 等纯年/年月字符串列，Spark
           默认 try_to_timestamp 也会返回 NULL（要求至少 yyyy-MM-dd）。
           用 RLIKE 锁形态后调用 to_timestamp(x, 'yyyy-MM' | 'yyyyMM' | 'yyyy')
           严格解析，月份非法（00 / 13+）/ 完整日期 / unix 数字均不会命中。

    覆盖格式（已实测全部 PASS）：
        '2017/10/10 21:25'      → 2017-10-10 21:25:00
        '2017/10/2'             → 2017-10-02 00:00:00（不补零）
        '2017-10-10'            → 2017-10-10 00:00:00
        '2017-10-10 21:25:30'   → 2017-10-10 21:25:30
        '2017-10-10T21:25:30'   → 2017-10-10 21:25:30（ISO-T）
        '2017/10/2T21:25'       → 2017-10-02 21:25:00（斜杠+T 混合）
        '2017.10.10 21:25'      → 2017-10-10 21:25:00（点分隔）
        '2017-01' / '2017/01' / '2017.01' / '2017-1'  → 2017-01-01 00:00:00（低粒度兜底）
        '201701' (yyyyMM)       → 2017-01-01 00:00:00
        '2017'                  → 2017-01-01 00:00:00

    安全返回 NULL（不报错）：
        'null' / 'NULL' / '' / '   ' / 'garbage' / '2017-13-40' / '2017-2-30' / NULL
        '2017-13' / '2017-00' / '20170145' / 'abcd'（非法月份/8 位非日期数字等）

    不支持（默认返回 NULL，如需启用见 spark_safe_to_timestamp_extended）：
        '20171010' 纯 8 位数字（yyyyMMdd）/ Unix 时间戳

    参数:
        col: SQL 列名（string 类型时间字段，无需 quote）

    返回:
        str: 可直接嵌入 SQL 的 timestamp 表达式

    使用方式（在 generate_kanban.py 的 sql_slots_list 中）:
        ts = spark_safe_to_timestamp('order_purchase_timestamp')
        sql = f\"\"\"SELECT DATE_FORMAT({ts}, 'yyyy-MM') AS mo

... [Content truncated, total 140,067 chars] ...