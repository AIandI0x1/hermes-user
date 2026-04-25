# Hermes User Plugins

Self-contained user plugin collection for Hermes Agent dashboard extensions,
tools, skills, documentation, and supporting plugin workflows.

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

## Local Dashboard URLs

Dashboard links such as `http://127.0.0.1:9119/plugins`,
`http://127.0.0.1:9119/theme-hub`, and
`http://127.0.0.1:9119/hackathon-hub` are local loopback URLs. They are only
reachable from the machine running `hermes dashboard` and are not public
support, contact, or remote access endpoints.

## Plugins

| Plugin | Status | Description |
| --- | --- | --- |
| [`hermes-dashboard-plugins`](plugins/hermes-dashboard-plugins) | Published | Dashboard sidebar plugin that adds the Plugins catalog page and plugin enable controls. |
| [`hermes-hackathon-hub`](plugins/hermes-hackathon-hub) | Published | Dashboard plugin for Hermes hackathon submission validation, Discord drafts, and plugin review workflow. |
| [`hermes-theme-hub`](plugins/hermes-theme-hub) | Published | Dashboard plugin for discovering, inspecting, installing, and activating Hermes dashboard themes. |
| [`plugin-publisher`](plugins/plugin-publisher) | Published | User plugin that audits Hermes plugins and prepares GitHub publishing commands. |

## Repository Layout

```text
plugins/
  hermes-dashboard-plugins/
  hermes-hackathon-hub/
  hermes-theme-hub/
  plugin-publisher/
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
