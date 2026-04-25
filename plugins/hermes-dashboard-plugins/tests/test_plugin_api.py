from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plugin_api", ROOT / "dashboard" / "plugin_api.py")
plugin_api = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(plugin_api)


def write_plugin(root: Path, manifest: dict) -> None:
    dashboard = root / "dashboard"
    (dashboard / "dist").mkdir(parents=True)
    (dashboard / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (dashboard / "dist" / "index.js").write_text("(function(){})();", encoding="utf-8")
    (dashboard / "dist" / "style.css").write_text(".x{}", encoding="utf-8")
    (dashboard / "plugin_api.py").write_text("from fastapi import APIRouter\nrouter = APIRouter()\n", encoding="utf-8")


def test_current_plugin_validates_cleanly():
    result = plugin_api.validate_plugin(ROOT)

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["warnings"] == []
    assert result["trust"]["status"] == "locally_validated"
    assert result["summary"]["has_backend_api"] is True


def test_missing_manifest_is_blocking_error(tmp_path):
    result = plugin_api.validate_plugin(tmp_path)

    assert result["ok"] is False
    assert result["errors"] == ["Missing dashboard/manifest.json"]
    assert result["trust"]["status"] == "unsigned"


def test_user_plugin_path_is_display_safe(tmp_path):
    plugin_root = tmp_path / ".hermes" / "plugins" / "demo-plugin"
    write_plugin(
        plugin_root,
        {
            "name": "demo-plugin",
            "label": "Demo Plugin",
            "description": "A demo",
            "icon": "Package",
            "version": "0.1.0",
            "tab": {"path": "/demo-plugin"},
            "entry": "dist/index.js",
        },
    )

    result = plugin_api.validate_plugin(plugin_root, "user")

    assert result["path"] == "~/.hermes/plugins/demo-plugin"
    assert str(tmp_path) not in result["path"]


def test_rejects_declared_files_outside_dashboard(tmp_path):
    write_plugin(
        tmp_path,
        {
            "name": "bad-plugin",
            "label": "Bad Plugin",
            "description": "Bad file reference",
            "icon": "Package",
            "version": "0.1.0",
            "tab": {"path": "/bad-plugin"},
            "entry": "../outside.js",
        },
    )

    result = plugin_api.validate_plugin(tmp_path)

    assert result["ok"] is False
    assert "Entry bundle must stay inside dashboard/: ../outside.js" in result["errors"]


def test_warns_for_publish_readiness_assets(tmp_path):
    write_plugin(
        tmp_path,
        {
            "name": "demo-plugin",
            "label": "Demo Plugin",
            "description": "A demo",
            "icon": "Package",
            "version": "0.1.0",
            "tab": {"path": "/demo-plugin"},
            "entry": "dist/index.js",
        },
    )

    result = plugin_api.validate_plugin(tmp_path)

    assert result["ok"] is True
    assert "Missing README.md at plugin root" in result["warnings"]
    assert "Missing LICENSE at plugin root" in result["warnings"]
    assert "Missing screenshots or video assets" in result["warnings"]


def test_classifies_bundled_plugins_as_upstream(tmp_path):
    result = plugin_api._plugin_origin("bundled", tmp_path, {}, {})

    assert result["type"] == "upstream"
    assert result["label"] == "Upstream"


def test_classifies_user_plugins_as_user_by_default(tmp_path):
    result = plugin_api._plugin_origin("user", tmp_path, {}, {})

    assert result["type"] == "user"
    assert result["label"] == "User"
    assert result["path"] == f"~/.hermes/plugins/{tmp_path.name}"


def test_classifies_explicit_third_party_metadata(tmp_path):
    result = plugin_api._plugin_origin(
        "user",
        tmp_path,
        {"metadata": {"hermes": {"origin": "third_party"}}},
        {},
    )

    assert result["type"] == "third_party"
    assert result["label"] == "Third Party"


def test_frontend_ownership_status_is_exposed():
    result = plugin_api.frontend_ownership_status()

    assert "ok" in result
    assert "errors" in result
    assert "plugins" in result
