# YesWeHack Platform Workflow

## Platform Overview
- French bug bounty platform (yeswehack.com), major EU programs
- Two API versions coexist — **v2 is partially broken**, use v1-style endpoints
- Unlike Bugcrowd (React SPA, needs aggregator), YesWeHack exposes program data directly

## Program Enumeration

### Search programs by keyword
```bash
curl -s "https://api.yeswehack.com/programs?search=<KEYWORD>" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Total: {data.get('pagination', {}).get('nb_results')} results\")
for p in data.get('items', []):
    print(f\"{p.get('slug')} | {p.get('title')} | bounty:{p.get('bounty')} | vdp:{p.get('vdp')}\")
"
```
- Pagination: `?page=N` (default 42 per page, `nb_pages` in response)
- Filter: `?search=teamviewer` returns fuzzy-matched results

### Get specific program (rules + scopes)
```bash
curl -s "https://api.yeswehack.com/programs/<SLUG>" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('Title:', data.get('title'))
print('Slug:', data.get('slug'))
print('Rules:', data.get('rules', 'N/A')[:500])
print('Rewards:', json.dumps(data.get('rewards', []), indent=2))
print('Scopes:', json.dumps(data.get('scopes', []), indent=2))
"
```

## ⚠️ API Pitfalls (discovered 2026-09-07)

### v2 endpoint is unreliable
The `https://api.yeswehack.com/v2/programs?slug=<SLUG>&with_fields=...` endpoint frequently returns 404. Do NOT rely on it.

### Correct endpoints
| Action | Endpoint |
|---|---|
| Search programs | `GET /programs?search=<q>` |
| Get program details | `GET /programs/<slug>` |
| Reports API | Not public (requires auth) |

### Scope format from API
Scopes come back with:
- `scope_type`: `"application"` (not `"in_scope"`)
- `type`: `"web-application"`, `"mobile-application-android"`, etc.
- `target`: often empty string in API — actual targets listed in `rules` text (parse manually)

### Rewards field
`rewards[]` is often **empty** even for bounty programs. Check the `rules` text for payout tiers, or view the program page directly.

## Browser Submission Flow
YesWeHack requires authenticated browser session for report submission:
1. Navigate to `https://yeswehack.com/programs/<slug>`
2. Click "Submit a report" button
3. Fill: Title, Severity, Category, Description, Steps to Reproduce
4. Attach PDF/screenshots
5. Submit

**When browser CDP is unavailable:** Prepare complete submission package (PDF + formatted report text) for user to submit manually.

## Key Response Fields
- `slug` — program identifier (URL: yeswehack.com/programs/<slug>)
- `title`, `company_name` — display names
- `bounty` — boolean (true/false), NOT min/max range
- `rules` — full program rules text (contains scope details, eligibility)
- `scopes[]` — scope entries (may have empty targets — check `rules` text)
- `status` — `"V"` = active/published

## Pitfalls
- **v2 API broken** — always prefer `/programs/<slug>` over `/v2/programs?slug=...`
- **Scope targets empty in API** — parse `rules` text for actual scope definitions
- **Rewards array empty** — check program page UI for payout tiers
- **Report submission requires auth** — no public API for creating reports

## Session Provenance
Updated from live session 2026-09-07: TeamViewer program discovery via `curl https://api.yeswehack.com/programs?search=teamviewer` → found slug `teamviewer-bounty-program`, confirmed `account.teamviewer.com` in-scope via rules text.
