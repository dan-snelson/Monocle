# Monocle

Monocle inspects scripts (and small local repos) and produces four audience-specific summaries (Executive, Security, Manager, Engineer) plus a 0–100 **Monocle Score**, where 100 means no issues.

Monocle is an [Agent Skill](https://agentskills.io) tuned for shell (sh/bash/zsh), Python, AppleScript, and Jamf/macOS automation. It pays particular attention to privilege elevation, silent failures, secrets, and environment assumptions.

| View      | For                       | Answers |
|-----------|---------------------------|---------|
| Executive | Leadership, change boards | What it does, business risk, and a clear recommendation (3–6 bullets) |
| Security  | Security reviewers        | Severity-ranked findings, privilege map, secrets, network, and persistence |
| Manager   | Team leads, service owners | Ownership, fragility, change risk, and prioritized action items |
| Engineer  | Maintainers, reviewers    | Control flow, footguns, edge cases, and before/after refactors with line references |

## Layout

```
monocle/
├── SKILL.md              # Core workflow: input detection, scoping, fact sheet, output template
└── references/
    ├── executive.md
    ├── security.md
    ├── manager.md
    └── engineer.md
```

## Install

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

## Usage

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
- `$monocle just the engineer view of ./scripts/enroll.zsh` (Codex)

All four views are produced by default. To get a subset, ask for it: "just the executive and manager views".

Every report is saved to one central directory as `monocle-{target}-{YYYY-MM-DD-HHMM}.md` (the directory is created if missing):

1. `$MONOCLE_REPORTS_DIR`, if set.
2. This repo's `reports/` directory, when the skill runs from this checkout, including through a symlink (see below).
3. Otherwise `~/monocle-reports`, which is what a copied install (`cp -Rv monocle …`) uses.

Reports contain security findings, so keep them out of version control. This repo's `.gitignore` already excludes `/reports/`; if you point `MONOCLE_REPORTS_DIR` inside another git repo, gitignore it there. To keep reports in this repo from any project, install with a symlink instead of a copy:

```zsh
ln -s "$PWD/monocle" ~/.claude/skills/monocle
```

Or set the directory explicitly:

```bash
export MONOCLE_REPORTS_DIR="$HOME/Documents/Monocle/reports"
```

The reply gives the path, the Monocle Score, the overall risk and recommendation, and the findings table. If the directory can't be written, the report comes back inline instead.

### Monocle Score

Each report starts at 100 and loses points for every distinct issue:

| Issue | Deduction |
|---|---|
| Critical / High / Medium / Low Security finding | 40 / 20 / 8 / 3 |
| Info Security finding | 0 |
| Non-security issue (Manager fragility, Engineer footgun or edge case) | 2 each, 20 at most |

The most severe finding sets the range the score must land in, in both directions: Critical 0–39, High 25–69, Medium 50–89, otherwise 70–100. A raw score outside that range is capped or floored to it. One serious finding can't hide in an otherwise clean report, and a pile of small issues can't push a report into a band its worst finding doesn't justify. Bands: 90–100 Excellent, 70–89 Good, 50–69 Fair, 25–49 Poor, 0–24 Critical.

The score rates the code, not the Mac Admin. Mac Admin tools are meant to be powerful, and deploying them carefully is the admin's job:

- **Capabilities aren't defects.** A documented operation behind an admin-controlled gate (a Jamf parameter, policy scope, a confirmation dialog) isn't scored, even if it removes an EDR agent or deletes data. It counts only when the gate can be bypassed, fails open, or is defeated by the code. A blank-parameter default that offers everything counts as one Low finding.
- **Documented-deployment headline.** When a severity depends on deployment, the headline assumes the tool is deployed as documented. The misconfigured score is given as the alternate, and the report lists each assumption as an **Operator baseline** checklist. If the code offers no safe way to deploy, the exposure counts in the headline.
- **Maintainer-only tooling isn't scored.** Examples are release helpers and sync scripts. Its issues are still reported.

The full rules are in `monocle/SKILL.md`, Step 5 and Rule 14.

Fetching from GitHub works best with an authenticated [`gh`](https://cli.github.com) CLI, which also covers private repos. In Codex, fetching from GitHub needs network access in the sandbox; if network access is off, clone the repo locally and point Monocle at the path.
