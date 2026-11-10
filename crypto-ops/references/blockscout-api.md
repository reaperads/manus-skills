# Blockscout API — Free Tx History & Token Balances

Etherscan now requires API keys and blocks browser access via Cloudflare. **Blockscout** is the free alternative — no API key, no Cloudflare.

## Endpoints

```
# Transaction history (returns {items: [...], next_page_params: {...}})
GET https://<chain>.blockscout.com/api/v2/addresses/<ADDR>/transactions

# Token balances (ERC-20 holdings with exchange rates)
GET https://<chain>.blockscout.com/api/v2/addresses/<ADDR>/token-balances

# Token transfers
GET https://<chain>.blockscout.com/api/v2/addresses/<ADDR>/token-transfers
```

## Chain → Blockscout Base URL Mapping

| Chain | Base URL |
|-------|----------|
| Ethereum | `https://eth.blockscout.com` |
| BSC | `https://bsc.blockscout.com` |
| Polygon | `https://polygon.blockscout.com` |
| Arbitrum | `https://arbitrum.blockscout.com` |
| Optimism | `https://optimism.blockscout.com` |
| Base | `https://base.blockscout.com` |
| Avalanche | `https://avalanche.blockscout.com` |
| Fantom | `https://ftm.blockscout.com` |
| Gnosis | `https://gnosis.blockscout.com` |

## Parse TX History

```python
import json, urllib.request

resp = urllib.request.urlopen(f"https://base.blockscout.com/api/v2/addresses/{addr}/transactions")
data = json.loads(resp.read())
for tx in data["items"][:10]:
    direction = "OUT" if tx["from"]["hash"].lower() == addr.lower() else "IN"
    value_eth = int(tx.get("value", "0")) / 1e18
    method = tx.get("method") or "transfer"
    ts = tx["timestamp"][:19]
    fee_eth = int(tx.get("fee", {}).get("value", "0")) / 1e18
    print(f"{direction} | {method} | {value_eth} ETH | fee:{fee_eth} | {ts}")
```

## Parse Token Balances

```python
resp = urllib.request.urlopen(f"https://base.blockscout.com/api/v2/addresses/{addr}/token-balances")
tokens = json.loads(resp.read())
for t in tokens:
    sym = t["token"]["symbol"]
    dec = int(t["token"].get("decimals") or 18)  # CRITICAL: decimals can be null
    val = int(t["value"]) / (10 ** dec)
    rate = t["token"].get("exchange_rate")
    usd = f" (~${float(rate) * val:.2f})" if rate else ""
    if val > 0:
        print(f"{sym}: {val}{usd}")
```

## Pitfalls

1. **`decimals: null`** — Some tokens return null decimals. Always default: `int(t["token"].get("decimals") or 18)`
2. **No pagination params** — First page returns 50 items. Use `next_page_params` from response for pagination.
3. **Token spam** — Airdrop scam tokens appear in token-balances with value > 0 but zero market rate. Filter by `exchange_rate` being None.
4. **Etherscan V2** — Old V1 API is deprecated. V2 requires API key. Blockscout is preferred for free access.
