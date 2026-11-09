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
- **Privileged helpers:** SMAppService or `SMJobBless` daemons run as root, and every method they export is a root operation for whoever passes the client check. Check that job files dropped into a shared directory are owner-checked, then work through the helper checks below.
- **Pipe deadlock:** calling `readDataToEndOfFile()` only after `waitUntilExit()` hangs once the child fills the pipe buffer (about 64 KB). This is an Engineer footgun, not a security finding.

### Privileged helpers and local IPC

The attacker is another local account, a process running as the console user, or a web page, not the helper's own GUI app. Name which one can reach each method.

- **Client identity by audit token, not PID.** The listener should check the connection with `setCodeSigningRequirement` (macOS 13+) or a `SecCode` lookup by audit token (`kSecGuestAttributeAudit`), then `SecCodeCheckValidity`. A lookup by `processIdentifier` (`kSecGuestAttributePid`) checks whatever process holds that PID at lookup time, and a PID can be reused between the check and the request.
- **Requirement strength.** `anchor apple generic` alone matches any code signed with an Apple-issued certificate, every Developer ID included. The requirement should pin the Team ID (`certificate leaf[subject.OU] = "TEAMID"`) and the client's identifier.
- **Injectable trusted client.** A client signed without hardened runtime, or with the `com.apple.security.cs.disable-library-validation`, `com.apple.security.cs.allow-dyld-environment-variables`, or `com.apple.security.get-task-allow` entitlement, can load attacker code and still satisfy the requirement. Read the client's signing flags and entitlements in the repo (`--options runtime`, `.entitlements` files). An older signed build without these protections still matches a requirement that has no version floor.
- **Confused deputy.** An exported method that takes a path, command, URL, script, package, or user name from the client must validate the normalized argument itself: resolve symlinks and `..`, then compare against an exact allowlist. A `hasPrefix` check on the unresolved path, or a generic `run`, `write`, or `install` method, gives root to any client that passes the identity check.
- **Verify, then use the same file.** A helper that checks a signature on a client-supplied path, then installs or runs that path, re-opens a file the user can replace in between. Copy it into a root-owned directory first, then verify and use the copy.
- **Authorization rights.** When the helper relies on an authorization prompt, it should rebuild the reference with `AuthorizationCreateFromExternalForm` and call `AuthorizationCopyRights` for a specific right before each privileged operation, not once per connection. `AuthorizationExecuteWithPrivileges` is deprecated; flag it, and check what it runs and from which path.
- **URL schemes and Apple events.** `CFBundleURLTypes` handlers (`application(_:open:)`, `kAEGetURL`) receive URLs from any web page or app. A handler that changes settings, runs commands, or calls the helper from URL parameters without user confirmation is a remote-content-to-local-action path.
- **Local listeners.** A Unix socket or loopback TCP listener (`NWListener`, `bind`) is reachable by every local account, and loopback TCP by browser pages. Check peer authentication before any action: `getpeereid` or `LOCAL_PEERCRED` for Unix sockets, a per-session secret for TCP. Check the socket file's directory and mode as a shared path.
- **Rating.** Through the Decision procedure in `security.md`: a helper method that gives a local user root with no race is 🟠 High; one that needs a race, such as a verify-then-install swap, is 🟡 Medium.
