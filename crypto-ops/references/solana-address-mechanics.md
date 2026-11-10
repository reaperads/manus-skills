# Solana Address Mechanics, Fund Recovery & MEV

## Address Generation

```
Address = base58(ed25519_public_key)  # 32 bytes
Space = 2^256 ≈ 1.16 × 10^77
```

- **Ed25519** keypair (NOT secp256k1 like EVM)
- Address = base58-encoded 32-byte public key
- Collision probability = 1/2^256 → **completely impossible** to brute-force

### Random Wallet Generation Cannot Find Funded Addresses
- New wallet = 0 SOL, 0 token accounts, 0 history
- No SPL token accounts exist until someone sends you a token
- No Jito tips exist (tips go to registered validators, not random addresses)
- **Wallet creation does NOT create claimable value**

## SPL Token Account Rent

### How It Works
- Every SPL token/NFT received creates a token account at your wallet
- Token account holds a **rent deposit** (~0.002 SOL)
- When you sell/burn all tokens, the token account persists (empty but rent-locked)
- Rent can be reclaimed by calling `closeAccount()`

### Claimable Rent Sources
| Source | Amount | Claimable? | Method |
|--------|--------|------------|--------|
| Empty SPL token accounts | ~0.002 SOL each | ✅ Yes | `closeAccount()` |
| Deactivated stake accounts (amount=0) | ~0.002 SOL | ✅ Yes | `closeAccount()` |
| Jito unclaimed MEV tips | Variable | ✅ Yes | Jito claim program |
| Failed tx fees | Variable | ❌ No | Goes to validator |

### Tools for Rent Reclaim
- **claimyoursol.com** — scan + close empty SPL accounts, reclaim rent
- **sol-incinerator.com** — burn unwanted tokens/NFTs + reclaim rent
- **Solana CLI** — manual `close-account` command
- **solana-py** — programmatic batch close

### Key Limitation
- Can only claim accounts **in YOUR OWN wallet**
- Cannot sweep other people's wallets (private key required)
- New wallet = 0 SPL accounts = 0 rent = nothing to claim

## Solana MEV Landscape

### Jito Bundle MEV (Most Viable)
- Jito = Solana MEV infrastructure (validators + bundle submission)
- Bundles = grouped txs executed atomically
- Supports: arbitrage, sandwich, liquidation

| Strategy | Profit/tx | Competition | Capital Needed |
|----------|-----------|-------------|----------------|
| Sandwich | 0.5-5% | High (mostly dead post-Jito protections) | 5+ SOL |
| DEX Arbitrage | 0.1-1% | Very high (professional bots) | 10+ SOL |
| Liquidation | 5-15% | Medium (opportunistic) | 20+ SOL |
| Jito Bundles | Variable | High | 5+ SOL |

### Why Solana MEV Is Harder Than EVM
- Priority fees + Jito tips eat into sandwich margins
- Slippage protection on Jupiter/Raydium
- Very low latency required (sub-second)
- Professional teams dominate with custom infrastructure

### Non-MEV SOL Earning
| Method | Returns | Capital | Difficulty |
|--------|---------|---------|------------|
| Staking | ~7% APY | 1+ SOL | Easy (passive) |
| Airdrop farming | Speculative | Gas fees only | Medium |
| LP provision | Trading fees | 10+ SOL | Hard (impermanent loss) |
| Validator | Block rewards | 100K+ SOL delegated | Very hard |

## Post-Dencun (EIP-6780) Impact on Solana Parallel

While EIP-6780 is EVM-specific, Solana has analogous patterns:
- **Rent reclamation** replaces "selfdestruct recycling" as fund recovery vector
- Pre-Dencun EVM ghosts = SOL empty SPL accounts (both are "dead" state holding value)
- Both require specific parameters to reclaim
- Both have dedicated tools (claimyoursol.com = claimyoursol for EVM)

## Solana RPC Methods for Fund Recovery

```python
# Check balance
resp = client.post(rpc_url, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "getBalance",
    "params": [pubkey]
})

# Get transaction history
resp = client.post(rpc_url, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "getSignaturesForAddress",
    "params": [pubkey, {"limit": 1000}]
})

# Get token accounts (find empty SPL accounts)
resp = client.post(rpc_url, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "getTokenAccountsByOwner",
    "params": [pubkey, {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}, {"encoding": "jsonParsed"}]
})

# Close empty token account (reclaim rent)
# Use solana-py or solders to build closeAccount instruction
```

## Pitfalls
1. **New wallets have nothing to claim** — SPL accounts must be created by incoming token transfers
2. **Jito tips go to validators** — not to random addresses you generate
3. **Solana address space (2^256)** — 17 orders of magnitude larger than EVM (2^160); brute force even more impossible
4. **solana-py 0.40+ is async-only** — use httpx + raw JSON-RPC instead
5. **Ed25519 keypair format** — `Keypair.from_bytes()` needs 64 bytes (secret + public), not 32
6. **Gas on Solana is cheap but non-zero** — batch operations to minimize per-account cost
7. **Claimyoursol only works on YOUR wallet** — connect wallet → scan → claim; cannot sweep others
