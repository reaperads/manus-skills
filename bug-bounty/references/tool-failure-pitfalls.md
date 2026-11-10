# Reference: Tool Failure Pitfalls — Documented Failures & Recovery Patterns

Real-world tool failures with exact errors and verified recovery pivots. Check here
BEFORE concluding the environment is broken. Pattern discipline: capture the FIX, not
the failure — never harden "X is broken" into a rule; backends and configs change.

---

## web_extract Returns Search-Backend Error (cannot extract URL)

**Exact error:** `DuckDuckGo (ddgs) is a search-only backend and cannot extract URL content. Set web.extract_backend to firecrawl, tavily, exa, or parallel.`

**Cause:** `web.extract_backend` unset or `ddgs` — search-only, no extraction capability.

**Recovery (first that fits):**
1. **GitHub repos/READMEs** — skip extract, go straight to terminal:
   `curl -sL https://raw.githubusercontent.com/<org>/<repo>/main/README.md`
   (try `main` then `master`; instant, works when web_extract cannot)
2. Plain-text endpoints (`.md` `.txt` `.json` `.csv`, raw.githubusercontent.com) — same curl pattern.
3. Durable fix: set `web.extract_backend: firecrawl|tavily|exa|parallel` in config.yaml.
4. Dynamic/JS pages — `browser_navigate` + JS extraction.

**Pattern:** web_extract ≠ web_search. On a search-only backend, extraction-class tasks
fall immediately to curl (static) or browser (dynamic) — don't retry web_extract.

## Browser Tool Non-Functional (CDP Connection Refused)

**Problem:** All `browser_navigate` calls return HTTP 500 from localhost:9377 with CDP connection refused.

**Recovery:**
- Use `execute_code` for API testing that needs token lifecycle (bypasses subagent timeouts)
- Use `web_search`/`web_extract` for public program enumeration (faster than browser)
- Use `terminal` for CLI tool install/verification (`tool-installation-windows.md`)
- **Stealth/scripted need:** CloakBrowser from Python — `from cloakbrowser import launch` (see `cloakbrowser-stealth-browser.md`); verified working when the built-in browser stack is down.

**Pattern:** browser fails → `execute_code` for attacks, `web_search` for recon, `terminal` for tool management, CloakBrowser for anti-bot/scripted browsing.

## DuckDuckGo Rate Limiting

**Problem:** `web_search` returns empty results after ~10 queries.

**Recovery:**
- Aggregator endpoints: `bugcrowd.com/engagements.json`, `curl https://api.yeswehack.com/v2/programs?states=published`
- Cached scope data: `arkadiyt/bounty-targets-data` (Bugcrowd)
- Batch similar searches; reduce query frequency

**Pattern:** program discovery → `curl` → `python3` parsing, not repeated `web_search`.

## search_files Pattern "*" Fails (rg regex error)

**Error:** rg "repetition operator missing expression".

**Cause:** bare `*` is an invalid regex (glob≠regex confusion).

**Fix:** content search → `pattern: "."`; file listing → `target='files'` with a real glob (`*.py`), or terminal `ls`/`find`.

## Program-Page Extraction 503/504 (Immunefi, program portals)

**Problem:** curl returns 503 on lab/program URLs; `web_extract` often 504 on SPA program pages.

**Recovery:** `browser_navigate` + JS extraction from the live page. Immunefi is a client-rendered SPA — no static endpoint; use SmartContractsHacking.com aggregator or `web_search` for program discovery (`immunefi-program-discovery.md`).

## Subagent Timeout on Sequential Workflows

**Problem:** Subagents timeout on sequential API workflows (create account → test endpoints) due to 300s hard limit.

**Recovery:**
- `execute_code` from main thread for token-lifecycle API testing
- `terminal` for external scripts with `timeout=300`
- `process` tool for background tasks with explicit `wait`/`poll` verification

---
Master KB: agent-kb-bounty-exploit-master.md authority > SKILL.md. Unproven/blocked chain = INFORMATIONAL.
