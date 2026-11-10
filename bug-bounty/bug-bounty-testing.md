## PHASE 4-4.5: VERIFY, EXPLOIT & DEEPDIVE + REFERENCE INDEX

> Reference index = EXPLOIT LOOKUP. Find the right playbook for your target.

---

## 🎯 PIVOT STRATEGY — When WAF Blocks Web Attacks

**NEVER accept "no finding" after WAF blocks.** Pivot to:
1. **Infrastructure:** S3 buckets, pre-prod, staging, third-party APIs
2. **JS Bundles:** Source maps, config objects, API keys, debug endpoints
3. **Analytics Proxies:** Datadog, Sentry, Amplitude, PostHog injection
4. **PaaS SDKs:** Firebase, AWS Amplify, LaunchDarkly misconfiguration
5. **Third-Party Services:** Auth0, Cloudinary, Stripe test keys
6. **Non-Cloudflare Services:** CT log enumeration for non-Cloudflare origins
7. **Client-Side:** Deep link schemes, WebView handlers, intent filters, `__NEXT_DATA__` script tag (staff emails, internal URLs, config — see `references/nextjs-nextdata-disclosure.md`), **multi-environment JS bundle key extraction** — prod/dev/staging/mobile subdomains each ship separate bundles with potentially DIFFERENT Segment/Hightouch/Amplitude keys; extract from each (`assets`, `devassets`, `stageassets`, `mobileassets`) — see `references/bitso-2026-complete-session.md`
8. **CMS Backends:** Headless CMS GraphQL/REST APIs (Payload, Strapi, Directus, Contentful) — introspection, login mutations, public queries → `references/payload-cms-graphql-attack-patterns.md`

---

## 🏴 RED TEAM / OFFENSIVE OPS

### Kill Chain (8 Phases)
```
1. RECON → OSINT, subdomain enum, tech fingerprint
2. DISCOVERY → Port scan, service enum, vuln scan
3. EXPLOIT → Initial access, RCE, auth bypass
4. DELIVERY → Payload delivery (phishing, watering hole)
5. POST-EXPLOIT → Priv esc, credential harvest, dump
6. C2 → Command & control infrastructure
7. EXFILTRATION → Data staging, covert channels
8. CLEANUP → Log removal, artifact deletion
```

### C2 Architecture
| Pattern | Stealth | Complexity | Use Case |
|---------|---------|------------|----------|
| Direct | Low | Low | Lab/internal |
| Redirector | Medium | Medium | External engagements |
| Domain Fronting | High | High | Cloud-heavy targets |
| DNS Tunneling | High | High | Restricted egress |
| P2P | Very High | Very High | APT simulation |

### MITRE ATT&CK Quick Map
```
T1566.001 → Spearphishing | T1059.001 → PowerShell | T1053.005 → Scheduled Task
T1547.001 → Registry Run Keys | T1055 → Process Injection | T1003 → OS Credential Dumping
T1021 → Remote Services (lateral) | T1048 → Exfil alt protocol | T1070 → Indicator Removal
```

### OPSEC Checklist (Pre-Engagement)
- [ ] VPN/proxy chain verified (no DNS leaks)
- [ ] Separate attacker identity (not personal)
- [ ] Scope JSON signed and valid_until checked
- [ ] C2 infrastructure spun up and tested
- [ ] Payload obfuscation applied
- [ ] Logging infrastructure ready
- [ ] Clean-up scripts prepared

**Hard rules:** ALL operations require scope.json. Document every action. Never leave persistence without authorization. C2 callbacks encrypted only.

---


---

## 🏥 IMMUNEFI — Prohibited Behaviors (32 Rules = Ban)

**Whitehat:** No mainnet testing, no misrepresentation, no automated mass traffic, no social engineering, no public disclosure before fixed+paid, no duplicate submissions, no AI-generated reports, no multiple accounts, no KYC fraud.
**Project:** No "no fix no pay" then stealth fix, no routing around Immunefi, no closing reports without evidence, no SLA breaks.
**Enforcement:** Forfeiture + loss of access + zero payout.
→ Full rules: `references/immunefi-rules.md`

### PoC Requirements (MANDATORY)
- Runnable code: Foundry/Hardhat tests (NOT screenshots)
- Test on mainnet fork, NOT mainnet
- Calculate: tokens at risk × price = funds at risk
- Optimize for MAXIMUM economic damage

### Immunefi PoC Templates
```solidity
// Foundry
contract ExploitTest is Test {
    function setUp() public { vm.createSelectFork("mainnet", BLOCK_NUMBER); }
    function testExploit() public { /* exploit */ }
}
```
```javascript
// Hardhat
await hre.network.provider.request({ method: "hardhat_reset",
    params: [{ forking: { jsonRpcUrl: "RPC_URL", blockNumber: BLOCK_NUMBER }}]});
```
→ Full templates: `references/immunefi-poc.md`

---

## 🌐 DeFi API AUDIT — Off-Chain Layer

**API often MORE vulnerable than contracts.**

### Phase 0: SDK + OpenAPI Recon
```bash
npm search <protocol>; npm pack @scope/sdk; tar xzf *.tgz  # Extract ABIs, endpoints, auth
curl -sk https://api.domain/v1/openapi.json  # Enumerate ALL endpoints
```

### Vulnerability Classes
- **IDOR:** Sequential IDs, no auth → HIGH
- **WebSocket Hijacking:** Subscribe to ANY user without auth → HIGH (front-running chain)
- **CORS Wildcard on User Data:** `Access-Control-Allow-Origin: *` on private endpoints → MEDIUM
- **Infrastructure Disclosure:** Admin endpoints exposed publicly → MEDIUM-HIGH
- **Mass Assignment:** Extra fields accepted → MEDIUM-HIGH

### Severity Overclaim Prevention (NON-NEGOTIABLE)
```
Direct fund theft (replay, forge tx) → CRITICAL
Write IDOR that PERSISTS (referral overwrite) → HIGH
Read IDOR (user data, positions) → HIGH (info disclosure)
API key hashes / public addresses leaked → MEDIUM
Write IDOR that DOESN'T persist (server reject) → MEDIUM
```
**Common traps:** API key addresses ≠ private keys. READ-only endpoints = info disclosure, NOT fund theft. Test persistence before claiming write IDOR.
→ Full methodology: `references/neony-exchange-findings.md`

---


---

## SMART CONTRACT / WEB3 WORKFLOWS

### Solidity / EVM Audit
→ `smart-contract-audit--*.md` — Methodology + deep security analysis
→ `smart-contract-audit-lab--*.md` — Toolchain setup (Foundry, Slither, Halmos, Mythril, Echidna, Z3)
→ `defi-exploit-patterns--*.md` — AMM manipulation, StableSwap, integer overflow
→ `oracle-security-audit--*.md` — Timelock bypass, staleness, price bounds
→ `contract-audit-remote-recon--*.md` — Audit via Blockscout API + RPC

**Tools:**
```
Slither    → Static analysis (CFG, reentrancy, overflow)
Aderyn     → AST-based static analysis
Mythril    → Symbolic execution
Echidna    → Fuzzing / property testing
Medusa     → Alternative fuzzer
Halmos     → Formal verification (symbolic testing)
Z3         → Constraint solver
Foundry    → Build + test + fork
```

**Immunefi Severity (quick):**
- CRITICAL: Direct drain, permanent loss, protocol insolvency
- HIGH: Temporary DoS of critical function, contract upgrade without timelock
- MEDIUM: Rug pull potential, oracle failure, MEV extraction
- LOW: Griefing, unbounded gas, non-critical function DoS
- INFO: Gas optimization, best practice violations

### Solana / Anchor
→ `rust-solana-audit--*.md` — Rust/Solana DeFi audit
→ `anchor-discriminator-attacks--*.md` — Discriminator shadowing

### Move / Sui
→ `move-sui-audit--*.md` — Compiler bugs, match-arm, gas underflow

### TON (FunC / Tolk)
→ `ton-blockchain-audit--*.md` — TON contract vulnerabilities

### Browser Wallets / Extensions
→ `wallet-extension-security--*.md` — Static IV, vault swap, cipher analysis

### Remote Contract Recon
→ `contract-audit-remote-recon--*.md` — Blockscout API + direct RPC

---


---

## REFERENCE FILES INDEX (736 files) [updated 2026-09-15]

## OpenEMR / PHP-Core Advisory Techniques (additional attack variants — Phase 0C)
```
read_file('skills/security/exploit-cookbook/references/openemr-php-advisory-techniques.md')
```
> **⛔ RULE: additive. Loaded alongside the "2026 Public Disclosures" bundle; does not alter phase order,
> budget or eviction.** Use as a variant checklist per vuln class: §A IDOR/ACL (write-vs-read gaps,
> case-sensitive guard bypass, criteria-key injection, ACL-map fail-open), §B escaping-context XSS
> (`text()` in attribute/JS context, `json_encode` without HEX flags, XSLT `@*`), §C traversal/
> file write-read (per-vendor guard parity, `file_path`, LFI router), §D eval/backup/import/XInclude/
> jwks_uri-SSRF, §E legacy dispatcher abuse, §F auth/session/2FA, §G SQLi contexts (ORDER BY, `_sort`,
> bitwise, pg `E''`, Firebird NUL), §J PHP-core/ext surface, §M screen -> variant probe matrix.
> **Still gated by `hunt-dispatch` Step 0 + `triage-validation`** (soft-404 control, body-diff, negative
> control). These are vectors, not findings.


> Load via: read_file('skills/security/bug-bounty/references/{filename}')

## REFERENCE FILES (COMPLETE INDEX — 736 files) [updated 2026-09-15]

> ⚠️ **ALL files below are reachable via explicit backtick paths.** Agent MUST load by filename, never by glob. If a file is not listed here, it does not exist.

### Core Methodology
- `references/agent-kb-bounty-exploit-master.md` — **MASTER GUIDE** — 7 hard rules, Stage 0–7 pipeline, scope/recon/vuln-class/DeFi/MPC/LLM-redteam playbooks, verification discipline, Gold-Standard reporting, Stage 7 14-point gate. **READ FIRST on EVERY task.**
- `references/pitfalls-library.md` — Every dated failure + the rule it produced. Read before Phase 3 and before declaring exhausted.
- `references/pitfalls-discipline.md` — Evidence ladder, 2-strike rule, time-box.
- `references/target-viability-criteria.md` — Methodology: when to invest vs when to pivot. Decision matrix.
- `references/playbook-authoring-guide.md` — How to write playbook files. Methodology reference.
- `references/account-first-exploitation.md` — §1.0 taxonomy: TARGET account ≠ PLATFORM account. Auth matrix, precondition-pivot, state persistence.
- `references/advanced-vuln-vectors-2026.md` — OAuth bypass, cookie tossing, JWT alg confusion, LDAP/XSLT injection, prototype pollution, SSTI via error pages, WebSocket frame attacks, signature replay, sandwichable logic, slippage manipulation, minOut validation.
- `references/vuln-classes.md` — Web/API vulnerability classes taxonomy.
- `references/scope-validation.md` — Scope validation gate.
- `references/operator-workflow.md` — Stage 7 final gate checklist (14 points).

### Recon & Discovery
- `references/recon.md` — Recon methodology: passive, active, prioritization.
- `references/recon-program-info-and-auth-probes.md` — Program info extraction + auth endpoint probing.
- `references/subdomain-enumeration.md` — Subdomain enumeration techniques.
- `references/cloud-infra-recon-patterns.md` — Cloud infrastructure recon (S3, GCP, Azure).
- `references/infrastructure-pivot-patterns.md` — Non-Cloudflare service discovery.
- `references/dns-subdomain-takeover-and-recon-pitfalls.md` — DoH-only DNS triage, can-i-take-over-xyz claimability gate, client-side token pitfalls.
- `references/js-bundle-recon.md` — JavaScript bundle analysis, source map extraction.
- `references/source-map-analysis.md` — Source map deep analysis, config extraction.
- `references/auth-flow-recon-playbook.md` — Authentication flow reconnaissance.
- `references/blockchain-gaming-recon.md` — Blockchain gaming target recon.
- `references/mobile-app-bundle-recon.md` — React Native/Expo bundle analysis.
- `references/nextjs-nextdata-disclosure.md` — Next.js `__NEXT_DATA__` info disclosure (emails, config, lockout settings).
- `references/recaptcha-signup-probes.md` — reCAPTCHA signup enumeration probes.
- `references/security-txt-mass-scan.md` — Security.txt mass scan pipeline (Tranco top-1M).
- `references/defillama-target-discovery.md` — DeFiLlama new-protocol target discovery (listedAt <1yr + TVL>$10M).
- `references/bugcrowd-brief-scraping.md` — Bugcrowd brief/program page scraping.

### Research Articles (PortSwigger Compendium)
- `references/articles-timing-attacks-playbook.md` — Single-packet attack, hidden param discovery, blind JSONi/SSPF, scoped SSRF → reverse-proxy chain, jQuery CSS selector exfil.
- `references/articles-parser-waf-bypass-playbook.md` — Parser discrepancy round-trips, WAF fingerprint + bypass via HTTP quirks.
- `references/articles-saml-auth-tokens-playbook.md` — SAML/signed-token forgery, parser confusion, WS-Fed metadata abuse.
- `references/articles-dom-clobbering-playbook.md` — Clobbering gadget chains → DOM XSS; clobber w/o sink = INFO.
- `references/articles-tools-methodology-playbook.md` — Turbo Intruder gate/last-byte racing, WebSocket Turbo Intruder, custom scanner methodology, Clickbandit.
- `references/articles-misc-research-playbook.md` — Behavioural/visual fuzzing (ZalgoScript unicode-whitespace bypass), researcher craft.
- `references/articles-cache-attacks-playbook.md` — Cache attack patterns (web cache deception, cache poisoning variants).
- `references/articles-cors-origin-playbook.md` — CORS origin bypass techniques, parser differentials.
- `references/articles-csp-bypass-playbook.md` — Content Security Policy bypass vectors.
- `references/articles-css-exfil-xsleak-playbook.md` — CSS exfiltration, cross-site leak (XS-Leak) via CSS selectors.
- `references/articles-proto-pollution-playbook.md` — Prototype pollution gadget chains, server-side RCE via pollution.
- `references/articles-race-conditions-playbook.md` — Race condition exploitation, single-packet techniques.
- `references/articles-smuggling-desync-playbook.md` — HTTP request smuggling, desync attacks, H2.CL/H2.TE downgrade.
- `references/articles-template-injection-playbook.md` — Server-Side Template Injection (SSTI) deep-dive, polyglot probes, per-engine RCE.
- `references/articles-xss-vectors-playbook.md` — Advanced XSS vectors, filter bypass, CSP-aware payloads.

### Vulnerability-Specific Playbooks (Web/API)
- `references/xss-testing-playbook.md` — Reflected/stored/DOM XSS: context-based payloads, filter bypass table, CSP analysis, dangling markup.
- `references/csrf-testing-playbook.md` — 3-prerequisites check, token/SameSite/Referer bypass, JSON API CSRF.
- `references/clickjacking-testing-playbook.md` — Frame protection analysis, sandbox frame-bust bypass, Clickbandit.
- `references/dom-based-vulnerabilities-playbook.md` — Source→sink taint-flow matrix (16 vuln types), DOM clobbering, postMessage sinks.
- `references/websockets-testing-playbook.md` — WS message tampering, handshake manipulation, CSWSH.
- `references/deserialization-playbook.md` — Language magic-byte markers, gadget chains (ysoserial/phpggc), PHAR, magic-method abuse.
- `references/ssti-playbook.md` — Polyglot probe, 7*7 engine-ID decision tree, per-engine RCE payload table.
- `references/request-smuggling-playbook.md` — CL.TE/TE.CL/TE.TE timing + differential, 8 TE obfuscation variants, H2.CL/H2.TE downgrade.
- `references/web-cache-poisoning-playbook.md` — Unkeyed header probing (Param Miner), cache-key identification, Fat GET/parameter cloaking.
- `references/web-cache-deception-complete.md` — Cache poisoning, CDN-specific attacks.
- `references/host-header-playbook.md` — Arbitrary-Host probe, duplicate/indented/absolute-URL override, X-Forwarded-Host chain, reset-poisoning → ATO.
- `references/prototype-pollution-playbook.md` — `__proto__`/`constructor.prototype` probes, blind server oracles, client-side gadget scan → DOM XSS, server RCE gadgets.
- `references/oauth-playbook.md` — Flow fingerprinting, redirect_uri bypass matrix, state-missing CSRF, code interception, implicit token theft, scope upgrade.
- `references/jwt-playbook.md` — `alg:none`, HS256/RS256 confusion, jku/jwk/x5u injection, kid path traversal/SQLi, hashcat brute-force.
- `references/graphql-playbook.md` — Endpoint discovery, introspection, suggestion enumeration/Clairvoyance, BOLA, batch/alias bypass, CSRF on mutations.
- `references/graphql-attack-patterns.md` — GraphQL API attacks (error-based enumeration, reCAPTCHA null-token bypass).
- `references/llm-attacks-playbook.md` — System prompt extraction, direct/indirect prompt injection, excessive agency/tool abuse, insecure output handling.
- `references/saml-exploitation-patterns.md` — SAML SSO: key extraction from JS bundles, assertion signing, relay state bypass, ACS endpoint testing.
- `references/payload-cms-graphql-attack-patterns.md` — Payload CMS GraphQL: introspection, `loginUser`/`forgotPasswordUser` mutations, lockout bypass.
- `references/waf-bypass-cdn-origin.md` — WAF bypass via CDN origin discovery, direct IP access.
- `references/cdn-waf-bypass-playbook.md` — CDN/WAF bypass techniques, origin IP discovery.
- `references/cdn-waf-bypass-nykaa.md` — Nykaa CDN/WAF bypass case study.
- `references/essential-skills-playbook.md` — WAF/filter bypass obfuscation matrix (double URL encoding, SQL CHAR(), comment insertion, unicode normalization), Burp Match-Replace workflows.
- `references/cloakbrowser-stealth-browser.md` — CloakBrowser: source-level stealth Chromium, Turnstile/FingerprintJS/reCAPTCHA pass, auth→cookie-export workflow.

### Access Control & Authentication
- `references/access-control-complete.md` — IDOR, BOLA/BFLA, privilege escalation.
- `references/authentication-complete.md` — Auth attacks, OAuth, JWT, MFA bypass.
- `references/cors-findings.md` — CORS misconfiguration patterns.
- `references/cors-testing-playbook.md` — 6 CORS vectors: arbitrary reflection, regex/suffix/prefix bypass, null origin, XSS+CORS chain, TLS break via HTTP trusted sub, intranet unauthenticated access.
- `references/keycloak-attack-patterns.md` — Keycloak enumeration & attacks.
- `references/privy-siws-auth-and-trading-api-testing.md` — Privy SIWS programmatic auth (Python, no wallet needed), Next.js chunk recon, perps-DEX trading-engine edge-case test matrix.
- `references/privy-siws-auth-bypass.md` — Privy SIWS auth bypass techniques, signature manipulation.

### Injection & Code Execution
- `references/sql-injection-complete.md` — SQLi, blind, UNION, time-based, OOB.
- `references/nosql-injection-complete.md` — MongoDB, CouchDB, Redis, Elasticsearch.
- `references/os-command-injection-complete.md` — OS command injection, reverse shells.
- `references/file-path-traversal-complete.md` — Directory traversal, HTTP smuggling, CORS.
- `references/ssrf-complete.md` — SSRF, cloud metadata, filter bypass, Gopher.
- `references/xxe-complete.md` — XXE, blind, SVG upload, DOCX/XLSX, DoS.
- `references/info-disclosure-complete.md` — Source code, debug, SSRF, SSTI, cloud metadata.
- `references/analytics-data-injection.md` — Analytics proxy injection (Segment, Amplitude, Mixpanel).
- `references/segment-write-key-escalation.md` — Segment key escalation → write to any field.

### Business Logic & Race Conditions
- `references/logic-flaws-complete.md` — Business logic, race conditions, payment tampering.
- `references/race-conditions-complete.md` — TOCTOU, single-packet attack, limit overrun.
- `references/advanced-vuln-vectors-2026.md` — (listed above in Core — also covers sandwichable logic, slippage manipulation, minOut validation).

### Platform Workflows — Bugcrowd
- `references/bugcrowd-workflow--tier-methodology.md` — Tier-based methodology (Tier 1/2/3 target selection).
- `references/bugcrowd-workflow--vrt-analysis-workflow.md` — VRT analysis workflow, priority mapping.
- `references/bugcrowd-workflow--recon-tools-patterns.md` — Recon tools + patterns for Bugcrowd targets.
- `references/bugcrowd-workflow--sourcemap-recon.md` — Source map recon on Bugcrowd targets.
- `references/bugcrowd-workflow--chipotle-program.md` — Chipotle program workflow.
- `references/bugcrowd-workflow--aurory-program.md` — Aurory (Solana gaming) program workflow.
- `references/bugcrowd-workflow--rapyd-program.md` — Rapyd (fintech) program workflow.
- `references/bugcrowd-workflow--nasa-vdp-program.md` — NASA VDP program workflow (18.2KB — comprehensive).
- `references/bugcrowd-workflow--klaviyo-recon-pattern.md` — Klaviyo recon pattern (14KB — deep SaaS recon).
- `references/bugcrowd-workflow--atlassian-marketplace-pattern.md` — Atlassian Marketplace pattern (9.5KB — Jira/Confluence cloud).
- `references/bugcrowd-workflow--bitso-engagement-analysis.md` — Bitso engagement analysis.
- `references/bugcrowd-workflow--erc4626-vault-patterns.md` — ERC4626 vault patterns.
- `references/bugcrowd-workflow--oft-layerzero-patterns.md` — OFT/LayerZero cross-chain patterns.

### Platform Workflows — SaaS Bounty Hunting
- `references/saas-bounty-hunting--auth-endpoint-testing-patterns.md` — Auth surface testing (already referenced in SKILL.md body).
- `references/saas-bounty-hunting--jira-cloud-endpoints.md` — Jira/Atlassian cloud endpoints (already referenced).
- `references/saas-bounty-hunting--ai-chatbot-attack-surface.md` — AI features attack surface (already referenced).
- `references/saas-bounty-hunting--appsheet-audit-methodology.md` — Low-code platform audit (already referenced).
- `references/saas-bounty-hunting--browserbase-vs-chrome.md` — Browser tool comparison (1.6KB).
- `references/saas-bounty-hunting--cleanliness-report-app-audit.md` — Cleanliness report app audit (2.8KB).
- `references/saas-bounty-hunting--crowdproof-session-2026-08-27.md` — CrowdProof session archive (5.7KB).
- `references/saas-bounty-hunting--atmail-session-2026-08-28.md` — Atmail session archive (4.8KB).
- `references/saas-bounty-hunting--bitso-session-2026-08-29.md` — Bitso session archive (6.3KB).
- `references/saas-bounty-hunting--fireblocks-2026-09-02-findings.md` — Fireblocks findings (Sep 2, 2026).
- `references/saas-bounty-hunting--fireblocks-2026-09-findings.md` — Fireblocks findings (Sep 2026, broader).

### Platform Workflows — Immunefi
- `references/immunefi-recon-workflow.md` — Proven recon workflow: program discovery, 5-step single-target recon, known top programs, pitfalls.
- `references/immunefi-program-discovery.md` — Program listing methods, tier data, aggregator sources.
- `references/immunefi-rules.md` — Platform rules, SLAs, 32 prohibited behaviors.
- `references/immunefi-severity.md` — Severity Classification System v2.2.
- `references/immunefi-poc.md` — PoC guidelines, templates. **→ Also read `immunefi-workflow--poc-templates.md` for Foundry template code.**
- `references/immunefi-workflow--poc-templates.md` — Foundry/Hardhat PoC templates (ready-to-use code). Complements `immunefi-poc.md`.

### Platform Workflows — YesWeHack & HackenProof
- `references/yeswehack-workflow.md` — Public API enumeration (no auth), scope/policy/bounty extraction, scope_type filtering, URL-encoding pitfalls.
- `references/hackenproof-workflow.md` — Platform URL patterns, program discovery (HTML scrape), scope extraction.

### Web3 / Blockchain — General
- `references/web3.md` — Web3 bug bounty: smart contracts, dApps, on-chain.
- `references/web3-dapp-backend.md` — Off-chain/backend API security for dApps.
- `references/web3-vuln-patterns.md` — Proxy, reentrancy, flashloan, oracle, bridge, MEV patterns.
- `references/web3-writeups.md` — Top bounty writeups ($10M-$560K).
- `references/web3-tools.md` — Foundry, Hardhat, Slither, Echidna, Mythril.
- `references/web3-tools-solana.md` — Solana BPF decompilation (WSL required).
- `references/web3-learning.md` — Web3 security learning roadmap.
- `references/solflow-integration.md` — SolFlow call-graph visualization.

### Web3 / Blockchain — Smart Contract Audit
- `references/smart-contract-audit-lab--gates.md` — Audit gates (what must pass before claiming).
- `references/smart-contract-audit-lab--false-positives.md` — False positive patterns, how to avoid them.
- `references/smart-contract-audit-lab--access-control-modifier-mismatch-pattern.md` — Access control modifier mismatch pattern.
- `references/smart-contract-audit-lab--bulk-live-recon.md` — Bulk live recon via Blockscout API.
- `references/smart-contract-audit-lab--foundry-monorepo-slither-fix.md` — Foundry monorepo + Slither fix.
- `references/smart-contract-audit-lab--mythril-python314-install-fix.md` — Mythril Python 3.14 install fix.
- `references/smart-contract-audit-lab--mythril-windows-native-install.md` — Mythril Windows native install (5.2KB).
- `references/smart-contract-audit-lab--windows-audit-tool-status.md` — Windows audit tool status (4.5KB).
- `references/smart-contract-audit-lab--windows-wsl-install-notes.md` — Windows WSL install notes.
- `references/smart-contract-audit-lab--z3-formal-verification.md` — Z3 formal verification (6.6KB).

### Web3 / Blockchain — Contract Audit Remote Recon
- `references/contract-audit-remote-recon--jackpot-dos-verification.md` — Jackpot DOS verification via Blockscout.
- `references/contract-audit-remote-recon--pk-leak-scan.md` — Private key leak scan.
- `references/contract-audit-remote-recon--prelaunch-detection-biaohui.md` — Pre-launch detection.
- `references/contract-audit-remote-recon--uponzi-blockscout-rpc.md` — Uponzi Blockscout RPC analysis (6.5KB).

### Web3 / Blockchain — DeFi Exploit Patterns
- `references/defi-exploit-patterns--gamefi-attack-recipes.md` — GameFi attack recipes (6.5KB).
- `references/defi-exploit-patterns--gamefi-infrastructure.md` — GameFi infrastructure attacks (3.8KB).
- `references/defi-web-static-sweep.md` — DeFi web static sweep (4.8KB).
- `references/compound-v2-fork-analysis.md` — Compound V2 fork analysis (4.6KB).
- `references/fork-diff-audit.md` — Fork diff audit methodology (3.9KB).

### Web3 / Blockchain — Oracle & On-Chain
- `references/oracle-security-audit--termstructure-labs-analysis.md` — TermStructure Labs oracle analysis.
- `references/onchain-cast-recon.md` — On-chain `cast` recon playbook (liveness gate, exchange-rate scaling pitfall).
- `references/onchain-live-verification.md` — On-chain live verification gate (proxy resolution, deployed bytecode, reachable-path proof).
- `references/onchain-token-side-audit.md` — On-chain token side audit (7.2KB).

### Web3 / Blockchain — Rust/Solana
- `references/rust-solana-audit--blackbox-onchain-analysis.md` — Blackbox on-chain analysis (8.5KB).
- `references/rust-solana-audit--bulk-case-study.md` — Bulk case study (3.4KB).
- `references/rust-solana-audit--pdf-reporting-workflow.md` — PDF reporting workflow (3.6KB).

### Web3 / Blockchain — TON
- `references/ton-blockchain-audit--torch-finance-case-study.md` — Torch Finance TON case study (3.8KB).

### Web3 / Blockchain — Privy Auth
- `references/privy-siws-auth-and-trading-api-testing.md` — (listed above in Auth section).
- `references/privy-siws-auth-bypass.md` — (listed above in Auth section).

### CDN/WAF Bypass
- `references/cdn-waf-bypass-playbook.md` — CDN/WAF bypass techniques (3.1KB).
- `references/cdn-waf-bypass-nykaa.md` — Nykaa case study (2.7KB).
- `references/waf-bypass-cdn-origin.md` — WAF bypass via CDN origin (3KB).

### Reporting & Validation
- `references/reporting.md` — Report structure, CVSS scoring, triage, reportlab PDF pipeline, evidence directory structure.
- `references/pre-submission-verification.md` — Pre-submission checklist: watermark/PII detection, VRT classification, platform-specific submission guides.
- `references/verification-and-poc.md` — PoC principles + reproduction templates.
- `references/god-eye-validation.md` — False positive table + escalation path.
- `references/viability-gate.md` — 5-min CDN/WAF check + decision matrix.
- `references/humanize-screenshots.md` — Humanize gate, screenshot standards.
- `references/pdf-generation-pitfalls.md` — PDF generation pitfalls (reportlab, Pillow RGBA, MSYS paths).
- `references/tooling.md` — Standard tools + ethical usage.

### Tool Failure & Troubleshooting
- `references/tool-failure-pitfalls.md` — Documented real-world tool failures: browser CDP connection refused, DuckDuckGo rate limiting after ~10 queries, web search becoming empty, cached HTML extraction patterns. Includes recovery commands, fallback methods, and the exact errors that trigger them.
- `references/tool-installation-windows.md` — Windows tool install guide, 30+ tools, pitfalls, audit script.
- `references/windows-repo-cleanup.md` — Windows `node_modules` deletion: `cmd /c rmdir /s /q` fix for MSYS "Permission denied" errors.

### Session Archives (Historical — for pattern reference)
- `references/arlo-session-2026-08-27.md` — Arlo session archive (3.5KB).
- `references/arlo-session-techniques.md` — Arlo session techniques (6.1KB).
- `references/upscrolled-session-2026-08-31.md` — UpScrolled session archive (3KB).
- `references/upscrolled-session-2026-09.md` — UpScrolled Sep 2026 findings.
- `references/bitso-2026-findings.md` — Bitso findings.
- `references/bitso-2026-complete-session.md` — Bitso full session archive (multi-env key extraction, exhausted verdict).
- `references/chime-2026-findings.md` — Chime Financial: geo-blocks, event router, HeyMarvin multi-stack, CSP analysis.
- `references/fireblocks-2026-findings.md` — Fireblocks H1 + Bugcrowd MBB: H1 failures, MPC-lib audit, scope verification (10.7KB).
- `references/adafruit-2026-findings.md` — Adafruit exhaustive API data dump audit: 5 findings, 12-page PDF.
- `references/kinsta-2026-findings.md` — Kinsta GraphQL unauth mutations, reCAPTCHA bypass, Discourse enumeration.
- `references/nasa-vdp-findings.md` — NASA VDP findings (8.8KB).
- `references/neony-exchange-findings.md` — Neony exchange findings.
- `references/program-luno-og.md` — Luno OG program notes.

### CMS & Platform-Specific
- `references/wordpress-admin-attack-surface.md` — WordPress admin attack surface.
- `references/wordpress-vip-testing.md` — WordPress VIP testing.
- `references/liferay-dxp-testing.md` — Liferay DXP testing (1.1KB).
- `references/cantina-bounty-scraping.md` — Cantina bounty page scraping (curl + RSC payload extraction).

### AI / LLM
- `references/ai-agents.md` — AI agent security references.

### Batch & Workflow
- `references/batch-self-hosted-bounty-workflow.md` — Excel-driven multi-target bounty audit: parse sheet, filter active, per-target 24h exhaustive cycle, ONE PDF per project.

### Duplicate Consolidation
- **Fireblocks findings** — 3 overlapping files exist. Prefer `fireblocks-2026-findings.md` (10.7KB, most comprehensive, H1+Bugcrowd). The other two (`saas-bounty-hunting--fireblocks-2026-09-02-findings.md`, `saas-bounty-hunting--fireblocks-2026-09-findings.md`) are subsets — read only if first lacks detail on a specific finding.
- **Immunefi PoC** — `immunefi-poc.md` (guidelines/templates) and `immunefi-workflow--poc-templates.md` (Foundry/Hardhat code) are **complementary**. Read BOTH when writing PoC: first `immunefi-poc.md` for rules, then `immunefi-workflow--poc-templates.md` for code.
**Problem:** All `browser_navigate` calls return HTTP 500 from localhost:9377 with CDP connection refused. **Recovery:** 
- Use `execute_code` for API testing that needs token lifecycle (bypasses subagent timeouts)
- Use `web_search`/`web_extract` for public program enumeration (faster than browser)
- Use `terminal` for CLI tool installation and verification (see `references/tool-installation-windows.md`)
- Use `skill_view` for skill content without browser
- Use `memory` for user preferences without browser
- **CloakBrowser fallback (stealth, scripted):** when browser tool/Camofox is down OR the
  target sits behind Turnstile/FingerprintJS/reCAPTCHA/Kasada, drive a real stealth
  Chromium from Python — `pip install cloakbrowser` (installed v0.5.10, binary cached,
  launch verified). Drop-in Playwright API: `from cloakbrowser import launch;
  launch(headless=False, humanize=True, proxy=..., geoip=True)`. Passes Turnstile
  auto, webdriver=false, TLS identical to Chrome. Full recipes (auth→cookie export,
  screenshot POC, persistent profiles): `references/cloakbrowser-stealth-browser.md`.

**Pattern:** When browser fails: switch to `execute_code` for attacks, `web_search` for recon, `terminal` for tool management. Heavy anti-bot target or scripted need → CloakBrowser.

### DuckDuckGo Rate Limiting
**Problem:** `web_search` returns empty results after ~10 queries. **Recovery:**
- Use aggregator endpoints: `bugcrowd.com/engagements.json`, YesWeHack API
- Use programmatic scraping: `curl https://api.yeswehack.com/v2/programs?states=published`
- Use cached data sources: `arkadiyt/bounty-targets-data` for Bugcrowd scope
- Reduce search query frequency; batch similar searches together

**Recovery pattern:** For program discovery, use `curl` → `python3` parsing instead of repeated `web_search`.

### Subagent Timeout on Sequential Workflows
**Problem:** Subagents timeout on sequential API workflows (create account → test endpoints) due to 300s hard limit. **Recovery:**
- Use `execute_code` from main thread for API testing requiring token lifecycle
- Use `terminal` for external script execution (e.g., `$HOME/.hermes/scripts/`) with timeout=300
- Use `process` tool for background tasks with explicit `wait`/`poll` verification

### Tool Installation Debugging (Windows)
**Recovery:** Use `references/tool-installation-windows.md` for Windows-specific tool installation with pitfalls and Go runtime installation requirements.

### Auth0 Enumeration Patterns (Detect Signup Status Without Account)
**Recovery:** Use these API patterns to enumerate Auth0 signup status without requiring credentials:
```bash
# Check if signup is enabled
curl -s "https://TARGET.auth0.com/oidc/register" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('Signup endpoint accessible:', 'enabled' if data.get('signup') else 'disabled')
except:
    print('Endpoint 404 = disabled')
"

# Enumerate enabled grant types
curl -s "https://TARGET.auth0.com/oauth/token" -X POST -d "grant_type=password&client_id=CLIENT_ID&username=probe&password=probe" | python3 -c "
import sys, json
try:
    print(json.dumps(json.loads(sys.stdin), indent=2))
except:
    print('Error response:', sys.stdin.read())
"
```

### Web/API Security
- `references/recon.md` — Recon methodology: passive, active, prioritization
- `references/advanced-vuln-vectors-2026.md` — NEW: OAuth redirect bypass, cookie tossing, JWT alg confusion, privilege escalation, UUID/seq IDOR classification, integer overflow (web2), sandwichable logic, slippage manipulation, minOut validation, signature replay across chains, unchecked return values, LDAP injection, XSLT injection, prototype pollution, SSTI via error pages, WebSocket frame manipulation, trust boundary diagrams, state-change tables, PoC format (expected vs actual), CVSS v3.1 mandatory vector, business impact categories, remediation snippets (Easy/Med/Hard), WAF hardening, false-positive reduction checklist
- `references/vuln-classes.md` — Web/API vulnerability classes
- `references/access-control-complete.md` — IDOR, BOLA/BFLA, privilege escalation
- `references/api-testing-complete.md` — GraphQL, mass assignment, rate limit bypass
- `references/api-webapp-testing.md` — JS bundle recon, unauth endpoints
- `references/authentication-complete.md` — Auth attacks, OAuth, JWT, MFA bypass
- `references/cors-findings.md` — CORS misconfiguration patterns
- `references/file-path-traversal-complete.md` — Directory traversal, HTTP smuggling, CORS
- `references/info-disclosure-complete.md` — Source code, debug, SSRF, SSTI, cloud metadata
- `references/logic-flaws-complete.md` — Business logic, race conditions, payment tampering
- `references/os-command-injection-complete.md` — OS command injection, reverse shells
- `references/race-conditions-complete.md` — TOCTOU, single-packet attack, limit overrun
- `references/sql-injection-complete.md` — SQLi, blind, UNION, time-based, OOB
- `references/ssrf-complete.md` — SSRF, cloud metadata, filter bypass, Gopher
- `references/web-cache-deception-complete.md` — Cache poisoning, CDN-specific attacks
- `references/xxe-complete.md` — XXE, blind, SVG upload, DOCX/XLSX, DoS
- `references/nosql-injection-complete.md` — MongoDB, CouchDB, Redis, Elasticsearch
- `references/analytics-data-injection.md` — Analytics proxy injection
- `references/graphql-attack-patterns.md` — GraphQL API attacks
- `references/nextjs-nextdata-disclosure.md` — Next.js `__NEXT_DATA__` info disclosure (emails, config, lockout settings)
- `references/infrastructure-pivot-patterns.md` — Non-Cloudflare service discovery
- `references/segment-write-key-escalation.md` — Segment key escalation
- `references/tool-installation-windows.md` — Windows tool install guide, 30+ tools, pitfalls, audit script

### Platform-Specific Findings
- `references/keycloak-attack-patterns.md` — Keycloak enumeration & attacks
- `references/yeswehack-workflow.md` — YesWeHack public API recon, scope/policy extraction
- `references/bitso-2026-findings.md` — Bitso bug bounty findings
- `references/bitso-2026-complete-session.md` — Bitso full session archive (all vectors tested, multi-env key extraction, exhausted verdict)
- `references/cantina-bounty-scraping.md` — Cantina (cantina.xyz) bounty page scraping: curl + RSC payload extraction (scope, assets, rewards), Python parsing recipe, gotchas (Windows paths, escaped JSON, minReward:null)
- `references/paxos-cantina-2026-findings.md` — Paxos $1M Cantina bounty: repo status, Slither false-positive patterns for proxy contracts, code review progress, Hardhat compilation fix taxonomy
- [references/fireblocks-2026-findings.md] — Fireblocks H1 + Bugcrowd MBB: H1 failures (F1-F4 Cloudinary/env-config), MPC-lib audit, scope verification
- `references/upscrolled-session-2026-09.md` — UpScrolled VDP15 findings
- `references/chime-2026-findings.md` — Chime Financial recon: geo-blocks, event router, HeyMarvin multi-stack, CSP analysis
- `references/mobile-app-bundle-recon.md` — React Native/Expo bundle analysis
- `references/adafruit-2026-findings.md` — Adafruit exhaustive API data dump audit: 5 findings, 12-page PDF, full product/category API exposure
- `references/kinsta-2026-findings.md` — Kinsta GraphQL unauth mutations, reCAPTCHA bypass, Discourse enumeration, JS bundle internal URL leak

### Batch Workflow
- `references/batch-self-hosted-bounty-workflow.md` — Excel-driven multi-target bounty audit: parse sheet, filter active, per-target 24h exhaustive cycle, ONE PDF per project, evidence rules

### Reporting & Validation
- `references/reporting.md` — Report structure, CVSS scoring, triage, reportlab PDF pipeline, evidence directory structure
- `references/pre-submission-verification.md` — Pre-submission checklist: watermark/PII detection (pixel + text), VRT classification mapping, platform-specific submission guides (Bugcrowd/NASA), final gate checklist
- `references/operator-workflow.md` — Stage 7 final gate checklist
- `references/verification-and-poc.md` — PoC principles + reproduction templates
- `references/pitfalls-discipline.md` — Evidence ladder, 2-strike rule, time-box
- `references/viability-gate.md` — 5-min CDN/WAF check + decision matrix
- `references/scope-validation.md` — Scope validation gate
- `references/god-eye-validation.md` — False positive table + escalation path
- `references/humanize-screenshots.md` — Humanize gate, screenshot standards
- `references/tooling.md` — Standard tools + ethical usage
- `references/ai-agents.md` — AI agent security references

### Web3 / Blockchain
- `references/web3.md` — Web3 bug bounty: smart contracts, dApps, on-chain
- `references/web3-dapp-backend.md` — Off-chain/backend API security
- `references/web3-vuln-patterns.md` — Proxy, reentrancy, flashloan, oracle, bridge, MEV
- `references/web3-writeups.md` — Top bounty writeups ($10M-$560K)
- `references/web3-tools.md` — Foundry, Hardhat, Slither, Echidna, Mythril
- `references/web3-tools-solana.md` — Solana BPF decompilation (WSL required)
- `references/web3-learning.md` — Web3 security learning roadmap
- `references/solflow-integration.md` — SolFlow call-graph visualization
- `references/immunefi-rules.md` — Immunefi platform rules, SLAs
- `references/immunefi-severity.md` — Immunefi Severity Classification v2.2
- `references/immunefi-poc.md` — Immunefi PoC guidelines
- `references/immunefi-recon-workflow.md` — Immunefi target recon: program discovery, 5-step deep recon, known programs, pitfalls
- `references/defillama-target-discovery.md` — DeFiLlama new-protocol target discovery pipeline: API filter, bounty/email enrichment, Windows data-pipeline pitfalls

### Absorbed Skills (content now inline in SKILL.md)

**All absorbed skills' content is inline in SKILL.md sections above.** Their reference files are listed in the REFERENCE FILES section (736 files) [updated 2026-09-15]. When the agent loads `bug-bounty` skill, ALL absorbed skill content is available.

**Round 1 (18 skills absorbed):** audit-discipline, bug-bounty-auto, bugcrowd-workflow, bugcrowd-vrt, bugcrowd-researcher-guide, immunefi-workflow, saas-bounty-hunting, smart-contract-audit, smart-contract-audit-lab, defi-exploit-patterns, oracle-security-audit, wallet-extension-security, ai-llm-redteam, anchor-discriminator-attacks, move-sui-audit, rust-solana-audit, ton-blockchain-audit, contract-audit-remote-recon

**Round 2 (6 skills absorbed):** offensive-security, exploit-builder, immunefi-bounty-master, defi-api-audit, scope-guard, vdp-recon

---


---

## EXTERNAL REPOSITORY REFERENCES (19 repos)

### External Repository References (19 repos integrated 2026-09-15)
- `references/nahamsec/` -- 14 files: basics, vulns, tools, labs, mobile, health, coding, media, setup, talks
- `references/cbh-disclosed-reports/` -- 36 HackerOne/Bugcrowd disclosed reports
- `references/cbh-verification-labs/` -- 25 CVE PoC verification lab files
- `references/cbh-research-scripts/` -- 9 research harvest scripts (h1, bugcrowd, cve)
- `references/cbh-docs/` -- 8 architecture + CLI docs
- `references/cbh-engine/` -- skill_index.json + CLI module
- `references/kingofbb-tips/` -- 7 GraphQL/SSRF/Swagger YAML templates
- `references/tbhm-methodology/` -- 18 methodology chapters (jhaddix) + Fast Testing Checklist + `Project (OD).xmind`
  - The oversized raw path wordlist shipped with this book (`all2.txt`, 1.3M lines / 17MB) was moved OUT of the skill to
    `D:/data hermes/bug-bounty/wordlists/tbhm-all2-paths.txt`; the book PDF was archived to
    `D:/data hermes/bug-bounty/_archive/How-Do-I-shot-Web.pdf` (binary/image PDF the agent cannot read).
    Use the wordlist directly with ffuf/gobuster via that path; do not expect it inside the skill folder.
- `references/edoverflow-cheatsheets/` -- 20 cheatsheets (XSS, SQLi, SSRF, OAuth, etc)
- `references/src-hunter/` -- 267 files: 20 playbooks, 50 payloader dirs, 6 methodology, 141 H1 reports, 3 dicts, 3 templates
- `references/nuclei-templates/` -- 21 Nuclei scan templates (IDOR, LFI, RCE, SQLi, SSRF, SSTI, XSS, XXE)
- `references/spyhunt-payloads/` -- 7 payload files (API, bypasses, proxies, SQLi, SSRF, traversal, XSS)
- `references/awesome-osint/` -- OSINT tools list (250KB)
- `references/awesome-android/` -- Android security resources (29KB)
- `references/awesome-web3/` -- Web3 security resources
- `references/burpsuite-pentester/` -- BurpSuite cheatsheet (5KB)
- `references/cbh-hunt-skills/` -- 58 specialized hunt skills (IDOR, OAuth, GraphQL, SAML, etc)
- `references/cbh-skills/` -- 25 other skills
- `references/cbh-commands/` -- 15 command references


---

## TOOL CHAIN SCRIPTS (Phase 4 workflow)

### Audit Workflow Scripts (in tools/ dir)
- `finding_gate.py` — Finding severity gate (add/list/check findings)
- `chain_builder.py` — Attack chain documentation (build/list/export)
- `finding_report.py` — Per-finding report generation
- `congress.py` — Automated report formatting (bugcrowd/immunefi/custom)
- `evidence_collector.py` — Evidence gathering (headers, body, cookies)
- `remedy_writer.py` — Remediation recommendations (8 vuln types)
- `dry_run_test.py` — Safe exploit chain preview (5 chains, no damage)

### External Port Scanners (Optional — NOT INSTALLED)
- `masscan` — Fast port sweep (⚠️ NOT INSTALLED)
- `nmap` — Detailed port scan (⚠️ NOT INSTALLED)
- `rustscan` — Fast port scan (⚠️ NOT INSTALLED)

### Referenced Skills (loaded by bb-audit-launcher Phase 0)
- `exploit-cookbook` — Exploit playbooks for web2/web3 targets
- `vuln-hunter` — Autonomous vulnerability hunting framework
- `bug-bounty-exhaustive-testing` — 50+ enumeration techniques
- `crypto-library-audit` — Cryptographic library auditing
- `onchain-finding-verification` — On-chain finding verification
- `bb-audit-launcher` — Master audit orchestrator (10 skills, 3 checkpoints)
- `bug-report-delivery` — PDF report generation and delivery
- `humanizer` — Remove AI patterns from reports

---

## INTEGRATED TOOLS (from repos)

### Integrated Tools (from repos)
- `tools/abh/` -- 64 files: hunt.py, intel_engine.py, llm_redteam.py, sast_scan.py, oob_listener.py, lead_board.py, visual_triage.py, waf_encoder.py, spray_orchestrator.sh, etc
- `tools/cbh-engine/` -- 11 files: engine, llm_client, token_manager
- `tools/cbh-scripts/` -- 16 files: validation, test harness
- `tools/dnsReaper/` -- 155 files: full subdomain takeover detection tool (50+ service signatures)
- `tools/ezXSS/` -- 111 files: full blind XSS server (PHP)
- `tools/spyhunt/` -- 177 modules + 150 WAF plugins + 5 smuggler files + 7 payloads
- `tools/bxss/` -- 39 files: blind XSS server (Node.js)
- `tools/jshunter/` -- 34 files: JS endpoint extractor (Go)
- `tools/allforone/` -- Nuclei template updater
- `tools/src-hunter/` -- src-hunter CLI

