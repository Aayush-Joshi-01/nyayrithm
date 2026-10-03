---
title: How it works
nav_order: 4
permalink: /how-it-works/
---

# How it works

Follow one matter from upload to verdict.

```
 evidence files                                         firm's plan
      │                                                      │
      ▼                                                      ▼
 ┌─────────┐   text    ┌──────────┐  vectors  ┌────────┐   ┌───────────────────────┐
 │ ingest  │──────────▶│ chunk +  │──────────▶│ Qdrant │   │  quota & status check │
 │ (OCR,   │           │ embed    │           └───┬────┘   └──────────┬────────────┘
 │ Whisper)│           └──────────┘               │                   │ before every turn
 └─────────┘                                      │ role-scoped       ▼
                                                  │ retrieval   ┌──────────────┐
   jurisdiction pack ──▶ applicable law ──────────┼────────────▶│ orchestrator │
   procedure engine  ──▶ whose turn, what stage ──┼────────────▶│  one turn    │
                                                  │             └──────┬───────┘
                                                  ▼                    ▼
                                            ┌───────────┐       ┌────────────┐
                                            │   agent   │──────▶│ model call │ (metered)
                                            └─────┬─────┘       └────────────┘
                                                  │ the turn's text
                    ┌─────────────────────────────┼─────────────────────────────┐
                    ▼                             ▼                             ▼
          citation + procedure          persist turn (document        hash into the audit
          review → flags, and           store) and stream it to       chain, add usage to
          a correction for next turn    the browser                   the firm's counters
```

## 1. Evidence becomes searchable text

A file is stored, then ingested in the background. The ingester for its type extracts text
(PDF text, Word paragraphs), transcribes audio and video with timestamps, or sends an image
or a scanned page to a vision model. The text is cut into overlapping chunks, each chunk is
embedded, and the vectors go into a per-case collection in Qdrant.

If no vision model is configured, an image stays indexable by its existence and its status
says that its text was not extracted; the system does not pretend.

## 2. A cast is assembled

The proceeding's agents are built from their definitions. Each has a role (judge,
prosecutor, defence, plaintiff, accused, witness, investigator, expert witness or custom), a
persona, a knowledge scope and a model. Roles come with a system prompt that states what the
role knows, does not know, and may do.

## 3. One turn

For each turn the orchestrator:

1. **Checks the firm's plan.** If the subscription has lapsed or the monthly token budget is
   spent, the proceeding pauses before the turn is spent, and says why.
2. **Chooses the speaker.** In a courtroom or deposition the procedure engine names the role
   for this stage (and, after a counsel's objection, hands the floor to the judge). The least
   recently used agent of that role speaks.
3. **Builds the agent's context:**
   - the last turns of the proceeding;
   - the **evidence passages** that role may retrieve, found by semantic search over the case
     (a witness reaches only evidence linked to them; a judge reaches everything admitted);
   - an **applicable-law excerpt** drawn from the jurisdiction pack by relevance to the case
     and the recent turns;
   - the **stage directive** ("You are cross-examining. Leading questions are allowed…");
   - a **registry correction**, if the agent's previous turn cited law that cannot be right.
4. **Calls the model**, streaming tokens to the browser as they arrive. The call is metered:
   provider, model, tokens (reported or estimated), latency, time to first token, estimated
   cost, and which firm, simulation and role it was for.
5. **Reviews what was said.** Evidence markers (`[EVIDENCE:id:n]`) are resolved to their
   passages. Legal citations are verified against the pack. The turn is checked against
   procedure.
6. **Records it.** The turn, with its review, is stored. An audit event is appended with the
   hashes of the prompt and the response and the list of passages retrieved. The firm's
   monthly usage counters are updated.
7. **Spawns, if needed.** If the judge asks for an expert, or a forensic topic comes up with
   none present, a specialist is added to the cast.

## 4. Procedure

In a courtroom the proceeding moves through stages, and the turn budget is divided among
them:

> Opening → Framing of the charge → Prosecution evidence → Examination of the accused →
> Defence evidence → Final arguments → Judgment

Examination alternates counsel and witness: examination in chief, then cross. When counsel
objects, the next turn is the judge's, who must rule sustained or overruled. The engine does
not block a misstep, it *flags* it: a verdict pronounced before closing arguments, a judgment
with no verdict, a witness who "objected".

## 5. Law that is checked

Every statute, article and case in a turn is extracted and checked by rules against the
jurisdiction pack. The result is one of six verdicts, from *in the index* to *does not exist*.
Only the last two (a section number beyond the end of its act; a case citation that belongs to
a different case) are proofs of error. The rest mean "could not be checked". Details are in
[Legal accuracy]({{ '/legal-accuracy/' | relative_url }}).

## 6. The record cannot be quietly rewritten

Each audit event contains the hash of the previous one. Change, delete or reorder any past
event and every hash after it stops matching. *Verify record* in the proceeding view recomputes
the chain. PostgreSQL additionally refuses `UPDATE` on the audit table. Read the limits in
[Trust and security]({{ '/trust-and-security/' | relative_url }}).

## 7. What the firm and the operator see

While this happens, the **firm** sees its record, its citations, its usage against its plan.
The **operator** sees only that a proceeding ran, how many tokens it used, which models, how
fast, and whether calls failed, never what was said.

## A short example

An associate uploads the FIR, two witness statements and a forensic report in a murder case
and starts a courtroom proceeding of 60 turns.

- Turns 1 to 4: the judge calls the matter; counsel open; the charge is framed and the
  accused pleads.
- The prosecutor calls the first witness and asks open questions; the witness answers from
  their statement. The defence cross-examines, noticing the witness's account differs from the
  report, and the orchestrator raises a *conflict detected* event.
- The prosecutor cites "Section 9999 of the BNS". The registry flags it: the BNS has 358
  sections. The associate sees a red chip on the line, and on the prosecutor's next turn the
  agent is told the citation could not be right.
- The defence raises an objection; the judge rules it overruled and the examination continues.
- At turn 60 the judge delivers a reasoned judgment. The associate clicks *verify record* and
  gets "record intact, 187 events".
- The associate clones the proceeding, replaces the defence agent with one on a different
  model, and runs it again to compare.
