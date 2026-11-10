---
name: onchain-finding-verification
description: "Use when verifying an on-chain finding before reporting."
version: "1.1"
author: Fauzi Susanto
license: "internal"
tags: [web3, smart-contract, defi, verification, false-positive, severity, evidence]
metadata:
  hermes:
    tags: [web3, smart-contract, defi, verification, false-positive, severity, evidence]
    related_skills: [bug-bounty, vuln-hunter]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# On-chain Finding Verification

## ⛔ CANDIDATE RULE (MANDATORY — EVERY TEST)
- **Each test = one candidate. Finding something = mark candidate. CONTINUE to next test.**
- **Candidates become FINDINGS only after Phase 5 REPORT GATE (Phase 0F).**
- **DO NOT generate report during Phase 0C. Report = ABSOLUTE LAST.**
- **If you find CRITICAL → mark candidate → KEEP TESTING. Do NOT stop.**

## ⛔ REFERENCE AUTO-LOAD (MANDATORY — load when this skill is activated)
When this skill is loaded, IMMEDIATELY read these reference files:
```
read_file('references/decode-false-positives.md')
read_file('references/ern-protocol-case-study.md')
read_file('references/bulk-exchange-case-study.md')
read_file('references/forensics-trace.md')
read_file('references/move-supra-rpc-verification.md')   # only when the target is Move/Supra
```

The gate between "I saw something alarming on-chain" and "I am reporting this".

An on-chain anomaly is not a finding. Before any report, PoC, or severity claim, the anomaly
must survive the staged verification in sections 1-3 -- and the first suspect is always
your own decoder. This skill exists because a large share of on-chain "CRITICAL" alarms are
self-inflicted artifacts, and because a fabricated `from` can invent a dead exploit chain --
which is INFORMATIONAL, never HIGH.

> Companion technique detail: `references/decode-false-positives.md` (the full
> alarm -> real-cause table, pagination rules, and the honest severity floor).

## When to Use

Load this before writing up, PoC-ing, or severity-rating any on-chain / DeFi finding --
and whenever an on-chain read produces an alarming result that would make a great headline.

Trigger phrases: "verify this finding", "is this on-chain bug real", "escrow underfunded",
"claim path bricked", "role revoked so payouts stopped", "drain", "unverified contract holds
a role", or any point where a decoded value is about to become a report.

Do not load it for pure recon (address discovery, ABI fetching) with no finding claimed yet.

### Extra trigger: a finding derived from a historical-exploit pattern

If the finding came from matching a known technique rather than from reading the code cold — i.e. you
arrived here because the protocol's shape resembles an exploited one (share↔asset conversion
rounding, a batch dispatch entry, solver-based invariants, a declared field trusted over an
independent source) — this skill still applies, **unchanged**, and one extra rule is mandatory:

> **A technique match is a lead, not a finding.** The historical case proves the *shape* is
> exploitable somewhere; it says nothing about whether *this* deployment is reachable by it.

So the verification must still establish reachability on the live contract: real caller, real state,
real value at risk. Cite the historical exploit tx hash as *corroboration* in the report — never as
the proof.

Where the shapes come from: `defi-exploit-forensics` → `skills/security/defi-exploit-forensics/references/technique-library-2025-2026.md`
(T1–T12) and `skills/security/defi-exploit-forensics/references/detection-patterns.md` (patterns 1–9). Confirm the deployment actually
carries the vulnerable code before any severity claim — the fast path is the selector pre-check in
`live-vs-source-bytecode-forensics`.

---

## 1. The #1 killer -- simulating with the WRONG `from`

Never run a capability probe with a `from` address that has no business being the caller.

Probing a role-gated function with `from=0x0` returns `AccessControl.MissingRole` and
"proves" the path is bricked. It proves nothing -- only that `0x0` lacks the role.

The decisive test is a REPLAY of a historical successful transaction, at the current block:

```
eth_call({ from: <original tx.sender>, to: <contract>, data: <original tx.input>, value: 0 })
```

| Outcome | Meaning |
|---|---|
| Reverts with a later, deeper error ("Invalid proof", a business require) | The gate before it passed -> path is LIVE |
| Reverts with the access-control error | Genuinely blocked for that caller |
| Succeeds | Currently live for that caller |

The position of the revert in the call chain is the entire signal. Note that read-only
reads (`balanceOf`, `getCode`) do not enforce `msg.sender` and work with any `from` -- do not
let that lull you into a bogus `from` for a state-changing signature. Probes must stay
read-only; a probe that would move funds is not a probe.

---

## 1b. Dormant contract triage -- BEFORE any severity claim

User correction (Ern Protocol audit 2026-09-15): "Jgn kasih sy potensial, kasih yg real."
Code vulnerability with zero on-chain impact is INFORMATIONAL, never HIGH/CRITICAL.

Before claiming ANY severity, run this check:

```bash
# 1. Contract balance (ETH + major ERC20s)
cast balance $CONTRACT --rpc-url $RPC
cast call $USDC "balanceOf(address)(uint256)" $CONTRACT --rpc-url $RPC
cast call $USDT "balanceOf(address)(uint256)" $CONTRACT --rpc-url $RPC
cast call $DAI  "balanceOf(address)(uint256)" $CONTRACT --rpc-url $RPC
cast call $WETH "balanceOf(address)(uint256)" $CONTRACT --rpc-url $RPC

# 2. Transaction count -- has this contract ever been used?
cast tx-count $CONTRACT --rpc-url $RPC

# 3. Log events -- any activity at all?
cast logs $CONTRACT --from-block 0 --to-block latest --rpc-url $RPC
```

| Outcome | Action |
|---------|--------|
| Zero balance + zero txns + zero logs | STOP. Contract is dormant. Vulnerability = code-only finding. Report as INFORMATIONAL/LOW with note: "currently dormant, risk materializes if assets deposited." |
| Zero balance but has past txns | Check if funds were drained or never deposited. Historical != current. |
| Non-zero balance | Proceed to full verification (section 2). |
| Unknown (RPC fails) | Try alternate RPC. Do NOT skip this step. |

Severity mapping for dormant contracts:

| Code vuln severity | On-chain state | Report as |
|-------------------|---------------|-----------|
| CRITICAL | Zero balance, zero activity | INFORMATIONAL -- "code vulnerability exists but contract is dormant" |
| HIGH | Zero balance, zero activity | LOW -- "architectural risk, no current impact" |
| MEDIUM | Zero balance, zero activity | LOW/INFO -- "design flaw, dormant" |
| Any | Non-zero balance | Full severity (verify section 2) |

This is the #1 false-severity trap in bug bounties. Programs reject "CRITICAL" findings on
dormant contracts. Honest severity = faster payout.

See: references/ern-protocol-case-study.md

---

## 1c. Solana program verification — RPC-based live analysis

When the BPF source is unavailable (closed-source, only client SDK found), verify
program state and architecture purely via Solana RPC calls. No decompilation needed.

### Step 1: Program existence and upgradeability

```bash
SOL_RPC="https://api.mainnet-beta.solana.com"

# Check program account — BPFLoaderUpgradeab1e = upgradeable
curl -s -X POST "$SOL_RPC" -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "getAccountInfo",
  "params": ["PROGRAM_ID", {"encoding": "jsonParsed"}]
}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
info = d['result']['value']
print(f'Owner: {info[\"owner\"]}')  # BPFLoaderUpgradeab1e = upgradeable
print(f'Executable: {info[\"executable\"]}')
print(f'Lamports: {info[\"lamports\"]}')
data = info['data']
if isinstance(data, dict):
    print(f'Program data: {data.get(\"parsed\",{}).get(\"info\",{}).get(\"programData\",\"N/A\")}')
"
```

| Owner | Meaning |
|-------|---------|
| BPFLoaderUpgradeab1e | Program is UPGRADEABLE — find upgrade authority |
| BPFLoader2002728 | Program is immutable (deployed before upgradeable loader) |

### Step 2: Extract upgrade authority

```bash
# Get program data account from Step 1, then decode it
curl -s -X POST "$SOL_RPC" -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "getAccountInfo",
  "params": ["PROGRAM_DATA_ACCOUNT", {"encoding": "base64"}]
}' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
raw = base64.b64decode(d['result']['value']['data'][0])
print(f'Data length: {len(raw)} bytes')
# First 4 bytes: slot as u32, next 4: padding
# Last 32 bytes: upgrade authority pubkey (if set, all zeros if none)
auth = raw[-32:]
if auth == b'\x00' * 32:
    print('Upgrade authority: NONE (immutable)')
else:
    import base58 as b58
    print(f'Upgrade authority: {b58.b58encode(auth).decode()}')
    print(f'Authority is EOA (not multisig) → single key compromise risk')
"
```

**CRITICAL:** If upgrade authority is an EOA (not Squads multisig), the program can be
silently upgraded to steal all funds. Cross-check with docs claims — if docs say
"multisig" but on-chain shows EOA, that's a finding.

### Step 6: API attack surface enumeration (for DEX / CeFi targets)

Solana DEX targets almost always have offchain API servers — these are OUT of scope
for on-chain audits but are prime IDOR/auth-escalation targets.

**Subdomain discovery:**
```bash
subfinder -d target.trade -all 2>/dev/null | sort -u
# Look for: api, mainnet-api, staging-api, admin, docs, app, ws, mobile
```

**API endpoint enumeration:**
```bash
# Probe discovered subdomains
for sub in api mainnet-api staging admin docs mobile ws; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://${sub}.target.trade" --max-time 5)
  echo "$sub: $code"
done
```

**IDOR test on DEX account endpoints:**
```bash
# Most DEX APIs expose account data via POST with user pubkey
API="https://mainnet-api1.target.trade/api/v1"
curl -s -X POST "$API/account" \
  -H "Content-Type: application/json" \
  -d '{"type":"fullAccount","user":"<KNOWN_USER_PUBKEY>"}'
# If returns position data → IDOR confirmed
# Test sub-types: positions, orders, balances, margin, equity, subAccounts
```

**User pubkey source for batch IDOR:**
```bash
# Get real users from on-chain transaction history
curl -s -X POST "https://api.mainnet-beta.solana.com" \
  -H "Content-Type: application/json" -d '{
    "jsonrpc":"2.0","id":1,
    "method":"getSignaturesForAddress",
    "params":["PROGRAM_ID",{"limit":50}]
  }'
# For each signature, decode instruction to extract signer pubkey
# Then test IDOR against each discovered pubkey
```

**Zellic/audit blind spot:** On-chain program audits (Zellic, OtterSec, Neodyme) do NOT
cover offchain API endpoints. IDOR on API is a separate finding class — always test.

### Step 3: Vault/token balance verification

```bash
# Get vault ATA balance
curl -s -X POST "$SOL_RPC" -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "getTokenAccountBalance",
  "params": ["VAULT_ATA_ADDRESS"]
}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
bal = d['result']['value']
amt = int(bal['amount'])
dec = bal['decimals']
human = amt / (10 ** dec)
print(f'Vault balance: \${human:,.2f} ({amt} raw, {dec} decimals)')
if human > 1_000_000:
    print('HIGH TVL — real money at risk')
"
```

### Step 4: Instruction decoding from transactions

```bash
# Get recent signatures for program
curl -s -X POST "$SOL_RPC" -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0", "id": 1,
  "method": "getSignaturesForAddress",
  "params": ["PROGRAM_ID", {"limit": 10}]
}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
for s in d.get('result', []):
    print(f\"{s['signature']}  {s.get('err', 'OK')}\")
"

# Decode instruction data (base58 → opcode + params)
python3 -c "
import base58
data = 'BASE58_INSTRUCTION_DATA'
raw = base58.b58decode(data)
print(f'Opcode byte: {raw[0]}')
print(f'Full data: {raw.hex()}')
# Common Solana DEX patterns:
# byte 0 = instruction discriminator
# bytes 1-8 = amount (u64 little-endian)
if len(raw) >= 9:
    import struct
    amount = struct.unpack('<Q', raw[1:9])[0]
    print(f'Amount: {amount}')
"
```

### Step 5: Cross-reference SDK source with on-chain transactions

When a public client SDK exists (e.g. Rust crate), cross-reference:

1. **PDA derivation** — Verify on-chain vault PDA matches SDK's PDA seeds
2. **Instruction format** — Verify opcode bytes match SDK's `Action` enum
3. **Account layout** — Verify transaction accounts match expected positions
4. **Signing** — Compare clear-sign message format with what user actually signs

**Red flags when cross-referencing:**
- SDK shows different signing paths (e.g. V1 vs V2) for same instruction
- On-chain instruction has accounts NOT in SDK's expected layout
- SDK documents fee caps but on-chain has no cap enforcement

### Solana-specific severity mapping

| Finding | On-chain state | Report as |
|---------|---------------|-----------|
| Upgradeable program, EOA authority | TVL > $1M | HIGH — single key can steal all funds |
| Upgradeable program, EOA authority | TVL < $100K | MEDIUM — limited impact |
| Upgradeable program, multisig authority | Any TVL | LOW/INFO — governance mechanism exists |
| SDK signing divergence | Active users signing | HIGH — user may unknowingly sign wrong data |
| Missing on-chain validation | Offchain matching only | HIGH — no settlement guarantees |
| Admin-controlled risk params | Active liquidations | MEDIUM — manipulation possible |

See: references/bulk-exchange-case-study.md

---

## 1d. Move / Supra program verification — RPC-based live analysis

Supra's public RPC is as rich as Solana's for black-box work, and richer than most EVM nodes:
you can enumerate every module, read the **full ABI including struct field types**, and
**execute view functions** to test the protocol's own math. No explorer, source, or GitHub
needed. Full recipe: `references/move-supra-rpc-verification.md`.

Shape of it:
- `GET /rpc/v1/accounts/{addr}/modules` → module list; the *names* reveal the design
  (`voter`+`voting_escrow`+`gauge_*`+`bribe`+`fee_distributor`+`minter` = ve(3,3) port;
  `clmm_math`+`tick_math` = concentrated liquidity).
- `GET /rpc/v1/accounts/{addr}/modules/{name}` → `exposed_functions`
  (`is_entry`, `is_view`, full param types) + `structs` (state layout and integer widths —
  where overflow lives) + `friends`.
- `POST /rpc/v1/view` with `{"function":"0xPKG::mod::fn","type_arguments":[],"arguments":[…]}`.
  **u64/u128/u256 are JSON strings, not numbers.** Struct args are objects of their fields.
  Read the parse errors — they name the expected type.
- **ABI only, no bytecode/source.** Plan around it.

### The Move access-control sweep — cheap, high-signal, do it first

Enumerate every module, take every function with `is_entry == true`, and split:

```
entry WITHOUT "&signer"                        -> callable by ANYONE, review hard
entry WITH "&signer" AND a bare "address"      -> ownership-check review
```

**The reasoning rule that kills most false positives:**

> A Move function with **neither `&signer` nor `&TxContext` cannot know who called it**, so it
> cannot pay the caller. Any value it releases must be credited to an address it was *given*.
> A no-signer function taking `address` and paying that address is a gasless
> "poke / claim for someone else" helper — not a theft primitive.

This disposed of two alarming-looking candidates in one session
(`voter::claim_bribes_for_address(address, …)` with no signer while every sibling claim had
one; `vesting::vest_individual(address, address)`). It is a filter, not a proof: it rules out
*paying the caller*, so still check whether an authorization is required for the named address
and whether shared state can be advanced in the caller's favour.

Signed integers are per-package structs, so the **same type name can carry two encodings**
(Dexlyn: core `{bits:u64}` two's complement vs tokenomics `{value:u64,is_negative:bool}` s
sign-magnitude). Negative values arrive as `bits - 2**64`. Two encodings is a hardening note,
not a finding, until you show a value crossing between them.

---

## 1e. Solana read-only execution — simulate the program, never submit

§2b item 5 says "execute it or drop it". On Solana the execution that costs nothing is
`simulateTransaction` with `sigVerify: false`: the program really runs, you get its actual
Anchor error code and `Program log:` lines, and **no state changes and no signature** are
needed. Use it whenever the hypothesis is about what the program *enforces* (claim window,
proof binding, ownership, ordering) rather than what account *state* says — an account-state
read can only ever tell you what was recorded, not what will be rejected.

Full recipe + the worked case (Merkle-distributor "claim window closed" hypothesis, refuted in
one call): `references/solana-read-only-simulation.md`.
Runnable builder: `scripts/simulate_solana_ix.py` (JSON ix spec → legacy wire format → simulate).

Four things that decide whether it works:

1. **Validate your layout offsets against a field you already know.** Re-implement the client's
   own parser (it is in the JS bundle), then assert the `mint` field equals the token mint you
   expect and the 8-byte Anchor discriminator matches. If `mint` does not round-trip, every
   timestamp you read from that struct is fiction — a wrong offset here produced a whole
   "claim window closed 26 hours ago, 138,123 users locked out" story that the simulation then
   killed in one call.
2. **Message-level counts are shortvec; Anchor `Vec` lengths inside instruction data are u32
   LE.** Mixing them yields `InstructionDidNotDeserialize (102 / 0x66)`, which reads like a
   wrong discriminator but is only a wrong length prefix. The instruction's 8-byte
   discriminator itself comes from the client bundle, not from guesswork.
3. **Instruction order is part of the contract.** An account-creating instruction (e.g. ATA
   `CreateIdempotent`, opcode `0x01`) must come *before* the instruction that reads that
   account, or you get `AccountNotInitialized (3012)` naming the *consumer's* account — a
   message about your harness order, not about the program's security. ComputeBudget ixs are
   optional for simulation; the client's own order is the template to copy.
4. **The success log is the evidence, and it can refute you.** A passing simulation prints the
   program's own interpretation of the fields
   (`Created new claim with locked 0 and 2985147 unlocked with lockup start:1791822372 end:1791822672`)
   — that single line both disproved the window hypothesis (those are *vesting* timestamps, and
   `end` had already passed) and confirmed the rest of the parse.

Pitfalls: a public RPC will 429 after a handful of calls — pace, and never read that as
target-side blocking. Getting `Instruction: <Name> invoke [1]` into the logs already proves the
discriminator and account list are correct even when the program then fails; iterate from that
point instead of rebuilding. And remember that a *successful* simulation only proves the
instruction would be accepted — the missing signature is the real gate, so state that gate
explicitly rather than implying the call could be landed.

---

## 2. Staged verification order -- stop at the first contradiction

1. Role truth -- `hasRole(role, candidate)` for every actor (admin, operator, contract, EOA);
   plus `getRoleAdmin(role)` and whether the admin can re-grant. If `getRoleMemberCount`
   reverts, the contract is plain AccessControl, not Enumerable -- enumerate by
   candidate list instead of giving up and declaring the role unknown.
2. Capability -- replay a historical successful call at the current block (section 1). Never fabricate `from`.
3. Actor identity -- `eth_getCode` for every privileged address. Contract vs EOA changes
   the whole narrative; an unverified contract holding a privileged role is a different
   finding from an EOA holding it. Never trust a single mis-parsed `code_len`.
4. Magnitude -- the real at-risk amount: Active-state records only, correct `decimals()`
   read from the token, and a fixed pagination window.
5. Destination -- identify every outflow counterparty before calling it a drain
   (a verified CErc20Delegator is a yield deposit, not a rug).

Only when all five agree do you have a finding. Contradiction between any two = decoder bug,
not a vulnerability.

---

## 2b. Fork-PoC controls -- what makes an integration finding defensible

A PoC that only shows the bad thing happening is half evidence. A PoC with both controls is
what a triager cannot wave away with "maybe your test is wrong". Three assertions, every time:

1. **Healthy-environment control.** One call that must SUCCEED and prove the harness is real:
   a selector the live contract genuinely implements, a live read returning a sane value.
   Without it, "X reverts" is indistinguishable from a bad RPC, a wrong address, or a stale
   fork block. `cast call <live addr> "currentRound()(uint256)"` returning a plausible number
   is enough, and it costs one call.
2. **Root-cause assertion.** Isolate the MECHANISM, not just the symptom: assert the exact
   thing that is missing. For a selector that does not exist, assert the `staticcall` returns
   `ok == false` **with EMPTY revert data** -- empty payload is what distinguishes "no such
   selector and no fallback" from "the function exists and reverted for a business reason".
3. **Positive control.** Drive the SAME code path with the broken input replaced by a working
   one, and assert it then behaves correctly. This is the assertion that proves "the defect is
   the wiring, not the logic", and it is the one that closes the "your harness is broken"
   reply. Worked shape (TimbSwap F1): vault wired to the live registry -> `release()` reverts
   (effect); the SAME vault wired to a three-line `MockOracle` returning a matured value ->
   `release()` pays exactly half and credits the treasury (positive control). Two
   environments, one variable changed.
4. **The blocked path must have a path that SUCCEEDS.** When the finding is "this guard stopped
   me", the probed call has to succeed the moment the guard lets it through — otherwise a
   revert from the call BODY is indistinguishable from the guard holding, and the test reports
   the OPPOSITE of the truth.

   Live example (2026-10-08, a reentrancy-guard finding): the probe wrapped its reentrant call
   in `try/catch` and scored any revert as "guard blocked me". It went green. But the revert
   was `safeTransfer` failing on an empty balance — the guard was *already* defeated and the
   test said it held. Fixing the probe to call a **successful no-op when permitted**
   (`cleanupNative(0, address(this), "")`, which does nothing but must not revert) flipped the
   result to the real one:

   ```solidity
   try router.cleanupNative(0, address(this), "") {
       reentered = true;              // guard let us through
   } catch {
       reentryReverted = true;        // guard held
   }
   ```

   Two corollaries. (a) If EVERY path reverts, you have measured nothing — go read the revert
   selector before concluding the control protected anything. (b) A guard keyed on `msg.sender`
   rejects a *different* address with its own error (e.g. `InvalidMsgSender(stored, actual)`),
   so an intermediate contract calling in on your behalf fails for the wrong reason; pick a
   trigger the guard is designed to admit (a self-call, `target == address(this)`) and let the
   disarm do the work.

5. **A hypothesis formed by READING is not evidence. Execute it or drop it.** The single most
   repeated failure mode in this class of work is a confident source-reading that turns out to
   be wrong the moment it runs. Four in one session (2026-10-08), each of which would have been
   a false positive shipped to a program that only pays for real impact:

   | Reading said | Execution showed | Why the reading was wrong |
   |---|---|---|
   | `memoryToBytes(ptr, 0)` skips its `assembly` block → returns a null `bytes` → reads scratch space | pointer `0x60`, length `0`, unaffected by a value planted at `0x00` | Solidity **pre-allocates** memory variables; the block only *reassigns*, so length 0 returns a valid empty `bytes` |
   | `claim_bribes_for_address` (no `&signer`) lets anyone claim a victim's bribes | no signer and no `&TxContext` ⇒ cannot know the caller ⇒ must credit the `address` arg | Move semantics — see §1d |
   | probe's `try/catch` scoring any revert as "guard held" | the revert was `safeTransfer` on an empty balance; the guard was *already* defeated | §2b item 4 — the blocked path needs a path that SUCCEEDS |
   | a `forge test` run read as total failure | tests had actually passed | output parsed wrong |

   Two rules fall out, and they are the honest counterpart of §2b:

   - **Build the control first.** Every one of these was caught by the control assertion
     (§2b items 1 and 3), not by re-reading the code more carefully. If a candidate has no
     control, it has no result.
   - **A failed hypothesis is a NEGATIVE, and negatives get stated, not silently dropped.**
     Report "tested, disproved" to the operator with the same clarity as a find. A reading-based
     claim that never executed is the thing that damages credibility — and it taints the valid
     findings sitting next to it in the same report.

   Corollary for the operator's own framing: when a session produces only negatives, say so
   plainly. Do not promote a structural curiosity (e.g. two encodings of one integer type) to a
   finding to avoid an empty result.

**⛔ Before reporting: does the vendor already know?** Grep their own test/audit tree for the
mechanism and for issue IDs (`VIG`, `AUDIT-`, `SEC-`, `FIX-` in filenames). This session found
`ReentrancyGuardMsgSenderVIG084Test.sol` asserting the guard must **not** be cleared — the class
was known internally, and the fix existed in the repo while the **deployed** contract still
carried the vulnerable code. That changes the framing, the expected triage reply, and whether to
spend a report slot at all: say "known internally, still not deployed" in the report instead of
discovering it from the response. Confirm it behaviourally on a fork (§2b) — a behavioural proof
survives any argument about which source is authoritative. Detection shape and the deployed-vs-repo
diff: `smart-contract-audit` → `skills/security/smart-contract-audit/references/reentrancy-guard-and-approval-defects.md`.

**Live-fork assertion discipline.** On `--fork-url`, any address that exists on the live chain
already has a balance, so an ABSOLUTE assertion is a false failure waiting to happen:
`assertEq(token.balanceOf(TREASURY), 0.5e18)` FAILED against a fork where the treasury already
held ~31,928 TIMBS -- and the failure text reads like a finding when it is only the test's
fault. Snapshot first, assert the DELTA:

```solidity
uint256 before = IERC20(T).balanceOf(dest);
... act ...
assertEq(IERC20(T).balanceOf(dest) - before, expected, "delta");
```

Also `deal()` the actor's balance instead of assuming it, and pick an amount the token will
actually move -- if the token has a transfer cap / whitelist, read it and size the transfer
against it, or the test dies on the setup line. Two setup cycles lost to exactly this.

Two compile-side details that cost cycles against a Cancun contract: an `address constant`
hard-coded in the test must be **EIP-55 checksummed** or solc refuses the file outright with
`Invalid checksum ... please prepend '00'` (it will hand you the corrected literal — copy it,
do not reformat by eye), and `foundry.toml` needs `evm_version = "cancun"` whenever the contract
under test (or the harness) touches transient storage, or compilation fails on `tstore`/`tload`.

**Deliver the test, not a transcript.** Name the runnable path and the one-line command
(`forge test --match-contract <Name> -vv --rpc-url <rpc>`) plus the verbatim output. A triager
re-running it themselves is the strongest acceptance a finding can get, and it also makes your
own later re-verification free.

---

## 3. Non-negotiable habits

- Cross-check your decode against the explorer's `decoded` fields. Disagreement means you
  are wrong -- find out why before writing anything.
- Report the real revert string. A permission revert means one thing; a business-logic
  revert ("Invalid proof") means the earlier gate passed. Never collapse the two into
  "access denied".
- Role events invert easily -- decode in spec order. OZ:
  `RoleGranted(bytes32 indexed role, address indexed account, address indexed sender)` ->
  `topics[1]=role`, `topics[2]=account`, `topics[3]=sender`. Never conclude "payouts stopped"
  from a RoleRevoked without a later event that proves the path is dead.
- Identifiers are not always numeric. Check whether the id is an ASCII string before
  indexing a mapping by integer.
- Scope the vendor audit before invoking "by-design". If the audit covered a different
  component (e.g. a Compound fork while the finding sits in an un-audited reward registry),
  then "already audited" does not apply -- but the finding still does not become Critical.

---

## 4. Honest severity floor for trust-model findings

A capability that requires already-privileged access is a trust-model note, never a
severity-inflated exploit. The residue after false positives are removed is typically:

- A privileged escrow whose payout validation is delegated downstream (no per-recipient proof
  at the registry layer) -> Low/Medium trust assumption, not an exploit -- no attacker
  capability was demonstrated.
- A privileged role held by an unverified deployed contract -> transparency gap -> Low.
- All roles in one EOA, no multisig -> Info unless the program scopes it.

Standing user rule: severity inflation is omong kosong -- a blocked exploit chain is
informational, never HIGH or CRITICAL. State plainly when a finding dies.