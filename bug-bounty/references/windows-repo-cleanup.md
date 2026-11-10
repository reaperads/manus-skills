# Windows: Node_modules Deletion Pitfall

## The Problem
On Windows (Git Bash / MSYS), `rm -rf` on `node_modules` folders (especially large monorepos like Hardhat, Truffle, or Foundry with deeply nested symlinks, read-only files, and npm lockfiles) frequently fails with:

```
rm: cannot remove '.../node_modules/...': Permission denied
```

This happens even after killing all running processes — Windows file indexing (SearchIndexer), antivirus scanners, or lingering file locks from closed-but-not-released terminal processes can hold file handles.

## The Fix
Use the native Windows `rmdir` command via `cmd` instead of bash `rm`:

```bash
# Step 1 (optional): Remove hidden/system/read-only attributes recursively
attrib -r -s -h /s /d 2>&1 | head -3

# Step 2: Delete using native cmd rmdir (unblocks Windows file locks)
cmd /c rmdir /s /q "D:\\data hermes\\bugbounty\\target-repo" 2>&1
```

### MSYS `cmd //c` path caveat
MSYS automatically converts `D:/path/to/dir` to `C:\D:\path\to\dir` — always pass the Windows path in `\\` backslash format inside double quotes:
```bash
# WRONG — MSYS converts to invalid C:\D:... path
cmd //c "rmdir /s /q D:/data hermes/bugbounty/paxos"

# CORRECT
cmd /c rmdir /s /q "D:\\data hermes\\bugbounty\\paxos"
```

## When to Use
- After a target scan is abandoned (user says "delete this target" or "switch target")
- `rm -rf` fails with Permission Denied on node_modules
- Any large cloned repo that needs full recursive deletion on Windows

## Fallback
If `cmd /c rmdir /s /q` also fails:
1. Check `tasklist | grep -i node` — kill orphaned node processes
2. Open Task Manager → Details → kill `SearchIndexer.exe` temporarily
3. Retry `cmd /c rmdir /s /q`
4. Last resort: reboot, then delete
