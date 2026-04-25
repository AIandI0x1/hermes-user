# Hermes Hackathon Hub Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan step by step. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Hermes dashboard plugin that validates local plugin packages and generates Discord-ready hackathon submissions.

**Architecture:** The plugin is a drop-in Hermes dashboard extension with a static JavaScript IIFE frontend and a small FastAPI backend mounted under `/api/plugins/hermes-hackathon-hub/`. The backend owns filesystem scanning and validation; the frontend renders status, forms, and generated Discord text using the Hermes Plugin SDK.

**Tech Stack:** Hermes dashboard plugin manifest, plain JavaScript IIFE, React from `window.__HERMES_PLUGIN_SDK__`, theme-aware CSS, FastAPI `APIRouter`, Python standard library.

---

## File Structure

- Create: `dashboard/manifest.json`
  - Declares the dashboard plugin tab, JS entry, CSS file, and backend API.
- Create: `dashboard/dist/index.js`
  - React UI bundle written as a plain IIFE using `window.__HERMES_PLUGIN_SDK__`.
- Create: `dashboard/dist/style.css`
  - Theme-aware plugin styles scoped under `.hhh-*` classes.
- Create: `dashboard/plugin_api.py`
  - FastAPI routes for scanning plugin folders and validating package structure.
- Create: `tests/manual-test-checklist.md`
  - Manual verification checklist for dashboard loading, validation, and submission drafting.
- Modify: `README.md`
  - Add install, usage, and screenshot instructions after the plugin works.

## Validation Rules

Errors:

- Missing `dashboard/manifest.json`.
- Invalid JSON in manifest.
- Missing `name`, `label`, `tab.path`, or `entry`.
- `entry` points to a missing file.
- Declared `css` points to a missing file.
- Declared `api` points to a missing file.
- `tab.path` does not start with `/`.

Warnings:

- Missing `description`.
- Missing `version`.
- Missing `icon`.
- No README found at package root.
- No LICENSE found at package root.
- No screenshots folder or screenshot files.
- Plugin name contains characters outside lowercase letters, numbers, and hyphen.

## Task 1: Create Drop-In Dashboard Manifest

**Files:**
- Create: `dashboard/manifest.json`

- [ ] **Step 1: Write manifest**

Create this exact file:

```json
{
  "name": "hermes-hackathon-hub",
  "label": "Hackathon Hub",
  "description": "Validate Hermes dashboard plugins and prepare Discord review submissions.",
  "icon": "Package",
  "version": "0.1.0",
  "tab": {
    "path": "/plugins",
    "position": "after:skills"
  },
  "entry": "dist/index.js",
  "css": "dist/style.css",
  "api": "plugin_api.py"
}
```

- [ ] **Step 2: Install skeleton into Hermes plugin folder**

Run:

```bash
mkdir -p ~/.hermes/plugins
cd ~/.hermes/plugins/hermes-hackathon-hub
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

Expected: JSON response from the rescan endpoint, or dashboard remains reachable if rescan output is minimal.

- [ ] **Step 3: Commit manifest**

```bash
git add dashboard/manifest.json
git commit -m "feat: add dashboard plugin manifest"
```

## Task 2: Build Static Plugin Tab

**Files:**
- Create: `dashboard/dist/index.js`
- Create: `dashboard/dist/style.css`

- [ ] **Step 1: Create static UI bundle**

Create `dashboard/dist/index.js`:

```javascript
(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { Card, CardHeader, CardTitle, CardContent, Badge, Button } = SDK.components;

  function HackathonHubPage() {
    return React.createElement("div", { className: "hhh-page" },
      React.createElement(Card, null,
        React.createElement(CardHeader, null,
          React.createElement("div", { className: "hhh-title-row" },
            React.createElement(CardTitle, null, "Hermes Hackathon Hub"),
            React.createElement(Badge, { variant: "outline" }, "v0.1.0"),
          ),
        ),
        React.createElement(CardContent, null,
          React.createElement("p", { className: "hhh-muted" },
            "Validate local Hermes dashboard plugins, prepare Discord submissions, and track certification readiness.",
          ),
          React.createElement("div", { className: "hhh-actions" },
            React.createElement(Button, {
              onClick: function () {
                window.open("https://discord.com/channels/1053877538025386074/1497492452452470875", "_blank", "noopener,noreferrer");
              },
            }, "Open Discord Channel"),
          ),
        ),
      ),
      React.createElement("div", { className: "hhh-grid" },
        React.createElement(Card, null,
          React.createElement(CardHeader, null, React.createElement(CardTitle, null, "Local Validation")),
          React.createElement(CardContent, null, React.createElement("p", { className: "hhh-muted" }, "Backend validation arrives in Task 3.")),
        ),
        React.createElement(Card, null,
          React.createElement(CardHeader, null, React.createElement(CardTitle, null, "Certification")),
          React.createElement(CardContent, null, React.createElement("p", { className: "hhh-muted" }, "Official verification unavailable until a Hermes registry and public key exist.")),
        ),
      ),
    );
  }

  window.__HERMES_PLUGINS__.register("hermes-hackathon-hub", HackathonHubPage);
})();
```

- [ ] **Step 2: Create scoped styles**

Create `dashboard/dist/style.css`:

```css
.hhh-page {
  display: flex;
  flex-direction: column;
  gap: calc(1rem * var(--spacing-mul, 1));
}

.hhh-title-row,
.hhh-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.hhh-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: calc(1rem * var(--spacing-mul, 1));
}

.hhh-muted {
  color: var(--color-muted-foreground);
  font-size: 0.875rem;
  line-height: 1.5;
}
```

- [ ] **Step 3: Verify tab loads**

Run:

```bash
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

Then open:

```text
http://127.0.0.1:9119
```

Expected: dashboard route renders `Hermes Hackathon Hub`.

- [ ] **Step 4: Commit static tab**

```bash
git add dashboard/dist/index.js dashboard/dist/style.css
git commit -m "feat: add hackathon hub dashboard tab"
```

## Task 3: Add Backend Scan And Validation API

**Files:**
- Create: `dashboard/plugin_api.py`

- [ ] **Step 1: Implement validation backend**

Create `dashboard/plugin_api.py`:

```python
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

PLUGIN_NAME_RE = re.compile(r"^[a-z0-9-]+$")


class ValidateRequest(BaseModel):
    path: str


def _check_file(root: Path, relative: str, errors: list[str], label: str) -> None:
    target = root / relative
    if not target.exists():
        errors.append(f"{label} is declared but missing: {relative}")


def validate_plugin(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    dashboard_dir = root / "dashboard"
    manifest_path = dashboard_dir / "manifest.json"

    if not manifest_path.exists():
        return {
            "path": str(root),
            "ok": False,
            "errors": ["Missing dashboard/manifest.json"],
            "warnings": warnings,
            "manifest": None,
        }

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "path": str(root),
            "ok": False,
            "errors": [f"Invalid manifest JSON: {exc.msg}"],
            "warnings": warnings,
            "manifest": None,
        }

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
    if manifest.get("css"):
        _check_file(dashboard_dir, str(manifest["css"]), errors, "CSS file")
    if manifest.get("api"):
        _check_file(dashboard_dir, str(manifest["api"]), errors, "API file")

    if not (root / "README.md").exists():
        warnings.append("Missing README.md at plugin root")
    if not (root / "LICENSE").exists():
        warnings.append("Missing LICENSE at plugin root")

    screenshots_dir = root / "screenshots"
    if not screenshots_dir.exists() or not any(screenshots_dir.iterdir()):
        warnings.append("Missing screenshots or video assets")

    return {
        "path": str(root),
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "manifest": manifest,
        "trust": {
            "status": "locally_validated" if not errors else "unsigned",
            "official_verification": "unavailable",
        },
    }


@router.get("/scan")
async def scan_plugins() -> dict[str, Any]:
    roots = [
        Path.home() / ".hermes" / "plugins",
    ]
    candidates = []
    for root in roots:
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.is_dir() and (child / "dashboard").exists():
                candidates.append(validate_plugin(child))
    return {"plugins": candidates}


@router.post("/validate")
async def validate(body: ValidateRequest) -> dict[str, Any]:
    return validate_plugin(Path(body.path).expanduser().resolve())
```

- [ ] **Step 2: Verify backend route imports**

Run:

```bash
python -m py_compile dashboard/plugin_api.py
```

Expected: command exits with status `0`.

- [ ] **Step 3: Verify scan endpoint**

Run:

```bash
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
curl http://127.0.0.1:9119/api/plugins/hermes-hackathon-hub/scan
```

Expected: JSON containing a `plugins` array.

- [ ] **Step 4: Commit backend**

```bash
git add dashboard/plugin_api.py
git commit -m "feat: add plugin validation backend"
```

## Task 4: Connect Frontend To Backend

**Files:**
- Modify: `dashboard/dist/index.js`
- Modify: `dashboard/dist/style.css`

- [ ] **Step 1: Replace static validation panel with live scan**

In `dashboard/dist/index.js`, add `useState` and `useEffect`, call
`SDK.fetchJSON("/api/plugins/hermes-hackathon-hub/scan")`, and render returned
plugins with error and warning badges.

- [ ] **Step 2: Add validation status styles**

In `dashboard/dist/style.css`, add:

```css
.hhh-plugin-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.hhh-plugin-row {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.75rem;
  background: color-mix(in srgb, var(--color-card) 92%, transparent);
}

.hhh-status-ok {
  color: var(--color-success);
}

.hhh-status-warn {
  color: var(--color-warning);
}

.hhh-status-error {
  color: var(--color-destructive);
}
```

- [ ] **Step 3: Verify live scan renders**

Open:

```text
http://127.0.0.1:9119
```

Expected: at least `hermes-hackathon-hub` appears in the local plugin list.

- [ ] **Step 4: Commit frontend integration**

```bash
git add dashboard/dist/index.js dashboard/dist/style.css
git commit -m "feat: show live plugin validation results"
```

## Task 5: Add Discord Submission Composer

**Files:**
- Modify: `dashboard/dist/index.js`
- Modify: `dashboard/dist/style.css`

- [ ] **Step 1: Add form state**

Add state fields for:

- plugin name
- short pitch
- GitHub repo URL
- screenshots/video URLs
- install command
- notes

- [ ] **Step 2: Generate submission text**

Generate text using the template in `docs/DISCORD_REVIEW_PROTOCOL.md`.

- [ ] **Step 3: Add copy action**

Use `navigator.clipboard.writeText(submissionText)` from the button handler.
If clipboard write fails, show the text in a selectable `<textarea>`.

- [ ] **Step 4: Verify composer manually**

Expected:

- Editing form fields updates the generated post.
- Copy button copies the full post.
- Submit button opens the official Discord submission channel.
- No message is posted automatically.

- [ ] **Step 5: Commit composer**

```bash
git add dashboard/dist/index.js dashboard/dist/style.css
git commit -m "feat: add discord submission composer"
```

## Task 6: Add Manual Test Checklist And README Usage

**Files:**
- Create: `tests/manual-test-checklist.md`
- Modify: `README.md`

- [ ] **Step 1: Create manual checklist**

Create `tests/manual-test-checklist.md` with:

```markdown
# Manual Test Checklist

- [ ] `hermes dashboard --no-open` starts successfully.
- [ ] `curl http://127.0.0.1:9119/api/dashboard/plugins/rescan` succeeds.
- [ ] `http://127.0.0.1:9119/plugins` renders.
- [ ] Local plugin scan shows `hermes-hackathon-hub`.
- [ ] Validation distinguishes errors and warnings.
- [ ] Discord post preview updates from form fields.
- [ ] Copy button copies the generated post.
- [ ] Submit button opens the official Discord submission channel.
- [ ] Browser console has no plugin load errors.
```

- [ ] **Step 2: Update README**

Add install instructions:

```bash
mkdir -p ~/.hermes/plugins
git clone <repo-url> ~/.hermes/plugins/hermes-hackathon-hub
hermes dashboard --no-open
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

- [ ] **Step 3: Commit docs**

```bash
git add README.md tests/manual-test-checklist.md
git commit -m "docs: add install and manual test checklist"
```

## Self-Review

Spec coverage:

- Local validation is covered by Tasks 3 and 4.
- Discord submission drafting is covered by Task 5.
- Certification honesty is covered by the backend trust field and UI copy.
- Publishing docs are covered by Task 6.

Placeholder scan:

- The plan intentionally leaves no implementation placeholders for Tasks 1-3.
- Task 4 and Task 5 describe bounded frontend edits because final UI code should be adapted after Task 2 is visible in the dashboard.

Risk:

- `Path.home() / ".hermes" / "plugins"` is acceptable for this plugin's first external release because it is a user-installed plugin helper, not Hermes core code. If this later becomes bundled Hermes code, use `get_hermes_home()` from `hermes_constants`.
