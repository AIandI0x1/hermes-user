# Security

Hermes Hackathon Hub is a local dashboard plugin helper. It scans dashboard
plugin package structure and generates a review post draft.

## Supported Model

- Local validation is not official Hermes certification.
- Official certification requires a Hermes-controlled registry and public
  signing key.
- Discord posting is manual in this MVP.
- Backend routes run inside the local Hermes dashboard process.

## Sensitive Data Policy

Do not commit:

- `.env` files
- API credentials
- Discord credentials
- browser session data
- local Hermes config files
- private keys
- screenshots containing private workspace or account data

Before publishing, run the repository's current leak-scan command from the
maintainer checklist and manually review any matches before pushing.

## Reporting Issues

For public issues, open a GitHub issue with reproduction steps.

For private security-sensitive reports, use the maintainer's preferred private
contact channel once it is listed in the GitHub repository.
