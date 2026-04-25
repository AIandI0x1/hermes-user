# Dashboard Frontend Ownership

## Rule

Dashboard design changes made by a plugin must live in that plugin's own
folder.

Each plugin that changes the Hermes dashboard owns its own frontend surface:

```text
~/.hermes/plugins/<plugin-name>/
└── dashboard/
    ├── manifest.json
    ├── plugin_api.py        # optional backend API
    └── dist/
        ├── index.js
        └── style.css
```

Hermes core should provide generic dashboard plugin loading and generic hooks.
It should not contain plugin-specific routes, labels, cards, buttons, modals,
icons, or styling.

## Current Ownership

- `hermes-dashboard-plugins` owns `/plugins`, plugin cards, enablement controls,
  catalog styling, and this rule.
- `hermes-plugin-publisher` owns `/plugin-publisher`, publish buttons, publish
  modal, publish API, and publisher styling.
- `hermes-hackathon-hub` owns `/hackathon-hub`, Discord submission workflow,
  roadmap/docs UI, and hub styling.

## Enforcement

The local checker is:

```text
scripts/enforce_frontend_ownership.py
```

It verifies:

- every dashboard plugin declares frontend/backend files inside its own
  `dashboard/` folder
- declared `entry`, `css`, and `api` files exist
- declared dashboard files do not escape the plugin folder through `..` or
  absolute paths
- core dashboard source files do not hardcode discovered plugin-owned routes

Run it before publishing:

```bash
python scripts/enforce_frontend_ownership.py
```

The dashboard API also exposes the current rule status:

```text
GET /api/plugins/hermes-dashboard-plugins/rules/frontend-ownership
```

## If The Rule Fails

Move plugin-specific UI code into the owning plugin's `dashboard/` folder.

Only change Hermes core when the missing capability is generic, reusable plugin
infrastructure. Examples of acceptable core work are a new generic dashboard
extension hook, a generic plugin manifest field, or a loader bug fix.
