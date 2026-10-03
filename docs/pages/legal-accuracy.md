---
title: Legal accuracy
nav_order: 8
permalink: /legal-accuracy/
---

# Legal accuracy

Language models write fluent legal argument, and the same fluency covers invented section numbers and made-up judgments. Nyayrithm does not try to prompt its way out of that. It checks what the agents say, keeps proceedings in order, and keeps a record that cannot be quietly rewritten. This page describes what exists, and where its limits are.

Everything here is a **simulation aid**. It is not legal advice, and a "verified" citation means only that the provision or case appears in the reference index, not that it supports the argument made.

---

## Jurisdiction packs

A pack is a JSON file describing one jurisdiction: its acts (with each act's last valid section number), an index of provisions and landmark cases, and a concordance from repealed to current law. Packs live in `backend/app/legal/packs/`; extra packs are loaded from `LEGAL_PACKS_DIR`.

A case picks its pack from `country` (aliases such as `India`, `IN` and `Bharat` all resolve to the Indian pack). A country with no pack still runs, but its citations are reported as `no_pack` rather than guessed at.

### The bundled Indian pack is a starter index

It covers the Constitution (Articles 14, 19, 20, 21, 22, 32, 39A, 136, 141, 142, 226), a selection of BNS, BNSS and BSA provisions, the IPC → BNS, CrPC → BNSS and Evidence Act → BSA concordance for those provisions, and about seventeen landmark Supreme Court decisions. Summaries are paraphrased for retrieval and are **not the statutory text**. Check them against [India Code](https://www.indiacode.nic.in/) before relying on them.

To extend a pack, add entries in the same schema:

```json
{
  "id": "IN",
  "acts": [{ "code": "BNS", "name": "Bharatiya Nyaya Sanhita, 2023", "aliases": ["bns"],
             "unit": "Section", "max_section": 358, "replaces_act": "IPC" }],
  "provisions": [{ "act": "BNS", "section": "103", "title": "Punishment for murder",
                   "summary": "…", "replaces": ["IPC 302"], "keywords": ["murder"] }],
  "concordance": [{ "old": "IPC 302", "new": "BNS 103" }],
  "cases": [{ "name": "…", "citations": ["(1978) 1 SCC 248"], "court": "…", "year": 1978,
              "holding": "…", "keywords": ["article 21"] }]
}
```

---

## Citation verification

After every turn, the text is scanned for statute sections (`Section 103 BNS`, `Sections 302 and 34 IPC`, `u/s 498A IPC`, `BNS 103`), constitutional articles (`Article 19(1)(a)`) and cases (`Maneka Gandhi v. Union of India (1978) 1 SCC 248`, `AIR 1973 SC 1461`, or a bare case name). Each is checked with fixed rules, not another model:

| Status | Meaning | Severity |
|--------|---------|----------|
| `verified` | In the index; title shown | ok |
| `superseded` | A repealed act (IPC, CrPC, Evidence Act). Still valid for conduct before 1 July 2024; the current equivalent is named | notice |
| `unindexed` | The section number is possible for that act, but the index has no entry, so it cannot be checked | notice |
| `unverified` | A case that is not in the index | warning |
| `mismatch` | A reporter citation that belongs to a different case than the one named | error |
| `nonexistent` | A section or article number beyond the end of the act, which cannot exist | error |

`unindexed` and `unverified` mean *could not be checked*, not *wrong*. Only `mismatch` and `nonexistent` are proofs.

What happens next:

- the review is stored with the turn (`legal_review`) and shown beside it as **authorities** chips;
- flagged citations raise a `citation.flagged` WebSocket event and an audit event;
- on that agent's **next** turn the prompt carries a registry correction naming each citation that could not be right, so it does not repeat it;
- agents are given a short "applicable law" excerpt, drawn from the index by relevance to the case and recent turns, instead of being left to recall provisions.

`POST /api/v1/legal/verify` checks any text on demand. Set `LEGAL_REVIEW_ENABLED=false` to turn the whole layer off.

### What it cannot do

It does not read the cited authority or judge whether it supports the point. A real section cited for the wrong proposition, or a real case with a distorted holding, is `verified`. Within the starter index, most real citations will be `unindexed` or `unverified`.

---

## Procedure enforcement

For `courtroom` and `deposition` simulations a procedure engine fixes the order of stages, chooses who speaks, and tells each agent what the stage requires of it. The courtroom stages are: opening → framing of charge → prosecution evidence → examination of the accused → defence evidence → final arguments → judgment. The turn budget (`max_turns`) is divided among stages by weight, every stage getting at least one turn when the budget allows.

- Examination stages alternate counsel and witness: examination in chief, then cross, with the instruction to ask non-leading questions in chief and leading ones in cross.
- When counsel objects, the **next** turn goes to the judge, who must rule *sustained* or *overruled*.
- Each turn is checked and any problem is shown on it: `premature_verdict` (a verdict before final arguments), `verdict_missing` (a judgment without one), `ruling_missing`, `objection_by_non_counsel`.
- Stage-specific notes (for India: the examination of the accused under BNSS s.351) come from the pack.

The engine is stateless (stage is a function of the turn number and budget), so it survives the worker rebuilding the orchestrator each turn. See the plan at `GET /api/v1/simulations/{id}/procedure`. Disable with `"enforce_procedure": false` in the simulation `config`. `strategy` mode has no procedure.

---

## Audit trail

Every simulation keeps a hash-chained log (`audit_events`). Each event stores the hash of the one before it, so changing, deleting or reordering any past event breaks every hash after it.

Recorded: simulation created / started / paused / stopped / completed; each generated turn (agent, role, provider and model, SHA-256 of the full prompt and of the response, the evidence chunks retrieved, stage, legal status, procedural violations); flagged citations; and human edits to a turn (hashes of the before and after text, never the text itself).

`GET /api/v1/simulations/{id}/audit/verify` recomputes the chain, and the **verify record** control in the simulation view runs it. On PostgreSQL the table also rejects `UPDATE` with a trigger.

**Limits.** Someone with full database access could rewrite the whole chain consistently. To close that, export the head hash from `/audit/verify` and keep it somewhere the database cannot reach. Truncating the *end* of a chain is detectable only against such an anchored head hash.

---

## Disclaimer

Simulation responses and turn lists carry a `disclaimer` field, `GET /api/v1/legal/disclaimer` returns it, and the simulation view shows a standing notice under the header.
