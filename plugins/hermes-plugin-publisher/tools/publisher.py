from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


MAX_SCAN_BYTES = 512_000
TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".env",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
IGNORED_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "dist-info",
}
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("openai_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("github_token", re.compile(r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("discord_webhook", re.compile(r"https://discord(?:app)?\\.com/api/webhooks/[A-Za-z0-9_./-]+")),
    ("env_secret_assignment", re.compile(r"(?i)\\b(api[_-]?key|secret|token|password)\\b\\s*[:=]\\s*['\\\"]?[^'\\\"\\s]{8,}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


HERMES_PLUGIN_PUBLISH_PLAN_SCHEMA = {
    "name": "hermes_plugin_publish_plan",
    "description": (
        "Audit a Hermes plugin folder for GitHub publishing readiness. "
        "Returns redacted secret-scan findings, plugin metadata, git status, "
        "and explicit gh/git commands. This tool does not push or create repos."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "plugin_path": {
                "type": "string",
                "description": "Absolute or user-relative path to the plugin folder.",
            },
            "repo_name": {
                "type": "string",
                "description": "GitHub repository name to publish to. Defaults to the plugin directory name.",
            },
            "owner": {
                "type": "string",
                "description": "Optional GitHub owner or org. When omitted, gh uses the authenticated account.",
            },
            "visibility": {
                "type": "string",
                "enum": ["public", "private"],
                "default": "public",
                "description": "GitHub repository visibility for the generated command.",
            },
        },
        "required": ["plugin_path"],
    },
}


def _run(cmd: list[str], cwd: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "missing": cmd[0], "stdout": "", "stderr": ""}
    except subprocess.TimeoutExpired:
        return {"ok": False, "timeout": True, "stdout": "", "stderr": ""}

    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "[REDACTED]"
    return value[:4] + "[REDACTED]" + value[-4:]


def _iter_scan_files(root: Path):
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
        except OSError:
            continue
        yield path


def _scan_secrets(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in _iter_scan_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, 1):
            for name, pattern in SECRET_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                findings.append(
                    {
                        "file": str(path.relative_to(root)),
                        "line": number,
                        "type": name,
                        "redacted_match": _redact(match.group(0)),
                    }
                )
    return findings


def _read_yaml_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _read_json_metadata(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _plugin_summary(root: Path) -> dict[str, Any]:
    plugin_yaml = _read_yaml_metadata(root / "plugin.yaml")
    dashboard_manifest = _read_json_metadata(root / "dashboard" / "manifest.json")
    codex_manifest = _read_json_metadata(root / ".codex-plugin" / "plugin.json")

    return {
        "root": str(root),
        "name": (
            (plugin_yaml or {}).get("name")
            or (dashboard_manifest or {}).get("name")
            or (codex_manifest or {}).get("name")
            or root.name
        ),
        "has_plugin_yaml": plugin_yaml is not None,
        "has_dashboard_manifest": dashboard_manifest is not None,
        "has_codex_manifest": codex_manifest is not None,
        "has_readme": (root / "README.md").exists(),
        "has_license": (root / "LICENSE").exists(),
        "provides_tools": (plugin_yaml or {}).get("provides_tools", []),
        "dashboard_route": ((dashboard_manifest or {}).get("tab") or {}).get("path"),
    }


def _git_summary(root: Path) -> dict[str, Any]:
    inside = _run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if not inside.get("ok"):
        return {"is_repo": False, "status": None, "branch": None, "remote": None}

    return {
        "is_repo": True,
        "status": _run(["git", "status", "--short"], root).get("stdout", ""),
        "branch": _run(["git", "branch", "--show-current"], root).get("stdout", ""),
        "remote": _run(["git", "remote", "-v"], root).get("stdout", ""),
    }


def _repo_status(root: Path, full_repo: str) -> dict[str, Any]:
    view = _run(["gh", "repo", "view", full_repo, "--json", "nameWithOwner,visibility,url"], root)
    if not view.get("ok"):
        return {
            "exists": False,
            "name_with_owner": full_repo,
            "visibility": None,
            "url": None,
            "error": view.get("stderr") or "Repository not found",
        }
    try:
        payload = json.loads(view.get("stdout") or "{}")
    except json.JSONDecodeError:
        return {
            "exists": False,
            "name_with_owner": full_repo,
            "visibility": None,
            "url": None,
            "error": "Unable to parse gh repo view output",
        }
    visibility = payload.get("visibility")
    return {
        "exists": True,
        "name_with_owner": payload.get("nameWithOwner") or full_repo,
        "visibility": str(visibility).lower() if visibility else None,
        "url": payload.get("url"),
    }


def _commands(root: Path, repo_name: str, owner: str | None, visibility: str, is_repo: bool, repo_exists: bool) -> list[str]:
    full_repo = f"{owner}/{repo_name}" if owner else repo_name
    flag = "--public" if visibility == "public" else "--private"
    commands: list[str] = []
    if not is_repo:
        commands.extend([
            "git init",
            "git add .",
            "git commit -m \"Initial plugin publish\"",
        ])
    else:
        commands.extend([
            "git status --short",
            "git add .",
            "git commit -m \"Prepare plugin publish\"",
        ])
    if repo_exists:
        commands.extend([
            f"git remote set-url origin https://github.com/{full_repo}.git  # or add origin if missing",
            "git push -u origin $(git branch --show-current)",
        ])
    else:
        commands.append(f"gh repo create {full_repo} {flag} --source {str(root)!r} --remote origin --push")
    return commands


def publish_plan(args: dict[str, Any], **_: Any) -> str:
    root = Path(str(args.get("plugin_path", ""))).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return json.dumps(
            {"ok": False, "error": f"Plugin path does not exist or is not a directory: {root}"},
            indent=2,
        )

    summary = _plugin_summary(root)
    repo_name = str(args.get("repo_name") or summary["name"] or root.name)
    owner = args.get("owner")
    owner = str(owner) if owner else None
    visibility = str(args.get("visibility") or "public")
    if visibility not in {"public", "private"}:
        visibility = "public"

    secret_findings = _scan_secrets(root)
    git = _git_summary(root)
    full_repo = f"{owner}/{repo_name}" if owner else repo_name
    repo = _repo_status(root, full_repo)
    warnings: list[str] = []
    if not summary["has_readme"]:
        warnings.append("Missing README.md")
    if not summary["has_license"]:
        warnings.append("Missing LICENSE")
    if secret_findings:
        warnings.append("Secret-risk findings must be reviewed before publishing")
    if git["is_repo"] and git["status"]:
        warnings.append("Git working tree has uncommitted changes")
    if repo.get("exists") and repo.get("visibility") != visibility:
        warnings.append(
            "Target repo already exists as "
            + str(repo.get("visibility") or "unknown")
            + "; publishing will not change repository visibility."
        )

    return json.dumps(
        {
            "ok": True,
            "plugin": summary,
            "git": git,
            "repo": repo,
            "target": {
                "repo_path": full_repo,
                "requested_visibility": visibility,
                "action": "push_existing_repo" if repo.get("exists") else "create_repo_then_push",
            },
            "secret_scan": {
                "ok": not secret_findings,
                "findings": secret_findings,
                "note": "Matches are redacted. Review files locally before publishing.",
            },
            "warnings": warnings,
            "publish_commands": _commands(root, repo_name, owner, visibility, bool(git["is_repo"]), bool(repo.get("exists"))),
            "safety": (
                "The tool only generates commands. Creating a repo, pushing, or changing visibility "
                "shares files with GitHub and needs explicit user confirmation at action time."
            ),
        },
        indent=2,
    )
