# Pricing and offer

This is the default commercial packaging for `agent-handoff-bus`. Adjust prices
only in an order form or invoice; do not sell “unlimited automation.”

## Positioning

`agent-handoff-bus` is sold as local AI-agent coordination infrastructure and
setup support. It helps teams move work between local AI agents without UI paste,
focus stealing, or hidden public actions.

Do not sell it as:

- token resale;
- a hosted AI model;
- guaranteed autonomous revenue;
- compliance automation;
- public posting or credential handling.

## Ideal customer profile

Best first buyers:

- AI-heavy founders and operators;
- agencies using multiple AI coding/ops agents;
- internal automation teams with local-first security requirements;
- consultants who need auditable handoffs between Codex, Claude Code, or similar agents.

Avoid as first customers:

- teams that cannot run Python/Git locally;
- regulated workflows requiring formal compliance review;
- buyers expecting a no-human public-action bot;
- buyers that require hosted SaaS SSO/admin dashboards on day one.

## SKU 1: Guided install pilot

Price hypothesis: **USD $499 one-time**.

Includes:

- AI-assisted or live guided install;
- one local workspace setup;
- `doctor/send/catchup/inbox` smoke test;
- optional auto-receipt bridge guidance;
- one 45-minute onboarding session;
- 7 calendar days of install-blocker support.

Success definition:

- `INSTALL_READY` achieved; or
- exact blocker documented with next fix.

Not included:

- custom integrations;
- OAuth/login/account automation;
- public posting/release/deploy automation;
- managed hosting;
- secret handling.

## SKU 2: Managed operator setup

Price hypothesis: **USD $1,500/month** after pilot.

Includes:

- up to two local agent handoff workflows;
- weekly improvement review;
- support for install and handoff reliability issues;
- one workflow change request per week;
- monthly health summary.

Guardrails:

- no public/paid/OAuth/credential actions without separate approval;
- no unlimited custom workflows;
- customer owns local machine and data.

## SKU 3: Team enablement

Price hypothesis: **USD $3,000 one-time workshop**.

Includes:

- team walkthrough;
- install guide customization;
- handoff workflow design session;
- internal champion training;
- readiness checklist.

## Sales promise

Promise:

- local-first handoff coordination;
- repeatable install path;
- clear receipt semantics;
- safety boundary for public/paid/credential actions.

Do not promise:

- perfect autonomy;
- legal, medical, or financial compliance;
- no human review;
- guaranteed cost savings or revenue;
- support for every OS policy.

## Buyer-facing 30-second pitch

> Your AI agents are acting like isolated chat boxes. `agent-handoff-bus` gives
> them a local, auditable handoff inbox so Codex, Claude Code, and other local
> agents can pass work without UI paste, focus stealing, or hidden public
> actions. We install it, prove it with a smoke test, and leave you with a repeatable
> AI-assisted setup prompt.

## Objection handling

### “Why not just paste between chats?”

Manual paste loses state, is not auditable, and does not scale. The bus gives a
local inbox with IDs, ACKs, receipt semantics, and repeatable scripts.

### “Does it send data to your server?”

No. The core package stores state locally under `AGENT_HANDOFF_HOME` or
`~/.agent-handoff-bus` and has no telemetry.

### “Will it post or deploy automatically?”

No. A handoff is not approval for public, paid, OAuth, or credential actions.
Those remain separately approved.

### “Can we buy self-serve?”

The recommended first purchase is the guided install pilot. Self-serve source
install is available, but paid onboarding reduces setup friction.
