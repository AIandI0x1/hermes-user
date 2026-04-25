# Contributing

Hermes Hackathon Hub uses a small, evidence-first workflow adapted from the
0x1 / Orchestra operating style.

## Workflow

1. Keep work scoped to one coherent change.
2. Make the intended behavior visible in docs or tests before calling it ready.
3. Run verification locally.
4. Commit only files that belong to the change.
5. Treat GitHub as the public mirror and collaboration surface, not as the
   only source of review truth. Discord review links belong in submission
   metadata and release notes.

## Branch Names

Use lowercase, hyphenated branch names:

```text
feature/plugin-registry
fix/path-validation
docs/review-workflow
release/v0.1.0
```

Avoid spaces, uppercase words, personal names, or temporary chat labels in
published branch names.

## Commit Style

Use short conventional-style subjects:

```text
feat: add plugin registry panel
fix: reject unsafe dashboard paths
docs: document discord review flow
test: cover invalid manifest validation
```

## Required Checks

Run these before publishing changes:

```bash
python -m pytest tests/test_plugin_api.py -q
node --check dashboard/dist/index.js
python -m py_compile dashboard/plugin_api.py
curl http://127.0.0.1:9119/api/plugins/hermes-hackathon-hub/scan
```

The scan should report:

```text
ok: true
errors: []
warnings: []
```

## Review Boundaries

- Do not add automatic Discord posting without an explicit, documented review
  and confirmation flow.
- Do not claim official Hermes certification from local checks.
- Do not add broad filesystem scanning. Keep scan roots explicit and local.
- Do not commit generated Python caches, local dashboard state, credentials,
  or personal environment files.

