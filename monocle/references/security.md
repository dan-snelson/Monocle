# 🔒 Security View

## Contents
- Purpose
- Structure and tone
- Key questions the summary must answer
- Severity scale
  - Likelihood
  - Decision procedure
  - Credential severity
- Good vs weak examples
  - Weak finding
  - Good finding
  - Weak secrets inventory
  - Good secrets inventory

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

### Credits
- {good practice} — `file:line`
{or "None noted."}

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
- **Give every Low or higher finding its own row and `S#`.** Merge only under the distinct-issue test (`scoring-procedure.md`). The **Credits** list holds credits only, with no ID. An ⚪ Info row keeps its `S#` and table row; write it up in full only when its alternate is Low or higher. Past 10 findings, drop the **Impact** line from each extra Low write-up; keep every other line.
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

Assign exactly one severity to each finding. Base it on **impact × reachability × likelihood** (see **Likelihood** below) in the code's real execution context, not on theoretical worst cases.

| Severity | Criteria | Typical examples |
|---|---|---|
| 🔴 **Critical** | Remote or unauthenticated code execution as root, **or** a plaintext credential that grants write/admin access to a fleet-wide system and is hardcoded in the code, repo, or shipped payload (see **Credential severity**), **or** deliberate disabling of a core security control on many devices | `curl http://… \| sudo bash`; Jamf API admin creds hardcoded; `spctl --master-disable` fleet-wide |
| 🟠 **High** | Local privilege escalation to root that needs no race (a link or file planted before the run, or a user-owned path that root executes); code injection from an attacker-influenced input; a secret with meaningful scope exposed in logs, the process list, or a world-readable file; TLS verification disabled on a download that gets executed; unverifiable (obfuscated) behavior | `eval "$4"`; root reads and executes `~/Library/…/script.sh`; `curl -k` then run; `curl -u admin:pass` visible in `ps` |
| 🟡 **Medium** | Exploitable only with local access plus winning a race, or the security impact (code execution, data access, or loss of a control) is limited to one user or device, not a changed reminder, notice, or self-reported value; weak integrity checks; overly broad permissions | Predictable `/tmp/foo` written as root (clobber only); `chmod 777`; downloaded pkg installed without a signature/Team ID check; narrow or read-only credential in a Jamf param (see **Credential severity**) |
| 🔵 **Low** | Defense-in-depth gaps with no clear exploit path | Missing `umask` (a root-written file left to the default mode that captures other programs' output); verbose logging of non-secret identifiers; no `--proto '=https'` on an HTTPS URL |
| ⚪ **Info** | Observations useful for context, not risk | Uses `launchctl asuser` correctly; TLS pinned; runs read-only; a readable log holding only data local users can already read; forged install.log text that only changes a DDM reminder |

### Likelihood

A finding can be possible without being probable (SKILL.md Rule 15). Classify every row that needs a deliberate actor into one tier, and record the tier and the criteria it meets in the **Severity basis** line. A row whose only actor is an admin records `Likelihood: n/a (admin only)` and uses Adjustment 2 instead.

- **Expected** is the default. It covers failures that happen on their own (a race that occurs in normal operation, a typo in a parameter, Q1b-type silent failures), any remote or network attacker, and any gain of root, code execution as another account, another account's data, or a secret.
- **Improbable** applies only when all three hold:
  - (a) the only actor is a local user acting deliberately on that Mac;
  - (b) no privilege or account boundary is crossed: no root, no code execution as another account, no other account's data, and no secret. Changing what the tool displays in another account's session crosses no boundary;
  - (c) the gain is no more than the tool's normal UI already gives that user (dismiss, defer, opt out), **or** a control the tool doesn't own enforces the real requirement regardless, such as DDM installing at its deadline or an MDM-installed profile, even when the forged text invents a different requirement. Cite the `patterns.md` entry for the platform control.
- **Self-scoped and backstopped** is an Improbable row whose criterion (c) is met by a platform control, and whose effect is limited to what the tool shows, defers, or escalates for that Mac's users (including holding off its own aggressive or forced-restart modes), or reports about that Mac. Forged text that makes the tool take an action nobody requested, such as a restart, isn't self-scoped; walk it normally. Q2 rates it ⚪ Info. Example: a user appends forged lines to `/var/log/install.log` so a DDM reminder tool suppresses or misstates its reminder, or an Extension Attribute reports a wrong pending date for that Mac; DDM still installs at the deadline.
- **Non-factors.** An undocumented format, required skill or knowledge, no public exploit, and "users wouldn't do that" never make a row Improbable. A row whose only support is one of these stays Expected.
- Forged text that reaches a sink (`eval`, `${(P)…}`, `printf -v`, a command, or a path root writes) is rated as injection or path trust, never by this section.

### Decision procedure

Answer these questions in order for each ledger row (`scoring-procedure.md`) before you choose a severity, and record the path in the finding's **Severity basis** line. The first question that decides ends the walk; then apply **Adjustments**.

- **Q0 — Capability?** If the row is about a high-impact operation *being available* (EDR removal, data deletion, app removal), run the Rule 14 checklist in `scoring-procedure.md` and use its outcome (SKILL.md Rule 14). Defects in how the code performs the operation skip Q0.
- **Q1 — Credential?** Use **Credential severity** below. Its result is final; adjustments don't apply.
- **Q1b — Floors.** A silent failure in a security or compliance control is at least 🟡 Medium, for example a FileVault enforcement script that exits 0 on error, or a firewall-enable step whose failure is swallowed. So is non-production data that reaches production compliance records. The floor binds the Q4–Q5 rating. When Q3 finds that the deployment never runs the path or closes its precondition, Q3 sets the headline and the floor applies to the alternate.
- **Q2 — Gain.** Name the attacker (a non-admin local user, a network attacker, or a remote party), the precondition, and the gain.
  - ⚪ **Info** applies only when the gain isn't security-relevant even with the precondition met: something cosmetic, the availability of a non-security feature, or data the attacker can already read. Credits and observations are also Info.
  - A **self-scoped and backstopped** row (**Likelihood** above) is ⚪ Info: the actor only gives up a non-security nudge, or misreports their own Mac, while the platform still enforces the outcome. The walk ends here. The Q1b floor doesn't bind, the row has no alternate, and the code's safer source (for example, a root-owned state file) goes in **Fix** as hardening.
  - Otherwise the row is at least 🔵 Low. A security-relevant gap with a concrete code fix is never Info.
  - Rate disclosure by what the code itself writes. Treat relayed output of other programs as unknown content: 🔵 Low at most, and never assume it holds a specific secret.
  - If only an admin can trigger the gap, rate it here as if a non-admin could, then apply the lowering adjustment.
- **Q3 — Baseline and context.** Rate Deployment-origin exposure at the operator's Deployment Context when one is supplied, otherwise at the documented-deployment baseline (SKILL.md Rule 11, `deployment-context.md`).
  - If the deployment never runs the vulnerable code (an undeployed file, a parameter the documentation leaves blank, or a mode the operator's context puts out of scope), the headline is ⚪ Info.
  - If the deployment runs the code but closes the precondition, the headline is 🔵 Low, and the walk ends.
  - In both cases, the alternate is what Q4–Q5 give with the precondition met. When the code offers no safe way to deploy, the exposure stays in the headline.
- **Q4 — Example match.** If a Typical examples cell in the table above names the same sink and the same gain as the scenario that remains after Q3, use that row. A match on the sink alone doesn't cap the gain: when the gain meets a higher row's criteria, go to Q5.
- **Q5 — Criteria.** Otherwise, test the Critical, High, and Medium criteria in that order; the first match wins. If none matches, the row is 🔵 Low.

**Definitions:**

- **Weak integrity check (Medium):** a check an attacker can pass without the pinned vendor's signing key. Examples: a name-only signature check, a hash fetched over the same channel as the file, or no check at all. When the code pins the vendor's identity, a missing Gatekeeper, notarization, or revocation verdict is 🔵 Low, and crediting the pin elsewhere doesn't retire it. An already-installed binary the code accepts on version alone, with no publisher check on that path, is its own row: 🔵 Low when only root can write its path, otherwise rate it by the walk.
- **Inferred rows:** when the code path that depends on a third-party behavior is observed, rate the behavior as if it holds and label the row inferred (SKILL.md Rule 3). Never drop or downgrade a row because it is inferred.

**Adjustments.** Apply these after the walk, in this order and at most once each, and name each one in the Severity basis line. They never apply to credential findings (see **Credential severity**), to a Q0 outcome, to ⚪ Info, or to a row whose headline Q3 set.

1. **Raise one level** when the target's own documentation or packaging deploys it fleet-wide by default, or the operator's Deployment Context states fleet-wide deployment, for example a pkg in the enrollment prestage, an Extension Attribute, or documentation that tells admins to scope it to All Computers. A Jamf policy or LaunchDaemon pkg whose scope the administrator chooses is not fleet-wide by default; without such documentation or Deployment Context, don't raise. Never raise into 🔴 Critical: only the Critical criteria give Critical.
2. **Lower one level** when the vulnerable path requires admin access that already implies equivalent power. Say so explicitly.
3. **Lower one level** when the row's Likelihood is Improbable (and not self-scoped and backstopped, which is already Info). Name criteria (a)–(c) in the Severity basis. This never lowers below 🔵 Low.

Apply at most one lowering adjustment: 2 or 3, not both.

Overall risk equals the highest headline severity, or 🔵 Low when no finding is Low or higher. When the alternate's highest severity differs, give it too.

Severities drive the Monocle Score (SKILL.md, Step 5, Monocle Score): Critical −40, High −20, Medium −8, Low −3, Info 0. The highest severity also sets the score's range (Critical 0–39, High 25–69, Medium 50–89, otherwise 70–100). Info findings are observations and cost nothing. Rate each finding on its merits, never to reach a target score.

### Credential severity

Rate every credential finding with this table. Other sections of this file and of SKILL.md defer to it.

| Where the credential lives | Fleet-wide write/admin scope | Narrow or read-only scope |
|---|---|---|
| Hardcoded in the code, repo, or shipped payload (includes base64) | 🔴 **Critical** (Origin: Code) | 🟠 **High** (Origin: Code) |
| Jamf parameter `$4`–`$11`, while a policy populates it | 🟠 **High** (Origin: Platform + Deployment): readable in `argv` by every local user for the whole run, and in the Jamf policy UI | 🟡 **Medium** (Origin: Platform + Deployment) |
| Written to a log, a world-readable file, or `set -x` output | 🟠 **High** (Origin: Code) | 🟡 **Medium** (Origin: Code) |
| Sent over a connection that doesn't verify TLS | 🟠 **High** (Origin: Code) | 🟡 **Medium** (Origin: Code) |
| CI secret passed to a third-party action pinned to a mutable tag | 🟡 **Medium** (Origin: Code + Deployment) | 🔵 **Low** (Origin: Code + Deployment) |
| Under the user's home, with the mode set only on create (per-user tools) | 🔵 **Low** (Origin: Code) | 🔵 **Low** (Origin: Code) |
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
#### S1 — Remote script executed as root without integrity check  ·  **🔴 Critical**
- **Location:** `install.zsh:57`
- **Origin:** Code — the script pipes a mutable remote branch into a root shell; nothing in the platform or deployment requires it, and the code does no integrity check.
- **Context:** Independent of deployment model
- **Severity basis:** Q2: anyone who can push to `example/tools` `main`, or tamper with DNS/TLS on the client network, gets root code execution; Q4: matches the Critical example `curl http://… | sudo bash`
- **Evidence:** `curl -sL "https://raw.githubusercontent.com/example/tools/main/setup.sh" | /bin/bash`
- **Impact:** Runs as root on every Mac the Jamf policy is scoped to. Anyone who can push to `example/tools` `main` gets root code execution on those Macs, and the branch is mutable, so content can change between runs.
- **Fix:** Vendor `setup.sh` into this repo, or pin to a commit SHA and verify it before running: download to `mktemp`, check with `shasum -a 256 -c`, then execute. Add `--fail --proto '=https' --tlsv1.2`.
```

### Weak secrets inventory

```markdown
- There might be some secrets.
```

### Good secrets inventory

```markdown
- Jamf Pro API client secret — Jamf param `$5` — `api-helper.zsh:14` — readable by every local user in the script's `argv` for the whole run, and by Jamf admins in the policy UI (Platform + Deployment). Also passed to `curl -d "client_secret=$5"` at `api-helper.zsh:31`, which adds the `curl` child's `argv` (Code).
- Slack webhook URL — hardcoded — `notify.py:8` (`https://hooks.slack.com/services/…`) — anyone with read access to the repo can post to the channel.
```
