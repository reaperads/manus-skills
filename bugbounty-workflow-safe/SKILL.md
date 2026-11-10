---
name: bugbounty-workflow-safe
description: Bug Bounty Workflow — Safe Version
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Bug Bounty Workflow — Safe Version

Run a scoped bug-bounty engagement end to end, with proof discipline.
This is a safe rewrite of the structure in the user's note
`bugbounty-workflow-0xkonde.md`. It keeps the phase order and the
validation discipline, but it does NOT adopt full autonomy, no-ask
testing, or unauthenticated-first attacks on live targets. Scope and
permission come first, always.

## Non-negotiable rules

- Only test assets that are explicitly in scope in a written program
  policy, a VDP, or a scoped test the user has authorised. If scope is
  unclear, stop and ask before sending any live request.
- Read the policy first: in-scope assets, exclusions, rate limits, and
  disclosure terms. Deny wins: an excluded asset is out, even if it
  looks interesting.
- Check disclosed reports for the same asset, endpoint, and parameter
  before testing, so you do not re-report a known issue.
- Use only the user's own test accounts and the user's own data for
  proof. Never use another person's account, project, or production
  data as a victim.
- One hypothesis per request. Change one variable, keep everything
  else constant.
- Minimal data access: read one record to prove impact, not a table.
  Stop at the first proof of impact.
- No destructive payloads (delete, drop, mass change) without a stated
  rollback and the user's explicit approval for that step.
- Stay inside rate limits. Do not hammer a target, and do not bypass
  a captcha, MFA, or safety block to keep testing.
- A live action that sends, changes, or submits something needs the
  user's approval for that action. A general "do your best" does not
  approve a specific live test, purchase, or submission.

## Phase order

```
0 scope      -> policy, in-scope list, out-of-scope list, scope.md
1 recon      -> subdomains, live hosts, crawl, JS, API spec, passive first
2 surface    -> rank attack surface: auth-required first, then money paths,
                uploads, then admin surfaces
3 attack tree-> threat model + crown jewel, grounded in recon
4 hunt       -> one bug class at a time, deep rather than spray
5 ideation   -> read writeups and old CVE patterns, look for new variants
6 chain      -> combine small issues only where the chain is real
7 validate   -> use the gate skills below, do not skip to report
8 report     -> one report per root cause, submission-grade evidence
9 remember   -> record lessons, what worked, what was a false positive
```

## Validation gate

Do not report a finding unless all of these are present:

- Raw request and response, verbatim, not a summary.
- A control test against default or official behaviour. If the result
  matches by-design behaviour, retract the finding.
- Clear impact and severity, argued from the reproduction, not from
  the class name alone.
- Reproduction from a clean session, with the smallest privilege set.
  For authorisation issues, prove with two accounts.
- For a rejected hypothesis, use the gate-rule skill: default to
  INCONCLUSIVE when evidence is insufficient, and record the
  steelman scenario and the root cause of any failed reproduction.

Use these companion skills for validation:

- `gate_pipeline_end_to_end` for gates at every stage, and for
  carrying any recon or threat-model gap forward as an explicit
  risk note.
- `gate_rule_validasi_hipotesis` for CONFIRMED, FALSIFIED, or
  INCONCLUSIVE verdicts, the 7-gate checklist, and Observed
  evidence.

## Report structure

Title: one line, class + asset + impact.
Severity: CVSS 3.1 vector and score, each metric justified.
Summary: 2-3 sentences, root cause named.
Steps: numbered, copy-pasteable, with two accounts where
authorisation is involved.
Evidence: request and response pairs, timestamps, and any
callback log.
Impact: what an attacker concretely gets.
Remediation: the fix at the layer that is wrong.
Notes: what was tested, what was not tested, and any
limitation on how a key, token, or identifier could be
obtained by another party.

## What this skill does not do

- It does not authorise testing a target without a policy or scope.
- It does not approve a submission, a purchase, a payment, or a
  destructive action on its own.
- It does not turn a lab finding into a live claim. A lab result
  must be re-proven on the live in-scope asset before it is
  reported as live.