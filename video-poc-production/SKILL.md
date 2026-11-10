---
name: video-poc-production
description: "Produce a video proof-of-concept (screen recording + live HTTP evidence) when a triager or vendor asks for a 'video PoC' with a report. Covers the three routes (re-runnable exploit / CLI-API / static PDF), the capture-to-MP4 pipeline (curl transcripts, PIL terminal frames, Playwright browser recording, ffmpeg composite + concat), and the verification step that catches truncated segments and letterboxed frames before you ship."
version: 1.0.0
author: Fauzi Susanto
license: MIT
metadata:
  hermes:
    tags: [video, poc, ffmpeg, playwright, evidence, bug-bounty, report]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Video PoC production

Dipakai ketika triager/vendor minta **"video PoC"** untuk laporan yang sudah ada. Terjadi pada
Todoist DCR 2026-10. Vendor sering minta video setelah laporan teks masuk, jadi ini kerjaan
lanjutan — bukan bikin temuan baru.

## Prinsip yang tidak bisa ditawar

1. **Semua isi video harus berasal dari capture nyata.** Output terminal = respons HTTP mentah dari
   perintah yang ditampilkan di frame itu. Kalau tidak bisa menjalankan ulang, jangan mengarang.
2. **Bahasa Inggris.** Artefak eksternal wajib Inggris (caption, kartu judul, komentar).
3. **Redact rahasia asli.** `client_secret`, token, API key → tampilkan `xxxx...[REDACTED, N chars]`.
   Nilai yang jadi bukti demo boleh tampil; kredensial hidup tidak.
4. **Jangan lakukan interaksi korban.** Berhenti di titik terakhir yang aman (mis. halaman login).
   Tulis di kartu penutup: "No victim account was created or used."
5. **Domain reserved, bukan infra nyata.** `*.example.com`, `*.test`, `attacker.test` — jangan pakai
   domain yang benar-benar kamu kontrol, nanti dianggap infra penyerang sungguhan.
6. **Catat state yang kamu buat.** Setiap klien/akun/objek yang lahir untuk rekaman harus dilaporkan
   ke user untuk di-revoke, beserta ID-nya.

## Tiga rute — pilih yang paling kuat

Tanyakan: **eksploitasinya bisa dijalankan ulang sekarang?**

| Rute | Kapan | Hasil |
|---|---|---|
| **A. Browser nyata** | target web, ada UI/redirect yang perlu dilihat | Playwright rekam native → bukti hidup. Paling meyakinkan. |
| **B. HTTP/CLI nyata** | eksploitasi lewat API/CLI | Render gaya terminal dari transkrip curl nyata + highlight. |
| **C. PDF statis saja** | tidak bisa diulang, cuma ada PDF | Halaman PDF di-render + zoom/pan + caption. **Ini slideshow, bukan PoC** — bilang ke user bahwa triager sering menganggapnya kurang. |

Rekaman jendela cmd Windows nyata **dihindari** — user tidak suka window console muncul. Pakai
frame sintetis yang isinya output nyata (rute B), bukan screen capture desktop.

## Pipeline

```
1. capture   → jalankan perintahnya, simpan headers+body ke file (jangan ketik ulang!)
2. render    → frame PIL 1920x1080 (kartu + terminal + band komentar) → pipe ke ffmpeg
3. composite → rekaman Playwright + overlay address bar asli + caption → mp4
4. concat    → semua segmen, fps disamakan
5. VERIFY    → sampling piksel per timestamp (wajib, lihat bawah)
```

Skrip kerja lengkap ada di `references/video-poc-pipeline.md` — salin dan sesuaikan.

## Pitfall yang benar-benar kejadian

**Playwright merekam viewport saja — tanpa address bar.** Padahal untuk temuan OAuth/redirect,
"domainnya tetap target.com" adalah inti argumennya. Solusi: rekam viewport, lalu composite
address bar sendiri dengan URL **asli** hasil `page.url()` / header `Location`. Jangan mengarang URL.

**Campur fps merusak timeline concat.** Rekaman Playwright keluar 25 fps; segmen PIL 30 fps. Setelah
concat, segmen browser terpotong jadi ~8 detik dan kartu penutup melebar jadi 20 detik — total durasi
tetap benar, jadi kelihatan sehat kalau tidak diverifikasi. Paksa `fps=30` di setiap segmen DAN
`-r 30 -fps_mode cfr` saat concat.

**`-vsync` sudah dihapus di ffmpeg 9.x.** Pakai `-fps_mode cfr`.

**MemoryError saat render frame PIL.** 1920x1080 RGB = 6,2 MB per frame; 500 frame = 3 GB dan box
6 GB akan mati. Render sebagai **generator**, tulis tiap frame langsung ke stdin ffmpeg
(`-f rawvideo -pix_fmt rgb24`), jangan pernah menampung list frame.

**Koordinat `overlay` relatif ke rantai saat itu, bukan ke canvas.** Menaruh bar di `y=0` setelah
`scale+pad` akan menimpa bagian atas video, bukan duduk di atasnya. Bikin canvas eksplisit dulu
(`color=c=0x0D1117:s=1920x1080:d=1[bg]`), baru `[bg][base]overlay=0:BAR_H`.

**Letterbox/pillarbox merusak kualitas.** `force_original_aspect_ratio=decrease` + `pad` menyisakan
bar gelap (21% di kasus nyata). Pakai `increase` + `crop` supaya halaman mengisi penuh.

**Vision tool belum tentu bisa QA hasil render.** Kalau tidak bisa melihat gambar, verifikasi
deterministik: ambil teks DOM dari halaman (Playwright `inner_text`), dan statistik piksel
(komposisi terang/gelap, bbox logo, densitas tepi). Itu lebih dapat dipercaya daripada vision.

## VERIFY — langkah yang tidak boleh dilewati

Build sukses ≠ video benar. Extract frame di timestamp yang diketahui dan ukur:

- **band komentar ada di setiap segmen** → bright piksel di strip bawah
- **typing animation jalan** → ink di body naik bertahap
- **segmen browser full-frame** → tidak ada strip gelap di kiri/kanan
- **transisi segmen tepat** → bandingkan dengan akumulasi durasi segmen

Kasus nyata: build melaporkan sukses, tapi segmen browser cuma 8 detik dan ada pillarbox 21%.
Keduanya ketangkap hanya karena sampling piksel.

## Spesifikasi deliverable

MP4 · H.264 (`libx264`) · `-pix_fmt yuv420p` · 1920x1080 · 30 fps · `-movflags +faststart` ·
**tanpa audio** (kecuali diminta narasi) · durasi 60-120 detik · caption Inggris menyatu di video
(bukan file .srt terpisah, supaya jalan di player apa pun).

`faststart` penting: portal vendor sering streaming, bukan download.

## Struktur video yang terbukti

```
0:00  kartu judul       judul, target, endpoint, severity, peneliti, tanggal
0:05  langkah 1         aksi utama (registrasi/request) → respons sukses, highlighted
0:20  kontrol A         bukti hal yang seharusnya menghalangi memang tidak ada / salah jenis error
0:27  langkah 2         aksi lanjutan
0:37  kontrol B         kontrol positif yang ada tapi sia-sia (kalau ada)
0:46  browser nyata     konsekuensi yang bisa dilihat mata
1:01  kartu penutup     dampak + pernyataan tidak ada akun korban dipakai
```

Band komentar di bawah layar di **setiap** segmen — ini yang user minta eksplisit ("buatkan komentar
di dalam video bisa?"). Kalau tidak diminta pun, tambahkan: triager menonton tanpa audio.

## Kalau langkah di video berbeda dari laporan PDF

Ini yang paling penting: **jangan diamkan.** Kalau saat produksi video ketemu bahwa langkah di
laporan tidak akurat (host salah, endpoint berubah, klaim yang tidak terbukti), hasilkan tiga hal:

1. Video yang mengikuti jalur **yang benar-benar jalan**.
2. Ringkasan langkah terkoraksi (plain text, siap tempel ke submission) — jelaskan apa yang berubah
   dan mengapa, plus tabel perbandingan.
3. PDF versi baru dengan seksi terbuka "Correction to the previous submission" + tegaskan apakah
   koreksinya mengubah kerentanan atau tidak.

Jangan sembunyikan perbedaan itu; kalau triager mereproduksi langkah lama dan gagal, laporan bagus
bisa ditolak. Lihat `references/correcting-a-submitted-report.md`.