# Plugin Publisher

Self-contained Hermes user plugin for preparing plugins for GitHub publication.

It provides:

- `hermes_plugin_publish_plan` tool
- `plugin-publisher:plugin-publisher` skill

The tool audits a plugin folder, scans text files for common secret patterns with redacted output, checks git state, and returns explicit `git` / `gh` commands. Dashboard publishing requires explicit confirmation before creating repositories or pushing.

In the dashboard:

- **Publish destination path** is the user-plugin collection destination used by `Confirm publish`, for example `AIandI0x1/hermes-user/plugins/hermes-dashboard-plugins`.
- **Catalog reference path** is the public user-plugin collection path for humans and future registry work, for example `AIandI0x1/hermes-user/plugins/hermes-dashboard-plugins`.
- Successful publishes update the collection repository `README.md` automatically so the plugin table and repository layout stay current.
- Readiness plans check that a screenshot file or video link is present before hackathon-style publication.

User plugins should not be published into a `hermes-agent` source checkout,
because that can conflict with upstream Hermes Agent history.

Publishing to GitHub transmits files to a third party, so repo creation and push commands should be run only after explicit confirmation.
