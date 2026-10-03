---
title: Product tour
nav_order: 3
permalink: /product-tour/
---

# Product tour

The platform has two faces: the **firm portal**, where attorneys prepare matters, and the
**admin portal**, where the platform operator runs the service. This page walks through both.

---

## The firm portal

### 1. Cases

A case is a matter: a title, the country and jurisdiction it sits in, its legal system and a
short description. Cases belong to the firm. An attorney sees the cases they created and the
ones shared with them; owners and admins see every case in the firm.

The country matters beyond labelling. It selects the [jurisdiction pack]({{ '/legal-accuracy/' | relative_url }})
used to check the law the agents cite.

### 2. Evidence

Drop files onto a case. Each is read by the ingester that fits its type:

| Type | What happens |
|---|---|
| PDF | Text extracted page by page. Pages with no text layer (scans) are read by a vision model, and the status says so. |
| Word, plain text, Markdown, CSV | Text extracted. |
| Images | Transcribed by a vision model, in the original script (including Devanagari), followed by a neutral description. |
| Audio and video | Transcribed with timestamps, then indexed in 30-second windows. |

Everything is chunked, embedded and indexed. Files can be re-indexed or removed, and removing
one also removes its chunks from the search index. The extracted text itself is stored apart
from the file, in the document store.

You can search the whole case from the evidence page. Results show the source file and the
matching passage.

### 3. A proceeding

A **proceeding** (a simulation) is one run of the case. You choose a mode:

| Mode | Use it for |
|---|---|
| **Courtroom** | A full trial: judge, prosecution, defence, accused, witnesses, in procedural stages. |
| **Deposition** | A questioner and a deponent, with cross and re-examination. |
| **Strategy** | A private session with no judge: counsel, an investigator and an expert weighing options. |

A default cast is seeded for each mode and you can add or remove agents, give each a persona,
and pick the model behind each seat (Gemini, OpenAI, Anthropic or a local Ollama model). You
set the number of turns; the plan sets the ceiling.

### 4. The record

Press start and the proceeding streams in live. Each line of the record shows:

- **Who spoke**, in which role, and in which stage ("Prosecution evidence", "Final arguments").
- **Evidence citations**: seamed chips that open to the exact passage the claim rests on.
- **Authorities**: every statute, article and case the agent cited, each marked *in the
  index*, *repealed (see successor)*, *not in the index*, *could not be verified*,
  *citation does not match* or *does not exist*.
- **Provenance** in the margin: *cited*, *inferred* or *disputed*.
- **Procedure flags**: a premature verdict, a judgment with no verdict, a judge who ignored
  an objection.

The bar above the record shows the current stage, a reminder that this is a simulation, and
a **verify record** control that recomputes the audit chain and tells you whether anything
was altered.

You can pause ("recess"), resume, stop ("adjourn"), clone a proceeding to run it a different
way, or enter an override on any line. An override is stored beside the agent's original
words, labelled, and logged with a fingerprint of both versions.

### 5. The spawn graph

When a judge asks for an expert, or a forensic topic comes up with no expert present, the
orchestrator brings one in. The graph tab shows who is in the court and who called them.

### 6. Team

Owners and admins invite attorneys by email, change roles, remove people and see how many
seats are used. An invitation is bound to an email address, works once and expires in
seven days.

### 7. Plan and usage

Every firm sees its plan, what it has paid until, and this month's use of tokens,
simulations, seats and evidence storage. When the firm nears a limit, a notice appears; at
the limit, a running proceeding pauses and can be resumed.

---

## The admin portal

A separate application for the platform operator. It is deliberately blind to case content:
it deals with *who has access to what* and *what the platform is consuming*.

| Page | What it is for |
|---|---|
| **Overview** | Firms, people, subscriptions that need attention, this month's tokens and estimated cost, and whether every service is up. |
| **Firms** | Create a firm and invite its first owner; suspend or reactivate it; edit its subscription (plan, status, seats, paid-until, invoice reference); see members, counts and usage history. |
| **Plans** | The limits a subscription grants: seats, simulations and tokens per month, turns per simulation, storage. Edit once, applies to every firm on the plan. |
| **Users** | Everyone who belongs to a firm. Disabling an account blocks sign-in and ends live sessions. |
| **LLMOps** | Every model call: requests, tokens, estimated cost, latency (p50, p95, first token), failures. Break down by model, provider, agent role, firm and call type. Quota use per firm, recent failures, and an editable price table. |
| **System** | Live health of Postgres, MongoDB, Redis, Qdrant, Keycloak, the Celery workers and the legal packs. |
| **Activity** | Every change made from the console, with who made it. |

Read more in [Admin portal and LLMOps]({{ '/admin-and-llmops/' | relative_url }}).

---

## What it will not do for you

It will not tell you whether the argument is sound, whether a real citation supports the
proposition it is attached to, or what a real court would do. It shows its sources and its
limits so that you can decide.
