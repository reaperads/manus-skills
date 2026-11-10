# Multi-Session Audit Resume — Implementation (2026-09-26)

Problem: 0C exploit layer (C1..C6b) can run for hours with 150-repo caps; a
session/context/provider break forced full restart from 0A because the
orchestrator never persisted per-phase progress (only force-full-execution
saved its own state file, and `audit-state.py` was not wired in at all).

## Files

`~/AppData/Local/hermes/scripts/audit-pipeline-orchestrator.py` additions:

```python
def _state_file(self):          # trackers/audit-pipeline-<safe>.json
def _load_state(self):          # {target, tech, completed_phases:[], current, updated}
def _save_state(self, completed_phase=None, current=None, note=""):
def _phase_done(self, phase):   # phase in completed_phases
```

`run_pipeline` now:
```python
if not self._phase_done("0A"): self.run_setup(); self._save_state(completed_phase="0A", current="0B")
if not self._phase_done("0B"): self.run_recon(); self._save_state(completed_phase="0B", current="0C")
if not self._phase_done("0C"): self.run_force_execution(); self.run_variants_and_pocs(); self._save_state(completed_phase="0C", current="0D")
if not self._phase_done("0D"): self.verify_tool_usage(); self._save_state(completed_phase="0D", current="0E")
if not self._phase_done("0E"): validated_json = self.run_findings_layer(); self._save_state(completed_phase="0E", current="0E-REVIEW")
if not self._phase_done("0E-REVIEW"): self.run_review_candidates(); self._save_state(completed_phase="0E-REVIEW", current="0F")
if not self._phase_done("0F"): final_report = self.generate_report(); self._save_state(completed_phase="0F", current="DONE")
```

## Sub-phase skip (Level 2) — inside run_variants_and_pocs

```python
def _done(fname):
    f = self.output_dir / fname
    return f.exists() and f.stat().st_size > 100
skip_c2  = _done("variant-usage.json")
skip_c3  = _done("business-logic-usage.json")
skip_c4  = _done("poc-execution.json")
skip_c5  = _done("poc-variant-usage.json")
skip_c6  = _done("reference-usage.json")
skip_c6b = _done("poc-techniques-usage.json")
```
Each block then wraps with `if skip_cX: log SKIP else: run`.

## Verified behavior (unit test)

```
SAVED: completed=['0A'] current=0B
SAVED: completed=['0A','0B'] current=0C
0A done: True, 0C done: False
state file contains full JSON {target, tech, completed_phases, current, updated}
```

## Notes

- Sanitize target for filename: `re.sub(r'[^A-Za-z0-9._-]', '_', target)` —
  colon/slash in URL breaks Windows paths.
- Test state files (`audit-pipeline-https___example.com.json`) must be cleaned up
  after testing; real target state files should be left alone (no delete without approval).
- `audit-state.py` remains for simple list/save/complete but the orchestrator
  does NOT depend on it — do not expect one to update the other.