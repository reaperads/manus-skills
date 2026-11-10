---
name: financial-logic-verification
description: "Verify a money-handling product's computed figures against the authoritative domain rules (tax, fees, interest, entitlements) using its own itemised output as the oracle."
version: 1.0.0
author: hermes
license: MIT
metadata:
  hermes:
    tags: [tax, business-logic, arithmetic, compliance, fintech, hmrc, verification, bug-bounty]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Financial / Tax Logic Verification

Use when the target computes money: tax software, payroll, billing and invoice engines, fee
and interest calculators, payout/settlement logic, entitlement maths. The question is not
"can I break the endpoint" but **"is the number it shows correct, and what does being wrong
cost the user"**. This is a product-correctness class, not a security class — and it is where
tax and fintech engagements actually produce value once the injection/IDOR surface is clean.

This operator asks for it explicitly and repeatedly on financial SaaS: *"review kepatuhan
aturan pajak … diverifikasi ke sumber resmi, bukan cuma bug teknis"*. Assume it is in scope
whenever the product touches a regulator's rules.

## The oracle: never grade the app against your memory

Two sources, and you need both before you test anything:

1. **The rule** — from the authority, not from the app's marketing. gov.uk / HMRC internal
   manuals (PIM, BIM, HS helpsheets), the regulator's published tables, the fee schedule.
   Write the expected arithmetic by hand, with the specific numbers you are going to enter.
   If you cannot state the expected figure to the penny before you run the scenario, you are
   not ready to test.
2. **The product's own itemised breakdown** — the dashboard estimate, the P&L card, the
   invoice line items, the CSV/Excel/PDF export. This is the oracle you compare against. It
   is also the best evidence for the report: the vendor cannot argue with their own export.

Two bonus sources that make a report land better:
- **The vendor's own public calculators / guides / FAQ.** They encode the vendor's stated
  understanding of the rule. If the app contradicts its own calculator, that is a very strong
  bug argument ("your public Section 24 calculator applies the 20% reducer; the ledger does
  not"). If they contradict the authority, quote both.
- **The plan boundary.** Many of these panels are paid-tier only. Check what a free account
  shows before concluding "the estimate ignores X" — it may just not render that panel.

## Method

1. **Harvest the rules.** Read the vendor's guides, FAQ and public tools; then pull the
   authoritative rule and write the expected figures down. Keep them in a reference file
   (see `references/uk-landlord-tax-rules.md` for the UK landlord set, with worked examples).
2. **Build a controlled scenario, one variable at a time.** A fresh property/source/invoice,
   exact amounts posted through the API (bulk post beats UI typing for precision), and a
   positive control that must not move.
3. **Read the itemised output.** Capture the whole breakdown block, not just one figure — the
   label text often contradicts the arithmetic and is itself the bug.
4. **Minimise with a pair.** "Rent £60,000 + interest £20,000" tells you less than
   "£60,000 alone" versus "£60,000 + £1 of interest": the pair isolates which input changes
   which line.
5. **Convert the delta into money at each band.** "Taxable is £1,000 too high" is abstract;
   "£200 too much at 20%, £400–£450 at 40/45%" is a finding. Always state the rate(s) used.
6. **Decide the class honestly.** Arithmetic errors that only affect the user's own figures are
   product-correctness defects, not access-control findings — say which it is, and check
   whether it is arguably by-design before writing it up.
7. **Clean up and verify.** Delete the probe sources and entries, restore any share/percentage
   you changed, then read the state back through the API. Vendors lend accounts; leave them as
   found and say in the report what you created and removed.

## Pitfalls that produce wrong conclusions

- **Aggregates poison isolation.** The account-level estimate sums every source. Once three
  probe properties exist, "income £130,000" tells you nothing about the scenario you just
  built. Either delete between scenarios or read the per-source panel.
- **A floored estimate hides the effect.** If the computed liability is already £0, adding a
  legitimate deduction cannot visibly change it — the screen shows £0.00 before and after.
  Raise income until the tax is clearly positive before testing whether something reduces it.
- **"No error message" is not "accepted".** Read the raw response. On RSC/Server-Action apps
  the real error lives in the flight segment (`1:{"error":"..."}`); a plain page render with no
  visible error often means a silent no-op. Capture it with `page.on("response")`.
- **A validation error may be about your test value, not the logic.** We concluded "replay
  prevented" from an action that had actually failed because the test identifier was
  invalid (a check-digit suffix). Always run a positive control — same action, same code path,
  a value you know is accepted — before attributing a failure to the rule you were testing.
- **Do not hand-compute with the wrong tax year or band.** Rates change annually; state the
  year you assumed and cite the source. Off-by-one-year assumptions are how you write a false
  positive against a tax product.
- **Regulator-gated features are legitimately untestable.** If the arithmetic sits behind a
  connection to the authority that you are not allowed to make, do not fake it — report it as
  untested, explain the gate, and cite the vendor's public calculator for the rule set.

## Reporting shape that works

- Lead with what is **correct** (the verified-working list). It is the reason a vendor trusts
  the rest, and it is genuinely useful to them.
- Each issue: scenario, the app's own output verbatim, the authoritative rule, the corrected
  figure, the money delta per band, and — where it exists — the vendor's own copy that
  contradicts the behaviour ("we've used whichever saves you more").
- Bundle cosmetic/UI defects (wrong example in an error message, a fabricated status string,
  a duplicate element id) into one paragraph rather than separate reports; they are real but
  they are not findings.
- Keep "not tested / gated" separate and explicit. Never let an untested area read as clean.