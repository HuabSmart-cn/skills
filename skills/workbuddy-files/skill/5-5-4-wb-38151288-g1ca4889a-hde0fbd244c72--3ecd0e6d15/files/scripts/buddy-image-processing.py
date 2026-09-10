# -*- coding: utf-8 -*-
"""Process existing images through Buddy image services."""

import argparse
import base64
import io
import json
import os
import re
import subprocess
import sys
import time
from urllib.parse import urlparse


if sys.stdout.encoding and sys.stdout.encoding.lower().replace("-", "") != "utf8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower().replace("-", "") != "utf8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


_IMAGE_API_PATH = "/v2/async/images"
_FALLBACK_ENDPOINT = "https://copilot.tencent.com" + _IMAGE_API_PATH
_OPERATION_MODELS = {
    "erase": "vod-image-erase",
    "restore": "vod-image-restore",
    "enhance": "vod-image-enhance-fidelity",
    "beauty": "vod-portrait-beauty",
    "matting": "vod-image-matting",
}
_MAX_IMAGE_BYTES = 4 * 1024 * 1024
_ACTIVE_TOKEN = ***REDACTED***


def _ensure_requests():
    try:
        import requests as requests_module
        return requests_module
    except ImportError:
        print("[INFO] Installing required dependency...", file=sys.stderr)
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "requests", "-q"],
            stdout=sys.stderr,
            stderr=sys.stderr,
            timeout=60,
        )
        print("[INFO] Dependency installed successfully.", file=sys.stderr)
        import requests as requests_module
        return requests_module


requests = _ensure_requests()


def _resolve_default_endpoint() -> str:
    explicit = os.environ.get("BUDDY_CLOUD_IMAGE_ENDPOINT")
    if explicit:
        return explicit.rstrip("/")

    product_config_raw = os.environ.get("ACC_PRODUCT_CONFIG_V3")
    if product_config_raw:
        try:
            config = json.loads(product_config_raw)
            endpoint = config.get("endpoint")
            if endpoint:
                return endpoint.rstrip("/") + _IMAGE_API_PATH
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    return _FALLBACK_ENDPOINT


_DEFAULT_ENDPOINT = _resolve_default_endpoint()


def _redact_token(text: ***REDACTED***
    if not _ACTIVE_TOKEN or len(_ACTIVE_TOKEN) < 8:
        ***REDACTED***
    return text.replace(_ACTIVE_TOKEN, "[REDACTED]")


def _sanitize_error_message(message: str) -> str:
    if not message:
        return "Image processing failed. Please try again."
    return _redact_token(message)


def _error_out(payload: dict):
    print(_redact_token(json.dumps(payload, ensure_ascii=***REDACTED***
    sys.exit(1)


def _safe_print_json(payload: dict):
    print(_redact_token(json.dumps(payload, ensure_ascii=***REDACTED***


def _read_short_key(args) -> str:
    token = ***REDACTED***
    global _ACTIVE_TOKEN
    _ACTIVE_TOKEN = ***REDACTED***

    if not token:
        ***REDACTED***
            "error": "SHORT_KEY_NOT_CONFIGURED",
            "message": "A short-lived Client API Key must be provided through --token.",
        })
    if not token.startswith("ck_t_"):
        ***REDACTED***
            "error": "INVALID_SHORT_KEY",
            "message": "Only a short-lived ck_t_ Client API Key is accepted.",
        })
    return token


def _endpoint_url(endpoint: str, route: str) -> str:
    base = endpoint.rstrip("/")
    for suffix in ("/edits", "/tasks"):
        if base.endswith(suffix):
            base = base[:-len(suffix)]
            break
    return f"{base}/{route}"


def _call_image_api(
    endpoint: str,
    route: str,
    body: dict,
    token: ***REDACTED***
    task_id: str = None,
) -> dict:
    url = _endpoint_url(endpoint, route)
    headers = {
        "Authorization": ***REDACTED***
        "Content-Type": "application/json",
    }

    print(f"[INFO] Calling image {route} endpoint...", file=sys.stderr)
    response = requests.post(url, headers=headers, json=body, timeout=120)

    if response.status_code == 401:
        error = {
            "error": "AUTHENTICATION_EXPIRED",
            "message": "The short-lived Client API Key is invalid or expired.",
        }
        if task_id:
            error["task_id"] = task_id
        _error_out(error)

    try:
        result = response.json()
    except Exception:
        error = {
            "error": "HTTP_ERROR" if response.status_code >= 400 else "INVALID_RESPONSE",
            "message": f"Unexpected response (HTTP {response.status_code}). Please try again.",
        }
        if response.status_code >= 400:
            error["http_status"] = response.status_code
        if task_id:
            error["task_id"] = task_id
        _error_out(error)
        return {}

    if response.status_code >= 400:
        message = result.get("msg", result.get("message", f"HTTP {response.status_code}"))
        error = {
            "error": "HTTP_ERROR",
            "message": _sanitize_error_message(str(message)),
            "http_status": response.status_code,
        }
        if task_id:
            error["task_id"] = task_id
        _error_out(error)

    if result.get("code", 0) != 0:
        error = {
            "error": "IMAGE_API_ERROR",
            "message": _sanitize_error_message(
                str(result.get("msg", "Image request failed."))
            ),
        }
        if task_id:
            error["task_id"] = task_id
        _error_out(error)

    data = result.get("data")
    if not isinstance(data, dict):
        error = {
            "error": "INVALID_RESPONSE",
            "message": "The image service returned an invalid response.",
        }
        if task_id:
            error["task_id"] = task_id
        _error_out(error)

    return {
        "data": data,
        "request_id": result.get("requestId", ""),
    }


def _decode_image_base64(value: str) -> bytes:
    encoded = value.strip()
    if encoded.startswith("data:"):
        if ";base64," not in encoded:
            raise ValueError("Invalid image data URL.")
        encoded = encoded.split(";base64,", 1)[1]
    try:
        payload = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise ValueError("Invalid image Base64 data.") from exc
    if not payload:
        raise ValueError("Image Base64 data is empty.")
    if len(payload) >= _MAX_IMAGE_BYTES:
        raise ValueError("Image Base64 data must decode to less than 4 MB.")
    return payload


def _encode_image_file(path: str) -> str:
    try:
        with open(os.path.expanduser(path), "rb") as image_file:
            payload = image_file.read(_MAX_IMAGE_BYTES)
            exceeds_limit = bool(image_file.read(1))
    except (OSError, TypeError) as exc:
        raise ValueError("Unable to read --image-file.") from exc

    if not payload:
        raise ValueError("Image file is empty.")
    if len(payload) >= _MAX_IMAGE_BYTES or exceeds_limit:
        raise ValueError("Image file must be less than 4 MB.")
    return base64.b64encode(payload).decode("ascii")


def _build_image_edit_body(
    operation: str,
    image_url: str = None,
    image_base64: str = None,
    image_file: str = None,
    prompt: str = "",
) -> dict:
    if sum(bool(value) for value in (image_url, image_base64, image_file)) != 1:
        _error_out({
            "error": "INVALID_IMAGE_INPUT",
            "message": "Provide exactly one of --image-url, --image-base64, or --image-file.",
        })

    body = {
        "model": _OPERATION_MODELS[operation],
        "response_format": "url",
    }
    if image_url:
        parsed = urlparse(image_url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            _error_out({
                "error": "INVALID_IMAGE_URL",
                "message": "--image-url must be an HTTP(S) URL.",
            })
        body["image_url"] = [image_url]
    else:
        try:
            encoded = _encode_image_file(image_file) if image_file else image_base64
            _decode_image_base64(encoded)
        except ValueError as exc:
            _error_out({
                "error": "INVALID_IMAGE_FILE" if image_file else "INVALID_IMAGE_BASE64",
                "message": str(exc),
            })
        body["image"] = [encoded]
    if prompt:
        body["prompt"] = prompt
    return body


def _poll_image_task(
    endpoint: str,
    task_id: str,
    token: ***REDACTED***
    poll_interval: int,
    max_poll_time: int,
) -> dict:
    print(f"[INFO] Waiting for image task {task_id} to complete...", file=sys.stderr)
    start_time = time.time()

    while True:
        elapsed = time.time() - start_time
        if elapsed > max_poll_time:
            _error_out({
                "error": "POLL_TIMEOUT",
                "message": f"Image task did not complete within {max_poll_time}s.",
                "task_id": task_id,
            })

        result = _call_image_api(
            endpoint, "tasks", {"task_id": task_id}, token, task_id=task_id,
        )
        data = result["data"]
        status = str(data.get("status", "")).lower()

        if status == "completed":
            return result
        if status == "failed":
            upstream_error = data.get("error") or {}
            _error_out({
                "error": "IMAGE_EDIT_FAILED",
                "message": _sanitize_error_message(
                    str(upstream_error.get("message", "Image processing failed."))
                ),
                "task_id": task_id,
                "status": status,
            })
        if status not in ("queued", "in_progress"):
            _error_out({
                "error": "INVALID_TASK_STATUS",
                "message": "The image service returned an unknown task status.",
                "task_id": task_id,
            })

        print(
            f"[INFO] Image task {task_id}: status={status}, "
            f"elapsed={int(elapsed)}s, next check in {poll_interval}s ...",
            file=sys.stderr,
        )
        time.sleep(poll_interval)


def _image_extension(payload: bytes, content_type: str = "", url: str = "") -> str:
    signatures = (
        (b"\x89PNG\r\n\x1a\n", "png"),
        (b"\xff\xd8\xff", "jpg"),
        (b"GIF87a", "gif"),
        (b"GIF89a", "gif"),
        (b"BM", "bmp"),
    )
    for signature, extension in signatures:
        if payload.startswith(signature):
            return extension
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        return "webp"

    media_type = content_type.split(";", 1)[0].strip().lower()
    content_extensions = {
        "image/png": "png",
        "image/jpeg": "jpg",
        "image/gif": "gif",
        "image/webp": "webp",
        "image/bmp": "bmp",
    }
    if media_type in content_extensions:
        return content_extensions[media_type]

    path = urlparse(url).path.lower()
    match = re.search(r"\.([a-z0-9]{2,5})$", path)
    if match and match.group(1) in {"png", "jpg", "jpeg", "gif", "webp", "bmp"}:
        return "jpg" if match.group(1) == "jpeg" else match.group(1)
    return "png"


def _write_image_file(
    payload: bytes,
    task_id: str,
    index: int,
    extension: str,
    output_dir: str,
) -> str:
    safe_task_id = re.sub(r"[^A-Za-z0-9_-]", "_", task_id)[:80] or "task"
    filename = f"processed_image_{safe_task_id}_{index}.{extension}"
    output_path = os.path.abspath(os.path.join(output_dir, filename))
    temp_path = output_path + ".part"
    try:
        with open(temp_path, "wb") as output_file:
            output_file.write(payload)
        os.replace(temp_path, output_path)
    except (IOError, OSError):
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except OSError:
            pass
        raise
    return output_path


def _persist_image_results(task_data: dict, output_dir: str = None) -> list:
    task_id = str(task_data.get("id", ""))
    items = task_data.get("data") or []
    if not task_id or not isinstance(items, list) or not items:
        _error_out({
            "error": "IMAGE_RESULT_MISSING",
            "message": "The completed image task did not return an image result.",
            "task_id": task_id,
        })

    destination = os.path.abspath(output_dir or os.getcwd())
    files = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            _error_out({
                "error": "INVALID_IMAGE_RESULT",
                "message": "The image service returned an invalid result item.",
                "task_id": task_id,
            })

        source_url = item.get("url")
        encoded = item.get("b64_json")
        try:
            if source_url:
                response = requests.get(source_url, timeout=120)
                response.raise_for_status()
                payload = response.content
                extension = _image_extension(
                    payload, response.headers.get("Content-Type", ""), source_url,
                )
            elif encoded:
                payload = _decode_image_base64(encoded)
                extension = _image_extension(payload)
            else:
                raise ValueError("Result item has neither url nor b64_json.")
            path = _write_image_file(payload, task_id, index, extension, destination)
        except (requests.exceptions.RequestException, ValueError, IOError, OSError):
            _error_out({
                "error": "RESULT_DOWNLOAD_FAILED",
                "message": "Failed to save an image processing result locally.",
                "task_id": task_id,
            })
        files.append({"path": path})
    return files


def _format_task_output(result: dict, persist_result: bool = True) -> dict:
    data = result["data"]
    task_id = str(data.get("id", ""))
    output = {
        "task_id": task_id,
        "status": data.get("status", ""),
    }
    for field in ("created_at", "completed_at", "expires_at"):
        if data.get(field) is not None:
            output[field] = data[field]
    if result.get("request_id"):
        output["request_id"] = result["request_id"]
    if data.get("status") == "completed" and persist_result:
        output["result_files"] = _persist_image_results(data)
    if data.get("status") == "failed" and data.get("error"):
        task_error = data["error"]
        output["error"] = {
            "code": task_error.get("code", ""),
            "message": _sanitize_error_message(str(task_error.get("message", ""))),
        }
    return output


def _run_image_edit(args, token: ***REDACTED***
    body = _build_image_edit_body(
        args.operation,
        image_url=args.image_url,
        image_base64=args.image_base64,
        image_file=args.image_file,
        prompt=args.prompt,
    )
    try:
        submit_result = _call_image_api(endpoint, "edits", body, token)
    except requests.exceptions.Timeout:
        _error_out({
            "error": "SUBMISSION_STATUS_UNKNOWN",
            "message": (
                "The image submission timed out and may have created a task. "
                "It was not retried."
            ),
        })
    except requests.exceptions.RequestException:
        _error_out({
            "error": "CONNECTION_ERROR",
            "message": "Failed to connect to the image service. The request was not retried.",
        })

    task_data = submit_result["data"]
    task_id = str(task_data.get("id", ""))
    if not task_id:
        _error_out({
            "error": "NO_TASK_ID",
            "message": "The image service did not return a task ID. The request was not retried.",
        })

    print(f"[INFO] Image task submitted: {task_id}", file=sys.stderr)
    if args.no_poll:
        _safe_print_json(_format_task_output(submit_result, persist_result=False))
        return

    try:
        result = _poll_image_task(
            endpoint, task_id, token, args.poll_interval, args.max_poll_time,
        )
    except requests.exceptions.RequestException:
        _error_out({
            "error": "TASK_QUERY_FAILED",
            "message": "Failed to query the existing image task.",
            "task_id": task_id,
        })
    _safe_print_json(_format_task_output(result))


def _query_image_task(args, token: ***REDACTED***
    try:
        result = _call_image_api(
            endpoint, "tasks", {"task_id": args.task_id}, token, task_id=args.task_id,
        )
    except requests.exceptions.RequestException:
        _error_out({
            "error": "TASK_QUERY_FAILED",
            "message": "Failed to query the existing image task.",
            "task_id": args.task_id,
        })
    _safe_print_json(_format_task_output(result))


def _add_common_args(parser, include_poll=True):
    parser.add_argument(
        "--token",
        default="",
        help="Short-lived ck_t_ Client API Key",
    )
    parser.add_argument(
        "--endpoint",
        default=None,
        help="Override the image service endpoint URL",
    )
    if include_poll:
        parser.add_argument(
            "--no-poll",
            action="store_true",
            help="Submit only and do not wait for the result",
        )
        parser.add_argument(
            "--poll-interval",
            type=int,
            default=5,
            help="Seconds between status checks",
        )
        parser.add_argument(
            "--max-poll-time",
            type=int,
            default=600,
            help="Maximum seconds to wait for completion",
        )


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Buddy Image Processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  buddy-image-processing.py image-edit --operation erase "
            "--image-file ./photo.png --token <ck_t_>\n"
            "  buddy-image-processing.py status <task_id> --token <ck_t_>\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", help="Image processing command")

    edit_parser = subparsers.add_parser("image-edit", help="Process an existing image")
    edit_parser.add_argument(
        "--operation",
        required=True,
        choices=sorted(_OPERATION_MODELS),
        help="Image operation: erase, restore, enhance, beauty, or matting",
    )
    image_input = edit_parser.add_mutually_exclusive_group(required=True)
    image_input.add_argument("--image-url", help="HTTP(S) URL of the source image")
    image_input.add_argument(
        "--image-base64",
        help="Source image Base64 data, decoded size <4 MB",
    )
    image_input.add_argument(
        "--image-file",
        help="Local image file path, size <4 MB",
    )
    edit_parser.add_argument(
        "--prompt",
        default="",
        help="Optional processing instruction passed through unchanged",
    )
    _add_common_args(edit_parser)

    status_parser = subparsers.add_parser("status", help="Check an existing image task")
    status_parser.add_argument("task_id", help="Task ID to check")
    _add_common_args(status_parser, include_poll=False)
    return parser


def main():
    parser = _build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    token = ***REDACTED***
    endpoint = args.endpoint or _DEFAULT_ENDPOINT

    try:
        if args.command == "image-edit":
            _run_image_edit(args, token, endpoint)
        elif args.command == "status":
            _query_image_task(args, token, endpoint)
        else:
            _error_out({
                "error": "UNKNOWN_COMMAND",
                "message": f"Unknown command: {args.command}",
            })
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[DEBUG] {_redact_token(str(exc))}", file=***REDACTED***
        _error_out({
            "error": "UNEXPECTED_ERROR",
            "message": "An unexpected error occurred. Please try again or check the logs.",
        })


if __name__ == "__main__":
    main()
