---
name: bugbounty-workflow-0xkonde
description: WORKFLOW BUG BOUNTY — 0xkonde // ZERO-DAY HUNTER
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# WORKFLOW BUG BOUNTY — 0xkonde // ZERO-DAY HUNTER
> Model: opus 5.5 via Hermes Agent. Doktrin: PROVEN Critical/High only. Medium/Low = fuel, bukan hasil.

## 0. DOCTRINE (non-negotiable)
1. FULL AUTONOMY. Gas, jangan tanya "lanjut gak?".
2. Stop cuma 2: (a) Critical/High PROVEN via validation gate, atau (b) semua vector habis -> `SAFE + NEGATIVE SPACE`.
3. Urutan serang: UNAUTH dulu, akun test PALING AKHIR.
4. Tiap klaim wajib PoC real dari terminal. Kata "possibly" = HARAM.
5. Chain anomaly kecil jadi 1 serangan lethal. Critical lahir dari chain, bukan single bug.
6. Resource-frugal: OTP 1x/akun, captcha max 2x STOP, proxy residential cuma kalau diblokir/geo. Money-path butuh deposit real -> STOP, lapor dulu.

## 1. VALIDATION GATE (jangan report kalau ada yg missing)
1. Raw request+response VERBATIM (bukan summary).
2. CONTROL-TEST vs behavior default/official. Sama -> RETRACT (by-design).
3. Impact + severity jelas.
4. Repro dari clean session.

## 2. PHASE ORDER
```
0 scope      -> cek scope deny-wins SEBELUM sentuh HTTP
1 recon      -> subdomain, live host, crawl, JS, API spec
2 surface    -> ranking attack surface
3 attack tree-> threat model + crown jewel
4 hunt       -> 1 bug class at a time, deep bukan spray
5 ideation   -> baca writeup, pola CVE lama -> pola baru
6 chain      -> A->B->C escalation
7 validate   -> 7-Question Gate + 4 gates
8 report     -> H1/Bugcrowd/Immunefi
9 remember   -> catat lesson
```

## 3. PHASE 0 — SCOPE
- Paste scope dari program page ke `targets/<target>/scope.md`
- Verify tiap asset/domain milik org target.
- Out-of-scope disentuh = N/A, bunuh validity ratio.

## 4. PHASE 1 — RECON (wajib sebelum testing)
```bash
# 1. Subdomain
subfinder -d TARGET -silent | anew /tmp/subs.txt
assetfinder --subs-only TARGET | anew /tmp/subs.txt

# 2. Live hosts
cat /tmp/subs.txt | dnsx -silent | httpx -silent -status-code -title -tech-detect -o /tmp/live.txt

# 3. URLs
cat /tmp/live.txt | awk '{print $1}' | katana -d 3 -silent | anew /tmp/urls.txt
echo TARGET | waybackurls | anew /tmp/urls.txt
gau TARGET | anew /tmp/urls.txt

# 4. Nuclei critical/high/medium
nuclei -l /tmp/live.txt -severity critical,high,medium -silent -o /tmp/nuclei.txt

# 5. API spec — sikat duluan, sering no-auth
for p in "/swagger/v1/swagger.json" "/swagger.json" "/api/swagger.json" "/openapi.json" "/api/openapi.json" "/v1/api-docs" "/api-docs" "/swagger-ui.html" "/redoc"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://TARGET$p")
  [ "$code" = "200" ] && echo "FOUND: $p"
done
curl -s "https://TARGET/swagger/v1/swagger.json" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m.upper(),p) for p,v in d.get('paths',{}).items() for m in v]"

# 6. JS secrets
cat /tmp/urls.txt | grep "\.js$" | sort -u > /tmp/jsfiles.txt
# + SecretFinder / jsluice / grep manual

# 7. Takeover + quick wins
nuclei -l /tmp/subs.txt -t ~/nuclei-templates/takeovers/ -o /tmp/takeovers.txt
curl -s https://TARGET/.git/config
curl -s https://TARGET/.env
curl -s https://TARGET/api/graphql -X POST -H 'Content-Type: application/json' -d '{"query":"{__schema{queryType{name}}}"}'
```

Quick-wins checklist:
- [ ] takeover (github.io, heroku, azure, s3 NoSuchBucket, dsb)
- [ ] /.git, /.env, /actuator/env, /actuator/heapdump
- [ ] JS secret beneran (bukan curve constant / i18n / public key)
- [ ] open redirect (?redirect= ?next= ?url=)
- [ ] CORS `Origin: https://evil.com` + creds
- [ ] S3/GCS listable
- [ ] GraphQL introspection ON
- [ ] Firebase `https://APP.firebaseio.com/.json`

Fingerprint:
- `XSRF-TOKEN` + `*_session` = Laravel -> coba /horizon /telescope /storage/logs/laravel.log
- `PHPSESSID` = PHP
- `X-Powered-By: Express` = Node
- `wp-json` = WordPress -> /wp-json/wp/v2/users /xmlrpc.php /?author=1

## 5. PHASE 2 — SURFACE + THREAT MODEL
```
TARGET:
CROWN JEWELS: 1.___ 2.___ 3.___
SURFACE:
 [ ] unauth: login, register, reset, public API
 [ ] auth: upload, export, API calls
 [ ] cross-tenant: org/team/workspace ID
 [ ] admin: /admin /internal /debug
PRIORITAS: crown jewel x entry termudah
```
- Pake app 15 menit kayak user asli.
- Tech stack: bahasa, framework, auth, cache.
- Baca 3 disclosed report program itu.
- Siapin 2 akun (attacker + victim).
- 5-MINUTE RULE: semua 401/403/404 5 menit -> MOVE ON.
- 1-HOUR RULE: 1 jam no progress -> SWITCH CONTEXT.

## 6. PHASE 3 — HUNT (satu class, deep)

### IDOR (30% paid) — 10 varian
1. Direct `/api/users/123` -> 456
2. Body `{"user_id":456}`
3. GraphQL `node(id: base64(OtherType:123))`
4. Batch `?ids=1,2,3,4,5`
5. Nested `/orgs/{org}/users/{user}`
6. File `?path=../other-user/file.pdf`
7. Predictable (seq int, timestamp)
8. Method swap (GET 403? coba PUT/PATCH/DELETE)
9. Version rollback (/api/v2 blocked? coba /api/v1/)
10. Header `X-User-ID: victim` `X-Org-ID: victim_org`
- Wajib 2 akun. Test GET+PUT+DELETE+PATCH semua. Chain: read PII=Med, write=High, admin=Critical.

### Auth / JWT / OAuth
- Tanpa token, token expired, token user lain.
- JWT: `alg:none`, weak secret, kid injection.
- OAuth: missing `state`, `redirect_uri` wildcard, missing PKCE, implicit flow.
- Open redirect -> OAuth code theft (11 bypass: `//evil.com`, `https://target.com@evil.com`, `https://target.com\\@evil.com`, `%252F%252F`, `///evil.com`, `%09`, `#`, `%00`, param pollution, `..%2F`, unicode).

### SSRF
- `http://169.254.169.254/latest/meta-data/` , `http://127.0.0.1:6379/` `:9200` `:27017`
- Bypass IP (11): `2130706433` `0x7f000001` `0177.0.0.1` `127.1` `[::1]` `[::ffff:127.0.0.1]` redirect chain, DNS rebinding, `%2523@`, unicode `①②⑦.⓪.⓪.①`, `gopher://`
- Impact: DNS-only=Info JANGAN submit. metadata readable=High. +exfil keys=Critical.

### XSS
Sinks: `innerHTML outerHTML document.write eval setTimeout(string) new Function`
Chain: stored + admin panel = High. + CSRF token theft = Critical.
SQLi: JANGAN manual exploit. Tanda -> langsung sqlmap:
```bash
sqlmap -u 'https://TARGET/api/search?q=test' --batch --level=3 --risk=2
```

### GraphQL
- Introspection doang = Info.
- `node()` bypass per-object auth = bug.
- Batching 100x login = rate limit bypass.

### Race
```bash
seq 20 | xargs -P 20 -I {} curl -s -X POST https://TARGET/redeem -H "Authorization: Bearer $TOKEN" -d 'code=PROMO10' &
```
Target: kupon, gift, transfer/withdraw, vote, OTP.

### SSTI detect
`{{7*7}}` `${7*7}` `<%= 7*7 %>` `#{7*7}` `*{7*7}` `{{7*'7'}}`
Jinja2 RCE: `{{config.__class__.__init__.__globals__['os'].popen('id').read()}}`

### ATO taxonomy (7 path)
1. Reset poisoning via Host/X-Forwarded-Host
2. Reset token leak via Referer
3. Token predictable -> ffuf `seq -w 000000 999999`
4. Token reuse / no expiry
5. Email change tanpa password
6. OAuth linking abuse
7. Session fixation (session ID gak ganti habis login)

### File upload bypass
`file.php.jpg` `file.pHp` `.phtml .phar .shtml` Content-Type spoof `GIF89a; <?php` `.htaccess` `<svg onload=alert(1)>` race upload+exec polyglot zip-slip.

### LLM/AI (wajib chain ke exfil/RCE/ATO, ASI doang = Info)
Prompt injection, tool misuse (fetch URL=SSRF, code tool=RCE), IDOR chat history, system prompt extract, indirect injection via doc/URL, excessive agency.

### Cache poisoning / Smuggling
- Unkeyed header `X-Forwarded-Host X-Original-URL X-Rewrite-URL`, param cloaking `?a=v;poison=xss`, fat GET, deception `/account/settings.css`
- CL.TE / TE.CL / H2.CL, `Transfer-Encoding: xchunked` + tab/space prefix.

## 7. PHASE 4 — CHAIN (A->B->C, bayaran 3-10x)
| A | B | C |
|---|---|---|
| IDOR read | PUT/DELETE same endpoint | full manipulate |
| SSRF | metadata | IAM exfil -> RCE |
| stored XSS | HttpOnly miss | hijack -> ATO |
| open redirect | OAuth redirect_uri | code theft -> ATO |
| S3 listing | JS bundle secret | OAuth chain |
| no rate limit | OTP brute | ATO |
| GraphQL introspection | missing field auth | mass PII |
| CORS reflect | +credentials | data theft |
| host header | reset poisoning | ATO |

Protokol: CONFIRM A -> MAP SIBLINGS -> TEST SIBLINGS -> CHAIN -> QUANTIFY (N users / $X / N records) -> 1 report per chain.

## 8. PHASE 5 — ITERATION
- Gagal (revert/403/error): tulis 1 baris LESSON, ganti payload, RUN AGAIN. Min 3 iterasi per vector.
- Stuck -> pindah endpoint/fungsi beda total. Jangan stop nanya.
- Tiap beberapa step tulis STATE:
```
STATE @ <target> <HH:MM>
findings: <proven + kandidat + tier>
invariants: <yg harus hold>
tested-safe: <vector -> kenapa gagal>
untouched: <belum disentuh>
next: <3 move konkret>
```

## 9. PHASE 6 — VALIDATE (7-Question Gate, semua YES)
1. Bisa exploit SEKARANG dgn PoC real?
2. Kena user real yg gak ngapa-ngapain?
3. Impact konkret (duit, PII, ATO, RCE)?
4. In-scope sesuai policy?
5. Udah cek duplicate (hacktivity/changelog/issues)?
6. Bukan di always-rejected list (atau udah di-chain)?
7. Triager capek jam 5 sore bakal bilang "yes real bug"?

4 gates: Reality (bug real, in-scope, repro, evidence) -> Impact (attacker bisa apa yg tadinya gak bisa? ada victim real?) -> Dedup (5 disclosed terakhir dibaca) -> Quality (judul formula, req copy-paste, screenshot impact, CVSS, fix 1 kalimat, <600 kata).

CVSS patokan: IDOR read 6.5 Med, IDOR write 7.5 High, auth bypass admin 9.8 Crit, SQLi exfil 8.6 High, SSRF metadata 9.1 Crit, race double-spend 7.5 High, JWT none 9.1 Crit.

ALWAYS REJECTED (jangan submit): CSP/HSTS/SPF header doang, introspection doang, banner version tanpa CVE exploit jalan, clickjacking halaman non-sensitif, tabnabbing, CSV injection, CORS wildcard tanpa PoC exfil creds, logout CSRF, self-XSS, open redirect doang, client_secret di mobile app, SSRF DNS-ping doang, host header doang, no rate limit form non-kritis, session gak invalid logout, concurrent session, IP internal, mixed content, cipher lemah, cookie flag doang, broken link, autocomplete password.

## 10. PHASE 7 — REPORT
Formula judul: `[Class] in [endpoint] allows [actor] to [impact] [scope]`
Bagus: `IDOR in /api/v2/invoices/{id} allows auth user to read any customer invoice`
Jelek: `IDOR vulnerability found`

Template H1:
```
Title: [Class] in [endpoint] leads to [Impact]
## Summary (2-3 kalimat: apa, dimana, attacker bisa apa)
## Steps To Reproduce (1. login attacker 2. req exact 3. observe 4. confirm gain)
## Supporting Material (screenshot/video/Burp req-resp)
## Impact (attacker bisa [aksi] -> [harm]. N users / Y data / $Z)
## Severity CVSS 3.1 X.X (AV:N AC:L PR:N UI:N)
```

60-detik checklist: judul formula, kalimat pertama impact, req copy-paste, bukti impact (bukan cuma 200), 2 akun, CVSS, fix 1 kalimat, no typo path, <600 kata, severity = impact (jangan overclaim).

Counter downgrade:
- "Requires auth" -> "cuma butuh akun gratis, no role khusus"
- "Limited impact" -> "kena N users / tipe PII / $ amount"
- "Known" -> "minta nomor report, gue search gak ada"
- "By design" -> "minta docs yg bilang intended"

Operator: agent bikin teks per-field copy-paste, satu field sekali jalan. Humanize first-person, active voice "I found", tanpa em-dash / leverage / seamless / ensure.

## 11. NOTE-TAKING (jangan hunt tanpa ini)
```markdown
# TARGET: x.com -- SESSION 1
## Leads
- [14:22] /api/v2/invoices/{id} no auth visible, testing...
## Dead Ends
- /admin IP restricted (15+ bypass header gagal)
## Anomalies
- GET /api/export 200 tanpa cookie
- POST /api/check-user 150ms vs 8ms (user enum?)
## Rabbit Holes (max 15 mnt)
- [ ] 10 mnt: JWT kid injection
## Confirmed
- [15:10] IDOR /api/invoices/{id} read+write
```

## 12. SEVERITY MAP (Bugcrowd/H1)
P1 Crit: RCE, SQLi, auth bypass full, SSRF metadata+exfil
P2 High: IDOR sensitif, stored XSS B2B, priv esc
P3 Med: stored XSS B2C, SSRF internal, mass assignment
P3/P4: reflected XSS, info disclosure keys, CORS+creds
P4/Info: open redirect, no rate limit, self-XSS

---
Scaffold: `targets/<target>/scope.md findings/ evidence/ submissions.txt recon/`
Ingat: teori = buang waktu. "Could" bukan bug. Prove it atau drop it.
