---
name: plugin-publisher
description: "Audit and publish Hermes user plugins to GitHub with a redacted secret-risk scan, git readiness checks, and explicit gh/git commands. Use before sharing a plugin repo publicly or submitting it to Discord."
version: 0.1.0
author: 0x1-Main
license: MIT
metadata:
  hermes:
    tags: [Plugins, GitHub, Publishing, Security, Hackathon]
---

# Plugin Publisher

Use this skill when preparing a Hermes plugin for GitHub release.

## Workflow

1. Run `hermes_plugin_publish_plan` against the plugin folder.
2. Review the redacted secret-risk scan.
3. Check publish readiness warnings.
4. Only after explicit user confirmation, run the generated `git` and `gh` commands.

## Dashboard Terms

- Publish destination path: the `owner/repo/path` GitHub destination that will be created or pushed to.
- Catalog reference path: the public user-plugin collection path shown for registry/reference purposes.
- Default destination: `owner/hermes-user/plugins/<plugin-name>`, not `owner/hermes-agent/plugins/<plugin-name>`.

## Safety Rules

- Do not publish automatically.
- Treat GitHub repo creation and push as external transmission of files.
- Confirm at action time before `gh repo create`, `git push`, or any command that changes GitHub state.
- Never print full detected secret values; use the redacted findings from the tool.

## Example

```json
{
  "plugin_path": "~/.hermes/plugins/hermes-hackathon-hub",
  "repo_name": "hermes-hackathon-hub",
  "visibility": "public"
}
```
