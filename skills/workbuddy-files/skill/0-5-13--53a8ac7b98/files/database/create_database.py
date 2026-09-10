#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
database/create_database.py —— 创建 Database

客户端模式用法（macOS / Linux / Git Bash；沙箱模式见 SKILL.md §调用方式与运行模式）：
    printf '%s' '<token>' | python3 database/create_database.py --token-stdin --schema '<JSON>'
    printf '%s\n%s' '<token>' '<JSON>' | python3 database/create_database.py --token-stdin --stdin

行为：
    - 解析 schema JSON（含 title、properties，可选 space_id / parent_id）
    - POST <API_BASE>/space/api/agent/v1/create-database
    - 成功 → stdout JSON: {"database_id": "...", "space_id": "...", "property_count": N, "properties": [...]}
    - 失败 → stdout JSON: {"error": "具体错误描述"}，exit 0

参数变更说明：
    - create_database 是 5 个接口中唯一保留 spaceId 的（可为空）
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

_PATH_CREATE_DATABASE = "/space/api/agent/v1/create-database"


def db_post(url: str, token: str, body: dict, *, timeout: float = 15.0) -> dict:
    """Database POST 封装：发请求 + 解包 {code, msg, data} 信封，失败抛 HttpError。"""
    return unwrap_data(http_request("POST", url, token, body=***REDACTED***


def _read_schema(args: argparse.Namespace) -> dict:
    """从参数或 stdin 读取 schema JSON，返回完整 schema dict。"""
    raw = ""
    if args.schema:
        raw = args.schema
    elif args.stdin:
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


def _validate_properties(properties) -> list | str:
    """校验并规范化 properties 结构。

    properties 格式: array，每项为 { "name": str, "config": PropertyConfig }
    返回：list（成功）或 str（错误信息）。
    """
    if isinstance(properties, dict):
        properties = [
            {"name": name, "config": config}
            for name, config in properties.items()
        ]
    if not isinstance(properties, list):
        return "properties 必须是数组或对象格式"

    if not properties:
        return "properties 不能为空"

    validated: list = []
    for i, item in enumerate(properties):
        if not isinstance(item, dict):
            return f"properties[{i}] 不是有效的对象"

        field_name = item.get("name", "")
        if not isinstance(field_name, str) or not field_name.strip():
            return f"properties[{i}] 缺少有效的 name 字段"

        config = item.get("config", {})
        if not isinstance(config, dict):
            return f"字段「{field_name.strip()}」的 config 不是有效的对象"

        # 检查是否有合法的类型 key
        type_keys = set(config.keys()) & VALID_TYPE_KEYS
        if len(type_keys) != 1:
            return f"字段「{field_name.strip()}」必须且只能包含一种合法类型（{', '.join(sorted(VALID_TYPE_KEYS))}）"

        # 取唯一命中的类型 key
        type_key = next(iter(type_keys))
        validated.append({"name": field_name.strip(), "config": {type_key: config[type_key]}})

    return validated


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    _common.register_token_arg(parser)
    parser.add_argument("--schema", default="")
    parser.add_argument("--stdin", action="store_true")
    try:
        args, _ = parser.parse_known_args()
    except SystemExit:
        error_exit("参数解析失败")

    # 读取 token（必须在读 stdin 之前，因为 --token-stdin 从 stdin 读首行）
    token = ***REDACTED***

    schema = _read_schema(args)
    if not schema:
        error_exit("schema JSON 为空或格式非法")

    properties = schema.get("properties", [])
    validated_props = _validate_properties(properties)
    if isinstance(validated_props, str):
        # 校验失败，返回错误信息
        error_exit(validated_props)
    if not validated_props:
        error_exit("properties 校验后为空")

    # 构建请求 body（properties 为 array）
    body: dict = {
        "properties": validated_props,
    }

    # 可选字段
    title = schema.get("title", "")
    if title and isinstance(title, str):
        body["title"] = title.strip()

    # create_database 保留 spaceId（可为空）
    space_id = schema.get("space_id", "")
    if space_id and isinstance(space_id, str):
        body["spaceId"] = space_id.strip()

    parent_id = schema.get("parent_id", "")
    if parent_id and isinstance(parent_id, str):
        body["parentId"] = parent_id.strip()

    try:
        data = db_post(_common.build_url(_PATH_CREATE_DATABASE), token, body, timeout=15.0)
    except HttpError as e:
        error_exit(f"创建数据库请求失败: {e}")

    database_id = str(data.get("id", "")).strip()
    space_id_out = str(data.get("spaceId", data.get("space_id", ""))).strip()
    properties_out = data.get("properties")

    if not database_id:
        error_exit("服务端返回的 database_id 为空")
    if not isinstance(properties_out, list):
        error_exit("服务端返回的 properties 格式非法")

    output = {
        "database_id": database_id,
        "space_id": space_id_out,
        "property_count": len(validated_props),
        "properties": properties_out,
    }
    safe_print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
