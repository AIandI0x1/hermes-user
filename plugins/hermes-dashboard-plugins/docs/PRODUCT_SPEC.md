# Hermes Hackathon Hub Product Spec

## Summary

Hermes Hackathon Hub is the first plugin inside a dedicated **Plugins** section
for the Hermes dashboard. Hermes exposes dashboard plugin APIs and
plugin-created tabs, but there is no built-in dashboard plugin manager yet.
Hackathon Hub fills that gap: it lists dashboard plugin cards from the Hermes
Agent plugin locations and helps creators prepare, validate, and
submit dashboard plugins to the Discord review workflow. After the hackathon,
the same surface can become a plugin discovery and trust hub for
community-reviewed and Hermes-certified plugins.

## Primary User

The first user is the plugin creator working locally during the hackathon.
They need to move quickly from idea to usable dashboard plugin, publish it to
GitHub, and post a complete submission to Discord.

## Product Promise

If a user has a local Hermes dashboard plugin folder, Hackathon Hub should tell
them what is valid, what is missing, what to fix before submission, and what to
post to Discord.

## Product Voice

The product can be playful about the recursive premise, but the actual workflow
must stay practical and trustworthy. The submission should read as:

> A plugin for building and submitting Hermes plugins, inside Hermes.

It should not imply that the project is already the official Hermes plugin hub.
Use "designed to grow into" or "candidate community hub" language until the
Hermes team explicitly accepts or certifies it.

## MVP Scope

### Included

- Dashboard tab named `Plugins`.
- Backend route that scans user and bundled Hermes Agent candidate plugin folders.
- Card catalog for discovered dashboard plugins.
- Validation report for dashboard plugin package structure.
- Readiness checklist for hackathon submission.
- Discord submission draft generator.
- Direct link to the official Discord submission channel.
- Trust panel with honest certification states.

### Excluded From MVP

- Automatic Discord posting.
- Discord login flow.
- Bot/webhook integration.
- Remote GitHub installation.
- Official certification claims without an official Hermes registry.
- Theme creation workflow.

## User Stories

### Creator Validates A Plugin

As a creator, I can select or scan a local plugin folder and see whether it has
the required dashboard plugin files.

Acceptance criteria:

- The report checks for `dashboard/manifest.json`.
- The report checks that `manifest.name`, `manifest.label`, `manifest.tab.path`,
  and `manifest.entry` exist.
- The report checks that the JS entry file exists.
- The report checks optional `css` and `api` files if declared.
- The report rejects declared file paths that escape the plugin's
  `dashboard/` directory.
- The report distinguishes errors from warnings.

### Creator Prepares A Submission

As a creator, I can enter project metadata and receive a Discord-ready post.

Acceptance criteria:

- The form captures plugin name, short pitch, GitHub repo URL, screenshot or
  video URLs, install command, and notes.
- The generated post includes validation status.
- The generated post includes the official Discord submission channel URL.
- The user manually copies and sends the post.

### Creator Understands Trust Status

As a creator, I can see whether my plugin is unsigned, locally validated, or
officially verified.

Acceptance criteria:

- Local validation never appears as official certification.
- If no official registry is configured, official verification displays
  `Unavailable`.
- The UI explains that Hermes certification requires a public trust source.

## Trust Model

MVP trust states:

- `Unsigned`: no signature metadata found.
- `Locally Validated`: structure and manifest checks passed locally.
- `Official Verification Unavailable`: no official registry or public key is
  configured.

Future trust states:

- `Submitted`: the plugin has a Discord review thread URL.
- `Under Review`: official or community reviewers are evaluating it.
- `Hermes Certified`: signed metadata verifies against the Hermes public key.
- `Deprecated`: official registry marks the plugin as outdated or unsafe.
- `Rejected`: official registry marks the submission as not accepted.

## Data Sources

MVP local sources:

- Hermes dashboard plugin discovery endpoint: `/api/dashboard/plugins`
- Hackathon Hub backend endpoint: `/api/plugins/hermes-hackathon-hub/scan`
- Hackathon Hub backend endpoint:
  `/api/plugins/hermes-hackathon-hub/validate`

Future remote sources:

- Official Hermes plugin registry URL.
- Official Hermes public signing key.
- Discord review thread URLs stored in registry metadata.

## UX Shape

Recommended dashboard layout:

- Top summary card: Plugins section purpose and scan action.
- Left column: discovered dashboard plugins and validation report.
- Right column: submission checklist and trust status.
- Bottom section: Discord post composer and copy/open actions.

## Safety

The plugin must not send Discord messages automatically in v1. Posting to
Discord is representational communication to a third party and should remain a
manual user action unless the product later adds explicit action-time
confirmation and a documented Discord auth flow.
