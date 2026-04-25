from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("publisher_api", ROOT / "dashboard" / "plugin_api.py")
publisher_api = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(publisher_api)


def test_repo_status_reports_existing_visibility(monkeypatch, tmp_path):
    def fake_run(cmd, cwd, timeout=120):
        assert cmd[:4] == ["gh", "repo", "view", "AIandI0x1/demo-plugin"]
        return {
            "ok": True,
            "stdout": json.dumps(
                {
                    "nameWithOwner": "AIandI0x1/demo-plugin",
                    "visibility": "PUBLIC",
                    "url": "https://github.com/AIandI0x1/demo-plugin",
                }
            ),
        }

    monkeypatch.setattr(publisher_api, "_run", fake_run)

    status = publisher_api._repo_status(tmp_path, "AIandI0x1/demo-plugin")

    assert status == {
        "exists": True,
        "name_with_owner": "AIandI0x1/demo-plugin",
        "visibility": "public",
        "url": "https://github.com/AIandI0x1/demo-plugin",
    }


def test_repo_status_reports_missing_repo(monkeypatch, tmp_path):
    def fake_run(cmd, cwd, timeout=120):
        return {"ok": False, "stderr": "not found"}

    monkeypatch.setattr(publisher_api, "_run", fake_run)

    status = publisher_api._repo_status(tmp_path, "AIandI0x1/demo-plugin")

    assert status["exists"] is False
    assert status["name_with_owner"] == "AIandI0x1/demo-plugin"


def test_github_account_reads_authenticated_login(monkeypatch, tmp_path):
    def fake_run(cmd, cwd, timeout=120):
        assert cmd == ["gh", "api", "user", "--jq", ".login"]
        return {"ok": True, "stdout": "AIandI0x1"}

    monkeypatch.setattr(publisher_api, "_run", fake_run)

    account = publisher_api._github_account(tmp_path)

    assert account == {"ok": True, "owner": "AIandI0x1"}


def test_default_repo_path_uses_authenticated_owner(monkeypatch, tmp_path):
    monkeypatch.setattr(publisher_api, "_github_account", lambda root: {"ok": True, "owner": "AIandI0x1"})

    assert publisher_api._default_repo_path(tmp_path, "demo-plugin") == "AIandI0x1/hermes-user/plugins/demo-plugin"


def test_github_plugin_path_uses_user_plugins_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(publisher_api, "_github_account", lambda root: {"ok": True, "owner": "AIandI0x1"})

    path = publisher_api._github_plugin_path(tmp_path, "demo-plugin")

    assert path == {
        "path": "AIandI0x1/hermes-user/plugins/demo-plugin",
        "url": "https://github.com/AIandI0x1/hermes-user/tree/main/plugins/demo-plugin",
    }


def test_plugin_readme_returns_markdown(monkeypatch, tmp_path):
    plugin_root = tmp_path / "demo-plugin"
    plugin_root.mkdir()
    (plugin_root / "README.md").write_text("# Demo\n\nReadme body.\n", encoding="utf-8")
    monkeypatch.setattr(publisher_api, "_plugin_root", lambda name: plugin_root)

    result = publisher_api._plugin_readme("demo-plugin")

    assert result["ok"] is True
    assert result["has_readme"] is True
    assert result["content"].startswith("# Demo")


def test_publish_creates_missing_repo_with_selected_visibility(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, cwd, timeout=120):
        calls.append(cmd)
        if cmd[:3] == ["git", "rev-parse", "--is-inside-work-tree"]:
            return {"ok": True, "stdout": "true"}
        if cmd[:3] == ["git", "diff", "--cached"]:
            return {"ok": True}
        if cmd[:4] == ["gh", "repo", "view", "AIandI0x1/demo-plugin"]:
            return {"ok": False, "stderr": "not found"}
        return {"ok": True, "stdout": ""}

    monkeypatch.setattr(publisher_api, "_run", fake_run)

    publisher_api._publish(tmp_path, "AIandI0x1/demo-plugin", "private")

    assert [
        "gh",
        "repo",
        "create",
        "AIandI0x1/demo-plugin",
        "--private",
        "--source",
        str(tmp_path),
        "--remote",
        "origin",
        "--push",
    ] in calls


def test_publish_pushes_existing_repo_without_create(monkeypatch, tmp_path):
    calls = []

    def fake_run(cmd, cwd, timeout=120):
        calls.append(cmd)
        if cmd[:3] == ["git", "rev-parse", "--is-inside-work-tree"]:
            return {"ok": True, "stdout": "true"}
        if cmd[:3] == ["git", "diff", "--cached"]:
            return {"ok": True}
        if cmd[:4] == ["gh", "repo", "view", "demo-plugin"]:
            return {
                "ok": True,
                "stdout": json.dumps(
                    {
                        "nameWithOwner": "AIandI0x1/demo-plugin",
                        "visibility": "PUBLIC",
                        "url": "https://github.com/AIandI0x1/demo-plugin",
                    }
                ),
            }
        if cmd[:3] == ["git", "remote", "get-url"]:
            return {"ok": False}
        if cmd[:3] == ["git", "branch", "--show-current"]:
            return {"ok": True, "stdout": "main"}
        return {"ok": True, "stdout": ""}

    monkeypatch.setattr(publisher_api, "_run", fake_run)

    publisher_api._publish(tmp_path, "demo-plugin", "private")

    assert not any(cmd[:3] == ["gh", "repo", "create"] for cmd in calls)
    assert ["git", "remote", "add", "origin", "https://github.com/AIandI0x1/demo-plugin.git"] in calls
    assert ["git", "push", "-u", "origin", "main"] in calls


def test_plan_accepts_user_plugin_collection_path(monkeypatch, tmp_path):
    plugin_root = tmp_path / "demo-plugin"
    plugin_root.mkdir()
    (plugin_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (plugin_root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    monkeypatch.setattr(publisher_api, "_plugin_root", lambda name: plugin_root)
    monkeypatch.setattr(publisher_api, "_github_account", lambda root: {"ok": True, "owner": "AIandI0x1"})
    monkeypatch.setattr(
        publisher_api,
        "_repo_status",
        lambda root, repo_path: {
            "exists": True,
            "name_with_owner": repo_path,
            "visibility": "public",
            "url": f"https://github.com/{repo_path}",
        },
    )

    plan = publisher_api._plan("demo-plugin", "AIandI0x1/hermes-user/plugins/demo-plugin", "public")

    assert plan["target"]["repository"] == "AIandI0x1/hermes-user"
    assert plan["target"]["subpath"] == "plugins/demo-plugin"
    assert plan["target"]["repo_path"] == "AIandI0x1/hermes-user/plugins/demo-plugin"
    assert "git clone https://github.com/AIandI0x1/hermes-user.git /tmp/hermes-plugin-publish" in plan["publish_commands"]
    assert any("git add plugins/demo-plugin" in command for command in plan["publish_commands"])


def test_plan_warns_when_no_screenshot_or_video_link(monkeypatch, tmp_path):
    plugin_root = tmp_path / "demo-plugin"
    plugin_root.mkdir()
    (plugin_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (plugin_root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    monkeypatch.setattr(publisher_api, "_plugin_root", lambda name: plugin_root)
    monkeypatch.setattr(publisher_api, "_github_account", lambda root: {"ok": True, "owner": "AIandI0x1"})
    monkeypatch.setattr(
        publisher_api,
        "_repo_status",
        lambda root, repo_path: {
            "exists": True,
            "name_with_owner": repo_path,
            "visibility": "public",
            "url": f"https://github.com/{repo_path}",
        },
    )

    plan = publisher_api._plan("demo-plugin", "AIandI0x1/hermes-user/plugins/demo-plugin", "public")

    assert plan["media_check"]["ok"] is False
    assert "Missing screenshot or video link" in plan["warnings"]


def test_plan_accepts_screenshot_as_media_evidence(monkeypatch, tmp_path):
    plugin_root = tmp_path / "demo-plugin"
    screenshots = plugin_root / "screenshots"
    screenshots.mkdir(parents=True)
    (plugin_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (plugin_root / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (screenshots / "demo.png").write_bytes(b"png")
    monkeypatch.setattr(publisher_api, "_plugin_root", lambda name: plugin_root)
    monkeypatch.setattr(publisher_api, "_github_account", lambda root: {"ok": True, "owner": "AIandI0x1"})
    monkeypatch.setattr(
        publisher_api,
        "_repo_status",
        lambda root, repo_path: {
            "exists": True,
            "name_with_owner": repo_path,
            "visibility": "public",
            "url": f"https://github.com/{repo_path}",
        },
    )

    plan = publisher_api._plan("demo-plugin", "AIandI0x1/hermes-user/plugins/demo-plugin", "public")

    assert plan["media_check"]["ok"] is True
    assert "screenshots/demo.png" in plan["media_check"]["screenshots"]
    assert "Missing screenshot or video link" not in plan["warnings"]


def test_update_collection_readme_lists_published_plugins(tmp_path):
    checkout = tmp_path / "repo"
    plugins_dir = checkout / "plugins"
    plugins_dir.mkdir(parents=True)

    dashboard = plugins_dir / "hermes-dashboard-plugins"
    dashboard.mkdir()
    (dashboard / "plugin.yaml").write_text(
        "name: hermes-dashboard-plugins\n"
        "description: Dashboard sidebar plugin that adds the plugins catalog page and plugin enable controls.\n",
        encoding="utf-8",
    )

    publisher = plugins_dir / "plugin-publisher"
    publisher.mkdir()
    (publisher / "plugin.yaml").write_text(
        "name: plugin-publisher\n"
        "description: Dashboard plugin for preparing, checking, and publishing Hermes user plugins to GitHub.\n",
        encoding="utf-8",
    )

    publisher_api._update_collection_readme(checkout, "AIandI0x1/hermes-user")

    readme = (checkout / "README.md").read_text(encoding="utf-8")
    assert "Self-contained user plugin collection" in readme
    assert "| [`hermes-dashboard-plugins`](plugins/hermes-dashboard-plugins) | Published | Dashboard sidebar plugin" in readme
    assert "| [`plugin-publisher`](plugins/plugin-publisher) | Published | Dashboard plugin for preparing" in readme
    assert "AIandI0x1/hermes-user/plugins/<plugin-name>" in readme
