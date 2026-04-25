# Minimal Dashboard Plugin

Small reference dashboard plugin for the Hermes user plugin contract.

It adds a dashboard tab at `/minimal-dashboard-plugin` and keeps every frontend
file inside its own plugin folder.

## Install

```bash
cp -R examples/minimal-dashboard-plugin ~/.hermes/plugins/minimal-dashboard-plugin
hermes dashboard --no-open
```

## Validate

```bash
python scripts/validate_plugin.py examples/minimal-dashboard-plugin
```
