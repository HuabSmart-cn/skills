#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database/delete_database_field.py —— 删除 Database 单列（属性）

客户端模式用法（macOS / Linux / Git Bash；沙箱模式见 SKILL.md §调用方式与运行模式）：
    printf '%s' '<token>' | python3 database/delete_database_field.py --token-stdin --database-id "<id>" --field-id "<fid>"
    printf '%s\n%s' '<token>' '{"database_id":***REDACTED***

行为：
    - POST <API_BASE>/space/api/agent/v1/delete-field
      body = {"databaseId": "...", "fieldId": "..."}
    - 成功 → stdout JSON: {"properties": [...]}
    - 失败 → stdout JSON: {"error": "具体错误描述"}，exit 0

约束：
    - 删除后该列的数据将不可恢复
    - field_id 可通过 get_database_schema.py 获取（properties[].id）
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 复用 library/_common.py 的 token / HTTP / 脱敏 / 静默退出约定。
_LIB_DIR = Path(__file__).resolve().parents[1]
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

import _common  # noqa: E402
from _common import HttpError, error_exit, http_request, safe_print, unwrap_data  # noqa: E402

_PATH_DELETE_FIELD = "/space/api/agent/v1/delete-field"


def db_post(url: str, token: str, body: dict, *, timeout: float = 15.0) -> dict:
    """Database POST 封装：发请求 + 解包 {code, msg, data} 信封，失败抛 HttpError。"""
    return unwrap_data(http_request("POST", url, token, body=***REDACTED***


def _read_input(args: argparse.Namespace) -> dict:
    """从参数或 stdin 读取输入 JSON。

    --stdin 模式下期望完整的 {"database_id": "...", "field_id": "..."}
    非 --stdin 模式下从 --database-id 和 --field-id 参数组合。
    """
    if args.stdin:
        try:
            raw = sys.stdin.read()
        except (OSError, IOError):
            return {}
        if not raw or not raw.strip():
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    database_id = (args.database_id or "").strip()
    field_id = (args.field_id or "").strip()
    if not database_id or not field_id:
        return {}
    return {"database_id": database_id, "field_id": field_id}


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    _common.register_token_arg(parser)
    parser.add_argument("--database-id", dest="database_id", default="")
    parser.add_argument("--field-id", dest="field_id", default="")
    parser.add_argument("--stdin", action="store_true")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        error_exit("参数解析失败")

    token = ***REDACTED***

    data = _read_input(args)
    if not data:
        error_exit("输入 JSON 为空或格式非法")

    database_id = (data.get("database_id") or "").strip()
    field_id = (data.get("field_id") or "").strip()
    if not database_id or not field_id:
        error_exit("database_id 或 field_id 缺失")

    body = {
        "databaseId": database_id,
        "fieldId": field_id,
    }

    try:
        resp_data = db_post(_common.build_url(_PATH_DELETE_FIELD), token, body, timeout=15.0)
    except HttpError as e:
        error_exit(f"删除字段请求失败: {e}")

    properties = resp_data.get("properties")
    if not isinstance(properties, list):
        error_exit("服务端返回的 properties 格式非法")

    safe_print(json.dumps({"properties": properties}, ensure_ascii=False))


if __name__ == "__main__":
    main()
