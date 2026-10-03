---
title: Home
nav_order: 1
permalink: /
description: Nyayrithm is a multi-agent courtroom simulation platform for law firms. AI counsel argue a case from the evidence you give them, every claim traced to its source.
---

# Nyayrithm

<p class="nc-lede">
A firm uploads the evidence in a matter. A court of AI agents, each playing a legal
role with its own knowledge and its own model, argues it out. Every claim points back to
the passage it came from, every legal citation is checked, and the whole proceeding is
kept in a record that cannot be quietly rewritten.
</p>

<div class="nc-actions">
  <a class="primary" href="{{ '/product-tour/' | relative_url }}">Take the tour</a>
  <a href="{{ '/how-it-works/' | relative_url }}">How it works</a>
  <a href="{{ '/running-locally/' | relative_url }}">Run it yourself</a>
</div>

---

## The problem

Preparing a case is mostly imagining the other side. What will the prosecution lead with?
Where will cross-examination find the soft spot in this witness? Which exhibit does the
judge keep asking about? Moot rooms and mock trials answer those questions, but they cost
a day of several people's time, and they happen once.

General-purpose chatbots are cheap and fast, and they are unsafe for this work for three
reasons. They answer from everything they have ever read, not from *this* record. They
cite law that does not exist with complete confidence. And nothing they produce can be
audited afterwards.

## What Nyayrithm does about it

| | |
|---|---|
| **Argues from your record** | Evidence (PDFs, Word files, scans, photographs, audio, video) is read, transcribed and indexed. Each agent retrieves only what its role is allowed to know. |
| **Plays the whole court** | Judge, prosecutor, defence, accused, witnesses, investigator, expert. Agents can call in specialists mid-hearing, and every seat can run on a different model. |
| **Keeps procedure** | A courtroom runs in stages: opening, charge, evidence, cross, closing, judgment. An objection hands the floor to the judge for a ruling. |
| **Checks its own law** | Every statute, article and case an agent cites is verified against a jurisdiction pack. Citations that cannot be right are flagged, and the agent is told so. |
| **Leaves a record** | Each turn's prompt, model and sources are hashed into a tamper-evident log, and one click re-checks it. |

## Built for firms

Nyayrithm is sold to firms, not individuals. A firm takes out a subscription, invites its
attorneys, and works inside its own walled workspace. Owners manage the team and the plan,
attorneys work on their own cases and the ones shared with them, and the platform operator
runs the service without ever seeing what a firm is working on.

[How firms, roles and invitations work]({{ '/firms-and-access/' | relative_url }})

## Honest about what it is

Nyayrithm is a **simulation and preparation tool**. It does not give legal advice, does not
predict outcomes, and its agents can be wrong. The legal checks prove that a citation
*cannot* be right; they never prove that an argument is sound. The bundled Indian pack is a
starter index, not the statute book. Read [what the platform can and cannot promise]({{ '/trust-and-security/' | relative_url }}) before relying on any of it.

## Where to go next

| If you want to | Read |
|---|---|
| See what it does, screen by screen | [Product tour]({{ '/product-tour/' | relative_url }}) |
| Understand how a proceeding actually runs | [How it works]({{ '/how-it-works/' | relative_url }}) |
| Know the aims and the limits | [Vision and aims]({{ '/vision/' | relative_url }}) |
| Run it on your own machine | [Running locally]({{ '/running-locally/' | relative_url }}) |
| Put it in front of a firm | [Deployment]({{ '/deployment/' | relative_url }}) |
| See what comes next | [Roadmap]({{ '/roadmap/' | relative_url }}) |
