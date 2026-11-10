# audit-run-all.py — Permanent Execution Architecture

## Why This Exists

User correction (2026-09-22): "Enforce, rule, checkpoint, hard gate — tapi semua apa efeknya? Tetap kamu langkahi juga. Sy mau solusi permanen."

ALL rules, checkpoints, hard blocks are TEXT the agent can read and ignore.
The PERMANENT fix is a SCRIPT that forces execution.

## Architecture

```
audit-run-all.py <TARGET> --tech "<tech>"
  │
  ├── Phase 0A: Init tracker + PHASE_LOG
  │     └── audit-exec-tracker.py init
  │
  ├── Phase 0B: Recon
  │     ├── subfinder → subs.txt
  │     ├── httpx → live.txt
  │     ├── naabu → ports.txt
  │     ├── gau → urls.txt
  │     └── katana → crawled.txt
  │
  ├── Phase 0C: EXPLOIT EXECUTION
  │     ├── audit-sequential.py → 30 vector output files
  │     ├── nuclei scan → nuclei-results.txt
  │     ├── poc-pipeline.py → poc-results.md
  │     ├── aggregate-findings.py → findings.json
  │     ├── finding_gate.py → REPORT-survivors.md
  │     └── chain_builder.py → exploit-chains.json
  │
  ├── Phase 0D: Checkpoint (verify-tool-usage gate)
  ├── Phase 0E: Findings (aggregate → gate → validate → review)
  └── Phase 0F: Report
        ├── audit-checkpoint.py --phase all
        └── AUDIT-SUMMARY.md
```

## Verification Chain

Every step verified by:
1. File exists on disk (not self-reported)
2. File has content (not empty)
3. State saved (resume works)
4. Checkpoint PASS before next phase

## Resume on Failure

If script breaks mid-run:
1. `audit-state.py list` → shows last saved state
2. Re-run `audit-run-all.py <TARGET>` → picks up from where it stopped
3. Each phase is idempotent — safe to re-run

## Why Scripts > Rules

- Rules are advisory text → agent can skip
- Scripts are executable code → forces execution
- Scripts verify their own output → can't claim done without proof
- Scripts save state → resume works
- One command → no room for "I'll do it later"
