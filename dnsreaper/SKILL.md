---
name: dnsreaper
description: "Subdomain takeover scanner — 50+ signatures, 50 subs/sec, supports AWS/Azure/Cloudflare/GoDaddy/DigitalOcean/GCP. Use during recon phase for subdomain takeover checks."
version: 1.0.0
author: Punk Security (adapted for Hermes)
license: MIT
metadata:
  hermes:
    budget_kb: 6
    tags: [security, recon, subdomain, takeover, dns]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# dnsReaper — Subdomain Takeover Scanner

## When to Use

Load during Phase 0B (Recon) of any BB audit, specifically for subdomain takeover detection. Works with 50+ takeover signatures across all major cloud providers.

## Location

`D:\data hermes\dnsReaper\`

## Usage

### Single domain scan
```bash
cd "D:\data hermes\dnsReaper"
python main.py single --domain target.com
```

### File-based scan (list of domains)
```bash
python main.py file --filename domains.txt
```

### Docker (full features including Google Cloud)
```bash
docker run -it --rm -v "$(pwd):/etc/dnsreaper" punksecurity/dnsreaper file --filename /etc/dnsreaper/domains.txt
```

### Output formats
```bash
python main.py single --domain target.com --out stdout --out-format json
python main.py single --domain target.com --out results --out-format csv
```

### Cloud provider scans (need credentials)
```bash
# AWS
python main.py aws --aws-access-key-id KEY --aws-access-key-secret SECRET
# Cloudflare
python main.py cloudflare --cloudflare-api-token TOKEN
# Azure
python main.py azure --azure-subscription-id ID
```

## Integration with Audit Workflow

Add to `security-recon` Phase 0B:
1. After subdomain enumeration (subfinder/crt.sh)
2. Pipe discovered subdomains to dnsReaper
3. Check for takeover-able CNAME records
4. Report as findings if takeover is possible

## Known Issue — FIXED

Google Cloud provider was broken on Python 3.14 (missing `pkg_resources`).
**Fix applied:** upgraded `google-cloud-dns` from 0.34.1 → 0.37.1 (uses `importlib.metadata`).
All providers now work including GCP.

## Signatures

50+ takeover signatures covering:
- AWS S3/CloudFront/EB/Lambda
- Azure Blob/CDN/VM/Functions
- GitHub Pages/Shopify/Heroku
- Fastly/Netlify/Cloudflare Pages
- Many more...