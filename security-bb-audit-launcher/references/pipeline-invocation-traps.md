# Pipeline invocation traps (audit-pipeline-orchestrator.py)

Observed live 2026-10-12 (blink.sv) while resuming an engagement. These are *invocation* traps: the
pipeline is fine, the command line is what costs you a run.

## 1. `--scope` takes DOMAIN(S), not the policy prose
```
# WRONG — blocks instantly, prints "SCOPE GATE BLOCKED ... Tidak ada request yang dikirim"
python audit-pipeline-orchestrator.py "https://blink.sv" \
  --scope "Blink's software or services (blink.sv + blinkbtc.com estate, web apps, APIs, mobile)"

# RIGHT — the gate is a deterministic hostname check (`scope_checker.py --domain <list>`)
python audit-pipeline-orchestrator.py "https://blink.sv" --scope "blink.sv,blinkbtc.com"
# or omit --scope entirely: the pipeline logs its own gate message — the scope rule stays:
#   Scope = written artifact (program policy, platform listing, security.txt).
#   Self-hosted program without stated scope → the program's own assets are treated as
#   in-scope; third-party infrastructure stays out of scope.
#   (the log line itself is tool output, not a scope decision)
```
The blocked run still writes `run-meta.json`/`PHASE_LOG`-adjacent state, so remove/ignore that dir before
relaunching, otherwise you resume a failed 0A.

**The match is on the EXACT hostname(s), not the apex + wildcard.** `--scope "gasunie.nl"` rejected a
target of `https://www.gasunie.nl` with `OUT OF SCOPE: www.gasunie.nl not in gasunie.nl` — a bare
apex does not cover its `www.` sibling, and a `*.gasunie.nl` entry alone also wasn't accepted. List
every form explicitly:
```
--scope "www.gasunie.nl,gasunie.nl,*.gasunie.nl"     # apex + www + wildcard
```
Rule of thumb: seed the list with the literal host of the `TARGET` URL, then add apex + `*.` wildcard.

## 2. `STALL-WARN` is ADVISORY — prove liveness with file mtimes, never by killing
A long 0C sub-step (dense forced-execution, payload variants, DOM-XSS with a headless browser) emits
nothing to stdout for 15–45 min while the orchestrator's step counter stays put:
```
[STALL-WARN] orchestrator: no step progress for 1821s (last phase 0A, pid=...) - still running, not killed.
```
Before touching it, check what the step is actually producing:
```
find "<orchestrator-workdir>" -type f -printf "%TH:%TM %p\n" | sort -r | head -6
```
New `variants/*.txt` / `tool-evidence/*.txt` inside the last few minutes = alive, keep waiting (the step
counter tracks phase transitions, not work). Only kill on an empty mtime delta *and* no child tool process.

## 3. Children outlive the parent — reap leftovers before the next run
Three orphaned `nuclei.exe` from earlier attempts were still holding ~1.3 GB on a 6 GB host while a new run
started (the orchestrator warns below 1.2 GB free RAM: "proses akan DIBUNUH Windows tanpa traceback").
Check with `tasklist | grep -iE "nuclei|sqlmap|dalfox|ffuf"` and kill by PID (via Python `taskkill /PID <n>
/F`) before relaunching.

## 4. The pipeline's own recon can be thinner than the engagement's
Its `httpx` step returned `0 live hosts (rc=255)` and seeded only 2 hosts, so single-target template runs
covered essentially `blink.sv` + `www` (host histogram in `urls.txt` is the tell: 268/316 URLs on one host)
while ~80 other hosts of the estate went unscanned. **Always cross-check the pipeline's host coverage
against the engagement's own host inventory and run a supplementary scan yourself** — otherwise a clean
pipeline result means "clean on two hosts", not "clean on the estate":
```
nuclei -l <engagement>/recon/nuclei_hosts_list.txt \
  -tags exposures,exposed-panels,misconfiguration,default-login,takeovers,unauth \
  -severity low,medium,high,critical -rl 20 -c 6 -timeout 10 -retries 1 \
  -stats -no-color -o "<ENGAGEMENT>/recon/nuclei_hosts2.txt"    # native path, not /c/... (MSYS)
```
Tag-set sizing matters: an 11-tag set hit 267 k requests at 11 rps (~6.7 h); trimming to 6 tags and
`-rl 20 -c 6` cut it to ~220 k at 25 rps (~2.4 h) — and the low-signal `wildcard-dns-detect` /
`dns-waf-detect` hits dominate the output, so filter them before reading a result set.

## 5. Scanner candidates are candidates — verify before they reach the report
The DOM-XSS check flagged `https://blink.sv/#"><img src=x onerror="window.__DOMXSS=1">`
(`reason: dom-sink:window.onerror`); a real-Chrome check showed the fragment stays URL-encoded
(`location.href` = `#%22%3E%3Cimg%20src=x…`), no injected node, marker flag never set → **false positive**.
Verify each automated candidate once, in your own browser, and record the dismissal in the report's
coverage section (the guard checks for exactly this kind of unverified claim).

## 6. Resuming
`STATE saved: completed=['0A','0B'] current=0C` + "resume" semantics mean re-running the same command
continues instead of restarting — so fix the invocation (scope/tech) in place rather than deleting the
workdir, unless 0A itself failed.

## 7. linkfinder (and fetchers like it) 403 on a Cloudflare-protected root — aim at a JS asset
`linkfinder.py -i https://gasunie.nl -o cli` fails with `HTTP Error 403: Forbidden` (Cloudflare) and the
wrapper records `status: FAILED_USAGE`, which then fails `verify-tool-usage` CHECK 2b and blocks the
gate. Fix: point `-i` at a real first-party JS asset instead of the domain root — pull one from the
pipeline's own crawl (`grep -iE '\.js($|\?)' <workdir>/crawled.txt | grep -vE 'piwik|google|gartner'`),
e.g. `-i https://www.gasunie.nl/compiled/js/project_js-9917cd9.js`. Then, so the gate sees it as run:
rewrite `tool-evidence/linkfinder-source-leak.txt` with the new command + stdout, and flip
`tools-usage.json` (`status`→`EXECUTED`, real `command`/`output_bytes`) and `asset-coverage.json`
(`0C:tools:linkfinder` → `status: USED` + evidence path). Same pattern applies to any source-leak
fetcher that gets WAF-blocked on the bare domain.

## 8. The deep-audit guard rarely goes green on a general web target — that is INFRA, not a signal
For a Cloudflare-fronted corporate site with `--tech "general"`, `deep-audit-mode.py guard` typically
stays RED because the PoC-corpus stages can't do anything applicable: `execute-poc-variants.py` /
`execute-poc-techniques.py` report `Matched repos: 0` (the tech-match yields repos with
`status: NO_ENTRY_POINT` or non-web payload types — deserialization/protocol/firmware, "not fireable via
HTTP params"), so C4/C5/C6b stay `NOT_RUN`, `candidates.json` is empty, and CHECK 8/11/12 fail. This is
NOT evidence the target is safe or unsafe — it means the local PoC corpus simply has nothing for this
target class. Confirmed by prior engagements: even completed targets (`atg.se`, `yandex.fr`) still
`RESULT: FAIL` the guard.

Report discipline when the guard is red but your real scanners ran clean:
- State the negative honestly with **coverage + the tool list that actually executed** (e.g. "23 tools:
  nuclei/sqlmap/dalfox/sstimap/nikto/xsstrike/CORScanner/... — all `confirmed: 0`"), and record the
  false-positive dismissals (sqlmap/dalfox "interesting" flags that turned out to be no-ops).
- Say explicitly the guard is blocked on **PoC-corpus infra + WAF**, not on a finding — and name the
  untested surface (authenticated flows behind login, OT/SCADA behind the perimeter).
- Do NOT upgrade the language to "matang / terkunci rapi / no findings" on a red guard. The gate exists
  to stop exactly that overclaim. Mark the pool `audited --note "0 temuan valid; N tool jalan; semua
  confirmed=0; <WAF> depan"` and offer next moves (self-provision a test account for the authed surface,
  or pivot).
