from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "enforce_frontend_ownership",
    ROOT / "scripts" / "enforce_frontend_ownership.py",
)
enforcer = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(enforcer)


def write_dashboard_plugin(root: Path, name: str = "demo-plugin") -> None:
    dashboard = root / "dashboard"
    (dashboard / "dist").mkdir(parents=True)
    (dashboard / "manifest.json").write_text(
        json.dumps(
            {
                "name": name,
                "label": "Demo Plugin",
                "description": "Demo dashboard plugin",
                "icon": "Package",
                "version": "0.1.0",
                "tab": {"path": f"/{name}"},
                "entry": "dist/index.js",
                "css": "dist/style.css",
                "api": "plugin_api.py",
            }
        ),
        encoding="utf-8",
    )
    (dashboard / "dist" / "index.js").write_text("window.demo = true;", encoding="utf-8")
    (dashboard / "dist" / "style.css").write_text(".demo{}", encoding="utf-8")
    (dashboard / "plugin_api.py").write_text("from fastapi import APIRouter\nrouter = APIRouter()\n", encoding="utf-8")


def test_clean_plugin_owns_declared_dashboard_files(tmp_path):
    plugin = tmp_path / "plugins" / "demo-plugin"
    write_dashboard_plugin(plugin)

    result = enforcer.run_checks(
        plugin_roots=[tmp_path / "plugins"],
        core_roots=[tmp_path / "web"],
    )

    assert result.ok is True
    assert result.errors == []


def test_rejects_dashboard_entry_outside_plugin_dashboard(tmp_path):
    plugin = tmp_path / "plugins" / "bad-plugin"
    write_dashboard_plugin(plugin, "bad-plugin")
    manifest = json.loads((plugin / "dashboard" / "manifest.json").read_text(encoding="utf-8"))
    manifest["entry"] = "../leaked.js"
    (plugin / "dashboard" / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    result = enforcer.run_checks(
        plugin_roots=[tmp_path / "plugins"],
        core_roots=[tmp_path / "web"],
    )

    assert result.ok is False
    assert any("bad-plugin declares entry outside its dashboard folder" in error for error in result.errors)


def test_rejects_plugin_specific_core_dashboard_route(tmp_path):
    plugin = tmp_path / "plugins" / "demo-plugin"
    write_dashboard_plugin(plugin)
    core_page = tmp_path / "web" / "src" / "App.tsx"
    core_page.parent.mkdir(parents=True)
    core_page.write_text('const route = "/demo-plugin";', encoding="utf-8")

    result = enforcer.run_checks(
        plugin_roots=[tmp_path / "plugins"],
        core_roots=[tmp_path / "web"],
    )

    assert result.ok is False
    assert any("core dashboard file contains plugin-owned route /demo-plugin" in error for error in result.errors)
