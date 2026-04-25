# Hermes Plugin Publisher

User plugin for preparing Hermes plugins for GitHub publication.

It provides:

- `hermes_plugin_publish_plan` tool
- `hermes-plugin-publisher:plugin-publisher` skill

The tool audits a plugin folder, scans text files for common secret patterns with redacted output, checks git state, and returns explicit `git` / `gh` commands. It does not create repositories or push by itself.

In the dashboard:

- **Publish destination path** is the user-plugin collection destination used by `Confirm publish`, for example `AIandI0x1/hermes-user/plugins/hermes-dashboard-plugins`.
- **Catalog reference path** is the public user-plugin collection path for humans and future registry work, for example `AIandI0x1/hermes-user/plugins/hermes-dashboard-plugins`.

User plugins should not be published into a `hermes-agent` source checkout,
because that can conflict with upstream Hermes Agent history.

Publishing to GitHub transmits files to a third party, so repo creation and push commands should be run only after explicit confirmation.
