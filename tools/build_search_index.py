#!/usr/bin/env python3
"""Build the lightweight, public search directory for every catalog asset."""
from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OUTPUT = ROOT / "registry" / "search-index.json"
VERSION_ONLY = re.compile(r"^v?\d+(?:\.\d+){1,3}$")


def text_values(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for item in (value.get("zh"), value.get("en")) if isinstance(item, str) and item]
    return []


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    categories = {item["id"]: item.get("name", {}) for item in manifest.get("categories", []) if isinstance(item, dict) and item.get("id")}
    platforms = {item["id"]: item.get("name", {}) for item in manifest.get("platforms", []) if isinstance(item, dict) and item.get("id")}
    entries = []
    for asset in manifest["assets"]:
        meta = asset["asset"]
        names = []
        for value in (asset.get("displayName"), asset.get("profession"), asset.get("agentName")):
            names.extend(text_values(value))
        names = [name for name in dict.fromkeys(names) if not VERSION_ONLY.fullmatch(name)]
        tags = list(dict.fromkeys(tag for item in asset.get("tags", []) for tag in text_values(item)))
        platform_id, category_id = asset.get("platformId"), asset.get("categoryId")
        entries.append({
            "assetId": asset["id"],
            "names": names,
            "summary": asset.get("description", {}),
            "tags": tags,
            "kind": asset.get("sourceKind"),
            "platform": {"id": platform_id, "name": platforms.get(platform_id, asset.get("platformName", {}))},
            "category": {"id": category_id, "name": categories.get(category_id, {})},
            "artifact": {"directory": meta["directory"], "entry": meta["primaryFile"]},
            "status": "cataloged_unverified",
        })
    payload = {
        "schemaVersion": "1.0.0",
        "kind": "huabsmart-capability-search-index",
        "source": {"repository": "HuabSmart-cn/skills", "manifestVersion": manifest.get("version"), "assetCount": len(entries)},
        "resolutionRules": {
            "exactAssetId": "Select the exact assetId when supplied.",
            "uniqueName": "A unique name match may be proposed, but install needs explicit user approval.",
            "multipleMatches": "Compare summary, tags, platform, kind, and artifact before asking the user to choose; never silently select.",
            "noMatch": "Report dependency_missing; never simulate installation or invocation."
        },
        "entries": entries,
    }
    # This is a machine-facing network index. Compact JSON keeps the public
    # artifact and Git history small; its generator is the maintainable source.
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(entries)} entries")


if __name__ == "__main__":
    main()
