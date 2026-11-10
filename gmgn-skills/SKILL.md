---
name: gmgn-skills
description: "Use when querying GMGN on-chain data or trading meme tokens across sol/bsc/base/eth/arbitrum/hyperevm/robinhood/arc/stable — 15 gmgn-cli skills for trending, trenches (new launches), token security, holder/wallet analysis, portfolio, swap, and cooking (buy+TP/SL). Covers guest vs API-key access and the IPv6 trap."
version: 1.0.0
author: Qwen
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [crypto, gmgn, meme, solana, bsc, base, robinhood, sniper, onchain]
    related_skills: [crypto-ops, hoodsniper-ops, hermes-crypto-agent]
---

## Working principles

- Validate each claim with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps and check state changes and side effects.
- Work only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data.
- Never submit, send, or publish anything without the user's explicit confirmation for that specific action. Never send the same thing twice. Never reply to a vendor without approval.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# GMGN Skills (15) — On-chain Data & Meme Trading

Official GMGN OpenAPI skills: [GMGNAI/gmgn-skills](https://github.com/GMGNAI/gmgn-skills) (524★, active).
Powered by the `gmgn-cli` npm binary. Supported chains: `sol` `bsc` `base` `eth` `arbitrum`
`hyperevm` `robinhood` `arc` `stable` (+ dynamically enabled `tron` `monad` `megaeth` `xlayer`).

## Install

```bash
npm install -g gmgn-cli        # v1.6.2+
gmgn-cli --version
gmgn-cli config --check; echo "EXIT=$?"   # 0 = fine
```

Skills installed under `~/AppData/Local/hermes/skills/crypto/gmgn-*` (15 dirs, `SKILL.md` only).
Every one begins with: **run `gmgn-cli config --check` first**.

## ⭐ Guest access — data works with NO API key

Verified 2026-09: all **read-only market endpoints work unauthenticated** (no 401):

```bash
gmgn-cli market trending --chain sol --interval 1h     # live ranks, price/vol/mcap
gmgn-cli market trending --chain bsc --interval 1h
gmgn-cli market hot-searches --chain sol               # most-searched tokens
gmgn-cli market trenches --chain robinhood             # new launches
gmgn-cli token info     --chain sol --address <addr>
gmgn-cli token security --chain sol --address <addr>   # honeypot/renounce/burn flags
```

An API key is required only for **authenticated** actions — anything touching your own funds
or position: `swap`, `multi-swap`, `order`, `cooking`, `portfolio` (holdings/activity/stats/profits),
and `gas-price`. Get one with `gmgn-cli config` (prints a pre-filled Ed25519-signed link) then
`gmgn-cli config --apply <KEY>`. Config lives in `~/.config/gmgn/`.

## ⚠️ IPv6 is NOT supported — the #1 cause of 401/403

The API is IPv4-only. If `gmgn-cli config --check` exits 0 but calls return **401/403 with correct
credentials**, outbound traffic is going over IPv6. Diagnose:

```bash
curl -s -4 https://ipv4.icanhazip.com      # IPv4 address (fine)
curl -s -6 https://ipv6.icanhazip.com      # if this returns an address, IPv6 is LIVE
```

On Windows the usual culprit is **Cloudflare WARP**, which enables IPv6 by default:

```bash
"/c/Program Files/Cloudflare/Cloudflare WARP/warp-cli.exe" --version
```

Fix: disable IPv6 on the active interface, disconnect WARP, or force IPv4
(`curl -4` / a SOCKS proxy — `gmgn-cli` honours socks via its `socks` dependency).

## Gotchas

- **`--filter` has per-chain defaults.** Omitting it is NOT "no filter".
  SOL defaults to `renounced frozen`; EVM (bsc/base/eth) to `not_honeypot verified renounced`.
- **`volume` vs `amount` (kline).** `volume` = USD traded; `amount` = token units. Differ by
  the token's price (5,000× for a $0.0002 token).
- **`rug_ratio`** is a 0–1 score, not a boolean. >0.3 is high risk; combine with
  `top_10_holder_rate`, `dev_team_hold_rate`, `is_honeypot`.
- **Trenches categories:** `new_creation` (on bonding curve) → `near_completion` (curve almost
  full) → `completed` (graduated). `near_completion` always returns under key `data.pump`
  regardless of the requested `--type`.
- **`hot_level` is not normalised** — compare within one result set, never across time windows.
- **EVM/SOL field mismatch:** `is_honeypot` is EVM-only (always null on SOL);
  `renounced_mint`/`renounced_freeze_account` are SOL-only.
- **Never** scrape gmgn.ai with curl/web-fetch — the site needs login and returns no structured
  data. The CLI is the only correct method.

## The 15 skills

| Skill | Purpose |
|---|---|
| `gmgn-market` | kline, trending, trenches, signal, hot-searches, search |
| `gmgn-token` | token research: price, holders, traders, smart money, security |
| `gmgn-token-buy` | buy execution |
| `gmgn-swap` | on-chain swap |
| `gmgn-cooking` | **buy + TP/SL + condition orders in one flow** |
| `gmgn-track` | follow wallets / KOL / smart-money trades |
| `gmgn-portfolio` | holdings, activity, stats, P&L (1–100 wallets) |
| `gmgn-wallet-analysis` / `gmgn-wallet-score` | wallet behaviour & scoring |
| `gmgn-holder-analysis` | top holders, insiders, bundled wallets |
| `gmgn-contract-dd` | contract due diligence |
| `gmgn-dev-score` | developer score |
| `gmgn-heat-rank` | token heat ranking |
| `gmgn-kline-pattern` | candlestick pattern detection |
| `gmgn-narrative` | narrative / social signals |

## Windows CLI gaps to patch

The upstream `SKILL.md` files assume a \*nix shell. On this box:

- Replace `ifconfig | grep inet6` (macOS) / `ip addr show | grep inet6` (Linux) with
  `ipconfig | grep -i -A5 "IPv6"` or the `curl -6` test above.
- `gmgn-cli` installs to `%APPDATA%\npm`; if not on PATH, `export PATH="$PATH:/c/Users/<USER>/AppData/Roaming/npm"`.
- Output is raw JSON to stdout — pipe through `jq` or a Python `json.load` before printing.

## Live smoke test

```bash
gmgn-cli market trending --chain sol --interval 1h | head -c 300
```
`"code": 0` + a populated `data.rank[]` = working. Anything else = auth or IPv6 problem.