# Changelog

All notable customer-facing changes are recorded here.

## v0.2.0 — 2026-06-20

### Added

- Packaged `handoff-bus` operator command alias.
- `catchup` and `inbox` commands for low-friction pending handoff review.
- `--source-session` alias for portable send commands.
- Customer/operator installation guide.
- AI-assisted 5-minute install guide.
- GitHub Actions Node 24-compatible action versions.
- Release artifact build/checksum helper.
- Commercial readiness docs: terms, privacy, support, pricing/offer, demo/FAQ.

### Changed

- `doctor` now accepts either `agent-handoff` or `handoff-bus` on PATH as a valid CLI check.
- README install flow now defaults to source install until package-index release is actually visible.

### Validation

- Python 3.10, 3.11, and 3.12 CI.
- Local wheel/sdist build and wheel install smoke.
- Docs link check.
- Maintainer check bundle.
- Bumblebee scan with zero findings at release-readiness audit time.

## v0.1.0 — 2026-06-03

Initial public release:

- Local-first SQLite/file-backed handoff bus.
- CLI for send, latest, show, list, ack, watch, doctor, and serve.
- Optional localhost API.
- Auto-receipt bridge and reliable sender.
- Secret-like content scanner.
- Safety, maintainer, and adapter documentation.
