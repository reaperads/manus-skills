---
name: gate-pipeline-end-to-end
description: Gate Pipeline End-to-End: Recon → Threat Modeling → Hipotesis → Validasi
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Gate Pipeline End-to-End: Recon → Threat Modeling → Hipotesis → Validasi

Dokumen ini menyambung ke `gate-rule-validasi-hipotesis.md` (gate di tahap validasi). Prinsip dasarnya sama: **tiap tahap punya gate eksplisit, dan tidak boleh lanjut ke tahap berikutnya kalau gate belum lolos** — kecuali dicatat sebagai gap eksplisit yang dibawa ke tahap berikutnya sebagai catatan risiko, bukan diabaikan diam-diam.

Alasan kenapa ini penting: hipotesis yang generic/dangkal hampir selalu lahir dari recon/threat-model yang generic/dangkal. Gate di validasi doang cuma nyaring di ujung — gate di tiap tahap nyaring dari akar, sehingga hipotesis yang sampai ke validasi punya dasar lebih kuat dan potensi CONFIRMED lebih besar.

---

## Tahap 1: Recon

**Tujuan gate:** pastikan attack surface benar-benar ter-mapping, bukan cuma yang kelihatan di permukaan.

### Checklist wajib sebelum lanjut
1. **Entry point enumeration** — semua titik masuk (API endpoint, contract function/event, admin panel, webhook, third-party integration) sudah didaftar, bukan cuma yang "kelihatan jelas".
2. **Trust boundary mapping** — titik-titik di mana data/kontrol berpindah dari domain tidak-dipercaya ke domain dipercaya sudah diidentifikasi (contoh: user input → backend, off-chain → on-chain, contract A → contract B, frontend → smart contract).
3. **Dependency/version inventory** — library, framework, dan versi kontrak/protokol yang dipakai sudah dicatat (buat cross-check known-CVE pattern).
4. **Data flow sketch** — minimal garis besar bagaimana data mengalir antar komponen (siapa yang trust siapa, dan atas dasar apa).

### Gate
- ❌ **Tidak boleh** lanjut ke threat modeling kalau checklist di atas belum lengkap.
- Kalau terpaksa lanjut karena keterbatasan (rate limit, akses terbatas, dokumentasi kurang), wajib ditandai:
  ```
  RECON GAP: <bagian mana yang belum ke-cover, dan kenapa>
  ```
  Gap ini **wajib dibawa** sebagai catatan risiko eksplisit ke tahap threat modeling — bukan hilang begitu saja.

---

## Tahap 2: Threat Modeling

**Tujuan gate:** paksa threat spesifik dan grounded ke hasil recon, bukan template generic ("mungkin ada injection", "mungkin ada IDOR").

### Elemen wajib per threat (4 elemen, semua harus diisi konkret)
1. **Attacker capability** — apa persis yang bisa dikontrol attacker? (input tertentu? timing? akun lain? akses ke kontrak lain?)
2. **Trust boundary yang dilanggar** — merujuk langsung ke trust boundary spesifik dari hasil recon tahap 1, bukan boundary generik.
3. **Asumsi yang mau dipatahkan** — developer/protokol berasumsi apa, dan threat ini mau membuktikan asumsi itu salah di kondisi apa.
4. **Expected observable effect** — kalau threat ini berhasil, apa yang akan terlihat/terukur? (state berubah? fund berpindah? akses tidak sah? data bocor?)

### Gate
- ❌ Threat yang tidak bisa mengisi ke-4 elemen secara konkret → **ditolak**, tidak boleh naik jadi kandidat hipotesis.
- ❌ Threat yang cuma menyalin nama kelas vuln generik tanpa mengaitkan ke elemen recon spesifik → ditolak, suruh diformulasikan ulang.
- Threat yang lolos gate ini yang boleh diteruskan ke tahap hipotesis.

---

## Tahap 3: Hipotesis

**Tujuan gate:** hipotesis harus falsifiable, spesifik, dan bisa diuji dengan langkah konkret — bukan sekadar dugaan kelas vuln.

### Format wajib
```
Jika [actor] melakukan [aksi konkret]
pada [target spesifik — fungsi/endpoint/kontrak tertentu, bukan "sistem"],
maka [expected effect terukur] akan terjadi,
yang melanggar [asumsi/invariant tertentu dari tahap threat modeling].
```

### Gate
1. **Gate spesifisitas** — hipotesis harus bisa diuji dengan langkah eksekusi konkret. Kalau isinya masih "perlu dicek lebih lanjut apakah ini vulnerable", itu belum hipotesis, itu masih threat — kembalikan ke tahap 2.
2. **Gate keterkaitan (novelty ringan)** — hipotesis harus eksplisit mengaitkan diri ke elemen dari threat model (attacker capability + trust boundary + asumsi yang mau dipatahkan). Hipotesis yang cuma pattern-matching nama kelas vuln tanpa kaitan konkret ke target → ditolak, generate ulang.
3. **Gate testability** — harus ada minimal 1 langkah eksekusi awal yang jelas ("apa hal pertama yang dicoba untuk menguji ini") sebelum hipotesis ini boleh masuk ke antrian validasi.

Hipotesis yang lolos ketiga gate ini yang lanjut ke tahap validasi (lihat `gate-rule-validasi-hipotesis.md`).

---

## Tahap 4: Validasi

Lihat dokumen terpisah: **`gate-rule-validasi-hipotesis.md`**

Ringkasan koneksinya ke pipeline ini:
- Ladder validasi (gate 1 di dokumen validasi) sekarang punya input yang lebih kuat karena hipotesis yang masuk sudah lolos gate spesifisitas & keterkaitan.
- `RECON GAP` yang dicatat di tahap 1 tetap relevan di sini — kalau ada gap recon yang berkaitan langsung dengan hipotesis yang sedang divalidasi, itu jadi salah satu alasan sah untuk verdict `INCONCLUSIVE` (bukan `FALSIFIED`), sesuai gate 6 di dokumen validasi (root-cause kegagalan reproduce).

---

## Ringkasan Alur Gate (satu baris per tahap)

| Tahap | Yang divalidasi sebelum lanjut | Konsekuensi gagal gate |
|---|---|---|
| Recon | Coverage entry point, trust boundary, dependency | Tandai `RECON GAP`, bawa sebagai risiko ke tahap berikutnya |
| Threat Modeling | 4 elemen konkret per threat | Threat ditolak, tidak naik jadi hipotesis |
| Hipotesis | Spesifisitas, keterkaitan, testability | Hipotesis dikembalikan/di-generate ulang |
| Validasi | 7 gate anti-premature-falsification | Verdict turun ke `INCONCLUSIVE`, bukan `FALSIFIED` |

**Prinsip inti yang menyatukan semua tahap:** setiap kali ada ambiguitas atau gap, default-nya adalah **"tandai gap eksplisit dan bawa ke tahap berikutnya"** — bukan diam-diam diabaikan, dan bukan dipaksa jadi kesimpulan biner (lolos/gagal) padahal buktinya belum cukup.