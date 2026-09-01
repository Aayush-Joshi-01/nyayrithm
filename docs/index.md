---
title: Home
nav_order: 1
permalink: /
description: Developer and self-hosting documentation for Nyayrithm, a multi-agent, evidence-grounded courtroom simulation platform.
---

# Nyayrithm docs

<p class="nc-lede">
A graph of AI agents argues a case from evidence you supply. Each agent plays a
distinct legal role with its own knowledge scope and model, and every claim
resolves to the exact source passage behind it.
</p>

<div class="nc-actions">
  <a class="primary" href="/nyayrithm/setup/windows/">Get started</a>
  <a href="https://nyayrithm.ai.aayushjoshi.dev">Open the app</a>
  <a href="https://github.com/Aayush-Joshi-01/nyayrithm">Source on GitHub</a>
</div>

---

## Where things live

| Surface | What it is |
|---|---|
| **This site** | Developer and self-hosting docs: setup, architecture, providers, deployment. |
| **[nyayrithm.aayushjoshi.dev](https://nyayrithm.aayushjoshi.dev)** | The product landing page and in-app documentation. |
| **[nyayrithm.ai.aayushjoshi.dev](https://nyayrithm.ai.aayushjoshi.dev)** | The app itself: sign in, add evidence, run proceedings. |

## What it does

| Capability | Detail |
|---|---|
| **9 legal roles** | Judge, Prosecutor, Defense, Plaintiff, Accused, Witness, Investigator, Expert Witness, and a Custom role |
| **Dynamic agent graph** | Agents spawn specialist sub-agents mid-proceeding; the orchestrator auto-spawns when a domain gap opens |
| **Multi-modal evidence** | PDF, DOCX, audio (Whisper), video (ffmpeg and Whisper), images |
| **Role-scoped retrieval** | Each agent retrieves only the evidence its role is permitted to see |
| **Citations** | Inline `[EVIDENCE:uuid:chunk_idx]` markers resolve to the exact passage; each turn is marked cited, inferred, or disputed |
| **Provider-agnostic** | Mix OpenAI, Anthropic, Gemini, and Ollama per agent, or run one free provider for the whole court |
| **Any backend** | PostgreSQL, MongoDB, SQLite, or DynamoDB for data; Qdrant, Chroma, Pinecone, or pgvector for vectors. One env var each. |

## Start here

| Guide | For |
|---|---|
| [Windows](/nyayrithm/setup/windows/), [macOS](/nyayrithm/setup/macos/), [Linux](/nyayrithm/setup/linux/) | Platform setup, Docker or native |
| [Running locally](/nyayrithm/running-locally/) | Docker down to container-free, zero-cost |
| [LLM providers](/nyayrithm/llm-providers/) | Free tiers, per-role model assignment |
| [Architecture](/nyayrithm/architecture/) | Abstractions, data flow, auth, the frontend |
| [Deployment](/nyayrithm/deployment/) | The two-domain production topology |

## The zero-cost path

A free Google Gemini key plus SQLite, Chroma, and `sentence-transformers` (or a
local Ollama model) is a complete stack with no external calls. See
[Running locally](/nyayrithm/running-locally/).
