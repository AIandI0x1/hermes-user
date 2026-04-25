from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("theme_hub_api", ROOT / "dashboard" / "plugin_api.py")
plugin_api = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(plugin_api)


def test_theme_summary_uses_safe_plugin_path(tmp_path):
    plugin_root = tmp_path / ".hermes" / "plugins" / "demo-theme-pack"
    theme_dir = plugin_root / "theme"
    theme_dir.mkdir(parents=True)
    theme_file = theme_dir / "demo.yaml"
    theme_file.write_text(
        "name: demo\nlabel: Demo Theme\ndescription: Test theme\nlayoutVariant: tiled\n",
        encoding="utf-8",
    )

    summary = plugin_api._theme_summary(theme_file, source="user", plugin_root=plugin_root)

    assert summary["name"] == "demo"
    assert summary["plugin_path"] == "~/.hermes/plugins/demo-theme-pack"
    assert str(tmp_path) not in summary["plugin_path"]
    assert summary["layout_variant"] == "tiled"


def test_theme_files_only_include_yaml(tmp_path):
    plugin_root = tmp_path / "theme-plugin"
    theme_dir = plugin_root / "theme"
    theme_dir.mkdir(parents=True)
    (theme_dir / "alpha.yaml").write_text("name: alpha\n", encoding="utf-8")
    (theme_dir / "beta.yml").write_text("name: beta\n", encoding="utf-8")
    (theme_dir / "notes.txt").write_text("ignore", encoding="utf-8")

    files = plugin_api._theme_files(plugin_root)

    assert [path.name for path in files] == ["alpha.yaml", "beta.yml"]


def test_rejects_unsafe_install_names():
    assert plugin_api.install_theme("../bad", "theme")["ok"] is False
    assert plugin_api.install_theme("plugin", "../bad")["ok"] is False
