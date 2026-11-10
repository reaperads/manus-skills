# External Wallet Auto-Sweep (Cron-Based)

Monitor arbitrary wallets (not part of fleet) and auto-sweep when native balance exceeds a USD threshold. Useful for sweeping airdrop wallets, bug bounty wallets, or any externally-owned wallet.

## Architecture

```
monitor script (Python)
    → checks native balance on all 9 EVM chains
    → if balance > threshold USD: sign + send to destination wallet
    → outputs result (TX links or "no sweep needed")
        → Hermes cron runs every 10m
            → if sweep occurred: deliver TX links to Telegram
            → if nothing: stay silent
```

## Monitor Script Template

Place at `~/.hermes/scripts/wallet_monitor.py`:

```python
#!/usr/bin/env python3
"""Auto-sweep: check native balances across chains, sweep if > threshold."""
from web3 import Web3
from eth_account import Account

SOURCE_PK = "0x..."
SOURCE_ADDR = Account.from_key(SOURCE_PK).address
DEST_ADDR = "0x..."
DEST_PK = "0x..."
MIN_USD = 5.0

CHAINS = {
    "1":    {"name": "Ethereum",  "symbol": "ETH",  "rpc": "https://ethereum-rpc.publicnode.com",        "chain_id": 1,    "explorer": "https://etherscan.io"},
    "56":   {"name": "BSC",       "symbol": "BNB",  "rpc": "https://bsc-rpc.publicnode.com",             "chain_id": 56,   "explorer": "https://bscscan.com"},
    "137":  {"name": "Polygon",   "symbol": "POL",  "rpc": "https://polygon-bor-rpc.publicnode.com",     "chain_id": 137,  "explorer": "https://polygonscan.com"},
    "42161":{"name": "Arbitrum",  "symbol": "ETH",  "rpc": "https://arbitrum-one-rpc.publicnode.com",    "chain_id": 42161,"explorer": "https://arbiscan.io"},
    "10":   {"name": "Optimism",  "symbol": "ETH",  "rpc": "https://optimism-rpc.publicnode.com",        "chain_id": 10,   "explorer": "https://optimistic.etherscan.io"},
    "8453": {"name": "Base",      "symbol": "ETH",  "rpc": "https://base-rpc.publicnode.com",            "chain_id": 8453, "explorer": "https://basescan.org"},
    "43114":{"name": "Avalanche", "symbol": "AVAX", "rpc": "https://avalanche-c-chain-rpc.publicnode.com","chain_id": 43114,"explorer": "https://snowtrace.io"},
    "250":  {"name": "Fantom",    "symbol": "FTM",  "rpc": "https://fantom-rpc.publicnode.com",          "chain_id": 250,  "explorer": "https://ftmscan.com"},
    "100":  {"name": "Gnosis",    "symbol": "xDAI", "rpc": "https://gnosis-rpc.publicnode.com",          "chain_id": 100,  "explorer": "https://gnosisscan.io"},
}

NATIVE_USD = {"ETH": 3800.0, "BNB": 600.0, "POL": 0.50, "AVAX": 35.0, "FTM": 0.50, "xDAI": 1.0}

def check_and_sweep():
    sweepable = []
    for cid, chain in CHAINS.items():
        try:
            w3 = Web3(Web3.HTTPProvider(chain["rpc"], request_kwargs={"timeout": 10}))
            addr = Web3.to_checksum_address(SOURCE_ADDR)
            bal = w3.eth.get_balance(addr)
            bal_usd = (bal / 1e18) * NATIVE_USD.get(chain["symbol"], 0)
            if bal_usd >= MIN_USD:
                gas_reserve = w3.eth.gas_price * 21000 * 2  # 2x safety
                sendable = bal - gas_reserve
                if sendable > 0:
                    sweepable.append({"chain": chain, "sendable": sendable, "usd": bal_usd})
        except Exception as e:
            print(f"  {chain['name']}: ERR - {e}")

    if not sweepable:
        print(f"All chains < ${MIN_USD}. No sweep needed.")
        return

    for item in sweepable:
        c = item["chain"]
        try:
            w3 = Web3(Web3.HTTPProvider(c["rpc"], request_kwargs={"timeout": 30}))
            dest = Web3.to_checksum_address(DEST_ADDR)
            nonce = w3.eth.get_transaction_count(dest)
            gas_price = w3.eth.gas_price
            tx = {
                "nonce": nonce,
                "to": dest,
                "value": item["sendable"],
                "gas": 21000,
                "gasPrice": int(gas_price * 1.1),
                "chainId": c["chain_id"],
            }
            signed = w3.eth.account.sign_transaction(tx, DEST_PK)
            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            print(f"SWEEP {c['name']}: {c['explorer']}/tx/{receipt.transactionHash.hex()}")
        except Exception as e:
            print(f"SWEEP FAILED {c['name']}: {e}")

if __name__ == "__main__":
    check_and_sweep()
```

## Cron Setup

```
cronjob action=create schedule="every 10m" script="wallet_monitor.py"
  enabled_toolsets=["terminal","file"] deliver="telegram"
  prompt="Run the wallet monitoring script. If sweep occurred (SWEEP in output), report TX links to user. If all balances below threshold, respond silently."
```

## Key Design Decisions

1. **Gas reserve**: Always reserve 2x estimated gas (`gas_price * 21000 * 2`) to avoid failed sweeps
2. **Silent when nothing happens**: Cron prompt instructs agent to stay silent when no sweep — avoids spam
3. **USD threshold**: Configurable via `MIN_USD` constant. $5 is good default for dust filtering
4. **Price oracle**: Hardcoded `NATIVE_USD` dict. For production, integrate CoinGecko/DexScreener API

## Pitfalls

1. **Lifecycle guard blocks script path**: If terminal tool crashes with `embedded null character in path`, install deps in `execute_code` sandbox first (`pip install web3 eth_account`), then run script from there
2. **Hardcoded prices**: Native token prices drift. Update `NATIVE_USD` or use live oracle
3. **Fantom RPC 403**: Public Fantom endpoints return 403 Forbidden. Skip or use private RPC
4. **PK ≠ Address**: Always verify `Account.from_key(pk).address` matches source before deploying
5. **Zero-nonce chains**: If source wallet has nonce=0 on a chain, it was never used there — skip to save RPC calls
