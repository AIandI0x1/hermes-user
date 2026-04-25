# Roadmap

This roadmap follows the project workflow: make useful local behavior first,
record validation evidence, then expose public/community surfaces. The guiding
idea is recursive but practical: a plugin for building and submitting Hermes
plugins, inside Hermes.

## 0.1 Hackathon Entry

Status: implemented.

- Dashboard tab loads through the Hermes plugin system.
- Local plugin scan validates this package cleanly.
- Submission composer generates a Discord-ready post.
- Trust panel distinguishes local validation from official certification.
- README, screenshot, license, and manual checklist are present.

Validation:

- `python -m pytest tests/test_plugin_api.py -q`
- `node --check dashboard/dist/index.js`
- `python -m py_compile dashboard/plugin_api.py`
- `GET /api/plugins/hermes-hackathon-hub/scan`

## 0.2 Review Tracker

Goal: turn the hackathon helper into a Discord review companion.

Planned tasks:

- Add a field for Discord review thread URL.
- Persist local submission metadata in a small JSON file under the plugin
  package, not in Hermes core state.
- Add statuses: `draft`, `ready`, `submitted`, `needs_changes`, `accepted`.
- Show review history in the dashboard tab.
- Add tests for metadata loading and invalid metadata recovery.

## 0.2.1 Plugins Section

Goal: make explicit that this project provides the dashboard plugin section
Hermes does not currently ship as a built-in page.

Implemented:

- Show all discovered dashboard plugins with source labels.
- Show plugin cards from the Hermes Agent plugin locations.
- Add route and source chips for each discovered plugin.

Planned tasks:

- Surface hidden/slot-only plugins separately from visible tab plugins.
- Add API health badges for each plugin.
- Add install path and rescan guidance per plugin.

## 0.3 Community Registry Reader

Goal: make the hub useful after the hackathon as a plugin discovery surface.

Planned tasks:

- Define a simple registry JSON schema.
- Read a configured registry URL or local registry file.
- Display reviewed plugins with repo URL, install command, review link, and
  compatibility notes.
- Keep install as a generated command, not an automatic remote execution step.

## 0.4 Certification Verification

Goal: support Hermes team certification without inventing trust locally.

Planned tasks:

- Document the expected signed metadata format.
- Add registry public-key configuration.
- Verify exact plugin name, version, repo URL, and artifact digest.
- Display `Hermes Certified` only when cryptographic verification succeeds.
- Add negative tests for wrong key, wrong digest, and stale version.

## 0.5 Reviewer Mode

Goal: help community reviewers evaluate plugin submissions consistently.

Planned tasks:

- Add a reviewer checklist view.
- Export validation report as Markdown.
- Highlight risky plugin API behavior.
- Surface declared slots, route overrides, backend API routes, and external
  links in one review panel.
