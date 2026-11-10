---
name: hunt-business-logic
description: Hunting skill for business logic vulnerabilities. Built from real engagements — includes the inert-value probe for testing write endpoints safely, cart/quantity/coupon patterns, and Hybris/commercetools specifics.
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Business-logic hunting — field-tested notes

## The inert-value probe (test a WRITE endpoint's auth wall without creating anything)

When a write endpoint (create/issue/generate) validates its arguments BEFORE it checks
authorization — visible from validation errors arriving with no 401/403 — you can still settle
the security question with zero side effects: send arguments that PASS the declared format but
are semantically inert.

Worked example (SAP Commerce / Hybris, target.com.au 2026-09):
  POST /rest/v2/target/vouchers  -> ExtendedVouchersController.createSerialVoucherCodes
  * gating pattern leaked in the error: `code must match ^[A-Z0-9]{3}$`
  * send {"code":"ZZ9","quantity":0}  -> 401 Access is denied   => control holds, nothing created
  * send {"code":"ZZ0"}               -> 400 (only `quantity` missing) => field names confirmed
Quantity 0 makes the "generate N codes" operation a no-op no matter what happens next, so the
test is decisive AND harmless. Do that BEFORE you ever consider sending quantity>=1 against a
live base record — minting real vouchers/gift cards is a business side effect, and a VDP is not
the place to produce one without explicit operator sign-off.

Generalise: for any "create N of X" endpoint, find the parameter that scales the side effect and
set it to zero (quantity, count, iterations, amount). For "apply/consume" endpoints use an
obviously invalid identifier. Only escalate to a real value when the zero/sentinel test shows
the auth wall is missing AND the operator has approved the side effect.

## Wallet-signed write endpoints — the inert target is YOUR OWN keypair

For an API whose write path is gated by a wallet signature (`POST …/add` with
`{data, signature, signer}`) there is no session to steal and no login to bypass, so the inert
probe becomes "sign for an account I just minted". You hold the key, so every check is decidable
in one pass and none of them touches anyone else's record:

1. honest self-signed write → `200`, then read back **under your own signer's namespace** —
   proves the endpoint is live and shows where the record is keyed.
2. same message but a **field edited after signing** → `401 Invalid signature` (server verifies).
3. valid signature with the **`signer` swapped for another pubkey** → `401`. This is the check that
   settles cross-user injection: Ed25519 cannot recover a pubkey from a signature, so the server
   must be verifying against the claimed signer — if instead it stored by a client-supplied owner
   you would have to write into a victim's namespace to learn that.
4. a field the **client** validates only (length ≤ 24, regex) → oversized/HTML value →
   `400 Label cannot exceed 24 characters` = real server-side validation, not just UI.

Two details that decide whether the test even runs: the signed bytes are
`JSON.stringify({fieldA, fieldB})` — **no spaces, no domain, no nonce** — so reproduce them with
`json.dumps(..., separators=(',',':'))`, otherwise you get a `500 Internal server error` that reads
like "the server accepted it". And an unbound message (no domain/purpose/expiry) is a hardening
note about signature reuse or phishing, not an access-control finding.

Finish with the read-back: `GET …?wallet_address=<your signer>` **and** `?<the account you
labelled>`. Only the first returning your value means the store is signer-keyed and there is no
cross-user injection — a negative worth stating because you executed it, not inferred it.

## On-chain counterpart: SIMULATE the transaction, never send it

When the write path is a blockchain instruction, the "prove it without side effects" discipline above has a
native implementation: `simulateTransaction` runs the instruction against current state and rolls everything
back. Use it whenever a hypothesis would otherwise cost a real transfer to confirm. Worked case — DFX
MerkleDistributor claim, 0.xyz audit, 2026-10:

- **Hypothesis:** distributor `startTs→endTs` was a 5-minute span, so every other claimant must be locked out
  by `ClaimExpired` while the site's FAQ says "claim until October 2027".
- **Instead of sending a claim** (real funds, real state change, needs a key I don't hold) I rebuilt the exact
  transaction the client builds and called `simulateTransaction` with
  `{"sigVerify":false,"replaceRecentBlockhash":true,"encoding":"base64"}`.
- **Result:** `Program log: Created new claim with locked 0 and 2985147 unlocked with lockup start:1791822372
  end:1791822672` + `Program … success`. The window is a **lockup/vesting stamp, not a claim gate** —
  hypothesis refuted, zero side effects, and it would have been reported as a critical finding otherwise.

Getting the simulation to run took three fixes, each surfacing as a *different* error worth memorising:
1. `InstructionDidNotDeserialize (102)` → Anchor `Vec<T>` lengths inside instruction data are **u32 LE**, not
   shortvec. Shortvec is only for message-level counts (signatures / account keys / instructions).
2. `AccountNotInitialized (3012)` on account `to` → the client sends `createAssociatedTokenAccountIdempotent`
   **before** the claim; instruction order inside one transaction is part of the contract.
3. A 64-byte zero signature satisfies the wire format when `sigVerify:false`, but the required signer still
   must be *marked* signer in the message header.

**Verification anchor before trusting any account parse:** check a field you already know independently. Here
`MerkleDistributor.mint` had to equal the DFX mint; once it did, the offsets were right and the "5-minute
window" reading was confirmed as a lockup. Without that check an off-by-N offset produces confident nonsense
that looks exactly like a finding.

The same simulation answers the *authorization* half of the question: reading the client's
`keys:[{pubkey, isSigner:true}]` showed the claimant must sign, so the **publicly fetchable Merkle proof is
not a bearer credential** — an unauthenticated `GET /api/proof/{wallet}` leak stays a privacy issue and never
gets mis-filed as "anyone can claim someone else's allocation".

## Cart / quantity patterns actually observed
- Negative and zero quantities: Kmart (commercetools) rejects server-side ("quantity must not be
  less than 1") — correct. target.com.au (Hybris) answers **500** instead, which is sloppy input
  handling but no impact (no stack trace, no state change) → typically INFORMATIVE.
- Silent caps: adding 999 gave a cart of 99, and repeating the add did NOT exceed it → the cap is
  enforced on the cart, not per-request. Always test the *repeat* case before claiming a bypass.
- Client-supplied fields in the add payload (postCode, storeCode) are worth watching for pricing
  or fulfilment-logic deviations — but only report when a price/entitlement actually changes.

## Two front-ends, one cart = inconsistent protection
target.com.au exposes two cart write paths:
  POST /uir-pdp/api/cart/add   — no CSRF token at all (201 from the PDP itself)
  POST /ws-api/v1/target/cart/add — carries `_csrf` in the JSON body
When you see that, test the untokened path with CORS-simple content types (text/plain,
x-www-form-urlencoded) to see whether a cross-site form could drive it (that is the CSRF test
that matters — a JSON content type forces a preflight and is therefore not CSRF-reachable).
Note: an edge rate/reputation rule (Akamai `429 {"cpr_chlge":"true"}`) can start blocking your
POSTs mid-session after a burst; that is environment, not the app — pace yourself, and use the
parameterised content-type trick from `bot-protected-target-testing` when you need back in.

## Mass-assignment probe on add-to-cart (cheap, high-signal)
Send the app's own payload plus every price-shaped field you can think of, then READ THE CART BACK:
    {"productCode":"X","quantity":1,"postCode":2020,"storeCode":"5121",
     "price":1,"basePrice":1,"totalPrice":1,"unitPrice":1,"discount":99,"shippingCost":0,
     "currency":"AUD","discountCode":"FREE100","lineItemPrice":0.01,
     "custom":{"priceOverride":"0.01"}}
On target.com.au this returned 200 and the cart still charged $22.00/unit → pricing is
server-side and extra fields are ignored. Record it as a verified negative; on a less careful
stack the same request would have rewritten the price.

Same trick for fulfilment: the delivery-estimate endpoint took a bogus postcode (0000) without
complaint but the cost stayed flat ($9 HD / $0 CC), while a bogus storeNumber produced a business
error. Conclusion: server-computed, no client leverage — with the hardening note that the
postcode value itself is never validated.

## The read-back is what makes it evidence
Never report a business-logic bug from a status code. After each tampering step, re-read the
authoritative state (cart JSON, order total, entitlement list) and diff it. "200 + unchanged
price" is a control working; "200 + changed price" is the finding; "500 + unchanged state" is
informative-only and belongs in a hardening note, not a report.

## Idempotency / replay checks on a write API (the test has two halves)

When the docs say writes are idempotent on your own reference key, prove BOTH:
1. **same key + same payload** → deduplicated, no duplicate row created;
2. **same key + DIFFERENT payload** → also deduplicated, and the ORIGINAL value is kept (no overwrite).
Half 2 is the one people skip, and it is where a silent overwrite hides. Re-read the resource after
each call and diff the stored value, not the status code.

## Body-shape trap: "Required" for fields you DID send

If a write endpoint returns per-field errors (`0.date: Required`, `0.type: Required`, `0.amountPence:
Required`) for fields that ARE in your body, the **envelope is wrong, not the fields**. Many APIs take
a BARE JSON ARRAY (`[{...},{...}]`), not a wrapper object (`{"transactions":[...]}`) — and the validator
reports "missing" because it iterates the wrong level. Read the error's array index (`0.x`) as the tell,
and re-send as a bare array before you start doubting your field names. Same class: an `?mutation=1` op
that answers **415 on POST** but **400 on GET** is a GET-with-query-vars endpoint, not a POST one — the
415 is the edge rejecting the method/body, and the 400 is the app parsing you.

## The prior pass's leftover data is a confound, not baseline

On a re-audit, the account often still carries the LAST pass's scenario rows (identifiable by names like
"R4 audit test …"). Any control that is evaluated on an AGGREGATE (a running total, a shared allowance,
a bucket) is then contaminated: the rule may be evaluated against the old data and never exercise the
case you are testing. Note the existing rows first, and if the aggregate hides the case, temporarily
clear the other rows, run the isolated leg, then restore them exactly and re-read the aggregate to
confirm you are back to the starting figures.

## The automated/pipeline pass is NOT a business-logic check

The audit pipeline's 0C biz-logic phase fires a fixed vector set and reports something like
`business-logic: 15/15 vectors, 56 probes, 0 interesting`. Treating that as "business logic covered"
invites the direct question — *"sudah kamu cek dr sisi business logic nya?"* — and the honest answer
on that occasion was no, not by hand. That question is the operator running the check the agent
should have run.

The automated pass fires payloads at endpoints; a real pass asks *"what is this product supposed to
DO, and can I make it do something else?"* — limits, caps, idempotency, eligibility, ordering,
quotas, state transitions, cross-entity rules — with the product's own copy/claims as the oracle.
Run it as its own step. And report negatives as results: "the write validates its argument (400 on a
non-existent id), rejects duplicates (idempotent), and is session-scoped (no write-IDOR)" is a
deliverable, not an absence — that verdict only exists because you replayed the mutation and read the
state back.

## Edge throttling is part of the methodology
After a few dozen POSTs the same request that returned 200 starts returning the edge challenge.
Plan bursts, leave the "must be tested" cases for a fresh session, and record which tests were
abandoned for that reason instead of quietly reporting them as negative.

sources: hackerone_public, github
report_count: 25
---

## Crown Jewel Targets

Business logic vulnerabilities pay highest in platforms where financial transactions, identity verification, and access controls intersect with real-world consequences. The richest targets are:

- **E-commerce & payment platforms** (Valve/Steam, Shopify) — payment flow manipulation, free goods, price tampering
- **Marketplace & gig economy apps** (Airbnb, Uber) — identity/verification bypass enabling fraud or unsafe interactions
- **SaaS with tiered access** (Mozilla Monitor) — bypassing verification to unlock monitoring features without entitlement
- **High-traffic consumer apps** (Snapchat, Yelp) — rate-limit bypass enabling spam, enumeration, or abuse at scale

Asset types that pay: checkout flows, subscription endpoints, callback/verification systems, webhook handlers, employee/internal portals exposed to the internet, and any endpoint that trusts client-supplied data to make authorization decisions.

---

## Attack Surface Signals

**URL patterns to watch:**
- `/checkout`, `/order`, `/subscribe`, `/payment`, `/verify`, `/confirm`, `/callback`
- `/internal`, `/employee`, `/summit`, `/staff`, `/admin` — internal pages accidentally public
- `/api/v*/payment`, `/api/v*/notify`, `/webhook` — payment provider callbacks
- Endpoints accepting `X-Forwarded-For`, `X-Real-IP`, `CF-Connecting-IP` headers

**Response/header signals:**
- `Set-Cookie` with unvalidated session state tied to cart or order data
- Payment provider names in responses: `Smart2Pay`, `Stripe`, `PayPal`, `Braintree`
- Redirect chains through third-party payment pages (in-flight data opportunity)
- `200 OK` on subscription/verification endpoints with no CAPTCHA or token

**JS patterns:**
- Hardcoded internal URLs in frontend bundles (`/employee/`, `/staff/`, `/internal/`)
- Client-side price calculation before server submission
- Verification logic that only checks on the frontend (`if (verified) { ... }`)
- `fetch('/api/subscribe', { method: 'POST', body: ... })` with no anti-CSRF token or rate-limit token

**Tech stack signals:**
- Shopify storefronts with draft/unpublished channel pages
- Apps using IP-based rate limiting without session/account binding
- Payment webhooks with no HMAC signature validation
- SMS/phone callback flows that don't verify ownership before enabling features

---

## Step-by-Step Hunting Methodology

1. **Map all authentication boundaries.** Spider the target. Identify pages/endpoints that serve authenticated content (employee portals, premium features, order pages) and test each unauthenticated. Look for internal pages indexed in JS bundles or linked from robots.txt/sitemap.xml.

2. **Identify every verification flow.** Enumerate: email verification, phone/SMS verification, payment verification, CAPTCHA, age gates. For each, test: what happens if you skip the verification step entirely? What happens if you replay a valid token on a different account?

3. **Test rate-limiting controls on every form.** For every POST endpoint (subscribe, login, OTP, search), send 50+ rapid requests. Vary: remove cookies, rotate `X-Forwarded-For` / `X-Real-IP` headers, change `User-Agent`. Check if the server uses IP from headers rather than connection IP.

4. **Intercept and tamper with payment flows.** Use Burp Suite to intercept every request between your browser, the application, and the payment provider. Identify where price, currency, order ID, or status fields are set. Attempt to modify amounts to $0.01 or currency to a low-value currency. Look for POST-back/webhook endpoints that accept payment confirmation — test if they validate HMAC/signature.

5. **Test phone/callback number verification.** Whenever a platform accepts a callback number, test: can you set it to a number you don't own? Does the platform call/text that number and grant trust based solely on submission? Try setting it to a victim's number.

6. **Check for unprotected employee/internal surfaces.** Search Shodan, GitHub, JS bundles, and Wayback Machine for internal subdomain/path references. Test access without authentication. Check if these surfaces allow order placement, data access, or privilege escalation.

7. **Validate business impact.** For each finding, determine: does this result in financial loss, unauthorized access, or data exposure? Document the end-to-end chain.

---

## Payload & Detection Patterns

**Rate limit bypass via header rotation:**
```bash
# Rotate X-Forwarded-For to bypass IP rate limiting
for i in $(seq 1 100); do
  curl -s -X POST https://target.com/api/subscribe \
    -H "X-Forwarded-For: 10.0.0.$i" \
    -H "X-Real-IP: 10.0.0.$i" \
    -H "Content-Type: application/json" \
    -d '{"email":"victim+'"$i"'@example.com"}' \
    -o /dev/null -w "%{http_code}\n"
done
```

**Payment tampering — modify in-flight price:**
```http
POST /payment/initiate HTTP/1.1
Host: target.com

amount=0.01&currency=USD&order_id=12345&product_id=99
```
```bash
# Look for unvalidated webhook endpoints
curl -X POST https://target.com/payment/callback \
  -H "Content-Type: application/json" \
  -d '{"status":"success","amount":"0.01","order_id":"12345","transaction_id":"fake-txn"}'
```

**Unauthenticated internal page discovery:**
```bash
# Check robots.txt and sitemap for internal paths
curl -s https://target.com/robots.txt | grep -iE "(disallow|allow)" 
curl -s https://target.com/sitemap.xml | grep -iE "(employee|internal|staff|summit|admin)"

# Grep JS bundles for internal paths
curl -s https://target.com/assets/app.js | grep -oE '"/[a-zA-Z0-9/_-]{3,50}"' | sort -u
```

**Email verification bypass:**
```bash
# Skip the verification step: hit the post-verification API endpoint directly
# with an unverified session. If it succeeds, the gate is UI-only.
curl -s -X POST https://monitor.target.com/api/monitoring/enable \
  -H "Cookie: session=<your_unverified_session>" \
  -H "Content-Type: application/json" \
  -d '{"email":"victim@example.com"}'

# Replay verification token on different account
curl -X POST https://target.com/verify \
  -d 'token=VALID_TOKEN_FROM_ACCOUNT_A&email=account_b@example.com'
```

**Grep patterns for client-side logic issues:**
```bash
# Find price calculations in JS
grep -iE "(price|amount|total|cost)\s*[=*+]" app.js

# Find internal URLs in JS bundles
grep -oE '"/(employee|internal|staff|admin|summit)[^"]*"' *.js

# Find unvalidated IP header usage in server code
grep -iE "x-forwarded-for|x-real-ip|cf-connecting-ip" src/ -r
```

---

## Common Root Causes

1. **Server trusts client-supplied data for financial decisions.** Developers offload price calculation to the frontend or pass amount fields through forms/URLs without re-validating on the server against a canonical source (the product database).

2. **Verification is enforced only in the UI, not the API.** Frontend hides features behind a verification gate, but the backend API endpoints are fully functional without a verified status — any authenticated request succeeds.

3. **IP-based rate limiting reads from spoofable headers.** Developers implement rate limits using `request.headers['X-Forwarded-For']` instead of the actual connection IP, allowing trivial bypass by header manipulation.

4. **Payment webhooks lack signature validation.** Developers implement "success" webhooks without verifying the HMAC signature provided by the payment provider, allowing anyone to POST a fake success notification.

5. **Internal/employee pages aren't access-controlled.** Internal tools are deployed to production domains without authentication middleware, either because developers assume obscurity (unlisted URL) or forgot to apply auth to a new route.

6. **Phone/callback verification is advisory, not enforced.** Systems accept a phone number and grant trust to whoever submitted it, without confirming the submitter owns or controls that number.

7. **Draft/channel-specific storefronts inherit full order functionality.** Platforms like Shopify allow creating storefronts for specific channels (employee events) that are unlisted but still fully functional for order placement if the URL is known.

---

## Bypass Techniques

| Defense | Bypass |
|---|---|
| IP-based rate limiting | Rotate `X-Forwarded-For`, `X-Real-IP`, `True-Client-IP`, `CF-Connecting-IP` headers per request |
| CAPTCHA on subscription forms | Use header-based bypass first; if CAPTCHA is only on the web form, call the underlying API endpoint directly |
| Email verification gate | Access the post-verification API endpoint directly; replay valid tokens; check if `verified=true` is a client-set cookie/param |
| Payment amount server validation | Modify currency to a lower-value currency; test with $0.00 or negative amounts; manipulate order IDs to reference different products |
| Webhook HMAC validation | Test with no/empty signature header (is validation enforced at all — a modified payload only "passes" if it isn't); replay an UNMODIFIED captured webhook to test missing idempotency/anti-replay |
| Auth on internal pages | Try unauthenticated; try with a low-privilege account; try path traversal variants (`/employee/../employee/`) |
| Phone verification (OTP sent) | Submit someone else's number without OTP validation; check if the system grants trust on submission vs. OTP confirmation |

---

## Off-chain entitlement / claim-proof endpoints (DeFi, airdrops, incident recovery)

When a product pays out from an **off-chain-computed** allocation — Merkle tree, points DB, loss
snapshot after an exploit — the client only ever needs `amount + proof`, so it asks for them over
plain HTTP. That read endpoint is where this class lives. Check it in this order:

1. **Does it answer for a wallet that is not yours?** `GET /api/proof/<arbitrary-wallet>` returning
   `{"amount":"2985147","proof":[…18 nodes]}` unauthenticated is the candidate. The `404
   {"error":"not_found"}` for a wallet outside the tree is the **control** that proves the endpoint is
   really querying the allocation set rather than stubbing — without the negative you cannot tell
   enumeration from echo.
2. **Membership oracle.** `200` vs `404` / `"no DFX entitlement in this snapshot"` lets an attacker
   test whether an arbitrary wallet was affected by a publicised incident. Reportable on its own
   when the amounts are not.
3. **Amplifier: read `access-control-allow-origin` on that response.** `*` means any web page can
   pull a victim's entitlement **from the victim's own browser** with zero server infrastructure;
   no `ACAO` header means the same URL is only reachable server-side. Identical body, one tier apart
   in severity, decided by that one header.

Then the gate that decides the whole class — **who can act on the proof?** Read the claim
instruction's account metas in the client bundle before choosing words:

- `{pubkey: claimant, isSigner: true}` + destination derived from the claimant's own key ⇒ the proof
  is **not** a bearer credential; the report is confidentiality/Low, never theft. Also verify the
  client-only gate against the chain: a hard-coded `earlyClaimants` Set or a `startTs`/`endTs` window
  enforced only in JS must be checked against the program (`onchain-finding-verification` §1e —
  read-only `simulateTransaction`, never a live send). In the worked case the 5-minute window turned
  out to be a *vesting lockup*, and the simulation refuted a "138k users locked out" story before it
  was written.
- claimant **not** a signer ⇒ stop, prove it with that simulation first; do not report theft from a
  source reading.

**Triage rule for the data itself.** Anything recomputable from public chain state (positions,
health, TVL, bad debt) is **abuse/cost**, not confidentiality — the reportable part is the
*delivery*: e.g. an unauthenticated `Content-Length: 82255403` aggregate (87,774 accounts) served
with `ACAO: *` and no observed rate limit despite the spec documenting an "anonymous rate limit".
Numbers that exist nowhere else off-chain (points, adjustments, a pre-claim loss snapshot) are real
confidentiality — Low unless they unlock an account-level action. Always say which of the two you
are reporting; conflating them is how a privacy note gets bounced as "that data is on-chain anyway".

---

## Gate 0 Validation

Before writing any report, answer all three:

1. **What can the attacker DO right now?**
   Be specific: "An unauthenticated user can place an order for physical goods at $0 cost" or "An attacker can bypass email verification and monitor any email address without owning it" or "An attacker can send unlimited subscription emails to any address." Vague impact = reject.

2. **What does the victim LOSE?**
   Identify a concrete, attributable loss: financial loss (free goods, fraudulent payments), privacy loss (phone number spoofed, unauthorized monitoring), service abuse (spam campaigns via rate-limit bypass), or security degradation (unverified identity trusted for sensitive actions). If the loss is purely theoretical, re-evaluate severity.

3. **Can it be reproduced in 10 minutes from scratch?**
   Create a fresh account (or use no account). Follow your documented steps. Achieve the impact. If you can't reliably reproduce it end-to-end in under 10 minutes with the steps you've written, your methodology is incomplete — refine before submitting.

---

## Real Impact Examples

**Scenario 1 — Free Physical Goods via Exposed Internal Storefront (Shopify-style)**
An employee summit page was deployed to a public Shopify storefront as a private channel for distributing free books to staff. The URL was discoverable via JS bundle analysis or link sharing. An anonymous user who navigated to the URL could browse and complete a checkout with no authentication required, receiving physical merchandise shipped at the company's expense. Impact: direct financial loss per order, potential for bulk ordering if not caught quickly.

**Scenario 2 — Payment Manipulation via In-Flight Tampering (Valve/Steam-style)**
A payment flow passed order amount and currency through client-controlled parameters before redirecting to a third-party payment provider (Smart2Pay). By intercepting the redirect with Burp Suite and modifying the amount field, an attacker could complete a real payment for $0.01 while the application's webhook — lacking HMAC validation — accepted the provider's confirmation and credited the full item/service to the account. Impact: critical financial loss; attacker receives full value goods/services for near-zero cost, infinitely repeatable.

**Scenario 3 — Email Verification Bypass for Unauthorized Monitoring (Mozilla-style)**
A breach-monitoring service required email verification before enabling monitoring alerts for an address. The verification check was enforced in the UI flow but the underlying API accepted monitoring setup requests for any address using a valid session — skipping the verification step entirely. An attacker could set up monitoring for email addresses they don't own, receiving breach notification data (potentially including credential exposure status) for victim accounts. Impact: privacy violation; attacker gains intelligence on whether a target's email was in a breach without the target's knowledge or consent.

---

## Disclosed Report Citations (Backfill +5 — 2016-2023)

The following real, verified bug-bounty / coordinated-disclosure cases extend this skill. All five share a measurable financial-impact angle (actual $ loss demonstrated or quantifiable platform-wide exposure).

8. **Stripe — Fee discount race redemption** ([H1 #1849626](https://hackerone.com/reports/1849626))
    - Subclass: coupon/discount race-multi-redemption + financial primitive
    - Payload: Stripe Support applied a one-time $20,000 fee-credit. Researcher captured the "accept-discount" POST and replayed it 30× in parallel via Burp Turbo Intruder, each acceptance crediting the account anew
    - Root cause: idempotency missing on discount-acceptance endpoint; no unique constraint on (account_id, discount_id)
    - Year: 2023 — **$5,000**, $600,000 of fee-free transactions accrued before fix (~$18,000 real Stripe loss at 3% take rate)

9. **Reverb.com — Gift-card race multi-redemption** ([H1 #759247](https://hackerone.com/reports/759247))
    - Subclass: gift-card / store-credit race-redemption
    - Payload: single valid gift card, parallel-POST to `/redeem` from 10 sockets via Turbo Intruder. Balance credits N× the face value
    - Root cause: no row-level lock on gift_card table; balance debit and credit live in separate transactions
    - Year: 2019 — **$1,500**

10. **Upserve / OLO — Negative-quantity price manipulation** ([H1 #364843](https://hackerone.com/reports/364843))
    - Subclass: negative-quantity-in-cart price tampering
    - Payload: `POST /api/order {"items":[{"id":1,"qty":1,"price":50},{"id":2,"qty":-3,"price":50}]}` — order total computes to `-$100`, floors to ~$0 at payment capture, food still fulfills
    - Root cause: server multiplies `qty * price` with no `qty >= 1` guard
    - Year: 2018 — textbook citation for the subclass (acknowledged-only program)

11. **Krisp — Pay-less-per-seat via PUT tampering** ([H1 #1446090](https://hackerone.com/reports/1446090))
    - Subclass: price-per-unit mass-assignment / quantity-discount manipulation
    - Payload: `PUT /v2/seats` body includes a server-trusted `price` field. Set `price=1` instead of $60. Subscription updates, billing engine charges $1/seat for 100 seats
    - Root cause: server reads price from request body instead of looking it up by plan_id; classic mass-assignment
    - Year: 2021 — Stripe-billed SaaS pricing exposure

12. **Stripe — Pay using archived price via mid-flow swap** ([H1 #1328278](https://hackerone.com/reports/1328278))
    - Subclass: cart-state TOCTOU / cancel-then-deliver (price-version race at checkout)
    - Payload: merchant archives an old price (e.g., $5 instead of new $50). Buyer starts checkout via the new payment-link, then mid-flow swaps `price_id` back to the archived one. Stripe charges $5; subscription provisions at the new tier
    - Root cause: payment-link validates "is active", price object validates "exists" — but the join "price.active AND price ∈ link.allowed_prices" is missing
    - Year: 2021 — Stripe Medium (per-subscription recurring loss)

---

## Related Skills & Chains

- **`hunt-race-condition`** — Every uniqueness/quota check in a logic flow is a race candidate. Chain primitive: Business logic (coupon/credit/promotion) + race condition → coupon redeemed N times in a single TCP packet via Turbo Intruder.
- **`hunt-idor`** — Logic flows that trust a client-supplied identifier (order_id, tenant_id, beneficiary_id) overlap directly with IDOR. Chain primitive: business-logic step-skip + IDOR on beneficiary_id → transfer funds from victim account.
- **`hunt-api-misconfig`** — Step-skip and verification-bypass often live next to mass-assignment fields. Chain primitive: business-logic email-verify skip + API mass assignment (`verified:true, role:admin`) → ATO without email control.
- **`hunt-ato`** — Logic bugs in password reset, email change, and recovery flows are core ATO paths. Chain primitive: business logic (email change accepts without re-auth) + `hunt-ato` Path 2 → silent victim email swap → password reset to attacker mailbox.
- **`security-arsenal`** — Load the Business-Logic Probe Checklist (negative quantity, decimal overflow, currency swap, step-skip via direct URL nav, state-machine reverse) and the Always-Rejected list to avoid filing self-inflicted bugs.
- **`triage-validation`** — Apply the 7-Question Gate (especially Q4 "Is this exploitable by an outside attacker without unrealistic preconditions?"): logic bugs need a concrete dollar/PII/state impact, not just "the flow looks weird".