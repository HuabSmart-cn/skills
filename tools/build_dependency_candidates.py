#!/usr/bin/env python3
"""Extract conservative cross-asset Skill references from captured source files.

The output is *not* an executable dependency graph.  It records only explicit
textual call patterns and never upgrades a match to required/optional.  A
maintainer or a runtime probe must make that decision in registry metadata.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.json"
OUTPUT = ROOT / "registry/dependency-candidates.json"

CALL_PATTERNS = [
    re.compile(r"Call (?:the )?Skill tool (?:twice, )?for\s+[\"`']([A-Za-z0-9._-]+)[\"`']", re.I),
    re.compile(r"Call (?:the )?Skill tool with\s+[\"`']([A-Za-z0-9._-]+)[\"`']", re.I),
    re.compile(r"(?:自动调用|调用)\s*[`'\"「]?([A-Za-z][A-Za-z0-9._-]{1,})[`'\"」]?\s*(?:Skill|技能)", re.I),
]
# Explicit bullet syntax used by several captured WorkBuddy agents.
AUTO_BULLET = re.compile(r"^\s*[-*]\s*\*\*([A-Za-z][A-Za-z0-9._-]{1,})\*\*.*(?:自动调用|自动触发)", re.I)


def normalize(name: str) -> str:
    return name.strip().lower()


def entry_path(asset: dict) -> Path | None:
    meta = asset.get("asset", {})
    directory, primary = meta.get("directory"), meta.get("primaryFile")
    if not isinstance(directory, str) or not isinstance(primary, str): return None
    path = ROOT / directory / primary
    return path if path.is_file() else None


def names_for(asset: dict, path: Path | None) -> set[str]:
    names = {asset.get("agentName", "")}
    if path:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[:40]
        for line in lines:
            match = re.match(r"name:\s*[\"']?([^\"'#]+)", line.strip(), re.I)
            if match: names.add(match.group(1).strip())
    return {normalize(name) for name in names if isinstance(name, str) and name.strip()}


def evidence(text: str) -> list[tuple[str, int, str]]:
    matches = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for pattern in CALL_PATTERNS:
            for match in pattern.finditer(line):
                matches.append((normalize(match.group(1)), line_no, line.strip()))
        bullet = AUTO_BULLET.search(line)
        if bullet: matches.append((normalize(bullet.group(1)), line_no, line.strip()))
    return matches


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = manifest["assets"]
    name_index: dict[str, set[str]] = defaultdict(set)
    paths: dict[str, Path | None] = {}
    for asset in assets:
        path = entry_path(asset)
        paths[asset["id"]] = path
        for name in names_for(asset, path): name_index[name].add(asset["id"])
    records = []
    for asset in assets:
        source_id, path = asset["id"], paths[asset["id"]]
        if not path: continue
        candidates = []
        for name, line, excerpt in evidence(path.read_text(encoding="utf-8", errors="replace")):
            targets = sorted(name_index.get(name, set()) - {source_id})
            status = "resolved_candidate" if len(targets) == 1 else "ambiguous" if targets else "unresolved"
            candidates.append({
                "mentionedAs": name, "status": status, "candidateAssetIds": targets,
                "evidence": {"path": str(path.relative_to(ROOT)), "line": line, "excerpt": excerpt},
            })
        # Keep one source/name/line record; repeated prose elsewhere remains evidence, not an edge.
        unique = {(x["mentionedAs"], x["evidence"]["line"]): x for x in candidates}
        if unique:
            records.append({"sourceAssetId": source_id, "candidates": list(unique.values())})
    payload = {
        "$schema": "schemas/dependency-candidates-v1.schema.json",
        "schemaVersion": "1.0.0",
        "sourceManifestVersion": manifest.get("version"),
        "sourceManifestGeneratedAt": manifest.get("generatedAt"),
        "semantics": "textual-candidates-only",
        "records": sorted(records, key=lambda row: row["sourceAssetId"]),
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = defaultdict(int)
    for row in records:
        for candidate in row["candidates"]: counts[candidate["status"]] += 1
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(records)} source assets, {dict(sorted(counts.items()))}")


if __name__ == "__main__": main()
