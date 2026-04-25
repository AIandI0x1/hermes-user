from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

PLUGIN_NAME_RE = re.compile(r"^[a-z0-9-]+$")
DEFAULT_SCAN_ROOTS: tuple[tuple[str, Path], ...] = (
    ("user", Path.home() / ".hermes" / "plugins"),
    ("bundled", Path.cwd() / "plugins"),
)
SCREENSHOT_SUFFIXES = {".gif", ".jpeg", ".jpg", ".mov", ".mp4", ".png", ".webm"}
HERMES_USER_REPO = "https://github.com/AIandI0x1/hermes-user"
HERMES_USER_SOCIAL_PREVIEW = (
    "https://raw.githubusercontent.com/AIandI0x1/hermes-user/main/"
    "docs/assets/social-preview-plugin-cubes.png"
)


class ValidateRequest(BaseModel):
    path: str


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


def _has_screenshot_assets(root: Path) -> bool:
    screenshots_dir = root / "screenshots"
    if not screenshots_dir.exists() or not screenshots_dir.is_dir():
        return False

    return any(
        path.is_file() and path.suffix.lower() in SCREENSHOT_SUFFIXES
        for path in screenshots_dir.iterdir()
    )


def _display_path(root: Path, source: str) -> str:
    if source == "user":
        return f"~/.hermes/plugins/{root.name}"
    if source == "bundled":
        return f"plugins/{root.name}"
    return root.name


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


class _GitHubMetaParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "meta":
            return
        data = {key: value for key, value in attrs if value is not None}
        key = data.get("property") or data.get("name")
        content = data.get("content")
        if key and content:
            self.meta[key] = content


def fetch_github_repo_metadata(repo_url: str) -> dict[str, Any]:
    request = Request(repo_url, headers={"User-Agent": "Hermes-Hackathon-Hub/0.1"})
    try:
        with urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", "replace")
    except Exception as exc:
        return {
            "ok": False,
            "repo_url": repo_url,
            "media_url": HERMES_USER_SOCIAL_PREVIEW,
            "description": "Self-contained Hermes Agent user plugin collection with plugin manager, hackathon hub, publisher, examples, validation, and CI.",
            "error": str(exc),
        }

    parser = _GitHubMetaParser()
    parser.feed(html)
    return {
        "ok": True,
        "repo_url": repo_url,
        "media_url": parser.meta.get("og:image") or parser.meta.get("twitter:image") or HERMES_USER_SOCIAL_PREVIEW,
        "description": parser.meta.get("og:description") or parser.meta.get("description") or "Self-contained Hermes Agent user plugin collection.",
        "title": parser.meta.get("og:title") or "Hermes User Plugins",
    }


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


def collection_submission_candidate() -> dict[str, Any]:
    repo_metadata = fetch_github_repo_metadata(HERMES_USER_REPO)
    media_url = str(repo_metadata.get("media_url") or HERMES_USER_SOCIAL_PREVIEW)
    description = str(
        repo_metadata.get("description")
        or "Self-contained Hermes Agent user plugin collection with plugin manager, hackathon hub, publisher, examples, validation, and CI."
    )
    manifest = {
        "name": "hermes-user",
        "label": "Hermes User Plugins",
        "description": description,
        "icon": "Package",
        "version": "0.1.0",
        "entry": "",
        "tab": {"path": ""},
    }
    return {
        "path": HERMES_USER_REPO,
        "source": "github",
        "ok": True,
        "errors": [],
        "warnings": [],
        "summary": {
            "has_readme": True,
            "has_license": True,
            "has_media": bool(media_url),
            "has_backend_api": False,
            "has_css": False,
            "tab_path": "",
            "repo_url": HERMES_USER_REPO,
            "media_url": media_url,
            "media_source": "github_open_graph" if repo_metadata.get("ok") else "fallback_repo_asset",
            "install_command": "git clone https://github.com/AIandI0x1/hermes-user.git",
        },
        "manifest": manifest,
        "trust": {
            "status": "locally_validated",
            "official_verification": "unavailable",
            "detail": "Public user plugin collection with local validator and passing GitHub Actions. This is not official Hermes certification.",
        },
    }


def _candidate_roots() -> list[tuple[str, Path]]:
    candidates: list[tuple[str, Path]] = []
    seen: set[Path] = set()

    for source, scan_root in DEFAULT_SCAN_ROOTS:
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


@router.get("/scan")
async def scan_plugins() -> dict[str, Any]:
    return {
        "plugins": [
            collection_submission_candidate(),
            *[validate_plugin(path, source) for source, path in _candidate_roots()],
        ]
    }


@router.post("/validate")
async def validate(body: ValidateRequest) -> dict[str, Any]:
    return validate_plugin(Path(body.path))
