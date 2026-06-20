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


## 2026-06-12 — local release-notes dry run

- Category: release-management dry run and maintainer workflow
- Issue: #16, `Add local release-notes dry run`
- Changed files:
  - `tools/release_notes_dry_run.py`
  - `tools/maintainer_check.py`
  - `tests/test_core.py`
  - `README.md`
  - `CONTRIBUTING.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/release_notes_dry_run.py --limit 10` returns `PASS`
  - non-git root fixture returns `FAIL_RELEASE_NOTES_DRY_RUN`
  - `PYTHONPATH=src python3 tools/maintainer_check.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/docs_link_check.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/service_template_guard.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Review this local patch. Do not push, post, release, or access credentials."`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft <clean-draft> --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #16 with reviewed validation evidence"`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers can now draft grouped release notes from local git commit summaries while keeping release, tag, package upload, OAuth, paid API, service lifecycle, and credential actions human-gated.
- Next action: keep release preparation as local draft generation unless a maintainer explicitly approves a separate public release action.


## 2026-06-15 — local worktree health check

- Category: maintainer checkout hygiene and fail-closed local diagnostics
- Issue: #17, `Add local worktree health check`
- Changed files:
  - `tools/worktree_health_check.py`
  - `tools/maintainer_check.py`
  - `tests/test_core.py`
  - `README.md`
  - `CONTRIBUTING.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/worktree_health_check.py` returns `PASS`
  - non-git root fixture returns `FAIL_WORKTREE_HEALTH`
  - `PYTHONPATH=src python3 tools/maintainer_check.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/docs_link_check.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/service_template_guard.py` returns `PASS`
  - `PYTHONPATH=src python3 tools/handoff_policy_check.py --body "Review this local patch. Do not push, post, release, or access credentials."`
  - `PYTHONPATH=src python3 tools/public_action_draft_guard.py --draft <clean-draft> --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #17 with reviewed validation evidence"`
  - `PYTHONPATH=src python3 tools/local_adapter_dry_run.py --body "Dummy local-only request. No credentials. No public action."`
  - `PYTHONPATH=src python3 tools/receipt_benchmark.py`
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `git diff --check`
  - tracked/untracked high-confidence secret and private-data scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 after push
- Result: maintainers can now fail closed on broken or partial checkouts before deeper scripts produce confusing errors, while keeping repair, clone, push, release, package, OAuth, paid API, service lifecycle, and credential actions human-gated.
- Next action: keep the checker diagnostic-only; do not turn it into destructive cleanup or automatic repair.


## 2026-06-18 — maintainer-check JSON receipt output

- Category: recurring maintainer evidence and scheduled local-run hygiene
- Issue: #18, `Add maintainer check receipt output`
- Changed files:
  - `tools/maintainer_check.py`
  - `tests/test_core.py`
  - `README.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `PYTHONPATH=src python3 tools/maintainer_check.py --check worktree_health --check docs_link --output <tmp-json>` writes the same JSON payload it prints
  - failure-path output is still written for a non-git-root `worktree_health` failure
  - `PYTHONPATH=src python3 tools/maintainer_check.py --output <artifact-json>` returns `PASS`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v` passes
  - `git diff --check` passes
  - tracked/untracked high-confidence private/secret scan passes
  - `bumblebee selftest` passes
  - `bumblebee scan --root . --emit-summary` returns 0 findings
  - GitHub Actions matrix for Python 3.10, 3.11, and 3.12 passes after push
- Result: scheduled or repeated local maintenance can now persist a machine-readable receipt without relying on shell `tee` or changing the public-action boundary.
- Next action: keep the output receipt local-only; do not let it become a public status poster without a separate explicit approval gate.


## 2026-06-18 — packaged operator command and catch-up aliases

- Category: operator packaging and cross-agent handoff usability
- Issue: local TOM/Jelly operator packaging request
- Changed files:
  - `src/agent_handoff_bus/cli.py`
  - `pyproject.toml`
  - `tests/test_core.py`
  - `README.md`
  - `docs/MAINTAINER_RECIPES.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/docs_link_check.py`
  - `PYTHONPATH=src python3 tools/maintainer_check.py`
  - `git diff --check`
  - tracked/untracked high-confidence private/secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
- Result: the package now installs `handoff-bus` as a first-class command alias, accepts `--source-session` on send, and exposes `catchup`/`inbox` commands so TOM/Jelly-style operator workflows do not need one-off local shell wrappers.
- Next action: keep machine-specific LaunchAgent and private dispatcher tuning outside the public package; promote only portable commands, templates, and documented recipes.


## 2026-06-19 — GitHub Actions Node 24 action compatibility

- Category: CI maintenance and runner compatibility
- Issue: GitHub Actions warning that Node 20 actions were being forced onto Node 24
- Changed files:
  - `.github/workflows/ci.yml`
  - `tests/test_core.py`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/docs_link_check.py`
  - `PYTHONPATH=src python3 tools/maintainer_check.py`
  - `git diff --check`
  - tracked/untracked high-confidence private/secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
- Result: CI now uses `actions/checkout@v6` and `actions/setup-python@v6`, and the test suite checks that the workflow does not regress to the Node 20-era action versions that produced the warning.
- Next action: confirm the pushed workflow run completes without the previous Node 20 deprecation annotation.


## 2026-06-19 — customer/operator installation guide

- Category: installation documentation and operator readiness
- Issue: sales/customer install path needed to avoid one-off tuning
- Changed files:
  - `docs/INSTALL.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
  - `src/agent_handoff_bus/core.py`
  - `tests/test_core.py`
- Verification:
  - `python3 -m pip index versions agent-handoff-bus` currently reports no matching distribution, so README now defaults to source install and points to the install guide instead of implying a published package is available.
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/docs_link_check.py`
  - `PYTHONPATH=src python3 tools/maintainer_check.py`
  - temporary virtual-environment console-script smoke for `handoff-bus doctor`, `send`, `catchup`, and `inbox --plain`
  - `git diff --check`
  - tracked/untracked high-confidence private/secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
- Result: operators now have a dedicated install guide covering source install, pipx-from-Git install, future package-index release checks, isolated smoke tests, reliable receipt smoke tests, persistent local service templates, common commands, troubleshooting, and production/customer readiness checks. `doctor` now treats either `agent-handoff` or `handoff-bus` as a valid CLI on PATH.
- Next action: when a package-index release is actually published, update the guide with the pinned release command and verify it against the published artifact.


## 2026-06-19 — AI-assisted 5-minute install guide

- Category: customer onboarding and AI-assisted installation
- Issue: fastest realistic customer install path should be a bounded local-AI prompt, not a long manual
- Changed files:
  - `docs/AI_ASSISTED_5_MIN_INSTALL.md`
  - `docs/INSTALL.md`
  - `README.md`
  - `ROADMAP.md`
  - `docs/MAINTENANCE_LOG.md`
  - `tests/test_core.py`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/docs_link_check.py`
  - `PYTHONPATH=src python3 tools/maintainer_check.py`
  - temporary virtual-environment smoke of the prompt's core command sequence
  - `git diff --check`
  - tracked/untracked high-confidence private/secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
- Result: customers with a local terminal-capable AI assistant can now paste one bounded prompt that checks prerequisites, installs from Git, creates an isolated smoke-test state, runs `doctor`, `send`, `catchup`, and `inbox --plain`, and returns either `INSTALL_READY` or an exact blocker.
- Next action: if customers repeatedly lack Python/Git, add a separate preflight guide instead of letting the AI install system dependencies silently.

## 2026-06-20 — commercial readiness and release artifact gate

- Category: sales readiness, release packaging, and customer support surface
- Issue: 360° sales audit found self-serve sale blockers around commercial terms, support, pricing, demo material, stale release surface, and artifact checksums
- Changed files:
  - `pyproject.toml`
  - `.github/workflows/ci.yml`
  - `TERMS.md`
  - `PRIVACY.md`
  - `SUPPORT.md`
  - `CHANGELOG.md`
  - `docs/PRICING_AND_OFFER.md`
  - `docs/DEMO_AND_FAQ.md`
  - `tools/build_release_artifacts.py`
  - `README.md`
  - `docs/INSTALL.md`
  - `ROADMAP.md`
  - `tests/test_core.py`
  - `docs/MAINTENANCE_LOG.md`
- Verification:
  - `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
  - `PYTHONPATH=src python3 -m unittest discover -s tests -v`
  - `PYTHONPATH=src python3 tools/docs_link_check.py`
  - `PYTHONPATH=src python3 tools/maintainer_check.py`
  - `python tools/build_release_artifacts.py --dist-dir dist`
  - wheel/sdist `twine check`
  - wheel install smoke with `handoff-bus doctor/send/catchup/inbox --plain`
  - `git diff --check`
  - tracked/untracked high-confidence private/secret scan
  - `bumblebee selftest`
  - `bumblebee scan --root . --emit-summary`
- Result: the repository now has customer-facing commercial wrapper docs, support/refund policy, pricing hypotheses, demo/FAQ, changelog, version `0.2.0`, and a local release artifact builder that emits wheel/sdist checksums without uploading or performing public actions.
- Next action: after CI passes, create a GitHub release for `v0.2.0` with artifacts and checksums; publish to PyPI only after a separate package-index approval and credential check.


## Earlier baseline

- Initial public release established the local-first handoff bus, dependency-free Python package, safety model, MIT license, CI workflow, roadmap, contributing guide, and security policy.
- Follow-up hardening added HTTP API tests, reliable-send timeout behavior, and maintainer gate coverage.
