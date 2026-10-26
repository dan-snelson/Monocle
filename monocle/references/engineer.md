# 🛠️ Engineer View

## Contents
- Purpose
- Structure and tone
- Key questions the summary must answer
- Prioritization
- Good vs weak examples
  - Weak
  - Good

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
- **Ledger tags:** end each footgun and edge case with `(N#)`, `(see S#)`, or `(not scored: {reason code})`, from the issue ledger (`scoring-procedure.md`).
- **Check refactor snippets as well as citations** (extends SKILL.md Step 5 item 7). Test each "after" snippet against every platform variant the target supports: Apple silicon and Intel Homebrew prefixes, zsh and bash, and the oldest supported interpreter as well as the current one. Snippets that derive paths or parse tool output are wrong most often. For example, `Path(brew).resolve()` gives the wrong prefix on Intel.

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
- **Empty-var `rm -rf`** — `cleanup.zsh:42` — `rm -rf ${targetDir}/*`. If `$4` is blank, `targetDir` is empty and this expands to `rm -rf /*` as root (see S1).
- **Pipeline hides failure** — `cleanup.zsh:61` — `curl -s "$url" | tar -xz -C "$dest"`. Without `pipefail`, a failed download extracts nothing and the script continues as if it succeeded (N1).
- **Wrong GUI context** — `notify.zsh:18` — `sudo -u "$user" osascript -e 'display dialog …'`. This runs outside the user's Aqua session, so the dialog never appears and `osascript` returns an error that is then ignored (N2).
- **Subshell variable loss** — `inventory.sh:33–40` — `cat list | while read -r app; do count=$((count+1)); done`. In bash, `count` is 0 after the loop because the pipe runs the loop in a subshell. (zsh runs the last pipeline element in the current shell, so this works there. The `#!/bin/bash` shebang makes it a bug.) (N3)

### Edge cases not handled
- Console user is `loginwindow` (no one logged in) → `defaults write` targets `/Users/loginwindow/…`, which doesn't exist — `setup.zsh:22` (N4).
- App path contains a space (`/Applications/Microsoft Word.app`) → unquoted `$appPath` splits into two arguments — `check.sh:15` (N5).
- Second run after a partial failure → `mkdir /Library/Org` fails because the directory exists; the error is ignored, but the `cp` that follows overwrites the config without a backup — `install.zsh:70–72` (N6).

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
entries=( "${targetDir}"/*(N) )
if (( ${#entries} )); then rm -rf -- "${entries[@]}"; fi
```
Fails closed on an empty or unexpected path, and skips an empty directory: `(N)` stops zsh's "no matches found" from aborting the script (zsh 5.9). `--` stops option parsing on names that start with `-`.

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
