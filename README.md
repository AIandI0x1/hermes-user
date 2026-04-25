# Hermes User Plugins

User plugin collection for Hermes Agent dashboard extensions, tools, and
supporting plugin workflows.

This repository is separate from upstream `hermes-agent` source code. Plugins
published here are user-owned packages intended to be installed into a Hermes
user plugin directory, for example:

```text
~/.hermes/plugins/<plugin-name>
```

## Plugins

| Plugin | Status | Description |
| --- | --- | --- |
| [`hermes-plugin-publisher`](plugins/hermes-plugin-publisher) | Published | Dashboard plugin for preparing, checking, and publishing Hermes user plugins to GitHub. |

## Repository Layout

```text
plugins/
  hermes-plugin-publisher/
```

Each plugin should own its frontend, docs, tools, skills, and tests inside its
own plugin folder. User plugin work should not require direct edits to upstream
Hermes Agent core files.

## Publishing Rule

The canonical destination format for plugins in this repository is:

```text
AIandI0x1/hermes-user/plugins/<plugin-name>
```

Before publishing, run the plugin publisher readiness plan and review the secret
scan, destination path, repo visibility, and generated GitHub commands.
