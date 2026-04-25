from __future__ import annotations

import json
import importlib.util
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
import yaml

router = APIRouter()

PLUGIN_NAME_RE = re.compile(r"^[a-z0-9-]+$")
MANAGER_PLUGIN_NAME = "hermes-dashboard-plugins"
DEFAULT_SCAN_ROOTS: tuple[tuple[str, Path], ...] = (
    ("user", Path("~/.hermes/plugins")),
    ("bundled", Path.cwd() / "plugins"),
)
SCREENSHOT_SUFFIXES = {".gif", ".jpeg", ".jpg", ".mov", ".mp4", ".png", ".webm"}
THEME_SUFFIXES = {".yaml", ".yml"}
ORIGIN_LABELS = {
    "upstream": "Upstream",
    "user": "User",
    "third_party": "Third Party",
}


class ValidateRequest(BaseModel):
    path: str


class ToggleRequest(BaseModel):
    name: str
    enabled: bool


def _check_file(root: Path, relative: str, errors: list[str], label: str) -> None:
    if Path(relative).is_absolute():
        errors.append(f"{label} must be a relative path: {relative}")
        return

    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        errors.append(f"{label} must stay inside dashboard/: {relative}")
        return

    if not target.exists():
        errors.append(f"{label} is declared but missing: {relative}")
    elif not target.is_file():
        errors.append(f"{label} points to a non-file path: {relative}")


def _safe_manifest(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"Invalid manifest JSON: {exc.msg}"
    except OSError as exc:
        return None, f"Cannot read manifest: {exc}"

    if not isinstance(parsed, dict):
        return None, "Manifest must be a JSON object"
    return parsed, None


def _safe_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return None, f"Invalid plugin YAML: {exc}"
    except OSError as exc:
        return None, f"Cannot read plugin YAML: {exc}"

    if not isinstance(parsed, dict):
        return None, "Plugin YAML must be an object"
    return parsed, None


def _metadata_origin(plugin_cfg: dict[str, Any], manifest: dict[str, Any]) -> str | None:
    candidates: list[Any] = [
        plugin_cfg.get("origin"),
        plugin_cfg.get("distribution"),
        manifest.get("origin"),
    ]
    for source in (plugin_cfg, manifest):
        metadata = source.get("metadata")
        if isinstance(metadata, dict):
            hermes = metadata.get("hermes")
            if isinstance(hermes, dict):
                candidates.append(hermes.get("origin"))
                candidates.append(hermes.get("distribution"))

    for value in candidates:
        normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
        if normalized in {"upstream", "official", "bundled", "core"}:
            return "upstream"
        if normalized in {"user", "local", "first_party", "firstparty"}:
            return "user"
        if normalized in {"third_party", "thirdparty", "community", "external"}:
            return "third_party"
    return None


def _plugin_origin(source: str, root: Path, plugin_cfg: dict[str, Any], manifest: dict[str, Any]) -> dict[str, str]:
    explicit = _metadata_origin(plugin_cfg, manifest)
    if explicit:
        origin_type = explicit
    elif source == "bundled":
        origin_type = "upstream"
    elif source == "user":
        origin_type = "user"
    else:
        origin_type = "third_party"

    details = {
        "upstream": "Bundled with the Hermes Agent checkout.",
        "user": "Installed in the active Hermes user plugin folder.",
        "third_party": "Installed locally but marked as an external/community plugin.",
    }
    return {
        "type": origin_type,
        "label": ORIGIN_LABELS[origin_type],
        "source": source,
        "detail": details[origin_type],
        "path": _display_path(root, source),
    }


def _display_path(root: Path, source: str) -> str:
    if source == "user":
        return f"~/.hermes/plugins/{root.name}"
    if source == "bundled":
        return f"plugins/{root.name}"
    return root.name


def _has_screenshot_assets(root: Path) -> bool:
    screenshots_dir = root / "screenshots"
    if not screenshots_dir.exists() or not screenshots_dir.is_dir():
        return False

    return any(
        path.is_file() and path.suffix.lower() in SCREENSHOT_SUFFIXES
        for path in screenshots_dir.iterdir()
    )


def _theme_files(root: Path) -> list[Path]:
    themes_dir = root / "theme"
    if not themes_dir.exists() or not themes_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in themes_dir.iterdir()
            if path.is_file() and path.suffix.lower() in THEME_SUFFIXES
        ),
        key=lambda path: path.name.lower(),
    )


def _theme_names(root: Path) -> list[str]:
    names: list[str] = []
    for theme_file in _theme_files(root):
        theme_data, _ = _safe_yaml(theme_file)
        raw_name = theme_data.get("name") if isinstance(theme_data, dict) else None
        names.append(str(raw_name or theme_file.stem))
    return names


def _trust_for(errors: list[str], manifest: dict[str, Any] | None) -> dict[str, str]:
    signature = None
    if isinstance(manifest, dict):
        signature = manifest.get("signature") or manifest.get("certification")

    if signature:
        status = "unsigned"
        detail = "Signature metadata found, but no official Hermes registry or public key is configured."
    elif errors:
        status = "unsigned"
        detail = "Package has validation errors and no official signature metadata."
    else:
        status = "locally_validated"
        detail = "Local structure checks passed. This is not official Hermes certification."

    return {
        "status": status,
        "official_verification": "unavailable",
        "detail": detail,
    }


def _plugin_config_state() -> dict[str, set[str]]:
    try:
        from hermes_cli.config import load_config
        config = load_config()
    except Exception:
        config = {}

    plugins_cfg = config.get("plugins", {}) if isinstance(config, dict) else {}
    if not isinstance(plugins_cfg, dict):
        plugins_cfg = {}

    enabled = plugins_cfg.get("enabled", [])
    disabled = plugins_cfg.get("disabled", [])
    return {
        "enabled": set(enabled) if isinstance(enabled, list) else set(),
        "disabled": set(disabled) if isinstance(disabled, list) else set(),
    }


def _scan_roots() -> tuple[tuple[str, Path], ...]:
    try:
        from hermes_constants import get_hermes_home

        hermes_home = get_hermes_home()
    except Exception:
        hermes_home = Path("~/.hermes").expanduser()

    return (
        ("user", hermes_home / "plugins"),
        ("bundled", Path.cwd() / "plugins"),
    )


def _set_plugin_enabled(name: str, enabled: bool) -> dict[str, Any]:
    if not PLUGIN_NAME_RE.match(name):
        return {"ok": False, "error": "Invalid plugin name"}
    if name == MANAGER_PLUGIN_NAME and not enabled:
        return {"ok": False, "error": "The dashboard plugin manager cannot disable itself"}

    from hermes_cli.config import load_config, save_config

    config = load_config()
    plugins_cfg = config.setdefault("plugins", {})
    if not isinstance(plugins_cfg, dict):
        plugins_cfg = {}
        config["plugins"] = plugins_cfg

    enabled_set = set(plugins_cfg.get("enabled", []) or [])
    disabled_set = set(plugins_cfg.get("disabled", []) or [])

    if enabled:
        enabled_set.add(name)
        disabled_set.discard(name)
    else:
        enabled_set.discard(name)
        disabled_set.add(name)

    plugins_cfg["enabled"] = sorted(enabled_set)
    plugins_cfg["disabled"] = sorted(disabled_set)
    save_config(config)

    return {"ok": True, "name": name, "enabled": enabled}


def validate_plugin(root: Path, source: str = "unknown") -> dict[str, Any]:
    root = root.expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    dashboard_dir = root / "dashboard"
    manifest_path = dashboard_dir / "manifest.json"

    if not manifest_path.exists():
        return {
            "path": _display_path(root, source),
            "source": source,
            "ok": False,
            "errors": ["Missing dashboard/manifest.json"],
            "warnings": warnings,
            "manifest": None,
            "trust": _trust_for(["Missing dashboard/manifest.json"], None),
        }

    manifest, manifest_error = _safe_manifest(manifest_path)
    if manifest_error:
        return {
            "path": _display_path(root, source),
            "source": source,
            "ok": False,
            "errors": [manifest_error],
            "warnings": warnings,
            "manifest": None,
            "trust": _trust_for([manifest_error], None),
        }

    assert manifest is not None

    for key in ("name", "label", "entry"):
        if not manifest.get(key):
            errors.append(f"Missing manifest.{key}")

    tab = manifest.get("tab")
    if not isinstance(tab, dict):
        errors.append("Missing manifest.tab object")
    elif not tab.get("path"):
        errors.append("Missing manifest.tab.path")
    elif not str(tab["path"]).startswith("/"):
        errors.append("manifest.tab.path must start with /")

    name = str(manifest.get("name", ""))
    if name and not PLUGIN_NAME_RE.match(name):
        warnings.append("manifest.name should use lowercase letters, numbers, and hyphen only")

    if not manifest.get("description"):
        warnings.append("Missing manifest.description")
    if not manifest.get("version"):
        warnings.append("Missing manifest.version")
    if not manifest.get("icon"):
        warnings.append("Missing manifest.icon")

    entry = manifest.get("entry")
    if entry:
        _check_file(dashboard_dir, str(entry), errors, "Entry bundle")
        if not str(entry).endswith(".js"):
            warnings.append("manifest.entry should point to a JavaScript bundle")
    if manifest.get("css"):
        _check_file(dashboard_dir, str(manifest["css"]), errors, "CSS file")
        if not str(manifest["css"]).endswith(".css"):
            warnings.append("manifest.css should point to a CSS file")
    if manifest.get("api"):
        _check_file(dashboard_dir, str(manifest["api"]), errors, "API file")
        if not str(manifest["api"]).endswith(".py"):
            warnings.append("manifest.api should point to a Python file")

    if not (root / "README.md").exists():
        warnings.append("Missing README.md at plugin root")
    if not (root / "LICENSE").exists():
        warnings.append("Missing LICENSE at plugin root")
    if not _has_screenshot_assets(root):
        warnings.append("Missing screenshots or video assets")

    return {
        "path": _display_path(root, source),
        "source": source,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "has_readme": (root / "README.md").exists(),
            "has_license": (root / "LICENSE").exists(),
            "has_media": _has_screenshot_assets(root),
            "has_backend_api": bool(manifest.get("api")),
            "has_css": bool(manifest.get("css")),
            "tab_path": str(tab.get("path", "")) if isinstance(tab, dict) else "",
        },
        "manifest": manifest,
        "trust": _trust_for(errors, manifest),
    }


def _candidate_roots() -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    seen: set[Path] = set()

    for source, scan_root in _scan_roots():
        root = scan_root.expanduser()
        if not root.exists() or not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir() or not (child / "dashboard").exists():
                continue
            resolved = child.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append((source, resolved))

    def sort_key(item: tuple[str, Path]) -> tuple[int, str]:
        source, path = item
        if path.name == "hermes-hackathon-hub":
            return (0, path.name.lower())
        if source == "user":
            return (1, path.name.lower())
        return (2, path.name.lower())

    return sorted(candidates, key=sort_key)


def _all_user_plugin_roots() -> list[tuple[str, Path]]:
    roots: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for source, scan_root in _scan_roots():
        root = scan_root.expanduser()
        if not root.exists() or not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda p: p.name.lower()):
            if not child.is_dir():
                continue
            if not (child / "plugin.yaml").exists() and not (child / "dashboard" / "manifest.json").exists():
                continue
            resolved = child.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            roots.append((source, resolved))
    return roots


def _catalog_plugin(source: str, root: Path, state: dict[str, set[str]]) -> dict[str, Any] | None:
    dashboard_manifest, dashboard_error = _safe_manifest(root / "dashboard" / "manifest.json") if (root / "dashboard" / "manifest.json").exists() else (None, None)
    plugin_yaml, plugin_error = _safe_yaml(root / "plugin.yaml") if (root / "plugin.yaml").exists() else (None, None)
    manifest = dashboard_manifest or {}
    plugin_cfg = plugin_yaml or {}
    theme_names = _theme_names(root)
    name = str(plugin_cfg.get("name") or manifest.get("name") or root.name)
    if not name:
        return None
    tab = manifest.get("tab") if isinstance(manifest.get("tab"), dict) else {}
    enabled = name in state["enabled"] or (name not in state["disabled"] and source == "bundled")
    if name in state["disabled"]:
        enabled = False
    return {
        "id": name,
        "name": name,
        "label": manifest.get("label") or name.replace("-", " ").title(),
        "description": plugin_cfg.get("description") or manifest.get("description") or "",
        "icon": manifest.get("icon") or "Package",
        "version": str(plugin_cfg.get("version") or manifest.get("version") or "0.0.0"),
        "source": source,
        "origin": _plugin_origin(source, root, plugin_cfg, manifest),
        "kind": plugin_cfg.get("kind") or ("theme" if theme_names and dashboard_manifest is None else "dashboard"),
        "enabled": enabled,
        "has_dashboard": dashboard_manifest is not None,
        "has_theme": bool(theme_names),
        "theme_names": theme_names,
        "has_backend_api": bool(manifest.get("api")),
        "provides_tools": plugin_cfg.get("provides_tools") if isinstance(plugin_cfg.get("provides_tools"), list) else [],
        "provides_hooks": plugin_cfg.get("provides_hooks") if isinstance(plugin_cfg.get("provides_hooks"), list) else [],
        "route": str(tab.get("path", "")) if tab else "",
        "entry": manifest.get("entry") or "",
        "errors": [error for error in (dashboard_error, plugin_error) if error],
        "warnings": [],
        "trust": _trust_for([], manifest or plugin_cfg),
    }


def catalog_plugins() -> list[dict[str, Any]]:
    state = _plugin_config_state()
    items = [
        item for source, root in _all_user_plugin_roots()
        if (item := _catalog_plugin(source, root, state)) is not None
    ]

    def sort_key(item: dict[str, Any]) -> tuple[int, str]:
        if item["name"] == MANAGER_PLUGIN_NAME:
            return (0, item["name"])
        if item["name"] == "hermes-hackathon-hub":
            return (1, item["name"])
        if item["source"] == "user":
            return (2, item["name"])
        return (3, item["name"])

    return sorted(items, key=sort_key)


def frontend_ownership_status() -> dict[str, Any]:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "enforce_frontend_ownership.py"
    if not script_path.exists():
        return {
            "ok": False,
            "errors": [f"Missing frontend ownership rule script: {script_path}"],
            "warnings": [],
            "plugins": [],
        }

    spec = importlib.util.spec_from_file_location("hermes_dashboard_frontend_ownership", script_path)
    if spec is None or spec.loader is None:
        return {
            "ok": False,
            "errors": [f"Cannot load frontend ownership rule script: {script_path}"],
            "warnings": [],
            "plugins": [],
        }

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.run_checks()
    return result.as_dict()


@router.get("/scan")
async def scan_plugins() -> dict[str, Any]:
    return {"plugins": [validate_plugin(path, source) for source, path in _candidate_roots()]}


@router.get("/catalog")
async def plugin_catalog() -> dict[str, Any]:
    return {"plugins": catalog_plugins()}


@router.get("/rules/frontend-ownership")
async def frontend_ownership_rule() -> dict[str, Any]:
    return frontend_ownership_status()


@router.post("/validate")
async def validate(body: ValidateRequest) -> dict[str, Any]:
    return validate_plugin(Path(body.path))



@router.get("/state")
async def plugin_state() -> dict[str, Any]:
    state = _plugin_config_state()
    return {
        "enabled": sorted(state["enabled"]),
        "disabled": sorted(state["disabled"]),
    }


@router.put("/toggle")
async def toggle_plugin(body: ToggleRequest) -> dict[str, Any]:
    return _set_plugin_enabled(body.name, body.enabled)
