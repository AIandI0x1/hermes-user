# Theme Hub Workflow

## Install

```bash
mkdir -p ~/.hermes/plugins
cp -R plugins/hermes-theme-hub ~/.hermes/plugins/hermes-theme-hub
hermes dashboard --no-open
export HERMES_DASHBOARD_URL="${HERMES_DASHBOARD_URL:-http://127.0.0.1:9119}"
curl "$HERMES_DASHBOARD_URL/api/dashboard/plugins/rescan"
```

Open the local dashboard and select **Theme Hub**.

## Create A Theme Plugin

```text
~/.hermes/plugins/my-theme-pack/
  plugin.yaml
  theme/
    my-theme.yaml
```

Theme YAML files should include at least:

```yaml
name: my-theme
label: My Theme
description: Local dashboard theme
```

## Verify

```bash
python -m pytest tests/test_theme_hub_api.py -q
node --check dashboard/dist/index.js
python -m py_compile dashboard/plugin_api.py
```
