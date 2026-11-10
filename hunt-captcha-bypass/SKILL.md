---
name: hunt-captcha-bypass
description: "Hunt CAPTCHA Bypass — 6 distinct patterns: (1) CAPTCHA field simply omitted from the request (server-side validation absent), (2) CAPTCHA token replayed from a solved challenge (no single-use enforcement), (3) CAPTCHA response accepted on a different endpoint than it was solved on (no binding to action/session), (4) static or predictable CAPTCHA values accepted (e.g. '0', 'null', empty string), (5) audio/accessibility CAPTCHA trivially solvable programmatically, (6) CAPTCHA only enforced after N failures (first N requests bypass it). Detection: intercept a successful form submission, remove the CAPTCHA field entirely, replay — if it still succeeds, server-side validation is absent. Medium severity standalone; High when it removes the only rate-limit gate protecting a login, registration, or payment endpoint."
sources: public_research, operator_experience
report_count: 6
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

## Field notes — proving token replay (verified 2026-09, Rapyd Client Portal)

Pattern (2) is easy to *suspect* and hard to *prove*. The reliable recipe, in order:

1. **Find the wire field name first — never assume it.** Hook `Network.enable` +
   `Network.requestWillBeSent` and read `postData` of the real submit. Seen in the wild:
   Cloudflare Turnstile token travels as **`recaptcha_token`** in the JSON body, while the DOM
   field is `input[name=cf-turnstile-response]`; Google v2 fills
   `textarea[name=g-recaptcha-response]` and may travel under that name or as `recaptcha_token`.
   Guessing the field name produces "captcha failed" for every test and hides a real finding.
2. **Three controls, same endpoint, same account:**
   - no token → must return the captcha error (`*_CAPTCHA_VALIDATION_FAILED`)
   - garbage token (`1.zzzz…`) → must return the captcha error
   - one real token, submitted **3×** → if uses 2 and 3 stop returning the captcha error,
     the token is not single-use. If uses 2/3 return the same *next* error as use 1
     (e.g. `..._ERROR_MAX_LOGIN_ATTEMPTS`, `..._MISSING_DEVICE_FINGERPRINT`,
     `..._INVALID_CREDENTIALS`), that next-error is your proof: validation had to pass to get there.
3. **Use a second, untouched account for the replay attempts** if the first one is already inside a
   lockout — otherwise a per-account counter changes the error code and the signal gets muddy.
4. **Cross-endpoint reuse is a separate claim.** Send the used token to a *different* endpoint
   (e.g. login token → password-reset endpoint). Often it fails, which means the token IS bound to
   the action while not being single-use. Report the two properties separately; do not merge them
   into one inflated "captcha bypass".
5. **Turnstile ≠ Google v2 for automation.** Turnstile tokens are readable from the widget input
   and replay cleanly. With invisible/checkbox Google v2 the response textarea is frequently empty
   in headless/CDP automation, so you cannot harvest a token at all — record that endpoint as
   **unverified** instead of assuming the same behaviour.

**Honest severity:** token replay removes the per-attempt cost of solving a challenge, but if the
app still enforces an IP/device/account lockout the impact is bounded. File it P4/P5 as
"insufficient anti-automation" with the lockout named as a mitigating control — not as
"authentication bypass". Do not hammer the form to test it (many programs treat aggressive
automation against auth forms as abuse); 3–4 requests is enough evidence.

**App-side symptom worth recognising:** after one failed submit the widget can keep serving an
already-consumed token, so every *legitimate* retry on the same page load fails with a captcha
error. Hard-reload before each attempt in your own automation, and treat a sudden "captcha failed
even with a token present" as this artefact rather than a new bug.

## Autonomous Testing Priority

**The fastest test: just omit the CAPTCHA field entirely. Most CAPTCHA bypass bugs are client-side-only validation.**

**Pattern 1 — Omit the CAPTCHA field (most common, most automatable):**
1. GET the form/endpoint that shows a CAPTCHA to understand its field name (usually `g-recaptcha-response`, `captcha`, `captcha_token`, `captcha_answer`, `h-captcha-response`)
2. POST the form with ALL fields EXCEPT the CAPTCHA field
3. If the action succeeds (200, redirect, or "success" message) → no server-side CAPTCHA validation
4. Proof: the state-changing action completes without a valid CAPTCHA field (compare against a baseline request that includes it)

**Pattern 2 — Empty or null CAPTCHA value:**
Instead of omitting the field entirely, include it with an empty string, `null`, `0`, or `undefined`:
```
captcha=&email=test@example.com&password=test123
```
Some apps validate field presence but not content.

**Pattern 3 — Replay a previously solved CAPTCHA token:**
1. Complete one legitimate CAPTCHA challenge and capture the `g-recaptcha-response` token
2. Submit a second request immediately with the SAME token value
3. If the second submission also succeeds → token is not single-use (replay attack)
4. A replayed token can be shared across automated requests

**Pattern 4 — Test without CAPTCHA on similar endpoints:**
Some apps add CAPTCHA to the registration form but forget the password reset, API endpoint, or mobile API path (`/api/register` vs `/register`). Try the same action via the API path without any CAPTCHA field.

**Pattern 5 — Rate/throughput-gated "prove you're automated" challenges:**
Some apps define CAPTCHA "bypass" as simply exceeding the rate a human could plausibly sustain —
e.g. "N submissions within T seconds" — checked by a middleware that counts REQUESTS REACHING the
route, not successful outcomes. Garbage/placeholder payloads satisfy this exactly as well as valid
ones, since the counter increments regardless of whether the request's own validation passes.

**Timing note (sliding-window counters):** don't solve this one request at a time — a sequential
pace (seconds between each request) structurally cannot land N requests inside a short sliding
window, and issuing more requests serially does not fix it. A typical failing pattern is 12
requests spread across ~250 seconds when the check requires ~10 requests within 20 seconds.
Instead fire the requests **concurrently** (e.g. `"concurrency": N` on a single request call, or
any parallel-request primitive your tooling offers, with N >= the required count) so they arrive
simultaneously and satisfy the sliding window trivially. Check the endpoint's own
required-field validation first (e.g. a `rating` field that can't be null) so the concurrent
payload is at least well-formed enough to reach the counting middleware, even if other fields
(like the CAPTCHA answer itself) are wrong or reused.

**What to skip in automated testing:** Solving real reCAPTCHA/hCaptcha programmatically (OCR, audio bypass) requires external services. Only attempt if patterns 1-4 fail and the test budget allows.

**Proof:** Any successful state-changing action (account created, login succeeded, form submitted) that completed without a valid CAPTCHA token confirms the bypass.

---

## Vulnerability Classes in This Skill

### 1. Client-Side-Only CAPTCHA Validation
JavaScript hides/disables the submit button until CAPTCHA is solved, but the server never checks the CAPTCHA token. Direct API calls bypass the UI gate entirely.

### 2. CAPTCHA Not Tied to Session or Action
A token solved for login is accepted on the registration endpoint (or any other). The server validates "is this a real CAPTCHA solution?" but not "is this the right solution for THIS action?".

### 3. Single-Use Not Enforced
CAPTCHA tokens (especially reCAPTCHA v2) are meant to be consumed after one use. If the server doesn't revoke them after verification, a single human-solved token becomes reusable for many requests.

### 4. CAPTCHA Added Reactively (Only After N Failures)
Some apps only show CAPTCHA after 3-5 failed login attempts. Before that threshold, no CAPTCHA is required → an attacker can make N-1 attempts per account indefinitely by resetting state between attempts.

### 5. Static or Predictable CAPTCHA
Math CAPTCHAs (`3 + 4 = ?`), simple image CAPTCHAs, or text CAPTCHAs with a finite answer set can be automated. These are custom CAPTCHA implementations, not Google/hCaptcha.

---

## Impact Chain

CAPTCHA bypass alone: **Medium** (enables automation of rate-limited actions)

CAPTCHA bypass + login endpoint = **brute force gate removed** → chain with `hunt-brute-force` → High/Critical

CAPTCHA bypass + registration endpoint = **account farming** → abuse, spam, resource exhaustion

CAPTCHA bypass + password reset = **token flooding** → chain with `hunt-forgot-password`

---

## Related Skills

- **`hunt-brute-force`** — CAPTCHA is often the only rate-limit gate; bypass unlocks brute force
- **`hunt-forgot-password`** — reset endpoints sometimes protected by CAPTCHA only
- **`hunt-race-condition`** — race the CAPTCHA validation window (submit before the token is revoked)