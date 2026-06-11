# Contributing

Thanks for your interest in improving `agent-handoff-bus`.

This project is for local-first AI agent coordination. Contributions should preserve the core safety boundary: a handoff is delivery/coordination, not permission to perform public, paid, credential, OAuth, or account actions.

## Development setup

```bash
git clone https://github.com/Voicle99/agent-handoff-bus.git
cd agent-handoff-bus
python3 -m pip install -e .
```

Use an isolated local state directory while developing:

```bash
export AGENT_HANDOFF_HOME="$PWD/.agent-handoff-bus"
agent-handoff doctor
```

## Run checks

```bash
python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 tools/docs_link_check.py
```

Maintainers can also run the bundled local routine:

```bash
PYTHONPATH=src python3 tools/maintainer_check.py --skip-receipt-benchmark
```

For release preparation, draft notes locally before any public release action:

```bash
PYTHONPATH=src python3 tools/release_notes_dry_run.py --limit 10
```

Before opening a pull request, also check that no personal paths or secret-like values are present in the diff.

GitHub issue forms and the pull request template are intentionally strict. They help first-time contributors provide enough context while keeping real secrets, private logs, account details, and public-action requests out of public artifacts.

Maintainers can rehearse issue triage and PR review locally with the [GitHub issue and PR dry-run workflow](docs/GITHUB_WORKFLOW_DRY_RUN.md) before making any public comment, push, release, or package action.

## Pull request guidelines

A good PR should include:

- a concise description of the maintainer workflow or safety issue it improves
- tests or a clear reason why tests are not applicable
- documentation updates for user-facing behavior
- no real secrets, private logs, or personal local paths
- explicit discussion of safety impact if the change touches send, receipt, ACK, HTTP, or adapter behavior

## Safety requirements

Do not introduce behavior that:

- binds the HTTP API to public interfaces by default
- treats `AUTO-RECEIVED` as completion
- silently ACKs a handoff without receiver-side handling
- sends public posts, email, deployments, or paid API calls without explicit human approval
- reads credentials, keyrings, browser storage, or private account state
- stores real API keys or user data in tests or examples

## Issue triage labels

Suggested labels for future maintenance:

- `bug`
- `security`
- `documentation`
- `good first issue`
- `good-first-issue`
- `maintainer-workflow`
- `release-management`

## Philosophy

This project should help maintainers coordinate with AI tools safely. It should remain understandable, testable, and useful even for maintainers who are not full-time infrastructure engineers.
