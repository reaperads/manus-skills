---
name: realtime-capability-token-authz
description: "Test realtime/pubsub capability-token authorization."
version: 1.0.0
author: "[K]vk (operator: Kovak)"
license: "MIT"
metadata:
  hermes:
    tags: [security, bug-bounty, realtime, ably, pubsub, capability-token, authz, websocket, ssrf]
    related_skills: [saas-test-account-provisioning, hunt-ssrf, hunt-auth-bypass, exploit-cookbook, security-arsenal]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Realtime / Pub-Sub Capability-Token Authorization Testing

## When to Use
- The target is a **realtime / pub-sub / messaging** platform (Ably, Pusher, PubNub, Firebase RTDB, Supabase Realtime, Centrifugo, Socket.IO) or any product that mints **scoped tokens** (`capability`, `claims`, `grants`).
- You have a key/secret or a revocable **token** and want to test whether the platform **bounds** what a token can do.
- Also load when hunting **webhook SSRF** on such a platform (outbound integration URLs).

The core question: **does a token/derived credential enforce the intersection of key ∩ requested capability, per channel, and bind `clientId`?** Most realtime bugs live here.

## Model (Ably; adapt names to the vendor)
- **Key** (`APPID.keyid:secret`, Basic auth) = a **trusted server credential**. It may set any `clientId` and request any token — that is *by design*, not a bug.
- **Token** (`requestToken` / `createTokenRequest`) = a *scoped* credential handed to untrusted clients. It MUST be bounded.
- Capability = map `{channel: [ops]}`, ops = `publish|subscribe|presence|history|stats|push-*…`.

## Step 1 — Establish key capabilities empirically
```bash
# list channels (needs 'channel-metadata' / broad cap)
curl -s -u "$KEY" https://rest.ably.io/channels
# publish / history / presence
curl -s -u "$KEY" -X POST https://rest.ably.io/channels/T/messages -H 'Content-Type: application/json' -d '{"name":"n","data":"x"}'
curl -s -u "$KEY" https://rest.ably.io/channels/T/messages
curl -s -u "$KEY" https://rest.ably.io/channels/T/presence
```
Record per key: `publish=? channels=? history=? presence=?`. On the audited target one key was
**presence-only** (publish=401) and another **full** (publish=201) — always test **both**.

## Step 2 — requestToken contract (the easy-to-miss fields)
```bash
curl -s -u "$KEY" -X POST https://rest.ably.io/keys/<FULL_KEYNAME>/requestToken \
  -H 'Content-Type: application/json' \
  -d '{"keyName":"<APPID>.<keyid>","capability":"{\"*\":[\"*\"]}","clientId":"x","timestamp":<ms>}'
```
- `404 No application found with id <x>` → you used the **wrong keyname segment** (needs the FULL `APPID.keyid`).
- `400 no keyName / no timestamp` → **both are required**; `capability` is a **JSON string**, not an object.
- `401 intersection … empty` → key cannot grant that op at all (good). Note: `{"*":["*"]}` often still returns **201** — because the grant is intersected with the key, not rejected.

## Step 3 — PROVE enforcement by round-tripping (the whole point)
A `201` is **not** escalation. Use the returned token and prove the bound:
```bash
TOK=...   # from requestToken response
# op the KEY cannot do, channel the token should NOT reach:
curl -s -H "Authorization: Bearer $TOK" -X POST https://rest.ably.io/channels/esc/messages -d '{"name":"e","data":"x"}'
# must be 401 if bounded
curl -s -H "Authorization: Bearer $TOK" https://rest.ably.io/channels
curl -s -H "Authorization: Bearer $TOK" https://rest.ably.io/channels/esc/presence
```
**Escalation = token does an op the key could NOT.** On the audited target the limited-key token was
correctly bounded (publish 401, presence 200) — NO escalation. Report only if the token exceeds the key.

## Step 4 — clientId binding
```bash
# token bound to clientId=bound-client
curl -H "Authorization: Bearer $TOK" -X POST .../channels/c/messages -d '{"name":"n","data":"x","clientId":"bound-client"}'   # 201
curl -H "Authorization: Bearer $TOK" -X POST .../channels/c/messages -d '{"name":"n","data":"x","clientId":"ADMIN"}'          # expect 400 invalid clientId
```
- **Token** with a bound `clientId` MUST reject a different one (→ 400 *invalid clientId*). Verified.
- **Key (Basic)** setting an arbitrary `clientId` is **by design** (trusted server) — NOT a bug. Do not report it.
- A token minted **without** `clientId` is free to choose one — also by design; note it, don't over-claim.

## Step 5 — Channel-level & REST surface checks
- `GET /channels/<any>` on a limited key → confirm scoping is per-channel (presence=200 on any channel is normal if the key grants presence).
- `POST /batch` → 404 on Ably (no batch endpoint here); try `createTokenRequest` batch if present.
- Presence over REST is not a plain `POST` (405) — use the realtime protocol or the right verb.
- `?limit/?direction/?rewind/?until` on history — check for cross-channel leakage, not just 200s.

## Step 6 — Outbound webhook / integration SSRF
Realtime platforms let you register **outbound** URLs (webhook/Kafka/Kinesis/Firehose/Lambda).
- Start a collaborator: `interactsh-client -json -o out.jsonl` (keep it running; fresh `-o` only records what arrives).
- Register a rule whose URL is `https://<collab>/x`, then **trigger** it (publish a message that matches the rule/filter; some rules only fire on a published event, not on creation).
- **0 interactions = not proven.** Do not report an SSRF without a captured hit. Note "inconclusive".
- Note the *inbound* side too: "register inbound webhook" generates a URL that publishes INTO the app — check if that URL is guessable/leakable/undefended, but it is not an SSRF sink.

## Pitfalls (all hit for real)
- Truncated HTTP bodies break `json.loads` — read **full** response text for token bodies.
- `/accounts/<id>/x.json` may need `Accept: text/html` (else `406`).
- Distinguish a **limited** vs **full** key before concluding; a "401 not permitted" is often just the wrong key.
- `{"*":["*"]}` returning 201 is expected; the enforcement is the **round-trip**, not the mint.
- Key-setting-clientId being allowed is **by design** — the classic false positive here.
- Native tooling on this host does not translate MSYS paths — use `D:/…` in Python.

## Verification checklist
- [ ] Per-key capability recorded (publish/channels/history/presence)
- [ ] requestToken issued (keyName + timestamp + capability-as-string)
- [ ] Token round-tripped: bounded ops → 401, granted ops → 200
- [ ] clientId spoof rejected on token, allowed on key (documented as by-design)
- [ ] Channel-level scoping confirmed per channel
- [ ] Webhook SSRF: collaborator running + a real trigger attempted (0 hits → documented inconclusive)