# Forensic audit summary
**Prepared for:** Mehra Textiles Pvt. Ltd.  |  **By:** K. Banerjee & Associates, forensic accountants
**Date:** 12 March 2026  |  **Status:** summary of findings, not a certificate

## Scope
Review of the net-banking audit trail for transaction **6190442211** (IMPS, Rs 18,00,000, to
Vikram Kulkarni) and the company's two-authoriser mandate.

## Findings
1. **Initiation.** The payment was created (maker step) on **1 March 2026 at 23:49** from an
   internet address that belongs to the company's office broadband, not a residential
   connection. The maker credentials are Sanjay Kulkarni's.
2. **Release.** The IMPS debit posted on **1 March at 23:52**.
3. **Second authorisation.** The bank's approval log records the checker approval **on
   2 March at 08:40**, using Rohit Mehra's security token serial ending 4471. The approval
   therefore post-dates the debit by almost nine hours. The bank has not yet explained how a
   debit can precede its approval; a configuration allowing "approve after release" for
   existing beneficiaries is suspected but unconfirmed.
4. **Token location.** The token's last login metadata shows a device fingerprint registered
   to the office, not to Surat. We have not examined the physical token.
5. **Beneficiary.** Vikram Kulkarni was added as a beneficiary on **1 March at 23:41**, eight
   minutes before the payment was created, by the same maker credentials.
6. **Repayment.** Rs 6,00,000 was credited from Vikram Kulkarni on 9 March 2026.

## Limitations
* We have not interviewed the bank.
* We cannot say who physically used the token.
* Timestamps are in IST as reported by the bank and have not been independently verified.
