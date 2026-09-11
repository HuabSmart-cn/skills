#!/usr/bin/env python3
"""Materialize repository file sizes in the legacy public manifest.

The manifest is the website's asset-discovery index.  A missing size is not a
zero-byte file, so every companion file is represented as ``{path, size}``.
This tool is deterministic and intentionally performs no network access.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for asset in manifest.get("assets", []):
        metadata = asset.get("asset", {})
        directory = metadata.get("directory")
        attachments = metadata.get("attachments", [])
        unavailable = metadata.get("unavailableAttachments", [])
        if not directory or not isinstance(attachments, list) or not isinstance(unavailable, list):
            continue
        enriched = []
        unavailable_next = []
        seen = set()
        for item in [*attachments, *unavailable]:
            path = item if isinstance(item, str) else item.get("path")
            if not isinstance(path, str) or not path:
                raise ValueError(f"Invalid attachment for {asset.get('id')}: {item!r}")
            if path in seen:
                continue
            seen.add(path)
            file_path = ROOT / directory / path
            if not file_path.is_file():
                unavailable_next.append({"path": path, "reason": "file_missing"})
            else:
                enriched.append({"path": path, "size": file_path.stat().st_size})
        metadata["attachments"] = enriched
        if unavailable_next:
            metadata["unavailableAttachments"] = unavailable_next
        else:
            metadata.pop("unavailableAttachments", None)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
