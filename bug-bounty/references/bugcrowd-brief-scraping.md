# Bugcrowd Brief Scraping (JS-rendered) — camofox recipe

## When to use
Bugcrowd engagement briefs (scope, rewards, announcements) do NOT render via plain curl:
- `curl bugcrowd.com/engagements/<slug>/brief` → 301
- JSON endpoint probes (`/brief.json`, `/targets`) → 200 but useless SPA shell (~6KB)
Use the local anti-detect browser stack instead.

## FAST PATH first — built-in browser tools + DOM queries (verified 2026-09, Rapyd)
Before starting the camofox server, try the built-in browser tools. `browser_navigate` renders the
engagement page and the scope targets are plain `<table>` elements — quickest, most structured read:

```js
[...document.querySelectorAll('table')].map((t,i)=>({i, txt:t.innerText.slice(0,2500)}))   // scope tables
[...document.querySelectorAll('h3,h2,h4')].map(h=>h.innerText.trim()).filter(t=>/tier|scope|target/i.test(t))
document.body.innerText.slice(document.body.innerText.indexOf('Things to know'))           // rules/limits
```
Verified shape on a public Bugcrowd engagement:
- Table 0 = Tier 3 (Premium) — rows carry tags like `API Testing`
- Table 1 = Tier 2, Table 2 = Tier 1 wildcards
- Last table = **Out of Scope Targets** (rows typically have NO tag column — that missing tag is the tell)
- Headings read `Tier 3 In scope Premium` / `Tier 2 In scope` / `Tier 1 In scope` /
  `Out of Scope Targets`; use them to label tables instead of trusting order
- Per-tier reward bands, "Out-of-scope vulnerabilities", harder rate-limit wording and the
  required traffic header all live in body text, not tables
- Stable anchors: `#targets`, `#resources`, `#things_to_know`

If the extract step returns nothing for these pages (search-only extract backends), skip retries and
render in a browser — the briefs are SPAs.

## Stack: camofox server (~/camofox-browser)
- Start: `cd /c/Users/WINDOWS10/camofox-browser && npm start` (background, port 9377)
- Health: `curl -s http://localhost:9377/health`
- Underlying binary: Camoufox (anti-detect Firefox) at `~/AppData/Local/camoufox/`

## API (verified working)
1. Open tab:
   `curl -s -X POST http://localhost:9377/tabs/open -H "Content-Type: application/json" -d '{"userId":"hermes","url":"https://bugcrowd.com/<slug>"}'`
   → `{"ok":true,"targetId":"<id>",...,"title":"..."}`
2. Snapshot (a11y tree, YAML-ish, includes refs + full text):
   `curl -s "http://localhost:9377/tabs/<targetId>/snapshot?userId=hermes" -o snap.json`
   → `{"url", "snapshot", "refsCount", "truncated", "totalChars"}`
   **PITFALL: `userId` is REQUIRED as query param — omitting returns `{"error":"userId required"}`.**
3. Extract + parse:
   ```python
   import json
   d = json.load(open('snap.json', encoding='utf-8'))
   open('snapshot.txt','w',encoding='utf-8').write(d['snapshot'])
   ```
   Then read snapshot.txt with offset/limit and mine sections: rewards tables, targets, announcements, exclusions.

## Camoufox binary recovery (server fails to launch: cache empty/incomplete)
Symptom: `/tabs/open` hangs or errors; cache dir `~/AppData/Local/camoufox/camoufox/Cache/browsers/official/<ver>/` empty or missing exe.
`camoufox fetch` / `python -m camoufox fetch` can hang past 5min timeout (500MB download) — do it MANUALLY:
1. Check cache: `ls ~/AppData/Local/camoufox/camoufox/Cache/browsers/official/` → note version dir name (e.g. `152.0.4-beta.30-ea52a02f`).
2. Download matching release zip (~500MB, run in background):
   `https://github.com/daijro/camoufox/releases/download/v<release>/camoufox-<release>-<build>-win.x86_64.zip`
   e.g. `v152.0.4-beta.30/camoufox-152.0.4-beta.30-win.x86_64.zip`
3. Unzip INTO the version dir: `cd ~/AppData/Local/camoufox/camoufox/Cache/browsers/official/<ver> && unzip -o -q <zip>`
4. Create `version.json` in that dir: `{"release":"152.0.4","version":"beta.30"}` (match dir name parts).
5. **CRITICAL: server resolves the exe at Cache ROOT, not only the version dir:**
   `cd ~/AppData/Local/camoufox/camoufox/Cache && cp -rn browsers/official/<ver>/* .`
   Verify: `ls camoufox.exe version.json properties.json` all present at Cache root.
6. Restart server (`npm start`), then POST /tabs/open → must return targetId in seconds.

## Per-program capture workflow (consistent with _progress convention)
Dir: `D:\data hermes\bug-bounty\_progress\<program-slug>\`
Files: `snap.json` (raw) → `snapshot.txt` (extracted) → `scope.md` (facts: payout tables, targets, credentials, headers/bonus, exclusions, announcements w/ their special header IDs) → `progress.md` (gates + phased plan + log).
- Always capture: per-target-class reward tables (mobile vs web differ), excluded submission types, N-day policy, per-announcement `X-Luno-Announcement-ID`-style required headers, signup/credentials section.
- Announcements = freshest attack surface; owners explicitly state what they want tested.

## Pitfalls
- `camoufox fetch` via terminal foreground WILL timeout on 500MB — always background the manual zip download (notify_on_complete=true).
- Snapshot can include hundreds of trailing `- img` lines (avatars) — stop reading there, real content ends before.
- Never test/live-claim from the snapshot alone: snapshot = scope intel; actual probing needs the program's required traffic-identification headers from the brief.
