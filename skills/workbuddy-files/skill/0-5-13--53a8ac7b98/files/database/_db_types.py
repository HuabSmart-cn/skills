# -*- coding: utf-8 -*-
"""
database/_db_types.py —— database 品类内部共享的字段类型常量
"""

from __future__ import annotations

# Database 列/字段合法类型 key（PropertyConfig / PropertyValue 的 oneof 类型集合）。
# create_database / add_database_field / update_database_field /
# batch_add_database_records / batch_update_database_records
# 共用此白名单校验字段类型。新增列类型时**只改这一处**。
VALID_TYPE_KEYS = frozenset({
    "text", "number", "currency", "select", "multi_select",
    "date", "checkbox", "url", "email", "phone_number",
    "image", "attachment", "person",
})


def validate_properties(properties: object) -> dict:
    """校验并规范化 map<字段名, PropertyValue>；任一字段非法则整条拒绝。"""
    if not isinstance(properties, dict):
        return {}

    validated = {}
    for field_name, value in properties.items():
        if not isinstance(field_name, str) or not field_name.strip():
            return {}
        if not isinstance(value, dict):
            return {}

        type_keys = set(value.keys()) & VALID_TYPE_KEYS
        if len(type_keys) != 1:
            return {}

        type_key = next(iter(type_keys))
        validated[field_name.strip()] = {type_key: value[type_key]}

    return validated
