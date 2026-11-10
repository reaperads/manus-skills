---
name: hunt-spa-api
description: Discover a single-page-app's hidden backend API from its public JS bundle, then test that API for broken access control / missing authentication. One of the highest-yield web plays in modern recon — SPAs ship their entire backend route map to the browser, and the API behind them is frequently missing the auth middleware the login page implies. Built from an authorized engagement where this play found an unauthenticated financial API that an ASM scan reporting hundreds of "Criticals" completely missed. Use whenever a target serves a JS-heavy SPA (React/Vue/Angular/Next), an "app"/"console"/"dashboard"/"portal" subdomain, or any `*api*` host shows up in recon. Leaked build artifacts (source maps / .env / .git / asset-manifest) are owned by hunt-source-leak; API version-inventory and behavioral diffing by hunt-shadow-api; this skill owns mapping a live SPA's backend routes from its JS bundle and testing them for broken access control / missing auth.
sources: authorized-engagement
report_count: 1
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

## When to use this skill

Trigger when:
- A target host returns a tiny HTML shell + big `/static/js/*.js` or `/_next/static/*` bundles (React/Vue/Angular/Next/Svelte SPA)
- You see a subdomain named `console`, `app`, `dashboard`, `portal`, `admin`, `panel`, `manage`, `internal`
- Recon surfaces any `*api*`, `*-api*`, `api.*` host
- A login page is OAuth/SSO-gated (the *frontend* auth tells you nothing about whether the *API* enforces auth)

The core insight: **a SPA is a client to a backend API, and it ships the full map of that API — hosts, routes, sometimes keys — to anyone who views source.** The login page being protected says nothing about whether the API behind it checks tokens. Auth is frequently enforced on the *gateway/login* and missing on a *route group* of the API.

DO NOT skip this because "the app needs login" — that's exactly when this pays off.

---

## The play (5 steps)

### 1. Pull the shell + enumerate the bundles
```bash
curl -s https://console.target.com/ -o index.html
# React/CRA:
grep -oE '/static/js/[^"]+\.js' index.html
# Next.js:
grep -oE '/_next/static/[^"]+\.js' index.html
# generic:
grep -oiE 'src="[^"]+\.js[^"]*"' index.html
```
Download every bundle (they can be multi-MB — that's fine, it's all route data):
```bash
mkdir bundles
for j in $(grep -oE '/static/js/[^"]+\.js' index.html | sort -u); do
  curl -s "https://console.target.com$j" -o "bundles/$(echo "$j"|tr '/' '_')"
done
```

### 2. Harvest API hosts, routes, and secrets from the bundles
```bash
B=bundles/*.js
# Backend API hosts (incl. dev/beta/staging variants — often weaker auth)
grep -ohiE 'https://[a-z0-9.-]*(api|console|backend|service)[a-z0-9.-]*\.target\.com[a-z0-9/_-]*' $B | sort -u
# Versioned API base paths
grep -ohiE '/api/v[0-9]+/?' $B | sort -u
# Route literals — minified bundles store routes as STRING segments, not full URLs.
# Grep for quoted "resource/action" strings:
grep -ohiE '"[a-z0-9_-]+/[a-z0-9_/-]+"' $B | tr -d '"' \
  | grep -iE '(login|user|account|order|billing|invoice|payment|deal|report|token|otp|password|reset|admin|profile|auth|upload|export|role|permission|dashboard|wallet|finance|sales)' | sort -u
# Secrets (validate before trusting — most AIza keys are Maps/analytics, not Auth)
grep -ohiE '(AIza[0-9A-Za-z_-]{35}|AKIA[0-9A-Z]{16}|sk_live_[0-9A-Za-z]+|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|apiKey["'"'"']?\s*[:=]\s*["'"'"'][^"'"'"']+)' $B | sort -u
```
**Note:** minifiers store routes as concatenated string segments (e.g. `"account/payment/list"`), NOT full `/api/v2/...` URLs — so a naive `/api/v*` grep returns nothing. Grep for the **resource-word route strings** and prepend the base yourself.

**Lazy-loaded (async) chunks — don't stop at HTML-referenced bundles.** CRA/webpack SPAs reference only runtime+main+vendor in index.html; numbered async route chunks are named inside main.js's chunk map and loaded at runtime, so grepping only `/static/js/*.js` from the shell truncates route coverage to eager chunks.
```bash
grep -oE '[0-9]+:"[a-f0-9]+"' bundles/*main*.js        # {chunkId:"hash"} pairs
# reconstruct /static/js/<id>.<hash>.chunk.js, download each, re-run route/host/secret harvest
# asset-manifest.json (if present) lists them all -> hunt-source-leak
```

### 2b. SSR SPAs — the API base is in the HTML shell, not the bundle

React/Next SSR apps frequently inject a **server-built config object** into an inline `<script>` in
the HTML (React-Helmet renders it with `data-rh="true"`). The bundle only references it symbolically
(`window.app.apiHost + window.app.apiPath`), so a bundle-only grep misses the API base entirely.
Grep the shell:
```bash
curl -s https://$TARGET/ -o shell.html
grep -oiE 'window\.app\s*=\s*\{[^}]{0,2000}' shell.html
grep -oiE '(apiHost|apiPath|apiUrl|graphqlUrl|baseUrl|staticBaseUrl)\s*[:=]\s*["'"'"'][^"'"'"']{0,120}' shell.html
```
Field gotchas:
- `apiHost: ""` → same-origin; the client concatenates `apiHost + apiPath`.
- `apiPath` is often a **comma-separated list** of gateways, e.g.
  `/api/pub/gql/<client>,/api/pub/<other>/<client>,/api/auth/gql/<client>` — `pub` = public,
  `auth` = the gated one.
- The advertised path can be **internal-only**. Observed on a live target: `POST /api/pub/gql/<client>`
  → the edge returned a plain **404 from `openresty/1.27.1.2`**, while `/api/auth/gql/<client>`
  reached the backend and answered **401 "unauthorized request"**. The two bodies differ (edge
  default-404 page vs the app's JSON/plaintext) — that difference is how you tell which prefix is
  actually routed to the app. The *public* data gateway on that target was a separate namespace
  (`/__chameleon/*`) that the bundle referenced by relative path. So: test the advertised path; if it
  404s at the edge, hunt the namespace the live SSR/endpoints actually call.
- **APQ shape — a `…/gql/<client>` prefix that 404s on `POST` is often Apollo Automatic Persisted
  Queries exposed as `GET …/gql/<client>/<Operation>/<sha256>?variables=<json>`.** The sha256 hashes
  are unguessable; harvest the `<Op>/<hash>` pairs from **archive URL sets** — the SPA's own historic
  calls are archived (`waymore -i host -mode U -oU wm.txt`, then `grep -oE '/api/pub/gql/[^ ?]+'`).
  It is **hash-locked** (bogus hash → `"PersistedQueryNotFound"`; `&query=` override ignored), so no
  arbitrary queries/introspection — but the GraphQL validation errors leak schema types, valid field
  names and required variable names+types (`Cannot query field "sponsor" on type "INewsArticle"…`,
  `Variable "$cityId" of required type "String!"…`). Full play:
  `references/apollo-apq-persisted-queries.md`.

**The SSR state blob is both a route map and a reflection sink.** The `<script>`-embedded state
(`window.__APOLLO_STATE__`, `__NEXT_DATA__`, `__INITIAL_STATE__`) contains the *exact* GraphQL
operation strings + variables — a map of operations you cannot see in the bundle:
```bash
grep -oE '\$ROOT_QUERY\.[^"]*' shell.html | sort -u   # e.g. page({"path":…,"ressort":…}), search.fulltext.ressorts({…})
```
Two cautions:
- Values you feed in (a path segment, `?q=`) are reflected into this JSON. React serialises it
  **escaped** (`"`→`\"`, `<`→`\u003C`), so scanners that flag "reflected payload in JS" (dalfox
  `[W] Reflected Payload in JS`) throw a **false positive** here. Verify the surrounding bytes before
  writing XSS up — if the value sits inside the `\u003C`-escaped JSON string, it is inert.
- The state is a static artefact of one server render; grep it, don't drive a browser for it.

### 2c. Next.js — three one-shot artefacts that hand you the entire map

On a Next.js target these three requests front-load the whole attack surface before any scanner fires
(verified on a crypto-exchange estate, 2026-10):

- **`/gen-cfg.js`** (or `/config.js`, `/env.js`) — a server-rendered config object:
  `window.<App>FeConfig = { BASE_URL, AUTH_DOMAIN, EXCHANGE_PUBLIC_API_URL, RECAPTCHA_SITEKEY, … }`.
  One request names the estate's entry points (app, IdP, public API) plus the captcha sitekey.
- **`_next/static/chunks/pages/_app-<hash>.js`** — the BFF route map, whole in one grep. The routes are
  stored as `name:function(){return"/api/..."}`:
  ```bash
  grep -oE '[a-zA-Z0-9_]+:function\(\)\{return"/[a-zA-Z0-9/_.?$-]*"' app.js
  ```
  Yields every backend path (`/api/fe/profile`, `/api/fe/…/calculate`, sibling product namespaces
  like `/crypto-loans/api/…`) — including paths the UI never links.
- **IdP host `/.well-known/openid-configuration` + `/.well-known/jwks.json`** — endpoints, grant
  types, `code_challenge_methods_supported`, signing alg, `id_token_signing_alg_values_supported`.
  Zero guessing for the OAuth surface. (A standalone `/oauth/token` answering
  `{"error":"invalid_client"}` on `client_credentials`/`authorization_code` = confidential client,
  correctly authenticated.)

Two extras worth one request each:
- **Legacy surface** — probe `?wsdl` on API paths (`/api/oauth2?wsdl`). Uncovered a public SOAP
  service (`OAuth2ServiceService`, ns `…spectrofinance.lt`) that no web2 scanner touches — its own
  XXE / operation-enumeration pass, not a template hit.
- **Backend fingerprint from the error envelope** — `{errorCode,category,key,defaultMessage,spanId,traceId}`
  = Spring; a `403 invalid_csrf_token` proves CSRF is enforced, so a "no CSRF" claim needs a token-less
  POST against a real route, not an assumption.
- **`X-Matched-Path` hands you the internal route template (Vercel).** API responses carry the
  server's own file path — `X-Matched-Path: /api/points/[wallet]`, `/api/account-label/add` —
  including dynamic segments the request URL never shows. Capture headers on every API probe
  (`curl -D-`) and you get the app-router route map without guessing. It also tells you the API
  is a **Next.js route handler**, which decides the next two questions: the Origin / CSRF gate
  lives in the handler (so `403 {"message":"Origin not allowed"}` is bypassed by any non-browser
  client — that is anti-abuse, not access control), and you must check whether the response
  carries `Access-Control-Allow-Origin` before calling anything cross-origin exploitable. A gate
  with no `ACAO` at all is not a CORS bug, no matter how many Origin values it accepts.

**CORS: a fixed `access-control-allow-origin` is NOT proof of safety or of misconfig.** Here the value
was hard-coded to the app origin, so `Origin: https://app.tld` "passed". Always send lookalike origins
(`https://app.tld.evil.example`, `https://evil-app.tld`, `http://app.tld`, `null`, `app.tld:evil`) and
confirm the header does **not** track the request Origin. A single same-origin test proves nothing.

### 3. Establish a CONTROL — find an endpoint that IS gated
Before declaring anything vulnerable, send an unauthenticated request to an endpoint you expect to be protected, and capture what *correct* rejection looks like:
```bash
curl -s -X POST https://api.target.com/api/users -H 'Content-Type: application/json' -d '{}'
# secure → {"error":"Missing or invalid authorization header"} or HTTP 401
```
This is your differential. A sibling API (e.g. a second API host, or a different route group on the same host) is the ideal control — same stack, so a different response = real authz gap, not a quirk.

### 4. Test each route family UNAUTHENTICATED, both methods
For every discovered route, send it with **no `Authorization` header** and compare to the control:
```bash
for r in <routes>; do
  curl -s -o /tmp/r -w "[%{http_code}] $r\n" -X POST -H 'Content-Type: application/json' -d '{}' "https://api.target.com/api/v2/$r"
done
```
Interpret:
- **`401`/`"Missing authorization"`** → gated (correct). Move on.
- **`200` with data** → unauthenticated data exposure. **Finding.**
- **`400 "field X is mandatory"`** → the route processed your request and reached *business-logic validation* without an auth check → **auth bypass; supply the field minimally to confirm.**
- **`200` + verbose DB/stack error** (e.g. `PROCEDURE db_x.sp_y does not exist`) → reached the data layer unauthenticated; also a SQLi-surface signal.
- **Mandatory fields named like `is_admin` / `is_internal` / `requested_by` / `role_id` / `account_type`** → **authorization derived from client-supplied parameters** — set the privilege flag and you self-elevate. Critical-class.

### 5. Pivot & prove (minimally)
- IDs returned by one endpoint (`account_id`, `order_id`, `deal_id`) are the keys the *other* endpoints consume — they prove the whole router is reachable, not just one route.
- Test `dev-`/`beta-`/`staging-` API variants — they frequently have weaker/disabled auth.
- Check the response headers: `Access-Control-Allow-Origin: *` compounds the issue (any web origin reads it from a victim's browser).
- **STOP at minimum-necessary proof.** A handful of records (or a `totalCount`) confirms the missing check. Do NOT enumerate the table — see `redteam-mindset` data-minimization boundary. The finding is the absent auth, not the data volume.

---

### 2d. A host that fuzzes to zero is NOT dormant — ask a technology-specific template

`api.0.xyz` answered `404` to *every* path from both `common.txt` **and** `raft-large-directories.txt`
(ffuf `-fc 404`, two runs, 0 results) — which reads like a dead host. It was a fully documented 72-endpoint
API. What found it was a nuclei `swagger-api` template hit on `/swagger-ui/swagger-ui.js`: a **deep,
two-segment path no directory wordlist carries**. Zero wordlist hits is evidence about the wordlist, not
about the host.

Three calls reconstruct the whole map once a Swagger UI exists:

```bash
curl -s https://HOST/swagger-ui/swagger-initializer.js | grep -o '"url": "[^"]*"'
#  -> "/api-doc/openapi.json"   (NOT /v3/api-docs, /openapi.json, /swagger-resources — those all 404'd)
curl -s https://HOST/api-doc/openapi.json -o spec.json     # 308 KB / 72 paths in one request
```

Then turn the spec into a **coverage matrix** instead of fuzzing: one `HEAD` per path, recording status +
`Content-Length` + `access-control-allow-origin`. Use HEAD — one endpoint here returned **82 MB**. The
matrix *is* the report (`43×200 / 11×400 / 10×404`, `ACAO:* 64/64`) and it is far stronger evidence than
any wordlist run. Read `components.securitySchemes` too: the descriptions leak the auth design verbatim
(`"Public routes also accept anonymous requests at the anonymous rate limit"`,
`"Bearer API key, or INTERNAL_ADMIN_TOKEN for internal admin routes"`), which hands you the exact header
name and the admin token concept.

Split ops by their `security` array: ops whose list omits `{}` are the keyed surface. Probe each with an
**empty-body POST** (inert) and confirm `401` arrives *before* argument validation — that single check
separates "admin API exists but is gated" from "admin API is wide open". Then triage in this order:
(1) paths named `internal|admin|debug|smoketest|api-key`, (2) the heaviest `Content-Length` (amplification),
(3) any endpoint answering a **membership oracle** (`200` vs `404 {"error":"… not in this snapshot"}`),
(4) whether the documented rate limit actually fires (30 benign requests, 0×429 = say so, don't invent a
threshold).

## What "the API behind the SSO login" really means

A common, dangerous architecture:
- `console.target.com` (the SPA) → login is **Entra/Okta/Google OAuth** (looks airtight).
- `api.target.com` (the backend) → some route groups enforce the bearer token, **some route groups forgot the middleware.**

The frontend login is theatre if the API doesn't independently validate the token on every route. Always test the API directly, bare, regardless of how locked-down the login UI is.

---

## Anti-patterns

- **"The app requires login, so the API must be protected."** No — test the API directly, unauthenticated. The whole point.
- **"Minified bundle, can't read it."** You don't need to read it — grep it for hosts/routes/secrets. 5 minutes.
- **"`/api/v1/foo` returned 404, so no API here."** Wrong base or wrong method. Try `/api/`, `/api/v2/`, POST not GET, and the exact route strings from the bundle (Express's 404 echoes the path — use it to calibrate).
- **"AIza key found → critical secret."** Validate first — most are Maps/analytics keys (`CONFIGURATION_NOT_FOUND` on identitytoolkit = not Auth-enabled). Don't over-claim.
- **Dumping the whole dataset once you get a 200.** Stop at PoC. (`redteam-mindset`.)
- **Account-creation / write endpoints as "proof".** Read endpoints prove the auth gap without creating state. Never POST a `create`/`signup`/`upload` to "demonstrate" — that's a destructive write needing explicit per-action authorization.

---

## Related Skills & Chains

- **`hunt-api-misconfig`** — once the API is mapped, run the broader misconfig matrix (method tampering, mass assignment, JWT alg confusion) per route.
- **`hunt-idor`** — the `account_id`/`order_id` pivots feed straight into IDOR testing across discovered routes.
- **`hunt-source-leak`** — sourcemaps (`*.js.map`) reconstruct original source for deeper route/secret extraction; same harvesting muscle.
- **`hunt-nextjs`** — for Next.js targets, layer the middleware-bypass (`x-middleware-subrequest`) and `/_next/data` route tests on top of this.
- **`redteam-mindset`** — the data-minimization boundary governs step 5: prove the missing check, don't exfiltrate the table.
- **`recon-scope-triage`** — verify the API host actually belongs to the target before testing (don't pop a same-named third party's API).