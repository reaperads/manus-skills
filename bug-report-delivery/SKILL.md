---
name: bug-report-delivery
author: Fauzi Susanto
description: "PDF bug report: use skill format, deliver to chat."
metadata:
  hermes:
    tags: [bug-bounty, reporting, delivery]
    budget_kb: 30
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

## ⛔ KONTRAK INTEGRASI (WAJIB DIBACA SEBELUM PAKAI SKILL INI)

Isi skill ini **dipecah**: core ada di file ini (auto-load), sisanya di `references/_split/`.
File di `references/` **TIDAK ikut ter-load otomatis** — hanya ter-LIST saat skill dibuka.
**Karena itu: buka file di tabel bawah ini lewat `skill_view(name=..., file_path=...)`
sebelum mengerjakan bagian yang relevan. Jangan menebak dari judulnya.**

Aturan pakai:
- Bagian CORE di bawah = aturan wajib, selalu berlaku, jangan dilewati.
- Bagian yang dipisah = kedalaman per-topik. **Panggil saat pemicunya muncul, jangan dibiarkan tak terpakai.**
- Kalau ragu bagian mana yang relevan, baca `references/_split/_INDEX.md` dulu (satu file, murah).

### Tabel pemicu → file (WAJIB dipanggil saat kondisi terpenuhi)

| kapan dipanggil | file |
|---|---|
| saat mengerjakan: **Email-draft delivery (vendor correspondence by email) — NEVER SE** | `references/_split/01-email-draft-delivery-vendor-correspondence-by-email-never-.md` |
| saat mengerjakan: **Workflow** | `references/_split/02-workflow.md` |
| saat mengerjakan: **PDF Generation — reportlab Patterns** | `references/_split/03-pdf-generation-reportlab-patterns.md` |
| saat mengerjakan: **Evidence Authenticity — CRITICAL LESSON (Chime 2026-09)** | `references/_split/04-evidence-authenticity-critical-lesson-chime-2026-09.md` |
| saat mengerjakan: **File Locking Pitfall (Windows)** | `references/_split/05-file-locking-pitfall-windows.md` |
| saat mengerjakan: **Complete Report Structure (Standard Sections)** | `references/_split/06-complete-report-structure-standard-sections.md` |
| saat mengerjakan: **⚠️ `execute_code` Pitfall — DO NOT Generate PDFs Inline** | `references/_split/07-execute_code-pitfall-do-not-generate-pdfs-inline.md` |
| saat mengerjakan: **📂 Related Files** | `references/_split/08-related-files.md` |
| saat mengerjakan: **🏆 GOLD STANDARD REPORT — Zinc/Zootbox Case Study (PATUHI, DITIRU** | `references/_split/09-gold-standard-report-zinczootbox-case-study-patuhi-ditiru.md` |
| butuh daftar lengkap split / arsip | `references/_split/_INDEX.md`, `references/_split/_full-archive.md` |


# ⛔ PRE-LOAD CHECK (MANDATORY — DO NOT SKIP)

Before loading this skill, ALL of these MUST be verified:

```
[ ] $BB_DATA/_progress/<target>/PHASE_LOG.md exists
[ ] PHASE_LOG.md shows Phase 0C COMPLETE (all vectors tested)
[ ] $BB_DATA/_progress/<target>/findings.json exists
[ ] findings.json has ≥1 candidate entry OR explicit "vectors tested, no bounty-worthy findings"
[ ] Phase 0F is the ONLY remaining phase
```

**VERIFICATION METHOD (not optional):**
```bash
# MUST run this — do not assume
cat $BB_DATA/_progress/<target>/PHASE_LOG.md
# Verify: Phase 0A=COMPLETE, Phase 0B=COMPLETE, Phase 0C=COMPLETE
# Verify: Phase 0F=PENDING
```

**If ANY item unchecked or Phase 0C ≠ COMPLETE:**
- REFUSE to load report generation
- Print: "⛔ PRE-LOAD CHECK FAILED: Phase 0C incomplete. Return to testing."
- Return user to Phase 0C with: "Testing must complete before report. See PHASE_LOG.md for gaps."
- DO NOT generate ANY report content until this passes.

**Exception — ad-hoc target with NO pipeline workspace.** If there is no `$BB_DATA/_progress/<target>/`
directory at all (the target was worked directly, outside the 0A-0F pipeline), the PHASE_LOG gate has
nothing to check and must NOT be used to refuse — the operator can legitimately ask for a report on a
target that was never run through the pipeline. In that case: (a) do the VRT/viability/program-exclusion
reasoning by hand (Phase 1 + 2), (b) label every finding with its honest severity (an info-disclosure =
Low/Informational, likely excluded — say so), and (c) when the operator explicitly asks for low/info
reports, produce them as clearly-labelled *documentation*, never inflated — **one PDF + one staged draft
email per finding** (see "Self-hosted VDPs" below for the mechanics). Re-confirm no workspace with
`ls $BB_DATA/_progress/` before treating a target as ad-hoc. A clean negative ("no exploitable finding
on this surface") remains a valid deliverable and needs no PDF at all.

**After PRE-LOAD PASS:**
- EVICT Phase 0C skills from context (summarize to digest)
- Load this skill (30KB)
- Proceed with report generation

> This hard gate prevents report-before-done. A report generated before all vectors
> are tested is worse than no report — it wastes the bounty opportunity.

> **⚠️ COMPACTION RECOVERY:** If context was compressed and you're unsure where you are,
> read PHASE_LOG.md FIRST. It is the single source of truth for audit progress.
> Resume from the last COMPLETE phase. Do NOT restart from scratch.

---

# Bug Report Delivery — MANDATORY HARD RULE



## Trigger
User requests: PDF bug report, exploit results PDF, security finding report, laporan temuan, laporan PDF.
**Applies globally** — dari mana aja (Telegram DM, Telegram topic, WhatsApp), kapan aja. Hard rule ini berlaku untuk SEMUA permintaan user, bukan hanya topik tertentu.



## Hard Rules (WAJIB — no exceptions)

**0a. ONE FINDING = ONE DRAFT = ONE PDF (operator hard rule, restated 2026-10).** Every finding gets
its **own separate draft email** with its **own complete PDF PoC attached**. Never bundle two or more
findings into a single email, and never send a finding as bare text with no PDF. If a target yields
N findings, you produce N drafts and N PDFs. Filename the PDF after the finding so it is unambiguous
which draft carries which PoC. (This is separate from, and additional to, the validate-≥3× rule:
validate first, then one self-contained draft+PDF per finding.)

**0b. IMPACT MUST BE DEMONSTRATED — the four-part reportability test (operator, 2026-10-10).**
*"draft gmail yg lengkap poc pdf nya, dgn hasil yg benar2 ada impactnya, ada demonstrated impact
dalam poc nya ... bukan berhenti di teoritis, krn wajib dibuktikan."* A finding is reportable only
when **all four** hold; fail any one and it is EXCLUDED with its reason written down:

| # | requirement | why |
|---|---|---|
| 1 | present in `passed-findings.json` | it cleared the impact gate **and** the 7-question triage gate |
| 2 | carries a **demonstrated-impact record** — `probe` (the exact action) **and** `observed` (raw, unedited output, ≥40 chars) | a claim without its raw result is theory |
| 3 | that record **re-verified CONFIRMED 3x** (`reverify.py`) | a finding that does not reproduce is not a finding |
| 4 | an impact statement saying what the observed output **proves** | `"impact: potential"` is not an impact |

Enforced by `scripts/final-deliverable.py` (ships with this skill — see that file's own
docstring for the exact `passed-findings.json` schema it expects):

```bash
python scripts/final-deliverable.py check <target_dir>          # reportability only, writes nothing
python scripts/final-deliverable.py build <target_dir> --to <vendor> --from <me>
```

It emits, per reportable finding: `poc-pdfs/<slug>.pdf` (reportlab, the structure in rule 1 below,
with a **PROOF OF CONCEPT — DEMONSTRATED IMPACT** section carrying probe + raw observed output +
"what this proves", a **Verification** block with the 3x verdict and its artefact, and a supporting-
material table) and `email-drafts/<slug>.eml` — RFC5322 with that PDF attached. `.eml` on purpose: no
OAuth token needed, inspectable byte-for-byte, importable into Gmail. **Staging is never sending.**

**When nothing qualifies it produces NOTHING — that refusal is the feature.** Manufacturing a draft
for a finding with no demonstrated impact is the phantom-evidence failure that gets reports closed
without investigation, and it is the same failure class as writing up a gate-dropped finding. Report
the negative result instead (see the negative-report guidance in `audit-execution-discipline`).

Wired into the pipeline's 0F on **both** branches (positive after `report-agent.py`, negative after
the no-findings path), so it fires automatically the moment a real finding clears the gates.

**0c. THE DRAFT BODY HAS A FIXED SHAPE — the default body baked into `scripts/stage_finding_draft.py` is
a PLACEHOLDER and MUST be replaced (operator correction, 2026-10-12).** Verbatim: *"kamu perkenalan, terus
jelaskan temuannya, tutup dgn sopan, tanpa tanya reward, kasih nama saya … jgn lupa pdf pocnya yg lengkap
dan rapi, pakai skill humanizer"*. Shipping the stub ("Hi, / Findings attached. Full technical detail…")
is a rejected deliverable even when the PDF is perfect and every verification passed. Pass `--body <file>`
with, in this order:

1. greeting, who you are, and the channel — "My name is <operator's real name>. I am an independent
   security researcher, and I am sending this report through your responsible disclosure programme at
   <policy URL>.";
2. what you found, with the exact command and the exact value it returned;
3. one sentence stating that nothing was changed and the report is not shared with anyone else;
4. a polite close offering the raw evidence / a walkthrough / to retest a fix, then the operator's
   **real name and contact address** as the signature.

Banned in the body: any reward / bounty / credit / Hall-of-Fame request, "I hope this helps", emoji, and a
handle or bare "researcher" where the operator's real name belongs (this operator: **Fauzi Susanto**,
fzsusanto@gmail.com). Run every body through the `humanizer` skill and assert it mechanically before
staging — `[t for t in ["\u2014","\u2013","delve","pivotal","leverage","seamless"] if t in body] == []`.
The PDF that rides with it must be complete and tidy: markdown → PDF → `qa_pdf_layout.py --margin-mm <m>`
must report `clean` for *every* finding (wrap long curl lines in the markdown first — an overflowing code
line is the usual offender), then re-stage the affected drafts.

**The stub is now STRUCTURALLY unreachable, not just discouraged.** `scripts/stage_finding_draft.py` takes
`--body` as a **required** argument and its loader refuses to stage a body that (a) lacks the intro /
channel / signature markers, or (b) contains a reward word (`bounty`, `reward`, `credit`, `hall of fame`,
`swag`) or an AI-ism (`delve`, `pivotal`, `leverage`, `seamless`, em/en dash). The old generic fallback
body was deleted. Skeleton to copy per finding: **`templates/disclosure-email-body.md`** — it carries the
rules, the fill-in slots, and a shipped worked example.

Lesson worth keeping: when the operator corrects an *output shape*, fix the **generator's default**, not
just the prose rule. A rule the agent can forget will be forgotten; a required argument it cannot omit
will not be. Rule 0c existed before this session and the stub still shipped — that is what "patch the
root cause" means in practice.

0. **GATE BEFORE FORMAT (pre-step — do not skip):** Before a single word of the report is written,
   run the findings through the toolkit gate and chain builder:
   ```bash
   python $TOOLKIT/shared/finding_gate.py findings.json --report REPORT-survivors.md
   python $TOOLKIT/shared/chain_builder.py findings.json --goal <impact>
   ```
   - Only findings that **survived the gate** may enter the PDF. A dropped finding is informational —
     writing it up anyway is severity inflation and it will be rejected.
   - **The gate is a keyword heuristic, not an oracle — review its verdict, never obey it blindly.**
     `finding_gate.py` scores a finding with regexes over its text, so it is wrong in BOTH directions
     (verified by reading the source, 2026-10):
     - **False POSITIVE**: `IMPACT_PATTERNS` includes `\b(pii|email|phone|address|kyc|...)\b` weighted 6.
       Two crypto findings whose text merely quoted a **contract address** scored "pii-exposure 6" and
       sailed through as REPORT, with no privacy impact at all.
     - **False NEGATIVE**: `fund-loss` (weight 10) only fires on
       `\b(funds?|balance|withdraw|transfer|mint|steal|drain)\b.{0,30}\b(unauthor\w*|arbitrar\w*|without)\b`.
       A proven on-chain reward-accounting bug — half of a funded emission window never credited to
       stakers, the matching TIMBS locked in the contract, PoC 3/3 PASS — scored 0 and was DOWNGRADED
       with "no concrete impact signal (data/funds/authz) found", because the prose said "loss of
       rewards to LPs" instead of "funds ... without authorisation".
     So: when the gate and your evidence disagree, the **evidence wins** — but state the gate's verdict
     and your disagreement explicitly in the write-up and to the operator. Never reword a finding to
     farm a keyword (that is gaming the filter), and never let a 0 score delete a PoC that passes.
   - If the gate drops everything, the correct deliverable is the one-line statement
     *"no reportable finding on this surface"* + the gate output as evidence — **not** a padded PDF.
   - Every finding in the PDF needs its PoC evidence to match the gate's recorded proof
     (screenshots / raw HTTP / tx hash). No evidence → no section.

1. **FORMAT:** Always use skill reporting format (references/reporting.md from bug-bounty skill). Structure: Title → Summary → Severity/CVSS → Steps to Reproduce → Proof of Concept → Impact → Remediation → Supporting Material.

2. **SAVE LOCALLY:** Save PDF to working directory (e.g., `/c/Users/WINDOWS10/arlo-bounty/` or project dir). Always use clear, descriptive filenames.

3. **DELIVER TO CHAT:** After generating the PDF, MUST deliver it to the SAME chat/topic where the request was made using `MEDIA:<absolute_path>` format. This means:
   - If user asks in Telegram topic X → send MEDIA: to topic X
   - If user asks in WhatsApp → send MEDIA: to WhatsApp
   - The file must be sendable/clickable, not just text output

4. **SCREENSHOTS/POC:** Reports must include evidence — screenshots (browser capture) or terminal output as POC. If browser blocked by WAF, use curl terminal output as evidence.

5. **EVIDENCE FILES:** Also create and send evidence text files (curl logs) alongside the PDF.



## Deliverable integrity — identity, version hygiene, cross-artifact agreement

### Identity / contact block: never leak another platform's alias

Operator correction, 2026-10: *"kok ad tulisan bugcrowdninja? ini an self host"*.

- A **platform-specific alias** (e.g. `mrfz@bugcrowdninja.com`, which exists for Bugcrowd) must NOT
  appear in a report for a **self-hosted / vendor-direct** program. It signals the wrong taxonomy and
  makes the triager question where the report is coming from.
- Default to the operator's **own established convention for that program**. Their prior reports are
  the reference: if those carry name + role and no address, match that. Do not add an email just
  because a template has a contact field.
- **Check every artifact, not just the body.** That one string is also pushed into the PDF canvas
  header/footer on *every* page, so a single constant fixes — or breaks — all of them. Grep the built
  PDF for `@` and for the platform name before delivering.
- If a reply address is genuinely needed, ask which address to use **for that program**. Bugcrowd
  alias, personal mail, and program-specific mail are not interchangeable.

### Version hygiene: if the operator has NOT submitted yet, ship ONE clean version

Operator correction, 2026-10: *"jgn ad koreksi segla macam, samakan dgn video, sy blm submit,
jd msh aman"*. Two situations, two different artefacts:

| Situation | What to produce |
|---|---|
| Already submitted / the vendor holds the old one | Explicit **correction framing is correct** — state what changed and why so the triager can re-verify |
| **Nothing submitted yet** | A single clean document stating the corrected facts as plain truth. **No** "correction", "corrected", "previous version", "previous submission", "erratum", "originally", "was changed", "no longer" — not in the subtitle, not as a section, not in metadata |

Mechanics for the clean case:

1. **Rewrite, don't annotate.** Delete the wrong value entirely instead of adding prose that explains it.
2. **Grep the built PDF for the forbidden words** plus the superseded value itself. Any hit means the
   rewrite is incomplete.
3. **Drop version suffixes** from the filename once it is the only version — `-v2` in a filename is a
   tell that a v1 is still sitting somewhere.
4. **Move superseded PDF/MP4 into `superseded/`** the moment a replacement exists. Side by side, the
   operator ships the wrong file.
5. **PDF and video share one basename** — they are a single deliverable.

### Cross-artifact agreement: every claim must appear in both

Any statement in the written report must be something the video also shows, and vice versa. A video
demonstrating a different URL / chain / parameter than the PDF describes is **worse than no video** —
it invites the triager to distrust both. Before delivering, walk the report's numbered steps and tick
off the segment that proves each one. If a step cannot be shown live, cut the claim or list it
explicitly under "Not claimed" (the Proven/Not-claimed table pattern in the gold-standard structure).

When the video reveals the report's steps are wrong, the operator usually needs **three** things, not
one — ask which they want, and default to all three:

1. the **regenerated clean PDF** (see version hygiene above),
2. the **video**, and
3. a **corrected-steps summary** — a plain-text, copy-pasteable block containing the corrected
   reproduction steps, the control tests, the artifacts to revoke, and a one-line note of what
   changed. The operator pastes it into the submission form / a triager reply; it is not a PDF.

Deliver (3) as a `.txt` in the same folder so it can be pasted without reformatting. Say plainly in
the reply which URLs/values changed and why — the operator may have **not** submitted yet, in which
case the summary silently fixes their draft before it goes out.

For the video side of this — routes, assembly, ffmpeg/Playwright pitfalls, vision-free verification,
and the live-target safety rails — see `references/video-poc-production.md`.

### ⛔ Every staged draft needs an explicit unique `Message-ID` — the REST path replaces drafts too

Hit live 2026-10-13 (Arrakis engagement, 2 findings). Finding F1 was staged through the Gmail **REST**
API (`users().drafts().create()`), read back, verified — attachment hash matched, `To:` correct.
Finding F2 was staged minutes later by the same code. F1 was **gone**: `drafts().list()` returned
exactly one draft. No error on either `create()`.

The `Message-ID` warning elsewhere in the library is written up as an IMAP `append` problem. **It is
not IMAP-specific.** `EmailMessage()` does not add a `Message-ID`, and Gmail treats an appended message
without one as a *revision of the previously appended draft*. `scripts/stage_finding_draft.py` had the
same hole and now sets it itself:

```python
from email.utils import make_msgid, formatdate
msg["Message-ID"] = make_msgid(domain="report.local")   # unique per draft — REQUIRED on REST too
msg["Date"] = formatdate(localtime=True)
```

Two corollaries, both of which cost time in that session:

- **Stage N drafts, THEN assert N live subjects in one pass.** The natural "stage one → verify one"
  loop passes for every draft and still misses the loss, because the victim is only destroyed when the
  *next* draft lands. Count by subject across the whole batch after staging, never per-draft alone.
- **`Message-ID: NONE` in the `format="metadata"` read-back is NOT a missing header.** After the fix
  the metadata view still showed `MSGID: NONE` — Gmail normalises an API-created draft. The
  authoritative proof is one draft per subject plus `sha256(attachment) == sha256(local pdf)` read back
  through `messages().attachments().get()`. Do not re-stage a draft that is already correct.
- **`drafts.list()` can return ZERO drafts while the draft demonstrably exists — never trust it as the
  existence check** (hit live 2026-10-13, Oh Dear). Stager reported `DRAFT r1856229749558253171
  VERIFIED`, but both `drafts.list()` and `drafts.list(q='subject:"…"')` returned `0`, which reads like
  the staging was lost. `drafts.get(id=…)` returned the full raw message and the attachment sha matched,
  so the draft was fine — only the listing index was empty. The reliable batch assertion is
  `messages().list(labelIds=['DRAFT'])`, then decode each `raw` and count by subject. In that run it
  showed 23 total drafts, exactly 1 for the finding. Rule unchanged: stage N, then assert N in ONE pass
  over `labelIds=['DRAFT']` — but run the assertion on messages, not on drafts.list.

Full transcript and the second trap in the same helper (the rule-0c body validator rejecting the word
`bounty`): `reportlab-security-pdf` → `references/gmail-message-id-rest-path.md`.

### Re-running the stager must not resurrect a draft the operator already sent

The staging script is re-run once per new finding, so it must be safe to run repeatedly against
a mailbox where earlier findings have already shipped. Operator caught this 2026-10-08: after they
said *"f3 sudah sy kirim"*, a re-run **created a second draft** for that same finding.

- **A tracked draft id returning 404 does NOT mean "lose the draft and remake it".** In Gmail a
  draft disappears from `drafts/` precisely because it was **sent**. Recreating it silently leaves
  a duplicate of content the vendor already has — and the operator may ship it twice.
- So: on 404, **recreate but mark it loudly** (`recreated_after_missing: true`, printed as a
  distinct `RECREATED: tracked draft was missing (already sent?)` line in the run output), rather
  than treating it as a routine create.
- **Add a duplicate sweep after staging** — list every matching draft and count by attachment
  filename; any filename appearing more than once is flagged. This is the safety net that catches
  the case the per-finding known-id check cannot see.

```python
by = defaultdict(list)
for c in api(".../drafts?q=" + quote('"<subject-stem>"')):
    m = message_from_bytes(b64urlsafe_b64decode(raw(draft_id)["message"]["raw"]))
    for p in m.walk():
        if p.get_filename():
            by[p.get_filename()].append(c["id"])
for fn, ids in sorted(by.items()):
    print(f"{fn:<46} {len(ids)}x {ids}" + ("  <-- DUPLICATE" if len(ids) > 1 else ""))
```

- **Do not delete the redundant draft to clean up.** The operator owns the mailbox and may have
  already acted on it. Flag it and let them decide — deleting without asking is the kind of
  irreversible action that needs a confirmation, and a stale duplicate is cheap next to a
  wrongly-deleted draft.

Note the distinction from the version-hygiene rule above: that one is about the *artefact* being
superseded and moving files to `superseded/`. This one is about the *transport* — a draft that is
gone from `drafts/` is gone because it shipped, not because it needs rebuilding.



## Resuming a paused engagement (recover state BEFORE writing anything)

When the user says *"continue the X audit"* / *"lanjutkan audit yang tertunda"* on a target that
already has a workspace, do not start from the workspace alone. The workspace shows what was
**tested**; the mailbox shows what was **committed to and answered**. Recover both, in this order:

1. **Inventory the workspace.** `<BB_DATA>/_progress/<target>*/` — reports, session logs, logs/,
   scripts, creds. Read the session log and the newest report first; they carry the honest
   "outcome" and any cleanup/state residue.
2. **Rebuild the correspondence state from the mailbox** (read-only, `[Gmail]/Semua Email`,
   `TEXT "<vendor-domain>"`). Dump the bodies of the ~5 newest in the thread and answer, explicitly:
   was the report actually SENT (is there a sent copy)? did the vendor reply, and to what? which
   items did they already accept/fix? is a finder's fee or reward pending/paid? is there an open
   promise you made ("I'll do another pass")? That last one is usually THE pending task, and it is
   invisible in the workspace.
3. **Re-verify the findings LIVE before writing.** Note the build fingerprint in the old report and
   check whether it still holds — vendors redeploy between sessions (chunk hashes, server-action ids,
   and the arithmetic of public tools can all change). Re-running the read-only probe is cheap and it
   is what makes "confirmed still live on <date>" honest. Public/unauthenticated surface is the
   cheapest to re-verify and the most likely to have been missed by the account-based sweep.
4. **Then** generate the deliverable and exactly one in-thread draft (see above), threading on the
   captured Message-ID chain so it lands inside the existing conversation rather than as a new one.

Capture the Message-IDs you will thread on in step 2 and reuse them in step 4 — do not re-search for
them at send time.



## Headless-Chrome screenshot of a live endpoint (use BEFORE Pillow when a real capture is possible)

For a genuine visual of an HTTP response (metrics page, JSON body, error page) you do not need a
browser tab or a base64 round-trip through the conversation — write the PNG straight to disk:

```bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --no-sandbox \
  --hide-scrollbars --user-data-dir="D:/.../hl-shot" --user-agent="$UA" \
  --window-size=1280,1000 --screenshot="D:/.../evidence/metrics_screenshot.png" "https://host/metrics"
```

Then **verify it before embedding** — a blank or error-page screenshot inside a PDF is the fastest
way to lose triager trust. Two checks, neither of which needs a vision model:

```bash
# ink check: unique==1 or min==max ⇒ blank ⇒ throw it away
python3 -c "from PIL import Image;px=list(Image.open('metrics_screenshot.png').convert('L').getdata());print('unique',len(set(px)),'min',min(px),'max',max(px))"
# content check: prints the rendered DOM (for text/plain Chrome wraps it in <pre>)
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --dump-dom --user-data-dir="D:/.../hl2" "$URL" | head -c 400
```

Embed with `--dump-dom` output quoted in the PDF caption as the machine-readable counterpart, so the
artifact proves both what the endpoint emitted and how it rendered. Note `--headless=new` still
returns the real page for a WAF-free endpoint; if the shot comes back as a challenge/error page, say
so rather than shipping it.



## Pillow POC Screenshot Generation (Fallback when browser fails)

Browser Swagger UI/console tools sometimes fail (console returns null, clicks don't work, WAF blocks). Use Python Pillow to generate professional terminal-style POC screenshots.

### ⚠️ TARGET-SPECIFIC CONSTANTS (CRITICAL — not optional)
**`scripts/gen_poc_screenshots.py` contains hardcoded constants from a PREVIOUS target (Aurory).** Before generating screenshots for ANY new target, you MUST:
1. Open the script and find the constants section at the top
2. Replace ALL values: OWNERSHIP_ID, ACCOUNT_ID, PLAYER_ID, BASE_AUTH, BASE_URL, endpoints, etc.
3. New constants must match the values used in the PDF text exactly (single-source-of-truth)
4. If you skip this step, screenshots will show WRONG evidence (wrong IDs, wrong endpoints) while PDF text shows correct values — triagers WILL notice

**Pitfall (Chime session 2026-09-03):** Generated 4 PDFs with Chime-specific data but used Aurory screenshots. User caught it: "sudah dipastikan bahwa pdfnya dbuat brdasarkan skill report bugcrowd y? yg semuanya sinkron antara pdf, ss, dan poc nya?" — had to regenerate everything.

**Style:** Dark background (#1e1e1e), green (#00ff41) for success/request text, red (#ff4444) for vulnerability highlights, monospace font, step headers, watermark footer with "Reporter @ Bugcrowd | Timestamp".

**Reusable script pattern:**
```python
from PIL import Image, ImageDraw, ImageFont
import textwrap, os

W, BG, FG, RED, TITLE = 1200, '#1e1e1e', '#00ff41', '#ff4444', '#00bcd4'

def make_screenshot(lines, output_path, title="POC Evidence"):
    """Generate a terminal-style POC screenshot."""
    font = ImageFont.truetype("consola.ttf", 16)
    h = 40 + len(lines) * 24 + 60
    img = Image.new('RGB', (W, h), BG)
    draw = ImageDraw.Draw(img)
    y = 20
    # Title
    draw.text((20, y), title, fill=TITLE, font=font); y += 36
    for line, color in lines:
        draw.text((20, y), line[:110], fill=color, font=font); y += 24
    # Watermark
    draw.text((20, h-35), f"POC Evidence | MrFz @ Bugcrowd | {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", fill='#666666', font=font)
    img.save(output_path)
```

**Files to generate per finding:**
- `01-swagger-ui-overview.png` — API docs showing endpoint
- `02-endpoint-no-auth.png` — Swagger showing no lock icon
- `03-step1-[action].png` — First request + response
- `04-step2-[vuln].png` — Vulnerability trigger + response
- `05-step3-[verify].png` — Verification of exploit
- `06-step4-[impact].png` — Impact demonstration
- `07-impact-summary.png` — Attack chain + impact overview

The gen_screenshots.py from `~/aurory-report/` is a working reference implementation.



## Embedding Screenshots in PDFs (reportlab Image)

When building bug bounty PDFs with embedded POC screenshots, use reportlab's `Image` flowable:

```python
from reportlab.platypus import Image, KeepTogether
from reportlab.lib.units import inch

def screenshot_flowable(filepath, caption_text, max_width=460, max_height=340):
    """Embed a screenshot image with caption, auto-scaled to fit."""
    if not os.path.exists(filepath):
        return Paragraph(f"[Screenshot not found: {os.path.basename(filepath)}]", caption_style)
    img = Image(filepath)
    aspect = img.imageWidth / img.imageHeight
    w = max_width
    h = w / aspect
    if h > max_height:
        h = max_height
        w = h * aspect
    img.drawWidth = w
    img.drawHeight = h
    img.hAlign = 'CENTER'
    caption = Paragraph(f"<i>{caption_text}</i>", caption_style)
    return KeepTogether([img, caption])

# Usage in story:
story.append(screenshot_flowable("evidence/01-swagger-overview.png",
    "Figure 1: API Swagger UI — no auth required"))
story.append(screenshot_flowable("evidence/02-mint-jwt-vuln.png",
    "Figure 2: JWT minted WITHOUT authentication"))
```

**Key rules:**
- Always use `KeepTogether` to prevent page breaks between image and caption
- Scale to fit A4 margins (max_width ≈ page_width - margins)
- Use `img.hAlign = 'CENTER'` for consistent placement
- Save screenshots as PNG (reportlab supports PNG and JPEG natively)
- File size matters: 8 screenshots ≈ 600-700KB total PDF. Keep individual PNGs under 200KB

### ⚠️ Pillow RGBA Color Mode Pitfall (CRITICAL — hit 3x in UpScrolled 2026-09-01)

Pillow's `Image.new('RGB', ...)` creates RGB images, but certain operations (transparency, compositing, alpha channels) silently convert to RGBA mode. When reportlab tries to embed an RGBA PNG in PDF, it crashes with:
```
OSError: cannot save mode RGBA as PDF
```

**The fix — convert to RGB BEFORE saving to PNG:**
```python
# WRONG — may produce RGBA PNG that crashes reportlab
img = Image.new('RGB', (W, h), BG)
# ... draw stuff ...
img.save(output_path, 'PNG')  # Could be RGBA if any alpha operation occurred

# CORRECT — force RGB before save
img = Image.new('RGB', (W, h), BG)
# ... draw stuff ...
if img.mode == 'RGBA':
    img = img.convert('RGB')
img.save(output_path, 'PNG')
```

**Even better — guard in the screenshot function itself:**
```python
def make_screenshot(lines, output_path, title="POC Evidence"):
    img = Image.new('RGB', (W, h), BG)
    # ... draw ...
    # SAFETY: always convert before save
    img = img.convert('RGB')
    img.save(output_path, 'PNG')
```

**When embedding in reportlab PDF, also guard:**
```python
from reportlab.platypus import Image as RLImage

def safe_screenshot_flowable(filepath, caption_text, max_width=460, max_height=340):
    if not os.path.exists(filepath):
        return Paragraph(f"[Screenshot not found]", styles['CaptionStyle'])
    # Force RGB for reportlab compatibility
    pil_img = Image.open(filepath)
    if pil_img.mode != 'RGB':
        pil_img = pil_img.convert('RGB')
        pil_img.save(filepath, 'PNG')  # Overwrite with RGB version
    img = RLImage(filepath)
    # ... rest of flowable ...
```

**Root cause:** Pillow `Image.new('RGB', ...)` is RGB, but `.paste()` with transparency, `Image.alpha_composite()`, or font rendering with antialiasing can silently promote to RGBA. Always verify `.mode` before save.

### Pillow Screenshot Generation → reportlab Embedding Pipeline
Full pipeline for when browser fails:
1. Generate screenshots with Pillow (see gen_poc_screenshots.py)
2. Embed them in reportlab PDF via `Image()` flowable (above)
3. Final PDF is self-contained — no external file dependencies



## ⚠️ Re-verify every candidate LIVE before writing — drop what does not survive (edge-vs-origin trap)

A finding "found" during recon can evaporate on a second pass. Re-run the probe, capture verbatim
**dated** output, and only then write it up. The single most common way a phantom finding survives
into a PDF is attributing an **edge/CDN** response to the **origin**.

Concrete trap (2026-10, synology.com self-hosted VDP):

- `405 Not Allowed` on `TRACE /api/profile` looked like framework/route+method disclosure. On re-test
  the response carried `X-Cache: Error from cloudfront` and `X-Amz-Cf-Pop: SIN2-P9` — the **edge**
  answered, not the origin. That is standard CDN behaviour, not origin disclosure, and not a finding.
- The `404` for `DELETE /c2/api/v1/...` returned body `404 page not found` (Go-style), no framework
  signature either — so the whole "framework disclosure" candidate collapsed.
- **Rule:** before calling a 404/405 "framework / route / method disclosure", attribute the response
  to a layer. Inspect `Server`, `X-Cache`, `X-Amz-Cf-Pop`, `CF-Ray`, `Via`, `X-Powered-By`. If an
  edge produced it, it is not origin behaviour — drop it.

Apply the same discipline to every candidate: a header / CSP / hostname / storage-state observation
that cannot be reproduced on a fresh run is NOT a finding. Drop it, and name it in the report's
**"Negative Tests / What I Explicitly Excluded"** section with the reason — an honest exclusion list
is stronger than a padded report, and it pre-empts the triager's "did you check X?".

**A public repo / OSS snapshot is a hypothesis generator, not the deployed code. One live probe per claim, before the draft.** The clone you review is usually months-to-years behind the build in production, and the deployed build is where the validations live. Verified on pay.blink.sv (2026-10-12): the public Galoy snapshot's `POST /api/lnurl-proxy` had **no session check** and interpolated an attacker-supplied `callback` URL with **no origin validation**, relaying the upstream body back to the caller — a textbook unauthenticated read-SSRF on paper. Live, the same route produced three *different* error messages that expose a hardening the repo does not contain: a public JSON `lnurl` really was fetched (`Not a properly configured lnurl withdraw tag`), `http://169.254.169.254/…`, `http://127.0.0.1:3000/…` and `http://10.0.0.1/` were rejected in <1.1 s (`Invalid lnurl` — blocked at validation, not at fetch), and any callback whose host differed from the lnurl host got `Invalid callback URL`, including the userinfo bypass `https://paste.rs@httpbin.org/json`. Shipping the repo-derived chain would have been a phantom finding.

The mechanic to reuse: when source says "no validation", **read the server's own error strings as the deployed policy** — send the valid case, a private-IP case, and an off-origin case, and keep the matrix (status + body + latency per case) as the evidence. A fast uniform rejection = validator; a slow/partial one = real fetch. The candidate then goes into the exclusion list with its matrix, and the report gets stronger for it.

When only **one** low/informational candidate survives, ship exactly that one. Do not inflate the
count to satisfy "one draft per finding" — say which candidates you dropped and why. If the survivor
is informational-grade, flag it once to the operator (the skill's own gate says informational →
SKIP, and submitting noise damages reputation) and let them choose; then stage the single draft and
PDF regardless.



## POC Consistency Rule (HARD RULE)

When generating **multiple deliverables** (e.g., PDF report + screenshots + BUGCROWD_SUBMISSION.md + submission form text), the PoC content **MUST be identical** across ALL of them.

**User explicitly caught this twice:**
1. "POC yg ad di submission.md dgn yg ad d pdf kok beda?" — PDF POC differed from submission guide
2. Screenshots showed DIFFERENT account_id, player_id, endpoint hosts, and request bodies than the text narrative — making the report look fabricated/reconstructed

**How to enforce — SINGLE-SOURCE-OF-TRUTH pattern:**
1. Define ALL PoC data as Python constants at the TOP of the generation script:
   ```python
   OWNERSHIP_ID = "fad6fac2-..."
   ACCOUNT_ID = "s-00001337"
   PLAYER_ID = "p-maJF0Dg9QRijpfb"
   SECRET = "poc_test_secret_12345"
   BASE_AUTH = "https://auth-public-api.live.aurory.io"
   ```
2. The SAME constants drive: PDF text, PDF code blocks, screenshot text, AND submission.md
3. After generation, MANUALLY VERIFY these values match across ALL outputs:
   - account_id in PDF text == account_id in screenshots
   - endpoint host in PDF text == endpoint host in screenshots
   - request body in PDF text == request body in screenshots
   - account_id/player_id in submission.md == PDF == screenshots
4. Never hardcode different values in different generators

**CVSS Pitfalls (user caught these):**
- **UI:R vs UI:N**: If IDOR enumeration works WITHOUT victim interaction (attacker just guesses/brute-forces ownership_id), score it UI:N, not UI:R. UI:R is only when victim must click a link or perform an action.
- **Scope:Changed**: Don't use generic justifications ("impacts client account security boundary"). Scope Changed requires that exploitation in one component affects security authority of a DIFFERENT component outside its control. If you can't prove this, use Scope:Unchanged.
- **expires_at edge case**: If your PoC ownership record has expires_at BEFORE the report submission date, it looks sloppy. Always set expiry well into the future.



## Why This Rule Exists
User was frustrated that:
- Reports were text-only, not clickable files
- Reports were sent as text output, not actual file attachments
- Reports lacked screenshots/POC evidence
- Files were saved but user didn't know where to find them
- Reports used wrong format (not skill-based)

---