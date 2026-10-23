# Shell Checks

## Purpose

Language checks for sh, bash, and zsh targets, for SKILL.md Step 4. Load this file at the start of Step 4 when the fact sheet's Language(s) row lists shell code, before the manual checks. Each section names the view its hits usually feed; every hit still gets a ledger row (`scoring-procedure.md`).

---

### Security checks

- **Injection sinks:** `eval`, `sh -c "$var"`, `bash -c`, unquoted `$var` in command position, backticks or `$(…)` around untrusted data, `xargs` without `-0`, and `find -exec sh -c '… {}'`.
- **Unquoted variables in `rm`/`mv`/`chown`:** `rm -rf $dir/` with `$dir` empty becomes `rm -rf /`. Check for `${var:?}` guards.
- **Temp files:** `/tmp/name` as root means symlink races. Expect `mktemp` plus a `trap 'rm -f "$tmp"' EXIT`.
- **Process-list exposure:** secrets in command-line args (`curl -u`, `-H "Authorization: …"`, `security add-generic-password -w pass`). Prefer stdin, `--config`, or `-K -`.
- **`set -x` / `xtrace`** combined with secrets means secrets end up in logs.
- **`sudo` inside a root script** is usually redundant. `sudo -u user` without `launchctl asuser` is a context bug, not a privilege drop into the GUI session.
- **zsh indirection is a sink:** `${(P)name}` evaluates a subscript in `name`, including `$(…)`, when the base variable is set; `printf -v "$name"` evaluates it even when unset (zsh 5.9: with `fooX` set, `n='fooX[$(id>out)]'` ran `id` through `${(P)n}`; with it unset, `${(P)n}` ran nothing but `printf -v` still ran `id`). Any variable name built from root-read, user-controlled data, such as the console user's own preferences (`AppleLanguages`, `~/Library/Preferences/…`), is code injection. Case folding (`:l`, `(C)`) doesn't neutralize it: APFS is case-insensitive by default, so `Id` runs `/usr/bin/id`. Fix with an allowlist regex before use, or an associative array keyed by the value.
- **zsh specifics:** `setopt` changes can alter word splitting. `$=var` forces splitting. Unquoted `$var` doesn't word-split in zsh the way it does in bash, but it does glob, and empty vars vanish.

### Engineer checks

- **Identify the dialect from the shebang** and hold the code to that dialect. `#!/bin/sh` on macOS is bash 3.2 in POSIX mode by default (switchable to dash via `/private/var/select/sh`). Flag bashisms or zshisms under `sh`.
- **Shellcheck-class issues:** unquoted expansions (SC2086), `cd` without `|| exit` (SC2164), `read` without `-r` (SC2162), `$(…)` inside `[ ]` without quotes, `local var=$(cmd)` masking the exit code (SC2155), `for f in $(ls)`, and `[ $var == x ]` in `sh`.
- **Error handling:** `set -euo pipefail` (bash) or `setopt ERR_EXIT PIPE_FAIL NO_UNSET` (zsh). Note that `set -e` is disabled inside `if`, `&&`, `||`, and functions called in those contexts. Suggest explicit checks for critical commands rather than relying on `-e` alone.
- **zsh vs bash differences:** arrays are 1-indexed in zsh and 0-indexed in bash. Unquoted vars don't word-split in zsh unless `SH_WORD_SPLIT` is set. `read -p` means something different in zsh. zsh has `print -u2` and `${var:A}`. `[[ ]]` behaves differently with `=~` captures (`$match` vs `BASH_REMATCH`).
- **Traps:** check that a `trap … EXIT` exists for temp files, locks, and caffeinate/`dialog` PIDs.
- **Exit codes:** make sure the script's final exit code reflects failure. Look for a terminal `exit 0` that masks earlier errors.
- **Idempotency:** `mkdir -p`, `ln -sf`, `defaults write` (idempotent) vs `>>` appends, `dscl -append`, and `sysadminctl -addUser` (not idempotent).

### Manager checks

- Check the header block for author, version, and changelog. Mac admin scripts commonly carry `# Version`, `# Author`, and `# Changelog` headers. Stale ones (the version string doesn't match the changelog) are a maintenance signal.
- A long single-file script (over 500 lines) with no functions means high change risk.
- Note hardcoded org values (URLs, org names, support phone numbers, Jamf server URLs) as coupling that needs a change when environments differ.
