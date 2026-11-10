# forge ≥1.7 build-info, fuzzer invocation, and deployed-source verification

Session-proven detail (SSV Network, 2026-10) for the three things that block the standard toolchain on a
modern Foundry repo, plus the correct way to compare a deployed contract against a source tree. Companion
detail lives in the `live-vs-source-bytecode-forensics` skill.

---

## 1. ⛔ `forge` ≥1.7 `--build-info` breaks crytic-compile (slither / aderyn / echidna / medusa)

`forge` ≥1.7 writes `out/build-info/<id>.json` as **only** `{id, source_id_to_path, language}`. That is
NOT the hardhat-shaped `{solcVersion, input, output}` that `crytic-compile` 0.4.2 expects
(`foundry.py` → `hardhat_like_parsing` → `get_targets_json`).

Symptoms, in the order you hit them:

| attempt | result |
|---|---|
| `slither .` | `FileNotFoundError: .../out/build-info/<id>.output.json` |
| `slither .` (after creating a stub `.output.json`) | `KeyError: 'output'` |
| `slither . --compile-force-framework solc` | `contracts is a directory. Expected a Solidity file when not using a compilation framework.` |

**Fix — synthesise the shape yourself:**

1. Read `source_id_to_path` from the compact build-info; build a standard-JSON input using those paths as
   source-unit names, the project's real remappings, and `optimizer{runs}`, `viaIR`, `evmVersion` copied
   from `foundry.toml`. Request `abi, evm.bytecode, evm.deployedBytecode, evm.methodIdentifiers, devdoc,
   userdoc, metadata, ast`.
2. Run `solc --standard-json` yourself (Windows binary: download `solc-windows.exe` for the exact
   version from the solidity GitHub release).
3. Overwrite `out/build-info/<id>.json` with `{"id", "solcVersion", "input", "output"}`, and delete any
   `<id>.output.json` you created while debugging so the parser uses the real file.

Then `slither . --compile-force-framework foundry --foundry-ignore-compile` works normally.

**Gotcha that silently truncates results:** keep `solcVersion` a **bare** `0.8.24`. Slither's
`incorrect-solc` detector does `int()` on it and dies on `0.8.24+commit.e11b9ed9` with
`ValueError: invalid literal for int() with base 10: '24+commit'` — and it dies *after* several detectors
have already printed, so a truncated run is easy to mistake for a complete one. Distinguish the two by
the run's **final summary line** (`analyzed (N contracts with M detectors), K result(s) found`): present
= complete; a traceback instead = incomplete.

Also: `slither` can exit **127 while the analysis fully succeeded** — do not discard the run on `$?`.
Verify by the summary line + the `--json` artifact.

---

## 2. Fuzzer invocation that bypasses the build-info entirely

`echidna` compiles a single harness file directly, so a vendor's own property harnesses run unmodified:

```bash
echidna test/echidna/X.sol --contract X --test-mode property --test-limit 4000 --seq-len 100 \
  --crytic-args "--compile-force-framework solc --solc-remaps @openzeppelin=node_modules/@openzeppelin"
```

Notes that cost time when missed:

- **Property-prefix trap.** echidna collects `echidna_*()`; medusa's property mode collects
  `property_*()`. A vendor suite written for echidna therefore yields **0 properties** under medusa —
  running it proves nothing and its green output is meaningless. Check the prefix before budgeting time.
- **medusa 1.5.1 has no `--crytic-args` CLI flag**; crytic args live in the config file.
- **Coverage caveat to read with the green ticks.** echidna logs
  `Running slither failed. Echidna will continue, however fuzzing will likely be less effective.` when its
  slither-guided fuzzing is off. Grep every log for that line: in one 16-harness batch it appeared in
  exactly **one** harness (15 ran guided). A degraded run is "no counterexample in a degraded campaign",
  **not** "the invariant is safe" — and a rerun of the same file reproduced the failure deterministically,
  proving it was the file + echidna's internal invocation, not memory pressure (slither run *directly* on
  that file analysed it fine).
- Do **not** derive a severity mix from slither's console output — it carries no `Impact:` field, so
  counting High/Medium there is a formatting artefact, not a measurement. Use `--json` and parse it.

---

## 3. halmos: the viaIR thrash trap

Adding a test file that imports a vendor's whole echidna suite forces a recompile of the entire test unit.
On a `viaIR = true` project (>100 sources) that can swap-thrash for 30+ minutes while writing **zero**
artifacts.

Detect before waiting: `find out -name '*.json' -newermt '-5 minutes' | wc -l` — `0` new artifacts plus a
pinned CPU means it is not progressing, it is thrashing. Kill it, drop the vendor-suite import (use a
minimal self-contained harness), and record the aborted run as a **tooling GAP with the cause** — never as
a clean result. Kill orphaned children too (`solc-*.exe`, `forge.exe` survive the parent and keep the box
saturated).

Good pattern when it *does* run: reuse the vendor's own harness instead of authoring a spec —
drive their `action_*` functions with symbolic arguments and assert their `echidna_*` properties, wrapping
each action in `try/catch` so an infeasible symbolic input is not counted as a revert-counterexample.

---

## 4. Comparing a deployed contract to a source tree — compare the CODE SECTION, not the length

Never treat a bytecode-length difference as proof that the deployed build differs from the source.

Solidity appends CBOR metadata that embeds the **source paths of the contract's dependency closure**. A
build whose paths are `project/contracts/...` (the usual verifier-db layout) is *longer* than one using
`contracts/...` with byte-identical code. On SSV Network this manufactured a fake "+231 bytes of
unexplained live code" that collapsed to **0 differing bytes** once the tree was recompiled with its
original paths + `npm/@openzeppelin@4.9.6` + `forge-std@1.9.4`.

Procedure:

1. Recover the live source from `https://eth.blockscout.com/api/v2/smart-contracts/<ADDR>`
   (`source_code`, `additional_sources[]`, `compiler_settings` with remappings/viaIR/optimizer runs).
2. Recompile that tree with those exact settings and its original paths.
3. Compare `deployedBytecode` vs `cast code <ADDR>`. **Equal length + code section identical + only the
   trailing metadata hash differing = same code.**
4. If the code section genuinely differs, pin the deployed build's branch before writing anything up:
   `git ls-remote --heads origin`, then per candidate `git diff --stat <audited-commit>..<branch> -- contracts/`.
   On SSV the whole live-vs-audited delta was `main` + **10 lines** living in a public `deploy/hotfix`
   branch — worth knowing before claiming "the deployed code is unaudited".

Related trap: a contract that does **not** use a given constant or library still verifies against a source
tree carrying a *different* version of it, so a module's own verification bundle can contain stale copies
of files it does not affect. Only files that change that contract's codegen are evidence.

Path trap on Windows/MSYS: `curl -o /tmp/x` (a Windows binary) writes `C:\tmp\x` while `head /tmp/x`
(MSYS) reads `C:/Users/<u>/AppData/Local/Temp/x` — so you can read a **stale file from an earlier write
and mistake it for this response's body**. Use explicit or relative paths for anything you then read back.
