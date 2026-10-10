# 🔒 Security View

## Contents
- Purpose
- Structure and tone
- Key questions the summary must answer
- Severity scale
  - Decision procedure
  - Credential severity
- Good vs weak examples
  - Weak finding
  - Good finding
  - Weak secrets inventory
  - Good secrets inventory
- Language notes
  - Shell (sh / bash / zsh)
  - Python
  - Swift / Objective-C (macOS helpers, daemons, GUI apps)
  - AppleScript / osascript
  - Jamf / macOS

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
**Overall risk:** {🔴 Critical | 🟠 High | 🟡 Medium | 🔵 Low} — {one-sentence justification}
**Deployment context:** {Operator-stated | None supplied} — {how it changes the risk picture: which S# it mitigates and why, which it raises, and "independent of deployment model:" the rest}

### Findings

| ID | Severity | Title | Location |
|----|----------|-------|----------|
| S1 | 🟠 High  | …     | `file:line` |
| S2 | 🟡 Medium | …     | `file:line` |

#### S1 — {Title}  ·  **{severity emoji} {Severity}**
- **Location:** `file:line` (or function name)
- **Origin:** {Code | Platform | Deployment, or a combination} — {one sentence: the platform behavior or configuration choice involved, and what the code already does about it} (see SKILL.md Rule 13)
- **Context:** {Mitigated by deployment context — {context item}; {alternate severity} outside it | Raised by deployment context — {context item} | Independent of deployment model}
- **Severity basis:** {path through the Decision procedure, e.g. "Q2: a local user gets root code execution; Q3: the documented baseline closes the precondition → Low; alternate High"}
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
- **Order findings by severity,** then by first `file:line` (`scoring-procedure.md`, Issue ledger).
- **Write the Deployment context line after rating,** from each row's Context effect (`deployment-context.md`). Keep it to one to three sentences. With no context, write "None supplied — rated at the documented-deployment baseline", and name the findings an operator context could change, if any. Every finding's **Context:** line agrees with it.
- **Give every Low or higher finding its own row and `S#`.** Merge only under the distinct-issue test (`scoring-procedure.md`). The "Low / Info" roll-up holds credits and Info observations only. Past about 10 findings, keep the extra Low write-ups to Location, Evidence, and Fix.
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
| 🔴 **Critical** | Remote or unauthenticated code execution as root, **or** a plaintext credential that grants write/admin access to a fleet-wide system and is hardcoded in the code, repo, or shipped payload (see **Credential severity**), **or** deliberate disabling of a core security control on many devices | `curl http://… \| sudo bash`; Jamf API admin creds hardcoded; `spctl --master-disable` fleet-wide |
| 🟠 **High** | Local privilege escalation to root; code injection from an attacker-influenced input; a secret with meaningful scope exposed in logs, the process list, or a world-readable file; TLS verification disabled on a download that gets executed; unverifiable (obfuscated) behavior | `eval "$4"`; root reads and executes `~/Library/…/script.sh`; `curl -k` then run; `curl -u admin:pass` visible in `ps` |
| 🟡 **Medium** | Exploitable only with local access plus timing, or the impact is limited to one user or device; weak integrity checks; overly broad permissions | Predictable `/tmp/foo` written as root; `chmod 777`; downloaded pkg installed without a signature/Team ID check; narrow or read-only credential in a Jamf param (see **Credential severity**) |
| 🔵 **Low** | Defense-in-depth gaps with no clear exploit path | Missing `umask` (a root-written file left to the default mode that captures other programs' output); verbose logging of non-secret identifiers; no `--proto '=https'` on an HTTPS URL |
| ⚪ **Info** | Observations useful for context, not risk | Uses `launchctl asuser` correctly; TLS pinned; runs read-only; a readable log holding only data local users can already read |

### Decision procedure

Answer these questions in order for each ledger row (`scoring-procedure.md`) before you choose a severity, and record the path in the finding's **Severity basis** line. The first question that decides ends the walk; then apply **Adjustments**.

- **Q0 — Capability?** If the row is about a high-impact operation *being available* (EDR removal, data deletion, app removal), run the Rule 14 checklist in `scoring-procedure.md` and use its outcome (SKILL.md Rule 14). Defects in how the code performs the operation skip Q0.
- **Q1 — Credential?** Use **Credential severity** below. Its result is final; adjustments don't apply.
- **Q1b — Floors.** A silent failure in a security or compliance control is at least 🟡 Medium, for example a FileVault enforcement script that exits 0 on error, or a firewall-enable step whose failure is swallowed. So is non-production data that reaches production compliance records.
- **Q2 — Gain.** Name the attacker (a non-admin local user, a network attacker, or a remote party), the precondition, and the gain.
  - ⚪ **Info** applies only when the gain isn't security-relevant even with the precondition met: something cosmetic, the availability of a non-security feature, or data the attacker can already read. Credits and observations are also Info.
  - Otherwise the row is at least 🔵 Low. A security-relevant gap with a concrete code fix is never Info.
  - Rate disclosure by what the code itself writes. Treat relayed output of other programs as unknown content: 🔵 Low at most, and never assume it holds a specific secret.
  - If only an admin can trigger the gap, rate it here as if a non-admin could, then apply the lowering adjustment.
- **Q3 — Baseline and context.** Rate Deployment-origin exposure at the operator's Deployment Context when one is supplied, otherwise at the documented-deployment baseline (SKILL.md Rule 11, `deployment-context.md`).
  - If the deployment never runs the vulnerable code (an undeployed file, a parameter the documentation leaves blank, or a mode the operator's context puts out of scope), the headline is ⚪ Info.
  - If the deployment runs the code but closes the precondition, the headline is 🔵 Low, and the walk ends.
  - In both cases, the alternate is what Q4–Q5 give with the precondition met. When the code offers no safe way to deploy, the exposure stays in the headline.
- **Q4 — Example match.** If a Typical examples cell in the table above matches the scenario that remains after Q3, use that row.
- **Q5 — Criteria.** Otherwise, test the Critical, High, and Medium criteria in that order; the first match wins. If none matches, the row is 🔵 Low.

**Definitions:**

- **Weak integrity check (Medium):** a check an attacker can pass without the pinned vendor's signing key. Examples: a name-only signature check, a hash fetched over the same channel as the file, or no check at all. When the code pins the vendor's identity, a missing Gatekeeper, notarization, or revocation verdict is 🔵 Low.
- **Inferred rows:** when the code path that depends on a third-party behavior is observed, rate the behavior as if it holds and label the row inferred (SKILL.md Rule 3). Never drop or downgrade a row because it is inferred.

**Adjustments.** Apply these after the walk, in this order and at most once each, and name each one in the Severity basis line. Neither applies to credential findings (see **Credential severity**).

1. **Raise one level** when the target's own documentation or packaging deploys it fleet-wide by default, or the operator's Deployment Context states fleet-wide deployment, for example a pkg in the enrollment prestage, an Extension Attribute, a LaunchDaemon on every Mac, or a Jamf policy scoped to All Computers. Never raise into 🔴 Critical: only the Critical criteria give Critical.
2. **Lower one level** when the vulnerable path requires admin access that already implies equivalent power. Say so explicitly.

Overall risk equals the highest headline severity. When the alternate's highest severity differs, give it too.

Severities drive the Monocle Score (SKILL.md, Step 5, Monocle Score): Critical −40, High −20, Medium −8, Low −3, Info 0. The highest severity also sets the score's range (Critical 0–39, High 25–69, Medium 50–89, otherwise 70–100). Info findings are observations and cost nothing. Rate each finding on its merits, never to reach a target score.

### Credential severity

Rate every credential finding with this table. Other sections of this file and of SKILL.md defer to it.

| Where the credential lives | Fleet-wide write/admin scope | Narrow or read-only scope |
|---|---|---|
| Hardcoded in the code, repo, or shipped payload (includes base64) | 🔴 **Critical** (Origin: Code) | 🟠 **High** (Origin: Code) |
| Jamf parameter `$4`–`$11`, while a policy populates it | 🟠 **High** (Origin: Platform + Deployment): readable in `argv` by every local user for the whole run, and in the Jamf policy UI | 🟡 **Medium** (Origin: Platform + Deployment) |
| Written to a log, a world-readable file, or `set -x` output | 🟠 **High** (Origin: Code) | 🟡 **Medium** (Origin: Code) |
| Read from a root-only file or the Keychain, never logged | ⚪ Info (good practice) | ⚪ Info |

- The "raise one level for fleet-wide" adjustment above doesn't apply here; scope is already a column.
- When the code documents and supports a safer delivery than parameters, apply SKILL.md Rule 11: the headline uses that baseline and the populated-parameter rating is the alternate. When parameters are the only way the code accepts the secret, the parameter rating is the headline.

---

## Good vs weak examples

### Weak finding

```markdown
#### S1 — Insecure curl usage · 🟠 High
The script uses curl which can be insecure. Consider using best practices for downloads.
```

Why it's weak: no location, no evidence, no specific impact, and a generic fix.

### Good finding

```markdown
#### S1 — Remote script executed as root without integrity check · 🔴 Critical
- **Location:** `install.zsh:57`
- **Origin:** Code — the script pipes a mutable remote branch into a root shell; nothing in the platform or deployment requires it, and the code does no integrity check.
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
- **zsh indirection is a sink:** `${(P)name}` evaluates a subscript in `name`, including `$(…)`, when the base variable is set; `printf -v "$name"` evaluates it even when unset (zsh 5.9: with `fooX` set, `n='fooX[$(id>out)]'` ran `id` through `${(P)n}`; with it unset, `${(P)n}` ran nothing but `printf -v` still ran `id`). Any variable name built from root-read, user-controlled data, such as the console user's own preferences (`AppleLanguages`, `~/Library/Preferences/…`), is code injection. Case folding (`:l`, `(C)`) doesn't neutralize it: APFS is case-insensitive by default, so `Id` runs `/usr/bin/id`. Fix with an allowlist regex before use, or an associative array keyed by the value.
- **zsh specifics:** `setopt` changes can alter word splitting. `$=var` forces splitting. Unquoted `$var` doesn't word-split in zsh the way it does in bash, but it does glob, and empty vars vanish.

### Python

- **`subprocess` with `shell=True`** and interpolated strings leads to injection. Prefer list arguments.
- **`os.system`, `os.popen`, `eval`, `exec`, `pickle.loads`, and `yaml.load` (without `SafeLoader`)** on untrusted data.
- **`requests` with `verify=False`,** or `ssl._create_unverified_context()`.
- **`tempfile.mktemp`** (racy) vs `mkstemp`/`NamedTemporaryFile`.
- **Secrets in source,** in `argparse` defaults, or written to logs through `logging.debug(f"{token}")`.
- **Python 2 `input()`** evaluates what it reads. Flag it if the script targets Python 2.
- **Missing interpreter:** macOS no longer bundles `/usr/bin/python3` without the CLT. Code that falls back to an arbitrary `python3` on `PATH` could run a user-installed interpreter as root.
- **The stdlib doesn't verify TLS for mail and FTP clients.** Called without `context=`, these use `ssl._create_stdlib_context()`, which is `CERT_NONE` with no hostname check (observed on 3.9.6 and 3.14.7):
  - `smtplib.SMTP_SSL` and `SMTP.starttls()`
  - `imaplib.IMAP4_SSL` and `IMAP4.starttls()`
  - `poplib.POP3_SSL` and `POP3.stls()`
  - `ftplib.FTP_TLS`

  A network attacker can present any certificate and receive the login. `urllib.request` and `http.client` do verify by default. Fix: create `ctx = ssl.create_default_context()` once and pass `context=ctx` to each constructor and to `starttls()`/`stls()`. A server without STARTTLS raises an error, so these clients fail closed against a downgrade. The risk is interception, not stripping. A credential sent over an unverified channel is Medium when it is one user's narrow-scope credential; rate it higher with scope.
- **Credit when present:** `subprocess` called with argument lists and never `shell=True`; values interpolated into an AppleScript string literal escaped for `\` and `"`; plist values passed through `xml.sax.saxutils.escape`.

### Swift / Objective-C (macOS helpers, daemons, GUI apps)

- **`Process` with `executableURL` and an `arguments` array** doesn't use a shell, so it's safe from injection. Credit it. `/bin/sh -c` or `/bin/zsh -c` with an interpolated string isn't.
- **`Process` calling `/usr/sbin/chown` or `/bin/chmod`** without `-h` follows symlinks, exactly as in shell. Check the path's directory for user write access (SKILL.md Step 4, shared-directory trust).
- **`Darwin.open` / `open(2)` flags:** a root writer without `O_NOFOLLOW` (and `O_CLOEXEC`) follows a planted symlink, and `O_CREAT` creates the target. Prefer `fstat` ownership checks plus `fchown`/`fchmod` on the descriptor over path-based calls.
- **`FileManager`:** `copyItem` copies a symlink as a link, so a later `zip -r` dereferences it. `createFile(atPath:)` and `Data.write(to:)` on a fixed path in a shared directory follow symlinks. `.atomic` writes replace the file through a temporary file, which is safer for the target but still trusts the directory.
- **Root reading user-controlled plists:** `NSDictionary(contentsOfFile:)` or `UserDefaults` on `~/Library/Preferences/…` inside a root daemon is untrusted input. Check what reaches a sink (process arguments, paths, URLs), and credit allowlist filtering when it's present.
- **Privileged helpers:** SMAppService or `SMJobBless` daemons run as root. Check that the XPC listener validates the client's code-signing requirement (`setCodeSigningRequirement` or an audit-token check) before acting on requests, and that job files dropped into a shared directory are owner-checked.
- **Pipe deadlock:** calling `readDataToEndOfFile()` only after `waitUntilExit()` hangs once the child fills the pipe buffer (about 64 KB). This is an Engineer footgun, not a security finding.

### AppleScript / osascript

- **`do shell script "…" & userInput`** without `quoted form of` leads to shell injection.
- **`with administrator privileges`** prompts for credentials or runs as root. Flag a `password "…"` literal as Critical when it's an admin password.
- **`display dialog … default answer`** used to collect passwords invites credential phishing. Note whether `with hidden answer` is set and where the value goes.
- **`System Events` / UI scripting** requires an Accessibility (TCC) grant. Check whether a PPPC profile grants it broadly.
- **`run script` / `load script`** from a user-writable path, when run as root, is privilege escalation.

### Jamf / macOS

- **Params `$4`–`$11`** are visible to anyone with policy read access in Jamf Pro, and to every local user through the script's `argv` (`specialized-checks.md`, Jamf parameter secrets). Rate credentials there with **Credential severity** above.
- **Bearer-token handling:** check that tokens are invalidated (`/api/v1/auth/invalidate-token`) and not written to disk.
- **Extension Attributes** run as root on every recon. Keep them read-only; any write is a finding.
- **`jamf` binary calls** (`jamf policy -event`, `jamf recon`, `jamf manage`) can chain into other root code. Note the dependency.
- **Security-control changes:** `spctl`, `csrutil`, `fdesetup`, `socketfilterfw`, `profiles remove`, `tccutil reset`, `dscl . -append /Groups/admin`, `sysadminctl -addUser`, and `/etc/sudoers` or `/etc/sudoers.d/` edits.
- **Downloaded pkgs/apps** without `pkgutil --check-signature` or `spctl -a -vv` / Team ID verification before install.
- **Log trust:** system log text is evidence, not trusted state. `/var/log/install.log` and other syslog files can contain local-user messages. Unified-log predicates such as `process == "softwareupdated"` filter by executable name; they do not authenticate the sender. Prefer root-owned state files or APIs that expose authenticated state, and document any residual spoofing risk when logs are the only source.
