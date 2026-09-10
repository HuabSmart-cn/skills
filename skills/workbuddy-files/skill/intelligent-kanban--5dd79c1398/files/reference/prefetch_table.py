#!/usr/bin/env python3
"""
看板专用：表名解析（支持中文/英文/三段式）+ 同步拉 schema + 后台预取 CSV。

协议总览
--------
1) 找表（语义召回）：wedatacli search 双通道（wildcard + match）；
   决策成功后透出 (full_name, connection_type, connection_id)，并跑单源闸门。
   三段式快路径：仍调一次 search（按 full_name 精确匹配）补全路由，避免 OLAP
   表被错误默认到 lakehouse SqlType=1。
2) Schema：内联客户端调 wedatacli get columns（fallback get table）—— 与
   lakehouse/OLAP 元数据接口同协议；ThreadPoolExecutor 并行 N 张表，3 张
   表 ~2s（原串行 ~6s）。
3) 取数：wedatacli query-sql CLI 入口，lakehouse 走 SqlType=1，
   OLAP 走 SqlType=3 + DataSourceId；CLI 内部承接提交、轮询和 CSV 下载闭环。

依赖：仅依赖 plugin 自身的 l0-cli/wedatacli.sh（基础设施层）；
      不直接调用 DataclawToolService HTTP 接口，不依赖其它 skill 脚本。

主线程时序：找表 (~1s) → schema 并行 (~2s) → 立即 print JSON 给 LLM；
后台 fork：N 张表整体并行 wedatacli query-sql → 落 /tmp/wedata_kanban_cache/<key>.meta.json，
runner 端通过 (table, where='', limit) 寻址命中。
"""

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

# ═══════════════════════════════════════════════════════════════
# 路径解析
# ═══════════════════════════════════════════════════════════════

def _resolve_plugin_root() -> str:
    """定位 plugin 根目录（含 l0-cli/wedatacli.sh 的目录）。

    优先级：
    1. `CODEBUDDY_PLUGIN_ROOT` 环境变量（若指向真实目录）
    2. 从 __file__ 向上爬升，找到含 `l0-cli/wedatacli.sh` 的最近祖先
       —— 兼容新布局 `<root>/scenarios/data-analysis/skills/intelligent-kanban/reference/`
       与老布局 `<root>/l3-skill-scenario/intelligent-kanban/reference/`
    3. 兜底：`<script_dir>/../../..`（对老布局仍等价）
    """
    env_root = os.environ.get("CODEBUDDY_PLUGIN_ROOT", "").strip()
    if env_root and os.path.isdir(env_root):
        return os.path.normpath(env_root)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    cur = script_dir
    for _ in range(8):  # 最多向上 8 层，防止无限循环
        if os.path.isfile(os.path.join(cur, "l0-cli", "wedatacli.sh")):
            return os.path.normpath(cur)
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.normpath(os.path.join(script_dir, "..", "..", ".."))


PLUGIN_ROOT = _resolve_plugin_root()
# wedatacli.sh 标准位置：<plugin_root>/l0-cli/wedatacli.sh（与 plugin manifest 一致）
WEDATACLI_SH = os.path.join(PLUGIN_ROOT, "l0-cli", "wedatacli.sh")

# 缓存目录与 runner 端 _SQL_CACHE_DIR 字节级一致
# 解析优先级：KANBAN_SQL_CACHE_DIR > WEDATA_WORKSPACE_FOLDER/tmp/wedata_kanban_cache > /tmp/wedata_kanban_cache
def _resolve_sql_cache_dir():
    explicit = os.environ.get("KANBAN_SQL_CACHE_DIR", "").strip()
    if explicit:
        return explicit
    workspace_folder = os.environ.get("WEDATA_WORKSPACE_FOLDER", "").strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        return os.path.join(workspace_folder, "tmp", "wedata_kanban_cache")
    return "/tmp/wedata_kanban_cache"


SQL_CACHE_DIR = _resolve_sql_cache_dir()


def _resolve_workspace_tmp_dir():
    """临时文件目录：WEDATA_WORKSPACE_FOLDER/tmp > 系统默认（None 让 tempfile 自选）。"""
    workspace_folder = os.environ.get("WEDATA_WORKSPACE_FOLDER", "").strip()
    if workspace_folder and os.path.isdir(workspace_folder):
        tmp_dir = os.path.join(workspace_folder, "tmp")
        try:
            os.makedirs(tmp_dir, exist_ok=True)
            return tmp_dir
        except OSError:
            return None
    return None
# 【DEFAULT_LIMIT 契约】此值必须与 kanban_dsl.py:Source.limit 默认值 / SKILL.md DSL 速查
#   / kanban_spec_example.py 中的 limit 参数**四处同步**。
#   看板端 duckdb 视图做聚合 + top_k 硬截断，1w 行的样本对图表精度影响可忽略；
#   服务端 sql.query 预算 5min，10 000 行对绝大多数 lakehouse/OLAP 数据源均可
#   在 2s 内完成，避免踩线全表 500k 触发全量扫描 + COS 上传。
#   如需更大样本，请用户在 spec 里显式覆盖 Source(limit=...)，不要改这里的默认值。
DEFAULT_LIMIT = 10_000
SCHEMA_TIMEOUT = 30        # schema 单表 wedatacli 调用最长等 30s（并行后总耗时 ≈ max(单表)）
FETCH_TOTAL_TIMEOUT = 600  # 单表 wedatacli query-sql 总取数最长 10 分钟
# 【常量对齐锚点】此值必须与 kanban_runner.py:_QUERY_SQL_CLI_TIMEOUT_BUFFER 同步。
#   两处均为「Python subprocess.wait 相对 CLI 自身 --timeout 的额外收尾/落盘缓冲」，
#   偏离会导致：值过小 → subprocess 先超时杀 CLI，落盘信封不完整；
#             值过大 → 用户观察到超时后仍需继续等 60s+，体感差。
QUERY_SQL_CLI_TIMEOUT_BUFFER = 60  # 若调整此值，请同步 kanban_runner.py 端

# resolve 阶段
SEARCH_TIMEOUT = 30
SEARCH_TOP_K = 10

# wedatacli 双通道决策阈值（详见 _decide_one）
MATCH_FLOOR = 2.5
MATCH_RATIO = 2.0
WILDCARD_TOP = 5
DISAMBIGUATION_TOP = 5
EXIT_DISAMBIGUATION = 2
EXIT_NOT_FOUND = 3

# 看板单次最多预取 3 张表（对话体验 + 取数效率双优化）
MAX_TABLES = 3

# 语义召回阶段命中的 fields.columns 缓存（key=full_name），
# schema 阶段作为 fast-path 消费，避免对同一表再多打一次 wedatacli get columns。
# 命中要求：columns 是非空 list，每列至少有 name（type 缺失允许，schema 里降级为空串）。
# 缺失或字段不完整 → schema 阶段回落到原先的 get columns / get table 双路兜底。
_SEARCH_COLUMNS_CACHE: dict = {}


def _extract_columns_from_search_item(it: dict) -> list:
    """从 wedatacli search 返回项抽 columns fast-path 数据。

    支持两种协议：
      1) fields.columns 为 list[{name,type,...}]（新协议，见 t_user 样例）
      2) fields.metadata 为 JSON 字符串，含 columns 数组（老协议兜底）
    输出结构与 _fetch_one_table_schema 对齐。任一列缺 name → 视为脏数据，返回 []。
    """
    if not it:
        return []
    fields = it.get("fields") or {}
    raw_cols = fields.get("columns")
    if not isinstance(raw_cols, list) or not raw_cols:
        meta_str = fields.get("metadata")
        if isinstance(meta_str, str) and meta_str:
            try:
                meta_obj = json.loads(meta_str)
                if isinstance(meta_obj, dict):
                    raw_cols = meta_obj.get("columns")
            except Exception:
                raw_cols = None
    if not isinstance(raw_cols, list) or not raw_cols:
        return []
    out = []
    for c in raw_cols:
        if not isinstance(c, dict):
            return []
        name = str(c.get("name") or c.get("Name") or "").strip()
        if not name:
            return []
        out.append({
            "name": name,
            "type": str(c.get("type") or c.get("Type") or "").strip(),
            "comment": str(c.get("comment") or c.get("Comment") or ""),
            "is_partition": bool(c.get("is_partition") or c.get("IsPartition") or False),
        })
    return out


def _remember_search_columns(full_name: str, it: dict) -> None:
    """将命中项 columns 缓存到 _SEARCH_COLUMNS_CACHE，供 schema 阶段 fast-path 消费。
    幂等：非空覆盖，空值不覆盖已有值。"""
    if not full_name or not it:
        return
    cols = _extract_columns_from_search_item(it)
    if cols:
        _SEARCH_COLUMNS_CACHE[full_name] = cols


# ═══════════════════════════════════════════════════════════════
# 缓存层（与 runner 端 _SQL_CACHE_DIR / _data_cache_key / meta 协议字节对齐）
# ─────────────────────────────────────────────────────────────
# cache key = sha1(table || where='' || limit)；prefetch 永远以 where='' 全量写入。
# runner 端按 spec.source 的 (table, where, limit) 寻址；列子集校验由 runner 做。
# ═══════════════════════════════════════════════════════════════

def _normalize_table_for_cache_key(table: str) -> str:
    """双端 cache key 归一：取尾两段（catalog.db.table → db.table）。

    动机：spec.source.table 由 LLM 按方言规约填写：
      - lakehouse/StarRocks/Doris → 三段式；MySQL/PG/GaussDB → 两段式。
    prefetch 内部一律用完整 full_name（三段式）跑取数，直接算 hash 会与 runner 端
    两段式 key 不一致 → runner 100% miss → 走同步兜底 → 服务端要 computeResource。
    统一裁到尾两段后，双端天然一致，SPARK/StarRocks/Doris 的三段式经归一裁到两段
    仍等价（同 hash 空间），零回归。runner 端已同步落地同一份归一。
    """
    name = (table or "").strip()
    if not name or "." not in name:
        return name
    parts = [p for p in name.split(".") if p]
    if len(parts) <= 2:
        return name
    return ".".join(parts[-2:])


def _data_cache_key(table: str, where: str, limit: int) -> str:
    norm_table = _normalize_table_for_cache_key(table)
    norm_where = re.sub(r"\s+", " ", (where or "").strip())
    payload = f"{norm_table}||{norm_where}||{int(limit)}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _build_fetch_sql(table: str, conn_type: str = "", limit: int = DEFAULT_LIMIT) -> str:
    """整轮看板单表只取一次数 → 固定 `SELECT * FROM <table> LIMIT N`。

    取数端已有限流保护；这里不做 schema 列裁剪、不做分阶段取数。
    外部数据源按方言裁剪表名段数，避免 MySQL/PostgreSQL/GaussDB 收到
    Spark 风格 catalog.schema.table 后报 unknown database/table。
    """
    query_table = _project_table_name_for_sql(table, conn_type)
    return f"SELECT *\n FROM {query_table}\n LIMIT {int(limit)}"


def _cache_already_hit(table: str, limit: int = DEFAULT_LIMIT) -> bool:
    try:
        ttl = int(os.environ.get("KANBAN_SQL_CACHE_TTL", str(6 * 3600)))
    except ValueError:
        ttl = 6 * 3600
    if ttl <= 0 or not table:
        return False
    key = _data_cache_key(table, "", limit)
    meta_path = os.path.join(SQL_CACHE_DIR, f"{key}.meta.json")
    if not os.path.isfile(meta_path):
        return False
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        csv_path = meta.get("csv_path", "")
        created_at = float(meta.get("created_at", 0))
        return bool(csv_path and os.path.isfile(csv_path) and (time.time() - created_at) <= ttl)
    except Exception:
        return False


def _pending_path(table: str, limit: int = DEFAULT_LIMIT) -> str:
    key = _data_cache_key(table, "", limit)
    return os.path.join(SQL_CACHE_DIR, f"{key}.pending.json")


def _write_pending(table: str, limit: int = DEFAULT_LIMIT) -> None:
    if not table:
        return
    try:
        os.makedirs(SQL_CACHE_DIR, exist_ok=True)
        with open(_pending_path(table, limit), "w", encoding="utf-8") as f:
            json.dump({
                "table": table,
                "where": "",
                "limit_used": int(limit),
                "started_at": time.time(),
                "pid": os.getpid(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


def _clear_pending(table: str, limit: int = DEFAULT_LIMIT) -> None:
    try:
        path = _pending_path(table, limit)
        if os.path.isfile(path):
            os.unlink(path)
    except Exception:
        pass


def _store_cache(table: str, csv_path: str, sql: str, limit: int,
                 conn_type: str, conn_id: str, sql_type: int,
                 job_id: str, resource_id: str = "") -> None:
    """写 meta.json：runner 端同时消费 CSV 缓存与路由信息。

    协议字段（runner 端字节级对齐）：
      - resource_id：真实执行资源 ID，供看板 PREVIEW 入库 UpdateAiKanBan.ExecuteResourceId 使用；
        不得用 query-sql JobId/TaskId 兜底，否则 lakehouse 刷新会把任务 ID 当计算资源。
      - connection_type / connection_id：runner 同步 miss 兜底直接复用，无需重查 wedatacli
      - sql_type：1=lakehouse / 3=OLAP，与 wedatacli query-sql 协议一致
      - job_id：query-sql 落盘 quant.JobId（追日志用）
    """
    if not table or not csv_path:
        return
    try:
        os.makedirs(SQL_CACHE_DIR, exist_ok=True)
        key = _data_cache_key(table, "", limit)
        meta_path = os.path.join(SQL_CACHE_DIR, f"{key}.meta.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({
                "csv_path": csv_path,
                "resource_id": resource_id or "",
                "created_at": time.time(),
                "sql_preview": (sql or "").strip()[:200],
                "table": table,
                "where": "",
                "limit_used": int(limit),
                "prefetched": True,
                "route_only": False,
                "connection_type": conn_type or "",
                "connection_id": conn_id or "",
                "sql_type": int(sql_type),
                "job_id": job_id or "",
                "route_updated_at": time.time(),
            }, f, ensure_ascii=False)
    except Exception:
        pass


def _store_route_meta(table: str, conn_type: str, conn_id: str,
                      sql_type: int, data_source_id: str,
                      limit: int = DEFAULT_LIMIT) -> None:
    """先写 route-only meta，保证 runner 即使没等到 CSV 也能正确走 OLAP 同步兜底。

    若已存在可用 CSV meta，则只补充路由字段，不刷新 created_at，避免延长旧数据缓存 TTL。
    """
    if not table:
        return
    try:
        os.makedirs(SQL_CACHE_DIR, exist_ok=True)
        key = _data_cache_key(table, "", limit)
        meta_path = os.path.join(SQL_CACHE_DIR, f"{key}.meta.json")
        meta = {}
        if os.path.isfile(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    old = json.load(f) or {}
                if isinstance(old, dict):
                    meta = old
            except Exception:
                meta = {}

        csv_path = (meta.get("csv_path") or "").strip()
        has_csv = bool(csv_path and os.path.isfile(csv_path))
        if not has_csv:
            meta.update({
                "csv_path": "",
                "resource_id": meta.get("resource_id") or "",
                "created_at": time.time(),
                "sql_preview": _build_fetch_sql(table, conn_type, limit).strip()[:200],
                "table": table,
                "where": "",
                "limit_used": int(limit),
                "prefetched": False,
                "route_only": True,
            })
        else:
            meta["route_only"] = False

        meta.update({
            "table": table,
            "connection_type": conn_type or "",
            "connection_id": conn_id or "",
            "sql_type": int(sql_type),
            "data_source_id": data_source_id or "",
            "route_updated_at": time.time(),
        })
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
    except Exception:
        pass


def _resolve_plugin_env() -> str:
    env_path = os.environ.get("WEDATA_PLUGIN_ENV", "").strip()
    if env_path and os.path.isfile(env_path):
        return env_path
    default_path = os.path.expanduser("~/.wedata/plugin-env")
    if os.path.isfile(default_path):
        return default_path
    return ""


def _workspace_folder_extra_args() -> list:
    """从 env WEDATA_WORKSPACE_FOLDER 读取工作空间目录，非空则返回 ['--workspace_folder', <path>]。

    - DataBuddy 沙箱场景：env 未设置 → 返回 [] → CLI argv 不变。
    - WorkBuddy 连接器场景：intelligent-kanban SKILL.md 已在 Step B/D 前置 export，
      追加到 argv 后满足 WorkBuddy 严格模式（runtimeMode=workbuddy）对 --workspace_folder 的强制要求。
    """
    wf = os.environ.get("WEDATA_WORKSPACE_FOLDER", "").strip()
    if wf:
        return ["--workspace_folder", wf]
    return []


# ═══════════════════════════════════════════════════════════════
# Resolve 阶段：自然语言/中文表名 → catalog.db.table + 路由信息
# ─────────────────────────────────────────────────────────────
# 决策树（强证据优先；弱证据一律不接受）：
#   ① wildcard total==1            → 表名字面唯一精确包含，零歧义直采
#   ② wildcard total>=2            → 字面多解，消歧 wildcard 候选
#   ③ match Top1.score≥FLOOR ∧
#      (同名 ∨ N=1 ∨ ratio≥RATIO)  → BM25 高置信直采
#   ④ match Top1.score≥FLOOR ∧
#      ratio<RATIO                 → 真歧义，消歧 match 候选
#   ⑤ 其它                          → not_found（不接受 fuzzy 兜底）
# ═══════════════════════════════════════════════════════════════

_THREE_SEG_RE = re.compile(r"^[A-Za-z_][\w$]*\.[A-Za-z_][\w$]*\.[A-Za-z_][\w$]*$")
_INTENT_SPLIT_RE = re.compile(r"[、，,]|以及|和|与")


def _is_three_segment(s: str) -> bool:
    return bool(_THREE_SEG_RE.match(s.strip()))


def _split_intents(raw: str) -> list:
    """显式并列分隔符切意图；切完后任一段 <2 字符则整体保留（防误切「共和国」）。"""
    raw = (raw or "").strip()
    if not raw:
        return []
    parts = [p.strip() for p in _INTENT_SPLIT_RE.split(raw) if p and p.strip()]
    if not parts:
        return [raw]
    if any(len(p) < 2 for p in parts):
        return [raw]
    return parts


def _it_field(it: dict, key: str) -> str:
    """wedatacli search 双协议字段读取（嵌套 verbose 优先，回退顶级 compact）。

    特殊键 'table'：compact 协议没有顶级 table 字段，回退顶级 name；
    特殊键 'connection_type' / 'connection_id'：兼容大小写 + 下划线/驼峰。
    """
    if not it:
        return ""
    f = it.get("fields") or {}
    v = f.get(key)
    if v is None or v == "":
        v = it.get(key)
    if (v is None or v == "") and key == "table":
        v = it.get("name")
    if (v is None or v == "") and key in ("connection_type", "connection_id"):
        # 兼容驼峰命名（后端 trpc_client.go 透出 ConnectionType/ConnectionId）
        camel = "ConnectionType" if key == "connection_type" else "ConnectionId"
        v = f.get(camel) or it.get(camel)
    return str(v).strip() if v is not None else ""


def _it_acl_masked(it: dict) -> bool:
    if not it:
        return False
    f = it.get("fields") or {}
    if f.get("_acl_masked"):
        return True
    if it.get("acl_masked"):
        return True
    # compact legacy: catalog/schema 被打码成 "***"（旧协议）
    cat = (it.get("catalog") or "").strip()
    sch = (it.get("schema") or "").strip()
    return cat == "***" or sch == "***"


def _wedatacli_search_one(query: str, mode: str, field: str = "") -> list:
    qspec = {"query": query, "mode": mode}
    if field:
        qspec["field"] = field
    payload = json.dumps(
        {"resource": "table", "queries": [qspec], "top_k": SEARCH_TOP_K},
        ensure_ascii=False,
    )
    wf_suffix = "".join(f" {shlex.quote(a)}" for a in _workspace_folder_extra_args())
    plugin_env = _resolve_plugin_env()
    if plugin_env:
        cmd = (
            f". {shlex.quote(plugin_env)} && "
            f'"$WEDATACLI_PATH" search {shlex.quote(payload)}{wf_suffix}'
        )
    elif os.path.isfile(WEDATACLI_SH):
        _ensure_wedatacli_executable()
        cmd = f"{shlex.quote(WEDATACLI_SH)} search {shlex.quote(payload)}{wf_suffix}"
    else:
        cmd = f"wedatacli search {shlex.quote(payload)}{wf_suffix}"
    try:
        res = subprocess.run(
            cmd, shell=True,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace", timeout=SEARCH_TIMEOUT,
        )
    except Exception:
        return []
    if res.returncode != 0:
        return []
    try:
        data = json.loads(res.stdout)
    except Exception:
        return []
    # wedatacli stdout > 16KB 自动截断为 {truncated, file, ...}，回读文件
    if data.get("truncated") and data.get("file"):
        file_path = data.get("file") or ""
        if file_path and os.path.isfile(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                return []
    items = data.get("items", []) or []
    return [it for it in items if not _it_acl_masked(it)]


def _wedatacli_search(query: str) -> dict:
    """单意图双通道并行（wildcard + match）。两通道独立无依赖，并行节省约 45% 单意图耗时。"""
    with ThreadPoolExecutor(max_workers=2) as ex:
        fut_wc = ex.submit(_wedatacli_search_one, f"*{query}*", "wildcard", "table")
        fut_mc = ex.submit(_wedatacli_search_one, query, "match")
        return {"wildcard": fut_wc.result(), "match": fut_mc.result()}


def _extract_full_name(it: dict) -> str:
    """从 item 抽三段式：full_name → knowledge_id → catalog.schema.table 拼接。"""
    if not it:
        return ""
    full = _it_field(it, "full_name")
    if full and full.count(".") >= 2:
        return full
    kid = _it_field(it, "knowledge_id")
    if kid and kid.count(".") >= 2:
        return kid
    cat = _it_field(it, "catalog")
    sch = _it_field(it, "schema")
    tab = _it_field(it, "table")
    if cat and sch and tab:
        return f"{cat}.{sch}.{tab}"
    return ""


def _extract_route(it: dict) -> tuple:
    """从 item 抽路由信息：(connection_type, connection_id)。

    后端 TableInfoHit 已带 ConnectionType/ConnectionId（knowledge.go:72-73），
    wedatacli search 透传时按 _it_field 双协议读取。未透出 → ('','') → 默认 lakehouse。
    """
    return (
        _it_field(it, "connection_type"),
        _it_field(it, "connection_id"),
    )


def _candidate_brief(it: dict) -> dict:
    comment = (
        _it_field(it, "comment")
        or _it_field(it, "description")
        or _it_field(it, "desc")
    )
    return {
        "full_name": _extract_full_name(it),
        "table": _it_field(it, "table"),
        "schema": _it_field(it, "schema"),
        "catalog": _it_field(it, "catalog"),
        "comment": comment,
        "score": it.get("score", 0),
    }


def _route_fallback_from_match(full_name: str, mc: list) -> tuple:
    """wildcard 通道 field=table 限制了字段返回，可能拿不到 connection_type/connection_id。
    从 match 通道（无 field 限制）按 full_name 精确匹配兜底取路由。"""
    if not full_name or not mc:
        return "", ""
    for it in mc:
        if _extract_full_name(it) == full_name:
            return _extract_route(it)
    return "", ""


def _decide_one(query: str, buckets: dict):
    """单意图双通道决策。返回 (full_name, conn_type, conn_id, ambiguous_candidates, not_found)。
    额外副作用：命中项若带 fields.columns 则写入 _SEARCH_COLUMNS_CACHE，
    schema 阶段可 fast-path 复用，避免重复 get columns。"""
    wc = buckets.get("wildcard", []) or []
    mc = buckets.get("match", []) or []

    # ① wildcard 唯一命中 → 直采（路由缺失时从 match 通道兜底）
    if len(wc) == 1:
        full = _extract_full_name(wc[0])
        if full:
            ct, ci = _extract_route(wc[0])
            if not ct and not ci:
                # wildcard field=table 没透 connection_*，match 通道兜底
                ct, ci = _route_fallback_from_match(full, mc)
            # wildcard field=table 通道通常不带 columns，优先用 match 通道同 full_name 命中项补齐
            _remember_search_columns(full, wc[0])
            for _mit in mc:
                if _extract_full_name(_mit) == full:
                    _remember_search_columns(full, _mit)
                    break
            return full, ct, ci, [], False

    # ② wildcard 多命中 → 消歧
    if len(wc) >= 2:
        return "", "", "", [_candidate_brief(it) for it in wc[:WILDCARD_TOP]], False

    # ③ ④ match 通道判真伪
    if mc:
        s1 = float(mc[0].get("score", 0) or 0)
        if s1 >= MATCH_FLOOR:
            same = [it for it in mc if _it_field(it, "table").lower() == query.lower()]
            if len(same) == 1:
                full = _extract_full_name(same[0])
                if full:
                    ct, ci = _extract_route(same[0])
                    _remember_search_columns(full, same[0])
                    return full, ct, ci, [], False
            elif len(same) >= 2:
                return "", "", "", [_candidate_brief(it) for it in same[:DISAMBIGUATION_TOP]], False

            if len(mc) == 1:
                full = _extract_full_name(mc[0])
                if full:
                    ct, ci = _extract_route(mc[0])
                    _remember_search_columns(full, mc[0])
                    return full, ct, ci, [], False

            s2 = float(mc[1].get("score", 0) or 0)
            if s2 > 0 and s1 / s2 >= MATCH_RATIO:
                full = _extract_full_name(mc[0])
                if full:
                    ct, ci = _extract_route(mc[0])
                    _remember_search_columns(full, mc[0])
                    return full, ct, ci, [], False

            return "", "", "", [_candidate_brief(it) for it in mc[:DISAMBIGUATION_TOP]], False

    # ⑤ not_found
    return "", "", "", [], True


# ═══════════════════════════════════════════════════════════════
# 单源闸门：与 nl2sql_datasource.go::canonicalConnectionType 字节对齐
# ═══════════════════════════════════════════════════════════════

_CANONICAL_MAP = {
    "": "SPARK", "SPARK": "SPARK", "HIVE": "SPARK", "LAKEHOUSE": "SPARK", "DLC": "SPARK",
    "MYSQL": "MYSQL",
    "STARROCKS": "STARROCKS", "STAR_ROCKS": "STARROCKS", "EMR_STARROCKS": "STARROCKS",
    "GAUSSDB": "GAUSSDB", "OPENGAUSS": "GAUSSDB", "OPEN_GAUSS": "GAUSSDB",
    "DORIS": "DORIS", "APACHE_DORIS": "DORIS", "TCHOUSE_D": "DORIS",
    "POSTGRESQL": "POSTGRESQL", "POSTGRES": "POSTGRESQL", "PGSQL": "POSTGRESQL", "PG": "POSTGRESQL",
}


def _canonical_conn_type(raw: str) -> str:
    s = (raw or "").strip().upper().replace("-", "_").replace(" ", "_")
    return _CANONICAL_MAP.get(s, s)  # 未知类型透传，单源闸门会拦下


def _build_route(conn_type: str, conn_id: str) -> dict:
    """与 nl2sql_datasource.go::buildExecutionRoute 对齐。
    返回 {sql_type, data_source_id, mode}。"""
    raw_type = (conn_type or "").strip()
    raw_id = (conn_id or "").strip()
    canon = _canonical_conn_type(raw_type)
    if canon == "SPARK":
        if not raw_type and raw_id:
            raise RuntimeError("empty ConnectionType with non-empty ConnectionId")
        return {"sql_type": 1, "data_source_id": "", "mode": "lakehouse"}
    if canon in ("MYSQL", "STARROCKS", "GAUSSDB", "DORIS", "POSTGRESQL"):
        if not raw_id:
            raise RuntimeError(f"OLAP {canon} 缺 ConnectionId（语义召回未透出）")
        return {"sql_type": 3, "data_source_id": raw_id, "mode": "olap"}
    raise RuntimeError(f"unsupported connection_type: {conn_type}")


def _table_name_segments_for_conn(conn_type: str) -> int:
    """返回该数据源 SQL 可接受的表名最大段数，与 nl2sql_dialect.go 对齐。"""
    canon = _canonical_conn_type(conn_type)
    if canon in ("SPARK", "STARROCKS", "DORIS"):
        return 3
    if canon in ("MYSQL", "GAUSSDB", "POSTGRESQL"):
        return 2
    return 2


def _project_table_name_for_sql(table: str, conn_type: str) -> str:
    """按 OLAP 方言裁剪表名段数；不加引号、不改列，避免引入额外方言差异。"""
    name = (table or "").strip()
    if not name or "." not in name:
        return name
    parts = name.split(".")
    max_segments = _table_name_segments_for_conn(conn_type)
    if max_segments <= 0 or len(parts) <= max_segments:
        return name
    return ".".jo

... [Content truncated, total 59,864 chars] ...