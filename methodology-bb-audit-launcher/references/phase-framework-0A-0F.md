# The audit phase model is 0A → 0F (authoritative)

Source of truth: `scripts/audit-pipeline-orchestrator.py`. `audit-run-all.py` is now a thin wrapper
around it, and the manual skill pipeline must mirror it exactly.

## Phase → artifact map

| Phase | Name | Produces / gates on |
|---|---|---|
| 0A | SETUP | `PHASE_LOG.md` + `audit-exec-tracker.py init`; scope check runs before any request |
| 0B | RECON | `subs.txt`, `live.txt`, `urls.txt`, `ports.txt`, `crawled.txt` |
| 0C | EXPLOIT | C1 `force-full-execution` → `tools-usage.json`; C2 `execute-variants` → `variant-usage.json`; C3 `execute-business-logic` → `business-logic-usage.json`; C4 `track-poc-execution` → `poc-execution.json`; C5 `execute-poc-variants` → `poc-variant-usage.json` |
| 0D | GATE | `verify-tool-usage.py` returns 0 (11 checks, HARD BLOCK, auto-rework ×3); no `FAILED_USAGE` |
| 0E | FINDINGS | `aggregate-findings.py` → `findings.json`; `chain_builder.py`; `finding_gate.py` → `REPORT-survivors.md`; `validate-findings.py` → `validated-findings.json` |
| 0E-REVIEW | (sub-phase) | `review-candidates.py` → `review-candidates.json` + `review-candidates.md` (3× cek, low→high) |
| 0F | REPORT | `report-agent.py` → `AUDIT-REPORT.md/.html/.pdf` |

`audit-checkpoint.py` must accept `--phase 0A|0B|0C|0D|0E|0F|all` and must label them
SETUP / RECON / EXPLOIT EXECUTION / GATE / FINDINGS / REPORT. A checkpoint that stops at `0D` and
calls it "REPORT" is the drift bug: it silently makes 0E and 0F ungated.

## Drift sweep — run this before claiming the framework is aligned

```bash
cd ~/AppData/Local/hermes/skills
grep -rn "0A-0D\|0A→0D\|Phase 0D" --include=*.md .
```

Every hit must be either (a) explicitly documenting that `0A→0D` is WRONG, or (b) a real 0D **gate**
reference (contains `verify-tool-usage`, `GATE`, `checkpoint`, `--phase 0D`, `0D→0E`, `must PASS`).
Anything else is stale and means "report", i.e. now 0F.

On the sweep that produced this file the stale `0D == report` convention was spread over ~30 files,
so expect it to be broad rather than a single line:

- `security/bb-audit-launcher/SKILL.md` (+ `references/{audit-execution-tracker,crypto-knowledge-index,defi-patterns,execution-discipline-protocol,phase-execution-enforcement,redteam-playbook}.md`)
- `bb-audit-launcher/references/*` (a second, top-level copy of the same reference set exists — sweep both)
- `security/bug-bounty/SKILL.md` + `references/redteam-playbook.md`
- `security/audit-execution-discipline/SKILL.md` + `references/audit-run-all-architecture.md`
- `security/bug-bounty-exhaustive-testing/SKILL.md`
- `security/exploit-cookbook/references/{execution-discipline-protocol,redteam-playbook,phase-execution-enforcement,slowmist-vulns,sqlmap-advanced,sqli-exfiltration-lab}.md`
- `security/{cex-event-contract-audit,crypto-library-audit,onchain-finding-verification,security-cloud,security-scanners,security-web-attacks,smart-contract-audit}/SKILL.md` — all carry the same `REPORT GATE (Phase 0D)` line
- `bug-report-delivery/SKILL.md` + `references/writeup-index.md`
- `context-resilient-skill-design/SKILL.md` (context-budget table row)

Also update the PHASE_LOG **templates**, or every new engagement re-introduces the drift:
`_progress/_template/PHASE_LOG.md` and the live engagement's own `PHASE_LOG.md`.

## Verify, don't assume

```bash
python audit-checkpoint.py <completed_target_dir> --phase all   # expect all ✅ on a finished audit
python audit-checkpoint.py <fresh_target_dir>     --phase all   # expect ❌ 0A "marked COMPLETE"
```

Run it against a target that genuinely HAS a report — that is the only way the 0F branch gets
exercised, and it is exactly where the `*report*` vs `reports/` directory bug showed up. A fresh
empty target passes the "report missing" path trivially and hides the defect.
