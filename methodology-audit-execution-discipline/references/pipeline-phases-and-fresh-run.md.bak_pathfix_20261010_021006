# Audit pipeline: the current phase model and how to force a genuinely fresh run

Applies to `audit-pipeline-orchestrator.py` / `audit-run-all.py` in
`~/AppData/Local/hermes/bundle-src/audit-pipeline-bundle-v1/toolkit/scripts/`.

## 1. The phase model is 0A → 0F (not 0A → 0D)

Read off the orchestrator's own docstring — do not assume the older 4-phase list:

```
0A SETUP      : PHASE_LOG + audit-exec-tracker init
0A-SCOPE      : HARD GATE — refuses to run without --scope
0B RECON      : subfinder + httpx + URL probes → urls.txt
0C EXPLOIT    : C1 dedicated tools (force-full-execution) | C2 payload variants
                | C3 business-logic (15 vectors) | C4 matched PoC repos
                | C5 PoC variants | C6 reference attacks | C6b poc-techniques
0D GATE       : verify-tool-usage (11 checks, HARD BLOCK, auto-rework ×3)
0E FINDINGS   : aggregate-findings → chain_builder → finding_gate → validate-findings
0E-REVIEW     : review candidates one-by-one, 3× check, low→high (only survivors reach 0F)
0F REPORT     : report-agent → AUDIT-REPORT.md/.html/.pdf
```
The operator expects the NEWEST model. Writing a PHASE_LOG that stops at 0D is treated as a stale
pipeline (a real user correction: "kok sampai phase 0d aj, kan phase udh sampai 0f yg terbarunya").
Copy the phase list into the target's PHASE_LOG.md verbatim and update it as you go.
`0E-REVIEW` is the triage gate: pipeline output (review-candidates "READY", validated-findings
"High") is INPUT, not findings — see `pipeline-triaging-2026-09-26.md`.

## 2. Correct invocation

```bash
python <bundle>/toolkit/scripts/audit-pipeline-orchestrator.py \
    https://target.example --tech "nextjs,cloudflare,node,react" \
    --scope "target.example,*.target.example"
```
- Target MUST be a full URL (a bare domain makes force-full-execution skip every tool).
- `--scope` is **mandatory**: without it the 0A-SCOPE gate aborts with
  `"❌ SCOPE GATE: --scope WAJIB diisi ... Pipeline ditolak sebelum menembak request apa pun."`
- `--output-dir` is NOT honoured by the orchestrator (it derives the dir from the target:
  `~/AppData/Local/hermes/poc-plans/orchestrator-<target-with-underscores>`). `audit-run-all.py`
  forwards some flags, but the orchestrator itself only parses `--tech/--scope/--exclude`.
- Run it in the background with notify: it is long, and it can die mid-0C without a non-zero exit that
  you would otherwise notice.

## 3. Forcing a FRESH run (the state that silently skips recon)

Even after moving the poc-plans output dir aside, the orchestrator printed
`RESUME MODE: already completed ['0A', '0B'] — skip those` and jumped straight into 0C. The phase state
lives OUTSIDE the output dir, in `~/AppData/Local/hermes/trackers/`:

| File | Role |
|---|---|
| `audit-pipeline-<url-encoded-target>.json` | `completed_phases` / `current` (the resume driver) |
| `force-state-<target>.json` | force-full-execution per-tool state (a "done" tool is skipped) |
| `<target>.json` | audit-exec-tracker state |

Reset procedure (archive, never delete — the operator's rule is "don't delete state without asking"):

```bash
cd ~/AppData/Local/hermes/trackers
for f in "audit-pipeline-https___target.example.json" \
         "force-state-https___target.example.json" "https___target.example.json"; do
  [ -f "$f" ] && mv "$f" "$f.bak_$(date +%Y%m%d_%H%M)"
done
```
Then relaunch. Verify the log shows `PHASE 0A: SETUP … ✅ PHASE 0A COMPLETE` → `STEP RECON: subfinder +
httpx … urls.txt: N candidate URLs written` before trusting any later phase. A run that starts at
"STEP 1: Running FORCE FULL EXECUTION" with no urls.txt means the fresh reset did not take.

## 4. Known rough edges (verify, don't trust the label)
- `httpx: 0 live hosts (rc=255)` — a tool-level failure, not "no hosts". Re-run httpx yourself with
  simple flags (`-title -tech-detect -status-code -server -silent`) before reporting a dead surface.
- force-full-execution can stall or die inside 0C (observed: arjun + sqlmap wrote evidence, then the
  process vanished with the log stuck on "STEP 1"). Check `tool-evidence/` mtimes and the process list;
  if it is gone, treat C1 as partial and finish the layer yourself with rate-limited commands.
- Tool-invocation bugs to expect inside C1 (log them, re-run manually when the vector matters):
  dalfox needs `dalfox url <u>`; ffuf/CORScanner reject `--headless`; graphqlmap crashes on pyreadline
  under Python 3.14; SSRFmap needs `-r REQFILE -p PARAM`.
- An `--output-dir`-less run writes into the shared user profile, so two targets never collide but the
  same target re-uses state — hence §3.

## 5. Vendor-rules override
When the target publishes a VDP/disclosure policy, its rules outrank the pipeline's appetite: read
`/.well-known/security.txt` (→ policy URL) before 0C and obey the in/out-of-scope list. Practical
consequences seen on a self-hosted SaaS program: **subdomains and origin-IP exposure are explicitly out
of scope** (record them as internal notes, never as findings), "no automated scanning that puts
noticeable load" ⇒ skip full-tag nuclei and cap ffuf (`-rate 10–15`), own accounts only, and no mail to
third parties. Put these in the PHASE_LOG under a "VENDOR DISCLOSURE POLICY" heading so every later
phase (and the 0E-REVIEW gate) is judged against them.
