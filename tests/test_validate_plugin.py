from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_plugin.py"


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def make_base_plugin(root: Path, name: str = "demo-plugin") -> Path:
    plugin = root / name
    plugin.mkdir()
    (plugin / "README.md").write_text("# Demo Plugin\n", encoding="utf-8")
    (plugin / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (plugin / "plugin.yaml").write_text(
        f"name: {name}\nversion: 0.1.0\ndescription: Demo plugin.\norigin: user\nkind: standalone\n",
        encoding="utf-8",
    )
    return plugin


class ValidatePluginTests(unittest.TestCase):
    def test_accepts_minimal_dashboard_example(self) -> None:
        result = run_validator(ROOT / "examples" / "minimal-dashboard-plugin")

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("ok: examples/minimal-dashboard-plugin", result.stdout)

    def test_rejects_missing_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = Path(tmp) / "missing-docs"
            plugin.mkdir()
            (plugin / "plugin.yaml").write_text("name: missing-docs\nversion: 0.1.0\n", encoding="utf-8")

            result = run_validator(plugin)

        self.assertEqual(result.returncode, 1)
        self.assertIn("Missing README.md", result.stdout)
        self.assertIn("Missing LICENSE", result.stdout)

    def test_rejects_dashboard_manifest_that_escapes_dashboard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = make_base_plugin(Path(tmp), "bad-dashboard")
            dashboard = plugin / "dashboard"
            dashboard.mkdir()
            (dashboard / "manifest.json").write_text(
                json.dumps(
                    {
                        "name": "bad-dashboard",
                        "label": "Bad Dashboard",
                        "description": "Bad dashboard.",
                        "icon": "Package",
                        "version": "0.1.0",
                        "tab": {"path": "/bad-dashboard"},
                        "entry": "../outside.js",
                    }
                ),
                encoding="utf-8",
            )

            result = run_validator(plugin)

        self.assertEqual(result.returncode, 1)
        self.assertIn("Entry bundle must stay inside dashboard/", result.stdout)

    def test_rejects_personal_user_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plugin = make_base_plugin(Path(tmp), "leaky-plugin")
            (plugin / "README.md").write_text(
                "Screenshot from /Users/example/.hermes/plugins/leaky-plugin\n",
                encoding="utf-8",
            )

            result = run_validator(plugin)

        self.assertEqual(result.returncode, 1)
        self.assertIn("Personal local path leak", result.stdout)


if __name__ == "__main__":
    unittest.main()
