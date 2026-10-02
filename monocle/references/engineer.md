# Engineer View

## Purpose

The Engineer view helps someone who will maintain, review, or extend the code:

- Understand how it actually works.
- See where it breaks.
- Know exactly what to change.

The reader is technical and has the code open next to your summary. Be precise, cite lines, and suggest refactors they can apply directly.

---

## Structure and tone

Use exactly this structure:

~~~markdown
## Engineer View

**Shape:** {language/dialect, ~N lines, M functions, entry point, invocation}
**Inputs → Outputs:** {args/params/env/files} → {files/prefs/services/exit codes/stdout}

### Control flow
1. {Step} — `file:line`
2. {Step, including branches: "if X → …, else → …"} — `file:line`
3. …

### Footguns
- **{Short name}** — `file:line` — {what goes wrong, and under what input or state}

### Edge cases not handled
- {Condition} → {actual behavior} — `file:line`

### Refactor suggestions
#### R1 — {Title}  ·  {Quick win | Deeper}
`file:line`
```{lang}
# before
…
```
```{lang}
# after
…
```
{One-line rationale.}

### Quick wins vs deeper work
- **Quick wins (< 1 hr):** R1, R3, …
- **Deeper work:** R2 — {why it's bigger}
~~~

Rules:

- **Tone:** direct and technical. Write like a senior engineer in a code review.
- **Control flow:** use 5–15 numbered steps. Cover branches, loops, early exits, and traps. Mention every function only if the file is small; otherwise cover the main path and the risky branches.
- **Footguns:** these are bugs or traps that already exist in the code, not stylistic preferences. Each one needs a trigger condition.
- **Refactors:** give up to 6 suggestions, each with a concrete benefit tied to a footgun, finding, or edge case. If none are justified, write "No refactors warranted." (SKILL.md Rule 7). Keep before/after snippets minimal: the changed lines plus 1–2 lines of context. Make sure they're syntactically valid for the dialect.
- **Use line references wherever you can.** If lines aren't reliable (for example, pasted snippets), use `function_name()` or a short quoted snippet.
- **Don't restate the Security view's findings in full.** Reference them ("see S2") and focus on the code-level fix.

---

## Key questions the summary must answer

1. **What is the entry point, and what's the order of operations?**
2. **What inputs does it trust, and are they validated?** Empty, missing, malformed, or containing spaces or special characters.
3. **What happens when each external command fails?** Is the failure detected, propagated, or ignored?
4. **Is it idempotent?** What happens on a second run, or on a run after a partial failure?
5. **What state does it assume?** User logged in, network up, file present, specific OS or architecture, tool versions.
6. **Where are the footguns?** Quoting, word splitting, globbing, race conditions, subshell variable loss, and exit-code masking.
7. **What would I change first,** and exactly how?

---

## Prioritization

Order footguns and refactors by:

1. **Data loss or destructive misbehavior.** Examples: `rm` with a possibly empty variable, overwriting user files.
2. **Silent wrong results.** Examples: exit 0 on failure, a wrong user context, a swallowed exception.
3. **Crashes on common edge cases.** Examples: no console user, spaces in paths, missing tools.
4. **Maintainability.** Duplicated logic, magic values, giant functions.
5. **Style.** Mention it only when it causes one of the above.

Label each refactor **Quick win** (localized, low risk, under an hour) or **Deeper** (touches structure, needs testing).

---

## Good vs weak examples

### Weak

```markdown
### Footguns
- Variables should be quoted.
- Error handling is missing.

### Refactor suggestions
- Use functions.
- Follow shellcheck.
```

Why it's weak: no locations, no trigger conditions, no concrete change.

### Good

~~~markdown
### Footguns
- **Empty-var `rm -rf`** — `cleanup.zsh:42` — `rm -rf ${targetDir}/*`. If `$4` is blank, `targetDir` is empty and this expands to `rm -rf /*` as root.
- **Pipeline hides failure** — `cleanup.zsh:61` — `curl -s "$url" | tar -xz -C "$dest"`. Without `pipefail`, a failed download extracts nothing and the script continues as if it succeeded.
- **Wrong GUI context** — `notify.zsh:18` — `sudo -u "$user" osascript -e 'display dialog …'`. This runs outside the user's Aqua session, so the dialog never appears and `osascript` returns an error that is then ignored.
- **Subshell variable loss** — `inventory.sh:33–40` — `cat list | while read -r app; do count=$((count+1)); done`. In bash, `count` is 0 after the loop because the pipe runs the loop in a subshell. (zsh runs the last pipeline element in the current shell, so this works there. The `#!/bin/bash` shebang makes it a bug.)

### Edge cases not handled
- Console user is `loginwindow` (no one logged in) → `defaults write` targets `/Users/loginwindow/…`, which doesn't exist — `setup.zsh:22`.
- App path contains a space (`/Applications/Microsoft Word.app`) → unquoted `$appPath` splits into two arguments — `check.sh:15`.
- Second run after a partial failure → `mkdir /Library/Org` fails because the directory exists; the error is ignored, but the `cp` that follows overwrites the config without a backup — `install.zsh:70–72`.

### Refactor suggestions
#### R1 — Guard destructive paths  ·  Quick win
`cleanup.zsh:42`
```zsh
# before
rm -rf ${targetDir}/*
```
```zsh
# after
: "${targetDir:?targetDir is empty; refusing to delete}"
[[ "$targetDir" == /Library/Org/Cache/* ]] || { print -u2 "Unexpected path: $targetDir"; exit 1; }
rm -rf -- "${targetDir}"/*
```
Fails closed on an empty or unexpected path. `--` stops option parsing on names that start with `-`.

#### R2 — Run UI in the user's session  ·  Quick win
`notify.zsh:18`
```zsh
# before
sudo -u "$user" osascript -e 'display dialog "Update ready"'
```
```zsh
# after
uid=$(id -u "$user")
launchctl asuser "$uid" sudo -u "$user" osascript -e 'display dialog "Update ready"'
```
Targets the correct per-user bootstrap namespace, so the dialog actually appears.
~~~

---

## Language notes

### Shell (sh / bash / zsh)

- **Identify the dialect from the shebang** and hold the code to that dialect. `#!/bin/sh` on macOS is bash 3.2 in POSIX mode by default (switchable to dash via `/private/var/select/sh`). Flag bashisms or zshisms under `sh`.
- **Shellcheck-class issues:** unquoted expansions (SC2086), `cd` without `|| exit` (SC2164), `read` without `-r` (SC2162), `$(…)` inside `[ ]` without quotes, `local var=$(cmd)` masking the exit code (SC2155), `for f in $(ls)`, and `[ $var == x ]` in `sh`.
- **Error handling:** `set -euo pipefail` (bash) or `setopt ERR_EXIT PIPE_FAIL NO_UNSET` (zsh). Note that `set -e` is disabled inside `if`, `&&`, `||`, and functions called in those contexts. Suggest explicit checks for critical commands rather than relying on `-e` alone.
- **zsh vs bash differences:** arrays are 1-indexed in zsh and 0-indexed in bash. Unquoted vars don't word-split in zsh unless `SH_WORD_SPLIT` is set. `read -p` means something different in zsh. zsh has `print -u2` and `${var:A}`. `[[ ]]` behaves differently with `=~` captures (`$match` vs `BASH_REMATCH`).
- **Traps:** check that a `trap … EXIT` exists for temp files, locks, and caffeinate/`dialog` PIDs.
- **Exit codes:** make sure the script's final exit code reflects failure. Look for a terminal `exit 0` that masks earlier errors.
- **Idempotency:** `mkdir -p`, `ln -sf`, `defaults write` (idempotent) vs `>>` appends, `dscl -append`, and `sysadminctl -addUser` (not idempotent).

### Python

- **Version:** check the shebang (`/usr/bin/python` is gone on macOS 12.3+), f-strings, and walrus operators. Python 2 syntax is a blocking issue on current macOS.
- **`subprocess`:** prefer `subprocess.run([...], check=True, capture_output=True, text=True)`. Flag `shell=True`, `os.system`, and unchecked `Popen`.
- **Exceptions:** flag bare `except:` and `except Exception: pass`. Suggest catching specific exceptions (`subprocess.CalledProcessError`, `FileNotFoundError`, `plistlib.InvalidFileException`).
- **Plists:** use `plistlib` rather than shelling out to `defaults read` and parsing text.
- **Paths:** use `pathlib.Path` and `Path.home()`. Note that `home` is root's when the script runs as root, which is a common bug in Jamf-run Python.
- **Mutable default args, globals as state, and `if __name__ == "__main__":` missing** (which makes the module untestable).
- **Timeouts:** `smtplib`, `imaplib`, `ftplib`, `socket`, and `urllib.request.urlopen` wait forever unless given `timeout=`, because `socket.getdefaulttimeout()` is `None`. In a scheduled job that stalls the schedule (SKILL.md Step 4, Silent failures). Suggest one module constant, such as `TIMEOUT_S = 30`, and pass it to every network call.
- **Secret parsing:** `value.strip().strip('"').strip("'")` and `getpass().strip()` silently change secrets that start or end with quotes or spaces, and the result shows up as a misleading auth failure. Strip only a matched pair of surrounding quotes, and don't strip `getpass` input.

### AppleScript / osascript

- **Quoting:** every value passed into `do shell script` needs `quoted form of`. Show the corrected line.
- **Error handling:** `try … on error errMsg number errNum … end try`. Flag empty `on error` blocks.
- **Timeouts:** `with timeout of N seconds` around app-driven commands. The default of 120 s causes hangs.
- **Context:** `osascript` run as root can't show UI in a user session. Use `launchctl asuser`. `tell application "System Events"` needs a TCC grant.
- **Output parsing:** `do shell script` returns text with `\r` line endings in some contexts, and `paragraphs of` behaves differently than splitting on `\n`.
- **Maintainability:** in shell scripts, prefer heredoc `osascript <<'EOF' … EOF` over long chains of `-e` arguments.

### Jamf / macOS

- **Parameters:** `$1` is the mount point, `$2` the computer name, `$3` the username (often empty outside login triggers). `$4`–`$11` are custom. Check for defaults (`${4:-default}`) and validation.
- **Console user:** the robust pattern is `scutil <<< "show State:/Users/ConsoleUser" | awk '/Name :/ && ! /loginwindow/ { print $3 }'`, or `stat -f%Su /dev/console` plus explicit `loginwindow`/`_mbsetupuser`/`root` checks.
- **Extension Attributes:** must print `<result>…</result>` on every path, including errors, and must be fast and read-only.
- **Logging:** prefer a consistent log function writing to a known path (for example `/var/log/org.example.script.log`) with timestamps. `echo` goes to the Jamf policy log only.
- **`PATH`:** Jamf runs with a minimal `PATH`. Use absolute paths to binaries, or set `PATH` explicitly at the top.
- **Architecture:** use `arch`/`uname -m` or `sysctl -n machdep.cpu.brand_string`, and handle Homebrew paths for both `/opt/homebrew` and `/usr/local`.
