---
name: crypto-ops
author: Fauzi Susanto
description: "Multi-chain crypto operations tooling — HD wallet fleets (generate, monitor, auto-distribute, Tornado Cash deposit/withdraw) and trading/sniper bot porting (EVM↔Solana, Jupiter DEX, LLM decision engine, 9router integration)."
metadata:
  hermes:
    tags: [crypto, wallets, evm, solana, bitcoin, hd-wallet, bots, sniper, tornado, 9router, automation]
---

## Working principles

- Validate each claim with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps and check state changes and side effects.
- Work only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data.
- Never submit, send, or publish anything without the user's explicit confirmation for that specific action. Never send the same thing twice. Never reply to a vendor without approval.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Crypto Ops — Wallets, Bots & Chain Integration

Class umbrella for the user's multi-chain crypto tooling. Two sub-classes live here:

- **A. HD Wallet Fleets** — generate, monitor, auto-distribute funds across EVM/Solana/Bitcoin; optional Tornado Cash deposit/withdrawal pipeline.
- **B. Trading/Sniper Bot Porting** — port bots between chains (EVM↔Solana), integrate with Hermes 9router LLM + Telegram listener/LLM decision engine.

Full workflow detail for each sub-class: `references/crypto-wallet-fleet.md` and `references/crypto-bot-porting.md` (absorbed bodies; their support files live alongside in this skill's `references/`).

## When to Use

- wallet fleet / HD wallet / mnemonic / slave-master wallet / auto-distribute / balance monitor
- port bot to Solana / EVM↔Solana migration / sniper bot / CA detection / Jupiter swap
- Tornado Cash deposit or withdrawal / ZK proof / relayer
- multi-chain balance sweep / fund recovery / RPC failover
- any crypto bot referencing 9router LLM, Telegram listener, or Hermes `.env`

## Shared Chain-Library Quirks (read first — most errors are here)

| Library | Quirk | Fix |
|---|---|---|
| web3.py 7.x | HD wallet features blocked by default | `Account.enable_unaudited_hdwallet_features()` before any HD op |
| web3.py | rejects non-checksummed addresses (`ValueError`) | `Web3.to_checksum_address(raw)` before every call |
| solana-py 0.40+ | sync API removed (`solana.rpc.api` import fails) | raw JSON-RPC via `httpx` |
| solders | Ed25519 keypair needs clamped 32B secret + 64B total | clamp bits + `Keypair.from_bytes(kL3 + verify_key)` |
| embit | `p2wpkh` is module-level; WIF is `key.key.wif()` | not `Script.p2wpkh()` / not `key.to_wif()` |
| hdwallet (npm) | needs C++ build tools | use pure-Python `embit` for Bitcoin |
| Fantom RPC | public endpoints unreliable (403) | skip or use private RPC |

RPC: `publicnode.com` free endpoints for all 9 EVM chains (list in the wallet reference).

## Shared Hermes Integration

- **9router LLM gateway:** `http://127.0.0.1:20128/v1`, OpenAI-compatible, key `9router`, model `try` (auto-route) or specific; protocol must be `openai`, never `anthropic`.
- **`.env` precedence:** project `.env` wins over Hermes `.env` (`load_dotenv(HERMES_ENV)` loads first, no override). Standard Hermes vars usable in bots: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS` (first ID = admin), `TG_API_ID`/`TG_API_HASH` (may be absent — accept user-provided values as config defaults).
- **Never expose keys:** wallet keys/notes/mnemonics never in logs, chat, or repos.

## Shared Windows Python Execution

- Preferred: `uv run --python .venv/Scripts/python.exe <script>` — avoids lifecycle-guard null-char crash.
- Fallback when the guard still blocks: `execute_code` → `terminal("pip install <pkg>")` + inline script.
- `python` in PATH is the broken Windows Store stub — never use it directly.

## A. HD Wallet Fleets

- **Structure:** 1 main + 9 slave wallets, single mnemonic (BIP44 EVM `m/44'/60'/0'/0/i`, Solana `m/44'/501'/0'/0/i`, Bitcoin BIP84 P2WPKH). Daemon monitors and splits when main balance > threshold.
- **Commands:** `generate_wallets.py` → `fleet_engine.py balance|dry-run|distribute|daemon` (always `dry-run` first on a new setup).
- **Tornado Cash (EVM only):** auto-deposit to pools + two-mode withdrawal (self-service ZK proof via **old snarkjs 0.1.x** — modern 0.7.x cannot read legacy proving keys — with relayer fallback). Withdrawal notes are the ONLY way to get funds back — never lose `notes/`.
- **Full detail + quirks + tools setup:** `references/crypto-wallet-fleet.md`; Tornado contracts/relayers/notes: `references/tornado-cash.md`, `references/zk-proof-troubleshooting.md`.

## B. Trading/Sniper Bot Porting (EVM↔Solana)

- **Verify EVERYTHING before claiming done** — grep ALL references, fix in one pass, `python -c "from sniper import config, db; db.init()"`, then run; never say "sudah fix" without proof.
- **CA detection regex per chain** (silent-failure trap): EVM `0x[a-fA-F0-9]{40}`; Solana `[1-9A-HJ-NP-Za-km-z]{32,44}` (base58 excludes 0,O,I,l) — validate with a known CA before deploy.
- **Porting order:** fix chain-specific patterns first → swap libraries (web3→solders, Uniswap→Jupiter lite-api, ERC-20→SPL) → DON'T rename DB columns (`eth_spent` etc. are just names) → audit every `config.*` reference.
- **Dexscreener bonding-curve trap:** new pump.fun tokens report `liquidity: null` — parse MC/LIQ/VOL/HLD from the Telegram post first, Dexscreener second.
- **LLM learning loop:** token fingerprinting on entry → outcome on close → `derive_lessons()` every 5 closes → inject win/loss patterns into the decision context.
- **Dedup:** `dict.fromkeys` in-message + persistent `calls` table recorded BEFORE any check — never buy the same CA twice, never re-process a skipped CA.
- **Full checklist, DB schema, post parser, error patterns:** `references/crypto-bot-porting.md`.
- **Telegram sessions/QR login/control bots:** skill `telegram-automation` → `references/bot-dual-client-sessions.md` + `scripts/qr_login_telegram.py`.

## Pitfalls (cross-cutting)

- New Solana wallets have NOTHING to claim (no SPL accounts, no rent) — "generate → scan → claim" is impossible (`references/solana-address-mechanics.md`).
- EVM address mechanics / CREATE2 / ghost addresses: `references/evm-address-mechanics.md`.
- Always dry-run first; never hardcode RPCs without failover; verify `Account.from_key(pk).address` matches the target before sweeping funds.
- Operator communication: direct, technical, zero fluff, no fabricated results, respond in Bahasa Indonesia.