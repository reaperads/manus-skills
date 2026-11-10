---
name: poc-technique-atlas
author: Fauzi Susanto
description: >-
  Method-level technique atlas extracted from the local PoC corpus (2,223 GitHub PoC repos,
  filtered + deduped) plus PortSwigger Web Security Academy topic structure. Use during a
  web2 / pentest / bug-bounty audit when you need the METHOD for a vulnerability class —
  RCE & command injection, SQLi, XSS, SSRF, LFI, XXE, SSTI, deserialization, auth bypass,
  IDOR/BOLA, CSRF, race conditions, file upload, CRLF/smuggling, prototype pollution,
  GraphQL, NoSQL, memory corruption, crypto flaws, cloud/metadata, supply chain — or want to
  see how a CVE class is actually exploited without pulling raw exploit code. Reference shelf,
  NOT an orchestrator: owner skills' rules win on conflict. Read ONE class file per phase.
metadata:
  hermes:
    tags: [security, techniques, poc, web2, portswigger, reference-shelf]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# PoC Technique Atlas

A **method shelf**: what each bug class *is* and how it is actually exploited, distilled from
a 2,223-repo local PoC corpus and the PortSwigger Web Security Academy. **No exploit bodies,
no malware, no payload dumps** — technique lines + one exemplar repo to read if you need
detail.

> Provenance: `D:/data hermes/poc-compact/` (2,223 GitHub PoC repos; 61,135 files after
> compaction) → classified → malware/scam-filtered → deduped → 1,901 techniques in 27 class
> files. PortSwigger: 29 topic files scraped from portswigger.net/web-security (topic +
> subtopic technique headings). Rebuild with `D:/data hermes/_poc_techniques/` scripts.

---

## When to use

Load this when an audit reaches a phase where you know the *class* but want the concrete
*methods* — e.g. "how do CVE-2024→2026 SSRF bypasses actually slip past hostname filters",
"which deserialization gadget families exist", "what race-condition patterns pay".

**Do not** load the whole shelf. Pick ONE class file for the phase you're in.

## Navigation

- `references/00-INDEX.md` — all 28 classes with technique counts and one-line scope.
- `references/<class>.md` — technique table: `# | Technique (method) | Exemplar repo`.
- `references/nuclei-detection.md` — 13,777 nuclei templates → per-class detection
  observables (matcher kinds) + severity mix. Use to build your own scanner rule.
- `references/distilled/00-INDEX.md` — distilled technique index of the pre-existing
  reference shelves (bug-bounty 730 files, exploit-cookbook 89, bb-audit-launcher 69,
  bugbounty-playbook 187, exhaustive-testing 20) → 827 KB, ~24x smaller. Check here
  before opening the original heavy shelf.
- `references/portswigger/00-INDEX.md` — 29 WSA topics → technique counts.
- `references/portswigger/<slug>.md` — WSA topic: technique headings + subtopic pages.
- `references/web-blogs/yeswehack.md` — 48 technique-relevant YesWeHack posts (URLs + gist).

Map from task → file:

| If the target shows… | Read |
|---|---|
| eval/exec/template/upload → code exec | `rce.md` |
| query params, auth forms, ORDER BY errors | `sqli.md` |
| reflected/stored/DOM input sinks | `xss.md` |
| URL fetchers, webhooks, image importers | `ssrf.md` |
| file/template includes, download paths | `lfi.md` |
| XML/SOAP/SAML parsers | `xxe.md` |
| template engines | `ssti.md` |
| serialized blobs (Java/PHP/Python/Node/.NET) | `deserialization.md` |
| login/MFA/JWT/OAuth/SAML/session | `auth-bypass.md` |
| object ids, /api/{id}, role gates | `idor-bola.md` |
| state-changing POST w/o token | `csrf.md` |
| limits, coupons, stock, check-then-act | `race-condition.md` |
| upload endpoints | `file-upload.md` |
| proxies/CDN, header handling | `crlf-injection.md` |
| redirect params | `open-redirect.md` |
| debug/VCS/backup/verbose errors | `info-disclosure.md` |
| JS merges, client state | `prototype-pollution.md` |
| /graphql | `graphql.md` |
| Mongo/operator queries | `nosql.md` |
| IMDS, buckets, containers | `cloud.md` |
| native parsers, binaries | `buffer-overflow.md` |
| crypto/tokens/hashes | `crypto.md` |
| CI/CD, packages | `supply-chain.md` |
| anything else | `other.md` (876) |

## How to read a class file

Rows are **methods**, not payloads. Take the method, adapt it to the target, and use the
exemplar repo name only as a pointer if you need the low-level detail. Never paste a payload
body from the corpus into a live target without adapting + validating impact first.

## Integration (additive, never overrides)

| Owner skill | Relationship |
|---|---|
| `web2-vuln-classes` | classes + root causes; this atlas = the *methods* per class |
| `security-arsenal` | payload tables; this atlas = the technique *shapes* |
| `exploit-cookbook` | worked playbooks; this atlas = the raw method inventory behind them |
| `bugbounty-playbook` | bugbounty.info mirror; complementary |
| `hunt-*` skills | per-class hunting steps; atlas supplies method breadth |
| `bb-audit-launcher` / `audit-execution-discipline` | on-demand shelf, read ONE file, does NOT count against phase context budget |

Where two skills disagree, the owner skill's rule wins.

## Hygiene

- Malware/scam repos (stealer, RAT, backdoor, miner, ransomware, dropper/loader, C2,
  credential-dumper, skimmer, phishing-hit) were **excluded** during extraction.
- `dos.md` is report-only: never run DoS/ReDoS against a live target (out of scope on most
  programs).
- One root cause per technique. If a row is a vendor CVE, the *method* is the transferable
  part — the CVE id is the exemplar.