# Pipeline operations — backgrounding, stalls, workspace hygiene
Measured on one full web run (0A→0C), 2026-10-14.

## 0. Invocation gotchas (fail in the first 30 seconds)

- **`--scope` is an exact-host matcher, not a suffix matcher.** `--scope "gasunie.nl"` rejects
  the target itself: `❌ OUT OF SCOPE: www.gasunie.nl not in gasunie.nl`. Pass every variant
  explicitly, comma-separated: `--scope "www.gasunie.nl,gasunie.nl,*.gasunie.nl"`. The apex
  and `www.` are different strings to the matcher.
- **No `--help`.** The first positional arg must be the target URL; `--help` is parsed as a
  target and dies with `target tidak dikenali tipe-nya`. Read the `add_argument`/usage block
  from the script source instead (`grep -n "add_argument" audit-pipeline-orchestrator.py`).
- State persists per-target under `~/AppData/Local/hermes/poc-plans/orchestrator-<slug>/`;
  a failed invocation still writes state, and re-running the fixed command resumes cleanly.

## 1. Background the orchestrator with a timeout that fits a real run

Observed wall-clock for one target: 0A ~3 min · 0B ~17 min (subfinder/httpx/dork-recon/amass/
naabu/katana/gau/waymore) · force-full-execution ~28 min · payload variants ~43 min ·
DOM-XSS ~20 min. **≈ 1h50m total.**

`timeout 3000` killed the run mid-variants and cost a rework cycle. Launch with
`timeout 7000`+ (or none) and let the notification tell you when it ends.

## 2. RESUME MODE is real — re-run the identical command

Log confirms both behaviours:
```
RESUME MODE: already completed ['0A','0B'] — skip those
STEP 1: SKIP force-full-execution (force-state sudah complete)
```
So a killed run costs only the phase it died in. Do not restart from a clean directory.

## 3. STALL-WARN is a warning, not a kill

```
[STALL-WARN] orchestrator: no step progress for 927s (last phase 0A, pid=18044)
             - still running, not killed. Unblock: python toolguard.py unblock --pid <pid>
```
It names the *watcher's* phase, which can lag reality — do not read "last phase 0A" as
"the run is stuck in 0A".

## 4. Diagnose the blocking CHILD, never restart the parent

Walk the tree (`psutil.Process(pid).children(recursive=True)`) and read `age` + `cpu_percent`:
the guilty process was a variant tool at `age≈764s, cpu=0.0%`. Killing that child (and its
`cmd.exe` wrapper) let the runner advance and record the tool as NO RESULT.

A hung variant tool may also be **re-spawned in a loop** by the runner — one kill is not
enough; watch for respawn over ~2 minutes before concluding you fixed it. When it respawns
immediately, stop killing and remove the blockage so the runner gets an instant failure
instead (only a fix that produces an honest `NOT_FOUND`/`NO RESULT` record — never a stub that
prints fake output).

## 5. Evidence lags the log

`tool-evidence/` kept filling (17 → 19 → 20 → 25 → 28 files) while `orchestrator.log` still
showed the same STEP line for many minutes. For liveness, watch **file count/mtime** in the
evidence directory, not log silence. (`STALL-WARN` firing during that time was noise.)

`PHASE_LOG.md` is worse: it freezes after `PHASE 0A — SETUP COMPLETE` and never gets another
line — two full 0B/0C runs left it untouched. Never diagnose progress from it; the truth is
`asset-coverage.json` (per-asset USED/N-A/NOT_RUN) + newest file mtime in the run directory.

## 6. Variant failures are recorded, not backfilled

The runner emits:
```
❌ Variants FAILED — flagged for REWORK: [tool_router] auth-bypass ->
   FAILED-UNCLASSIFIED:  (NO RESULT - record as such, do NOT substitute curl)
```
Honour it verbatim in the coverage section: `NOT RUN / NO RESULT`, with the reason. The gate
refuses a "clean" claim built on a tool that produced nothing.

## 7. One workspace, one tree (Windows/MSYS twin directories)

An engagement directory very often exists **twice** — once with the path segment that carries
a space (`D:/data hermes/<target>/`) and once without (`D:/data/hermes/<target>/`), because
`write_file` paths and shell paths get typed/normalised differently. Symptoms: a script you
just wrote is "not found", evidence files split across two directories, `cat` seeing files that
`ls` in the canonical dir does not.

Discipline:
1. After the **first** write into a new engagement dir, `ls -d` **both** candidate paths.
2. Pick the one matching the pool/engagement convention as canonical; immediately
   `mv` the stray files over and `rmdir` the twin.
3. Re-check after every `write_file` whose `resolved_path` you did not read; the twin re-forms
   silently.
4. Run scripts with `cd "<canonical>" && python3 <relative-name>` so no spaced path is ever
   passed as an argument (a spaced arg gets mangled between shell and Windows Python).

## 8. Redirected Python output is block-buffered

`python3 script.py > log` may show only a handful of lines for many minutes, and a
`timeout` kill **discards the buffer** — a killed run looks like it did almost nothing.
Use `python3 -u`, or tail the artefact files instead of the stdout log.

## 9. Dead parent across sessions — detect, then re-run identical command

The orchestrator run usually outlives its chat/CLI session; when you come back later the
parent may be **gone** (its `process` entry vanished, `run-meta.json`'s `pid` absent from
`tasklist`). Detection in 3 checks:
1. `process list` empty for the session that launched it (a new session never inherits it).
2. `tasklist /FI "PID eq <pid from run-meta.json>"` → "No tasks are running".
3. Newest mtime in `orchestrator-<slug>/` frozen minutes ago (compare `asset-coverage.json`,
   `tool-evidence/`).

Fix = **relaunch the identical command** (resume mode, §2); state picks up where it stopped.
Two things that look alarming but are normal on relaunch:
- `⚠️ RAM bebas <1.2 GB` warning — reclaim first with `wsl --shutdown` (~0.5-1 GB), the
  pipeline historically gets OOM-killed by Windows with no traceback.
- `❌ GATE FAILED (attempt 1)` at 0D followed by `🔁 REWORK (generic): re-running full force
  execution` — that's the built-in auto-rework loop doing its job, not a crash. Read the
  3 named failures, let it run; report only after the gate turns green.
