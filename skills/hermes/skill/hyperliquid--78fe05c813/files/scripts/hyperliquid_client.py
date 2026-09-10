#!/usr/bin/env python3
"""
Hyperliquid CLI Tool for Hermes Agent
-------------------------------------
Queries the Hyperliquid info endpoint for market and account data.
Uses only Python standard library - no external packages required.

Usage:
  python3 hyperliquid_client.py dexs
  python3 hyperliquid_client.py markets [--dex DEX] [--limit N]
  python3 hyperliquid_client.py spots [--limit N]
  python3 hyperliquid_client.py candles <coin> [--interval 1h] [--hours 24]
  python3 hyperliquid_client.py funding <coin> [--hours 72]
  python3 hyperliquid_client.py l2 <coin> [--levels 10]
  python3 hyperliquid_client.py state [address] [--dex DEX]
  python3 hyperliquid_client.py spot-balances [address]
  python3 hyperliquid_client.py fills [address] [--hours N] [--limit N]
  python3 hyperliquid_client.py orders [address] [--limit N]
  python3 hyperliquid_client.py review [address] [--coin COIN] [--hours N]
  python3 hyperliquid_client.py export <coin> [--interval 1h] [--hours N]

Environment:
  HYPERLIQUID_API_URL  Override API base URL
                       (default: https://api.hyperliquid.xyz)
  HYPERLIQUID_USER_ADDRESS  Default address for state/fills/orders/review commands
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


USER_AGENT = "HermesAgent/1.0"
DEFAULT_USER_ENV = "HYPERLIQUID_USER_ADDRESS"
DEFAULT_API_BASE = "https://api.hyperliquid.xyz"


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()


def _dotenv_paths() -> List[Path]:
    paths: List[Path] = []
    project_env = Path.cwd() / ".env"
    if project_env.exists():
        paths.append(project_env)

    user_env = _hermes_home() / ".env"
    if user_env.exists():
        paths.append(user_env)

    return paths


def _load_dotenv_values() -> Dict[str, str]:
    values: Dict[str, str] = {}
    for env_path in _dotenv_paths():
        try:
            lines = env_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            lines = env_path.read_text(encoding="latin-1").splitlines()

        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = raw_line.partition("=")
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"') and len(value) >= 2:
                value = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
            values[key] = value
    return values


def _env_lookup(key: str, default: str = "") -> str:
    value = os.environ.get(key, "").strip()
    if value:
        return value
    dotenv_value = _load_dotenv_values().get(key, "").strip()
    if dotenv_value:
        return dotenv_value
    return default


def _api_base() -> str:
    return _env_lookup("HYPERLIQUID_API_URL", DEFAULT_API_BASE).rstrip("/")


def _info_url() -> str:
    api_base = _api_base()
    if api_base.endswith("/info"):
        return api_base
    return f"{api_base}/info"


def _resolve_user(user: Optional[str]) -> str:
    candidate = (user or "").strip()
    if candidate:
        return candidate

    env_value = _env_lookup(DEFAULT_USER_ENV, "")
    if env_value:
        return env_value

    sys.exit(
        "Missing Hyperliquid address. Pass <address> explicitly or set "
        f"{DEFAULT_USER_ENV} in your environment or {_hermes_home() / '.env'}."
    )


def _post_info(payload: Dict[str, Any], timeout: int = 20, retries: int = 2) -> Any:
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }

    for attempt in range(retries + 1):
        request = urllib.request.Request(_info_url(), data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.load(response)
            return body
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            sys.exit(f"Hyperliquid HTTP error: {exc}")
        except urllib.error.URLError as exc:
            sys.exit(f"Hyperliquid connection error: {exc}")
        except json.JSONDecodeError as exc:
            sys.exit(f"Hyperliquid response was not valid JSON: {exc}")

    return None


def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _limit_items(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    if limit <= 0:
        return items
    return items[:limit]


def _hours_ago_ms(hours: float, now_ms: Optional[int] = None) -> int:
    end_ms = now_ms if now_ms is not None else int(time.time() * 1000)
    return end_ms - int(hours * 60 * 60 * 1000)


def _format_timestamp_ms(value: Any) -> str:
    try:
        ts_ms = int(value)
    except (TypeError, ValueError):
        return "-"
    return dt.datetime.utcfromtimestamp(ts_ms / 1000).strftime("%Y-%m-%d %H:%M:%S UTC")


def _compact_number(value: Any, decimals: int = 2) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    sign = "-" if number < 0 else ""
    number = abs(number)
    if number >= 1_000_000_000:
        return f"{sign}{number / 1_000_000_000:.{decimals}f}B"
    if number >= 1_000_000:
        return f"{sign}{number / 1_000_000:.{decimals}f}M"
    if number >= 1_000:
        return f"{sign}{number / 1_000:.{decimals}f}K"
    if number >= 100:
        return f"{sign}{number:.2f}"
    if number >= 1:
        return f"{sign}{number:.4f}".rstrip("0").rstrip(".")
    return f"{sign}{number:.6f}".rstrip("0").rstrip(".")


def _format_price(value: Any) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    if abs(number) >= 1000:
        return f"{number:,.2f}"
    if abs(number) >= 1:
        return f"{number:,.4f}".rstrip("0").rstrip(".")
    return f"{number:,.6f}".rstrip("0").rstrip(".")


def _format_percent(value: Any, decimals: int = 2) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    return f"{number:+.{decimals}f}%"


def _format_fraction_percent(value: Any, decimals: int = 4) -> str:
    number = _safe_float(value)
    if number is None:
        return "-"
    return f"{number * 100:+.{decimals}f}%"


def _percent_change(current: Any, previous: Any) -> Optional[float]:
    curr = _safe_float(current)
    prev = _safe_float(previous)
    if curr is None or prev is None or prev == 0:
        return None
    return ((curr - prev) / prev) * 100


def _short_address(address: Any) -> str:
    if not isinstance(address, str) or len(address) < 12:
        return str(address)
    return f"{address[:6]}...{address[-4:]}"


def _render_table(headers: List[tuple[str, str]], rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "(no data)"

    prepared_rows: List[List[str]] = []
    widths = [len(label) for label, _ in headers]

    for row in rows:
        rendered = []
        for index, (_label, key) in enumerate(headers):
            value = row.get(key, "")
            text = str(value)
            rendered.append(text)
            if len(text) > widths[index]:
                widths[index] = len(text)
        prepared_rows.append(rendered)

    lines = []
    header_line = "  ".join(label.ljust(widths[idx]) for idx, (label, _key) in enumerate(headers))
    separator = "  ".join("-" * widths[idx] for idx in range(len(headers)))
    lines.extend([header_line, separator])

    for rendered in prepared_rows:
        lines.append("  ".join(rendered[idx].ljust(widths[idx]) for idx in range(len(rendered))))
    return "\n".join(lines)


def _normalize_dexs(payload: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return rows

    for index, item in enumerate(payload):
        if item is None:
            rows.append(
                {
                    "index": index,
                    "name": "",
                    "label": "first-perp-dex",
                    "full_name": "First perp dex",
                    "deployer": "-",
                    "asset_caps": 0,
                }
            )
            continue

        if not isinstance(item, dict):
            continue

        caps = item.get("assetToStreamingOiCap") or []
        rows.append(
            {
                "index": index,
                "name": item.get("name", ""),
                "label": item.get("name") or "first-perp-dex",
                "full_name": item.get("fullName") or "-",
                "deployer": item.get("deployer") or "-",
                "asset_caps": len(caps) if isinstance(caps, list) else 0,
            }
        )
    return rows


def _normalize_perp_markets(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) < 2:
        return []

    meta = payload[0] if isinstance(payload[0], dict) else {}
    ctxs = payload[1] if isinstance(payload[1], list) else []
    universe = meta.get("universe") if isinstance(meta, dict) else []
    if not isinstance(universe, list):
        return []

    rows: List[Dict[str, Any]] = []
    for index, spec in enumerate(universe):
        if not isinstance(spec, dict):
            continue
        ctx = ctxs[index] if index < len(ctxs) and isinstance(ctxs[index], dict) else {}
        mark_px = ctx.get("markPx") or ctx.get("midPx") or ctx.get("oraclePx")
        row = {
            "coin": spec.get("name", f"asset-{index}"),
            "mark_px": mark_px,
            "mid_px": ctx.get("midPx"),
            "oracle_px": ctx.get("oraclePx"),
            "prev_day_px": ctx.get("prevDayPx"),
            "change_pct": _percent_change(mark_px, ctx.get("prevDayPx")),
            "funding": ctx.get("funding"),
            "premium": ctx.get("premium"),
            "open_interest": ctx.get("openInterest"),
            "day_ntl_vlm": ctx.get("dayNtlVlm"),
            "day_base_vlm": ctx.get("dayBaseVlm"),
            "max_leverage": spec.get("maxLeverage"),
            "sz_decimals": spec.get("szDecimals"),
            "is_delisted": bool(spec.get("isDelisted")),
            "only_isolated": bool(spec.get("onlyIsolated")),
            "margin_mode": spec.get("marginMode") or "-",
        }
        rows.append(row)
    return rows


def _normalize_spot_markets(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, list) or len(payload) < 2:
        return []

    meta = payload[0] if isinstance(payload[0], dict) else {}
    ctxs = payload[1] if isinstance(payload[1], list) else []
    pairs = meta.get("universe") if isinstance(meta, dict) else []
    tokens = ***REDACTED***
    token_lookup = ***REDACTED***
    if isinstance(tokens, list):
        ***REDACTED***
            if isinstance(token, dict) and "index" in token:
                ***REDACTED***

    rows: List[Dict[str, Any]] = []
    if not isinstance(pairs, list):
        return rows

    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict):
            continue
        ctx = ctxs[index] if index < len(ctxs) and isinstance(ctxs[index], dict) else {}
        raw_name = pair.get("name", f"@{index}")
        tokens_for_pair = ***REDACTED***
        display_name = raw_name
        if "/" not in raw_name and len(tokens_for_pair) =***REDACTED***
            base = token_lookup.get(tokens_for_pair[0], str(tokens_for_pair[0]))
            quote = token_lookup.get(tokens_for_pair[1], str(tokens_for_pair[1]))
            display_name = f"{base}/{quote} ({raw_name})"

        mark_px = ctx.get("markPx") or ctx.get("midPx")
        rows.append(
            {
                "pair": raw_name,
                "display_name": display_name,
                "mark_px": mark_px,
                "mid_px": ctx.get("midPx"),
                "prev_day_px": ctx.get("prevDayPx"),
                "change_pct": _percent_change(mark_px, ctx.get("prevDayPx")),
                "day_ntl_vlm": ctx.get("dayNtlVlm"),
            }
        )
    return rows


def _normalize_candles(payload: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return rows

    for candle in payload:
        if not isinstance(candle, dict):
            continue
        rows.append(
            {
                "time": candle.get("t") or candle.get("time"),
                "open": candle.get("o"),
                "high": candle.get("h"),
                "low": candle.get("l"),
                "close": candle.get("c"),
                "volume": candle.get("v"),
                "trades": candle.get("n"),
            }
        )

    rows.sort(key=lambda item: int(item.get("time") or 0))
    return rows


def _normalize_funding_history(payload: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return rows

    for item in payload:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "coin": item.get("coin", "-"),
                "funding_rate": item.get("fundingRate"),
                "premium": item.get("premium"),
                "time": item.get("time"),
            }
        )

    rows.sort(key=lambda item: int(item.get("time") or 0))
    return rows


def _normalize_book_levels(payload: Any) -> Dict[str, List[Dict[str, Any]]]:
    if not isinstance(payload, dict):
        return {"bids": [], "asks": []}

    levels = payload.get("levels")
    if not isinstance(levels, list) or len(levels) < 2:
        return {"bids": [], "asks": []}

    def convert(side: Iterable[Any]) -> List[Dict[str, Any]]:
        converted = []
        for entry in side:
            if isinstance(entry, dict):
                converted.append(
                    {
                        "px": entry.get("px"),
                        "sz": entry.get("sz"),
                        "orders": entry.get("n"),
                    }
                )
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                converted.append(
                    {
                        "px": entry[0],
                        "sz": entry[1],
                        "orders": entry[2] if len(entry) > 2 else None,
                    }
                )
        return converted

    return {"bids": convert(levels[0]), "asks": convert(levels[1])}


def _normalize_positions(payload: Any) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        return {"summary": {}, "positions": []}

    positions: List[Dict[str, Any]] = []
    for item in payload.get("assetPositions", []):
        if not isinstance(item, dict):
            continue
        position = item.get("position") if isinstance(item.get("position"), dict) else item
        if not isinstance(position, dict):
            continue
        leverage = position.get("leverage") if isinstance(position.get("leverage"), dict) else {}
        positions.append(
            {
                "coin": position.get("coin", "-"),
                "size": position.get("szi"),
                "entry_px": position.get("entryPx"),
                "position_value": position.get("positionValue"),
                "unrealized_pnl": position.get("unrealizedPnl"),
                "return_on_equity": position.get("returnOnEquity"),
                "liquidation_px": position.get("liquidationPx"),
                "margin_used": position.get("marginUsed"),
                "leverage": leverage.get("value"),
                "leverage_type": leverage.get("type"),
            }
        )

    positions.sort(
        key=lambda item: abs(_safe_float(item.get("position_value")) or 0.0),
        reverse=True,
    )

    summary = payload.get("marginSummary") if isinstance(payload.get("marginSummary"), dict) else {}
    cross_summary = (
        payload.get("crossMarginSummary") if isinstance(payload.get("crossMarginSummary"), dict) else {}
    )

    return {
        "summary": {
            "account_value": summary.get("accountValue"),
            "total_ntl_pos": summary.get("totalNtlPos"),
            "total_raw_usd": summary.get("totalRawUsd"),
            "withdrawable": payload.get("withdrawable"),
            "cross_account_value": cross_summary.get("accountValue"),
        },
        "positions": positions,
    }


def _normalize_spot_balances(payload: Any) -> List[Dict[str, Any]]:
    if not isinstance(payload, dict):
        return []

    rows: List[Dict[str, Any]] = []
    for item in payload.get("balances", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "coin": item.get("coin", item.get("token", "-")),
                "total": item.get("total"),
                "hold": item.get("hold"),
                "entry_ntl": item.get("entryNtl"),
            }
        )

    rows.sort(key=lambda item: abs(_safe_float(item.get("entry_ntl")) or 0.0), reverse=True)
    return rows


def _normalize_fills(payload: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return rows

    for item in payload:
        if not isinstance(item, dict):
            continue
        fill = item.get("fill") if isinstance(item.get("fill"), dict) else item
        rows.append(
            {
                "coin": fill.get("coin", "-"),
                "dir": fill.get("dir") or fill.get("side") or "-",
                "px": fill.get("px"),
                "sz": fill.get("sz"),
                "closed_pnl": fill.get("closedPnl"),
                "fee": fill.get("fee"),
                "fee_token": ***REDACTED***
                "start_position": fill.get("startPosition"),
                "time": fill.get("time"),
                "hash": fill.get("hash"),
                "oid": fill.get("oid"),
                "twap_id": item.get("twapId"),
            }
        )

    rows.sort(key=lambda item: int(item.get("time") or 0), reverse=True)
    return rows


def _normalize_orders(payload: Any) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    if not isinstance(payload, list):
        return rows

    for item in payload:
        if not isinstance(item, dict):
            continue
        order = item.get("order") if isinstance(item.get("order"), dict) else item
        rows.append(
            {
                "coin": order.get("coin", "-"),
                "side": order.get("side", "-"),
                "limit_px": order.get("limitPx") or order.get("px"),
                "size": order.get("sz") or order.get("origSz"),
                "timestamp": item.get("statusTimestamp")
                or order.get("timestamp")
                or order.get("time"),
                "status": item.get("status") or order.get("status") or "-",
                "oid": order.get("oid"),
                "order_type": order.get("orderType") or "-",
            }
        )

    rows.sort(key=lambda item: int(item.get("timestamp") or 0), reverse=True)
    return rows


def _direction_bucket(direction: Any) -> str:
    text = str(direction or "").strip().lower()
    if "open" in text and "long" in text:
        return "open_long"
    if "close" in text and "long" in text:
        return "close_long"
    if "open" in text and "short" in text:
        return "open_short"
    if "close" in text and "short" in text:
        return "close_short"
    if text in {"b", "buy"}:
        return "buy"
    if text in {"s", "sell"}:
        return "sell"
    return "other"


def _average(values: Iterable[Optional[float]]) -> Optional[float]:
    clean_values = [value for value in values if value is not None]
    if not clean_values:
        return None
    return round(sum(clean_values) / len(clean_values), 12)


def _is_spot_coin(coin: str) -> bool:
    return "/" in coin or coin.startswith("@")


def _safe_info_query(payload: Dict[str, Any]) -> Any:
    try:
        return _post_info(payload)
    except SystemExit:
        return None


def _market_context_for_coin(coin: str, interval: str, start_ms: int, end_ms: int) -> Dict[str, Any]:
    candles = _normalize_candles(
        _safe_info_query(
            {
                "type": "candleSnapshot",
                "req": {
                    "coin": coin,
                    "interval": interval,
                    "startTime": start_ms,
                    "endTime": end_ms,
                },
            }
        )
    )
    funding_history: List[Dict[str, Any]] = []
    if not _is_spot_coin(coin):
        funding_history = _normalize_funding_history(
            _safe_info_query(
                {
                    "type": "fundingHistory",
                    "coin": coin,
                    "startTime": start_ms,
                    "endTime": end_ms,
                }
            )
        )

    candle_change = None
    if candles:
        candle_change = _percent_change(candles[-1].get("close"), candles[0].get("open"))

    funding_average = _average(_safe_float(item.get("funding_rate")) for item in funding_history)
    return {
        "coin": coin,
        "interval": interval,
        "candle_count": len(candles),
        "price_change_pct": candle_change,
        "window_open": candles[0].get("open") if candles else None,
        "window_close": candles[-1].get("close") if candles else None,
        "average_funding_rate": funding_average,
        "funding_samples": len(funding_history),
    }


def _build_coin_review(coin: str, fills: List[Dict[str, Any]], interval: str, start_ms: int, end_ms: int) -> Dict[str, Any]:
    pnl_values = [_safe_float(fill.get("closed_pnl")) for fill in fills]
    fee_values = [_safe_float(fill.get("fee")) for fill in fills]
    scored = [value for value in pnl_values if value is not None]
    wins = [value for value in scored if value > 0]
    losses = [value for value in scored if value < 0]
    breakeven = [value for value in scored if value == 0]

    direction_counts = Counter(_direction_bucket(fill.get("dir")) for fill in fills)
    market_context = _market_context_for_coin(coin, interval, start_ms, end_ms)
    total_pnl = sum(value for value in pnl_values if value is not None)
    total_fees = sum(value for value in fee_values if value is not None)
    net_after_fees = total_pnl - total_fees

    if direction_counts["open_long"] > direction_counts["open_short"]:
        open_bias = "long"
    elif direction_counts["open_short"] > direction_counts["open_long"]:
        open_bias = "short"
    elif direction_counts["open_long"] or direction_counts["open_short"]:
        open_bias = "mixed"
    else:
        open_bias = "none"

    return {
        "coin": coin,
        "fill_count": len(fills),
        "realized_pnl": total_pnl,
        "total_fees": total_fees,
        "net_after_fees": net_after_fees,
        "wins": len(wins),
        "losses": len(losses),
        "breakeven": len(breakeven),
        "win_rate_pct": (len(wins) / (len(wins) + len(losses)) * 100) if (len(wins) + len(losses)) else None,
        "open_long_count": direction_counts["open_long"],
        "open_short_count": direction_counts["open_short"],
        "close_long_count": direction_counts["close_long"],
        "close_short_count": direction_counts["close_short"],
        "open_bias": open_bias,
        "market_context": market_context,
    }


def _review_findings(summary: Dict[str, Any], coin_reviews: List[Dict[str, Any]]) -> List[str]:
    findings: List[str] = []

    if summary["fill_count"] == 0:
        return ["No fills were found in the requested review window."]

    if summary["outcome_fill_count"] == 0:
        findings.append("Most fills in this window look like opens or adjustments, so realized-outcome review is limited until positions close.")

    if summary["net_after_fees"] < 0:
        findings.append(
            f"Net realized PnL after fees was negative ({_compact_number(summary['net_after_fees'])} USDC-equivalent units in reported fill terms)."
        )
    elif summary["net_after_fees"] > 0:
        findings.append(
            f"Net realized PnL after fees was positive ({_compact_number(summary['net_after_fees'])} USDC-equivalent units in reported fill terms)."
        )

    realized_abs = abs(summary["realized_pnl"])
    if summary["total_fees"] > 0:
        if realized_abs == 0:
            findings.append("Fees were non-trivial while realized PnL stayed flat, which usually means churn without 

... [Content truncated, total 60,190 chars] ...