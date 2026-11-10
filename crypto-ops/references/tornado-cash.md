# Tornado Cash Reference

## Pool Addresses (1 ETH denomination)

| Chain ID | Chain | Pool Address | Currency |
|----------|-------|-------------|----------|
| 1 | Ethereum | `0x47CE0C6ed5b0Ce3d3A51Fdb1C52DC66a7C3C2936` | ETH |
| 56 | BSC | `0x85794A17F1c4A5cA77E7B8A29b23E6B5B1C22d3A` | BNB |
| 137 | Polygon | `0x11d98c03510BC436C3cAF90f8Ab4a4482ea3C142` | MATIC |
| 42161 | Arbitrum | `0x7221dD4a1b3E883A40fAe10bb68C11C070Aa0C02` | ETH |
| 10 | Optimism | `0xd4911b0E8De47584F5C79028bE1C98F136C74343` | ETH |
| 8453 | Base | `0x330BDFADE1820f50E292D4800682d5869C0de7b2` | ETH |
| 100 | Gnosis | `0xA160cDAB225685dA1d56aA342Ad8841c3b53f291` | xDAI |

## Other Denominations (per pool)

Each pool also supports: 0.1, 10, 100 ETH equivalents.

## Withdrawal ABI

```json
{
  "inputs": [
    {"name": "_proof", "type": "bytes"},
    {"name": "_root", "type": "bytes32"},
    {"name": "_nullifierHash", "type": "bytes32"},
    {"name": "_recipient", "type": "address"},
    {"name": "_relayer", "type": "address"},
    {"name": "_fee", "type": "uint256"},
    {"name": "_refund", "type": "uint256"}
  ],
  "name": "withdraw",
  "outputs": [],
  "stateMutability": "nonpayable",
  "type": "function"
}
```

## Relayer API Format

```json
POST /
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "relay",
  "params": [{
    "proof": "<note_string>",
    "contract": "<pool_address>",
    "recipient": "<result_wallet_address>",
    "relayer": "0x0000000000000000000000000000000000000000",
    "fee": "0",
    "refund": "0"
  }]
}
```

## ZK Tools Setup

### Architecture (key concept)
The proving key is **circuit-level and shared by ALL Tornado Cash users**. It is NOT per-wallet and NOT per-deposit. What IS unique per-transaction: the randomness (secret + nullifier → commitment). The zkey is generated once from the circuit + ptau ceremony.

### Self-service requires:
1. **circom v2.x binary** (from iden3 releases, NOT npm circom 0.5.x)
2. **circomlib 0.5.5** (NOT 2.x — MiMCSponge template signature differs)
3. `withdraw.r1cs` — compiled from circuit source
4. `withdraw.wasm` — compiled witness generator
5. `proving_key.zkey` — generated from r1cs + ptau (takes HOURS)
6. `pot20.ptau` — powers of tau (~4GB, generated locally)

### ⚠️ Format Incompatibility (CRITICAL)
Tornado Cash releases v2.1 ship files in legacy formats that DO NOT work with snarkjs 0.7.x:
- `withdraw_proving_key.json` (32MB) → snarkjs 0.1.x format → `Invalid File format`
- `withdraw_proving_key.bin` (14MB) → websnark format → `Invalid File format`
- `circuit.json` (19MB) → circom JSON (not binary R1CS) → `Invalid File format`

**Solution**: Compile from source. Download circom v2.x binary, install circomlib 0.5.5, compile withdraw.circom.

### Windows Compilation
```powershell
# Use powershell to bypass Git Bash lifecycle guard
powershell -Command "./circom.exe circuits\withdraw.circom --wasm --r1cs"
```

### Generate ptau + proving key
```bash
npx snarkjs powersoftau new bn128 20 pot20.ptau  # ~4GB, local generation
npx snarkjs zkey new withdraw.r1cs pot20.ptau proving_key.zkey  # Takes HOURS
```

### Alternative: Relayer (recommended)
Skip all ZK tooling — send note to relayer API, they handle proof + gas (fee ~0.5%).

## Note JSON Format

```json
{
  "chain_id": 1,
  "denomination": 1,
  "currency": "ETH",
  "commitment": "0x...",
  "nullifier": "0x...",
  "nullifier_hash": "0x...",
  "secret": "0x...",
  "note_string": "tornado-1-...",
  "deposited": true,
  "deposited_at": "2026-08-11T13:00:00",
  "tx_hash": "0x...",
  "depositor_role": "slave_1",
  "withdrawn": false
}
```
