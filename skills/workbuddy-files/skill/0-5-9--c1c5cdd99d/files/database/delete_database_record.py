#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database/delete_database_record.py —— 删除 Database 单条记录

用法（macOS / Linux / Git Bash）：
    echo -n "<token>" | python3 database/delete_database_record.py --token-stdin --database-id "<id>" --record-id "<rid>"
    (printf '%s\n' "<token>"; printf '%s' '{"database_id":***REDACTED***

行为：
    - POST <API_BASE>/space/api/agent/v1/delete-record
      body = {"databaseId": "...", "recordId": "..."}
    - 成功 → stdout: "MINDX_RECORD_DELETED <record_id>"
    - 失败 → stdout JSON: {"error": "具体错误描述"}，exit 0
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
from _common import HttpError, error_exit, http_request, read_token_from_stdin, safe_print, unwrap_data  # noqa: ***REDACTED***

_PATH_DELETE_RECORD = "/space/api/agent/v1/delete-record"


def db_post(url: str, token: str, body: dict, *, timeout: float = 15.0) -> dict:
    """Database POST 封装：发请求 + 解包 {code, msg, data} 信封，失败抛 HttpError。"""
    return unwrap_data(http_request("POST", url, token, body=***REDACTED***


def _read_input(args: argparse.Namespace) -> dict:
    """从参数或 stdin 读取输入 JSON。

    --stdin 模式下期望完整的 {"database_id": "...", "record_id": "..."}
    非 --stdin 模式下从 --database-id 和 --record-id 参数组合。
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
    record_id = (args.record_id or "").strip()
    if not database_id or not record_id:
        return {}
    return {"database_id": database_id, "record_id": record_id}


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--token-stdin", dest=***REDACTED***
    parser.add_argument("--database-id", dest="database_id", default="")
    parser.add_argument("--record-id", dest="record_id", default="")
    parser.add_argument("--stdin", action="store_true")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        error_exit("参数解析失败")

    token = ***REDACTED***
    if args.token_stdin:
        ***REDACTED***
    if not token and not _common.is_sandbox():
        ***REDACTED***

    data = _read_input(args)
    if not data:
        error_exit("输入 JSON 为空或格式非法")

    database_id = (data.get("database_id") or "").strip()
    record_id = (data.get("record_id") or "").strip()
    if not database_id or not record_id:
        error_exit("database_id 或 record_id 缺失")

    body = {
        "databaseId": database_id,
        "recordId": record_id,
    }

    try:
        db_post(_common.build_url(_PATH_DELETE_RECORD), token, body, timeout=***REDACTED***
    except HttpError as e:
        error_exit(f"删除记录请求失败: {e}")

    safe_print(f"MINDX_RECORD_DELETED {record_id}")


if __name__ == "__main__":
    main()
