---
name: disclosure-contact-discovery
version: 1.0.0
author: Hermes Curator
license: MIT
description: "Use when finding/verifying a disclosure contact email."
metadata:
  hermes:
    tags: [osint, disclosure, bug-bounty, contact-discovery, recon, email]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Disclosure Contact Discovery & Verification

Find the correct contact for a vulnerability disclosure — **and prove the mailbox is real and
belongs to the target** before sending. An address that looks right but is dead (or belongs to a
different company) silently voids the report, and worse lets you *claim* you disclosed when you
did not.

Everything here is public-source. No email is ever sent during discovery.

## When to use

- "find the security email / contact for <target>"
- "where do I submit this bug for <target>"
- a target has a repo/`SECURITY.md` but no obvious security mailbox
- before sending any disclosure email (verify, don't guess)

## Core order of preference (most official first)

1. **Registered program** — HackerOne / Bugcrowd / Immunefi / HackenProof. Check even if you
   found the bug outside it. Expect gates (see §5).
2. **Dedicated security channel** on the target's own site — `/.well-known/security.txt`
   (RFC 9116), `/security`, `SECURITY.md`, imprint/legal page.
3. **Verified general mailbox** — `info@` / `abuse@` from their legal docs. **Prove it answers**
   (§1) and that the domain is really the target (§2).
4. **Maintainer / owner direct** — commit authors, package maintainers, verified social.
5. **Coordinator** — CERT/CC, national CERT, disclose.io.

## The four verifications (proven — DeXe Protocol case, 2026-10-11)

### 1. Probe the mailbox with SMTP `RCPT TO` (never sends)

`RCPT TO` only asks "does this mailbox exist?". Cheap, rerunnable.

```python
import smtplib, socket
socket.setdefaulttimeout(8)
host = "aspmx.l.google.com"        # from: nslookup -type=MX <domain>
for c in ["security", "abuse", "info", "support", "contact", "admin",
          "psirt", "disclosure", "report", "vulnerability", "research"]:
    try:
        s = smtplib.SMTP(host, 25, timeout=8); s.ehlo("m.t")
        s.mail("test@example.com")
        code, msg = s.rcpt(f"{c}@<domain>")
        print(f"[{code}] {c}@<domain>", msg.decode(errors="replace")[:50]); s.quit()
    except Exception as e:
        print(f"[ERR] {c}@<domain>", type(e).__name__, str(e)[:40])
```

- **`250 … OK`** → exists. Use it.
- **`550 5.1.1 … does not exist`** → dead. Do not send.
- **`[ERR] TimeoutError`** → refused/rate-limited. **Do not conclude dead** — try another MX host
  or fall back to a form/policy page.

Pitfalls:
- Keep to ~6 names per call, socket timeout 6-8 s — one hanging MX blows the `terminal` 180 s timeout.
- **There is often no `security@` at all.** On DeXe, `security@`/`psirt@`/`disclosure@`/`report@`/
  `vulnerability@`/`research@`/`support@`/`contact@`/`legal@` were ALL **550**; only `info@`,
  `abuse@`, `admin@` answered 250. Never assume the canonical `security@` exists.

### 2. The near-miss domain trap (HARD pitfall)

A similar-looking domain is **not** the target. A researcher reported a DeXe Protocol vuln to
**`info@dexe.com`** and told the team he'd emailed them. `dexe.com` is a **Chinese shampoo
manufacturer** (MX `mxbiz2.qq.com`, Tencent QQ — not Google Workspace). The report vanished.

- **Who is behind the domain:** `curl -sL https://<domain> | grep -io "<title>[^<]*"`.
  `dexe.com` → shampoo; `dexe.network` → DeXe Protocol.
- **Match the MX/provider.** A real crypto target is usually Google Workspace
  (`aspmx.l.google.com`) or comparable; odd MX (Tencent/QQ, parker) = wrong domain.
- Mirrors that get confused: `dexe.network` vs `dexe.io` vs `dexe.com` vs `deex.exchange`
  (old DeeX exchange — a **different** entity, now dead). **`deex` ≠ `dexe`.**

### 3. The authoritative address often lives only in a legal PDF

The site may expose zero addresses (no `mailto:`, `/contact` → 404). The official, legally
binding contact is in the legal documents:

- `https://documents.<domain>/Privacy_Policy.pdf`, `Terms_of_Use.pdf`, imprint pages.
  DeXe's Privacy Policy named the entity + responsible email verbatim:
  *"DeXe Protocol Association … Baarerstrasse 141, 6300, Zug … Email: `info@dexe.network`"*,
  corroborated byte-for-byte by the Terms of Use PDF.
- Extract emails from a compressed-text PDF (regex gate + `zlib.decompress` on stream objects).
  **Write the script to a file** — a heredoc with inline `\(`, `\)`, `[` trips
  `re.PatternError: unterminated character set` under this shell/host combo.
- **Check the entity's legal status** on a company register (Swiss: `moneyhouse.ch`, `help.ch`,
  `local.ch`; otherwise country of incorporation). DeXe Protocol Association was listed
  **"in Liquidation"** (2024-2025) while the protocol kept running — so legal email is not the
  only route.

### 4. Mine the target's GitHub issues for channels + gates

A project with a `SECURITY.md` but a silent team often has a pile of *"Security: Responsible
Disclosure Request"* issues with **no reply**. Read them:

```bash
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<org>/<repo>/issues/<n>"
curl -s -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/<org>/<repo>/issues/<n>/comments"
```

Yields other researchers' emails + PoCs + channels tried (including near-miss domains), and the
**platform gate** they hit. If requests pile up unanswered → you need several parallel channels.

### 5. Expect submission gates on the paid platforms

From the DeXe case: **Immunefi required a Whitehat Level**, **HackenProof required 120
reputation points + KYC + a $5 submission fee**. This is *why* researchers fall back to email /
GitHub. Plan for the gate; if you can't clear it, say so and use the verified email instead of
claiming a platform submission you didn't make.

## Reporting the result

State **which mailbox you verified (250) and which returned 550**, and that the domain was
confirmed to belong to the target. A later reviewer must be able to see the contact was proven,
not guessed.

## Related skills

The end-to-end disclosure workflow (triage → PoC → report → coordination), email templates, and
PGP/Gmail-draft mechanics live in the user-owned `bug-bounty-disclosure` skill — read it for the
write-up side. This skill owns the **contact discovery + verification** step specifically.