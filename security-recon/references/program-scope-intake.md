# Program scope + exclusion intake (Step 0)

Read the target's own published rules **before** touching a scanner. The scope + exclusion list
decides reward vs $0 and defines authorised footing. Getting this first turns "fire everything" into
"spend effort where it pays".

## The three lists to extract
1. **In-scope assets** — exact hostnames / wildcards; write down the *explicit excludes* too.
2. **Reward tiers** — which asset class pays most, so you prioritise correctly.
3. **Exclusions / non-qualifying** — the highest-signal list. It names every finding triage will
   close as informational / $0 regardless of PoC quality.

## Recurring exclusion patterns (kill scanner volume on sight)
Vendor programs re-use the same non-qualifying list almost verbatim:
- vulnerability-scanning reports that don't describe the impact
- missing security headers / cookie flags
- banner grabbing / software version disclosure
- open redirect alone (informational unless chained into something bigger)
- reflected XSS / self XSS
- user enumeration (unless you demonstrate the absence of rate limits)
- most brute-force, DoS, phishing / fake-site / fraud
- issues requiring a MITM position or user network control
- local privilege escalation that isn't chained to a network vuln
- theoretical findings without a standalone PoC (raw screenshots / Burp replays alone are rejected)
- root cause in upstream open-source / third-party, not vendor code
- findings from QEMU / emulator environments

**Implication:** volume scanners mostly produce reports that get auto-closed on these programs.
Lead with manual, impact-first work on the highest-tier asset.

## Worked example — Synology (recorded 2026-10)
- `https://www.synology.com/.well-known/security.txt` → `Policy: https://www.synology.com/security/bounty_program`
- Three tiers:
  - **OS** (DSM 7 / SRM 1.3 / Camera fw / BeeStation OS): up to **$30k** — but tested on *your own*
    device/VM, not their infra. This is where most DSM CVE research actually happens.
  - **Software & C2 cloud** (`*.account.synology.com`, `*.identity.synology.com`,
    `*.c2.synology.com`): up to **$10k**.
  - **Web services** (`*.synology.com`, excluding `openstack-ci-logs`, `router`, `ask`): up to **$5k**.
- Exclusions matched the generic list above, plus: directory traversal on `*archive.synology.com`,
  reflected file download, version disclosure, and 0-days disclosed within 90 days.
- **Takeaway:** "audit synology.com" literally = the $5k web tier. The $30k lives in self-hosted
  DSM research.

Non-intrusive auth-surface notes gathered with single public requests only (OIDC discovery):
`identity.synology.com` is the OIDC provider (Hydra-style:
`/.well-known/openid-configuration` + `/.well-known/jwks.json`); the chain is
`account → identity/oauth2/auth → signin.synology.com?login_challenge=…`; `c2` and `account` both
expose `/api/c2`; community/event apps are Laravel (`eyJpdi…` session cookies). These are leads, not
findings — surface mapping only.
