from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from tools.publisher import publish_plan  # noqa: E402


router = APIRouter()

PLUGIN_NAME_RE = re.compile(r"^[a-z0-9-]+$")
REPO_PATH_RE = re.compile(r"^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$")
IGNORED_COPY_NAMES = {".git", "__pycache__", ".pytest_cache", ".DS_Store"}
USER_PLUGIN_REPO = "hermes-user"


class PlanRequest(BaseModel):
    plugin_name: str
    repo_path: str | None = None
    visibility: str = "public"


class PublishRequest(BaseModel):
    plugin_name: str
    repo_path: str
    visibility: str = "public"
    confirm: bool = False


class DefaultsRequest(BaseModel):
    plugin_name: str


class ReadmeRequest(BaseModel):
    plugin_name: str


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "cmd": cmd, "error": f"Missing executable: {cmd[0]}"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "cmd": cmd, "error": "Command timed out"}

    return {
        "ok": completed.returncode == 0,
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
    }


def _plugin_root(name: str) -> Path:
    if not PLUGIN_NAME_RE.match(name):
        raise ValueError("Invalid plugin name")
    try:
        from hermes_constants import get_hermes_home

        hermes_home = get_hermes_home()
    except Exception:
        hermes_home = Path("~/.hermes").expanduser()
    root = (hermes_home / "plugins" / name).resolve()
    plugins_root = (hermes_home / "plugins").resolve()
    root.relative_to(plugins_root)
    if not root.is_dir():
        raise FileNotFoundError(f"Plugin folder not found: {name}")
    return root


def _parse_repo(repo_path: str) -> tuple[str | None, str, str | None]:
    clean = repo_path.strip()
    if not clean or not REPO_PATH_RE.match(clean):
        raise ValueError("GitHub path must be repo, owner/repo, or owner/repo/path")
    parts = clean.split("/")
    if len(parts) == 1:
        return None, parts[0], None
    subpath = "/".join(parts[2:]) if len(parts) > 2 else None
    return parts[0], parts[1], subpath


def _github_account(root: Path) -> dict[str, Any]:
    result = _run(["gh", "api", "user", "--jq", ".login"], root)
    if not result["ok"] or not result.get("stdout"):
        return {
            "ok": False,
            "owner": None,
            "error": result.get("stderr") or result.get("error") or "Unable to read gh authenticated user",
        }
    return {"ok": True, "owner": str(result["stdout"]).strip()}


def _default_repo_path(root: Path, plugin_name: str) -> str:
    account = _github_account(root)
    owner = account.get("owner")
    return f"{owner}/{USER_PLUGIN_REPO}/plugins/{plugin_name}" if owner else f"{USER_PLUGIN_REPO}/plugins/{plugin_name}"


def _github_plugin_path(root: Path, plugin_name: str) -> dict[str, str | None]:
    account = _github_account(root)
    owner = account.get("owner")
    if not owner:
        return {"path": None, "url": None}
    path = f"{owner}/{USER_PLUGIN_REPO}/plugins/{plugin_name}"
    return {
        "path": path,
        "url": f"https://github.com/{owner}/{USER_PLUGIN_REPO}/tree/main/plugins/{plugin_name}",
    }


def _plugin_readme(plugin_name: str, max_chars: int = 12_000) -> dict[str, Any]:
    root = _plugin_root(plugin_name)
    readme_path = root / "README.md"
    if not readme_path.exists() or not readme_path.is_file():
        return {
            "ok": True,
            "plugin_name": plugin_name,
            "has_readme": False,
            "content": "",
        }
    content = readme_path.read_text(encoding="utf-8", errors="replace")
    truncated = len(content) > max_chars
    return {
        "ok": True,
        "plugin_name": plugin_name,
        "has_readme": True,
        "content": content[:max_chars],
        "truncated": truncated,
    }


def _repo_status(root: Path, repo_path: str) -> dict[str, Any]:
    view = _run(
        ["gh", "repo", "view", repo_path, "--json", "nameWithOwner,visibility,url"],
        root,
    )
    if not view["ok"]:
        return {
            "exists": False,
            "name_with_owner": repo_path,
            "visibility": None,
            "url": None,
            "error": view.get("stderr") or view.get("error") or "Repository not found",
        }

    try:
        payload = json.loads(view.get("stdout") or "{}")
    except json.JSONDecodeError:
        return {
            "exists": False,
            "name_with_owner": repo_path,
            "visibility": None,
            "url": None,
            "error": "Unable to parse gh repo view output",
        }

    visibility = payload.get("visibility")
    return {
        "exists": True,
        "name_with_owner": payload.get("nameWithOwner") or repo_path,
        "visibility": str(visibility).lower() if visibility else None,
        "url": payload.get("url"),
    }


def _full_repo(owner: str | None, repo_name: str) -> str:
    return f"{owner}/{repo_name}" if owner else repo_name


def _destination_path(owner: str | None, repo_name: str, subpath: str | None) -> str:
    repo = _full_repo(owner, repo_name)
    return f"{repo}/{subpath}" if subpath else repo


def _path_publish_commands(root: Path, full_repo: str, subpath: str, visibility: str, repo_exists: bool) -> list[str]:
    flag = "--public" if visibility == "public" else "--private"
    commands: list[str] = []
    if not repo_exists:
        commands.append(f"gh repo create {full_repo} {flag}")
    commands.extend([
        f"git clone https://github.com/{full_repo}.git /tmp/hermes-plugin-publish",
        f"rm -rf /tmp/hermes-plugin-publish/{subpath}",
        f"mkdir -p /tmp/hermes-plugin-publish/{str(Path(subpath).parent)}",
        f"cp -R {str(root)!r} /tmp/hermes-plugin-publish/{subpath}",
        f"cd /tmp/hermes-plugin-publish && git add {subpath}",
        f"cd /tmp/hermes-plugin-publish && git commit -m \"Publish {root.name} plugin\"",
        "cd /tmp/hermes-plugin-publish && git push origin $(git branch --show-current)",
    ])
    return commands


def _plan(plugin_name: str, repo_path: str | None, visibility: str) -> dict[str, Any]:
    root = _plugin_root(plugin_name)
    owner = None
    repo_name = plugin_name
    subpath = None
    resolved_repo_path = repo_path or _default_repo_path(root, plugin_name)
    if resolved_repo_path:
        owner, repo_name, subpath = _parse_repo(resolved_repo_path)
    plan = json.loads(
        publish_plan(
            {
                "plugin_path": str(root),
                "repo_name": repo_name,
                "owner": owner,
                "visibility": visibility,
            }
        )
    )
    target_repo = _full_repo(owner, repo_name)
    destination = _destination_path(owner, repo_name, subpath)
    repo_status = _repo_status(root, target_repo)
    plan["repo"] = repo_status
    plan["target"] = {
        "repo_path": destination,
        "repository": target_repo,
        "subpath": subpath,
        "github_path": _github_plugin_path(root, plugin_name),
        "requested_visibility": visibility if visibility in {"public", "private"} else "public",
        "action": "push_existing_repo" if repo_status.get("exists") else "create_repo_then_push",
    }
    if repo_status.get("exists") and repo_status.get("visibility") != plan["target"]["requested_visibility"]:
        plan.setdefault("warnings", []).append(
            "Target repo already exists as "
            + str(repo_status.get("visibility") or "unknown")
            + "; publisher will push without changing repository visibility."
        )
    if subpath:
        plan["publish_commands"] = _path_publish_commands(
            root,
            target_repo,
            subpath,
            plan["target"]["requested_visibility"],
            bool(repo_status.get("exists")),
        )
    return plan


def _ensure_git_repo(root: Path, message: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    inside = _run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if not inside["ok"]:
        results.append(_run(["git", "init"], root))
    results.append(_run(["git", "add", "."], root))
    diff = _run(["git", "diff", "--cached", "--quiet"], root)
    if not diff["ok"]:
        results.append(_run(["git", "commit", "-m", message], root))
    return results


def _current_branch(root: Path) -> str:
    branch = _run(["git", "branch", "--show-current"], root)
    if branch["ok"] and branch["stdout"]:
        return str(branch["stdout"])
    return "main"


def _copy_plugin_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in IGNORED_COPY_NAMES or item.suffix == ".pyc":
            continue
        target = destination / item.name
        if item.is_dir():
            shutil.copytree(
                item,
                target,
                ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".DS_Store", "*.pyc"),
            )
        elif item.is_file():
            shutil.copy2(item, target)


def _read_plugin_description(plugin_root: Path) -> str:
    plugin_yaml = plugin_root / "plugin.yaml"
    if not plugin_yaml.exists():
        return "Hermes user plugin."
    for line in plugin_yaml.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("description:"):
            return line.split(":", 1)[1].strip().strip("\"'") or "Hermes user plugin."
    return "Hermes user plugin."


def _update_collection_readme(checkout: Path, full_repo: str) -> None:
    plugins_dir = checkout / "plugins"
    plugin_roots = sorted(path for path in plugins_dir.iterdir() if path.is_dir()) if plugins_dir.exists() else []
    rows = [
        f"| [`{plugin.name}`](plugins/{plugin.name}) | Published | {_read_plugin_description(plugin)} |"
        for plugin in plugin_roots
    ]
    layout = "\n".join(f"  {plugin.name}/" for plugin in plugin_roots) or "  <plugin-name>/"
    plugins_table = "\n".join(rows) or "| `<plugin-name>` | Planned | Hermes user plugin. |"
    content = f"""# Hermes User Plugins

Self-contained user plugin collection for Hermes Agent dashboard extensions,
tools, skills, documentation, and supporting plugin workflows.

This repository is separate from upstream `hermes-agent` source code. Plugins
published here are user-owned packages. Each plugin folder is intended to be
portable on its own and should include the files it needs to run, document,
test, and expose its dashboard or tool functionality.

Install a plugin by placing its folder in the local Hermes user plugin
directory:

```text
~/.hermes/plugins/<plugin-name>
```

For profile-based Hermes installs, use the active profile's Hermes home:

```text
<HERMES_HOME>/plugins/<plugin-name>
```

## Plugins

| Plugin | Status | Description |
| --- | --- | --- |
{plugins_table}

## Repository Layout

```text
plugins/
{layout}
```

Each plugin should own its frontend, docs, tools, skills, tests, and metadata
inside its own plugin folder. User plugin work should not require direct edits
to upstream Hermes Agent core files.

## Publishing Rule

The canonical destination format for plugins in this repository is:

```text
{full_repo}/plugins/<plugin-name>
```

Before publishing, run the plugin publisher readiness plan and review the secret
scan, destination path, repo visibility, and generated GitHub commands.
"""
    (checkout / "README.md").write_text(content, encoding="utf-8")


def _publish_into_repo_path(root: Path, full_repo: str, subpath: str, visibility: str) -> list[dict[str, Any]]:
    flag = "--public" if visibility == "public" else "--private"
    results: list[dict[str, Any]] = []
    repo = _repo_status(root, full_repo)
    if not repo["exists"]:
        results.append(_run(["gh", "repo", "create", full_repo, flag], root, timeout=180))

    with tempfile.TemporaryDirectory(prefix="hermes-plugin-publish-") as tmp:
        tmp_root = Path(tmp)
        clone_url = f"https://github.com/{full_repo}.git"
        clone = _run(["git", "clone", clone_url, "repo"], tmp_root, timeout=180)
        results.append(clone)
        if not clone.get("ok"):
            return results

        checkout = tmp_root / "repo"
        target = (checkout / subpath).resolve()
        target.relative_to(checkout.resolve())
        _copy_plugin_tree(root, target)
        _update_collection_readme(checkout, full_repo)
        results.append(_run(["git", "add", subpath, "README.md"], checkout))
        diff = _run(["git", "diff", "--cached", "--quiet"], checkout)
        if not diff["ok"]:
            results.append(_run(["git", "commit", "-m", f"Publish {root.name} plugin"], checkout))
        results.append(_run(["git", "push", "origin", _current_branch(checkout)], checkout, timeout=180))
    return results


def _publish(root: Path, repo_path: str, visibility: str) -> list[dict[str, Any]]:
    owner, repo_name, subpath = _parse_repo(repo_path)
    full_repo = _full_repo(owner, repo_name)
    if subpath:
        return _publish_into_repo_path(root, full_repo, subpath, visibility)

    flag = "--public" if visibility == "public" else "--private"
    results = _ensure_git_repo(root, "Prepare plugin publish")

    repo = _repo_status(root, full_repo)
    if repo["exists"]:
        name_with_owner = repo["name_with_owner"]
        remote_url = f"https://github.com/{name_with_owner}.git"
        remote = _run(["git", "remote", "get-url", "origin"], root)
        if remote["ok"]:
            results.append(_run(["git", "remote", "set-url", "origin", remote_url], root))
        else:
            results.append(_run(["git", "remote", "add", "origin", remote_url], root))
        results.append(_run(["git", "push", "-u", "origin", _current_branch(root)], root, timeout=180))
    else:
        results.append(
            _run(
                ["gh", "repo", "create", full_repo, flag, "--source", str(root), "--remote", "origin", "--push"],
                root,
                timeout=180,
            )
        )
    return results


@router.post("/plan")
async def plan(body: PlanRequest) -> dict[str, Any]:
    try:
        return _plan(body.plugin_name, body.repo_path, body.visibility)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/defaults")
async def defaults(body: DefaultsRequest) -> dict[str, Any]:
    try:
        root = _plugin_root(body.plugin_name)
        account = _github_account(root)
        repo_path = _default_repo_path(root, body.plugin_name)
        return {
            "ok": True,
            "plugin_name": body.plugin_name,
            "github": account,
            "repo_path": repo_path,
            "github_path": _github_plugin_path(root, body.plugin_name),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/readme")
async def readme(body: ReadmeRequest) -> dict[str, Any]:
    try:
        return _plugin_readme(body.plugin_name)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@router.post("/publish")
async def publish(body: PublishRequest) -> dict[str, Any]:
    if not body.confirm:
        return {"ok": False, "error": "Confirmation is required"}
    try:
        root = _plugin_root(body.plugin_name)
        plan = _plan(body.plugin_name, body.repo_path, body.visibility)
        findings = ((plan.get("secret_scan") or {}).get("findings") or [])
        if findings:
            return {
                "ok": False,
                "error": "Secret-risk findings must be resolved before publishing",
                "plan": plan,
            }
        results = _publish(root, body.repo_path, body.visibility)
        return {
            "ok": all(item.get("ok") for item in results),
            "plugin": body.plugin_name,
            "repo_path": body.repo_path,
            "results": results,
            "plan": plan,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
