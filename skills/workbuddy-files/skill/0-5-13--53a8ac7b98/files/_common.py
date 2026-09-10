# -*- coding: utf-8 -*-
"""
library/_common.py —— 资料库 skill 顶层共享工具

统一收口 token 读取 / HTTP 调用 / 脱敏 / 退出逻辑。
业务脚本禁止自行实现上述能力，一律通过本模块导出的公共 API 调用。

运行模式：
- 客户端模式：base URL 默认生产，LIBRARY_ENV=staging 时优先 staging；
  首次请求鉴权失败会自动 fallback 到另一环境并锁定。
- 沙箱模式（X_IDE_IS_CLOUDSTUDIO=true）：固定走 auth-proxy，不读 token。

仅依赖 Python 标准库。
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Mapping, Optional, Tuple

# ---------------------------------------------------------------------------
# 运行模式
# ---------------------------------------------------------------------------

_SANDBOX_ENV_KEY = "X_IDE_IS_CLOUDSTUDIO"
_TRUE_VALUES = frozenset({"1", "true", "yes", "y", "on", "enabled"})


def is_sandbox() -> bool:
    """当前是否运行在 CodeBuddy 沙箱内。"""
    return os.environ.get(_SANDBOX_ENV_KEY, "").strip().lower() in _TRUE_VALUES


# ---------------------------------------------------------------------------
# Endpoint 与 base 状态
# ---------------------------------------------------------------------------

_PROD_BASE = "https://www.workbuddy.cn"
_STAGING_BASE = "https://staging.workbuddy.cn"
_SANDBOX_BASE = "http://codebuddy.auth-proxy.local"
_ENV_KEY = "LIBRARY_ENV"


def _client_api_bases() -> Tuple[str, str]:
    """返回 (首选 base, fallback base)。"""
    if os.environ.get(_ENV_KEY, "").strip().lower() == "staging":
        return _STAGING_BASE, _PROD_BASE
    return _PROD_BASE, _STAGING_BASE


API_BASE: str = _SANDBOX_BASE if is_sandbox() else _client_api_bases()[0]
_base_locked: bool = is_sandbox()


def _lock_api_base(base: str) -> None:
    global API_BASE, _base_locked
    API_BASE = base
    _base_locked = True


def build_url(path: str) -> str:
    """拼接 API 全 URL。业务脚本统一走这里。"""
    return f"{API_BASE}{path}"


USER_AGENT = f"library-skills/{os.environ.get('KS_SKILL_VERSION', '0.1.0')}"

# ---------------------------------------------------------------------------
# 脱敏
# ---------------------------------------------------------------------------

_REDACTIONS: List[str] = []


def _register_redaction(secret: ***REDACTED***
    if secret and len(secret) >= ***REDACTED***
        _REDACTIONS.append(secret)


def redact(text: Any) -> str:
    """把已注册的敏感串替换为 [REDACTED]。"""
    try:
        s = text if isinstance(text, str) else str(text)
    except Exception:
        return "[REDACTED]"
    for secret in _REDACTIONS:
        ***REDACTED***
            s = s.replace(secret, "[REDACTED]")
    return s


# ---------------------------------------------------------------------------
# Token 读取
# ---------------------------------------------------------------------------

_TOKEN_MIN_LEN = ***REDACTED***


def read_token_from_stdin() -> str:
    ***REDACTED***
    if is_sandbox():
        return ""
    try:
        if sys.stdin.isatty():
            return ""
    except Exception:
        pass
    try:
        line = sys.stdin.readline()
    except Exception:
        return ""
    token = ***REDACTED***
    if len(token) < _TOKEN_MIN_LEN:
        ***REDACTED***
    _register_redaction(token)
    return token


_TOKEN_ARG_DEST = ***REDACTED***


def register_token_arg(parser: ***REDACTED***
    """向 argparse 注册 `--token-stdin` 开关。"""
    import argparse
    parser.add_argument(
        "--token-stdin", dest=***REDACTED***
        action="store_true", help=argparse.SUPPRESS,
    )


def acquire_token(args: ***REDACTED***
    """业务脚本 token 唯一入口。沙箱返回空串，客户端从 stdin 读取。"""
    _ = args
    if is_sandbox():
        return ""
    token = ***REDACTED***
    if not token:
        ***REDACTED***
            "missing token", error_code=***REDACTED***
            backend_message="token 缺失或无效",
        )))
    return token


# ---------------------------------------------------------------------------
# HTTP 错误类型
# ---------------------------------------------------------------------------

class HttpError(Exception):
    """HTTP / 业务层错误。"""

    def __init__(self, message: str, *, error_code: Any = "UNKNOWN",
                 backend_message: Any = "", traceid: Optional[str] = None) -> None:
        super().__init__(message)
        self.error_code = _safe_error_code(error_code)
        self.backend_message = _safe_backend_message(backend_message)
        self.traceid = traceid

    def __str__(self) -> str:
        if self.backend_message:
            return f"code={self.error_code}; msg={self.backend_message}"
        return f"code={self.error_code}"


class HttpResponse(dict):
    """JSON 响应体 dict，附带 traceid。"""

    def __init__(self, payload: Mapping[str, Any], *, traceid: Optional[str] = None) -> None:
        super().__init__(payload)
        self.traceid = traceid


# ---------------------------------------------------------------------------
# HTTP 辅助
# ---------------------------------------------------------------------------

def _extract_traceid(headers: Any) -> Optional[str]:
    """从响应 headers 取 traceid。"""
    if not headers:
        return None
    try:
        val = headers.get("traceid")
        if val is not None and str(val).strip():
            return str(val).strip()
    except Exception:
        pass
    try:
        for k, v in headers.items():
            if str(k).lower() == "traceid" and v is not None and str(v).strip():
                return str(v).strip()
    except Exception:
        pass
    return None


def _safe_error_code(value: Any) -> str:
    text = str(value if value is not None else "UNKNOWN").strip()
    if not text or len(text) > 64:
        return "UNKNOWN"
    if not all(ch.isalnum() or ch in "_.-" for ch in text):
        return "UNKNOWN"
    return text


def _safe_backend_message(value: Any) -> str:
    if value is None:
        return ""
    text = redact(value).strip()
    if not text:
        return ""
    if "Traceback (most recent call last)" in text or "goroutine " in text:
        return "[INTERNAL_DETAIL_REDACTED]"
    text = re.sub(r"https?://\S+", "[URL_REDACTED]", text, flags=re.I)
    text = re.sub(
        r"(?i)(?:bearer\s+|(?:token|cookie)\s*[:=]\s*|authorization\s*[:=]\s*(?:bearer\s+)?|x-skill-token\s*[:=]\s*)\S+",
        "[CREDENTIAL_REDACTED]", text)
    text = re.sub(r"(?i)\b(?:request_?id|trace_?id)\s*[:=]\s*\S+", "[ID_REDACTED]", text)
    text = re.sub(r"(?i)\b(?:request|body|payload)\s*[:=].*$", "[REQUEST_BODY_REDACTED]", text)
    text = re.sub(r"\{.*\}", "[REQUEST_BODY_REDACTED]", text, flags=re.S)
    text = re.sub(r"(?:/Users|/home|/var|[A-Za-z]:\\)\S+", "[PATH_REDACTED]", text)
    return " ".join(text.split())[:256]


def _read_http_error_meta(error: urllib.error.HTTPError) -> Tuple[Any, str]:
    """从 HTTPError 响应体提取 code/msg。"""
    try:
        payload = json.loads(error.read(65537).decode("utf-8"))
    except Exception:
        return f"HTTP_{error.code}", ""
    if not isinstance(payload, Mapping):
        return f"HTTP_{error.code}", ""
    code = payload.get("code", payload.get("retcode"))
    msg = payload.get("msg", payload.get("message", ""))
    if code in (None, 0, "0", "OK", "ok"):
        code = f"HTTP_{error.code}"
    return code, _safe_backend_message(msg)


def _swap_base(url: str, base: str) -> str:
    """把 url 的 host 替换为 base；裸 path 直接拼 base。"""
    parts = urllib.parse.urlsplit(url)
    if not parts.scheme and not parts.netloc:
        return f"{base.rstrip('/')}{url}"
    tail = parts.path or ""
    if parts.query:
        tail = f"{tail}?{parts.query}"
    if parts.fragment:
        tail = f"{tail}#{parts.fragment}"
    return f"{base.rstrip('/')}{tail}"


# ---------------------------------------------------------------------------
# HTTP 调用
# ---------------------------------------------------------------------------

_SKILL_TOKEN_HEADER = ***REDACTED***

# 触发跨环境 fallback 的错误码：10034(introspect unauthorized) / HTTP 401/403 / AUTH_REQUIRED
_AUTH_FAILURE_CODES = frozenset({"10034", "HTTP_401", "HTTP_403", "AUTH_REQUIRED"})
_OK_CODES: Tuple[Any, ...] = (0, "0", "OK", "ok")


def _is_auth_failure(code: Any) -> bool:
    return code is not None and str(code).strip() in _AUTH_FAILURE_CODES


def _do_http_request(
    method: str, url: str, token: str, *,
    params: Optional[Mapping[str, Any]] = None,
    body: Optional[Mapping[str, Any]] = None,
    timeout: float = 15.0,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> HttpResponse:
    """单次 HTTP 请求，不做 fallback。"""
    if not token and not is_sandbox():
        ***REDACTED***
    if not url:
        raise HttpError("missing url", error_code="INVALID_PARAMS")

    full_url = url
    if params:
        qs = urllib.parse.urlencode(
            {k: v for k, v in params.items() if v is not None}, doseq=True)
        if qs:
            full_url = f"{full_url}{'&' if '?' in full_url else '?'}{qs}"

    headers: Dict[str, str] = {
        "Accept": "*/*", "Accept-Language": "zh-CN", "User-Agent": USER_AGENT,
    }
    if token:
        ***REDACTED***
    data: Optional[bytes] = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        try:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError) as e:
            raise HttpError("invalid body", error_code="INVALID_PARAMS") from e
    if extra_headers:
        for k, v in extra_headers.items():
            if k and v is not None:
                headers[str(k)] = str(v)

    req = urllib.request.Request(full_url, data=data, method=method.upper(), headers=headers)
    ctx = (ssl._create_unverified_context() if os.environ.get("KS_SSL_INSECURE") == "1"
           else ssl.create_default_context())

    traceid: Optional[str] = None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            status = getattr(resp, "status", 200)
            resp_headers = getattr(resp, "headers", None)
            if not resp_headers:
                try:
                    resp_headers = resp.info()
                except Exception:
                    resp_headers = None
            traceid = _extract_traceid(resp_headers)
            raw = resp.read()
    except urllib.error.HTTPError as e:
        traceid = _extract_traceid(getattr(e, "headers", None))
        ec, msg = _read_http_error_meta(e)
        raise HttpError("http request rejected", error_code=ec,
                        backend_message=msg, traceid=traceid) from e
    except urllib.error.URLError as e:
        raise HttpError("network error", error_code="NETWORK_ERROR") from e
    except Exception as e:
        raise HttpError("request failed", error_code="TEMPORARY_ERROR", traceid=traceid) from e

    if not (200 <= status < 300):
        raise HttpError("http request rejected", error_code=f"HTTP_{status}", traceid=traceid)

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise HttpError("json parse failed", error_code="INVALID_RESPONSE", traceid=traceid) from e
    if not isinstance(payload, Mapping):
        raise HttpError("json payload is not object", error_code="INVALID_RESPONSE", traceid=traceid)

    response = HttpResponse(payload, traceid=traceid)
    biz_code = response.get("code", response.get("retcode"))
    if biz_code is not None and biz_code not in _OK_CODES:
        raise HttpError("business request rejected", error_code=biz_code,
                        backend_message=response.get("msg", response.get("message", "")),
                        traceid=traceid)
    return response


def http_request(
    method: str, url: str, token: str, *,
    params: Optional[Mapping[str, Any]] = None,
    body: Optional[Mapping[str, Any]] = None,
    timeout: float = 15.0,
    extra_headers: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """发送 HTTP 请求，自动注入鉴权头。

    客户端模式首次请求若鉴权失败，会自动切另一环境重试并锁定成功的 base。
    """
    kwargs = dict(params=params, body=body, timeout=timeout, extra_headers=extra_headers)

    if _base_locked:
        return _do_http_request(method, url, token, **kwargs)

    # 首次请求：依序探测候选 base，任一成功即锁定
    first_err: Optional[HttpError] = None
    for base in _client_api_bases():
        try:
            resp = _do_http_request(method, _swap_base(url, base), token, **kwargs)
        except HttpError as e:
            if not _is_auth_failure(e.error_code):
                raise
            if first_err is None:
                first_err = e
            continue
        _lock_api_base(base)
        return resp

    raise HttpError(
        "http request rejected on both environments",
        error_code=first_err.error_code if first_err else "AUTH_REQUIRED",
        backend_message="token 在生产与 staging 环境均鉴权失败；请确认 token 未过期且客户端登录正常",
        traceid=first_err.traceid if first_err else None,
    )


# ---------------------------------------------------------------------------
# 响应解包
# ---------------------------------------------------------------------------

def unwrap_data(envelope: Mapping[str, Any]) -> Dict[str, Any]:
    """从 {code, msg, data} 信封中取出 data；非成功抛 HttpError。"""
    traceid = getattr(envelope, "traceid", None)
    if not isinstance(envelope, Mapping):
        raise HttpError("invalid envelope", error_code="INVALID_RESPONSE", traceid=traceid)
    code = envelope.get("code", envelope.get("retcode"))
    if code not in _OK_CODES:
        raise HttpError("business request rejected", error_code=code,
                        backend_message=envelope.get("msg", envelope.get("message", "")),
                        traceid=traceid)
    data = envelope.get("data") or envelope.get("result", {}) or {}
    if not isinstance(data, Mapping):
        raise HttpError("data is not object", error_code="INVALID_RESPONSE", traceid=traceid)
    return dict(data)


# ---------------------------------------------------------------------------
# 输出
# ---------------------------------------------------------------------------

def safe_print(line: str) -> None:
    """stdout 唯一出口；自动 redact。"""
    try:
        sys.stdout.write(redact(line))
        if not line.endswith("\n"):
            sys.stdout.write("\n")
    except Exception:
        pass


def error_exit(message: str, code: int = 0, traceid: Optional[str] = None) -> "None":
    """输出结构化错误 JSON 后退出。"""
    payload: Dict[str, str] = {"error": redact(message)}
    if traceid:
        payload["traceid"] = redact(traceid)
    safe_print(json.dumps(payload, ensure_ascii=False))
    try:
        sys.stdout.flush()
    except Exception:
        pass
    sys.exit(code)


__all__ = [
    "API_BASE", "USER_AGENT",
    "HttpError", "HttpResponse",
    "is_sandbox", "build_url",
    "read_token_from_stdin", "register_token_arg", "acquire_token",
    "http_request", "unwrap_data",
    "redact", "safe_print", "error_exit",
]
