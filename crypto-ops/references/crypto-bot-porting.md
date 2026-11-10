# Crypto Bot Porting — Full Reference (absorbed body of the former `crypto-bot-porting` skill)

> Telegram session/QR-login support now lives in skill `telegram-automation` (`references/bot-dual-client-sessions.md`, `scripts/qr_login_telegram.py`). Shared Hermes/9router integration details are in the `crypto-ops` SKILL.md.

---
name: crypto-bot-porting
description: "Port crypto bots EVM-Solana with Hermes 9router."
---

# Crypto Bot Porting and Integration

Port crypto trading bots between chains (EVM-Solana) and integrate with Hermes infrastructure (9router LLM, Telegram/Telethon, Solana RPC). Full lifecycle: config, wallet, DEX, Telegram listener, LLM decision engine, testing.

## Critical Workflow: Verify EVERYTHING Before Claiming Done

**Pitfall:** Never tell user "sudah fix" without running the code and confirming it works. The #1 frustration in bot porting is cascading errors - fixing one file reveals the next broken import/attribute.

**MANDATORY verification sequence:**
1. `grep -rn "OLD_TERM" sniper/ bot.py` - find ALL references before patching
2. Fix ALL files in one pass, not one-at-a-time
3. Run `python -c "from sniper import config, db; db.init(); print('OK')"` to verify imports + DB
4. Only then run the actual bot
5. If bot crashes, read the FULL traceback, fix the root cause, verify again

## Solana CA Detection (CRITICAL)

**Pitfall:** EVM addresses (`0x...40hex`) and Solana addresses (base58, 32-44 chars) are COMPLETELY different formats. If the bot listens to Telegram for CA detection and uses the wrong regex, it will silently detect NOTHING — no errors, just silence.

### Regex by chain:
```python
# EVM (Ethereum, BSC, Base, etc.)
EVM_CA_RE = re.compile(r"0x[a-fA-F0-9]{40}")

# Solana (base58 public key)
SOLANA_CA_RE = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")
```

**Validation:** Solana base58 excludes `0`, `O`, `I`, `l` to avoid confusion. Always test regex with known CAs before deploying:
```python
test = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
assert SOLANA_CA_RE.fullmatch(test)  # must match
assert not EVM_CA_RE.fullmatch(test)  # must NOT match
```

## EVM-Solana Porting Checklist

### 0. Fix ALL chain-specific patterns FIRST
Before running ANYTHING, do a global search-and-replace for:
- CA regex: `0x[a-fA-F0-9]{40}` → Solana base58
- Chain ID: `"robinhood"` / `"ethereum"` → `"solana"`
- Native coin: `ETH` → `SOL` in user-facing strings
- Balance functions: `eth_balance()` → `sol_balance()`
- DEX chain match: `DEX_CHAIN_MATCH="solana"`

```bash
grep -rn "0x\[a-fA-F0-9\]{40}\|ETH\b\|robinhood\|ethereum\|eth_balance\|eth_spent\|ERC.20" sniper/ bot.py
```

### 1. Replace Core Libraries
| EVM | Solana |
|-----|--------|
| web3.py | solders + solana-py |
| Uniswap router | Jupiter API (lite-api.jup.ag) |
| ERC-20 ABI | SPL Token (solders) |
| ETH native coin | SOL/lamports |
| eth_balance() | sol_balance() |
| Blockscout explorer | Solscan |

### 2. DEX Integration (Jupiter)
- Quote: GET `https://lite-api.jup.ag/swap/v1/quote?inputMint=So111...&outputMint={CA}&amount={lamports}`
- Swap: POST `https://lite-api.jup.ag/swap/v1/swap` with quote + user publicKey
- SOL mint: `So11111111111111111111111111111111111111112`
- Lamports: `int((usd / sol_price) * 1e9)`
- SPL decimals: assume 6 for most tokens

### 3. DB Schema Reuse
**Pitfall:** DB column names like `eth_spent`, `realized_eth` can stay as-is even on Solana - they are just column names. Do not waste time renaming schema columns. Only fix user-facing strings and Python variable references.

### 4. Config Attributes - Audit ALL References
Before running, scan every .py file for `config.SOMETHING`:
```bash
grep -rn "config\." sniper/ bot.py | grep -v __pycache__
```
Every attribute referenced must exist in config.py. Common missing ones:
- `SEED_GROUP_ID`, `SEED_TOPIC_DEGEN`, `SEED_TOPIC_MEMBER` - seed data for DB init
- `LLM_BASE_URL`, `LLM_API_KEY` - LLM connection
- `EXPLORER_URL`, `BLOCKSCOUT_API` - explorer links

## Hermes Infrastructure Integration

### 9router LLM Gateway
- Port: `20128` (local)
- Base URL: `http://127.0.0.1:20128/v1`
- API Key: `9router` (or any non-empty string)
- Protocol: `openai` (OpenAI-compatible chat completions)
- Active model: check with `curl http://127.0.0.1:20128/v1/models`
- Request:
```python
requests.post("http://127.0.0.1:20128/v1/chat/completions", json={
    "model": "try",
    "messages": [{"role": "user", "content": prompt}],
    "max_tokens": 200
}, headers={"Authorization": "Bearer 9router"})
```

### Hermes .env Loading
Project `.env` takes precedence over Hermes `.env` because `load_dotenv()` (no override) is called after `load_dotenv(HERMES_ENV)`. Put project-specific secrets in project `.env`.

Standard Hermes env vars usable in bots:
- `TELEGRAM_BOT_TOKEN` - bot token
- `TELEGRAM_ALLOWED_USERS` - comma-separated admin IDs
- `TG_API_ID`, `TG_API_HASH` - Telethon API credentials

### Project .env Template
```
TG_API_ID=<telethon_api_id>
TG_API_HASH=<telethon_api_hash>
BOT_TOKEN=<telegram_bot_token>
SESSION_NAME=hoodsniper
ADMIN_ID=<admin_telegram_id>
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
LLM_PROTOCOL=openai
LLM_BASE_URL=http://127.0.0.1:20128/v1
LLM_API_KEY=9router
DB_PATH=hoodsniper.db
```

## Telegram and Telethon Session

### Reusing Existing Sessions
If user provides a `.session` file, copy it to project root:
```bash
cp /path/to/provided.session ./hoodsniper.session
```
Session filename must match `SESSION_NAME` config value.

### QR Login (Fresh Session)
Requires `qrcode` + `pypng` packages:
```bash
uv pip install qrcode[pil]
python bot.py login
```
Scan QR from Telegram > Settings > Devices > Link Desktop Device.

### Bot Token vs User Session (CRITICAL — TWO CLIENTS REQUIRED)

**Pitfall:** Do NOT merge into a single bot-token client. Bots can only read group messages if they are members of that group. User accounts can read any group they've joined. Merging into one client = silent failure (bot not in group → 0 messages detected).

**Architecture (MUST be two separate clients):**
1. **User client** — `TelegramClient(SESSION_NAME, API_ID, API_HASH)` → QR login with personal Telegram account → reads group messages
2. **Bot client** — `TelegramClient("hoodsniper_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)` → sends notifications, control panel

```python
# CORRECT — two clients
user = TelegramClient(config.SESSION_NAME, config.TG_API_ID, config.TG_API_HASH)
await user.connect()
if not await user.is_user_authorized():
    raise SystemExit("Belum login. Jalankan dulu: python bot.py login")

bot = TelegramClient("hoodsniper_bot", config.TG_API_ID, config.TG_API_HASH)
await bot.start(bot_token=config.BOT_TOKEN)

listener.register(user, trader, notify)     # user client → baca grup
control_bot.register(bot, trader)           # bot client → control panel
```

**WRONG — single bot client (SILENT FAILURE):**
```python
# THIS WILL FAIL — bot not in group → silent, no messages detected
bot = TelegramClient("bot_session", API_ID, API_HASH)
await bot.start(bot_token=BOT_TOKEN)
listener.register(bot, trader, notify)  # ← bot can't read group!
```

**Verification:** After connecting user client, test group access:
```python
entity = await user.get_entity(-1002103131992)  # CVC FORUM
print(entity.title)  # should print group name
```

**If `hoodsniper.session` was accidentally authorized with bot_token:** Delete it and re-login:
```bash
rm -f hoodsniper.session
python bot.py login  # QR login with personal account
```

## Windows Python Environment

**Pitfall:** On Windows with git-bash, `python` on PATH is often the Windows Store stub (Permission denied). Always use uv python directly:
```
/c/Users/WINDOWS10/AppData/Roaming/uv/python/cpython-3.11.15-windows-x86_64-none/python.exe
```
Or via uv: `uv run --python .venv/Scripts/python.exe script.py`

## Telethon Forum Topics Discovery

When user specifies a group name + topic name (e.g. "CVC" + "SOLANA POTENTIAL PUMP"):

1. **List all groups first** — same name may exist as multiple entities:
```python
async for dialog in client.iter_dialogs():
    if type(dialog.entity).__name__ in ('Channel', 'Chat'):
        has_forum = getattr(dialog.entity, 'forum', False)
        print(f'{dialog.id} | {dialog.title} | {type(dialog.entity).__name__} [FORUM={has_forum}]')
```
2. **Identify the FORUM group** — topics only exist in groups with `forum=True`.
3. **List topics** via `GetForumTopicsRequest`:
```python
from telethon.tl.functions.messages import GetForumTopicsRequest
from telethon.tl.types import InputChannel
entity = await client.get_entity(group_id)
input_ch = InputChannel(entity.id, entity.access_hash)
result = await client(GetForumTopicsRequest(peer=input_ch, offset_date=0, offset_id=0, offset_topic=0, limit=100))
for t in result.topics:
    print(f'topic_id={t.id} | {t.title}')
```
4. **Config values**: `SEED_GROUP_ID` = forum group ID, `SEED_TOPIC_DEGEN` = topic_id.

**Pitfall:** `topic.title` NOT `topic.name`. Also `GetForumTopicsRequest` requires `InputChannel`, not raw entity.

## 9router Model Strategy

**Never lock to a single model.** 9router uses auto-routing combo providers. Use model name `try` which auto-selects the best available provider:
- `try` = auto-route (recommended default)
- `prod/f/mimo-v2.5-free` = specific free model
- `kr/claude-sonnet-4.5` = specific provider model
- User can change via bot panel `/menu` → 🤖 Model LLM

**Protocol must be OpenAI-compatible**, not Anthropic. Check: `LLM_PROTOCOL` should NOT be `"anthropic"` for 9router.

## Settings Panel Labels

**Pitfall:** If `SETTING_LABELS={}` (empty dict), the `/setting` or `/menu` command returns completely empty — user sees nothing. Always populate SETTING_LABELS for every key in SETTING_DEFAULTS. Use emoji + human-readable labels.

## Common Error Patterns

### AttributeError: module config has no attribute X
Cause: Some file references `config.X` but `X` not defined in config.py.
Fix: `grep -rn "config\." sniper/ bot.py` then add missing attributes to config.py.

### AttributeError: Trader object has no attribute eth_balance
Cause: Renamed chain but not function names.
Fix: Search for old function names across all files: `grep -rn "eth_balance" sniper/`

### patch tool errors (no path)
Cause: The patch tool requires `path` parameter for replace mode.
Fix: Always pass path explicitly. If patch fails repeatedly, use terminal + sed instead:
```bash
sed -i 's/old/new/g' file.py
```

## User Preference: Agent Runs Everything

**CRITICAL:** User expects the agent to execute all commands. Never say "jalankan sendiri" or "run this yourself." Run it in background with `terminal(background=true)` if needed. If a command requires user interaction (QR scan), tell user to do ONLY that one step, then resume executing.

**After every fix:** Immediately run the bot in background and monitor output. Do NOT say "sudah fix, coba jalankan" — run it yourself and report result.

## User Preference: Notify ALL Events via Bot Chat

**CRITICAL:** Every event (skip, buy, sell, safety fail, LLM decision) must be sent to the bot chat via `_notify()`. Do NOT use bare `print()` for user-facing events. Silent `print()` = user thinks bot is broken.

```python
# WRONG — user sees nothing:
print(f"[skip] {sym} mcap too high")
continue

# CORRECT — user gets notification:
await _notify(f"⏭ **SKIP {sym}** _via {src['name']}_\n`{ca}`\n💰 mcap ${mcap:,.0f} > limit")
continue
```

Also: Check wallet balance BEFORE buy attempt. If insufficient, report "skip: saldo tidak cukup" — user needs visibility that the pipeline detected and evaluated the token. Silent failures = user thinks bot is broken.

**Pattern in listener.py:**
```python
# Check balance BEFORE buy
bal = await asyncio.to_thread(_trader.sol_balance)
if bal <= 0:
    await _notify(
        f"⏭ **SKIP {sym}** _via {src['name']}_\n`{ca}`\n"
        f"💰 mcap ${mcap:,.0f} | 💧 liq ${liq:,.0f}\n"
        f"❌ **Saldo wallet kosong** — tidak ada SOL untuk beli")
    continue

usd = db.get("buy_usd") * decision["size_mult"] if decision else None
sol_needed = (usd or db.get("buy_usd")) / float(pair.get("priceNative") or 1)
if bal < sol_needed * 1.1:  # buffer 10% untuk gas
    await _notify(
        f"⏭ **SKIP {sym}** _via {src['name']}_\n`{ca}`\n"
        f"💰 mcap ${mcap:,.0f} | 💧 liq ${liq:,.0f}\n"
        f"❌ **Saldo tidak cukup** — balance {bal:.6f} SOL, butuh ~{sol_needed*1.1:.6f} SOL")
    continue
```

**Also:** Engine loop = 20 seconds (NOT 60). This is for position monitoring (TP/SL checks). The listener is event-based (real-time on NewMessage), not polling.

## Context Compaction Pitfall

When context is compacted (session too long), previous tool outputs get summarized and fix history may be lost. This causes:
- Re-applying patches that already landed
- Forgetting which errors were actually fixed vs just attempted
- Repeating the same debugging cycle

**Prevention:** After compaction, ALWAYS re-read the actual file contents (not rely on summary) before making changes. Use `read_file` to verify current state, not memory of what was done.

## Token Fingerprinting & LLM Learning Loop (CRITICAL)

**The LLM's primary value is LEARNING from past trades — not just initial entry decisions.** Without fingerprinting, the LLM has no data to learn from and decisions remain generic.

### Architecture
```
Entry → save_fingerprint(mcap, liq, age, dev%, top10%, vol, buy/sell ratio)
  ↓
Close → update_fingerprint_outcome(ca, "win_tp2"/"loss_sl"/"loss_rug", pnl%)
  ↓
Every 5 closes → derive_lessons() analyzes win/loss patterns via LLM
  ↓
Lessons + win/loss examples → injected into _memory_context()
  ↓
LLM entry decision now has DATA: "token < $1k mcap + liq < $5k = 80% rug"
```

### DB Table
```sql
CREATE TABLE IF NOT EXISTS token_fingerprints(
    ca TEXT PRIMARY KEY, symbol TEXT, mcap_usd REAL, liq_usd REAL,
    pool_age_min REAL, dev_pct REAL, top10_pct REAL,
    vol_m5 REAL, vol_h1 REAL, buys_m5 INT, sells_m5 INT,
    source TEXT, outcome TEXT, pnl_pct REAL, ts INTEGER)
```

### Save fingerprint on entry (listener.py)
```python
# After buy or dry_run decision, BEFORE open_position():
age_min = None
if pair.get("pairCreatedAt"):
    age_min = int((time.time() * 1000 - pair["pairCreatedAt"]) / 60000)
tx5 = (pair.get("txns") or {}).get("m5") or {}
vol = pair.get("volume") or {}
db.save_fingerprint(
    ca=ca.lower(), symbol=sym, mcap_usd=mcap, liq_usd=liq,
    pool_age_min=age_min, dev_pct=0, top10_pct=0,
    vol_m5=float(vol.get("m5") or 0), vol_h1=float(vol.get("h1") or 0),
    buys_m5=int(tx5.get("buys") or 0), sells_m5=int(tx5.get("sells") or 0),
    source=src["name"], outcome="open", pnl_pct=0)
```

### Update outcome on close (engine.py)
```python
# After mark_decision_outcome():
fp_outcome = {"tp2": "win_tp2", "sl": "loss_sl", "rug": "loss_rug", "trail": "win_trail"}.get(reason, reason)
db.update_fingerprint_outcome(pos["ca"], fp_outcome, real_pnl * 100)
```

### Inject patterns into LLM context (agent.py)
```python
def _memory_context():
    fp = db.win_patterns()  # returns {"wins": [...], "losses": [...]}
    return {
        "lessons": [l["text"] for l in db.recent_lessons(5)],
        "recent_decisions": [...],
        "token_patterns": {
            "win_examples": fp["wins"][:5],
            "loss_examples": fp["losses"][:5],
        },
    }
```

**Pitfall:** `derive_lessons()` needs ≥5 closed fingerprints to activate. Until then, falls back to generic text-based lessons. When upgrading, use `LESSONS_FP_SYSTEM` prompt that analyzes fingerprint patterns (mcap ranges, liquidity levels, pool age, buy/sell ratios) to extract data-driven lessons:

## Dedup Logic (No Double Entry)

**CRITICAL:** Bot must NEVER buy the same CA twice, and must skip CAs it already processed (even if skipped).

### Pattern (listener.py)
```python
for ca in dict.fromkeys(CA_RE.findall(text)):  # dict.fromkeys deduplicates within same message
    if db.seen_call(ca):  # checks calls table — global dedup
        continue
    db.record_call(ca, src["id"], caller_id, caller_name)  # record BEFORE any processing
    # ... safety checks, LLM decision, buy/skip ...
```

**Key:** `record_call()` is called BEFORE safety/mcap/LLM checks. So even if a CA is skipped (low mcap, safety fail, LLM SKIP), it won't be re-processed if it appears again.

### Dedup covers:
- Same CA in same message (dict.fromkeys)
- Same CA across different messages (seen_call → calls table)
- Same CA even after position close (calls table persists)

## Verification Checklist Before Running Bot

After ALL fixes, run this exact sequence:
```bash
# 1. Verify config imports cleanly
python -c "from sniper import config, db; db.init(); print('OK')"

# 2. Check CA regex matches Solana addresses
python -c "import re; r=re.compile(r'[1-9A-HJ-NP-Za-km-z]{32,44}'); assert r.fullmatch('DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263'); print('regex OK')"

# 3. Check Dexscreener lookup works
python -c "from sniper import dexscreener as dx; p=dx.best_pair('DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263'); print(f'dex OK: {p[\"baseToken\"][\"symbol\"]}' if p else 'FAIL')"

# 4. Run bot in background
python bot.py run  # background, monitor for 30+ seconds
```

## Dexscreener Limitation: Bonding Curve Tokens

**Pitfall:** Dexscreener returns `liquidity: null` for tokens still on bonding curves (pump.fun, CA ending with `pump`). The token HAS liquidity in the bonding curve, but Dexscreener doesn't report it until migration to Raydium. This means `liq_usd() → 0 → SKIP` for ALL new pump.fun tokens.

**Solution: Parse token stats directly from the Telegram post** instead of relying on Dexscreener. CVC and similar call groups post structured data (MC, LIQ, VOL, HLD).

**Post parser pattern (listener.py):**
```python
import re

def parse_post_stats(text):
    """Parse MC, LIQ, VOL, HLD from structured post text like:
    MC: $18.75K  LIQ: $13.5K  VOL: $36.84K (24h)  HLD: 237
    """
    stats = {"mcap": 0, "liq": 0, "vol24h": 0, "symbol": "", "holders": 0}
    t = text.replace("\u200b", "")
    for key, pattern in [
        ("mcap", r"MC:\s*\$([0-9,]+\.?[0-9]*)\s*([KMB])?"),
        ("liq", r"LIQ:\s*\$([0-9,]+\.?[0-9]*)\s*([KMB])?"),
        ("vol24h", r"VOL:\s*\$([0-9,]+\.?[0-9]*)\s*([KMB])?"),
    ]:
        m = re.search(pattern, t, re.I)
        if m:
            val = float(m.group(1).replace(",", ""))
            sfx = (m.group(2) or "").upper()
            stats[key] = val * {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}.get(sfx, 1)
    hld = re.search(r"HLD:\s*([0-9,]+)", t, re.I)
    if hld: stats["holders"] = int(hld.group(1).replace(",", ""))
    return stats
```

**Architecture: Post data PRIMARY, Dexscreener SECONDARY (fallback only):**
```python
post = parse_post_stats(text)
mcap, liq, sym = post["mcap"], post["liq"], post["symbol"]

if mcap <= 0 or liq <= 0:  # fallback to Dexscreener
    pair = await asyncio.to_thread(dx.best_pair, ca)
    if pair:
        if mcap <= 0: mcap = dx.mcap_of(pair)
        if liq <= 0: liq = dx.liq_usd(pair)
```

## Telethon Session Management

**Pitfall: NEVER delete session files unless truly authorized with wrong account.** Session files (`.session`) are fragile on Windows (PermissionError `[WinError 5]`). Deleting them forces a full QR re-login which requires user interaction.

**When to delete:**
- Session authorized with bot_token instead of user account → delete + re-login
- Session corrupted (Telegram errors, not just connection timeouts) → delete + re-login

**When NOT to delete:**
- Bot process died/crashed → session is fine, just restart
- Connection timeout → transient, retry
- Bot not detecting messages → check architecture (two clients), not session

## Login Link Delivery (Telegram Bot Context)

**Problem:** When running via Telegram bot, user can't see QR codes from terminal. The `tg://login?token=...` URL must be delivered to the user's Telegram chat.

**Pattern (programmatic — recommended):**
Use `client.qr_login()` API instead of CLI for full control:
```python
from telethon import TelegramClient
import qrcode

client = TelegramClient(session_name, API_ID, API_HASH)
await client.connect()
if not await client.is_user_authorized():
    qr_login = await client.qr_login()
    url = qr_login.url
    img = qrcode.make(url)
    img.save("qr_fresh.png")
    await bot.send_message(ADMIN_ID, f"🔐 Login link:\n{url}")
    await qr_login.wait()  # blocks until scan
```
Complete implementation: skill `telegram-automation` → `scripts/qr_login_telegram.py`; dual-client architecture + session lifecycle: `telegram-automation` → `references/bot-dual-client-sessions.md`.

**Pattern (CLI fallback):**
```python
login_url = f"tg://login?token={qr_token}"
await bot.send_message(ADMIN_ID, f"🔐 Login link (berlaku ~2 menit):\n{login_url}")
```

**Caveat:** Login tokens expire in ~2 minutes. If user is slow, need to regenerate. Best UX: put login in a separate `python bot.py login` command that user runs directly, OR generate link on-demand when user requests it.

**CRITICAL pitfall: NEVER `rm -f *.session*` when debugging.** If bot process dies or seems stuck, the session file is almost always fine — just restart the process. Deleting session forces full QR re-login which requires user interaction and wastes time. Only delete if: (a) session was authorized with wrong account (bot_token instead of user), or (b) confirmed corruption (Telegram errors, not connection timeouts).
