---
name: gate-rule-validasi-hipotesis
description: Gate Rule: Validasi Hipotesis — Anti Premature Falsification
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Gate Rule: Validasi Hipotesis — Anti Premature Falsification

## Prinsip Dasar

1. **Beban pembuktian setara di dua sisi.** Menyimpulkan FALSIFIED sama beratnya dengan menyimpulkan CONFIRMED — keduanya klaim yang butuh bukti, bukan default.
2. **Default saat ragu = INCONCLUSIVE**, bukan FALSIFIED. Agent tidak boleh memaksa diri memilih biner kalau bukti belum cukup.
3. **FALSIFIED harus "dimenangkan" dengan bukti eksekusi**, bukan muncul karena reproduce gagal atau resource/tooling terbatas.

---

## Status yang Diizinkan (hanya 3, tidak boleh dua)

| Status | Syarat |
|---|---|
| `CONFIRMED` | Lolos semua gate positif (di skill lo yang sudah ada) |
| `FALSIFIED` | Lolos semua gate di bawah ini |
| `INCONCLUSIVE` | Salah satu gate FALSIFIED tidak terpenuhi |

---

## Gate Wajib Sebelum Boleh Menyimpulkan FALSIFIED

Agent **wajib** menjawab checklist ini eksplisit di output sebelum boleh menulis verdict FALSIFIED. Kalau satu saja gagal → verdict otomatis turun jadi `INCONCLUSIVE`.

1. **Ladder tuntas** — semua tahap validasi (recon → threat model → hipotesis → validasi, atau ladder 7-tahap kalau ada) sudah dijalani. Tahap yang di-skip wajib ditandai `SKIPPED: <alasan>`, dan itu otomatis menggagalkan gate ini.
2. **Multi-variasi test** — minimal 3 variasi kondisi/input berbeda dicoba (bukan 1 percobaan tunggal) sebelum menyerah.
3. **Steelman wajib** — sebelum menulis alasan reject, agent harus menulis dulu skenario serangan terkuat yang mungkin (asumsikan jadi attacker paling pintar), baru jelaskan kenapa skenario itu gagal. Kalau agent tidak bisa mengartikulasikan steelman yang konkret, itu sinyal dia belum paham kasusnya — verdict wajib `INCONCLUSIVE`.
4. **Bukti mitigasi konkret** — kalau alasan reject "ada proteksi X" (rate limit, auth check, validasi, dll), wajib ada bukti dari **eksekusi nyata** bahwa proteksi itu benar-benar blokir, bukan cuma dari baca kode. Plus minimal 1 percobaan bypass terhadap proteksi tersebut.
5. **Evidence tier eksplisit** — tandai apakah kesimpulan berbasis:
   - `Observed` = dieksekusi langsung, ada hasil konkret
   - `Prepared` = cuma dari baca kode / simulasi / asumsi, belum dieksekusi
   
   Verdict FALSIFIED final **hanya boleh** dari evidence tier `Observed`. Kalau cuma `Prepared` → wajib `INCONCLUSIVE`.
6. **Klasifikasi root-cause kegagalan reproduce** — kalau reproduce gagal, wajib diklasifikasi ke salah satu:
   - (a) Gagal karena vulnerability memang tidak ada → boleh lanjut ke FALSIFIED
   - (b) Gagal karena keterbatasan tooling/resource/akses (network block, RAM/fork limit, rate limit test env, dll) → **wajib** `INCONCLUSIVE`
   - (c) Gagal karena environment test beda dari target real (fork vs mainnet, testnet vs production) → **wajib** `INCONCLUSIVE`
7. **Independent re-check (cross-framing)** — jalankan ulang reasoning dengan framing berlawanan: sekali dengan instruksi "coba cari cara break ini", sekali dengan "asumsikan ini vulnerable, buktikan kenapa salah". Kalau hasil dua framing itu tidak konsisten → `INCONCLUSIVE`, tandai untuk review manual.

---

## Larangan Eksplisit

- ❌ Menyimpulkan FALSIFIED hanya dari 1 observasi / 1 percobaan.
- ❌ Menyamakan "tidak berhasil reproduce" dengan "terbukti tidak vulnerable" tanpa klasifikasi root-cause (gate 6).
- ❌ Berhenti di tahap awal ladder validasi tanpa alasan eksplisit yang dicatat.
- ❌ Pakai bahasa hedging sebagai verdict final ("kemungkinan besar aman", "sepertinya sudah dimitigasi") — verdict harus didukung bukti eksekusi, bukan estimasi kualitatif.

---

## Format Output Wajib per Verdict

```
Verdict: CONFIRMED / FALSIFIED / INCONCLUSIVE
Evidence tier: Observed / Prepared
Steelman scenario: <2-3 kalimat skenario serangan terkuat yang dipertimbangkan>
Counter-evidence: <bukti konkret yang menggagalkan skenario, kalau reject>
Gate checklist: [pass/fail per poin 1-7 di atas, dengan alasan singkat tiap poin]
Root-cause (kalau reproduce gagal): (a)/(b)/(c) — lihat gate 6
Next step (kalau INCONCLUSIVE): <rekomendasi konkret apa yang perlu dicek manual atau di-retry>
```

---

## Rule Tambahan Khusus (karena validasi dilakukan otonom tanpa arahan manual)

Karena agent bekerja full otonom dan operator tidak punya basic security untuk sanity-check independen:

- Kalau verdict `INCONCLUSIVE`, agent **wajib** menyertakan ringkasan awam: apa yang sudah dicoba, kenapa belum bisa disimpulkan, dan langkah manual konkret apa yang bisa dilakukan operator (command spesifik, endpoint yang perlu dicek, dll) — bukan cuma "butuh investigasi lebih lanjut".
- Kalau verdict `CONFIRMED`, sebelum lanjut ke tahap report generation, agent **wajib** menampilkan checklist evidence lengkap ke operator dalam bentuk yang bisa di-review manual (bukan langsung auto-generate report), supaya ada satu titik jeda untuk sanity-check sebelum submit ke program bug bounty.