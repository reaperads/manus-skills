---
name: disposable-auth-identity
description: Use when a test needs disposable accounts for IDOR proof.
version: 1.0.0
author: Hermes
license: MIT
metadata:
  hermes:
    tags: [security, bug-bounty, idor, authz, cdp, keycloak, mail-tm]
    related_skills: [security:bug-bounty, security:exploit-cookbook, security:security-recon]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Disposable Authenticated Identity (Test-Account Bootstrap)

Many high-value bug-bounty surfaces (IDOR, cross-tenant data access, API-key scoping,
business logic) are gated behind login. The decisive proof requires **real, independent,
disposable accounts** - not theoretical reasoning. This skill bootstraps that:
disposable email + CDP-driven browser signup + activation + session capture +
2-account cross-tenant verification.

## Cheap second identity: the invite flow, not a second signup (verified 2026-09)

If the target lets an existing account **invite members**, that is the cheapest second identity —
it usually skips the public signup gauntlet (email verification, SMS, captcha on the form).

1. Sign up ONE real owner account (the expensive path — do it once).
2. Owner → Settings → Team members → **invite `you+tag@yourdomain`** (plus-addressing delivers to the
   same inbox; note the invitee *name* is also a user-controlled field — see `hunt-html-injection`
   for why that matters).
3. Read the invite from the inbox, decode ESP click-tracking wrappers (Mandrill:
   `mandrillapp.com/track/click/<id>/<href>?p=<b64>` → base64url-decode `p` → JSON → `p.url` is the
   real `dashboard.example/invite/<128-hex>` URL).
4. Open the invite link, set a password. **The phone step can be bypassed**: pick
   *"Use authenticator app"*, which calls `POST …/generate-authenticator-app-uri` and returns the TOTP
   secret in `data.config_uri` (`otpauth://…&secret=<BASE32>`). Capture the **full** response body —
   the same endpoint refuses to regenerate (`…USER_ALREADY_HAVE_AUTHENTICATOR_APP_URI`), so a
   truncated capture leaves you without the secret. In practice the invited session also comes up
   already authenticated, so no OTP is needed for the first tests.
5. A phone number already bound to another account is rejected (`INVALID_PHONE`, sometimes only
   visible in `localStorage.error_requests`) — another reason to prefer the invite+authenticator path.
6. **Invite links expire fast** (~30–45 min observed). Open promptly; re-send via
   `POST …/users/invitation {email}` if it lapses.

**Prove the privilege delta, don't assume it.** Log in as the low-privileged identity with its own
browser profile/port and replay the *same* endpoint list you ran as the owner, then diff statuses:
`…_UNAUTHORIZED_ACTION` / 401 = correctly gated; 200 = reachable. Repeat after any role change.
Remember partial leaks are still findings-worth-checking: a read-only member may be denied the key
*secret* while still being served the org's *access key* (`/organization/api-keys/access-key`) —
evaluate that on impact, not on the endpoint's name.

**Cleanup (do it, and record it).** Delete throwaway members with the same API the UI uses
(`DELETE /users/user {email}`), keep at most the one low-privileged identity you still need for later
tests, and write down which identity was kept and with what password/TOTP secret.

## When to use
- Target's valuable endpoints all return 401/403 unauthenticated and you must PROVE or disprove an authz flaw with a second real identity.
- Signup is behind a bot check (Cloudflare) that you must pass and drive.
- You must prove cross-tenant IDOR (account A cannot read/modify account B's data) - needs two independent accounts.

## Quick start
- A ready-to-run CDP driver that encodes ALL the pitfalls below (launch/goto/fill/click/eval/cookies/logout):
  `scripts/cdp_driver.py` - run `python scripts/cdp_driver.py launch` first, then
  `goto`, `fill`, `click`, `cookies <jar>`, `logout`. Prefer it over hand-typed CDP.
- Cross-tenant server-action testing on Next.js App Router targets (change-share, delete,
  invite actions): see `references/nextjs-server-action-replay.md` — three DIFFERENT wire
  formats exist (`$ACTION_REF_N` form, `$ACTION_ID_<hash>` form, and client-fetch `$K1`/JSON);
  using the wrong one returns the SPA shell and looks like a 404 verdict. The reference now
  leads with the decisive own-render id-swap method, which beats victim-capture replay.
- Full verified-negative VDP audit cookbook (scope gate from security.txt, per-tool
  coverage map to answer "did you use all tools?", OTP probing within policy, Chrome CDP
  session re-login, false-positive traps that manufacture findings, the cache-deception probe set,
  the OAuth callback state-binding matrix, and how to declare unreachable zones): see
  `references/verified-negative-vdp-audit.md`.

## Prerequisites
- Chrome installed on the host.
- Python 3 with `websocket-client` (`pip install websocket-client`).
- A temp-mail provider with an anonymous API. **mail.tm** works; **mailinator** is
  paywalled / returns 404 - do NOT rely on it.
- Authorized scope only: create accounts solely on in-scope, authorized targets.

## Step 0 - Disposable inbox (mail.tm)
```
POST https://api.mail.tm/accounts  {"address":"<user>@<domain>","password":"<pw>"}     # 201
POST https://api.mail.tm/token      {"address":"<user>@<domain>","password":"<pw>","grant_type":"password"}  # -> .token
GET  https://api.mail.tm/domains                                                                               # list usable domains
GET  https://api.mail.tm/messages   (Authorization: Bearer <token>)                                            # list mail
GET  https://api.mail.tm/messages/<id> (Authorization: Bearer <token>)                                         # full mail (text/html)
```
- `address` is required. Use a fresh random user each time.
- `html` may be a string OR a list - join defensively before regex.

## Step 1 - Launch a CDP Chrome (make it persist)
```
chrome --remote-debugging-port=9222 --remote-allow-origins=* \
  --user-data-dir="<tmp>/chrome_cdp_audit" --no-first-run --no-default-browser-check about:blank
```
- Launch with `terminal background=true`. A foreground launch with a short timeout KILLS Chrome.
- Readiness check: `curl -s http://localhost:9222/json/version`.
- Chrome >= ~117: creating a new tab is `PUT /json/new?<url>` (GET returns 405).

## Step 2 - Drive the page over CDP
- Open a websocket to the page's `webSocketDebuggerUrl` (from `/json/list`).
- Use `Runtime.evaluate` with `returnByValue=True`; read `result.result.value`.
- **Selector escaping:** pass CSS selectors as JSON strings INSIDE the JS (`JSON.stringify`).
  NEVER interpolate them through Python `%s`/f-strings - `input[name=email]` and `#id`
  get mangled by Python escaping.
- **Set a React-controlled input's value:**
```js
const el = document.querySelector('#password');
Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set.call(el, 'val');
el.dispatchEvent(new Event('input',{bubbles:true}));
el.dispatchEvent(new Event('change',{bubbles:true}));
```
- **Bot check:** after `Page.navigate`, poll `location.href` for 10-20s; a Cloudflare
  challenge auto-resolves and the URL changes to the real app/signup. Detect the change.
- **Button re-rendering:** React can re-render (button briefly vanishes). Locate the button
  by matching leaf `<span>`/`<button>` text, climb to the `<button>` ancestor, then either
  `.click()` or a real `Input.dispatchMouseEvent` at its `getBoundingClientRect()` center.
  Prefer real mouse events for forms that reject synthetic clicks.
- **Single CDP id counter:** keep ONE incrementing `id` shared across all commands and use it
  as the correlation id. Two separate counters cause `Network.enable`/`Runtime.evaluate`
  responses to collide.

## Step 3 - Complete signup + activate
1. Navigate to the target `/signup` (or the provider's registration URL).
2. Identify the captcha flavour — do NOT blanket-STOP. **Cloudflare Turnstile**
   (`cf-turnstile`, hidden `input[name=cf-turnstile-response]`) is not a stop-sign: a clean
   Camoufox/CDP fingerprint **auto-solves it with zero interaction** (verified end-to-end
   2026-10 on a Synology Account signup — token auto-filled to 666 chars, account created, no
   solver written). Just tick any required consent checkbox and submit; confirm via
   `document.querySelector('input[name=cf-turnstile-response]').value.length` (≈600+ = solved)
   and the `.cf-turnstile` widget being gone from the DOM. Build NO Tab/Space/coordinate logic
   for it. **reCAPTCHA v2 INVISIBLE is the same story — do not treat it as a stop case.** If the
   anchor iframe src contains `size=invisible` (and the widget carries a `data-callback`, e.g.
   `onRecaptchaSubmit`), there is no checkbox and no image grid: fill the form, click SUBMIT, and a
   clean Camoufox/CDP fingerprint passes silently (verified 2026-10 on the CH Media Keycloak
   registration — Tab/Space and coordinate-clicks all no-op'd because no box exists; a plain submit
   created the account first try). Read the type with
   `document.querySelector("iframe[src*=api2/anchor]").src` before writing any solver. Only **visible**
   reCAPTCHA-v2 image challenges
   and **reCAPTCHA-Enterprise** escalations
   (query `g-recaptcha`, `h-captcha`, iframes matching `recaptcha|arkose|hcaptcha`) are the
   STOP / hand-to-human case.
3. Fill email + password (strong - many Keycloak realms reject short/weak; use 16-20 chars,
   upper+lower+digit+symbol).
4. Click Continue/Submit; confirm you land on an "email verification" step.
5. Poll the inbox for the verification mail; regex out the activation link.
6. `Page.navigate` to the activation link; the app should land on the dashboard.

## Step 4 - Capture the session for curl
- `Storage.getCookies` -> all cookies.
- Write a **Netscape cookie jar** so `curl -b jar` works:
```
# Netscape HTTP Cookie File
<domain>\tTRUE|FALSE\t<path>\tTRUE|FALSE\t<expiry>\t<name>\t<value>
```
- Save user id / org id / api-key / connection string from self endpoints
  (`/users/me`, `/users/me/memberships`).
- **⚠️ Modern sessions ROTATE — refresh the jar from the LIVE state before every curl phase.**
  A Next.js/App-Router app re-issues its session cookie on login, and every Playwright run that
  loads the state and navigates writes the NEW cookie back. A jar you wrote 20 minutes ago is
  stale and every request silently returns `307 → /login`. Symptom that looks like a security
  result but is not: `A=307` where you expected `200` on your own resource, or a "race" whose POSTs
  all return `303` and leave you logged out. Always re-export right before the curl battery:
  ```python
  # storage_state.json -> Netscape jar, cookie by cookie (domain, flag, path, secure, expiry, name, value)
  # then sanity-check ONE authed request (expect 200, not 307) before trusting any matrix row.
  ```
- **Capture request bodies with the browser's own network events, not a JS monkey-patch.**
  `pg.on("request", h)` then `req.post_data` gets FormData/multipart bodies verbatim (incl.
  `_1_`-prefixed fields and the trailing `0=[{},$K1]` marker) — safer than a `fetch` init-script,
  which can silently fail to install and misses native form POSTs. Replay with `ctx.request.post`,
  which shares the same cookie jar.

## Step 4b - When you CANNOT export the cookie jar (HttpOnly session, no persisted profile)

Not every browser backend lets you walk away with the session. A Camofox REST session gives you a
logged-in tab but no jar: the login cookie is `HttpOnly` (so absent from `document.cookie`) and the
per-user `storage-state.json` is only written later in the session's life, so a session you just
created has no exported cookies at all. Do not spend the engagement mining `cookies.sqlite`.

Instead, **issue the authenticated requests from inside the page** — they are credentialed by the
browser itself:

```
POST /tabs/{tabId}/evaluate  {"userId":"<u>","expression":"<async IIFE that fetch()es>","awaitPromise":true}
```

- `fetch(url, {credentials:'include'})` replaces the jar for every probe (GET, POST with `FormData`).
- CSRF comes from the live DOM: `document.querySelector('meta[name=csrf-token]').content`.
- Forms come from the real page: `new FormData(document.querySelector('form#id'))`, then `fd.set(k,v)`
  to override one field. Other pages' forms can be enumerated offline with
  `new DOMParser().parseFromString(await (await fetch(u,{credentials:'include'})).text(),'text/html')`.
- Always wrap the expression in try/catch — a throw returns `result: null` and tells you nothing.

Full recipe plus the two traps that cost the most time (a client-validated submit button stays
`disabled` until you dispatch `input`/`change`; "same page came back" is not a success signal) live
in the **`camoufox`** skill, section *"When you CANNOT export the session: drive everything from
inside the tab"*. Scanners that need a jar (sqlmap/dalfox/nuclei with `--cookie`) simply stay
unauthenticated in this mode — say so in the coverage table rather than implying they ran authed.

## Step 5 - Second account + cross-tenant IDOR

⛔ **Two accounts must not share a browser CONTEXT — a second tab is not enough.**
A single Chrome *context* shares ONE cookie jar across every tab If you open account B in a second tab of the
same browser, `document.cookie` / fetch will carry account A's `qw_session` (or
Keycloak SSO cookie) and B's "second login" silently reuses A's session → your entire
cross-tenant matrix is testing A vs A and proves nothing. Launch a SECOND Chrome with a
different `--user-data-dir` AND different `--remote-debugging-port`:
```
cmd.exe /c start chrome --remote-debugging-port=9223 --remote-allow-origins=* \
  --user-data-dir="C:\Users\me\chrome_cdp_B" --no-first-run about:blank   # account B
# (account A already on 9222 / its own user-data-dir)
```

**Simpler equivalent that avoids a second browser entirely (Playwright):** one browser, TWO
contexts — each context has its own cookie jar, which is all you need.

```python
br  = pw.chromium.launch(headless=True)
ctxA, ctxB = br.new_context(), br.new_context()      # isolated jars
# seed each from its own storage_state; after login, ASSERT the session cookies differ
# before running any cross-tenant matrix:
assert ckA.get("qw_session") != ckB.get("qw_session"), "A vs A — matrix proves nothing"
ctx1.storage_state(path="stateA.json"); ctx2.storage_state(path="stateB.json")   # persist BOTH
```
Two bonus uses: (1) it is the clean way to prove **session revocation** — "sign out on other
devices" in A, then B's next navigation must land on `/login`; (2) `ctx.request` inherits the
context's jar, so authed API probes need no curl at all.

⛔ **Do NOT start two Playwright sync instances in one process.** `sync_playwright().start()`
twice raises *"It looks like you are using Playwright Sync API inside the asyncio loop."* Use one
browser + N contexts (above), or separate OS processes.
Drive each via an env switch (e.g. `CDP_PORT`/`CDP_TAB`) in your CDP driver. Verify
isolation before trusting any cross-tenant result:
```js
// In B's tab, the target's session cookie must be DIFFERENT from A's:
document.cookie   // and Storage.getCookies() on port 9223 must show a distinct qw_session
```
Then:
1. Log out cleanly: `Page.navigate` to the realm/app logout AND `Network.clearBrowserCookies`.
2. Repeat steps 2-4 for a second disposable account.
3. Run cross-tenant checks **with account B's jar against account A's resource ids**
   (projects, orgs, api_keys, connections, billing, guests).
   - `404 "project not found"` / `404 "not an organization member"` / 405 = proper authz (no vuln).
   - `200` returning A's data while B is authenticated = cross-tenant IDOR (confirmed -> report).
   - "Param ignored, returns caller's own data" (safe) vs "returns other party's data" (vuln):
     ALWAYS prove by creating a real object in A, then checking B cannot see it. A list-scope
     endpoint returning `[]` for both your org and a foreign org is NOT an IDOR on its own.

## Pitfalls
- **Playwright sync API: two `sync_playwright().start()` calls in ONE process collide** with
  `It looks like you are using Playwright Sync API inside the asyncio loop`. Do not spawn a
  second driver — for a two-identity test run ONE `sync_playwright()` + ONE browser + TWO
  `browser.new_context()` objects. Each context carries its own cookie jar, which is exactly
  the isolation you need, and it is cheaper than a second Chrome. Assert the two session
  cookie values differ before running the cross-tenant matrix. A second `--user-data-dir` +
  `--remote-debugging-port` (two processes) is still the right call when you need genuinely
  separate OS profiles (installed extensions, SSO state).
- **Re-export the cookie jar immediately before each authed curl run, and assert a logged-in
  marker.** On targets that rotate the session cookie per login, a stale jar makes requests
  return `307 -> /login` with no error; a regex expecting page content then returns "0 results",
  which reads as a finding. Cheap guard: assert `"Log out"` / `"Welcome,"` in the body (or
  `/app != 307`) before trusting anything, and re-login when it fails. Symptom of skipping
  this: a race/replay test reporting "0 resources" or "not logged in" mid-campaign.
- **`window.__drain` / hook helpers must live OUTSIDE the idempotency guard.** If the init
  script is `if (window.__nHooked) return; ... window.__drain = ...`, a re-injected script
  returns early and `__drain` is undefined on that document (`TypeError: window.__drain is not
  a function`). Define the hook and keep the drain inline (`() => { const a = window.__n || [];
  window.__n = []; return a; }`) instead of relying on a stored helper.
- Foreground Chrome launch = dead Chrome. Always `background=true`.
- `PUT` vs `GET` for `/json/new` (405 on newer Chrome).
- Python selector escaping corrupts `[]`, `#`, quotes -> `JSON.stringify` in JS.
- mailinator is dead (404/paywalled). Use mail.tm.
- **mail.tm account creation is per-IP rate limited.** `POST /accounts` can answer `429` with an
  empty body; retry the SAME address with ~20 s backoff (up to ~8 tries) instead of minting a new
  address each attempt. Separately, `POST /token` immediately after a successful create can return
  401 `Invalid credentials` before the record is readable — loop the token call a few times with a
  short sleep before concluding the inbox is dead. Only one active domain is normal
  (`hydra:member[0].domain`), so don't treat a single-entry domain list as a failure.
- **When the SECOND mailbox is genuinely dead, fall back to plus-addressing on a mailbox you already
  control.** Observed 2026-10: `POST /accounts` returned OK for a second address but `POST /token`
  answered 401 on every retry for ~100 s (5 attempts, 20 s apart) — mail.tm throttles a second account
  per IP even when creation reports success, so the backoff loop above never clears. Don't burn the
  session on it. Use an alias on the operator's own inbox — `user+tag@domain` still delivers to
  `user@domain` — and read the verification mail via the Gmail API:
  ```
  # refresh google_token.json -> access_token, then:
  GET /gmail/v1/users/me/messages?q=to:user+tag@domain%20subject:(Benutzerkonto)%20newer_than:1h
  GET /gmail/v1/users/me/messages/<id>?format=full     # walk payload.parts, base64url-decode body
  ```
  Regex the activation link out of the decoded body (`.replace('&amp;','&')` first — Keycloak escapes
  it). That gives two real identities off ONE inbox with no second provider. The two accounts must still
  use separate cookie jars (Camofox `userId`, or two `BrowserContext`s) or the cross-tenant matrix is A
  vs A. Note which alias was used, so the identity stays traceable during cleanup.
- **Playwright alternative to two Chrome profiles: one browser, two `BrowserContext`s.** Each
  context owns its own cookie jar, so `browser.new_context()` ×2 gives two genuinely independent
  sessions with no port juggling or `--user-data-dir` bookkeeping. Do NOT call
  `sync_playwright().start()` twice in one process — the second sync instance raises
  `It looks like you are using Playwright Sync API inside the asyncio loop`. Start Playwright once,
  launch once, then `new_context()` per identity, and assert the two `context.cookies()` sets
  actually differ before trusting any cross-tenant result.
- SSO cookies outlive app logout -> clear browser cookies + hit realm logout.
- **SSO account ≠ app session: START the OIDC flow from the APP, not from Keycloak.** Registering or
  verifying an email directly on the realm sets the *realm* SSO cookie, but the app's OIDC callback
  (`/auth/redirected`) also needs its OWN `state` bound to an app-side session. Navigate straight at the
  realm registration / confirm link and let Keycloak bounce back to the app and you get
  `500 "request to the redirect_uri path but there's no session state found"` — that is NOT a bug and NOT
  a failed signup, it means the flow did not originate at the app. Enter via `https://<app>/auth/login`
  so the app seeds the state first; the realm SSO cookie then carries the login through. Sequence that
  worked on sunshine.ch/CH Media: app `/auth/login` → realm register → submit → `VERIFY_EMAIL`
  required-action → read confirm link from mail.tm → open it (verifies the account) → re-enter
  `https://<app>/auth/login` → lands logged in.
- **Registering on a shared IdP may be a scope step — flag it before you do it.** A realm shared across
  many brands (CH Media realm "ET" serves ~16 radio/TV clients) means one account lives on the provider's
  central IdP, not just the target host. When the operator has said third-party scope is "brief, not
  allow-all", surface that and get a go-ahead before creating the identity.
- Weak password rejected by Keycloak -> strong password.
- Synthetic clicks may be ignored on validated forms -> real mouse events.
- **A 200 is not proof you are logged in — check a body marker.** With a following-redirect
  client, an expired session yields `307 → /login → 200` with the login page body. A test that
  counts resources or properties after that reads "0 resources" and looks like a successful
  deletion / cap. Verify with a rendered marker (`Log out` / `Welcome, <name>`) in the body, and
  when reading a matrix of status codes pass `allow_redirects=False` so you see the real 3xx.
- **Session cookies rotate on login and periodically — jars go stale mid-run.** Refresh the curl
  jar from the storage_state file immediately before each batch, and do
  **login → attack → verify inside one process/context** for anything mutating. A stale jar
  mid-run produces fake "the cap let 2 through" and fake "the entry was deleted" results.
- **Replay that returns `500 {"digest":"..."}` after the same request worked in the browser is
  per-render binding, not a finding.** Some Next.js route actions are bound to a specific page
  render; replaying the captured POST later is rejected with an opaque digest. That is
  *inconclusive* — it proves the replay failed, not that the authorization held. Re-capture with
  fresh headers, or fall back to the decisive test: drive the victim's own form, swap the
  object id, and read back the state. Never report a digest error as either a pass or a bug.
- **`request_id` in every error makes naive `"id" in body` checks false-positive** -> assert on
  concrete fields (`project.id`, `key.id`) and the ABSENCE of `request_id`.
- **Two accounts in ONE browser = A vs A.** One Chrome process = one cookie jar = one
  session. A new tab "logging in as B" silently inherits A's session cookie. Always use a
  second `--user-data-dir` + second `--remote-debugging-port` for the second identity and
  verify the two session cookies differ before running the cross-tenant matrix.
- **Email-code signup has a short pending-token TTL.** On many stacks (e.g. Next.js
  app-router signups) the "we sent a 6-digit code" step expires in ~60s: enter the code
  promptly, and re-request a fresh code (button cooldown ~45-60s) rather than re-navigating
  to /signup (which drops the pending token and forces a new email). The code itself stays
  valid for the pending token's lifetime even after the resend cooldown expires.
- **6-digit codes are rate-limited globally** (a "global_cap" / codeLimit throttle).
  Budget: one fresh code per identity; don't spam resend or you lock the shared pool.
- **OTP rate-limit counter leaks in the redirect URL — use it as free evidence.** After a
  few wrong-code submits on a Next.js reset flow, the app 302s to
  `/reset?codeLimit=12&why=cooldown` — the URL itself proves the attempt budget (12) and
  reason (cooldown). Check the browser `location.href` after each failed OTP attempt: the
  counter may be exposed without you needing to brute-force to find it. This turns "is
  there a rate limit?" into a one-request answer and gives you hard evidence that the
  control exists (useful for a verified-negative report). Do NOT keep testing wrong codes
  until lockout — that is volume testing against VDP policy.
- **CDP `Input.dispatchMouseEvent` needs `type=` in params**: method is
  `Input.dispatchMouseEvent`, and `type` ("mousePressed"/"mouseReleased"/"mouseMoved") goes
  INSIDE params, not as an argument. Passing two positional args to your send() helper is a
  recurring error; keep one `csend(method, **params)` helper.
- **Cookie banners hijack submits**: after navigating to /login on a fresh profile, a
  "Accept analytics cookies" row can be the visible submit path — the login POST silently
  no-ops and you stay on /login with no error. Click Accept (or Decline) BEFORE submitting
  the login form, and read `document.body.innerText` after each submit to catch the trap.
- **A multi-step signup that answers with JSON field errors is handing you its API contract.**
  Posting the wrong step of a 3-step wizard returns e.g.
  `{"errors":{"username":"Required.","password":"Required.","password_confirm":"Required."}}` —
  read the required field list straight out of the response instead of guessing the endpoint shape,
  then re-post with the correct step's fields. Supplying a value for a field the current step does
  not accept is silently ignored, so the error list is the only reliable map.
- **Probe anti-automation enforcement instead of assuming it — replay a step with an EMPTY captcha token.**
  A reCAPTCHA-Enterprise signup (2026-09) accepted a direct POST of step 1 with
  `g-recaptcha-response` left empty: the API replied with per-field validation errors
  (`{"errors":{…}}`), never a captcha rejection, so the token was not strictly enforced on that
  endpoint (the widget loaded with `tokenLen: 0` and the step still advanced). Record it as an
  anti-automation *observation*, not a paid finding — it is Low/Info at best, and
  "brute force"/automation classes are out of policy on many programs. Do **not** generalise
  "the captcha is broken" from one endpoint; a sibling endpoint may verify it properly.
- **A code-gated step can still be walked past the widget.** If the flow advances to "enter the
  verification code" without you solving the captcha, the mailbox is the only remaining gate —
  poll it (mail.tm `GET /messages` with the Bearer token) and regex the 6-digit code out of
  `html`/`text`; that is the whole bypass, and it is worth knowing before you abandon a signup.
- **Record real passwords at signup, not "in-head" values.** A multi-account session tends
  to reuse the wrong account's password across fills. Write each identity's actual password
  into a creds file the moment it's typed, and re-read it for every subsequent login.
- **Share/invite tokens are email-bound (Next.js VDP targets)**: opening an
  `/app/shares/accept?token=...` link under a different logged-in account shows
  "this invite was sent to X, log in with the invited email" and blocks the accept.
  Verify this with a third disposable account whenever the share flow is in scope —
  a non-bound token is a reportable share-grab chain.
- **Next.js server-action cross-tenant replay**: to test whether account B can invoke an
  owner action (change share %, delete, invite), capture the action's wire format by
  hooking `window.fetch` on the OWNER's tab (headers carry `next-action: <id>` and
  `next-router-state-tree: <tree>`; body is urlencoded with `_1_`-prefixed field names and a
  `_1_$ACTION_KEY` that ROTATES per page render — fetch it fresh, don't reuse stale keys).
  Replay the identical POST with the VICTIM's jar; a `404 not found` / no-op where the owner's
  own call succeeds = action is ownership-scoped. Manual reconstruction without the exact
  `_1_` prefix + current `$ACTION_KEY` returns 404 even for the legitimate owner, so always
  capture the real browser POST first. See `references/nextjs-server-action-replay.md`.
- **Invited co-owner write access is BY DESIGN on shared books** (e.g. Quarterwise property
  sharing): a co-owner can read/export the full shared books and add entries — that is the
  feature. What is NOT allowed: invoking owner-only actions (share update/invite/delete)
  cross-tenant. Don't report co-owner read access as an IDOR; report only the action-scope
  bypass if the owner-only actions succeed under the co-owner's jar.
- **Viewer vs contributor role — same propertyId-swap test, different expected denial.**
  Adviser flows (e.g. Quarterwise `/app/account/advisers` invite → accept → clients
  dashboard) grant a VIEWER who can read/CSV-export the client's books but has NO write
  buttons in the UI. To prove the write block is server-side (not just hidden UI): viewer
  opens its OWN property's "Record income" form, swaps the hidden `propertyId` to the
  shared client property, submits → expect **404 "That property could not be found."** =
  write actions are scoped to WRITE-permitted properties, authz verified. Also test invite
  token binding with a THIRD disposable account: opening the accept link while logged in as
  a different user renders "This invitation was sent to <masked>, sign in with the invited
  address" — a non-bound token would be a share-grab finding. The accept page's hidden
  `accessId` (server-issued) has no direct update/remove endpoint (404s) — do not chase it.
- **Hidden record ids leak through the EDIT control.** When the target hides the dangerous
  button from the attacker's role (adviser/viewer sees no "Delete" on someone else's row) you
  still need the victim's record id to run the decisive swap. Open the *Edit* form for that
  row: it ships the id in a hidden input (`input[name=txnId]`, `entryId`, `accessId`). Click
  Edit on each row and read `[...document.querySelectorAll('input[name=txnId]')].map(i=>i.value)`
  to map id → row label. Not a bug on its own — it is the input to the authz test.
- **Submit the form that CONTAINS your field, never `form button[type=submit]`.** On these
  apps the FIRST form in the DOM is a hidden no-arg action form (usually "Log out"). A generic
  `pg.locator("form button[type=submit]")` click silently logs you out and bounces you to `/`,
  which reads like a failed test. Always `el.closest('form')` → its own submit button, or use a
  `submitform` helper keyed on a field selector you know exists.
- **React-controlled hidden inputs revert between set and submit.** `input.value = X` on a
  hidden field bound to component state gets re-rendered back to the original value before the
  request fires (0 network requests, no error). Use the native setter +
  `dispatchEvent(new Event('input',{bubbles:true}))`; if it STILL reverts, the guard is real
  client state and you should fall back to the own-render-swap replay instead of fighting it.
- **Parameter-pollution test without hand-building requests.** To check first-vs-last parsing
  in an action (`get()` vs `getAll()`), append a duplicate hidden input to the live form from
  the page console and submit normally — the browser serialises both. Malformed hand-built
  multipart bodies return 500 that is indistinguishable from a rejected swap, so verify the
  control (own id → 200 + visible change) in the same run before reading anything into a 500.


- **Full server-action body needs `Network.getRequestPostData`, not the event's `postData`.**
  `Network.requestWillBeSent` truncates/omits multipart bodies. Collect the `requestId`,
  then after submit call `Network.getRequestPostData {requestId}` and write the returned
  `postData` verbatim to a file for curl `--data-binary @file` replay. Never reconstruct the
  multipart from visible fields — `_1_`-prefixes and the trailing `0=[{},$K1]` marker are easy
  to get wrong and yield 404/500 on an otherwise-valid action.
- **Cross-tenant server-action replay matrix — only ONE of three outcomes is a finding.**
  (a) Replay account A's captured POST verbatim with account B's jar → **500**
  (action id + `$ACTION_KEY` are bound to A's page render; inconclusive, do not report).
  (b) DECISIVE TEST: account B opens its OWN form and swaps the hidden object id
  (e.g. `propertyId`) to account A's uuid → **404 "That property could not be found." /
  "We can't find that page" / "Only the owner can change these settings."** =
  data-layer authz enforced → document as "authz verified" with the denial string.
  (c) Same as (b) but the write SUCCEEDS on A's object → **BOLA, report immediately.**
  Always run (b); it defeats the per-render action-key binding that makes (a) useless.
- **Long multi-line `js()` expressions on heavy SPA pages time out** (5s Runtime.evaluate
  budget in the browser harness). Hoist a one-line helper into the page once
  (`window.__qprobe = async u => { const r = await fetch(u,{credentials:'include'}); ... }`)
  then call it with tiny expressions. The Python-websocket CDP driver
  (`scripts/cdp_driver.py`) is the more robust path for multi-step flows.
- **Role/field tampering on real forms beats page-swap IDOR on hardened targets.** Open a
  legit invite/share/settings form, mutate a hidden or radio field to a privileged value
  (`role=owner|admin`, `sharePercent=101|−10|0`, `sharePercent=60` when only 50% remains),
  submit, READ BACK the resulting server state. Server-side enum validation shows the old
  label unchanged ("CAN VIEW") → control works. State that CHANGED → mass-assignment finding.
  A radio re-render is the proof, not the submit status.
- **Secondary-role escalation (invite→accept→capability matrix).** After account B accepts a
  real co-owner/contributor invite from account A, test what B can do against A's objects:
  rename, delete, change OWNER's share, invite more co-owners, remove owner. Co-owner WRITE
  on shared books (record income/expense, view full books, CSV export) is BY DESIGN — report
  only the owner-ONLY actions succeeding under B's jar. UI hiding controls ("Only the owner
  can change settings") is not proof: capture the owner's action POST and replay it with B's
  cookie, then re-read the object.
- **CSRF on Next.js server actions = same-session evil-Origin replay.** Cross-session replay
  (A's captured POST + B's jar) returns 500 "Server action not found" — that tests authz, not
  CSRF, and is inconclusive. Correct test: replay the legit POST with the SAME session cookie
  but `Origin: https://evil.example.com` + evil Referer → 500 digest error + verify via export
  JSON that only ONE object was created = Origin/CSRF check enforced. Two objects = CSRF.
- **Pro/feature-gate bypass.** Free-plan session hitting a Pro-gated endpoint directly
  (AI receipt scan, document store, API key mgmt) → 403 "Pro feature" = plan check works;
  200/201 = gate is UI-only (reportable priv-esc on tiered SaaS).
- **Export endpoints are double surface (IDOR + injection).** On SaaS with xlsx/pdf/csv
  exports, test (a) other-role access → 404 = scoped, and (b) formula injection: set a field
  to `=SUM(A1:C1)` / `=2+2`, export, then verify the file internals — XLSX sharedStrings
  (`<si><t>=SUM..</t></si>` without `<f>`) and CSV `'`-prefix are correct mitigations; raw
  formula in a data cell or CSV cell without prefix is CSV-injection.
- **⛔ DO THIS FIRST: check the mitigation before you call formula injection a finding.** This
  class is the single easiest way to burn a session on an over-claim. Raw text in an export is
  NOT execution. Two checks, both decisive, both cheap:
  1. **XLSX — cell type decides, not the bytes.** `grep -c '<f[ >]' sheet1.xml` → **0 `<f>`
     elements means NO formula cell exists anywhere in the file**. A `=2+2` sitting in
     `<si><t>=2+2</t></si>` referenced by a cell typed `t="s"` (shared string) is *text*; Excel
     does not evaluate it. Cell shape to look for: `<c r="D6" t="s"><v>11</v></c>` = inert.
  2. **CSV — test the guard for the WHOLE dangerous set, and parse it properly.** A guard that
     only handles `=` is incomplete; `+ - @ TAB CR` also trigger evaluation.
     ```
     =1+1 → '=1+1      +1+1 → '+1+1      -1+1 → '-1+1      @SUM(1) → '@SUM(1)
     <TAB>=1+1 → '=1+1   <CR>=1+1 → '=1+1   =cmd|'/C calc'!A0 → '=…   (all guarded = pass)
     ```
     **False-negative trap:** parse with `csv.reader`, never `line.split(',')`. A field needing
     quoting (it contains a comma or a quote) *starts with `"`*, so a naive
     `field.startswith("'")` reports NO GUARD on a correctly-guarded value. Parsed correctly the
     value is `'=HYPERLINK("http://evil.test/x","click")` — apostrophe present, quoting correct.
  **Verdict rule:** mitigation present on every export path = **NOT a finding**. Record it as
  "VERIFIED MITIGATED" and downgrade/withdraw any earlier claim immediately. The residual note
  worth sending a vendor is defence-in-depth only: *the XLSX path stores the raw value without the
  `'` guard, so it is inert only because the cell is text-typed — apply the guard at the data
  layer so both exports inherit it, in case a future change emits formula-typed cells or a
  consumer re-serialises the xlsx to CSV without re-guarding.* Never ship a P4 for an inert value.
- **Adjudicate XLSX injection at the CELL, not the string table.** `<t>=2+2</t>` inside
  `sharedStrings.xml` proves nothing: what matters is the referring cell's `t` attribute in
  `xl/worksheets/sheet*.xml`. `<c r="D6" t="s"><v>11</v></c>` = shared-string cell = Excel
  renders it as literal text, NOT a formula → mitigated, do not report. Only a cell carrying
  an `<f>` child (or a raw `=` with no `t` and no shared-string index) executes. Unzip the
  export and grep BOTH files before claiming CSV/Excel injection.
- **PDF exports: distinguish HTML-rendering from text-only generators with an OOB probe.**
  Set the injectable field to `<img src="http://<interactsh-domain>/x"><iframe src=...>` and
  export. No callback + the payload appearing hex-encoded inside a `Tj` text operator in the
  decompressed content stream (`<3C696D6720737263...>`) = a vector/text PDF writer (pdfkit-style),
  so no HTML injection, no SSRF, no local-file read. A callback would mean the generator
  renders HTML and the whole class reopens. This one probe closes five hypotheses honestly —
  run it before writing "PDF injection" as an open lead.
- **HTTP 500 on a manual urllib replay is NOT proof a password changed.** When testing
  change-password-without-current-password, a 500 from a hand-built multipart means the
  request was malformed, not that the server accepted it. Definitive verification: fresh
  browser (separate Chrome profile / cleared cookies) login with the OLD password → success
  means change rejected = safe; old fails + new succeeds = finding.
- **Login rate-limit probing can lock the account you need for the rest of the test.**
  A 10-20 wrong-password run on the SECOND account (the one with no MFA / the one you keep
  for testing) can lock it for 15 minutes ("Too many attempts. Please wait about 15
  minutes.") and stall every later step. Order your tests so rate-limit probing is LAST,
  or do it on a throwaway account.
- **Lockout probing burns the identity — the CORRECT password is also rejected during the window.**
  Measured on a hardened Next.js SaaS (2026-09): 10 wrong passwords passed with a generic
  email/password-mismatch error, attempt 11 returned a too-many-attempts message quoting a
  15-minute wait, and an immediate login with the *correct* password was refused as well. So
  (a) the control is real and the honest finding is 'no missing rate limit', and (b) run this as
  the very LAST action on a disposable identity — never on the account you still need for
  cross-tenant work. Probe a non-existent email first: it exercises the throttle without touching
  a real account, and the generic error message there also documents anti-enumeration. Same for MFA-OTP probing on your main account: 6 wrong
  codes → 6-minute lockout that blocks re-login mid-audit.
- **MFA enrollment changes the login flow for the rest of the session.** After you
  self-enroll TOTP (see modern-web-framework-attacks §9d) on the account you keep using,
  EVERY subsequent login needs a TOTP code — including automated re-login scripts. Keep
  the secret file handy and generate fresh codes (secrets rotate per enrollment page
  render; the ENROLLED secret stays valid for later logins). If a re-login script only
  fills email+password, it will stall at `/login/mfa`.
- **Account-level OTP lockout persists across fresh sessions — use the two-round probe**
  to distinguish account-level (safe) from per-session (brute-forceable) counters: round 1
  wrong OTPs until blocked; round 2 fresh login → immediately blocked = account-level.
  Numbers that proved safe on one target: login wrong-password 11, login-MFA OTP 6,
  MFA-recovery code 6, all persisting. Full detail:
  `modern-web-framework-attacks` → `../modern-web-framework-attacks/references/otp-lockout-and-duplicate-race.md`.

## Verification
- Both accounts: `/users/me` returns the correct email + distinct `id`s.
- Two distinct cookie jars.
- Cross-tenant matrix executed; you can state, per endpoint, whether B saw A's resources.

## Scope / Safety
- In-scope, authorized targets only. Disposable emails only - never personal.
- Never store plaintext passwords longer than needed; redact them in reports.