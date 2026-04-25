# Project Workflow

This project borrows the useful parts of the 0x1 / Orchestra workflow while
remaining a small standalone plugin repository.

## Operating Principles

1. Coherence beats visible churn.
2. GitHub is the public mirror; local validation and Discord review carry the
   submission evidence.
3. Do not claim certification without a Hermes-controlled trust root.
4. Do not automate third-party posting in the MVP.
5. Keep names normalized for GitHub and install paths.
6. Keep the recursive premise clear: useful first, funny second.

## Naming

Canonical project name:

```text
hermes-hackathon-hub
```

GitHub repository:

```text
AIandI0x1/hermes-hackathon-hub
```

Dashboard manifest name:

```text
hermes-hackathon-hub
```

Install folder:

```text
~/.hermes/plugins/hermes-hackathon-hub
```

Avoid alternate names such as `HackathonHub`, `Hermes Plugin Hub`, or
`discord-hub` in filenames, branch names, package names, or install commands.
Use those only as descriptive prose when needed.

## Validation Before Publishing

Run:

```bash
python -m pytest tests/test_plugin_api.py -q
node --check dashboard/dist/index.js
python -m py_compile dashboard/plugin_api.py
curl http://127.0.0.1:9119/api/plugins/hermes-hackathon-hub/scan
```

Then check the browser route after selecting **Plugins** in the dashboard
navigation:

```text
http://127.0.0.1:9119/plugins
```

Expected:

- plugin page renders
- scan reports `ok: true`
- no errors or warnings in the validation report
- submission draft is visible
- trust status is `Locally Validated`, not official certification

## Publish Flow

1. Commit all intended files.
2. Run validation commands.
3. Run a public-leak scan.
4. Create or update the public GitHub repository.
5. Open the dashboard, copy the generated Discord draft, and manually submit
   it in the official channel.
6. Record the Discord review URL in release notes.
