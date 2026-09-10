"""
看板 Runner —— Spec → 看板产物 的唯一执行入口。

LLM 永不触碰本文件。LLM 只编写 kanban_spec_*.py（约 80~120 行声明式），
调用 build_kanban(spec) 即完成全流程：
    1. 取数 SQL 生成 + wedatacli query-sql 执行（lakehouse + OLAP 双路径同入口）
    2. 时间字段解析（spark_safe_* helper，物理消除 H11/H12/H13）
    3. 编译 Spec → SLOT_DATA（19 类图统一处理，物理消除 H9/H10/H14/H15/H16）
    4. 编译 Spec → sqlSlots（同环比 WITH 双层结构，物理消除 H22/H32）
    5. 拼装 subtitle（数据源 + 更新时间；供 DSL page_title.description 使用）
    6. 调 builder.write_kanban_outputs（sqlSlots lint 兜底 H19/H21/H24/H27 等 + 准备 save_meta）
    7. 调 kanban_dsl_emitter.emit_dsl（DSL 落盘 + 一次性写入 kanban_save_params.json 的 HtmlContent/SqlSlots）
    8. 调 builder.update_to_kanban_list（UpdateAiKanBan 写 PREVIEW；三端统一入库权威源）

设计原则：
- **通用**：不假设任何业务领域；任何场景都能写 spec
- **零样板**：业务方零样板代码；DSL 字段直接映射数据/视觉意图
- **三端统一**：入库唯一权威源 = UpdateAiKanBan.HtmlContent(DSL) + UpdateAiKanBan.SqlSlots(Datasets)
- **可逃生**：复杂 SQL 走 raw_sql 旁路，仍走 builder 全 lint
"""

from __future__ import annotations

import os
import re
import sys
import glob
import json
import time
import shlex
import shutil
import hashlib
import subprocess
import tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from kanban_dsl import (
    Spec, Source, Dim, Metric, Chart, Compare,
)

# ============================================================
# 兼容常量：Python 3.11 之前 f-string 表达式内不允许出现反斜杠
# （PEP 701 落地于 3.12）。把所有 SQL 拼接里 ',\n  '.join(...) 通过
# 模块级常量在 f-string 外层使用，保证 runner 在 3.10 / 3.11 沙箱也能直接 import。
# ============================================================
_NL_INDENT = ',\n  '   # SELECT 列分隔（缩进对齐 SELECT 后两空格）

# ============================================================
# 0. 加载 builder（保留兼容，复用全部底层 API）
# ============================================================

def _load_builder() -> Dict[str, Any]:
    """exec 加载 builder.py 到独立命名空间，返回符号表。

    路径解析（first-wins，兼容多种部署布局）：
      1. runner 自身 __file__ 所在目录 —— 最强定位，reference/ 内部相对稳定
      2. CODEBUDDY_PLUGIN_ROOT 下按新→旧顺序探测：
         <root>/scenarios/data-analysis/skills/intelligent-kanban/reference/
         <root>/l3-skill-scenario/intelligent-kanban/reference/
      3. os.getcwd()/reference/ 兜底（本地开发）
    """
    candidates: List[str] = []
    try:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kanban_builder.py'))
    except NameError:
        pass
    plugin_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '').strip()
    if plugin_root:
        candidates.append(os.path.join(
            plugin_root, 'scenarios', 'data-analysis', 'skills',
            'intelligent-kanban', 'reference', 'kanban_builder.py',
        ))
        candidates.append(os.path.join(
            plugin_root, 'l3-skill-scenario', 'intelligent-kanban',
            'reference', 'kanban_builder.py',
        ))
    candidates.append(os.path.join(os.getcwd(), 'reference', 'kanban_builder.py'))

    builder_path = next((p for p in candidates if p and os.path.isfile(p)), '')
    if not builder_path:
        raise FileNotFoundError(
            '[Runner] kanban_builder.py 未找到；尝试路径：\n  - ' + '\n  - '.join(candidates)
        )

    ns: Dict[str, Any] = {'__name__': 'kanban_builder', '__file__': builder_path}
    with open(builder_path, 'r', encoding='utf-8') as f:
        exec(compile(f.read(), builder_path, 'exec'), ns)
    return ns


_B = _load_builder()


# ============================================================
# 1. 取数 SQL 构造 + 执行
# ============================================================

def _build_fetch_sql(src: Source, route_meta: Optional[dict] = None) -> str:
    """生成远端取数 SQL：只做 `SELECT * + LIMIT`，永不下推 WHERE。

    设计契约（与 prefetch_table.py:_build_fetch_sql 对齐）：
      - 表的取数接口端已有行数保护；这里不做 schema 列裁剪、不做分阶段取数
      - spec.source.where 由 DuckDB _kb_src 视图本地过滤，零远端二次开销
      - cache key 固化为 (table, where='', limit)，prefetch 写入与 runner 命中共用同一把 key
      - 外部数据源按方言裁剪表名段数，避免 MySQL/PostgreSQL/GaussDB 收到三段式
    """
    conn_type = (route_meta or {}).get('connection_type') or ''
    query_table = _runner_project_table_name_for_sql(src.table, conn_type)
    return f'SELECT *\n FROM {query_table}\n LIMIT {int(src.limit)}'


# ============================================================
# 1bis. wedatacli query-sql 客户端（lakehouse + OLAP 双路径同入口）
# ────────────────────────────────────────────────────────────
# Runner 不再直接调用工具任务 HTTP 接口；统一走与 search 相同的
# wedatacli 入口。CLI 内部承接提交、轮询、CSV 下载和结果落盘，本处只消费
# 清洗后的 {Status, TaskId, CsvPath, Schema, CostMs}，并从落盘信封补充
# quant 里的真实执行资源字段；JobId 只作排障字段，不能写入 ExecuteResourceId。
# ============================================================

# 【常量对齐锚点】此值必须与 prefetch_table.py:QUERY_SQL_CLI_TIMEOUT_BUFFER 同步。
#   两处均为「Python subprocess.wait 相对 CLI 自身 --timeout 的额外收尾/落盘缓冲」，
#   偏离会导致：值过小 → subprocess 先超时杀 CLI，落盘信封不完整；
#             值过大 → 用户观察到超时后仍需继续等 60s+，体感差。
_QUERY_SQL_CLI_TIMEOUT_BUFFER = 60  # 若调整此值，请同步 prefetch_table.py 端

# 【聚合打印累加器】sqlSlots 方言段数裁剪的命中统计，Step C 结束时统一聚合打印。
#   避免 KPI + 30 chart 场景下 30+ 行「已裁剪 xxx」刷屏。
#   由 _project_slot_sql_table_segments 增量累加、_flush_slot_projection_summary 消费清零。
_slot_projection_stats: Dict[str, int] = {}


def _resolve_runner_plugin_root() -> str:
    """定位 plugin 根目录（含 l0-cli/wedatacli.sh 的目录）。

    与 prefetch_table.py::_resolve_plugin_root 策略一致：
    env 优先 → __file__ 向上爬升找 l0-cli/wedatacli.sh → ../../.. 兜底。
    """
    env_root = os.environ.get('CODEBUDDY_PLUGIN_ROOT', '').strip()
    if env_root and os.path.isdir(env_root):
        return os.path.normpath(env_root)
    try:
        here = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        here = os.path.join(os.getcwd(), 'reference')
    cur = here
    for _ in range(8):
        if os.path.isfile(os.path.join(cur, 'l0-cli', 'wedatacli.sh')):
            return os.path.normpath(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.normpath(os.path.join(here, '..', '..', '..'))


_RUNNER_PLUGIN_ROOT = _resolve_runner_plugin_root()
_RUNNER_WEDATACLI_SH = os.path.join(_RUNNER_PLUGIN_ROOT, 'l0-cli', 'wedatacli.sh')
_RUNNER_WEDATACLI_BIN_CHECKED = False


def _resolve_runner_plugin_env() -> str:
    env_path = os.environ.get('WEDATA_PLUGIN_ENV', '').strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    default_path = os.path.expanduser('~/.wedata/plugin-env')
    if os.path.isfile(default_path):
        return default_path
    return ''


def _runner_workspace_folder_extra_args() -> list:
    """从 env WEDATA_WORKSPACE_FOLDER 读取工作空间目录，非空则返回 ['--workspace_folder', <path>]。

    - DataBuddy 沙箱场景：env 未设置 → 返回 [] → CLI argv 不变。
    - WorkBuddy 连接器场景：intelligent-kanban SKILL.md 已在 Step B/D 前置 export，
      追加到 argv 后满足 WorkBuddy 严格模式（runtimeMode=workbuddy）对 --workspace_folder 的强制要求。
    """
    wf = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if wf:
        return ['--workspace_folder', wf]
    return []


def _ensure_runner_wedatacli_executable() -> None:
    global _RUNNER_WEDATACLI_BIN_CHECKED
    if _RUNNER_WEDATACLI_BIN_CHECKED:
        return
    _RUNNER_WEDATACLI_BIN_CHECKED = True
    try:
        if os.path.isfile(_RUNNER_WEDATACLI_SH) and not os.access(_RUNNER_WEDATACLI_SH, os.X_OK):
            os.chmod(_RUNNER_WEDATACLI_SH, 0o755)
        cli_dir = os.path.dirname(_RUNNER_WEDATACLI_SH)
        if os.path.isdir(cli_dir):
            for name in os.listdir(cli_dir):
                if name.startswith('wedatacli-'):
                    p = os.path.join(cli_dir, name)
                    if os.path.isfile(p) and not os.access(p, os.X_OK):
                        os.chmod(p, 0o755)
    except Exception:
        pass


def _runner_wedatacli_available() -> bool:
    if _resolve_runner_plugin_env():
        return True
    if os.path.isfile(_RUNNER_WEDATACLI_SH):
        return True
    return bool(shutil.which('wedatacli'))


def _runner_wedatacli(args: List[str], timeout: int,
                      input_text: Optional[str] = None) -> subprocess.CompletedProcess:
    if not args:
        raise RuntimeError('[Runner] wedatacli args 为空')
    str_args = [str(a) for a in args] + _runner_workspace_folder_extra_args()
    plugin_env = _resolve_runner_plugin_env()
    if plugin_env:
        quoted_args = ' '.join(shlex.quote(a) for a in str_args)
        cmd = f'. {shlex.quote(plugin_env)} && "$WEDATACLI_PATH" {quoted_args}'
        return subprocess.run(
            cmd, shell=True,
            input=input_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace', timeout=timeout,
        )
    if os.path.isfile(_RUNNER_WEDATACLI_SH):
        _ensure_runner_wedatacli_executable()
        return subprocess.run(
            [_RUNNER_WEDATACLI_SH] + str_args,
            input=input_text,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', errors='replace', timeout=timeout,
        )
    exe = shutil.which('wedatacli') or 'wedatacli'
    return subprocess.run(
        [exe] + str_args,
        input=input_text,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace', timeout=timeout,
    )


def _runner_read_cli_json_stdout(stdout: str) -> Dict[str, Any]:
    stdout = (stdout or '').strip()
    if not stdout:
        raise RuntimeError('[Runner] wedatacli 输出为空')
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find('{')
        end = stdout.rfind('}')
        if start < 0 or end <= start:
            raise RuntimeError(f'[Runner] wedatacli 输出非 JSON: {stdout[:500]}')
        try:
            data = json.loads(stdout[start:end + 1])
        except json.JSONDecodeError as ex:
            raise RuntimeError(f'[Runner] wedatacli 输出非 JSON: {stdout[:500]}') from ex
    if isinstance(data, dict) and data.get('truncated') and data.get('file'):
        file_path = data.get('file') or ''
        if file_path and os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    if not isinstance(data, dict):
        raise RuntimeError(f'[Runner] wedatacli JSON 输出不是对象: {type(data).__name__}')
    return data


_RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID: Optional[str] = None
_RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED = False


def _runner_find_resource_id_in_obj(obj: Any) -> str:
    if not isinstance(obj, dict):
        return ''
    basic = obj.get('BasicInfo') if isinstance(obj.get('BasicInfo'), dict) else {}
    available = obj.get('AvailableStatus')
    if available not in (None, '', 1, '1'):
        return ''
    resource_type = basic.get('ResourceType') if isinstance(basic, dict) else None
    if resource_type not in (None, '', 3, '3'):
        return ''
    for key in ('ResourceId', 'resourceId', 'resource_id'):
        rid = str(basic.get(key) or obj.get(key) or '').strip()
        if rid:
            return rid
    return ''


def _runner_extract_first_analysis_resource_id(data: Any) -> str:
    if not isinstance(data, dict):
        return ''
    response = data.get('Response') if isinstance(data.get('Response'), dict) else data
    payload = response.get('Data') if isinstance(response.get('Data'), dict) else response
    resources = payload.get('Resources') if isinstance(payload, dict) else None
    if not isinstance(resources, list):
        return ''
    for item in resources:
        rid = _runner_find_resource_id_in_obj(item)
        if not rid:
            continue
        basic = item.get('BasicInfo') if isinstance(item, dict) and isinstance(item.get('BasicInfo'), dict) else {}
        exec_available = basic.get('ExecAvailableStatus')
        if exec_available in (None, '', 1, '1'):
            return rid
    return ''


def _runner_default_analysis_resource_id() -> str:
    """获取 lakehouse 默认数据分析计算资源 ID；失败返回空，避免把 JobId 误写为资源。"""
    global _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID, _RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED
    if _RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED:
        return _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID or ''
    _RUNNER_DEFAULT_ANALYSIS_RESOURCE_LOADED = True
    _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID = ''
    if not _runner_wedatacli_available():
        return ''
    workspace_id = os.environ.get('TENCENTCLOUD_WORKSPACE_ID', '').strip()
    if not workspace_id:
        cfg_path = os.path.expanduser('~/.wedata/config.json')
        try:
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f) or {}
            workspace_id = str(cfg.get('defaultWorkspace') or '').strip()
        except Exception:
            workspace_id = ''
    if not workspace_id:
        return ''
    payload = {
        'WorkspaceId': workspace_id,
        'Page': {'PageNumber': 1, 'PageSize': 100},
        'ResourceTypes': [3],
    }
    try:
        result = _runner_wedatacli(
            ['ListComputeResourceOptions', '-'],
            timeout=30,
            input_text=json.dumps(payload, ensure_ascii=False),
        )
        if result.returncode != 0:
            return ''
        data = _runner_read_cli_json_stdout(result.stdout or '')
        _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID = _runner_extract_first_analysis_resource_id(data)
    except Exception:
        _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID = ''
    return _RUNNER_DEFAULT_ANALYSIS_RESOURCE_ID or ''


def _runner_load_query_sql_quant(task_id: str) -> Dict[str, Any]:
    task_id = (task_id or '').strip()
    if not task_id:
        return {}
    path = os.path.expanduser(os.path.join('~', '.wedata', 'query-sql-results', f'{task_id}.json'))
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            env = json.load(f) or {}
        result = env.get('Result') or '{}'
        findings = json.loads(result) if isinstance(result, str) else (result or {})
        quant_raw = findings.get('quant') or '{}'
        quant = json.loads(quant_raw) if isinstance(quant_raw, str) else (quant_raw or {})
        return quant if isinstance(quant, dict) else {}
    except Exception:
        return {}


class _SqlQueryClient:
    """wedatacli query-sql 取数客户端。CLI 内部承接提交、轮询和 CSV 下载。"""

    def __init__(self):
        self.available = _runner_wedatacli_available()

    def query(self, sql: str, sql_type: int, data_source_id: str = '',
              compute_resource: str = '', total_timeout: int = 600) -> Dict[str, Any]:
        if not self.available:
            raise RuntimeError('[Runner] wedatacli 不可用（plugin-env / l0-cli / PATH 均未找到）')
        sql = (sql or '').strip()
        if not sql:
            raise RuntimeError('[Runner] query-sql SQL 为空')
        try:
            cli_timeout = max(1, int(total_timeout or 600))
        except (TypeError, ValueError):
            cli_timeout = 600
        process_timeout = cli_timeout + _QUERY_SQL_CLI_TIMEOUT_BUFFER

        sql_file = ''
        try:
            with tempfile.NamedTemporaryFile(
                'w', encoding='utf-8', suffix='.sql', prefix='kanban_runner_query_', delete=False,
                dir=_resolve_workspace_tmp_dir(),
            ) as f:
                f.write(sql)
                f.write('\n')
                sql_file = f.name

            args = [
                'query-sql',
                '--sql-file', sql_file,
                '--sql-type', str(int(sql_type)),
                '--timeout', f'{cli_timeout}s',
                '--no-progress',
                '--output', 'json',
            ]
            if data_source_id:
                args.extend(['--data-source-id', data_source_id])
            if compute_resource:
                args.extend(['--compute-resource', compute_resource])

            try:
                result = _runner_wedatacli(args, timeout=process_timeout)
            except subprocess.TimeoutExpired as ex:
                raise RuntimeError(f'[Runner] wedatacli query-sql 调用超时（{process_timeout}s）') from ex
        finally:
            if sql_file:
                try:
                    os.unlink(sql_file)
                except OSError:
                    pass

        data = None
        parse_err = None
        if (result.stdout or '').strip():
            try:
                data = _runner_read_cli_json_stdout(result.stdout)
            except Exception as ex:
                parse_err = ex
        if result.returncode != 0:
            msg = ''
            if isinstance(data, dict):
                msg = str(data.get('Message') or data.get('message') or '').strip()
            if not msg:
                msg = (result.stderr or result.stdout or str(parse_err or '')).strip()
            raise RuntimeError(f'[Runner] wedatacli query-sql failed (code={result.returncode}): {msg[:500]}')
        if data is None:
            if parse_err:
                raise parse_err
            raise RuntimeError('[Runner] wedatacli query-sql 未返回 JSON')

        status = str(data.get('Status') or '').upper()
        task_id = str(data.get('TaskId') or '').strip()
        if status != 'SUCCESS':
            msg = str(data.get('Message') or 'query-sql failed without message').strip()
            raise RuntimeError(f'[Runner] wedatacli query-sql failed: task_id={task_id} msg={msg}')
        csv_path = str(data.get('CsvPath') or '').strip()
        if not csv_path or not os.path.isfile(csv_path):
            raise FileNotFoundError(f'[Runner] wedatacli query-sql SUCCESS 但 CsvPath 不存在: {csv_path or "<empty>"}')

        quant = _runner_load_query_sql_quant(task_id)
        job_id = str(quant.get('JobId') or '').strip()
        resource_id = str(
            quant.get('ExecuteResourceId')
            or quant.get('ResourceId')
            or quant.get('ComputeResource')
            or quant.get('ComputeResourceId')
            or compute_resource
            or ''
        ).strip()
        return {
            'task_id': task_id,
            'csv_path': csv_path,
            'schema': data.get('Schema') or [],
            'cost_ms': data.get('CostMs') or 0,
            'job_id': job_id,
            'resource_id': resource_id,
            'quant': quant,
        }


# ── 取数结果 CSV 缓存（按"数据物理形态"复用：table+limit）──
# 设计动机：Spec 重写时，LLM 抄写的字面格式漂移会导致 sha1(SQL) 全部 miss。
#         改为锁定"数据物理形态"后：
#           - cache key = sha1(table+where='' + limit)：列变更 / SQL 空白差异不再 miss
#           - 远端取数统一 SELECT * + LIMIT，不做 schema 列裁剪或分阶段取数
#           - spec.where 由 DuckDB 本地过滤，远端永远只取一次同一物理表样本
# 安全护栏：
#   1) limit 不同 → 严格 miss（不串数据）；表名按精确字面对齐
#   2) TTL 默认 21600s（6 小时），可通过 KANBAN_SQL_CACHE_TTL 调整
#   3) KANBAN_SQL_CACHE_DISABLE=1 一键关闭
#   4) 缓存目录：KANBAN_SQL_CACHE_DIR > WEDATA_WORKSPACE_FOLDER/tmp/wedata_kanban_cache > /tmp/wedata_kanban_cache
def _resolve_sql_cache_dir():
    explicit = os.environ.get('KANBAN_SQL_CACHE_DIR', '').strip()
    if explicit:
        return explicit
    workspace_folder = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        return os.path.join(workspace_folder, 'tmp', 'wedata_kanban_cache')
    return '/tmp/wedata_kanban_cache'


_SQL_CACHE_DIR = _resolve_sql_cache_dir()
_SQL_CACHE_DEFAULT_TTL = 6 * 3600  # 6 小时


def _resolve_workspace_tmp_dir():
    """临时文件目录：WEDATA_WORKSPACE_FOLDER/tmp > 系统默认（None 让 tempfile 自选）。"""
    workspace_folder = os.environ.get('WEDATA_WORKSPACE_FOLDER', '').strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        tmp_dir = os.path.join(workspace_folder, 'tmp')
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            return tmp_dir
        except OSError:
            return None
    return None


def _normalize_table_for_cache_key(table: str) -> str:
    """把表名归一到"最短稳定形态"作为 cache key 输入。

    问题：prefetch 用完整三段式 full_name 写 cache（如 gsdb_catalog.public.t_user），
    runner 端 spec.source.table 由 LLM 按 SKILL.md 规约填写：
      - lakehouse/StarRocks/Doris → 三段式（写盘 = 读取，天然一致）
      - MySQL/PG/GaussDB          → 两段式 db.table（与 prefetch 三段式**不一致**）
    结果：MySQL/PG/GaussDB 场景 100% cache miss → runner 走同步 query-sql 兜底
         → 服务端要 computeResource → 报 `computeResource is blank`。

    修复：统一取"尾两段"（catalog.db.table → db.table；db.table → db.table），
    双端算 hash 前都做同一次归一。SPARK/StarRocks/Doris 三段式经归一裁到两段仍等价
    （二者也因该归一天然一致，零回归）。
    """
    name = (table or '').strip()
    if not name or '.' not in name:
        return name
    parts = [p for p in name.split('.') if p]
    if len(parts) <= 2:
        return name
    return '.'.join(parts[-2:])


def _data_cache_key(table: str, where: str, limit: int) -> str:
    """对"数据物理形态"取 sha1 前 16 位作为缓存 key。

    与 SQL 字面解耦：列序、字面空白差异都不影响 key —— 这是消除 LLM
    重写 spec 导致缓存 miss 的核心。table 归一到尾两段（跨方言双端一致，
    详见 _normalize_table_for_cache_key），where 折叠连续空白，limit 强转 int。
    """
    norm_table = _normalize_table_for_cache_key(table)
    norm_where = re.sub(r'\s+', ' ', (where or '').strip())
    payload = f'{norm_table}||{norm_where}||{int(limit)}'
    return hashlib.sha1(payload.encode('utf-8')).hexdigest()[:16]


def _load_cache_meta(key: str, ttl: int) -> Optional[Dict[str, Any]]:
    """读取并校验单个 CSV 缓存 meta：文件存在 + csv 存在 + 未过期。任何异常 → None。"""
    meta_path = os.path.join(_SQL_CACHE_DIR, f'{key}.meta.json')
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception:
        return None
    csv_path = (meta.get('csv_path') or '').strip()
    created_at = float(meta.get('created_at') or 0)
    if not csv_path or not os.path.isfile(csv_path):
        return None
    if ttl > 0 and (time.time() - created_at) > ttl:
        return None
    return meta


def _load_route_meta(key: str) -> Optional[Dict[str, Any]]:
    """读取 route-only/CSV meta 中的路由字段；不要求 CSV 已落盘。"""
    meta_path = os.path.join(_SQL_CACHE_DIR, f'{key}.meta.json')
    if not os.path.isfile(meta_path):
        return None
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f) or {}
    except Exception:
        return None
    if not isinstance(meta, dict):
        return None
    has_route = any(
        meta.get(k) not in (None, '')
        for k in ('connection_type', 'connection_id', 'sql_type', 'data_source_id')
    )
    return meta if has_route else None


def _route_meta_from_src(src) -> dict:
    """从 prefetch 预写的 meta 中读取路由；失败返回空 dict。"""
    if src is None:
        return {}
    try:
        table = (getattr(src, 'table', '') or '').strip()
        limit = int(getattr(src, 'limit', 0) or 0)
        if not table or limit <= 0:
            return {}
        meta = _load_route_meta(_data_cache_key(table, '', limit))
        if not meta:
            return {}
        return {
            'connection_type': meta.get('connection_type') or '',
            'connection_id': meta.get('connection_id') or meta.get('data_source_id') or '',
            'sql_type': int(meta.get('sql_type') or 1),
            'data_source_id': meta.get('data_source_id') or meta.get('connection_id') or '',
            'job_id': meta.get('job_id') or '',
        }
    except Exception:
        return {}


def _sql_cache_lookup(src) -> Tuple[str, str, dict]:
    """按 spec.source 的物理数据形态查询 prefetch 缓存。

    设计契约（与 _build_fetch_sql 配套）：
      - 远端取数 SQL 永不带 WHERE，cache key 固化为 sha1(table, where='', limit)
      - 取数统一 SELECT *，不做 schema 列裁剪；spec.columns 的列投影在 DuckDB 本地完成
      - 任一异常都视为未命中（缓存绝不能影响主流程）

    返回 (csv_path, resource_id, route_meta)；未命中返回 ('', '', route_meta或{})。
    route_meta 含：connection_type / connection_id / sql_type / job_id（runner miss
    兜底同步取数直接复用，无需重查 wedatacli search 路由信息）。
    """
    route_meta = _route_meta_from_src(src)
    if os.environ.get('KANBAN_SQL_CACHE_DISABLE', '').strip() in ('1', 'true', 'True'):
        return '', '', route_meta
    try:
        ttl = int(os.environ.get('KANBAN_SQL_CACHE_TTL', _SQL_CACHE_DEFAULT_TTL))
    except ValueError:
        ttl = _SQL_CACHE_DEFAULT_TTL
    if ttl <= 0 or not src:
        return '', '', route_meta

    try:
        table = (getattr(src, 'table', '') or '').strip()
        limit = int(getattr(src, 'limit', 0) or 0)
    except Exception:
        return '', '', route_meta
    if not table or limit <= 0:
        return '', '', route_meta

    meta = _load_cache_meta(_data_cache_key(table, '', limit), ttl)
    if not meta:
        return '', '', route_meta
    route_meta = {
        'connection_type': meta.get('connection_type') or route_meta.get('connection_type', ''),
        'connection_id': meta.get('connection_id') or meta.get('data_source_id') or route_meta.get('connection_id', ''),
        'sql_type': int(meta.get('sql_type') or route_meta.get('sql_type') or 1),
        'data_source_id': meta.get('data_source_id') or meta.get('connection_id') or route_meta.get('data_source_id', ''),
        'job_id': meta.get('job_id') or route_meta.get('job_id', ''),
    }
    resource_id = str(meta.get('resource_id') or '').strip()
    if not resource_id and int(route_meta.get('sql_type')

... [Content truncated, total 234,533 chars] ...