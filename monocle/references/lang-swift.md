# Swift and Objective-C Checks

## Purpose

Language checks for Swift and Objective-C (macOS helpers, daemons, GUI apps) targets, for SKILL.md Step 4. Load this file at the start of Step 4 when the fact sheet's Language(s) row lists Swift or Objective-C code, before the manual checks. Each section names the view its hits usually feed; every hit still gets a ledger row (`scoring-procedure.md`).

---

### Security checks

- **`Process` with `executableURL` and an `arguments` array** doesn't use a shell, so it's safe from injection. Credit it. `/bin/sh -c` or `/bin/zsh -c` with an interpolated string isn't.
- **`Process` calling `/usr/sbin/chown` or `/bin/chmod`** without `-h` follows symlinks, exactly as in shell. Check the path's directory for user write access (SKILL.md Step 4, shared-directory trust).
- **`Darwin.open` / `open(2)` flags:** a root writer without `O_NOFOLLOW` (and `O_CLOEXEC`) follows a planted symlink, and `O_CREAT` creates the target. Prefer `fstat` ownership checks plus `fchown`/`fchmod` on the descriptor over path-based calls.
- **`FileManager`:** `copyItem` copies a symlink as a link, so a later `zip -r` dereferences it. `createFile(atPath:)` and `Data.write(to:)` on a fixed path in a shared directory follow symlinks. `.atomic` writes replace the file through a temporary file, which is safer for the target but still trusts the directory.
- **Root reading user-controlled plists:** `NSDictionary(contentsOfFile:)` or `UserDefaults` on `~/Library/Preferences/…` inside a root daemon is untrusted input. Check what reaches a sink (process arguments, paths, URLs), and credit allowlist filtering when it's present.
- **Privileged helpers:** SMAppService or `SMJobBless` daemons run as root. Check that the XPC listener validates the client's code-signing requirement (`setCodeSigningRequirement` or an audit-token check) before acting on requests, and that job files dropped into a shared directory are owner-checked.
- **Pipe deadlock:** calling `readDataToEndOfFile()` only after `waitUntilExit()` hangs once the child fills the pipe buffer (about 64 KB). This is an Engineer footgun, not a security finding.
