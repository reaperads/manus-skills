---
name: codebase-bounty-review
author: Fauzi Susanto
description: "White-box bug-bounty review of a SOURCE-CODE target (GitHub repo / SDK / node / protocol codebase) where there is no live host to scan and the program forbids live testing. Use when the program's assets are repos (Immunefi Blockchain/DLT, OSS security programs) rather than websites/APIs. Adapts the 0A-0F phase model to the codebase track and integrates with bb-audit-launcher + audit-execution-discipline."
tags: [security, bug-bounty, audit, codebase, source-review, blockchain, immunefi]
metadata:
  hermes:
    version: 1.0.0
    tags: [security, bug-bounty, audit, codebase]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Codebase Bounty Review (source-only track)

Companion to `bb-audit-launcher` (the 0A-0F orchestrator) for targets whose in-scope assets are
**source repositories**, not live hosts. Example trigger: "audit exploit <Immunefi program> whose
assets are GitHub repos". Load `bb-audit-launcher` **first** (rules + gate table), then this skill.

## PART 0 — Decide the track BEFORE any tool fires

Read the program text. Route:

| Program says | Track | 0C tool layer | 0D gate |
|---|---|---|---|
| assets = GitHub repos; "no testing on mainnet/testnet"; "local forks only" | **codebase (white-box)** | SAST + dependency scan + source review | **N/A** (no HTTP surface) |
| assets = live domains | web2 (normal launcher flow) | nuclei/ffuf/… | normal |
| assets = on-chain contracts | web3 (foundry/slither) | contract scanners | N/A / fork |
| **live hosts exist BUT `security.txt`/policy forbids automated scanning, AND the product source is public** (open-source SaaS with a hosted Cloud edition — carbon.ms 2026-10) | **hybrid: source track + passive-only recon** | **N/A** (quote the clause); CT / robots / llms / OpenAPI / `.well-known` only | `N/A (policy prohibits automated scanning — quoted)` |

**Third row, in detail:** the scanner layer is **N/A, never "passed"** — same HARD RULE as
row 1, with the *policy clause* as the reason instead of the absence of a host. Quote the
clause verbatim into the risk log once (see `recon-scope-triage` → "policy EXISTS but
PROHIBITS the method") and proceed on the source track without re-raising it each turn.
Passive enumeration (certspotter CT, `robots.txt`/`llms.txt`, `openapi.json`,
`.well-known/*`) is not automated scanning and stays in play — it is also how you find the
subdomain-per-vertical split that tells you where the tenant-isolation surfaces are.
Full recipe + the bug classes this track pays on:
`references/multi-tenant-cache-scope-review.md`.

**HARD RULE (same as the launcher's vendor rules):** if the program forbids live testing, the
scanner layer (nuclei/ffuf/gobuster/dalfox/sqlmap/subfinder/naabu/httpx/katana/gau/waybackurls/arjun/
trufflehog/subzy/…) is **N/A / NOT RUN** — never "passed". Say it in PHASE_LOG. Absence of a live
host is not a scanner result.

## PART 1 — Phase mapping (0A-0F, codebase track)

- **0A SCOPE** — parse the program page: assets (repo list), reward tiers, prohibited activities,
  impact definitions (these tell you WHICH bug classes pay). Write `SCOPE.md` + `PHASE_LOG.md`
  (`_progress`/target dir), phases 0A-0F. Note `engagement_type` = bug-bounty (impact-demonstrated).
- **0B RECON (code)** — clone every in-scope repo (`--depth 1`; big Java repos may fail Windows
  checkout → see pitfalls). Map modules (LOC, entry points, newest/most-security-relevant packages).
  Pull recent history (`git fetch --depth N`) — *newest commits = least-reviewed code*.
- **0C HUNT (white-box)** — see PART 2.
- **0D GATE** — **N/A** (mark `N/A-BLOCKED` / `N/A (codebase track)`; never "passed").
- **0E FINDINGS** — `findings.json` with `validated_findings[]` **and** `observations[]`, plus a
  **coverage ledger** of verified negatives. `PHASE_LOG.md` carries the ledger.
- **0F REPORT** — per-program format. Impact-first. PoC = code path + line refs (+ runtime PoC if
  feasible). One root cause = one report.

## PART 2 — The hunt: order of operations

1. **Automated layer (cheap, evidence-first)**
   - JS/TS: `npm audit --json` (needs package-lock). Note runtime vs dev deps.
   - Go: `govulncheck ./...` and `gosec -fmt=json -out=<WINPATH> ./...` (see pitfalls).
   - Java/Gradle: `./gradlew dependencies` / OWASP dependency-check if network allows.
   - Rust: `cargo audit`.
   - Secrets/dangerous-API sweep with **ripgrep** (not Python os.walk — too slow on big trees):
     `rg -n -i -e 'BEGIN [A-Z ]*PRIVATE KEY' -e '(private_?key|secret|api_?key|password)\s*[:=]\s*"[^"]{16,}"'`
     plus sinks: `exec(|child_process|eval(|innerHTML|unsafe {|Math.random|MD5|SHA1`.
2. **Triage the automated hits.** Most are noise (Go G115 integer conversions; test keys; TLS
   `InsecureSkipVerify` *followed by* a real `VerifyPeerCertificate`). Read the body before believing any
   finding.
3. **High-value manual review** — prioritise by the program's *paid impacts*, not by LOC:
   - verification / authz paths (signature checks, quorum, allowlists) → theft / "authorize without signer"
   - proof verification (SSZ / Merkle-Patricia / IAVL / RLP) → forgery
   - **newest features** (grep recent commits; `NEW == UNREVIEWED`)
   - **the target's own docs for self-declared open issues** — `ROADMAP.md`, `docs/bugs/`,
     `docs/superpowers/specs/`, and `TODO`/`FIXME`/`not supported yet` in security code. These name
     what the vendor itself considers unfinished, so a genuinely-still-open one is a high-quality
     lead *and* pre-empts "this is by design". **Verify the current status in code before you write
     it up** — such banners are often stale (observed 2026-10: "still open — active cfcheckpt
     rejection" was fully implemented by the target version, complete with task-numbered code and
     counters; the item was closed, not a finding). Language stubs with `TODO Phase N` for a whole
     feature set (e.g. a rules engine) are usually *guarded* elsewhere — find the guard (a
     fail-closed gate that only lets the safe case through) before treating the stub as the bug.
   - stubs in security code: `rg -i -e 'fake|stub|placeholder|temporary|accepts (every|any)|return true;|not implemented|TODO' <security dirs>`
   - money paths (fees, staking, bridge/messages, balances)
   - **Soroban/Stellar + generic Rust contracts** — the five defect classes that paid in practice
     (caller-supplied argument, no-op verification, missing `require_auth`/`assert_admin`,
     fail-open guards, client-controlled identity) and the `cargo test` + `vitest` runtime-PoC
     recipe live in `references/soroban-stellar-review.md`.
4. **Confirm the isolated-defect pattern.** A strong finding is often *one* code path that skips a
   control the rest of the codebase enforces. Prove the contrast (e.g. peer verifier X does real crypto,
   the audited one does not) — it pre-empts "this is by design".
5. **On multi-tenant / RLS-backed targets, sweep the tenant-boundary code FIRST** — auth,
   claims/permissions, session and their caches — before module logic. The paying shape there is
   a *cache or memo key missing a dimension its value depends on* (user-only key holding a
   company-scoped value), because a stale value crosses the tenant boundary. Checklist, related
   shapes and the candidate-vs-filing gate:
   `references/multi-tenant-cache-scope-review.md`.

## PART 2b — Mature / heavily-audited protocols: find the UNAUDITED surface first

If the target already carries a dozen+ audits and a long Known-Issues list (common for DeFi
lending / prime-broker / L1 protocols), do NOT read the code blind — run audit-coverage gap analysis
first, or you will burn the budget on already-covered ground and re-report known issues.

1. **`SECURITY.md` is the door** (a protocol site's `/security` page links to it; pull it raw from
   `raw.githubusercontent.com`). It holds scope, tiers, the **complete Known-Issues list** (= your
   dedup map), and the **Credits** section (= the bug classes they actually pay for).
2. **Map audit PDFs → modules** (`audits/*.pdf`, extract with `pypdf`, count module keywords). Zero
   hits = unaudited = highest value.
3. **NEW == UNREVIEWED.** `git fetch --unshallow` (depth-1 hides history), then
   `git diff --stat <last-audit-tag>..HEAD -- <src>` and `git log --oneline -60`. Rank modules by
   insertions since the last audit; the bullseye is *large insertion count AND no audit-keyword hit*.
   Read commit subjects for recently-*fixed* bug classes — hunt their siblings.
4. **Known-Issues list = auto-reject list.** Grep each candidate against it (and the audit text)
   before writing up. "Accepted approximation" / "by design" doc-comments are defences, not docs.
5. Confirm the **deployed** version before claiming on-chain impact — release/pre-release scope wording
   is in `SECURITY.md`.

Full recipe, commands and pitfalls: `references/audit-coverage-gap-analysis.md`.

## PART 3 — Finding quality bar (what makes it pay)

- **Impact-first**, mapped to a named in-scope impact tier.
- **Reachability**: gated behind a feature flag / privileged account? Say so and pre-empt the program's
  own downgrade clauses ("Functionality Not Active in Production", "privileged account"). Downgrade
  yourself honestly rather than overclaim; the program text says non-active bugs are still encouraged.
- **Code = proof** for "verification is a no-op" bugs: cite the exact `return true;` line and every
  call site. A runtime PoC is often cheap even in a 300 MB repo — don't assume you must build the whole
  project: **isolated-compile** the *verbatim* production class(es) with `javac` and a shim for any
  missing annotation, then drive them from a tiny `Main`. Recipe + worked case:
  `references/isolated-compile-poc.md`; skeleton: `templates/IsolatedPocMain.java`.
- **Ship two PoC forms:** the isolated harness for YOUR evidence (`evidence/<name>-run.txt`), and a
  JUnit test dropped into the repo's own test tree for the MAINTAINER to run with their build.
- **Verified negatives are deliverables** — list them; "not tested" ≠ "clean".

## PART 4 — Pitfalls (learned)

- **Verify a surface EXISTS before calling it "remaining" — and before calling it untestable.**
  Two self-inflicted errors in one engagement (2026-10, nym-vpn-client), both erring in the
  direction of *understating* coverage:
  - The agent listed a crate called `nym-exports` as "still unexamined". **No such crate existed** —
    the name was generated from memory. Enumerate what is really there (`ls -d */` at the cargo
    workspace root, `find <dir> -name '*.rs'`) before writing any remaining/untested list.
  - The agent reported the Windows firewall as an "opaque native lib, not verifiable from source".
    The C++ source was **in the repo** at a sibling path (`nym-vpn-windows/winfw/`), so the "honest
    gap" was testable — and closed as a PASS in one pass once found.
  Rules: (1) never name a surface from memory — list the real paths first; (2) before declaring
  FFI/native code unreviewable, hunt its source: sibling top-level dirs, `.cpp`/`.h`/`.vcxproj`/
  `CMakeLists.txt`, and `build.rs` link lines (`println!("cargo:rustc-link-lib=…")` names the lib and
  usually points at its source dir); (3) if the native component is third-party-derived, say so and
  name the upstream — `winfw` is a **Mullvad** WFP fork (`mullvadguids.cpp`, `mullvadobjects.cpp`),
  which changes the prior from "unaudited" to "a widely-deployed kill switch with its own audit
  history"; (4) **when you discover a mislabel, retract it explicitly** in the deliverable and the
  PHASE_LOG — a false "untested" line is a false negative the next session inherits (and a false
  "tested" line is worse).

- **MSYS path trap (Windows):** with `MSYS_NO_PATHCONV=1`, native tools (rg/gosec/go) receive `/d/...`
  unmodified and fail ("cannot find path"). Pass **Windows** paths (`D:/data/...`) to native tools;
  pure/bash-builtins accept `/d/...`. `gosec -out=/d/...` silently fails to save → use `-out=D:/...`.
- **Huge Java repo checkout fails on Windows** (long paths): `git config core.longpaths true` then
  `git restore --source=HEAD :/`. rc=128 with "Clone succeeded, but checkout failed" is recoverable.
- **`delegate_task` for source review is unreliable here** — 600 s timeout, work discarded. Do the
  review directly.
- **Python os.walk sweeps on 300 MB repos time out** under Defender — use ripgrep, or run in background.
- **gosec on a whole Go repo compiles every `examples/` package → very slow.** Scope it:
  `gosec … ./sdk/...` with `-exclude-dir=examples,tck`.
- **Don't report dependency CVEs as findings** without a reachable impact on the in-scope asset.
- **A single very long heredoc/command gets truncated by the command channel.** Writing a long
  report or PoC file as one `cat > f <<'EOF' … EOF` fails with a bare shell parse error
  (`unexpected EOF while looking for matching \`''\`) and **nothing executes** — not even an
  earlier `mkdir` in the same `&&` chain, because the parse fails before the first command runs.
  Chunk it: several `cat > f <<'EOF'` / `cat >> f <<'EOF'` appends, or write the body as separate
  per-file pieces and let a small script assemble them. Keep each chunk to a few KB. A bare parse
  error (not a tool error) on a long write is this, every time.
- **The same size limit bites every WRITE path, not just the heredoc.** A tool call whose *arguments*
  are very large — a single `write_file`/`patch` carrying a whole multi-KB document, or a big
  `file_content` blob — can stall the request stream so the call never lands at all (observed
  2026-10: one oversized write "timed out before it could be delivered"; nothing changed on disk).
  Split the work: create the file small, then append in several `patch`/`write_file` calls, each
  comfortably under ~8K tokens of arguments. A stalled/undelivered call is silent — verify the file
  exists and grew afterward rather than assuming the write happened.
- **A value that reads back as `***` was redacted by the output layer, not corrupted in the file.**
  When a source constant or env-shaped value in tool output shows `***`, do not conclude the source
  is malformed or "empty" — it is the harness redacting it. Read around it (surrounding lines,
  call-site usage) and reason from that; only treat it as a real value if the behaviour contradicts
  it.
- **Java/Gradle: use the repo's exact JDK.** Read `gradle/toolchain-versions.properties` (e.g.
  `jdk=25.0.2`). A wrong JDK fails the buildSrc/convention plugin (JDK 21 rejects the unnamed-variable
  `_`, a JDK 22+ feature). Install that JDK and pass `-Dorg.gradle.java.home=<jdk-dir>`.
- **Gradle user home must share a drive with the project (Windows).** A split-drive checkout
  (project on `D:`, `~/.gradle` on `C:`) dies in the PBJ compiler with
  `IllegalArgumentException: 'other' has different root` (`Path.relativize` across roots, because the
  plugin adds classpath jars to the source-root set). Fix: put `GRADLE_USER_HOME` on the same drive as
  the repo (copy the cache there). Directory junctions/symlinks do NOT help — Gradle canonicalises the
  project path back to its real drive.
- **Get the real Gradle project path from `./gradlew projects`.** hiero names projects by artifact
  (`:app-service-clpr-impl`), not by directory (`:hedera-node:hedera-clpr-service-impl`).
- **Runtime > static when the finding is "X returns true".** Write a JUnit test that drives the REAL
  production path end-to-end (here `verifyBundle(...)` → `VerifiedBundle`) and run it with the node's
  own test task; cite the JUnit XML (`tests=N failures=0`) as evidence. Standalone harnesses over
  copies of production classes are a weaker, secondary proof.
- **Rust/Soroban PoC: crate dir != package name for `-p`.** Directories are snake_case
  (`zk_credit_verifier`), packages hyphenated (`zk-credit-verifier`). `cargo test -p zk_credit_verifier`
  dies with `package ID specification ... did not match any packages; help: a package with a similar
  name exists: zk-credit-verifier`. Read `[package] name` from the crate's `Cargo.toml`.
- **First Rust test build of a fresh workspace is slow (~2–8 min).** Run it with
  `background=true, notify_on_complete=true`; later `cargo test -p <crate>` runs reuse the cache in seconds.
- **Next.js/TS PoC: assert by KEY PRESENCE, not `JSON.stringify`.** `JSON.stringify(call.args)` on a
  Drizzle `set({...})` throws `TypeError: Converting circular structure to JSON` (PgTable/PgUUID close a
  cycle). Use `"totalLiquidity" in c.args[0]`.
- **The target's OWN tests are corroboration gold.** Repo tests frequently encode the insecure behaviour
  (`__tests__/api/cron/liquidation.test.ts:88` "runs without auth when CRON_SECRET is unset";
  `__tests__/api/kyc/webhook.test.ts:196` "accepts ... when no webhook secret is configured"). Cite the
  line numbers — it pre-empts "this is by design". Full recipes: `references/source-only-poc-harness.md`.

## PART 4b — Multi-language stacks: Rust/Soroban + Next.js APIs

DeFi repos often ship a `contracts/*` Soroban workspace **plus** a Next.js `app/api/*` surface.
Two extra layers pay off; full recipe + worked example in
`references/rust-soroban-and-nextjs-codebase-review.md`.

**Runtime PoC for Rust/Soroban (real evidence, cheap):** drop a `#[test]` into the crate's own
`src/test.rs` (already declared `mod test;`) and run it with the project's toolchain.
- **`-p` takes the Cargo PACKAGE name — NEVER guess it from the directory or from a rule of thumb.**
  Hyphenation is per-crate and inconsistent inside one workspace: `contracts/zk_credit_verifier` is
  package `zk-credit-verifier`, but `contracts/usdc_lending_pool` is package `usdc_lending_pool`
  (underscore!). Both mistakes look identical: `package ID specification … did not match any packages`.
  Read `name =` from that crate's `Cargo.toml` (or take the cargo error's own suggestion) before running.
- The first `soroban-sdk` build compiles ~200 crates ≈ 4 min → run in **background with notify**;
  a 600 s foreground call times out mid-compile.
- `env.mock_all_auths()` in the harness mocks `require_auth`, so a passing PoC proves the *logic*
  (a fabricated argument is accepted), not the auth layer — say so honestly.
- The repo's OWN test suite is evidence: a test that asserts the insecure behaviour (e.g. an arbitrary
  caller receiving a payout) is a ready-made finding — cite it beside your PoC.

**Soroban contract bug-class checklist (order of value):**
1. `caller.require_auth()` present but `assert_admin`/`assert_multisig_admin` **absent** on money fns.
2. Invariants evaluated over **caller-supplied arguments** instead of stored state (collateral entries,
   `yield_amount`, `bid_amount`, score/tier).
3. **"Verification is a no-op"**: a comment claims crypto (proof/signature) validation, the body only
   checks length / non-zero bytes, and the fetched provider key is unused (`_pubkey_hash`).
4. Cross-contract reward/payout fns must pin the caller to the expected contract
   (`if caller != lending { return 0 }`) — flag the ones that don't transfer from the contract balance.
5. `if (secret) { check }` guards that **fail open** when the env var is unset.

**Next.js API white-box checklist:**
- Per-route auth-guard matrix: grep each `app/api/**/route.ts` for
  `requireApiAdmin|requireApiUser|requireTradeVaultAdmin|...` and hunt the odd route out
  (e.g. a `requireAuthenticatedUser` where siblings use `requireApiAdmin`).
- Webhook signature verification wrapped as `if (header) {...} else if (!isTestnet) reject` ⇒ logic is
  effectively closed when the deployment's passphrase includes "Test" → attackers just omit the header.
- HMAC verifiers that `return true` when the secret env var is missing.
- Unauthenticated POST routes whose handler builds+signs a transaction with a server key
  (`Keypair.fromSecret(ADMIN_SECRET_KEY)`) — check whether that key is ALSO the on-chain contract admin.
- Rate limiters that trust `x-forwarded-for` / `x-real-ip` and fail open when the shared store is down.

- **Cargo package names are hyphenated, not the directory name.** `contracts/zk_credit_verifier` is
  package `zk-credit-verifier`; `cargo test -p zk_credit_verifier` fails with "did not match any
  packages". Use the hyphenated name (or read the crate's `Cargo.toml` `name`).
- **First Soroban build is slow (~4–8 min compiling `soroban-env-host`).** A foreground `cargo test`
  trips the 600 s tool timeout mid-build. Launch `background=true, notify_on_complete=true`, then
  `process(action=wait)`; subsequent runs are seconds.
- **`npm ci` on a large Next.js repo can take ~8 min.** Background it. Targets usually ship a
  `__tests__/helpers/fake-db.ts` chainable DB stub + `vitest.config.ts` — reuse them for API PoCs
  rather than hand-rolling mocks. Mock any module that imports `"use client"` browser-only code
  (e.g. a Stellar wallet kit) so the route imports cleanly under the node vitest env.

## PART 4b — Validation & delivery order (user-mandated)

On a source-only review the user requires this order — do not jump straight to a report:

1. **Validate first.** Re-read every finding from disk (never from memory) and re-run its PoC
   (`cargo test` / `npx vitest`) before claiming anything. Re-run the crate's FULL suite to prove the
   added PoC breaks nothing (e.g. `cargo test -p lending` → 108/108 + proptest).
2. **Then draft + complete PoC.** Produce the disclosure draft (external artifact: **English, with a
   short introduction** — name/context/channel) and a *runnable* PoC per finding, dropped into the
   repo's own test tree (Rust `src/test.rs`, JS `__tests__/`) **plus** a copy under `_audit/pocs/`.
3. **Hand over for MANUAL user check** before any submission. Do NOT send or place in Gmail Drafts
   until the user says GO.
4. **Only then continue hunting** other surfaces.

Honesty bar: label runtime-validated findings `validated-runtime`, code-only ones `code-verified`;
where the target's own tests *intend* a fail-open as "dev mode", say so and still report it (note the
missing `NODE_ENV` guard) — don't inflate, don't drop.

## PART 5 — Integration

- Start with `bb-audit-launcher` (rules, stop-rules, coverage-claim gate); this skill supplies the
  codebase-track adaptation only.
- Execution rules: `audit-execution-discipline` (verify from disk, not from memory).
- Reporting: `bug-report-delivery` / `report-writing`; for Immunefi use the program's impact table.
- Delivery to email draft (if asked): see the operator's `~/check_basabasi_email.py` for IMAP creds;
  APPEND to `[Gmail]/Draf` (draft folder), never send. The full draft workflow (locale folder, X-Unsent,
  verify-by-refetch, load-secret-at-runtime) is in the `email-automation` skill — load it instead of
  re-deriving it.

## PART 6 — Report hygiene & claim discipline (user-mandated)

Direct user corrections from a real engagement — a report that violates these loses credibility with the
triager, regardless of how good the finding is.

- **Never claim a result you did not execute.** If you added a test/script but did not run it, say exactly
  that and label the outcome *expected*, not *observed*. "Test PASSES on current source" while the build was
  never run is a self-contradiction — and it directly contradicts the coverage section that says "no build
  was run". The triager checks this.
- **Keep the whole document internally consistent.** Finding text, PoC section and coverage/residual-gaps
  section are read together. Re-read the full report for contradictions before saving/sending.
- **The PoC must drive the REAL production entry point end-to-end** — not a helper class or the stand-in's
  own unit test. A test on the fake proves nothing about the shipped path. Wire the real path, show it
  accepts the forged input, and ship two forms: the executed test in the repo's own tree (cite the JUnit
  XML: `tests=N failures=0 errors=0`) plus the isolated harness. (Cross-ref: PART 3, PART 4.)
- **No personal identity in the report header.** Bug-bounty platforms already bind the report to the
  submitter's account; name/alias/email in the document is unwanted disclosure and pure noise. Header =
  program / asset / date / revision only.
- **Do not pad with low-value observations.** Dependency-advisory dumps, well-known public test keys,
  and informational nits lower credibility and invite "N/A". Either drop them or compress to ONE line
  under a clearly-labelled "Notes (informational, not part of the finding)" header.
- **Follow the impact chain, but file it under the ORIGINAL root cause.** A no-op verification can be
  reachable *only* through downstream code, which makes it look like a second finding. Example:
  `zk_credit_verifier` accepts a 1-byte "proof" (the root cause), and separately
  `borrower_reputation::apply_zk_tier_upgrade` raises `reputation_score` to ≥1000 while
  `governance` uses that score directly as voting power — so the same defect escalates to governance
  capture. That is **impact amplification for TL-03**, not a new report: one root cause = one reward.
  Write the chain into the affected impact/severity section instead of minting a duplicate.
- **When a candidate finding is disproved, say so and keep the artefact.** A code shape that matches a
  known bug class can be dead on the target's runtime (see the Soroban re-entry guard). Convert the PoC
  into a `#[should_panic]` regression test and log it under VERIFIED NEGATIVES in the PHASE_LOG —
  that prevents the next session (and the next reviewer) from re-deriving and re-reporting it.
- **A self-contained PDF must EMBED its PoC — never cite an "attached PoC" file you did not attach.**
  Observed 2026-10: three per-finding PDFs referred to "the attached PoC `X.py`" while only the PDF was
  ever attached, so the deliverable contradicted itself. Fix: inline the PoC source into the PDF as an
  appendix, and have the delivery check assert a marker string from the PoC survives into the rendered PDF.
- **Verify delivery by re-reading it.** After writing the report to its channel (file, email draft, PDF),
  re-fetch and confirm the content actually landed (e.g. re-open the saved Gmail draft and assert key
  strings are present) instead of trusting the write call.
- **ONE finding = one report = one draft/email = one PoC.** Never bundle N findings into a single
  disclosure document. Observed correction (2026-10, TrustLend): the agent wrote ONE email draft holding
  all 12 findings; the user rejected it — *"perbaiki draftnya dulu, kan sy udh blg 1 draft 1 email 1 poc"* —
  and the redo was: delete the combined draft, emit one draft per finding, each with its own PoC command.
  Bundling is allowed ONLY for a genuine chain attack (A enables B). The delivery mechanics (per-finding
  draft loop, delete-then-append, Gmail subject-fold verification pitfall) live in the `email-automation`
  skill — load it for the send/draft step.
- **Every finding carries its own runnable PoC.** If a finding only has a "code path" description, add the
  missing runtime test before writing the report (see `references/source-only-poc-harness.md`). In the
  TrustLend pass five findings were still code-path only; adding 5 PoCs (2 Rust + 3 vitest) took the set to
  12/12 runtime-validated, which is what makes the report land.
- **Before claiming a follow-on / escalation impact, read the port's WRITE-path preflight — and if it
  blocks the chain, correct any earlier report you already wrote.** A read-path divergence ("the wallet
  credits units the chain does not") looks like it escalates to fund loss via "the user then spends the
  phantom" — so check the send/act path before writing that sentence. (Observed 2026-10: the same wallet
  refuses to build a send unless EVERY asset input is confirmed by an indexer to hold exactly the recorded
  quantity and asset id — `AssetInputCheck` → `VERIFIED`, else `MISMATCH` ⇒ set aside, `UNAVAILABLE` ⇒
  refuse — so the phantom cannot be spent and the burn chain never materialises. The claim had already gone
  out in an earlier report; the honest move was to **surface the overstatement unprompted and offer an
  erratum**, not to wait to be asked.) A fail-closed gate on the write path **caps severity but does not
  close the divergence** — report the divergence, state the gate, and stop short of the escalation.

## PART 7 — Source-only PoC recipes (any stack) + multi-finding delivery discipline

### Runtime PoCs beat code-path claims — build one PER finding
Each finding ships its OWN runnable PoC, dropped into the repo's existing test tree so the maintainer
runs it with the project's own build. Worked examples (actual code + commands + evidence):
`references/source-only-poc-recipes.md`.

**Rust / Soroban contracts (`cargo test`)**
- Drop `#[test] fn poc_<finding>()` into `contracts/<crate>/src/test.rs` (the crate already ends with
  `#[cfg(test)] mod test;`). Reuse the crate's own `setup()` helper — it calls `env.mock_all_auths()`.
- Run from `contracts/`: `cargo test -p <crate> <poc_name>`.
- ⛔ **`-p` takes the Cargo PACKAGE name — read `Cargo.toml`'s `name =`, never infer it.**
  Inconsistency is real: `zk_credit_verifier/` → `-p zk-credit-verifier` (hyphen) but
  `usdc_lending_pool/` → `-p usdc_lending_pool` (underscore). Wrong guess ⇒
  *"package ID specification … did not match any packages"*.
- First build compiles soroban-env-host (~3-6 min cold) — run it in the background, not foreground.
- **Make the PoC PRINT the exploit values, not just assert.** A bare `... ok` is weak evidence and the
  user will reject it (*"kurang lengkap … jgn hanya keterangan singkat"*). Print principal/balance
  before→after, tier granted, amounts, and a final `RESULT: <bool>`. Recipe: a `#![no_std]` crate has no
  `println!` in scope — add `extern crate std;` immediately after `#![cfg(test)]` in the crate's
  `src/test.rs`, then call `std::println!`, and run the single test with `-- --nocapture`.
- ⛔ **`soroban_sdk::Address` does not implement `Display`.** `{}` with an Address argument fails to
  compile (`error[E0277]`). Use `{:?}`. This bites on any "print the attacker address" line.
- **Capture transcripts per finding, not one merged log:** redirect each run to `evidence/raw/<ID>.txt`
  (`cargo test -p <pkg> <poc> -- --nocapture > …/TL-XX.txt 2>&1`) so each finding owns its evidence.
  Vitest `console.log` output carries ANSI escapes — strip `\x1b\[[0-9;]*[A-Za-z]` before parsing or
  your line filters silently match nothing.

**Next.js / TypeScript (`vitest`)**
- Drop PoCs in `__tests__/poc/*.test.ts`; run `npx vitest run __tests__/poc`. The repo's
  `vitest.config.ts` already aliases `@` → root and excludes `e2e/**` + `contracts/**`.
- Reuse the repo's `__tests__/helpers/fake-db.ts` (a thenable query-builder stub) for any Drizzle
  route: `vi.mock("@/lib/db/client", () => ({ getDb: () => db }))`, then `db.queue(result)` in the
  exact order the route awaits. Mock adjacent heavy modules (`@/lib/stellar/*`, `@/lib/contracts/*`,
  `@/lib/monitoring/*`) so the test isolates the auth/authz branch, not the network.
- ⛔ **Never `JSON.stringify` a Drizzle builder's `args`** — table/column objects are circular →
  *"Converting circular structure to JSON"*. Assert the shape instead:
  `c.method === "set" && "totalLiquidity" in (c.args[0] as object)`.
- ⛔ **`npm ci` first** — a fresh clone has no `node_modules` (~8 min); the vitest run needs it.

### Multi-finding delivery: 1 finding = 1 PDF = 1 draft = 1 email = 1 PoC
The user's HARD rule (canonical detail lives in the `email-automation` skill). When an engagement
yields N findings: **N drafts, N PDFs, N PoCs, N emails — never one combined draft holding all of
them.** This session built a single draft containing all 12 findings and the user rejected it
(*"kan sy udh blg 1 draft 1 email 1 poc"*). Only a genuine CHAIN attack may be bundled.
- **Sequence the user expects:** validate the findings → THEN produce the per-finding draft + complete
  PoC → user reviews manually → only then continue hunting. ("Validasi dulu, baru draft + PoC.")
- **"Pastikan divalidasi ulang" = re-run every PoC fresh** (cargo + vitest) and capture transcripts.
  Never assert a result from memory.
- **Regenerate the whole draft SET idempotently:** delete every prior draft matching the subject
  prefix, then append all N (folder / `X-Unsent` / attachment mechanics → `email-automation` and
  `reportlab-security-pdf`).

### Contract + API hunt patterns that paid here
- **A security decision that reads a CALLER-SUPPLIED value** — collateral, yield, price, count. The
  bug is trusting the argument instead of the stored/measured value (Soroban `create_loan_request`
  checked `request.collateral_entries`, not the borrower's stored entries).
- **"Verify" functions that only check a shape** — non-empty bytes, non-null, non-zero. A step labelled
  *cryptographic proof validation* that only scans for one non-zero byte is a no-op (`zk_credit_verifier`).
- **A money function that calls `require_auth()` but NOT `assert_admin`** while the rest of the contract
  gates admin actions — the odd-one-out contrast IS the proof (`collect_fees`, `treasury::distribute`).
- ~~State written AFTER an external call, no reentrancy guard~~ **NOT exploitable on Soroban —
  do not report it.** Soroban's host enforces a *contract-level* re-entry guard: re-entering a contract
  mid-execution aborts the whole call with `Contract re-entry is not allowed`
  (`Error(Context, InvalidAction)`). `multisig_admin::execute`, `governance::execute` and
  `usdc_lending_pool::withdraw` all do dispatch/transfer BEFORE writing their state — the shape is a
  smell, but a hostile target/token that calls back is rejected by the host. **Verified 2026-10:** a
  purpose-built re-entrant mock (`contracts/multisig_admin/src/test.rs::poc_execute_reentrancy_action_runs_twice`)
  aborted with exactly that error. Before flagging any state-ordering bug, ask "can the callee call
  back?" — on Soroban the runtime answers *no*. (On EVM this same shape IS a real bug; don't import
  that reflex into a Soroban review.) Keep the PoC as a `#[should_panic]` regression marker instead of
  deleting it — it documents the negative and keeps the repo suite green.
- **Fail-open auth guards** — `const secret = env.X; if (secret) { check }` skips the check entirely when
  the env var is absent (no `NODE_ENV` guard), and `if (!secret) return true` verifiers. Grep EVERY
  cron/webhook route for this shape and enumerate the whole set.
- **Conditional signature verification** — `if (sig) {...} else if (!isTestnet) reject` makes a
  testnet/default deployment accept unsigned events that credit state (`webhooks/sep31`).
- **Rate-limit key from a client-controllable header** — `x-real-ip` / `x-forwarded-for`. Prove the
  bypass A/B: same IP → 429 after the window; rotating the header → never limited.

### Endpoint-client / privileged-daemon review (native app, NOT a web API)

When the in-scope repo is a **client + privileged daemon** (VPN client, sync agent, updater,
security tool), the auth surface is the **local IPC channel**, not HTTP. This is a different
checklist from the web/contract patterns above, and it is easy to skip past while focused on the
client's networking code.

- **Fail-open client verification (the one that pays).** The daemon authenticates connecting
  clients by verifying the *client process is vendor-signed* — but a helper like
  `skip_authentication_checks()` returns **true** when the *daemon's own* signature cannot be
  verified, and the caller then sets the auth material to `None`, dropping client verification
  entirely. Grep `skip_auth|skip_authentication|self_is_signed|verify_certificate_signature` and
  READ THE FAIL-OPEN BRANCH — the happy path looks fine. Correct design is fail-*closed*.
  (Observed: `nym-ipc/src/authentication/{windows,macos}.rs` — identical shape on both platforms.)
- **Over-permissive IPC ACL/DACL.** The named pipe / socket grants READ+WRITE to
  `WellKnownSid::World` = **Everyone (S-1-1-0)**, so the fail-open branch above is reachable by ANY
  local user and the ACL provides no second line of defence. Grep
  `WellKnownSid|SecurityDescriptor|AbsoluteSecurityDescriptor|Trustee|ExplicitAccess|0o[0-7]{3}`.
- **Cite the platform contrast** — it pre-empts "this is by design". Linux (`SO_PEERCRED` → uid +
  vendor group membership, else a polkit prompt) is fail-*closed*; the inconsistency between
  platforms IS the argument.
- **Check the store layer too** (cheap, often clean): on-disk secret file modes (`0600`), parent dir
  (`0700`), keyring vs plaintext. Note it as a verified negative when it holds.
- **Severity discipline:** this is conditional on an unsigned / mis-signed daemon, and shipped builds
  are signed ⇒ LOW/MEDIUM. State the precondition and the affected population; do not inflate it to
  a Critical "any local user owns the VPN".

### Privacy / VPN client — leak-surface + swallowed-error review

Same native-client track, different payload: for a VPN/privacy client the paying impact is a
**traffic or DNS leak**, so review the *protections*, not just the auth.

- **Enumerate every swallowed-error site, then check each for a missing `return`.** Highest-yield
  grep on this codebase class:
  `rg -n "if let Err\(|inspect_err|trace_err_chain|\.ok\(\)|unwrap_or\(Ok\(\(\)\)\)" <state-machine dir>`
  For each hit ask: does the branch `return` / transition state, or does it only log? A log-only
  branch sitting among siblings that DO return is itself the defect — **the sibling set is your proof
  it is a bug, not a style choice.** (Observed 2026-10: `connected_state.rs` logs
  `"failed to enable dns forwarding"` with no return, while `connecting_state.rs` `return`s
  `ErrorState` and `error_state.rs` uses `.inspect_err(..).map_err(?)`.)
- **Check the CALLEE too — double fail-open is common.** A helper declaring `Result` may be
  *incapable* of returning `Err`:
  `if tx.send(..).is_ok() { rx.await.ok().unwrap_or(Ok(())) } else { Ok(()) }`
  discards the inner error AND treats a dead worker as success. When the callee always returns `Ok`,
  the caller's `if let Err` guard is **dead code** — say that explicitly; it is the finding.
- **Look for the "resource is live but unconfigured" shape.** If the socket/handle is bound at
  `spawn()` and its address is published *independently* of the config step, a failed config leaves
  the system pointed at a live-but-misconfigured endpoint → outage, or fallback outside the tunnel.
- **Check the apply/set SIGNATURE, not just the call site.** A helper declared `fn … -> ()` on a
  security-critical config path **cannot express failure** — every per-item error is log-only, so the
  caller's guarantee is empty. Read the *other branches* of the same caller: an intra-function
  asymmetry (`save(..)?` on the re-apply branch vs log-and-continue on the first-set branch) is the
  fix-it argument, and if the sibling `reset()` accumulates a `first_error`, the codebase demonstrably
  knows the pattern. (Observed: `nym-dns/src/macos.rs` — `apply_desired_state` returns `()`;
  `apply_new_config`'s `None` branch returns `Ok(())` unconditionally.)
- **Classify swallowed calls by security ROLE, not by count.** If the calls that *prevent* the leak
  are the swallowed ones while a benign one propagates, **the diff is simultaneously the proof and the
  impact analysis** — you don't argue severity separately. Learn each platform call's semantics before
  writing the impact paragraph (systemd-resolved `SetDomains(link, &[(".", true)])` = route *every*
  domain to this link + default-route flag; `disable_dot`; macOS `DnsSettings::save`). Enumerate
  **every** backend — Linux ships both `systemd-resolved` and `resolvconf`, each a separate candidate
  with its own semantics; do not stop at the first backend you read.
- **Kill switch must fail CLOSED.** Confirm the error path lands in a *blocked* state, not a bypass:
  check the policy enum (`Connecting|Connected|Blocked`) and that the error state itself applies
  `Blocked`. A firewall-apply failure that continues to connect is Critical-class.
- **Dual-stack default-deny.** An IPv4-only block-all on a dual-stack host is an IPv6 leak. All
  three platforms have now been verified — use these as the checklist:
  - **Linux:** nftables table family must be `inet` (covers v4+v6) with `Policy::Drop` on
    in/out/forward.
  - **macOS:** a pf `block drop all` with no family qualifier (matches inet+inet6).
  - **Windows:** WFP filters on **all four** ALE layers — `FWPM_LAYER_ALE_AUTH_CONNECT_V4`,
    `ALE_AUTH_RECV_ACCEPT_V4`, `ALE_AUTH_CONNECT_V6`, `ALE_AUTH_RECV_ACCEPT_V6` — added as
    match-all (`libwfp NullConditionBuilder`) at `wfp::FilterBuilder::WeightClass::Max`, in BOTH
    the session and the persistent variant. Only v4+v6 connect+accept at Max weight is a pass.
  `enable_ipv6=false` should *remove IPv6 from the allow-lists*, not just flip a separate switch.
- **The vendor's own leak comments are a map.** In-code notes like `"Hyper-V/WSL may leak in blocked
  states"` or an Apple-services PF-bypass workaround point at the areas worth probing — and at
  runtime toggles that weaken the control (e.g. an env var that disables the block rule: same shape
  as the fail-open auth above). Worked casebook of these shapes:
  `references/native-client-fail-open-casebook.md`.

## PART 8 — Reference-implementation differential review (ports, forks, reimplementations)

When the target is a **port / fork / re-implementation** of a known upstream (a wallet, a protocol
client, a consensus/asset library, a mobile app wrapping a C core), the highest-yield move is not
reading the port in isolation — it is **cloning the upstream the port cites and diffing behaviour
function-by-function**. Every divergence from the reference is a candidate finding, and the port's
own comments hand you the map. This is the technique that produced **both** new findings in a
heavily pre-audited Android wallet (2026-10): a fail-closed LOW from the reference's *success* path
(F4) and a HIGH false-positive-receive from its *error* path (F5) — same function, and the error
path was the exploitable one.

1. **Find the reference.** Grep the target for citations: `Ported from`, `confirmed vs`,
   `matches <X>`, `see <file>.cpp:NNN`, `Ported from RenzoDD/… BitIO.cpp`. The cited repo is your
   reference. Clone it `--depth 1`.
2. **Map function↔function.** For each ported unit, locate its counterpart in the reference.
3. **Compare the semantics that can differ:** bit/field widths, condition **scoping** (does the
   check carry the operation / type / version guard?), loop bounds and stop conditions, defaults,
   and overflow behaviour.
4. **Strongest signal = the port ALSO contradicts itself.** If module A scopes a rule to an
   operation and module B (fed by A's output) does not, you have an internal inconsistency *plus* an
   external divergence — that pairing pre-empts "this is by design". Cite both sides.
   (Observed: `DigiAssetDecoder.kt:241` sets `isBurn` for a transfer instruction to output 31 with
   no operation guard, while `AssetTxQuantity.kt:139` correctly scopes the same marker to BURN.)
5. **Check test coverage of the divergent branch.** Grep the test tree for the exact construct
   (the flag name, `outputIndex = 31`). If the tests only ever build it with the flag hardcoded —
   exercising one branch and never the divergent one — the divergence is uncovered. That is part of
   the finding.
6. **PoC = two-sided line citations + a deterministic simulation.** Exact `file:line` on the
   reference side and the target side, plus a small arithmetic/behaviour simulation that
   re-implements both branches and prints the divergent totals. Recipe + worked case:
   `references/reference-differential-review.md`.
7. **Diff the reference's ERROR / ABORT paths, not just its success semantics** — this is the
   highest-yield extension of the technique, and it found the bigger bug of the pair. A port that
   mirrors only the happy path will credit state the reference *discards*. Read every `throw` /
   `catch` / early `return` / `break` in the reference function and ask **what the reference's state
   is after it fires**. (Observed 2026-10, same function as F4: the reference's
   `decodeAssetTransfer` throws `exceptionInvalidTransfer` on any instruction naming a non-existent
   output, and its `catch` **clears every output's assets**, restores the inputs, and lets the
   trailing loop credit the whole input amount to the **last** output. The port has no
   whole-transfer validity step — it credits each in-range instruction independently — so it shows a
   recipient units the chain places at the sender's change output: a **false-positive receive**, the
   class the program names as HIGH, versus the fail-closed LOW of the success-path divergence.
   Same reference function, same technique; the *error* path was the exploitable one.)
   **Make it a checklist, not one look.** F5 was the *first* abort trigger; a later pass on the same
   function found a second (F6). Enumerate EVERY abort path in the reference function and check the
   port models each:
   - *argument / instruction invalid* (index out of range, bad count) → reference aborts, clears
     every output, and drops the remaining input units on the **last** output (F5).
   - *rule / permission failure* → the reference's `checkRulesPass()` throws `exceptionRuleFailed`
     and the handler clears every output; the port gated that rule on the **SEND** path only and
     never evaluated it on the **credit** path (F6). A rule-bound asset's transfer therefore
     credits units the chain wiped.
   - *pre-classification precedence* → the reference runs `decodeKYC` / `decodeExchangeRate`
     **before** the asset path and `return`s early, so a tx it classifies as another kind is never
     credited as an asset. A port with no such pre-classification diverges. **Unproven here**
     (the exchange-rate matcher needs output[1] to be a watch/exchange address) — record it as an
     unproven candidate, never as a finding.
   **Generalises to:** *a control the port enforces on the WRITE/send path but not on the
   READ/credit path is a bug class by itself.* Grep every gate the port applies before *acting*, then
   ask whether the same condition also governs *accepting* state. (Such a gate only caps severity —
   it does not close the divergence.)
8. **Align the two index spaces before comparing anything index-based.** Establish whether the
   port's output/input list is the **raw** list or a filtered one by reading the bridge/serializer
   that builds it — do not infer it from a comment. (Here `jni_asset.c`
   `getTransactionOutputsForHash` emits **all** outputs with their raw indices, so
   `outputCount == _outputs.size()`. Without that check, "the port uses a shifted index space" is
   untestable — and a comment elsewhere in the port claimed the opposite.)
9. **Also diff the port against its OWN pinned spec — the repo's `docs/…` canonical-rule document,
   not only an external reference.** A reimplementation of a consensus/wire format usually ships a
   document the code cites by name ("see docs/superpowers/specs/…", "spec §3.2"). Where that
   document declares a rule **CANONICAL (consensus) — PINNED** and the code implements something
   *stricter or looser*, that mismatch is a finding **before** you even have the upstream in hand —
   and the inline comment is usually the confession. (Observed 2026-10, DigiDollar: spec §3.2 says a
   DD output is "exactly 34 bytes beginning with `OP_1(0x51)`", while `BRDigiDollar.c:219` *also*
   requires `script[1] == 0x20`, and the comment right above admits "Requiring the second byte too
   keeps a 34-byte OP_1 script that is not that exact form from binding to an amount slot."). Grep
   the doc for the rules the code implements — counters/ordinals, ordering, widths, skip conditions
   — and compare operator-for-operator; a **counter that advances on a different set of items** is
   the highest-yield shape, because everything after the divergence is mis-bound. (Cents here bind by
   *output ordinal*, so a stricter test shifts `k` and every later output reads the wrong amount
   slot → false-positive balance.) Frame the fix as **"make spec, comment and code agree"** — you do
   not have to decide which side is right, and either way it is a real inconsistency.
   - **Gate the severity on how the divergent INPUT can reach the chain.** The F7 trap is a
     non-standard output (34-byte script, first byte `OP_1`, second byte not `0x20`), which default
     relay policy drops, so it only lands in a block if a miner includes it ⇒ **MEDIUM**, and say that
     gate out loud instead of claiming HIGH. (Same discipline as PART 3 reachability.)
10. **Check the port's TRUST SOURCES for the same datum — and whether it treats them alike.**
   A port usually carries one *authenticated* view of a datum (derived from the chain/protocol) and
   one *claimed* view (from a document or a service). The paying shape is **asymmetric trust of the
   same field**: the port correctly refuses the untrusted source, then accepts the same
   unverifiable string from a *different* third party.
   - Observed 2026-10 (Android wallet, F8): `AssetMetadataService` states in a comment that an
     asset's `issuer` must never be read from the metadata document — "the easiest thing in the
     file to forge" — and `provenIssuerOnly(proven, claimed)` ignores `claimed` entirely (so a
     missing proven value renders no row: *absent beats wrong*). Yet on the **provider** path the
     provider's own `issuer` string is passed into the **`proven`** slot
     (`AssetMetadataService.kt:180,195` → `:317 issuerAddress = provenIssuerOnly(proven =
     provenIssuer, claimed = null)`), and `updateIpfsFacts` writes `issuerAddress` unconditionally
     (`AssetMetadataDao.kt:35-48`). A provider that lies forges the attributed issuer ⇒ MEDIUM.
   - **For every datum the UI presents as authoritative, ask: where does it come from, and can the
     client re-derive it independently?** Grep the native/bridge surface for the matching
     `derive*` (here: `deriveIssuanceAssetId` existed, but **no** issuer derivation — so the
     wallet could not check the string at all). If no independent derivation exists, the only
     honest options are to omit it or label it third-party-claimed; rendering it inside the
     authoritative field is the bug. **The port's own distrust comment is the argument** — quote it
     beside the provider line, so the finding reads as "you already applied this rule to the other
     source".
   - **The cleanest reachable case usually needs no adversary trickery.** Pass-1 (authenticated
     source) failing for an ordinary reason — a gateway down — drops the client into Pass-2, where
     the *authenticated* payload (CID/name/image all verified) still carries a *claimed* issuer.
     Authenticated content + forged attribution in one row is the strongest framing.
   - **Put the trust boundary in the severity line**: *who must misbehave* decides the tier. A
     cert-pinned first-party provider must itself lie ⇒ MEDIUM; an unauthenticated network peer
     that can inject the response ⇒ HIGH. **Verify the pinning before claiming a MITM path**
     (`DigiScopePins.kt` / `DigistampPins.kt` here — all provider hosts pinned, so no MITM).

11. **Check whether a SIBLING path in the same codebase already verifies the same datum — and whether
    the path you are reading skips it.** The strongest form of "the port misses a control" is not "the
    reference does X and the port does not"; it is **"the port does X on one path and not on the sibling
    path handling the same datum"** — the contrast is internal, so "by design" is dead on arrival.
    Enumerate every consumer of a datum before judging any one of them.
    - Observed 2026-10 (Android wallet, F9): `ChainReconciliationService.fetchTransactionBytes` documents
      and enforces *"every transaction is accepted only when its bytes hash to the id asked for"*
      (`NativeBridge.rawTransactionId(bytes) == txid`), and `MultiEndpointAssetClient.getRawTransaction`
      enforces the same. The history-recovery import in the SAME file
      (`importPlannedHistory` → `register(bytes, raw.blockHeight, raw.blockTime)`) never compares the bytes
      to the planned txid, and the native `registerRawTransaction` **takes no expected-txid parameter** —
      so it stamps `tx->blockHeight` from the caller and registers whatever arrived. A signed,
      wallet-associated transaction the chain does not have enters the ledger at a caller-claimed height
      ⇒ **false balance, HIGH** — reached through the *repair* path, not the asset path.
    - **A missing parameter is structural, not a call-site oversight.** When the leaf function has no
      argument for the expected identity, verification is *impossible* at that layer — say in the fix that
      the parameter must be added, not that a caller should compare. A caller-side check leaves the next
      caller to reintroduce the hole.
    - **Where to look first: reconcile / recovery / re-import / repair flows.** They are written as
      best-effort bulk re-ingestion, which is exactly where a verification norm established on the primary
      path gets dropped. Grep `register*` / `import*` / `reconcile*` / `fetch*` functions that take a
      claimed height, index, or position alongside the payload (`rg -n "fun (register|import|reconcile)"`).
    - **The gate is "who must misbehave"** — state it: here an answer whose bytes differ from the requested
      txid is enough, which a merely buggy or desynced node produces as readily as a hostile one, so the
      severity does not rest on an adversary. (Contrast item 10, where the datum came from a cert-pinned
      first party ⇒ MEDIUM.)

⛔ **A quirk that MATCHES the reference is NOT a finding.** Before claiming a silent integer
overflow (e.g. `mantissa * pow10(exponent)`), an odd default, or a lenient parser, read the
reference's equivalent line. Ports deliberately mirror upstream bugs; only a port that *disagrees*
with its reference (or with its own documented rule) is a finding. Say "matches the reference, not
a finding" out loud and move on.

⛔ **A cited convention can kill a candidate — check before writing it up.** "The walk follows
`input[0]`, so it could name the wrong asset" dies the moment you find that `input[0]` *is* the
protocol convention (here `AssetDuplicateDetector` states ids derive from `input[0]` of the
issuance). Record it as a VERIFIED NEGATIVE, don't report it.

- **A port with a KAT / "UNFIXED"-flag harness has already audited those classes.** Compile-time
  flags that switch a function back to pre-fix behaviour for a known-answer test
  (`#ifndef WIRE_COUNT_BOUNDS_UNFIXED`) plus `invariant:` comments bounding every wire count mean
  the memory-safety surface is done. Do not burn the budget re-deriving it — move to **logic**
  (attribution, scoping, ordering, which-entity), which those flags do not cover. That is where
  F4-class bugs survive.
- **Verify the SHIPPED build actually sets the strict level of any compile-time security flag.**
  A check gated behind `#if SEC_CHECK >= 2` (hard-reject) vs `>= 1` (compute-and-log) has its
  effective level decided by the *build*, not by the header default (`#ifndef … #define … 0`).
  Before calling such a gate weak, grep the build config for the `-D` override —
  `native/build.gradle.kts` `cFlags(...)`, `CMakeLists.txt`, `app/build.gradle.kts` — and confirm
  which buildType it applies to. (Observed: a `DGB_HEADER_POW_CHECK`/`DGB_HEADER_DIFF_CHECK`
  "level-1 weakens rejection" candidate died because `defaultConfig` sets both to `2` for every
  build type. Candidate closed, not filed.)
- **When surface-by-surface is exhausted, sweep by bug CLASS instead of by file.** One grep over
  the whole tree for a narrowing/arithmetic shape finds every instance of a recurring defect class
  at once — then check each hit against its guard before believing it. Shapes worth a sweep:
  `.toInt()/.toShort()/.toByte()` on a parsed `Long`, `copyOfRange`/`substring`/`sliceArray` with a
  computed index, and array indexing after a varint/length read. (Observed 2026-10 in an Android
  wallet: a decimal formatter whose cut index derives from issuer-controlled `divisibility` was
  safe **only** because the digits were `padStart(decimals + 1)`; a varint reader was safe **only**
  because every multi-byte branch checks `offset + N <= data.size` first. Both hits, both already
  guarded — the guards are the thing to look for.)

## Support files

- `references/multi-tenant-cache-scope-review.md` — **multi-tenant SaaS with an RLS
  boundary (open-source code + hosted Cloud, scanner-forbidden policy)**: the third PART 0
  routing row, the passive surface map to build before reading code (`security.txt` →
  `llms.txt` → `openapi.json` → OAuth/MCP `.well-known` → certspotter CT), and the
  highest-value bug class on this shape — **a cache key that omits a dimension its cached
  value depends on** (`permissions:${userId}` holding a company-scoped `role`, where that
  `role` gates `bypassRls` → service-role client) — with the four-step verification
  checklist that decides candidate-vs-filing, plus the sibling sweeps (`SECURITY DEFINER`
  RPCs under service-role, company-scoping proxies that wrap only `update`/`delete`,
  open-by-design DCR, auth-path parity).

- `references/audit-coverage-gap-analysis.md` — PART 2b: mature / heavily-audited protocols. The
  `/security` → `SECURITY.md` door, the Known-Issues list as the dedup map, mapping `audits/*.pdf` →
  modules with `pypdf` (no hits = unaudited), and `git diff --stat <last-audit-tag>..HEAD` to rank the
  post-audit surface; includes the `git fetch --unshallow` trap and the deployed-version check.
- `references/cross-path-verification-consistency.md` — PART 8 item 11: the *a sibling path already
  verifies this* shape (F9 — the history-recovery import registers provider-supplied bytes without the
  txid check its sibling enforces), the "missing parameter makes verification structurally impossible"
  rule, the repair/reconcile-flow heuristic, and the who-must-misbehave severity framing.
- `references/trust-boundary-source-asymmetry.md` — PART 8 item 10: the *same datum from two sources,
  opposite trust* shape (the port refuses the metadata document's `issuer` but writes the provider's
  into the authoritative column, F8), the source→sink sweep, "migrations are a confession", and the
  who-must-misbehave severity rule.
- `references/spec-vs-code-divergence.md` — diffing the code against the repo's OWN pinned spec
  (`docs/…` sectioned "CANONICAL (consensus) — PINNED"): the *stricter predicate shifts the ordinal*
  shape (F7, DigiDollar cent binding), severity gating when the divergent input is a non-standard script
  that needs a miner, reusable DigiDollar wire-format notes, and the write-path-preflight discipline for
  retracting an overclaimed escalation.
- `references/reference-differential-review.md` — clone-the-upstream differential recipe + three worked
  DigiByte-wallet cases on the SAME reference function (success-path LOW / out-of-range-error-path HIGH /
  rule-failure-error-path MEDIUM), the multi-trigger invalidation checklist (argument-invalid,
  rule-failure, pre-classification-precedence), and the write-path-vs-credit-path asymmetry. the *success*-path divergence (DigiAsset
  output-index-31 burn marker scoped to the BURN op in the reference, unscoped in the port → units
  dropped from crediting, LOW) and the *error*-path divergence (an out-of-range instruction makes the
  reference discard the whole transfer and move all input units to the last output, while the port
  keeps the in-range credits → false-positive receive, HIGH); plus the recipe extension for error
  paths and index-space alignment, and the candidates disproven by convention/reference check.
- `references/evidence-screenshots-and-pdf.md` — the "make it triager-grade" pass: make the PoC print
  real exploit values, capture one transcript per finding, render a terminal-style evidence PNG with
  Pillow (exact sizes/colours + the ANSI-strip trap), teach `md_to_report_pdf.py` to embed `![cap](path)`,
  QA the PDF (layout + whitespace-normalised text checks + embedded-image assertion), rebuild drafts.
- `references/github-pvr-submission.md` — GitHub Private Vulnerability Reporting: vetting an advertised
  security address, the PVR report endpoint vs. the advisory endpoint, fine-grained vs. classic token
  permissions (`repository_advisories=write` / `public_repo`), the content-creation secondary limit on
  young accounts, and how to hand a token to a script without the secret-scrubber eating it.
- `references/source-only-poc-recipes.md` — copy-paste recipes for runtime PoCs in source-only
  engagements: Soroban `cargo test` harness, Next.js/vitest route PoCs with the repo's fake-db,
  plus a worked finding→PoC map.
- `references/isolated-compile-poc.md` — compile a verbatim production class standalone (javac + annotation
  (`app/api/*`) white-box playbook: `cargo test` runtime-PoC recipe, Soroban contract bug-class
  checklist (missing admin guard, caller-supplied invariant data, no-op verification, cross-contract
  caller pinning), the fail-open/conditional-auth API checklist, and a worked example.
- `references/isolated-compile-poc.md` — compile a verbatim production class standalone (javac + annotation
  shim) to get a real runtime PoC without building the project; worked CLPR/FakeBls case.
- `references/immunefi-dlt-program-mechanics.md` — how to read an Immunefi Blockchain/DLT program page
  (rewards, prohibited activities, impact tiers, the downgrade clauses to pre-empt).
- `templates/IsolatedPocMain.java` — driver skeleton for that harness.
- `references/source-only-poc-harness.md` — drop-a-test PoC recipes for the two most common source-only
  stacks: Rust/Soroban contracts (`cargo test -p <hyphenated-name>`, `env.mock_all_auths()`, slow first
  build) and Next.js/TS API routes (`npm ci` + `vitest run __tests__/poc`, reuse the repo's `fake-db`,
  Drizzle circular-JSON assertion pitfall, corroboration-by-existing-tests).
- `references/soroban-stellar-review.md` — Soroban/Stellar + generic Rust contract review: the five
  defect classes that pay, recon/grep commands, the `cargo test` + `vitest` runtime-PoC recipe, the
  "target's own tests encode the bug" corroboration trick, and the validate→draft→manual-check order.
- `references/native-client-fail-open-casebook.md` — client+privileged-daemon reviews: the five
  fail-open shapes that pay — A: fail-open IPC client auth + Everyone DACL; B: double fail-open on a
  privacy-critical config where the callee can't return `Err` and the caller only logs; C: runtime
  toggles that disable a control; D: **failure unrepresentable in the signature** (unit-returning
  apply helper + an unconditional `Ok(())` caller, vs its own `?`-using sibling branch); E:
  **swallowed-call asymmetry by security role** (the anti-leak calls swallowed while a benign one
  propagates — the diff is the impact analysis) — with the exact code shapes, the swallowed-error
  enumeration grep, the sibling-contrast argument, per-platform call semantics
  (`SetDomains((".", true))`, `disable_dot`, `DnsSettings::save`), severity discipline, and the
  labelled-untested rule for FFI/native-only platform code.