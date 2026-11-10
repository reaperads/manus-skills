## PHASE 5-8: FINAL GATE → SEVERITY → VERIFICATION → REPORT (LAST)

> LAST STAGES. All testing + referencing must be complete before entering.
> Report = ABSOLUTE LAST STEP.

---

### Phase 5: FINAL GATE — 219-Box Checklist
→ `references/operator-workflow.md` — Complete 14-point checklist.
- **Checklist MUST be 100% complete before proceeding to severity or report.**
- Every box checked = ready for severity calibration. Missing box = stop, fix, re-verify.

### Phase 6: SEVERITY CALIBRATION
→ `references/severity-rules.md`
- Calibrate severity for ALL findings based on PROVEN impact only.
- Apply overclaiming filter (10 banned patterns).
- Apply social engineering filter (phishing = OUT OF BOUNTY).
- Apply finding priority order (IDOR > Auth Bypass > RCE > Logic > CORS).
- **Severity BEFORE report. Never write report with uncalibrated severity.**

### Phase 7: FINAL VERIFICATION
- All 219 boxes PASS
- No overclaiming
- No severity inflation
- No social engineering findings
- All findings reproducible 3x
- ONE comprehensive report
- Finding priority order correct
- **Final verification BEFORE report. Never write report without final check.**

### Phase 8: REPORT — Write submissions that pass triage (ABSOLUTE LAST)
→ `references/reporting.md` + `references/humanize-screenshots.md` + `references/advanced-vuln-vectors-2026.md` (remediation snippets) + `references/pre-submission-verification.md` (watermark/VRT/submission checklist)
- Structure: Title → Summary → Severity/CVSS → Steps to Reproduce → Impact → PoC → Remediation.
- CVSS scoring with **mandatory vector string** + impact argument.
- Clear, neutral, reproducible language.
- **Remediation (MANDATORY per finding):** Secure code snippet + fix difficulty rating (Easy/Medium/Hard) + WAF hardening if applicable.
- **Business impact (MANDATORY):** Data exfil sample, PII leakage, or financial loss path.
- **Batch mode:** ONE comprehensive PDF per project containing ALL findings (not separate PDFs per finding). Each finding gets its own section within the document.
- **Impact Filter (MANDATORY):** Only report findings that demonstrably impact data, sistem, user, akun, or dana. **SKIP** findings that are:
  - **By-design** — intended behavior (e.g., unsigned Cloudinary presets, public product API, health endpoints)
  - **Informational-only** — no exploitation path to data/system/user/account/funds
  - **Requires phishing/social engineering** — not a technical vulnerability
  - **Public documentation** — data already in official docs, blog, atau GitHub README
  - **Auth wall blocked with no bypass** — all auth required, signup disabled, no error differential
  - **Sandbox infra metadata** — AWS Account ID, queue names, bucket names in sandbox health endpoints (P4 Low max unless chained)
  - **Config bugs without exploit path** — typos, double-equals di env-config.js TANPA proof of auth bypass

---


---

## 🔧 AUTOMATION ENGINE (v2 — universal toolkit)

> **This toolkit ships with the skill bundle.** Paths below are relative to the bundle
> root; if the tools are installed elsewhere, adjust. `bash verify.sh` must print
> `passed: 6 failed: 0` — run it once before trusting any tool.

| Phase | Tool | What it replaces |
|:--|:--|:--|
| 1 SCOPE | `$TOOLKIT/web2/scope_narrower.py` | eyeballing a 540-subdomain list. Scores every asset by bounty value, emits `--top N`. |
| 2 RECON | preexisting CLI chain (subfinder/httpx/nuclei) | still correct for inventory |
| 4 AUTH MATRIX | `$TOOLKIT/web2/idor_harness.py` | manual A/B curl. Two identities, `setup` then `verify`, emits `IDOR-CONFIRMED` + raw HTTP proof. |
| 3 ANALYSIS (web3) | `$TOOLKIT/web3/diff_vs_upstream.py` | reading 60KB of forked Solidity. Isolates the only code that differs from upstream. |
| 4 EXPLOIT (web3) | `$TOOLKIT/web3/invariant_scaffold.py` | hand-writing a Foundry harness. `targets.yaml` → runnable invariant test (Echidna/Medusa/Halmos). |
| 4.5 DEEPDIVE | `$TOOLKIT/shared/finding_gate.py` | self-deceiving severity. Drops info-only / by-design / **dead-chain** findings even at high score. |
| 5 REPORT | `$TOOLKIT/shared/chain_builder.py` | one weak finding = one weak report. Links 2+ findings into an impact chain. |

```bash
# typical run, any target
python $TOOLKIT/web2/scope_narrower.py recon.txt --top 5 --json shortlist.json
python $TOOLKIT/web2/idor_harness.py setup  -c target.yaml     # identity A creates objects
python $TOOLKIT/web2/idor_harness.py verify -c target.yaml     # identity B replays A's ids
python $TOOLKIT/web3/diff_vs_upstream.py ./src --upstream-repo <url>
python $TOOLKIT/web3/invariant_scaffold.py targets.yaml --out test/invariant
python $TOOLKIT/shared/finding_gate.py findings.json --report R.md
python $TOOLKIT/shared/chain_builder.py findings.json --goal account_takeover
```

**Contract these tools enforce** (they exist because the doctrine kept getting violated):
- `finding_gate.py` will **drop a finding with a high score but a dead exploit chain**. If you
  find yourself arguing with it, the finding is informational — no severity inflation.
- `chain_builder.py` only marks a link PROVEN when adjacent findings share a capability or a
  common entry point. A "chain" of two unrelated lows is not a chain.
- `invariant_scaffold.py` is only trustworthy if the generated test **passes on the safe
  contract AND breaks on the buggy one**. Test both directions or the tool lied to you.

### Legacy pipeline components
```bash
# Recon Pipeline
subfinder -d TARGET -silent | httpx -silent -status-code | nuclei -t exposures/

# API Discovery
katana -u TARGET -jc | grep -E '/api/|/v[0-9]+/' | sort -u

# Subdomain Takeover
subfinder -d TARGET -silent | httpx -silent | nuclei -t takeovers/
```

### Report Generation
- Template: `references/reporting.md`
- CVSS Calculator: NVD or manual vector scoring
- Format: Markdown → PDF (bug-report-delivery skill)
- **Batch mode:** ONE comprehensive PDF per project, ALL findings in one document

---

## 📊 BUGCROWD VRT v1.19 — QUICK REFERENCE

### Severity Levels
- **P1 Critical** — Authentication bypass, RCE, SQL injection, full account takeover
- **P2 High** — IDOR with sensitive data, SSRF to internal, stored XSS
- **P3 Medium** — CSRF with impact, open redirect, reflected XSS
- **P4 Low** — Information disclosure, missing security headers
- **P5 Informational** — Best practice, defense-in-depth

### Priority Multipliers
- P1: 1.0x (base bounty)
- P2: 0.75x
- P3: 0.50x
- P4: 0.25x
- P5: 0.0x (may get swag/recognition)

### 33 VRT Categories (key ones)
- A Sans-serif: Authentication Bypass
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection (SQL, NoSQL, OS, LDAP)
- A04: Insecure Design
- A05: Security Misconfiguration
- A06: Vulnerable Components
- A07: Identity & Auth Failures
- A08: Software & Data Integrity Failures
- A09: Security Logging & Monitoring Failures
- A10: Server-Side Request Forgery

### Smart Contract (added in v1.19)
- CRITICAL: Direct drain, protocol insolvency
- HIGH: Access control, reentrancy, flashloan
- MEDIUM: Oracle manipulation, MEV
- LOW: Gas griefing, front-running

### AI Security (added in v1.19)
- CRITICAL: Model extraction, data leakage
- HIGH: Prompt injection → system access
- MEDIUM: Training data poisoning
- LOW: Model bias, hallucination exploitation

---

## 🛡️ IMMUNEFI WORKFLOW

### Submission Checklist
1. Verify bug exists on in-scope contract
2. Write clear PoC with Foundry/Hardhat test
3. Assess severity per Immunefi v2.2
4. Submit via immunefi.com with:
   - Title (concise, descriptive)
   - Vulnerability details (step-by-step)
   - Impact assessment (financial, protocol, users)
   - PoC code (working, reproducible)
   - Suggested fix
5. Wait for triage (SLA: acknowledgment within days)
6. Respond to triager questions promptly

### Severity (Immunefi v2.2)
- **Critical:** Direct fund loss > $X, protocol insolvency, permanent freeze
- **High:** Temporary DoS, contract upgrade without timelock, rug pull potential
- **Medium:** Oracle failure, MEV extraction, griefing with financial impact
- **Low:** Non-critical function DoS, gas griefing, best practice violations
- **Note:** Reporting only, not classification — Immunefi triages final severity

---

## 🤖 AI/LLM RED TEAMING

### Attack Vectors
1. **Prompt Injection** — Malicious input that overrides system prompt
2. **Model Extraction** — Query to reconstruct model behavior
3. **Data Extraction** — Extract training data or PII
4. **Bypass Guardrails** — Circumvent safety filters
5. **Abuse Functions** — Exploit tool/plugin integrations

### Testing Methodology
1. Enumerate AI features (chat, search, recommendations)
2. Test input sanitization (prompt injection payloads)
3. Test output filtering (data leakage, harmful content)
4. Test rate limiting (DoS via API abuse)
5. Test authentication (access control on AI features)

---

