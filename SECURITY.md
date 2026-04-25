# Security

This repository is a public user plugin collection for Hermes Agent. Treat every
plugin as local executable code until reviewed.

## Reporting Security Issues

Do not open a public issue for secrets, credential leaks, or exploitable bugs.
Use a private GitHub security advisory for this repository when available, or
contact the repository owner through GitHub.

Include:

- Affected plugin path.
- Impact and reproduction steps.
- Whether credentials, private paths, screenshots, or logs were exposed.
- Suggested mitigation if known.

## Secret Handling

Plugins must not commit:

- API keys, OAuth tokens, passwords, cookies, or private keys.
- Local `.env` files or Hermes runtime config containing credentials.
- Personal filesystem paths in screenshots or generated docs.
- Logs, caches, session stores, or database files.

Use redacted output when documenting scanner results.

## Plugin Trust Model

Local validation is not official Hermes certification.

Until Hermes publishes an official plugin registry and signing key, this
collection uses conservative trust language:

- `local`: package exists on disk and can be inspected.
- `locally_validated`: local checks passed.
- `unsigned`: no official signature is available.
- `official_verification_unavailable`: Hermes official verification is not yet
  available for this package.

Do not claim a plugin is certified, signed, or endorsed by the Hermes team
unless that claim can be verified against an official Hermes trust root.

## External Actions

Plugins that create repositories, push to GitHub, post to Discord, upload files,
or transmit data to third parties must show the destination and require explicit
confirmation before the action.

## Local Dashboard Routes

Dashboard routes under `http://127.0.0.1:9119` are loopback-only development
and runtime URLs. They are only reachable from the local machine running Hermes
dashboard and should not be presented as public contact, support, webhook, or
remote service URLs.
