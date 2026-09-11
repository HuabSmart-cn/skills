import json
import subprocess
import tempfile
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class RegistryValidationTests(unittest.TestCase):
    def test_bootstrap_registry_is_structurally_valid(self):
        result = subprocess.run(
            [sys.executable, "tools/validate_registry.py", "--json"], cwd=ROOT,
            check=False, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["errors"], 0)

    def test_all_remaining_legacy_entries_are_real_files(self):
        result = subprocess.run(
            [sys.executable, "tools/validate_registry.py", "--json"], cwd=ROOT,
            check=False, text=True, capture_output=True,
        )
        report = json.loads(result.stdout)
        codes = {item["code"] for item in report["diagnostics"]}
        self.assertNotIn("LEGACY_ENTRY_MISSING", codes)

    def test_cross_skill_candidates_preserve_uncertainty(self):
        subprocess.run([sys.executable, "tools/build_dependency_candidates.py"], cwd=ROOT, check=True, capture_output=True)
        report = json.loads((ROOT / "registry/dependency-candidates.json").read_text(encoding="utf-8"))
        douyin = next(row for row in report["records"] if row["sourceAssetId"] == "DouyinStrategist")
        states = {item["mentionedAs"]: item["status"] for item in douyin["candidates"]}
        self.assertEqual(states["humanizer"], "ambiguous")
        self.assertEqual(states["anti-distill"], "unresolved")

    def test_resolver_blocks_ambiguous_and_missing_cross_skill_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "douyin.zip"
            subprocess.run([sys.executable, "tools/build_download_bundle.py", "--asset-id", "DouyinStrategist", "--output", str(bundle)], cwd=ROOT, check=True, capture_output=True)
            result = subprocess.run([sys.executable, "tools/resolve_bundle_dependencies.py", "--bundle", str(bundle), "--repository-root", str(ROOT)], cwd=ROOT, check=True, text=True, capture_output=True)
        plan = json.loads(result.stdout)
        codes = {item["code"] for item in plan["blocked"]}
        self.assertIn("DEPENDENCY_AMBIGUOUS", codes)
        self.assertIn("DEPENDENCY_MISSING", codes)
        self.assertEqual(plan["planStatus"], "blocked")
        self.assertEqual(plan["runtimeVerification"], "not_verified")

    def test_resolver_plans_a_declared_required_dependency(self):
        asset_id = "lark-skills:skill:skills__lark-calendar__SKILL.md"
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "calendar.zip"
            subprocess.run([sys.executable, "tools/build_download_bundle.py", "--asset-id", asset_id, "--output", str(bundle)], cwd=ROOT, check=True, capture_output=True)
            result = subprocess.run([sys.executable, "tools/resolve_bundle_dependencies.py", "--bundle", str(bundle), "--repository-root", str(ROOT)], cwd=ROOT, check=True, text=True, capture_output=True)
        plan = json.loads(result.stdout)
        self.assertEqual(plan["planStatus"], "ready_for_runtime_install")
        self.assertEqual(plan["runtimeVerification"], "not_verified")
        self.assertEqual(plan["actions"][0]["capabilityId"], "cap.skill.lark-skills.lark-shared.v1")

    def test_cli_bundle_includes_the_same_search_guidance_as_web_downloads(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "calendar.zip"
            subprocess.run([sys.executable, "tools/build_download_bundle.py", "--asset-id", "lark-skills:skill:skills__lark-calendar__SKILL.md", "--output", str(bundle)], cwd=ROOT, check=True, capture_output=True)
            with zipfile.ZipFile(bundle) as archive:
                readme_path = next(name for name in archive.namelist() if name.endswith("/README_HUABSMART.md"))
                readme = archive.read(readme_path).decode("utf-8")
        self.assertIn("https://raw.githubusercontent.com/HuabSmart-cn/skills/main/registry/search-index.json", readme)
        self.assertIn("只有用户明确说“一起安装”后", readme)


if __name__ == "__main__":
    unittest.main()
