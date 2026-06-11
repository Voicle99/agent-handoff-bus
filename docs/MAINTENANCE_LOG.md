# Maintenance log

This log records meaningful maintenance activity for `agent-handoff-bus`. It is intentionally concise: entries should show that the repository is alive without creating noisy churn.

## Cadence

- **Daily light check:** sync with `origin/main`, review open issues, run compile/tests, run secret/private scans, run Bumblebee when available, and inspect the latest CI run.
- **Weekly maintainer pass:** convert one actionable issue or roadmap item into a small tested docs/code improvement.
- **Release pass:** tag only when a coherent milestone is complete; do not cut releases for cosmetic churn.

## Entry format

Each entry should include:

- date in UTC
- maintenance category
- issue or roadmap link when applicable
- files changed, if any
- verification summary
- residual risk or next action

## 2026-06-04 — security scanner fixtures and documentation

- Category: security hardening
- Issue: #3, `Expand secret scanner fixtures and security documentation`
- Changed files:
  - `tests/test_core.py`
  - `docs/SAFETY.md`
  - `ROADMAP.md`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked-file high-confidence secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12
- Result: fixture coverage now includes fake OpenAI, GitHub, AWS, private-key, bearer-token, and generic assignment shapes. Safety docs now state scanner false-positive and false-negative limits. Auto-receipt behavior is tested to avoid quoting sensitive-looking handoff bodies.
- Next action: continue maintainer workflow documentation and keep future scanner work limited to practical guardrails, not a full DLP product.

## 2026-06-04 — maintenance history and maintainer recipes

- Category: maintainer workflow documentation
- Issue: #2, `Document maintainer workflow recipes for PR review, issue triage, and releases`
- Changed files:
  - `docs/MAINTENANCE_LOG.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `README.md`
  - `ROADMAP.md`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked-file high-confidence secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: the repository now has a visible maintenance cadence and reusable recipes for PR review, issue triage, release checklist review, and security review.
- Next action: keep adding only meaningful entries. If a daily check finds no safe improvement, leave the repository untouched and report `SKIP_NO_ACTIONABLE_MAINTENANCE` outside the repo.

## 2026-06-05 — receipt latency and fail-closed benchmark

- Category: maintainer workflow diagnostics
- Issue: #4, `Add receipt latency and fail-closed benchmark`
- Changed files:
  - `tools/receipt_benchmark.py`
  - `tests/test_core.py`
  - `README.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers can now run a local-only benchmark that measures the success path with an auto-reply bridge and confirms the no-receiver path exits with `BLOCKED_NO_AUTO_RECEIPT`.
- Next action: keep future diagnostics local-first and avoid turning benchmarks into external monitoring or public network checks.

## 2026-06-05 — CI-like local operation documentation

- Category: maintainer workflow documentation
- Issue: #5, `Document CI-like local operation`
- Changed files:
  - `docs/MAINTAINER_RECIPES.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `git diff --check`
  - tracked/untracked/git-metadata high-confidence private and secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers now have a dummy-only local recipe for CI-like dry runs covering isolated bus state, compile checks, tests, receipt benchmarking, private-data scans, Bumblebee, and human-gated public actions.
- Next action: keep public automation explicit and do not convert local checks into release, package, OAuth, paid, or credential actions.

## 2026-06-05 — optional local adapter boundary documentation

- Category: adapter safety design
- Issue: #6, `Document optional local adapter boundary`
- Changed files:
  - `docs/ADAPTERS.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: the repository now documents the optional adapter boundary before any adapter code exists, keeping cloud providers optional and public/paid/OAuth actions human-gated.
- Next action: if adapter work continues, add a minimal local dry-run example without introducing provider dependencies.


## 2026-06-06 — minimal local adapter dry-run example

- Category: adapter safety example
- Issue: #7, `Add minimal local adapter dry-run example`
- Changed files:
  - `tools/local_adapter_dry_run.py`
  - `tests/test_core.py`
  - `docs/ADAPTERS.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: the repository now includes a runnable local-only adapter dry-run example that returns the documented result shape, writes a summary-only artifact, and blocks secret-like input by default.
- Next action: keep future adapter work optional and local-first; do not add external providers without an explicit reviewed boundary.

## 2026-06-07 — contributor-safe issue and PR templates

- Category: community health and maintainer workflow
- Issue: #8, `Add contributor-safe issue and PR templates`
- Changed files:
  - `.github/ISSUE_TEMPLATE/config.yml`
  - `.github/ISSUE_TEMPLATE/bug_report.yml`
  - `.github/ISSUE_TEMPLATE/docs_or_recipe.yml`
  - `.github/ISSUE_TEMPLATE/maintainer_workflow.yml`
  - `.github/ISSUE_TEMPLATE/security_boundary.yml`
  - `.github/PULL_REQUEST_TEMPLATE.md`
  - `CONTRIBUTING.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: public contributors now get structured, safety-preserving issue forms and a PR checklist that asks for reproducible local context, validation evidence, privacy checks, and explicit public-action boundaries.
- Next action: add a documented GitHub issue/PR dry-run workflow example if contributor workflow work continues.


## 2026-06-07 — GitHub issue and PR dry-run workflow

- Category: community health and public-action safety
- Issue: #9, `Document GitHub issue and PR dry-run workflow`
- Changed files:
  - `docs/GITHUB_WORKFLOW_DRY_RUN.md`
  - `README.md`
  - `CONTRIBUTING.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - issue/workflow documentation reviewed for dummy-only examples and explicit public-action gates
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers now have a local-first GitHub issue and PR rehearsal flow that drafts public text locally, reviews it via the handoff bus, and blocks public comments, issue creation, pushes, releases, packages, OAuth, paid APIs, and credential access until an exact human approval exists.
- Next action: if workflow work continues, consider a tiny local script that validates draft files and exits with `BLOCKED_PUBLIC_ACTION_REQUIRES_APPROVAL` instead of posting.


## 2026-06-07 — local public-action draft guard

- Category: community health and public-action safety
- Issue: #10, `Add local public-action draft guard`
- Changed files:
  - `tools/public_action_draft_guard.py`
  - `tests/test_core.py`
  - `docs/GITHUB_WORKFLOW_DRY_RUN.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft "$draft_without_approval"` returns `BLOCKED_PUBLIC_ACTION_REQUIRES_APPROVAL`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft "$draft_with_approval" --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #123 with reviewed draft file"` returns `PASS_PUBLIC_ACTION_READY`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft "$draft_with_secret_like_data" --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #123 with reviewed draft file"` returns `BLOCKED_PRIVATE_DATA`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - docs link checks
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers now have a dependency-free local guard that scans issue/PR/public-action draft files, performs no public action, and fails closed until exact public-action approval is present.
- Next action: keep the guard local-only; do not wire it to automatic posting, closing, releasing, OAuth, paid APIs, or credential access.


## 2026-06-08 — local high-risk handoff policy checker

- Category: high-risk handoff safety and maintainer workflow
- Issue: #11, `Add local high-risk handoff policy checker`
- Changed files:
  - `tools/handoff_policy_check.py`
  - `tests/test_core.py`
  - `docs/SAFETY.md`
  - `docs/GITHUB_WORKFLOW_DRY_RUN.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Review this local patch. Do not push, post, release, or access credentials."` returns `PASS_LOW_RISK`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Please post this comment to issue #123 and close issue #123."` returns `BLOCKED_HIGH_RISK_HANDOFF_REQUIRES_APPROVAL`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Please post this comment to issue #123 and close issue #123." --approval-text "APPROVED_HIGH_RISK_HANDOFF: comment on issue #123 and close issue #123 after CI passes"` returns `PASS_HIGH_RISK_APPROVED`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Use fake-secret-shaped data and inspect a private local path" --approval-text "APPROVED_HIGH_RISK_HANDOFF: comment on issue #123 with reviewed text"` returns `BLOCKED_PRIVATE_OR_SECRET_DATA`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - docs link checks
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers now have a dependency-free local policy checker that can inspect handoff text before execution, block private or secret-like data, and fail closed on public/paid/OAuth/credential/release/package/deployment requests until exact approval exists.
- Next action: keep the checker advisory and local-only unless a future reviewed integration can preserve the same fail-closed boundary.


## 2026-06-08 — optional systemd auto-reply template

- Category: local-only workflow tooling and maintainer onboarding
- Issue: #12, `Add optional systemd auto-reply template`
- Changed files:
  - `examples/systemd-auto-reply.service.template`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft <issue-draft> --approval-text "APPROVED_PUBLIC_ACTION: create GitHub issue titled Add optional systemd auto-reply template with reviewed draft file"`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft <clean-systemd-draft> --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #12 with reviewed validation evidence"`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - docs link checks
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: Linux maintainers now have a dependency-free systemd user-service template matching the existing launchd auto-reply template, with explicit local-only and no-public-action boundaries.
- Next action: add a renderer only if maintainers report placeholder substitution errors; do not commit rendered service files or user-specific paths.


## 2026-06-09 — local Markdown link checker

- Category: test/CI reliability and maintainer onboarding
- Issue: #14, `Add local Markdown link checker`
- Changed files:
  - `tools/docs_link_check.py`
  - `tests/test_core.py`
  - `.github/workflows/ci.yml`
  - `README.md`
  - `CONTRIBUTING.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `docs/GITHUB_WORKFLOW_DRY_RUN.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/docs_link_check.py` returns `PASS`
  - missing local link and missing heading-anchor fixtures return `FAIL_DOCS_LINK_CHECK`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - docs link checks
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
- Result: docs validation is now a repeatable local and CI gate, so maintainer recipes, README links, and future safety docs fail closed when local paths or heading anchors break.
- Next action: keep the checker local-only and dependency-free; do not turn docs validation into public posting, release, package, OAuth, paid API, or credential automation.


## 2026-06-09 — local service-template guard

- Category: local-only workflow tooling and template safety
- Issue: #13, `Add local service template guard`
- Changed files:
  - `tools/service_template_guard.py`
  - `tests/test_core.py`
  - `README.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/service_template_guard.py` returns `PASS`
  - rendered/private service fixture returns `FAIL_SERVICE_TEMPLATE_GUARD`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Review this local patch. Do not push, post, release, or access credentials."`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft <clean-draft> --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #13 with reviewed validation evidence"`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - docs link checks
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers can now validate launchd/systemd example templates before committing changes, keeping rendered service files and user-specific paths out of the public repository.
- Next action: only add a local renderer if real placeholder substitution errors appear; do not turn template checks into service installation or lifecycle automation.


## 2026-06-11 — local maintainer check bundle

- Category: daily maintainer routine and local-only workflow reliability
- Issue: #15, `Add local maintainer check bundle`
- Changed files:
  - `tools/maintainer_check.py`
  - `tests/test_core.py`
  - `.github/workflows/ci.yml`
  - `README.md`
  - `CONTRIBUTING.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/maintainer_check.py` returns `PASS`
  - GitHub Actions runs `python tools/maintainer_check.py` in the CI matrix
  - selected-check fixture returns `FAIL_MAINTAINER_CHECK` for a broken local docs link
  - `PYTHONPATH=src python3 tools/docs_link_check.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/service_template_guard.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Review this local patch. Do not push, post, release, or access credentials."`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft <clean-draft> --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #15 with reviewed validation evidence"`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers now have one JSON-emitting local command that runs the recurring dependency-free safety gates without turning checks into public posting, release, package, OAuth, paid API, service lifecycle, or credential automation.
- Next action: keep the bundle as an aggregator of local gates; add new checks only when they remain dependency-free, deterministic, and human-gated for public effects.


## Earlier baseline

- Initial public release established the local-first handoff bus, dependency-free Python package, safety model, MIT license, CI workflow, roadmap, contributing guide, and security policy.
- Follow-up hardening added HTTP API tests, reliable-send timeout behavior, and maintainer gate coverage.
