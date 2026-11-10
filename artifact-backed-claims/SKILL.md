---
name: artifact-backed-claims
description: "Use when stating a finding. Ship proof, not prose."
version: 1.0.0
author: Fauzi Susanto
license: MIT
metadata:
  hermes:
    tags: [verification, evidence, bug-bounty, reporting, discipline]
    budget_kb: 20
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Artifact-backed claims

A finding is not what you concluded. It is what someone else can reproduce from the
artefacts you left behind.

This skill governs the moment between "I observed something" and "I told the operator or
the vendor what it means". Most bad reports and most wrong conclusions die here.

## When to Use

Load this skill when:

- You are about to state a technical finding, confirm one, or write it into a report.
- The operator asks for proof, asks "ad sampelnya?", or says your claim "cm kamu tulis aja"
  (that was just you writing it).
- You are about to conclude something is **not** reachable/exploitable — negative results
  need controls too.
- A finding's artefact might belong to a party outside the engagement target.
- You are about to claim impact beyond what the raw response actually shows.

Do NOT use for exploratory recon notes with no claim attached.

## The two rules

### 1. Every claim carries a re-runnable artefact

When the operator asks for proof, a written summary of what you found is **not** proof.
They said it plainly after a bucket finding was described in prose only:

> "td itu cm kamu tulis aja" — that was just you writing it.

Deliver, together:

| Artefact | Why |
|---|---|
| The raw response / file itself (attachment via `MEDIA:<abs path>`) | They can look at it without trusting you |
| The exact command that produced it, copy-pasteable | They can re-run it and get the same bytes |
| `sha256` of each retrieved file | Ties the artefact to the transcript; catches drift between capture and report |
| A saved transcript file (`evidence/PROOF-<topic>.txt`) | Survives the chat; re-runnable months later |

A claim in chat with none of the above is a draft, not a finding. Label it as such
("observed, not yet evidenced") rather than stating it as fact.

### 2. Every claim ships with the control that kills the boring explanation

Before believing an anomaly, ask what mundane thing would produce the same observation —
then test that. A signal without its control is not evidence.

- **Encoding control** — if a probe 404s, re-probe one case with the naive/obvious input.
  A `%2F`-encoded object key returns 404 while the plain path returns 200; the bug was the
  probe, not the bucket. See `references/negative-controls.md`.
- **Blanket-cache control** — a listing that appears open must return 404 for a random
  key, or it is a catch-all responder, not an exposure.
- **Ownership control** — a name matching your target is not ownership. Attribute from
  content or explicit config, never from the name.
- **Population control** — if you invented the input set (guessed IDs, guessed
  addresses), an answer about it says nothing about the system. Confirm identifiers came
  from the system itself.

## Never claim content you did not read

A folder was named `driving_licence_user`, so it read like a KYC leak. The retrievable
files were a stock photograph and a chat-app export. Asserting "customer licences are
exposed" would have been false on the evidence.

State the reachability you proved and stop:

> "objects under a folder named `driving_licence_user` are publicly retrievable (HEAD 200,
> N bytes, image/jpeg, JPEG magic bytes verified); I did not read their contents."

Fingerprinting substitutions that satisfy the proof requirement without opening the
document: `HEAD` (status, size, ETag, type) plus a **4-byte `Range`** for magic bytes.
That is the minimum that demonstrates reachability and stays inside the usual
safe-harbour clause ("do not access data beyond what is needed to demonstrate the issue").

## State boundary and uncertainty in the same message as the claim

Where a chain is only partly built, say which link is missing in the same breath as the
finding — not in a footnote after the vendor has already read an inflated title:

> "What I proved: X (evidence). What I am NOT claiming: the prediction/recovery chain —
> it was not executed end to end."

This is what keeps a "Low/Medium with honest limits" report accepted instead of a
retracted Critical. A candidate that does not reproduce on re-test is **unstable** — do
not report it; record it as excluded with the reason.

## Verification ladder — before the word "confirmed"

```
[ ] Probed from a clean session (not reusing a cached/authenticated state)
[ ] Re-verified 3x; disagreements recorded as UNSTABLE, not averaged away
[ ] Control for the boring explanation executed (see rule 2)
[ ] Raw artefact + command + sha256 on disk
[ ] Operator can re-run every line without asking a follow-up question
[ ] Reading the artefact does not exceed the programme's "minimum needed" limit
[ ] Claim text stops exactly where the evidence stops
```

## Third-party assets

If the artefact turns out to belong to someone who is not the engagement target, the
finding does not transfer. Escalate to the operator, mark it
`excluded — third-party asset, ownership elsewhere`, and do **not** submit it to the
engagement's vendor channel. Submitting a third party's misconfiguration to the wrong
company ends the engagement.

## Related

- `triage-validation` — the 7-question gate that runs before any report.
- `evidence-hygiene` — capture-and-redact protocol for PoC evidence.
- `bug-report-delivery` — report/PDF/draft mechanics once a claim clears this ladder.
- `references/negative-controls.md` — concrete control recipes, incl. the S3 `%2F` trap and
  the bucket-ownership attribution table.