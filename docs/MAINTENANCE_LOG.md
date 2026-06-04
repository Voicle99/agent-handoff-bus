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

## Earlier baseline

- Initial public release established the local-first handoff bus, dependency-free Python package, safety model, MIT license, CI workflow, roadmap, contributing guide, and security policy.
- Follow-up hardening added HTTP API tests, reliable-send timeout behavior, and maintainer gate coverage.
