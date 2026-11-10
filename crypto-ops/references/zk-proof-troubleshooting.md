# ZK Proof Troubleshooting — Tornado Cash

## Common Errors and Fixes

### `Invalid File format` (snarkjs)
**Cause**: Proving key or circuit file is in legacy format.
- Tornado releases v2.1 `withdraw_proving_key.json` → snarkjs 0.1.x format
- Tornado releases v2.1 `withdraw_proving_key.bin` → websnark format
- Neither works with snarkjs 0.7.x

**Fix**: Use `snarkjs@0.1.11` which reads the old format natively. The API is different:
```javascript
// OLD (0.1.x) — WORKS
const snarkjs = require('snarkjs');
const circuit = new snarkjs.Circuit(circuitDef);
const witness = circuit.calculateWitness(input);
const {proof, publicSignals} = snarkjs.groth.genProof(provingKey, witness);

// MODERN (0.7.x) — DOES NOT WORK
const {proof, publicSignals} = await snarkjs.groth16.fullProve(input, './circuit.wasm', './proving_key.zkey');
```

### `Invalid number of parameters: MiMCSponge`
**Cause**: circomlib version mismatch. Tornado circuits use MiMCSponge(nInputs, nOutputs) — 2 params. circomlib 2.x changed to MiMCSponge(nInputs, nRounds, nOutputs) — 3 params.

**Fix**: `npm install circomlib@0.5.5` (NOT 2.x).

### `Expecting 'EOF'` in circom compilation
**Cause**: npm `circom@0.5.46` cannot parse `pragma circom 2.0.0` syntax.

**Fix**: Use circom v2.x binary from iden3 GitHub releases:
```
https://github.com/iden3/circom/releases/download/v2.2.3/circom-linux-amd64
https://github.com/iden3/circom/releases/download/v2.2.3/circom-windows-amd64.exe
```

### `bash: no job control` + null char crash
**Cause**: Running `./circom.exe` directly in Git Bash triggers lifecycle guard.

**Fix**: `powershell -Command "./circom.exe circuits\\withdraw.circom --wasm --r1cs"`

### `WebAssembly.compile(): expected magic word`
**Cause**: `tornado.wasm` from GitHub raw is actually an HTML 404 page.

**Fix**: Compile WASM from circuit source: `circom withdraw.circom --wasm`

### ptau download 403 AccessDenied
**Cause**: Hermez S3 URLs for `powersOfTau28_hez_final_*.ptau` are access-restricted.

**Fix**: Generate locally: `snarkjs powersoftau new bn128 20 pot20.ptau` (~4GB file, hours of computation). Or skip entirely if using old snarkjs 0.1.x.

### Constraint doesn't match (during witness calculation)
**Cause**: Input values don't satisfy circuit constraints (expected with dummy/zero inputs).

**This is EXPECTED behavior** — means the circuit is working correctly. Real deposits with valid nullifier/secret will pass.

## File Compatibility Matrix

| File | Source | Format | Works with snarkjs 0.7.x? | Works with snarkjs 0.1.x? |
|------|--------|--------|--------------------------|---------------------------|
| `withdraw_proving_key.json` | Tornado releases v2.1 | snarkjs 0.1.x JSON | ❌ | ✅ |
| `withdraw_proving_key.bin` | Tornado releases v2.1 | websnark binary | ❌ | ❌ |
| `circuit.json` | Tornado releases v2.1 | circom JSON (not R1CS) | ❌ | ✅ |
| `tornado.wasm` | Compiled from source | WebAssembly | ✅ | ❌ |
| `withdraw.r1cs` | Compiled from source | R1CS binary | ✅ (for zkey gen) | ❌ |
| `withdraw.wasm` | Compiled from source | WebAssembly | ✅ | ✅ |
| `proving_key.zkey` | Generated from r1cs + ptau | snarkjs zkey binary | ✅ | ❌ |

## Proving Key Generation Time Estimates
- `snarkjs powersoftau new bn128 20` → ~4GB file, ~30-60 minutes
- `snarkjs zkey new withdraw.r1cs pot20.ptau` → Hours (4-12h depending on hardware)
- Total: Significant time + RAM investment for new zkey generation

## Recommended Approach
**Self-service works with old snarkjs 0.1.x** — no ptau needed, just install `snarkjs@0.1.11` and download `proving_key.json` from Tornado Cash releases.

For most use cases: **relayer API** is simpler (zero setup, ~0.5% fee). Self-service is better when:
1. You need to withdraw without revealing IP to relayer
2. You're operating at scale (many withdrawals)
3. You want full control over the withdrawal process
