#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
腾讯电子签合同AI工具主入口
支持 Python 2.7+ / 3.x，零第三方依赖。

导出文件（合同 docx / 审查批注与摘要 / 对比报告与明细）在获取到链接后
自动下载到技能根目录 downloads/ 下；JSON 输出中的 _downloaded_files 为已
下载文件的本地绝对路径（下载失败时回退为输出原链接，_downloaded_files 为空）。

Usage:
    python3 scripts/tencent_esign.py <command> [args...]

Commands:
    auth-check                          检查 Token 是否已配置
    auth-save   <token>                 保存 Token
    auth-validate <token>               验证并保存 Token
    upload      <file...>               上传文件(支持多个)，返回 ResourceId
    call        <action> '<json>'       调用任意 API
    wait-draft  <task_id>               轮询起草任务直到完成，返回含 _links_md
    wait-review <task_id>               轮询单个审查任务直到完成
    wait-compare <task_id> [原文件名]    轮询对比任务直到完成，自动下载报告到 ./downloads/（文件名：原文件名_对比报告/差异明细）
    review-batch '<["id1","id2"]>'      轮询多个审查任务并返回摘要+链接（多文件必用）
    review-links <task_id>              获取已完成审查任务的预览/下载链接列表
    compare-links <task_id> [原文件名]   获取已完成对比任务的预览/下载链接并自动下载（文件名规则同 wait-compare）
    review-progress-url <task_id>       获取审查进行中的实时查看链接
    compare-progress-url <task_id>      获取对比进行中的实时查看链接
    search-laws '<json>'                法条检索，返回结构化结果列表
    version                             显示版本信息
"""

import json
import os
import re
import socket
import ssl
import sys
import time
import uuid

PY3 = sys.version_info[0] >= 3

if PY3:
    from http.client import HTTPSConnection, HTTPConnection
    from urllib.parse import urlparse, urljoin
    from pathlib import Path
else:
    from httplib import HTTPSConnection, HTTPConnection
    from urlparse import urlparse, urljoin

TOKEN_FILE = os.path.join(os.path.expanduser("~"), ".esign-token")


# ---------------------------------------------------------------------------
# Config (cached at module level)
# ---------------------------------------------------------------------------

_config_cache = None

_DEFAULT_CONFIG = {
    "baseUrl": "https://appgw.ess.tencent.cn/plugin/openapi/",
    "fileUploadUrl": "https://file.ess.tencent.cn/upload/",
    "version": "v1.2.0",
}

def load_config():
    global _config_cache
    if _config_cache is not None:
        return _config_cache
    if PY3:
        script_dir = str(Path(__file__).parent.absolute())
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(script_dir, "config.json")
    try:
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                cfg = json.load(f)
            merged = dict(_DEFAULT_CONFIG)
            merged.update(cfg)
            _config_cache = merged
        else:
            _config_cache = dict(_DEFAULT_CONFIG)
    except (IOError, ValueError, OSError) as e:
        sys.stderr.write("Warning: config.json 读取失败 (%s)，使用默认配置\n" % str(e))
        _config_cache = dict(_DEFAULT_CONFIG)
    return _config_cache


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------

def get_token():
    """Token 统一从 ~/.esign-token 文件读取（由 auth-save / auth-validate 命令写入），不读环境变量。

    单一数据源：写入即生效，不存在环境变量旧值遮蔽文件新值的问题。
    """
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                t = f.read().strip()
            if t and t != "***************":   # 掩码防护：防止脱敏值被误当真 Token
                return t
    except (IOError, OSError) as e:
        sys.stderr.write("Warning: 读取 Token 文件失败: %s\n" % str(e))
    return ""


def save_token(token):
    try:
        token_dir = os.path.dirname(TOKEN_FILE)
        if token_dir and not os.path.exists(token_dir):
            os.makedirs(token_dir)
        with open(TOKEN_FILE, "w") as f:
            f.write(token.strip())
        try:
            os.chmod(TOKEN_FILE, 0o600)
        except Exception:
            pass
        return TOKEN_FILE
    except (IOError, OSError) as e:
        sys.stderr.write("Warning: 保存 Token 失败: %s\n" % str(e))
        return None


# ---------------------------------------------------------------------------
# HTTP (persistent connections with auto-reconnect)
# ---------------------------------------------------------------------------

_conn_pool = {}

MAX_RETRIES = 3


def _get_conn(url):
    """Get or create a persistent HTTPS/HTTP connection for the given URL's host."""
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme

    if not host:
        raise ValueError("无效的 URL: %s" % url)

    key = "%s:%s:%s" % (scheme, host, port or (443 if scheme == "https" else 80))

    conn = _conn_pool.get(key)
    if conn is not None:
        return conn, parsed

    if scheme == "https":
        ctx = ssl.create_default_context()
        conn = HTTPSConnection(host, port or 443, timeout=120, context=ctx)
    else:
        conn = HTTPConnection(host, port or 80, timeout=120)

    _conn_pool[key] = conn
    return conn, parsed


def _drop_conn(url):
    """Remove a cached connection (call after unrecoverable errors)."""
    parsed = urlparse(url)
    key = "%s:%s:%s" % (parsed.scheme, parsed.hostname,
                        parsed.port or (443 if parsed.scheme == "https" else 80))
    conn = _conn_pool.pop(key, None)
    if conn:
        try:
            conn.close()
        except Exception:
            pass


def _parse_response(raw, status_code):
    """Parse HTTP response body, tolerating empty or non-JSON content."""
    if not raw or not raw.strip():
        if 200 <= status_code < 300:
            return {"Response": {}}
        return {"error": "HTTP %d: (空响应)" % status_code}
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {"error": "HTTP %d: %s" % (status_code, raw[:500])}


def _request(url, method, body, headers, timeout=120):
    """Send an HTTP request with connection reuse. Retries up to MAX_RETRIES on transient failures."""
    if not url:
        return {"error": "URL 未配置，请检查 config.json 或环境变量。"}

    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            conn, parsed = _get_conn(url)
            path = parsed.path
            if parsed.query:
                path = path + "?" + parsed.query

            conn.timeout = timeout
            conn.request(method, path or "/", body=body, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            if PY3:
                raw = raw.decode("utf-8")

            if resp.status in (502, 503, 504) and attempt < MAX_RETRIES - 1:
                sys.stderr.write("HTTP %d, 第 %d 次重试...\n" % (resp.status, attempt + 1))
                _drop_conn(url)
                time.sleep(min(2 ** attempt, 5))
                continue

            return _parse_response(raw, resp.status)

        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            last_err = e
            _drop_conn(url)
            if attempt < MAX_RETRIES - 1:
                wait = min(2 ** attempt, 5)
                sys.stderr.write("连接异常 (%s), %ds 后第 %d 次重试...\n" % (str(e), wait, attempt + 1))
                time.sleep(wait)

    return {"error": "网络错误 (重试 %d 次后失败): %s" % (MAX_RETRIES, str(last_err))}


# ---------------------------------------------------------------------------
# File download (export files land in the skill's downloads/ directory)
# ---------------------------------------------------------------------------

CONTENT_TYPE_EXT_MAP = {
    "application/pdf": ".pdf",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
}

_FILENAME_UNSAFE_RE = re.compile(r'[\\/:*?"<>|\r\n\t]')

_KNOWN_EXTS = (".pdf", ".doc", ".docx", ".xls", ".xlsx")

DOWNLOAD_MAX_REDIRECTS = 5


def _sanitize_filename(name):
    cleaned = _FILENAME_UNSAFE_RE.sub("_", (name or "").strip()).strip(" .")
    return cleaned[:80] if cleaned else "file"


def _strip_known_ext(name):
    low = (name or "").lower()
    for e in _KNOWN_EXTS:
        if low.endswith(e):
            return (name or "")[:-len(e)]
    return name or ""


def _get_download_dir():
    """下载目录：技能根目录下的 downloads/（基于脚本自身位置定位，不依赖 cwd）。"""
    skill_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(skill_root, "downloads")
    if not os.path.exists(d):
        os.makedirs(d)
    return d


def _unique_path(directory, filename):
    candidate = os.path.join(directory, filename)
    base, ext = os.path.splitext(filename)
    i = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, "%s(%d)%s" % (base, i, ext))
        i += 1
    return candidate


def _ext_from_url(url):
    ext = os.path.splitext(os.path.basename(urlparse(url).path))[1]
    if ext and 1 < len(ext) <= 6 and ext[1:].isalnum():
        return ext.lower()
    return ""


def _is_internal_host(host):
    """SSRF 防护：拒绝内网/私有网段地址；解析失败视为不安全。"""
    if not host:
        return True
    h = host.strip().lower()
    if h == "localhost" or h.endswith(".local") or h.endswith(".internal"):
        return True
    try:
        ip = socket.gethostbyname(h)
    except Exception:
        return True
    parts = ip.split(".")
    if len(parts) != 4:
        return True
    try:
        a, b = int(parts[0]), int(parts[1])
    except ValueError:
        return True
    if a in (0, 9, 10, 11, 21, 30, 127) or a >= 224:
        return True
    if a == 169 and b == 254:
        return True
    if a == 192 and b == 168:
        return True
    if a == 172 and 16 <= b <= 31:
        return True
    return False


def _download_file(url, base_name, default_ext=".bin", max_redirects=DOWNLOAD_MAX_REDIRECTS):
    """下载 url 到技能目录 downloads/ 下。返回 (本地绝对路径, None) 或 (None, 错误信息)。

    - 手动跟随 301/302/303/307/308 重定向（上限 max_redirects），每跳校验目标 host 非内网
    - 5xx / 网络异常指数退避重试（共 MAX_RETRIES 次尝试）
    - 扩展名三级推断：URL path → Content-Type → 调用方默认值
    - 同名文件自动加 (1)(2) 序号，不覆盖已有文件
    - 预签名 URL 无需鉴权头（与 API 网关不同域，连接池按 host 天然隔离）
    - 失败原因仅由调用方记录到 stderr，输出回退为原链接文案，不向用户暴露
    """
    if not url:
        return None, "URL 为空"
    last_err = None
    for attempt in range(MAX_RETRIES):
        current = url
        try:
            for _ in range(max_redirects + 1):
                parsed = urlparse(current)
                host = parsed.hostname or ""
                if _is_internal_host(host):
                    return None, "目标地址为内网/无效主机，已拒绝下载: %s" % host
                conn, _p = _get_conn(current)
                path = parsed.path
                if parsed.query:
                    path = path + "?" + parsed.query
                conn.request("GET", path or "/", headers={"Accept": "*/*"})
                resp = conn.getresponse()
                if resp.status in (301, 302, 303, 307, 308):
                    loc = resp.getheader("Location") or ""
                    resp.read()
                    if not loc:
                        return None, "HTTP %d 且缺少 Location" % resp.status
                    current = urljoin(current, loc)
                    continue
                if resp.status == 200:
                    content_type = (resp.getheader("Content-Type") or "").split(";")[0].strip().lower()
                    ext = _ext_from_url(current) or CONTENT_TYPE_EXT_MAP.get(content_type, "") or default_ext
                    filename = _sanitize_filename(_strip_known_ext(base_name)) + ext
                    final_path = _unique_path(_get_download_dir(), filename)
                    with open(final_path, "wb") as f:
                        while True:
                            chunk = resp.read(65536)
                            if not chunk:
                                break
                            f.write(chunk)
                    return final_path, None
                if resp.status >= 500:
                    resp.read()
                    raise IOError("HTTP %d" % resp.status)
                resp.read()
                return None, "HTTP %d" % resp.status
            return None, "重定向次数超限（>%d 次）" % max_redirects
        except Exception as e:
            last_err = e
            _drop_conn(current)
            if attempt < MAX_RETRIES - 1:
                wait = min(2 ** attempt, 5)
                sys.stderr.write("下载异常 (%s), %ds 后第 %d 次重试...\n" % (str(e), wait, attempt + 1))
                time.sleep(wait)
    return None, "下载失败 (重试 %d 次后): %s" % (MAX_RETRIES, str(last_err))


def _format_export_line(url, local_path, link_text, local_text, fail_text):
    """导出行三态：已下载→本地路径文案；有 URL→原链接文案（与自动下载功能加入前逐字一致）；无 URL→失败提示。"""
    if local_path:
        return local_text % local_path
    if url:
        return link_text % url
    return fail_text


def call_api(action, params, token=None):
    if token is None:
        token = get_token()
    if not token:
        return {"error": "Token 未配置。请先运行 auth-validate <token>（推荐，验证后写入 ~/.esign-token）或 auth-save <token>。"}

    cfg = load_config()
    url = os.environ.get("ESIGN_BASE_URL", cfg.get("baseUrl", ""))

    if "Action" not in params:
        params["Action"] = action

    _PLATFORM_ACTIONS = {
        "CreateDraftContractByPromptsTask",
        "CreateBatchContractReviewTask",
        "CreateContractComparisonTask",
        "DescribeRiskIdentificationLawDocuments",
    }
    _KNOWN_PLATFORMS = {"claude code", "codebuddy", "workbuddy", "qclaw", "codex"}
    if action in _PLATFORM_ACTIONS:
        val = (params.get("SkillPlatformName") or "").strip()
        if not val or val.lower() not in _KNOWN_PLATFORMS:
            params["SkillPlatformName"] = "其它"

    body = json.dumps(params, ensure_ascii=False)
    if PY3:
        body = body.encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "X-Tc-Version": "2020-11-11",
        "x-tc-action": action,
        "Authorization": token,
        "X-Skill-Version": cfg.get("version", "v1.0.0"),
    }

    return _request(url, "POST", body, headers, timeout=120)


# ---------------------------------------------------------------------------
# Auth commands
# ---------------------------------------------------------------------------

def cmd_auth_check():
    token = get_token()
    if token:
        out({"success": True, "message": "Token 已配置", "preview": token[:8] + "..."})
    else:
        out({"success": False, "message": "未找到 Token。请前往 https://qian.tencent.com/aiSkill 获取 SIGN-TOKEN。"})
        sys.exit(1)


def cmd_auth_save(token):
    path = save_token(token)
    if path:
        out({"success": True, "message": "Token 已保存至 " + path})
    else:
        out({"success": False, "message": "Token 保存失败，请检查 ~/.esign-token 的写入权限。"})
        sys.exit(1)


def cmd_auth_validate(token):
    result = call_api("DescribeContractReviewTask",
                      {"Action": "DescribeContractReviewTask", "TaskId": "__validate__"},
                      token=token)
    auth_fail = False
    server_error = False
    if "error" in result:
        err = str(result["error"]).lower()
        for kw in ("401", "403", "unauthorized", "authfailure", "invalidcredential", "forbidden"):
            if kw in err:
                auth_fail = True
                break
        for kw in ("500", "502", "503", "429", "timeout", "network error"):
            if kw in err:
                server_error = True
                break
    else:
        resp = result.get("Response", {})
        if "Error" in resp:
            code = resp["Error"].get("Code", "")
            auth_codes = ("AuthFailure", "UnauthorizedOperation", "InvalidCredential",
                          "AuthFailure.SignatureFailure", "AuthFailure.TokenFailure")
            if code in auth_codes:
                auth_fail = True
            elif code in ("InternalError", "RequestLimitExceeded"):
                server_error = True

    if auth_fail:
        out({"success": False, "message": "Token 验证失败。请前往 https://qian.tencent.com/aiSkill 重新获取 SIGN-TOKEN。"})
        sys.exit(1)
    elif server_error:
        out({"success": False, "message": "服务暂时不可用，无法验证 Token，请稍后重试。", "detail": result})
        sys.exit(1)
    else:
        path = save_token(token)
        if path:
            out({"success": True, "message": "已成功安装。Token 已验证并保存。", "path": path})
        else:
            out({"success": True, "message": "Token 验证通过，但保存到 ~/.esign-token 失败，请检查 home 目录写入权限。"})


# ---------------------------------------------------------------------------
# Upload (multipart/form-data to dedicated file endpoint)
# ---------------------------------------------------------------------------

def build_multipart(file_paths, business_type="DOCUMENT"):
    boundary = "----EsignBoundary" + uuid.uuid4().hex
    parts = []

    # business_type field
    header = (
        "--%s\r\n"
        "Content-Disposition: form-data; name=\"business_type\"\r\n"
        "\r\n"
        "%s\r\n" % (boundary, business_type)
    )
    parts.append(header.encode("utf-8") if PY3 else header)

    # file fields
    for fp in file_paths:
        fname = os.path.basename(fp).replace('"', '\\"').replace('\n', '_')
        with open(fp, "rb") as f:
            data = f.read()
        header = (
            "--%s\r\n"
            "Content-Disposition: form-data; name=\"file\"; filename=\"%s\"\r\n"
            "Content-Type: application/octet-stream\r\n"
            "\r\n" % (boundary, fname)
        )
        if PY3:
            parts.append(header.encode("utf-8") + data + b"\r\n")
        else:
            parts.append(header + data + b"\r\n")

    footer = ("--%s--\r\n" % boundary)
    parts.append(footer.encode("utf-8") if PY3 else footer)

    body = b"".join(parts)
    content_type = "multipart/form-data; boundary=%s" % boundary
    return body, content_type


def upload_single(file_path, token, url):
    try:
        body, content_type = build_multipart([file_path])
    except (IOError, OSError) as e:
        return {"error": "读取文件失败 (%s): %s" % (file_path, str(e))}
    headers = {
        "Content-Type": content_type,
        "AccessToken": token,
    }
    return _request(url, "POST", body, headers, timeout=300)


def cmd_upload(file_paths):
    for fp in file_paths:
        if not os.path.exists(fp):
            out({"error": "文件不存在: " + fp})
            sys.exit(1)

    token = get_token()
    if not token:
        out({"error": "Token 未配置。请先运行 auth-validate <token>（推荐，验证后写入 ~/.esign-token）或 auth-save <token>。"})
        sys.exit(1)

    cfg = load_config()
    url = os.environ.get("ESIGN_FILE_URL", cfg.get("fileUploadUrl", ""))

    if len(file_paths) == 1:
        result = upload_single(file_paths[0], token, url)
        out(result)
        if "error" in result:
            sys.exit(1)
    else:
        results = []
        resource_ids = []
        for fp in file_paths:
            result = upload_single(fp, token, url)
            results.append(result)
            if "error" in result:
                out({"error": "上传 %s 失败" % fp, "detail": result})
                sys.exit(1)
            rid = result.get("Response", {}).get("ResourceId", "")
            resource_ids.append(rid)
            sys.stderr.write("已上传: %s -> %s\n" % (os.path.basename(fp), rid))
        out({"Response": {"ResourceIds": resource_ids, "TotalCount": len(resource_ids), "Details": results}})


# ---------------------------------------------------------------------------
# Generic call
# ---------------------------------------------------------------------------

def cmd_call(action, params_json):
    try:
        params = json.loads(params_json)
    except Exception as e:
        out({"error": "JSON 解析失败: %s" % str(e)})
        sys.exit(1)
    out(call_api(action, params))


# ---------------------------------------------------------------------------
# Polling helpers
# ---------------------------------------------------------------------------

MAX_POLL_ERRORS = 5

def poll(action, task_id, success_status, fail_status, max_wait=600, exit_on_fail=True):
    """Poll until task reaches a terminal status or max_wait is exceeded.

    Never gives up early due to transient network/API errors — only a terminal
    status from the server (success or fail) or a timeout stops the loop.
    Consecutive errors are logged and counted, but polling continues until the
    server explicitly signals completion or max_wait seconds have elapsed.

    If exit_on_fail=False, returns the result even on fail_status instead of
    calling sys.exit(). Useful for batch processing where individual failures
    should not abort the whole run.
    """
    interval = 3
    elapsed = 0
    consecutive_errors = 0
    while elapsed < max_wait:
        result = call_api(action, {"Action": action, "TaskId": task_id})
        if "error" in result:
            consecutive_errors += 1
            sys.stderr.write("轮询出错 (%d/%d，继续等待): %s\n" % (consecutive_errors, MAX_POLL_ERRORS, result["error"]))
            # Log a warning after MAX_POLL_ERRORS consecutive failures, but keep polling.
            if consecutive_errors >= MAX_POLL_ERRORS:
                sys.stderr.write("警告: 已连续 %d 次轮询出错，继续等待服务端响应...\n" % consecutive_errors)
            time.sleep(interval)
            elapsed += interval
            interval = min(int(interval + 2), 10)
            continue
        consecutive_errors = 0
        resp = result.get("Response", {})
        if "Error" in resp:
            err_code = resp["Error"].get("Code", "")
            sys.stderr.write("服务端错误 (%s)，等待后重试...\n" % err_code)
            time.sleep(interval)
            elapsed += interval
            interval = min(int(interval + 2), 10)
            continue
        status = resp.get("Status", -1)
        status_labels = {
            "DescribeDraftContractByPromptsTask": {0: "已创建", 1: "执行中", 2: "成功", 3: "失败"},
            "DescribeContractReviewTask":         {1: "创建成功", 2: "排队中", 3: "执行中", 4: "成功", 5: "失败"},
            "DescribeContractComparisonTask":     {0: "待创建", 1: "对比中", 2: "成功", 3: "失败"},
        }
        label = status_labels.get(action, {}).get(status, "未知")
        if status in (success_status if isinstance(success_status, (list, tuple)) else [success_status]):
            sys.stderr.write("[%s] 任务 %s 状态: %s(%s) ✓\n" % (action, task_id, label, status))
            return result
        if status in (fail_status if isinstance(fail_status, (list, tuple)) else [fail_status]):
            sys.stderr.write("[%s] 任务 %s 状态: %s(%s) ✗\n" % (action, task_id, label, status))
            if exit_on_fail:
                out(result)
                sys.exit(1)
            else:
                return result
        sys.stderr.write("[%s] 任务 %s 状态: %s(%s), 已等待 %ds, %ds 后再次查询...\n" % (
            action, task_id, label, status, elapsed, interval))
        time.sleep(interval)
        elapsed += interval
        interval = min(int(interval + 2), 10)
    if exit_on_fail:
        out({"error": "超时 (%d秒)" % max_wait})
        sys.exit(1)
    return {"error": "超时 (%d秒)" % max_wait}


def cmd_wait_draft(task_id, is_revision=False):
    result = poll("DescribeDraftContractByPromptsTask", task_id, success_status=2, fail_status=3, max_wait=600)
    resp = result.get("Response", {})
    name = resp.get("ContractName", "")
    url = resp.get("ContractUrl", "")
    status = resp.get("Status", -1)
    if url:
        dl_path, dl_err = _download_file(url, (name if name else "合同") + "_起草合同", default_ext=".docx")
        if dl_path:
            result["_links_md"] = "📄 合同《%s》已下载到本地：`%s`（请前往该目录查看）" % (
                name if name else "合同", dl_path)
            result["_downloaded_files"] = [dl_path]
        else:
            sys.stderr.write("[WARN] wait-draft: 合同文件自动下载失败 (%s)，回退为链接输出\n" % dl_err)
            result["_links_md"] = "📄 [点击下载《%s》](%s)（链接 20 分钟内有效）" % (name if name else "合同", url)
    else:
        sys.stderr.write("[WARN] wait-draft: ContractUrl 为空 (task_id=%s), 完整响应: %s\n" % (
            task_id, json.dumps(resp, ensure_ascii=False)))
        result["_links_md"] = ""
    if status == 2:
        if is_revision:
            result["_next_steps"] = (
                "还需要继续调整吗？\n"
                "- **a. 继续修改** — 告诉我需要调整的内容\n"
                "- **b. 下载保存** — 直接使用\n"
                "- **c. 签署合同** — 直接发起和签署合同"
            )
        else:
            result["_next_steps"] = (
                "接下来你可以：\n"
                "- **a. 修改合同** — 告诉我需要调整的内容\n"
                "- **b. 下载保存** — 直接使用\n"
                "- **c. 签署合同** — 直接发起和签署合同\n"
                "- **d. 刷新链接** — 重新获取下载链接（链接过期时使用）"
            )
    out(result)


def cmd_wait_review(task_id, limit=10, offset=0):
    """Wait for review task and return formatted risk summary with pagination.

    Returns:
        _summary: overview line (total risks, high risk count)
        _risks_md: pre-formatted markdown table of risks (sorted by severity)
        _has_more: True if there are more risks beyond the current page
 

... [Content truncated, total 54,264 chars] ...