---
title: Admin portal and LLMOps
nav_order: 7
permalink: /admin-and-llmops/
---

# Admin portal and LLMOps

The admin portal is a separate application, with its own address, its own sign-in cookies and
its own Keycloak client. It is for the people who run the service, not for firms.

## Who can sign in

Only accounts with the **`platform_admin`** realm role. The portal checks the role when you
sign in, and the API checks it again on every request. A firm owner, however senior, cannot
open it.

To make someone a platform admin in a real deployment:

```bash
make admin-user EMAIL=you@example.com
```

That grants the role through Keycloak's admin API. The person signs in again to pick it up.
No default administrator ships with a production stack.

## What it will not show you

The operator manages access and consumption. The portal and the API behind it return **counts
and usage only**: how many cases a firm has, never their titles; how many tokens a proceeding
used, never what was said. There is no route from an operator account to a firm's cases,
evidence, turns or audit payloads. This is enforced and tested, not just a convention.

## Firms

Create a firm (name, plan, seats, paid-until, invoice reference, first owner), then manage it:

- **Subscription:** plan, status (*trialing*, *active*, *past due*, *cancelled*), seats,
  paid-until, invoice reference. Saving takes effect immediately: a firm set to *past due*
  stops being able to create cases on its next request.
- **Suspend or reactivate:** a suspended firm's members are locked out at once.
- **Members and pending invitations:** who is in, in what role, who has been invited.
- **Usage history:** tokens, estimated cost, simulations and turns, month by month.
- **Invite another owner**, for example when the first one has left.

## Plans

Define the limits a subscription grants: seats, simulations per month, tokens per month, turns
per proceeding and evidence storage. Editing a plan applies to every firm on it. A plan with
firms on it cannot be retired; move them first. A retired plan can no longer be assigned.

## Users

A directory of everyone in any firm, with the firms and roles they hold. **Disable** blocks
sign-in and ends live sessions immediately (through Keycloak), in every firm that person
belongs to. **Enable** reverses it.

## LLMOps

Every model call the platform makes is recorded: chat completions for the agents, embeddings
for evidence and search, and vision calls for images and scanned pages.

### What a record holds

| Field | Meaning |
|---|---|
| firm, user, simulation, agent role | who the call was for |
| kind | chat, embedding or vision |
| provider, model | which model answered |
| input and output tokens | as reported by the provider, or estimated |
| estimated | true when the provider reported no usage (counted from text length instead) |
| cost | estimated, from the price table |
| latency, time to first token | how long it took, and how long until it began to speak |
| status, error code | whether it worked, and the error class if not |

Prompts and responses are **not** stored here.

### The dashboard

- **Summary:** requests, failures and failure rate, tokens in and out, estimated cost, latency
  at p50 and p95, average time to first token, the share of calls whose tokens were estimated,
  and how many calls have no price.
- **Over time:** tokens, cost or requests per day (per hour over seven days). Hover for the
  exact value; bars with failures are outlined.
- **Breakdown** by model, provider, agent role, firm or call type.
- **Quota use this month:** each firm's tokens and simulations against its plan, highest first.
  This is the page to watch to see who is about to hit a limit.
- **Recent failures:** when, which firm, which model, the error class.
- **Prices:** reference prices per million tokens, and your own overrides.

### About the cost figures

They are **estimates**. Providers change prices, add tiers and discount cached input, so the
built-in table is a reference. Override any model's price in the *Prices* section to match
your real contract. A model with no price is counted as *unpriced*, not as free, and the
summary says how many calls that affects. Local models (Ollama, sentence-transformers) cost
nothing and are priced at zero.

### How metering stays out of the way

Recording is best-effort. If the document store is down, the model call still succeeds and a
warning is logged. Failed calls are recorded (so the failure list is real) but do not count
against a firm's token allowance. Streaming calls use the provider's reported usage when it
gives one (Gemini, OpenAI, Anthropic and Ollama all do) and fall back to an estimate.

## System

A live check of each dependency, with latency and a detail line: PostgreSQL, MongoDB, Redis,
Qdrant, Keycloak, the Celery workers, and the loaded legal packs. It refreshes every thirty
seconds. A red row is a service that is not answering.

## Activity

Every change made from the console (a firm created or suspended, a subscription edited, a
plan changed, a price overridden, a user disabled) is logged with the acting administrator.
It is the answer to "who changed that?".

## Development mode

In a development stack the console can run in *open* mode (no sign-in; you act as the seeded
dev administrator) or *credentials* mode (real sign-in with a static dev account). Both show a
"Development mode" banner. See [Running locally]({{ '/running-locally/' | relative_url }}).
