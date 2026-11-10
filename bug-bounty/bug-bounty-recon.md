## PHASES 1-3: SCOPE + RECON + ANALYZE (Detailed)

---

### Phase 1: SCOPE — Lock the target & rules
- Map the target: what it does, data flows, trust boundaries.
- Parse the bounty program policy: in-scope / out-of-scope assets.
- Build quick threat model: what's valuable, who are the actors.
- **Rank the surface before you touch it:** `python $TOOLKIT/web2/scope_narrower.py recon.txt --top 5`
  — a 500-host inventory is not a plan. Emit a shortlist, then work the shortlist.
- **Mobile App targets (React Native/Expo):** Load `references/mobile-app-bundle-recon.md`
- **Solidity/DeFi targets:** Load `references/solflow-integration.md`
- Output: target map + initial vulnerability hypotheses.

### Phase 2: RECON — Map the full attack surface
→ `references/recon.md` + `references/viability-gate.md` (5-min CDN/WAF + API pulse + decision)
- Subdomain enumeration, port scanning, tech fingerprinting (passive first).
- Crawl, spider, JS analysis, source map extraction.
- Wayback machine, cert transparency, GitHub reconnaissance.
- **SaaS/API:** `references/saas-bounty-hunting--*.md` (split topic files — `ls references/saas-bounty-hunting--*.md`)
- **Smart Contract:** `smart-contract-audit-lab--*.md` for toolchain setup
- Output: complete asset inventory + prioritized test candidates.
- **TIME BUDGET 20/60/20 (v3.2.0):** recon max 20% of window. Recon = inventory, NOT findings. If >30%
  of window spent with zero authenticated requests → STOP recon, provision accounts (Stage 1.5, non-blocking:
  30m → degradasi §1.0), enter
  authenticated test matrix (`references/account-first-exploitation.md` §3-4).
- **DELTA LIST (v3.2.0):** recon MUST also output what is NEW/untested (features <30d, staging in-scope,
  org/invite/billing flows, new API versions) — attack the delta first (`account-first-exploitation.md` §8).

### Phase 3: ANALYZE — Understand & form attack hypotheses
→ `references/vuln-classes.md` (web/API) + `references/web3.md` (blockchain) + `references/web3-dapp-backend.md` + `references/advanced-vuln-vectors-2026.md` (OAuth bypass, cookie tossing, JWT alg confusion, LDAP/XSLT injection, prototype pollution, SSTI via error pages, WebSocket frame attacks, signature replay, sandwichable logic, slippage manipulation, minOut validation)
- Match each candidate to relevant vulnerability classes.
- Trace: input → processing → sink. Identify broken trust boundaries.
- Prioritize by **impact × likelihood**.
- **DeFi:** Load `defi-exploit-patterns--*.md` (AMM, StableSwap, flashloan patterns)
- **Smart Contract:** Load `smart-contract-audit--*.md` (Solidity/Vyper deep analysis)
- **Oracle:** Load `oracle-security-audit--*.md` (timelock, staleness, price bounds)
- Output: ordered hypothesis list.

### Phase 4: VERIFY & EXPLOIT — Prove with working PoC
→ `references/verification-and-poc.md` + `references/pitfalls-discipline.md` + `references/advanced-vuln-vectors-2026.md` (PoC format section)
**⛔ STAGE 1.5 HARD GATE (v3.2.2 NON-BLOCKING):** auth matrix (IDOR A×B, priv-esc, tenant isolation,
business logic — `references/account-first-exploitation.md` §3) needs ≥2 TARGET accounts (aplikasi yang
diaudit), sessions in `_progress/<target>/target-state.json`. Provisioning >30m → degradasi §1.0:
(1) vektor vertikal dgn 1 akun SEKARANG + cron-retry akun ke-2, (2) OAuth khusus bounty, (3) vektor anonim
ber-value. PLATFORM accounts (Comolho/H1/BC — portal submit) = Stage 5-7, haram memblokir audit.
Anonymous-only findings (info disclosure, headers, misconfig) = the by-design graveyard. Read §9 checklist
before declaring the target exhausted.
- Confirm hypotheses with **minimal but complete** proof steps.
- **Prove the auth matrix with the harness, not by hand:** `python $TOOLKIT/web2/idor_harness.py setup -c target.yaml`
  then `verify -c target.yaml` — two identities, replays A's object ids as B, emits `IDOR-CONFIRMED`
  with both raw HTTP responses attached. If you cannot produce that pair of responses, you do not
  have an IDOR — you have a hypothesis.
- For Web3: Foundry fork test (NOT mainnet blind execution).
  Generate the harness: `python $TOOLKIT/web3/invariant_scaffold.py targets.yaml --out test/invariant`
  — then **verify it two ways** (passes on the clean contract, breaks on the injected-bug copy)
  before you trust a green run.
- **MUST exploit to report.** "Gimana mau buat bug report kl ternyata gkbs dites d real chain"
- Document every reproduction step precisely.
- **PoC format (MANDATORY per finding):**
  ```
  ### PoC: [Vulnerability Name]
  Setup: [prerequisite steps]
  Request: [exact HTTP request / contract payload / WebSocket frame]
  Expected Behavior: [what SHOULD happen]
  Actual Behavior: [what ACTUALLY happens + evidence]
  Impact: [data exfil sample / PII leakage / financial loss path]
  CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N — Score: 8.6 (HIGH)
  ```
- Output: verified exploit code + evidence.

### Phase 4.5: DEEPDIVE GATE — MANDATORY before presenting findings
**⛔ SEQUENCING RULE (HARD STOP):** Do NOT write report scripts until:
1. Phase 4.5 deepdive is complete
2. VRT comparison done for EACH finding
3. Viability gate passed
4. User has been presented the list and chosen which to report

**Persistence rule:** If user says "deepdive again", you've already failed. When web-app returns 403/401 consistently → PIVOT to infrastructure, JS bundles, third-party services. NEVER accept "no finding" without exhausting these angles.


## PLATFORM WORKFLOWS

### Bugcrowd
→ `bugcrowd-workflow--*.md` (setup, headers, reporting, SPA recon)
→ `bugcrowd-vrt--*.md` (VRT v1.19 — 33 kategori, P1-P5, smart contract, AI security)
→ `bugcrowd-researcher-guide--*.md` (onboarding, program discovery, submission, disclosure, payment)

### Bugcrowd Quick Reference:
- Identity: `MrFz <MrFz@bugcrowdninja.com>`
- Header: `Bug-Priority: P1` atau `P2` di body JSON
- Endpoint: `https://bugcrowd.com/submissions.json`
- Program pages: Use `browser_navigate` + JS extraction (web_extract sering 504)
- **Program Discovery API:** `https://bugcrowd.com/engagements.json` — returns ALL public bounty programs as JSON (no auth needed). Filter by name/tag to find targets. Faster than crawling React SPA pages.

### YesWeHack (Platform Workflows)
→ `references/yeswehack-workflow.md` — public API enumeration (no auth), scope/policy/bounty extraction, scope_type filtering, URL-encoding pitfalls

### Program Discovery — Bugcrowd API Method
Bugcrowd program pages are React SPA (can't extract via curl/web_extract). BUT the underlying API works:

```bash
# List all public programs
curl -s "https://bugcrowd.com/engagements.json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for eng in data:
    name = eng.get('name','')
    tagline = eng.get('tagline','')
    status = eng.get('status','')
    offers = eng.get('offers',{})
    max_payout = offers.get('max_payout','?')
    print(f'{name} | {status} | max=${max_payout} | {tagline}')
"
```

**Filter by keyword:**
```bash
curl -s "https://bugcrowd.com/engagements.json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for eng in data:
    if 'KEYWORD' in eng.get('name','').lower() or 'KEYWORD' in eng.get('tagline','').lower():
        print(json.dumps(eng, indent=2))
"
```

**Returns per engagement:** `name`, `tagline`, `status`, `offers` (min/max payout), `engagement_id`, `program_type` (bug_bounty/vdp), `safe_harbor`, `targets` (in-scope URLs).

**Cross-reference with `bounty-targets-data`:** For scope details, use `arkadiyt/bounty-targets-data` (already documented in pitfalls). The `engagements.json` endpoint gives the overview; `bounty-targets-data` gives detailed scope.

### YesWeHack
**Public API (no auth required)** — full program enumeration + scope details:
```bash
# List ALL programs with bounty info
curl -s "https://api.yeswehack.com/v2/programs?with_fields=program+scopes" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for p in data.get('data', []):
    slug = p.get('slug','')
    name = p.get('name','')
    bounty = p.get('bounty', {})
    min_b = bounty.get('min', '?')
    max_b = bounty.get('max', '?')
    print(f'{slug} | {name} | ${min_b}-${max_b}')
"

# Get specific program scope + details
curl -s "https://api.yeswehack.com/v2/programs?slug=<PROGRAM_SLUG>&with_fields=program+scopes+program+disclosure+program+policy+program+bounty" | python3 -c "
import sys, json
data = json.load(sys.stdin)
p = data['data'][0]
print(json.dumps(p, indent=2))
"

# Filter by published state
curl -s "https://api.yeswehack.com/v2/programs?states=published&with_fields=program+scopes"
```

**Key fields returned:** `slug`, `name`, `company_name`, `bounty` (min/max), `rewards[]` (severity → reward mapping), `scopes[]` (type, target, scope_type, in_scope/out_of_scope), `policy`, `disclosure`, `created_at`, `updated_at`.

**Pitfall:** URL encoding matters — `with_fields=program+scopes` (space encoded as `+`). Omitting `with_fields` returns programs WITHOUT scope data.

### HackenProof (Smart Contract / Blockchain Bounties)
→ `references/hackenproof-workflow.md` — Platform URL patterns, program discovery (HTML scrape works), scope extraction

**Quick Reference:**
- Programs page: `https://hackenproof.com/programs` (HTML-rendered, `curl` + `grep` works)
- Specific program: `https://hackenproof.com/program/{slug}` (singular, NOT `/programs/`)
- Dashboard: `https://dashboard.hackenproof.com`
- **No public API** — use `curl` scrape for discovery (unlike Bugcrowd's `engagements.json`)
- **Known programs:** Cetus (Sui/Move DEX), Solana ecosystem, TON ecosystem
- **Pitfall:** `/programs/{slug}` (WRONG, redirects) vs `/program/{slug}` (RIGHT)

```bash
# Program discovery
curl -s "https://hackenproof.com/programs" | grep -oP 'href="[^"]*"' | grep -i '/program/' | sort -u

# Scope extraction for a specific program
curl -s "https://hackenproof.com/program/PROGRAM_SLUG"
```

### Immunefi
→ `immunefi-workflow--*.md` (submission + PoC + report template)
→ `references/immunefi-recon-workflow.md` — Proven recon workflow: program discovery (ranked list from web_search), 5-step single-target recon (bounty page → GitHub API → docs → audits → attack surface map), known top programs, common protocol patterns (lending/liquid staking/bridge/DEX), pitfalls (broken data sources, payout calc)
→ `references/immunefi-program-discovery.md` (program listing methods, tier data, aggregator sources)
→ `references/defillama-target-discovery.md` — DeFiLlama NEW-protocol discovery (listedAt <1yr + TVL>$10M → fresh attack surface pre-bounty), bounty/email enrichment workflow, Windows large-JSON pipeline pitfalls
→ `references/immunefi-rules.md` (platform rules, SLAs)
→ `references/immunefi-severity.md` (Severity Classification System v2.2)
→ `references/immunefi-poc.md` (PoC guidelines, templates)
→ `references/web3-vuln-patterns.md` (proxy, reentrancy, flashloan, oracle, bridge, MEV)

**⚠️ Immunefi website is a client-rendered SPA** — curl/web_extract/browser all fail to extract program lists. Use SmartContractsHacking.com aggregator or web_search for program discovery. No official API exists. See `references/immunefi-program-discovery.md` for full methodology.

### SaaS / API Targets
→ `references/saas-bounty-hunting--*.md` — the SaaS guide, split into focused files (~20). Pick by topic, e.g.:
- `saas-bounty-hunting--auth-endpoint-testing-patterns.md` — auth surface
- `saas-bounty-hunting--jira-cloud-endpoints.md` — Jira/Atlassian cloud
- `saas-bounty-hunting--ai-chatbot-attack-surface.md` — AI features
- `saas-bounty-hunting--appsheet-audit-methodology.md` — low-code platforms
- `saas-bounty-hunting--*-session-*.md` — dated real-session notes (what was tried, what held)

Covering: JS bundle recon, unauth endpoint discovery, token lifecycle, rate-limit pivoting,
business-logic testing, AI/LLM feature testing, analytics proxy injection, third-party SDK abuse.
```bash
ls references/saas-bounty-hunting--*.md    # full list
```

**CMS Backend Testing:** When target uses headless CMS (Payload, Strapi, Directus):
- Check `/api/graphql` for introspection (default enabled on Payload CMS)
- Test `loginUser` and `forgotPasswordUser` mutations (no auth required)
- Check staging variants for weaker security
- **GraphQL lockout bypass:** If portal form has account lockout, test if GraphQL `loginUser` enforces the same lockout — often it doesn't, giving unlimited brute force
- **`__NEXT_DATA__` extraction:** On Next.js/Payload CMS pages, extract emails, internal URLs, lockout config from the script tag — see `references/nextjs-nextdata-disclosure.md`
→ `references/payload-cms-graphql-attack-patterns.md`

**SAML/SSO Testing:** When target has SAML SSO login:
- Extract keys from JS bundles (SignedXml, PEM patterns)
- Sign assertions with extracted keys, test ACS endpoints
- Test relay state bypass (empty, null, random, omitted)
- **VERIFY the full chain** before claiming CRITICAL — see VERIFY BEFORE CLAIMING pitfall
→ `references/saml-exploitation-patterns.md`

**GraphQL Error-Based Enumeration:** When introspection is disabled but mutations exist, probe each mutation name with `mutation { MutationName(test:"probe") { id } }` — error messages reveal argument names, types, enums, and database structure. See `references/graphql-attack-patterns.md` Sections 15-16 for full technique + reCAPTCHA null-token bypass.

### AI / LLM Red Teaming
→ `ai-llm-redteam--*.md` (adversarial prompt research, guardrail bypass)
- Adversarial prompt research for LLM-integrated applications
- Prompt injection via input fields
- Model extraction, system prompt leakage
- Guardrail bypass testing
- Content policy violation testing

---


---

## 📜 SCOPE GUARD — Authorization Enforcement

```python
from scope_guard import assert_in_scope, is_in_scope, load_scope
scope = load_scope("scope.json")
ok, reason = is_in_scope("https://chal.ctf.example/01", scope)
assert_in_scope("https://chal.ctf.example/01")
```

### scope.json Format
```json
{
  "competition": "Example CTF 2026",
  "allow_hosts": ["chal.ctf.example", "*.ctf.example"],
  "allow_cidrs": ["10.13.37.0/24"],
  "deny_hosts": ["admin.ctf.example"]
}
```
Deny-wins: deny_hosts checked FIRST. Wildcard + CIDR supported.

---


---

## 📡 VDP RECON PIPELINE

### Phase -1: Security.txt Mass Scan
```bash
curl -sL "https://tranco-list.eu/top-1m.csv.zip" -o tranco.zip && unzip tranco.zip
awk -F',' '{print $2}' top-1m.csv > domains.txt
python3 ~/scan_optimized.py domains.txt results.csv  # 50 workers, 3s timeout
```
→ Full script: `references/security-txt-mass-scan.md`

### WordPress REST API Enumeration
```bash
# Namespace discovery (custom sites: 20+ namespaces = many findings)
curl -s "https://target.com/wp-json/" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(n) for n in d.get('namespaces',[])]"

# Custom post type enum
for type in post page hdsnav topic gallery reference; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://target.com/wp-json/wp/v2/${type}?per_page=1")
  [ "$code" != "404" ] && echo "[${code}] ${type}"
done

# Author archive enum (separate from REST API, usually NOT excluded)
for i in 1 2 3 4 5; do
  curl -sI -o /dev/null -w "%{http_code} → %{redirect_url}" "https://target.com/?author=$i"
done
# 301 → /author/admin = username leaked

# Login error-based enum
curl -s -X POST "https://target.com/wp-login.php" -d "log=admin&pwd=wrong" | grep -o 'password for [^<]*'
```
**Key:** Custom namespace permission bypass — standard WP blocks `?status=unpublish` (400), custom plugin namespaces BYPASS this.
→ Full WordPress testing: `references/wordpress-admin-attack-surface.md`, `references/wordpress-vip-testing.md`

### Discourse Forum Enumeration
```bash
# User directory (paginated, usually 100/page, up to 2000 users)
curl -s "https://community.target.com/directory_items.json?page=0" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for item in data.get('directory_items',[]):
    u = item.get('user',{})
    print(f'{u.get(\"username\")} | posts:{item.get(\"posts_read\")} | likes:{item.get(\"likes_received\")}')
"

# User list with activity
curl -s "https://community.target.com/admin/users/list.json?order=posts"

# Recent topics (may leak internal info)
curl -s "https://community.target.com/latest.json" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for t in data.get('topic_list',{}).get('topics',[])[:10]:
    print(f'[{t.get(\"id\")}] {t.get(\"title\")} (views:{t.get(\"views\")})')
"
```
**Key:** Discourse exposes user data, topic content, and internal discussions via public JSON endpoints. Staging credentials, wp-config values, and user PII often appear in support topics.
