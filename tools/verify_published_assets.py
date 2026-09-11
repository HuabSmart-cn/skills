#!/usr/bin/env python3
"""Verify that files changed in a deployment are reachable from the public site.

This check runs after rsync, so it proves the deployed HTTP path rather than
only the Git checkout. It intentionally checks only changed public asset files:
checking every historical attachment on every deployment would create thousands
of unnecessary requests and make a transient external failure block unrelated
documentation changes.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def changed_asset_files(before: str, after: str) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", before, after, "--", "skills"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line and (ROOT / line).is_file()]


def public_url(base_url: str, path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    return base_url.rstrip("/") + "/" + "/".join(urllib.parse.quote(part) for part in relative.split("/"))


def verify(path: Path, base_url: str, timeout: float) -> str | None:
    url = public_url(base_url, path)
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "HuabSmart-Deploy-Verification/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return f"{path.relative_to(ROOT)}: expected HTTP 200, got {response.status} ({url})"
            remote_size = response.headers.get("Content-Length")
            if remote_size is not None and remote_size.isdigit() and int(remote_size) != path.stat().st_size:
                return f"{path.relative_to(ROOT)}: Content-Length {remote_size} does not match {path.stat().st_size} ({url})"
    except urllib.error.HTTPError as exc:
        return f"{path.relative_to(ROOT)}: expected HTTP 200, got {exc.code} ({url})"
    except (urllib.error.URLError, TimeoutError) as exc:
        return f"{path.relative_to(ROOT)}: public HEAD request failed ({exc}) ({url})"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--before", required=True, help="commit before deployment")
    parser.add_argument("--after", required=True, help="deployed commit")
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--workers", type=int, default=12)
    args = parser.parse_args()
    files = changed_asset_files(args.before, args.after)
    if not files:
        print("No changed public asset files; published attachment check skipped.")
        return 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        failures = [failure for failure in pool.map(lambda item: verify(item, args.base_url, args.timeout), files) if failure]
    if failures:
        print("Published asset verification failed:", *failures, sep="\n- ", file=sys.stderr)
        return 1
    print(f"Verified {len(files)} changed public asset file(s) by HTTP HEAD.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
