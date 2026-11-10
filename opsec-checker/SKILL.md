---
name: opsec-checker
author: Fauzi Susanto
description: "Operational Security Validator: VPN, DNS leaks, virtualization, browser fingerprint, hostname."
category: security
version: 1.0.0
metadata:
  hermes:
    tags: [opsec-checker]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# OPSEC Checker

## Triggers
- opsec check, operational security, VPN check, DNS leak, fingerprint
- pre-engagement opsec, red-team opsec, security validation

## Phases
- `pre-engagement` — validate infrastructure before starting
- `during-engagement` — continuous monitoring
- `post-engagement` — cleanup verification

## Checks

### Infrastructure
| Check | Method | Pass Criteria |
|-------|--------|---------------|
| VPN Active | `ip addr show` for tun0/wg0/utun/ppp0 | Interface exists |
| DNS Leak | `/etc/resolv.conf` content | No public ISP DNS |
| Virtualization | `systemd-detect-virt` | VM/container detected |
| Browser Fingerprint | Firefox/Chrome profile check | Config present |
| Hostname | `hostname` output | Not default/generic |

### Identity
| Check | Pass Criteria |
|-------|---------------|
| Separate attacker identity | Not personal accounts |
| Tor/proxy chain | Multiple hops verified |
| Timezone consistency | Matches target region |
| Language/locale | Consistent with assumed identity |

### Artifacts
| Check | Pass Criteria |
|-------|---------------|
| Tool signatures | No default user-agent strings |
| Compiled artifacts | Stripped, no debug symbols |
| Memory artifacts | Encrypted at rest |
| Log files | Rotated, not on disk |

## Quick Usage
```python
from opsec_checker import OpsecChecker, OPSECPhase

checker = OpsecChecker(phase=OPSECPhase.PRE)
results = checker.validate_infra()
print(results)
# {'vpn_active': True, 'dns_leak': False, 'virtualized': True, ...}
```

## Scoring
- **90-100**: Excellent — ready for engagement
- **70-89**: Good — minor gaps, acceptable
- **50-69**: Moderate — address before proceeding
- **0-49**: Poor — significant OPSEC risks, must fix

## Pitfalls
- VPN check is heuristic (interface name match) — may miss custom VPNs
- DNS leak check reads resolv.conf only — doesn't do live DNS test
- Browser fingerprint check is basic (config file presence, not actual fingerprint)
- Windows hosts: many Linux checks won't work — use platform-adaptive logic
- `systemd-detect-virt` not available on all systems