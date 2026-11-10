---
name: evm-chain-recon
description: "Black-box forensics of unknown EVM chains from public RPC."
version: 1.0.0
author: Hermes
tags: [web3, evm, rpc, chain-recon, testnet, forensics, security]
metadata:
  hermes:
    tags: [web3, evm, rpc, chain-recon, testnet, forensics, security]
    related_skills: [security-recon, web3-audit, offensive-osint]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# EVM Chain Recon — Black-box Forensics from a Public RPC

> Class-level skill. Verified workflow from the Monarca/SELEMAN audit (2026-09-24),
> where a chain (chainId 73571) was found only via a subdomain `/rpc` endpoint and had
> no explorer, no docs, and mislabeled DefiLlama addresses. Everything below worked
> with NOTHING but JSON-RPC over HTTPS.

## When to use
- Recon surfaces an RPC URL for an unfamiliar chain (subdomain `/rpc`, `/api` 301 to an
  explorer domain, ChainList/DefiLlama entry).
- Explorer/adapter claims (TVL, DEX pairs, factories) look wrong, stale, or point at
  addresses with no bytecode.
- You need to answer: **what is this chain, who is on it, where is the value, is it
  worth a full contract audit?**

## Phase 0 — Connection gotchas (all hit live, all verified)
1. **CF-fronted RPC may return EMPTY data instead of 403 when User-Agent looks non-browser-like.**
   Symptom: `eth_blockNumber` → `"0x0"`, `eth_getCode` → `"0x"` for contracts that DO have
   bytecode. Add `-A "ethers/6.13/axios"` (curl) or a `User-Agent` header (urllib/requests).
   Do NOT read empty results as "empty chain" — re-verify with a realistic UA first.
2. **`eth_call` param shape:** params[0] must be a JSON object `{"to":..,"data":..}`,
   params[1] = `"latest"`. Passing a pre-serialized JSON *string* as params[0] →
   `cannot unmarshal string into Go value of type ethapi.TransactionArgs`.
3. **`eth_getLogs` without filters times out** (`-32002 request timed out`) even in
   ~50k-block chunks. ALWAYS filter by `address` (and topic) — an address-filtered
   full-range query returns instantly and gives a token's complete history.
4. **Kernel cwd ≠ terminal cwd.** Files written by `terminal` in its working dir are
   invisible to `execute_code`/sandboxed Python — pass ABSOLUTE paths between the two.

## Phase 1 — Method allowlist (the node's posture)
Probe ~80 methods in one pass and classify each as: allowed / `method not allowed on
public RPC` / param-error / unknown. Dump the classification to disk; don't re-probe.

Probe set:
- `eth_*`: blockNumber, chainId, gasPrice, maxPriorityFeePerGas, syncing, accounts,
  getBalance, getCode, getStorageAt, getTransactionCount, getBlockByNumber/Hash,
  getTransactionByHash, getTransactionReceipt, estimateGas, call, getLogs, feeHistory,
  sendRawTransaction, newFilter/newBlockFilter/newPendingTransactionFilter,
  uninstallFilter, getFilterChanges, getFilterLogs
- `net_version`, `net_peerCount`, `net_listening` · `web3_clientVersion`, `web3_sha3`
- `admin_*`: peers, nodeInfo, datadir, unixSocket, fullSanityCheck, setHead
- `debug_*`: traceBlockByNumber, traceBlock, storageRangeAt, getBadBlocks, getBlockRlp
- `trace_*`: block, filter, transaction, call, replayBlockTransactions
- `miner_*`: start, stop, setEtherPrice · `personal_*`: listAccounts, newAccount,
  sendTransaction, unlockAccount, sign, signTypedData
- `txpool_status`, `txpool_content`, `txpool_inspect`
- PoA snapshot namespaces: `clique/ibft/parlia/authority/poa_getSnapshot`
- consensus/payload: `engine_getPayload`, `engine_forkChoiceUpdated`

Read the result the same way a node-admin config would:
- Strict allowlist (`not allowed on public RPC` on all sensitive) = correct lockdown,
  a **positive observation**, not a finding.
- `eth_sendRawTransaction` reachable through the allowlist is **normal for any public
  chain** (that's how you submit txs). A well-formed EIP-155 tx with a fake sig →
  `invalid sender` after passing signature recovery = working as designed. Only report
  if the node exposes `admin_*`/`debug_*`/`personal_*`/`miner_*` (then it's critical).

## Phase 2 — Chain identity + liveness
```
web3_clientVersion      # Geth/vX.Y.Z-stable-.../linux-amd64/go...
eth_chainId, eth_blockNumber, eth_gasPrice, eth_maxPriorityFeePerGas
net_peerCount, net_listening, eth_syncing
eth_getBlockByNumber 0x0   # genesis: timestamp, extraData, difficulty, totalDifficulty
eth_getBlockByNumber latest # head: timestamp, miner field, txs
```
Interpretation:
- Recent genesis timestamp + difficulty `0x1` + totalDifficulty `0x1` + PoA-looking
  extraData (hash blob) + `net_peerCount` < 10 + `miner` = zero address →
  **fresh private/testnet/GPU-simulator chain**. Set expectations: no mainnet value.
- `eth_getBalance` on the deployer(s) you find next: trivial native balance reinforces
  testnet verdict.
- `identityMode: parent-fork` in a sister explorer's token list + a cached parent-chain
  (e.g. Ethereum) token registry = fork testnet; all "tokens" may be parent fakes.

## Phase 3 — Full contract-creation enumeration (young chains are SHORT)
Walk blocks `0x1 .. ~0x500` (adjust: young testnets rarely exceed ~10k blocks):
1. `eth_getBlockByNumber(n, true)` for each block.
2. Every tx with `to == null` / `""` = **contract creation** →
   `eth_getTransactionReceipt(hash)` → `contractAddress` + `status`.
3. Record deployer, deploy gas, input length, tx timestamp.

Then classify:
- One deployer mass-deploying one identical template (same input length, e.g. ~3.2KB)
  across consecutive blocks = **simulation/GPU workload**, not an organization's app.
- Small number of distinct deployers with distinct contracts = real ecosystem; dig each.
- `inputLen` differences at the same deployer often = same template with a different
  constructor arg (e.g. different symbol).

## Phase 4 — Token/ABI forensics per candidate contract
For each interesting `contractAddress`:
1. `eth_getCode` → `0x` = EOA/dead (drop). Note bytecode size; ~1.5KB is a small
   custom token, ~3-15KB typical Solidity, >100KB proxy-ish/verified-library.
2. Standard ERC20 view selectors (batch, short sleep between calls):
   | selector | fn |
   |---|---|
   | `0x06fdde03` | name() |
   | `0x95d89b41` | symbol() |
   | `0x313ce567` | decimals() |
   | `0x18160ddd` | totalSupply() |
   | `0x8da5cb5b` | owner() |
   | `0x70a08231` + addr | balanceOf(addr) |
   | `0x095ea7b3` + addr | approve |
   | `0xa9059cbb` + addr,amt | transfer |
   | `0x23b872dd` + from,to,amt | transferFrom |
   | `0xdd62ed3e` + owner,spender | allowance |
   Dynamic strings: decode offset/len at words 1-2 (`ln=int(b[32:64])`, value `b[64:64+ln]`).
3. **Non-standard custom tokens** (custom storage layout, misspelled revert strings):
   read `eth_getStorageAt` slots `0x0..0xc` and decode ASCII/uints. E.g. slot0 = name,
   slot1 = symbol, slot2 = decimals, slot3 = totalSupply.
4. **Embedded revert strings in the deployment calldata** reveal dev naming even with a
   fully custom ABI: `re.findall(rb'[ -~]{6,}', bytes.fromhex(calldata[2:]))` —
   e.g. `"SEED: allownance"`, `"Alkimi [OLD]"`.
5. ERC721 candidates: try `0x80ac58cd` (tokenURI), `0x01ffc9a7` (supportsInterface),
   `0x6352211e` (ownerOf).

## Phase 5 — Event history without an explorer
```
eth_getLogs {"fromBlock":"0x0","toBlock":"latest","address":CONTRACT}
```
- Transfer topic0 = `0xddf252ad...55a4df523b3ef84`.
- topic1 == 20-byte zero = **MINT**; topic2 == zero = BURN.
- Aggregate holders, total minted, distribution, and first-mover.
- A contract with totalSupply > 0 but only 2 Transfer events and no DEX pair =
  launched-and-abandoned; no liquidity to attack.

## Phase 6 — DEX / value check
- Uniswap-V2 factory selectors: `0xe6a43905` (getPair), `0xf851a440` (allPairs).
  `execution reverted` on a 1.5KB "factory" = it's a token, not a DEX.
- Cross-check adapter/registry claims (DefiLlama PRs, ChainList): if their "factory"/
  "pair"/token addresses have **no code** on the live chain, the chain re-forked or the
  registry is stale — treat registry data as unverified.
- Value gate: if there is no DEX, no liquidity, peerCount < 10, and deployer balances
  are dust → **no bounty-grade value on-chain**. Kill the contract-audit track and say so
  explicitly (a fresh testnet with simulation workloads is not a DeFi protocol).

## By-design calibration (never report as findings)
- Public testnet RPC accepting `eth_sendRawTransaction` (EIP-155 replay-protected;
  fake sig → `invalid sender` after passing sig-recovery) = how public chains work.
- Public list endpoints (tokens/blocks/txs) on a testnet explorer = intended public access.
- A strict RPC method allowlist = correct lockdown, a POSITIVE observation.
- Parent-fork token lists (Ethereum token registry replayed on a testnet) = by design.

## Output discipline
- One `$DIR/evidence/BUNDLE.txt` per chain: allowlist table, genesis/head, deployers,
  contract table (addr, deployer, blk, template?), token table, events summary, DEX
  verdict, value verdict.
- Context gets only the verdict; the bundle stays on disk.
- Pair with `web3-audit` (class-level contract hunting) ONLY after Phase 6 says value
  exists; pair with the `security-recon` skill's `references/rpc-fingerprint.md` for
  node-posture reporting.