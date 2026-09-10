#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database/add_database_field.py —— 向 Database 添加一列（属性）

客户端模式用法（macOS / Linux / Git Bash；沙箱模式见 SKILL.md §调用方式与运行模式）：
    printf '%s' '<token>' | python3 database/add_database_field.py --token-stdin --database-id "<id>" --property '<JSON>'
    printf '%s\n%s' '<token>' '{"database_id":***REDACTED***

行为：
    - 解析 property JSON（{"name": str, "config": PropertyConfig}）
      PropertyConfig 是 oneof（text / number / select / multi_select / date /
      checkbox / url / email / phone_number / image）
    - POST <API_BASE>/space/api/agent/v1/add-field
      body = {"databaseId": "...", "property": {"name": "...", "config": {...}}}
    - 成功 → stdout JSON: {"field_id": "...", "properties": [...]}
    - 失败 → stdout JSON: {"error": "具体错误描述"}，exit 0

约束：
    - 字段名不能与已有字段重复（重复由服务端校验并报错）
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
from _common import HttpError, error_exit, http_request, safe_print, unwrap_data  # noqa: E402
from _db_types import VALID_TYPE_KEYS  # noqa: E402

_PATH_ADD_FIELD = "/space/api/agent/v1/add-field"


def db_post(url: str, token: str, body: dict, *, timeout: float = 15.0) -> dict:
    """Database POST 封装：发请求 + 解包 {code, msg, data} 信封，失败抛 HttpError。"""
    return unwrap_data(http_request("POST", url, token, body=***REDACTED***


def _read_input(args: argparse.Namespace) -> dict:
    """从参数或 stdin 读取输入 JSON。

    --stdin 模式下期望完整的 {"database_id": "...", "property": {...}}
    非 --stdin 模式下从 --database-id 和 --property 参数组合。
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
    if not database_id:
        return {}

    prop_raw = (args.property or "").strip()
    if not prop_raw:
        return {}

    try:
        prop = json.loads(prop_raw)
    except json.JSONDecodeError:
        return {}

    if not isinstance(prop, dict):
        return {}

    return {"database_id": database_id, "property": prop}


def _validate_property(prop) -> dict | str:
    """校验并规范化单个 property 结构。

    property 格式: { "name": str, "config": PropertyConfig }
    返回：dict（成功）或 str（错误信息）。
    """
    if not isinstance(prop, dict):
        return "property 必须是对象格式"

    field_name = prop.get("name", "")
    if not isinstance(field_name, str) or not field_name.strip():
        return "property 缺少有效的 name 字段"

    config = prop.get("config", {})
    if not isinstance(config, dict):
        return f"字段「{field_name.strip()}」的 config 不是有效的对象"

    type_keys = set(config.keys()) & VALID_TYPE_KEYS
    if len(type_keys) != 1:
        return f"字段「{field_name.strip()}」必须且只能包含一种合法类型（{', '.join(sorted(VALID_TYPE_KEYS))}）"

    # 取唯一命中的类型 key
    type_key = next(iter(type_keys))
    return {"name": field_name.strip(), "config": {type_key: config[type_key]}}


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    _common.register_token_arg(parser)
    parser.add_argument("--database-id", dest="database_id", default="")
    parser.add_argument("--property", default="")
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
    if not database_id:
        error_exit("database_id 缺失")

    validated_prop = _validate_property(data.get("property", {}))
    if isinstance(validated_prop, str):
        error_exit(validated_prop)

    body = {
        "databaseId": database_id,
        "property": validated_prop,
    }

    try:
        resp_data = db_post(_common.build_url(_PATH_ADD_FIELD), token, body, timeout=15.0)
    except HttpError as e:
        error_exit(f"添加字段请求失败: {e}")

    field_id = str(resp_data.get("fieldId", "") or resp_data.get("field_id", "")).strip()
    properties = resp_data.get("properties")
    if not field_id:
        error_exit("服务端返回的 field_id 为空")
    if not isinstance(properties, list):
        error_exit("服务端返回的 properties 格式非法")

    output = {
        "field_id": field_id,
        "properties": properties,
    }
    safe_print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
