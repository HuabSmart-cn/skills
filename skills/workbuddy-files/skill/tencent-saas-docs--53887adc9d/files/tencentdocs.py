#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tencentdocs.py —— 腾讯文档 MCP Skill 调用入口（插件版，纯 Python 标准库 / 跨平台 / 不落盘）。

与 setup.sh 等价的 Python 实现，解决 Windows 下无 bash/curl 无法使用的问题。

设计要点（与 setup.sh 完全一致的契约）：
  1. 不走 OAuth；票据由宿主（如 WorkBuddy）通过环境变量注入：
       TDOC_OAUTH_ACCESS_TOKEN  → C 端 OAuth token（透传 Authorization: ***REDACTED***
       TDOC_ONEID_ACCESS_TOKEN  → SaaS 端 OneID token（透传 X-Oneid-Access-Token）
     二者可同时存在（双票场景，服务端 mcp_dualtoken_middleware 处理）。
  2. 纯标准库 urllib，无 curl / requests / mcporter 依赖；票据仅在内存里通过 HTTP
     header 即时透传，不写入任何文件。
  3. 默认走系统代理（读 HTTP_PROXY / HTTPS_PROXY 环境变量）；可用 --no-proxy 绕过。
  4. 4 个 MCP endpoint，按 service 名路由：tencent-docs / slide-mcp / doc-mcp / sheet-mcp

用法（供 AI Agent 调用）：
    python3 tencentdocs.py tdoc_init
        → READY 或 ERROR:*

    python3 tencentdocs.py tdoc_call <service> <tool> [json_args]
        例：python3 tencentdocs.py tdoc_call tencent-saas-docs manage.recent_online_file '{"num":10}'
            python3 tencentdocs.py tdoc_call slide-mcp slide_add_shape '{"file_id":"xxx"}'

    python3 tencentdocs.py tdoc_list <service>
        → 原样输出该 endpoint 的 tools/list JSON-RPC 响应

    python3 tencentdocs.py tdoc_schema <service> <tool>
        → 输出单个工具的描述与完整参数（inputSchema）。
        ★ 调用 tdoc_call 之前，必须先用本命令拿到该工具的真实参数定义，
          按定义传参，严禁凭记忆/猜测拼参数。

可选参数：
    --no-proxy        本次请求绕过所有代理（默认走系统代理）
    --timeout <秒>    覆盖 HTTP 超时（默认取 TDOC_HTTP_TIMEOUT 或 120）
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

# ── 端点配置（SaaS 版 saas.docs.qq.com；个人版仅需改这三行） ────────────────────────
API_BASE = os.environ.get("TDOC_API_BASE_URL", "https://saas.docs.qq.com")
MAIN_SERVICE = "tencent-saas-docs"
# ── 身份契约（issue #76568）─────────────────────────────────────────────────
# SaaS 端点只认 OneID 票据（X-Oneid-Access-Token）。C 端 OAuth 票据仅在「双票」
# 场景作附带项；只有 C 端票时打 SaaS 端点必然 401 invalid_token。
REQUIRED_TICKET = "oneid"
IDENTITY_LABEL = "企业版（SaaS，OneID 票据）"
PEER_SKILL = "tencent-docs"
PEER_IDENTITY_LABEL = "个人版（QQ / 微信，C 端 OAuth 票据）"
MCP_URLS = {
    MAIN_SERVICE: f"{API_BASE}/api/v6/open/agent/mcp",
    "slide-mcp": f"{API_BASE}/api/v6/slide/mcp",
    "doc-mcp": f"{API_BASE}/api/v6/doc/mcp",
    "sheet-mcp": f"{API_BASE}/api/v6/sheet/mcp",
}
HTTP_TIMEOUT = int(os.environ.get("TDOC_HTTP_TIMEOUT", "120"))
_SERVICE_HINT = " / ".join(MCP_URLS)


def _debug(msg):
    if os.environ.get("TDOC_DEBUG") == "1" or os.environ.get("WORKBUDDY_TDOC_DEBUG") == "1":
        print(f"[TencentDocsSkillCredential] {msg}", file=***REDACTED***


# 最近一次网关凭据回退的失败原因（短标记，不含任何票据内容）；由 _load_tokens 写入，
# 拼进 ERROR:no_token 带出来。issue #101620 里这条链路静默失败：宿主日志零命中、
# skill 只吐一句 no_token，"配置缺失 / 网关不可达 / 401 / 连接器没连"四种失败模式无法区分。
_gateway_error = ""


def _no_token_hint():
    ***REDACTED***
    return f"（凭据获取失败：{_gateway_error}）" if _gateway_error else ""


# ── 票据加载：环境变量优先，回退 V2 MCP Gateway session provider ──────────────
def _load_tokens():
    ***REDACTED***
    global _gateway_error
    _gateway_error = ""
    oauth = os.environ.get("TDOC_OAUTH_ACCESS_TOKEN", "")
    oneid = os.environ.get("TDOC_ONEID_ACCESS_TOKEN", "")
    if oauth or oneid:
        _debug("using existing TDOC_* env tokens")
        return oauth, oneid

    cfg_raw = os.environ.get("CODEBUDDY_MCP_CONFIG")
    if not cfg_raw:
        _gateway_error = "no_mcp_config"
        _debug("no CODEBUDDY_MCP_CONFIG; skip V2 MCP Gateway credential provider")
        return oauth, oneid

    try:
        cfg = json.loads(cfg_raw)
        servers = cfg.get("mcpServers") or {}
        # 宿主 V2 MCP Gateway 条目名是 connector-proxy（WORKBUDDY_MCP_SERVER_NAME，
        # 见 workbuddy-mcp-protocol.ts）；workbuddy 是迁移期保留的旧名，兜底兼容。
        server = servers.get("connector-proxy") or servers.get("workbuddy") or {}
        gateway_url = server.get("url") or ""
        # 网关这一组认证头必须整组透传：除 Authorization 外还有 X-WorkBuddy-MCP-Context
        # （宿主签发的会话信封）。local-mcp-host.ts::resolveRequestContext 对每条
        # authenticated route 都要求两者同时成立，只带 Authorization 会被判 401
        # invalid_mcp_context —— 凭据永远取不到，且宿主侧不会留下任何日志（issue #101620）。
        # 逐个挑头名会在宿主再加必需头时重蹈覆辙，所以整组照搬。
        gateway_headers = {
            name: value
            for name, value in (server.get("headers") or {}).items()
            if isinstance(name, str) and isinstance(value, str) and value
        }
    except Exception as e:  # noqa: BLE001
        _gateway_error = "bad_mcp_config"
        _debug(f"parse CODEBUDDY_MCP_CONFIG failed: {e}")
        return oauth, oneid

    has_authorization = ***REDACTED***
    if not (gateway_url.endswith("/mcp") and has_authorization):
        ***REDACTED***
        _debug("connector-proxy/workbuddy V2 MCP Gateway entry not found in CODEBUDDY_MCP_CONFIG")
        return oauth, oneid

    token_url = ***REDACTED***
    _debug(f"request V2 MCP Gateway credential provider: ***REDACTED***
           f"headers={sorted(gateway_headers)}")
    try:
        req = urllib.request.Request(token_url, headers=gateway_headers, method="GET")
        # token provider 走宿主本地，固定不走代理
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        personal = data.get("personal") or {}
        enterprise = data.get("enterprise") or {}
        if personal.get("available") and personal.get("token"):
            ***REDACTED***
        if enterprise.get("available") and enterprise.get("token"):
            ***REDACTED***
        if not oauth and not oneid:
            # provider 答了但两侧都没票：reason 就是连接器态（connector_disabled /
            # not_connected / token_unavailable），直接透出去，别再让人猜。
            _gateway_error = (f"provider personal={personal.get('reason') or 'token_unavailable'}"
                              f" enterprise={enterprise.get('reason') or 'token_unavailable'}")
    except urllib.error.HTTPError as e:
        _gateway_error = f"provider HTTP {e.code}"
        _debug(f"V2 MCP Gateway credential provider request failed: ***REDACTED***
    except Exception as e:  # noqa: BLE001
        _gateway_error = f"provider unreachable ({type(e).__name__})"
        _debug(f"V2 MCP Gateway credential provider request failed: ***REDACTED***
    _debug(f"token provider result personal=***REDACTED***
           f"enterprise={'available' if oneid else 'unavailable'}")
    return oauth, oneid


def _identity_mismatch_error(oauth, oneid):
    """票据类型与本 skill 身份不匹配时返回可执行报错文案；匹配返回 None。

    issue #76568：个人账号下 Agent 误选企业版 skill，把 C 端 OAuth 票据打到
    saas.docs.qq.com，服务端回 401 invalid_token；用户按提示反复解绑重连也没用，
    因为换的是 token 不是 endpoint。这里在发请求前就把它变成可路由的错误。
    """
    if REQUIRED_TICKET == "oneid" and not oneid:
        have = PEER_IDENTITY_LABEL if oauth else "无可用票据"
    elif REQUIRED_TICKET == "oauth" and not oauth:
        have = PEER_IDENTITY_LABEL if oneid else "无可用票据"
    else:
        return None
    return (f"ERROR:identity_mismatch - 本 skill 面向腾讯文档{IDENTITY_LABEL}（{API_BASE}），"
            f"当前宿主提供的是：{have}。请改用 {PEER_SKILL} skill 重试；"
            f"这不是授权失效，解绑/重连腾讯文档连接器不会改变结果。")


def _build_opener(no_proxy):
    """no_proxy=True 时绕过所有代理；否则走系统代理（urllib 默认读 *_PROXY 环境变量）。"""
    if no_proxy:
        return urllib.request.build_opener(urllib.request.ProxyHandler({}))
    return urllib.request.build_opener()  # 默认 ProxyHandler 读取系统/环境代理


# ── 发一条 JSON-RPC 请求，返回原始响应文本（兼容 SSE） ─────────────────────────
def _post_jsonrpc(url, payload, oauth, oneid, no_proxy, timeout):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if oauth:
        headers["Authorization"] = ***REDACTED***
    if oneid:
        headers["X-Oneid-Access-Token"] = ***REDACTED***

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    opener = _build_opener(no_proxy)
    try:
        with opener.open(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            ctype = resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as e:
        # --fail-with-body 等价：把后端原始报文带出来
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
        hint = ""
        if e.code in (401, 403):
            hint = (f" | 提示：{API_BASE} 拒绝了当前票据。本 skill 面向腾讯文档{IDENTITY_LABEL}；"
                    f"若你是{PEER_IDENTITY_LABEL}用户，请改用 {PEER_SKILL} skill，"
                    f"重复解绑/重连连接器不会改变结果。")
        print(f"ERROR:http_failed - HTTP {e.code} {e.reason} {detail}{hint}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"ERROR:http_failed - {e.reason}", file=sys.stderr)
        return None
    except OSError as e:
        print(f"ERROR:http_failed - {e}", file=sys.stderr)
        return None

    # SSE（text/event-stream）：抽取 data: 行拼回 JSON；普通 JSON 原样返回
    if "text/event-stream" in ctype:
        return _extract_sse_json(raw)
    return raw


def _extract_sse_json(raw):
    """从 SSE 报文里抽取最后一条 data: 负载（MCP 流式响应的最终结果）。"""
    data_lines = [ln[len("data:"):].strip() for ln in raw.splitlines()
                  if ln.startswith("data:")]
    if not data_lines:
        return raw  # 不是预期 SSE，原样返回
    # 取最后一个能解析为 JSON 的 data 段
    for chunk in reversed(data_lines):
        try:
            json.loads(chunk)
            return chunk
        except json.JSONDecodeError:
            continue
    return data_lines[-1]


def _resolve_url(service):
    return MCP_URLS.get(service)


def put_upload(upload_url, file_path, no_proxy=False, timeout=None):
    """把本地文件以 PUT 方式上传到 COS 预签名 URL（import_file.py 复用）。

    返回 HTTP 状态码；网络失败抛 OSError。Content-Type 固定 application/octet-stream，
    与原 setup.sh + curl --data-binary 行为一致。
    """
    with open(file_path, "rb") as f:
        data = f.read()
    req = urllib.request.Request(
        upload_url, data=data, method="PUT",
        headers={"Content-Type": "application/octet-stream"})
    opener = _build_opener(no_proxy)
    with opener.open(req, timeout=timeout or HTTP_TIMEOUT) as resp:
        return resp.status


def call_tool(service, tool, arguments, no_proxy=False, timeout=None):
    """以模块方式调用一个 MCP 工具，返回解析后的 dict（import_file.py 复用）。

    返回 (result_dict, error_str)：成功时 error_str 为 None。
    """
    url = _resolve_url(service)
    if not url:
        return None, f"unknown_service: {service}"
    oauth, oneid = _load_tokens()
    if not oauth and not oneid:
        return None, "no_token"
    if _identity_mismatch_error(oauth, oneid):
        return None, "identity_mismatch"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}
    rsp = _post_jsonrpc(url, payload, oauth, oneid, no_proxy, timeout or HTTP_TIMEOUT)
    if rsp is None:
        return None, "http_failed"
    try:
        return json.loads(rsp), None
    except json.JSONDecodeError:
        return None, f"non_json_response: {rsp[:200]}"


def fetch_tools(service, oauth, oneid, no_proxy=False, timeout=None):
    """拉取某 endpoint 的 tools/list，返回 (tools_list, error_str)。"""
    url = _resolve_url(service)
    if not url:
        return None, f"unknown_service: {service}"
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    rsp = _post_jsonrpc(url, payload, oauth, oneid, no_proxy, timeout or HTTP_TIMEOUT)
    if rsp is None:
        return None, "http_failed"
    try:
        obj = json.loads(rsp)
    except json.JSONDecodeError:
        return None, f"non_json_response: {rsp[:200]}"
    if obj.get("error"):
        return None, f"jsonrpc_error: {obj['error']}"
    return (obj.get("result") or {}).get("tools", []), None


def _require_tokens():
    ***REDACTED***
    oauth, oneid = _load_tokens()
    if not oauth and not oneid:
        print("ERROR:no_token - 未检测到腾讯文档登录票据，请在 WorkBuddy 中打开并授权腾讯文档连接器后重试"
              + _no_token_hint())
        return None
    mismatch = _identity_mismatch_error(oauth, oneid)
    if mismatch:
        print(mismatch)
        return None
    return oauth, oneid


# ── 主入口 A：环境检查 ────────────────────────────────────────────────────────
def cmd_init(_args):
    oauth, oneid = _load_tokens()
    if not oauth and not oneid:
        print("ERROR:no_token - 未检测到环境变量 TDOC_OAUTH_ACCESS_TOKEN 或 "
              "TDOC_ONEID_ACCESS_TOKEN，请由宿主环境注入" + _no_token_hint())
        return 1
    mismatch = _identity_mismatch_error(oauth, oneid)
    if mismatch:
        print(mismatch)
        return 1
    print("READY")
    return 0


# ── 主入口 B：调用工具（tools/call） ──────────────────────────────────────────
def cmd_call(args):
    service, tool = args.service, args.tool
    url = _resolve_url(service)
    if not url:
        print(f"ERROR:unknown_service - 未知 service: {service}（应为 {_SERVICE_HINT}）")
        return 1

    arguments_str = args.json_args if args.json_args else "{}"
    try:
        arguments = json.loads(arguments_str)
    except json.JSONDecodeError:
        print(f"ERROR:bad_args_json - args 必须是合法的 JSON 对象字符串，收到: {arguments_str}")
        return 1
    if not isinstance(arguments, dict):
        print(f"ERROR:bad_args_json - args 必须是 JSON 对象（{{...}}），收到: {arguments_str}")
        return 1

    tokens = ***REDACTED***
    if tokens is None:
        ***REDACTED***

    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": arguments}}
    rsp = _post_jsonrpc(url, payload, tokens[0], tokens[1], args.no_proxy, args.timeout)
    if rsp is None:
        return 1
    print(rsp)
    return 0


# ── 主入口 C：列工具（tools/list） ────────────────────────────────────────────
def cmd_list(args):
    service = args.service
    url = _resolve_url(service)
    if not url:
        print(f"ERROR:unknown_service - 未知 service: {service}（应为 {_SERVICE_HINT}）")
        return 1

    tokens = ***REDACTED***
    if tokens is None:
        ***REDACTED***

    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    rsp = _post_jsonrpc(url, payload, tokens[0], tokens[1], args.no_proxy, args.timeout)
    if rsp is None:
        return 1
    print(rsp)
    return 0


# ── 主入口 D：查单个工具的参数定义（调用前必做） ──────────────────────────────
def cmd_schema(args):
    service, tool = args.service, args.tool
    url = _resolve_url(service)
    if not url:
        print(f"ERROR:unknown_service - 未知 service: {service}（应为 {_SERVICE_HINT}）")
        return 1

    tokens = ***REDACTED***
    if tokens is None:
        ***REDACTED***

    tools, err = fetch_tools(service, tokens[0], tokens[1], args.no_proxy, args.timeout)
    if err:
        print(f"ERROR:{err}")
        return 1

    t = next((x for x in tools if x.get("name") == tool), None)
    if t is None:
        names = ", ".join(sorted(x.get("name", "") for x in tools)[:60])
        print(f"ERROR:tool_not_found - 工具 {tool!r} 不在 {service}（可用工具名见 tdoc_list；部分：{names}）")
        return 1

    schema = t.get("inputSchema") or {}
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])

    if args.raw:
        # 原样输出该工具完整定义 JSON（name/description/inputSchema）
        print(json.dumps(t, ensure_ascii=False, indent=2))
        return 0

    # 人类可读：工具名 + 描述 + 参数表（✓=必填）
    print(f"# {t.get('name')}")
    desc = (t.get("description") or "").strip()
    if desc:
        print(f"\n{desc}")
    if not props:
        print("\n（无参数）")
    else:
        print("\n参数（✓=必填，调用前按此传参，勿猜）：")
        ordered = [k for k in schema.get("required") or [] if k in props] + \
                  [k for k in props if k not in required]
        for k in ordered:
            spec = props.get(k) or {}
            typ = spec.get("type", "")
            if typ == "array" and isinstance(spec.get("items"), dict):
                typ = f"array<{spec['items'].get('type', '')}>"
            mark = "✓" if k in required else " "
            d = (spec.get("description") or "").replace("\n", " ").strip()
            print(f"  [{mark}] {k} ({typ}): {d}")
    print("\n★ 用 tdoc_call 调用时，arguments 必须严格按以上参数定义传入；"
          "需要原始 JSON Schema 加 --raw。")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tencentdocs.py", add_help=True,
                                 description="腾讯文档 MCP 调用入口（纯 Python，跨平台）")
    ap.add_argument("--no-proxy", action="store_true", help="本次请求绕过所有代理（默认走系统代理）")
    ap.add_argument("--timeout", type=int, default=HTTP_TIMEOUT, help="HTTP 超时秒数（默认 120）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("tdoc_init", help="环境检查（token 检测）")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("tdoc_call", help="调用 MCP 工具（tools/call）。调用前先用 tdoc_schema 查参数，勿猜")
    p.add_argument("service", help=_SERVICE_HINT)
    p.add_argument("tool", help="工具名，如 manage.create_file / slide_add_shape")
    p.add_argument("json_args", nargs="?", default="", help="工具参数 JSON 对象字符串；须按 tdoc_schema 的定义传")
    p.set_defaults(func=cmd_call)

    p = sub.add_parser("tdoc_list", help="列出指定 endpoint 的所有 MCP 工具（tools/list）")
    p.add_argument("service", help=_SERVICE_HINT)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("tdoc_schema",
                       help="查单个工具的描述与参数定义（★ 调用 tdoc_call 前必做，按定义传参勿猜）")
    p.add_argument("service", help=_SERVICE_HINT)
    p.add_argument("tool", help="工具名，如 manage.create_file / slide_add_shape")
    p.add_argument("--raw", action="store_true", help="原样输出该工具完整定义 JSON（含 inputSchema）")
    p.set_defaults(func=cmd_schema)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
