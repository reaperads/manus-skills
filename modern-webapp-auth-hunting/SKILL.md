---
name: modern-webapp-auth-hunting
description: Use when auditing authenticated web apps in bug bounty.
version: 1.0.0
author: Fauzi Susanto
license: MIT
metadata:
  hermes:
    tags: [bug-bounty, web, auth, idor, bola, server-actions, nextjs, cdp, csrf]
    related_skills: [hunt-idor, hunt-auth-bypass, hunt-oauth, bb-methodology]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Modern Web App Auth Hunting (browser-CDP + server actions)

## When to Use
Trigger when the target is a modern JS-framework web app with:
- Next.js/React/SPA pages and `_next/static/chunks` in HTML
- `Vary: rsc, next-router-state-tree` or `next-action` POST headers (Server Actions / RSC)
- any authenticated `/app/*` or dashboard surface requiring a session cookie
- Disposable-account flows (signup OTP, invites) needing repeatable test identities

Class-level playbook for authenticated testing of modern JS-framework web apps where the UI is a
Next.js/React SPA and state-changing ops run through **Server Actions / RSC** (multipart POST to
the page URL with `next-action` header). curl-only testing fails on these apps; you drive a real
browser via Chrome CDP.

## Mindset (user-mandated — non-negotiable)
- **Exploiter, not defender.** "Apakah ini ke-block?" is the wrong question. The right question:
  "Gimana caranya nembus?" Every surface gets an attack matrix, not a single check.
- **Real tools per class, not just curl.** sqlmap for SQLi, dalfox for XSS, nuclei `-tags` for
  class sweeps, ffuf for discovery, interactsh for OOB. Curl is for verification/headers only.
  The user will call you out ("kamu gunakan semua tools? bukan sekadar curls?") if you lean on curl.
- **Never stop at "bersih".** A clean first pass is an invitation to deep-dive: child-object IDOR,
  file upload, Pro-gate bypass, share/co-owner flows, MFA-gated flows, server-action replay.
- **Server-side enforcement is the only truth.** UI hiding a button proves nothing. Replay the
  server action directly with tampered values / another account's cookie / evil Origin.
- **Honest negatives are still deliverables.** When a target genuinely holds (all vectors blocked),
  document the evidence trail — future sessions use it to avoid re-testing and to justify "no finding".

## Setup
### Two isolated browser profiles (account isolation)
Same Chrome profile shares one cookie jar — a second tab just redirects /signup to the logged-in
dashboard. Use separate profiles + ports per test account:
```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="$LOCALAPPDATA/Temp/qw-chrome-debug" --no-first-run --no-default-browser-check about:blank &
# second account: port 9223 + qw-chrome-debug2
```
**`--remote-allow-origins=*` is mandatory.** Without it, Python `websocket-client` gets
`403 Rejected an incoming WebSocket connection` on the CDP WS handshake. If the port was already
held by an older Chrome without the flag, kill the exact PID (`netstat -ano | grep :9222`).

### Disposable accounts + OTP (mail.tm)
`scripts/mailtm_helper.py` creates inboxes, fetches 6-digit OTPs, and extracts invite/share links.
Use ONE mailbox per test identity, plus a fresh one per tamper test (mail.tm rate-limits creates).

### TOTP enrollment (when MFA gates a valuable flow)
MFA setup pages show a base32 secret (grab `[A-Z2-7]{20,}` from body) + a confirm code field.
Generate the code in Python (RFC 6238, SHA1, 30s period) and submit — no phone needed. Secret
rotates on page reload: read the CURRENT secret from the live page, don't reuse an earlier one.

## Workflow
1. **Fingerprint**: headers (`Vary: rsc, next-router-state-tree`, `_next/static/chunks`,
   `next-action` header on POST) = Next.js server actions.
2. **Map authenticated surface**: nav each `/app/*` route in CDP, collect `performance resource`
   + `Network.requestWillBeSent` URLs, download per-route chunks, grep `"/api/...`, `/app/...`,
   `fetch("/api/...")`, action IDs. Also probe `/developers` → OpenAPI spec + docs (richest surface).
3. **Build account 2 (and 3) in isolated profiles** (see Setup). Create an object (property/
   business) in account 1 to get a target UUID.
4. **Cross-tenant matrix** (per state-changing action):
   - page-level: acc2 → acc1 object URL (expect 404/403 baseline)
   - server-action replay: acc1 action body + acc2 cookie → expect `Server action not found`/500
   - propertyId/BOLA swap: acc2 opens form on THEIR object, swaps id to acc1's → expect "not found"
   - role tamper: change hidden/radio values (`viewer`→`owner`) before submit → server falls back
   - accept-token binding: try accepting acc3's invite while logged in as acc2 → must be rejected
5. **Business logic**: over-allocation (invite sharePercent that pushes total >100%), negative/0
   sharePercent, invite-then-replay with tampered percent.
6. **CSRF (server actions)**: capture legit POST body via `Network.getRequestPostData`, replay
   SAME body + SAME cookie but `Origin: https://evil.example.com` → 500/digest error = enforced;
   2xx + double-write = vulnerable. Confirm via a count/export endpoint, never just status code.
7. **Export/injection**: XLSX formula injection — inspect `xl/sharedStrings.xml` (`<si><t>`) vs
   `<f>` elements; real formula = `<f>`. CSV — check for `'` prefix mitigation.

## Verify server-side, always
- After any write attempt, confirm via the app's export/JSON endpoint (count rows, list values).
- Password state after change attempts: actually log in with old vs new password in a clean profile.
- One 500 from a hand-built urllib POST ≠ vuln — repeat via browser (missing headers cause 500s).

## MFA / 2FA surface — audit the controls, not just the bypass

If the app lets you enroll 2FA (your own test account), enroll it and then verify each control.
Every one of these is reportable positive evidence when it holds, and a headline finding when it
does not:

1. **Half-authenticated session** (password accepted, code not yet entered) must not reach
   `/app`, `/app/account` — expect 307 → `/login`.
2. **Sensitive actions enforce the code server-side.** Watch for the form *revealing* extra
   fields only after the first submit (observed: changing the account email added
   `currentPassword` + `mfaCode`, and the copy said a code also goes to the NEW address before the
   change lands). Wrong code + "turn off 2FA" must fail and leave 2FA on. Saving a tax/NINO-style
   identifier must not change the stored value.
3. **Attempt cap**: count wrong codes until lockout (observed: 5 → "wait about 15 minutes"), then
   prove it is **account-level** (fresh login + CORRECT code still refused during the window) and
   that it **expires** (log in again ~15 min later).
4. **Code replay** — the clean test is ONE TOTP code driving TWO logins inside the same 30s
   window; the second must be refused. Do NOT judge replay by reusing a code for a data-entry
   action: that action's own value validation can reject you for an unrelated reason and you will
   draw the wrong conclusion (this session: a NINO ending in "E" failed the *checksum*, not the
   replay check — read the raw RSC error segment `1:{"error":"..."}` to tell them apart).
5. **Recovery path**: read `/login/mfa/recover` style copy (24h delay + "we'll email you first so
   you can stop it" = sound design). Do not press it on a borrowed account — it starts a real 24h
   disable timer.
6. **Expectation gap worth reporting**: MFA covers interactive login only. An API key keeps
   working while the login is locked out — say so, because "2FA is on" reads to a customer as
   "the data is protected".
7. **ATO chain to test explicitly**: stolen session → change email → password reset. It must
   require password + TOTP + a code to the new address. Any missing leg is the finding.

## When the app computes money (calculation-engine correctness)

- **The product's own itemised panel is the oracle.** Drive one controlled scenario and read the
  breakdown (income / expenses / profit / taxable / credit lines), not the headline number.
- **Isolate one variable at a time.** Add a £1 restricted cost versus £0 and watch whether the
  allowance/disregard comparison flips — a 1-unit delta proves the operator bug cleanly (this
  session: a £1 finance cost moved a £1,000 allowance the wrong way).
- **Enumerate EVERY write path to the same data** before declaring an invariant enforced: form
  add, form edit, delete, bulk import (CSV *and* XLSX), public API, and any AI-suggest / review
  queue path. Invariants are commonly enforced on the add form and nowhere else — that gap is the
  finding, and it is worth listing the paths you checked.
- **Prove the impact on the number that matters** (tax/amount due), with before/after values, then
  remove the test data and re-read to show it reverses.
- Verify the rule against the authoritative source before claiming (HMRC manual, gov.uk, RFC) and
  quote the rule in the report. Keep severity honest: a self-scoped bookkeeping error is not a
  cross-tenant break.

## Tool sweeps worth running (and their expected noise)

Order that fits one session: `ffuf` route discovery on both `/api/v1` and `/app` (`-ac` is
required — SPA catch-alls otherwise match everything) → `arjun` with the auth header for hidden
params → `nuclei` with LOCAL template dirs by tag (misconfiguration/exposures/technologies; a
whole-directory run can blow past 10 minutes per target, so run it in the background) → `sqlmap`
(`--level 3 --risk 2 --technique=BEUST`) on the parameter that actually reaches a query →
`dalfox` with the session cookie → `trufflehog` on the client bundles → `wafw00f`/`naabu` for the
edge.

Expected noise, so you don't over-read it:
- nuclei returns INFO header/CSP findings only on a hardened target.
- dalfox flags `Reflected ... param` for RSC flight echoes (escaped text in
  `self.__next_f.push`, not a sink) — confirm in the DOM before believing it.
- sqlmap can self-disprove its own verdict (`parameter ... does not seem to be injectable` after
  an initial "appears to be injectable") and may report thousands of 403s from the WAF — read the
  final `[CRITICAL] all tested parameters do not appear to be injectable` line and quote the
  403 count as a coverage caveat.
- A tool that misbehaves is an environment issue, not a target finding: check `-h` when flags act
  oddly (a stub binary can shadow the real one) and log it in your own notes, not the report.
- Long scans: background + explicit `timeout`, keep the raw output files — the verdict line is
  usually all you need later.

## Pitfalls
- **Playwright auto-dismisses native dialogs.** Buttons whose handler is
  `if (!confirm(...)) return;` never POST: no network request, page unchanged. Install
  `pg.on("dialog", lambda d: d.accept())` BEFORE concluding an endpoint is broken or unauthenticated.
  Also check `button.disabled` — a confirm-name field can gate the button until it matches.
- **Duplicate `id` attributes** (a wrapper div and the input inside it sharing `id="x"`) make
  `#x` resolve to the div: the native value setter throws `Illegal invocation` and Playwright's
  `fill()` refuses with "Element is not an <input>". Target by attribute (`input[name="x"]`).
- **Borrowed/vendor-granted accounts**: 2FA you enable locks the OWNER out (they don't hold the
  secret); never fill a documented daily write cap (it locks their quota for ~24h); keep a
  cleanup list and re-verify the account state (entries, properties, shares, MFA) at the end.
- curl/urllib multipart to Next.js Server Action endpoints → 500 (needs browser-generated
  `$ACTION_REF/_KEY` state + `next-action` header). Do signup/login in the browser.
- `requestWillBeSent.postData` is TRUNCATED — always `Network.getRequestPostData` for full bodies.
- HttpOnly session cookies are invisible to `document.cookie`; use `Network.getAllCookies`.
- mail.tm: poll inbox (3s x N); OTP subject is `Your <site> code is NNNNNN`; invite/share emails
  contain the accept link in text body.
- Cloudflare will 403 raw Python/urllib bursts; browser + cookie context works. `wafw00f`-style
  checks: treat 403 storms during tool scans as rate limiting, not WAF-block on a single request.

## Support files
- `scripts/cdp_helper.py` — minimal Chrome CDP driver: connect, navigate, js(), cookies, full
  post-body capture via getRequestPostData.
- `scripts/mailtm_helper.py` — mail.tm inbox create/OTP/link extraction.
- `references/quarterwise-vdp-case-2026-09.md` — full case study: surface map, every tested
  vector, and the exact mitigations that held (evidence for "hardened target" conclusions).
- `references/mfa-business-logic-and-tool-sweep.md` — MFA/2FA control matrix with observed
  numbers, calculation-engine oracle recipes, and the concrete tool sweep results
  (ffuf/arjun/nuclei/sqlmap/dalfox/trufflehog) from a Pro-plan follow-up engagement.