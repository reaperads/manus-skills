---
name: security-poc-video-production
description: Use when a vendor/triager asks for a video proof-of-concept for a vulnerability finding.
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Video PoC production (for vulnerability reports)

Trigger: a program or vendor says "we need a video PoC", or the operator hands you a finding /
PDF report and asks for a demonstration video.

## Rule 0 — re-run the exploit chain BEFORE you storyboard

**Do not plan the video from the written report.** The report may describe behaviour the live target
no longer has, and a video faithfully animating a stale claim is worse than no video.

Session case that created this rule: the report said the crafted OAuth authorize URL lands the victim
on the vendor's legitimate login page. Re-running it showed the chain from the `api.` host 302s into a
**404** — the SPA login is served on the `app.` host instead. A video built from the report would have
displayed a 404 and handed the triager a reason to reject the finding.

So: reproduce every reported step against the live target (or lab) first, capture the REAL output, and
only then decide what the video can honestly claim. If a step no longer behaves as documented, tell the
operator before building anything — that is a **report correction**, and finding it is the most
valuable thing you can do in this task.

## Route selection

| Situation | Route | Why |
|---|---|---|
| Exploit re-runnable in a browser or over an HTTP API | **A — hybrid: rendered terminal + Playwright** | highest fidelity; shows the real requests *and* the real page |
| CLI / API only | **B — rendered terminal from real transcripts** | no invented output, full control of pacing and highlighting |
| Only a static PDF exists | **C — page walkthrough with zoom/pan** | weakest. A triager asking for "video PoC" wants to see it happen. Say so before spending effort. |

Default to **A** for web findings: terminal segments carry the request/response proof, the browser
recording carries the visible impact.

## Segment order that works

1. **Title card** — finding title, target, endpoint, severity, researcher, date.
2. **The primitive**, as real HTTP: the unauthenticated request and its success response.
3. **"No auth gate" proof** — send a deliberately-invalid body and show the server answers with a
   *validation* error (400) rather than *unauthorized* (401). This demonstrates there is no auth check
   to fail, without creating extra state on the target.
4. **The control / negative case** that makes the finding precise (e.g. an unregistered redirect URI
   returns 400 while the registered one returns 302). This is what makes a triager trust the report.
5. **Browser recording** — the visible consequence, with a composited address bar.
6. **Closing card** — impact, plus an explicit statement of what was NOT done (no victim account used,
   no interaction).

Target 60-120 s. Triage attention is short.

## Hard rules for the artifact

- **MP4 / H.264 / `yuv420p` / `+faststart`.** That combination is what vendor portals accept.
- **English** captions and labels (external artifact).
- **Redact real secrets.** Render as `first8…[REDACTED, N chars]`; keep the full value's
  `len + sha256` in a side file for your own verification. Never put a live `client_secret` / token /
  key into a frame.
- **Never perform the destructive or impacting step.** Demonstrate the primitive and the mechanism,
  then state in the closing card that no victim interaction occurred. For a pre-auth RCE against live
  third-party production, build a local lab running the vulnerable version instead of firing the
  payload at them.
- **Minimise state created on live third-party services.** One registration, not five. Write every
  artifact ID you create into a file and tell the operator, so they can add it to the revocation list.
- **All on-screen text must come from real captured output.** Typed-looking terminal frames are fine;
  invented responses are not.
- **Deliver ONE version.** When the re-run forces a change and the submission has NOT happened yet,
  rebuild so the report and the video agree and ship that as the single version — no "correction",
  "v2", "corrected", "previously" or "superseded" framing anywhere, and do not leave the old build
  where it can be submitted by mistake (park it in `superseded/`). A correction section is only for a
  report that was *already* submitted. Name the video exactly as the report references it so the two
  are visibly a pair.
- **Prove the frames contain only your text.** Re-render the same card with PIL and diff it against the
  frame extracted from the finished MP4: H.264 noise is ~0.05 %, so a matching text bbox and an
  identical text-row count proves no extra line slipped in (this is how a wrong contact alias was
  cleared). Also grep the build scripts for anything that must not appear.

## Pitfalls (each one cost real time in the session)

1. **Playwright's video records the VIEWPORT ONLY — no address bar, no browser chrome.** If the whole
   point is "the URL stayed on the legitimate domain", you must composite the address bar back in
   (PIL-rendered PNG + `ffmpeg overlay`). Take the URL from `page.url()` / the redirect chain so the
   bar carries the truth.
2. **`ffmpeg` 9.x removed `-vsync`.** Use `-fps_mode cfr`. `Unrecognized option 'vsync'` means 9.x.
3. **Mixing frame rates in a concat silently truncates a segment.** A 25 fps Playwright recording
   concatenated with 30 fps segments collapsed from 15 s to ~8 s while the following card grew to
   absorb the difference — the total duration still looked correct, so nothing errored. Force
   `fps=30` inside every segment's filter chain AND pass `-r 30 -fps_mode cfr` at concat, then verify
   the timeline.
4. **Verify the finished file by sampling it, never by trusting the build log.** Extract frames at
   fixed timestamps and classify them by pixel composition (title bar present? address bar bright?
   caption strip populated?). That is what caught the truncated segment, a missing address bar, and
   pillarboxing. `scripts/verify_video_timeline.py` does exactly this.
5. **`force_original_aspect_ratio=decrease` + `pad` pillarboxes the page** — a 16:9 recording in a
   2.24:1 frame left 21 % dead bars. Use `increase` + `crop` to fill.
6. **Do not use an auxiliary vision model to QA the frames.** In this setup it could not see the image
   at all, and the reportlab skill records an unrelated case where it confidently described a
   different document. Use DOM text (`page.inner_text('body')`), `page.title()`, and pixel statistics.
7. **State your colour scale when bucketing.** A "suspiciously flat, mostly black" verdict was wrong:
   after integer division by 32 the bucket `(7,7,7)` is **white (224-255)**, not black. Print the
   actual light / dark / edge-density fractions instead of a verdict derived from a bucket label.
8. **`-t <seconds>` on a short input does not extend it.** With `-loop 1` stills it pads, but check the
   real source duration — a Playwright recording's length is the whole context lifetime, not just the
   part you wanted.
9. **`MemoryError` mid-render: never accumulate frames in a list.** A 1920x1080 RGB frame is ~6.2 MB,
   so a few hundred held frames exhaust a 6 GB box. Make the renderer a **generator** (`yield` one
   frame), write each into ffmpeg's stdin, then `del f`. The first build worked only because the
   machine happened to have RAM at the time; the rerun died with `MemoryError` at the same code.
10. **The operator asking for "comments in the video" means commentary on EVERY segment**, not just a
    closing card. Put a commentary band (dark strip + one bold sentence of plain English, optionally a
    status badge like `NO AUTH REQUIRED`) at the bottom of every segment, including the terminal ones.
    Verify with pixels that the band is populated in every sampled frame.

## Environment this was built on

Present: `ffmpeg` 9.0 (WinGet), Python `playwright` with Chromium installed, `cv2`, `Pillow`,
`PyMuPDF`. Absent: `asciinema`, `agg`, `ImageMagick`, `gifski`. So render terminal frames with PIL and
pipe raw RGB into ffmpeg — do not plan a pipeline around asciinema.

## Supporting files

- `references/ffmpeg-video-pipeline.md` — concrete filter graphs and commands: segment encode from
  PIL frames, the address-bar overlay graph, fps-normalised concat, ffprobe checks.
- `scripts/verify_video_timeline.py` — deterministic post-build verification: per-segment
  duration/fps table plus timestamped frame classification of the final MP4.