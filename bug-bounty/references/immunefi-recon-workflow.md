# Immunefi Target Recon Workflow

**Proven pattern** for systematic recon on Immunefi bounty targets. Works when Immunefi's Next.js SPA blocks curl/web_extract.

---

## Phase 1: Program Discovery (Ranked List)

When user asks for "immunefi" or "top programs":

```bash
# Immunefi is a Next.js SPA — curl returns empty <div id="root">
# web_extract on DuckDuckGo backend also fails (search-only, can't extract)

# WORKAROUND: Use web_search to compile list from multiple sources
# Search queries:
# 1. "immunefi.com bug bounty active 2026 highest payout"
# 2. "site:immunefi.com bug bounty critical payout million"
# 3. Cross-reference with bounties listed on sherlock.xyz, bountyhunte.rs, smartcontractshacking.com
```

**Known data sources for Immunefi program listings:**
- `smartcontractshacking.com/tools/web3-auditing-competitions-and-bug-bounties/immunefi` — Live tracker, but JS-rendered (curl returns partial data)
- `arkadiyt/bounty-targets-data` — `data/immunefi_data.json` (BROKEN as of 2026-09, returns 404)
- `sherlock.xyz/post/best-web3-bug-bounties-in-2026-*` — Curated high-payout list
- `m3dython.com/blog/immunefi-review-2026` — Reviews + marquee programs

**Known top Immunefi programs (Sep 2026):**
| Program | Max Payout | Category |
|---------|-----------|----------|
| Uniswap v4 | $15.5M | DEX |
| LayerZero | $15M | Interoperability |
| Stargate | $10M | Bridge |
| MakerDAO | $10M | Stablecoin |
| Arbitrum | $2M | L2 |
| Lido | $2M | Liquid Staking |
| Aave | $1M | Lending |
| Wormhole | $1M | Bridge |
| 0x | $1M | DEX Aggregator |
| Injective | $500K | L1 DeFi |
| Sei | $500K | L1 Trading |
| BENQI | $500K | Avalanche Lending |
| Maple | $500K | Institutional Lending |
| Orca | $500K | Solana DEX |
| Nucleus | $500K | Yield |

---

## Phase 2: Single Target Deep Recon

After user selects a target, follow this 5-step workflow:

### Step 1: Immunefi Bounty Page → Rules + Payout Structure
```bash
curl -sL "https://immunefi.com/bug-bounty/<PROGRAM>/information/" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, re
html = sys.stdin.read()
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', html)
lines = [l.strip() for l in text.split('\n') if l.strip()]
printing = False
for line in lines:
    if 'Maximum Bounty' in line or 'Live Since' in line:
        printing = True
    if printing:
        print(line[:200])
"
```

**Extract:** Max payout, payout calculation (e.g., "10% of funds affected"), severity tiers, PoC requirements, payment currency, KYC requirements, prohibited activities.

### Step 2: GitHub API → Contract File Inventory
```bash
# List repo contents
curl -s "https://api.github.com/repos/<ORG>/<REPO>/contents/" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for item in data:
    print(f'{item[\"type\"]:4s} {item[\"name\"]:50s} {item.get(\"size\",\"\")}')
"

# List subdirectories (repeat for each dir)
curl -s "https://api.github.com/repos/<ORG>/<REPO>/contents/<DIR>" | ...
```

**Extract:** Contract files, repo structure, file sizes (large files = complex logic = more attack surface).

### Step 3: Protocol Docs → Architecture + Addresses
```bash
# Check docs for contract addresses, architecture, risks
curl -sL "https://docs.<protocol>.fi/" -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, re
html = sys.stdin.read()
# Extract nav links for doc structure
links = re.findall(r'href=[\"\'](/[^\"\']*)[\"\']', html)
for link in sorted(set(links))[:50]:
    print(link)
"
```

**Key pages to check:**
- `/resources/contracts` — Deployed contract addresses
- `/resources/risks` — Known risk factors (often reveals attack surface)
- `/architecture` — System design + trust boundaries
- `/llms.txt` or `/master.md` — GitBook full content dump (may be small)

### Step 4: Audit Reports → Known Vulnerabilities
```bash
# Dedaub audit reports (most Web3 audits are here)
curl -sL "https://dedaub.com/audits/<PROGRAM>/<audit-slug>/" -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, re
html = sys.stdin.read()
html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', '\n', html)
lines = [l.strip() for l in text.split('\n') if l.strip()]
for line in lines:
    if len(line) > 15:
        print(line[:180])
"
```

**Extract:** Known findings (especially unfixed or acknowledged), severity ratings, audit scope gaps.

### Step 5: Attack Surface Map
Compile everything into structured analysis:
- **Contract inventory** with file sizes
- **Deployed addresses** (mainnet)
- **Oracle dependencies** (Chainlink feeds, staleness risks)
- **Access control model** (proxy, timelock, admin keys)
- **Known audit gaps** (findings from Step 4 that weren't fully fixed)
- **Recommended attack vectors** ranked by potential impact

---

## Common Immunefi Target Patterns

### Lending Protocol (Compound-fork)
- QiToken/CToken model → check reentrancy, oracle manipulation, interest rate model abuse
- Comptroller → liquidation logic, collateral factor manipulation
- Proxy upgradeability → storage slot collision risks

### Liquid Staking
- Exchange rate calculation → flash-stake-and-borrow loops
- P-Chain delegation → validator selection influence
- MPC key management → threshold signature bypass

### Bridge / Cross-Chain
- Validator set → guardian compromise
- Message verification → signature forge
- Replay attacks → same message on multiple chains

### DEX
- Price oracle → TWAP manipulation
- Flash loan → sandwich attacks, price manipulation
- Fee logic → fee-on-transfer token edge cases

---

## Pitfalls

1. **Immunefi data source broken:** `arkadiyt/bounty-targets-data` immunefi_data.json returns 404 as of 2026-09. Use web_search + direct curl of Immunefi pages instead.

2. **Smartcontractshacking.com is JS-rendered:** curl returns price/prize data but NOT program names. Use it for quick payout verification, not full enumeration.

3. **Dedaub audit reports are large:** 100KB+ HTML pages. The vulnerability summary is in the first ~2KB of extracted text — don't try to read the whole thing.

4. **Contract repos may be partial:** Some programs have private repos (e.g., BENQI Ignite). Focus on what's publicly available.

5. **Payout calculation matters:** Many Immunefi programs use "10% of funds affected up to $X" — this means your actual payout depends on proving LARGE economic damage, not just finding a bug.

6. **QI/token payment:** Some programs pay in native tokens (not USDC). Factor in token volatility and liquidity when assessing bounty attractiveness.
