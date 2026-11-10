# WordPress Admin Panel Attack Surface

## Pattern: Non-Cloudflare WordPress Admin

When WordPress site has admin panel accessible WITHOUT Cloudflare/WAF:

### 1. Information Disclosure
```bash
# Version leak
curl -s "https://TARGET/" | grep -oE 'content="WordPress [0-9.]+"'

# Plugin enumeration via REST API
curl -s "https://TARGET/wp-json/" | python3 -c "
import sys,json
d=json.load(sys.stdin)
for n in d.get('namespaces',[]):
    print(f'  {n}')
"

# jQuery version
curl -s "https://TARGET/wp-login.php" | grep -oE 'jQuery [0-9.]+' | head -1
```

### 2. Login Form Analysis
```bash
# Get CSRF token
CSRF=$(curl -s "https://TARGET/wp-login.php" | grep -o 'name="nonce" value="[^"]*"' | head -1)

# Test login error messages (username enumeration)
curl -s -X POST "https://TARGET/wp-login.php" \
  -d "log=admin&pwd=wrong&wp-submit=Log+In" \
  | grep -oE '(incorrect|not registered|invalid|error)[^<]*'
```

### 3. Hidden Form Fields
Check for exploitable hidden fields in login/admin forms:
- `server` field → SSRF potential
- `redirect_to` → Open redirect potential
- `testcookie` → Cookie manipulation

### 4. File Manager Plugin
```bash
# Check for file manager plugins
curl -s "https://TARGET/wp-json/" | grep -o 'file-manager[^"]*'

# Common file manager endpoints
for path in /wp-content/plugins/wp-file-manager/ /wp-content/plugins/advanced-file-manager/; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://TARGET${path}")
  echo "[${code}] ${path}"
done
```

### 5. XML-RPC
```bash
# Check if enabled
curl -s "https://TARGET/xmlrpc.php" | head -5

# Test methods
curl -s -X POST "https://TARGET/xmlrpc.php" \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?><methodCall><methodName>system.listMethods</methodName></methodCall>'
```

### 6. Debug/Info Endpoints
```bash
for f in /wp-content/debug.log /readme.html /license.txt /wp-config.php.bak /wp-content/db.php; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://TARGET${f}")
  [ "$code" != "404" ] && echo "[${code}] ${f}"
done
```

## Severity Guide

| Finding | Severity | Notes |
|---------|----------|-------|
| Admin panel exposed (no auth bypass) | Low/Info | By-design if admin knows |
| Username enumeration via login | Low | P4 |
| Version disclosure | Info | P5 |
| File manager plugin accessible | Medium | If allows upload |
| XML-RPC enabled | Low/Medium | If brute force possible |
| Debug log exposed | Medium | May contain sensitive data |
| wp-config.php.bak accessible | Critical | May contain DB creds |
| SSRF via hidden field | High/Critical | If server processes URL |
| CSP unsafe-eval | Medium | XSS→RCE chain needed |

## Proven Findings (Atmail, August 2026)
- admin.atmailcloud.com: nginx, no Cloudflare, CSP unsafe-eval, hidden server field, jQuery 3.5.0
- www.atmail.com: WordPress with Cloudflare + Wordfence + Shield (hardened)
- webmail.junara.com: SPA webmail, previous XSS worm (CVE-2017-11617)

---

# REST surface as the plugin map (highest-yield WP recon step)

On a marketing/docs WordPress site (in-scope Tier1 for many fintech programs) `/wp-json/` is usually
public and is the single best recon call — it returns the **full route table**, not just namespaces:

```bash
curl -s -H 'X-Bugcrowd: Bugcrowd-<alias>' https://TARGET/wp-json/ -o wp_json.json   # 472 routes / 24 namespaces observed
```

Mine it: ignore core namespaces (`wp/v2`, `wp-site-health`, `oembed`, `batch`, `wp-block-*`) and treat
every remaining namespace as a plugin fingerprint **plus** a probe list — e.g.
`ithemes-security/rpc`, `ithemes-security/v1`, `wpml/v1`, `ultimate-vc/v1`, `coauthors/v1`,
`redirection/v1`, `userway/v1`, `yoast/v1`, `wp-all-import/v1`, `duplicate-post/v1`,
`objectcache/v1`, `epic/v2`, `regenerate-thumbnails/v1`, `otgs/installer/v1`, `nps-survey/v1`.

Why this beats a plugin-name grep: the route table exposes argument names and the per-route
permission surface, so you can pick the few routes worth probing instead of fuzzing blind.

## The finding class: one plugin route that forgot `permission_callback`

Probe the plugin routes unauthenticated (GET only) and hunt for the **differential** — one route
returning 200 with data while its siblings return 401. The differential is the evidence a triager
accepts; "the plugin's REST API is exposed" is not.

```bash
for r in /wp-json/ithemes-security/v1/bans /wp-json/ithemes-security/v1/logs \
         /wp-json/ithemes-security/v1/settings /wp-json/redirection/v1/redirect \
         /wp-json/objectcache/v1/status /wp-json/wp/v2/users /wp-json/wp/v2/plugins ; do
  printf '%-58s ' "$r"; curl -s -o r.json -w '%{http_code} %{size_download}\n' \
    -H 'X-Bugcrowd: Bugcrowd-<alias>' "https://TARGET$r"; head -c 120 r.json; echo
done
```

Observed on a production fintech marketing site:

| Route | Result |
|---|---|
| `/wp-json/ithemes-security/v1/bans` | **200 with no auth** → ban records: `label` = the banned **IP** (v4+v6), `created_at`, `created_by {id:'brute_force', type:'lockout_module'}` |
| same namespace `logs`, `settings`, `modules`, `actors`, `site-scanner/scans`, `dashboard-available-cards`, `rpc/lockout-stats/top-blocked-ips` | 401 |
| `/wp-json/wp/v2/users` · `/wp/v2/plugins` · `/wp/v2/settings` | 401 (good) |
| `/xmlrpc.php` | 403 (good) |
| `/wp-json/ithemes-security/v1/geolocate/127.0.0.1` · `/169.254.169.254` | 401 — re-probe here for SSRF whenever it answers 200 |

- **Check sibling hosts for the same install.** A second in-scope host of the same brand served a
  byte-identical `/wp-json/` and the same exposed `/bans` → the finding covers two hosts; stating that
  also tells the triager whether it is one multisite or two installs.
- Severity, honestly: **P4/informational**. Leaked third-party IPs + security-posture data is
  GDPR-flavoured personal data, so Low is defensible, but expect "informational". Pair the leak with the
  401-sibling differential and let the triager rate it — never inflate an IP list to Medium.
- `?rest_route=/wp/v2/users` is an equivalent spelling of any REST path — test both when a rule looks
  like it matches on the URL only.

## Version fingerprinting + CVE discipline

Two sources and one hard rule:

1. per-plugin `readme.txt`: `curl -s https://TARGET/wp-content/plugins/<dir>/readme.txt | grep -E 'Stable tag|Version'`
2. `nuclei -tags wordpress,wp-plugin,wp-theme -rl 5`: its `wordpress-<slug>:detected_version` templates
   print `["<installed>"] [last_version="<known>"]` and name plugins you would not have guessed.

**A version string is not a vulnerability.** If `detected > last_version` (site runs newer than the
newest version the templates know) there is nothing to claim at all. Even when a version looks old, do
not write "vulnerable to CVE-XXXX-YYYY" unless you looked the CVE up and checked the affected range.
In one pass every detected plugin was *ahead* of `last_version` → zero CVE claims, which was the
correct output.

## User enumeration (two cheap paths)

```bash
# 1) author id → nicename (301 chain: follow Location, do not read the body)
curl -s -D - -o /dev/null "https://TARGET/?author=1" | grep -i '^location:'   # → /blog/author/<nicename>/
# 2) Yoast author sitemap (works even when /?author= is blocked)
curl -s "https://TARGET/author-sitemap.xml" | grep -oE '<loc>[^<]+' | head
```

nuclei reports the second as `wp-yoast-user-enumeration`. Username disclosure is P4/P5 and often OOS —
carry it as a secondary observation, never as the headline finding.

## Honest negatives worth repeating (so the next session skips them)

- `ffuf` with a curated sensitive-file wordlist across 10 hosts → **0 hits**; `.env`, `.git/config`,
  `wp-config.php` all 403 on hardened hosts. A 200 whose body is an **SPA shell** (775 bytes of
  `<!DOCTYPE html>`) means "route not found", not an exposed file — always read the body.
- `interactsh` OOB (blind XXE in a SAML ACS, JNDI `${jndi:ldap://…}` in User-Agent / X-Forwarded-For /
  X-Api-Version, SSRF via `?url=` / `?callback=` / `?redirect_url=` on app hosts) → zero callbacks.
- Request smuggling (CL.TE, TE.CL, TE-obfuscated, double-TE, duplicate-CL) and cache-poisoning headers
  (`X-Forwarded-Host/Scheme`, `X-Host`, `X-Original-URL`) → no desync, no reflection. One host answered
  200 to the ambiguous CL.TE/TE.CL pair where siblings answered 400 — a one-line hardening note, but
  with no follow-on response it is **not** smuggling.
- `dalfox` on a reflected `?s=` search parameter → no XSS. `kxss` reporting a parameter as
  "unfiltered" (`[$ | ( ) \` : ; { }]`) only means those characters are not stripped; WordPress still
  escapes the term in-context. Reflection != XSS; let dalfox decide.
