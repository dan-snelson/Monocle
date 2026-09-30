# Manager View

## Purpose

The Manager view helps a team lead or service owner decide:

- Who owns the code.
- How fragile it is.
- How risky it is to change or keep running.
- What work needs to be assigned.

The reader understands operations and staffing but won't debug the code. They want accountability, risk, and a to-do list.

---

## Structure and tone

Use exactly this structure:

```markdown
## Manager View

**Ownership:** {named author/maintainer, team, or "Unclear"} — {evidence: header, commits, CODEOWNERS}
**Maturity:** {Prototype | Working but fragile | Production-grade} — {one-line reason}
**Change risk:** {Low | Medium | High} — {one-line reason}

### What it depends on
- {external system / binary / service / person} — {why it matters}

### Fragility hotspots
- {what breaks, when, and how you'd find out} — `file:line`

### Change & rollback
- **Testing:** {what exists — or "None found"}
- **Rollback:** {how to undo its effects, or "No rollback; changes are permanent"}
- **Deploy path:** {Jamf policy / pkg / manual / CI — as observed or inferred}

### Action items

| # | Action | Owner role | Effort | Priority |
|---|--------|------------|--------|----------|
| 1 | …      | …          | S/M/L  | P1/P2/P3 |
```

Rules:

- **Tone:** pragmatic and operational. Write for someone planning a sprint or a change-board slot.
- **Keep line references light.** Include them where they help someone find a problem, but lead with the operational consequence.
- **Assign an owner role to every action item** ("Mac engineer", "Security", "Jamf admin", "Service owner"), not a person's name, unless the code names an owner.
- **Effort:** S is under 2 hours, M is under 2 days, L is more than that.
- **Priority:** P1 means before the next run or deployment. P2 means this quarter. P3 means backlog.
- **List up to 8 action items.** Include every Critical and High item from the Security view as a P1 action. Don't invent work for a clean script; if nothing needs doing, write "No action required." in place of the table (SKILL.md Rule 7).

---

## Key questions the summary must answer

1. **Who owns this?** Look for author headers, `CODEOWNERS`, and commit history. Note bus factor: if 90% or more of commits come from one author, say so.
2. **Is it actively maintained?** Last commit date, version string, changelog, and open TODOs/FIXMEs.
3. **What does it depend on?** External binaries, remote URLs, APIs, Jamf objects (policies, EAs, smart groups), OS versions, and specific people.
4. **What breaks it?** OS upgrades, a vendor URL change, credential rotation, a missing dependency, network changes, or renamed Jamf objects.
5. **How would we know it broke?** Logging, exit codes, alerts, or nothing.
6. **How risky is changing it?** Complexity, test coverage, coupling, and the number of devices affected by a bad change.
7. **Can we roll it back?** Whether its effects are reversible and a previous version is available.
8. **What should the team do next?** A prioritized, assignable list.

---

## Prioritization and rating guidance

### Maturity

| Rating | Signals |
|---|---|
| **Prototype** | No error handling, hardcoded values, no logging, no version, TODOs in critical paths |
| **Working but fragile** | Works on the happy path; silent failures, environment assumptions, single maintainer, no tests |
| **Production-grade** | Validates inputs, handles errors, logs to a known location, versioned, documented, idempotent, and has some testing or a staged rollout |

### Change risk

| Rating | Signals |
|---|---|
| **Low** | Short, read-only or easily reversible, few dependencies, clear structure |
| **Medium** | Writes system state, or has a few external dependencies, or has moderate complexity without tests |
| **High** | Fleet-wide root execution, irreversible changes (accounts, encryption, deletions), heavy coupling, large functions, no tests, single maintainer |

### Action item priority

- **P1:** Security Critical/High fixes; anything that causes silent failure in a security or compliance control; missing rollback for destructive operations.
- **P2:** Fragility that will break on a known upcoming event (OS release, credential rotation, vendor deprecation); missing logging or monitoring.
- **P3:** Documentation, refactors, tests, and style.

---

## Good vs weak examples

### Weak

```markdown
**Ownership:** Unknown.
**Change risk:** Medium.

### Action items
- Add error handling.
- Improve documentation.
- Consider security.
```

Why it's weak: no evidence, no reasons, and action items without owners, effort, or priority.

### Good

```markdown
**Ownership:** James Example (Mac Engineering) — script header `# Author: James Example`; 47 of 49 commits by the same author. **Bus factor: 1.**
**Maturity:** Working but fragile — solid happy path; every failure exits 0 and nothing alerts.
**Change risk:** High — runs as root at enrollment on every new Mac, and makes 3 irreversible changes (local admin demotion, FileVault enable, user rename).

### What it depends on
- swiftDialog 2.4+ at `/usr/local/bin/dialog` — installed by a separate Jamf policy; the script doesn't check the version.
- Jamf policy triggers `installChrome`, `installZoom`, `installOffice` — renaming any of them silently skips that app.
- `https://downloads.vendor.example/latest.pkg` — unversioned "latest" URL; behavior changes whenever the vendor publishes.
- Jamf API client in `$5`/`$6` — rotating the secret breaks the script with no error.

### Fragility hotspots
- Detecting the console user fails during Setup Assistant (`_mbsetupuser`), so the dialog never appears — `setup.zsh:88`.
- Assumes Apple silicon Homebrew path `/opt/homebrew` — breaks on the remaining Intel Macs — `setup.zsh:140`.
- Log goes to `/var/tmp/setup.log`, which is overwritten on each run, so there's no history for help desk triage.

### Change & rollback
- **Testing:** None found. No test harness and no dry-run mode.
- **Rollback:** Partial. Apps can be removed, but the user rename and admin demotion require manual repair.
- **Deploy path:** Jamf policy on the Enrollment Complete trigger (inferred from `$1`–`$3` usage and the header comment).

### Action items

| # | Action | Owner role | Effort | Priority |
|---|--------|------------|--------|----------|
| 1 | Move the Jamf API secret out of policy params; rotate the current one | Jamf admin + Security | M | P1 |
| 2 | Make failed steps exit non-zero so Jamf reports failure | Mac engineer | S | P1 |
| 3 | Add a `_mbsetupuser`/`loginwindow` wait loop before the UI starts | Mac engineer | S | P2 |
| 4 | Pin the vendor pkg URL to a version and verify its Team ID | Mac engineer | S | P2 |
| 5 | Add a second maintainer; document the dependent Jamf policies | Service owner | M | P2 |
| 6 | Add a `--dry-run` mode for pre-release testing | Mac engineer | M | P3 |
```

---

## Language notes

### Shell (sh / bash / zsh)

- Check the header block for author, version, and changelog. Mac admin scripts commonly carry `# Version`, `# Author`, and `# Changelog` headers. Stale ones (the version string doesn't match the changelog) are a maintenance signal.
- A long single-file script (over 500 lines) with no functions means high change risk.
- Note hardcoded org values (URLs, org names, support phone numbers, Jamf server URLs) as coupling that needs a change when environments differ.

### Python

- Check for `requirements.txt`/`pyproject.toml`. Missing or unpinned dependencies are a fragility risk.
- Note the interpreter source: system `python3` needs the CLT, and a bundled one (such as MacAdmins Python) is a dependency to track.
- If tests exist (`tests/`, `pytest`), note coverage of the risky paths, not just their presence.

### AppleScript

- `.scpt` files are compiled and hard to diff or review in git. Recommend storing `.applescript` source instead.
- Dependence on UI scripting (`System Events`, clicking menu items by name) breaks with app updates and localization. Rate it high fragility.

### Jamf / macOS

- **Hidden dependencies:** Jamf policies called by custom trigger, smart groups, Extension Attributes, configuration profiles (PPPC/TCC), and the scripts' parameter labels in the Jamf UI. None of these are visible in the code, so list them.
- **OS-upgrade exposure:** note `sw_vers` checks, deprecated tools (`kextload`, `systemsetup` quirks, `python` 2, `profiles -I`), and hardcoded OS version lists.
- **Blast radius:** scope is set in Jamf, not in code. When unknown, say "Scope not visible in code — confirm in Jamf Pro before changing".
