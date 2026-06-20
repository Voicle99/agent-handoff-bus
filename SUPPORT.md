# Support

## Support channels

Open-source users:

- Use GitHub Issues for reproducible bugs and documentation problems.
- Do not include secrets, private handoff bodies, customer data, or local private
  paths in public issues.

Paid pilot or managed setup customers:

- Use the support channel specified in the invoice, order form, or onboarding
  message.
- If no private channel has been specified yet, start with a redacted GitHub
  Issue or request a private support channel during onboarding.

## Support scope

Included in guided pilot support:

- installation troubleshooting;
- `handoff-bus doctor` interpretation;
- source or pipx-from-Git install support;
- basic send/catchup/inbox smoke tests;
- local auto-receipt bridge setup guidance;
- bug triage for supported Python versions.

Out of scope unless separately agreed:

- public posting, releases, uploads, deployments, or account actions;
- OAuth/login work;
- credential storage or secret recovery;
- regulated legal/medical/financial decisions;
- custom hosted infrastructure;
- unlimited workflow customization.

## Response targets

Open-source issues: best effort.

Paid pilot support target:

- first response within 2 business days;
- critical install blocker triage within 1 business day when the customer provides
  exact command output and environment details.

These are support targets, not uptime guarantees.

## Refund and cancellation policy

Guided setup pilot:

- If the installer cannot reach `INSTALL_READY` after one scheduled setup session
  because of a product bug, the customer may request either one remediation
  session or a refund of the setup fee.
- If the blocker is missing local prerequisites, unavailable customer permissions,
  unsupported operating system policy, or refusal to run local commands, the setup
  fee is not automatically refundable.

Monthly managed support:

- Cancel before the next billing period to stop future charges.
- Partial-month refunds are not guaranteed unless stated in the order form.

## Bug report checklist

Include:

```text
Operating system:
Python version:
Install method: source / pipx / wheel / other
Command that failed:
Exit code:
Redacted output:
AGENT_HANDOFF_HOME location type: default / custom / temp
Expected result:
Actual result:
```

Never include secrets or private handoff content.
