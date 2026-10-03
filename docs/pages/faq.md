---
title: FAQ and glossary
nav_order: 11
permalink: /faq/
---

# FAQ and glossary

## Questions

**Is this legal advice?**
No. It is a simulation and preparation tool. Its agents can be wrong, including about the law
they cite, and nothing it produces should be relied on without checking it against official
sources and applying a lawyer's judgment.

**Can it predict how a real court will rule?**
No, and it does not try to. Outcomes depend on the models and prompts. Use runs as stress
tests of an argument, not forecasts.

**Where does my evidence go?**
It is stored by the platform you run, and the text of evidence is sent to the model provider
you configure (Gemini, OpenAI, Anthropic) in order to be read and argued over. If a matter
cannot go to a hosted provider, run local models through Ollama and a local embedder; the
platform is built to work with no external calls at all.

**Can the platform operator read our cases?**
Not through the platform. The admin portal and its API return counts and usage, never case
content. Anyone with direct access to the servers or databases is outside those rules, which
is why access to them should be limited. See [Trust and security]({{ '/trust-and-security/' | relative_url }}).

**Does a "verified" citation mean it is right?**
No. It means the section or case exists in the reference index and the citation matches. It
does not mean the authority supports the point it is cited for. The checker can prove some
citations *wrong*; it can never prove an argument *right*.

**Why is a real case marked "could not be verified"?**
The bundled Indian pack is a starter index (seventeen landmark decisions, sixty-three
provisions). A real case outside it is simply not known to the checker. That is a prompt to
check it, not a finding of error. Larger packs can be loaded.

**What happens to the IPC, CrPC and Evidence Act?**
They were replaced by the BNS, BNSS and BSA for conduct on or after 1 July 2024. The checker
treats the old acts as repealed but still valid for earlier conduct, and names the current
equivalent where it knows it.

**How do we pay?**
Billing is manual for now: the operator records a plan, seats and a paid-until date against an
invoice you pay offline. A payment gateway can be added later without changing how limits are
enforced.

**What happens when we run out of tokens mid-hearing?**
The proceeding pauses before the next turn, says why, and resumes when the allowance renews or
the plan is raised. Nothing already recorded is lost.

**Can one attorney see another's cases?**
Only if they are an owner or admin, or the case has been shared with them.

**Can someone be in two firms?**
Yes. They switch between firms from the sidebar.

**Which models can I use?**
Gemini, OpenAI, Anthropic and local Ollama models, mixed freely per agent. The default roster
runs on one free Gemini key.

**Does it work offline?**
Yes, with Ollama for the agents and a local sentence-transformers embedder. Image and scan
reading needs a vision-capable hosted model.

**Why a separate admin application?**
So that the operator's console can have its own address, cookies, sign-in client and, if
desired, its own network exposure, entirely apart from what firms use.

**How do I run it?**
With Docker Compose. See [Running locally]({{ '/running-locally/' | relative_url }}) and [Deployment]({{ '/deployment/' | relative_url }}).

## Glossary

| Term | Meaning |
|---|---|
| **Admin portal** | The separate operations console for the platform operator. |
| **Agent** | One participant in a proceeding, with a role, persona, knowledge scope and model. |
| **Audit chain** | The hash-linked log of what happened in a proceeding. |
| **Authority** | A statute section, constitutional article or case cited in a turn. |
| **BNS, BNSS, BSA** | India's penal, criminal-procedure and evidence codes (2023), in force from 1 July 2024. |
| **Case** | A matter, owned by a firm. |
| **Entitlement** | A plan limit enforced by the server. |
| **Evidence citation** | An `[EVIDENCE:id:n]` marker resolving to a stored passage. |
| **Firm** | The tenant: the organisation that subscribes and owns its data. |
| **Jurisdiction pack** | A reference index of a legal system used to check citations. |
| **LLMOps** | Monitoring of model usage, cost, latency and errors. |
| **Override** | A human replacing a turn's displayed text, recorded beside the original. |
| **Platform admin** | The operator role. Manages firms and plans; has no access to firm data. |
| **Proceeding** | One run of a case in a mode (a simulation). |
| **Provenance** | Whether a line is *cited*, *inferred* or *disputed*. |
| **RAG** | Retrieval-augmented generation: agents answer from passages retrieved from the case. |
| **Role-scoped retrieval** | Retrieval filtered by what the agent's role may know. |
| **Spawn** | An agent calling another into the proceeding. |
| **Stage** | A phase of a courtroom proceeding (opening, evidence, closing, judgment). |
| **Turn** | One agent's contribution to a proceeding. |
