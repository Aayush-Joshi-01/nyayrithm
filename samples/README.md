# Sample material and a test walkthrough

Everything here is fictional. It exists so you can try every part of Nyayrithm on a case that has
real texture: a dispute of fact, a gap in the paperwork, a timestamp that doesn't add up, and
citations that are deliberately wrong.

```
samples/
  state-v-kulkarni/     nine evidence files for one criminal breach of trust case
  legal-check-demo.txt  a paragraph of correct and incorrect legal citations
```

## The case: *State v. Sanjay Kulkarni*

**Charge:** criminal breach of trust (BNS section 316), Delhi.
**Facts:** Sanjay Kulkarni, chief accountant of Mehra Textiles, moved Rs 18,00,000 of supplier money
to his brother Vikram late on 1 March 2026. He says the director, Rohit Mehra, agreed to a short
loan. Mehra says he never did, and that he was in Surat with his phone off.

| File | What it is | What to look for |
|---|---|---|
| `01-fir-118-2026.txt` | The FIR | The complainant says the transfer was "on the night of 1 March". |
| `02-statement-rohit-mehra.txt` | Complainant's statement | Says he did not message the accused, and that his security token was with him in Surat. |
| `03-statement-sanjay-kulkarni.txt` | The accused's statement | Says a phone call at 9 pm authorised a loan. Says he did not use Mehra's token. |
| `04-statement-priya-nair-accounts-assistant.txt` | A colleague | Says the approval showed on **2 March at 8:40**, which "looked odd". |
| `05-bank-statement-mehra-textiles.csv` | Bank statement | Debit at **1 March 23:52**; the second approval is logged at **2 March 08:40**. |
| `06-whatsapp-export-mehra-kulkarni.txt` | Chat export | "Do what is needed, will see on Monday" at 21:14 (not a phone call). **No certificate** under BSA section 63. |
| `07-forensic-audit-summary.md` | Forensic accountant | The debit *precedes* its approval by nine hours. The token's device fingerprint is the office, not Surat. |
| `08-company-bank-mandate.pdf` | Bank mandate (text PDF) | Two-authoriser rule above Rs 5 lakh; 24-hour cooling period for new beneficiaries. |
| `09-loan-acknowledgement-photo.png` | Photographed note (image only) | Needs OCR. Vikram acknowledges the loan and a Rs 6 lakh repayment. |

**Planted tensions** a good proceeding should surface:
1. *Phone call vs. WhatsApp.* The accused says a call; the record shows a message. Mehra says no contact at all; the chat shows he replied at 21:14.
2. *Debit before approval.* The money left 9 hours before the second authorisation. Who benefits, and what does the bank's explanation need to be?
3. *The token.* Mehra says it was with him; the audit says it was used from the office.
4. *Cooling period.* A new beneficiary was added 8 minutes before the payment, against the mandate.
5. *Electronic evidence.* The WhatsApp export has no section 63 BSA certificate. Does the defence's best document survive?
6. *Intent.* Part-repayment on 9 March and a signed acknowledgement point away from dishonest intention.

## 1. Sign in

Start the stack (`make dev` or `make dev-creds`; see [Running locally](../docs/pages/running-locally.md)).

| Mode | Firm portal `:3000` | Admin portal `:3001` |
|---|---|---|
| **Open** (`make dev`) | no login; you are the owner of "Dev Firm" | no login; you are the dev platform admin |
| **Credentials** (`make dev-creds`) | sign in as **Firm owner** or **Attorney** | sign in as **Platform admin** |

In credentials mode the login screen lists the development accounts. **Click one and the form fills
itself.** The same accounts are defined in `keycloak/realm-dev.json` and `.env.dev`.

Switch modes any time with `make dev` / `make dev-creds`. Other tools: Mailpit (invitation emails)
<http://localhost:8025>, API docs <http://localhost:8000/docs>, Keycloak console <http://localhost:8080>.

## 2. Load the case

**In the UI (firm portal):**
1. *Cases → New case.* Title `State v. Sanjay Kulkarni`, country **India**, jurisdiction `Delhi`.
2. Open it, go to *Evidence*, and drag in all nine files from `samples/state-v-kulkarni/`.
3. Wait until each shows **indexed** (the PNG takes a few seconds longer: a vision model reads it).
4. Use the evidence search: *"who approved the transfer and when"* and *"loan acknowledgement signed by Vikram"*.

> Country must be India (or `IN`): that selects the jurisdiction pack used to check the law.

## 3. Run a proceeding

*Case → New proceeding.* Suggested runs:

| Run | Settings | What to watch |
|---|---|---|
| **A. A short trial** | Courtroom, **12 turns** | The stage bar moves opening → charge → evidence → … → judgment; each line shows its stage. |
| **B. A fuller trial** | Courtroom, **40 turns** | Cross-examination of the witness; objections handing the floor to the judge; a reasoned judgment at the end. |
| **C. A deposition** | Deposition, 16 turns | Questions to the deponent, cross, re-examination. |
| **D. Defence strategy** | Strategy, 12 turns | No judge; counsel, an investigator and an expert weigh the timestamps. |

Press **Start** and watch it stream. Then try:
- **Citations:** click an evidence chip to open the exact passage it rests on.
- **Authorities:** click the chips under a line. Real sections show *in the index*; the old IPC shows *repealed → BNS*.
- **Provenance** in the left margin: *cited*, *inferred* or *disputed*.
- **Recess / Adjourn / Resume**, and **clone** a finished proceeding to run it again.
- **Override** a line (pencil icon). The original stays, the line is marked *overridden*.
- **Verify record** (bar above the record): *record intact, N events*.

## 4. Check the legal checker directly

Paste the contents of `legal-check-demo.txt` into the API (Swagger UI at `/docs` → `POST /api/v1/legal/verify`,
authorise with a token, or use the call below). Expected result:

| Citation | Verdict |
|---|---|
| Section 316 BNS, Section 318 BNS, Section 63 BSA, Article 21 | in the index |
| Section 406 IPC | repealed; corresponding provision is BNS 316 |
| Section 9999 of the BNS | **does not exist** (the act ends at 358) |
| Article 500 | **does not exist** |
| *Arjun Panditrao Khotkar* (2020) 7 SCC 1 | in the index |
| *Ramesh Kumar v. State of Haryana* (1978) 1 SCC 248 | **citation does not match** (that cite is *Maneka Gandhi*) |
| *Rajesh Verma v. State of Nowhere* (2019) 4 SCC 123 | could not be verified |

## 5. Test firms, roles and invitations (credentials mode)

1. **Attorney sees little.** Sign in as *Attorney*: the case list is empty. As *Firm owner*, open the case, share it with the attorney (API: `POST /cases/{id}/members`), and it appears.
2. **Invite someone.** As owner: *Team → Invite an attorney*, enter `new.hire@example.test`. Open **Mailpit** (`:8025`) for the email, or copy the link shown. Open it in a private window, create an account with that exact address, and accept.
3. **Wrong person.** Open the same link while signed in as a different user: it is refused. Re-using an accepted link: refused.
4. **Seats.** *Plan & usage* shows seats used. In the admin portal lower the firm's seats to the number in use and try inviting again: it is refused.
5. **No firm.** Register an account that has no invitation: the portal explains it needs an invitation.

## 6. Test the admin portal

Sign in at `:3001` as *Platform admin*.
- **Firms → New firm:** create "Rao Chambers" on the *Trial* plan with an owner email; the invitation link is shown.
- **Subscription:** set a firm to *past due*, then try creating a case as one of its members: blocked. Set it back to *active*: works at once.
- **Suspend** a firm: its members are locked out immediately. **Reactivate** it.
- **Plans:** edit *Trial* and set tokens per month very low (for example 2,000), run a proceeding in a firm on that plan, and watch it **pause itself** with a message about the token allowance.
- **LLMOps:** after any run, look at requests, tokens, estimated cost, latency, the breakdown by role and by model, and the quota table. Override a model's price under *Prices* and watch new estimates change.
- **System:** every service should be green. Stop one (`docker compose stop qdrant`) and see its row go red, then start it again.
- **Activity:** every change you made above is listed with your name.
- **What you cannot see:** open a firm's detail page. You get counts and usage, never case titles or content.

## 7. Security spot checks

```bash
curl -i http://localhost:8000/api/v1/cases/                         # open mode: works; credentials mode: 401
curl -i -H "Authorization: Bearer forged.token.here" http://localhost:8000/api/v1/cases/   # 401
```
As the attorney, request a case you don't have: **404**, identical to an id that never existed.
As the firm owner, request `/api/v1/admin/overview`: **403**.

## Reset

`make reset` wipes everything (databases, vectors, uploaded files, Keycloak users) and starts clean.
