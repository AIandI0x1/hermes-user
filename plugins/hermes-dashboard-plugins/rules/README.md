# Rules

This folder contains local rules owned by `hermes-dashboard-plugins`.

Rules in this plugin are not Hermes core patches. They document and enforce
how dashboard plugins should behave from the plugin manager's point of view.

## Active Rules

- [Dashboard frontend ownership](frontend-ownership.md)

## Run

```bash
python scripts/enforce_frontend_ownership.py
```

Machine-readable output:

```bash
python scripts/enforce_frontend_ownership.py --json
```
