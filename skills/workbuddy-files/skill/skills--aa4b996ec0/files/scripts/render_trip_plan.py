#!/usr/bin/env python3
"""Render an fbt_trip_planner itinerary preview into the WorkBuddy workspace.

样式迁移自 concerto app/btrip/features/tripAgent/myTripPopup（行程内容部分）：
- 750 设计稿的 px 经 postcss-pxtorem(rootValue:75) 生效，这里统一按 ÷2 落到桌面 px；
- --fbt-* CSS 变量取自 app/btrip/style/variable.css，全部转成字面色值；
- 只保留行程渲染，不含地图、换一换、推荐理由、创建申请、导出等交互。
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import os
import re
import secrets
import sys
import tempfile
from datetime import datetime
from pathlib import Path


MAX_PAYLOAD_BYTES = 512 * 1024
START_MARKER = "[TRIP_PLAN_PAYLOAD_V1]"
END_MARKER = "[/TRIP_PLAN_PAYLOAD_V1]"

# 行程类型 → 表头文案，对齐 scheduleCard/index.tsx 的 trip-type 标签
TRIP_TYPE_LABELS = {
    "flight": "✈️ 飞机",
    "train": "🚄 火车",
    "hotel": "🏨 酒店",
    "sub_taxi": "🚖 用车",
    "taxi": "🚖 用车",
    "walk": "🚶 步行",
    "meeting": "📅 会议",
    "meal": "🍽️ 用餐",
}
WEEKDAYS = ("周一", "周二", "周三", "周四", "周五", "周六", "周日")

ICON_LOCAL = (
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z'
    'm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/></svg>'
)
ICON_ATTENTION = (
    '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>'
    "</svg>"
)


# ── 载荷解码（与 render_apply_draft.py 同款契约）─────────────────────

def _payload_digest(payload: dict) -> str:
    canonical_payload = dict(payload)
    canonical_payload.pop("integrity_sha256", None)
    canonical = json.dumps(
        canonical_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _valid_integrity(payload: dict) -> bool:
    expected = str(payload.get("integrity_sha256") or "")
    return bool(expected) and secrets.compare_digest(expected, _payload_digest(payload))


def _decode_payload(encoded: str, *, require_integrity: bool = True) -> dict:
    try:
        raw = base64.b64decode(encoded.encode("ascii"), altchars=b"-_", validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise ValueError("行程预览载荷不是有效的 Base64") from exc
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise ValueError("行程预览载荷超过 512 KiB 限制")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("行程预览载荷不是有效的 UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("行程预览载荷必须是 JSON object")
    if payload.get("version") != 1 or payload.get("kind") != "fbt_trip_plan":
        raise ValueError("不支持的行程预览载荷版本")
    if not isinstance(payload.get("trips"), list):
        raise ValueError("行程预览载荷缺少 trips")
    if require_integrity and not _valid_integrity(payload):
        raise ValueError("行程预览载荷完整性校验失败")
    return payload


def _marker_payloads(text: str):
    cursor = 0
    while True:
        start = text.find(START_MARKER, cursor)
        if start < 0:
            return
        start += len(START_MARKER)
        end = text.find(END_MARKER, start)
        if end < 0:
            return
        encoded = text[start:end].strip()
        if encoded:
            yield encoded
        cursor = end + len(END_MARKER)


def _recover_from_workbuddy_session(conversation_id: str) -> dict | None:
    """Read the exact MCP result instead of trusting model-copied opaque data."""
    session_id = os.environ.get("CODEBUDDY_SESSION_ID") or os.environ.get("CLAUDE_SESSION_ID")
    if not session_id or not conversation_id:
        return None
    projects_root = Path.home() / ".workbuddy" / "projects"
    if not projects_root.is_dir():
        return None
    candidates = sorted(
        projects_root.glob(f"**/{session_id}.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for transcript in candidates:
        try:
            lines = transcript.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in reversed(lines):
            if START_MARKER not in line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "function_call_result":
                continue
            output = record.get("output") or {}
            text = output.get("text") if isinstance(output, dict) else ""
            if not isinstance(text, str):
                continue
            for encoded in _marker_payloads(text):
                try:
                    payload = _decode_payload(encoded, require_integrity=False)
                except ValueError:
                    continue
                if payload.get("integrity_sha256") and not _valid_integrity(payload):
                    continue
                if str(payload.get("conversation_id") or "") == conversation_id:
                    return payload
    return None


def _load_payload(encoded: str) -> dict:
    try:
        return _decode_payload(encoded)
    except ValueError as original_error:
        try:
            copied = _decode_payload(encoded, require_integrity=False)
        except ValueError:
            raise original_error
        recovered = _recover_from_workbuddy_session(str(copied.get("conversation_id") or ""))
        if recovered is None:
            raise original_error
        return recovered


# ── 取值与日期（替代前端的 dayjs / _first_value）────────────────────

def _text(value: object, fallback: str = "") -> str:
    if value in (None, "", [], {}):
        return html.escape(fallback)
    return html.escape(str(value))


def _pick(mapping: object, *keys: str, default: str = "") -> str:
    """按 snake_case/camelCase 别名取第一个非空值。"""
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        value = mapping.get(key)
        if value not in (None, "", [], {}):
            return str(value)
    return default


def _parse_date(value: object):
    try:
        return datetime.strptime(str(value).strip()[:10], "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def _day_diff(start: object, end: object) -> int:
    left, right = _parse_date(start), _parse_date(end)
    if left is None or right is None:
        return 0
    return (right - left).days


def _md(value: object) -> str:
    parsed = _parse_date(value)
    return parsed.strftime("%m/%d") if parsed else str(value or "")


def _weekday(value: object) -> str:
    parsed = _parse_date(value)
    return WEEKDAYS[parsed.weekday()] if parsed else ""


def _session_lookup_report(conversation_id: str) -> list:
    """逐步检查会话记录恢复链路，返回可读诊断行。

    用于确认脚本进程能否拿到 session id 并定位 transcript —— 这是把
    「模型搬运 Base64」换成「只传 conversation_id」的前提。
    """
    lines = []
    env_key = next((k for k in ("CODEBUDDY_SESSION_ID", "CLAUDE_SESSION_ID")
                    if os.environ.get(k)), None)
    session_id = os.environ.get(env_key, "") if env_key else ""
    lines.append(f"[1] session 环境变量 : {env_key or '未设置(CODEBUDDY_SESSION_ID / CLAUDE_SESSION_ID 都为空)'}")
    lines.append(f"[2] session_id       : {session_id or '(空)'}")

    root = Path.home() / ".workbuddy" / "projects"
    lines.append(f"[3] projects 目录    : {root} -> {'存在' if root.is_dir() else '不存在'}")
    if not session_id or not root.is_dir():
        lines.append("[!] 链路中断：拿不到 session_id 或找不到 projects 目录")
        return lines

    files = sorted(root.glob(f"**/{session_id}.jsonl"),
                   key=lambda path: path.stat().st_mtime, reverse=True)
    lines.append(f"[4] 匹配 transcript  : {len(files)} 个")
    if not files:
        lines.append("[!] 链路中断：没有与当前 session_id 同名的 .jsonl")
        return lines

    for transcript in files[:2]:
        try:
            content = transcript.read_text(encoding="utf-8")
        except OSError as exc:
            lines.append(f"    {transcript.name}: 读取失败 {exc.__class__.__name__}")
            continue
        marker_lines = [ln for ln in content.splitlines() if START_MARKER in ln]
        lines.append(f"    {transcript.name}: {len(content):,} 字符, 含标记的行 {len(marker_lines)}")
        hit = decoded = 0
        for ln in marker_lines:
            try:
                record = json.loads(ln)
            except json.JSONDecodeError:
                continue
            if record.get("type") != "function_call_result":
                continue
            output = record.get("output") or {}
            text = output.get("text") if isinstance(output, dict) else ""
            if not isinstance(text, str):
                continue
            for encoded in _marker_payloads(text):
                try:
                    payload = _decode_payload(encoded, require_integrity=False)
                except ValueError:
                    continue
                decoded += 1
                if str(payload.get("conversation_id") or "") == conversation_id:
                    hit += 1
        lines.append(f"      -> function_call_result 中可解码载荷 {decoded} 份，"
                     f"匹配 conversation_id={conversation_id} 的 {hit} 份")
    return lines


def _load_payload_by_conversation(conversation_id: str, verbose: bool) -> dict:
    """只凭 conversation_id 从会话记录取回原始载荷，模型无需搬运 Base64。"""
    report = _session_lookup_report(conversation_id)
    if verbose:
        print("\n".join("  " + line for line in report), file=sys.stderr)
    payload = _recover_from_workbuddy_session(conversation_id)
    if payload is None:
        raise ValueError(
            "未能从当前 WorkBuddy 会话记录中找到该 conversation_id 的行程载荷；"
            "请改用 --payload-base64 传入完整载荷"
        )
    return payload


def _safe_url(value: object) -> str:
    """只放行 http/https，挡掉 javascript: / data: 等伪协议。"""
    url = str(value or "").strip()
    return url if url.lower().startswith(("http://", "https://")) else ""


# ── 卡片内的公共片段 ────────────────────────────────────────────────

def _description(parts) -> str:
    items = [str(p) for p in parts if p not in (None, "", [], {})]
    if not items:
        return ""
    separator = '<i class="line"></i>'
    cells = "".join(
        '<span class="nowrap">%s%s</span>' % (separator if index else "", _text(item))
        for index, item in enumerate(items)
    )
    return '<div class="description">%s</div>' % cells


def _spliter_line(stop_info: str = "", transfer_info: str = "") -> str:
    """起终点之间的连线，纯 CSS（右端三角用 clip-path 画）。"""
    both = bool(stop_info) and bool(transfer_info)
    tags = ""
    if stop_info:
        tags += f'<div class="tag">{"停 " if both else ""}{_text(stop_info)}</div>'
    if both:
        tags += '<div class="center-blank"></div>'
    if transfer_info:
        tags += f'<div class="tag">{"转 " if both else ""}{_text(transfer_info)}</div>'
    return (
        '<span class="spliter-line">'
        '<span class="content"><span class="left-blank"></span><span class="left-line"></span></span>'
        f'<span class="content-wrapper">{tags}</span>'
        '<span class="content"><span class="right-arrow"></span><span class="right-line"></span></span>'
        "</span>"
    )


def _status_tag(trip: dict) -> str:
    """订单状态标签；规划阶段通常为空，与前端 getTagValue 的空值行为一致。"""
    value = _pick(trip, "orderStatusName", "order_status_name")
    return f'<span class="status-tag">{_text(value)}</span>' if value else ""


def _beyond_tag(trip: dict) -> str:
    return '<span class="beyond-rules-tag">超规</span>' if trip.get("beyond_rules") else ""


def _address(address: object) -> str:
    if not address:
        return ""
    return f'<div class="row address">{ICON_LOCAL}<span>{_text(address)}</span></div>'


def _booking(trip: dict, label: str) -> str:
    """可预订资源的名称：有链接则渲染为橙色下划线链接，否则纯文本。"""
    url = _safe_url(trip.get("booking_url"))
    if not url:
        return f'<span class="resource">{_text(label)}</span>'
    return (
        f'<a class="highlight-button" href="{html.escape(url, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{_text(label)}</a>'
    )


def _notice(trip: dict) -> str:
    """alertMessage 优先级高于 tipMessage，与前端一致。"""
    alert = _pick(trip, "alertMessage", "alert_message")
    tip = _pick(trip, "tipMessage", "tip_message")
    value, kind = (alert, "alert") if alert else (tip, "tip")
    if not value:
        return ""
    return f'<div class="notice {kind}">{ICON_ATTENTION}<span>{_text(value)}</span></div>'


# ── 各类行程卡片（迁移自 scheduleCard/common.tsx）────────────────────

def _card_flight(trip: dict) -> str:
    detail = trip.get("trip_detail") or {}
    segments = detail.get("segment_list") or []
    is_transfer = bool(segments)
    first_segment = segments[0] if is_transfer else {}
    transfer_vo = first_segment.get("segment_transfer_vo") or {}
    transit_vo = first_segment.get("segment_transit_vo") or {}

    fuel = _pick(trip, "fuelTax_airportTax", "fuel_tax_airport_tax")
    price = f'¥{_pick(trip, "estimated_price")}' + (f"+¥{fuel}(机建燃油)" if fuel else "")

    if is_transfer:
        transit = _pick(transit_vo, "city_name")
        transfer = _pick(transfer_vo, "city_name")
        parts = [
            f'经停 {_pick(transit_vo, "stay_time")}'.strip() if transit else "",
            f'转 {_pick(transfer_vo, "stay_time")}'.strip() if transfer else "",
            _pick(trip, "type_size"), _pick(trip, "meal"), price,
        ]
    else:
        parts = [
            _pick(detail, "airline_name"),
            "经停" if _pick(detail, "stop_info") else "",
            _pick(trip, "type_size"), _pick(trip, "meal"), price,
        ]

    flight_no = _pick(trip, "flight_no", "flightNo") or _pick(detail, "flight_no", "flightNo")
    head = (
        f'<span class="nowrap">{_text(_pick(trip, "departure_airport", "departure_city"))}'
        + _spliter_line(_pick(detail, "stop_info"), _pick(transfer_vo, "city_name"))
        + _text(_pick(trip, "destination_airport", "destination_city"))
    )
    if not is_transfer and flight_no:
        head += '<i class="line"></i>' + _booking(trip, flight_no)
    head += "</span>"

    # 中转航段：每段单独一行展示航司与航班号（航司 logo 因 CSP 去掉，只留名称）
    legs = ""
    if is_transfer:
        cells = "".join(
            f'<span class="plane-info">{_text(_pick(seg, "airline_name"))} '
            + _booking(trip, _pick(seg, "flight_no"))
            + "</span>"
            for seg in segments
        )
        legs = f'<div class="row">{cells}</div>'

    return (
        '<div class="trip-card">'
        f'<div class="wrap-row center-row">{head}{_status_tag(trip)}{_beyond_tag(trip)}</div>'
        f"{legs}"
        f'<div class="row">{_description(parts)}</div>'
        "</div>"
    )


def _card_train(trip: dict) -> str:
    detail = trip.get("trip_detail") or {}
    train_no = _pick(trip, "train_no", "trainNo") or _pick(detail, "train_code", "train_no")
    parts = [
        _pick(trip, "seat_type") or _pick(detail, "seat_type"),
        f'¥{_pick(trip, "estimated_price")}',
    ]
    start = _pick(trip, "departure_station") or _pick(detail, "from_station_name")
    end = _pick(trip, "destination_station") or _pick(detail, "to_station_name")
    head = (
        f'<span class="nowrap">{_text(start)}{_spliter_line()}{_text(end)}'
        '<i class="line"></i>' + _booking(trip, train_no) + "</span>"
    )
    return (
        '<div class="trip-card">'
        f'<div class="wrap-row center-row">{head}{_status_tag(trip)}{_beyond_tag(trip)}</div>'
        f'<div class="row">{_description(parts)}</div>'
        "</div>"
    )


def _card_hotel(trip: dict) -> str:
    end_date = _pick(trip, "trip_end_date_show") or _pick(trip, "trip_end_date")
    start_date = _pick(trip, "trip_start_date")
    nights = _day_diff(start_date, end_date)
    score = _pick(trip, "commentScore", "comment_score")
    price = _pick(trip, "estimated_price")
    parts = [
        f"{_md(start_date)}-{_md(end_date)} 共{nights}晚" if start_date else "",
        f"{score}分" if score else "",
        f"¥{price}" if price else "",
    ]
    name = _pick(trip, "hotel_name", "hotelName") or "酒店"
    return (
        '<div class="trip-card">'
        f'<div class="wrap-row center-row">{_booking(trip, name)}'
        f'{_status_tag(trip)}{_beyond_tag(trip)}</div>'
        f'{_address(_pick(trip, "address"))}'
        f'<div class="row">{_description(parts)}</div>'
        "</div>"
    )


def _card_taxi(trip: dict) -> str:
    toll = _pick(trip, "estimated_price_tolls")
    price = f'¥{_pick(trip, "estimated_price")}' + (f"+¥{toll}(过路费)" if toll else "")
    parts = [_pick(trip, "estimated_distance"), price]
    head = (
        _text(_pick(trip, "trip_start_detailed_address"))
        + _spliter_line()
        + _text(_pick(trip, "trip_end_detailed_address"))
    )
    return (
        '<div class="trip-card">'
        f'<div class="wrap-row">{head}{_beyond_tag(trip)}</div>'
        f'<div class="row">{_description(parts)}</div>'
        "</div>"
    )


def _card_walk(trip: dict) -> str:
    head = (
        _text(_pick(trip, "trip_start_detailed_address"))
        + _spliter_line()
        + _text(_pick(trip, "trip_end_detailed_address"))
    )
    return (
        '<div class="trip-card">'
        f'<div class="wrap-row">{head}</div>'
        f'<div class="row">{_description([_pick(trip, "estimated_distance")])}</div>'
        "</div>"
    )


def _card_meeting(trip: dict) -> str:
    return (
        '<div class="trip-card">'
        f'<div class="wrap-row">{_text(_pick(trip, "title"), "会议")}</div>'
        f'{_address(_pick(trip, "address"))}'
        "</div>"
    )


def _card_meal(trip: dict) -> str:
    score = _pick(trip, "commentScore", "comment_score")
    parts = [
        _pick(trip, "type"),
        f'{score}分 {_pick(trip, "evaluate")}'.strip() if score else "",
        f'人均¥{_pick(trip, "estimated_price", default="-")}',
    ]
    return (
        '<div class="trip-card">'
        f'<div class="wrap-row">{_text(_pick(trip, "name"), "餐厅")}</div>'
        f'{_address(_pick(trip, "address"))}'
        f'<div class="row">{_description(parts)}</div>'
        "</div>"
    )


def _card_empty(trip: dict) -> str:
    start = _pick(trip, "trip_start_detailed_address")
    end = _pick(trip, "trip_end_detailed_address")
    title = (
        f'<span class="title-text">{_text(start)} → {_text(end)}</span>'
        if start and end else ""
    )
    summary = _pick(trip, "summary")
    return (
        '<div class="empty-card">'
        f'<div class="title-row">{title}</div>'
        f'<div class="description-row">{_text(summary)}</div>'
        "</div>"
    )


CARD_RENDERERS = {
    "flight": _card_flight,
    "train": _card_train,
    "hotel": _card_hotel,
    "sub_taxi": _card_taxi,
    "taxi": _card_taxi,
    "walk": _card_walk,
    "meeting": _card_meeting,
    "meal": _card_meal,
    "empty": _card_empty,
}


# ── 时间轴与日期分组（迁移自 scheduleCard/index.tsx + index.tsx）──────

def _time_range(trip: dict) -> str:
    start = _pick(trip, "trip_start_time_of_arrive")
    end = _pick(trip, "trip_end_time_of_arrive")
    if not start and not end:
        return ""
    diff = _day_diff(_pick(trip, "trip_start_date"), _pick(trip, "trip_end_date"))
    span = f'<span class="diff-date">+{diff}</span>' if diff > 0 else ""
    return f'<span class="time-range">{_text(start)}-{_text(end)}{span}</span>'


def _schedule_item(trip: dict) -> str:
    trip_type = str(trip.get("trip_type") or "")
    renderer = CARD_RENDERERS.get(trip_type)
    if renderer is None:
        return ""

    duration = _pick(trip, "estimated_time")
    time_cell = _time_range(trip)
    if time_cell and duration:
        time_cell += f'<i class="line"></i>{_text(duration)}'
    elif not time_cell:
        time_cell = f'<span class="time-range">{_text(duration)}</span>'

    label = TRIP_TYPE_LABELS.get(trip_type, "")
    # 酒店没有时段，前端把类型标签直接放在左侧时间位，右侧留空
    if trip_type == "hotel":
        header = f'<div class="time-and-way">{_text(label)}</div>'
    else:
        header = (
            f'<div class="time-and-way">{time_cell}</div>'
            f'<div class="header-right"><span class="trip-type">{_text(label)}</span></div>'
        )
    return (
        '<div class="schedule-container">'
        f'<div class="header">{header}</div>'
        f"{renderer(trip)}"
        f"{_notice(trip)}"
        "</div>"
    )


def _group_by_date(trips: list) -> list:
    """按 trip_start_date 分组为 Day 1/2/…，酒店排在当天末尾（与前端排序一致）。"""
    groups: dict[str, dict] = {}
    last_date = ""
    for trip in trips:
        if not isinstance(trip, dict):
            continue
        # meal 等类型只有时刻没有日期，归入上一段所在的那天
        last_date = _pick(trip, "trip_start_date") or last_date
        date_key = last_date or "-"
        group = groups.setdefault(date_key, {"date": date_key, "trips": [], "cities": []})
        group["trips"].append(trip)
        for city in trip.get("trip_cities") or []:
            if city and city not in group["cities"]:
                group["cities"].append(str(city))
    ordered = sorted(groups.values(), key=lambda g: g["date"])
    for group in ordered:
        group["trips"].sort(key=lambda t: t.get("trip_type") == "hotel")
    return ordered


def _date_head(start: str, end: str) -> str:
    """概览首行：起止日期各带一个星期标签。"""
    head = f'{_md(start)}<span class="week-tag">{_weekday(start)}</span>'
    if end and end != start:
        head += f' - {_md(end)}<span class="week-tag">{_weekday(end)}</span>'
    return head


def _overview_from_total_trip(total_trip: dict) -> str:
    """概览优先用后端汇总对象，口径与 App「我的行程」一致。

    对齐 concerto myTripPopup/index.tsx 的 scheduleSummary：日期取 total_trip 的
    起止日，城市取 destination_city_short（往返路径，不去重），总价取
    total_estimated_price 原值（App 也不做千分位处理）。
    """
    start = _pick(total_trip, "trip_start_date")
    end = _pick(total_trip, "trip_end_date")
    city = _pick(total_trip, "destination_city_short")
    cost = _pick(total_trip, "total_estimated_price")
    if not (start and cost):
        return ""
    return (
        '<div class="overview">'
        f'<div class="date">{_date_head(start, end)}</div>'
        f'<div class="city">{_text(city)}</div>'
        f'<div class="cost">预估总成本：¥{_text(cost)}</div>'
        "</div>"
    )


def _overview_from_trips(trips: list, groups: list) -> str:
    """后端未下发 total_trip 时的回退：日期取首尾天，城市去重，总价累加。"""
    dates = [g["date"] for g in groups if g["date"] != "-"]
    if not dates:
        return ""

    cities = []
    for group in groups:
        for city in group["cities"]:
            if city not in cities:
                cities.append(city)

    total = 0.0
    for trip in trips:
        try:
            total += float(_pick(trip, "estimated_price") or 0)
        except ValueError:
            continue
    cost = f"{total:,.0f}" if total == int(total) else f"{total:,.2f}"

    return (
        '<div class="overview">'
        f'<div class="date">{_date_head(dates[0], dates[-1])}</div>'
        f'<div class="city">{_text("-".join(cities))}</div>'
        f'<div class="cost">预估总成本：¥{cost}</div>'
        "</div>"
    )


def _overview(trips: list, groups: list, total_trip: dict) -> str:
    return _overview_from_total_trip(total_trip) or _overview_from_trips(trips, groups)


# ── 页面样式（750 设计稿 ÷2；--fbt-* 变量已展开为字面色值）───────────

CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fff;color:#222;
     font:12px/1.5 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}
main{max-width:560px;margin:0 auto;padding:20px 16px 32px}
.icon{width:12px;height:12px;fill:currentColor;flex-shrink:0;transform:translateY(1px)}
.nowrap{white-space:nowrap}

/* 概览 */
.overview{color:#222;margin-bottom:24px}
.overview .date{display:flex;align-items:center;margin-bottom:4px;
                font-size:24px;font-weight:bold;line-height:30px;white-space:nowrap}
.overview .week-tag{display:inline-block;padding:0 4px;margin-left:4px;
                    font-size:14px;font-weight:400;line-height:1.5;color:#222;
                    border:1px solid #999;border-radius:2px;white-space:nowrap}
.overview .city{margin-bottom:4px;font-size:16px;font-weight:500;line-height:24px}
.overview .cost{font-size:14px;font-weight:400;line-height:22px}

/* 按天分组 */
.schedule{display:flex;flex-direction:column;margin-bottom:24px;color:#222}
.schedule:last-of-type{margin-bottom:0}
.schedule+.schedule{border-top:1px dashed #e8e8e8;padding-top:16px;margin-top:18px}
.schedule>.title{display:flex;justify-content:space-between;gap:12px;margin-bottom:18px;
                 font-size:16px;font-weight:600;line-height:26px;white-space:nowrap}

/* 时间轴 */
.schedule-container{position:relative;padding-bottom:16px;padding-left:15px;
                    margin-left:5px;border-left:1px solid #e9e9e9}
.schedule-container:last-of-type{padding-bottom:0}
.header{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:8px}
.time-and-way{position:relative;display:flex;align-items:center;flex:0 0

... [Content truncated, total 32,407 chars] ...