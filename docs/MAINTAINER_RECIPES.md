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
