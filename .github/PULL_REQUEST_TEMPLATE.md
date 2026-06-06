## Summary

<!-- What changed, and why is it useful for local-first maintainer workflows? -->

## Change type

- [ ] Bug fix
- [ ] Documentation or recipe
- [ ] Test or local validation improvement
- [ ] Maintainer workflow improvement
- [ ] Security boundary hardening
- [ ] Adapter boundary work

## Validation

Run the checks that match the change. Mark N/A with a short reason.

- [ ] `python3 -m py_compile src/agent_handoff_bus/*.py tests/*.py tools/*.py`
- [ ] `PYTHONPATH=src python3 -m unittest discover -s tests -v`
- [ ] `PYTHONPATH=src python3 tools/receipt_benchmark.py`
- [ ] `git diff --check`
- [ ] Secret/private-data scan over the diff and new files
- [ ] Bumblebee or equivalent local security scan

## Safety and privacy boundary

- [ ] I did not include real API keys, tokens, credentials, private logs, customer data, private chat transcripts, or personal local paths.
- [ ] The change does not make public posting, releases, package publication, email, deployments, paid API use, OAuth/login changes, or credential access automatic.
- [ ] If this touches send, receipt, ACK, HTTP, scanner, body-file, or adapter behavior, I explained the safety impact below.

Safety impact / N/A:

<!-- Describe the boundary impact, or say N/A for docs-only changes. -->

## Public action boundary

This PR may be reviewed and tested locally. Merging, tagging, publishing packages, creating releases, posting comments, sending email, OAuth changes, paid API actions, or credential access still require explicit maintainer approval.
