# Hermes Theme Hub

Dashboard plugin for discovering, inspecting, installing, and activating Hermes
dashboard themes.

This is a hub plugin, not a single theme. It appears as **Theme Hub** in the
Hermes dashboard and discovers theme-capable plugin packages automatically.

## What It Detects

A theme plugin is any Hermes user plugin folder that contains:

```text
plugin.yaml
theme/*.yaml
```

The hub lists installed dashboard themes from:

```text
<HERMES_HOME>/dashboard-themes
```

It lists theme plugins from normal Hermes plugin locations, including:

```text
~/.hermes/plugins/<plugin-name>
```

## Features

- Adds a **Theme Hub** sidebar entry at `/theme-hub`.
- Shows installed user themes.
- Shows discovered theme plugin packages.
- Installs a theme YAML from a theme plugin into the active Hermes home.
- Activates an installed or built-in theme by updating Hermes dashboard config.
- Avoids exposing personal local paths in the UI.

## Boundaries

- This plugin does not modify Hermes core files.
- This plugin does not publish themes to GitHub.
- This plugin does not claim official Hermes certification.
- Theme installation copies only a selected `theme/*.yaml` file into the active
  Hermes home.

## Verify Locally

```bash
python -m pytest tests/test_theme_hub_api.py -q
node --check dashboard/dist/index.js
python -m py_compile dashboard/plugin_api.py
```

Open the dashboard and select **Theme Hub**:

```text
http://127.0.0.1:9119/theme-hub
```
