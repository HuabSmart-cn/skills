#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""增量更新 Database 中的 1–100 条记录。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SELF_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SELF_DIR.parent
for _path in (str(_SELF_DIR), str(_LIB_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import _common  # noqa: E402
from _common import HttpError, error_exit, http_request, safe_print, unwrap_data  # noqa: E402
from _db_types import validate_properties  # noqa: E402

_PATH_BATCH_UPDATE_RECORDS = "/space/api/agent/v1/batch-update-records"


def db_post(url: str, token: str, body: dict, *, timeout: float = 15.0) -> dict:
    """发送 Database POST 请求并解包业务信封。"""
    return unwrap_data(http_request("POST", url, token, body=***REDACTED***


def _read_input(args: argparse.Namespace) -> dict:
    if args.stdin:
        try:
            raw = sys.stdin.read()
            data = json.loads(raw) if raw and raw.strip() else None
        except (OSError, IOError, json.JSONDecodeError):
            return {}
        return data if isinstance(data, dict) else {}

    database_id = (args.database_id or "").strip()
    records_raw = (args.records or "").strip()
    if not database_id or not records_raw:
        return {}
    try:
        records = json.loads(records_raw)
    except json.JSONDecodeError:
        return {}
    return {"database_id": database_id, "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    _common.register_token_arg(parser)
    parser.add_argument("--database-id", dest="database_id", default="")
    parser.add_argument("--records", default="")
    parser.add_argument("--stdin", action="store_true")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        error_exit("参数解析失败")

    token = ***REDACTED***
    data = _read_input(args)
    if not data:
        error_exit("输入 JSON 为空或格式非法")

    database_id = data.get("database_id")
    if not isinstance(database_id, str) or not database_id.strip():
        error_exit("database_id 缺失")

    records = data.get("records")
    if not isinstance(records, list) or not 1 <= len(records) <= 100:
        error_exit("records 必须包含 1–100 个对象")

    validated_records = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            error_exit(f"records[{index}] 必须是对象")

        record_id = record.get("record_id")
        if not isinstance(record_id, str) or not record_id.strip():
            error_exit(f"records[{index}].record_id 缺失")

        properties = validate_properties(record.get("properties"))
        if not properties:
            error_exit(f"records[{index}].properties 校验后为空，无有效字段")

        validated_records.append(
            {"recordId": record_id.strip(), "properties": properties}
        )

    body = {"databaseId": database_id.strip(), "records": validated_records}
    try:
        response = db_post(
            _common.build_url(_PATH_BATCH_UPDATE_RECORDS), token, body, timeout=***REDACTED***
        )
    except HttpError as exc:
        error_exit(f"批量更新记录请求失败: {exc}", traceid=exc.traceid)

    safe_print(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    main()
