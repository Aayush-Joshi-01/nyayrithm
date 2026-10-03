---
title: Core concepts
nav_order: 5
permalink: /concepts/
---

# Core concepts

The ideas the rest of the documentation assumes.

## Roles

Nine roles exist. Each has a system prompt that states what the role knows, does not know,
and may do, and a retrieval rule that enforces the "knows".

| Role | Plays | Retrieval |
|---|---|---|
| Judge | Presides, rules, delivers judgment | everything admitted to the record |
| Prosecutor | Presents the case against the accused | the case evidence |
| Defence | Challenges the prosecution, cross-examines | the case evidence |
| Plaintiff | The claimant (civil matters) | the case evidence |
| Accused | Responds, may assert innocence | evidence, minus their own sealed confession |
| Witness | Testifies to what they personally saw | only evidence linked to them |
| Investigator | Supplies facts from the investigation | the case evidence |
| Expert witness | Neutral technical assessment | the case evidence |
| Custom | Anything else | as a witness |

## Modes

A **courtroom** proceeding follows trial stages. A **deposition** has a questioner and a
deponent. A **strategy** session has no judge and no fixed order. See
[How it works]({{ '/how-it-works/' | relative_url }}) for the stages.

## The agent graph

Agents are nodes in a graph. The predefined cast are the roots. During a proceeding an agent
can *spawn* another (a judge appointing an expert) and the orchestrator can spawn one itself
when a forensic topic arises with no expert present. Spawned agents record who called them and
why, and appear in the spawn graph.

## Role-scoped retrieval

Retrieval is a permission, not just a search. A query goes to the case's vector collection and
the results are filtered by the role's rule before the agent sees them. A witness cannot
retrieve a document they were never linked to, however their question is phrased.

## Citations

An agent marks evidence it relies on with `[EVIDENCE:<id>:<chunk>]`. The platform resolves each
marker to the stored passage and shows it as a chip. A line with at least one resolved marker
is *cited*; a line with none is *inferred*; a line a human has overridden, or whose cited law is
provably wrong, is *disputed*.

Separately, **legal authorities** (sections, articles, cases) are verified against the
jurisdiction pack. The two are different things: an evidence citation says *where in the file*
a claim comes from; an authority citation says *what law* is relied on.

## Jurisdiction packs

A pack describes a jurisdiction: its acts and their last valid section numbers, an index of
provisions and landmark cases, and a concordance from repealed to current law (IPC to BNS,
for example). A case selects its pack by country. See [Legal accuracy]({{ '/legal-accuracy/' | relative_url }}).

## Procedure

A set of stages for a mode, a turn budget divided among them, and rules for who speaks. It is a
pure function of the turn number, so it survives the worker being restarted between turns.

## The audit chain

An append-only, hash-linked log of what happened in a proceeding. It records provenance
(model, prompt hash, response hash, passages retrieved) and not content.

## Turn, proceeding, override

A **turn** is one agent's contribution. A **proceeding** is a run of a case in a mode. An
**override** is a human replacing a turn's text for display: the agent's original words are
kept, the turn is labelled, and the audit chain records both fingerprints.

## Firms, members, roles

A **firm** is the tenant: it owns cases, evidence and proceedings and has one subscription.
**Members** belong to it as *owner*, *admin* or *attorney*. The platform operator is separate
and is not a member of any firm by virtue of that role. See [Firms and access]({{ '/firms-and-access/' | relative_url }}).

## Plans and entitlements

A **plan** is a set of limits: seats, simulations per month, tokens per month, turns per
proceeding, storage. A **subscription** attaches a plan to a firm with a status, a number of
seats and a paid-until date. **Entitlements** are those limits enforced by the server at the
points where they matter.
