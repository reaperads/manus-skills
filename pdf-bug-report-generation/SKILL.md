---
name: pdf-bug-report-generation
description: Use when building bug-bounty PDF reports with reportlab.
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# PDF Bug Report Generation (reportlab + Pillow)

Engineering mechanics for producing professional, readable bug-bounty PDF reports. Complements the reporting-flow skill (bug-report-delivery: format/flow/gates, user-owned) — this skill is the technical HOW and the quality bar.

## Quality bar (user-confirmed — treat as non-negotiable)

1. **No watermark** on screenshots or PDFs.
2. **No overlapping / clipped text** in POC screenshots — long lines must wrap, line height generous.
3. **Headings must stay with their content** — a heading stranded at a page bottom ("Negative Tests" on one page, its table on the next) is a defect. Wrap heading + first body flowable in `KeepTogether`.
4. **"Mepet" is unacceptable.** Generous typography: body 11pt/leading 17, code 9pt/13.5, headings 13pt, `spaceAfter` on paragraphs, `Spacer(1,10-14)` between sections, images capped ~400x240. A 6-page report beats a cramped 4-page one.
5. **Researcher alias**: user prefers `Mr Fz` in the meta table.
6. **Bugcrowd program metadata required** (RACV explicitly asks): date/time/timezone found + IP address used. Get public IP via `https://api.ipify.org` + `http://ip-api.com/json/?fields=query,country,city,timezone`.
7. **Validate ≥3× BEFORE writing anything up.** Operator rule, stated 2026-10: *"pastikan sudah
   divalidasi minimal 3x"*. A finding is not reportable until it has been reproduced at least three
   independent times — ideally from a fresh session/context (new cookie jar, new target id, or a
   different client such as curl-vs-browser) so you are testing the server, not your cached state.
   Two of the same request fired back-to-back is ONE validation, not two. Record the three runs in the
   findings file (evidence path per run) so the claim is auditable. Findings that evaporate on run 2
   or 3 are exactly the ones this rule exists to kill — e.g. a "raw tag present" grep banner that was
   really a shell exit-status artefact.
8. **Do not advance to the next task until the artefact set is COMPLETE.** Operator correction,
   2026-10: *"draft gmail tidak ada pdf poc-nya, harusnya kamu lengkapi semua baru lanjut"* — a draft
   that carries only the submission text is not done. The definition of done for one finding is:
   (a) PDF PoC built, (b) PDF **attached** to the Gmail draft, (c) draft fetched back and the
   attachment asserted by filename + size + content-type, (d) paths + credentials of any test account
   recorded in the engagement log. Only then move on. Half-finished artefacts are worse than none,
   because the operator has to come back and ask — and they will notice.

### A code block that ENDS with a quote kills the generator (the fourth member of the quote family)

Writing `C('''…  last line ends with an apostrophe''')` produces four consecutive quotes and Python dies
with `SyntaxError: unterminated string literal (detected at line N)`. Hit live 2026-10-12 on a control
line ending `…query parameter: account'`. The nested-quote traps below are about quotes *inside* the
block; this one is about the block's **last character**. Fix: never end a code block with `'` or `"` —
drop the trailing quote or rephrase the final line.

### The layout gate needs a NATIVE path on Windows — a `~/…` expansion looks like a missing script

```bash
PY="C:/Users/<u>/AppData/Local/Programs/Python/Python314/python.exe"
QA="C:/Users/<u>/AppData/Local/hermes/skills/security/pdf-bug-report-generation/scripts/qa_pdf_layout.py"
"$PY" "$QA" out.pdf --margin-mm 14.8
```

Invoking it as `"$PY" "$(echo ~/AppData/…/qa_pdf_layout.py)"` under `MSYS_NO_PATHCONV=1` hands Windows
Python `D:\c\Users\…` and it fails with `can't open file` — which reads like the gate is missing instead
of mis-invoked.

### A WRAPPED multi-line H1 is reported as `OVERLAP` — fix the style, not the content

With `fontSize=18, leading=23` a two-line title makes the gate report
`p1: OVERLAP 'Open builder registration allo' <-> 'registered for an app URL the '`. It is not a real
overlap — adjacent wrapped lines at ~1.28x leading intersect in bbox terms. Fix it in the style module:
`fontSize=16, leading=24` (1.5x) and keep titles to <=2 lines by moving the descriptive clause into the
Summary paragraph. Both affected PDFs went `clean` on the next build. The template shipped with this
skill already uses 16/24.

## reportlab pitfalls (verified live)

### `&` → `&...;` artifact (CRITICAL — kills reproduction)
reportlab `Paragraph` treats `&` as an HTML entity. A code block with `?a=1&b=2` renders as `&...;` entity text (`&startDate;`, `&lastname;`) — invalid curl, immediately flagged by reviewer as "URL artifact". 
**Fix:** escape ALL text fed to `Paragraph` — including code blocks:
```python
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
```
Use `esc()` for table text, body paragraphs, code paragraphs, captions. Keep raw `&` in plain-Python strings used only for non-Paragraph output (e.g. writing submission .md). Verify with pypdf: regex `&[a-zA-Z]+;` across extracted text must be empty.

### Named HTML entities are NOT supported (the mirror-image trap)

reportlab's `Paragraph` understands only `&amp; &lt; &gt;` plus **numeric** entities (`&#8212;`).
It does **not** know the named ones. So a named entity in text you deliberately pass as raw HTML
(bold/italic prose, i.e. the paragraphs you do NOT run through `esc()`) renders as literal
characters: `&mdash;` prints the string `&mdash;`, `&rarr;` prints `&rarr;`, and so do
`&nbsp;`, `&pound;`, `&ndash;`.

This is the opposite failure to the `&` trap above, and it lands in exactly the same place: the
customer-facing document. Hit live in a vendor report (2026-10) — 8 `&mdash;` and 5 `&rarr;`
leaked into an otherwise clean PDF, and the author only caught it because the same
`&[a-zA-Z]+;` assertion was already in the verification loop.

**Fix:** use the real Unicode character, never the entity. `\u2014` em dash, `\u2013` en dash,
`\u2192` arrow, `\u00a3` pound, `\u00a0` nbsp. These render identically, work in raw-HTML
paragraphs *and* survive `esc()`, so you never have to remember which path a string takes.

```python
# WRONG — literal "&mdash;" in the PDF (raw-HTML paragraph)
P("The engine is right <b>here</b> &mdash; the public tool is not.")
# RIGHT
P("The engine is right <b>here</b> \u2014 the public tool is not.")
```

If a generator already uses named entities, a one-line sweep before build is safe:
`s = s.replace("&mdash;", "\u2014").replace("&ndash;", "\u2013").replace("&rarr;", "\u2192")`
— confirm the counts it replaced match what you expected, then re-run the assertion.

### Multi-line H1 title trips the layout gate as a FALSE `OVERLAP` (hit live 2026-10)

`qa_pdf_layout.py` reports `OVERLAP '<title line 1>' <-> '<title line 2>'` when an H1 wraps. The lines do not
actually collide — the checker's bbox intersection fires because the leading is tight relative to the font box
(18pt font / 23pt leading). Both reports in one session were flagged this way while rendering correctly.

Two fixes, either is fine, neither is a "cosmetic" skip:
- loosen the heading style — `fontSize=16, leading=24` (ratio ~1.5) cleared both PDFs in one edit;
- and/or keep the H1 short and move the long descriptive clause into the Summary paragraph.

Do not accept it and ship: re-run the gate until it prints `layout: clean (no stranded headings, no margin
overflow, no overlap)`. A gate you have decided to ignore is worse than no gate, because the next real defect
hides behind the false positive.

### Authoring the generator from `execute_code`: a `\"` inside a double-quoted cell string ENDS the cell (2 cycles, 2026-10)

The `'''`-for-code-blocks rule protects the *generated* file. A separate collision fires one level up, in the cell
that writes the generator: any `"...\"...\"..."` inside a **double-quoted** cell string terminates that string, so
the cell dies with a misleading `SyntaxError: '[' was never closed` pointing at the opening of a multi-line list.

```python
# in the cell — BROKEN (the \\" ends the string, so the list never closes)
bl(["appUrl is not unique ... the published client says \\"No admin approval, no captcha\\"."])
# in the cell — RIGHT: single-quoted cell string, the " is then literal
bl(['... the published client says "No admin approval, no captcha".'])
```

Rules that made it work:
- **single-quote every cell string whose content contains `"`** (helper emitters already escape `"` on the way out,
  so the generated file stays correct);
- multi-line `helper([...])` calls are the worst place for this — one bad element kills the whole cell;
- if a helper list is long, emit one `w(...)`/`bl([...])` line per item rather than one giant literal.

### Gmail draft attachments: verify through `attachmentId`, not `body.data` (hit live 2026-10)

`users.drafts.get(format=full)` returns an attached PDF as
`{"mimeType":"application/pdf","filename":"<finding>.pdf","body":{"size":N,"attachmentId":"ANGjd..."}}` —
**there is no inline `data` on that part**. A naive walk that only counts parts carrying `body.data` therefore
reports "attachment missing" on a draft that is perfectly fine, and the obvious conclusion ("re-append") is wrong.

Correct verification (the only assertion that counts):
1. walk `message.payload.parts` for `mimeType == "application/pdf"`, read `filename` + `body.size`;
2. `GET users.messages/{messageId}/attachments/{attachmentId}` → base64url `data` → decode;
3. compare `sha256(decoded)` to the local PDF file — byte-identity, per report.

Also: the metadata view can show `Message-ID: None` on API-created drafts (Gmail normalises headers). That is not
evidence of a problem — confirm instead that the draft **count per subject is exactly one** and that each
attachment hash matches. Two reports staged this way each kept a distinct draft id.

### Heading stranding (KeepTogether)
```python
def keep(heading, *flows):
    return KeepTogether([Paragraph(heading, H2)] + list(flows))
```
Use for every section: `keep("Negative Tests", neg_table([...]))`. Long sections (steps loop, evidence images) keep their own heading + first content together; insert `PageBreak()` before the evidence screenshot block so figures never split awkwardly.

### Other known reportlab traps (relevant when building)
- `SimpleDocTemplate(pagesize=A4)` — pass the tuple; `pagesize=A4[0]` crashes.
- Style names `Code`, `Bullet`, `Title` are taken — use `CodeSafe`, `BulletItem`, etc.
- **Use `'''` (single-quote) triple strings for code blocks that contain `"`.** Embedding a curl/JSON
  block via `C("""...""")` when the block itself contains double quotes (e.g. `-d '{"type":"simple"}'`,
  or `(WP "critical error" page)`) is a Python **syntax** error — `SyntaxError: '(' was never closed`,
  and reportlab is never reached. The parser error points at the *opening* `C(` line, so the real
  culprit is far below it. Write every code block as `C(''' ... ''')`; then inner `"` is always safe
  and the `esc()` inside `C()` still handles `&`/`<`/`>`.
- **Name the file/report after the finding, not the session.** Per-finding PDFs (`F1_<slug>`,
  `F2_<slug>`) are the deliverable shape for this user; a single combined PDF is wrong unless the
  findings are one chain attack.

- **ONE finding = ONE report = ONE PDF + ONE draft email.** This user states it explicitly ("1 temuan
  1 laporan, gabung hanya kalau itu chain attack"). The rule is about the *draft email* as much as the
  PDF — do not bundle two unrelated findings into a single disclosure email, even when they were found
  in the same hour and share a contact. A chain attack (finding A is the only path to finding B) is the
  single permitted merge.

- **Same root cause across multiple hosts is ONE finding, not several.** If the identical defect exists
  on two hosts (e.g. the same unescaped error page on `pipe.orf.at` and `bolek.orf.at`), that is one
  report whose *breadth* line says "two hosts, the same application deployed twice". Two unrelated
  findings (e.g. a reflected XSS **and** an untrusted-header cookie issue) are two reports even though
  both were found on the same engagement and both go to the same `security@` address.

- **Re-staging an updated report = delete the superseded draft, then append.** Never leave two versions
  of the same report in the mailbox (see the Message-ID section below). After staging N reports, assert
  exactly one draft per finding subject before telling the user it is done.
- Close nested tags inner-first: `</b></font>`, never `</font></b>` (reportlab XML parser).
- Convert Pillow images to RGB before embedding (`if img.mode != 'RGB': img.convert('RGB')`) — RGBA PNG crashes reportlab.
- Windows file lock: build to temp path then `os.replace`; or save `-v2.pdf`.
- Generate PDF scripts via `write_file` + run with the reportlab-having Python (`C:/Users/WINDOWS10/AppData/Local/Programs/Python/Python314/python.exe`), NOT execute_code (escape-sequence landmines with long XML/curl strings).
- **Nested triple-quotes inside the generator: use `'''`, not `"""`, for code blocks.** Generators
  wrap code as `C("""…""")`. If that block itself contains a double quote (e.g.
  `curl -H "Content-Type: text/xml"`), Python tokenises the string wrong and the file dies with
  `SyntaxError: '(' was never closed` **reported at the opening `C(` line** — a line that looks
  perfectly valid, so you debug the wrong place (cost a cycle 2026-10). Use a triple-SINGLE-quoted
  string for any block containing `"`: `C('''…''')`. Lint the `.py` immediately after `write_file`;
  the syntax error surfaces there, before any build or run.

### Nested triple-quote in the generator → use `'''` for every code block (verified live 2026-10)

A generator that passes code blocks as `C("""...""")` breaks the moment the block contains a `"`
(JSON payloads, `-w "%{http_code}"`, a document title like `"critical error"`). Python
mis-tokenises the string and the file fails to compile with a **misleading** error:

```
SyntaxError: '(' was never closed (line 377, column 15)
```

The reported line is the *outermost* unclosed `C(` — hundreds of lines away from the real cause,
so reading the flagged line tells you nothing.

**Fix:** use single-quoted triple strings for every code block.

```python
# WRONG - dies as soon as the block contains a double quote
C("""curl -s -o /dev/null -w "%{http_code}" https://x/wp-json/ctxfeed/v8/dashboard/$ep""")

# RIGHT - ''' for code blocks, """ for prose that contains apostrophes
C('''curl -s -o /dev/null -w "%{http_code}" https://x/wp-json/ctxfeed/v8/dashboard/$ep''')
```

Rule of thumb: code blocks are `'''`, prose is `"""`. A `'''` block is only unsafe if the payload
itself contains three consecutive quotes (essentially never). After a rewrite, ALWAYS run
`python -c "import ast;ast.parse(open('gen.py').read())"` (or rely on the linter) before building —
the syntax error otherwise surfaces only at build time.

### …and if you AUTHORED that generator through `execute_code`, the trap fires one level up

`execute_code` hands your code in as a string, so a generator written the obvious way collides:

```python
# inside execute_code — BROKEN
src = '''#!/usr/bin/env python3
story.append(C('''Tax paid late: 5000'''))     # <-- the inner ''' closes the outer literal
'''
# SyntaxError: invalid syntax   (reported at the generator's own C( line)
```

The tell is identical to the build-time trap — a syntax error pointing at a line that looks fine —
but it fires while *writing* the file, so `ast.parse` never gets a chance to catch it.

Fix: stop hand-typing triple quotes. Build the generator as a **list of lines** with the quote run
held in a constant, and emit code blocks through a helper:

```python
TQ = "'''"                      # one place, so no literal ever collides with the wrapper
L = []
def w(s=""): L.append(s)
def cb(block):                  # a multi-line code block inside A(C(...))
    L.append("A(C(" + TQ + block + TQ + "))")

w("import re, pathlib")
w("from reportlab.platypus import Paragraph, Spacer, Table, KeepTogether")
w('A(P("Quarterwise - product review", H1))')
cb("Tax paid late (GBP)      : 5000\nDays the payment is late : 40")
...
pathlib.Path("gen.py").write_text("\n".join(L), encoding="utf-8")

import ast; ast.parse("\n".join(L))      # lint BEFORE the build, in the same cell
```

Rules that made it work:
- Append in slices (`part1` scaffolding, then `part2`/`part3` content) with
  `.open("a").write(...)` — a long generator survives an interrupted cell, and each slice is small
  enough to re-read.
- `ast.parse` the assembled source **in the same cell** that writes it; the syntax error then costs
  one cell, not a build cycle.
- Build f-strings as ordinary `"..."` lines with `%`-formatting for the data rows
  (`'["%s","%s","%s"],' % row`) — you cannot nest an f-string inside a string that is itself being
  assembled, and table rows are where generators get long.
- Keep prose (with apostrophes) and code blocks (with `"`) on different emit paths; never mix them in
  one literal.

### Nesting level 2 — authoring the generator FROM another script (the outer-`'''` collision)

The `'''`-for-code-blocks rule above fixes the generator's *own* parsing. The mirror problem appears
when you **emit the generator source from inside a second script** (a Python one-shot that writes
`gen_report.py`). The writer's literal then collides with the generator's content:

```python
# WRITER (fails to even parse — SyntaxError on the line that OPENS the generator string)
gen = '''
...
A(C('''curl -s -o /dev/null -w "%{http_code}" https://x/$ep'''))
...
'''
```

The reported error points at the outer `gen = '''` line, so it reads like an unrelated syntax problem.
Two fixes, both verified:

1. **Emit line-by-line.** Build the generator as a list of lines and write it once — with a constant
   for the triple quote used inside code blocks:

   ```python
   TQ = "'''"
   L = []
   def w(s=""): L.append(s)
   def cb(block): L.append("A(C(" + TQ + block + TQ + "))")     # block may contain any quotes
   w("A(P('Body text', BODY))")
   cb('curl -s -H "Content-Type: application/json" https://x/api')
   pathlib.Path("gen_report.py").write_text("\n".join(L), encoding="utf-8")
   ```

   Append long generators in **chunks** (`open("a")` after the first `write_text`) — a single very long
   writer call gets truncated and reports a bogus unmatched-quote error.
2. **Lint before building.** `ast.parse(src)` on the generated file catches the collision at write time;
   run the generator only after it passes. `python -c "import ast;ast.parse(open('gen.py').read())"`.

Rule of thumb: a generator that is *typed* uses `'''` inside `"""…"""`; a generator that is *emitted*
must be assembled as lines. Never nest the same triple-quote token at two levels.

### `qa_pdf_layout.py --margin-mm` MUST match the generator's margin (false-positive trap)

This session's generator used `MARGIN = 42.0` pt (the shared style module value) → run
`qa_pdf_layout.py out.pdf --margin-mm 14.8`. Verified clean; the header/footer canvas strings drawn at
`x0=42` / `x1=553` are the ones 18 mm wrongly flags. Always derive the value
(`margin_pt * 25.4 / 72`) from the generator before trusting an overflow report.



`qa_pdf_layout.py` defaults to **18 mm** margins. Per the skill's own quality bar you should cap
images/typography but the *frame* margin is the generator's choice — the reusable
`att_style.py`-style module uses `MARGIN = 42.0` pt ≈ **14.8 mm**. Run the gate with the matching
value or it flags every canvas header/footer line as an overflow:

```
python qa_pdf_layout.py out/report.pdf --margin-mm 14.8
# layout: clean (no stranded headings, no margin overflow, no overlap)
```

Symptoms of the mismatch: the reported "overflows" are exactly the page header
(`Cardoma.shop - Security Report`, x0=42), the page footer (`Page N of M`, x1=553), and the heading
lines (x0=48). Those are all *inside* a 42pt margin — it is the checker's bound that is wrong, not
the document. Convert with `margin_mm = MARGIN_pt * 25.4 / 72`. Do not "fix" the layout to satisfy a
mis-parameterised gate; fix the invocation.

### Authoring the generator PROGRAMMATICALLY (line-append) — flat statements, escaped text

When the generator is written by an agent (built up as a list of source lines rather than typed once),
the nested-quote trap above fires repeatedly and a second trap appears alongside it. Both cost real
cycles in one session (2026-10: three failed builds before the PDF existed).

- **Do not count closing parentheses across appended lines.** `A(KT("Heading", A(P("text", BODYS))))`
  needs the right number of `)` in the emitted source; when you emit a `KT(...)` block as several
  `L.append(...)` calls, a miscount is invisible until `ast.parse` fails — and `SyntaxError: unmatched
  ')'` points at a line whose visible text looks correct. **Emit flat statements instead**:
  `A(P("Heading", H2))` then `A(P("body", BODYS))`. The heading-stays-with-content property the
  quality bar demands is already provided by `keepWithNext=True` on the H1/H2 styles, so `KeepTogether`
  is belt-and-braces, not a requirement. Reserve `KT(...)` for the rare case where you are writing the
  generator by hand.
- **Never hand-write nested quotes in the emitted source.** Give yourself two helpers and use them for
  every line: `def para(t, st): emit('A(P("%s", %s))' % (t.replace('"','\\"'), st))` and
  `def code(b): emit("A(C('''" + b + "'''))")`. The first escapes the text so the outer `"` survives;
  the second uses triple-SINGLES for every code block, which is safe as long as the payload does not
  contain three consecutive quotes (essentially never). Writing these by hand is what produced
  `SyntaxError: unterminated string literal (detected at line N)` on a line that looked fine.
- **Lint before running, every time.** `python -c "import ast;ast.parse(open('gen.py').read())"` takes
  under a second and turns a build failure into a one-line parse error. Do it as part of writing the
  file, not after the build fails.
- Re-verify the PDF after the build with the same three assertions you already use (no `&entity;`,
  no watermark, key strings present) plus the margin-overflow scan — a generator rewrite can silently
  drop a section.

### Reusable per-engagement style module (copy, do not re-derive)

A known-good shared style module exists at
`templates/report_style_compact.py` in this skill (copy it next to the generator as `<target>_style.py`). The old pointer to `D:/data hermes/bug-bounty/_progress/fira.money_v1/submission/att_style.py` is **DEAD** — `_progress/` gets purged (confirmed 2026-10-12: a 7-report engagement found that path gone and had to rebuild the module from this skill's own rules). Never copy the style module out of a previous engagement's submission dir. Copy it to
the new engagement as `<target>_style.py` and build the per-finding generator on top of it. It already
enforces the skill's rules:

**⚠️ That `_progress/<engagement>/submission/` path is engagement data, not part of the skill — it can
be gone (workspace purge, different box).** Verified 2026-10: the fira copy had been deleted and the
path returned nothing mid-engagement, which cost a re-derive. If it is missing, do NOT hand-roll
reportlab from scratch: copy the packaged template **`templates/report_style.py`** from this skill
instead (same contract — `MARGIN = 42.0` pt, `esc()` inside `C()`/`tbl()`, `keepWithNext` headings,
two-pass build for "Page X of Y", `P/C/B/H1/H2/KT/tbl/meta_table/make_docs`). Either way, keep the
engagement constants at the top of the per-finding generator so the PDF text and the e-mail body
cannot drift.

- `esc()` applied inside `C()` and `tbl()` (fixes the bare-`&` → `&...;` artifact),
- `keepWithNext=True` on H1/H2 + a `KT()` KeepTogether helper (fixes stranded headings),
- two-pass `make_docs(out, header_left, header_right, title, subject, story)` so the footer prints
  `Page X of Y`,
- `meta_table()` / `tbl()` builders and a navy/blue palette.

Keep the engagement-specific constants (target, policy URL, researcher handle, severity, CWE) at the
top of the generator as the single source of truth so PDF text and the e-mail body cannot drift.
- **Nested-quote SyntaxError in the generator (hit live 2026-10).** Writing a code block as `C("""...""")` breaks when the block itself contains a double quote (e.g. a JSON payload, or `curl -w "%{http_code}"`). It surfaces as `SyntaxError: '(' was never closed` pointing at the `C(` line — NOT at the offending quote — so it looks like a missing paren. If a generator already has this, fix the block. Rule: write **every** multi-line code block with `'''...'''`; inner `"` is then always safe.
- **Shared style module (reuse, don't re-write).** `_progress/fira.money_v1/submission/att_style.py` is the single-source-of-truth generator base: MARGIN=42pt, `esc()` applied inside `tbl()`, `keepWithNext` headings, two-pass build for "Page X of Y", helpers `P/C/B/H1/H2/KT/tbl/meta_table/make_docs`. Copy it into a new engagement and import it; don't hand-roll styles per report. `META()` meta table + a "What I proved vs What I argue" `honesty_table()` are the default per-report furniture.

## Pillow POC screenshot design (verified — fixes "teks ketimpa")

```python
W = 1400; FONT = 14-16; TITLE = 17-19; LINE_H = 34-42   # <-- key: LINE_H must be ~2.3x font size
```
- Wrap long curl/JSON lines: break at last space > ~60 chars, indent continuation `"  "+rest`; simulate line count AFTER wrap, then compute canvas height (`pad_top + title_h + n*LINE_H + pad_bot`).
- Insert a blank spacer line after every logical block (request / response / verdict) to avoid visual cramming.
- Dark theme `#1e1e1e`, text `#d4f7dc`/`#00ff41`, verdict cyan, vuln-highlight red.
- Always `img.convert("RGB")` before save.

### Capturing a live-HTTP PoC image when the evidence is a text/JSON response

When the finding is an endpoint returning `text/plain` or JSON (metrics dump, debug/status page,
verbose error), the cleanest "screenshot" is a one-shot headless Chrome render straight to disk — but
you MUST verify it, because a blank page, an error page and a captcha page all render "successfully":

```bash
UA="Mozilla/5.0 (compatible; Bugcrowd-Research-bugcrowd; <program>)"
"/c/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --no-sandbox \
  --hide-scrollbars --user-data-dir="D:/…/browser-profiles/hl-shot" --user-agent="$UA" \
  --window-size=1280,1000 --screenshot="D:/…/evidence/metrics_screenshot.png" "<URL>"
```

Verify the content is really in the frame (do NOT rely on the vision tool — see the hallucination
warning below; in one session `vision_analyze` also reported the model had no vision support at all,
so plan for a text-based check):

```bash
# 1) textual proof of what the page body is
chrome.exe --headless=new --disable-gpu --user-data-dir="<fresh dir>" --dump-dom "<URL>" | head -c 400
#    → e.g. <pre …># HELP tripadvisor_client_sla …   (confirms the metrics text rendered)
# 2) proof the PNG is not blank
python -c "from PIL import Image;im=Image.open('metrics_screenshot.png').convert('L');p=list(im.getdata());print(im.size,len(set(p)),min(p),max(p))"
#    → e.g. (1280, 1000) 61 0 255   (61 distinct greys + full 0..255 range = real text)
```

Embed with `Image(SHOT, width=168*mm, height=131*mm)` and caption the provenance
("Figure 1: headless GET of `<url>` rendering the response body"). Ship the raw capture
(`curl -o file`, headers included) *alongside* the image — a screenshot whose provenance the analyst
cannot explain is worth less than the bytes. Keep `--user-data-dir` unique per shot; a reused dir
locked by a live Chrome silently produces the wrong (or no) image.

## Verification loop before delivery (pypdf or PyPDF2)

```python
full = "\n".join((p.extract_text() or "") for p in reader.pages)
assert not re.findall(r'&[a-zA-Z]+;', full)          # no entity artifact
assert "watermark" not in full.lower()
assert sum(len(p.images) for p in reader.pages) == expected
# heading placement: map each heading -> page; ensure no heading in last ~140 chars of a page
```

### Layout QA must be programmatic — do NOT trust the vision tool for it

`vision_analyze` on a local PNG path has been observed to **hallucinate**: one call claimed no image
was attached, the next described an unrelated academic paper ("1. Introduction… 2. Related Work") for a
page that contained neither. Never sign off a PDF's layout on a vision description.

Use PyMuPDF for the three defects that actually matter — stranded headings, margin overflow, overlap:

```python
import pymupdf  # fitz
doc = pymupdf.open(pdf_path)
LEFT, RIGHT, BOTTOM = 51.0, 544.0, 806.0          # A4 with 18mm margins
for pno, page in enumerate(doc, 1):
    lines = []
    for blk in page.get_text("dict")["blocks"]:
        if blk.get("type") != 0: continue
        for ln in blk["lines"]:
            t = "".join(s["text"] for s in ln["spans"]).strip()
            if not t: continue
            lines.append({"t": t, "bold": any("Bold" in s["font"] for s in ln["spans"]),
                          "size": max(s["size"] for s in ln["spans"]), "bbox": ln["bbox"]})
            x0, y0, x1, y1 = ln["bbox"]
            assert x0 >= LEFT - 2 and x1 <= RIGHT + 2, f"p{pno} margin overflow: {t[:60]}"
    # a bold >=12.5pt heading with nothing below it on the page == stranded
    for ln in lines:
        if ln["bold"] and ln["size"] >= 12.5 and ln["bbox"][1] > 0:
            below = [l for l in lines if l["bbox"][1] > ln["bbox"][1] + 12]
            assert below or (BOTTOM - ln["bbox"][1]) < 0, f"p{pno} stranded heading: {ln['t'][:60]}"
```

Cheap, deterministic, and it catches exactly the `KeepTogether` failures the skill's quality bar
forbids. Keep it next to the generator and re-run after every content edit.

### Named HTML entities render literally (second `&` trap)

`esc()` fixes bare `&`, but named entities like `&mdash;` / `&rarr;` / `&pound;` are **not** valid in
reportlab's mini-HTML and come out as literal `&mdash;` in the PDF text. The pypdf check above catches
it (`raw entities: ['&mdash;', '&rarr;']`). Fix by using the real characters (`\u2014`, `\u2192`) or
numeric refs (`&#8212;`) — including inside bullet helpers that run `esc()` first, where `&rarr;`
becomes `&amp;rarr;` and renders as the literal string.

### Layout QA must be deterministic — run the script, don't eyeball it

**Pass `--margin-mm` matching YOUR generator or the checker lies.** `qa_pdf_layout.py` defaults to
18mm; the shared style module (`att_style.py` / `cardoma_style.py`) uses `MARGIN = 42.0` pt ≈
**14.8mm**. With the default, *every* canvas header/footer line ("Cardoma.shop - Security Report",
"Mr Fz", "Page N of M") is reported as `overflows margins` — a wall of false positives that looks
like a broken layout and is really just a mismatched assumption. Correct invocation:
```bash
python qa_pdf_layout.py out/Report.pdf --margin-mm 14.8     # 42pt style module
# layout: clean (no stranded headings, no margin overflow, no overlap)
```
Sanity rule: if the flagged lines are all header/footer/heading text at x0≈42 and x1≈553, it is the
margin constant, not the content.

### The other false positive: a multi-line H1 title reads as an OVERLAP

Verified 2026-10 on two freshly built reports. Both came back
`p1: OVERLAP 'Open builder registration allo' <-> 'registered for an app URL the '` — i.e. the
*checker* reported the wrapped lines of the H1 title as intersecting each other. With
`fontSize=18, leading=23` (leading ≈ 1.28×) the title's line boxes touch; at ≤ 1.35× the
`get_text("dict")` bboxes can intersect by a point or two and trip the overlap rule.

Fix (either is enough, both is better):
- set the title style to `fontSize=16, leading=24` (≈1.5×) in the style module, and
- keep H1 titles to **one or two lines** — move the long descriptive clause into the Summary
  paragraph instead of letting it wrap to three lines.

Then re-run `qa_pdf_layout.py --margin-mm <MARGIN_pt*25.4/72>`; the overlap disappears and the
report is still `layout: clean`. Do not "fix" this by widening the margin or shrinking the body —
the flagged text was the title, so the title's leading is the defect.

`scripts/qa_pdf_layout.py` does the heading-placement / margin / overlap checks mechanically
(pymupdf). Run it as the last gate before delivery:

```bash
python scripts/qa_pdf_layout.py out/report.pdf --margin-mm <MARGIN_pt * 25.4 / 72>
# layout: clean (no stranded headings, no margin overflow, no overlap)
```

**⛔ `--margin-mm` MUST match the generator's margin, or every page is a false positive.**
The checker defaults to 18 mm. The shared bounty-report style module (`att_style.py`, and every
per-engagement copy of it) sets `MARGIN = 42.0` **points** = `42 * 25.4 / 72` ≈ **14.8 mm**. Run at
the default and it reports `overflows margins x0=42.0 x1=553.3` on the canvas-drawn header/footer and
on every `KeepTogether` heading — which reads exactly like a real layout defect and burns a "fix"
cycle on output that is already correct. Derive the value from the module constant
(`--margin-mm 14.8` for MARGIN=42) before trusting ANY reported overflow. Confirmed live 2026-10:
three per-finding PDFs each reported ~6 "overflows" at the default; all vanished at `--margin-mm 14.8`.

**Margin mismatch = false positives (hit live 2026-10).** The checker defaults to `--margin-mm 18`, but the shared `att_style.py` uses `MARGIN = 42pt` = **~14.8mm**, and its canvas header/footer strings are drawn from x=42 to x=553.3. Run it as `--margin-mm 14.8` for that style module, otherwise *every* header/footer line is reported as a margin overflow and a clean PDF looks broken. The `LEFT, RIGHT, BOTTOM = 51.0, 544.0, 806.0` constants quoted in the earlier snippet carry the same 18mm assumption — align them to the generator's real margin before trusting any failure.

**`--margin-mm` MUST match your generator's margin — the default is a false-positive factory.**
`qa_pdf_layout.py` defaults to `--margin-mm 18` (= 51 pt). If your generator uses the shared style
module (`MARGIN = 42.0` pt ≈ 14.8 mm), 18 mm is *wider* than your real margin, so every header/footer
canvas string and every left-edge heading is flagged "overflows margins" — a wall of false positives
that buries any genuine defect. Hit live 2026-10: 20+ bogus `overflows margins` lines across three
perfectly clean PDFs, all caused by the margin mismatch. Pass the real value:

```bash
python scripts/qa_pdf_layout.py out/report.pdf --margin-mm 14.8   # for MARGIN = 42 pt
# margin_mm = margin_pt * 25.4 / 72
```

Baseline the checker against ONE known-good PDF before trusting either a "clean" or an "ISSUES"
verdict.

**Reuse a shared style module instead of re-rolling reportlab plumbing.** Copy the prior submission's
`att_style.py` next to your generator and import `{B, C, H1, H2, KT, tbl, meta_table, make_docs}` — it
already enforces `esc()` inside every table cell, `keepWithNext` on headings, and a two-pass build for
"Page X of Y". Changing only its `MARGIN` constant makes the QA margin above the single thing you must
re-check. (Fira `submission/att_style.py` is a working copy: ~206 lines, palette + builders + doc.)

**Sweep named entities BEFORE the build, not after.** `esc()` fixes bare `&`, but `&mdash;` / `&ndash;`
handed to a *raw-markup* paragraph render literally in the PDF. Do a pre-build replace and assert zero
remain: `s = s.replace("&mdash;", "\u2014").replace("&ndash;", "\u2013")` then
`assert not re.findall(r'&[a-zA-Z]+;', s)`. This session did exactly that (10 entities replaced → 0
left) before the first build, so the pypdf assertion passed first try.

It flags: a bold H2-sized line with nothing after it on the page (stranded heading), a heading
within ~40pt of the page bottom, any text crossing the margins, and overlapping text spans. The
`KeepTogether` pattern above should make it pass first time — if it fires, the structure is
wrong, not the checker.

**Sanity-check any vision-based review of a rendered page.** A vision model asked to "check this
page for layout problems" can return a confident, well-formatted answer describing a *different*
document — it does not always report that it never received the image. Treat such a response as
a non-answer whenever the text it quotes does not appear in your PDF (grep the description for
one of your own headings). Fall back to the script, which cannot hallucinate. Vision is still
fine for "does this look right to a human" on a screenshot you have confirmed renders.

## Bugcrowd VRT look-up (scripts/lookup_vrt.py)

- VRT JSON: `https://raw.githubusercontent.com/bugcrowd/vulnerability-rating-taxonomy/master/vulnerability-rating-taxonomy.json`
- Top key is **`content` (a list)** — NOT `image`. Recursion must handle both dict and list nodes.
- For entitlement/cookie-trust bugs (server trusts client-set membership cookies → member pricing/URLs): pick **`Broken Access Control > Privilege Escalation`** (no baseline priority → argue P3). Do NOT pick IDOR children unless the bug references other users' objects:
  - `Modify Sensitive Information (Iterable Object Identifiers)` P2
  - `Modify/View Sensitive Information (Iterable Object Identifiers)` P1
  - `View Sensitive Information (Iterable Object Identifiers)` P3
  - `Modify/View Sensitive Information (Complex Object Identifiers GUID/UUID)` P4
- Re-check the PROGRAM page exclusions before mapping (e.g. RACV excludes rate limiting — frame such findings as captcha/control gaps, not rate-limit findings).

## Severity honesty (keeps validity ratio)

Always include a **"What I proved" vs "What I argue (not proven)"** table in severity justification. If PII/real-monetary impact wasn't demonstrated (only fabricated data), say so and price accordingly (P4 not P2). Note "fabricated data only" in the disclosure statement. This gives the appeal foundation if triagers downgrade.

## Single source of truth

Define ALL constants once (BASE, endpoints, query strings, cookies, response snippets, researcher, IP, timestamp) at the top of the generator; the SAME values must appear in PDF text, screenshots, and submission guide. Verify after generation that an endpoint/ID/URL in the PDF == screenshot == guide.

## Delivery: the submission e-mail draft (Gmail via IMAP)

The PDF is only half the deliverable — the operator's workflow is **PDF + a ready e-mail draft**. Rules
(these are operator preferences, treat as non-negotiable):

0. **The body is WRITTEN PER FINDING. Never ship the stager's default text.**
   `stage_finding_draft.py` is happy to run with no `--body`, and what it then writes is a generic
   "Hi, Findings attached…" note. That is a rejected deliverable. Operator, 2026-10-12, verbatim:
   *"kan kamu udh biasa buat draft, kok jadi ngaco, kamu perkenalan, terus jelaskan temuannya, tutup
   dgn sopan, tanpa tanya reward, kasih nama saya, kok gini aja harus diajarin terus."* Write a
   `body_<F>.txt` per finding and pass it with `--body`. Fixed shape, in this order:

   1. **Perkenalan** — `Hello <Vendor> team,` then who is writing (**full name**), "I am an
      independent security researcher", and the channel. If a program exists, name it and link it.
      If none does, say so and name where you got the address — *"I could not find a bug bounty
      programme or a security.txt for <domain>, so I am sending this to the address published on your
      legal pages. If there is a better place for it, please point me there and I will resend."*
   2. **The finding, explained** — what you saw, the paste-ready request, the observed response, in
      plain language, before any numbered section. One finding per body.
   3. **Honesty block** — what you did NOT do: "I only used GET requests", "I did not modify
      anything", "I did not create an account", "I have not shared this with anyone else",
      "reproduced N times, byte identical". This is not padding; it is what makes the report credible.
   4. **Suggested fix** — one short paragraph.
   5. **Polite close + signature** — "Thank you for your time." / "Best regards," / **the operator's
      full name** (Fauzi Susanto) / contact address.

   HARD: **never ask for a reward, bounty, or payment, and never mention bounty eligibility.** The
   operator reads that as the amateur tell. Run the `humanizer` skill over the body, then assert
   mechanically before staging:
   `[t for t in ["\u2014","\u2013","delve","pivotal","testament","leverage","seamless","I hope this helps"] if t in body] == []`.
   The generic-body failure is invisible from the staging output — the draft verifies fine and looks
   complete. It is only caught by reading the body.

   **"PDF lengkap dan rapi" is a gate, not a preference.** Rebuild the PDF, then run
   `qa_pdf_layout.py --margin-mm <MARGIN_pt*25.4/72>` and require `layout: clean`. The usual overflow
   cause is a long `curl`/JSON line inside a fenced code block: `Preformatted` does not wrap, so the
   line leaves the frame. Break it with a shell `\` continuation, or hoist a `BASE=`/`V=` variable at
   the top of the block so every URL is short. Then re-stage — a rebuilt PDF is a CHANGED PDF, so the
   previously staged draft is stale.

1. **Draft only. Never send.** Create the message in Gmail's Drafts folder (`[Gmail]/Draf` in an Indonesian
   locale profile) and stop. The operator reviews and sends. Create a draft only when there is a genuine
   finding, and never re-create/resend the same one before the operator has verified the first.
2. **External artefacts are English**, and the body needs an **introduction before any technical content**:
   who is writing (researcher handle), their status (independent security researcher), the channel the report
   goes through (program + asset placeholder), and the context (private/coordinated disclosure, nothing sent
   to mainnet/testnet, no scanner against the live protocol). Technical sections come after that block.
   Run the body through the `humanizer` skill before staging — the operator checks for this explicitly
   ("badan emailnya sesuai humanizer"). Concretely: varied sentence length, no ALL-CAPS template feel beyond
   the few section labels, no em dashes, no "delve/pivotal/leverage/seamless", straight quotes. Keep the
   numbers exact and leave the honesty section (bounds, "what I did not test") in — a humanised body must not
   become a vaguer body. Assert it mechanically before staging:
   `[t for t in ["\u2014","\u2013","delve","pivotal","testament","leverage","seamless"] if t in body] == []`.
3. **Do not invent a recipient.** When the program is dashboard-based (Immunefi, HackenProof, Bugcrowd) or
   publishes no security mailbox, leave `To:` unset and tell the operator the channel options in chat. A
   fabricated address sends a report to an unmonitored inbox — worse than no recipient at all. Only set `To:`
   when the program's own policy names a working address (e.g. a vendor-run `security@…`).
4. **One set of constants, two outputs.** Programme URL, asset, implementation, chain, severity argued,
   researcher, timestamp, finding title — define once and feed both the PDF generator and the e-mail body, so
   they cannot drift. The e-mail is the PDF's summary, not a second independently-written document.
5. **Mirror the honesty furniture in the e-mail**, not just the PDF: severity argued (never oversold), the
   "what I proved vs what I argue" split, and the caveat list. Triagers read the e-mail first.

Mechanics that worked (verified 2026-10):

```python
# imap_tools 1.15: MailMessage.__init__ takes fetch_data, so there is no from-scratch builder.
# Build the MIME with the stdlib instead and hand `append` the raw bytes.
from email.message import EmailMessage
from imap_tools import MailBox

msg = EmailMessage()
msg["From"] = EMAIL
msg["Subject"] = SUBJECT          # no "&" — keep it plain
# msg["To"] intentionally unset (rule 3)
msg["Message-ID"] = make_msgid()  # MANDATORY — see the pitfall below
msg.set_content(BODY)             # the English body with its introduction block
with open(PDF, "rb") as fh:
    msg.add_attachment(fh.read(), maintype="application", subtype="pdf",
                       filename=os.path.basename(PDF))

with MailBox("imap.gmail.com").login(EMAIL, app_password()) as box:
    box.append(msg.as_bytes(), folder="[Gmail]/Draf", flag_set="\\Draft")
```

- **Reuse the operator's existing app-password source** rather than storing a second copy of the secret
  (read it out of the existing helper script by regex); never echo it into logs or the reply.
- **Reuse the existing stager's token resolver instead of hand-typing the token path.** The
  output-masking tripwire rewrites secret-shaped literals **inside files you write**: a hand-typed
  `TOKEN = "goo" + "gle_" + "token" + ".json"` came back out as `TOKEN = "***" + "gle_" + ...`, which
  still `ast.parse`s and then dies at runtime with a misleading `FileNotFoundError`. Do not fight the
  masker — import the already-correct helper:

  ```python
  import importlib.util
  spec = importlib.util.spec_from_file_location("sfd", STAGE_FINDING_DRAFT_PY)
  sfd  = importlib.util.module_from_spec(spec); spec.loader.exec_module(sfd)
  creds = Credentials.from_authorized_user_file(sfd.token_path())   # correct + lint-safe
  ```

  Same principle as the app-password bullet above: the working copy of the secret-resolution logic
  already lives in the stager, so call it rather than re-deriving it.
- **Do not build an emitted generator's inline formatting with `re.sub`.** Escaping a replacement such
  as `r"<font face=\"Courier\">\1</font>"` through a writer (`*_code` → file on disk) doubles the
  backslashes once per layer, so you ship `\\1` (a literal, not a back-reference) or reportlab raises
  `ValueError: Can't map determine family/bold/italic for \"courier\"`. Use a split-based formatter —
  no regex, no backslashes, no escape layers:

  ```python
  def inline(t):                       # t is ALREADY esc()'d
      parts = t.split("**")
      if len(parts) > 1:
          t = "".join(p if i % 2 == 0 else "<b>" + p + "</b>" for i, p in enumerate(parts))
      parts = t.split(chr(96))         # backtick as chr(96) so no quoting layer can eat it
      if len(parts) > 1:
          t = "".join(p if i % 2 == 0
                      else "<font face='Courier'>" + p + "</font>" for i, p in enumerate(parts))
      return t
  ```

  Order matters: `esc()` first, then `inline()` — injecting markup before escaping makes reportlab
  print the tags as text.
- The append returns `('OK', [b'[APPENDUID … (Success)']])` — **then verify by fetching the draft back** and
  asserting the attachment filename / size / content-type and that the introduction markers are present in the
  extracted `text`. A successful `append` is not proof the attachment survived.

### Re-staging after a finding ESCALATES mid-engagement (hit live 2026-10)

A second deep-dive pass turned a staged High into a bigger High (answer key → full per-answer explanations +
5.3 MB measured). The finding had already been drafted. What has to change together, in one run:

1. **The PDF** — rebuild, re-run `qa_pdf_layout.py --margin-mm <margin>`, and re-assert the new numbers are
   actually IN the text (`pymupdf` + a `s in full` check for the new figure). A rebuilt PDF that silently
   dropped the escalation is worse than the old one.
2. **The subject line** — if the headline claim changed, the subject must change with it. The old subject is
   then the duplicate-detection key, so:
3. **Delete the superseded draft, then append the new one.** Search on the OLD subject fragment; do not rely on
   the draft id you recorded earlier.
4. **Re-verify the STAGED artefact, not the local file** — attachment `sha256` must equal the *local* PDF you
   just rebuilt, one draft per subject, and the intro marker present in the fetched body.
5. **Update the findings file** so `findings.json` and the PDF cannot drift.

Do not stage a "v2" alongside the v1 and let the operator choose. One finding, one current draft.

### Patching a generator that contains multi-line `C('''...''')` blocks

`str.replace()` on the generator will bite you when the target text spans a triple-quoted code block: the
replacement string's own quotes/newlines unbalance the parens and Python dies with
`SyntaxError: unmatched ')'` — **and the build may still produce output from the un-patched file**, so you get
a "successful" rebuild of the OLD content. Two rules:

- After any generator patch, `ast.parse` it AND grep the built PDF text for a string only the new version
  contains. A build that succeeds is not a build that changed.
- For anything more than a one-line edit, rewrite the generator outright (`cat > gen.py <<'PYEOF'` with
  single-quoted triple strings for every code block) instead of string-surgery. Same rule as the skill's
  nested-quote guidance, applied to *edits* rather than first authoring.

### Staging via the Gmail REST API (no app password) — two mechanics that bite (hit live 2026-10)

When the engagement already has an OAuth token (here: `%LOCALAPPDATA%\hermes\google_token.json`, scopes
including `gmail.modify` + `gmail.send`) you can stage drafts without IMAP at all:

```python
# 1) refresh: POST https://oauth2.googleapis.com/token  (client_id, client_secret,
#             refresh_token, grant_type=refresh_token)
# 2) build the MIME exactly as in the IMAP recipe (Message-ID + Date + PDF attachment),
#    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
# 3) POST https://gmail.googleapis.com/gmail/v1/users/me/drafts  {"message": {"raw": raw}}
#    -> {"id": "r-4595695067593860620", "message": {"id": "1a12c00977bccca1"}}
```

Two traps, both silent:

1. **`DELETE users/me/drafts/{id}` returns an EMPTY body (204).** `json.load(resp)` raises
   `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` — and because that raise happens *inside*
   the delete loop, the re-stage aborts part-way. Measured: 1 of 7 superseded drafts deleted, six left
   behind, so a naive re-run stages seven more and the mailbox holds two generations of every report.
   Treat an empty response as success:
   `raw = resp.read(); return json.loads(raw) if raw else {}`.
   Print the delete result per id, then re-assert one draft per finding before claiming done.
2. **Match the vendor's required subject format when the policy specifies one.** A repo `SECURITY.md` can
   mandate `[SECURITY] <repo> — <description>` while the docs-level policy specifies nothing. Stage with
   the format of the channel you are actually sending to, and use a `[SECURITY]`-class prefix even when
   unmandated (shared inbox triage). Re-staging to change the prefix means delete-then-append — never
   leave both generations.

Verification is the same assertion as the IMAP path, expressed against the REST API: list by subject
fragment (`drafts?q=subject:"<fragment>"`), walk `payload.parts` for `mimeType == "application/pdf"`, then
`GET users/messages/{messageId}/attachments/{attachmentId}`, base64url-decode and compare `sha256` with the
local PDF. Note `Message-ID` reads back as `None` in this view — that is Gmail normalising the header, not
a missing header; the count-per-subject plus the hash match is what proves the draft is correct.

### ⛔ ALWAYS SET AN EXPLICIT UNIQUE `Message-ID` ON EVERY APPENDED DRAFT (verified live 2026-10-08)

`EmailMessage()` does **not** add a `Message-ID` by default. Gmail treats an appended message with no
`Message-ID` as a **revision of the previously appended draft**, so staging report B silently *replaces*
report A. Symptom: report A verifies fine right after staging, then vanishes from `[Gmail]/Draf` the moment
report B is appended — an IMAP `SEARCH SUBJECT "<report A fragment>"` returns 0, and a subject listing shows
only the newest ORF/vendor draft. Nothing in the append response warns you (`APPENDUID` succeeds both times).

```python
from email.utils import make_msgid, formatdate
msg["Message-ID"] = make_msgid(domain="report.local")   # unique per draft — REQUIRED
msg["Date"] = formatdate(localtime=True)
```

Verification that actually catches it — **count per subject, not "did my append succeed"**:

```python
M.select('"[Gmail]/Draf"')
for frag in ("<target-domain-A>", "<target-domain-B>"):
    typ, data = M.search(None, 'SUBJECT', '"%s"' % frag)
    print(frag, len(data[0].split()))          # must be exactly 1 per finding
```

If you already staged a `Message-ID`-less draft, delete the stale copy in the SAME run that appends the
replacement (`STORE <id> +FLAGS \Deleted` → `EXPUNGE`), then re-count.

**Corollary for multi-finding engagements:** after staging N reports, assert exactly one draft per
finding subject. When re-staging an updated report, delete the superseded draft first, then append —
otherwise the mailbox holds two versions and the operator has to pick. Evidence of the trap in the wild:
a 2-report engagement lost report A when report B was staged, and only the per-subject count exposed it.

**Bounded fetch, not `limit=500`.** `box.fetch(reverse=True, limit=500)` on a busy Drafts folder takes
minutes and can be killed mid-run. Search by subject with IMAP (`M.search`) instead — it is one round trip
and is the only thing you actually need.

### ⛔ Set an explicit unique `Message-ID` on every appended draft (report-stealing bug, hit live 2026-10)

`EmailMessage` does **not** add a `Message-ID` by default. Gmail treats an appended draft that has no
`Message-ID` as a **revision of the previously appended draft** rather than a new one — so staging
report #2 **silently deletes report #1**. Observed exactly: report A staged and verified (subject,
`to`, attachment all confirmed by refetch); minutes later report B was appended and report A was gone
from `[Gmail]/Draf` — an IMAP `SUBJECT` search for report A's subject returned 0 hits. Re-staging A
then removed B. Alternating losses, no error at any point.

```python
from email.utils import make_msgid, formatdate
msg["Message-ID"] = make_msgid(domain="report.local")   # MUST be unique per draft
msg["Date"] = formatdate(localtime=True)
```

When there are **several findings, each with its own draft** (the operator's 1-finding-1-report rule),
this is the difference between one report and none. Also when re-staging a corrected version of a
report, **delete the superseded draft in the same run** (IMAP `STORE +FLAGS \Deleted` then `EXPUNGE`,
matched on the old subject) — do not leave two versions for the operator to choose from.

**Verify with a raw `imaplib` FETCH of `HEADER.FIELDS (SUBJECT TO MESSAGE-ID)`**, one search per
distinct subject fragment, asserting exactly one hit each. Do NOT verify with a bulk
`fetch(limit=N)` and eyeball it: a large draft folder is slow (a 500-message fetch ran >3 min and had
to be killed) and IMAP `SUBJECT` search is what actually proves presence/absence. Note that a subject
naming two hosts (`... on pipe.orf.at and bolek.orf.at ...`) legitimately matches two fragments —
count **drafts**, not fragment hits.

### Building and later patching the generator (two traps, hit live)

- Write the generator by **appending fully-expanded lines** through tiny helpers
  (`def para(t,st)` → `A(P("…", STYLE))`, `def table(rows,widths)` → `A(tbl([…]))`, `def code(b)` →
  `A(C('''…'''))`). This sidesteps the nested-triple-quote trap entirely instead of dodging it, and the
  parenthesised `KeepTogether` helper is what actually causes unbalanced-paren syntax errors — prefer
  plain `H2` paragraphs, which already carry `keepWithNext=True`, over wrapping every section in `KT`.
- **When you later patch such a generator, the file no longer contains your helper calls** — it
  contains the *expanded* form (`A(P("…", BODYS))`, `A(B("…"))`). String-replacement patches must
  target the expanded text. Grep the generated file for a distinctive phrase before writing the
  `old_string`, or every patch attempt asserts `NOT FOUND`.
- **⚠️ ALWAYS set a unique `Message-ID` on an appended draft, or Gmail treats it as a REVISION of the
  previous appended draft and silently deletes the earlier one.** Hit live 2026-10: two per-finding
  reports staged minutes apart to the same vendor — staging report B made report A vanish from
  `[Gmail]/Draf`. `EmailMessage()` does not add a `Message-ID` for you; add
  `msg["Message-ID"] = email.utils.make_msgid(domain="<engagement>.local")` and add `msg["Date"]` too.
  After staging N reports, delete any duplicate that lacks a `Message-ID` (that is the superseded copy),
  then assert exactly one draft per subject.
- **Verify with an IMAP `SUBJECT` search, not a positional fetch.** `box.fetch(reverse=True, limit=N)`
  silently misses older drafts once the folder grows (seen: `limit=60` returned 30 messages and the
  draft in question was not among them, while `M.search(None, 'SUBJECT', '"<fragment>"')` found it
  instantly). Use `imaplib` for the check:
  `M.select('"[Gmail]/Draf"'); M.search(None, 'SUBJECT', '"pipe.orf.at"')` → expect 1 hit per report.
  Fetch headers with `BODY.PEEK[HEADER.FIELDS (SUBJECT TO MESSAGE-ID)]` so the check does not mutate
  the draft. Also note `imap_tools`' `fetch()` defaults to `mark_seen=True`, which is a side effect you
  do not want on a draft folder.
- **One finding = one report. Merge ONLY when the items are a single chain attack.** Before splitting,
  ask: does fixing one item fix the other, and can one item be used to reach the other? Same root cause
  with different blast radius (e.g. one host's cookie reflection vs 16 hosts minting the same
  header-derived token) is ONE report. Two unrelated primitives that merely coexist on the same target
  (e.g. a header-derived session cookie and a reflected XSS on an unrelated endpoint) are TWO reports,
  even though the same `security@`/`ciso@` mailbox receives both — a shared recipient is not a shared
  finding. Add `msg["Message-ID"]` (above) or the second staging will eat the first.
- **A subject-match refetch can miss a draft that WAS appended — do not conclude "append failed" from one
  equality check.** Hit live 2026-10: `append` returned `OK [APPENDUID 6 1078] (Success)`, then
  `box.fetch(reverse=True, limit=12)` filtering on `msg.subject == SUBJECT` found nothing and the script
  exited 3. The draft was sitting in `[Gmail]/Draf` the whole time. Two causes compound: the folder is often
  busy enough that `limit=12` does not reach it, and `imap_tools` returns long subjects with embedded
  line breaks, so `==` against your literal subject fails. Do this instead:
  ```python
  box.folder.set("[Gmail]/Draf")
  msgs = list(box.fetch(reverse=True, limit=30))          # generous limit
  for mm in msgs:                                          # print every candidate BEFORE asserting
      print((mm.subject or "").replace("\n", " ")[:90],
            [(a.filename, len(a.payload)) for a in mm.attachments])
  hit = [m for m in msgs if "product accuracy review" in (m.subject or "").lower()]   # short fragment
  ```
  Match on a short lowercased **fragment**, not the full subject; raise the limit; and list every draft's
  subject + attachments so a miss is visibly a miss rather than a silent exit code.
- **Verify by LISTING the folder, not by a keyword-limited reverse fetch.** A refetch of the shape
  `box.fetch(reverse=True, limit=12)` + `if mm.subject == SUBJECT` reported `DRAFT NOT FOUND ON REFETCH`
  immediately after a successful `append` — the mailbox simply had more recent drafts than the limit, so the
  new one was outside the window. Do it this way instead:

  ```python
  box.folder.set(draft)
  msgs = list(box.fetch(reverse=True, limit=30))
  for mm in msgs: print("-", (mm.subject or "")[:90], [(a.filename, len(a.payload)) for a in mm.attachments])
  hit = [mm for mm in msgs if "product accuracy review" in (mm.subject or "").lower()]   # fragment, not ==
  ```

  Match on a lowercased **fragment** (fetched subjects arrive line-wrapped, so `==` fails on long subjects),
  and print the folder listing either way — the listing is what tells you the draft is really there. Assert
  attachment filename + byte size + `content_type` on the hit, then assert the body is English
  (`re.search(r"\b(yang|tidak|adalah|dengan|untuk|pajak)\b", body, re.I) is None`).
- Run the generator through `write_file` + the reportlab-bearing interpreter, with every code block as a
  `'''…'''` literal (see the nested-quote trap above) — lint the generator before building.
- Keep the generator and the draft script in the engagement's `submission/` dir next to the PDF, so the whole
  chain (constants → PDF → draft) is reproducible from disk. State the absolute paths in the reply, since the
  CLI has no attachment channel.

### Authoring the generator FROM `execute_code` re-triggers the nested-quote trap

The `'''`-for-code-blocks rule above is not only about the generated file. When you *write* the
generator from an `execute_code` cell, the cell's own triple-quoted string collides with the
generator's blocks and dies with the same misleading `SyntaxError: '(' was never closed`.

Two things that work:

1. **Build the file line-by-line instead of as one heredoc.** Keep a `TQ = "'''"` constant and
   emit each code block as `L.append("A(C(" + TQ + block + TQ + "))")`, then
   `path.write_text("\n".join(L))`. The block text is a normal Python string, so `"` inside
   curl/JSON payloads is harmless.
2. **Append the long content sections in a second pass** (`open(path, "a")`) rather than one
   200-line blob — a failure in the second pass leaves the working header/styles on disk.

Always lint immediately after writing: `ast.parse(src)` inside the same cell. The `C(` line the
parser blames is never the culprit; the actual culprit is the block far below it.

## Support files
- `scripts/qa_pdf_layout.py` — deterministic layout QA gate (stranded headings, margin overflow, overlap) via pymupdf. Run it on every generated PDF before delivery.
- `scripts/lookup_vrt.py` — fetch VRT JSON, dump a category subtree (e.g. Broken Access Control) + keyword search. Re-runnable.
- `references/content-json-builder-pattern.md` — **the cheapest way past every nested-quote trap in
  this skill**: keep report content in `content_<FID>.json` and write ONE generic ~40-line builder,
  instead of a per-finding generator. Content-vs-wrapper collisions become impossible; verified on
  two reports built first try (also covers why a quoted shell heredoc fails with
  `unexpected EOF while looking for matching`).
- `references/per-finding-split-and-draft-hygiene.md` — the one-report-per-finding decision test (same root cause vs chain attack), and the Gmail `Message-ID` trap that silently deletes a previously staged draft, with the re-runnable staging + IMAP `SUBJECT`-search verification recipe.