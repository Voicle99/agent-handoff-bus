# GitHub issue and PR dry-run workflow

Use this workflow when you want to rehearse an issue triage, pull request review,
or public maintainer response before touching GitHub.

The rule is simple: **draft locally first, publish only after explicit maintainer
approval for that exact public action.**

## What this protects

A local dry run helps maintainers avoid common public-repo mistakes:

- posting private logs, real tokens, account details, or personal paths
- treating an AI handoff as permission to comment, push, release, or publish
- closing an issue before checks actually pass
- confusing an `AUTO-RECEIVED` delivery receipt with a completed review
- turning local automation into hidden public automation

## Start from a clean local state

```bash
git fetch --prune origin main --tags
git status --short --branch
export AGENT_HANDOFF_HOME="$(mktemp -d)"
trap 'rm -rf "$AGENT_HANDOFF_HOME"' EXIT
agent-handoff doctor
```

If the working tree is dirty, decide whether those files belong to the current
maintenance task before drafting any public response. Do not stage unrelated
files.

## Dry-run an issue triage

Create a local issue draft with dummy or sanitized information only:

```bash
draft_dir="$(mktemp -d)"
cat > "$draft_dir/issue-draft.md" <<'ISSUE'
# Draft issue triage

Issue: #123
Type: documentation
Reader: first-time maintainer
Problem: receipt benchmark setup is unclear
Proposed next action: add one local-only example

Public action requested: none yet
Secrets/private data included: no
ISSUE
```

Hand the draft to a local reviewer without posting it:

```bash
agent-handoff send \
  --from maintainer \
  --to triage-reviewer \
  --title "Dry-run issue triage" \
  --file "$draft_dir/issue-draft.md" \
  --meta '{"dry_run": true, "public_action_allowed": false}'
```

Expected reviewer answer:

```text
TRIAGE_DRY_RUN: PASS
Suggested label: documentation
Suggested next action: update docs with dummy-only local example
Public action: not authorized
```

Only after explicit maintainer approval should someone create or comment on a
GitHub issue. The local draft is not approval.

## Dry-run a PR review

Create a local PR summary before opening or updating a PR:

```bash
draft_dir="${draft_dir:-$(mktemp -d)}"
cat > "$draft_dir/pr-draft.md" <<'PR'
# Draft PR summary

What changed:
- Added local-only documentation for a maintainer workflow.

Validation planned:
- py_compile
- unittest
- receipt benchmark
- git diff --check
- secret/private-data scan
- Bumblebee

Safety impact:
- No public posting, releases, package uploads, OAuth, paid APIs, or credential access.
PR
```

Send it to a local reviewer:

```bash
agent-handoff send \
  --from maintainer \
  --to pr-reviewer \
  --title "Dry-run PR review" \
  --file "$draft_dir/pr-draft.md" \
  --meta '{"dry_run": true, "public_action_allowed": false}'
```

Expected reviewer answer:

```text
PR_DRY_RUN: PASS_WITH_NOTES
Checks required before public update: compile, tests, diff check, secret/private scan, Bumblebee, CI after push
Public action: not authorized
```

## Convert a dry run into a public action

Before any public action, require all of the following:

1. The draft contains no real secrets, private logs, customer data, account
   details, private chat transcripts, or personal local paths.
2. The maintainer names the exact public action, for example:
   - create issue `Title...`
   - comment on issue `#123` with the reviewed text
   - push commit `abc123`
   - open PR from branch `example-branch`
3. Local validation passes for the touched area.
4. The repository state is clean except for the intended files.
5. The final public text is inspected after any automated rewrite.

Safe public-action wording:

```text
APPROVED_PUBLIC_ACTION: comment on issue #123 with reviewed draft file "$draft_dir/reviewed-public-comment.md"
```

Unsafe wording:

```text
Looks good, handle it.
```

The unsafe wording is too broad. It does not identify the exact action, target,
or public text.

## Run the local public-action draft guard

Use the guard script to inspect one or more local draft files before any issue,
PR, or maintainer response is posted. The script performs no network or public
action.

```bash
PYTHONPATH=src python3 tools/public_action_draft_guard.py \
  --draft "$draft_dir/issue-draft.md"
```

With a clean draft but no exact approval, the expected status is:

```text
BLOCKED_PUBLIC_ACTION_REQUIRES_APPROVAL
```

After a human has reviewed the final public text and approved the exact target,
record that approval separately:

```bash
PYTHONPATH=src python3 tools/public_action_draft_guard.py \
  --draft "$draft_dir/reviewed-public-comment.md" \
  --approval-text "APPROVED_PUBLIC_ACTION: comment on issue #123 with reviewed draft file"
```

The success status is `PASS_PUBLIC_ACTION_READY`, but it still means no public
action has been taken. Posting, pushing, closing issues, releases, package
uploads, OAuth/login changes, paid APIs, and credential access remain separate
human-approved actions.

## Check high-risk handoff text before execution

Use the handoff policy checker before acting on a handoff that asks for posting,
commenting, releases, tags, package uploads, OAuth/login changes, paid APIs,
credential access, or public network exposure:

```bash
PYTHONPATH=src python3 tools/handoff_policy_check.py \
  --body-file "$draft_dir/handoff-request.md"
```

If the request is high-risk, the checker returns
`BLOCKED_HIGH_RISK_HANDOFF_REQUIRES_APPROVAL` until the exact action and target
are approved with `APPROVED_HIGH_RISK_HANDOFF:`. This complements the public
comment/PR draft guard; neither tool posts anything.

## Suggested validation bundle

For docs or workflow changes:

```bash
python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 tools/receipt_benchmark.py
git diff --check
bumblebee version
bumblebee selftest
bumblebee scan --root . --emit-summary
```

Also run a high-confidence scan over the diff and new files for real secrets,
private local paths, account data, and private transcripts.

## What stays out of scope

A dry run must not perform these actions by default:

- GitHub issue creation or issue comments
- pull request creation or review comments
- pushes, merges, tags, releases, or package uploads
- PyPI publication or package signing
- email, DMs, deployments, or public posts
- OAuth/login/account-permission changes
- paid API calls or purchases
- credential, keyring, browser-cookie, or private account access

If a future script automates any part of this workflow, it should default to
local draft files and return `BLOCKED_PUBLIC_ACTION_REQUIRES_APPROVAL` before
crossing the public boundary.
