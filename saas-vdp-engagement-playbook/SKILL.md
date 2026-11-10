---
name: saas-vdp-engagement-playbook
description: Use for VDP bug-bounty audits of SaaS web apps.
version: 1.0.0
author: Fauzi Susanto
license: MIT
metadata:
  hermes:
    tags: [vdp, bug-bounty, saas, nextjs, server-actions, mfa, otp, idempotency, csrf, race-condition, report]
    related_skills: [security-arsenal, bb-methodology, hunt-race-condition, hunt-business-logic, hunt-oauth]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# SaaS VDP Engagement Playbook

## When to Use

Start here when running an authorized VDP/bug-bounty engagement against a SaaS web app — especially a Next.js/React app with a signed-in area and an API (tax/accounting SaaS, fintech, property tools). Use it after reading the target's disclosure policy through reporting and vendor email delivery. It complements `bb-methodology` (5-phase workflow) with implementation details: multi-account browser rig, Server Action testing traps, OTP/MFA lockout verification, idempotency-race detection, rate-limit-aware batch design, and single-send email discipline.

Class-level playbook distilled from full-scope VDP engagements against Next.js SaaS apps (e.g. UK MTD tax software). The target was unusually hardened; the value here is the *methodology that proved coverage* and the pitfalls that would have caused false findings or duplicate sends.

## 1. Engagement Setup (before any exploit)

1. **Read the VDP/disclosure policy first** — scope, safe harbor, rewards, and rules. Quarterwise-style policies: main domain + signed-in app + API in scope; ALL subdomains & third-party services (Stripe/Postmark/Cloudflare/HMRC) out of scope. Follow rules exactly (own accounts only, no third-party email, no DoS/volume) — violations void the report, not "unlock" it.
2. Write engagement type + scope as the first line of notes (bb-methodology Phase 0).
3. Record `/api/v1/openapi.json` and `/developers/docs.md` if exposed — free API surface map. Note promised behaviors (e.g. "writes are idempotent on externalRef") — they become checkable claims for the UI path.

## 1b. Resuming a multi-session engagement ("lanjutkan audit X dari progres terakhir")

This operator runs engagements across days and opens with exactly that sentence. Do not restart
from recon and do not ask what to work on — the engagement's own artefacts are the brief.

1. **Read the engagement's own state first**: the progress directory (`_progress/<target>/`), the
   findings doc (`FINDINGS*.md`, `PRO-*.md`), and the newest `SESSION-*.md`. `session_search` on
   the target name recovers the previous session's closing message, which usually ends with an
   explicit option list ("(a) … (b) … (c) … — default is (b)"). Treat that list as the queue and
   say which item you are closing.
2. **The `BELUM DIUJI / UNTESTED / COVERAGE GAPS` block is the work queue.** It is written by the
   previous session specifically to stop the next one re-deriving it. Pull the items from there
   rather than inventing new surface — then, when you have closed one, rewrite that block.
3. **Verify the live state before running anything.** Saved cookies and API keys expire: check
   `GET /api/v1/me` → 200 and that the browser-state cookie still returns 200 on an authed page.
   A half-dead session produces a page of confusing results that look like target behaviour
   (see the "re-check `location.href`" pitfall in `nextjs-server-actions-audit`).
4. **Count the data before trusting the previous cleanup.** Enumerate `/sources` and read each
   one's entries — leftovers hide in a *previous tax year* the default list does not render, and
   an earlier import may have left an extra probe property. Restore a clean account before you
   add new test data, or your scenarios aggregate with the leftovers and the numbers stop making
   sense.
5. **Re-verify a re-used finding before it goes back in the report.** Two outcomes both matter:
   the file/API write-path bug reproduced exactly as written (keep it), while an item from the
   previous draft had to be **softened** ("the form asks for no code" → "I inspected the fields;
   the submit never fired through automation, so the server behaviour is unverified"). Re-checking
   your own prior claim and downgrading it is part of the job, not a setback.
6. **Re-stage the deliverable, don't spawn a second one.** Find the existing draft's uid, confirm
   nothing was sent, then supersede it (delete the old draft, append the updated one) so the
   thread keeps exactly one copy. Verify the new body by re-fetching and probing landmark phrases
   per section.
7. **Report resume results in the same shape every time**: what was already verified (unchanged,
   one line), what you closed this round with figures, what is still open with the reason, and the
   files touched. The operator is tracking several engagements in parallel; a consistent shape is
   what makes that possible.

## 2. Multi-Account Browser Infrastructure

Per-target test rig that survived an entire engagement:

- **Isolated Chrome profiles per account**, one port each:
  `chrome.exe --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir=...`
  `--remote-allow-origins=*` is REQUIRED or external websocket clients get HTTP 403.
- **Temp mailboxes** via mail.tm API (`POST /accounts`, `POST /token`, `GET /messages`) — one mailbox per account; poll for OTP/invite/share emails and extract links/tokens.
- **Login with MFA**: enroll TOTP in the app (settings → authenticator → "Show setup code"), extract base32 secret from the page, generate RFC 6238 codes in Python (hmac/hashlib/struct). Store secret for later login + NINO/role-change MFA prompts.
- **Cookie extraction** for CLI tools: CDP `Network.getAllCookies` (works for HttpOnly), save as `Cookie:` header. Refresh after each re-login.
- **Ground truth = account export JSON** (`/api/account/export`): verify what *actually* persisted (transactions, NINO, property attrs, roles). UI "saved" text lies; export is the source of truth.

## 3. Next.js Server Action Testing — Critical Pitfalls

Server Actions (`/app/...` POSTs, multipart with `$ACTION_REF/KEY` + `next-action` header) are the real attack surface in Next.js apps. Testing them wrong generates **false positives**:

- **Manual urllib/curl replay of a captured Server Action body almost always returns 500** — this is an *artifact* of missing `next-router-state-tree` / `_N_` prefixed field names / action-key session binding, NOT a finding. The 500-vs-404 matrix distinction here: POST + `multipart/form-data` to unknown `/api/*` paths → 500 (Next.js body-parser runs before route match); same path with GET/PUT or empty body → 404. Report to vendor as a hygiene/status-code inconsistency, not a vuln.
- **Use the browser (CDP) to perform actions**, capturing requests via `Network.requestWillBeSent` + `Network.getRequestPostData` (postData in requestWillBeSent is truncated).
- **Cross-user server-action replay** (capture owner's action, send with another session's cookie) → expect 500 + action-bound errors; that's the server binding actions to session, i.e. safe.
- **RSC flight data reflection ≠ XSS**: payloads echoed inside `self.__next_f.push([1,"...\u003cscript\u003e..."])` are JSON-escaped (`\u003c`, `\x3c`, `&lt;`). A naive grep for the payload in raw HTML flags it. Check DOM for real executable elements (img src=x count, script textContent contains alert, svg onload). Escape forms to check: `&lt;`, `\u003c`, `\x3c`.

## 4. OTP / MFA / Rate-Limit Verification

Quick, decisive tests (own accounts, small N):

- **Login wrong-password lockout**: count attempts until "Too many attempts. Please wait..." (typical 11).
- **Login-MFA wrong-OTP lockout**: count until block (typical 6).
- **MFA-recovery-code lockout**: trigger "Forgot MFA?" → email code → wrong codes until block; then **fresh session, submit 1 wrong code** — if "Too many attempts" persists, it's **account-level lockout (safe)**; if it resets to "wrong code", counter is per-session (**brute-forceable → finding**).
- **Session-rotation OTP test**: after block, fresh login + wrong OTP again. Account-level lockout = anti-brute solid.
- **OTP reuse cross-email**: use an old OTP from another signup on a fresh signup flow → expect "That code is not correct" (OTP bound to email).
- **User-enum**: signup + forgot-password, existing vs fresh email → identical responses/timing = no enum oracle (forgot timing needs n≥4; means within ~0.1s = indistinguishable).
- **Timing-based SQLi false positive**: a single 12s delay on `' ; WAITFOR DELAY '0:0:5'--` was pure jitter. Always validate with **n=10 interleaved control/payload trials**; signal requires payload mean ≥ control mean + 2σ (rule from bb-methodology). Here payload mean was actually *faster* than control → clean debunk.

## 4b. Response-Identity Rule (200 ≠ exists)

Before recording any "endpoint found", confirm the response is *specific to that path* — not a catch-all, a framework rewrite, or an executed-script stub. **Verified false-positive signatures:**

| Symptom | What it actually is | Confirm by |
|---|---|---|
| Every arbitrary path → 200 + byte-identical HTML | **SPA/SSR catch-all** (React Router/Remix/Next). A random 24-char path returning the same `len=5932` shell = shell, not endpoint | Request a random nonsense path; compare body length/hash |
| `/index.php~`, `/x.bak` → 200/301 | **Framework route fallback**, not a leftover backup | Diff against baseline root |
| `/vendor/*.php` → 200 with **0 bytes** | PHP **executing** (no source disclosure). A real leak is non-empty | `Content-Length: 0` + `text/html` = executed stub |
| Path → 202 containing `/.well-known/sgcaptcha/` | **Hosting WAF/CAPTCHA interstitial**, not a signup/activate endpoint | Grep body for `sgcaptcha`, `cf-challenge`, `__cf_chl` |
| Keyword grep hit (`locked`, `blocked`, `error`) in HTML | **Boilerplate JS/comment text**, not a control firing | Print ±100 chars; inside a `<script>` string about popups = decoration |
| Header value reflected into a **JSON error string** | Lookup echo, not injection | Require reflection into `Location:`, `Set-Cookie`, or a rendered HTML node **and** a cacheable response. `no-cache` + JSON-escaped = no impact |
| Marker domain appears in `Location:` | May be a **signin bounce echoing the param**, validation deferred to token exchange | Decode it; is the marker the redirect *target* or an echoed parameter? |

**Rule:** ask *"is this response specific to this path, or would any path get it?"* Diff against a **random-path baseline** before claiming existence.

**Lesson from an Atmail (email SaaS) engagement:** ~7 candidates died to this rule — SPA shell 200s (every "endpoint" on the billing portal), executed-PHP 200s, `/index.php~` 301, a SiteGround CAPTCHA 202 (`/activate`), a "lockout" keyword that was boilerplate JS, and an XFH reflection that was JSON-escaped + `no-cache`. All would have been N/A'd.

## 4c. Cross-Component Control Comparison (upgrading a weak control finding)

"Missing rate limiting" is on most NEVER SUBMIT lists and reads as a hardening preference. The evidence that upgrades it is **comparative**:

1. Enumerate the vendor's *separate* components on in-scope hosts (gateway, admin, BFF, signup/billing API — often different stacks behind different hostnames).
2. Probe the **same control class** on each (throttling, preconditions, idempotency, CSRF, session binding).
3. If one absorbs unbounded attempts while another answers `429` + `Retry-After`, you have an **internal inconsistency**, not a missing capability.

**Why a triager cares:** "they can't do X" invites "known limitation". "They do X *here* and not *there*, same product, same control" is a defect with a fix path. It converts a probable-Informative into an arguable finding. **Corollary:** quote the vendor's own throttling shape in your remediation (e.g. the exact `retryAfter` field they already emit elsewhere) — proves the fix is wiring, not new engineering.

**Boundary discipline:** label coverage accurately. A flow that throttles OTP resend but not password verify is **partially** controlled — never write "no rate limiting anywhere". Overstating coverage converts a valid finding into a retracted one.

**Lesson from Atmail:** the login gateway absorbed 60 consecutive failures with zero `429` (config value `blockDuration: 0` confirmed lockout disabled). On its own, that class was explicitly written off as Informative by the program. The vendor's *separate* signup/billing BFF emitted `429 {retryAfter:900}` after five OTP resends, `409 PRECONDITION` on stage-skipping, and required an `Idempotency-Key` on payment — same vendor, opposite behaviour. That comparison became the strongest paragraph in the report.

## 4d. Cloud-Bucket and Takeover Claim Gates

- **S3/cloud bucket (CWE-494):** the claim is *world-listable or world-writable*. `403 AccessDenied` on list/read/PUT is the **secure** result — not a finding. `404 NoSuchBucket` is *not better*: the name is unused. Test list (`GET /`), read (known object key), write (`PUT` a benign unique-named marker) separately; only list=200 or write=2xx counts. Delete your marker and say so in the report.
- **Subdomain takeover (CWE-16):** **dangling CNAME ≠ takeover.** The disqualifier is *registrability of the target*. If the CNAME target sits inside the victim's own apex (`foo.target.com` → `dead-host.target.com`), an attacker cannot register it — that's DNS hygiene, not a takeover. Only third-party targets (S3/Heroku/GitHub Pages/Azure…) are claimable. Run `nuclei -t http/takeovers/` **and** resolve the chain one hop past the first CNAME before concluding.
- **Config values containing raw HTML** (`<script>`, `<iframe>`, `<style nonce=…>`) are not automatically XSS. You need a reachable *write* path **and** proof the render is unsanitised. If the render path is DOMPurify-backed (e.g. a `SafeHtml` component), raw HTML in config is by design.

## 4e. Signup/Billing BFF Probing (session state machine)

Modern signup payment flows expose a rich, mostly-unauthenticated surface. Map it from the SPA bundle, then attack the *state machine*:

- Session create is often **unauthenticated by design** (`POST /api/signupapi/v2/sessions` → 201 + session cookie). That is not a finding.
- The session JSON usually leaks server-authoritative fields — `emailVerified`, `mobileVerified`, `vip`, `payment.methodId`, `payment.subscriptionId`, `plan`, `stage`. **Test mass assignment** by sending those back as input; the good implementations ignore them (verify by re-reading state).
- **Test stage skipping** (set plan/identity/payment before verification). Correct implementations answer `409 PRECONDITION` naming the required stage.
- Check for `Idempotency-Key` requirements on payment calls, version-downgrade paths (`v0/v1/v3` → 404 = good), and whether the signup cookie unlocks the OIDC-gated billing API (should not).
- Check the session cookie flags: `HttpOnly; Secure; SameSite=Lax; Path=/…; Max-Age=…` is correct.

**Experience note:** on Atmail's Junara portal *every one of these was implemented correctly* — no bypass, no mass assignment, throttling with `429 retryAfter`, durable across the session. Budget your time accordingly: a hardened BFF is a legitimate negative result, not a failure to try.

**OTP-deliverability blocker (design batches around it):** the signup verification email may never arrive even though the API returns `202` (fire-and-forget). Poll INBOX **and** Spam, listing *all* senders rather than a sender-filtered match — a filtered match will hand you a 6-digit code from an unrelated email (e.g. another vendor's "your code is…") and you will submit a wrong OTP. If it never arrives, stop at `email_pending`, record the blocked stages honestly, and do not claim anything about later-stage price/coupon tampering.

## 4f. Shared-Resource / Cross-Account API Scoping

When the app has sharing (co-owner, adviser/accountant, team member), the API is a second
authorization surface that the UI's permission copy says nothing about. Test it with **two
accounts you own** — no victim needed.

Matrix that matters (each cell = GET `/api/v1/sources` + a POST to the shared resource):

| Grant | See in API? | Write via API? | Expected |
|---|---|---|---|
| owner | yes | yes | yes |
| co-owner (shares the books, `role: sharer` + `sharePercent`) | **yes** | **yes** | by design — but this is now a machine path into someone else's books |
| adviser "Can keep the books" | yes | yes | by design |
| adviser **"View only"** | **no** | **no** (404 `source_not_found`) | the control to verify |

- Acceptance is what activates it: a pending invite does **not** appear in the API. Re-check
  `/sources` after the invitee clicks Accept.
- If a view-only adviser's key can read or write → that is a clean privilege-escalation
  finding. If it 404s, record it as a proven control (it is the sentence that makes your
  cross-account finding look rigorous rather than alarmist).
- The sharp finding shape: **the grant is legitimate, the payload is not.** "Co-owner may
  add entries" is intended; "co-owner's key can write a fabricated tax/credit/refund line
  into the owner's books, which then appears in the owner's own export" is not. Say both
  halves explicitly or the vendor will answer with "working as designed".
- Docs gap worth one paragraph: if the public API reference never mentions shared sources
  while `/sources` returns them, note it — it means the integrator (and the owner) cannot
  know a second party's key is writing into their books.

## 4g. Impact Proof: drive the app's own derived number, then restore

A validation gap is only Low/Informative until you show it moving a number the product
computes for the user. For finance/tax/accounting SaaS the derived number is the impact.

Procedure (all inside your own account; no HMRC/authority connection needed):

1. Put the account into a state where the derived number is **non-zero** (here: add a large
   income entry so the estimated tax is positive). If the derived figure is `£0.00`, a
   reduction is invisible and the test proves nothing — this exact mistake cost a round trip.
2. Read the breakdown (gross tax, adjustment lines, net due) and **screenshot it**.
3. Inject the fabricated rows through the vulnerable path.
4. Read the same breakdown again — the adjustment line should equal your injected total and
   the net due should fall (here: Estimated tax £11,327.77 → "still to pay" £0.00).
5. **Delete the injected rows and read a third time** — the net due must come back
   (£11,227.77). That third reading is what converts a correlation into a causation and it
   is also your cleanup.
6. Write the three readings as a table in the report. Quote the app's own explanatory copy
   ("this nets off the tax already deducted at source that you recorded") — it proves the
   number is load-bearing, not decorative.

**Domain-rule testing is a vulnerability class of its own** in regulated software: tax
deadlines/basis rules (cash vs accrual), ownership-share handling, allowance/credit
arithmetic. Read the vendor's own policy/help text for the promised rule and test *that
rule* — you are checking the product's compliance claim, not just its HTTP codes.

## 4h. Vendor-Granted Test Accounts: isolate, then clean up

When the vendor hands you a 30-day Pro account, you are a guest in a live tenant.

- **Metered/global caps are off-limits without written permission.** A documented quota
  (e.g. "5,000 transactions written per 24h") is account-wide: filling it locks the vendor's
  own test account for a day. Skip it, and say in the report *that you deliberately did not
  test it and why* — that reads as discipline, not as missing coverage.
- **Bulk arrays can trip the cap accidentally.** A 501-item request that is *supposed* to be
  rejected is safe; if the boundary check is broken it silently writes all 501. Prefer a size
  you would be happy to delete.
- **Isolate destructive/volume tests in a throwaway container** the product lets you delete
  (here: a second property created just for the pagination test, then deleted). Never run
  them against the resource the vendor gave you.
- **…unless the operator says the account is his own and authorises writes.** This operator does,
  in these words: *"ini akun pribadi sy yg dikasih akses pro, bebas diujicoba asal tidak connect
  dan upload data k hmrc."* Once stated, write and destructive tests on **that account's own test
  objects** are in scope — create and delete test entries, commit and undo imports, confirm queued
  records, populate a review queue so its action can be reached. Do not re-ask each session, and do
  not treat it as a reason to skip the write-path matrix. The permission is bounded: only objects
  you created, only in that tenant, and the tenant is left as found.
- **The boundary that survives every authorisation: the external authority.** Never connect to or
  submit anything to the regulator (HMRC filing/connect, quarterly or annual submission, final
  declaration). Some actions exist *only* to file — treat the whole submit family as never-invoke,
  even when the same session has blanket write permission, and say so explicitly in the report
  ("the HMRC-submit family was never invoked"). Never press a control whose only outcome is a
  filing, and never use "click any submit on the page" as a fallback.
- **Creating data can be the only way to reach an otherwise untestable action.** To test a
  review-queue `Confirm`, the queue has to be non-empty: upload a CSV whose row categories are set to
  the *"Review later"* mapping option, import it, and one row lands in the queue. That is legitimate
  under the authorisation above — delete the created rows afterwards and disclose any residue
  (e.g. an empty import-batch record with no UI to remove it).
- **Prefer the proven per-row cleanup over an "Undo import"-style control** that emits no request;
  delete the rows individually, and check the tax-year view and tab first or the rows are not in the
  DOM at all.
- **Restore what you can and prove it.** Re-read `/sources` and the export after cleanup and
  put the final state ("1 property, 0 entries") in the report footer. Also restore any
  cosmetic damage — a data-driven account *name* you changed for a CSV test must be changed
  back.
- Destructive UI actions in the vendor's tenant deserve their own care (see the
  destructive-action pitfall in `nextjs-server-actions-audit`).

## 4i. Programs That Outlaw Automation (the scope gate overrides the launcher)

Some policies ban automated vulnerability/scanning tools outright (FreeAgent: "TIDAK BOLEH
memakai tool automated vulnerability/scanning … IP bisa diblokir permanen"), plus mass brute force
and account enumeration.  When that happens it **overrides the audit launcher**, which otherwise
mandates scanners and a scanner-evidence gate:

- Do **not** run nuclei/ffuf/gobuster/dalfox/sqlmap/subfinder/naabu/arjun/CORScanner against the
  host, and do not run `audit-run-all.py` — its scanner steps would break the rules you are
  testing under.
- **Phase 0D (`verify-tool-usage`) is N/A-BLOCKED, not "passed".** Its evidence cannot exist
  without violating the program. Say so in one line; never imply scanner coverage you did not have.
- Substitute manual/targeted work at low volume (curl + browser + the vendor's own API with your
  own accounts) and keep the same evidence discipline: one file per probe, status + body saved.
- A negative engagement delivered this way is still a real deliverable — 30+ rows of
  vector / what-was-done / result / evidence path with an honest `BELUM diuji` block beats a
  scanner dump, and the vendor's rules stay intact.

## 4j. A 200 on a resource the UI hides needs an owner-vs-low-priv FIELD DIFF

Testing a low-privilege persona against an API is the highest-yield move on a multi-tenant SaaS —
and the easiest place to manufacture a false finding.

`GET /v2/contacts` returned **200** for a "Time"-only user while the web UI answered
"Sorry, you're not allowed to see that page" for `/contacts`; the same identity was 403 on
invoices/bills/expenses/bank/journal/VAT. Textbook BFLA shape.

Disproof: request **the same object with the owner token and diff the fields**. Owner got
`email`, `phone_number`, `address1`, `town`, `postcode`, `account_balance`, …; the low-priv
response carried only url / org name / first / last / timestamps. The API is *permission-aware*
and shapes the representation by level — deliberate. Not a finding.

**Rule: the status code tells you the resource exists; only the owner-vs-low-priv field diff
tells you whether the access is intended.** (Same family as the §4b response-identity rule —
verify content, not code.) Mirror it on write paths: a write the low-priv persona is *allowed* is
worth diffing against what the UI offers them, and a denied one is a control worth recording.

## 4k. Period/Accounting Locks: drafts are not postings — check the DERIVED REPORT

A "lock the books to date X" control that appears to let writes through is a strong finding
candidate on any finance/accounting target. Before reporting it, separate **posted** from
**unposted**:

| operation dated inside the lock | FreeAgent result |
|---|---|
| create expense / bill | 422 `dated_on is in a locked period` |
| create/edit/delete a **draft** invoice or credit note | allowed (201/200) |
| re-date a **posted** invoice into the lock | 422 `dated_on is in a locked period` |
| `mark_as_sent` (the posting step) on an invoice/credit note dated in the lock | 403 `… is locked.` |
| limited user managing the lock itself (`PUT`/`DELETE`/`GET /account_locks`) | 403 — only Full Access |

The allowed rows are **not** a bypass: drafts have no ledger effect. Prove it with the product's
own report endpoint (`GET /v2/accounting/balance_sheet?as_at_date=<lock date>` was identical
before and after) — the same "drive the derived number" discipline as §4g. Also read the lock
bounds first: `earliest_lock_date` / `latest_lock_date` are in the list response and a lock date
outside them returns a confusing `404 Resource not found`.

Generalised rule: **for a control that guards a period/state, the question is never "did the write
succeed" but "did the number the user sees change".** A candidate that survives the write but not
the report is a false positive — record it as a proven control instead.

## 4l. Windows git-bash rewrites `/<path>` arguments (MSYS path conversion)

Driving an HTTP API from a shell one-liner — `python api.py GET /v2/company` — silently breaks:
MSYS converts `/v2/company` into a drive path, which concatenates onto the base URL and yields a
bogus host (`api.freeagent.comc`), surfacing as `getaddrinfo failed` from `urllib`/`requests`
while `curl` and a plain `socket.getaddrinfo()` in a fresh process work. Hours can go into
"DNS is broken" before anyone prints the URL.

- `export MSYS_NO_PATHCONV=1` for the session, **or** prefer scripts that build the path in
  Python and take only a short token as argv (matrix scripts are immune by construction).
- **Always print the constructed URL** before blaming the network when a script's code works
  interactively but fails as a CLI call.
- Related: system-proxy inheritance is not the culprit when `urllib.request.getproxies()` is `{}`
  — check the URL string first.

## 5. Duplicate-Write / Idempotency Race Detection

The one real finding class that kept surfacing:

- Fire the submit twice in the **same JS tick** (`btn.click(); btn.click();` in one CDP `Runtime.evaluate`) — creates 2 identical rows when the server action lacks idempotency.
- A 150ms-apart double click often only creates 1 (form closes after first submit) → this is a **scripted/replay-only race**, rate it Low, not Medium; normal-user double-click won't trigger it.
- **Verify via account export JSON** (count duplicate (date, type, amountPence) groups; both `externalRef: null`), not by page-text count (label + entry double-counts).
- Contrast with API v1 promise ("idempotent on externalRef") → report as *missing idempotency on UI path* with that contrast as the root-cause argument.

## 6. Rate-Limit-Aware Batch Attack Design

When running payload banks (XSS/SQLi/SSTI/SSRF/CMDi banks × endpoints × params):

- Cloudflare 429s start after moderate volume; batches with `time.sleep(0.08–0.15)` still take 10–25+ min for ~500–1100 probes and get rate-limited before finishing. Design batches to **log incrementally** (append per request), not write the log at the end — a killed/timeout batch otherwise loses everything.
- Expect 429s; treat them as a rate-limit confirmation (itself a defensive signal), and lower concurrency for the tail.
- Keep a cumulative variant counter in the reply; be honest that "1000 variants" gets capped by the server's rate limit, not by effort.

## 7. Finding Validation & Report/Email Delivery

- **One invariant, every write path.** When a control is enforced somewhere, enumerate every
  path that reaches the same data before calling it fixed: UI **add**, UI **edit**, UI
  **delete** (does deleting the parent orphan the child?), **file import** (does the mapping
  screen offer the forbidden value as a dropdown option?), and the **REST API**. A vendor's
  "now refused when adding or editing" is a statement about two paths out of five. Report the
  matrix; the unfixed cells are the finding and the fixed cells are your credibility.
- **Reporting to the operator (this user): plain language first, impact second, severity
  last.** They ask for it explicitly — "jelaskan temuannya dengan bahasa sederhana dan
  impactnya apa" — and a severity table alone is not an answer. Structure it as: what the
  feature is in one line → an everyday analogy → what an attacker can actually do per path →
  **what they cannot do** (the honest boundary) → what it means in the domain (e.g. a tax
  figure that can be fabricated in tax software) → severity, with the downgrade stated
  outright. Then, separately, the technical write-up. Do not skip the "cannot do" half; this
  user downgrades overclaim themselves and expects you to have done it first.
- **Rate-limit claims need a real burst and a UA control.** Sequential requests rarely exceed
  a per-minute quota (125 sequential in 64s ≈ 118/min proves nothing). Fire a concurrent
  burst (200 in ~7s ≈ 1,600/min) and state the observed rate. If the traffic then gets a CDN
  block (`Cloudflare Error 1010 Access denied`) instead of the documented `429`, report the
  *difference*: the documented per-key quota is not enforced and is replaced by a blunt
  IP-level block that also hits legitimate API use. Keep a browser-like User-Agent on all API
  probes and pace afterwards — a CDN block mid-engagement costs you the rest of the session.
- **Validation before report**: reproduce twice, verify via ground truth (export/DOM-reload), then assess severity honestly (scripted-only race → Low). Writing a PDF via `reportlab` (A4, brand colors, no watermark) yields a clean professional artifact; include exec summary, finding with steps-to-reproduce + real evidence, coverage table, hardening observations, remediation.
- **Email to the vendor**: send **once, verified** — Gmail SMTP (smtplib, port 587 STARTTLS, app password) does NOT auto-save to Sent; if you also IMAP-append a copy to `[Gmail]/Surat Terkirim` it looks like a duplicate send. Use ONE code path. Never resend before confirming; save replies the user asks for as **Drafts** (`[Gmail]/Draf` on Indonesian locale, `flag_set=MailMessageFlags.DRAFT`) until the user approves.
- **Human-sounding body**: plain intro, short version of the finding first, PDF highlights, professional close, no "compiled by AI" mention, no watermark.

## Pitfalls (quick list)

- Chrome profiles: separate `--user-data-dir` per account — same profile shares cookies and breaks cross-tenant tests.
- Multi-line buttons (`"Rental property\nA house..."`) need `textContent.trim().startsWith(...)`, not exact equality.
- `process(write)` vs `process(submit)` on Windows PTY: Enter is CR; use submit.
- Lockout traps: after wrong-password/MFA tests the account is locked (6–15 min); run rate-limit tests last against a sacrificial account, or use the no-MFA account for business-logic tests.
- NINO/personal-data fields: server may reject on format first (e.g. `QQ123456C` invalid prefix) — use a definitely-valid pattern (`AB123456C`) before concluding anything about MFA gating.
- MFA-enroll re-renders a fresh secret every page load — read the secret from the page right before generating the code, don't cache across navigations.
- **Log every constructed request URL** in CLI-driven API work. On Windows git-bash an argv like `/v2/company` is rewritten into a drive path, producing a fake host and a `getaddrinfo failed` that looks like DNS — see §4l (`MSYS_NO_PATHCONV=1`).
- A vendor policy that forbids scanners makes the launcher's tool gate **N/A-BLOCKED**, never "passed" — label it that way or the coverage claim is false (§4i).

## Related

- `security-arsenal` — payload banks; `bb-methodology` — 5-phase + validation rules; `hunt-race-condition`, `hunt-business-logic`, `hunt-oauth` — class checklists.
- `references/quarterwise-co-uk-2026.md` — concrete numbers and evidence from this engagement (lockout counters, duplicate-race export rows, false-positive debunks, endpoint map).
- `references/quarterwise-pro-api-2026-09.md` — Pro/REST-API phase: the invariant-vs-write-path matrix (add/edit/delete/import/API), the three-reading impact proof, the co-owner-vs-view-only-adviser cross-account chain, AI receipt-scan prompt injection, pagination/idempotency/key-lifecycle results, and the rate-limit/Cloudflare nuance.
- `references/atmail-email-saas-2026-09.md` — email-SaaS program reference: hostile "pre-declared Informative" policy classes, the cross-component control comparison that upgraded a rate-limit finding, the 8-row false-positive kill table, S3/takeover claim gates, signup-BFF state-machine results, sqlmap/dirsearch/gobuster invocation pitfalls, and OTP-deliverability handling.
- `references/freeagent-accounting-saas-2026-10.md` — accounting-SaaS program that **forbids
  scanners** (how 0D becomes N/A-BLOCKED, and what to deliver instead): the own-two-tenant BOLA
  matrix, the permission-filtered-200 false positive, the period-lock draft-vs-ledger triage,
  authenticated `redirect_uri` testing at the real decision point, invite-token binding proof,
  email-OTP login rig + API-token/refresh mechanics, and the MSYS `/path` argument trap.