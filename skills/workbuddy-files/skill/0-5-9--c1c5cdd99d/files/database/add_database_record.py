#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database/add_database_record.py —— 往 Database 插入一条记录

用法（macOS / Linux / Git Bash）：
    echo -n "<token>" | python3 database/add_database_record.py --token-stdin --database-id "<id>" --properties '<JSON>'
    (printf '%s\n' "<token>"; printf '%s' '{"database_id":***REDACTED***

行为：
    - 解析 properties JSON（map<字段名, PropertyValue>）
      PropertyValue 形如 {"text":"..."}/{"number":1}/{"select":"选项文本或ID"}/{"multi_select":["选项文本或ID"]}
    - POST <API_BASE>/space/api/agent/v1/add-record
      body = {"databaseId": "...", "properties": {...}}
    - 成功 → stdout: "MINDX_RECORD_ADDED <record_id>"
    - 失败 → stdout JSON: {"error": "具体错误描述"}，exit 0

参数变更说明：
    - 本接口不再需要 spaceId 参数
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 复用 library/_common.py 的 token / HTTP / 脱敏 / 静默退出约定。
_SELF_DIR = Path(__file__).resolve().parent
_LIB_DIR = _SELF_DIR.parent
for _p in (str(_SELF_DIR), str(_LIB_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _common  # noqa: E402
from _common import HttpError, error_exit, http_request, read_token_from_stdin, safe_print, unwrap_data  # noqa: ***REDACTED***
from _db_types import VALID_TYPE_KEYS  # noqa: E402

_PATH_ADD_RECORD = "/space/api/agent/v1/add-record"


def db_post(url: str, token: str, body: dict, *, timeout: float = 15.0) -> dict:
    """Database POST 封装：发请求 + 解包 {code, msg, data} 信封，失败抛 HttpError。"""
    return unwrap_data(http_request("POST", url, token, body=***REDACTED***


def _read_input(args: argparse.Namespace) -> dict:
    """从参数或 stdin 读取输入 JSON。

    --stdin 模式下期望完整的 {"database_id": "...", "properties": {...}}
    非 --stdin 模式下从 --database-id 和 --properties 参数组合。
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

    # 从命令行参数组合
    database_id = (args.database_id or "").strip()
    if not database_id:
        return {}

    props_raw = (args.properties or "").strip()
    if not props_raw:
        return {}

    try:
        properties = json.loads(props_raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(properties, dict):
        return {}

    return {"database_id": database_id, "properties": properties}


def _validate_properties(properties: dict) -> dict:
    """校验并规范化 properties 结构。

    properties 格式: map<string, PropertyValue>
    PropertyValue 是 oneof（text / number / select / multi_select / date /
    checkbox / url / email / phone_number / image）
    """
    if not isinstance(properties, dict):
        return {}

    validated = {}
    for field_name, value in properties.items():
        if not isinstance(field_name, str) or not field_name.strip():
            continue
        if not isinstance(value, dict):
            continue

        type_keys = set(value.keys()) & VALID_TYPE_KEYS
        if not type_keys:
            continue

        type_key = next(iter(type_keys))
        validated[field_name.strip()] = {type_key: value[type_key]}

    return validated


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--token-stdin", dest=***REDACTED***
    parser.add_argument("--database-id", dest="database_id", default="")
    parser.add_argument("--properties", default="")
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
    if not database_id:
        error_exit("database_id 缺失")

    properties = data.get("properties", {})
    validated_props = _validate_properties(properties)
    if not validated_props:
        error_exit("properties 校验后为空，无有效字段")

    body = {
        "databaseId": database_id,
        "properties": validated_props,
    }

    try:
        resp_data = db_post(_common.build_url(_PATH_ADD_RECORD), token, body, timeout=15.0)
    except HttpError as e:
        error_exit(f"添加记录请求失败: {e}")

    record_id = str(resp_data.get("id", "") or resp_data.get("record_id", "")).strip()
    if not record_id:
        record_id = "unknown"

    safe_print(f"MINDX_RECORD_ADDED {record_id}")


if __name__ == "__main__":
    main()
