# Liferay DXP Testing Quick Reference

## Fingerprint
```bash
curl -sI https://target.com | grep -iE "Liferay-Portal|Set-Cookie|Server"
curl -s https://target.com | grep -oE 'liferay-[0-9]+-theme-[a-z0-9-]+'
```

## API Discovery
```python
import urllib.request, re
req = urllib.request.Request("https://target.com")
html = urllib.request.urlopen(req, timeout=10).read().decode()
o_paths = set(re.findall(r'/o/([a-zA-Z0-9_/-]+)', html))
portlets = set(re.findall(r'([a-z_]+_portlet_[a-zA-Z0-9_]+)', html))
```

## Key Endpoints
| Endpoint | Purpose | Auth |
|----------|---------|------|
| `/o/headless-delivery/v1.0/` | Content API | 403 |
| `/o/document-library-web` | Documents | Empty/403 |
| `/api/jsonws/invoke` | JSONRPC | 404/500 |
| `/c/portal/rss` | RSS (CVE-2022-29082) | Needs p_l_id |
| `/c/portal/forgot_password` | User enum | Same msg all |

## CVEs
- CVE-2022-29082: SSRF via RSS — needs valid p_l_id
- CVE-2023-36196: Deserialization — test render_portlet

## Pitfalls
- Headless API always 403
- JSONRPC empty/500
- Search blocked by WAF
- p_l_id hard to guess without auth
