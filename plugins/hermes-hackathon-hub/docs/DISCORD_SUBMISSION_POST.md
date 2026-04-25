# Hermes Dashboard Plugin Submission: Hermes User Plugins

https://github.com/AIandI0x1/hermes-user

## Short Pitch

Self-contained Hermes Agent user plugin collection for dashboard plugins, theme hubs, validation, publishing, and Discord-ready hackathon submissions.

## What It Includes

- **Hermes Dashboard Plugins** (`hermes-dashboard-plugins`): Adds the `/plugins` catalog page, origin labels, validation state, and local enable/disable controls.
- **Hermes Hackathon Hub** (`hermes-hackathon-hub`): Builds Discord-ready Hermes plugin submissions with readiness checks and honest trust language.
- **Hermes Theme Hub** (`hermes-theme-hub`): Discovers installed and plugin-provided dashboard themes, then installs or activates them.
- **Plugin Publisher** (`plugin-publisher`): Audits plugin folders and prepares explicit GitHub publishing commands.

## Plugin Enablement

Plugin enablement is managed locally through `hermes-dashboard-plugins`. It adds the `/plugins` dashboard page and lets installed dashboard plugins be enabled or disabled without editing Hermes core.

## Screenshots / Video

Attached below.

## Install

```bash
mkdir -p ~/.hermes/plugins
REPO_URL="<repository URL above>"
git clone "$REPO_URL" /tmp/hermes-user
cp -R /tmp/hermes-user/plugins/<plugin-name> ~/.hermes/plugins/<plugin-name>
export HERMES_DASHBOARD_URL="${HERMES_DASHBOARD_URL:-http://127.0.0.1:9119}"
curl "$HERMES_DASHBOARD_URL/api/dashboard/plugins/rescan"
```

## Validation

- Structure: passed
- Manifest: passed
- Entry bundle: passed
- Backend API: not present
- Trust: locally validated

## Notes

MVP does not auto-post to Discord. It generates a review-ready submission and keeps certification claims honest.

Draft generated with `hermes-hackathon-hub` from this repository.

For best Discord layout, send the text post first, then attach screenshots in a
reply or thread. Discord may place uploaded image previews before link previews
depending on attachment order.
