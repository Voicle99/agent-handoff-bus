# Roadmap

`agent-handoff-bus` is intentionally small: a local-first handoff bus that helps AI-assisted maintainers coordinate work without UI paste, focus stealing, or implicit public actions.

This roadmap focuses on maintainer workflows: pull request review, issue triage, release management, and security review.

## v0.1.x — harden the core

- Keep the core dependency-free and standard-library only.
- [x] Add tests for the localhost HTTP API.
- [x] Add tests for reliable-send timeout and receipt acknowledgment behavior.
- [x] Improve secret-like content detection with more fixture coverage.
- [x] Add structured examples for common maintainer flows:
  - [x] PR review handoff
  - [x] issue triage handoff
  - [x] release checklist handoff
  - [x] security review handoff

## v0.2.x — maintainer workflow recipes

- Publish reusable recipes for:
  - triaging new issues into `bug`, `question`, `security`, or `maintenance`
  - preparing release notes from local commit summaries
  - coordinating multi-agent review without sharing private credentials
  - verifying that public/post/publish actions remain human-gated
- [x] Add a small local benchmark/check script for receipt latency and fail-closed behavior.
- [x] Add documentation for operating the bus in CI-like local environments.

## v0.3.x — adapters and integrations

- Add optional adapter interfaces for local LLM tools without making any cloud provider mandatory.
  - [x] Document the optional local adapter boundary.
  - [x] Add a minimal local adapter dry-run example.
- Add optional launchd/systemd templates generated from local configuration.
- Add a stricter policy layer for high-risk handoffs.
- Explore GitHub issue/PR workflow examples while keeping public writes explicit and human-approved.
  - [x] Add contributor-safe issue and PR templates.
  - [x] Add a documented GitHub issue/PR dry-run workflow example.
  - [x] Add a local public-action draft guard for issue and PR text.

## Non-goals

- No credential extraction.
- No private browser/session scraping.
- No default public posting, deployment, publishing, email, or paid API actions.
- No non-loopback API bind by default.

## Maintenance principles

1. Local-first by default.
2. Receipts are delivery signals, not task completion.
3. Public or paid actions require explicit human approval.
4. Safety gates should be easy to test.
5. The project should stay useful for maintainers with different levels of engineering experience.
