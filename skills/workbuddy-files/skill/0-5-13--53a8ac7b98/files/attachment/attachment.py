#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
attachment/attachment.py —— 节点附件的上传与下载（单脚本双子命令：upload / download）。

调用形态、参数、三步链路与输出契约见 attachment/entry.md。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_LIB_DIR = Path(__file__).resolve().parents[1]
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

import _common  # noqa: E402
from _common import (  # noqa: E402
    HttpError,
    error_exit,
    http_request,
    safe_print,
    unwrap_data,
)

_PATH_APPLY = "/space/api/agent/v1/attachment-apply"
_PATH_CONFIRM = "/space/api/agent/v1/attachment-confirm"
_PATH_DOWNLOAD = "/space/api/agent/v1/attachment-download"

# 单次内存读取上传，PUT 超时；文件大小上限不在客户端硬编码，交由服务端 apply 校验。
PUT_TIMEOUT = 120


def _file_size(path: str) -> int:
    """返回文件字节数；读取失败返回 0。

    仅取大小（stat），不读文件内容——大小上限不在客户端预判，
    交由服务端 apply 凭证接口按 fileSize 校验，避免服务端配额调整后
    本地硬编码不同步导致误拦；文件内容延迟到 PUT 直传前才读。
    """
    try:
        return os.path.getsize(path)
    except (OSError, IOError):
        return 0


def _put_to_cos(upload_url: str, headers: dict[str, str], body: bytes) -> bool:
    """携带服务端返回的直传 headers 执行 PUT；不注入 WorkBuddy 鉴权头。"""
    if not upload_url or not headers or not body:
        return False
    req = urllib.request.Request(
        url=upload_url,
        data=body,
        headers=headers,
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req, timeout=PUT_TIMEOUT) as resp:
            return 200 <= resp.status < 300
    except (
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        OSError,
        ValueError,
    ):
        return False
    except Exception:  # noqa: BLE001 - 统一转结构化失败
        return False


def _cmd_upload(args: argparse.Namespace, token: str) -> None:
    node_id = (args.node_id or "").strip()
    if not node_id:
        error_exit("--node-id 必填")

    path = (args.path or "").strip()
    if not path or not os.path.isfile(path):
        error_exit("文件路径无效或文件不存在")

    size = _file_size(path)
    if size == 0:
        error_exit("文件为空，无法上传")

    file_name = (args.file_name or os.path.basename(path)).strip()
    if not file_name:
        error_exit("文件名为空")

    # Step 1：申请上传凭证
    try:
        apply_data = unwrap_data(
            http_request(
                "POST",
                _common.build_url(_PATH_APPLY),
                token,
                body={"nodeId": node_id, "fileName": file_name, "fileSize": size},
                timeout=10.0,
            )
        )
    except HttpError as e:
        error_exit(f"申请附件上传凭证失败: {e}")

    upload_url = (apply_data.get("uploadUrl") or "").strip()
    upload_headers = apply_data.get("headers")
    confirm_key = (apply_data.get("confirmKey") or "").strip()

    if not upload_url or not confirm_key:
        error_exit("当前账号尚未开放附件上传")
    if not isinstance(upload_headers, dict) or not upload_headers:
        error_exit("附件上传凭证格式无效")
    if not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in upload_headers.items()
    ):
        error_exit("附件上传凭证格式无效")

    # Step 2：服务端已按 fileSize 放行，此时才读文件内容并 PUT 直传
    try:
        with open(path, "rb") as f:
            content = f.read()
    except (OSError, IOError):
        error_exit("读取文件内容失败")
    if not _put_to_cos(upload_url, upload_headers, content):
        error_exit("附件直传失败")

    # Step 3：确认上传完成
    try:
        confirm_data = unwrap_data(
            http_request(
                "POST",
                _common.build_url(_PATH_CONFIRM),
                token,
                body={"nodeId": node_id, "confirmKey": confirm_key},
                timeout=30.0,
            )
        )
    except HttpError as e:
        error_exit(f"确认附件上传失败: {e}")

    attachment_id = (confirm_data.get("attachmentId") or "").strip()
    if not attachment_id:
        error_exit("服务端返回的 attachmentId 为空")

    out = {
        "node_id": node_id,
        "attachment_id": attachment_id,
        "file_name": (confirm_data.get("fileName") or file_name).strip(),
        "file_size": confirm_data.get("fileSize") if confirm_data.get("fileSize") is not None else size,
        "file_type": str(confirm_data.get("fileType") or "").strip(),
        "media_type": str(confirm_data.get("mediaType") or "").strip(),
    }
    safe_print(
        "KS_ATTACHMENT_UPLOAD_OK "
        + json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    )
    safe_print(f"KS_USER_REPLY\t文件「{out['file_name']}」已作为附件上传完成。")


def _cmd_download(args: argparse.Namespace, token: str) -> None:
    node_id = (args.node_id or "").strip()
    attachment_id = (args.attachment_id or "").strip()
    if not node_id:
        error_exit("--node-id 必填")
    if not attachment_id:
        error_exit("--attachment-id 必填")

    try:
        data = unwrap_data(
            http_request(
                "POST",
                _common.build_url(_PATH_DOWNLOAD),
                token,
                body={"nodeId": node_id, "attachmentId": attachment_id},
                timeout=10.0,
            )
        )
    except HttpError as e:
        error_exit(f"获取附件下载链接失败: {e}")

    download_url = (data.get("downloadUrl") or "").strip()
    if not download_url:
        error_exit("服务端返回的 downloadUrl 为空")

    out = {
        "node_id": node_id,
        "attachment_id": attachment_id,
        "download_url": download_url,
    }
    safe_print(
        "KS_ATTACHMENT_DOWNLOAD "
        + json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    )
    # download_url 是短期 COS 签名，禁止在用户回复中原样展开；仅供 Agent 立即直拉文件字节使用。
    safe_print("KS_USER_REPLY\t已取到该附件的下载链接（短期有效），如需保存请及时下载。")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    _common.register_token_arg(parser)
    parser.add_argument("command", nargs="?", default="")
    parser.add_argument("path", nargs="?", default="")
    parser.add_argument("--node-id", dest="node_id", default="")
    parser.add_argument("--file-name", dest="file_name", default="")
    parser.add_argument("--attachment-id", dest="attachment_id", default="")
    try:
        args, _unknown = parser.parse_known_args()
    except SystemExit:
        error_exit("参数解析失败")

    command = (args.command or "").strip().lower()
    if command not in ("upload", "download"):
        error_exit("子命令必须是 upload 或 download")

    token = ***REDACTED***

    if command == "upload":
        _cmd_upload(args, token)
    else:
        _cmd_download(args, token)


if __name__ == "__main__":
    main()
