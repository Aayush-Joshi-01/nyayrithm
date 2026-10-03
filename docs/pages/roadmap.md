---
title: Roadmap
nav_order: 10
permalink: /roadmap/
---

# Roadmap

Where the project is and where it is going. Dates are deliberately absent; order is what
matters.

## Shipped

**The simulation core**
- Courtroom, deposition and strategy modes with a default cast for each
- Nine roles, dynamic spawning, role-scoped retrieval
- Multi-modal evidence: PDF, Word, text, images (vision OCR), audio and video (Whisper), scanned PDFs
- Live streaming over WebSocket; pause, resume, stop, clone, override
- Gemini, OpenAI, Anthropic and Ollama providers, assignable per agent

**Trust and legal accuracy**
- Jurisdiction packs and deterministic citation verification, with a starter Indian pack
- Courtroom and deposition procedure engine with objection handling and procedural flags
- Registry corrections fed back to the agent that cited non-existent law
- Hash-chained audit trail with a verify control, and a standing disclaimer

**Firms and operations**
- Firm tenancy with owner, admin and attorney roles, case sharing
- Email-bound, single-use, seat-aware invitations
- Plans and subscriptions (manual billing) enforced on the server, including a mid-run token-budget pause
- Admin portal: firms, plans, subscriptions, users, system health, activity log
- LLMOps: per-call metering of chat, embedding and vision, cost estimates with price overrides
- PostgreSQL and MongoDB split by data shape; Docker Compose as the only deployment mechanism
- Development stack with open and static-credential modes

## Next: richer procedure

- Hearing types beyond the criminal trial: bail, appeal, civil suit stages, arbitration
- Leading-question and compound-question detection as procedural flags
- Burden and standard of proof tracked through a proceeding
- Judge temperament and witness reliability as persona controls

## Next: take a seat yourself

- Play counsel (or the witness) against AI agents, with coaching afterwards
- Edit what an agent said and **replay from that turn**
- Branch a proceeding at any turn and compare branches side by side

## Next: outcome analysis

- Run the same case N times across models and seeds
- Report the spread of verdicts, the arguments that recur, the exhibits that changed outcomes
- A scorecard per proceeding: argument strength, procedural errors, missed evidence

## Next: evidence intelligence

- Timelines and entity-relationship maps extracted from the record
- A contradiction finder across documents and witness statements
- Chain-of-custody and hash-on-upload for evidence files
- Redaction of personal data before anything is sent to a model provider
- Diarised transcripts with speaker labels

## Next: work product

- Exportable transcripts, case briefs, argument outlines and cross-examination question banks (PDF and Word)
- Post-session reports
- Read-only share links

## Later: deeper jurisdictions

- A full-text statute and case-law corpus for India, loaded through the pack mechanism
- Packs for other common-law jurisdictions
- Multilingual output, starting with Hindi

## Later: commercial and platform

- Self-serve billing through a payment gateway, behind the existing billing interface
- Single sign-on for firms
- Per-firm data retention and residency settings
- Webhooks and an API for integration with firm systems
- Anchoring the audit chain's head hash outside the database
- An evaluation harness: golden cases, citation-accuracy checks and regression runs on prompt or model changes

## What will not be on it

Predicting real verdicts, giving legal advice, or filing anything with a court.
