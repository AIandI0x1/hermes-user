#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Iterable


DASHBOARD_DECLARED_FILES = ("entry", "css", "api")
SCANNED_CORE_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".jsx",
    ".json",
    ".mjs",
    ".py",
    ".ts",
    ".tsx",
}
IGNORED_DIRS = {
    ".git",
    ".next",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}


class CheckResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.plugins: list[dict[str, str]] = []

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": self.errors,
            "warnings": self.warnings,
            "plugins": self.plugins,
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _hermes_home() -> Path:
    configured = os.environ.get("HERMES_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".hermes"


def _default_plugin_roots() -> list[Path]:
    return [
        _hermes_home() / "plugins",
        _repo_root() / "plugins",
    ]


def _default_core_roots() -> list[Path]:
    root = _repo_root()
    return [
        root / "web" / "src",
        root / "web" / "public",
        root / "hermes_cli",
    ]


def _load_manifest(path: Path, result: CheckResult) -> dict[str, Any] | None:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.errors.append(f"{path}: invalid dashboard manifest JSON: {exc.msg}")
        return None
    except OSError as exc:
        result.errors.append(f"{path}: cannot read dashboard manifest: {exc}")
        return None

    if not isinstance(parsed, dict):
        result.errors.append(f"{path}: dashboard manifest must be a JSON object")
        return None
    return parsed


def _is_inside(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _iter_dashboard_plugins(plugin_roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for plugin_root in plugin_roots:
        root = plugin_root.expanduser()
        if not root.exists() or not root.is_dir():
            continue
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if not child.is_dir() or not (child / "dashboard" / "manifest.json").exists():
                continue
            resolved = child.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield resolved


def _iter_core_files(core_roots: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for core_root in core_roots:
        root = core_root.expanduser()
        if not root.exists():
            continue
        if root.is_file():
            files = [root]
        else:
            files = (
                path
                for path in root.rglob("*")
                if path.is_file() and not any(part in IGNORED_DIRS for part in path.parts)
            )
        for path in files:
            if path.suffix.lower() not in SCANNED_CORE_SUFFIXES:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield resolved


def _check_declared_dashboard_files(plugin: Path, manifest: dict[str, Any], result: CheckResult) -> None:
    dashboard = plugin / "dashboard"
    name = str(manifest.get("name") or plugin.name)
    for key in DASHBOARD_DECLARED_FILES:
        value = manifest.get(key)
        if not value:
            continue
        relative = Path(str(value))
        if relative.is_absolute():
            result.errors.append(f"{name} declares absolute dashboard {key}: {value}")
            continue
        target = dashboard / relative
        if not _is_inside(target, dashboard):
            result.errors.append(f"{name} declares {key} outside its dashboard folder: {value}")
            continue
        if not target.exists():
            result.errors.append(f"{name} declares missing dashboard {key}: {value}")
        elif not target.is_file():
            result.errors.append(f"{name} declares dashboard {key} as a non-file path: {value}")


def _route_from_manifest(manifest: dict[str, Any]) -> str:
    tab = manifest.get("tab")
    if not isinstance(tab, dict):
        return ""
    route = tab.get("path")
    if not isinstance(route, str):
        return ""
    return route if route.startswith("/") else ""


def _check_core_leaks(plugins: list[dict[str, str]], core_roots: Iterable[Path], result: CheckResult) -> None:
    routes = {
        plugin["route"]: plugin["name"]
        for plugin in plugins
        if plugin.get("route")
    }
    if not routes:
        return

    for path in _iter_core_files(core_roots):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            result.warnings.append(f"{path}: skipped core scan: {exc}")
            continue
        for route, name in routes.items():
            quoted = (f'"{route}"', f"'{route}'", f"`{route}`")
            if any(token in text for token in quoted):
                result.errors.append(
                    f"{path}: core dashboard file contains plugin-owned route {route} for {name}"
                )


def run_checks(
    plugin_roots: Iterable[Path] | None = None,
    core_roots: Iterable[Path] | None = None,
) -> CheckResult:
    result = CheckResult()
    plugin_roots = list(plugin_roots or _default_plugin_roots())
    core_roots = list(core_roots or _default_core_roots())

    for plugin in _iter_dashboard_plugins(plugin_roots):
        manifest = _load_manifest(plugin / "dashboard" / "manifest.json", result)
        if manifest is None:
            continue
        name = str(manifest.get("name") or plugin.name)
        route = _route_from_manifest(manifest)
        result.plugins.append(
            {
                "name": name,
                "route": route,
                "path": str(plugin),
            }
        )
        _check_declared_dashboard_files(plugin, manifest, result)

    _check_core_leaks(result.plugins, core_roots, result)
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enforce that Hermes dashboard frontend changes stay inside each plugin folder."
    )
    parser.add_argument(
        "--plugin-root",
        action="append",
        dest="plugin_roots",
        help="Directory containing plugin folders. Can be passed more than once.",
    )
    parser.add_argument(
        "--core-root",
        action="append",
        dest="core_roots",
        help="Core dashboard/source directory to scan for plugin-owned routes. Can be passed more than once.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    plugin_roots = [Path(path) for path in args.plugin_roots] if args.plugin_roots else None
    core_roots = [Path(path) for path in args.core_roots] if args.core_roots else None
    result = run_checks(plugin_roots=plugin_roots, core_roots=core_roots)

    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"frontend ownership rule: {status}")
        print(f"dashboard plugins checked: {len(result.plugins)}")
        for error in result.errors:
            print(f"ERROR: {error}")
        for warning in result.warnings:
            print(f"WARNING: {warning}")

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
