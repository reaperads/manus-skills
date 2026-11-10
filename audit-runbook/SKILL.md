---
name: audit-runbook
description: Toma's enforced audit SOP. Use at the START of every bug-bounty audit and follow it phase by phase. Ordered checklists per phase with REQUIRED skills/tools and the evidence each must leave on disk. The usage ledger proves skills/tools were really invoked, not skipped. Includes the differential-testing core technique, deep-dive procedure, and the account factory SOP (make test accounts yourself, never ask the user).
sources: operator_defined
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Audit Runbook — enforced SOP (toma, 2026-10-09)

Three laws:
1. **Differential testing.** Every check compares two states: valid vs invalid, auth vs anon,
   user A vs user B, before vs after. A single response means nothing; a DIFFERENCE is the finding.
   (This is what caught heise.de H-01.)
2. **Ordered.** Phases run in sequence. Each phase has entry/exit criteria — no skipping ahead.
3. **Verified usage.** Every required skill/tool must leave an evidence artifact on disk.
   The coordinator produces the **usage ledger**; a skill without evidence = not done.
   "Skip" is allowed only with a written N/A reason.

## Phase 0A — SCOPE GATE (before any request)
- Read `security.txt` → record Contact, Policy, Expires. Open Policy/Disclosure pages.
- Record: program type (bounty/VDP/none), rewards, scope allow/blocklist, safe-harbor sentence, rules.
- No written scope → do NOT assume allow-all: authorization = artifact, not assertion.
  Without artifact → passive-only + program inquiry, then next target.
- Evidence: `PHASE0.md` (business understanding: fund flow, data flow, user roles, trust boundaries,
  hunting angles derived from the flows). No hunting before Phase 0 is written.
- Exit: PHASE0.md exists with scope verdict.

## Phase 0B — RECON (ordered; each step leaves a file)
| # | Action | Tools | Evidence |
|---|---|---|---|
| 1 | Subdomain enum | subfinder, amass, crt.sh | `subs.txt` (all), `live.txt` (httpx) |
| 2 | URL/JS harvest | katana, gau, waybackurls | `urls.txt`, `js.txt` |
| 3 | Endpoint extraction | grep JS for `/api/`, fetch, paths | `endpoints.txt` |
| 4 | Vuln scan baseline | nuclei (all templates relevant) | `nuclei.txt` |
| 5 | Exposed files | git-dumper, ffuf (common paths) | `exposed/` |
| 6 | Smuggling probe | `tools/smuggler/` | `smuggling.txt` (or honest N/A: egress block) |
| 7 | Scope ranking | `scope_narrower.py` | `targets-ranked.txt` |
- Exit: all files exist or N/A-with-reason recorded in ledger.

## Phase 0C — HUNT (per class, ordered by business value)
For EACH class below: load the skill, run the differential, save evidence.
| Class | Skill | Core differential |
|---|---|---|
| Auth/session | hunt-auth-bypass, hunt-session | valid vs invalid creds; pre vs post-login session; concurrent sessions |
| Password reset | hunt-forgot-password | valid vs invalid email (response + timing); token entropy/expiry |
| IDOR/BOLA | hunt-idor + `idor_harness.py` (2 identities) | user A object vs user B replay |
| Price/business logic | hunt-business-logic | tampered vs original (server recompute?) |
| Paywall/entitlement | (deep-dive) | anon vs free vs paid response bodies |
| XSS (stored) | hunt-xss | canary payload vs plain text rendering |
| SSRF | hunt-ssrf | OOB callback vs no-callback |
| SQLi | hunt-sqli | true vs false boolean; time differential |
| OAuth/OIDC | hunt-oauth | state/nonce binding; redirect_uri manipulation |
| Rate limit | hunt-brute-force (5 states) | burst vs single; known-good seed under load |
| GraphQL | graphql-audit | persisted-query vs ad-hoc; introspection on/off |
| API misconfig | hunt-api-misconfig | anon vs authenticated role boundary |
- Exit: every class has a ledger row (tested + evidence, or N/A reason).

## Phase 0D — DEEP-DIVE (the sharp part)
Pick the 1–2 highest-value flows (money flow, auth). For each:
1. Read ALL JS bundles for the flow; list every endpoint + parameter.
2. Map the state machine (guest → registered → paid → admin); test every transition,
   especially downgrades and skipped steps.
3. Invariant checklist per flow: price/quantity/currency/discount tamper, race on
   limited resources, replay of callbacks/webhooks, entitlement confusion.
4. Chain pass: feed confirmed primitives into `chain_builder.py`
   (weak entry → impact goal; mark links PROVEN/PARTIAL/UNPROVEN).
- Exit: `deepdive/<flow>/` with endpoint map + invariant test log.

## Phase 0E — CANDIDATE REVIEW (RULE 24)
Every finding = CANDIDATE. After ALL phases: review one by one, severity low→high.
- CEK-1 VALID: real bug? Reject by-design / speculative / info-only.
- CEK-2 REPRODUCIBLE: evidence file on disk ≥100B. No file = REJECT.
- CEK-3 IMPACT: who is harmed, what is lost? No impact signal = REJECT.
Only READY → draft + PDF. Evidence: `CANDIDATES.md` with per-candidate verdicts.

## Phase 0F — REPORT
One finding = one Gmail draft + one complete PDF PoC. Drafts stay UNSENT unless
the user explicitly orders sending. Program inquiries are pre-authorized to send.

## Usage ledger (MANDATORY — coordinator produces this)
`LEDGER.md` in the audit workdir, one row per required skill/tool:
`| Phase | Skill/Tool | Invoked? | Evidence file | Result |`
- Invoked?=yes requires a real evidence file path. Invoked?=no requires an N/A reason
  (e.g. "no GraphQL endpoint found in endpoints.txt", "smuggling: VM egress blocks POST bodies").
- The final report must state: X/Y skills invoked, and list every N/A with its reason.
- Claiming "all tools used" without the ledger = the audit did not happen.

## Account factory SOP (make them yourself — never ask the user)
1. Try temp-mail first (mail.tm API or similar); verify inbox receives.
2. If the target blocklists disposable domains → fall back to Gmail plus-addressing
   (`tokoman71+<target><n>@gmail.com`); fetch OTP/links via the gmail skill yourself.
3. Never invent PII (no fake real names/IDs); if a flow demands a real name → mark
   that surface not-tested with reason, do not fake it.
4. Two accounts for IDOR differential whenever the target allows (note: Gmail
   plus-addresses may normalize to one account — then record single-identity limit).
5. Passwords: generate strong random, store in `creds.json` (chmod 600) inside the
   audit workdir. Never reuse across targets.