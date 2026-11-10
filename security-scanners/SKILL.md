---
name: security-scanners
description: "Use during Phase 0C for scanner selection and fuzzing."
metadata:
  hermes:
    budget_kb: 25
    tags: [scanner, fuzzer, nuclei, ffuf, security]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Scanner & Fuzzer Guide (Phase 0C)

## ⛔ CANDIDATE RULE (MANDATORY — EVERY TEST)
- **Each test = one candidate. Finding something = mark candidate. CONTINUE to next test.**
- **Candidates become FINDINGS only after Phase 5 REPORT GATE (Phase 0F).**
- **DO NOT generate report during Phase 0C. Report = ABSOLUTE LAST.**
- **If you find CRITICAL → mark candidate → KEEP TESTING. Do NOT stop.**

## ⛔ Load Rules
- Load during Phase 0C alongside attack playbooks
- Provides tool selection, config, wordlists
- Budget: 25KB — read_file for detailed config

---

## Scanner Selection Matrix

| Scenario | Tool | Command |
|----------|------|---------|
| Directory busting | dirsearch | `dirsearch -u https://target.com -o $DIR/dirs.txt` |
| Directory busting (fast) | ffuf | `ffuf -u https://target.com/FUZZ -w $WORDLIST -mc 200,301,302,403` |
| Subdomain takeover | dnsReaper | `dnsreaper predict --domain target.com` |
| Vuln scanning (templates) | nuclei | `nuclei -u https://target.com -t cves/ -t vulnerabilities/` |
| Vuln scanning (comprehensive) | w3af | `w3af_console -s "target https://target.com"` |
| Vuln scanning (quick) | wapiti | `wapiti -u https://target.com -o report.html` |
| Vuln scanning (AI) | afrog | `afrog -u https://target.com -o $DIR/afrog.json` |
| API fuzzing (stateful) | restler | `restler/restler_driver.exe --grammar $GRAMMAR --target $URL` |
| API fuzzing (quick) | ffuf | `ffuf -u https://target.com/api/FUZZ -w api-words.txt` |
| Browser crawling | crawlergo | `crawlergo -c chrome -t 5 -u https://target.com` |
| Secrets scanning | titus | `titus scan --dir $DIR` |
| Web cache poisoning | wcvs | `wcvs -u https://target.com` |
| Multi-tool scan | rapidscan | `rapidscan https://target.com` |
| Full audit | w3af | `w3af_console -s "target https://target.com"` |
| Booter/stress test | killshot | `killshot https://target.com --scan` |
| AI scan | SILENTCHAIN | Burp extension + Ollama/OpenAI |
| AI pentest | Zen-Ai-Pentest | Multi-agent AI pentest framework |

---

## Wordlists

### Directory Busting
```bash
# OneListForAll (comprehensive)
curl -sL https://raw.githubusercontent.com/six2dez/OneListForAll/main/onelistforall.txt -o /tmp/wordlist.txt
# SecLists common
curl -sL https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt -o /tmp/common.txt
```
**Repos:** six2dez/OneListForAll (3.2K)

### API Endpoint Discovery
```bash
cat $DIR/urls.txt | grep -iE 'api|v1|v2|graphql|rest' | sort -u > $DIR/api_endpoints.txt
```

---

## Fuzzer Configuration

### ffuf Best Practices
```bash
ffuf -u https://target.com/FUZZ -w /tmp/wordlist.txt \
  -mc 200,301,302,403 -fs 0 -ac \
  -t 40 -p 0.5 \
  -o $DIR/ffuf.json -of json
# Filter by size (avoid noise)
ffuf -u https://target.com/FUZZ -w wordlist.txt -fs 4242
# Recursive
ffuf -u https://target.com/FUZZ -w wordlist.txt -recursion -recursion-depth 2
```

### ⛔ Verify the scan actually ran — and that the log contains hits
A fuzzer that mis-parses its arguments writes its **banner/help text to stdout** and exits 0.
With `2>/dev/null` you get a 300-line "results file" containing zero results. Both happened
here on the same day (ffuf):

```bash
# does this log actually contain hits?
grep -cE 'Status:|https?://' ffuf_sensitive2.log     # 0  -> no hits (or the run failed)
head -3 ffuf_sensitive2.log                          # "Fuzz Faster U Fool ..." / "HTTP OPTIONS:" = it failed
```
Rules:
- Never promote a scanner log to "evidence" before grepping it for the tool's **hit format**
  (`Status:` for ffuf non-silent, a URL for most others). `-s/--silent` changes the output shape.
- Re-run suspicious invocations with stderr visible (`2>&1 | head`) before concluding anything.
- **Silent-mode output can look like the wordlist.** `ffuf -s` prints only the matched FUZZ
  payload, so on a host whose SPA answers `200` to *every* path (including the wordlist's
  `# comment` lines) the log degenerates into a copy of the wordlist — every entry "matches".
  Pre-check the host: fetch two random nonsense paths; identical bytes/status = catch-all, and
  then only `-mc 200` fuzzing is meaningless there. Use `-fs <size>` / `-ac` to filter.
- **Native-path gotcha (Windows/MSYS):** `ffuf`/`gobuster` are native binaries — `-w /c/Users/...`
  silently fails; pass `C:/Users/...`. `gobuster dir -s 200,301 -b ""` (its default status
  blacklist conflicts with `-s` and the run refuses to start).
- A verified **"0 hits"** is a real deliverable — write it into the log with the exact command,
  and separate "tested, nothing there" from "not tested".
- **Loopback hostnames can fail resolution inside the scanner.** `nuclei -u http://localhost:1322`
  printed `Skipped localhost:1322 from target list as found unresponsive permanently:
  cause="no address found for host"` and *still* ended with a normal-looking
  `Scan completed in 3.5s. 0 matches found.` — after issuing **36 of 5649** requests. Against a
  local/lab target use the literal address (`http://127.0.0.1:<port>`) and prove reachability from
  the scanner's point of view before launching: `curl -o /dev/null -w '%{http_code}' http://127.0.0.1:<port>/`.
- **A `timeout` kill looks like a finished scan.** `timeout 900 nuclei ... | tail -35` that is
  SIGTERM'd mid-run prints the banner plus whatever the tail buffer held, and no error. Real
  completion always prints `[INF] Scan completed in <t>` **and** an `HTTP connections: N total`
  line. Missing that line = the run was cut short, so re-run with a tighter set (drop the huge
  `cve` tag on a single-app target) and write to a live file rather than a `tail` pipe.
- **When the TARGET advertises its own rate limit, "0 matches" is a weak negative.** This session
  hit `Skipped 127.0.0.1:1322 ... as found unresponsive 30 times` while the app was answering
  fine — it advertises `Octopus-RateLimit-Policy: l=200;rpm=60`, so a scanner at `-rl 30` starves
  itself against the app's own limiter. Record *"0 matches, coverage curtailed by the product's
  rate limiter"*, never *"clean"*. A protective rate limit is a control, not a weakness — don't
  report it as one.
- **Never judge a scan from `grep`-filtered output alone.** Piping a scanner through a whitelist
  (`| grep -iE "injectable|parameter|CRITICAL"`) hides the tool's own startup failure: an
  invocation of a **non-existent launcher** failed instantly on all three URLs and yielded an
  empty, clean-looking result. Run `<tool> --version` once per session before the first real
  invocation, and always keep the unfiltered first run in a file.

### ⛔ An ABORTED scan is not a negative — preflight the flags (wpscan, and any tool that aborts)
A scanner can exit 0 having scanned **nothing**. Read the first lines of its output before writing
"no findings". Two real wpscan aborts in one session (2026-10) — both looked like "0 results", and
one was nearly mis-recorded as "the CDN blocked wpscan":

```
Scan Aborted: --api-token Empty option value supplied
Scan Aborted: --enumerate Incompatible choices detected: ap, p
```

Rules:
- **wpscan without an API token cannot enumerate vulnerable plugins/themes.** `--enumerate vp,vt`
  (or a bare `--api-token ""`) makes it print `Scan Aborted: An API token is required...` and write a
  ~320-byte JSON with only `"scan_aborted"`. That is a **flag/config failure, NOT a WAF block and NOT
  "no vulns"**. Drop the `v` classes and use `--enumerate ap,u,cb,dbe` for what works untokened
  (fingerprint plugins, users, config backups, DB exports). Without a token, get plugin→CVE mappings
  from public DBs instead (Wordfence / cvefeed / cvebrief / SentinelOne).
- **`ap` (all plugins) and `p` (popular plugins) are mutually exclusive** — combining them aborts.
- Any tool that prints `Scan Aborted` / `Aborted` / a usage or banner block has produced **zero**
  evidence. Classify it as *"not run"*, never as a clean negative (owner rule: run gagal ≠ negatif —
  wajib diulang). Same session, the same run had been recorded as "wpscan blocked by Cloudflare"
  when it had actually died on my own empty `--api-token`; reporting a vendor block that never
  happened is a false claim.
- Also applies to `curl`/`dig` **leftover-file traps**: if a loop writes to a fixed `/tmp/x` and a
  request fails (`000`), the surviving file from the *previous* iteration is what you end up reading.
  Use a fresh path per iteration, or check the exit/`%{http_code}` before reading the body.

### ⛔ A vulnerable VERSION is not an exploitable TARGET — read the CVE's precondition
Version-only CVE matches are leads, not findings. Before a version match becomes a finding, prove
the exploit's **stated precondition** exists on the target.

Real case (2026-10, nordnetab.com WordPress): Beaver Builder `2.8.6.1` (< 2.11.0.6) matched three
CVEs including **CVE-2026-92084 (CVSS 9.1, UNAUTHENTICATED arbitrary shortcode execution)**. The
advisory's own precondition: *a Beaver Builder page containing the Sidebar module populated with a
widget that shows attacker-controllable content*. Checked on the target: **0 of 120** sitemap pages
contain `fl-module-sidebar`, and comments are **closed** — the path is absent, so it is **not
exploitable**. Recorded as "outdated component" (hardening note), never as an RCE finding.

Checklist:
1. Pull the CVSS **vector and the exploitation-requirements sentence**, not just the version range.
   `PR:N` (unauth) vs `PR:L` (Contributor+) changes everything — CVE-2026-95865 on the same plugin is
   `PR:L` and therefore not unauth.
2. Map the precondition to a **checkable artefact** and check it: grep the served markup for the
   module/feature (`fl-module-sidebar`), read the shipped plugin code for the vulnerable function,
   confirm the enabling config (comments open, module in use). **Precondition absent ⇒ not a finding.**
3. For a plugin CVEs list, `web_search` `<cve-id> <vendor> <vector>`; Wordfence pages often 202
   (bot-protected) — cvefeed / cvebrief / SentinelOne serve the same text.
4. Honest wording: *"version affected, precondition absent, not exploited"* — plus a patch
   recommendation. Never inflate a version match into an exploit claim.

### nuclei Best Practices
```bash
nuclei -u https://target.com -t ~/nuclei-templates/ -severity critical,high,medium
nuclei -u https://target.com -t ~/nuclei-templates/cves/
nuclei -u https://target.com -rl 50 -c 10        # only for your OWN infra / lab
```

### ⛔ `-l` = TARGETS, `-t` = TEMPLATES — swapping them fails SILENTLY (looks like "clean")

`nuclei -l <file>` reads a list of **target URLs**. `-t` takes a template (file or directory).
Passing your *template* list to `-l` does not error — nuclei treats each template **path** as a
target and prints a normal-looking run:

```
[INF] Templates loaded for current scan: 1      <- the "target" was a template path
[INF] Skipped .:80 from target list as found unresponsive permanently: cause="no address found for host"
[INF] Scan completed in 3m. No results found.
```

That reads exactly like "the target is clean" when **nothing was scanned**. Hit live 2026-10 (a
~400 s run wasted, and the false "no results" nearly went into the ledger).

Rules:
- To scan with a template *set*, pass a **directory** or repeat `-t`:
  `nuclei -u https://cardoma.shop -t ./http -tags wordpress,woocommerce`. There is no
  `-t <listfile>` equivalent of `-l`.
- Before believing "No results found", sanity-check the counters: `Templates loaded for current scan`
  must be the real count (hundreds/thousands), `Targets loaded for current scan` must be 1, and
  `HTTP connections: N total` must be non-trivial. `Skipped ... no address found for host` against a
  real hostname is the tell that you fed the wrong file.
- A genuinely clean run has real HTTP connection counts and none of that "unresponsive" spam —
  write the counters into the ledger as the evidence either way.

### ⛔ Volume discipline — read the program rules BEFORE you launch a scan
The `-rl 50 -c 10` preset above is a lab default. Against a live bounty target it can be
disqualifying. Real case (2026-09): `nuclei -l <260 live hosts> -t <full local template mirror>
-tags exposure,misconfiguration,disclosure,takeover,default-login` queued **1,271,200 requests**
(2011 templates x 260 hosts). It had to be killed mid-run and replaced with a curated list at
`-rl 4`. The program brief had already said rate limits are enforced environment-wide, that
rate-limit findings are out of scope, and that DoS-adjacent behaviour is prohibited.

Checklist before launching:
1. **Estimate first.** `templates x hosts = requests`. nuclei's own `-stats` line shows
   `Requests: N/M` — glance at it in the first 30 seconds, before it becomes a problem.
2. **Curate hosts, don't pass the whole live list.** Keep a `priority_hosts.txt` (the 15-25 hosts
   that actually matter: auth surfaces, admin panels, the app itself) instead of all 260.
3. **Prefer `-tags` / `-t <subdir>` over the entire `http/` tree**, and drop tags the brief excludes.
4. **Rate for the program, not the lab.** Rate-limited or WAF-fronted targets: `-rl 3..5 -c 2..3`.
   If Cloudflare returns 429 / `error code: 1015` during manual probing, your automated rate is
   already too high.
5. **Respect the brief's exclusions.** "No automated scanning against forms", "no rate-limit
   testing", "no DoS" all constrain scan volume and concurrency, not just payload choice.
6. **Never test rate limits as a finding on endpoints the brief excludes** (commonly non-auth
   endpoints). The finding is out of scope even when it works.
7. A killed scan leaves **partial state**: a partial output file, a stale `nuclei` child process,
   and half-written stats. Clean up (`tasklist | grep nuclei`) before re-running, and write results
   to a fresh filename so a partial file is never mistaken for a complete one.
8. **The blast radius outlives the scan.** A broad-template run (`-rl 30`, full local mirror) against
   a bank's LB tripped a **per-IP Cloud Armor limit that 429'd every `www.*` host for ~45 minutes** —
   and silently poisoned *other* tools in the same window (`sqlmap`, `linkfinder`, `race-checker` all
   logged `429`, and the pipeline's own XSS/CMDi candidates were invalidated by it). Two consequences:
   (a) prefer the **targeted template dirs** (`http/exposures`, `http/misconfiguration`,
   `http/exposed-panels`, `http/default-logins`, `ssl`) over the whole `http/` tree;
   (b) after a 429 storm, treat every scan that ran inside that window as **poisoned, not negative**,
   re-verify later, and record `HTTP 429` hits in the ledger so a "negative" is never claimed from a
   throttled run. Verify the block has lifted (`curl -o /dev/null -w '%{http_code}'`) before resuming.

### ⛔ A pipeline that "is running" can still be scanning ONE host — audit its coverage, then supplement

An orchestrator reporting `✅ Force execution COMPLETE` says nothing about how much of the estate it
touched. On the Blink engagement (2026-10-12) the pipeline's recon stage failed silently
(`httpx: 0 live hosts (rc=255)`) and it seeded itself with the two hostnames it could reach — so a
"completed" 0C had scanned **316 URLs on one host** while the engagement had **81 known-live hosts**.
Nothing downstream flagged it.

Do this after (and once during) any long automated pass:

1. **Prove liveness from the FILESYSTEM, not from the orchestrator's chatter.** A watchdog line like
   `[STALL-WARN] no step progress for 2721s … still running, not killed` is not evidence of death: check
   the newest mtime in the pipeline's workdir (`find <workdir> -type f -printf '%TH:%TM %p\n' | sort -r`)
   and its child processes. Progress every ~2 minutes = alive; nothing written for 20+ minutes with a
   live PID = stalled, and that is when you intervene.
2. **Histogram the pipeline's own host list against your recon ledger.** `grep -oE 'https?://[^/]+'
   <workdir>/urls.txt | sort | uniq -c | sort -rn` and read `<workdir>/live.txt`. If it covers one or
   two hosts out of dozens, the pipeline's coverage is an illusion — run your own nuclei over the full
   live-host list you already have and merge the evidence. Do not report the pipeline's negative as an
   estate-wide negative.
3. **Expect wildcard DNS to poison both the host list and the results.** With `*.target.tld` resolving,
   a naive host sweep reports every subdomain as "live" (mostly 404s) and nuclei's own
   `[wildcard-dns-detect]` template dominates the output — one run produced **64 of the first 66 hits**
   as wildcard noise. De-dupe by body/status, and filter the DNS templates out (`grep -v
   'wildcard-dns-detect'`) before reading results, or the real hits are invisible in the noise.
4. **Compute the ETA before launching, and cut tags rather than waiting.** `templates × hosts ≈
   requests`; at `-rl 8` a `1106-template × 81-host` pass queued **219,510 requests ≈ 2.2 h**, and an
   earlier `6186-template × 81-host` pass at `-rl 60` implied **6.7 h** (killed after 3 h at 66 %).
   If `requests ÷ rate > ~1 h`, trim to the high-signal tag set (`exposures, exposed-panels,
   misconfiguration, default-login, takeovers, unauth` — drops the template count by ~5x) and raise the
   rate to a still-polite `-rl 20 -c 6`. Seconds of arithmetic beats hours of waiting on a 4-vCPU box
   that is simultaneously running the pipeline.

### ⛔ Template severity is a HYPOTHESIS — read every hit body before you believe it
A curated run returning "3 hits" is not "3 findings". Same session as above, the complete output was:

```
[config-json-exposure-fuzz] [critical] https://dashboard.rapyd.net/config.json
[config-json-exposure-fuzz] [critical] https://m.dashboard.rapyd.net/config.json
[readme-md]                 [info]     https://ai-assessment.rapyd.org/README.md
```

Verification changed the ranking completely:
- `/config.json` on a SPA is **public by design** — it held only reCAPTCHA *site* keys (public),
  analytics IDs, feature flags, an SFTP allow-list and test numbers. No secret. The template's
  "critical" is a false positive here; reporting it burns credibility. (`/config.json` diffed between
  desktop and mobile builds showed only benign per-build differences.)
- The `[info]` README was the **only** item worth reporting, and it is P4 (internal architecture,
  endpoint semantics, KV key schema, deployment notes — not a credential or PII leak).

Per-hit checklist before anything enters a report:
1. `curl` the exact matched path/parameter and **read the body**, not the template's claim.
2. Ask what the hit actually grants: credentials/tokens? cross-tenant data? write access? If none,
   it is informational regardless of the template's severity tag.
3. Confirm it is a real endpoint and not the SPA catch-all — identical byte-length for unrelated
   paths (e.g. every `/portal/api/*` returning the same 35,235-byte `index.html`) means there is no
   API there at all.
4. Map to the platform VRT *after* step 1-3, and check the brief's out-of-scope class list (public
   config, non-sensitive info disclosure and "missing best practices" are commonly excluded).
5. Keep the fuzzing templates (`*-fuzz`, `*-exposure`) in the run — just treat their output as leads.

### ⛔ When the template run is infeasible: bounded path sweep, then filter the FP classes
Full-template nuclei over a wide host list is almost never the right call on a rate-limited program
(see Volume discipline above — 1.5M requests queued, 0.5% done in half an hour). The replacement that
still finds the class that actually pays (stray docs/configs) is a **bounded sweep you write yourself**:
a short curated path list (`README.md`, `.env`, `.dev.vars`, `config.json`, `wrangler.toml`,
`package.json`, `swagger.json`, `openapi.json`, `.git/config`, `CHANGELOG.md`, `/api-docs`,
`.well-known/security.txt`) × the host list, single-threaded-ish at ~4 req/s. Real numbers from one
engagement: **260 hosts × 14 paths ≈ 3,600 requests in ~8.5 minutes**, 99 raw 200-hits.

**Most of those hits are NOT findings.** Filter these three classes before you read anything:

| FP class | Tell | Verdict |
|---|---|---|
| Edge/access interstitial | every path on a gated host returns the *same* ~48 KB HTML (`Sign in ・ Cloudflare Access`) while the root returns 302/403 | not a hit — 45 of 99 in one run |
| SPA catch-all | body hash ≈ the host's root document | not a hit |
| Upstream template file | `README.md` that is the stock WordPress/Pantheon or Cloudflare boilerplate (`git clone cloudflare/ai`, `worker-name.account-name` placeholders) | **public upstream file — do not report** |
| Public front-end config | `config.json` with reCAPTCHA *site* key, analytics IDs, OAuth *client_id*, feature flags | not a secret — not a finding |

Comparison against the root body is not sufficient on its own: it fails exactly on the gated hosts
(root = 302, path = 200 interstitial). Also match on body markers (`Cloudflare Access`, `__next`,
`id="root"`, `@vite/client`) and de-dupe by (host, body-hash).

- `references/bounded-exposure-sweep.md` — budget math, marker lists, survivor triage table, pitfalls.
- `scripts/bounded_exposure_sweep.py` — ready to run:
  `python bounded_exposure_sweep.py --hosts hosts.txt --outdir ./scan --rps 4 --header "X-Bugcrowd: <handle>"`
  (it prints only survivors and writes the full classified JSON).

---

## ⛔ sqlmap on a Cloudflare-fronted target: check the UA before blaming the WAF

A run that reports thousands of `403 (Forbidden)` is usually the CDN rejecting **the tool's own
User-Agent**, not filtering payloads. Measured on one engagement (2026-09):

```
sqlmap's default UA + a CLEAN request        -> 403
browser UA + the same clean request          -> 200
browser UA + a tamper payload                -> 422 (from the app, not the WAF)
same run with --random-agent                 -> 0 x 403 across the whole scan
```

Rules:
- **Prove the block is UA-based before writing "the WAF blocks everything."** Two requests, same
  path, tool UA vs browser UA. If the *clean* request is 403'd with the tool's UA, the 403s in the
  scan log say nothing about payload filtering. (The earlier sqlmap run in that engagement reported
  "403 (Forbidden) - 3742 times" and called its own result inconclusive because of it.)
- `--random-agent` (or an explicit browser `--user-agent`) is effectively mandatory on CDN-fronted
  targets; `sqlmap/1.x` is on every WAF's list.
- **A wall of 422s is APP validation, not the WAF.** Read one body: `422 {"error":{"code":
  "validation_error","message":"limit must be a whole number from 1 to 200."}}` means the value is
  enum/format-checked before it reaches a query — that is a *control*, and sqlmap will correctly
  report "does not appear to be dynamic". sqlmap may even print "checking if the target is protected
  by some kind of WAF/IPS" because of those 422s; that guess is wrong here — say so in the write-up.
- **Budget the run.** `--level=5` + a 4-script tamper chain on a slow CDN target ran 2.5 h without
  finishing the first parameter. For a quotable verdict, `--level=2..3 --risk=2
  --tamper=space2comment --random-agent` finished 5 parameters in ~40 min and produced
  `[CRITICAL] all tested parameters do not appear to be injectable`. If you want the risk-3
  OR-based family it skipped, cover it with 3-5 manual payloads (`' OR '1'='1` per parameter →
  expect 422) rather than a second long run.
- **Kill the whole process tree, and kill it twice.** Stopping the wrapper's session left the bash
  script alive: t1 was killed, t2 started on its own, and t3 later ran as an orphan whose log froze
  mid-file (parent SIGTERM'd, stream closed) while `tasklist` still showed `sqlmap.exe`. Check
  `tasklist | grep -i sqlmap` again after killing, and archive the partial log labelled as stopped
  so a frozen file is never mistaken for a completed scan.
- Report the tool verdict **verbatim** next to the request-shape evidence (0 x 403, 422s from the
  app). "No injection here" is far more credible with the UA/422 explanation attached.

---

## Scanner Comparison

| Scanner | Speed | Accuracy | False Pos | Best For |
|---------|-------|----------|-----------|----------|
| nuclei | ★★★★★ | ★★★★ | Low | Known vulns (CVE, misconfigs) |
| ffuf | ★★★★★ | ★★★ | Medium | Directory/param fuzzing |
| dirsearch | ★★★★ | ★★★ | Medium | Directory discovery |
| w3af | ★★★ | ★★★★ | Low | Full web audit |
| wapiti | ★★★ | ★★★ | Medium | Quick vuln scan |
| afrog | ★★★★ | ★★★★ | Low | AI-assisted scanning |
| rapidscan | ★★★ | ★★★ | Medium | Multi-tool combo |
| restler | ★★ | ★★★★★ | Low | API stateful fuzzing |

---

## Integrated Repos (18)

| Repo | Stars | What We Took |
|------|-------|--------------|
| maurosoria/dirsearch | 14.7K | Directory scanning workflow |
| OWASP/Nettacker | 5.6K | Automated pentest framework |
| andresriancho/w3af | 4.9K | Web audit framework config |
| six2dez/OneListForAll | 3.2K | Fuzzing wordlists |
| Qianlitp/crawlergo | 3K | Browser crawler config |
| microsoft/restler-fuzzer | 2.9K | REST API stateful fuzzing |
| lijiejie/BBScan | 2.4K | Fast vuln scanner |
| wapiti-scanner/wapiti | 1.9K | Web vuln scanner |
| Hackmanit/Web-Cache-Vulnerability-Scanner | 1.2K | Cache poisoning scanner |
| w-digital-scanner/w9scan | 1.1K | Plugin web scanner |
| bahaabdelwahed/killshot | 783 | Pentest framework |
| praetorian-inc/titus | 701 | Secrets scanner (487 rules) |
| fgeek/pyfiscan | 575 | Web vuln + version scanner |
| silentchainai/SILENTCHAIN | 463 | AI Burp scanner extension |
| SHAdd0WTAka/Zen-Ai-Pentest | 458 | AI pentest framework |
| aress31/burpgpt | 2.4K | Burp GPT passive scan |
| cypherpunk-symposium/security-pentesting-toolkit | 242 | CTF/pentest resource |
| jassics/security-study-plan | 5.1K | Study plan (pentest roles) |

---

## Cross-References
- Recon → `security-recon` (Phase 0B)
- Attack playbooks → `security-web-attacks` (Phase 0C)
- Cloud → `security-cloud` (Phase 0C)
- Report → `bug-report-delivery` (Phase 0F, ABSOLUTE LAST)