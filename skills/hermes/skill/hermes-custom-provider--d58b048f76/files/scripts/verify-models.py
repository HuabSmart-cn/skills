#!/usr/bin/env python3
"""Batch-probe a candidate model list against an OpenAI-compatible endpoint.

Given a base URL, API key, and a list of model IDs, send a one-token chat
request to each and bucket the result:

    200  -> real, your key/subscription can call it
    403  -> exists on the platform but your subscription tier doesn't include it
    404  -> model literally doesn't exist on the gateway
    other -> transport / auth / other failure

Use this BEFORE you commit model IDs to `model_aliases:` in config.yaml.
The official `/v1/models` catalog and vendor docs ("plan X supports Y, Z") are
*platform* support — not necessarily your individual subscription tier.
Trust HTTP status codes from a real chat completion, not the catalog.

Usage:
    python3 verify-models.py \
        --base-url https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1 \
        --api-key-env ALIBABA_TOKEN_PLAN_API_KEY \
        --models qwen3.7-plus qwen3.6-plus qwen3.6-flash kimi-k2.5 glm-5.2

Or pass the key directly with --api-key (avoid shell history):
    ***REDACTED***
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def probe(base_url: str, api_key: str, model: str, timeout: float = 15.0) -> tuple[int, str]:
    """Return (http_status, response_body_snippet)."""
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "p"}],
        "max_tokens": ***REDACTED***
    }).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": ***REDACTED***
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode()
            return resp.status, data[:120]
    except urllib.error.HTTPError as e:
        return e.code, (e.read().decode(errors="replace") if e.fp else "")[:120]
    except Exception as e:
        return 0, f"EXC: {type(e).__name__}: {e}"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base-url", required=True)
    p.add_argument("--api-key-env", help=***REDACTED***
    p.add_argument("--api-key", help=***REDACTED***
    p.add_argument("--models", nargs="+", required=True)
    p.add_argument("--timeout", type=float, default=15.0)
    args = p.parse_args()

    key = args.api_key or (os.environ.get(args.api_key_env) if args.api_key_env else None)
    if not key:
        print(f"ERROR: --api-key or --api-key-env must provide a non-empty key", file=sys.stderr)
        return 2

    buckets: dict[int, list[tuple[str, str]]] = {}
    for m in args.models:
        code, snippet = probe(args.base_url, key, m, timeout=args.timeout)
        buckets.setdefault(code, []).append((m, snippet))
        print(f"{m:<35} HTTP={code:<3}  {snippet}")

    print()
    print("=" * 60)
    print(f"SUMMARY")
    print(f"  200 (callable): {len(buckets.get(200, []))}")
    print(f"  403 (subscription restricted): {len(buckets.get(403, []))}")
    print(f"  404 (not in gateway): {len(buckets.get(404, []))}")
    other = sum(len(v) for k, v in buckets.items() if k not in (200, 403, 404))
    print(f"  other: {other}")
    return 0


if __name__ == "__main__":
    sys.exit(main())