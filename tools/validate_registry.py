#!/usr/bin/env python3
"""Static validation for the HuabSmart capability registry.

This deliberately does not execute assets, contact services, inspect secrets, or
claim that a third-party runtime is installed.  It validates only repository
facts and metadata declarations.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAP_ID = re.compile(r"^cap\.(skill|agent|prompt|mcp|plugin|workflow|knowledge)\.[a-z0-9.-]+\.v[0-9]+$")
KINDS = {"skill", "agent", "prompt", "mcp", "plugin", "workflow", "knowledge"}
STATUSES = {"available", "incomplete", "dependency_missing", "runtime_unsupported", "deprecated", "unverified", "archived"}
OPERATIONS = {"read", "create", "update", "delete", "auth", "external_write", "publish", "execute", "search"}
ERROR_CODES = {
    "DEPENDENCY_REQUIRED_MISSING", "DEPENDENCY_OPTIONAL_MISSING", "DEPENDENCY_CYCLE",
    "ENTRY_MISSING", "INVALID_PATH", "ID_CONFLICT", "ALIAS_CONFLICT", "INVALID_FIELD",
    "VERIFICATION_RECEIPT_MISSING", "LEGACY_ENTRY_MISSING",
}


class Reporter:
    def __init__(self): self.items = []
    def add(self, code, severity, message, path=None, asset_id=None, remediation=None):
        self.items.append({"code": code, "severity": severity, "assetId": asset_id,
                           "path": str(path) if path else None, "message": message,
                           "remediation": remediation})


def read_json(path: Path, report: Reporter):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report.add("INVALID_FIELD", "error", f"Cannot parse JSON: {exc}", path)
        return None


def safe_relative(value, report, path, asset_id):
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        report.add("INVALID_PATH", "error", "Path must be a non-empty repository-relative path without '..'.", path, asset_id)
        return None
    return ROOT / value


def validate_legacy(report: Reporter, severity: str):
    manifest = read_json(ROOT / "manifest.json", report)
    if not isinstance(manifest, dict): return
    assets = manifest.get("assets")
    if not isinstance(assets, list):
        report.add("INVALID_FIELD", "error", "manifest.assets must be an array.", ROOT / "manifest.json")
        return
    if manifest.get("count") != len(assets):
        report.add("INVALID_FIELD", "error", "manifest.count does not equal assets.length.", ROOT / "manifest.json")
    categories = {x.get("id") for x in manifest.get("categories", []) if isinstance(x, dict)}
    platforms = {x.get("id") for x in manifest.get("platforms", []) if isinstance(x, dict)}
    seen = set()
    for asset in assets:
        aid = asset.get("id") if isinstance(asset, dict) else None
        if not isinstance(aid, str) or not aid:
            report.add("INVALID_FIELD", "error", "Asset needs a non-empty id.", ROOT / "manifest.json")
            continue
        if aid in seen: report.add("ID_CONFLICT", "error", "Duplicate legacy asset id.", ROOT / "manifest.json", aid)
        seen.add(aid)
        if asset.get("categoryId") not in categories:
            report.add("INVALID_FIELD", "error", "Unknown categoryId.", ROOT / "manifest.json", aid)
        if asset.get("platformId") not in platforms:
            report.add("INVALID_FIELD", "error", "Unknown platformId.", ROOT / "manifest.json", aid)
        meta = asset.get("asset", {})
        base = safe_relative(meta.get("directory"), report, ROOT / "manifest.json", aid)
        entry = meta.get("primaryFile")
        if base and isinstance(entry, str) and entry and "/" not in entry and "\\" not in entry:
            if not (base / entry).is_file():
                report.add("LEGACY_ENTRY_MISSING", severity, "Legacy primaryFile does not exist.", base / entry, aid,
                           "Repair the captured asset or mark it withheld in migration metadata.")
        else:
            report.add("INVALID_PATH", "error", "asset.primaryFile must be a file name.", ROOT / "manifest.json", aid)


def validate_registry(report: Reporter):
    index_path = ROOT / "registry/index.json"
    index = read_json(index_path, report)
    if not isinstance(index, dict): return
    records = index.get("capabilities")
    if not isinstance(records, list):
        report.add("INVALID_FIELD", "error", "registry capabilities must be an array.", index_path); return
    ids, aliases, details = set(), {}, {}
    for row in records:
        if not isinstance(row, dict):
            report.add("INVALID_FIELD", "error", "Registry entry must be an object.", index_path); continue
        cid = row.get("id")
        if not isinstance(cid, str) or not CAP_ID.fullmatch(cid):
            report.add("INVALID_FIELD", "error", "Invalid canonical capability id.", index_path, cid); continue
        if cid in ids: report.add("ID_CONFLICT", "error", "Duplicate capability id.", index_path, cid)
        if cid in aliases: report.add("ALIAS_CONFLICT", "error", f"Canonical id conflicts with alias owned by {aliases[cid]}.", index_path, cid)
        ids.add(cid)
        if row.get("kind") not in KINDS or row.get("status") not in STATUSES:
            report.add("INVALID_FIELD", "error", "Invalid kind or status.", index_path, cid)
        target = safe_relative("registry/" + str(row.get("detail", "")), report, index_path, cid)
        detail = read_json(target, report) if target else None
        if not isinstance(detail, dict): continue
        details[cid] = detail
        required = {"schemaVersion", "id", "kind", "identity", "summary", "artifact", "origin", "dependencies", "runtime", "permissions", "contracts", "failurePolicy", "lifecycle", "verification"}
        missing = required - detail.keys()
        if missing: report.add("INVALID_FIELD", "error", f"Missing required fields: {sorted(missing)}", target, cid)
        if detail.get("id") != cid or detail.get("kind") != row.get("kind"):
            report.add("INVALID_FIELD", "error", "Index and detail id/kind must agree.", target, cid)
        artifact = detail.get("artifact", {})
        root = safe_relative(artifact.get("root"), report, target, cid)
        entry = artifact.get("entry")
        if root and isinstance(entry, str) and "/" not in entry and "\\" not in entry:
            if not (root / entry).is_file(): report.add("ENTRY_MISSING", "error", "Capability entry file does not exist.", root / entry, cid)
        else: report.add("INVALID_PATH", "error", "artifact.entry must be a file name.", target, cid)
        for alias in detail.get("identity", {}).get("aliases", []):
            if not isinstance(alias, str) or not alias:
                report.add("INVALID_FIELD", "error", "Alias must be a non-empty string.", target, cid); continue
            if alias in aliases or alias in ids:
                report.add("ALIAS_CONFLICT", "error", f"Alias conflicts with {aliases.get(alias, alias)}.", target, cid)
            aliases[alias] = cid
        operations = detail.get("permissions", {}).get("operations", [])
        if not isinstance(operations, list) or not set(operations) <= OPERATIONS:
            report.add("INVALID_FIELD", "error", "Unknown permission operation.", target, cid)
        policy = detail.get("failurePolicy", {})
        if policy.get("mode") not in {"must_execute", "no_fallback", "llm_fallback_allowed"}:
            report.add("INVALID_FIELD", "error", "Invalid failurePolicy.mode.", target, cid)
        if set(operations) & {"create", "update", "delete", "external_write", "publish", "search"} and policy.get("mode") == "llm_fallback_allowed":
            report.add("INVALID_FIELD", "error", "Observed external or state-changing operations cannot allow an LLM fallback.", target, cid)
        runtime = detail.get("runtime", {})
        hosts = runtime.get("hosts", [])
        if not isinstance(hosts, list) or not hosts:
            report.add("INVALID_FIELD", "error", "runtime.hosts must declare at least one host runtime.", target, cid)
        for host in hosts if isinstance(hosts, list) else []:
            if not isinstance(host, dict) or host.get("compatibility") not in {"supported", "adaptable", "unsupported", "unverified"}:
                report.add("INVALID_FIELD", "error", "Invalid runtime compatibility declaration.", target, cid)
        for env in runtime.get("environment", []):
            if not isinstance(env, dict) or not re.fullmatch(r"[A-Z][A-Z0-9_]*", str(env.get("name", ""))) or not isinstance(env.get("required"), bool):
                report.add("INVALID_FIELD", "error", "Environment requirement needs uppercase name and boolean required; never store its value.", target, cid)
        verification = detail.get("verification", {})
        if verification.get("status") == "verified" and not verification.get("receipts"):
            report.add("VERIFICATION_RECEIPT_MISSING", "error", "Verified status requires at least one receipt.", target, cid)
    graph = defaultdict(list)
    for cid, detail in details.items():
        deps = detail.get("dependencies", {})
        for group, severity in (("required", "error"), ("optional", "warning")):
            values = deps.get(group, [])
            if not isinstance(values, list):
                report.add("INVALID_FIELD", "error", f"dependencies.{group} must be an array.", None, cid); continue
            for dep in values:
                target = dep.get("id") if isinstance(dep, dict) else None
                if target not in ids:
                    report.add("DEPENDENCY_REQUIRED_MISSING" if group == "required" else "DEPENDENCY_OPTIONAL_MISSING", severity,
                               f"{group} dependency is not registered: {target}", None, cid)
                elif group == "required": graph[cid].append(target)
    visiting, visited = set(), set()
    def visit(node, trail):
        if node in visiting:
            report.add("DEPENDENCY_CYCLE", "error", "Required dependency cycle: " + " -> ".join(trail + [node]), None, node); return
        if node in visited: return
        visiting.add(node)
        for nxt in graph[node]: visit(nxt, trail + [node])
        visiting.remove(node); visited.add(node)
    for node in ids: visit(node, [])


def validate_dependency_candidates(report: Reporter):
    path = ROOT / "registry/dependency-candidates.json"
    payload = read_json(path, report)
    if not isinstance(payload, dict): return
    if payload.get("semantics") != "textual-candidates-only":
        report.add("INVALID_FIELD", "error", "Dependency candidate report must retain textual-candidates-only semantics.", path)
        return
    manifest = read_json(ROOT / "manifest.json", report)
    asset_ids = {asset.get("id") for asset in manifest.get("assets", []) if isinstance(asset, dict)} if isinstance(manifest, dict) else set()
    for record in payload.get("records", []):
        source = record.get("sourceAssetId") if isinstance(record, dict) else None
        if source not in asset_ids:
            report.add("INVALID_FIELD", "error", "Candidate source asset is absent from manifest.", path, source)
            continue
        for candidate in record.get("candidates", []):
            if candidate.get("status") not in {"resolved_candidate", "ambiguous", "unresolved"}:
                report.add("INVALID_FIELD", "error", "Unknown candidate resolution status.", path, source)
            for target in candidate.get("candidateAssetIds", []):
                if target not in asset_ids:
                    report.add("INVALID_FIELD", "error", "Candidate target asset is absent from manifest.", path, source)
            evidence_path = candidate.get("evidence", {}).get("path")
            if safe_relative(evidence_path, report, path, source) and not (ROOT / evidence_path).is_file():
                report.add("ENTRY_MISSING", "error", "Candidate evidence file does not exist.", ROOT / evidence_path, source)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--legacy-entry-severity", choices=("warning", "error"), default="error")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = Reporter()
    validate_legacy(report, args.legacy_entry_severity)
    validate_registry(report)
    validate_dependency_candidates(report)
    errors = [x for x in report.items if x["severity"] == "error"]
    output = {"ok": not errors, "errors": len(errors), "warnings": len(report.items) - len(errors), "diagnostics": report.items}
    if args.json: print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        for item in report.items: print(f"{item['severity'].upper()} {item['code']} {item['assetId'] or '-'}: {item['message']}")
        print(f"Validation {'passed' if not errors else 'failed'}: {len(errors)} error(s), {output['warnings']} warning(s).")
    return 0 if not errors else 1

if __name__ == "__main__": sys.exit(main())
