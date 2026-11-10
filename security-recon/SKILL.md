---
name: security-recon
description: "Use during Phase 0B recon of any security audit."
metadata:
  hermes:
    budget_kb: 25
    tags: [recon, osint, subdomain, enumeration, security]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Security Recon Playbook (Phase 0B)

## ⛔ Load Rules
- Load ONLY during Phase 0B (recon phase)
- EVICT after attack surface map complete → move to Phase 0C
- Output ALL recon data to FILE (CO-1 rule). Context gets summary ≤5KB.
- Budget: 25KB — read_file for reference files, never full-load

---

## Recon Pipeline (6 Steps)

### Step 0: Program scope + exclusion intake (BEFORE any enumeration)

Never let a scanner define the engagement. The target's own published rules decide whether a finding
is $500 or $0, and they define your authorised footing. Read them first.

1. `curl -sSL https://<target>/.well-known/security.txt` → follow the `Policy:` line to the
   bounty / VDP page. Fast path: `bash scripts/program-scope-intake.sh <domain>`.
 **Scope is often defined BY security.txt presence, not by the apex domain.** Some policies say
 "only domains/subdomains which have a security.txt file in their root are in scope" and then add
 "currently, the scope is limited to \<apex\>". Sweep `https://<host>/.well-known/security.txt`
 across EVERY live host and keep the ones whose body matches the canonical file. A 302 to the
 canonical URL counts; a soft-200 HTML error page does NOT (Shopware "Sales Channel Not Found"
 is the classic false positive). That gives an objective in-scope set you can defend, and it tells
 you which tempting hosts to leave alone. Full recipe + worked examples:
 `references/securitytxt-scope-sweep.md`.
   The file itself is also an audit surface — RFC 9116 conformance plus the mail-auth
   posture of its `Contact` address → `references/security-txt-audit.md`.
2. Extract three lists into `$DIR/scope.md`:
   - **In-scope assets** — exact hostnames / wildcards, and note the *explicit excludes*.
   - **Reward tiers** — which asset class pays most → prioritise that class. **Read this section for
     whether the program pays at ALL before you invest a session.** Some VDPs are acknowledgement-only
     by design ("due to our funding structure it is not currently possible for us to offer a paid bug
     bounty" — ORF, 2026-10: a token plus a Hall-of-Fame credit). That does not make the work worthless,
     but it changes the deliverable: no severity/bounty argument, and the report must say *in the body*
     that it carries no reward claim, or the first thing triage does is read it as a shakedown. Decide
     the framing at intake, not at write-up time.
   - **Exclusion / non-qualifying list** — the highest-signal part. It names every finding that
     triage will auto-close as informational / $0, no matter how clean the PoC.
3. Map the exclusion list onto the rest of this pipeline. When a program excludes
   "vulnerability-scanning reports without described impact", "missing headers / cookie flags",
   "banner / version disclosure", "open redirect alone", "reflected / self XSS",
   "user enumeration without a rate-limit demo", "most brute force", "DoS", and "phishing", then
   blind nuclei / dirsearch / ffuf volume on that target is wasted effort — and on programs that
   state global rate limits, a program-rule risk. Lead with manual, impact-first testing on the
   highest-tier asset instead.
4. Record the rules verbatim. Vendor triage (and any later reviewer) will hold you to the exact
wording, and a documented scope file stops the next session re-deriving it.

5. **When the policy defines scope by a FILE, derive the in-scope host set empirically** — the canonical
   procedure, the two traps, and the worked case are in `scripts/securitytxt_scope_map.py` and
   `references/security-txt-scope-mapping.md`. One extra trap worth keeping inline: `/security.txt` and
   `/.well-known/security.txt` can differ on the same host (one 404'd the latter while the former
   redirected to the canonical file), so probe the well-known path (the RFC 9116 location) and record
   what the root path did.

6. **A client-IP header reflected into a cookie is worth chasing, but prove the escalation or drop it.**
   Legacy estates routinely mint session ids from the request IP, and the IP often comes from an
   untrusted `X-Forwarded-For` / `Client-IP`. Two things to test, in this order:
   - **Reflection into `Set-Cookie`**: send `X-Forwarded-For: 1.2.3.4; Domain=evil.example` and read
     the raw header. On ORF `bits./boa.orf.at` the attribute text landed inside the cookie value
     (`Vietnam2Session=127.0.0.1.2.3.4; Domain=evil.<rand>`) — reproducible 3/3, cookie scoped
     `Domain=.orf.at`. Note precisely which attribute names survive; on that target only `Domain=`
     did (`Path=`, `Max-Age=`, `SameSite=`, `secure`, `expires=` were truncated), and the sibling
     `HopSession` hosts stripped the attribute entirely.
   - **Then the decisive test**: does ANY in-scope endpoint change its answer when the header
     changes? Fetch every candidate path twice (clean vs `X-Forwarded-For: 127.0.0.1`) and diff
     status + body sha256 + length. Re-runnable:
     `python scripts/xff_authz_diff.py live.txt paths.txt evidence/xff_authz_diff.json`. On ORF: 42 hosts x 5 paths = 420 requests -> **0
     XFF-sensitive endpoints**, which is what demoted the whole family to Low. Without this step the
     honest severity is unknowable, and overclaiming it is the easy mistake.
   Also rule these out explicitly before writing the report (each was negative on ORF): raw-CRLF
   response splitting (use a raw socket — curl refuses CR/LF in a header value, and the server
   stripped at CR), cache poisoning (`X-Cache: MISS` on the `Set-Cookie` response), session
   fixation (server re-mints regardless of the supplied cookie), and XFF-based ACL bypass with a
   matching token.

#### Step 0b-ii — mine the in-scope set for hosts your enumeration never found

The sweep only sees what `subfinder`/`httpx` already returned. Two cheap ways to widen it:

1. **Follow 3xx out of the in-scope hosts.**

   ```bash
   curl -s -D - -o /dev/null "https://<in-scope-host>/<path>" | grep -i '^location:'
   ```

   Observed (ORF 2026-10): `bits.orf.at/filehandler/` answered
   `303 Location: https://websys.orf.at/admincenter/` — an internal AdminCenter on a host the subdomain
   sweep never surfaced; scope-testing *that* host's security.txt put it in scope too. A redirect chain
   out of an in-scope host is the cheapest way to find in-scope services missing from your enumeration.
2. **Read the CSP headers on the in-scope hosts.** One ORF app's
   `frame-ancestors *.orf.at http://*.orf.at:8080 http://me.orf.at:*` handed over an internal hostname
   and a non-standard port for free — and a CSP's `connect-src` / `form-action` lists do the same job for
   API and auth hosts.

### Step 0b: Objective scope map — sweep security.txt across EVERY live host (not just the apex)

When a policy defines scope by a marker ("only domains/subdomains which have a security.txt file in
their root"), do not read that as a hint — **measure it**. After httpx has produced the live-host list,
request `/.well-known/security.txt` from each host **with `-L`** and keep the ones whose FINAL body is
the canonical file: match on the `Contact:` line, never on the status code. Output two files:

- `recon/securitytxt_map.txt` — every host :: IN-SCOPE / out
- `recon/in_scope_hosts.txt` — the in-scope set (this is what every later phase filters on)

Re-runnable: `scripts/securitytxt_scope_map.py <httpx.txt> <outdir>`.

Two traps, both hit against a live broadcaster VDP (2026-10):

- **A soft-200 is not a security.txt.** A 3rd-party shop subdomain answered `200` with an HTML error
  page (a Shopware "Sales Channel Not Found" template). A status-code check would have declared it
  in scope and sent the whole engagement at a vendor-hosted service the policy excludes. Matching the
  `Contact:` line filtered it instantly.
- **A 302 to the canonical file DOES count — and that is usually where the estate is.** Dozens of
  subdomains answered `302 -> https://<apex>/.well-known/security.txt` (200, byte-identical body).
  The vendor redirects the file deliberately, so they fall inside the written rule. On the example
  engagement the marker rule yielded **41 in-scope hosts** (legacy Jetty/Helma apps, an admin portal,
  per-region CMS instances) versus **1** under a strict "apex only" reading. Skipping this step would
  have thrown away essentially the entire attack surface.

**Resolve the ambiguity with the operator, once, in writing — then stay inside that line.** Policies
routinely carry both "only subdomains with a security.txt are in scope" *and* "currently the scope is
limited `<apex>`". Under-reading costs coverage; over-reading forfeits safe harbour. State both readings,
apply the written marker rule, and list every host you are deliberately **not** touching and why.

Then apply the same test to hosts you *discover later*: a modern SPA bundle referenced
`konto-api.<target>`, `anmeldung.<target>`, `on-newsletter.<target>` — none of which were in the
httpx sweep and **none of which serve a security.txt**. They were therefore out of scope and got no
further requests. The identity/account services are the most interesting modern target and the one a
marker rule is most likely to exclude — discover that boundary *before* probing, not after.

**Always run a negative control on the test itself.** `tvthek.<apex>` and `shop.<apex>` both failed
the security.txt test while sitting in the same brand. That is what proves the test *discriminates*
rather than passing every host you hand it — state the negative in PHASE_LOG next to the in-scope
count, so a later reviewer can see the sweep was not rubber-stamping.

Confirming authorised footing (a published program, or a signed RoE) is part of this step — not a
separate lecture. See `references/program-scope-intake.md` for the recurring exclusion patterns and a
worked example.

#### Step 0c: framework error pages are a reflection surface — check them on every new host

A host that returns a **framework-generated error page** (not a branded 404) is echoing request data.
The classic shape: *"Error: Unhandled request: /<decoded path>"* — the path is written into the HTML
unescaped, in `<title>` **and** again in the body. That second copy executes.

```bash
curl -s "https://<host>/<any-path>/%3Cscript%3Ealert(1)%3C/script%3E" | grep -c "<script>alert(1)</script>"
# 0 = clean; >0 = unescaped reflection, confirm in a browser before writing anything up
```

Confirm execution properly (never report a reflection as an XSS): load the payload URL in a headless
browser, register a `dialog` handler for `alert(document.domain)`, and add a second, dialog-free proof
with a DOM mutation (`document.title='XSSED-'+document.domain`). Two independent proofs. Only then
check `Content-Security-Policy` — a policy with `upgrade-insecure-requests; frame-ancestors …` and **no
`script-src`** does not block inline script, whereas the legacy `X-XSS-Protection: 1` header that looks
reassuring is ignored by current browsers.

Breadth matters more than the single hit: re-run the marker against **every** in-scope host (one request
each) before writing the report. In the worked case the same defect existed on a second host
(`pipe.orf.at` **and** `bolek.orf.at`) and that changed the breadth line, not the severity.

#### Step 0b-iii — the four decision rules for a marker-defined scope set (detail under Step 0b above)

Some policies state the scope conditionally: *"only domains/subdomains which have a security.txt file
in their root are in scope"*. Do not guess which hosts qualify — enumerate them and record the map.
Canonical procedure: the `### Step 0b` section above. Worked ORF.at case:
`references/security-txt-scope-mapping.md`.

```bash
# for every live host: does it serve the CANONICAL file, or just some 200?
while read -r line; do
  host=$(echo "$line" | awk '{print $1}' | sed 's#https\?://##' | cut -d/ -f1)
  out=$(curl -s -A "$UA" -L --max-time 12 "https://$host/.well-known/security.txt")
  echo "$out" | grep -q "Contact: mailto:<canonical-contact>" \
    && echo "$host :: IN-SCOPE" || echo "$host :: out"
done < live.txt
```

Four rules that decide the answer:

1. **Match the canonical CONTENT, not the status code.** A 200 is not in scope — an in-scope host is one
   that serves *the program's* security.txt fields.
2. **A 302 → the canonical URL counts as in scope.** That is the RFC 9116 `Canonical:` mechanism and
   the vendor redirecting it is a deliberate signal. Whole host families alias this way.
3. **A soft-200 HTML error page does NOT count.** A shop/SPA that answers `/security.txt` with a
   200 HTML shell ("Sales Channel Not Found", an SPA catch-all) has no security.txt. This is the single
   highest-yield false positive — it inflates the scope set with hosts the policy never covered.
4. **The policy may carry a narrowing sentence that contradicts rule 1** ("currently, the scope is
   limited to `<domain>`"). Resolve that explicitly, record which reading you took and why, and say so
   in the report. Silence on this is what loses safe harbour.

Then: **check scope for every host you discover later, before touching it.** Hosts that matter most
(identity/account/API services) often never appear in passive subdomain enumeration and only surface
inside a JS bundle or a redirect from a host you were already allowed to touch. In the ORF.at run the
most interesting targets (`konto-api`, `konto`, `anmeldung`, `on-newsletter`, `data-*`) were all
discovered late, all out of scope, and were left untouched — with that discipline stated in the report.

**Also read the policy's exclusion list before starting**, not after. "Non-exploitable findings and
reports that services do not fully align with best practice (missing headers, TLS config, version
disclosure)" turns stack traces, banner leaks and legacy-version findings into non-reportable noise;
only the *exploitable* thing on the same page is worth writing up.

*(Consolidated — this section previously repeated the sweep verbatim. The canonical procedure is the
empirical map above (`scripts/securitytxt_scope_map.py`) plus the two traps and the ambiguity rule; the
worked example, the 303 pivot chain and the header-reflection validation discipline live in
`references/security-txt-scope-mapping.md`.)*

### Step 0c: Scope gating can HIDE your best lead — follow redirects out of a legacy host

An in-scope host can hand you the next target. The in-scope legacy host `bits.<apex>` answered
`GET /filehandler/` with `303 Location: https://websys.<apex>/admincenter/` — an internal admin
portal that no subdomain list had surfaced. Chase it:

1. `curl -D -` on every non-404 path you find on an in-scope host and **read the `Location`** — legacy
   front doors 303 straight to the modern admin/SSO surface.
2. Scope-test the destination host like any other (Step 0b) before touching it.
3. Note that a redirect is only a **lead**, not a finding: the target of the redirect is where the
   real surface lives.

Legacy-estate tells worth grepping for in `recon/httpx.txt`, all seen on one brand in a single pass:

| tell | what it means |
|---|---|
| `Server: Jetty(6.1.22)` / other EOL versions in `-tech-detect` | a 2007-era origin still serving production |
| body `Problem accessing /<path>` | the app framework's own error page, leaks the framework layout |
| `Set-Cookie: <Name>=127.0.0.<client-ip><rand>; Domain=<apex>` | session token built from a client-supplied value — see the header-injection recipe |
| one host returning byte-identical `robots.txt` to the apex | shared config/deploy, likely the same platform |

Head-of-chain discovery is worth more than breadth: one 303 on a legacy host outranked the other 149
live hosts. Spend the next hour there, not on more enumeration.

See `references/security-txt-scope-mapping.md` for the full worked example (counts, the ambiguity, the
pivot chain, and the header-injection validation discipline that falsified two of three payloads).

### Step 1: Subdomain Enumeration
```bash
amass enum -passive -d $DOMAIN -o $DIR/amass_subs.txt
subfinder -d $DOMAIN -silent -o $DIR/subfinder_subs.txt
cat $DIR/*_subs.txt | sort -u > $DIR/all_subs.txt
echo "Total unique subdomains: $(wc -l < $DIR/all_subs.txt)"
```
**Repos:** owasp-amass/amass, screetsec/Sudomy

### Step 2: Port Scan + Service Detection
```bash
naabu -list $DIR/all_subs.txt -top-ports 1000 -o $DIR/ports.txt
cat $DIR/all_subs.txt | httpx -status-code -title -tech-detect -o $DIR/live.txt
awk '{print $1}' $DIR/live.txt > $DIR/live_hosts.txt
echo "Live hosts: $(wc -l < $DIR/live_hosts.txt)"
```
**Repos:** projectdiscovery/naabu

### Step 3: Directory + Endpoint Discovery
```bash
cat $DIR/live_hosts.txt | gau --threads 5 | sort -u > $DIR/urls.txt
katana -list $DIR/live_hosts.txt -depth 3 -o $DIR/crawled.txt
dirsearch -l $DIR/live_hosts.txt -o $DIR/dirs.json --format json
cat $DIR/live_hosts.txt | waybackurls > $DIR/wayback.txt
```
**Repos:** leebaird/discover, bhavsec/reconspider, kpcyrd/sn0int

### Step 3b: JS-bundle API-surface extraction (highest yield on SPA/framework targets)

For any target whose UI ships a JS bundle (React/Vue/Angular/Next/bespoke), the bundle **is** the
client→server endpoint map. Extract it BEFORE you fuzz — it beats wordlist guessing and stays inside
program rules (no volume, no brute force). Re-runnable: `scripts/bundle_apimap.py`.

1. Fetch the HTML entry; collect every `src=`/`href=` `.js` asset; fetch each bundle.
2. Pull endpoint-shaped strings:
   `"/[a-zA-Z0-9_./{}:$-]*(api|v[0-9]|graphql|oauth2|login|sso|webapi|token|reset|verify|callback|upload|invite)[a-zA-Z0-9_./{}:$-]*"`
   plus sibling-service hosts (`https://<host>.<target-domain>`) and **relative-fetch bases** like
   `window.location.pathname+"/webapi"` — the real API root is often per-path, not site-root.
3. Read the *call context* (method, body keys, param names) around each path to know how to probe it.
4. Confirm each path with a single request; note backend/version leaks in the response headers
   (`X-<svc>-Version`, `Ratelimit-Remaining`, service name) — they tell you the shape of the API.

**PITFALL — never `grep -oE '.{120}NEEDLE.{120}'` for context on a minified bundle.** On a 3–4 MB
single-line file that regex backtracks and *hangs* (this session: 60 s `timeout`, zero output). Get
context with Python windowed `str.find` instead:

```python
data = open(bundle, encoding="utf-8", errors="ignore").read()
i = data.find("my/endpoint")                 # loop: i = data.find(..., i+1) for every hit
print(data[max(0, i-130):i+150])
```

**Classify recovered paths before testing** — a route is not an endpoint:
| Path shape | Meaning |
|---|---|
| `/forum/:boardId`, `/user/:id/topics` | client-side SPA route, not an API |
| any path that `302`s to the home page | frontend fallback — not an endpoint |
| `/<base>/webapi` (relative to page) | the real JSON API root |
| `POST`-only path that `405`s on `GET` | endpoint exists; method-locked |

Point each recovered API host at its own rate-limit budget (observe `Ratelimit-Remaining`) and lead
with impact-first manual testing, not scanning.

### Step 3d: SPA bundle + tRPC recon (Vite / rolldown / webpack)

When the front end ships a hashed chunk graph and/or talks to a `/trpc` backend, the bundle is the
config dump *and* the API map. Three high-yield moves (detail + framing: `references/spa-bundle-and-trpc-recon.md`):

1. **Walk the whole chunk graph**, not just the entry (`main-*.js` is ~9 KB of imports). Regex the
   `./X.js` and `import("./X")` edges, BFS to ~300 chunks, **write each chunk as it arrives** so a
   mid-run reset does not lose the run.
2. **Dump the injected env block** — `grep -rhoE 'VITE_[A-Z_0-9]+:[`"'"'"'][^`"'"'"']*[`"'"'"']' chunks/`.
   Publishable/site/client keys (Clerk `pk_live_`, Stripe `pk_`, Datadog `pub…`, PostHog `phc_`,
   OAuth *client IDs*) are public by design — **not findings**. What *is* reportable:
   tenant **allowlists** (`*_ALLOWLIST_ORG_IDS`, `*_TEST_ORGS`) and internal identifiers
   (`*_INTERNAL_USER_IDS` = staff IDs, internal workspace UUIDs) — server-side control data in a
   public artefact. API base URLs and `*_REDIRECT_URI`s are recon intel.
3. **Enumerate tRPC procedures unauthenticated** — the error codes are an existence oracle:
   `-32001`/401 = exists (gated), `-32004`/404 = missing, `-32005`/405 = mutation exists.
   **A 200 is the prize** (public procedure). Run `scripts/trpc_enum.py <host> <names.txt>`.
   Harvest candidate names from react-query hooks in the chunks. **GET only** — a GET to a mutation
   returns 405 without invoking it; never POST to one to "see what happens".

Chunk filenames and in-chunk dev paths (`apps/<svc>/src/trpc/routes/…`) hand you the feature and
router layout for free.

### Step 3c: Dork recon (Camoufox+DDG -> Wayback -> Google)

```bash
python C:/Users/WINDOWS10/AppData/Local/hermes/scripts/dork-recon.py --target <domain> --out <target_dir>/dork-recon
```
- Layer 1 **Camoufox + DuckDuckGo** (bulk, no CAPTCHA) -> layer 2 **Wayback CDX** (volume/history) -> layer 3 **Google** (thin spots only, human-paced).
- Outputs `dork-urls.txt` / `dork-results.json` / `dork-report.md` -> feed into httpx -> katana -> nuclei, and into the classifier.
- Surfaces: login/admin, `.bak/.env/.sql/.log`, swagger/openapi, staging/dev hosts, cloud buckets, pastebin leaks.
- **Why not plain scraping:** direct `curl`/headless Chrome hits CAPTCHA/challenge on Google/DDG/Startpage — a real browser (Camoufox/Chrome headful) is required. See `D:/data hermes/advisory-intel/` probes for evidence.


### Step 3d: Situational skill routing (condition -> skill)

Read `skills/security/bb-audit-launcher/references/situational-skill-router.md` and, for every CONDITION
that matches a signal you already found (stack, auth shape, blockers, money/tax logic, mobile, web3), load
that skill for the current phase. This is how the ~60 condition-triggered security skills become reachable
WITHOUT inflating the always-on phase budget. Do this again before each 0C batch.

### Step 4: Tech Fingerprinting + Analysis
```bash
cat $DIR/live_hosts.txt | httpx -title -status-code -tech-detect -follow-redirects -o $DIR/fingerprint.txt
cat $DIR/urls.txt $DIR/crawled.txt $DIR/wayback.txt | sort -u | \
  grep -iE '\.js$|\.json$|\.xml$|\.env$|admin|login|api|graphql|debug' \
  > $DIR/interesting.txt
echo "Interesting endpoints: $(wc -l < $DIR/interesting.txt)"
```

### Step 5: Subdomain Takeover + DNS Checks
```bash
cat $DIR/all_subs.txt | httpx -status-code -title | grep -iE 'CNAME|github\.io|herokuapp|amazonaws|cloudfront|azure|vercel|netlify'
```
**Repos:** punk-security/dnsReaper

### Step 5b: Anonymous fingerprint of exposed self-hosted dev infra

Engineering-heavy targets surface internal tooling in subdomain enum (code review, source control,
CI, monitoring) — usually less hardened than the product, and several leak version/config to
*anonymous* callers. Each candidate gets **one** unauthenticated request to establish product +
version + whether it is already behind an IAP/VPN (product table + framing:
`references/exposed-dev-infra-fingerprint.md`):

```bash
curl -s "https://gerrit.<t>/config/server/version"                            # )]}' "3.9.11"
curl -s "https://gitlab.<t>/help" | grep -oE '1[0-9]\.[0-9]+\.[0-9]+' | head   # version
curl -s "https://bitbucket.<t>/rest/api/latest/application-properties"        # {"version":"9.2.1"}
curl -s "https://github-test.<t>/api/v3/meta"                                 # GHES installed_version
curl -s "https://<ghes-host>/setup"                                           # GHES mgmt-console state
```

Two traps that flip the verdict: (a) a host that returns the *same* ~200 KB login HTML for every
path with `Server: Google Frontend`/`ESF` is the **Google IAP login page** — protected, move on;
(b) GHES `/setup` showing *"Authentication Required — unlock the management console"* is
password-gated, **not** an admin takeover — read the body before claiming an exploit. Version
disclosure alone is usually auto-closed; the reportable part is the **exposure**, framed against the
sibling services the target *did* put behind IAP/VPN.

### Step 5c: Harvest an OAuth `client_id` from a downstream app (no login, no guessing)

When the estate runs an OAuth2/OIDC server (Hydra, Keycloak, Auth0…) and you need a real `client_id`
to exercise the authorize/consent flow, do **not** guess names (`blink`, `web`, `mobile` all failed).
Every web app that signs in *through* that server leaks its own `client_id` on the first leg of an
intended, unauthenticated flow:

```bash
# 1) NextAuth apps: the providers map is public (it hides clientSecret, NOT clientId use)
curl -s https://<app>/api/auth/providers
# -> {"blink":{"id":"blink","name":"Blink","type":"oauth","signinUrl":".../api/auth/signin/blink", ...}}

# 2) Drive the signin leg and read the Location header of the 302
CSRF=$(curl -s -c j.jar https://<app>/api/auth/csrf | python -c "import sys,json;print(json.load(sys.stdin)['csrfToken'])")
curl -s -b j.jar -c j.jar -D - -o /dev/null -X POST https://<app>/api/auth/signin/<provider> \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "csrfToken=$CSRF" --data-urlencode "callbackUrl=https://<app>/"
# -> Location: https://oauth.<target>/oauth2/auth?client_id=<UUID>&scope=read%20write&response_type=code&redirect_uri=...
```

That one request yields **client_id, the exact `scope` the app is allowed, and the registered
`redirect_uri`** — the three inputs every authorize-endpoint test needs. Repeat per app in the estate:
different apps usually carry different scopes (a read-only cashier app vs a `read write` admin
dashboard), which maps the privilege ladder for free.

Generic equivalents: any app whose first auth hop is a 302 to the provider (Keycloak
`/realms/<r>/protocol/openid-connect/auth`, `/.well-known/openid-configuration` on the provider
itself lists endpoints + `scopes_supported`). Provider discovery also tells you whether DCR is open
and which grant types exist.

### Step 5d: Team-chat / CI / monitoring exposed to the internet — one request each

Self-hosted collaboration and build infra is frequently internet-facing and less hardened than the
product. One unauthenticated request per candidate settles product + version + whether registration
is open; the *config* endpoint is the highest-yield and is public by design:

| Product | One-request fingerprint | What turns it into a finding |
|---|---|---|
| Mattermost | `GET /api/v4/config/client?format=old` | `EnableOpenServer` + `EnableUserCreation` + `EnableSignUpWithEmail` = **anyone can self-register**. Also `NoAccounts`, `EnableMultifactorAuthentication`, `SiteName`, `SupportEmail`, `Version`, `BuildEnterpriseReady` |
| Concourse | `GET /api/v1/info` | leaks `version` + `external_url` (canonical host you did not know) |
| Grafana | `GET /api/health` | `version` + `commit` (then `/api/dashboards/home`, `/api/org` → 401 = gated) |
| GitLab / GHES / Jira / Gerrit | see Step 5b | version + IAP-vs-open discrimination |

**Triage before you report:** (a) is the host linked from the public site? Probe the apex for the
hostname — an unlinked chat subdomain is an *internal* instance (the finding); a linked one is a
public community (not a finding). (b) do the data APIs answer unauthenticated? Mattermost
`/api/v4/teams`, `/api/v4/channels`, `/api/v4/users/me` → 401 = auth works; only the *signup* surface
is open. State that limit honestly — "open registration" is Medium, "open registration + readable
channels" is High. (c) version disclosure alone is usually auto-closed.

**Do not stop at the config flag — the escalation is mechanical and cheap.** Registration-open is info,
join-201 is the finding: create the account over the API, verify the mail token, log in (the session token
sits in the **`Token` response header**, not the body), `GET /api/v4/teams` → open team, `POST
/teams/<id>/members {team_id,user_id}` → 201, read **channel names only**, then DELETE the membership in
the same run. Exact call sequence, the `400 invalid_body_param` trap, and the safe-harbour wording:
skill `saas-test-account-provisioning` → `references/self-registration-impact-proof.md`.

### Step 5e: Wildcard DNS — check it BEFORE you trust a host count or a takeover scan

An apex with a wildcard `A`/`AAAA` record makes every label resolve, which silently invalidates three
things you are about to measure. Probe once, for both prod and staging:

```bash
python -c "import socket,random,string;l=''.join(random.choices(string.ascii_letters,k=20));print(l, socket.gethostbyname(l+'.<apex>'))"
# resolves -> WILDCARD. Measured on blink.sv 2026-10-12: random label -> 34.70.145.127 (prod)
#                                                     and -> 34.148.140.242 (staging)
```

Consequences, all hit on that run:

| Symptom | Reality | What to do instead |
|---|---|---|
| "81 of 82 CT-log subdomains are LIVE" | every label answers; most are one shared nginx/Cloudflare edge | count hosts returning a **distinct title/status/content-type** — keep a `recon/host_inventory.json` (status + server + title + length per host) and count services, not resolutions |
| nuclei floods on `wildcard-dns-detect` / `dns-waf-detect` | per-host DNS-detection templates, not findings — 64 + 2 "matches" and zero real hits across 81 hosts | drop those template ids when triaging; don't pass `-tags dns` in an estate sweep |
| takeover scan returns hits everywhere | NXDOMAIN cannot be the signal under a wildcard | compare **CNAME target vs served content** (dnsReaper-style signature match), never "resolves vs doesn't" |

Corollary: record the wildcard in `recon_summary.md` next to the live-host count, because every later
phase's denominator ("we scanned N hosts") is inflated by it.

---

### Step 6: Reachability + scan-budget triage (BEFORE launching any scanner)

**Enumerated ≠ reachable ≠ exploitable.** Classify every host first — this is where overclaiming
starts and where request budgets get burned.

| Class | Signal | How to treat it |
|---|---|---|
| Live & testable | httpx 200/30x/401/403 with a real banner/title | real target |
| DNS-only / internal | `dnsx -silent -a -resp -d HOST` → no answer, httpx silent | internal hostname disclosure = **INFO at best, not a finding** |
| Behind an access proxy | 302 → `*.cloudflareaccess.com/cdn-cgi/access/login/...` ("authenticate via the warp client") | untestable without a tenant identity — record, move on |
| SPA catch-all | every path returns the **identical byte size** (index.html) | not an endpoint; stop enumerating it |
| WAF/CDN noise | `403 45xx "Attention Required! \| Cloudflare"` | needs WAF-bypass discipline, not blind retries |

Internal-tool hostnames harvested from passive DNS (`jenkins*`, `argocd*`, `grafana`, `kibana`,
`rundeck`, `sentry`, `sensu`, `clearpass`, `*vpn*`, `gitlab`, `*.private`) usually do **not resolve
publicly**. Verify with dnsx before writing a single sentence about them.

**Scan budget:** nuclei cost = templates × hosts. A tag-filtered full-template run against 260 hosts
computed **1.27 M requests** and had to be killed mid-run. Estimate first (`-stats` prints
Templates/Hosts/Requests), then scan a curated priority list (≈15–25 hosts) at `-rl 3-5 -c 3`.
When a program states it enforces rate limits globally, over-scanning is a *program-rule* risk, not
just noise. A `429` / Cloudflare `error code: 1015` means stop and slow down immediately.

**Two traps confirmed on a real 81-host run:**
- `nuclei -as` (adaptive) loaded **0 templates** and made ~300 requests, then printed a clean
  `Templates: 0 | Matched: 0 | Requests: 300/300 (100%)` — i.e. it *looks finished* with zero coverage.
  When Wappalyzer tech-detection returns nothing the adaptive set is empty. **Always read the
  `Templates:` count in the `-stats` line**; if it is 0, re-run with explicit `-tags`.
- Wall-clock is brutal: `5802 templates × 81 hosts = 1.17 M requests`; at `-rl 60` that is ~5 h.
  Either cut hosts to 15–25 priority hosts, or cut templates
  (`-tags cve,default-login,exposure,takeover,misconfig -severity high,critical`), and run it with
  `background=true, notify_on_complete=true`. **Never in the foreground** — a foreground timeout kills
  the run and leaves a partial output file that must not be read as "no findings".

#### Step 6b: Bounded replacement sweep (when full-template nuclei is not viable)

Do NOT just abandon the wide scan — replace it with a **bounded, targeted sweep** you can finish and
triage honestly: `hosts × curated_paths`, ~4 req/s, SPA-catch-all aware.

Recipe (re-runnable script: `scripts/doc_sweep.py`):
1. Build the in-scope live host list (filter OOS subdomains explicitly — `community.`, `support.`,
   `docs.`, `sandbox.`, `ghost.`, vendor/3rd-party domains).
2. Curated path set (~14): `/README.md /README /readme.md /CHANGELOG.md /.env /.dev.vars /config.json
   /wrangler.toml /package.json /swagger.json /openapi.json /.git/config /.well-known/security.txt /api-docs`.
3. **Catch-all awareness:** fetch each host's `/` first, keep its `(len, sha256[:16])`, and drop any
   response that matches it (or differs by <8 bytes when >1KB) — that single filter kills most of the
   false positives on SPA hosts.
4. Only report `200` whose body looks like a real document (`application/json|yaml|toml|text/plain|xml`
   or a doc-ish path) and whose body is not an SPA shell.
5. 260 hosts × 15 requests ≈ 3.6 K requests, finished in ~8 min at ~4 rps. Write hits + every host's
   root signature to one JSON so a later pass can re-triage without re-requesting.

#### Step 6c: Triage filters — what a sweep hit is NOT

Sweep output is raw noise until classified. Default to "not a finding" for all of these:

| Hit shape | Verdict |
|---|---|
| Byte-identical body across many paths/hosts, title `Sign in ・ Cloudflare Access` (~48 KB) | access-proxy login page, **false positive** |
| SPA shell (`__next`, `data-next-head`, `id="root"`, vite/`@vite/client`) | not an endpoint |
| Stock upstream template README (e.g. a WordPress/Pantheon or Cloudflare Workers starter README, `git clone` + placeholder hostnames) | **NOT a finding** — public boilerplate, self-debunk before reporting |
| Front-end `config.json` with GA ids, reCAPTCHA/Turnstile **site key**, Google OAuth **client_id**, feature flags, API base URLs | public by design — **not a finding** (site keys / client ids are not secrets) |
| Internal design doc, deployment notes, endpoint/KV schema, staff-only docs | genuine info-disclosure finding (usually P4) |

Write the classification into the log either way — a documented negative is what stops the next
session re-scanning the same 260 hosts.

#### Step 6d: CDN-hosted object-storage bucket — check the LIST operation

Highest-yield one-request check on a hardened target. Any `assets.` / `static.` / `cdn.` / `files.`
host that is a CNAME to a bucket (GCS / S3 / R2 / Azure Blob) may expose **anonymous listing**:
object *read* is the CDN working as designed, but a bucket-level `allUsers → objectViewer` binding
grants `storage.objects.list`, so anyone can enumerate every object.

```bash
curl -s "https://assets.<target>/?list-type=2&max-keys=25"     # <ListBucketResult> = exposed
curl -s "https://assets.<target>/?list-type=2&delimiter=%2F&max-keys=1000"   # top-level prefixes
```

If it lists: page the whole bucket with `scripts/bucket_list.py <host> <outfile>` (one target yielded
711 K objects / 466 release dirs), then **(a)** grep the key list for `.map .env config secret backup
.sql .gz`, and **(b)** test the WRITE path with a single benign labelled marker to set severity —
`PUT` returning `403 … storage.objects.create` = no write (Low/Med info-disclosure), `200` = CDN
content control (escalate). Full recipe, severity framing and the "don't claim the public objects are
the bug" wording: `references/cloud-storage-cname-bucket-listing.md`.


---

## Output → FILE, Summary → Context

After all steps, write `$DIR/recon_summary.md`:
```
# Recon Summary — $DOMAIN
- Total subdomains: N | Live hosts: N | Open ports: N
- Interesting endpoints: N | Tech stack: [list]
- Potential attack vectors: [list]
- Files: all_subs.txt, live.txt, ports.txt, urls.txt, crawled.txt, interesting.txt
```
Context receives ONLY the summary. NEVER display full file contents.

---

## ⛔ VERIFICATION
Before claiming recon complete, run:
```bash
python C:/Users/WINDOWS10/AppData/Local/hermes/scripts/audit-checkpoint.py <target_dir> --phase 0B
```
Checkpoint reads actual files from disk (subs.txt, live.txt, urls.txt).

## ⛔ RECON ENFORCEMENT (MANDATORY)
Setiap tool di playbook ini WAJIB dijalankan dengan TOOLS yang tepat.
Baca reference files → jalankan tools-nya → buktikan dengan output di disk.

Bukan hanya sebut nama tool. JALANKAN:
- subfinder → subfinder -d <target> -o subs.txt
- httpx → cat subs.txt | httpx -o live.txt
- naabu → naabu -list subs.txt -o ports.txt
- gau/waybackurls → gau <target> > urls.txt
- katana → katana -u <target> > crawled.txt
- whatweb → whatweb <target>
- ffuf → ffuf -u <target>/FUZZ -w wordlist
- nuclei → nuclei -l live.txt

Baca reference file recon-toolkit.md → ikuti langkah tool yang ada → JALANKAN.
Jangan skip tool karena "kemungkinan tidak ada hasil" — JALANKAN DULU.
Output KOSONG pun JALANKAN — buktikan target tidak punya subdomain, bukan asumsi.

## AI Recon Patterns
- **Autonomous Agent (pikpikcu/airecon):** fingerprint → LLM analysis → targeted testing
- **Swarm (Armur-Ai/Pentest-Swarm-AI):** parallel agents → merge

---

## Integrated Repos (19)

| Repo | Stars | What We Took |
|------|-------|--------------|
| owasp-amass/amass | 15.2K | Subdomain enum methodology |
| yogeshojha/rengine | 8.8K | Automated recon pipeline |
| projectdiscovery/naabu | 6.3K | Port scanning workflow |
| ivre/ivre | 4.1K | Self-hosted Shodan alternative |
| leebaird/discover | 3.9K | Recon automation scripts |
| Astrosp/Awesome-OSINT-List | 4.4K | OSINT tool index |
| bhavsec/reconspider | 2.8K | OSINT framework patterns |
| kpcyrd/sn0int | 2.5K | Semi-auto OSINT framework |
| screetsec/Sudomy | 2.4K | Subdomain analysis workflow |
| 1N3/BlackWidow | 1.8K | Web scanner with OSINT |
| m3n0sd0n4ld/GooFuzz | 1.6K | OSINT fuzzing technique |
| AlbusSec/Penetration-List | 1.3K | Vuln-type resource index |
| uphiago/recon-skills | 1.3K | Skill pack (CORS/XSS/SSRF) |
| pikpikcu/airecon | 1.1K | AI recon agent pattern |
| PhonePe/mantis | 1K | Recon workflow automation |
| gl4ssesbo1/Nebula | 635 | Cloud recon/enum framework |
| hisxo/ReconAIzer | 911 | Burp AI recon extension |
| zan8in/afrog | 4.4K | AI vuln scanner |
| skavngr/rapidscan | 2.1K | Multi-tool web scanner |

---

## Cross-References
- Attack playbooks → `security-web-attacks` (Phase 0C)
- Scanner selection → `security-scanners` (Phase 0C)
- Scope rules → `bug-bounty-recon.md`
- Launcher rules → `bb-audit-launcher`

## References
- `references/rpc-fingerprint.md` — Ethereum/EVM RPC endpoint fingerprinting + node security assessment (rpc-fingerprint + pwngeth)
- `references/security-txt-scope-mapping.md` — the ONE reference for policies that define scope by security.txt *presence*: the empirical host-by-host map, the 200-is-not-a-security.txt trap, rule-vs-summary ambiguity, the 303-`Location` pivot from an in-scope legacy host to an internal admin portal, and the header-reflection validation discipline (3× with the SAME payload; curl strips CRLF so raw-socket work is needed; proving the negatives). Supersedes the short-lived `securitytxt-defined-scope.md`. — ORF 2026-10 case
- `references/recon-toolkit.md` — 19 recon repos with tool selection guide
- `scripts/doc_sweep.py` — bounded SPA-catch-all-aware sensitive-file/exposure sweep (Step 6b); pair its output with the Step 6c triage filters before reporting anything
- `scripts/xff_authz_diff.py` — the decisive severity test for a client-IP-header finding: fetch every host x path twice (clean vs `X-Forwarded-For: 127.0.0.1`) and diff status + body sha256 + length. Zero diffs is what lets you report the family as Low honestly; low-rate by default so it stays inside a "no volumetric testing" rule.
- `references/program-scope-intake.md` — Step 0 detail: security.txt → Policy → the recurring exclusion patterns that auto-close scanner noise, plus a worked example
- `references/securitytxt-scope-mapping.md` — Step 0b detail: deriving an objective in-scope host set when the policy scopes by security.txt presence (302→canonical counts, soft-200 HTML does NOT), late-discovered hosts that never appear in passive enum, and the two follow-on sweeps a completed scope map enables (forwarding-header trust, legacy error-page reflection)
- `scripts/program-scope-intake.sh` — fetch `.well-known/security.txt`, follow `Policy:`, dump the program page text for scope intake (one command)
- `scripts/securitytxt_scope_map.py` — Step 0b: probe `/.well-known/security.txt` on every live host (redirects followed, body-matched not status-matched) and emit `securitytxt_map.txt` + `in_scope_hosts.txt`. Use when the policy defines scope by security.txt presence.
- `references/security-txt-audit.md` — audit a security.txt as a deliverable: RFC 9116 field conformance, the mail-auth cross-check on the `Contact` mailbox (DMARC/DKIM/SPF — `p=none` = spoofable report address), signature/encryption, and dangling-pointer checks
- `scripts/bundle_apimap.py` — fetch a page's JS bundles and extract the API endpoint map + call-context (Step 3b); use windowed `str.find`, never context-grep on minified JS
- `references/spa-bundle-and-trpc-recon.md` — Step 3d detail: recursive Vite/rolldown chunk crawl, the `VITE_*` env dump and which values are reportable vs public-by-design, and the tRPC 401/404/405 existence oracle with framing
- `scripts/trpc_enum.py` — GET-only unauthenticated tRPC procedure sweep; classifies 200/public, 400/needs-input, 401/auth, 404/missing, 405/mutation (Step 3d)
- `references/cloud-storage-cname-bucket-listing.md` — Step 6d detail: detecting anonymous bucket listing behind a CDN CNAME, the write-probe severity test, impact framing, and `.map`/`.env` sweep of the key list
- `scripts/bucket_list.py` — page a publicly-listable bucket (GCS XML / S3 API) to a key file with incremental writes and retry (Step 6d)
- `references/exposed-dev-infra-fingerprint.md` — Step 5b detail: anonymous product+version endpoints for Gerrit / GitLab / Bitbucket DC / GHES / Grafana / P4, the IAP false-positive tell, GHES mgmt-console state reading, and the comparison framing that makes exposure reportable

## Companion Reference — `bugbounty-playbook` (additive, never overrides)

Source-by-source recon playbook depth (mirror of bugbounty.info, 186 pages) lives in
the `bugbounty-playbook` skill — read it as a second opinion on *ordering and what
each source yields*, not as a replacement for the pipeline in this file:

- `references/recon/` — Subdomain-Enumeration, ASN-Mapping, Certificate-Transparency, Cloud-Range-Discovery, JavaScript-Analysis, GitHub-Dorking, Wayback-Mining, Parameter-Discovery, Port-Scanning, SaaS-Enumeration, Tech-Fingerprinting, OSINT-on-Employees, Shodan-Censys-Fofa, Exposed-Git, Pipeline, Data-Management, Monitoring.

Read: `skill_view(name='bugbounty-playbook', file_path='references/recon/Pipeline.md')`