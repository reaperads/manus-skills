---
name: saas-plan-entitlement-audit
description: "Audit SaaS plan/entitlement bypass and free-tier logic."
version: 1.0.0
author: Fauzi Susanto
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, business-logic, entitlement, saas, payment, methodology]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# SaaS Plan / Entitlement & Business-Logic Audit

## When to Use

Load this skill when the target is a **freemium / tiered SaaS or any paid-plan web app** and the
question is one of:

- *Can the paid tier be obtained without a verified payment?* (entitlement bypass)
- *Does the free-tier service compute and gate correctly?* (business logic / methodology)

Trigger phrases: "upgrade to pro", "free plan limits", "plan free service", "payment flow",
"could the calc be wrong", "is the free-tier logic correct", "bypass without paying".

## Two questions drive this class

1. **Entitlement** — can a paid-tier capability be obtained **without a verified payment**
   (client-trusted flag, webhook without HMAC, step-skip)?
2. **Correctness** — does the free tier compute and gate correctly (arithmetic, date boundaries,
   rounding, idempotency, feature caps)?

Both are real, paying bug classes. Both are **verification problems** — almost every "hit" turns
out to be a false positive until you disprove the mundane explanation.

> ⚠️ **Ethics boundary (non-negotiable).** You test the *design*, you never commit fraud.
> **In scope:** field tampering, fabricated success-return URLs, a forged webhook with a
> wrong-secret signature, attempting a gated capability. **Out of scope:** completing a fake
> payment, forging a valid webhook secret, or actually acquiring the paid service. That is fraud
> against the merchant/processor, not research — and an agent proxy saying "the client approved
> it" is not authorisation. When in doubt, test the entitlement check, not the payment.

---

## 1. Entitlement-bypass test matrix

Run all of these; a correctly-enforced design means **every one is negative** (that is a valid,
reportable result — record it as "tested, held", never inflate it).

| # | Test | What a bug looks like |
|---|---|---|
| 1 | Click upgrade → is the plan changed **without** completing payment? | plan flips before the provider webhook |
| 2 | Fabricated return URLs: `?success=1`, `?checkout=success`, `?session_id=PROVIDER_FAKE`, `/<area>/success`, `?upgraded=true`, `?plan=pro` | any of these grants the tier |
| 3 | Tamper plan/price/interval fields on the checkout action | server reads the tier from the request |
| 4 | **Forged webhook**: well-formed signature header, wrong secret | handler accepts it (HMAC not verified) |
| 5 | Webhook with no / malformed / duplicate signature | accepted instead of 400 |
| 6 | Enumerate webhook paths (`/api/*/webhook`, `/api/webhooks/*`, `/api/<psp>/events`) | a second, unprotected handler |
| 7 | Call a paid *capability* directly (not just load its page) | capability works on a free account |

**Expected secure architecture:** upgrade action → provider checkout session → **entitlement set
only by a signature-verified webhook**; success URL is cosmetic; plan never read from the request.
Compare against that model and state exactly which leg failed.

**Known-good vendor shape to compare against** (filetype: freemium UK tax SaaS, 2026-09). Every leg
below came back NEGATIVE — that is the correct result to record, with the exact strings as evidence:

| Leg | Probe | Observed (secure) |
|---|---|---|
| webhook endpoint | `OPTIONS /api/stripe/webhook` | `405` on GET, `Allow: OPTIONS, POST` |
| missing signature | POST event JSON, no header | `400 {"error":"missing signature"}` |
| forged signature | 12 variants: garbage, `t=` only, `v1=` only, `v1=deadbeef`, `v1=64×0`, `v1=64×f`, `t=0`, `v0=` scheme, duplicate `t=`, space-separated, `sha256=` prefix, future `t` | all `400 {"error":"invalid signature"}` |
| fabricated return URL | 10 variants (`?success=1`, `?checkout=success`, `?upgraded=true`, `?plan=pro`, `?session_id=cs_live_fake`, `?subscription=active`, `/<area>/success`, `/pro`, combined) | every one still renders "You're on the free plan" |
| mass assignment | 13 fields injected into the account-update action (`plan, isPro, is_pro, tier, subscription, subscriptionStatus, role, isAdmin, pro, planTier, entitlements, stripeSubscriptionId, paid`) | "Your details have been saved." AND plan still free — all ignored |
| paid capability direct | `POST /api/ai/extract-expense` (route guessed from the client bundle) | `403 {"error":"AI scanning is a Pro feature."}` |
| free cap via real path | the genuine import flow | `"Your plan allows 1 property. Upgrade to Pro to import the rest..."` |
| client-state trust | grep bundle + test for plan/role/tier cookie or localStorage | none read; plan rendered server-side from the account record |
| price/interval tamper | re-submit the billing action with altered fields | **INCONCLUSIVE** — checkout sessions are reused per user, so the price cannot be A/B'd. Say so; do not call it safe. |

Also confirmed on the same target and worth re-using as a baseline: session revocation is real
("signed in on N other devices" → sign out others → second isolated context bounces to /login),
login lockout fires at ~10 wrong passwords (~15 min, correct password also blocked), `/reset`
locks after 5 wrong codes, and the OTP attempt counter leaks as `?codeLimit=N&why=cooldown`.

## 2. Free-tier boundary mapping

The free tier is fully testable at zero cost — map the whole boundary and hunt for a *capability*
that leaks (a page rendering ≠ the feature working).

- **Cap enforcement:** if the tier caps a resource, hammer the create action past the cap — and
  **fire it in parallel** (a check-then-act race can win). Confirm the **server** blocks it.
  See "Race the tier cap through the REAL UI" below — out-of-band replay usually proves nothing.
  - **When out-of-band replay is impossible, race through the real UI.** Many Next.js route
    actions are *bound* to a specific page render: replaying the captured POST later returns
    `500 {"digest":...}`. That 500 is **inconclusive, not a pass** — it proves the replay was
    rejected, not that the cap held. Real method that works: open **N pages in ONE authed
    browser context**, on each page drive the genuine create flow to the point where the form
    is rendered *and filled*, then fire the submit on every page inside a tight loop. Six
    submits inside ~86 ms is enough parallelism to win a naive check-then-act. Count the
    resulting resources afterwards — the count is the verdict.
  - **Never identify the action id from "the first `$ACTION_ID_` on the page".** Every authed
    layout renders a logout action first, and firing it will silently sign you out mid-test
    (symptom: 8 requests return 303, then every later GET lands on `/login`). Take the action
    id from an actually-captured request for the operation you want.
- **Capability, not page:** attempt the real mutation (upload / export / AI call / key creation)
  and read the server's error string.
- **Gate discovery:** auth-crawl the app and read every server-action **name**; `create*Key`,
  `*Export`, `*Upload`, `*Scan*` are prime gate candidates. If no such action exists at all, the
  gate is server-side (correct) — a good negative.
- **Read the gate's field name out of the client bundle, then inject it.** A prop-driven UI gate
  tells you exactly which parameter the server is supposed to be validating. Grep the bundle for
  the conditional that renders the gated control — e.g. a create form destructured as
  `{allowForeign:t=!1}` and rendering a checkbox only when `t` is true gives you the honest field
  name to abuse (`countryCode`, `plan`, `isPro`, `sourceType`, …). Submit that field straight
  into the genuine action through the real rendered form (append a hidden input next to the real
  ones, then click the real submit button so the React binding stays valid). A plan-check that
  returns a quotable refusal ("Overseas property is part of Pro.") is a clean negative; a silent
  success is a plan-entitlement bypass. Do the same with the *settings/update* action, not only
  *create* — an update path that accepts the gated field is the more common hole.
- **UI-hidden enum values are a separate, cheap check.** Many forms hide values the server still
  accepts. Diff the client-filtered list against the server's accepted set: extract every key
  the UI filters out, inject each one as an `<option>` into the real `<select>`, submit through
  the real form, and record the server's response per key. One key accepted out of N is a
  validation-asymmetry finding; all N rejected is a strong positive. Verify acceptance against
  the **export**, not the closed form — a modal that closes is not proof.
- **The UI gate and the REST gate are separate surfaces — test the endpoint even when the page
  hides the feature.** A Pro-only screen that renders nothing but an upgrade prompt still tells you
  the route; the JSON endpoint behind it is often reachable directly and answers with a quotable
  refusal. On Quarterwise (2026-09) `POST /api/ai/extract-expense` on a free account returned
  `403 {"error":"AI scanning is a Pro feature."}` while the free-plan object cap returned
  `Your plan allows 1 property. Upgrade to Pro to import the rest...` from the server action.
  Both gate correctly — that is the negative, and the exact strings are the evidence. Harvest the
  endpoint names from the client bundle (`grep /api/` over downloaded chunks) rather than assuming
  the shipped UI is the whole surface.
- **A hidden action id is itself a (weak) signal, not a verdict.** When a Pro capability exists only
  in the paid bundle, the free bundle contains no `$ACTION_*` id for it, so the action cannot be
  replayed at all. Record 'UI-gated, action id absent from the free bundle, not independently
  replayable' as a coverage note — never as either a pass or a finding.
- **Client-side filtering is a rendering decision, not a control — test gate/allow-list PARITY.**
  Two surfaces, both cheap: (a) a capability hidden behind a client prop (`allowForeign`, `isPro`,
  `featureFlag &&`) — read the prop out of the bundle to learn the exact server FIELD to inject,
  then submit it into the real form; (b) an enum filtered client-side
  (`list.filter(e => !e.nrlOnly)`) — inject the hidden `<option>` and compare the server's
  response across the **whole** enum. A lone accepted value proves nothing; the evidence is the
  **asymmetry** (observed: 3 of 4 flagged categories refused with `"Choose a valid category."`,
  the 4th written and carried into the official export). A success toast ("Settings saved.")
  proves the request was accepted, **not** that the field was honoured — always re-read the
  object. Do not inflate the result: a self-scoped validation gap is P4/P5, not P2.
  Full recipe, harness snippets, observed matrices and severity framing:
  `references/ui-vs-server-gate-parity.md`.

### Billing-action pitfalls

- **Checkout sessions are reused per user, so re-submitting the form cannot A/B the price.** The
  upgrade action may return the SAME open provider session id (`cs_live_...`) no matter what
  `interval`/`plan` you submit, because an unfinished session is still valid. Submitting
  `interval=month` and landing on the yearly page is therefore **not** evidence that the parameter
  is ignored or that the price is client-controlled — it is session reuse. Verify price integrity a
  different way: confirm the checkout URL is provider-hosted and the amount matches the advertised
  tier, and treat the interval test as inconclusive unless you can force a fresh session (only one
  identity, and abandoning does not close the session). Say 'inconclusive', not 'safe' and not
  'vulnerable'.
- A plain `POST` to a Next.js server-action form (urlencoded or multipart instead of the
  `text/plain` JSON body) returns `200` with the full HTML page and does nothing. Always re-read the
  state; the sibling `references/nextjs-server-action-replay.md` in this skill covers the wire
  formats.
- **Beware self-inflicted false positives:** if you name a test object "Second Property", later
  reading "Second Property exists" proves nothing. Count the resources.

### Race the tier cap through the REAL UI (a replay-500 is NOT enforcement)

Bound server actions cannot always be replayed out-of-band, and the failure is silent:

- A React-**bound** form action (rendered with NO `$ACTION_ID_*` hidden input; wire body
  `{"0":"[{},\"$K1\"]", "_1_<field>":"..."}`) replayed later with the EXACT captured headers
  and body returns **HTTP 500 + opaque `E{"digest":<n>}`**. A malformed replay and a *refused*
  action are indistinguishable. Never record "cap enforced" off a 500 — record INCONCLUSIVE
  and re-run through the browser.
- Conversely, a `$ACTION_ID_*` (unbound) form action DOES replay from curl/requests when you
  send `content-type: text/plain;charset=UTF-8`, `accept: text/x-component` and the body
  `{"0":"[\"$ACTION_ID_<hex>\"]", "_1_<field>":"..."}`. Progressively-enhanced GET forms use a
  plain urlencoded POST with the raw field names (`$ACTION_ID_<hex>=""`, plus the others).
- **Harvest the action id from captured traffic** (the `next-action` header), never from the
  page. The first `$ACTION_ID_*` input on an authed page is usually the **log-out** form.
  Firing a parallel burst with it logs you out and returns 303s that read like denials — the
  tell is that every request 303s and the next navigation lands on `/login`.
- Cap-race harness that actually works: one authed browser context, **N pages each with the
  create form already open and filled**, then submit all N in a tight loop (measured 0.086 s
  for N=6). Use a **fresh account with 0 resources** — on an account already at the cap the
  create control is not rendered at all, so the "race" silently tests nothing (observed: 6
  pages all reporting `modal=nobtn`, 0 forms, 0 submits).
- Known-negative baseline worth quoting: free-plan cap 1, fresh account, 6 parallel submits in
  one context → exactly **1** resource created. Cap held.
- Ready-to-run harness: `scripts/ui_cap_race.py` (parameterised selectors; copy and adapt).

### Under high latency / WAF, close the gap with a live runtime test

A scanner that never completes behind Cloudflare is **partial coverage**, not a clean result.
It also produces misleading logs: sqlmap running 25 min with no output was a WAF-induced stall,
and its intermittent 403s were burst/rate artefacts, NOT signature blocking — proven by
re-sending the raw payloads (`UNION SELECT NULL--`, `AND SLEEP(5)--`) which returned HTTP 200
with the NORMAL response. Re-test the raw payload by hand before writing any WAF claim.

### Reporting shape when asked "did you check business logic / compare with our PoC variants"

Deliver a **variant-by-variant matrix, one status per leg** — `DONE (result)`,
`INCONCLUSIVE (reason)`, or `NOT REACHABLE (gate)` — instead of prose. Cite evidence next to
each line. Mark inconclusive legs explicitly and never let one read as "safe". List the legs you
could NOT run (provider-credential-gated API, subscription-gated surfaces) as coverage gaps with
the concrete unlock, not as findings. The user asks for this shape by default.

## 2b. Two test classes this playbook was missing

### 2b-1. Client-side filter vs server-side allow-list
A category/feature can be *hidden in the UI* while the server still accepts it. Hidden-by-default
is the normal shape of this bug, so you will never find it by clicking the UI — you have to
inject the value.

**Test:** render the real page, then inject the hidden value into the control the UI actually
uses, and submit through the genuine form (so the server action binding stays valid):

```js
// category dropdown: add the option the UI removed, then pick it
const sel = document.querySelector('#category');            // or whatever the real id is
if (![...sel.options].some(o => o.value === CATEGORY)) {
  const o = document.createElement('option');
  o.value = CATEGORY; o.text = 'INJECTED'; sel.appendChild(o);
}
sel.value = CATEGORY;
sel.dispatchEvent(new Event('change', { bubbles: true }));
// fill the other required fields, then submit the form containing that select
```

**Always run the full matrix, not just the interesting one.** Findings live in the
*inconsistency*: 1-of-4 hidden values accepted while the other 3 return the same rejection
is the strongest argument that the accepted one is unintentional. Test every sibling value
plus one obviously-bogus control, or you cannot make that argument.

Find the hidden set by reading the client bundle, not by guessing. Look for a boolean flag on
the item definitions plus one filter expression, e.g.
`list.filter(e => !e.nrlOnly)`. Then check whether the app exposes **any** setting that would
legitimately unlock those items — if it exposes none, "hidden for everyone" is the design
intent and server acceptance is a gap by definition.

**Severity discipline:** this is usually LOW and self-scoped. Say so in the finding itself:
it only alters the actor's own records, exposes nobody else's data, grants no entitlement,
crosses no account boundary. `CWE-20` improper input validation, not access control.

### 2b-2. Scalar-without-an-effective-date (calculation correctness)
Freemium SaaS that models anything time-varying usually stores a single scalar where the real
world needs a timeline: ownership share, seats, quota, discount %, tier multiplier. If the
scalar applies to the whole period, any mid-period event is unrepresentable and every
remediation available to the user produces a wrong number.

**Test:** build a dataset that straddles the event, then toggle the scalar and read the
authoritative output:

```
share = 100%  ->  period total  <A>
share =  50%  ->  period total  <A/2>
```

If the pre-event rows scaled too, the scalar is period-wide and the case is proven. Then
quantify the concrete loss: which pre-event rows should have kept the old value, and what
direction the customer ends up taxed/overcharged.

Check the UI for *what is missing*, not just what is present: no date input, no "effective
from", no "sold or transferred on" anywhere in the model. Absence in the bundle is the proof.

**Frame it correctly.** This is product correctness, not security — nobody is attacked, the
customer's own figure is wrong. Report it as a correctness gap with a suggested data-model
fix, and resist promoting it to a financial-impact finding.

## 3. Business-logic / methodology verification (prove with ground truth)

Do not eyeball the UI — pull the **authoritative export** (xlsx/csv/json) and compare to what you
submitted. See `references/accounting-app-logic-checks.md` for the tested pattern.

- **Precision:** store in minor units; assert `0.01 × 3 == 0.03` exactly (no float drift).
  A net figure must equal income − expenses to the penny.
- **Boundary dates:** probe the taxonomy's period edges with **unique values** per case, then read
  back which bucket each landed in. Off-by-one at a period boundary is a classic, high-impact
  methodology bug — and its *absence* is a strong positive result.
- **Idempotency:** replay a submission id / capture token; duplicates must dedupe.
- **Input validation:** test type-vs-category mismatch, unsupported precision, empty/oversized/
  negative/NaN/Unicode values, and injection-shaped strings. Lenient-but-correct parsing
  (`1,000.00`, `£100`, padded spaces) is a *hardening note*, not a bug.
- **Locale/ID validators:** national-insurance / tax / VAT-style IDs should be shape-validated.
  Confirm a plausible-but-fake value is *format*-accepted (registration is a separate,
  provider-side gate — accepting the format is not the bug).

## 4. Tooling discipline — a tool only counts if it was *aimed*

A lesson worth more than any single finding: **running a scanner is not coverage.** A pass that
"ran nuclei/sqlmap/dalfox and found nothing" is worthless if the tools were pointed at the root
page or a static asset instead of the real, parameterised, authenticated surface.

- **Point every tool at the real sink.** `sqlmap -u https://target/` → "no parameter(s) found"
  tested *nothing*. Real targets for `sqlmap`/`commix`/`dalfox` are **parameterised authed** URLs
  (`?ty=…`, `?id=…`, API endpoints) with the session cookie attached.
- **Verify each tool actually executed.** Read the tool's own log/evidence file. Classic silent
  failures: `dalfox <url>` (wrong CLI — needs `dalfox url`/`dalfox file`), `CORScanner --headless`
  (arg rejected), `SSRFmap` without `-r/-p` (refuses), a scanner pointed at a `gov.uk` link lifted
  from page content (out of scope). "EXECUTED" in a tracker ≠ a scan that produced results.
- **Authenticated scanning is mandatory** for tiered SaaS: pass `--cookie`/`-H "Cookie: …"` so the
  scanner sees the real app, not the login redirect.
- **If the user asks "did you use all the tools / all the variants?", the honest answer is often
  no.** Say which ran, which silently failed, and re-run the failures *correctly* — don't defend a
  thin pass.
- **Finish stalls on high-latency/WAF targets**: a dalfox/nuclei authed scan may never complete
  behind Cloudflare. Treat that as **partial coverage** and close the gap with a live browser
  runtime test (navigate to the payload URL, read a sentinel), then say so in the report.

## 5. Anti-false-positive discipline (the core skill here)

Every promising signal in this class had a mundane explanation. Kill it before you report: Kill it before you report:

| Symptom | Cheap disproof |
|---|---|
| "free-tier cap bypassed" | count the resources; the "extra" was the first one, mis-named by you |
| "LFI / SSTI / XSS via a query param" | use a **unique** marker and require *file content*, *arithmetic evaluation*, or *raw* markup — a reflected string in an RSC/flight payload or an escaped literal is not a sink |
| "unauth data export returned 200" | check content-type + final URL: a 200 HTML body that is the SPA shell after a 3xx→/login is not a leak |
| "page still shows the entries" | pagination / display truncation ≠ data loss — confirm against the export |
| "forged webhook accepted" | re-check the status code; 400 `invalid signature` is a **pass** |
| "formula/CSV injection in an export" | **check every sibling export path and the cell/field TYPE before claiming it.** See the hard-won lesson below — this is the easiest false positive in the whole class. |

### The formula-injection false positive (cost a whole finding)
The tempting observation is: *"input `=2+2` comes out raw in the export, therefore injection."*
That conclusion was wrong, and acting on it would have been a padded report.

Two things make raw output **non**-exploitable, and you must check both:

1. **XLSX: raw string ≠ formula.** A cell written as a shared string (`<c t="s"><v>N</v></c>`
   pointing at `<si><t>=2+2</t></si>`) is read by Excel as *text*. Only a formula-typed cell
   (`<f>=2+2</f>`) evaluates. So confirm: does the sheet contain any `<f>` elements at all?
   Count them. `0` means the value is inert regardless of its content.
2. **CSV: the guard usually exists on the *other* path.** Before claiming injection, test the
   guard's completeness across leading characters, and parse the file with `csv.reader`
   rather than eyeballing it — eyeballing a quoted field whose first byte is `"` looks like
   the guard is missing when the apostrophe is correctly the first character of the *content*.

Guard-completeness matrix to run (drive the value through whatever user-controlled field
lands in that export, then read the file back):

```
=1+1      -> '=1+1      guarded?
+1+1      -> '+1+1      guarded?
-1+1      -> '-1+1      guarded?
@SUM(1)   -> '@SUM(1)   guarded?
<TAB>=1+1 -> ?           guarded?
<CR>=1+1  -> ?           guarded?
=cmd|'/C calc'!A0       -> ?   (DDE)
=HYPERLINK("http://x/","c") -> ?   (contains quotes AND commas — quoting trap)
```

A product that guards `=`, `+`, `-`, `@` and control characters, and quotes correctly, is
**done** — downgrade the item to "verified mitigated", state that you could not achieve
execution on any path, and leave only a defence-in-depth note (hoist the guard into the data
layer so all exporters inherit it). Padding that into a bounty-grade finding costs the whole
report its credibility, and the honest negative is itself worth telling the vendor.

Corollary: **downgrade in writing.** Leave the corrected verdict in the report body and a
"FINAL VERDICT" block, don't quietly delete the earlier claim — the user needs to see the
reasoning changed.

## 5. Reference files

- `references/nextjs-server-action-replay.md` — replaying Next.js 14/15 Server Actions for real
  (required headers, router-state-tree, `_1_` field naming, capturing the app's own request), plus
  the RSC-reflection false-positive guard.
- `references/accounting-app-logic-checks.md` — ground-truth export verification, tax-year/period
  boundary matrix, integer-penny precision, idempotency, and the auth-hardening observations worth
  mentioning to the vendor.
- `references/excel-csv-injection-verification.md` — the CWE-1236 verification recipe: test every
  export path, prove XLSX cells are text-typed (0 `<f>` elements) before claiming anything, and
  test the CSV guard's completeness (`= + - @ TAB CR`) by parsing with `csv.reader` instead of
  eyeballing. Use it to decide "verified mitigated" honestly rather than shipping an overclaim.
- `references/uk-property-tax-rules.md` — condensed UK rules to check a bookkeeping/MTD product
  against: FHL abolished 6 Apr 2025, MTD thresholds and the 7 Aug/7 Nov 2026 update dates, cash
  basis as the property-income default plus the £150,000 cash-receipts ceiling, Form 17 / 50:50
  joint-ownership default, 6 Apr–5 Apr boundaries, and the scalar-ownership-share defect.
- `references/tax-software-compliance-review.md` — reviewing a tax/accounting app's calculation
  logic against current law: which claims to verify externally, which controls were verified
  correct, how to test gated features, and how to write the result without overclaiming.
- `references/uk-property-tax-compliance-review.md` — UK rule checkpoints (MTD dates/thresholds,
  FHL abolition, cash basis + the £150,000 ceiling, Form 17 beneficial split) with the test for
  each; the ownership-share-is-not-date-effective test; the Pro-gate-via-injected-field-name
  method; and the "raw value in an exported file is not a finding until you check the sink"
  rule with the `csv.reader` parsing trap.
- `references/ui-vs-server-gate-parity.md` — testing whether the server enforces the gate/allow-list
  the client merely *renders*: feature-gate prop → gated-field injection, enum allow-list parity
  across the whole set, the inconsistency-as-evidence rule, and severity framing for self-scoped
  validation gaps.
- `scripts/ui_cap_race.py` — re-runnable cap-race harness: N pages in one authed context, create
  form pre-opened and filled, all submits fired in a tight loop, resource recount + verdict.
  Refuses to run on a stale session or an account already at the cap (both of which silently
  produce a meaningless "0" result). **Windows/MSYS gotcha:** pass URL-ish args with
  `env MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'` *per command* — a bare `/app/...` argv gets
  rewritten to a `C:/...` path before Python sees it. Do **not** `export` those globally: an
  exported `MSYS2_ARG_CONV_EXCL='*'` later mangled an unrelated `$PWD` into `D:\d\data...`.

## 6. Reporting

- Findings need **demonstrated attacker impact** (funds / data / entitlement actually obtained).
  A well-built entitlement gate is a **negative** — say so plainly; do not pad the report.
- **Label correctness defects as correctness defects.** Tax/accounting, pricing and
  business-rule problems ("a transfer mid-year cannot be represented", "no £150k ceiling
  check", "a UI-hidden category the server still accepts") are real and worth reporting, but
  they are *product correctness*, not access control. Keep them in a separate section, state
  the impact precisely ("the taxpayer's figure is wrong and the shortfall falls on them"),
  and do not dress them up with a CVSS vector that implies a boundary crossing. Mixing the two
  is what makes a report get rejected as overclaimed.
- Where a category/field is hidden in the UI but accepted by the server, the strongest
  argument that it is a bug is **inconsistency**: prove it by testing the sibling fields that
  share the same flag. 1 accepted of 4 rejected with the same error message is a defect
  argument; 1 accepted of 1 is a design question.
- State coverage gaps honestly (e.g. provider-credential-gated flows you legitimately cannot pass).

### Separate "security finding" from "product correctness" in the report itself
This class of audit reliably turns up defects that are *real* but are **not security
vulnerabilities** — the tax/accounting logic computes something wrong, or a data model cannot
represent a legitimate case. They have no attacker, no boundary crossed and no other user
harmed, so they are not bounty findings, but they are exactly what a vendor wants to hear.

Structure the deliverable so the reader cannot mistake one for the other:
- A **summary table with separate `Type` and `Severity` columns**, filled in BEFORE the detail
  sections — `Server-side validation gap / Low` next to `Tax calculation correctness / Product
  correctness`.
- Put the sentence *"I do not consider these to be security vulnerabilities"* in the **opening
  paragraph**, not in a footnote. A reader who stops after paragraph one must not come away
  thinking you claimed five vulns.
- For each non-security item, give the rule, the reproduction, the **user-side impact**, and a
  suggested fix — it reads as product feedback rather than a demand.
- State the boundary of every finding explicitly ("self-scoped: it only affects the account that
  creates the entry; no cross-account boundary is crossed"). That sentence is what keeps a P5
  from being read as a P2.

**A high-value correctness class to probe on any stateful financial/lifecycle model: does the
model have a DATE dimension for the thing that changes?** Quarterwise stored ownership share as
a single per-property number (`name="percent"`, in basis points) with **no effective date**, so
a property changing hands mid-year could not be represented: setting 50% halved the *entire*
tax year including months owned 100%, and the UI copy confirmed it ("you file your 50% share
with HMRC"). Whole-year-scalar where a period is required = a defect you can prove
arithmetically from the export, with no exploit needed. Look for the same shape in:
ownership/beneficiary splits, plan or price changes, tax-residency changes, rate changes,
address of record, and any "share of X" field.

Related correctness probes worth a run on a tax/accounting product: is there a ceiling or basis
change the model never checks (e.g. a cash-basis receipts limit that forces accruals above a
threshold — Quarterwise accepted £254,878 of receipts with no warning), and does the product
handle a statutory declaration/ election it silently assumes (e.g. a jointly-owned-property
split that HMRC treats as 50:50 in the absence of the required form)?
  pass). Name the gate ("Pro plan", "live Government Gateway authorisation", "the feature is
  Pro-gated server-side and I proved it") so the reader can judge.
- Info-only observations worth a one-line mention (not bounty-worthy): lenient numeric parsing
  (`1,000.00`, `£100`, padded spaces — correct, just notable), out-of-period dates accepted
  when handled correctly downstream, unhandled 500 on absurd input with an empty body,
  device-fingerprint/telemetry fields posted client-side (untrustworthy for security decisions,
  privacy note only), and soft-404s (unknown API paths returning 200 + the SPA shell).