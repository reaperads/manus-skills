---
name: apk-redteam-pipeline
description: End-to-end Android APK red-team pipeline — automated APK acquisition (Play Store + apkpure + apkmirror fallback), jadx decompilation, secret/URL/JWT/Firebase grep, pinned-cert extraction, exported-component enumeration, Frida runtime instrumentation templates, intent-injection probes. Built from an authorized external red-team engagement where 7 APKs were pulled manually, 4 download attempts truncated, and a hardcoded JWT + 30 internal API endpoints were recovered from one of the apps. Use when target has a mobile app catalogue (Play Store developer page), when you find an APK URL hosted on a web server, or when post-recon mentions "mobile app" in scope.
sources: authorized-engagement
report_count: 1
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

## When to use this skill

Trigger when:
- Recon surfaces 1+ mobile apps under the target's developer name (Play Store dev page)
- A web app hosts `*.apk` files directly (e.g. `Recruitz.apk` found on a subdomain during one engagement)
- APK package IDs leaked via stealer logs (e.g. `com.<brand>.app`, `com.<brand>.<sub-brand>` patterns in stealer dump format)
- Customer-facing app, dealer/partner portal, or employee mobile companion app is in scope
- Bug bounty program lists Android in scope

DO NOT use for:
- iOS-only targets (different pipeline — IPA reverse, MobSF, frida-ios-dump)
- React Native / Flutter web apps already covered by JS bundle analysis
- Server-side only assessments

---

## Stage 0 — Inventory all org-owned apps

### Play Store developer-page scrape
```bash
# Find developer page from the target's brand name
curl -sk -A "Mozilla/5.0" "https://play.google.com/store/apps/developer?id=<Brand+Name>" -o /tmp/dev.html

# Extract package IDs
grep -oE 'id=[a-zA-Z0-9._]+' /tmp/dev.html | sort -u
```

Example output (anonymized — 7 packages typical for a multi-brand conglomerate):
```
com.events.<brand>build
com.<corp>.<sub-brand-1>
com.<corp>.<sub-brand-2>
com.<corp>.<flagship>
com.<corp>.<product-line-1>
com.<corp>.<product-line-2>
com.<corp>.<sub-brand-3>
```

### Cross-reference with stealer logs
Stealer-log format includes package names like `*@com.<corp>.<app>` — extract these from `creds_userpass.txt` if you have a leaked dump.

### Brand permutation guesses (multi-brand conglomerate patterns)
```
com.<brand>.app
com.<brand>.mobile  
com.<brand>.android
com.<brand>connect.app
in.<brand>.dealer
in.co.<brand>.app
```

---

## Stage 1 — APK acquisition

### Primary: APKCombo driven by a real browser (current working path)

**Status check first — the old one-liners are now Cloudflare-gated.** `d.apkpure.net/b/APK/<pkg>`
and APKMirror currently answer with an interstitial: `curl` writes a ~5 KB
`<!DOCTYPE html><title>Just a moment...</title>` page that *looks* like a finished download
(470 B – 6 KB, `text/html`). Two mandatory sanity checks before you analyse anything:

    ls -la <pkg>.apk            # multi-MB? an APK for a real app is never 5 KB
    head -c 4 <pkg>.apk | xxd   # must be 50 4b 03 04 ("PK.."); HTML means you got the block page

Working recipe (Playwright, verified end-to-end on a 141 MB XAPK):

    await pg.goto(f"https://apkcombo.com/<app>/<package_id>/download/apk",
                  wait_until="domcontentloaded")
    await pg.wait_for_timeout(6000)
    # READ THE DOM PROPERTY, NOT A REGEX OVER raW HTML (see pitfall below)
    href = await pg.evaluate("""() => {
        const a=[...document.querySelectorAll('a')]
                  .find(e=>/r2\?u=|cloudflarestorage/.test(e.href||''));
        return a ? a.href : null; }""")
    async with pg.expect_download(timeout=900000) as dl:
        await pg.evaluate("(u)=>{const a=document.createElement('a');"
                          "a.href=u;a.download='';document.body.appendChild(a);a.click();}", href)
    await (await dl.value).save_as("<pkg>.xapk")

**Pitfall — the `&amp;` signature trap (cost several wasted attempts).** Scraping the same URL by
regex straight out of the HTML leaves HTML entities in it. A signed R2/S3 URL is
`...?X-Amz-Signature=...&amp;fp=...`; requesting that literal string returns
`403 <Code>SignatureDoesNotMatch</Code>` and the body misleads you into thinking the link expired.
Two rules: (a) prefer the DOM `a.href` **property** — the browser has already entity-decoded it;
(b) if you must scrape, un-escape before use (`u.replace('&amp;','&')`) and fetch with
`ctx.request.get()` or a real browser download, never through a shell variable that can re-split it.

`.xapk` is a zip: `<pkg>.apk` (base) + `config.<abi>.apk` / `config.<density>.apk` splits +
`manifest.json`. Extract the base APK and analyse that.

### Primary (2026-10 verified): APKCombo through a real browser
`d.apkpure.net` and `apkmirror.com` now sit behind Cloudflare bot management: a plain `curl`
to either returns a 5-6 KB **HTML** page (title `Just a moment...`), which `file` will happily
report as `HTML document` and which is easy to mistake for a truncated download. Check the first
4 bytes (`PK\x03\x04`) before analysing anything.

The download that actually works is ApkCombo driven by Playwright, because the real link is a
**signed S3 URL behind a redirector** and only the browser resolves it correctly:

```python
# 1. read the *DOM property* (not the HTML attribute) — the attribute is HTML-escaped
href = await pg.evaluate("""() => {
    const a=[...document.querySelectorAll('a')].find(e=>/r2\\?u=|cloudflarestorage/.test(e.href||''));
    return a ? a.href : null; }""")     # -> https://apkcombo.com/r2?u=<urlencoded s3 url>

# 2. let the browser perform the download (do NOT replay the URL through ctx.request/curl)
async with pg.expect_download(timeout=900000) as dl_info:
    await pg.evaluate("(u)=>{const a=document.createElement('a');a.href=u;a.download='';document.body.appendChild(a);a.click();}", href)
await (await dl_info.value).save_as(str(out))
```

Two traps that each cost a full round-trip:

- **Never replay the extracted URL with `curl`/`ctx.request`.** The S3 URL is AWS4-signed and the
  href read from raw HTML carries `&amp;` entities; re-encoding or passing it through a shell makes
  the query string differ by one byte and S3 answers
  `<Error><Code>SignatureDoesNotMatch</Code>` (HTTP 403, ~3.4 KB XML). Entity-decode **and** use the
  browser's own download machinery — the URL is also `X-Amz-Expires`-bound and IP-pinned.
- A 3-5 KB result is always an error document, whatever the extension claims. Validate before
  spending analysis time: `head -c 4` must be `PK` (APK/XAPK are ZIPs).

### Legacy: APKPure direct — try `d.apkpure.com` (the `.com`), not `.net`

**2026-10 (Tripadvisor `com.tripadvisor.tripadvisor` v70.1):** where the `.net` host is CF-gated,
`https://d.apkpure.com/b/APK/<pkg>?version=latest` answered
`302 → data.winudf.com/APK/<base64>?…&token=…` and `curl -L` fetched the real **70 MB APK in one
shot, no browser**. Try `.com` before falling back to the Playwright/APKCombo route. Always validate:
`head -c 4` must be `PK\x03\x04` — a 5 KB `<!DOCTYPE html>` "Just a moment…" page is the CF block,
not a download. (and in MSYS bash, `curl -o` wants an *absolute* output path or the file lands in the
Windows cwd, not the shell's `cd`.)
```bash
curl -sk -L --max-time 60 \
  "https://d.apkpure.net/b/APK/<package_id>?version=latest" -o out.apk   # may be a CF challenge
```

> **⚠️ Reality check (verified 2026-10-01, Vinted/fr.vinted): APKPure and APKMirror are
> Cloudflare-gated and useless from a script.** `d.apkpure.net` returns a 5.6 KB
> `<!DOCTYPE html><title>Just a moment...</title>` page instead of the APK, `apkpure.com/search`
> returns 403, and `apkmirror.com` returns 403 with a "Performing security verification" body.
> `curl` cannot pass any of them. Do not burn time on retries — go straight to the Playwright route.
>
> **Working route (Playwright, headless is fine):**
> 1. `page.goto("https://apkcombo.com/<app-name>/<package>/download/apk")` — reaches 200 normally.
> 2. Read the download href from the **DOM property**, not by regexing the HTML:
>    ```python
>    href = await pg.evaluate("""() => {
>        const a=[...document.querySelectorAll('a')]
>                   .find(e=>/r2\\?u=|cloudflarestorage/.test(e.href||''));
>        return a ? a.href : null; }""")
>    ```
>    A regex over `page.content()` picks up the HTML-escaped form and the URL will not work.
> 3. Download with a real browser download so cookies/headers match:
>    ```python
>    async with pg.expect_download(timeout=900_000) as dl:
>        await pg.evaluate("(u)=>{const a=document.createElement('a');a.href=u;a.download='';"
>                          "document.body.appendChild(a);a.click();}", href)
>    (dl_ := await dl.value).save_as("app.xapk")     # 141 MB for Vinted, ~2 min
>    ```
> 4. **`&amp;` in the URL breaks AWS signed links.** apkcombo hands out a signed
>    `r2.cloudflarestorage.com/.../*.apks?X-Amz-Signature=...` URL. If any `&` arrives as `&amp;`
>    (HTML-escaped) the S3 side answers
>    `403 <Code>SignatureDoesNotMatch</Code> ... <StringToSign>AWS4-HMAC-SHA256 ...`
>    — which reads like an expired/blocked URL and isn't. Use the DOM href (step 2) and the
>    browser download (step 3); both avoid the escaping entirely.
> 5. A `.apks`/`.xapk` is a ZIP of split APKs: `fr.vinted.apk` (base) + `config.arm64_v8a.apk` +
>    `config.xxhdpi.apk` + `manifest.json`. Analyze the **base** APK.

### When every mirror says "Just a moment..." — drive a real browser (verified 2026-10-01)

`apkpure.com`, `d.apkpure.net` and `www.apkmirror.com` all answer **403 + Cloudflare "Just a moment..."**
to plain `curl` *and* to headless Playwright. `apkcombo.com` serves the download page to a browser, so
use it as the primary when the mirrors block:

```bash
https://apkcombo.com/<app-name>/<package_id>/download/apk       # e.g. /vinted/fr.vinted/download/apk
```

Then **do not `curl` the URL you scrape out of the HTML** — two traps, in order:

1. The href is HTML-escaped, so it contains `&amp;`. Feeding that to curl yields
   `403 SignatureDoesNotMatch` from S3/R2 (`StringToSign` echoes back in the error body). Un-escaping
   by hand is fragile — instead read the **DOM property**, which the browser already normalised:
   ```python
   href = await pg.evaluate("""() => {
       const a=[...document.querySelectorAll('a')].find(e=>/r2\\?u=|cloudflarestorage/.test(e.href||''));
       return a ? a.href : null; }""")
   ```
2. Even with a correct signed URL, `ctx.request.get()` and `curl` still 403 — the link is bound to the
   browser session. **Let the browser download it** (`accept_downloads=True`):

   ```python
   async with pg.expect_download(timeout=900000) as dl_info:
       await pg.evaluate("(u)=>{const a=document.createElement('a');a.href=u;a.download='';"
                         "document.body.appendChild(a);a.click();}", href)
   dl = await dl_info.value
   await dl.save_as(str(OUT / "app.xapk"))
   ```

Real numbers from that run: Vinted `fr.vinted` 26.38.0 → 141 MB `.xapk` in ~4 min. The signed URL
carries `X-Amz-Expires=14400`, so re-scrape if you stall. A 3-6 KB "download" is an error page, not a
truncated APK — check `head -c 4` for `<?xm` / `PK` before believing the size.

### APKCombo returns XAPK, not APK

The 141 MB file is a zip: `fr.vinted.apk` (base, 129 MB) + `config.arm64_v8a.apk` + `config.xxhdpi.apk`
+ `manifest.json` + `APKComboInstaller.url`. Extract the base and analyse that:

```bash
python -c "import zipfile;z=zipfile.ZipFile('app.xapk');z.extract('fr.vinted.apk','extract')"
```

### Secondary: APKMirror search
```bash
curl -sk -A "Mozilla/5.0" "https://www.apkmirror.com/?post_type=app_release&searchtype=apk&s=<brand>" \
  | grep -oE 'href="[^"]+\.apk[^"]*"' | sort -u
```

### Tertiary: APKPure web search
```bash
curl -sk "https://apkpure.com/search?q=<brand>" | grep -oE 'data-dt-app="[^"]+"'
```

### VERIFIED 2026-10-01 — what actually works when the mirrors fight back

Real run (Vinted `fr.vinted`, 141 MB XAPK). Both `d.apkpure.net` and `www.apkmirror.com` answered
Cloudflare **"Just a moment..."** to curl *and* to a plain HTTP call from a browser context.
APKPure's *page* loaded; its download link did not.

**APKCombo is the reliable route.** Load the download page in Playwright, then read the href off the
DOM element (attribute regexes mangle the HTML entities and break the S3 signature):

```python
await page.goto("https://apkcombo.com/<slug>/<package>/download/apk")
href = await page.evaluate("""() => {
  const a=[...document.querySelectorAll('a')].find(e=>/r2\\?u=|cloudflarestorage/.test(e.href||''));
  return a ? a.href : null; }""")          # DOM .href — already entity-decoded and normalised
```

Then either let the browser download it, or `ctx.request.get(href)`:

```python
async with page.expect_download(timeout=900_000) as dl_info:
    await page.evaluate("(u)=>{const a=document.createElement('a');a.href=u;a.download='';"
                        "document.body.appendChild(a);a.click();}", href)
dl = await dl_info.value
await dl.save_as(str(out / "app.xapk"))    # suggested_filename: Vinted_26.38.0_apkcombo.com.xapk
```

Trap that cost two failed downloads: the href in the raw HTML contains `&amp;`. Strip the entity,
not just `unquote()` — otherwise S3 answers `SignatureDoesNotMatch` on every retry (the signature
covers the query string verbatim). Fetching the signed URL with curl fails for the same reason the
regex does; the DOM href is the only correct source.

### Manifest + secret work without jadx: androguard

`pip install androguard` (4.1.4) is enough for the Stage-2 triage when you only need the manifest and
a string sweep — no jadx install required, and it works on Windows.

```python
from loguru import logger; logger.remove()      # androguard is deafening at DEBUG
logging.disable(logging.DEBUG)
from androguard.core.apk import APK
a = APK(path)
a.get_package(); a.get_androidversion_name(); a.get_min_sdk_version()
a.get_attribute_value("application", "debuggable")      # None == absent == good
mani = a.get_android_manifest_xml()                     # lxml element
```

API trap: **`APK` has no `get_elements()`** (that is the aapt/`APK`-from-old-version idiom) — use
`get_android_manifest_xml()` and plain lxml `findall`, with the namespace prefix
`"{http://schemas.android.com/apk/res/android}"` on every attribute. Deep links live in
`mani.findall(".//data")` (`scheme`/`host`/`pathPrefix`) regardless of which component holds them.

Also: `XAPK` outer archive holds `fr.vinted.apk` + `config.<abi>.apk` + `config.<dpi>.apk` — analyse
the base APK; the splits only carry native libs and density assets.

### XAPK vs APK
- `.xapk` = a zip containing multiple split APKs (base + config.armeabi-v7a + config.en + etc.)
- Unzip outer first, then unzip the inner `base.apk` or `<package>.apk`
- Some apkpure downloads return truncated XAPK with missing EOCD signature — symptom of CDN rate-limiting; rotate IP and retry, OR use `7z x` which is more lenient than `unzip`

```bash
# Standard unzip (works for clean APK)
unzip -o <package>.apk -d extracted_<package>/

# For truncated/repaired XAPK
7z x -y <package>.apk -o"extracted_<package>"

# For nested XAPK
for inner in extracted_<package>/*.apk; do
  mkdir -p "extracted_<package>/$(basename "$inner" .apk)"
  unzip -o "$inner" -d "extracted_<package>/$(basename "$inner" .apk)"
done
```

### Fallback: APKCombo when APKPure / APKMirror are CF-gated

APKPure (`d.apkpure.net/b/APK/<pkg>?version=latest`) and APKMirror both answer a Cloudflare
"Just a moment..." interstitial to plain curl. The failure is easy to misread as success: you get a
file with an `Archive:` header, but it is ~5 KB of HTML. Symptoms of a bad fetch: `.apk` size in the
low kilobytes, body starting `<!DOCTYPE html>`, `file` reporting HTML rather than a zip.

Working path (verified 2026-10-01, `fr.vinted` 26.38.0, 141 MB):

1. In a real browser, `page.goto("https://apkcombo.com/<name>/<package>/download/apk")`.
2. Read the download link from the **DOM**, not from the raw HTML:
   `[...document.querySelectorAll('a')].find(e => /r2\?u=|cloudflarestorage/.test(e.href)).href`
   The attribute value in the HTML carries HTML entities (`&amp;`). Unescaping those by hand still
   yields `SignatureDoesNotMatch` from S3 — the signed query string must match byte-for-byte. The
   element's `.href` **property** is the browser-normalised URL and is the only form that works.
3. Trigger a real download and save it, rather than requesting the URL:
   `async with page.expect_download(timeout=900000) as d: await page.evaluate(... a.click())`.
4. The result is an **`.xapk`** (a zip): `<pkg>.apk` + `config.<abi>.apk` +
   `config.<density>.apk` + `manifest.json`. Analyse the base APK; the split APKs are only native
   libs and resources.

Do not paste the signed URL into a shell variable and curl it — that path was reproduced failing
twice before the browser download worked.

## Stage 2b — androguard 4.x: manifest + strings, no jadx needed

`pip install androguard` is pure Python (no JVM) and is enough for the highest-yield first pass.
Two API traps cost real time:

- `APK.get_elements()` **does not exist** in androguard 4.x — it raises
  `AttributeError: 'APK' object has no attribute 'get_elements'`. Use
  `a.get_android_manifest_xml()` and walk it with lxml:
  `mani.findall(".//application/activity")`, attributes namespaced
  `{http://schemas.android.com/apk/res/android}name`, and deep links from
  `mani.findall(".//data")` via the `android:scheme` / `android:host` attributes.
- androguard logs at DEBUG through **loguru**, which `logging.disable()` does NOT silence. Kill it
  with `from loguru import logger as _lg; _lg.remove()` before importing androguard, or one scan
  writes megabytes of `_do_next` / `getAttributeValue` noise across the real output.

What this pass yields, and how to read it:

- **Exported components** — report only with a real impact path. An app shipping
  `androidx.compose.ui.tooling.PreviewActivity`,
  `androidx.test.core.app.InstrumentationActivityInvoker$*`, a `FacebookContentProvider` or ad-SDK
  receivers is *hardening feedback*; most bounty programs explicitly exclude crashes/DoS from
  malformed URLs, anti-debug/obfuscation complaints and third-party-SDK issues. Name them as notes,
  not findings.
- **Secret sweep** — scan every `.dex` / `.json` / `.properties` / `.js` / `.xml` entry for Google
  keys (`AIza…`), `AKIA…`, JWTs (`eyJ.eyJ.`), `*.firebaseio.com`, Stripe/Slack tokens, plus every
  `https?://` literal. Roll the hosts up and split them into **in-scope vs out-of-scope before
  touching anything**: a mobile binary routinely names internal k8s services, sandbox hosts and
  sibling country domains that are absent from the engagement's scope list.
- **Four one-line config checks** worth quoting: `android:debuggable`,
  `android:usesCleartextTraffic`, `android:allowBackup`, and an insecure `networkSecurityConfig`.

Runnable implementation of all of the above: `scripts/analyze_apk_static.py`.

---

## Stage 2 — DEX decompilation (jadx)

> **No jadx installed?** You do not need it for a first pass. `scripts/analyze_apk.py` (bundled with
> this skill) does manifest + exported-component + deep-link + secret/endpoint extraction with
> `androguard` alone (`pip install androguard`). That was enough to clear an entire in-scope mobile
> app — no hardcoded secrets, no `debuggable`, no cleartext policy, no app-only endpoint — without
> decompiling DEX to Java. Reach for jadx only when you need to *read logic*.
>
> androguard 4.x API notes that cost time:
> - `APK.get_elements()` / `get_activities()`-style XML helpers were removed. Use
>   `APK.get_android_manifest_xml()` (lxml element) and query it yourself with
>   `findall(".//application/activity")` etc., against the android namespace
>   `{http://schemas.android.com/apk/res/android}`.
> - Scalar attributes still come from `APK.get_attribute_value("application", "debuggable")`
>   (also `allowBackup`, `networkSecurityConfig`, `usesCleartextTraffic`).
> - androguard logs through **loguru**, not `logging` — `logging.disable()` does nothing. Call
>   `loguru.logger.remove()` first or expect ~1.8 MB of DEBUG per run.
## Stage 2 — DEX decompilation (jadx)

### Zero-install alternative: androguard (pure Python) for manifest + string sweep
When you only need the manifest, exported components, deep links and a secret/host sweep — not
readable Java — `pip install androguard` (4.x) is enough and needs no JDK:

```python
from loguru import logger; logger.remove()      # androguard logs at DEBUG and floods stdout
from androguard.core.apk import APK
a = APK(path)
a.get_package(); a.get_androidversion_name(); a.get_min_sdk_version()
a.get_permissions(); a.get_attribute_value("application", "debuggable")
mani = a.get_android_manifest_xml()             # lxml Element
A = "{http://schemas.android.com/apk/res/android}"
for e in mani.findall(".//application/activity"):
    e.get(A + "name"), e.get(A + "exported"), e.get(A + "permission")
for d in mani.findall(".//data"):               # deep links live here
    d.get(A + "scheme"), d.get(A + "host"), d.get(A + "pathPrefix")
```

`APK.get_elements()` does **not** exist in 4.x — that AttributeError is the API change, so go
through `get_android_manifest_xml()`. Deep links are `<data android:scheme=...>` *under each
component*, so query `.//data` (the earlier miss was scoping the search to the intent-filter only).

For secrets, a plain `zipfile` sweep over `*.dex/*.json/*.properties/*.js/*.xml` with regexes for
`AIza`, `AKIA`, JWT, `*.firebaseio.com`, `(sk|pk)_live_`, `xox[baprs]-` plus a URL regex is fast and
finds hardcoded endpoints without any decompiler. Worked case + expected clean baseline:
`references/apkcombo-acquisition-and-androguard.md`.
## Stage 1b — No jadx? Manifest + secret sweep in pure Python (androguard)

`jadx` is not always installed and decompiling a 129 MB APK is minutes of JVM. For a first pass you
need only the manifest and the string table, and **androguard** does both in pure Python
(`pip install androguard`, 4.1.4 verified). Quarantine the two API traps first:

```python
from loguru import logger as _lg; _lg.remove()   # else androguard emits ~1.8 MB of DEBUG per run
import logging; logging.disable(logging.DEBUG)

from androguard.core.apk import APK as AGAPK
a = AGAPK(path)
A = "{http://schemas.android.com/apk/res/android}"
mani = a.get_android_manifest_xml()      # <-- NOT a.get_elements(), which does not exist in 4.x
```

`APK.get_elements()` is an androguard-3 API; on 4.x it raises
`AttributeError: 'APK' object has no attribute 'get_elements'`. Use the lxml element above and
`findall(".//application/activity")` etc. with the namespace constant.

What is worth extracting:

| Field | Call |
|---|---|
| package / version | `get_package()`, `get_androidversion_name()`, `get_androidversion_code()` |
| SDK gate | `get_min_sdk_version()`, `get_target_sdk_version()` |
| release hygiene | `get_attribute_value("application", "debuggable" / "allowBackup" / "usesCleartextTraffic" / "networkSecurityConfig")` |
| permissions | `get_permissions()` — filter for SMS/CONTACTS/LOCATION/QUERY_ALL_PACKAGES/REQUEST_INSTALL |
| exported components | heuristic below |
| deep links | `for f in comp.findall(".//data"): f.get(A+"scheme")` — a scheme with no `host` answers **any** host on that scheme; flag those explicitly |

Exported-component heuristic (mirrors platform behaviour, so it catches implicit export):

```python
for e in mani.findall(f".//application/{tag}"):                 # tag in activity|service|receiver|provider
    exp, perm = e.get(A + "exported"), e.get(A + "permission")
    has_filter = bool(e.findall(".//intent-filter"))
    if exp == "true" or (exp is None and tag in ("activity", "receiver") and has_filter and not perm):
        report(e.get(A + "name"), perm, exp == "true")
```

Then sweep DEX/resources **without decompiling** — regex the raw bytes of every `.dex`/`.json`/
`.properties`/`.js` inside the zip:

```python
pats = {"google_key": rb"AIza[0-9A-Za-z_\-]{35}", "aws_key": rb"AKIA[0-9A-Z]{16}",
        "jwt": rb"eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}",
        "firebase": rb"[a-z0-9-]+\.(?:firebaseio|firebaseapp)\.com",
        "stripe": rb"(?:sk|pk)_(?:live|test)_[0-9A-Za-z]{16,}",
        "url": rb"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-]{6,120}"}
```

Group the `url` hits by host: the interesting output is the **split between in-scope hosts and
unlisted internal ones**. On the Vinted app that pulled 283 distinct hosts including `flags.svc.*`,
`metrics-ingress*.svc.*`, `logs-ingress*`, `*-sandbox` variants and an internal k8s ingress — every one
**out of scope** (unlisted subdomain) and therefore documented, not tested. Say that explicitly in the
report; it reads as discipline, not as a gap.

**Two expectations to set before reading results.** (1) A well-built app yields *no* hardcoded secrets
and no `debuggable` — that is the normal outcome, not a failed run; report it as a clean result.
(2) The output layer redacts matched secrets (you will see `AIzaSy...thAc`, `pk.***`) — that is
success, not truncation. Record the **classification** ("Google Maps API key + Mapbox public token
exposed in page config") and never the value.

## Stage 2 — DEX decompilation (jadx)

```bash
# Install
brew install jadx          # macOS
# or
wget https://github.com/skylot/jadx/releases/latest/download/jadx-1.5.x.zip
```
# Decompile
jadx -d decompiled_<package>/ <package>.apk

# For XAPK that contains multiple APKs
for inner in extracted_<package>/*.apk; do
  jadx -d decompiled_<package>_$(basename "$inner" .apk)/ "$inner"
done
```

### No jadx? androguard gives you 80% with zero install fuss (verified 2026-10-01)

`pip install androguard` (4.1.4, pure Python) is enough for manifest + string sweeps on a 129 MB APK
in ~90 s. Two API traps that cost time:

- **`APK` has no `get_elements()` in 4.x.** Use `a.get_android_manifest_xml()` to get an lxml
  Element, then `mani.findall(".//application/activity")` with the android namespace bound
  explicitly: `A="{http://schemas.android.com/apk/res/android}"`, `e.get(A+"name")`.
  Note that a bare `"{"+...+"}name"` in source is a Python syntax error — build the prefix into a variable.
- **androguard floods the log with per-attribute DEBUG lines** — a 2 MB log that buries your results.
  Kill it at the top of the script:
  ```python
  try:
      from loguru import logger as _lg; _lg.remove()
  except Exception: pass
  import logging; logging.disable(logging.DEBUG)
  ```
- Manifest-only attributes such as `a.get_attribute_value("application","debuggable")` return `None`
  when the attribute is **absent**, which is the secure case — absence is not an error.

String sweep without decompiling: `zipfile.ZipFile(apk).read()` every `.dex` / `.json` /
`.properties` / `.js` and regex for `AIza[0-9A-Za-z_-]{35}`, `AKIA[0-9A-Z]{16}`, JWTs, Firebase
hosts, Stripe/Slack keys, plus `https?://...` → collect the distinct host set (283 hosts for
Vinted). Result on Vinted 26.38.0: **no hardcoded secrets, `debuggable` absent, no cleartext
policy** — i.e. a clean negative is the normal outcome on a mature app, so script the whole sweep
rather than grepping by hand.

For a fast "strings only" pass without full decompilation:
```bash
find extracted_<package> -name "classes*.dex" -exec strings -8 {} \; > strings_<package>.txt
```

---

## Stage 3 — Secret grep (the 60-pattern catalog)

```bash
# URL grep — owned-domain references
grep -oE 'https?://[a-zA-Z0-9.-]+\.(target1|target2|target3)\.(com|io|net|in)[a-zA-Z0-9./_?=&%-]*' strings_<package>.txt | sort -u

# Internal IP / port URLs
grep -oE 'https?://(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.|127\.)[0-9.]+(:[0-9]+)?[a-zA-Z0-9./_?=&-]*' strings_<package>.txt

# Cloud credentials
grep -oE 'AKIA[A-Z0-9]{16}'                            # AWS Access Key
grep -oE 'aws_secret_access_key[\s:=]+[A-Za-z0-9/+=]{40}' # AWS Secret
grep -oE 'AIza[A-Za-z0-9_-]{35}'                       # Google API key
grep -oE 'ya29\.[A-Za-z0-9_-]+'                        # Google OAuth refresh token
grep -oE 'gh[ps]_[A-Za-z0-9]{36}'                      # GitHub PAT
grep -oE 'glpat-[A-Za-z0-9_-]{20}'                     # GitLab PAT
grep -oE 'xox[pbar]-[A-Za-z0-9-]+'                     # Slack token
grep -oE 'sk-[A-Za-z0-9]{48}'                          # OpenAI API key
grep -oE 'sk-ant-[A-Za-z0-9_-]{90,}'                   # Anthropic API key
grep -oE 'AC[a-f0-9]{32}'                              # Twilio Account SID
grep -oE 'sk_live_[A-Za-z0-9]{24}'                     # Stripe live key
grep -oE 'pk_live_[A-Za-z0-9]{24}'                     # Stripe publishable
grep -oE 'mailgun-[A-Za-z0-9-]{40}'                    # Mailgun
grep -oE 'SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}'    # SendGrid

# JWT (any algorithm)
grep -oE 'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*' strings_<package>.txt

# Firebase
grep -oE '"(api_key|project_id|database_url|storage_bucket|client_id|mobilesdk_app_id|google_app_id|gcm_defaultSenderId)"\s*:\s*"[^"]+"' \
  extracted_<package>/res/values/strings.xml \
  extracted_<package>/google-services.json \
  decompiled_<package>/resources/AndroidManifest.xml 2>/dev/null

# OAuth client secrets
grep -oE 'client_secret["\s:=]+[A-Za-z0-9_-]{24,}' strings_<package>.txt

# Hardcoded passwords (heuristic — many false positives, manual review)
grep -oE '"password"\s*:\s*"[^"]+"|password\s*=\s*"[^"]+"' decompiled_<package>/sources/**/*.java 2>/dev/null
```

### Real-world example finding (anonymized — from an authorized engagement)
```
# Customer-facing APK shipped a hardcoded URL of this shape:
https://api.<client>.example/<path-token>/<resource-token>?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.<payload>.<sig>

# Decoded JWT payload: {"sid":<int>,"iat":<unix-ts>,"exp":<unix-ts>}
# Expired ~8 years earlier — but path tokens + 30 /v1/* endpoints still useful intel
```

---

## Stage 4 — Pinned certificate extraction

```bash
# Find .cer / .der / .pem files in assets/
find extracted_<package>/assets -iname "*.cer" -o -iname "*.der" -o -iname "*.pem" -o -iname "*.crt" 2>/dev/null

# Or in network_security_config.xml
find extracted_<package> -name "network_security_config.xml" -exec cat {} \;

# For each cert, extract subject + SAN (might reveal new internal API hosts)
for cert in $(find extracted_<package>/assets -iname "*.cer"); do
  echo "=== $cert ==="
  openssl x509 -in "$cert" -noout -subject -issuer -dates 2>/dev/null
  openssl x509 -in "$cert" -noout -text 2>/dev/null | grep -E 'Subject:|DNS:|Issuer:|Validity'
done
```

### Real-world example
A customer-facing APK from an authorized engagement contained `assets/api_<service>_<domain>_com.cer` — revealed the existence of an `api.<service>.<domain>.example` asset that had NOT surfaced in passive recon.

---

## Stage 5 — Exported component enumeration

AndroidManifest.xml lists components. Exported ones (especially with `android:exported="true"` or implicit-export via intent-filter) can be triggered by other apps — potential intent-injection attack surface.

```bash
# Decode binary AndroidManifest if needed
apktool d <package>.apk -o decoded_<package>/    # apktool decodes binary manifest

# Or read directly from jadx output
cat decompiled_<package>/resources/AndroidManifest.xml | grep -E '<(activity|service|receiver|provider)' | head -50

# Filter exported
grep -E 'android:exported="true"' decompiled_<package>/resources/AndroidManifest.xml
```

For each exported component, check:
- Does it accept extras that flow into a WebView (intent → WebView → XSS / file://)
- Does it accept URI extras (potential SSRF via deep link)
- Does it pass extras to other Activities (intent redirection)

---

## Stage 6 — Firebase / cloud-service config inspection

```bash
# google-services.json — full Firebase config
find extracted_<package> -name "google-services.json" -exec cat {} \; | python3 -m json.tool

# Look for:
#   project_id   → can guess Firestore / RTDB URL: https://<project_id>.firebaseio.com/.json
#   storage_bucket → can guess GCS bucket: gs://<bucket>
#   web_api_key  → can use to enumerate Firebase tenant config

# Test if Firestore is publicly readable
curl -s "https://firestore.googleapis.com/v1/projects/<project_id>/databases/(default)/documents/users"

# Test if Realtime DB is publicly readable
curl -s "https://<project_id>.firebaseio.com/.json"

# Test if Storage Bucket is publicly listable
curl -s "https://firebasestorage.googleapis.com/v0/b/<bucket>/o"
```

---

## Stage 7 — Runtime instrumentation (Frida)

For when static analysis isn't enough — you want to dump tokens at runtime, bypass cert pinning, or trace API calls.

### Setup
```bash
pip install --break-system-packages frida-tools objection
adb devices  # ensure device/emulator connected
# Push frida-server to device (root required, or use rooted emulator like Genymotion / x86_64 AVD)
```

### Cert-pinning bypass (universal)
```javascript
// frida-script-pinning-bypass.js
Java.perform(function() {
    // OkHttp
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {
            console.log('[+] OkHttp pinning bypassed for: ' + arguments[0]);
            return;
        };
    } catch (e) {}
    // HttpsURLConnection
    try {
        var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
        TrustManagerImpl.verifyChain.implementation = function(chain) {
            console.log('[+] TrustManagerImpl verifyChain bypassed');
            return chain;
        };
    } catch (e) {}
});
```
```bash
frida -U -l frida-script-pinning-bypass.js -f <package_id> --no-pause
```

### Hook HTTP requests
```javascript
Java.perform(function() {
    var OkHttpClient = Java.use('okhttp3.OkHttpClient');
    var Request = Java.use('okhttp3.Request');
    var Call = Java.use('okhttp3.Call');
    
    OkHttpClient.newCall.implementation = function(req) {
        var url = req.url().toString();
        var headers = req.headers().toString();
        console.log('[REQ] ' + url);
        console.log('[HDRS] ' + headers);
        return this.newCall(req);
    };
});
```

### Quick token extraction via objection
```bash
objection --gadget com.target.app explore
# Inside:
android hooking watch class_method <class>.<method> --dump-args --dump-return
```

---

## Stage 8 — Network traffic capture (via mitmproxy)

For deeper API discovery once pinning is bypassed.

```bash
# Run mitmproxy on host
mitmproxy --listen-port 8080

# Configure Android device proxy to host:8080
# Install mitmproxy CA cert on device:
#   - Pull from http://mitm.it on the device, or
#   - Push to /system/etc/security/cacerts/ on rooted device

# Use the Frida pinning bypass script while traffic flows through mitmproxy
# All API calls visible in mitmproxy UI
```

---

## Decision tree — what to do with what you find

| Finding | Next move |
|---|---|
| Active JWT (not expired) | Test against the API host — does it grant access? Try sid manipulation |
| Expired JWT | Inspect path tokens / API endpoint structure — useful intel for post-VPN |
| AWS access key | Use `awscli` to test: `aws sts get-caller-identity` — many leaked keys still have permissions |
| Firebase project_id + web_api_key | Test public Firestore/RTDB/Storage read |
| Google API key (AIza*) | Test against `https://www.googleapis.com/customsearch/v1` etc. — see what API the key activates |
| Hardcoded HTTP URLs (http://) | Possible MITM via downgrade if cert pinning is missing |
| Pinned cert for internal host | New asset discovery — that host is real |
| Exported Activity with WebView | Test intent-injection → URL-loading abuse |
| Stack-trace artifacts (Stack Overflow URLs) | Identify the developer's questions → infer architecture |
| Hardcoded credentials | Spray immediately (respect any caps from related skills) |

---

## Anti-patterns

- **Don't grep only for "password"** — most secrets have specific high-signal patterns (AKIA, AIza, eyJ, etc.). Generic word grep produces too much noise.
- **Don't skip XAPK split APKs** — config.armeabi splits and config.<lang> splits sometimes contain different code paths.
- **Don't trust expired JWTs as "dead intel"** — the path structure, endpoint list, and signing algorithm are still useful. The 8-year-expired-JWT example above shows this.
- **Don't reverse only the latest version** — older APK versions (via APKMirror version history) sometimes have secrets removed in newer versions but still active server-side.
- **Don't ignore Firebase even if app looks "simple"** — Firebase rules misconfigurations (public read on Firestore) are extremely common.
- **Don't run Frida on a production device** — use rooted emulator or test device only.

---

## Tooling install (one-time)

```bash
brew install jadx p7zip
pip install --break-system-packages frida-tools objection
# Genymotion or AVD for rooted Android emulator
```

For APK download convenience, can add a `download-apk` shell function:
```bash
download-apk() {
  local pkg="$1"
  curl -sk -L --max-time 60 "https://d.apkpure.net/b/APK/$pkg?version=latest" -o "$pkg.apk"
  echo "Downloaded $(wc -c < "$pkg.apk") bytes"
  file "$pkg.apk"
}
```

---

## Bridge to neighboring skills

- `offensive-osint` — Play Store / APKMirror enum is part of broader OSINT
- `hunt-cloud-misconfig` — Firebase public-read is exactly this skill's specialty post-discovery
- `hunt-api-misconfig` — JWT manipulation once you have the algorithm + sample token
- `evidence-hygiene` — extracted secrets need redaction before report inclusion
- `redteam-mindset` — APK reverse on day-1 of an engagement, not as an afterthought

---

## Real-world finding template (anonymized — authorized engagement)

**Finding: Hardcoded JWT + 30+ Internal API Endpoints in a customer-facing APK**

- Subject: Hardcoded artifacts in legacy mobile build reveal internal API surface
- Observations: Decompilation of `com.<client>.<app>` revealed embedded JWT (expired ~8 years earlier) and 30+ `/v1/*` endpoint paths against `api2.<client>.example` (internal-only externally)
- Description: APK ships with developer build artifacts. Path tokens are security-by-obscurity; API endpoint inventory is reconnaissance-grade.
- Impact: Post-VPN-foothold (via cred compromise), attacker has full API surface map without binary reverse. HS256 secret recovery (via SSRF/LFI) would yield arbitrary token forging.
- Recommendation: rotate HS256 secret, migrate to RS256, remove hardcoded URLs from builds, audit all org APKs.
- Evidence: extracted strings, decoded JWT, endpoint inventory

---

## Related Skills & Chains

- **`cloud-iam-deep`** — APK secret extraction frequently yields live AWS/GCP/Azure credentials. Chain primitive: jadx string-grep produces AWS Access Key ID + Secret → `cloud-iam-deep` `aws sts get-caller-identity` → role/policy enumeration → IAM privilege-escalation path (one of 24 documented AWS escalation patterns) → cloud-plane takeover. Same flow applies to GCP service-account JSON and Azure shared-access-signature tokens extracted from APK resources.
- **`hunt-api-misconfig`** — APK endpoint inventory hands you the API surface for free; mass-assignment, JWT, and CORS bugs are typical. Chain primitive: APK reveals `/v1/users/me` and `/v1/admin/users` → `hunt-api-misconfig` mass-assignment probes (`{is_admin:true}`) against `/v1/users/me` → admin role escalation → access to `/v1/admin/users`.
- **`hunt-rce`** — Hardcoded JWT signing secrets (HS256) extracted from APK enable arbitrary token forging. Chain primitive: APK strings yield HS256 secret → forge admin token → access admin API → if API has eval/template/sink → `hunt-rce` to server. Also: exported components with intent-injection sinks can reach `Runtime.exec` if app is local-installed.
- **`offensive-osint`** — APK is one node in the broader org recon graph; pair with breach corpora and cert transparency. Chain primitive: APK reveals internal API hostname `api2.example.com` → `offensive-osint` certificate-transparency lookup → discover sibling subdomains → expanded attack surface.
- **`redteam-report-template`** — APK findings need clear "what the binary leaks" framing because client engineers often dismiss mobile-static findings as "obfuscation problem." Chain primitive: validated finding (token/URL/secret extracted) → `triage-validation` 7-Question Gate (specifically: "does this credential still authenticate today?") → `redteam-report-template` packaging with explicit binary version + extraction reproduction steps.