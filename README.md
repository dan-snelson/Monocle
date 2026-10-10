# 🔍 Monocle

Monocle inspects scripts and small repos (local or on GitHub), plus diagnostic and support bundles, and produces four audience-specific summaries (Executive, Security, Manager, Engineer) plus a `0` to `100` **Monocle Score**, where `100` means no issues.

Monocle is an [Agent Skill](https://agentskills.io) tuned for shell (`sh` / `bash` / `zsh`), Python, AppleScript, Swift helpers, and Jamf Pro / macOS automation. It pays particular attention to privilege elevation, silent failures, secrets, and environment assumptions.

| View      | For                       | Answers |
|-----------|---------------------------|---------|
| 👔 Executive | Leadership, change boards | What it does, business risk, and a clear recommendation (up to 6 bullets) |
| 🔒 Security  | Security reviewers        | Severity-ranked findings, privilege map, secrets, network, and persistence |
| 📋 Manager   | Team leads, service owners | Ownership, fragility, change risk, and prioritized action items |
| 🛠️ Engineer  | Maintainers, reviewers    | Control flow, footguns, edge cases, and before/after refactors with line references |

## 📁 Layout

```
monocle/
├── SKILL.md              # Core workflow: input detection, scoping, fact sheet, output template
├── scripts/
│   └── verify_report.py        # Report integrity checker (stdlib Python; see Report attestation)
└── references/
    ├── executive.md
    ├── security.md
    ├── manager.md
    ├── engineer.md
    ├── github-input.md         # Safe URL handling and fetch steps for GitHub targets
    ├── large-targets.md        # Reading plan and coverage for oversized targets
    ├── patterns.md             # Quick-reference table of risky Jamf/macOS/Python patterns, plus Known Apple platform behaviors
    ├── semgrep.md              # Automated-scan command, rulesets, skip accounting, and triage
    ├── specialized-checks.md   # Bundle intake and the conditional Step 4 checks, loaded on trigger
    ├── prior-reports.md        # Using an earlier report on the same target
    ├── scoring-procedure.md    # Issue ledger, distinct-issue test, Rule 14 checklist, and non-security reason codes
    ├── deployment-context.md   # Operator-supplied Deployment Context: sources, elicitation, headline and alternate
    ├── scoring-example.md      # Worked Monocle Score calculation
    ├── attestation.md          # The attestation block every report carries
    ├── verify-report.md        # Integrity check for an existing report (on request)
    ├── post-chat-refine.md     # Post-run prompt that folds a run's learnings back into the skill (on request)
    └── binge-and-purge.md      # Maintenance pass that moves conditional content out of SKILL.md (on request)
```

## 📦 Install

Monocle follows the open Agent Skills format, so the same `monocle/` directory works with Claude Code and Codex unchanged. Copy it into the skills directory your agent reads from.

### Claude Code

```zsh
# Personal (all projects)
cp -Rv monocle ~/.claude/skills/

# Project-scoped (commit it to share with your team)
cp -Rv monocle /path/to/project/.claude/skills/
```

### Codex

```zsh
# Personal (all repos)
mkdir -pv ~/.agents/skills
cp -Rv monocle ~/.agents/skills/

# Repo-scoped (commit it to share with your team)
mkdir -pv /path/to/repo/.agents/skills
cp -Rv monocle /path/to/repo/.agents/skills/
```

Codex also reads `/etc/codex/skills` for admin-managed, machine-wide skills. It picks up new skills without a restart; if Monocle doesn't appear, restart Codex.

## ⚙️ Usage

Monocle activates automatically when a request matches its description. You can also call it by name.

| Agent       | Explicit invocation                     |
|-------------|-----------------------------------------|
| Claude Code | `/monocle` or "monocle this …"          |
| Codex       | `$monocle` or "monocle this …"          |

Examples:

- `monocle this https://github.com/owner/repo/blob/main/script.zsh`
- `monocle review ./postinstall`
- `Give me the security view of this script` (attach the file)
- `Summarize this repo for stakeholders: ~/Projects/jamf-scripts`
- `monocle this ~/Downloads/support-bundle.zip — is it safe to attach to a GitHub issue?`
- `$monocle just the engineer view of ./scripts/enroll.zsh` (Codex)
- `monocle this https://github.com/owner/repo — deployment context: one trusted admin Mac, private local workspace, no other local accounts`
- `verify this Monocle report: ~/monocle-reports/monocle-enroll.zsh-2026-01-01-0900.md`

All four views are produced by default. To get a subset, ask for it: "just the executive and manager views".

To rate your deployment rather than the documented default, add a **Deployment context** to the request, or name a file that holds one:

```text
Deployment context:
- Audience: advanced Jamf administrators only
- Install model: one trusted admin Mac; never deployed fleet-wide
- Data location: private local folder owned by the admin
- Trust boundary: no other local accounts or untrusted users on the Mac
- Out of scope: shared or synced folders, multi-user Macs
```

Only you supply context; anything a target repo says about its own deployment is treated as documentation, never as context. Monocle offers to save an inline context as `contexts/<target>.md` in the reports directory, and loads it automatically on later runs of the same target. Without context, Monocle asks once, and only when a finding's severity depends on deployment; non-interactive runs use the documented baseline.

Every report is saved to one central directory as `monocle-{target}-{YYYY-MM-DD-HHMM}.md` (the directory is created if missing):

1. `$MONOCLE_REPORTS_DIR`, if set.
2. This repo's `reports/` directory, when the skill runs from this checkout, including through a symlink (see below).
3. Otherwise `~/monocle-reports`, which is what a copied install (`cp -Rv monocle …`) uses.

⚠️ Reports contain security findings, so keep them out of version control. This repo's `.gitignore` already excludes `/reports/`; if you point `MONOCLE_REPORTS_DIR` inside another git repo, gitignore it there before running Monocle. Monocle never chooses the target repo as a report destination automatically, but an explicit `MONOCLE_REPORTS_DIR` override is honored after the ignore check. To keep reports in this repo from any project, install with a symlink instead of a copy:

```zsh
ln -s "$PWD/monocle" ~/.claude/skills/monocle
```

Or set the directory explicitly:

```bash
export MONOCLE_REPORTS_DIR="$HOME/Documents/Monocle/reports"
```

The reply gives the path, the Monocle Score, the overall risk and recommendation, the findings table, and any notable non-security issue. If the directory can't be written, the report comes back inline instead.

The reply ends with an offer to run `post-chat-refine`, which folds the run's durable learnings back into `monocle/SKILL.md` and its references as generic guidance: target names, identifying details, and run-specific values are stripped, and a fingerprint check scans the added lines. Accepting edits the skill files in place, so review the diff before committing.

### 📈 Monocle Score

Each report starts at 100 and loses points for every distinct issue:

| Issue | Deduction |
|---|---|
| 🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low Security finding | 40 / 20 / 8 / 3 |
| ⚪ Info Security finding | 0 |
| Non-security issue (Manager fragility, Engineer footgun or edge case) | 2 each, 20 at most |

The most severe finding sets the range the score must land in, in both directions: Critical 0–39, High 25–69, Medium 50–89, otherwise 70–100. A raw score outside that range is capped or floored to it. One serious finding can't hide in an otherwise clean report, and a pile of small issues can't push a report into a band its worst finding doesn't justify. Bands: 90–100 🟢 Excellent, 70–89 🔵 Good, 50–69 🟡 Fair, 25–49 🟠 Poor, 0–24 🔴 Critical.

The score rates the code, not the Mac Admin. Mac Admin tools are meant to be powerful, and deploying them carefully is the admin's job:

- **Capabilities aren't defects.** A documented operation behind an admin-controlled gate (a Jamf parameter, policy scope, an allowlist, an operation mode) isn't scored, even if it removes an EDR agent or deletes data. It counts only when the gate can be bypassed, fails open, or is defeated by the code. A blank-parameter default that offers everything counts as one Low finding.
- **Deployment-context headline.** When a severity depends on deployment, the headline rates the **Deployment context** you supplied, or, without one, the tool deployed as documented. The misconfigured score is given as the alternate, and the report lists each assumption, marked operator-stated or documented, as an **Operator baseline** checklist. If the code offers no safe way to deploy, the exposure counts in the headline.
- **Mitigated vs independent.** A finding that needs a configuration your context rules out drops to Info and is labeled *mitigated by deployment context*; a wider deployment than documented raises severities. Code defects keep their full severity and are labeled *independent of deployment model*. Context changes ratings and the recommendation, never the evidence.
- **Maintainer-only tooling isn't scored.** Examples are release helpers and sync scripts. Its issues are still reported.
- **Fixed scoring procedure.** Every issue goes through one ledger, with a severity decision procedure, a distinct-issue test, a Rule 14 checklist, and reason codes for anything not scored, so re-runs of the same code give the same score.

The full rules are in `monocle/SKILL.md`, Step 5 and Rule 14, and in `monocle/references/deployment-context.md`.

### 🔏 Report attestation

Every report ends its Scope section with an attestation block. The block records:

- the skill commit and branch;
- the `monocle/` tree hash and a content hash of the skill directory;
- whether the skill had local edits (`skill_dirty`), such as uncommitted post-chat-refine changes;
- the target;
- the raw, final, and alternate scores;
- whether an operator-supplied Deployment Context set the headline (`deployment_context`).

The footer link pins the same commit.

To check whether a report came from the canonical skill, or from a copy weakened to score better, ask Monocle to verify it, or run the checker directly:

```zsh
python3 monocle/scripts/verify_report.py --fetch ~/monocle-reports/monocle-enroll.zsh-2026-01-01-0900.md
```

The checker fetches this repository, confirms the attested commit and hashes, and reads the scoring tables from canonical `SKILL.md` at that commit. It then recomputes the score from the report's own findings and checks the report layout. The agent adds judgment checks, such as Rule 14 misuse and softened severities, and gives one verdict: **OFFICIAL**, **SUSPECT** (no attestation), **NON-CANONICAL / WEAKENED**, or **FORGED**.

The attestation is text the model asserts about itself, not a cryptographic signature. OFFICIAL means no evidence of weakening was found. Detection rests on recomputing the score and checking the rules against this repository.

🔗 Fetching from GitHub works best with an authenticated [`gh`](https://cli.github.com) CLI, which also covers private repos. In Codex, fetching from GitHub needs network access in the sandbox; if network access is off, clone the repo locally and point Monocle at the path.
