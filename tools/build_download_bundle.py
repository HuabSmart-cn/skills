#!/usr/bin/env python3
"""Create one downloadable asset bundle with a non-invasive dependency sidecar."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--output", required=True, help="Output ZIP path")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    asset = next((x for x in manifest["assets"] if x["id"] == args.asset_id), None)
    if not asset: raise SystemExit(f"Unknown asset id: {args.asset_id}")
    meta = asset["asset"]
    source = ROOT / meta["directory"]
    entry = source / meta["primaryFile"]
    if not source.is_dir() or not entry.is_file(): raise SystemExit(f"Asset entry is unavailable: {entry}")
    candidates = json.loads((ROOT / "registry/dependency-candidates.json").read_text(encoding="utf-8"))
    row = next((x for x in candidates["records"] if x["sourceAssetId"] == args.asset_id), None)
    registry_index = json.loads((ROOT / "registry/index.json").read_text(encoding="utf-8"))
    declared = {"required": [], "optional": []}
    for capability_row in registry_index["capabilities"]:
        detail_path = ROOT / "registry" / capability_row["detail"]
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
        if detail.get("artifact", {}).get("legacyAssetId") == args.asset_id:
            declared = detail.get("dependencies", declared)
            break
    try: revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError): revision = "unknown"
    sidecar = {
        "schemaVersion": "1.0.0",
        "asset": {"id": args.asset_id, "entry": meta["primaryFile"], "sourceRevision": revision},
        "registry": {
            "searchIndexUrl": "https://raw.githubusercontent.com/HuabSmart-cn/skills/main/registry/search-index.json",
            "searchIndexPageUrl": "https://github.com/HuabSmart-cn/skills/blob/main/registry/search-index.json",
            "resolutionPolicy": "trusted-github-registry-only"
        },
        "declaredDependencies": declared,
        "textualCandidates": row["candidates"] if row else [],
        "installerBehavior": {
            "resolved_candidate": "May propose the exact candidate; do not install without the caller's install policy.",
            "ambiguous": "Do not choose automatically; present compatible candidates or request a preference.",
            "unresolved": "Return dependency_missing; never claim invocation or installation succeeded."
        }
    }
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hbs-skill-") as temp:
        staging = Path(temp) / source.name
        shutil.copytree(source, staging)
        sidecar["bundleKind"] = "huabsmart-download-bundle"
        sidecar["verification"] = {"runtime": "not_verified", "meaning": "Package metadata was generated; no Runtime install, discovery, load, or invocation has been proven."}
        (staging / "HBS_BUNDLE.json").write_text(json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        archive_base = output.with_suffix("")
        made = Path(shutil.make_archive(str(archive_base), "zip", root_dir=Path(temp), base_dir=source.name))
        if made != output: made.replace(output)
    print(output)


if __name__ == "__main__": main()
