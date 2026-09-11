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
SEARCH_INDEX_URL = "https://raw.githubusercontent.com/HuabSmart-cn/skills/main/registry/search-index.json"
SEARCH_INDEX_PAGE_URL = "https://github.com/HuabSmart-cn/skills/blob/main/registry/search-index.json"


def label(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("zh") or value.get("en") or ""
    return ""


def format_size(value):
    if not isinstance(value, int) or value < 0:
        return "大小未索引"
    if value < 1024:
        return f"{value} B"
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    return f"{value / (1024 * 1024):.1f} MB"


def build_readme(asset, meta, sidecar):
    name = label(asset.get("displayName")) or asset["id"]
    files = meta.get("attachments", [])
    lines = [
        f"# {name}",
        "",
        "## 技能档案",
        f"- **唯一资产 ID**: `{asset['id']}`",
        f"- **主入口文件**: `{meta['primaryFile']}`",
        f"- **条目类型**: {asset.get('sourceKind', 'unknown')}",
        f"- **来源平台**: {label(asset.get('platformName')) or asset.get('platformId', 'unknown')}",
        "",
        "## 文件清单",
        f"- `{meta['primaryFile']}`（主提示词 / 规则配置）",
        "- `HBS_BUNDLE.json`（机器可读下载包描述；不代表已安装或已验证）",
        "- `README_HUABSMART.md`（本说明文件）",
    ]
    for item in files:
        path = item.get("path") if isinstance(item, dict) else item
        size = item.get("size") if isinstance(item, dict) else None
        if isinstance(path, str):
            lines.append(f"- `{path}`（{format_size(size)}）")
    lines.extend([
        "",
        "## 协同 Skill 在线检索",
        f"- **官方机器目录**: {SEARCH_INDEX_URL}",
        f"- **GitHub 浏览目录**: {SEARCH_INDEX_PAGE_URL}",
        "当当前 Skill 的正文要求、建议或需要调用其他 Skill 时，只从上述 HuabSmart 官方目录搜索名称、别名或唯一 assetId。结合简介、标签、平台、类型和源路径比较候选；名称重复或不确定时必须展示差异并等待用户选择。只有用户明确说“一起安装”后，才可按当前 Runtime 的官方方式继续下载和安装。找不到时必须报告 dependency_missing，不能模拟调用、安装或执行结果。",
        "",
        "## 使用边界",
        "先读取 HBS_BUNDLE.json 和本说明。下载包生成不证明 Runtime 已安装、发现、加载或实际调用；执行脚本前应审阅权限、环境变量和外部服务要求。",
        "",
        "## 更新",
        "- 仓库: https://github.com/HuabSmart-cn/skills",
        "- 更新记录: https://github.com/HuabSmart-cn/skills/commits/main",
    ])
    return "\n".join(lines) + "\n"


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
            "searchIndexUrl": SEARCH_INDEX_URL,
            "searchIndexPageUrl": SEARCH_INDEX_PAGE_URL,
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
        (staging / "README_HUABSMART.md").write_text(build_readme(asset, meta, sidecar), encoding="utf-8")
        archive_base = output.with_suffix("")
        made = Path(shutil.make_archive(str(archive_base), "zip", root_dir=Path(temp), base_dir=source.name))
        if made != output: made.replace(output)
    print(output)


if __name__ == "__main__": main()
