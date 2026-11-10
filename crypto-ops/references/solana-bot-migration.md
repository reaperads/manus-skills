# Solana Bot Migration Notes

## Reusable migration pattern

For an existing EVM Telegram sniper, avoid rewriting the whole application. Preserve:

- Telegram listener/control bot
- SQLite schema and position lifecycle
- engine TP/SL/trailing logic
- Dexscreener pair lookup and source management

Replace chain-specific modules:

1. `trader.py`: use `solders` keypairs, raw Solana JSON-RPC, and Jupiter Quote/Swap API.
2. `config.py`: use `SOLANA_RPC_URL`, `SOLANA_PRIVATE_KEY`, `JUPITER_QUOTE_URL`, `JUPITER_SWAP_URL`, `CHAIN_ID=solana`, and `EXPLORER_URL=https://solscan.io`.
3. `safety.py`: replace Blockscout/EVM ABI calls with `getAccountInfo` parsed mint data, freeze-authority checks, total supply, and holder concentration where available.
4. Dexscreener matching: set chain filter to `solana`.

## Wallet generation

Generate a fresh bot wallet with `solders.Keypair()`. Store the address and Base58-encoded 64-byte keypair in a file with restrictive permissions (600). Never put the private key in chat, logs, source control, or generated reports. Validate the key by reconstructing the keypair and checking that the derived public key matches the displayed address.

## Jupiter execution checklist

- Use SOL mint `So11111111111111111111111111111111111111112` for native SOL input/output.
- Quote using raw token amount and explicit `slippageBps`.
- Request a serialized swap transaction from Jupiter.
- Decode the base64 transaction, sign the versioned message with `solders`, submit using `sendTransaction`, and confirm the returned signature.
- Record the actual signature and quote amounts; do not fabricate transaction links.
- Start with dry-run/quote-only mode and fund the wallet only after configuration is validated.

## Validation checklist

- Run Python compile/import checks for `config.py`, `trader.py`, and `safety.py`.
- Verify wallet generation output and file permissions.
- Run quote-only or RPC balance checks before broadcast.
- Confirm every remaining engine reference to `ETH`/EVM transaction semantics is either renamed to SOL or deliberately retained as a database compatibility field.
- Package only after inspecting the archive contents; report a packaging failure honestly rather than claiming a ZIP exists.

## Known implementation pitfall

A direct EVM-to-Solana replacement can leave engine notifications and DB fields named `ETH`/`eth_spent`. Keep compatibility fields temporarily if needed, but update user-facing text and PnL labels to SOL to avoid misleading reports. Prefer an adapter interface so both chains can coexist during migration.
