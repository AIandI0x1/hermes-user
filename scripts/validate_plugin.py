#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PLUGIN_NAME_RE = re.compile(r"^[a-z0-9-]+$")
PERSONAL_PATH_RE = re.compile(r"/Users/[^\s)\]\"']+")
SECRET_PATTERNS = {
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "OpenAI key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "Private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}


@dataclass
class ValidationResult:
    root: Path
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key:
            data.setdefault(current_key, []).append(stripped[2:].strip().strip('"\''))
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value == "[]":
            data[key] = []
        elif not value:
            data[key] = []
        else:
            data[key] = value.strip('"\'')
    return data


def check_relative_file(root: Path, base: Path, relative: str, label: str, result: ValidationResult) -> None:
    if Path(relative).is_absolute():
        result.error(f"{label} must be a relative path: {relative}")
        return
    target = (base / relative).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        result.error(f"{label} must stay inside dashboard/: {relative}")
        return
    if not target.exists():
        result.error(f"{label} is declared but missing: {relative}")
    elif not target.is_file():
        result.error(f"{label} points to a non-file path: {relative}")


def validate_dashboard(root: Path, result: ValidationResult) -> None:
    dashboard = root / "dashboard"
    manifest_path = dashboard / "manifest.json"
    if not dashboard.exists():
        return
    if not manifest_path.exists():
        result.error("Missing dashboard/manifest.json")
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        result.error(f"Invalid dashboard/manifest.json: {exc.msg}")
        return
    if not isinstance(manifest, dict):
        result.error("dashboard/manifest.json must be a JSON object")
        return
    for key in ("name", "label", "description", "icon", "version", "entry"):
        if not manifest.get(key):
            result.error(f"Missing manifest.{key}")
    if manifest.get("name") and manifest["name"] != root.name:
        result.error(f"manifest.name must match plugin folder name: {root.name}")
    tab = manifest.get("tab")
    if not isinstance(tab, dict) or not tab.get("path"):
        result.error("Missing manifest.tab.path")
    elif not str(tab["path"]).startswith("/"):
        result.error("manifest.tab.path must start with /")
    if manifest.get("entry"):
        check_relative_file(root, dashboard, str(manifest["entry"]), "Entry bundle", result)
    if manifest.get("css"):
        check_relative_file(root, dashboard, str(manifest["css"]), "CSS file", result)
    if manifest.get("api"):
        check_relative_file(root, dashboard, str(manifest["api"]), "API file", result)


def validate_theme(root: Path, result: ValidationResult) -> None:
    theme_dir = root / "theme"
    if not theme_dir.exists():
        return
    theme_files = sorted([p for p in theme_dir.iterdir() if p.suffix.lower() in {".yaml", ".yml"}])
    if not theme_files:
        result.error("theme/ exists but contains no .yaml or .yml theme files")
    for theme_file in theme_files:
        data = parse_simple_yaml(theme_file)
        if not data.get("name"):
            result.error(f"Missing theme name in {theme_file.relative_to(root)}")


def scan_text_files(root: Path, result: ValidationResult) -> None:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = path.relative_to(root)
        for match in PERSONAL_PATH_RE.finditer(text):
            result.error(f"Personal local path leak in {rel}: {match.group(0)}")
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                result.error(f"Potential secret detected in {rel}: {label}")


def validate_plugin(root: Path) -> ValidationResult:
    root = root.resolve()
    result = ValidationResult(root=root)
    if not root.exists() or not root.is_dir():
        result.error(f"Plugin path is not a directory: {root}")
        return result
    for filename in ("README.md", "LICENSE", "plugin.yaml"):
        if not (root / filename).exists():
            result.error(f"Missing {filename}")
    plugin_yaml = root / "plugin.yaml"
    metadata: dict[str, Any] = {}
    if plugin_yaml.exists():
        metadata = parse_simple_yaml(plugin_yaml)
        name = str(metadata.get("name") or "")
        if not name:
            result.error("Missing plugin.yaml name")
        elif not PLUGIN_NAME_RE.match(name):
            result.error("plugin.yaml name must use lowercase letters, numbers, and hyphens")
        elif name != root.name:
            result.error(f"plugin.yaml name must match plugin folder name: {root.name}")
        for key in ("version", "description", "origin", "kind"):
            if not metadata.get(key):
                result.error(f"Missing plugin.yaml {key}")
    validate_dashboard(root, result)
    validate_theme(root, result)
    scan_text_files(root, result)
    return result


def print_result(result: ValidationResult, repo_root: Path) -> None:
    try:
        label = result.root.relative_to(repo_root)
    except ValueError:
        label = result.root
    if result.ok:
        print(f"ok: {label}")
    else:
        print(f"failed: {label}")
    for error in result.errors:
        print(f"error: {error}")
    for warning in result.warnings:
        print(f"warning: {warning}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Hermes user plugin packages.")
    parser.add_argument("paths", nargs="+", help="Plugin directories to validate")
    args = parser.parse_args(argv)
    repo_root = Path.cwd().resolve()
    results = [validate_plugin(Path(path)) for path in args.paths]
    for result in results:
        print_result(result, repo_root)
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
