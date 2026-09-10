#!/usr/bin/env python3
"""Make a non-destructive dependency plan for an HuabSmart download bundle.

This tool resolves only against a supplied HuabSmart repository. It never
searches the web, downloads arbitrary same-name files, or changes an install.
The caller may execute the returned plan in its own runtime-specific installer.
"""
from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path


def read_sidecar(bundle: Path) -> dict:
    if bundle.is_dir():
        return json.loads((bundle / "HBS_BUNDLE.json").read_text(encoding="utf-8"))
    with zipfile.ZipFile(bundle) as archive:
        names = [name for name in archive.namelist() if name.endswith("/HBS_BUNDLE.json")]
        if len(names) != 1: raise ValueError("Bundle must contain exactly one HBS_BUNDLE.json")
        return json.loads(archive.read(names[0]).decode("utf-8"))


def load_registry(root: Path) -> tuple[dict, dict]:
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assets = {asset["id"]: asset for asset in manifest["assets"]}
    index = json.loads((root / "registry/index.json").read_text(encoding="utf-8"))
    capabilities = {}
    for row in index["capabilities"]:
        detail = root / "registry" / row["detail"]
        capabilities[row["id"]] = json.loads(detail.read_text(encoding="utf-8"))
    return assets, capabilities


def load_installed(path: Path | None) -> tuple[set[str], set[str]]:
    if not path: return set(), set()
    state = json.loads(path.read_text(encoding="utf-8"))
    return set(state.get("assetIds", [])), set(state.get("capabilityIds", []))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, help="ZIP created by build_download_bundle.py or its extracted directory")
    parser.add_argument("--repository-root", required=True, help="Trusted clone or mirror of HuabSmart Skills")
    parser.add_argument("--installed-index", help="Optional JSON: {assetIds: [], capabilityIds: []}")
    parser.add_argument("--allow-resolved-textual-candidates", action="store_true")
    parser.add_argument("--output", help="Write plan JSON to this path instead of stdout")
    args = parser.parse_args()
    sidecar = read_sidecar(Path(args.bundle))
    root = Path(args.repository_root).resolve()
    assets, capabilities = load_registry(root)
    installed_assets, installed_capabilities = load_installed(Path(args.installed_index) if args.installed_index else None)
    actions, blocked = [], []

    def resolve_capability(capability_id: str, requirement: str) -> None:
        detail = capabilities.get(capability_id)
        if not detail:
            blocked.append({"code": "DEPENDENCY_REQUIRED_MISSING", "dependency": capability_id,
                            "reason": "Capability is absent from the trusted registry."})
            return
        asset_id = detail.get("artifact", {}).get("legacyAssetId")
        asset = assets.get(asset_id)
        if not asset:
            blocked.append({"code": "DEPENDENCY_REQUIRED_MISSING", "dependency": capability_id,
                            "reason": "Capability has no installable asset in this registry."})
            return
        entry = root / asset["asset"]["directory"] / asset["asset"]["primaryFile"]
        if not entry.is_file():
            blocked.append({"code": "ENTRY_MISSING", "dependency": capability_id, "assetId": asset_id,
                            "reason": "Registry entry file is unavailable."})
        elif capability_id in installed_capabilities or asset_id in installed_assets:
            actions.append({"action": "already_installed", "requirement": requirement, "capabilityId": capability_id, "assetId": asset_id})
        else:
            actions.append({"action": "install", "requirement": requirement, "capabilityId": capability_id,
                            "assetId": asset_id, "sourceDirectory": asset["asset"]["directory"], "entry": asset["asset"]["primaryFile"]})

    declared = sidecar.get("declaredDependencies", {})
    for dependency in declared.get("required", []):
        resolve_capability(dependency.get("id") if isinstance(dependency, dict) else dependency, "required")
    for dependency in declared.get("optional", []):
        resolve_capability(dependency.get("id") if isinstance(dependency, dict) else dependency, "optional")
    for candidate in sidecar.get("textualCandidates", []):
        status, target_ids = candidate.get("status"), candidate.get("candidateAssetIds", [])
        mentioned = candidate.get("mentionedAs")
        if status == "resolved_candidate" and len(target_ids) == 1 and args.allow_resolved_textual_candidates:
            target = target_ids[0]
            if target in installed_assets:
                actions.append({"action": "already_installed", "requirement": "textual_candidate", "assetId": target, "mentionedAs": mentioned})
            elif target in assets:
                asset = assets[target]
                actions.append({"action": "install_candidate", "requirement": "textual_candidate", "assetId": target,
                                "mentionedAs": mentioned, "sourceDirectory": asset["asset"]["directory"], "entry": asset["asset"]["primaryFile"]})
        elif status == "resolved_candidate":
            blocked.append({"code": "TEXTUAL_CANDIDATE_REQUIRES_OPT_IN", "mentionedAs": mentioned,
                            "candidateAssetIds": target_ids, "reason": "Pass --allow-resolved-textual-candidates to plan this inferred install."})
        elif status == "ambiguous":
            blocked.append({"code": "DEPENDENCY_AMBIGUOUS", "mentionedAs": mentioned, "candidateAssetIds": target_ids,
                            "reason": "Choose a compatible implementation; no automatic selection was made."})
        elif status == "unresolved":
            blocked.append({"code": "DEPENDENCY_MISSING", "mentionedAs": mentioned,
                            "reason": "No matching asset exists in the trusted registry."})
    is_blocked = any(item["code"] in {"DEPENDENCY_REQUIRED_MISSING", "ENTRY_MISSING", "DEPENDENCY_AMBIGUOUS", "DEPENDENCY_MISSING"} for item in blocked)
    plan = {"schemaVersion": "1.0.0", "bundleAssetId": sidecar.get("asset", {}).get("id"),
            "planStatus": "blocked" if is_blocked else "ready_for_runtime_install",
            "runtimeVerification": "not_verified",
            "actions": actions, "blocked": blocked}
    rendered = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
    if args.output: Path(args.output).write_text(rendered, encoding="utf-8")
    else: print(rendered, end="")


if __name__ == "__main__": main()
