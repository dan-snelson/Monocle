# Security View

## Purpose

The Security view gives a security or risk reviewer:

- A ranked list of findings.
- A map of the privileges the code uses.
- An inventory of secrets.
- A picture of the code's network and persistence footprint.

The reviewer can read code but hasn't read this code. They need to know quickly: what can this code do, with what authority, and how could someone abuse or break it?

This view has the strictest evidence requirements in the report. Every finding needs a location and evidence.

---

## Structure and tone

Use exactly this structure:

```markdown
## Security View

**Execution context:** {root via Jamf policy | console user | launchd daemon as root | unknown — why}
**Overall risk:** {Critical | High | Medium | Low} — {one-sentence justification}

### Findings

| ID | Severity | Title | Location |
|----|----------|-------|----------|
| S1 | High     | …     | `file:line` |
| S2 | Medium   | …     | `file:line` |

#### S1 — {Title}  ·  **{Severity}**
- **Location:** `file:line` (or function name)
- **Evidence:** `{short code quote, secrets redacted}`
- **Impact:** {What an attacker or failure can achieve, and against what}
- **Fix:** {Specific change — command, flag, or pattern to use instead}

{repeat for each finding}

### Privilege map
- {operation} — `file:line` — {runs as whom}

### Secrets inventory
- {secret type} — {source: hardcoded / Jamf param / Keychain / env / file} — `file:line` — {exposure}
{or "No secrets observed."}

### Network egress
- {host / URL pattern} — {method} — {TLS verified? auth?} — `file:line`
{or "No network calls observed."}

### Persistence
- {mechanism} — {path} — `file:line`
{or "No persistence mechanisms observed."}
```

Rules:

- **Tone:** factual and technical. Don't use "catastrophic" or other hype. Let the severity carry the weight.
- **Rank findings by severity,** then by exploitability within the same severity.
- **Cap the list at about 10 findings.** Merge closely related ones. Put nitpicks in a single "Low / Info" roll-up bullet if they're worth mentioning at all.
- **Quote evidence verbatim,** with secrets redacted to the first 4 characters plus `…`.
- **Make fixes concrete.** "Use `curl --fail --proto '=https' --tlsv1.2`" is a fix. "Improve TLS handling" is not.
- If nothing notable is found, still fill in the sections and write "No Critical, High, or Medium findings", with a short reason.

---

## Key questions the summary must answer

1. **Which identity does the code run as?** Root, console user, or a service account. Does it ever switch?
2. **What privileged operations does it perform?** List them with locations.
3. **What secrets does it handle,** where do they come from, and where could they leak (process list, logs, disk, Jamf UI)?
4. **What untrusted input reaches a dangerous sink?** Jamf params, env vars, user-writable files, network responses, and filenames flowing into `eval`, `sh -c`, `rm`, `osascript`, `subprocess(shell=True)`, or SQL.
5. **What does it download or execute from remote sources,** and is integrity checked (TLS, hash, signature, Team ID)?
6. **What does it leave behind?** Daemons, agents, profiles, sudoers entries, user accounts, or open permissions.
7. **Can a local non-admin user influence it?** World-writable paths, user-owned files read by root, and `/tmp` races.
8. **Does it disable or weaken a security control?** Gatekeeper, SIP checks, the firewall, FileVault, XProtect, TCC, or `csrutil`.

---

## Severity scale

Assign exactly one severity to each finding. Base it on **impact × reachability** in the code's real execution context, not on theoretical worst cases.

| Severity | Criteria | Typical examples |
|---|---|---|
| **Critical** | Remote or unauthenticated code execution as root, **or** a plaintext credential that grants write/admin access to a fleet-wide system, **or** deliberate disabling of a core security control on many devices | `curl http://… \| sudo bash`; Jamf API admin creds hardcoded; `spctl --master-disable` fleet-wide |
| **High** | Local privilege escalation to root; code injection from an attacker-influenced input; a secret with meaningful scope exposed in logs, the process list, or a world-readable file; TLS verification disabled on a download that gets executed; unverifiable (obfuscated) behavior | `eval "$4"`; root reads and executes `~/Library/…/script.sh`; `curl -k` then run; `curl -u admin:pass` visible in `ps` |
| **Medium** | Exploitable only with local access plus timing, or the impact is limited to one user or device; weak integrity checks; overly broad permissions | Predictable `/tmp/foo` written as root; `chmod 777`; downloaded pkg installed without a signature/Team ID check; secret in a Jamf param (UI-visible to admins) |
| **Low** | Defense-in-depth gaps with no clear exploit path | Missing `umask`; verbose logging of non-secret identifiers; no `--proto '=https'` on an HTTPS URL |
| **Info** | Observations useful for context, not risk | Uses `launchctl asuser` correctly; TLS pinned; runs read-only |

Adjust severity for context:

- **Raise** it one level when the code runs fleet-wide by default (a Jamf policy scoped to All Computers, or a pkg in the enrollment prestage).
- **Lower** it one level when the vulnerable path requires admin access that already implies equivalent power. Say so explicitly.
- Rate **silent failures in security controls** at least Medium. Examples: a FileVault enforcement script that exits 0 on error, or a firewall-enable step whose failure is swallowed.

Overall risk equals the highest finding severity, unless you justify otherwise in one sentence.

---

## Good vs weak examples

### Weak finding

```markdown
#### S1 — Insecure curl usage · High
The script uses curl which can be insecure. Consider using best practices for downloads.
```

Why it's weak: no location, no evidence, no specific impact, and a generic fix.

### Good finding

```markdown
#### S1 — Remote script executed as root without integrity check · Critical
- **Location:** `install.zsh:57`
- **Evidence:** `curl -sL "https://raw.githubusercontent.com/example/tools/main/setup.sh" | /bin/bash`
- **Impact:** Runs as root via Jamf policy on all enrolled Macs. Anyone who can push to `example/tools` main, or who can tamper with DNS/TLS on the client network, gets root code execution fleet-wide. The `main` branch is mutable, so content can change between runs.
- **Fix:** Vendor `setup.sh` into this repo, or pin to a commit SHA and verify it before running: download to `mktemp`, check with `shasum -a 256 -c`, then execute. Add `--fail --proto '=https' --tlsv1.2`.
```

### Weak secrets inventory

```markdown
- There might be some secrets.
```

### Good secrets inventory

```markdown
- Jamf Pro API client secret — Jamf param `$5` — `api-helper.zsh:14` — visible to Jamf admins in the policy UI. Passed to `curl -d "client_secret=$5"` at line 31, so it's visible in `ps` for the duration of the call.
- Slack webhook URL — hardcoded — `notify.py:8` (`https://hooks.slack.com/services/T0AB…`) — anyone with read access to the repo can post to the channel.
```

---

## Language notes

### Shell (sh / bash / zsh)

- **Injection sinks:** `eval`, `sh -c "$var"`, `bash -c`, unquoted `$var` in command position, backticks or `$(…)` around untrusted data, `xargs` without `-0`, and `find -exec sh -c '… {}'`.
- **Unquoted variables in `rm`/`mv`/`chown`:** `rm -rf $dir/` with `$dir` empty becomes `rm -rf /`. Check for `${var:?}` guards.
- **Temp files:** `/tmp/name` as root means symlink races. Expect `mktemp` plus a `trap 'rm -f "$tmp"' EXIT`.
- **Process-list exposure:** secrets in command-line args (`curl -u`, `-H "Authorization: …"`, `security add-generic-password -w pass`). Prefer stdin, `--config`, or `-K -`.
- **`set -x` / `xtrace`** combined with secrets means secrets end up in logs.
- **`sudo` inside a root script** is usually redundant. `sudo -u user` without `launchctl asuser` is a context bug, not a privilege drop into the GUI session.
- **zsh specifics:** `setopt` changes can alter word splitting. `$=var` forces splitting. Unquoted `$var` doesn't word-split in zsh the way it does in bash, but it does glob, and empty vars vanish.

### Python

- **`subprocess` with `shell=True`** and interpolated strings leads to injection. Prefer list arguments.
- **`os.system`, `os.popen`, `eval`, `exec`, `pickle.loads`, and `yaml.load` (without `SafeLoader`)** on untrusted data.
- **`requests` with `verify=False`,** or `ssl._create_unverified_context()`.
- **`tempfile.mktemp`** (racy) vs `mkstemp`/`NamedTemporaryFile`.
- **Secrets in source,** in `argparse` defaults, or written to logs through `logging.debug(f"{token}")`.
- **Python 2 `input()`** evaluates what it reads. Flag it if the script targets Python 2.
- **Missing interpreter:** macOS no longer bundles `/usr/bin/python3` without the CLT. Code that falls back to an arbitrary `python3` on `PATH` could run a user-installed interpreter as root.

### AppleScript / osascript

- **`do shell script "…" & userInput`** without `quoted form of` leads to shell injection.
- **`with administrator privileges`** prompts for credentials or runs as root. Flag a `password "…"` literal as Critical when it's an admin password.
- **`display dialog … default answer`** used to collect passwords invites credential phishing. Note whether `with hidden answer` is set and where the value goes.
- **`System Events` / UI scripting** requires an Accessibility (TCC) grant. Check whether a PPPC profile grants it broadly.
- **`run script` / `load script`** from a user-writable path, when run as root, is privilege escalation.

### Jamf / macOS

- **Params `$4`–`$11`** are visible to anyone with policy read access in Jamf Pro. Credentials there are at least Medium; they are High if the account is admin-scoped and also logged.
- **Bearer-token handling:** check that tokens are invalidated (`/api/v1/auth/invalidate-token`) and not written to disk.
- **Extension Attributes** run as root on every recon. Keep them read-only; any write is a finding.
- **`jamf` binary calls** (`jamf policy -event`, `jamf recon`, `jamf manage`) can chain into other root code. Note the dependency.
- **Security-control changes:** `spctl`, `csrutil`, `fdesetup`, `socketfilterfw`, `profiles remove`, `tccutil reset`, `dscl . -append /Groups/admin`, `sysadminctl -addUser`, and `/etc/sudoers` or `/etc/sudoers.d/` edits.
- **Downloaded pkgs/apps** without `pkgutil --check-signature` or `spctl -a -vv` / Team ID verification before install.
