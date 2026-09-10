#!/usr/bin/env python3
"""
百望 MCP 工具调用脚本 — 通过 StreamableHTTP 或百望云平台协议调用 MCP Server

用法：
    # 列出 MCP Server 的所有工具
    python call_mcp.py list <mcp_server_url_or_config_key>

    # 调用指定工具
    python call_mcp.py call <mcp_server_url_or_config_key> <tool_name> [--params '{"key": "value"}']

URL 支持三种格式：
    1. 直接 URL：   "https://sandbox-openapi.baiwang.com/mcp/wukong/lctoolscall?key=xxx"
    2. 配置键名：   "BAIWANG_OCR_STANDARD_URL"（从系统环境、mcp-config.json 或 .env 文件读取）
    3. mcp-config.json 中的 key 名（自动从技能根目录读取配置）

示例：
    python call_mcp.py list BAIWANG_OCR_STANDARD_URL
    python call_mcp.py call BAIWANG_OCR_STANDARD_URL baiwang.ocr.stand.tickets --params '{"fileUrl": "https://example.com/invoice.pdf", "serviceMode": "0", "serviceMold": "1"}'
    python call_mcp.py call BAIWANG_INVOICE_RECOGNIZE_VERIFY_URL baiwang.input.compliance.validate --params '{"invoiceNumber": "24000000000000000001", "billingDate": "2025-03-15", "totalAmount": "13600.00", "taxNo": "<PLATFORM_TAXNO>"}'

> **注意**：示例中的 `<PLATFORM_TAXNO>` 为占位符，实际调用时自动从环境变量 `PLATFORM_TAXNO` 读取。

MCP Server URL 配置方式：
    1. 优先使用技能目录下的 mcp-config.json（当前包体已内置）
    2. 如需覆盖，可使用系统环境变量或 .env 文件
    3. 401/403 或 appKey 无权操作时，请检查 WorkBuddy/百望服务授权
"""

import argparse
import base64
import io
import json
import os
import ssl
import sys
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# Fix Windows console encoding: force UTF-8 for script output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', newline='\n')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', newline='\n')

# 重试配置
MAX_RETRIES = 3
RETRY_DELAYS = [2, 4, 8]  # 指数退避间隔（秒）

# 超时配置（秒）
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 120

# 错误码常量
ERROR_CODE_NETWORK = "MCP_NETWORK_ERROR"
ERROR_CODE_HTTP = "MCP_HTTP_ERROR"
ERROR_CODE_JSON = "MCP_JSON_PARSE_ERROR"
ERROR_CODE_UNAVAILABLE = "MCP_SERVICE_UNAVAILABLE"
ERROR_CODE_TOOL_ERROR = "MCP_TOOL_EXECUTION_ERROR"

IMAGE_RECOGCOLLECT_TOOL = "baiwang.image.invoices.recogcollect"

DEPRECATED_MCP_TARGETS = {
    "BAIWANG_RISK_QUERY_URL": "风险查询必须使用 BAIWANG_COUNTERPARTY_RISK_URL。",
}

DEPRECATED_TOOL_ALIASES = {
    "baiwang.risk.query": "风险查询没有 baiwang.risk.query 这个工具。",
}

DEPRECATED_TOOL_PREFIXES = ("baiwang.risk.",)

BAIWANG_CLOUD_TOOLS = [
    {
        "name": "baiwang.ocr.stand.tickets",
        "description": "发票标准 OCR，入参必须使用 OSS fileUrl，不接受 base64。",
        "inputSchema": {
            "type": "object",
            "required": ["fileUrl", "serviceMode", "serviceMold"],
            "properties": {
                "fileUrl": {"type": "string"},
                "serviceMode": {"type": "string"},
                "serviceMold": {"type": "string"},
            },
        },
    },
    {
        "name": IMAGE_RECOGCOLLECT_TOOL,
        "description": "发票影像识别采集，OFD/XML 等源文件使用裸 base64。",
        "inputSchema": {
            "type": "object",
            "required": ["filesMap", "userAccount"],
            "properties": {
                "filesMap": {"type": "array"},
                "userAccount": {"type": "string"},
                "isSave": {"type": "integer"},
                "collectWay": {"type": "integer"},
                "uploadMode": {"type": "integer"},
            },
        },
    },
    {
        "name": "baiwang.input.compliance.validate",
        "description": "发票四要素验真，totalAmount 与 checkCode_6 至少传一个。",
        "inputSchema": {
            "type": "object",
            "required": ["invoiceNumber", "billingDate", "taxNo"],
            "properties": {
                "invoiceCode": {"type": "string"},
                "invoiceNumber": {"type": "string"},
                "billingDate": {"type": "string"},
                "totalAmount": {"type": "string"},
                "checkCode_6": {"type": "string"},
                "taxNo": {"type": "string"},
            },
        },
    },
    {
        "name": "baiwang.dataasset.risktag.queryTaxnogrey",
        "description": "灰名单检测，taxNo 为平台标识，data 内传销方名称或税号。",
        "inputSchema": {
            "type": "object",
            "required": ["taxNo", "data"],
            "properties": {
                "taxNo": {"type": "string"},
                "data": {"type": "object"},
            },
        },
    },
    {
        "name": "baiwang.dataasset.risktag.queryTaxArrearsInfo",
        "description": "欠税信息查询，taxNo 为平台标识，data 内传销方名称或税号。",
        "inputSchema": {
            "type": "object",
            "required": ["taxNo", "data"],
            "properties": {
                "taxNo": {"type": "string"},
                "data": {"type": "object"},
            },
        },
    },
    {
        "name": "baiwang.dataasset.risktag.selectViolationInfo",
        "description": "重大税收违法查询，taxNo 为平台标识，data 内传销方名称或税号。",
        "inputSchema": {
            "type": "object",
            "required": ["taxNo", "data"],
            "properties": {
                "taxNo": {"type": "string"},
                "data": {"type": "object"},
            },
        },
    },
]

BAIWANG_CLOUD_TOOL_NAMES = {tool["name"] for tool in BAIWANG_CLOUD_TOOLS}
RISK_TOOL_NAMES = {
    "baiwang.dataasset.risktag.queryTaxnogrey",
    "baiwang.dataasset.risktag.queryTaxArrearsInfo",
    "baiwang.dataasset.risktag.selectViolationInfo",
}


def _print_risk_tool_hint():
    print("  风险查询请使用：", file=sys.stderr)
    print("    URL Key: BAIWANG_COUNTERPARTY_RISK_URL", file=sys.stderr)
    for name in sorted(RISK_TOOL_NAMES):
        print(f"    Tool: {name}", file=sys.stderr)
    print('    参数: {"taxNo":"<PLATFORM_TAXNO>","data":{"taxpayer":"销方名称","taxpayercode":"销方税号"}}', file=sys.stderr)


def validate_mcp_target(url_or_var):
    """拦截已废弃或不存在的 MCP URL 配置键。"""
    target = url_or_var[1:] if isinstance(url_or_var, str) and url_or_var.startswith("$") else url_or_var
    if target in DEPRECATED_MCP_TARGETS:
        print(f"  MCP URL 配置键不可用：{target}", file=sys.stderr)
        print(f"  {DEPRECATED_MCP_TARGETS[target]}", file=sys.stderr)
        _print_risk_tool_hint()
        return False
    return True


def validate_tool_name(tool_name):
    """拦截 LLM 猜测出的旧工具名或未登记的百望工具。"""
    if tool_name in DEPRECATED_TOOL_ALIASES or tool_name.startswith(DEPRECATED_TOOL_PREFIXES):
        reason = DEPRECATED_TOOL_ALIASES.get(tool_name, "baiwang.risk.* 不是本技能登记的 MCP 工具。")
        print(f"  MCP 工具名不可用：{tool_name}", file=sys.stderr)
        print(f"  {reason}", file=sys.stderr)
        _print_risk_tool_hint()
        return False

    if tool_name.startswith("baiwang.") and tool_name not in BAIWANG_CLOUD_TOOL_NAMES:
        print(f"  未登记的百望 MCP 工具：{tool_name}", file=sys.stderr)
        print("  本技能只能调用 scripts/call_mcp.py 中登记过 schema 的百望工具，避免 LLM 猜测接口。", file=sys.stderr)
        if "risk" in tool_name.lower() or "risktag" in tool_name.lower():
            _print_risk_tool_hint()
        return False

    return True


def _expand_env_placeholder(value):
    if not isinstance(value, str):
        return ""
    stripped = value.strip()
    if stripped.startswith("${") and stripped.endswith("}"):
        return os.environ.get(stripped[2:-1], "")
    return stripped


def _find_skill_root():
    """定位专家包根目录。

    优先使用 SKILL_ROOT_DIR 环境变量（适用于子 agent 沙箱/工作区场景，
    __file__ 被复制到临时目录时仍可正确定位）。
    兜底：从 __file__ 往上走四级推导。
    """
    env_root = os.environ.get("SKILL_ROOT_DIR", "").strip()
    if env_root and Path(env_root).is_dir():
        return Path(env_root)
    return Path(__file__).parent.parent.parent.parent


def load_mcp_config():
    """从技能根目录读取 mcp-config.json，将 URL 注入环境变量。

    mcp-config.json 格式：
    {
      "KEY_NAME": { "url": "https://...", "mcpId": "..." },
      ...
    }

    仅注入 url 非空的条目，不覆盖已有的环境变量。
    返回加载的配置 dict，文件不存在则返回 None。
    """
    config_path = _find_skill_root() / "mcp-config.json"
    if not config_path.exists():
        return None

    try:
        with open(config_path, encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"  mcp-config.json 读取失败：{exc}", file=sys.stderr)
        return None

    loaded_keys = []
    for key, value in config.items():
        if isinstance(value, dict):
            url = _expand_env_placeholder(value.get("url", ""))
            if url and key not in os.environ:
                os.environ[key] = url
                loaded_keys.append(key)

    if loaded_keys:
        print(f" 已从 mcp-config.json 加载：{', '.join(loaded_keys)}", file=sys.stderr)

    return config


def load_env_file():
    """从技能目录及父目录查找并加载 .env 文件。优先加载技能根目录的 .env（随专家包交付）。"""
    search_dirs = [
        _find_skill_root(),   # 技能根目录（优先，随专家包交付）
        Path(__file__).parent,  # scripts 目录
        Path.cwd(),             # 当前工作目录
    ]
    for directory in search_dirs:
        env_file = directory / ".env"
        if env_file.exists():
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip().lstrip("\ufeff")
                    value = value.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = value
            return str(env_file)
    return None


def sanitize_url(url):
    """脱敏 URL 中的敏感参数（如 key、token），用于日志输出。"""
    import re
    # 隐藏 query string 中的 key 参数
    sanitized = re.sub(r'([?&])(key|token|secret)=[^&]*', r'\g<1>\g<2>=***', url, flags=re.IGNORECASE)
    # 隐藏 URL 中的密码部分
    sanitized = re.sub(r'(://[^:]+:)[^@]+@', r'\g<1>***@', sanitized)
    return sanitized


def repair_mojibake_text(value):
    """修复百望返回中文偶发的 UTF-8 被 cp1252/latin1 误解码问题。"""
    if not isinstance(value, str):
        return value
    for encoding in ("cp1252", "latin1"):
        try:
            fixed = value.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        if any("\u4e00" <= char <= "\u9fff" for char in fixed):
            return fixed
    return value


def repair_mojibake_json(value):
    if isinstance(value, dict):
        return {k: repair_mojibake_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [repair_mojibake_json(v) for v in value]
    return repair_mojibake_text(value)


def resolve_url(url_or_var):
    """解析 URL：支持直接 URL、配置键名或 $ENV_VAR 格式的环境变量引用。"""
    if url_or_var.startswith("$"):
        var_name = url_or_var[1:]
        value = os.environ.get(var_name)
        if not value:
            print(f" 环境变量未设置：{var_name}", file=sys.stderr)
            print(f"   请在 mcp-config.json 或 .env 文件中配置：{var_name}=<your_url>", file=sys.stderr)
            print("   当前技能包通常从 mcp-config.json 自动加载；若仍失败，请检查 WorkBuddy/百望服务授权。", file=sys.stderr)
            sys.exit(1)
        return value
    if url_or_var in os.environ:
        return os.environ[url_or_var]
    return url_or_var


def make_jsonrpc_request(method, params=None):
    """构造 JSON-RPC 2.0 请求体。"""
    request_body = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": method,
    }
    if params is not None:
        request_body["params"] = params
    return request_body


def send_mcp_request(server_url, method, params=None):
    """向 MCP Server 发送请求并返回结果（单次，无重试）。

    自动检测协议：
    - 百望云平台（sandbox-openapi.baiwang.com）：method 放 query string，body 为 params JSON
    - 标准 StreamableHTTP（JSON-RPC 2.0）：body 为完整 JSON-RPC 请求
    """
    is_baiwang_cloud = "baiwang.com" in server_url

    if is_baiwang_cloud:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(server_url)
        qs = parse_qs(parsed.query)
        qs["method"] = method
        new_query = urlencode(qs, doseq=True)
        request_url = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, new_query, parsed.fragment
        ))
        data = json.dumps(params or {}).encode("utf-8")
        request = Request(
            request_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
    else:
        body = make_jsonrpc_request(method, params)
        data = json.dumps(body).encode("utf-8")
        request = Request(
            server_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
            method="POST",
        )

    try:
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        with urlopen(request, timeout=READ_TIMEOUT, context=ssl_ctx) as response:
            content_type = response.headers.get("Content-Type", "")
            raw = response.read().decode("utf-8")

            if is_baiwang_cloud:
                return parse_baiwang_response(raw, method)

            # StreamableHTTP 可能返回 SSE 格式或直接 JSON
            if "text/event-stream" in content_type:
                return parse_sse_response(raw)
            else:
                result = json.loads(raw)
                if "error" in result:
                    print(f" MCP 错误：{result['error']}", file=sys.stderr)
                    return None
                return result.get("result")
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        log_url = sanitize_url(server_url)
        print(f"[{ERROR_CODE_HTTP}] HTTP {error.code} ({log_url}): {error_body}", file=sys.stderr)
        return None
    except URLError as error:
        log_url = sanitize_url(server_url)
        print(f"[{ERROR_CODE_NETWORK}] 网络错误 ({log_url}): {error.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError as error:
        print(f"[{ERROR_CODE_JSON}] JSON 解析失败: {error}", file=sys.stderr)
        return None


def _is_graylist_no_info_error(method, err):
    return (
        method == "baiwang.dataasset.risktag.queryTaxnogrey"
        and str(err.get("code", "")) == "100006"
        and str(err.get("subCode", "")) == "90008"
        and "暂无信息" in str(err.get("subMessage", ""))
    )


def parse_baiwang_response(raw_text, method=None):
    """解析百望云平台响应。

    OCR 格式：{"success": true, "response": [{...}, ...]}
    验真格式：{"success": true, "response": {"data": {...}, "invoiceType": "..."}}
    失败格式：{"success": false, "errorResponse": {"code": ..., "message": ...}}

    返回格式统一为 {"content": [{"type": "text", "text": "..."}], "isError": bool}，
    与 call_tool 的 result.get("content", []) 读取方式对齐。
    """
    data = json.loads(raw_text)
    if data.get("success"):
        resp = data.get("response", {})
        if isinstance(resp, list):
            # OCR 场景：response 是数组
            text = json.dumps(resp, ensure_ascii=False)
            return {"content": [{"type": "text", "text": text}], "isError": False}
        elif isinstance(resp, dict):
            # 验真场景：response 是对象，包含 data + invoiceType 等
            raw_data = resp.get("data", {})
            extra = {k: v for k, v in resp.items() if k not in ("data", "ext", "requestId")}
            if isinstance(raw_data, dict):
                merged = {**raw_data, **extra}
            else:
                merged = {"data": raw_data, **extra}
            text = json.dumps(merged, ensure_ascii=False)
            return {"content": [{"type": "text", "text": text}], "isError": False}
        return {"content": [{"type": "text", "text": json.dumps(resp, ensure_ascii=False)}], "isError": False}
    err = repair_mojibake_json(data.get("errorResponse", {}))
    if _is_graylist_no_info_error(method, err):
        no_risk_result = {"riskLevel": "无风险", "reason": "暂未发现风险"}
        print(" 百望灰名单返回暂无信息，按无风险处理", file=sys.stderr)
        return {"content": [{"type": "text", "text": json.dumps(no_risk_result, ensure_ascii=False)}], "isError": False}

    print(f" 百望云错误：[{err.get('code')}] {err.get('message')} (subCode={err.get('subCode')})", file=sys.stderr)
    return {"result": {"error": err}, "isError": True}


def send_mcp_request_with_retry(server_url, method, params=None, max_retries=MAX_RETRIES):
    """带指数退避重试的 MCP 请求。

    Args:
        server_url: MCP Server URL
        method: JSON-RPC 方法名
        params: 请求参数
        max_retries: 最大重试次数（默认 3）

    Returns:
        成功返回 result dict，所有重试耗尽返回 None。
    """
    last_error = None

    for attempt in range(max_retries + 1):
        result = send_mcp_request(server_url, method, params)
        if result is not None:
            if attempt > 0:
                print(f" 第 {attempt + 1} 次尝试成功", file=sys.stderr)
            return result

        last_error = True
        if attempt < max_retries:
            delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
            print(f" 第 {attempt + 1} 次尝试失败，{delay}s 后重试（剩余 {max_retries - attempt} 次）...", file=sys.stderr)
            time.sleep(delay)

    log_url = sanitize_url(server_url)
    print(f" [{ERROR_CODE_UNAVAILABLE}] 已达最大重试次数（{max_retries}），请求失败 ({log_url})", file=sys.stderr)
    return None


def parse_sse_response(raw_text):
    """解析 SSE（Server-Sent Events）格式的响应，支持多帧与多行 data。

    SSE 规范要点：
      - 每个消息以空行分隔
      - data: 可跨多行，用 \n 拼接
      - event: 标记事件类型
      - [DONE] 表示流结束
    """
    last_error = None

    def dispatch(event_type, data_str):
        """处理一条完整的 SSE 数据帧。"""
        nonlocal last_error
        if not data_str:
            return
        try:
            data = json.loads(data_str)
        except json.JSONDecodeError:
            return
        # 流结束标记
        if data == "[DONE]":
            return
        # 优先返回含 result 的帧
        if "result" in data:
            return data["result"]
        if "error" in data:
            last_error = data["error"]
            return "ERROR"
        return None

    # 按空行分割为独立事件帧
    frames = raw_text.strip().split("\n\n")
    for frame in frames:
        event_type = None
        data_lines = []
        for line in frame.split("\n"):
            line = line.strip()
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                data_lines.append(line[5:].strip())
            elif line.startswith(":"):
                # 注释行，跳过
                continue

        if not data_lines:
            continue

        # 多行 data 用 \n 拼接（SSE 规范）
        combined_data = "\n".join(data_lines)
        result = dispatch(event_type, combined_data)
        if result == "ERROR":
            print(f"MCP 错误：{last_error}", file=sys.stderr)
            return None
        if result is not None:
            return result

    if last_error:
        print(f"MCP 错误：{last_error}", file=sys.stderr)
        return None
    print(" 未能从 SSE 响应中解析到结果", file=sys.stderr)
    return None


def check_health(server_url):
    """健康检查：验证 MCP Server 可用性。

    Returns:
        (ok, tools) — ok=True 时 tools 为工具列表；ok=False 时 tools 为错误信息。
    """
    is_baiwang_cloud = "baiwang.com" in server_url
    if is_baiwang_cloud:
        return True, BAIWANG_CLOUD_TOOLS

    result = send_mcp_request(server_url, "tools/list")
    if result is None:
        return False, "MCP Server 无响应"
    tools = result.get("result", {}).get("tools", [])
    return True, tools


def list_tools(server_url):
    """列出 MCP Server 的所有可用工具。"""
    is_baiwang_cloud = "baiwang.com" in server_url
    print(f" 正在获取工具列表...")
    print(f"   URL: {sanitize_url(server_url)[:80]}...")
    print()

    if is_baiwang_cloud:
        print("  百望 lctoolscall 网关不支持远程 tools/list，使用包内登记的工具清单。")
        print("  真实可用性以具体 call 调用返回为准。")
        print()
        tools = BAIWANG_CLOUD_TOOLS
    else:
        result = send_mcp_request_with_retry(server_url, "tools/list")
        if result is None:
            return False
        tools = result.get("tools", [])

    if not tools:
        print("  该 MCP Server 没有可用的工具")
        return True

    print(f" 共 {len(tools)} 个工具：")
    print()
    for tool in tools:
        name = tool.get("name", "未知")
        description = tool.get("description", "无描述")
        print(f"  [TOOL] {name}")
        # 截断过长的描述
        if len(description) > 120:
            description = description[:117] + "..."
        print(f"     {description}")

        # 显示参数
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])
        if properties:
            param_parts = []
            for param_name, param_info in properties.items():
                param_type = param_info.get("type", "any")
                is_required = "必填" if param_name in required else "可选"
                param_parts.append(f"{param_name}({param_type}, {is_required})")
            print(f"     参数: {', '.join(param_parts)}")
        print()

    return True


def sanitize_params(params):
    """递归脱敏参数中的敏感字段（如 base64、key、token）。"""
    sensitive_names = ("base64", "key", "token", "secret", "password")

    def _sanitize(value, key_name=""):
        if isinstance(value, dict):
            return {k: _sanitize(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [_sanitize(v, key_name) for v in value]
        if any(name in key_name.lower() for name in sensitive_names):
            val = str(value)
            return val[:20] + "..." if len(val) > 20 else "***"
        return value

    return _sanitize(params)


def _get_platform_taxno():
    """从环境变量或 mcp-config.json 获取平台标识税号。

    优先级：os.environ["PLATFORM_TAXNO"] > mcp-config.json → platform.taxNo
    """
    tax_no = os.environ.get("PLATFORM_TAXNO", "")
    if not tax_no:
        cfg_path = _find_skill_root() / "mcp-config.json"
        if cfg_path.exists():
            try:
                with open(cfg_path, encoding="utf-8") as f:
                    _cfg = json.load(f)
                platform = _cfg.get("platform", {})
                if isinstance(platform, dict):
                    tax_no = platform.get("taxNo", "")
            except (json.JSONDecodeError, OSError):
                pass
    return tax_no


def _get_recogcollect_user_account():
    """读取影像识别采集接口的用户账号。"""
    for env_key in ("BAIWANG_IMAGE_RECOGCOLLECT_USER_ACCOUNT", "BAIWANG_USER_ACCOUNT", "WORKBUDDY_USER_ACCOUNT"):
        value = os.environ.get(env_key, "").strip()
        if value:
            return value

    cfg_path = _find_skill_root() / "mcp-config.json"
    if cfg_path.exists():
        try:
            with open(cfg_path, encoding="utf-8") as f:
                _cfg = json.load(f)
            config = _cfg.get("imageRecogcollect", {})
            if isinstance(config, dict):
                value = str(config.get("userAccount", "")).strip()
                if value and not (value.startswith("${") and value.endswith("}")):
                    return value
        except (json.JSONDecodeError, OSError):
            pass
    return ""


def _strip_data_uri_prefix(file_base64):
    """接口只接受裸 base64，不接受 data URI 前缀。"""
    if isinstance(file_base64, str) and file_base64.startswith("data:") and "," in file_base64:
        return file_base64.split(",", 1)[1]
    return file_base64


def _validate_image_recogcollect_params(params, tool_name):
    """校验影像识别采集接口必填参数。"""
    if tool_name != IMAGE_RECOGCOLLECT_TOOL:
        return

    issues = []
    files_map = params.get("filesMap")
    if not isinstance(files_map, list) or not files_map:
        issues.append("缺少必填参数 filesMap，且必须为非空数组")
    else:
        for index, item in enumerate(files_map, start=1):
            if not isinstance(item, dict):
                issues.append(f"filesMap[{index}] 必须为对象")
                continue
            file_name = str(item.get("fileName", "")).strip()
            file_base64 = item.get("fileBase64")
            if not file_name:
                issues.append(f"filesMap[{index}].fileName 必填")
            elif len(file_name) > 50:
                issues.append(f"filesMap[{index}].fileName 长度不能超过 50")
            if not file_base64:
                issues.append(f"filesMap[{index}].fileBase64 必填")
            elif not isinstance(file_base64, str):
                issues.append(f"filesMap[{index}].fileBase64 必须为字符串")
            else:
                try:
                    base64.b64decode(file_base64, validate=True)
                except Exception:
                    issues.append(f"filesMap[{index}].fileBase64 必须为不带 data URI 前缀的合法 base64")

    if not str(params.get("userAccount", "")).strip():
        issues.append("缺少必填参数 userAccount")

    if issues:
        for issue in issues:
            print(f"  ❌ {issue}", file=sys.stderr)
        raise ValueError("影像识别采集接口参数不完整")


def _validate_standard_ocr_params(params, tool_name):
    """校验标准 OCR 工具必填参数。"""
    if tool_name != "

... [Content truncated, total 37,831 chars] ...