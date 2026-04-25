# Plugin Lifecycle

This lifecycle describes how a Hermes user plugin moves from local idea to
published package.

## 1. Create

Create a single plugin folder:

```text
~/.hermes/plugins/<plugin-name>
```

Keep all frontend, backend API, tools, skills, docs, tests, screenshots, and
metadata inside that folder.

## 2. Describe

Add:

- `plugin.yaml`
- `README.md`
- `LICENSE`

Dashboard plugins add:

```text
dashboard/manifest.json
dashboard/dist/index.js
dashboard/dist/style.css
```

Theme plugins add:

```text
theme/<theme-name>.yaml
```

## 3. Validate

Run local checks before publishing:

- Manifest and entry file validation.
- JavaScript syntax checks for dashboard bundles.
- Python compile checks for dashboard APIs.
- Focused pytest suite.
- Secret scan.
- Screenshot or video evidence check.
- Frontend ownership rule when the plugin changes dashboard UI.

## 4. Review Boundaries

Confirm:

- No plugin-specific Hermes core edits are required.
- No personal paths appear in UI, screenshots, or docs.
- No credentials or local runtime artifacts are included.
- Trust wording does not imply official Hermes certification.

## 5. Publish

The canonical user plugin collection destination is:

```text
AIandI0x1/hermes-user/plugins/<plugin-name>
```

Use `plugin-publisher` to prepare the plan and generated GitHub commands. Repo
creation and push operations require explicit confirmation.

## 6. Maintain

For later updates:

- Keep screenshots current.
- Update README and plugin metadata when behavior changes.
- Add regression tests for fixed bugs.
- Keep origin and trust metadata conservative.
- Avoid drift between local installed plugin folders and the public collection.
