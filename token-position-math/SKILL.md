---
name: token-position-math
description: "Quote a token position at a target MC; convert USD→IDR."
version: 1.0.0
author: Qwen
license: MIT
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [crypto, position, marketcap, projection, idr, fx, memecoin]
    related_skills: [gmgn-skills, gmgn-contract-dd, crypto-ops]
---

## Working principles

- Validate each claim with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps and check state changes and side effects.
- Work only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data.
- Never submit, send, or publish anything without the user's explicit confirmation for that specific action. Never send the same thing twice. Never reply to a vendor without approval.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Token Position Math — MC projections & fiat conversion

Turning a pasted position (or a bare contract address) into numbers the user can act on:
*"what is this worth if MC hits $X"*, *"how much MC is Nx"*, *"$X in rupiah"*.

Scope: **arithmetic on a position and its market cap**, plus fiat conversion. Contract safety
verdicts belong to `gmgn-contract-dd`; raw field dumps to `gmgn-token`; holder structure to
`gmgn-holder-analysis`. This skill answers the *"and therefore how much money"* question.

## When to use

- "brp nilai bersihnya kalau MC nya naik jadi $X"
- "kl naik Nx butuh brp MC nya" / "kalau 200x, market cap nya berapa"
- "$X brp rupiah" / "convert to IDR" / "jadi berapa juta"
- Any paste of a token tracker card (MC, liquidity, tax, position, entry MC) followed by a
  "what if" question.

## Step 0 — Before any math, pin the asset

Two traps, both seen in practice:

1. **A bare EVM `0x…` CA does not name its chain.** The same 20-byte shape lives on eth / bsc /
   base / arbitrum / hyperevm / robinhood / arc / stable. Sweep, do not assume `eth`:
   ```bash
   A=0x...; for c in eth bsc base arbitrum hyperevm robinhood arc stable; do
     echo "=== $c ==="; timeout 45 gmgn-cli token info --chain $c --address $A --raw 2>&1 | head -c 400; echo; done
   ```
   First chain with a populated token is where it lives; a single-chain launchpad mint
   (Robinhood/Pons and similar) exists on ONE chain only. A base58 CA is Solana — skip the sweep.
2. **The CA the user pasted may not be the token you were just discussing.** A bare address can be
   a completely different asset — different symbol, pool, MC. After resolving, compare symbol +
   MC + contract against the chat context and **lead with the discrepancy** if it differs:
   *"this CA is STREAM on robinhood, MC $8.9K — NOT the $Pepe you were asking about."*
   Getting this wrong means answering about the wrong asset.

Also read `supply` while you are there — the linear formula below assumes token count is constant.
If supply changed (mint / burn / rebuy), say the projection does not hold instead of computing it.

## Core formulas

```python
multiplier = mc_target / mc_now
value_new  = value_now * multiplier        # token count constant
mc_target  = mc_now * N                    # Nx measured on CURRENT value
mc_target  = mc_entry * N                  # Nx measured on CAPITAL (entry MC)
after_tax  = value_new * (1 - sell_tax)    # pool/sell tax, e.g. 0.0199 for 1.99%
profit     = value_new - capital
```

Always state the assumption in one line: **value scales linearly with market cap at fixed token
count.** It is a paper reprice, not a fill.

## Step 1 — Fiat (IDR)

- **Never invent a rate.** Fetch it: `web_search("USD to IDR exchange rate today")`.
- Quote the rate you used *and* the recent band (e.g. "rate ~17,500–17,870; I used 17,600").
- Convert at least two figures — the realistic exit and the paper number.
- Round to millions ("Rp 12,3 juta"). Never dump six decimals.

## Step 2 — Output shape (user preference — keep it identical every time)

1. Bold headline carrying the answer **and** the multiplier.
2. Compact table `Sekarang | @ target` with rows: Kapitalisasi, Multiplier, Nilai bersih,
   Setelah pajak jual, vs modal awal.
3. An explicit `Rumus:` line in the user's own notation (`Nilai baru = Nilai sekarang × (MC target ÷ MC sekarang)`),
   not prose.
4. Caveat block.
5. TL;DR one-liner ending in the multiple of capital ("profit ~$79 ≈ 18x modal").

Language: Bahasa Indonesia, sapaan "Bos". Numbers-led, no filler.

## Step 3 — Caveats (mandatory, never skip)

- **Paper value ≠ realized.** Tracker "nilai bersih" is mark-to-market, not a fill.
- **Liquidity is the binding constraint.** Compute exit ÷ pool depth. Above ~2–5% of the pool,
  slippage/price impact materially cuts what you receive — give a haircut band, don't just quote
  the gross.
- If MC rose **organically**, liquidity usually rose with it → slippage stops binding. Say that
  instead of scaring with a static pool number.
- Apply sell tax to the gross and show the net.
- IDR conversion adds exchange spread + transfer cost on top of all of it.

## Worked example — Pepe/PeiPei (Robinhood, CA `0x9bc7957d…`)

Position 84.15K $Pepe · net $4.03 · entry MC $54,399 · capital ±$4.58 · pool $10,130 · sell tax 1.99%.

| Ask | Result |
|---|---|
| MC → $1,000,000 | 20.67x → $83.30 → $81.65 after tax → **+18.2x modal** |
| 200x of current value | MC $9,676,400 → $806 → ~$790 → **~175x modal** |
| 200x of capital | MC ~$11.0M (different baseline) |
| $700 → IDR | ≈ Rp 12,3 juta @ 17,600; band $700–806 → Rp 12,3–14,2 juta |

Full detail + long-form caveat wording: `references/token-position-math.md`.

## Pitfalls

- **Two baselines for "Nx".** "Naik Nx" can mean the current value or the capital. Answer the
  current-value reading first, then give the entry-MC cross-check. Never silently pick one.
- **Never present a per-market-cap ratio times net value as a cash-out.** Apply the liquidity
  haircut before the user sizes a real exit on it.
- Do not fabricate an FX rate when a fetch is one call away.
- Keep the table shape stable across turns — the user compares successive answers.
- Don't route a "how much is my bag worth" question into a contract-safety verdict; different skill.