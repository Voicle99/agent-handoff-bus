# Security Policy

## Supported versions

The project is currently in an early `0.x` stage. Security fixes target the latest commit on `main` until versioned maintenance branches are introduced.

## Reporting a vulnerability

Please do **not** include API keys, credentials, private logs, customer data, or private chat transcripts in public issues.

Preferred reporting path:

1. Use GitHub's private vulnerability reporting or security advisory flow if it is available for this repository.
2. If private reporting is not available, open a public issue with a sanitized summary only.
3. Include enough detail to reproduce the behavior without exposing real secrets.

A good report includes:

- affected command or module
- expected behavior
- actual behavior
- minimal reproduction using fake tokens or dummy data
- whether the issue could allow secret disclosure, public network exposure, unsafe ACK/completion, or unintended public/paid action

## Security model

`agent-handoff-bus` is a local coordination primitive. It does not grant authority.

A handoff must not be treated as approval for:

- public posting, upload, publishing, deployment, or email/DM sending
- paid API calls or purchases
- OAuth/login/account-permission changes
- credential access, token extraction, keyring reads, or password handling
- private scraping or bypassing platform permissions

## Areas that need extra review

- secret-like content scanner behavior
- localhost-only HTTP server bind checks
- auto-receipt logic, because a receipt is not task completion
- reliable-send timeout behavior and fail-closed status
- path handling for body files and local state
- future adapters that connect to external tools or model providers

## Maintainer response goal

For credible security reports, the maintainer goal is to acknowledge the report, reproduce the issue, and publish a fix or mitigation note as soon as practical. Early-stage response times may vary, but security issues take priority over feature work.
