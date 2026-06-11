# Maintainer workflow recipes

These recipes show how maintainers can use `agent-handoff-bus` to coordinate local AI-agent work without UI paste, focus stealing, credential sharing, or implicit public actions.

Use an isolated local state directory while trying the commands:

```bash
export AGENT_HANDOFF_HOME="$PWD/.agent-handoff-bus"
agent-handoff doctor
```

A handoff is coordination only. Public comments, pushes, releases, package publishing, paid API use, OAuth/login changes, and credential access still require explicit human approval.

## Recipe 1: PR review handoff

Use this when one agent prepares a patch and another agent reviews it before a maintainer decides whether to push or merge.

```bash
agent-handoff send \
  --from maintainer \
  --to reviewer \
  --title "PR review: safe local patch" \
  --body "Review the current diff. Return PASS, BLOCKED, or CHANGE_REQUESTED. Do not push, merge, comment publicly, or access credentials."
```

Expected receiver output:

```text
PASS: local diff is safe to test
Validation requested: py_compile, unittest, git diff --check
Public action: not authorized
```

Human gate:

- The reviewer may inspect local files and recommend changes.
- Only the human maintainer or an explicitly authorized maintainer automation may push, merge, or comment publicly.

## Recipe 2: Issue triage handoff

Use this to classify a new issue and decide the smallest safe next action.

```bash
agent-handoff send \
  --from maintainer \
  --to triage \
  --title "Issue triage: #123" \
  --body "Classify issue #123 as bug, question, security, documentation, or maintenance. Propose one next action. Do not write a public reply unless explicitly approved."
```

Expected receiver output:

```text
TRIAGE: documentation
Next action: add a short example to docs/MAINTAINER_RECIPES.md
Risk: no public write authorized yet
```

Human gate:

- Treat security-looking reports as sensitive even if the public issue is vague.
- Do not quote private logs or suspected secrets into public comments.

## Recipe 3: Release checklist handoff

Use this before tagging a release.

```bash
agent-handoff send \
  --from maintainer \
  --to release-review \
  --title "Release checklist: v0.1.x" \
  --body "Check version, changelog/maintenance log, tests, secret scan, CI status, and package metadata. Return GO or BLOCKED. Do not tag, publish, or upload packages."
```

Expected receiver output:

```text
GO_LOCAL_ONLY: release candidate is internally consistent
Checks: compile PASS, unittest PASS, CI PASS, secret scan PASS
Blocked external action: tag/publish still needs explicit human approval
```

Human gate:

- Creating a Git tag, GitHub release, or PyPI package is a public action.
- Release automation must fail closed if CI or scans are uncertain.

## Recipe 4: Security review handoff

Use this when a change touches secret scanning, localhost binding, receipt semantics, ACK behavior, body-file handling, or external adapters.

```bash
agent-handoff send \
  --from maintainer \
  --to security-review \
  --priority high \
  --title "Security review: scanner/receipt boundary" \
  --body "Review the local diff for secret leakage, public bind risk, unsafe ACK/completion semantics, and public/paid action escalation. Use fake data only."
```

Expected receiver output:

```text
SECURITY_REVIEW: PASS_WITH_NOTES
No public bind added.
AUTO-RECEIVED still means delivery only.
No original body is quoted in secret-hint receipts.
```

Human gate:

- Do not include real tokens, private logs, customer data, local personal paths, or account details in the handoff.
- If real sensitive material appears, stop and clean local state before opening public issues or commits.

## Reliable receipt check

For critical handoffs, start a local auto-receipt bridge in a separate terminal:

```bash
agent-handoff-auto-reply --sessions reviewer --fallback-source maintainer --include-existing
```

Then send with a receipt requirement:

```bash
agent-handoff-reliable \
  --from maintainer \
  --to reviewer \
  --title "critical review" \
  --body "Return PASS or BLOCKED after reading the task." \
  --timeout 15
```

Expected output on success:

```json
{
  "status": "PASS",
  "receipt_acked": false
}
```

Expected output when no receiver bridge is running:

```json
{
  "status": "BLOCKED_NO_AUTO_RECEIPT"
}
```

Remember: `AUTO-RECEIVED` is delivery proof only. It is not task completion and not permission to perform public actions.

## Optional local auto-reply service templates

Use the templates in [`../examples/`](../examples/) only for local workstation
service managers:

- macOS launchd: [`../examples/launchd-auto-reply.plist.template`](../examples/launchd-auto-reply.plist.template)
- Linux systemd user service: [`../examples/systemd-auto-reply.service.template`](../examples/systemd-auto-reply.service.template)

Render placeholders such as `${PYTHON_BIN}`, source session, target session, and
`AGENT_HANDOFF_HOME` locally. Do not commit rendered service files, logs, or
user-specific paths.

The templates run only the local auto-receipt bridge. They do not approve,
post, publish, release, upload packages, call paid APIs, access credentials, or
mark the original task complete.

Guard template edits before committing them:

```bash
PYTHONPATH=src python3 tools/service_template_guard.py
```

Commit only `.template` files. Keep rendered launchd plist and systemd service
files local to the machine that will run them.

## Receipt benchmark check

When changing reliable-send or auto-reply behavior, run the local benchmark:

```bash
PYTHONPATH=src python3 tools/receipt_benchmark.py
```

Expected result:

```json
{
  "status": "PASS",
  "network": "local-only",
  "dummy_data_only": true
}
```

The benchmark uses an isolated temporary `AGENT_HANDOFF_HOME`. It checks both the local success path with an auto-reply bridge and the fail-closed path where no receiver bridge exists.

## CI-like local operation

Use this for repeatable local checks, scheduled maintainer dry runs, or a
developer workstation script that should behave like CI without becoming public
automation.

Start from a clean checkout and isolate bus state:

```bash
git status --short --branch
export AGENT_HANDOFF_HOME="$(mktemp -d)"
trap 'rm -rf "$AGENT_HANDOFF_HOME"' EXIT
```

Run the dependency-free local checks:

```bash
python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 tools/docs_link_check.py
PYTHONPATH=src python3 tools/receipt_benchmark.py
```

Or run the bundled maintainer routine for the recurring local gates:

```bash
PYTHONPATH=src python3 tools/maintainer_check.py
```

For fast focused checks, select only the relevant gates:

```bash
PYTHONPATH=src python3 tools/maintainer_check.py --check docs_link --check service_template
```

The bundle emits JSON and always reports `public_action_taken: false`; it does not push, post, release, upload packages, use OAuth, call paid APIs, or access credentials.

## Release-notes dry run

Use this before release planning or status updates that need a commit-summary draft:

```bash
PYTHONPATH=src python3 tools/release_notes_dry_run.py --limit 10
```

To draft a local markdown file for review:

```bash
PYTHONPATH=src python3 tools/release_notes_dry_run.py \
  --base-ref v0.1.0 \
  --output /tmp/agent-handoff-bus-release-notes.md
```

The draft is local-only. It does not create a GitHub release, tag, package upload, public post, OAuth flow, paid API call, service lifecycle action, or credential access.

Run private-data and security gates before making anything public:

```bash
git diff --check
git ls-files --others --exclude-standard
# Run your local high-confidence scan over tracked files, untracked candidate
# files, and git metadata before committing or opening public issues.
bumblebee version
bumblebee selftest
bumblebee scan --root . --emit-summary
```

Keep examples dummy-only. Do not put real API keys, private tokens, customer
data, personal paths, private chat transcripts, or account details into the
repository, local reports, issue comments, or release notes.

Human-gated actions stay human-gated even when every local check passes:

- public issue comments or pull request comments
- pushes, tags, GitHub releases, or package publication
- PyPI uploads or package-signing actions
- OAuth/login/account-permission changes
- paid APIs, purchases, or hosted-service calls
- credential access, browser/session scraping, or keyring reads

Expected dry-run result:

```text
LOCAL_CHECKS_PASS
Public action: not authorized by local checks alone
Next action: maintainer reviews the diff and decides whether to push/comment/release
```
