# Hermes User Plugin Contract

This contract defines the portable shape expected for Hermes Agent user plugins
published in this collection.

The goal is simple: a plugin should be installable as one folder under the
active Hermes user plugin directory, should own its own dashboard changes, and
should be auditable before publication.

```text
~/.hermes/plugins/<plugin-name>
```

For profile-based Hermes installs, the same folder lives under the active
profile home:

```text
<HERMES_HOME>/plugins/<plugin-name>
```

## Required Package Shape

```text
<plugin-name>/
├── README.md
├── plugin.yaml
├── LICENSE
├── dashboard/
│   └── manifest.json
├── screenshots/
└── tests/
```

Only `dashboard/` is required for dashboard plugins. Tool-only or skill-only
plugins may omit it, but they must document their entry points in `README.md`
and `plugin.yaml`.

## Metadata

`plugin.yaml` should identify the plugin and the runtime surfaces it exposes.

```yaml
name: plugin-name
version: 0.1.0
description: Short human-readable description.
origin: user
dashboard:
  manifest: dashboard/manifest.json
tools: []
skills: []
permissions:
  filesystem: []
  network: []
  github: false
validation:
  secret_scan: required
  screenshots: required
  frontend_ownership: required
trust:
  official_signature: unavailable
```

Use conservative permission descriptions. If a plugin can publish to GitHub,
write files, open network URLs, or inspect local plugin folders, document that
behavior explicitly.

## Dashboard Plugins

Dashboard plugins own their frontend files inside their own plugin folder.
They should not require direct edits to upstream Hermes Agent dashboard source.

Expected dashboard shape:

```text
dashboard/
├── manifest.json
├── plugin_api.py
└── dist/
    ├── index.js
    └── style.css
```

`dashboard/manifest.json` should reference files inside the same `dashboard/`
folder. Paths that escape the plugin folder are not portable and should fail
local validation.

## Ownership Boundary

Each plugin owns its own frontend, docs, tools, skills, tests, screenshots, and
metadata. Shared behavior should be added through generic plugin APIs or shared
documentation, not by hardcoding plugin-specific changes into Hermes core.

For dashboard frontend work, the collection uses the rule implemented by
`hermes-dashboard-plugins`:

```text
rules/frontend-ownership.md
scripts/enforce_frontend_ownership.py
```

## Publication Readiness

Before publishing a plugin, verify:

- README is present and explains install, usage, and boundaries.
- LICENSE is present.
- `plugin.yaml` is present.
- Dashboard manifest and frontend bundle validate, if the plugin exposes UI.
- Screenshot or video evidence is present.
- Secret scan is clear or every finding is reviewed.
- User-facing paths avoid personal local paths and use `~/.hermes/plugins/` or
  `<HERMES_HOME>/plugins/`.
- The destination path follows the user plugin collection format:

```text
AIandI0x1/hermes-user/plugins/<plugin-name>
```

## Trust Model

Local validation is not official Hermes certification.

Until Hermes publishes an official registry, signing key, and verification
workflow, plugins should describe trust states conservatively:

- `local`: package exists on disk and can be inspected.
- `locally_validated`: local checks passed.
- `unsigned`: no official signature is available.
- `official_verification_unavailable`: Hermes official verification is not yet
  available for this package.

Do not claim a plugin is certified, signed, or endorsed by the Hermes team
unless the claim can be verified against an official Hermes trust root.

## Publishing Boundary

Publishing sends files to GitHub and may create or update public repositories.
The publisher must show the destination path, secret scan result, media check,
and generated GitHub commands before any push.

Automated publish flows should require explicit confirmation.
