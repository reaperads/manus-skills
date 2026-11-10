---
name: security-tooling-setup
description: "Install/verify security tooling on Windows and WSL."
version: 1.0.0
author: Fauzi Susanto
license: MIT
sources: operator_experience
metadata:
  hermes:
    tags: [security, tooling, windows, wsl, install, inventory]
    related_skills: [exploit-cookbook, bb-local-toolkit, security-recon]
---

## Working principles

- Report only bugs that are actually proven, with evidence and reproduction steps. Negative tests stay in internal notes and are never submitted. Distinguish potential vs proven vs reportable.
- Validate each hypothesis with an explicit verdict: CONFIRMED, FALSIFIED, or INCONCLUSIVE. Do not conclude "0 confirmed" prematurely — re-evaluate for missed gaps (business logic, state transitions, value limits, feature interactions) and check state changes and side effects (HTTP 200 is not success; an error is not safety).
- Test only with the user's own accounts on free tiers. Never spend capital or pay for testing. No DoS, spam, high-volume automated scanning, social engineering, or other people's data. No bypassing gates by evasion.
- Never submit anything (a report, a grade, a mainnet/testnet submission) without the user's explicit confirmation for that specific submit. Never send a report twice. Never reply to a vendor without approval.
- Follow the program's "How to report" structure (Description, Potential Impact, Evidence, Steps to Reproduce). Vendor emails open with a greeting + short intro, tidy formatting, never raw markdown as the email body.
- Communicate terse, exact, and path-first. Indonesian for conversation, English for technical detail, code, identifiers, and error strings.

# Security Tooling — Verify, Install, Troubleshoot (Windows + WSL)

Companion to the bug-bounty workflow skills: those decide *what* to run; this one answers
*is it installed, where, and how do I install it here*.

## When to Use

Trigger when any of these is true:
- You are about to tell the user a tool is "missing" / "not installed".
- A tool or toolset needs installing on this machine (Windows or WSL).
- An inventory/discovery pass is needed over available security tooling.
- A tool "installed" but won't run, or an install command errored (errno 22, os error 225,
  `0xC0000142`, "not recognized as an internal or external command").
- A tool must be invoked across the Windows/WSL boundary.

Not for: choosing *which* vuln class to test (that's the hunt-* / bug-bounty skills).

## ⛔ RULE 0 — Never declare a tool "missing" from `command -v` alone

A PATH-only check produced **false MISSING verdicts** for tools that were installed
(mitmproxy, trufflehog, gosec, ghauri, commix, wafw00f, corscanner). Check, in order:

```
1. PATH                     command -v <tool>
2. Out-of-PATH user dirs    ~/.local/bin            (mitmproxy, uv tools, objection)
3. Go bins                  C:\go\bin  AND  %USERPROFILE%\go\bin   (trufflehog, gosec)
4. npm global               %APPDATA%\npm  +  ...\npm\node_modules  (aderyn, wscat)
5. pip user site            %APPDATA%\Python\Python3XX\Scripts
6. Project/tool dirs        D:\data hermes\tools\*, repo clones (dnsReaper, theo, quimera)
7. WSL                      wsl -d <distro> -e bash -lc 'command -v <tool>'
```

Space-safe existence test (**quote + arrays** — `D:\data hermes\...` breaks word-splitting):

```bash
DIRS=( "/c/Users/$USER/.local/bin" "/c/go/bin" "/c/Users/$USER/go/bin"
       "/c/Users/$USER/AppData/Roaming/npm" "/d/data hermes/tools" )
have() { command -v "$1" >/dev/null 2>&1 && { echo "PATH $(command -v "$1")"; return; }
  for d in "${DIRS[@]}"; do
    for e in "" ".exe" ".cmd"; do [ -e "$d/$1$e" ] && { echo "DIR $d/$1$e"; return; }; done
  done; echo MISSING; }
```

A re-runnable inventory lives at `D:/data hermes/advisory-intel/imm_inventory.sh` — run it, don't
re-derive. Also confirm with the tool's own version flag (`nmap --version`, `hashcat --version`,
`john --list=build-info`, `adb version`, `objection version`): an install that won't answer its
version flag is not done.

## ⛔ RULE 1 — Windows Defender quarantines offensive tooling

On Windows you may see `OSError: [Errno 22] Invalid argument` on write, `os error 225`, or
`0xC0000142` on exec, with "contains a virus or potentially unwanted software". Observed on
`impacket`'s scripts (`atexec.py`, …) and the `kerbrute` Windows binary. **Retrying on Windows
never fixes it.**

**Fix: install and run that class in WSL** (Defender does not scan the Linux filesystem):

```bash
wsl -d Ubuntu-26.04 -e bash -lc 'python3 -m pip install --user --break-system-packages impacket'
#   -> ~/.local/bin/{GetNPUsers,GetUserSPNs,secretsdump,psexec,wmiexec,atexec,smbclient,samrdump,lookupsid,ntlmrelayx}.py

wsl -d Ubuntu-26.04 -e bash -lc 'mkdir -p ~/tools && cd ~/tools && \
  curl -sL -o kerbrute https://github.com/ropnop/kerbrute/releases/download/v1.0.3/kerbrute_linux_amd64 && chmod +x kerbrute'

wsl -d Ubuntu-26.04 -u root -e bash -lc 'apt-get install -y hydra tcpdump tshark'

# tools needing an older Python (nxc, objection) — uv brings its own interpreter:
wsl -d Ubuntu-26.04 -e bash -lc 'uv tool install --python 3.12 objection'
wsl -d Ubuntu-26.04 -e bash -lc 'apt-get install -y pipx && pipx install "git+https://github.com/Pennyw0rth/NetExec"'
```

Invoke from Windows: `wsl -d <distro> -e bash -lc '~/.local/bin/GetNPUsers.py -h'`

## RULE 1b — Equipping a SKILL with its tools (matrix → install → shim → PROBE)

Operator's standing rule: when a vuln class has a skill but no working tool, **complete the
tooling — do not narrow the skill or drop the class.** (verbatim correction: *"kok rekomnya tutup
kelas, harusnya rekomnya lengkapi tools sesuai kebutuhan skill"*.) A hunt-* skill with no backing
tool is theory; the tool is what turns a guess into a proof.

Order matters — never skip step 4:

1. **Matrix** — per skill, list the tools it *requires*, test presence, group the gaps **by
   skill**. Re-runnable: `scripts/tool-coverage-matrix.py` (deployed copy at
   `~/AppData/Local/hermes/scripts/web2-tool-matrix.py`). It prints `N present / M missing`.
2. **Install in batches by METHOD** — pip → `go install` → release binaries → runtime-bound
   (Ruby/Java/Maven). Batch by method so one failure cannot abort the rest; on a machine with
   no Ruby, a whole batch degrades gracefully.
3. **Shim** so the tool is *callable*, not merely on disk (next section).
4. **PROBE every tool.** A tool that prints a traceback is NOT installed, whatever the matrix says.

### Cloned tools → callable via a `.bat` shim on PATH

`shutil.which()` (what the audit pipeline uses) resolves `.BAT`/`.CMD` through PATHEXT, and the
pipeline invokes tools with `shell=True` — so one small `.bat` in the Python Scripts dir (already
on PATH) promotes a git-cloned repo to a first-class tool:

```bat
@echo off
"C:\Users\<u>\AppData\Local\Programs\Python\Python3XX\python.exe" "D:\tools\<repo>\main.py" %*
```

Add `cd /d "<repo>"` as the second line whenever the repo imports **its own package**
(`import providers`, `from enum_tools import ...`), otherwise it dies on `ModuleNotFoundError`.

**⛔ Author shims with `write_file`, NEVER with bash `printf`.** `printf` expands escapes in the
format string, so `"...\\tools\\web2"` becomes `\t` + `ools` (a literal TAB) and the shim dies with
`The filename, directory name, or volume label syntax is incorrect` / `Errno 22`. This cost a full
debug cycle on 2026-10-07; writing the file directly avoids it entirely.

**Testing:** `subprocess.run([tool, ...])` **without** `shell=True` raises `WinError 2` for `.bat`.
That is a *test* artifact, not a broken shim — re-test with `shell=True` (which is what the
pipeline does) before declaring anything broken.

### ⛔ Extensionless wrappers: `shutil.which` needs BOTH a shebang script AND a `.cmd` (2026-10-12)

A bare (no-extension) bash wrapper named exactly like the tool in a PATH dir (`C:\Users\<u>\go\bin\ssrfmap`,
with `#!/bin/bash\nexec python "<repo>/main.py" "$@"`) resolved from **bash** but `shutil.which('ssrfmap')`
returned `None` from Python — so the pipeline would skip it. Creating a second file,
`<name>.cmd` (`@echo off` + `python "<repo>\main.py" %*`), made it resolve. **Ship both** for any
cloned tool you want a `shutil.which`-based runner to find: the shebang version for bash callers,
the `.cmd` version for PATHEXT-aware Python callers.

Working pattern used for 8 cloned tools (`linkfinder`, `secretfinder`, `cloud_enum`, `smuggler`,
`jwt_tool`, `sstimap`, `ssrfmap`, `graphqlmap`):
```bash
GB="/c/Users/$USER/go/bin"
printf '#!/bin/bash\nexec python "/d/data hermes/tools/LinkFinder/linkfinder.py" "$@"\n' > "$GB/linkfinder"
printf '@echo off\npython "D:\\data hermes\\tools\\LinkFinder\\linkfinder.py" %%*\n' > "$GB/linkfinder.cmd"
chmod +x "$GB/linkfinder"
```
(`write_file` for the `.cmd` is still the safer authoring route — see the `printf`-escape warning above.)

#### ⛔ A shim makes a tool RESOLVABLE — it does not make it REACHABLE (2026-10-12)

Adding the `.cmd` twin fixed `shutil.which`, and the tool still never ran in the audit pipeline.
The consumer derived its own tool name as `Path(tool_path).name.lower()` with only
`.exe/.bat/.py` stripped — so `linkfinder.cmd` stayed **`linkfinder.cmd`**, matched none of its
per-tool branches, and fell through to a `FUZZ_ONLY` "documented skip" that the gate accepts as
`N/A`. **The tool was green on disk, green in the gate, and never executed.**

Two lessons:

1. **When you shim a tool for a specific consumer, verify the consumer actually CALLS it** — read
   its status ledger (`tools-usage.json` / equivalent), not just `shutil.which`. A status like
   `FUZZ_ONLY` / `SKIP_WITH_REASON` / `N/A(documented skip)` means *not executed*, even when the
   surrounding gate reports PASS.
2. **Prefer a wrapper shape the consumer already understands.** If the consumer strips some
   extensions but not others, either match one it strips (`.exe`/`.bat`/`.py`) or fix the
   consumer's strip list. Shipping a `.cmd` and assuming reachability is the trap.

Full root cause + the producer-side fix: `security/audit-execution-discipline` →
`references/gate-rederive-tz-and-fuzz-only-2026-10-12.md` §3b.

### ⛔ `execute_code`'s Python has a DIFFERENT PATH than `terminal`'s — never verdict from `execute_code`

Measured: the same probe reported **16 tools missing** from `execute_code` and **0 missing** from
`terminal`, because `execute_code`'s interpreter did not inherit `C:\go\bin` on PATH. A tool can
look uninstalled in one and be perfectly callable by the pipeline (which is started from the
shell). **Always run the final presence/resolution check from `terminal`**, which is the env the
pipeline actually uses:
```bash
python -c "import shutil;M=['ffuf','nuclei',...];print('MISS:',[t for t in M if not shutil.which(t)])"
```
Corollary: `go` was missing from `execute_code`'s PATH but present in bash — build with
`terminal` (`export PATH="/c/go/bin:$PATH"; go build -o ...`), not from `execute_code`.

### Installed ≠ working — always PROBE

```python
r = subprocess.run(f'{tool} -h', shell=True, capture_output=True, text=True, timeout=60)
txt = (r.stdout or r.stderr or "")
FAIL if "Traceback" in txt or "syntax is incorrect" in txt or not txt.strip()
```

Report JALAN / GAGAL **per tool**, honestly. On 2026-10-07 this caught 4 of 19 "installed" tools
that never actually ran — a presence check alone would have shipped all 4 as working.

### Membership-level traps (capture the FIX, never "tool X is broken")

| Symptom | Cause | Fix |
|---|---|---|
| `No module named 'requests_futures'` (cloud_enum) | dep missing from requirements.txt | `pip install requests-futures` |
| `No module named 'pkg_resources'` (dnsReaper, google-cloud-dns) | setuptools ≥ 81 **removed** pkg_resources | `pip install "setuptools<81"` |
| `SyntaxError` on `print "text"` in a cloned repo | repo is Python 2 | check the major version BEFORE installing; **`lib2to3`/`2to3` was removed in Python 3.13**, so auto-conversion is not an option — use a py3 alternative or hand that class to its skill + wordlist |
| `ModuleNotFoundError` for the repo's own package | script executed from outside the repo | add `cd /d "<repo>"` to the shim |
| `The filename... syntax is incorrect` in a `.bat` | path corrupted by `printf` escapes | rewrite the shim with `write_file` |
| `undefined: Node` building a `go install` tool | package needs CGO, no C compiler present | `command -v gcc cc clang` FIRST; no compiler ⇒ skip the tool, don't claim it installed |
| `No module named X` right after X installed successfully | TWO Python 3.14 installs on this box; deps went to the interpreter the launcher does *not* use | resolve the launcher's interpreter, install there, then remove the broken duplicate so PATH resolves to the working one |
| `Errno 22 Invalid argument` opening a file that `ls` shows fine | Defender denies on *read* (not just exec) | same family as RULE 1 — move that tool to WSL or defang; distinguish from permissions (which would block consistently) |
| `ModuleNotFoundError: No module named 'dns.asyncresolver'` (dnsReaper) | **dns** imports fine because an **ancient `dnspython 1.16`** (2018) is installed; `dns.asyncresolver` only exists from 2.0, and plain `pip install dnspython` is a no-op because the package is "already satisfied" | `pip install --upgrade "dnspython>=2.4"` — verify with `python -c "import dns.asyncresolver, dns.version; print(dns.version.version)"` |
| `ModuleNotFoundError: No module named 'botocore.vendored.six.moves'` (dnsReaper → providers/aws.py → boto3) | **botocore 1.13** (2019) still ships `vendored.six`; modern botocore dropped it | `pip install --upgrade "boto3>=1.34" "botocore>=1.34"` — after both upgrades dnsReaper prints its banner + usage |
| A tool's wrapper resolves and executes, yet the tool fails | the *wrapper* is fine; the **tool's own dependencies** are stale — check versions, not paths | `pip show <dep>` and compare against the Python feature the traceback names (this is what made `dnsreaper` look path-broken while `dnsreaper.bat` was perfect) |
| the file is **gone** (`No such file or directory`) after an earlier `Errno 22` | Defender **deletes** payload-bearing files, it does not only lock them | re-clone the repo once AV is off, then redo the config steps (`nikto.conf`, modules) |
| `ruby.h: No such file or directory` building a gem, though `include/ruby-<ver>/ruby.h` exists | the generated **Makefile carries MSYS-style include dirs** (`/D/Ruby40/...`) that Windows gcc cannot resolve. `ridk install 3`, `ridk exec`, `--with-cppflags` and `--platform` do **not** fix it (all four tried, all four failed) | rewrite the paths in the Makefile (`/D/Ruby40` → `D:/Ruby40`), then `ridk exec make` — re-runnable: `scripts/fix-gem-ext.bat <gem> <version>` |
| `make failed, exit code 2` with nothing but *warnings* in the log | gem builds with `-j5` and the real error scrolls off | re-run `ridk exec make` **serially** in the ext dir to surface the true first error |
| `Could not find '<gem>' (~> x.y) among N total gem(s)` though files exist and `require` works | hand-built gem has no gemspec and/or no `gem.build_complete` | stub `specifications/<gem>-<ver>.gemspec`; carry the `.so` into `extensions/<arch>/<ver>/<gem>-<ver>/`; touch `gem.build_complete` |
| `Could not open library 'libcurl'` (error 126) — ethon/wpscan | FFI needs a UCRT-compatible DLL; git-bash's `libcurl-4.dll` is MSVCRT, and 126 = *dependency* missing, not file missing | `curl.se/windows` `libcurl-x64.dll` (NOT the `win64a` asset) → `D:/Ruby40/bin/libcurl.dll`; shim prepends the mingw64 runtime dir |
| `Could not find 'fiddle' (~> 1.1)` (Ruby 4.0) | **fiddle is no longer a default gem in Ruby 4.0** | build it like any native gem: `fix-gem-ext.bat fiddle 1.1.8` + stub spec |
| `Compilation failed in require ... App/Cpan.pm` | git-bash `cpan` is broken and `pacman` is absent | pure-Perl modules need no cpan: unpack the CPAN tarball and copy the `.pm` into `@INC` |
| `Could not find a valid nikto config file` with the config present | script resolves sibling dirs from the **cwd** | make the shim `cd /d "<program dir>"` first (nikto, joomscan) |
| `KeyError: 'argvals'` from `jwt_tool.py` (any mode) | stale `~/.jwt_tool/jwtconf.ini` from an older schema; its self-repair `createConfig()` also dies on modern Python (`configparser.InvalidWriteError: ... contains delimiter :`) so it can never regenerate | write a minimal ini **by hand** over `~/.jwt_tool/jwtconf.ini` with `[crypto] [customising] [services] [input] [argvals]` — drop the comment-keys that contain `:`. Keep `proxy = False` / `redir = False` unless you actually run one |
| `[-] No substitution occurred - check that a token is included in a cookie/header in the request` (jwt_tool) | the tool has no place to inject the forged token | pass the JWT as the **positional STRING** (a file path yields an empty `Original JWT:`) **and** give it a carrier: `-rh "Auth…: Bearer <tok>"` (or `-rc` cookie). Then it really sends and prints `Response Code: 401, NN bytes` |
| `ModuleNotFoundError: No module named 'urllib3.packages.six.moves'` on `import requests` | broken/old urllib3 (1.x with its vendored six missing) | `pip install --force-reinstall --no-deps "urllib3>=2.2,<3"` — this is what silently disabled jwt_tool's "Python Requests libraries not imported" path |
| a cloned tool's wrapper exists in a PATH dir but `shutil.which('<tool>')` still returns `None` | extensionless wrapper; PATHEXT-aware callers need an extension | add a `<tool>.cmd` twin beside it (see the shim section above) |
| `ERROR: No matching distribution found for graphql-cop` | **`graphql-cop` is not published on PyPI under that name** (the console script is `graphql-cop.py`, the package is not installable) | git-clone it, then install its pins: `git clone --depth 1 https://github.com/dolevf/graphql-cop.git tooling/graphql-cop && python -m pip install -r tooling/graphql-cop/requirements.txt` → run as `python tooling/graphql-cop/graphql-cop.py -t <url>`. The pins are old (`requests==2.25.1`, `simplejson==3.17.6`, `termcolor==2.2.0`, `PySocks==1.7.1`) and install fine on 3.14; if you install piecemeal the tool dies one import at a time (`No module named 'simplejson'`, then `'termcolor'`) — read the traceback bottom-up and just install `-r requirements.txt` |

**Per-tool sources, exact commands, and the wrong-module-path traps** (gitleaks, kiterunner,
the no-"win"-in-the-asset-name problem, jar mirrors, the two-Pythons trap, semgrep's
`mcp==1.29.0` pin): `references/web2-toolkit-install-recipes.md`. Read it before installing a
batch — several upstream paths look right and fail.

### Already repaired on this host — do NOT re-avoid or re-diagnose

Every item below was broken once, was FIXED, and is verifiably working. A stale "tool X is
broken" note (in memory or a handover) sends the next session down a solved path or makes it
route around a working tool — re-probe instead of trusting the note.

| tool | was | now |
|---|---|---|
| `semgrep` | ImportError chain (`httpx_sse`, `pydantic_settings`, `sse_starlette`) then `mcp` 2.x vs the required 1.29.0 | working — the real cause was **two Python 3.14 installs**; deps belonged to the interpreter the launcher uses, and the shadowing install had to be removed. Fix the interpreter, not the package. |
| `cloud_enum` | `ModuleNotFoundError: requests_futures` | working |
| `dnsreaper` | `No module named 'pkg_resources'` (setuptools ≥ 81) | working |
| `nikto` | AV had **deleted** `nikto.pl`; then `XML::Writer` missing (dead `cpan`); then no `nikto.conf`; then config-not-found from the wrong cwd | working — `nikto -Version` → 2.6.1 |
| `wpscan` / `WhatWeb` | six stacked failures (yajl Makefile paths, missing specs, `fiddle`, ethon/libcurl) | both working; see `references/ruby-perl-runtime-setup.md` |
| `kiterunner` (`kr`) | no Windows release asset | built from source (`./cmd/kiterunner`) |
| `gitleaks` | wrong module path | working (`zricethezav/gitleaks/v8`) |

Rule of thumb: **re-probe before believing any "broken" claim**, including one you wrote
yourself. The cost of a probe is seconds; the cost of routing around a working tool is the
whole class of work it covered.

### ⛔ Registry/verifier can report WORKS while the tool silently never ran (2026-10-13)

Operator asked *"Path tools msh ad yg hilang? Kn udh dperbaiki bolak balik"* — the honest answer
was yes, and the failure was **in the verifier itself**, not in any single tool. Three defects,
all in `tool-health-probe.py` / `tools-registry.json`, all producing confident false verdicts:

1. **The registry recorded no path.** Every entry was a bare `{"status": "WORKS"}` — `path` was
   never persisted, so a status inherited from the *router's* view could never be re-derived from
   disk. A binary could move and the registry still said WORKS. `verified_at` was also stale
   (2026-10-11) while the shims had migrated on 10-12.
   **Fix:** persist `declared_path` + `path_exists` on every verdict, and add two hard statuses —
   `PATH_MISSING` (router's declared path absent from disk) and `NO_PATH_RECORD` (router declares
   no path at all). A missing binary is now a visible fact, never an inherited opinion.
2. **The probe hard-coded its own paths instead of using `TOOL_PATHS`.** Entries like
   `python "<HOME>/AppData/Local/hermes/tools/smuggler/smuggler.py"` pointed at a directory that
   does not exist (the repos live under `D:/data hermes/tools/...` behind a `.cmd` shim). The
   probe therefore reported **BROKEN** for `smuggler`, `sstimap`, `ssrfmap`, `graphqlmap` while
   those tools ran perfectly through the router. **Fix:** build every probe command from
   `P("<tool>")` (the router's own resolved path), never a hand-typed literal.
3. **argparse rejection was classified as BROKEN.** A tool that prints `error: the following
   arguments are required` has *parsed its own command line* — it is RUNNING, and only the probe's
   flags were wrong. Same for `unrecognized arguments`. **Fix:** separate `ARGPARSE_SIGNAL` from
   `BAD_OUT` and return status `RUNS_BAD_FLAGS`. Also: probe the real binary, not an alias
   (`kr --help` → `kiterunner.exe --help`), and never probe a `.bat` wrapper with
   `python -c "import <name>"` (`DNSReaper` is a wrapper, not an importable module).

**Diagnostic recipe when a verify/gate tool reports PASS but coverage looks thin:**

```bash
# 1. does the registry even store a path?
python -c "import json,os;d=json.load(open(os.path.expanduser('~/AppData/Local/hermes/tools-registry.json')));\
k=[t for t,v in d['tools'].items() if not v.get('declared_path')];print('no path:',len(k),k)"
# 2. does every path the ROUTER declares exist on disk?
python -c "import importlib.util,os;s=importlib.util.spec_from_file_location('t',os.path.expanduser('~/AppData/Local/hermes/scripts/tool_router.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);\
print([ (n,p) for n,p in m.TOOL_PATHS.items() if not (p and os.path.exists(p)) ])"
# 3. run ONE probe command by hand and read the body — not the exit code
```

**Cross-check the auditor's own variables before trusting its findings.** The first audit in that
session reported *21 missing shims*; the bug was the auditor's own `SCRIPTS` variable pointing at
`hermes/scripts` instead of `Python314/Scripts` where the `.bat` shims actually live. Two of the
three defects above were the same mistake in different clothes. When an audit says "everything is
missing", **suspect the audit** before rewriting the tools.

**Runtime-bound batch (Ruby / Perl)** — RubyInstaller silent-install flags, `ridk` devkit init,
which gems are pure vs native, installing Perl modules when `cpan` is dead, and the full nikto
recipe: `references/ruby-perl-runtime-setup.md`. **Both CMS tools ended up WORKING**
(WhatWeb ✅, wpscan 4.1.0 ✅ — wpscan needed six fixes, none of them a Ruby downgrade; the
"install an older Ruby" theory is disproved there).

**`scripts/fix-gem-ext.bat <gem> <version>`** — the re-runnable fix for any native gem that dies
with `ruby.h: No such file or directory`. Rewrites the MSYS-style paths mkmf puts in the
generated Makefile, builds, and registers the result (`gem.build_complete`) so RubyGems
activation stops reporting the gem as missing. Use it before reaching for a second Ruby install.

## RULE 2 — Paths with spaces break Windows tooling

`D:\data hermes\...` breaks `cmd /c` one-liners, NSIS silent installs (`/S` silently no-ops), and
some launchers.

| Tool | Fix |
|---|---|
| gcloud SDK | set user env `CLOUDSDK_ROOT_DIR` + `CLOUDSDK_PYTHON`; run `python <sdk>/lib/gcloud.py --version`; or `cmd /c "cd /d \"<dir>\" && gcloud.cmd --version"` |
| NSIS installer (nmap, npcap) | prefer the **ZIP** distribution (`nmap.org/dist/nmap-*-win32.zip`); or copy the `.exe` to a space-free path (`C:\Users\<u>\x.exe`) first |
| `.bat`/`.cmd` from bash | bash can't run them (`@if: command not found`) — call via `cmd.exe /c` or a sibling wrapper `.bat` |

**npcap needs admin (UAC).** Without it nmap works in `connect()` mode (`-sT`); after the npcap
driver service is Running it gains `-sS`/OS-detect. Verify with `nmap --version` (no warning = good).

## RULE 2b — MSYS path-conversion mangles curl/tool args (git-bash)

The `terminal` tool runs git-bash (MSYS), which rewrites any argument that *looks* like a POSIX
path into a Windows path. This silently corrupts output and file writes:

- `-w "/path -> %{http_code}"` → the leading `/` becomes `C:/Users/.../git/...`, so your label is
  garbage (looks like `C:/Users/<u>/AppData/Local/hermes/git/.git/HEAD -> 404`). **Fix:** never
  start a `-w`/`--write-out` string with `/` — prefix it (`-w "R$p -> …"`), or set
  `MSYS_NO_PATHCONV=1`.
- But `MSYS_NO_PATHCONV=1` then **breaks `-o /dev/null`** (Windows curl gets a literal `/dev/null`
  and can't open it) → `curl: (23) client returned ERROR on write`. **Fix:** with NO_PATHCONV on,
  write with a Windows path (`-o "C:/Users/<u>/tmp/x.out"`) or use `-o NUL`. Best pattern: leave
  NO_PATHCONV **unset** and just avoid a leading `/` in `-w` — URLs (`https://…`) are never
  converted, so URL args are always safe.

Same class hits any tool arg beginning with `/` (wordlist paths, output paths). Sanity-check a
batch of curls against one known URL before trusting the numbers.

## RULE 2c — With `MSYS_NO_PATHCONV=1` ON, hand Windows binaries NATIVE paths (or they get a doubled drive)

The mirror image of RULE 2b, and the single most expensive trap of the Vana session (2026-10-12): once
`MSYS_NO_PATHCONV=1` is exported (which the audit pipeline and most of these recipes set), bash-expanded paths
are passed through **verbatim** to Windows programs that cannot read them.

| You typed | Windows program received | Symptom |
|---|---|---|
| `python ~/AppData/Local/hermes/skills/.../asset-coverage.py` | `D:\c\Users\<u>\AppData\...` | `can't open file 'D:\\c\\Users\\...': [Errno 2]` |
| `python "$(command -v tool)` (a `/c/...` path) | `/c/Users/...` | `WinError 2 The system cannot find the file specified` |
| `slither x.sol --solc "$(command -v solc)"` | `/c/Users/.../Scripts/solc` | crytic-compile `InvalidCompilation: [WinError 2]` — looks like a `solc` bug, is a path bug |
| `qa_pdf_layout.py /d/data ...` (MSYS path arg) | `D:\d\data ...` | file-not-found on a file that exists |

**Fix (pick one, per call):**

```bash
# A) native paths everywhere a Windows program is on either side of the call
SP="C:/Users/<u>/AppData/Local/hermes/scripts";  PY="C:/Users/<u>/AppData/Local/Programs/Python/Python314/python.exe"
"$PY" "$SP/asset-coverage.py" "D:/data hermes/bug-bounty/<engagement>" --phase 0C
slither "$F" --solc "C:/Users/<u>/AppData/Local/Programs/Python/Python314/Scripts/solc.exe"
# B) inside Python, never `~`: %LOCALAPPDATA%/%APPDATA% via expandvars (they hold Windows paths)
python -c "import os,pathlib;print(pathlib.Path(os.path.expandvars(r'%LOCALAPPDATA%\hermes\google_token.json')))"
# C) when you need the POSIX form for bash but a native form for the tool: convert explicitly
native() { cygpath -w "$1" 2>/dev/null || echo "$1"; }   # then pass "$(native ...)"
```

Also from the same session: **`solc-select` binary this build does not accept `--solc-select`** (argparse
rejects it) — set the version globally (`solc-select use 0.8.24`, verify with `solc --version`) and pass the
**native path to the shim** `.../Python3XX/Scripts/solc.exe` via `--solc`. And **`kiterunner brute <arg>`
treats its positional arg as a FILE unless it is a bare hostname**: `kiterunner brute https://host` →
`failed to open file: open https://host: The filename, directory name, or volume label syntax is incorrect`.
Pass `host.tld` or a file of hosts (`-w wordlist.txt hosts.txt`), and read results from stdout/log because
this build wrote no JSON at the `--output` path.

## RULE 3 — WSL pitfalls

- **One unknown package aborts the whole apt transaction** (`apt-get install a b netexec` installs
  *nothing* if `netexec` isn't in the repo). Install in groups; probe names first.
- Driving a long apt/pip run from Windows: **redirect a script into it** —
  `wsl -d <distro> -u root -e bash < script.sh > out.txt 2>&1` — inline quoting through
  `bash -lc` mangles large payloads.
- `--user` installs land in `~/.local/bin` — export it inside every `bash -lc`.
- `netexec`/`nxc` is **not on PyPI** → the pipx/git route above.
- First boot can take minutes; a wedged VM returns `Wsl/Service/CreateInstance/CreateVm/ERROR_TIMEOUT`.
  Recovery: `wsl --shutdown` from a normal terminal (not via the agent), or reboot.

## RULE 4 — Persistent PATH edits: use PowerShell, never `setx`

`setx` truncates PATH at 1024 chars and this box has a long PATH. Use (idempotent, additive):

```powershell
$cur = [Environment]::GetEnvironmentVariable('Path','User'); if ($null -eq $cur) { $cur = '' }
$parts = $cur -split ';' | Where-Object { $_ -ne '' }
$t = 'D:\data hermes\tools\nmap\nmap-7.92'
if ($parts -notcontains $t) { [Environment]::SetEnvironmentVariable('Path', (($parts + $t) -join ';'), 'User') }
```

New shells pick it up; no restart needed.

## Related

- `bb-local-toolkit` — the bug-bounty workflow whose TOOLS section names tools. **It is user-owned**,
  so install-path corrections that belong there need `hermes curator adopt bb-local-toolkit` rather
  than an autonomous write.
- Tool inventory + WSL recovery notes also live at
  `skills/security/exploit-cookbook/references/tool-install.md`.