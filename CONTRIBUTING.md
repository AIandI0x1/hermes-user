# Contributing

This repository contains self-contained Hermes Agent user plugins. Contributions
should preserve the user-space boundary: plugin behavior belongs inside the
plugin folder that owns it, not in upstream Hermes core.

## Contribution Scope

Good contributions include:

- New portable plugin folders under `plugins/<plugin-name>`.
- Documentation that clarifies the plugin contract, lifecycle, or publishing
  flow.
- Tests, screenshots, and validation scripts for existing plugins.
- Small fixes that keep plugin-owned frontend code inside each plugin folder.

Avoid:

- Hardcoding plugin-specific behavior into Hermes Agent core files.
- Publishing credentials, local caches, logs, or machine-specific paths.
- Claiming official Hermes certification without an official registry and
  signing workflow.

## Plugin Requirements

Before submitting a plugin, check:

- `README.md` explains install, usage, and boundaries.
- `plugin.yaml` identifies name, version, description, origin, and kind.
- `LICENSE` is present.
- Dashboard plugins include `dashboard/manifest.json`.
- Theme plugins include `theme/*.yaml`.
- Screenshots or video links are included where the plugin has UI.
- Secret scan output is clear or reviewed.
- User-facing paths use `~/.hermes/plugins/` or `<HERMES_HOME>/plugins/`.

See [PLUGIN_CONTRACT.md](PLUGIN_CONTRACT.md) and
[docs/PLUGIN_LIFECYCLE.md](docs/PLUGIN_LIFECYCLE.md).

## Local Validation

Run the focused checks for the plugin you changed. Examples:

```bash
python scripts/validate_plugin.py plugins/<plugin-name>
python -m pytest plugins/<plugin-name>/tests -q
node --check plugins/<plugin-name>/dashboard/dist/index.js
python -m py_compile plugins/<plugin-name>/dashboard/plugin_api.py
```

If a plugin does not have one of those surfaces, skip that command and document
what you did verify.

## Publishing

Publishing to GitHub is an external trust boundary. Use `plugin-publisher` to
review the destination path, secret scan, media evidence, and generated commands
before pushing.
