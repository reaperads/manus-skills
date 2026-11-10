---
name: target-pool
version: 1.0.0
author: Fauzi Susanto
description: "Query the deduped bug-bounty target pool."
metadata:
  hermes:
    tags: [bug-bounty, targets, pool, recon, self-hosted]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Target Pool — unified, deduped, queryable

## When to Use
- Kovak says "gas a target" / "ambil target" / starts a bounty session without naming a target
- Before auditing any domain — dup-check against past audits
- After finishing an audit — mark status in the pool
- When building a recon batch — pull N targets from `pending`

Kovak's standing bug-bounty target pool. **Query it first when starting work** instead of
asking him for a target.

## Where it lives

```
D:/data hermes/target-pool/
  pool.json     4.6 MB  full records (8106 domains)
  targets.csv   1.5 MB  flat view for Excel/Sheets
  dupes.json    109 KB  794 merge events (audit trail of dedupe)
```

CLI: `~/AppData/Local/hermes/scripts/pool.py`

## Usage

```bash
PY314="C:/Users/WINDOWS10/AppData/Local/Programs/Python/Python314/python.exe"
cd ~/AppData/Local/hermes/scripts

# discover
"$PY314" pool.py stats                        # counts by category + audit state
"$PY314" pool.py body eu                      # which TLDs count as a region
"$PY314" pool.py pick --region eu --limit 10  # ready-to-work candidates + score + reason
"$PY314" pool.py pick --country de --reward monetary
"$PY314" pool.py pending --limit 80           # monetary + live + untouched

### "yang terbaru" (newest) — pool.py has NO date sort
`pick` sorts by score, not by `first_seen`. For "ambil 1 terbaru" requests filter the
raw JSON yourself (fields `first_seen`, `last_seen` are ISO `YYYY-MM-DD`, sort descending):

```bash
"$PY314" - <<'PY'
import json, random
p = json.load(open("D:/data hermes/target-pool/pool.json", encoding="utf-8"))
recs = list(p["domains"].values())          # top level = {count, by_category, by_source, merge_events, domains}
EU = set("al ad am at az by be ba bg hr cy cz dk ee fi fr gr hu is ie it kz xi lv li lt lu mt md mc me nl mk no pl pt ro ru sm rs sk si se ch ua gb uk gi je gg im fo gl".split())
f = [r for r in recs if (r.get("country") or "").strip().lower() in EU
     and r.get("reward") == "monetary"
     and r.get("audit_status", "untouched") == "untouched"]
f.sort(key=lambda r: (r.get("first_seen") or "", r.get("last_seen") or ""), reverse=True)
top = f[:20]                                  # newest batch
print("\n".join(f'{r["first_seen"]} {r["domain"]:35} {r["country"]} live={r.get("live")}' for r in top))
print("PICK:", random.choice(top)["domain"])  # random dari 20 terbaru
PY
```

Then `pool.py why <dom>` for the full record before proposing.
"$PY314" pool.py list --reward monetary       # ALL paying (incl. already worked)
"$PY314" pool.py list --state finding-pending # what's awaiting report
"$PY314" pool.py search venice
"$PY314" pool.py get spectrocoin.com          # raw record
"$PY314" pool.py why spectrocoin.com          # record + state + notes

# mark results (PERSISTS + timestamped note)
"$PY314" pool.py set  <dom> audited       --note "0 temuan"
"$PY314" pool.py set  <dom> policy-dead   --note "policy 404"
"$PY314" pool.py set  <dom> no-reward     --note "credit-only"
"$PY314" pool.py skip <dom>               --note "terlalu susah"
```

### Programmatic access (execute_code / python)
`pool.json` top level is a dict: `{count, by_category, by_source, merge_events, domains}`.
`domains` is a **dict keyed by domain** (not a list!) and `live` is the **string** `"True"`,
not a bool. Direct access pattern:

```python
pool = json.load(open(r"D:/data hermes/target-pool/pool.json", encoding="utf-8"))
recs = list(pool["domains"].values())          # values, not the dict itself
cand = [r for r in recs
        if str(r.get("reward","")).lower()=="monetary"
        and str(r.get("country","")).lower() in EU_TLDS
        and str(r.get("live")).lower()=="true"   # string compare
        and r.get("audit_status","untouched")=="untouched"]
```

Gotchas that cost retries: iterating `pool["domains"]` directly yields domain
strings; `r.get(...)` on them raises AttributeError. `live == True` never matches
(string). EU region TLD list: `pool.py body eu` (38 codes incl. ch, uk, no, is).

### Audit states (`audit_status`)
`untouched` (default) · `recon-done` · `audited` · `finding-pending` · `submitted` ·
`paid` · `rejected` · `policy-dead` · `no-reward` · `skipped`

The `--untouched` filter (and `pick`/`pending`) excludes **every** non-`untouched` state —
so a target flagged `policy-dead` / `no-reward` / `skipped` never resurfaces for work.
`--note` is stored permanently and shows in `list`, `why`.

### Prompt cheat-sheet (natural language → action)
Full mapping in `references/prompt-cheatsheet.md`. Quick version:
"kasih target dari pool" → `pick` · "eropa monetary belum dikerjakan" → `pick --region eu`
· "yang country de" → `--country de` (aliases: jerman→de, inggris→uk)
· "<dom> udah digarap?" → `why <dom>`

## Pool contents (built 2026-10-12)

| category | count | what |
|---|---|---|
| `selfhosted-any` | 8046 | all self-hosted programs from the 2026-10-06 sheet |
| `master-list` | 49 | curated web3/web2 self-hosted (MASTER_SELFHOSTED_PROGRAMS.txt) |
| `quarterwise-competitor` | 11 | Quarterwise peer companies + their policy status |

Sources merged: `self-hosted-bug-bounty-programs-2026-10-06.xlsx` (3 sheets),
`MASTER_SELFHOSTED_PROGRAMS.txt`, `kompetitor_quarterwise_bugbounty.xlsx` (x2 revisions).

**794 duplicate domains were merged** (e.g. a domain present in both the big sheet and the
master list keeps both `sources[]` and the richer field set). `dupes.json` is the audit trail —
check it before claiming "no duplicates".

## Field schema (per domain)

`domain, program_name, category, reward (monetary|swag|...), policy_url, contact,
security_txt, safe_harbour (stated|not_stated), country, hosting, status, live,
first_seen, last_seen, expires, langs, sources[], already_audited`

## Rules

- **`reward: monetary` from the source sheet is NOT trustworthy.** Verified 2026-10-14:
  medatixx.de was flagged monetary but its policy explicitly says "Ein Bug-Bounty-Programm
  bieten wir derzeit nicht an" (VDP + Hall of Fame only). Before committing a target, fetch
  the `policy_url` and look for the actual bounty statement. VDP-only → `pool.py set <dom>
  no-reward --note "<evidence>"`. Common pattern in the selfhosted sheet: self-hosted VDPs
  default to monetary even when recognition is non-monetary. Discretionary reward ("appropriate
  reward or other form of recognition", e.g. gasunie.nl) still counts as monetary but note it.
- "no platform" / "self-hosted only" → filter `hosting != platform` (platform = Intigriti/
  HackerOne-hosted programs; the CLI `pick`/`list` don't expose a `--hosting` flag yet — use
  `pool.py get` + a JSON filter over `pool.json` domains dict, key is `domains` NOT a list).
- **Query before asking.** If Kovak says "gas a target", run `pool.py pending` and propose from it.
- **Dup-check before auditing.** `pool.py get <dom>` — if `already_audited` or
  `status != untouched`, say so instead of re-auditing.
- **Mark progress.** After an audit completes: `pool.py set <dom> audited --note "..."`
  (other values: `recon-done`, `finding-pending`, `submitted`, `paid`, `rejected`).
- **`reward: monetary` is NOT trusted — verify the policy first.** The source sheet
  tagged many EU self-hosted VDPs as `monetary` when they are actually VDP-only with
  Hall of Fame (verified example: medatixx.de — policy literally says "Ein Bug-Bounty
  Programm bieten wir derzeit nicht an"). Before proposing a target as "paying",
  fetch the policy page and look for an explicit reward/bounty statement. If no bounty
  → `pool.py set <dom> no-reward --note "policy: VDP-only/HallOfFame"`. Common tell:
  policy framed as EU Cyber Resilience Act (CRA) compliance — CRA mandates a disclosure
  channel, NOT a bounty, so CRA-worded VDPs are frequently non-paying.
- **"no platform" requests** = `hosting != "platform"` (i.e. `self_hosted`); platform =
  Intigriti/HackerOne/Bugcrowd-hosted programs. ~60/40 split in the EU monetary slice.
- **Respect each program's own policy** — the pool is a directory, not an authorization.
  Check `policy_url` / `safe_harbour` per target before active testing.
- **Deep-check the policy BEFORE proposing a target** (`policy_url` in the pool is often a
  shortlink or a JS-rendered page — the reward amounts and the real scope list are usually
  on a *different* page than the link itself). Verify: (a) ada nominal reward / memang bayar,
  (b) domain yang mau digarap ADA di scope list program. Pool entries are TLD/locale mirrors
  of one brand (e.g. `yandex.fr`) — the program scope may only list `*.yandex.com`.
  Recipe + worked example: `references/policy-amount-check.md`.
- **Do NOT put credential dumps in the pool.** `BB 10K.txt` (10k `sk-` keys) stays out.
- `pending` filters strictly (monetary + live=true + not audited) — if it returns few rows,
  relax with `list --reward monetary`.

## Rebuild / refresh

Scripts: `~/telegram_scraper/pool_step1.py` (xlsx) → `pool_step2.py` (master txt + competitors)
→ `pool_step3.py` (dedupe audit + write). Re-run all three after adding new source files;
`add()` in step2 merges by normalized domain (lowercase, strip `www.`, strip scheme/path).