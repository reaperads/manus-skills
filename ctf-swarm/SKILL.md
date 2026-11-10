---
name: ctf-swarm
author: Fauzi Susanto
description: "CTF auto-solver: CTFd API poll → model swarm consensus → Docker sandbox → HITL/auto-submit."
category: security
version: 1.0.0
metadata:
  hermes:
    tags: [ctf-swarm]
---

## Working principles

- Validate each claim with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps and check state changes and side effects.
- Work only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data.
- Never submit, send, or publish anything without the user's explicit confirmation for that specific action. Never send the same thing twice. Never reply to a vendor without approval.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# CTF Swarm Coordinator

## Triggers
- CTF, capture the flag, CTFd, flag submit, swarm solve
- contest, competition, hackthebox, tryhackme, picoCTF

## Workflow
1. Poll CTFd API for new challenges
2. Dispatch to 2-3 model variants (consensus)
3. Run exploit in Docker sandbox (timeout 120s)
4. Validate flag format → auto-submit or HITL

## Quick Usage
```python
import requests, time

def poll_challenges(base_url, token, interval=30):
    headers = {"Authorization": f"Token {token}"}
    seen = set()
    while True:
        r = requests.get(f"{base_url}/api/v1/challenges", headers=headers)
        for ch in r.json()["data"]:
            if ch["id"] not in seen:
                seen.add(ch["id"])
                yield ch
        time.sleep(interval)

def submit_flag(base_url, token, challenge_id, flag):
    headers = {"Authorization": f"Token {token}"}
    return requests.post(f"{base_url}/api/v1/submissions",
        headers=headers,
        json={"challenge_id": challenge_id, "submission": flag}).json()
```

## Safety
- Scope guard: never touch targets not in scope.json
- Flag validator: only submit flags matching known formats
- Rate limit: max 10 submissions/minute
- Wrong flag 2x → pause and ask operator

## Pitfalls
- CTFd API rate limits vary per instance
- Some challenges require interactive solving (netcat)
- Flag format must match exactly (case-sensitive)