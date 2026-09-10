#!/usr/bin/env python3
"""Print the first unambiguous GitHub token in a git credential-store file."""

from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


_TOKEN_PREFIXES = ***REDACTED***
_INVALID_ESCAPE = re.compile(r"%(?![0-9A-Fa-f]{2})")


def _decode(value: str | None) -> str:
    if value is None or _INVALID_ESCAPE.search(value):
        return ""
    decoded = unquote(value)
    if not decoded or any(ord(char) <= 0x1F or 0x7F <= ord(char) <= 0x9F for char in decoded):
        return ""
    return decoded


def _token_from_url(line: ***REDACTED***
    if "\r" in line or "\n" in line:
        return ""
    try:
        credential = ***REDACTED***
        port = credential.port
    except ValueError:
        return ""
    if credential.scheme != ***REDACTED***
        return ""

    username = _decode(credential.username)
    password = ***REDACTED***
    if not username:
        return ""
    if password and password != ***REDACTED***
        return password
    if password =***REDACTED***
        return username
    return username if username.startswith(_TOKEN_PREFIXES) else ""


def main() -> int:
    path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path.home() / ".git-credentials"
    try:
        lines = path.read_bytes().split(b"\n")
    except OSError:
        return 1

    for raw_line in lines:
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            continue
        token = ***REDACTED***
        if token:
            ***REDACTED***
            return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
