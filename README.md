# Hermes User Plugins

Self-contained user plugin collection for Hermes Agent dashboard extensions,
tools, skills, documentation, and supporting plugin workflows.

![Hermes User Plugins social preview](docs/assets/social-preview-plugin-cubes.png)

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
| [`hermes-dashboard-plugins`](plugins/hermes-dashboard-plugins) | Published | Dashboard sidebar plugin that adds the Plugins catalog page and plugin enable controls. |
| [`hermes-hackathon-hub`](plugins/hermes-hackathon-hub) | Published | Dashboard plugin for Hermes hackathon submission validation, Discord drafts, and plugin review workflow. |
| [`plugin-publisher`](plugins/plugin-publisher) | Published | User plugin that audits Hermes plugins and prepares GitHub publishing commands. |

## Quick Start

Install a plugin:

```bash
cp -R plugins/plugin-publisher ~/.hermes/plugins/plugin-publisher
hermes dashboard --no-open
```

Validate a plugin:

```bash
python scripts/validate_plugin.py plugins/plugin-publisher
```

Study a minimal example:

```text
examples/minimal-dashboard-plugin
examples/tool-only-plugin
examples/skill-only-plugin
```

## Plugin Contract

This collection follows the [Hermes User Plugin Contract](PLUGIN_CONTRACT.md).
Plugins should be portable folders installed under `~/.hermes/plugins/` or the
active `<HERMES_HOME>/plugins/` directory, with each plugin owning its own
frontend, docs, tools, skills, tests, screenshots, and metadata.

For contribution and release flow, see [CONTRIBUTING.md](CONTRIBUTING.md),
[SECURITY.md](SECURITY.md), and
[docs/PLUGIN_LIFECYCLE.md](docs/PLUGIN_LIFECYCLE.md).

## Screenshots

### Hermes Dashboard Plugins

![Plugins catalog screenshot](plugins/hermes-dashboard-plugins/screenshots/plugins-catalog.png)

### Hermes Hackathon Hub

![Hackathon Hub dashboard screenshot](plugins/hermes-hackathon-hub/screenshots/hackathon-hub-dashboard.png)

### Plugin Publisher

![Plugin Publisher dashboard screenshot](plugins/plugin-publisher/screenshots/plugin-publisher-dashboard.png)

## Repository Layout

```text
examples/
  minimal-dashboard-plugin/
  tool-only-plugin/
  skill-only-plugin/
plugins/
  hermes-dashboard-plugins/
  hermes-hackathon-hub/
  plugin-publisher/
scripts/
  validate_plugin.py
```

Each plugin should own its frontend, docs, tools, skills, tests, and metadata
inside its own plugin folder. User plugin work should not require direct edits
to upstream Hermes Agent core files.

## Publishing Rule

The canonical destination format for plugins in this repository is:

```text
AIandI0x1/hermes-user/plugins/<plugin-name>
```

Before publishing, run the plugin publisher readiness plan and review the secret
scan, destination path, repo visibility, and generated GitHub commands.

For contract validation, run:

```bash
python scripts/validate_plugin.py plugins/<plugin-name>
```
