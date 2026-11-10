# XXE Injection

_XML external entity: file read, SSRF, OOB exfil, blind XXE._

Techniques: 5  |  Source corpus: poc-compact (GitHub PoC repos)

Format: technique = the **method** (what the bug/exploit does). Repo = exemplar to read for detail.
Never paste payload bodies verbatim into a client; use the method + adapt.

| # | Technique (method) | Exemplar repo |
|---|---|---|
| 1 | POC for CVE-2024-34102 : Unauthenticated Magento XXE and bypassing WAF , You will get http connection on ur webhook | `11whoami99_CVE-2024-34102` |
| 2 | CVE-2024-50848: XXE in the WorldServer v11.8.2 | `1mhr4b_CVE-2024-50848` |
| 3 | XML External Entity Injection (XXE) in XDocReport | `AT190510-Cuong_CVE-2025-65482-XXE-` |
| 4 | Jinhe OA XXE Vulnerability | `BigMancer_Jinhe-OA-XXE-Vulnerability` |
| 5 | CVE-2026-11112 – XXE via SVG Image Upload | `George0Papasotiriou_CVE-2026-11112-XXE-via-SVG-Image-Upload` |
