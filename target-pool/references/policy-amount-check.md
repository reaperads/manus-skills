# Policy deep-check: reward amounts + real scope

Goal: sebelum propose target, pastikan (a) program MEMANG bayar dan (b) domain pool ADA di
scope program. `policy_url` di pool hampir selalu bukan halaman yang berisi keduanya.

## Generic recipe

1. **Resolve shortlink** — pool sering simpan `ya.cc/…`, `bit.ly/…`, dst.
   `curl -sL -A "Mozilla/5.0" -w '\n[[%{http_code} -> %{url_effective}]]' <url>`
   → catat final URL (di sini ketahuan path bener: `/bugbounty/i/rules`, bukan `/bugbounty/rules`).
2. **Baca halaman rules** → strip tag, cari keyword `наград|reward|вознаграж|приз|сумм|$|€|₽`.
   Rules page biasanya HANYA syarat (duplikat, 90 hari embargo, disclaimer) — **tanpa angka**.
3. **Cari dokumen yang megang duitnya**:
   - terms/legal page (`Положение о конкурсе`, p.9.2) biasanya *mendelegasikan* nominal ke
     halaman site tertentu → ikuti link-nya.
   - nav halaman utama: `Победителям`, `Вопросы про Охоту` (FAQ), `Hall of Fame`.
4. **Halaman utama sering SPA/JS-rendered** → teks reward TIDAK ada di HTML. Jangan nyerah:
   ambil semua `href` dari halaman utama, itu daftar sub-halaman program
   (`/i/main-scope`, `/i/browser`, `/i/mobile`, `/i/cloud`, …). Fetch satu-satu, cari tabel
   reward (`{ Rewards }` / `{ Вознаграждения }`).
   Cara cepat: `re.findall(r'href="([^"]+)"', html)` lalu filter path `/i/`.
5. **Scope check**: di halaman yang sama biasanya ada daftar domain in-scope
   (`*.yandex.ru`, `*.kinopoisk.ru`, …). Cocokkan domain pool. Kalau tidak ada →
   flag: domain pool kemungkinan mirror/locale, garap apex/canonical yang in-scope.
6. **Ambil juga payment terms** (FAQ): mata uang, tax, jadwal payout, dokumen wajib,
   e-wallet yang didukung/tidak.

## Worked example: Yandex (pool entry `yandex.fr`)

- `policy_url` pool = `https://ya.cc/t/1cSZixjB3gkSva`
  → 200, final `https://yandex.ru/bugbounty/i/rules` (`/bugbounty/rules` = **404**).
- `/i/rules` = syarat saja, **0 angka**. Ketemu clue di footer: `Положение о конкурсе`.
- terms `yandex.ru/legal/yandex_bug_bounty_terms_conditions/?lang=ru` p.9.2:
  "размер … установлен в разделе «Рамки программы и размеры вознаграждений» на Сайте
  по адресу https://yandex.ru/bugbounty" + bisa diubah **quarterly**.
- `yandex.ru/bugbounty/` SPA → HTML kosong dari angka. `href` harvest → sub-program pages.
- **Reward table**: `https://yandex.ru/bugbounty/i/main-scope` (₽) /
  `https://yandex.com/bugbounty/i/main-scope` ($):

  | Vulnerability | Auth | Key | Main | New |
  |---|---|---|---|---|
  | RCE | 3,000,000₽ / 36,000$ | 1,200,000 / 13,300 | 750,000 / 8,300 | 450,000 / 5,000 |
  | ATO (zero-click, 2FA) | 3,000,000 / 36,000 | — | — | 51,337 / 1,100 |
  | LFR/RFI/XXE, SQLi | 1,000,000 / 12,000 | 600,000 / 6,700 | 375,000 / 4,100 | 150,000 / 1,700 |
  | SSRF non-blind | 600,000 / 6,700 | 300,000 / 3,300 | 225,000 / 2,500 | 150,000 / 1,700 |
  | Blind SSRF | 200,000 / 2,200 | 150,000 / 1,600 | 115,000 / 1,200 | 45,000 / 500 |
  | IDOR / sensitive data | 225–550k / 2,500–6,100 | 75–500k / 800–2,100 | 45–120k / 500–1,300 | 24–45k / 200–500 |
  | CSRF | 30–187k / 300–2,100 | 30–75k / 300–800 | 30–45k / 300–500 | 15–30k / 100–300 |
  | XSS (no self-XSS) | 31–240k / 300–2,700 | 31–120k / 300–1,300 | 30–75k / 300–800 | 10–45k / 100–500 |

  ATO variants: SMS-only login 1,000,000₽ / butuh 2 klik 500,000₽ / service baru 51,337₽.
  Angka = **maksimum**, bisa naik (special case) / turun (compensating control, report jelek).

- Payment (FAQ `yandex.ru/bugbounty/i/blog/faq` + `yandex.com/support/bugbounty/ru/`):
  transfer bank tgl 13–15 bulanan, ≤3 bulan dari evaluasi, Yandex = tax agent 13% NDFL,
  non-resident dibayar **USD** kurs CB RF, **tanpa PayPal/e-wallet**, dokumen ≤10 hari.
- Scope (`/i/main-scope`): `*.yandex.ru/.com/.com.tr/.kz/.by/.st/.net`, `*.ya.ru`,
  `*.yandex-bank.net`, `*.kinopoisk.ru`, `*.auto.ru`, `*.edadeal.ru`, `*.bookmate.ru`,
  `*.band.link` + IP ASN Yandex. **`*.yandex.fr` TIDAK ada** → pool entry = mirror locale;
  garap `*.yandex.com`.
- AI/LLM rule khusus (`/i/rules` + `/i/llms.txt`): report wajib ringkas + PoC/video +
  reproduce sendiri; mass auto-report = blokir sementara. Untuk testing: baca `/llms.txt`
  dulu — kalau tidak bisa diakses, testing tidak authorized.

## Gotcha yang dipetakan sesi ini

- `pool.py` tidak punya sort-by-date → query "terbaru" = python inline (lihat SKILL.md).
- `web_extract` di env ini cuma search-backend (ddg) → **tidak bisa extract URL**; pakai
  `curl` (bukan browse) untuk halaman statis; browser hanya untuk SPA yang butuh render.
- `pool.json` struktur = `{count, by_category, by_source, merge_events, domains:{domain:rec}}`
  — list-nya `p["domains"].values()`, bukan root list.
