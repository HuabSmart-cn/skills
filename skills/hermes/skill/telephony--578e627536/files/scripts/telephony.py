#!/usr/bin/env python3
"""Telephony helper for the Hermes optional telephony skill.

Capabilities:
- Persist telephony provider credentials to the Hermes .env file ($HERMES_HOME/.env)
- Search for, buy, and remember Twilio phone numbers
- Make direct Twilio calls (TwiML <Say> or <Play>)
- Send SMS / MMS via Twilio
- Poll inbound SMS for an owned Twilio number using only this script + state
- Import a Twilio number into Vapi and persist the returned Vapi phone_number_id
- Make outbound AI voice calls via Bland.ai or Vapi

This file intentionally uses Python stdlib HTTP clients so the skill can run in a
minimal environment with no extra pip installs.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape as xml_escape
from pathlib import Path
from typing import Any

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01/Accounts"
VAPI_API_BASE = "https://api.vapi.ai"
BLAND_API_BASE = "https://api.bland.ai/v1"

BLAND_DEFAULT_VOICE = "mason"
BLAND_DEFAULT_MODEL = "enhanced"
BLAND_VOICES = {
    "mason": "Male, natural, friendly (recommended)",
    "josh": "Male, conversational",
    "ryan": "Male, professional",
    "matt": "Male, casual",
    "evelyn": "Female, natural, warm (recommended)",
    "tina": "Female, warm, friendly",
    "june": "Female, conversational",
}

VAPI_DEFAULT_VOICE_PROVIDER = "11labs"
VAPI_DEFAULT_VOICE_ID = "cjVigY5qzO86Huf0OWal"  # ElevenLabs "Eric"
VAPI_DEFAULT_MODEL = "gpt-4o"
TWILIO_DEFAULT_TTS_VOICE = "Polly.Joanna"
DEFAULT_AI_PROVIDER = "bland"
STATE_VERSION = 1


class TelephonyError(RuntimeError):
    """Domain-specific failure surfaced to the skill/user."""


@dataclass
class OwnedTwilioNumber:
    sid: str
    phone_number: str
    friendly_name: str
    capabilities: dict[str, Any]


def _hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()


def _env_path() -> Path:
    return _hermes_home() / ".env"


def _config_path() -> Path:
    return _hermes_home() / "config.yaml"


def _state_path() -> Path:
    return _hermes_home() / "telephony_state.json"


def _load_root_config() -> dict[str, Any]:
    path = _config_path()
    if not path.exists():
        return {}
    try:
        import yaml  # optional dependency; Hermes already ships PyYAML
    except Exception:
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _config_lookup(*paths: tuple[str, ...], default: str = "") -> str:
    root = _load_root_config()
    for path in paths:
        node: Any = root
        for key in path:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(key)
        if node not in {None, ""} and not isinstance(node, dict):
            return str(node)
    return default


def _load_dotenv_values(path: Path | None = None) -> dict[str, str]:
    env_file = path or _env_path()
    if not env_file.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
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


def _env_or_config(env_key: str, *config_paths: tuple[str, ...], default: str = "") -> str:
    value = os.environ.get(env_key, "")
    if value:
        return value
    dotenv_value = _load_dotenv_values().get(env_key, "")
    if dotenv_value:
        return dotenv_value
    return _config_lookup(*config_paths, default=default)


def _load_state(path: Path | None = None) -> dict[str, Any]:
    state_file = path or _state_path()
    if not state_file.exists():
        return {"version": STATE_VERSION}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("version", STATE_VERSION)
            return data
    except Exception:
        pass
    return {"version": STATE_VERSION}


def _save_state(state: dict[str, Any], path: Path | None = None) -> Path:
    state_file = path or _state_path()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state_file


def _quote_env_value(value: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_./:+@-]+", value):
        return value
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _upsert_env_file(updates: dict[str, str], env_path: Path | None = None) -> Path:
    path = env_path or _env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        lines = path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    seen: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue
        key, _, _rest = line.partition("=")
        key = key.strip()
        if key in updates:
            new_lines.append(f"{key}={_quote_env_value(str(updates[key]))}")
            seen.add(key)
        else:
            new_lines.append(line)

    if new_lines and new_lines[-1].strip():
        new_lines.append("")
    for key, value in updates.items():
        if key not in seen:
            new_lines.append(f"{key}={_quote_env_value(str(value))}")

    path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
    return path


def _normalize_phone(number: str) -> str:
    if not number:
        raise TelephonyError("Phone number is required")
    trimmed = number.strip()
    if not trimmed.startswith("+"):
        raise TelephonyError(
            f"Phone number must be E.164 format (for example +15551234567), got: {number}"
        )
    digits = "+" + re.sub(r"\D", "", trimmed)
    if len(digits) < 8:
        raise TelephonyError(f"Phone number looks too short: {number}")
    return digits


def _mask_phone(number: str) -> str:
    digits = re.sub(r"\D", "", number or "")
    if len(digits) < 4:
        return "***"
    return f"***-***-{digits[-4:]}"


def _parse_twilio_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _json_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    form: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{url}?{query}"

    request_headers = dict(headers or {})
    body: bytes | None = None
    if json_body is not None:
        body = json.dumps(json_body).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/json")
    elif form is not None:
        body = urllib.parse.urlencode(form, doseq=True).encode("utf-8")
        request_headers.setdefault("Content-Type", "application/x-www-form-urlencoded")

    req = urllib.request.Request(url, data=body, headers=request_headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = resp.read().decode("utf-8")
            return json.loads(payload) if payload else {}
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        try:
            parsed = json.loads(body_text) if body_text else {}
        except Exception:
            parsed = {"raw": body_text}
        raise TelephonyError(f"HTTP {exc.code} from {url}: {parsed or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise TelephonyError(f"Connection error for {url}: {exc.reason}") from exc


def _twilio_creds() -> tuple[str, str]:
    sid = _env_or_config(
        "TWILIO_ACCOUNT_SID",
        ("telephony", "twilio", "account_sid"),
        ("phone", "twilio", "account_sid"),
    )
    token = ***REDACTED***
        "TWILIO_AUTH_TOKEN",
        ("telephony", "twilio", "auth_token"),
        ("phone", "twilio", "auth_token"),
    )
    if not sid or not token:
        ***REDACTED***
            "Twilio credentials are not configured. Use 'save-twilio' or set "
            f"TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in {_env_path()}."
        )
    return sid, token


def _twilio_basic_headers() -> dict[str, str]:
    sid, token = ***REDACTED***
    auth = base64.b64encode(f"{sid}:{token}".encode("utf-8")).decode("ascii")
    return {"Authorization": ***REDACTED***


def _twilio_request(method: str, path: str, *, params=None, form=None) -> dict[str, Any]:
    sid, _token = ***REDACTED***
    return _json_request(
        method,
        f"{TWILIO_API_BASE}/{sid}/{path.lstrip('/')}",
        headers=_twilio_basic_headers(),
        params=params,
        form=form,
    )


def _twilio_owned_numbers(limit: int = 50) -> list[OwnedTwilioNumber]:
    payload = _twilio_request("GET", "IncomingPhoneNumbers.json", params={"PageSize": limit})
    items = payload.get("incoming_phone_numbers", []) or []
    results: list[OwnedTwilioNumber] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        caps = item.get("capabilities") if isinstance(item.get("capabilities"), dict) else {}
        results.append(
            OwnedTwilioNumber(
                sid=str(item.get("sid", "")),
                phone_number=str(item.get("phone_number", "")),
                friendly_name=str(item.get("friendly_name", "")),
                capabilities=caps,
            )
        )
    return results


def _remember_twilio_number(
    *,
    phone_number: str,
    phone_sid: str = "",
    save_env: bool = False,
    state_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    state = _load_state(state_path)
    twilio_state = state.setdefault("twilio", {})
    twilio_state["default_phone_number"] = phone_number
    if phone_sid:
        twilio_state["default_phone_sid"] = phone_sid
    _save_state(state, state_path)

    saved_env_keys: list[str] = []
    if save_env:
        updates = {"TWILIO_PHONE_NUMBER": phone_number}
        if phone_sid:
            updates["TWILIO_PHONE_NUMBER_SID"] = phone_sid
        _upsert_env_file(updates, env_path)
        saved_env_keys = sorted(updates)

    return {
        "state_path": str(state_path or _state_path()),
        "saved_env_keys": saved_env_keys,
    }


def _remember_vapi_number(
    *,
    phone_number_id: str,
    save_env: bool = False,
    state_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    state = _load_state(state_path)
    vapi_state = state.setdefault("vapi", {})
    vapi_state["phone_number_id"] = phone_number_id
    _save_state(state, state_path)

    saved_env_keys: list[str] = []
    if save_env:
        _upsert_env_file({"VAPI_PHONE_NUMBER_ID": phone_number_id}, env_path)
        saved_env_keys = ["VAPI_PHONE_NUMBER_ID"]

    return {
        "state_path": str(state_path or _state_path()),
        "saved_env_keys": saved_env_keys,
    }


def _resolve_twilio_number(identifier: str | None = None) -> OwnedTwilioNumber:
    if identifier:
        wanted = identifier.strip()
        normalized = None
        if wanted.startswith("+"):
            normalized = _normalize_phone(wanted)
        for item in _twilio_owned_numbers(limit=100):
            if item.sid == wanted or item.phone_number == normalized:
                return item
        raise TelephonyError(f"Could not find an owned Twilio number matching {identifier}")

    env_number = _env_or_config(
        "TWILIO_PHONE_NUMBER",
        ("telephony", "twilio", "phone_number"),
        ("phone", "twilio", "phone_number"),
    )
    env_sid = _env_or_config(
        "TWILIO_PHONE_NUMBER_SID",
        ("telephony", "twilio", "phone_number_sid"),
        ("phone", "twilio", "phone_number_sid"),
    )
    state = _load_state()
    twilio_state = state.get("twilio", {}) if isinstance(state.get("twilio"), dict) else {}
    preferred_number = env_number or str(twilio_state.get("default_phone_number", ""))
    preferred_sid = env_sid or str(twilio_state.get("default_phone_sid", ""))

    owned = _twilio_owned_numbers(limit=100)
    if preferred_sid:
        for item in owned:
            if item.sid == preferred_sid:
                return item
    if preferred_number:
        normalized = _normalize_phone(preferred_number)
        for item in owned:
            if item.phone_number == normalized:
                return item
    if len(owned) == 1:
        return owned[0]

    raise TelephonyError(
        "No default Twilio phone number is set. Use 'twilio-buy --save-env', "
        f"'twilio-set-default', or set TWILIO_PHONE_NUMBER in {_env_path()}."
    )


def _vapi_api_key() -> str:
    ***REDACTED***
        "VAPI_API_KEY",
        ("telephony", "vapi", "api_key"),
        ("phone", "vapi", "api_key"),
    )


def _vapi_phone_number_id() -> str:
    state = _load_state()
    vapi_state = state.get("vapi", {}) if isinstance(state.get("vapi"), dict) else {}
    return _env_or_config(
        "VAPI_PHONE_NUMBER_ID",
        ("telephony", "vapi", "phone_number_id"),
        ("phone", "vapi", "phone_number_id"),
        default=str(vapi_state.get("phone_number_id", "")),
    )


def _bland_api_key() -> str:
    ***REDACTED***
        "BLAND_API_KEY",
        ("telephony", "bland", "api_key"),
        ("phone", "bland", "api_key"),
    )


def _ai_provider(default: str = DEFAULT_AI_PROVIDER) -> str:
    return _env_or_config(
        "PHONE_PROVIDER",
        ("telephony", "provider"),
        ("phone", "provider"),
        default=default,
    ).lower().strip()


def _twilio_search_numbers(
    *,
    country: str = "US",
    area_code: str | None = None,
    contains: str | None = None,
    limit: int = 10,
    sms_enabled: bool = True,
    voice_enabled: bool = True,
) -> dict[str, Any]:
    params: dict[str, Any] = {
        "PageSize": max(1, min(limit, 20)),
        "SmsEnabled": str(bool(sms_enabled)).lower(),
        "VoiceEnabled": str(bool(voice_enabled)).lower(),
    }
    if area_code:
        params["AreaCode"] = str(area_code)
    if contains:
        params["Contains"] = str(contains)

    payload = _twilio_request(
        "GET",
        f"AvailablePhoneNumbers/{country.upper()}/Local.json",
        params=params,
    )
    items = payload.get("available_phone_numbers", []) or []
    return {
        "success": True,
        "country": country.upper(),
        "count": len(items),
        "numbers": [
            {
                "phone_number": item.get("phone_number"),
                "friendly_name": item.get("friendly_name"),
                "locality": item.get("locality"),
                "region": item.get("region"),
                "postal_code": item.get("postal_code"),
                "iso_country": item.get("iso_country"),
                "capabilities": {
                    "voice": item.get("voice_enabled"),
                    "sms": item.get("sms_enabled"),
                    "mms": item.get("mms_enabled"),
                },
            }
            for item in items
            if isinstance(item, dict)
        ],
    }


def _twilio_buy_number(
    phone_number: str,
    *,
    save_env: bool = False,
    state_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    normalized = _normalize_phone(phone_number)
    payload = _twilio_request("POST", "IncomingPhoneNumbers.json", form={"PhoneNumber": normalized})
    purchased = {
        "success": True,
        "provider": "twilio",
        "phone_number": payload.get("phone_number", normalized),
        "phone_sid": payload.get("sid"),
        "friendly_name": payload.get("friendly_name"),
        "capabilities": payload.get("capabilities", {}),
        "message": "Twilio number purchased successfully.",
    }
    purchased.update(
        _remember_twilio_number(
            phone_number=str(purchased["phone_number"]),
            phone_sid=str(purchased.get("phone_sid") or ""),
            save_env=save_env,
            state_path=state_path,
            env_path=env_path,
        )
    )
    return purchased


def _twilio_list_owned() -> dict[str, Any]:
    owned = _twilio_owned_numbers(limit=100)
    return {
        "success": True,
        "provider": "twilio",
        "count": len(owned),
        "numbers": [
            {
                "phone_number": item.phone_number,
                "phone_sid": item.sid,
                "friendly_name": item.friendly_name,
                "capabilities": item.capabilities,
            }
            for item in owned
        ],
    }


def _twilio_set_default(identifier: str, *, save_env: bool = False) -> dict[str, Any]:
    owned = _resolve_twilio_number(identifier)
    result = {
        "success": True,
        "provider": "twilio",
        "phone_number": owned.phone_number,
        "phone_sid": owned.sid,
        "message": "Default Twilio number updated.",
    }
    result.update(
        _remember_twilio_number(
            phone_number=owned.phone_number,
            phone_sid=owned.sid,
            save_env=save_env,
        )
    )
    return result


def _twiml_say(message: str, voice: str) -> str:
    return f"<Response><Say voice=\"{xml_escape(voice)}\">{xml_escape(message)}</Say></Response>"


def _twiml_play(audio_url: str) -> str:
    return f"<Response><Play>{xml_escape(audio_url)}</Play></Response>"


def _twilio_call(
    to_number: str,
    *,
    message: str | None = None,
    audio_url: str | None = None,
    voice: str = TWILIO_DEFAULT_TTS_VOICE,
    send_digits: str | None = None,
    from_identifier: str | None = None,
    record: bool = False,
) -> dict[str, Any]:
    destination = _normalize_phone(to_number)
    source = _resolve_twilio_number(from_identifier)
    if bool(message) == bool(audio_url):
        raise TelephonyError("Provide exactly one of 'message' or 'audio_url' for twilio-call")

    twiml = _twiml_play(audio_url) if audio_url else _twiml_say(message or "", voice)
    form: dict[str, Any] = {
        "To": destination,
        "From": source.phone_number,
        "Twiml": twiml,
    }
    if send_digits:
        form["SendDigits"] = send_digits
    if record:
        form["Record"] = "true"

    payload = _twilio_request("POST", "Calls.json", form=form)
    return {
        "success": True,
        "provider": "twilio",
        "call_sid": payload.get("sid"),
        "status": payload.get("status"),
        "from_phone_number": source.phone_number,
        "to_phone_number_masked": _mask_phone(destination),
        "mode": "play" if audio_url else "say",
        "recording_requested": record,
        "message": "Twilio call initiated.",
    }


def _twilio_call_status(call_sid: str) -> dict[str, Any]:
    payload = _twilio_request("GET", f"Calls/{call_sid}.json")
    return {
        "success": True,
        "provider": "twilio",
        "call_sid": payload.get("sid"),
        "status": payload.get("status"),
        "direction": payload.get("direction"),
        "duration": payload.get("duration"),
        "from_phone_number": payload.get("from"),
        "to_phone_number_masked": _mask_phone(str(payload.get("to") or "")),
        "start_time": payload.get("start_time"),
        "end_time": payload.get("end_time"),
        "answered_by": payload.get("answered_by"),
    }


def _twilio_send_sms(
    to_number: str,
    body: str,
    *,
    media_urls: list[str] | None = None,
    from_identifier: str | None = None,
) -> dict[str, Any]:
    destination = _normalize_phone(to_number)
    source = _resolve_twilio_number(from_identifier)
    if not body.strip():
        raise TelephonyError("SMS body cannot be empty")
    form: dict[str, Any] = {
        "To": destination,
        "From": source.phone_number,
        "Body": body,
    }
    if media_urls:
        form["MediaUrl"] = media_urls
    payload = _twilio_request("POST", "Messages.json", form=form)
    return {
        "success": True,
        "provider": "twilio",
        "message_sid": payload.get("sid"),
        "status": payload.get("status"),
        "from_phone_number": source.phone_number,
        "to_phone_number_masked": _mask_phone(destination),
        "media_count": len(media_urls or []),
        "message": "SMS/MMS queued via Twilio.",
    }


def _checkpoint_for_messages(messages: list[dict[str, Any]]) -> tuple[str, str]:
    if not messages:
        return "", ""
    newest = messages[0]
    return str(newest.get("sid") or ""), str(newest.get("date_sent") or newest.get("date_created") or "")


def _messages_after_checkpoint(messages: list[dict[str, Any]], last_sid: str) -> list[dict[str, Any]]:
    if not last_sid:
        return messages
    filtered: list[dict[str, Any]] = []
    for message in messages:
        if str(message.get("sid") or "") == last_sid:
            break
        filtered.append(message)
    return filtered


def _twilio_inbox(
    *,
    limit: int = 20,
    since_last: bool = False,
    mark_seen: bool = False,
    phone_identifier: str | None = None,
    state_path: Path | None = None,
) -> dict[str, Any]:
    owned = _resolve_twilio_number(phone_identifier)
    payload = _twilio_request(
        "GET",
        "Messages.json",
        params={"To": owned.phone_number, "PageSize": max(1, min(limit, 100))},
    )
    raw_messages = payload.get("messages", []) or []
    messages = [m for m in raw_messages if isinstance(m, dict)]

    state = _load_state(state_path)
    twilio_state = state.setdefault("twilio", {})
    last_sid = str(twilio_state.get("last_inbound_message_sid", ""))
    if since_last:
        messages = _messages_after_checkpoint(messages, last_sid)

    message_rows = [
        {
            "sid": msg.get("sid"),
            "direction": msg.get("direction"),
            "status": msg.get("status"),
            "from_phone_number": msg.get("from"),
            "to_phone_number": msg.get("to"),
            "date_sent": msg.get("date_sent"),
            "body": msg.get("body"),
            "num_media": msg.get("num_media"),
        }
        for msg in messages
    ]

    if mark_seen and message_rows:
        last_seen_sid, last_seen_date = _checkpoint_for_messages(message_rows)
        twilio_state["last_inbound_message_sid"] = last_seen_sid
        twilio_state["last_inbound_message_date"] = last_seen_date
        _save_state(state, state_path)

    return {
        "success": True,
        "provider": "twilio",
        "phone_number": owned.phone_number,
        "count": len(message_rows),
        "messages": message_rows,
        "since_last": since_last,
        "marked_seen": bool(mark_seen and message_rows),
        "state_path": str(state_path or _state_path()),
        "last_seen_message_sid": twilio_state.get("last_inbound_message_sid", ""),
    }


def _vapi_import_twilio_number(
    *,
    phone_identifier: str | None = None,
    save_env: bool = False,
    state_path: Path | None = None,
    env_path: Path | None = None,
) -> dict[str, Any]:
    api_key = ***REDACTED***
    if not api_key:
        ***REDACTED***
            f"Vapi is not configured. Use 'save-vapi' or set VAPI_API_KEY in {_env_path()} first."
        )
    owned = _resolve_twilio_number(phone_identifier)
    sid, token = ***REDACTED***
    payload = _json_request(
        "POST",
        f"{VAPI_API_BASE}/phone-number",
        headers={"Authorization": f"Bearer {api_key}"},
        json_body={
            "provider": "twilio",
            "number": owned.phone_number,
            "twilioAccountSid": sid,
            "twilioAuthToken": ***REDACTED***
        },
    )
    phone_number_id = str(payload.get("id") or "")
    if not phone_number_id:
        raise TelephonyError(f"Vapi did not return a phone number id: {payload}")
    result = {
        "success": True,
        "provider": "vapi",
        "phone_number_id": phone_number_id,
        "phone_number": owned.phone_number,
        "message": "Twilio number imported into Vapi."

... [Content truncated, total 46,410 chars] ...