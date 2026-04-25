from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel
import yaml

router = APIRouter()

THEME_SUFFIXES = {".yaml", ".yml"}


class ThemeActionRequest(BaseModel):
    name: str


class InstallThemeRequest(BaseModel):
    plugin: str
    theme: str


def _hermes_home() -> Path:
    try:
        from hermes_constants import get_hermes_home

        return get_hermes_home()
    except Exception:
        return Path("~/.hermes").expanduser()


def _display_plugin_path(plugin_root: Path, source: str) -> str:
    if source == "user":
        return f"~/.hermes/plugins/{plugin_root.name}"
    if source == "bundled":
        return f"plugins/{plugin_root.name}"
    return plugin_root.name


def _scan_roots() -> tuple[tuple[str, Path], ...]:
    return (
        ("user", _hermes_home() / "plugins"),
        ("bundled", Path.cwd() / "plugins"),
    )


def _safe_yaml(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        return None, f"Invalid YAML: {exc}"
    except OSError as exc:
        return None, f"Cannot read file: {exc}"

    if not isinstance(parsed, dict):
        return None, "Theme YAML must be an object"
    return parsed, None


def _theme_files(root: Path) -> list[Path]:
    theme_dir = root / "theme"
    if not theme_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in theme_dir.iterdir()
            if path.is_file() and path.suffix.lower() in THEME_SUFFIXES
        ),
        key=lambda path: path.name.lower(),
    )


def _installed_theme_files() -> list[Path]:
    themes_dir = _hermes_home() / "dashboard-themes"
    if not themes_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in themes_dir.iterdir()
            if path.is_file() and path.suffix.lower() in THEME_SUFFIXES
        ),
        key=lambda path: path.name.lower(),
    )


def _theme_summary(path: Path, *, source: str, plugin_root: Path | None = None) -> dict[str, Any]:
    data, error = _safe_yaml(path)
    data = data or {}
    name = str(data.get("name") or path.stem)
    return {
        "name": name,
        "label": str(data.get("label") or name.replace("-", " ").title()),
        "description": str(data.get("description") or ""),
        "file": path.name,
        "source": source,
        "plugin": plugin_root.name if plugin_root else "",
        "plugin_path": _display_plugin_path(plugin_root, source) if plugin_root else "<HERMES_HOME>/dashboard-themes",
        "installed": source == "installed" or (_hermes_home() / "dashboard-themes" / f"{name}.yaml").exists(),
        "layout_variant": str(data.get("layoutVariant") or "standard"),
        "has_custom_css": bool(data.get("customCSS")),
        "errors": [error] if error else [],
    }


def discover_theme_plugins() -> list[dict[str, Any]]:
    plugins: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for source, scan_root in _scan_roots():
        if not scan_root.is_dir():
            continue
        for child in sorted(scan_root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir():
                continue
            resolved = child.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            themes = [_theme_summary(path, source=source, plugin_root=resolved) for path in _theme_files(resolved)]
            if not themes:
                continue
            plugins.append(
                {
                    "name": child.name,
                    "source": source,
                    "path": _display_plugin_path(resolved, source),
                    "themes": themes,
                }
            )
    return plugins


def theme_inventory() -> dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        config = load_config()
    except Exception:
        config = {}
    active = "default"
    dashboard_cfg = config.get("dashboard", {}) if isinstance(config, dict) else {}
    if isinstance(dashboard_cfg, dict) and isinstance(dashboard_cfg.get("theme"), str):
        active = dashboard_cfg["theme"]

    installed = [_theme_summary(path, source="installed") for path in _installed_theme_files()]
    theme_plugins = discover_theme_plugins()
    return {
        "active": active,
        "installed": installed,
        "theme_plugins": theme_plugins,
        "themes_dir": "<HERMES_HOME>/dashboard-themes",
    }


def install_theme(plugin_name: str, theme_name: str) -> dict[str, Any]:
    if not plugin_name or "/" in plugin_name or ".." in plugin_name:
        return {"ok": False, "error": "Invalid plugin name"}
    if not theme_name or "/" in theme_name or ".." in theme_name:
        return {"ok": False, "error": "Invalid theme name"}

    for _, scan_root in _scan_roots():
        plugin_root = scan_root / plugin_name
        if not plugin_root.is_dir():
            continue
        for theme_file in _theme_files(plugin_root):
            data, error = _safe_yaml(theme_file)
            if error:
                return {"ok": False, "error": error}
            candidate_name = str((data or {}).get("name") or theme_file.stem)
            if candidate_name != theme_name:
                continue
            themes_dir = _hermes_home() / "dashboard-themes"
            themes_dir.mkdir(parents=True, exist_ok=True)
            destination = themes_dir / f"{candidate_name}.yaml"
            shutil.copyfile(theme_file, destination)
            return {
                "ok": True,
                "theme": candidate_name,
                "installed_to": "<HERMES_HOME>/dashboard-themes/" + destination.name,
            }
    return {"ok": False, "error": "Theme not found in discovered theme plugins"}


def activate_theme(theme_name: str) -> dict[str, Any]:
    if not theme_name or "/" in theme_name or ".." in theme_name:
        return {"ok": False, "error": "Invalid theme name"}
    try:
        from hermes_cli.config import load_config, save_config

        config = load_config()
        dashboard_cfg = config.setdefault("dashboard", {})
        if not isinstance(dashboard_cfg, dict):
            dashboard_cfg = {}
            config["dashboard"] = dashboard_cfg
        dashboard_cfg["theme"] = theme_name
        save_config(config)
    except Exception as exc:
        return {"ok": False, "error": f"Unable to save dashboard theme: {exc}"}
    return {"ok": True, "theme": theme_name}


@router.get("/themes")
async def themes() -> dict[str, Any]:
    return theme_inventory()


@router.post("/install")
async def install(body: InstallThemeRequest) -> dict[str, Any]:
    return install_theme(body.plugin, body.theme)


@router.put("/activate")
async def activate(body: ThemeActionRequest) -> dict[str, Any]:
    return activate_theme(body.name)
