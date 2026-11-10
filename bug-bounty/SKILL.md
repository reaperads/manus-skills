---
name: bug-bounty
author: Fauzi Susanto
description: "Use when hunting bug bounties or authorized testing. UNIFIED: covers web/API, smart contracts, DeFi, SaaS, LLM red-teaming, all platforms."
metadata:
  hermes:
    tags: [bug-bounty, security, web, api, blockchain, defi, saas, redteam, audit]
version: 4.0.0
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Bug Bounty — ROUTER

> **This SKILL.md is a lightweight router.** Content lives in split files below.
> Agent MUST load the correct split file per phase.
> 
> **⚠️ NEVER load all skills at once.** Use the phased matrix below.
> **⛔ NEVER skip to report. Phase 0C must be marked COMPLETE in PHASE_LOG.md before Phase 0F (report) loads.**
> **⛔ Phase transitions require PHASE_LOG.md verification. Read it first if resuming.**
> **⛔ Startup: ALWAYS create/read PHASE_LOG.md before ANY work.**
> Each phase loads ONLY its listed skills, then EVICTS before next phase.

---

## Pipeline (PHASED loading — avoid context compression)

```
Phase 0A: bb-audit-launcher (20KB) — evict after target type determined
Phase 0B: security-recon (25KB) + recon.md (17KB) — evict after surface mapped
Phase 0C: ONE TRACK ONLY (see matrix) — evict after testing complete
Phase 0D: verify-tool-usage gate (11 checks, HARD BLOCK)
Phase 0E: aggregate-findings → finding_gate → validate-findings → review-candidates
Phase 0F: bug-report-delivery + report.md (40KB) — ABSOLUTE LAST

NOTE: the block above is the MANUAL/skill pipeline. The AUTOMATED pipeline
(audit-pipeline-orchestrator.py / audit-run-all.py) runs 0A→0F:
0D = verify-tool-usage GATE, 0E = findings (aggregate→chain→gate),
0E-REVIEW = candidates 3x check (only survivors reach the report), 0F = report.
Read audit-execution-discipline references/audit-pipeline-phases-and-fresh-run.md
before invoking it (full-URL + --scope required; stale resume state lives in
~/AppData/Local/hermes/trackers/, not only in poc-plans).

⚠️ BUDGET: peak cumulative WITH eviction = 120KB (under 162KB threshold)
⚠️ WITHOUT eviction = 249KB → compression fires → skills pruned → audit dies
```

## Split Files

| File | Phase | Size | Content |
|------|-------|------|---------|
| `bug-bounty-main.md` | All | ~25KB | Rules, tool map, workflow overview, overclaiming patterns |
| `bug-bounty-recon.md` | 1-4 | ~18KB | Scope, recon, analyze, verify/exploit, deepdive gate |
| `bug-bounty-testing.md` | 4.5 | ~41KB | 10 layers, 736 refs, external repos, tool chains |
## Phase Definitions

| File | Phase | Budget | Content |
|------|-------|--------|---------|
| `bug-bounty-main.md` | All | ~25KB | Rules, tool map, workflow overview |
| `bug-bounty-recon.md` | 0B | ~17KB | Scope, recon, analyze, verify/exploit |
| `bug-bounty-testing.md` | 0C | ~41KB | 10 layers, 736 refs, tool chains |
| `bug-bounty-report.md` | 0D | ~8KB | 219-box checklist, severity, report |

## New Skills (Phase-specific — evict previous before loading)
| Skill | Phase | Budget | Repos |
|-------|-------|--------|-------|
| `security-recon` | 0B | 25KB | 15 |
| `security-web-attacks` | 0C-web2 | 30KB | 48 |
| `security-scanners` | 0C-any | 25KB | 18 |
| `security-cloud` | 0C-cloud | 25KB | 14 |

### Phase 0A: Router + Overview (START HERE)
- Load this skill (6KB)
- Load `bb-audit-launcher` skill (20KB)
- Load `bug-bounty-main.md` (27KB)
- Total: ~53KB

### Phase 0B: Recon Phase (before Phase 2)
- Load `security-recon` skill (25KB) — FULL recon playbook
- Load `bug-bounty-recon.md` (17KB) — scope/analyze rules
- Tools: subfinder, naabu, httpx, katana, gau, waybackurls, dirsearch
- Output → FILE ONLY (CO-1 rule). Context gets summary ≤5KB.
- Total: ~42KB (within 30KB budget by evicting 0A digest first)

### Phase 0C: Testing Phase (before Phase 4.5)
- **ONE TRACK ONLY** — load based on target type from Phase 0A:
  - **Web2:** `security-web-attacks` (30KB) + `security-scanners` (25KB) = 55KB
  - **Web3:** `smart-contract-audit` (17KB) + `onchain-finding-verification` (15KB) = 32KB
  - **Cloud:** `security-cloud` (25KB) + `security-scanners` (25KB) = 50KB
  - **RedTeam:** `exploit-cookbook` (6KB) + `references/redteam-playbook.md` (15KB) = 21KB
  - **Combined web2+web3:** `security-web-attacks` (30KB) + `smart-contract-audit` (17KB) = 47KB
- Load `bug-bounty-exhaustive-testing` (22KB) AFTER first batch of testing

- Load `exploit-cookbook/references/openemr-php-advisory-techniques.md` when the target is PHP/LAMP
  (extra attack variants, file-level, no phase-order/budget change)

- Load 5 reference files from `references/` on-demand (NOT all at once)
- ⛔ EVICT 0B skills BEFORE loading 0C (see CO-6 eviction protocol)

### Phase 0F: Report Phase (ABSOLUTE LAST)
- Load `bug-bounty-report.md` (9KB) — severity calibration
- Load `bug-report-delivery` (30KB, trimmed) — report generation
- Load `humanizer` (36KB) — screenshot/content polish
- Load 3 reference files from `references/`
- Total: ~75KB (within 40KB budget by evicting 0C first)
- **⛔ HARD BLOCK: bug-report-delivery has PRE-LOAD CHECK**
  - MUST verify PHASE_LOG.md shows 0C complete
  - MUST verify findings.json exists with candidates
  - If check fails → REFUSE to load, return to Phase 0C

> **Web3 target (from 0B recon)?** Load web3 skills + `references/web3-audit-abh.md` during Phase 0C (testing).

### Phase 1: SCOPE
- Lock target & rules
- HARD GATE: must complete BEFORE anything else
- See: `bug-bounty-recon.md` Phase 1

### Phase 2: RECON
- Map full attack surface
- See: `bug-bounty-recon.md` Phase 2

### Phase 3: ANALYZE
- Form attack hypotheses
- See: `bug-bounty-recon.md` Phase 3

### Phase 4: VERIFY & EXPLOIT
- Prove with working PoC
- See: `bug-bounty-recon.md` Phase 4

### Phase 4.5: DEEPDIVE GATE
- Exhaust ALL angles before presenting
- See: `bug-bounty-recon.md` Phase 4.5

### Phase 4.5+: EXHAUSTIVENESS GATE
- 30 vectors + 10 layers MUST pass
- See: `bug-bounty-testing.md`

### Phase 5: FINAL GATE — 219-Box Checklist
- ALL 219 boxes MUST pass
- See: `bug-bounty-report.md` Phase 5

### Phase 6: SEVERITY CALIBRATION
- Calibrate ALL findings
- No overclaiming, no inflation
- See: `bug-bounty-report.md` Phase 6

### Phase 7: FINAL VERIFICATION
- Last check before report
- See: `bug-bounty-report.md` Phase 7

### Phase 8: REPORT (ABSOLUTE LAST)
- Write + submit
- ONE report = ALL findings
- See: `bug-bounty-report.md` Phase 8

## Immediate Stop Rules (15)

1. JANGAN claim finding tanpa working PoC
2. JANGAN claim severity tanpa proven chain
3. JANGAN report(cors/csrf/clickjacking) sebagai finding utama
4. JANGAN skip deepdive — exhaustive testing MANDATORY
5. JANGAN claim "target solid" — test first
6. JANGAN overclaim — severity MUST match PROVEN chain
7. JANGAN submit partial — ONE report = ALL findings
8. JANGAN claim RCE padahal command injection ter-block
9. JANGAN claim ATO padahal hanya bisa akses data
10. JANGAN claim data exfil padahal hanya 1 field
11. JANGAN claim priv escalation padahal hanya lihat role
12. JANGAN claim SQLi padahal hanya boolean blind
13. JANGAN claim SSRF padahal hanya internal scan
14. JANGAN skip VRT — compare setiap finding
15. JANGAN lompat phase — ikut pipeline
16. JANGAN test CORS sebelum vector 1-13 selesai — CORS = vector #14
17. JANGAN loop bikin akun >2 attempt — max 5 menit, lalu MOVE ON
18. JANGAN mulai testing tanpa recon — Phase 0B wajib duluan
19. JANGAN hapus progress/evidence audit lama ketika user bilang "mulai dari awal / abaikan hasil
    sebelumnya". Itu instruksi untuk MULAI BERSIH, bukan izin menghapus state. Fork ke direktori
    sibling baru (`_progress/<target>_v2/`) dan jangan baca file lama — kalau `mv` gagal karena
    file terkunci, tetap lanjut di dir baru dan beri tahu user arsip lama dibiarkan utuh.
20. Selama belum ada PoC yang terbukti, status jujur yang benar adalah "verified-negative +
    catatan kontrol yang terbukti bekerja" — bukan daftar lead yang dibungkus seolah temuan.
    Lead yang belum dikunci ditulis sebagai "belum terbukti, butuh capture tambahan", bukan
    sebagai finding.
21. **JANGAN pakai curl saja.** User berulang kali menegaskan ini ("kerahkan semua kemampuan dan tools,
    jgn hanya curl"). Setiap kelas uji harus dijalankan dengan tool yang memang untuk itu: httpx/katana
    untuk surface, nuclei (template sempit + rate rendah, JANGAN full-tag 1,5 juta request), ffuf/dalfox/
    sqlmap untuk input, browser via CDP untuk apa pun yang butuh sesi/UI (form, react-select, OOPIF,
    iframe). curl hanya untuk probe satu titik / verifikasi cepat.
22. **Setiap perubahan state di akun target wajib dicatat, dipulihkan, dan di-disclose** sebelum sesi
    ditutup: nama tampilan yang dipakai sebagai payload, password yang berubah (termasuk efek samping
    permintaan reset), member uji yang dibuat/dihapus, client OAuth yang teregistrasi, file yang terunggah.
    Tulis di `ENGAGEMENT_LOG.md` + `findings.json`, dan sebutkan artefak yang tidak bisa dihapus sendiri
    (mis. DCR tanpa `registration_access_token`) supaya vendor bisa membersihkannya.
23. **Sebelum bilang "sudah deepdive", terbitkan TOOL-COVERAGE LEDGER — bukan narasi.** User menuntut ini
    berulang kali ("sudah deepdive lagi? pakai all tools dan varian attack yg blm dicoba"). Bentuk jawaban
    yang diterima: tabel eksplisit **tool → hasil**, termasuk tool yang BELUM dijalankan dan yang hasilnya
    NEGATIF. Aturan:
    - Setiap ronde "all tools" wajib menyebut tool mana yang baru dijalankan ronde itu dan mana yang
      belum (sqlmap/arjun/dalfox/naabu/gau+waybackurls/kxss/interactsh/ffuf/gobuster/smuggling/cache/
      graphql/dnsReaper/nuclei tag-rotation). Diam soal tool yang tidak dijalankan = overclaim.
    - Negatif itu deliverable: "OOB 0 callback", "smuggling tidak ada desync", "ffuf 0 hit",
      "CORS reflect tapi tanpa impact (auth API-key, bukan cookie)" ditulis apa adanya dengan alasan
      singkat — bukan disembunyikan.
    - Label severity dari tool ≠ temuan: template nuclei bisa bilang `[critical] config-json-exposure`
      padahal isinya cuma site key publik / feature flag. Buka body-nya dan nilai sendiri sebelum
      melaporkan; kalau FP, tulis "FP, sudah diverifikasi" agar tidak dihitung dua kali.
    - Satu varian per kelas: bila `kxss` menandai parameter terpantul, jalankan `dalfox` untuk memutuskan
      XSS — refleksi saja bukan temuan; bila `arjun` menemukan parameter hanya dari perbedaan HTTP code,
      itu heuristik lemah dan tidak boleh diklaim.

## Overclaiming Patterns (10 BANNED)

1. **Critical RCE** padahal command injection ter-block
2. **Account Takeover** padahal hanya bisa akses data
3. **Full data exfiltration** padahal hanya 1 field
4. **Privilege escalation** padahal hanya lihat role
5. **SQL injection** padahal hanya boolean blind
6. **SSRF** padahal hanya internal scan
7. **Business logic flaw** padahal hanya manipulasi quantity 1-2
8. **Mass assignment** padahal hanya tambah field kosong
9. **Authentication bypass** padahal hanya bypass rate limit
10. **Session fixation** padahal hanya fix session sendiri

## Severity Calibration

| Finding Type | Max Severity |
|-------------|-------------|
| CORS misconfiguration | P3 MAX |
| CSRF (no impact demonstrated) | P3 MAX |
| Clickjacking | P3 MAX |
| Open redirect (no chaining) | LOW MAX |
| SSL/TLS weak cipher | INFO MAX |
| Missing security headers | INFO MAX |
| Information disclosure (non-sensitive) | INFO MAX |
| Business logic (quantity 1-2) | P4 MAX |
| Mass assignment (empty field) | P4 MAX |
| Rate limit bypass | P4 MAX |
| Session fixation (own session) | P4 MAX |

## Finding Priority Order

```
IDOR/BOLA > Auth bypass > Priv esc > RCE/SSRF > SQLi > Business logic > Mass assignment > Info disclosure > CORS/CSRF/Clickjacking
```

## Tool Map (by phase)

| Phase | Tools |
|-------|-------|
| 1-2 | subfinder, httpx, naabu, katana, gau, waybackurls |
| 3 | ffuf, dalfox, kxss, nuclei, sqlmap |
| 4 | gobuster, ffuf, dalfox, manual testing |
| 4.5+ | slither, mythril, echidna, medusa, aderyn (web3) |
| 5-8 | finding_gate.py, chain_builder.py, bug-report-delivery |

## Reference Files (14)

| File | Purpose |
|------|---------|
| `references/operator-workflow.md` | 14-point checklist |
| `references/god-eye-validation.md` | Validation framework |
| `references/severity-rules.md` | Severity calibration |
| `references/checklist-219-boxes.md` | 219-box report gate |
| `references/reporting.md` | Report writing |
| `references/humanize-screenshots.md` | Screenshot standards |
| `references/advanced-vuln-vectors-2026.md` | Advanced vectors |
| `references/pre-submission-verification.md` | Pre-submission checks |
| `references/bb-methodology.md` | BB methodology |
| `references/recon-methodology.md` | Recon methodology |
| `references/vuln-methodology.md` | Vuln methodology |
| `references/bugcrowd-vrt.md` | VRT reference |
| `references/bugcrowd-ninja-alias-signup.md` | Self-signup with `@bugcrowdninja.com` alias + reading the forwarded verification mail (Mandrill decode) |
| `references/email-template-injection.md` | HTML/link injection in transactional mail (invite, resend, notifications): sink table, payload ladder, escape-differential evidence trick, DKIM/SPF capture, CRLF header-injection negative test, escape-map across templates, honest P4→P3 scoping |
| `references/postmessage-iframe-channel-testing.md` | Embedded/payment pages: find the `message` handler in the bundle, framing check (incl. the 429-page `X-Frame-Options` trap), local attacker-origin harness, CDP OOPIF attach to read the cross-origin iframe DOM, demo/preview-token hunting, "proved vs not proved" P4 scoping, re-test leads before submitting |
| `references/vendor-granted-account-constraints.md` | Vendor-granted accounts with a written "don't touch X" rule: enforce via rules file + env-var route guard + capability flags, prove compliance in the report, and avoid the generic-clicker near-miss that fired the forbidden action and killed the session |
| `references/wordpress-admin-attack-surface.md` | WordPress/CMS marketing sites: `/wp-json/` route table as the plugin map, the one-route-missing-`permission_callback` differential (e.g. iThemes `/bans` 200 vs siblings 401), `readme.txt` + nuclei `detected_version` fingerprinting with the "a version is not a CVE" rule, author/Yoast enum, and the OOB/smuggling/ffuf negatives so the next pass skips them |
| `references/sherlock-program-rules.md` | **Sherlock** programs (any of them): submission is a login-gated form not e-mail; the excluded-class list that gets reports rejected; the verbatim "user transferred tokens directly" clause + its two escape prongs (pre-empt it in the report); duplication is by ROOT CAUSE so several routes = ONE report; impact must name the missing control; mandatory prior-audit duty + what to do when the reports are unreachable (disclose + offer withdrawal) |
| `references/smart-contract-methodology.md` | Smart contract |
| `references/recon-triage-and-vendor-claim-verification.md` | Recon FP killers (wildcard-DNS test, NXDOMAIN sweep, S3 `AccessDenied` vs `NoSuchBucket`, "resolves ≠ live ≠ takeover", env-codename enumeration, auth-parity check), independently verifying a vendor's published advisory (npm publish dates + tarball grep + placeholder-vs-real secrets), in-memory handling of malicious payloads (AV Errno 22), and scanner-label-vs-finding triage (aderyn H×3 all FP) |
| `references/agent-kb-bounty-exploit-master.md` | Master KB |

## External Repos (19 integrated)

All 19 repos merged into `references/` and `tools/`. 739 reference files + 593 tool files.

## Session / Next.js notes

- `references/nextjs-server-actions-and-session-identity.md` — verify WHAT ACCOUNT your stored
  session cookie belongs to before testing (a stale jar may be an old free account while your key
  is paid); enumerate/replay/drive Next.js App Router **server actions** (42-hex ids, `Next-Action`
  header, per-render `$ACTION_KEY`, React native value setter, TOTP two-step gates); git-bash path
  mangling and Hermes secret-redaction gotchas.
- `references/nextjs-action-replay-and-authz.md` — replay actions HEADLESSLY: the static form format
  that works (bare field names; Chromium's `_1_` prefix always 500s from requests), why JS-invoked
  wire ids must be harvested live (they are not in the bundle or the RSC payload), the
  `page.route` body-rewrite authz test with mandatory positive controls, MFA-gated destructive
  actions, and the free-tier-cap replay recipe.
- `references/audit-pipeline-phases-and-fresh-run.md` (in `audit-execution-discipline`) — the
  orchestrator's real 0A→0F model, the mandatory full-URL + `--scope` gate, and where the resume
  state actually lives when you need a genuine fresh run.

## Data Conventions

- `$BB_DATA` = `D:/data hermes/bug-bounty/`
- `$TOOLKIT` = `D:/data hermes/bug-bounty/bundle/toolkit/`
- `$DATA` = `D:/data hermes/`

---

> **READ THE SPLIT FILES. This SKILL.md is just a router.**