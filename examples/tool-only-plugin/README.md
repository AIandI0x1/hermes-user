# Tool-Only Plugin

Small reference plugin for packages that expose tools without dashboard UI.

The example documents the package shape only. Real tool plugins should add a
Python entry point that registers tools through the Hermes plugin API.

## Validate

```bash
python scripts/validate_plugin.py examples/tool-only-plugin
```
