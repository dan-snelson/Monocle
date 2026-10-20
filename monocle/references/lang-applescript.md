# AppleScript Checks

## Purpose

Language checks for AppleScript and `osascript` targets, for SKILL.md Step 4. Load this file at the start of Step 4 when the fact sheet's Language(s) row lists AppleScript or `osascript` calls, before the manual checks. Each section names the view its hits usually feed; every hit still gets a ledger row (`scoring-procedure.md`).

---

### Security checks

- **`do shell script "…" & userInput`** without `quoted form of` leads to shell injection.
- **`with administrator privileges`** prompts for credentials or runs as root. Rate a `password "…"` literal with **Credential severity** in `security.md` (hardcoded row).
- **`display dialog … default answer`** used to collect passwords invites credential phishing. Note whether `with hidden answer` is set and where the value goes.
- **`System Events` / UI scripting** requires an Accessibility (TCC) grant. Check whether a PPPC profile grants it broadly.
- **`run script` / `load script`** from a user-writable path, when run as root, is privilege escalation.

### Engineer checks

- **Quoting:** every value passed into `do shell script` needs `quoted form of`. Show the corrected line.
- **Error handling:** `try … on error errMsg number errNum … end try`. Flag empty `on error` blocks.
- **Timeouts:** `with timeout of N seconds` around app-driven commands. The default of 120 s causes hangs.
- **Context:** `osascript` run as root can't show UI in a user session. Use `launchctl asuser`. `tell application "System Events"` needs a TCC grant.
- **Output parsing:** `do shell script` returns text with `\r` line endings in some contexts, and `paragraphs of` behaves differently than splitting on `\n`.
- **Maintainability:** in shell scripts, prefer heredoc `osascript <<'EOF' … EOF` over long chains of `-e` arguments.

### Manager checks

- `.scpt` files are compiled and hard to diff or review in git. Recommend storing `.applescript` source instead.
- Dependence on UI scripting (`System Events`, clicking menu items by name) breaks with app updates and localization. Rate it high fragility.
