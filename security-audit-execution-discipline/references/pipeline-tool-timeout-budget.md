# Bounding tool calls inside a looping layer — and why a Windows `timeout=` is a lie

Companion to **RULE 3** (Timeout = Retry) and the "Per-Tool Timeout Values" table.
Source: forexfactory.com engagement 2026-09-30, where `PHASE 0C-C6` killed the whole orchestrator with

```
subprocess.TimeoutExpired: Command '[… execute-references.py <target> --target-dir <dir> --max-clues 200]'
… timed out after 2400 seconds
```

A pipeline that aborts there produces **no report** (correct — the gate never passed), so this is a
coverage hole, not a target result. RULE 35.5 says "environment, re-run pending". This file records the
root cause and the patch, so the next session fixes it instead of re-deriving it.

---

## 1. Root cause: a looping layer multiplies per-tool timeouts

`execute-references.py` walks up to `--max-clues` (200) reference clues and, for every clue whose class
maps to a real tool, calls `tool_router.route_and_run(...)`. `route_and_run` had **no cap**:

| tool | per-call timeout |
|---|---|
| arjun | 600 s |
| sqlmap | 900 s |
| nuclei | 1200 s |
| dalfox / gobuster | 600 s |

The orchestrator gives that whole step **one** `timeout=2400`. So the budget arithmetic is:

```
worst case = Σ(per-call timeouts) = 200 clues × up to 1200 s
required    = one step timeout  = 2400 s
```

Any target where ≥4 heavy tool calls trigger is *guaranteed* to abort. The rule that generalises:

> **A layer that can invoke a tool more than once must carry its own wall-clock budget.
> Never let a looping caller inherit only the parent's subprocess timeout.**

The same shape exists in `execute-variants` / `execute-poc-variants` / `execute-poc-techniques` /
`execute-business-logic` (all call the router in a loop) — they were merely under the cliff because
their loops were shorter. Check them when touching this.

## 2. Second defect: on Windows, `subprocess.run(shell=True, timeout=N)` does not bound wall clock

`_run()` used:

```python
r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
```

With `shell=True`, the timeout kills **`cmd.exe` only**. The grandchild (`sqlmap`/`arjun`/`nuclei`) keeps
the stdout pipe open, so `communicate()` blocks until the *grandchild* exits. Measured:

```
_TIMEOUT_CAP=1 against a 3 s child  ->  reported 'TIMEOUT 1s', wall clock 3.2 s   ← the value is a lie
```

That is why a "2400 s" step can actually run far longer, and why a per-call cap alone is not enough.
Fix: `Popen` + tree-kill.

```python
_TIMEOUT_CAP = None  # set by route_and_run(timeout_cap=...) — clamps EVERY tool timeout


def _run(cmd, timeout=600):
    """On timeout HARD-KILL the whole process tree (Windows: shell=True children survive
    subprocess.run's timeout and keep the stdout pipe open, so the wall clock is unbounded)."""
    if _TIMEOUT_CAP:
        timeout = min(timeout, _TIMEOUT_CAP)
    try:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    except Exception as e:
        return -1, "", str(e)
    try:
        out, err = p.communicate(timeout=timeout)
        return p.returncode, out, err
    except subprocess.TimeoutExpired:
        for kill_cmd in (f'taskkill /F /T /PID {p.pid}', None):
            try:
                if kill_cmd:
                    subprocess.run(kill_cmd, shell=True, capture_output=True, timeout=20)
                else:
                    p.kill()
            except Exception:
                pass
        try:
            out, err = p.communicate(timeout=15)
        except Exception:
            out, err = "", ""
        return -1, (out or ""), (err or "") + f"\nTIMEOUT {timeout}s (process tree killed)"
    except Exception as e:
        return -1, "", str(e)
```

Keep the literal substring `TIMEOUT <n>s` in the message — existing status classifiers grep for it.
Same tree-kill family as the interactsh leak guard (RULE 2b item 3).

## 3. The patch: a cap on the router + a budget in the loop

`tool_router.route_and_run(class_id, target, output_dir, vector="", ev_dir=None, timeout_cap=None)`
sets a module global for the duration of the call:

```python
def route_and_run(class_id, target, output_dir, vector="", ev_dir=None, timeout_cap=None):
    global _TIMEOUT_CAP
    _TIMEOUT_CAP = timeout_cap          # default None ⇒ every existing caller unchanged
```

`execute-references.py` gained `--budget <sec>` (default 900) and `--tool-cap <sec>` (default 120):

```python
deadline = time.monotonic() + budget
for idx, item in enumerate(all_clues, 1):
    if time.monotonic() > deadline:
        skipped_budget = len(all_clues) - idx + 1
        log(f"⏱  BUDGET {budget}s HABIS di clue #{idx} — {skipped_budget} clue SKIPPED_BUDGET")
        break
    …
    evres = tr.route_and_run(clue_class, url, target_dir, vector=f"ref-{idx}",
                             ev_dir=ev_dir, timeout_cap=tool_cap)
```

On budget exhaustion append a **meta entry** to `reference-usage.json` so the gate still sees a non-empty
file and the log is honest:

```python
usage.append({"clue_idx": None, "ref": "META", "type": "SKIPPED_BUDGET",
              "clue": f"{skipped_budget} clue tidak dijalankan: budget {budget}s habis",
              "skipped_budget": skipped_budget, "budget": budget, …})
```

**Skipped ≠ negative.** Write it as `SKIPPED_BUDGET / NO RESULT (re-run pending)`, never as a clean result
— same rule as RULE 2c's DNS sub-case.

Recommended flags when re-running the stage standalone:

```bash
python <scripts>/execute-references.py "<target>" \
  --target-dir "<out-dir>" --max-clues 200 --budget 900 --tool-cap 120
```

## 4. Verification (run these, don't trust the patch landed)

```bash
python -m py_compile tool_router.py execute-references.py
grep -c _TIMEOUT_CAP tool_router.py            # expect ≥5
grep -c timeout_cap  tool_router.py execute-references.py
grep -c skipped_budget execute-references.py
```

Functional proof the cap is applied *and* the wall clock is bounded:

```python
tr._TIMEOUT_CAP = 2
rc, out, err = tr._run('python -c "import time;time.sleep(30)"', timeout=900)
# expect: rc=-1, elapsed ≈2.6 s (NOT 30 s), err contains 'TIMEOUT 2s (process tree killed)'
tr._TIMEOUT_CAP = None
rc, out, err = tr._run('python -c "print(123)"', timeout=60)   # expect rc=0, out '123'
```

Measured after the fix: 2.6 s (was 3.2 s for a 3 s child under `timeout=1`). Behaviour with the cap
disabled is unchanged, which is what protects every other executor.

## 5. Ship it — the bundle goes stale the moment you patch

Only two entries changed, so a surgical rebuild beats a full regeneration:

```python
# rebuild audit-pipeline-bundle-v1.zip in place, substituting the patched entries
import zipfile, hashlib, os
TARGETS = {"audit-pipeline-bundle-v1/toolkit/scripts/tool_router.py": "<scripts>/tool_router.py",
           "audit-pipeline-bundle-v1/toolkit/scripts/execute-references.py": "<scripts>/execute-references.py"}
zin = zipfile.ZipFile(ZIP); zout = zipfile.ZipFile(ZIP + ".rebuild", "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename in TARGETS:
        data = open(TARGETS[item.filename], "rb").read()
    zout.writestr(item, data)
zout.close(); zin.close()
z = zipfile.ZipFile(ZIP + ".rebuild")
assert z.testzip() is None
for name, live in TARGETS.items():                       # md5 in zip == md5 on disk, per entry
    assert hashlib.md5(z.read(name)).hexdigest() == hashlib.md5(open(live, "rb").read()).hexdigest()
assert len(z.namelist()) == ORIGINAL_ENTRY_COUNT          # 1932 for the 2026-09-29 bundle
os.replace(ZIP + ".rebuild", ZIP)
```

Back up the zip first (`audit-pipeline-bundle-v1.zip.bak_<date>`). Keep the entry count assertion — it is
what caught a truncated rebuild. Full flow (with `_gen_index.py` / MANIFEST / LOAD regeneration):
`references/audit-pipeline-bundle-rezip-2026-09-29.md`.

## 6. What this is NOT

- Not a target result. The stage that died told you **nothing** about the target; record
  `NO RESULT / re-run pending` and re-run it.
- Not a reason to lower per-tool timeouts globally. The cap is **per layer** (`timeout_cap` passed only by
  the looping reference layer); the top-level C1 battery keeps its long timeouts because it fires each tool
  once.
