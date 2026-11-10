---
name: bug-bounty
author: Fauzi Susanto
description: "Use when hunting bug bounties or authorized testing. UNIFIED: covers web/API, smart contracts, DeFi, SaaS, LLM red-teaming, all platforms."
metadata:
  hermes:
    tags: [bug-bounty, security, web, api, blockchain, defi, saas, redteam, audit]
version: 3.2.2
---

# Bug Bounty — UNIFIED Authorized Security Research

> **Path Conventions** (portable across systems):
> - `$BB_DATA` = bug bounty data root (default: `D:/data hermes/bug-bounty/`)
> - `$TOOLKIT` = toolkit scripts root (default: `D:/data hermes/bug-bounty/bundle/toolkit/`)
> - `$DATA` = general data root (default: `D:/data hermes/`)
> - Set these as env vars or adjust paths to match your system.

> 🧭 **MASTER GUIDE (authoritative, v1.0): `references/agent-kb-bounty-exploit-master.md`
> — READ THIS FIRST on EVERY
> bug bounty / security task.** It is the single source of truth for doctrine (7 hard rules), the Stage 0–7 pipeline,
> scope/recon/vuln-class/DeFi/MPC/LLM-redteam playbooks, verification discipline, Gold-Standard reporting, the
> Phase 5 219-box checklist gate, and §18 session workflow (scope.md + per-target progress.md under
> `$BB_DATA/_progress/<target>\`). Where this SKILL.md body and the master KB conflict, **the master KB wins**.
>
> 🔗 **On-chain / DeFi companion:** `references/onchain-cast-recon.md` — on-chain `cast` recon playbook
> (liveness gate, exchange-rate scaling pitfall, oracle selector probing, Safe-proxy recognition). Load it
> alongside the master KB whenever the target touches contracts.
>
> 📚 **Pitfalls library:** `references/pitfalls-library.md` — every dated failure + the rule it produced.
> Read before Phase 3 and before declaring a target exhausted.
> The rest of this file (and its 736 reference files) remains the long-form detail the KB points into.

**Core loop every task:** Stage 0 payout gate → Stage 1 SCOPE LOCK (hard gate, write scope.md) → Stage 1.5 TARGET-ACCOUNT PROVISIONING (NON-BLOCKING: 30m timebox → degradasi §1.0; PLATFORM portal account = urusan submit, haram memblokir audit; ladder §2A) → Stage 2 recon →
Stage 3 VRT gate BEFORE PoC work → Stage 4 verify/exploit (≥3x repro, Tier-1 evidence) → Stage 4.5 deepdive 17-vector
gate → Phase 5 219-box checklist → Phase 6 severity calibration → Phase 7 final verification → Phase 8 ONE comprehensive PDF → output "FINDING READY FOR REVIEW"
(never "READY TO SUBMIT" without user approval). Zero overclaim: blocked chain = INFORMATIONAL, never HIGH/CRIT.

📡 **ACCOUNT-FIRST EXPLOITATION GATE (v3.2.2):** read `references/account-first-exploitation.md` §1.0 BEFORE Stage 4 — TAKSONOMI: TARGET account (dibutuhkan Stage 4) ≠ PLATFORM account (portal bounty, hanya untuk submit — TIDAK PERNAH memblokir audit). Provisioning non-blocking: 30m → ladder §2A → degradasi (1 akun + vektor vertikal sekarang / OAuth / cron-retry).
Post-mortem 2026-09-10: 8 sessions, ~1 submittable finding — root cause = 100% anonymous testing. HARD RULES:
(1) Stage 4 auth matrix (IDOR A×B) needs ≥2 TARGET accounts in `target-state.json`; provisioning >30m → degradasi §1.0 (1 akun + vektor vertikal SEKARANG, cron-retry akun ke-2) — JANGAN idle nunggu akun. PLATFORM account (portal submit) di luar gate ini
(2) 20/60/20 time budget (recon/exploit/writeup) — if >30% spent with zero authenticated requests → STOP recon, provision now
(3) Authenticated test matrix: IDOR A×B sweep on EVERY mapped endpoint, priv-esc, tenant isolation, business logic, auth-flow abuse
(4) Precondition-pivot: blocked vector → "who gets this precondition legitimately?" → intercept legit flow; format-brute MAX 10 attempts
(5) Chain discipline: 2 weak findings linked = 1 strong report (self-XSS+CSRF=ATO etc.)
(6) State persistence: `_progress/<target>/target-state.json` + `reauth.py` survive context reset — never re-recon, never re-register
(7) §9 self-audit checklist before declaring target exhausted — any unchecked box = NOT exhausted.

📡 **WEB/API + RECON GATE:** before claiming a **subdomain takeover** or a **"leaked key"** from public JS/config blobs, read `references/dns-subdomain-takeover-and-recon-pitfalls.md` — DoH-only DNS triage (local WARP sinkhole lies), can-i-take-over-xyz claimability gate, client-side token ≠ vuln until proven static across sessions, and the by-design noise filters (Faro/Pendo/reCAPTCHA keys, CSP log sinks, Azure `UnsupportedHttpVerb`).

📡 **CORS GATE:** on ANY target with `Access-Control-Allow-Origin` or `Access-Control-Allow-Credentials`, read `references/cors-testing-playbook.md` BEFORE claiming. 6 vectors: arbitrary reflection, regex/suffix/prefix bypass, null origin, XSS+CORS chain, TLS break via HTTP trusted sub, intranet unauthenticated access. Skip by-design (Cloudinary CDN, public API `*`, no-credentials).

📡 **CLIENT-SIDE GATE** (XSS / CSRF / Clickjacking / DOM-based / WebSockets) — read the matching playbook BEFORE claiming any of these classes:
- `references/xss-testing-playbook.md` — reflected/stored/DOM XSS: context-based payloads, filter bypass table, CSP analysis, dangling markup. Severity = proven exfil/ATO chain, never alert() alone. Chrome ≥92: use `print()` in iframe PoCs.
- `references/csrf-testing-playbook.md` — 3-prerequisites check (relevant action + cookie-only session + predictable params), token/SameSite/Referer bypass vectors, JSON API CSRF via `enctype=text/plain`. No impactful action = INFO.
- `references/clickjacking-testing-playbook.md` — frame protection analysis (XFO ALLOW-FROM ignored by Chrome 76+), sandbox frame-bust bypass, Clickbandit. Frameable without sensitive action = INFO.
- `references/dom-based-vulnerabilities-playbook.md` — source→sink taint-flow matrix (16 vuln types), DOM clobbering, postMessage sinks. No sink = not a finding.
- `references/websockets-testing-playbook.md` — WS message tampering (XSS/SQLi via WS), handshake manipulation, CSWSH (cross-site WS hijacking = CSRF on handshake). Unauthenticated WS data = INFO.
All five: blocked/unproven chain = INFORMATIONAL per master KB rule. Raw PortSwigger extracts: `$BB_DATA/_portswigger-extracts\`.

📡 **SERVER-SIDE GATE** (Deserialization / SSTI / Smuggling / Cache / Host Header / Prototype Pollution) — read the matching playbook BEFORE claiming any of these classes:
- `references/deserialization-playbook.md` — language magic-byte markers (PHP `O:4:`, Java `AC ED`/`rO0ABQ`, Ruby `04 08`, Python pickle `80 04`), gadget chains (ysoserial/phpggc), PHAR, magic-method abuse. Signature-valid + no gadget = NOT A FINDING.
- `references/ssti-playbook.md` — polyglot probe `${{<%[%'"}}`, 7*7 engine-ID decision tree (Twig vs Jinja2 `{{7*'7'}}`), per-engine RCE payload table (Jinja2 MRO/globals, Twig `registerUndefinedFilterCallback`, ERB, Freemarker, Mako…). Probe-evaluated-only without engine ID = INFO.
- `references/request-smuggling-playbook.md` — CL.TE / TE.CL / TE.TE timing + differential confirmation, 8 TE obfuscation variants, victim request capture, CL.0, client-side desync, H2.CL/H2.TE downgrade. Timing-only without differential proof = INFO.
- `references/web-cache-poisoning-playbook.md` — unkeyed header probing (Param Miner), cache-key identification, Fat GET/parameter cloaking, Vary abuse, cache buster discipline. Reflection without cached response = INFO.
- `references/host-header-playbook.md` — arbitrary-Host probe, duplicate/indented/absolute-URL override, X-Forwarded-Host chain, reset-poisoning → ATO recipe, routing SSRF. Host reflected but never used = INFO.
- `references/prototype-pollution-playbook.md` — `__proto__`/`constructor.prototype` probes, blind server oracles (status/`json spaces`/charset), client-side gadget scan → DOM XSS, server RCE gadgets (NODE_OPTIONS, EJS `outputFunctionName`). Pollution without gadget chain = LOW.
📡 **AUTH / FLOW GATE** (OAuth / JWT / GraphQL / LLM) — read the matching playbook BEFORE claiming:
- `references/oauth-playbook.md` — flow fingerprinting, redirect_uri bypass matrix (prefix-match, traversal, parser confusion, `localhost.evil-user.net`), state-missing CSRF, code interception, implicit token theft, scope upgrade. Token theft must be proven end-to-end.
- `references/jwt-playbook.md` — `alg:none`, HS256/RS256 confusion, jku/jwk/x5u injection, kid path traversal/SQLi, hashcat `-m 16500` brute-force, unverified claim tampering. Tampered token must actually authenticate.
- `references/graphql-playbook.md` — endpoint discovery, one-line introspection, suggestion enumeration/Clairvoyance, BOLA `product(id:...)`, batch/alias bypass, CSRF on mutations. Complements `references/graphql-attack-patterns.md`.
- `references/llm-attacks-playbook.md` — system prompt extraction, direct/indirect prompt injection, excessive agency/tool abuse, insecure output handling → classic web vuln via LLM. Content-policy jailbreak alone = NOT A FINDING; prove backend impact.
📡 **TOOLING:** `references/essential-skills-playbook.md` — WAF/filter bypass obfuscation matrix (double URL encoding, SQL CHAR(), comment insertion, unicode normalization), Burp Match-Replace workflows. Apply to all other playbooks. Anti-bot browser escalation (Camofox → CloakBrowser): `references/cloakbrowser-stealth-browser.md` — source-level stealth Chromium, Turnstile/FingerprintJS/reCAPTCHA pass, auth→cookie-export workflow for protected targets.

📡 **RESEARCH ARTICLES GATE (v3.1.0):** before claiming ANY vuln class covered by the research-articles compendium playbooks, read the matching `references/articles-*-playbook.md` FIRST — these are distilled from full PortSwigger Research papers (Kettle/Heyes et al.) with literal payloads, SKIP filters, and evidence checklists the standard playbooks don't carry:
- `references/articles-timing-attacks-playbook.md` — single-packet attack, hidden param/header discovery (bottom-quartile methodology), blind JSONi/SSPF probes, scoped SSRF → reverse-proxy exploitation chain (firewall bypass, front-end impersonation), jQuery CSS selector exfil. Timing diff without identified mechanism = INFO.
- `references/articles-parser-waf-bypass-playbook.md` — parser discrepancy round-trips, WAF fingerprint + bypass via HTTP quirks. Blocked chain = INFO.
- `references/articles-saml-auth-tokens-playbook.md` — SAML/signed-token forgery, parser confusion, WS-Fed metadata abuse.
- `references/articles-dom-clobbering-playbook.md` — clobbering gadget chains → DOM XSS; clobber w/o sink = INFO.
- `references/articles-tools-methodology-playbook.md` — Turbo Intruder gate/last-byte racing (reCAPTCHA second-order race), WebSocket Turbo Intruder, custom scanner methodology (smallest-step automation + triage filters), extension patching, Clickbandit. Untriaged scanner output = never report.
- `references/articles-misc-research-playbook.md` — behavioural/visual fuzzing (ZalgoScript unicode-whitespace bypass pattern, modern-engine retest mandatory), researcher craft (breadcrumbs → chase "this makes no sense"). Quirk without sink = INFO.
Rule: research-article technique claims need the article playbook's own evidence checklist satisfied — differential/mechanism/engine-version/normalization checks BEFORE claiming. Raw extracts: `$BB_DATA/_portswigger-extracts\articles\` (15 compendium playbooks total).

> ⛔ **ON-CHAIN / DEFI MANDATORY GATE — read `references/onchain-live-verification.md`
> BEFORE writing any finding.** A vulnerability read from the GitHub repo is **VOID**
> until re-verified against the **deployed** bytecode: resolve proxies
> (`comptrollerImplementation()`, `oracle()`, EIP-1967 slots), pull verified source from
> the explorer API (strip double-braced `SourceCode`), fingerprint unverified bytecode via
> dispatcher selectors + 4byte.directory, then prove the vulnerable path is **reachable**
> with live reads (`getAssetConfig`/staleness, `borrowCaps`, `supplyRewardSpeeds`,
> `totalSupply`). In one real audit this gate killed 3 of 6 findings — both oracle findings
> were based on a stale repo oracle while live ran a completely different dual-oracle with
> staleness+deviation guards, and "no borrow caps" was false (guardian unset ≠ caps unset).
> Slither `impact: High` is a tool label, not severity. `vm.skip(true)` ≠ "Fork Verified".

**ONE SKILL TO RULE THEM ALL.** Full-spectrum security research: web/API pentest, smart contract auditing, DeFi analysis, SaaS bounty hunting, LLM red-teaming, recon, exploit/PoC development, severity assessment, and bounty report writing.

> ⚠️ **NO NEED TO LOAD OTHER SKILL.** This skill absorbs: audit-discipline, bug-bounty-auto, bugcrowd-workflow, bugcrowd-vrt, bugcrowd-researcher-guide, immunefi-workflow, saas-bounty-hunting, smart-contract-audit, smart-contract-audit-lab, defi-exploit-patterns, oracle-security-audit, wallet-extension-security, ai-llm-redteam, anchor-discriminator-attacks, move-sui-audit, rust-solana-audit, ton-blockchain-audit, contract-audit-remote-recon, offensive-security, exploit-builder, immunefi-bounty-master, defi-api-audit, scope-guard, vdp-recon.

## Reference Files
- `references/windows-repo-cleanup.md` — Windows `node_modules` deletion: `cmd /c rmdir /s /q` fix for MSYS "Permission denied" errors

- `references/privy-siws-auth-and-trading-api-testing.md` — Privy SIWS programmatic auth (Python, no wallet needed), Next.js chunk recon for API shape extraction, and perps-DEX trading-engine edge-case test matrix. Read this before any Solana/gaming/betting target gated by Privy auth.

## Triggers
- bug bounty / bugbounty / hunting / hunt target / bounty program
- recon / reconnaissance / enumerate / mapping attack surface
- audit smart contract / dApp security / on-chain finding / solidity review
- exploit / break / PoC / proof of concept / working exploit
- vulnerability / vulnerability class / finding / bug
- web recon / subdomain / port scan / crawl / spider
- injection / SQLi / SSTI / SSRF / XXE / RCE / LFI / IDOR
- report / write-up / vulnerability report / submission
- CVSS / severity / impact assessment
- HackerOne / Bugcrowd / Intigriti / Immunefi / YesWeHack / Code4rena
- scope / in-scope / out of scope / program policy
- triage / dedup / follow-up / dispute
- immunefi / web3 / defi / smart contract / solidity / blockchain
- flashloan / reentrancy / oracle manipulation / bridge hack
- proxy / uninitialized / delegatecall / upgradeable
- foundry / hardhat / slither / echidna / mythril
- SaaS / API / AI features / LLM / prompt injection
- browser wallet / extension security / vault swap
- TON / FunC / Move / Sui / Solana / Anchor

## Inputs
- **target** — asset/scope to work on (domain, repo, contract address, dApp)
- **program** — program name & platform (e.g., "Acme on HackerOne")
- **phase** — scope | recon | analyze | verify | exploit | report | triage (default: auto-detect)

## Role
You are an expert security researcher and exploit developer. Your value is working PoCs, deep analysis, and reports that get accepted.

> **🌍 GLOBAL SCOPE:** This skill applies to ALL security research requests — web/API pentest, smart contract audits, DeFi analysis, SaaS bounty hunting, LLM red-teaming, recon, exploit/PoC development, severity assessment, and bounty report writing. It is NOT limited to explicit "bug bounty" queries. When the user asks to audit, pentest, review, or security-test ANY target, this skill loads and runs.

---

## ⚠️ AUDIT DISCIPLINE — Hard Rules (NEVER VIOLATE)

### Rule 1: Compression Amnesia Guard
SEBELUM mulai deep task, **reload semua security skills** via `skill_view()`. Kalau ada `[SKILL_PRUNED]` → **STOP**, reload dulu, baru lanjut.

### Rule 2: ZERO OVERCLAIM — Skip Trash, Find Real Bugs
**⛔ HARD RULE: JANGAN OVERCLAIM. Skip these ENTIRELY — don't present, don't score, don't PDF:**

| Skip (waste of time) | Why | What to do instead |
|---|---|---|
| **By-design behavior** | Intended feature, not a bug | Move on immediately |
| **Informational** | No real-world impact | Don't present as finding |
| **Requires phishing/social engineering** | Out of scope for technical bounty | Skip unless program explicitly covers it |
| **Public data intentionally shared** | API/products/pricing/categories open by design | Don't waste cycles on it |
| **Missing security headers** | Usually handled by CDN/WAF | Skip unless chains to exploit |
| **CORS wildcard without credentials** | No cookie theft possible | Skip |
| **User enumeration via errors** | Standard behavior everywhere | Skip |
| **Open ports behind auth** | Auth working as designed | Skip |
| **env-config.js with public keys** | Auth0/Stripe/Datadog public by design | Skip |
| **reCAPTCHA site keys (6Le...)** | Embedded in every client-side form by Google's design | Skip |
| **RSA/EC public keys from source maps** | Public keys are PUBLIC — only private keys are secrets | Skip |
| **SRP params/config from source maps** | Client-side SRP params are harmless with server-side validation | Skip without cryptographic proof |
| **Staging URLs in source maps** | Must PROVE reachability first — if DNS→loopback, internal-only | Skip if unreachable |

**🎯 Only present findings that are:**
- ✅ **Truly exploitable** — working PoC with real damage
- ✅ **Impact on data** — PII leak, credential exposure, data modification
- ✅ **Impact on systems** — code injection, config change, RCE
- ✅ **Impact on users** — account takeover, session hijack, privilege escalation
- ✅ **Impact on accounts** — unauthorized access, auth bypass
- ✅ **Impact on dana (financial)** — fund theft, unauthorized transfer, payment tampering

**If you need to EXPLAIN why it's a finding → it's NOT a finding.** Real bugs are obvious from the PoC. Trier will say "and?" if you present informational.

**Self-check before presenting:** *"Would a Bugcrowd triager accept this as P3 or higher? If NO → skip it."*

### Rule 3: No Skip-Ahead — 7-Stage Pipeline
```
Phase 1: SCOPE      → Lock target & rules (HARD GATE — must complete BEFORE anything else)
Phase 1.5: ACCOUNTS → Provision ≥2 TARGET accounts, capture sessions → target-state.json (NON-BLOCKING v3.2.2: 30m → degradasi §1.0; PLATFORM portal account haram blokir)
Phase 2: RECON      → Map full attack surface + DELTA LIST (max 20% of window)
Phase 3: ANALYZE    → Form attack hypotheses
Phase 4: VERIFY     → Prove with working PoC
Phase 4.5: DEEPDIVE → Exhaust ALL angles before presenting
Phase 5: FINAL GATE → 219-box checklist (bug-bounty-report.md)
Phase 6: SEVERITY   → Severity calibration (bug-bounty-report.md)
Phase 7: VERIFICATION → Final check (bug-bounty-report.md)
Phase 8: REPORT     → Write submissions = ABSOLUTE LAST (bug-bounty-report.md)
```
**⛔ MANDATORY: Stage 1 MUST be fully complete before ANY Stage 2+ work begins.** No reconnaissance, no code analysis, no exploitation attempts until scope is locked. User decision tree: "先验证scope → outscope则op2 → inscope则PDF+SS+PoC"
**JANGAN pernah lompat ke Phase 5 sebelum Phase 4.5 selesai.**

### Rule 4: False Positive Gate
SEBELUM klaim finding:
1. Cek by-design / information-only
2. Kompare dengan VRT
3. Test reproducibility dari clean state
4. Verify dari external perspective (bukan internal)

### Rule 5: Persistence Over Premature Surrender + PRECONDITION-PIVOT
Kalau web-app testing blocked by WAF → **PIVOT**, jangan menyerah:
- Infrastructure (S3, pre-prod, third-party APIs)
- JS bundle analysis, client-side config
- Analytics proxy, PaaS SDK key abuse
- Third-party service enumeration
- **PRECONDITION-PIVOT (v3.2.0):** blocked by MISSING precondition (relay state, CSRF token, object ID,
  admin access) → do NOT brute-format it (max 10 attempts). Ask "who gets this precondition legitimately
  and how?" → the legit flow IS the attack surface: run it with a test account and intercept
  (full recipe: `references/account-first-exploitation.md` §5)

### Rule 6: Exhaustive Multi-Finding Per Target (MANDATORY)
When user specifies a time budget per target (e.g., "24 jam per project"):
1. **NEVER stop after first finding** — keep testing ALL attack vectors
2. **When stuck** → deepdive on untested endpoints/techniques
3. **When deepdive exhausted** → cross-check all previous findings for variations
4. **Only when time budget is nearly exhausted** → generate report
5. **ONE comprehensive report per project** containing ALL findings — NOT separate reports per finding

User explicitly corrected: *"Sy kasih waktu temukan Exploit sebanyak mungkin dalam waktu 24 jam. Kalau temuan udh mentok, kamu deepdive, kl udh juga, kamu crosschek ulang, sampai waktu 24 jam tsb tercapai baru kamu generate pdf dgn lengkap."*

---

## Scope & Authorization (mandatory gate)
- Work ONLY on targets the operator owns or has explicit authorization to test.
- Respect program policy: in-scope/out-of-scope assets, testing rules.
- Responsible disclosure: report privately first.
- No fabrication: real tool output or honest blocker disclosure.

### 🚫 PAYOUT GATE — Skip Non-Paying Targets FIRST (Stage 0, before SCOPE)
**Session: Xapo 2026-09-07.** User wasted a session deep-diving a VDP-only target, then said: *"Xapo gkbayar, stop"* / *"Skip Xapo kl gak pay"*.

**RULE: Before ANY recon/analysis, verify the program pays real bounties:**
1. Check Bugcrowd `engagements.json` / bounty-targets-data for `program_type` and payout range
2. VDP (vulnerability disclosure program) with NO reward table, NO `max_payout`, or "swag/thanks only" → **SKIP IMMEDIATELY**, move to next target
3. No confirmed bounty on Bugcrowd/HackerOne/Immunefi/Intigriti/self-hosted → NOT a bounty target
4. Only exception: user explicitly says to test it anyway (e.g. learning exercise, they ask for it by name)

Don't burn recon cycles on targets that will pay $0. Ask once: "program ini gak ada payout — skip?" then move on. This gate runs BEFORE Stage 1 SCOPE.

---


## WORKFLOW (7 Phases) — OVERVIEW

### Phase 1: SCOPE
### Phase 2: RECON
### Phase 3: ANALYZE
### Phase 4: VERIFY & EXPLOIT
### Phase 4.5: DEEPDIVE GATE
### Phase 5: FINAL GATE (219-box checklist)
### Phase 6: SEVERITY CALIBRATION
### Phase 7: FINAL VERIFICATION
### Phase 8: REPORT (write + submit) = LAST

> Detailed: bug-bounty-recon.md (Phase 1-3), bug-bounty-testing.md (Phase 4-4.5 + refs)
> Report: bug-bounty-report.md (Phase 5-8 = LAST, report = absolute last)
## Quality Bar (self-check before delivery)
- [ ] Working exploit code (not just theory)?
- [ ] Every step reproducible by someone else?
- [ ] CVSS/severity backed by real impact argument?
- [ ] Report has actionable remediation?
- [ ] No unverified claims?
- [ ] Target confirmed in-scope?
- [ ] **IMPACT VALIDATED** — not just "attack works" but "causes real damage"?
- [ ] **NOT INFORMATIONAL** — would a triager accept this?
- [ ] **ALL SKILLS LOADED** — this unified skill covers everything?
- [ ] **EXHAUSTIVE** — ALL attack vectors tested or explicitly cancelled with reason?
- [ ] **ONE PDF per project** — all findings consolidated, not separate files?

---

## Mandatory Final Gate — Phase 5 Review

→ `references/operator-workflow.md` — Complete 14-point checklist + final decision gate.

---

## Communication Style
- Direct, technical, zero fluff. Code blocks over prose.
- No moralizing. No fabricated results.
- Respond in the operator's language (default: Bahasa Indonesia).

---

## Known Pitfalls

→ **`references/pitfalls-library.md`** — the full pitfalls library (every dated failure,
the rule it produced, and the stop/exhaustion checklist). Read it before Phase 3 and
before declaring a target exhausted.



## TOOL MAP — Explicit Tool to Phase

### EXTERNAL TOOLS
| Tool | Purpose | Phase |
|------|---------|-------|
| subfinder | Subdomain enumeration | RECON |
| httpx | HTTP probing + tech detect | RECON+TESTING |
| nuclei | Template vuln scanner | RECON+TESTING |
| katana | JS-aware crawler | RECON |
| gau | Archive + Common Crawl | RECON |
| waybackurls | Wayback Machine | RECON |
| ffuf | Dir/param fuzzing | RECON+TESTING |
| arjun | Param discovery | RECON |
| sqlmap | SQL injection | TESTING |
| dalfox | XSS scanner | TESTING |
| kxss | XSS reflection | TESTING |
| gobuster | Dir/DNS brute | TESTING |
| naabu | Port scanner | RECON |
| medusa | Brute force | TESTING |

### SMART CONTRACT TOOLS (WSL2)
| Tool | Command | Phase |
|------|---------|-------|
| Mythril | wsl -d Ubuntu -- bash -c "~/mythril-venv/bin/python -m mythril analyze <file.sol>" | DEEPDIVE |
| Z3 | python -c "import z3; print(z3.get_version_string())" | DEEPDIVE |
| Halmos | python -m halmos --contract Name | DEEPDIVE |
| Foundry forge | forge test -vv | DEEPDIVE |
| Foundry cast | cast disassemble / cast selectors | DEEPDIVE |
| Slither | slither file.sol | DEEPDIVE |
| Aderyn | aderyn dir/ | DEEPDIVE |

### CUSTOM TOOLS (bug-bounty/tools/)
| Tool | Purpose | Phase |
|------|---------|-------|
| ABH hunt.py | Orchestrator (44 scripts) | ALL |
| ABH idor_scanner | IDOR/BOLA | TESTING |
| ABH cors_scanner | CORS misconfig | TESTING |
| ABH jwt_scanner | JWT weakness | TESTING |
| ABH race.py | Race condition | TESTING |
| ABH nosqli | NoSQL injection | TESTING |
| ABH crlf | CRLF injection | TESTING |
| ABH dom_xss | DOM XSS | TESTING |
| ABH bypass_403 | 403 bypass | TESTING |
| ABH oob_listener | OOB callback | TESTING |
| ABH llm_redteam | LLM prompt injection | TESTING |
| spyhunt smuggler | Request smuggling | TESTING |
| spyhunt whatwaf | WAF detection+bypass | TESTING |
| spyhunt pathhunt | Path traversal | TESTING |
| spyhunt sub_output | Subdomain takeover | RECON |
| allforone | Multi-vuln scanner | TESTING |
| ezXSS | Stored XSS verify | TESTING |
| dnsReaper | Subdomain takeover (55 sigs) | RECON |
| JShunter | JS secrets/links | RECON |
| bxss | Blind XSS server | TESTING |

### PHASE CHAIN
```
Phase 0:  Read scope.json -> load main.md + 8 skills
Phase 1:  curl (platform API) + python3 -> scope.json
Phase 2:  subfinder -> httpx -> nuclei (core)
          katana + gau + waybackurls (crawl)
          arjun + ffuf (params)
          naabu + dnsReaper (ports + takeover)
Phase 3:  Read testing.md refs index -> map attack surface
Phase 4:  ABH scripts + sqlmap + dalfox + kxss
          ffuf + gobuster (forced browse)
          spyhunt smuggler + whatwaf
          ezXSS + allforone + bxss
          Mythril + Z3 + Halmos + Foundry (web3)
Phase 5:  humanizer + bug-report-delivery (PDF)
```
