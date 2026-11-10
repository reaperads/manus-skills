# Manus Skills — custom skills (packaged for Manus AI)

Upload each ZIP in Manus: **Skills › + Add › Upload a skill**. After upload, type `/` in a Manus chat to pick the skill.

Each ZIP contains one skill folder (SKILL.md + scripts/ + references/ + assets/).
Sources were copied read-only from `~/workspace/custom-skills/`; only SKILL.md frontmatter (`name`/`description`) was added or fixed where missing, and a short "Working principles" block was added near the top of each SKILL.md (full version for hunting/audit/reporting skills, shorter version for other skills).

| ZIP | Skill | Principles | Description |
|---|---|---|---|
| advisory-intel.zip (9 KB) | advisory-intel | full | Use when ingesting vendor advisories into attack playbooks. |
| aem-attack-surface.zip (9 KB) | aem-attack-surface | full | Use when target runs Adobe Experience Manager (AEM) CMS. |
| ai-scanner-detection.zip (11 KB) | ai-scanner-detection | full | Blue-team view of autonomous AI-driven scanning and exploitation: what a defender can observe on the wire (target view) and on a host where such a framework ran (forensic view), our own behavioural de |
| apk-redteam-pipeline.zip (28 KB) | apk-redteam-pipeline | full | End-to-end Android APK red-team pipeline — automated APK acquisition (Play Store + apkpure + apkmirror fallback), jadx decompilation, secret/URL/JWT/Firebase grep, pinned-cert extraction, exported-com |
| argus.zip (10 KB) | argus | full | Argus — the all-seeing scanner suite. Six automated scanners for high-value web + LLM bug classes — CORS misconfiguration (origin reflection / null / credentialed read), CRLF & host-header injection,  |
| artifact-backed-claims.zip (6 KB) | artifact-backed-claims | full | Use when stating a finding. Ship proof, not prose. |
| audit-runbook.zip (4 KB) | audit-runbook | full | Toma's enforced audit SOP. Use at the START of every bug-bounty audit and follow it phase by phase. Ordered checklists per phase with REQUIRED skills/tools and the evidence each must leave on disk. Th |
| authed-webapp-audit.zip (26 KB) | authed-webapp-audit | full | Use when auditing authenticated web apps with test accounts. |
| autonomous-vuln-researcher.zip (39 KB) | autonomous-vuln-researcher | full | Autonomous vulnerability hunting: user gives a target, agent finds and validates vulns without stopping. Orchestrates subagents, uses all security skills, full lifecycle. |
| bb-local-toolkit.zip (92 KB) | bb-local-toolkit | full | Local-tooling companion to the bug-bounty orchestrator — carries the SAME complete bug-bounty workflow, but reach for THIS variant when you also need to resolve where tools, wordlists, and clones are  |
| bb-methodology.zip (65 KB) | bb-methodology | full | Use at the START of any bug bounty hunting session, when switching targets, or when feeling lost about what to do next. Master orchestrator that combines the 5-phase non-linear hunting workflow with t |
| binance-agentic-wallet.zip (87 KB) | binance-agentic-wallet | full | / |
| bot-protected-target-testing.zip (83 KB) | bot-protected-target-testing | full | Use when a web target returns 403/429 for curl, wget, headless browsers or scanners (Akamai, Cloudflare, DataDome, PerimeterX, Imperva) — how to build a harness that actually gets through, how to extr |
| browser-cdp-auth-audit.zip (37 KB) | browser-cdp-auth-audit | full | Use when auditing authenticated web apps via browser CDP. |
| browser-session-daemon.zip (14 KB) | browser-session-daemon | full | Use when a browser session must survive across many steps. |
| bug-bounty.zip (8.6 MB) | bug-bounty | full | Use when hunting bug bounties or authorized testing. UNIFIED: covers web/API, smart contracts, DeFi, SaaS, LLM red-teaming, all platforms. |
| bug-bounty-disclosure.zip (54 KB) | bug-bounty-disclosure | full | Skill end-to-end buat authorized/good-faith bug bounty & coordinated vulnerability disclosure ke developer atau pemilik projek — untuk SEMUA jenis bug (web, API, infra, mobile, cloud, smart contract/w |
| bug-bounty-exhaustive-testing.zip (89 KB) | bug-bounty-exhaustive-testing | full | Enforce exhaustive multi-skill loading during audits. |
| bug-report-delivery.zip (131 KB) | bug-report-delivery | full | PDF bug report: use skill format, deliver to chat. |
| bugbounty-playbook.zip (550 KB) | bugbounty-playbook | full | >- |
| bugbounty-workflow-0xkonde.zip (7 KB) | bugbounty-workflow-0xkonde | full | WORKFLOW BUG BOUNTY — 0xkonde // ZERO-DAY HUNTER |
| bugbounty-workflow-safe.zip (3 KB) | bugbounty-workflow-safe | full | Bug Bounty Workflow — Safe Version |
| bugcrowd-reporting.zip (34 KB) | bugcrowd-reporting | full | Bugcrowd-specific reporting tactics complementing report-writing: VRT category search-and-fallback strategy when no exact match exists, manual severity override when VRT defaults underrate impact, sev |
| business-poc-video-production.zip (10 KB) | business-poc-video-production | full | Use when a vendor/triager asks for a video proof-of-concept for a vulnerability finding. |
| cex-event-contract-audit.zip (8 KB) | cex-event-contract-audit | full | Audit CEX event contracts for settlement bias vectors. |
| cicd-security.zip (6 KB) | cicd-security | full | CI/CD pipeline security hunting — GitHub Actions workflow injection, secret exfiltration, self-hosted runner poisoning, dependency confusion, OIDC token theft, and supply chain attacks. Covers sisakul |
| cloud-bucket-exposure-forensics.zip (9 KB) | cloud-bucket-exposure-forensics | full | Prove a public S3/GCS bucket exposure before reporting. |
| cloud-iam-deep.zip (10 KB) | cloud-iam-deep | full | Cloud IAM red-team attack chain across AWS, Azure, GCP — focused on EXTERNAL exploitation paths and post-credential-discovery privilege analysis. Covers IAM enumeration (aws iam, az role, gcloud iam), |
| cms-security-testing.zip (17 KB) | cms-security-testing | full | Use when auditing CMS targets. CMS vuln patterns. |
| codebase-bounty-review.zip (79 KB) | codebase-bounty-review | full | White-box bug-bounty review of a SOURCE-CODE target (GitHub repo / SDK / node / protocol codebase) where there is no live host to scan and the program forbids live testing. Use when the program's asse |
| credential-attack.zip (9 KB) | credential-attack | full | Password spray methodology for bug bounty — when to do it vs web-vuln hunting, the wordlist-gen + breach-check + osint-employees + spray pipeline, mode selection (http-form / oauth / o365 / okta), rat |
| crypto-library-audit.zip (19 KB) | crypto-library-audit | full | Audit cryptographic libraries and MPC protocol implementations (C/C++/Rust/JS). Find crypto weaknesses: undersized parameters, broken invariants, seed/entropy flaws, arithmetic mode switches. Distinct |
| crypto-ops.zip (36 KB) | crypto-ops | short | Multi-chain crypto operations tooling — HD wallet fleets (generate, monitor, auto-distribute, Tornado Cash deposit/withdraw) and trading/sniper bot porting (EVM↔Solana, Jupiter DEX, LLM decision engin |
| ctf-swarm.zip (1 KB) | ctf-swarm | short | CTF auto-solver: CTFd API poll → model swarm consensus → Docker sandbox → HITL/auto-submit. |
| ctf-templates.zip (2 KB) | ctf-templates | short | CTF solver templates: pwntools + angr skeletons for common binary exploitation patterns. |
| defi-exploit-forensics.zip (32 KB) | defi-exploit-forensics | full | Turn a real exploit transaction into a reusable detection pattern for bug bounty. Use when given tx hashes of past DeFi hacks and asked to study them, when writing an on-chain incident analysis, or wh |
| disclosure-contact-discovery.zip (4 KB) | disclosure-contact-discovery | full | Use when finding/verifying a disclosure contact email. |
| disclosure-followup-evidence.zip (9 KB) | disclosure-followup-evidence | full | Use when a vendor asks for your tested commit or repro. |
| disposable-auth-identity.zip (31 KB) | disposable-auth-identity | full | Use when a test needs disposable accounts for IDOR proof. |
| dnsreaper.zip (2 KB) | dnsreaper | full | Subdomain takeover scanner — 50+ signatures, 50 subs/sec, supports AWS/Azure/Cloudflare/GoDaddy/DigitalOcean/GCP. Use during recon phase for subdomain takeover checks. |
| email-template-injection.zip (9 KB) | email-template-injection | full | Hunt HTML/link injection in transactional email (invitation, password reset, security alert, notification, receipt) where user-controlled fields — display names, org names, subjects — are interpolated |
| enterprise-vpn-attack.zip (7 KB) | enterprise-vpn-attack | full | External SSL VPN / remote-access appliance attack matrix — Cisco ASA/AnyConnect, Fortinet FortiGate/FortiOS, Citrix NetScaler/ADC, Palo Alto GlobalProtect, Pulse Secure / Ivanti Connect Secure, SonicW |
| entitlement-trust-testing.zip (10 KB) | entitlement-trust-testing | full | Use when client-set state unlocks member entitlements. |
| evidence-hygiene.zip (31 KB) | evidence-hygiene | full | Evidence-capture and PoC-redaction discipline for bug-bounty submissions: cookie redaction protocol (which fields to mask, Preview annotation / Burp panel hiding / DevTools workflow), PII black-bar di |
| evm-chain-recon.zip (5 KB) | evm-chain-recon | full | Black-box forensics of unknown EVM chains from public RPC. |
| exchange-trading-api-audit.zip (13 KB) | exchange-trading-api-audit | full | Audit a perp DEX / CEX exchange trading-API logic. |
| exploit-cookbook.zip (346 KB) | exploit-cookbook | full | Proven bounty-paying exploit playbooks with scripts. |
| financial-logic-verification.zip (7 KB) | financial-logic-verification | full | Verify a money-handling product's computed figures against the authoritative domain rules (tax, fees, interest, entitlements) using its own itemised output as the oracle. |
| forexfactory-engagement.zip (20 KB) | forexfactory-engagement | full | Use when auditing Forex Factory / Fair Economy sites (forexfactory.com, cryptocraft.com, energyexch.com, metalsmine.com) or any vBulletin-flex + Cloudflare + reCAPTCHA-Enterprise target — account crea |
| gandalf-solver.zip (2 KB) | gandalf-solver | short | LLM prompt injection solver for Lakera Gandalf (host-locked). Static strategies + adaptive mode. |
| gate-pipeline-end-to-end.zip (4 KB) | gate-pipeline-end-to-end | full | Gate Pipeline End-to-End: Recon → Threat Modeling → Hipotesis → Validasi |
| gate-rule-validasi-hipotesis.zip (3 KB) | gate-rule-validasi-hipotesis | full | Gate Rule: Validasi Hipotesis — Anti Premature Falsification |
| gmgn-contract-dd.zip (40 KB) | gmgn-contract-dd | short | Contract due-diligence score for one token address — contract safety, holder structure and price action combined into a single 0-100 composite, capped by GMGN's own rug label, where every deduction na |
| gmgn-cooking.zip (14 KB) | gmgn-cooking | short | [FINANCIAL EXECUTION] Create and launch meme coins and crypto tokens on launchpads (Pump.fun, FourMeme, Bonk, BAGS, Flap, Klik, Clanker, etc.) via bonding curve fair launch, or query token creation st |
| gmgn-dev-score.zip (6 KB) | gmgn-dev-score | short | >- |
| gmgn-heat-rank.zip (21 KB) | gmgn-heat-rank | short | >- |
| gmgn-holder-analysis.zip (5 KB) | gmgn-holder-analysis | short | Token holder chip analysis — deep analysis of holder structure including chip distribution, entry cost, whale/dev/KOL behavior, risk wallets (rat traders, bundlers, snipers), related wallets, smart mo |
| gmgn-kline-pattern.zip (7 KB) | gmgn-kline-pattern | short | Price-action pattern reading — classifies a token's candles into a named pattern (uptrend channel, breakdown, bounce off the lows, distribution at highs, basing, wide chop, consolidation) and scores i |
| gmgn-market.zip (21 KB) | gmgn-market | short | Get crypto and meme token price charts (K-line, candlestick, OHLCV), trending meme coin rankings by volume, newly launched tokens on launchpads (pump.fun, fourmeme, letsbonk, Raydium, etc.), the hot-s |
| gmgn-narrative.zip (10 KB) | gmgn-narrative | short | Independently research and write an AI-narrative / due-diligence card for a crypto token — the kind of "叙事分析" card that covers what story a token is telling and what's independently verifiable about i |
| gmgn-portfolio.zip (8 KB) | gmgn-portfolio | short | Analyze one or many crypto wallets by address — holdings, batch realized/unrealized P&L, win rate, trading history, performance stats, specific token balance, and tokens created by a developer wallet  |
| gmgn-skills.zip (3 KB) | gmgn-skills | short | Use when querying GMGN on-chain data or trading meme tokens across sol/bsc/base/eth/arbitrum/hyperevm/robinhood/arc/stable — 15 gmgn-cli skills for trending, trenches (new launches), token security, h |
| gmgn-swap.zip (15 KB) | gmgn-swap | short | >- |
| gmgn-token.zip (13 KB) | gmgn-token | short | Research any crypto or meme token by address — real-time price, market cap, liquidity, holder list, trader list, top Smart Money and KOL positions, security audit (honeypot, rug pull risk, dev wallet, |
| gmgn-token-buy.zip (13 KB) | gmgn-token-buy | short | >- |
| gmgn-track.zip (8 KB) | gmgn-track | short | Get real-time crypto buy/sell activity from Smart Money wallets, KOL influencer wallets, and personally followed wallets via GMGN API — alpha signals, whale tracking, meme token copy-trading ideas on  |
| gmgn-wallet-analysis.zip (14 KB) | gmgn-wallet-analysis | short | >- |
| gmgn-wallet-score.zip (15 KB) | gmgn-wallet-score | short | >- |
| godmode.zip (38 KB) | godmode | short | Jailbreak LLMs: Parseltongue, GODMODE, ULTRAPLINIAN. |
| google-dork-consistent.zip (4 KB) | google-dork-consistent | full | Use when Google dorking / Google SERP scraping hits the "unusual traffic" CAPTCHA wall, or when you need consistent, repeatable Google search results from an automated browser. Covers the profile-boun |
| graphql-audit.zip (12 KB) | graphql-audit | full | GraphQL security hunting — introspection abuse, field suggestion leaks, resolver-level authz/IDOR, batching and rate-limit issues, CSRF on GET mutations, and how to keep testing when introspection is  |
| hunt-aem.zip (11 KB) | hunt-aem | full | Use when hunting Adobe Experience Manager sites. |
| hunt-api-misconfig.zip (30 KB) | hunt-api-misconfig | full | Hunt API security misconfiguration — mass assignment, prototype pollution, HTTP verb tampering. Mass assignment: send {is_admin:true, role:admin, verified:true} on profile/account/reset endpoints — se |
| hunt-aspnet.zip (8 KB) | hunt-aspnet | full | Hunt ASP.NET-specific surface — ViewState deserialization (signed-only vs encrypted), machineKey recovery, dual-parser MAC-bypass anti-pattern, request-validator bypass, trace.axd/elmah.axd disclosure |
| hunt-ato.zip (7 KB) | hunt-ato | full | Hunt account takeover taxonomy — 9 distinct paths to ATO, plus chains. Paths: (1) password reset flaws (host-header injection redirects token, predictable/numeric token, Referer leak, no-expiry/reuse) |
| hunt-auth-bypass.zip (29 KB) | hunt-auth-bypass | full | Hunting skill for auth bypass vulnerabilities. Built from 12 public bug bounty reports across SAML XSW / parser-differential (GitHub Enterprise CVE-2025-25291/25292), SAML signature stripping (Uber, R |
| hunt-brute-force.zip (11 KB) | hunt-brute-force | full | Hunt Missing/Weak Rate Limiting — login brute force, OTP/2FA brute force (10^6 keyspace), password-reset-token brute, credential stuffing, username/email enumeration via error-string / status-code / t |
| hunt-business-logic.zip (14 KB) | hunt-business-logic | full | Hunting skill for business logic vulnerabilities. Built from real engagements — includes the inert-value probe for testing write endpoints safely, cart/quantity/coupon patterns, and Hybris/commercetoo |
| hunt-cache-poison.zip (9 KB) | hunt-cache-poison | full | Hunting skill for cache poison vulnerabilities. Built from 10 public bug bounty reports including X-Forwarded-Host poisoning, X-HTTP-Method-Override / GCS cache, reflected→stored XSS via cache, classi |
| hunt-captcha-bypass.zip (5 KB) | hunt-captcha-bypass | full | Hunt CAPTCHA Bypass — 6 distinct patterns: (1) CAPTCHA field simply omitted from the request (server-side validation absent), (2) CAPTCHA token replayed from a solved challenge (no single-use enforcem |
| hunt-cicd.zip (8 KB) | hunt-cicd | full | Hunt CI/CD pipeline vulnerabilities — GitHub Actions workflow injection (pull_request_target Pwnrequest + ${{ }}-into-shell), self-hosted runner poisoning, OIDC trust-policy abuse, Jenkins script-cons |
| hunt-clickjacking.zip (3 KB) | hunt-clickjacking | full | Hunt Clickjacking — missing X-Frame-Options / CSP frame-ancestors lets an attacker embed the target page in an invisible iframe and trick victims into clicking buttons they cannot see (UI redressing). |
| hunt-cloud-misconfig.zip (6 KB) | hunt-cloud-misconfig | full | Hunt cloud / infrastructure misconfigurations. AWS: public S3 buckets (s3:GetObject anonymous), permissive bucket policies (PutObjectAcl public-write), exposed CloudFront origin, public Lambda functio |
| hunt-cors.zip (6 KB) | hunt-cors | full | Hunt CORS Misconfiguration — origin-reflection with credentials, null-origin trust, subdomain-regex bypass (unanchored vs unescaped-dot vs prefix-only), pre-flight (OPTIONS) gating bypass, postMessage |
| hunt-csrf.zip (15 KB) | hunt-csrf | full | Hunting skill for CSRF — token presence/absence, content-type gating, SameSite reading over CDP, and running the cross-site proof from a real attacker origin. |
| hunt-deserialization.zip (4 KB) | hunt-deserialization | full | Hunt Insecure Deserialization — Java gadget chains (ysoserial), PHP object injection (phpggc), Python pickle RCE, .NET BinaryFormatter, Ruby Marshal.load, JNDI/Log4Shell. RCE via deserialization is al |
| hunt-dispatch.zip (26 KB) | hunt-dispatch | full | Skill-set loader for /hunt orchestrator. Fingerprints the target, picks the right platform attack skills, and loads the Red Team or WAPT skill set. Use when /hunt has just received a mode answer (redt |
| hunt-dom.zip (8 KB) | hunt-dom | full | Hunt client-side DOM vulnerabilities — DOM Clobbering (overwrite JS globals via HTML injection), PostMessage hijacking (missing origin check), Service Worker abuse (intercept requests from same-origin |
| hunt-exceptional-conditions.zip (2 KB) | hunt-exceptional-conditions | full | Hunt mishandling of exceptional conditions — feed an endpoint malformed/unexpected input (wrong type, broken JSON, oversized field, null byte) and make it fail OPEN or leak internals: a verbose stack- |
| hunt-file-upload.zip (4 KB) | hunt-file-upload | full | Hunt file upload bugs — RCE via webshell, XSS via SVG/HTML, SSRF via XXE in DOCX, path traversal via filename. Bypass tables (10 techniques): double extension (shell.php.jpg if server checks last ext  |
| hunt-fintech-graphql.zip (6 KB) | hunt-fintech-graphql | full | Hunt fintech-specific GraphQL vulnerabilities: money-movement mutations (transfers, redemptions, withdrawals, card top-ups), ledger/balance/portfolio query IDOR, decimal-precision and rounding abuse,  |
| hunt-forgot-password.zip (4 KB) | hunt-forgot-password | full | Hunt Forgot Password / Account Recovery Authentication Flaws — 5 distinct patterns: (1) username enumeration via different responses for valid vs invalid email, (2) reset token exposed directly in the |
| hunt-graphql.zip (23 KB) | hunt-graphql | full | Hunting skill for graphql vulnerabilities. Built from 12 public bug bounty reports across IDOR via node() / GID, mutation IDOR including AI/LLM features, cross-tenant IDOR, SSRF via argument, batching |
| hunt-grpc.zip (8 KB) | hunt-grpc | full | Hunt gRPC vulnerabilities — server reflection enabled (enumerate all services/methods), missing authentication / metadata-stripping on internal endpoints, plaintext gRPC over HTTP/2, internal endpoint |
| hunt-host-header.zip (8 KB) | hunt-host-header | full | Hunt Host Header Injection — password reset poisoning → ATO, web cache poisoning via unkeyed Host/X-Forwarded-Host, routing-based SSRF (Host picks upstream → cloud metadata/internal services), path-ov |
| hunt-html-injection.zip (4 KB) | hunt-html-injection | full | Hunt HTML Injection — user-supplied input is rendered as raw HTML in the response without sanitisation, allowing an attacker to inject arbitrary HTML tags (but not necessarily JavaScript). Lower sever |
| hunt-http-smuggling.zip (4 KB) | hunt-http-smuggling | full | Hunt HTTP request smuggling (CL.TE, TE.CL, H2.CL, H2.TE). Cause: front-end proxy and back-end server disagree on where one request ends and the next begins (Content-Length vs Transfer-Encoding header  |
| hunt-hybris.zip (7 KB) | hunt-hybris | full | Use when the target runs SAP Commerce (Hybris) — OCC v2 REST surface (/rest/v2/{site}/...), ws-api/v1 cart, /medias, /hac, /backoffice, verbose Spring validation leaks, serial-voucher endpoints, and t |
| hunt-idor.zip (44 KB) | hunt-idor | full | Hunting skill for idor vulnerabilities. Built from 26 public bug bounty reports. Use when hunting idor on any target. |
| hunt-jwt-crypto.zip (9 KB) | hunt-jwt-crypto | full | Hunt JWT cryptographic failures — alg:none signature-stripping and RS256→HS256 key-confusion that let an attacker forge a token for any identity (e.g. an admin) without knowing a secret. Use when the  |
| hunt-k8s.zip (9 KB) | hunt-k8s | full | Hunt Kubernetes & Docker — API anonymous access, kubelet 10250 exec (SPDY/WebSocket, NOT plain POST) and the simpler /run primitive, etcd 2379 unauth, dashboard skip-login, RBAC misconfig, secret/SA-t |
| hunt-laravel.zip (4 KB) | hunt-laravel | full | Hunt Laravel specific vulnerabilities — Debug mode leakage (APP_DEBUG=true exposes full stack trace + env vars), Laravel Telescope/Horizon dashboard unauthorized access, Ignition RCE (CVE-2021-3129),  |
| hunt-ldap.zip (7 KB) | hunt-ldap | full | Hunt LDAP Injection and XPath Injection — authentication bypass, blind char-by-char attribute exfiltration, AD user/group enumeration, XML-store XPath bypass. Covers the LDAP special-character set (*  |
| hunt-lfi.zip (8 KB) | hunt-lfi | full | Hunt Local File Inclusion (LFI), Remote File Inclusion (RFI), and Path Traversal — /etc/passwd read, log poisoning → RCE, PHP filter-chain RCE (no upload needed), php:// / data:// / zip:// / phar:// w |
| hunt-llm-ai.zip (8 KB) | hunt-llm-ai | full | Hunt LLM/AI feature bugs — prompt injection, indirect injection, exfiltration via tool-use/markdown, ASCII smuggling, agentic AI security (OWASP Agentic Apps 2026, ASI01-ASI10). Patterns: direct injec |
| hunt-mfa-bypass.zip (6 KB) | hunt-mfa-bypass | full | Hunt MFA / 2FA bypass — 7 distinct patterns. (1) MFA not enforced on sensitive endpoints (password change, email change accept without MFA challenge), (2) MFA-step skip via direct navigation to post-l |
| hunt-misc.zip (10 KB) | hunt-misc | full | Hunting skill for misc vulnerabilities. Built from 225 public bug bounty reports. Use when hunting misc on any target. |
| hunt-nextjs.zip (5 KB) | hunt-nextjs | full | Hunt Next.js specific vulnerabilities — Server Actions arbitrary function execution, Middleware auth bypass via static asset paths, ISR cache poisoning, Image Optimization SSRF (/_next/image), RSC pay |
| hunt-nodejs.zip (4 KB) | hunt-nodejs | full | Hunt Node.js specific vulnerabilities — Prototype Pollution → RCE chains (lodash/merge/assign), Express trust proxy misconfiguration, child_process/eval injection, template engine SSTI (EJS/Pug/Handle |
| hunt-nosqli.zip (3 KB) | hunt-nosqli | full | Hunt NoSQL Injection — MongoDB operator injection ($where, $regex, $gt, $ne), CouchDB, Redis command injection, auth bypass via NoSQLi, data dump. Use when target uses MongoDB/Mongoose, CouchDB, Redis |
| hunt-ntlm-info.zip (8 KB) | hunt-ntlm-info | full | Hunt NTLM/Negotiate information disclosure on internet-reachable IIS/SharePoint/Exchange. Anonymous NTLM Type-2 challenge capture leaks NetBIOS domain, internal DNS forest, computer name, AD timestamp |
| hunt-oauth.zip (58 KB) | hunt-oauth | full | Hunting skill for oauth vulnerabilities. Built from 19 public bug bounty reports. Use when hunting oauth on any target. |
| hunt-open-redirect.zip (3 KB) | hunt-open-redirect | full | Hunt Open Redirect — all types including low-impact, chained to OAuth token theft → ATO, phishing chains. URL parameter manipulation, JavaScript redirect, meta refresh, header injection. Use when hunt |
| hunt-race-condition.zip (14 KB) | hunt-race-condition | full | Hunting skill for race condition vulnerabilities. Built from 12 public bug bounty reports including modern HTTP/2 single-packet attack cases (James Kettle DEF CON 2023 "Smashing the State Machine"; Ry |
| hunt-rag-vector.zip (5 KB) | hunt-rag-vector | full | Hunt vector-store / embedding-layer weaknesses in RAG pipelines (OWASP LLM08 Vector and Embedding Weaknesses) — persistent corpus poisoning that survives across sessions and users (distinct from one-s |
| hunt-rce.zip (13 KB) | hunt-rce | full | Hunting skill for rce vulnerabilities. Built from 67 public bug bounty reports. Use when hunting rce on any target. |
| hunt-saml.zip (9 KB) | hunt-saml | full | Hunt SAML / SSO attacks. Patterns: XML Signature Wrapping (XSW) — modify Assertion while keeping Signature valid by relocating signed element, comment injection in NameID (admin@target.com<!--evil-->@ |
| hunt-session.zip (15 KB) | hunt-session | full | Hunt Session Management vulnerabilities — session fixation (no regeneration on login), insufficient invalidation on logout / password-change / email-change, predictable or low-entropy session IDs, JWT |
| hunt-shadow-api.zip (6 KB) | hunt-shadow-api | full | Hunt shadow / zombie / undocumented API surface (OWASP API9 Improper Inventory Management) — enumerate the full API version history (v1/v2/beta/legacy paths, header- and subdomain-based versioning), p |
| hunt-sharepoint.zip (12 KB) | hunt-sharepoint | full | Hunt Microsoft SharePoint Server (2013/2016/2019/Subscription Edition) on-prem farms — anonymous endpoint enumeration, version disclosure, legacy SOAP login bypass (Authentication.asmx), ToolShell pre |
| hunt-source-leak.zip (5 KB) | hunt-source-leak | full | Hunt source code and build artifact leakage — JavaScript source maps (.js.map) reconstructing TypeScript/ES6 source, Swagger/OpenAPI JSON endpoint discovery, .env/.git exposure, webpack chunks with ha |
| hunt-spa-api.zip (11 KB) | hunt-spa-api | full | Discover a single-page-app's hidden backend API from its public JS bundle, then test that API for broken access control / missing authentication. One of the highest-yield web plays in modern recon — S |
| hunt-springboot.zip (5 KB) | hunt-springboot | full | Hunt Spring Boot specific vulnerabilities — Actuator endpoints (heapdump, env, loggers, mappings, shutdown), Spring Expression Language (SpEL) injection → RCE, H2 console RCE, Jolokia JMX exposure, Sp |
| hunt-sqli.zip (10 KB) | hunt-sqli | full | Hunting skill for sqli vulnerabilities. Built from 12 public bug bounty reports including modern NoSQL injection (Rocket.Chat CVE-2021-22911 MongoDB $regex, Mongoose ORM CVE-2024-53900 $where bypass), |
| hunt-ssrf.zip (13 KB) | hunt-ssrf | full | Hunting skill for ssrf vulnerabilities. Built from 15 public bug bounty reports including AWS metadata SSRF (HackerOne $25k Analytics PDF, Shopify Exchange $25k, Capital One 106M-record breach, Dropbo |
| hunt-ssti.zip (4 KB) | hunt-ssti | full | Hunt server-side template injection (SSTI) across Jinja2 (Flask/Django), Twig (Symfony), Freemarker (Java), ERB (Rails), Spring, Velocity, Mako, Thymeleaf, Smarty. Detection probes use double-curly an |
| hunt-subdomain.zip (12 KB) | hunt-subdomain | full | Hunting skill for subdomain takeover vulnerabilities. Includes modern provider fingerprints — Microsoft Azure DevOps `cloudapp.azure.com` regional-pool re-issue (1-click OAuth ATO via wildcard `reply_ |
| hunt-tls-network.zip (9 KB) | hunt-tls-network | full | Hunt TLS/SSL and DNS misconfigurations — missing HSTS (downgrade attack), weak cipher suites, expired/invalid certificates, mTLS bypass, missing SPF/DKIM/DMARC (email spoofing), DNS Zone Transfer (AXF |
| hunt-websocket.zip (9 KB) | hunt-websocket | full | Hunt WebSocket vulnerabilities — Cross-Site WebSocket Hijacking (CSWSH), missing/weak Origin validation on the WS handshake, no per-message authentication, message tampering, socket.io namespace/room  |
| hunt-xss.zip (16 KB) | hunt-xss | full | Hunting skill for xss vulnerabilities. Built from 174 public bug bounty reports. Use when hunting xss on any target. For markup injection that reflects raw HTML but does NOT execute JavaScript (no `<s |
| hunt-xxe.zip (10 KB) | hunt-xxe | full | Hunting skill for xxe vulnerabilities. Built from 10 public bug bounty reports including SVG-upload XXE, Office-doc (PPTX/DOCX) XXE, SOAP XXE, SAML AssertionConsumer XXE, blind OOB XXE via DTD callbac |
| ios-redteam-pipeline.zip (7 KB) | ios-redteam-pipeline | full | End-to-end iOS red-team pipeline — IPA acquisition (App Store extraction, TestFlight, enterprise/ad-hoc sideload), class-dump/Hopper/Ghidra static analysis, Info.plist + entitlements + Keychain secret |
| live-vs-source-bytecode-forensics.zip (41 KB) | live-vs-source-bytecode-forensics | full | Use when auditing a deployed (bug-bounty) contract whose published repo may not match what is live. Proves, byte-for-byte, which source is deployed; recovers live source from verifier-alliance/eth-byt |
| m365-entra-attack.zip (10 KB) | m365-entra-attack | full | Microsoft 365 / Entra ID red-team attack chain — current 2026 reality. AADSTS code reference, user enumeration vectors (with hardening status), Smart Lockout math, Conditional Access bypass options, R |
| meme-coin-audit.zip (7 KB) | meme-coin-audit | full | Meme coin and token security audit — rug pull detection (honeypot, hidden mint, fee manipulation, LP lock bypass), Solana SPL token analysis (freeze authority, mint authority, metadata mutability), To |
| methodology-audit-execution-discipline.zip (760 KB) | methodology-audit-execution-discipline | full | Rules enforcing execution over skill loading. PRIMARY: audit-pipeline-orchestrator.py (force-full-execution → variants → PoC exec → PoC variants → references-exec → 13-check disk gate at 0D with auto- |
| methodology-bb-audit-launcher.zip (554 KB) | methodology-bb-audit-launcher | full | Bug Bounty Audit Launcher — pre-audit workflow with HARD GATES. Load skills, follow phases, check 219 boxes. |
| mobile-pentest.zip (32 KB) | mobile-pentest | full | Mobile app pentest for bug bounty (Android APK + iOS IPA) — runtime-first workflow: install app, proxy through Burp/mitmproxy, drive the UI, capture packets, then test the API exactly like a web targe |
| modern-web-framework-attacks.zip (52 KB) | modern-web-framework-attacks | full | Next.js RSC, CDP bypass, JS bundles, MCP, feature flags, RPC |
| modern-webapp-auth-hunting.zip (18 KB) | modern-webapp-auth-hunting | full | Use when auditing authenticated web apps in bug bounty. |
| nextjs-app-security-testing.zip (15 KB) | nextjs-app-security-testing | full | Use when auditing Next.js App Router apps under VDP scope. |
| nextjs-server-actions-audit.zip (128 KB) | nextjs-server-actions-audit | full | Use when auditing Next.js Server Actions authed flows. |
| offensive-osint.zip (130 KB) | offensive-osint | full | Operational arsenal for authorized external red-team and bug-bounty recon. Concrete probes, wordlists, regexes, dorks, curl one-liners for: subdomain enum, GraphQL/Swagger/REST discovery, identity fab |
| okta-attack.zip (10 KB) | okta-attack | full | Okta-as-IdP red-team attack chain — tenant discovery, user enumeration (multiple vectors), authentication flow analysis (factors enumeration, push-notification fatigue, SMS bypass), password spray wit |
| onchain-finding-verification.zip (32 KB) | onchain-finding-verification | full | Use when verifying an on-chain finding before reporting. |
| onchain-source-recovery.zip (23 KB) | onchain-source-recovery | full | Recover and validate a verified smart-contract's source from the chain (Blockscout/Sourcify) when it is absent from the public repo, then run slither + forge tests on it. Use when a vendor documents a |
| opsec-checker.zip (2 KB) | opsec-checker | full | Operational Security Validator: VPN, DNS leaks, virtualization, browser fingerprint, hostname. |
| osint-methodology.zip (40 KB) | osint-methodology | full | Comprehensive OSINT methodology for external red-team operations and authorized attack-surface assessments. Covers the 5-stage recon pipeline (seed discovery, asset expansion, enrichment, exposure ana |
| osint-toolkit.zip (3 KB) | osint-toolkit | full | Comprehensive OSINT tools directory — 70+ categories for recon, identity resolution, crypto investigation, social media, darknet, threat intel. Use when you need to find the right OSINT tool for any r |
| pdf-bug-report-generation.zip (41 KB) | pdf-bug-report-generation | full | Use when building bug-bounty PDF reports with reportlab. |
| perp-dex-audit.zip (11 KB) | perp-dex-audit | full | Use when auditing a perp DEX or trading-venue API. |
| perp-dex-engine-audit.zip (22 KB) | perp-dex-engine-audit | full | Use when auditing a perp/derivatives exchange engine. |
| perp-dex-protocol-audit.zip (17 KB) | perp-dex-protocol-audit | full | Audit live perp-DEX / exchange APIs via real positions. |
| poc-corpus-to-technique-atlas.zip (13 KB) | poc-corpus-to-technique-atlas | full | >- |
| poc-technique-atlas.zip (432 KB) | poc-technique-atlas | full | >- |
| portswigger-labs.zip (7 KB) | portswigger-labs | full | Use when solving PortSwigger Web Security Academy labs. |
| realtime-capability-token-authz.zip (4 KB) | realtime-capability-token-authz | full | Test realtime/pubsub capability-token authorization. |
| recon-scope-triage.zip (29 KB) | recon-scope-triage | full | Authorization + ownership triage before any active testing — FIRST confirm a live bounty/VDP artifact (security.txt + effective-dated policy + safe-harbor clause, or a platform listing you're enrolled |
| redteam-mindset.zip (16 KB) | redteam-mindset | full | Red-team operator discipline — the mindset corrections that separate offensive testing from defensive WAPT. Built from authorized red-team work where conservative defaults caused multiple findings to  |
| redteam-report-template.zip (7 KB) | redteam-report-template | full | Client-facing red-team deliverable format — codifies the Subject / Observations / Description / Impact / Recommendation / PoC structure used for external red-team engagements (not bug-bounty platform  |
| report-writing.zip (33 KB) | report-writing | full | Bug bounty report writing for H1/Bugcrowd/Intigriti/Immunefi — report templates, human tone guidelines, impact-first writing, CVSS 3.1 scoring, title formula, impact statement formula, severity decisi |
| reportlab-security-pdf.zip (79 KB) | reportlab-security-pdf | full | Use when generating PDF bug-bounty reports with reportlab. |
| rsa-attacks.zip (2 KB) | rsa-attacks | short | Offline RSA attack library: small-e, Fermat, Wiener, common-modulus, factordb, auto-dispatch. |
| saas-plan-entitlement-audit.zip (41 KB) | saas-plan-entitlement-audit | full | Audit SaaS plan/entitlement bypass and free-tier logic. |
| saas-test-account-provisioning.zip (36 KB) | saas-test-account-provisioning | full | Provision a verified SaaS test account pre-audit. |
| saas-vdp-engagement-playbook.zip (32 KB) | saas-vdp-engagement-playbook | full | Use for VDP bug-bounty audits of SaaS web apps. |
| secret-tripwire.zip (6 KB) | secret-tripwire | full | Output-layer secret redaction: detect private keys, mnemonics, API keys before they leak. |
| security-arsenal.zip (39 KB) | security-arsenal | full | Security payloads, bypass tables, wordlists, gf pattern names, always-rejected bug list, and conditionally-valid-with-chain table. Use when you need specific payloads for XSS/SSRF/SQLi/XXE/NoSQLi/comm |
| security-audit-execution-discipline.zip (333 KB) | security-audit-execution-discipline | full | Rules enforcing execution over skill loading. PRIMARY: audit-pipeline-orchestrator.py (force-full-execution → variants → PoC exec → PoC variants → references-exec → 10-check disk gate with auto-rework |
| security-bb-audit-launcher.zip (426 KB) | security-bb-audit-launcher | full | Bug Bounty Audit Launcher — pre-audit workflow with HARD GATES. Load skills, follow phases, check 219 boxes. |
| security-cloud.zip (3 KB) | security-cloud | full | Use during Phase 0C for cloud security audits. |
| security-lab-range-practice.zip (7 KB) | security-lab-range-practice | full | Drill exploit technique on a lab range, one lab at a time. |
| security-poc-video-production.zip (10 KB) | security-poc-video-production | full | Use when a vendor/triager asks for a video proof-of-concept for a vulnerability finding. |
| security-recon.zip (96 KB) | security-recon | full | Use during Phase 0B recon of any security audit. |
| security-scanners.zip (17 KB) | security-scanners | full | Use during Phase 0C for scanner selection and fuzzing. |
| security-tooling-setup.zip (28 KB) | security-tooling-setup | full | Install/verify security tooling on Windows and WSL. |
| security-web-attacks.zip (23 KB) | security-web-attacks | full | Use during Phase 0C for web2 attack playbooks. |
| server-actions-auth-audit.zip (31 KB) | server-actions-auth-audit | full | Use when auditing Next.js Server Actions auth or BOLA. |
| skill-anti-duplicate.zip (4 KB) | skill-anti-duplicate | full | Detect duplicate and overlapping skills using description matching, keyword analysis, and section comparison. Provides merge decision framework: which copy to keep, which to archive, and how to preser |
| smart-contract-audit.zip (178 KB) | smart-contract-audit | full | Use when auditing Solidity/EVM smart contracts. |
| src-hunter.zip (3.8 MB) | src-hunter | full | 实战 SRC / 众测 / Bug bounty 漏洞挖掘工作流 skill。包含：5 阶段方法论（intake → recon → enum → hunt → report）、19 个攻击类 playbook（SQLi/XSS/RCE/SSRF/IDOR/CSRF/Path Traversal/File Upload/SSTI/XXE/Race/HTTP Smuggling/OAuth/JWT/ |
| supply-chain-attack-recon.zip (17 KB) | supply-chain-attack-recon | full | External recon for software supply-chain attack surface — package-namespace squatting candidates, dependency-confusion vulnerabilities, GitHub Actions injection openings, container image registry expo |
| target-pool.zip (10 KB) | target-pool | full | Query the deduped bug-bounty target pool. |
| tax-calculation-audit.zip (16 KB) | tax-calculation-audit | full | Use when auditing tax-calculation correctness in tax/bookkeeping software (UK MTD, property, self-assessment first). Verifies arithmetic against published rules, not against vibes. |
| tax-rule-correctness-review.zip (7 KB) | tax-rule-correctness-review | full | Use when reviewing a financial/tax product's arithmetic against statutory tax rules (e.g. UK HMRC) rather than looking for security bugs. |
| tax-rule-verification.zip (39 KB) | tax-rule-verification | full | Use when auditing tax/finance SaaS arithmetic (HMRC/MTD cases) or any product that computes money from user-entered figures. |
| technique-capture.zip (9 KB) | technique-capture | full | The learning loop: capture a technique learned during an engagement (or from a URL/corpus), stage it, dedupe it against the atlas, distil it, and land it in poc-technique-atlas plus the owner skill. U |
| token-position-math.zip (3 KB) | token-position-math | short | Quote a token position at a target MC; convert USD→IDR. |
| triage-validation.zip (50 KB) | triage-validation | full | Finding validation before writing any report — 7-Question Gate (all 7 questions), 5 pre-submission gates incl. program-policy compliance (CVSS version currency, required report fields, reporting deadl |
| unauth-config-disclosure.zip (46 KB) | unauth-config-disclosure | full | Use when a target leaks tenant config or API keys pre-auth. |
| video-poc-production.zip (11 KB) | video-poc-production | full | Produce a video proof-of-concept (screen recording + live HTTP evidence) when a triager or vendor asks for a 'video PoC' with a report. Covers the three routes (re-runnable exploit / CLI-API / static  |
| vmware-vcenter-attack.zip (12 KB) | vmware-vcenter-attack | full | VMware vSphere / vCenter Server external attack matrix — version fingerprinting, the high-impact CVE chain (CVE-2021-21972 vRealize unauth file upload, CVE-2021-21985 vSAN plugin RCE, CVE-2022-22954 W |
| vuln-hunter.zip (15 KB) | vuln-hunter | full | Autonomous vulnerability hunter for ANY web2 or web3 target. Loads when user sends "1" or asks to hunt vulns on a target. Target-agnostic — drive it with a profile file, not hardcoded domains. |
| waf-stateful-bypass.zip (26 KB) | waf-stateful-bypass | full | Use when a WAF blocks every path on a bug-bounty target. |
| web2-recon.zip (30 KB) | web2-recon | full | Web2 recon pipeline — subdomain enumeration (subfinder, Chaos API, assetfinder), live host discovery (dnsx, httpx), URL crawling (katana, waybackurls, gau), directory fuzzing (ffuf), JS analysis (Link |
| web2-vuln-classes.zip (43 KB) | web2-vuln-classes | full | Complete reference for 26 web2 bug classes with root causes, detection patterns, bypass tables, exploit techniques, and real paid examples. Covers IDOR, auth bypass, XSS (postMessage), SSRF (11 IP byp |
| web3-audit.zip (91 KB) | web3-audit | full | Smart contract security audit — 12 bug classes (accounting desync, access control, incomplete path, off-by-one, oracle, ERC4626, reentrancy, flash loan, signature replay, proxy, cross-chain settlement |

## Install steps (Manus)

1. In Manus, open **Skills**.
2. Click **+ Add**, then **Upload a skill**.
3. Choose a `<skill-name>.zip` file from this folder.
4. Repeat for each skill you want.
5. In a Manus chat, type `/` and pick the skill to use it.

