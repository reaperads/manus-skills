# CRLF / Request Smuggling

_Header injection, response splitting, HTTP desync._

Techniques: 4  |  Source corpus: poc-compact (GitHub PoC repos)

Format: technique = the **method** (what the bug/exploit does). Repo = exemplar to read for detail.
Never paste payload bodies verbatim into a client; use the method + adapt.

| # | Technique (method) | Exemplar repo |
|---|---|---|
| 1 | A CRLF vulnerability (%0D%0A) exists in TinyWeb Server creating a potential risk for redirection, XSS and other cool tricks depending on how the client interprets the HTTP Response | `DMCERTCE_CRLF_Tiny` |
| 2 | CVE-2026-33149 — Host Header Injection in Tandoor Recipes | `FilipeGaudard_CVE-2026-33149-PoC` |
| 3 | CVE-2026-1010 – WebSocket Connection Smuggling | `George0Papasotiriou_CVE-2026-1010-WebSocket-Connection-Smuggling-via-M` |
| 4 | CVE-2026-11113 – SMTP Header Injection in Contact Form | `George0Papasotiriou_CVE-2026-11113-SMTP-Header-Injection-in-Contact-Fo` |
