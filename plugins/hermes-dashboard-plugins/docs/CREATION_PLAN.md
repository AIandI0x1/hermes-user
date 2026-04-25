# Hermes Hackathon Hub Creation Plan

## Objective

Create a publishable Hermes dashboard plugin that begins as a hackathon
submission assistant and can later become the Discord-centered plugin hub for
review, discovery, and certification.

## Phase 0: Planning Package

Owner: creator

Deliverables:

- Product spec.
- Implementation plan.
- Discord review protocol.
- README.
- Empty screenshot folder for later submission assets.

Exit criteria:

- A new contributor can understand the plugin goal without reading chat
  history.
- The plan clearly separates MVP behavior from future certification behavior.

## Phase 1: Static Dashboard Plugin

Owner: implementation agent

Deliverables:

- `dashboard/manifest.json`
- `dashboard/dist/index.js`
- `dashboard/dist/style.css`
- Static plugin tab rendered inside Hermes Dashboard.

User-visible behavior:

- Dashboard navigation shows `Plugins`.
- Page explains plugin purpose.
- Page shows mock sections for scan, validation, trust, and Discord composer.

Exit criteria:

- Plugin loads through `hermes dashboard`.
- No console errors.
- Screenshot can be captured.

## Phase 2: Backend Validation API

Owner: implementation agent

Deliverables:

- `dashboard/plugin_api.py`
- `GET /api/plugins/hermes-hackathon-hub/scan`
- `POST /api/plugins/hermes-hackathon-hub/validate`

User-visible behavior:

- Plugin lists local dashboard plugins discovered under configured scan roots.
- Plugin validates a selected plugin package.
- Plugin shows errors and warnings separately.

Exit criteria:

- API handles missing folders without crashing.
- API avoids scanning broad sensitive locations by default.
- Validation works against the plugin's own folder and bundled Hermes examples.

## Phase 3: Submission Composer

Owner: implementation agent

Deliverables:

- Metadata form in dashboard UI.
- Generated Discord post preview.
- Copy button.
- Button/link that opens the official Discord submission channel.

User-visible behavior:

- Creator can fill in repo URL, screenshots, install command, and pitch.
- Generated post includes validation result and trust status.
- Creator manually sends the post in Discord.

Exit criteria:

- No Discord credentials are needed.
- No automatic posting occurs.
- Generated post is usable as a hackathon submission.

## Phase 4: Trust And Certification Readiness

Owner: implementation agent

Deliverables:

- Trust status panel.
- Local metadata fields for future certification:
  - plugin name
  - version
  - repo URL
  - review thread URL
  - signature URL
  - registry entry URL
- Clear explanation of unavailable official verification.

User-visible behavior:

- Unsigned plugins are labeled honestly.
- Locally valid plugins do not appear certified.
- Future certification flow is discoverable.

Exit criteria:

- Trust UI is useful now and does not overclaim.
- Registry format is documented but not required.

## Phase 5: Publish Package

Owner: creator

Deliverables:

- GitHub repository.
- README install instructions.
- Screenshots or video.
- License.
- Discord submission post.

Exit criteria:

- A fresh Hermes user can clone or copy the plugin into
  `~/.hermes/plugins/hermes-hackathon-hub`.
- Dashboard can rescan and show the plugin tab.
- README includes the official Discord submission channel and manual submission flow.

## Future Roadmap

- Official registry support.
- Hermes public key verification.
- Discord review thread tracking.
- Community plugin browsing.
- Plugin install command generator.
- Compatibility checks by Hermes version.
- Reviewer mode for validating submitted plugins.
