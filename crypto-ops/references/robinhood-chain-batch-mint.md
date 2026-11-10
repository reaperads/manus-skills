# Robinhood Chain + Batch Minting Notes

## Robinhood Chain Details
- Chain ID: 4663
- RPC: https://rpc.mainnet.chain.robinhood.com
- Explorer: https://robinhoodchain.blockscout.com
- Gas: ~0.05 Gwei (very cheap, but fluctuates)
- WETH: 0x4200000000000000000000000000000000000006
- Uniswap V3 Router: 0xE592427A0AEce92De3Edee1F18E0157C05861564

## Batch Minting Pattern (2026-08-12)

### What worked:
1. Ad-hoc wallets via `Account.create()` (not HD derivation)
2. Distribute ETH from master/source wallet to new wallets
3. Mint by sending 0 ETH + empty data to contract
4. Uniswap swap via exactInputSingle (fee tier 30000 for new tokens)

### Critical pitfalls discovered:
1. **Checksum addresses mandatory**: `Web3.to_checksum_address()` required for ALL TX fields. Non-checksummed = `Transaction had invalid fields`
2. **Gas fluctuation**: Gas price changed between distribution and mint, causing insufficient funds. Always add 20-30% buffer.
3. **Data field**: Use `b''` (bytes) not `'0x'` (hex string) for mint transactions
4. **ETH consolidation**: When wallets have fragmented small balances, consolidate back to master before re-distributing

### Gas calculation formula:
```python
gas_price = int(w3.eth.gas_price * 1.2)
transfer_cost = 21000 * gas_price
mint_cost = 100000 * gas_price
per_wallet_needed = transfer_cost + mint_cost + 1000000  # buffer
```

### Wallet generation (ad-hoc):
```python
from eth_account import Account
acct = Account.create()
address = acct.address
pk = "0x" + acct.key.hex()
```

### Mint transaction:
```python
tx = {
    'from': Web3.to_checksum_address(addr),
    'to': Web3.to_checksum_address(CONTRACT),
    'value': 0,
    'gas': 100000,
    'gasPrice': int(w3.eth.gas_price * 1.2),
    'nonce': w3.eth.get_transaction_count(Web3.to_checksum_address(addr)),
    'chainId': 4663,
    'data': b'',
}
```

## Session: 2026-08-12
- Minted Monkey token (0x8156edd920be55e364b49cb95d2b3327d16bef60) from 11 wallets total
- First batch: 10 HD wallets + 1 source wallet
- Second batch: 1 ad-hoc wallet (ETH ran out after that)
- Attempted swap via Uniswap V3 but received 0 ETH (no liquidity)
- Total cost: ~0.00027 ETH (~$0.50)
