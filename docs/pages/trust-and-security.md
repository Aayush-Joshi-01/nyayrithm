---
title: Trust and security
nav_order: 9
permalink: /trust-and-security/
---

# Trust and security

What the platform protects, how, and where its promises stop.

## Identity

Sign-in is handled by **Keycloak**. Users never see Keycloak's own pages: login and
registration are part of the app and call Keycloak from the server side, so passwords never
touch browser JavaScript beyond the form. Sessions are held in `httpOnly` cookies.

The API verifies a Keycloak-signed (RS256) bearer token on every request and on the live
WebSocket. Tokens are checked against the realm's published keys (cached, refetched when a key
rotates), the issuer must be one we trust, and expired tokens are refused. Tokens signed with
a shared secret (`HS256`) or with no algorithm at all are rejected outright. The WebSocket
takes the token in the query string, closes with a distinct code for "bad token" or "not
yours", and checks ownership before streaming anything.

## Isolation between firms

Every case belongs to a firm, and every read and write goes through one access service that
enforces the firm boundary. An attorney sees their own cases and those shared with them; the
rest answer *not found*, the same as an id that never existed. Tests exercise every route as
an outsider, a colleague, an owner and a platform administrator.

## What the platform operator can and cannot see

| Can see | Cannot see |
|---|---|
| Firm names, slugs, status and plan | Case titles, descriptions, evidence, files |
| Member emails and roles | Proceedings, turns, what any agent said |
| Counts (cases, simulations, files) | The audit log's payloads |
| Tokens, cost, latency, errors per firm | Prompts and responses (never stored in LLMOps) |
| Which models were used, and for which agent role | |

Two caveats, stated plainly. First, someone with direct access to the databases or the
servers is not bound by the application's rules; operating the platform responsibly is a matter
of who is given that access. Second, evidence text is sent to the model provider you configure
in order to be read; if that is unacceptable for a matter, use a local model.

## Data handling

- **Where data lives:** relational state (firms, people, cases, proceedings, the audit chain)
  in PostgreSQL; turns, extracted evidence text and model-usage events in MongoDB; vectors in
  Qdrant; the original files on local disk or S3-compatible storage.
- **Uploads** are size-limited, their filenames are sanitised, and storage paths cannot escape
  the storage directory.
- **Deleting** a case removes its proceedings, turns, extracted text and vector collection.
  Deleting a proceeding removes its turns, agents and audit events.
- **Invitations:** the emailed token is random and single-use; only its hash is stored.

## The audit chain

Each proceeding's audit log is hash-linked: every event stores the hash of the previous one.
Editing, deleting or reordering a past event breaks all the hashes after it, and the
**verify record** control detects it. PostgreSQL also rejects `UPDATE` on the table.

What it does **not** do: stop someone with full database access from rewriting the *whole*
chain consistently, or from truncating its *end*. Closing that gap means exporting the head
hash that verification returns and keeping it somewhere the database cannot reach.

The log records provenance (which model, which prompt hash, which passages) and never the
words themselves.

## Legal checks: what they prove

| The check says | It means |
|---|---|
| in the index | the provision or case exists and the citation matches |
| repealed (see successor) | an old act; valid for conduct before 1 July 2024; the current provision is named |
| not in the index, or could not be verified | **we cannot tell**. This is not a finding of error |
| does not exist, or citation does not match | provably wrong: the section number is beyond the act, or the reporter citation belongs to another case |

The bundled Indian pack is a **starter index**: sixty-three provisions and seventeen landmark
decisions, with paraphrased summaries. It is not the statute book and not a law report. The
checker never reads the cited authority or judges whether it supports the point made: a real
section cited for the wrong proposition is "in the index".

## Production safeguards

The backend refuses to start in production with any development switch on (open auth mode,
the dev bypass, dev data seeding), or with the placeholder secret key. The production Compose
file never mounts the development realm and its static accounts.

## Reporting a vulnerability

See [SECURITY.md](https://github.com/Aayush-Joshi-01/nyayrithm/blob/main/SECURITY.md).
