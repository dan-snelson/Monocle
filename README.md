# Monocle

Monocle inspects scripts (and small local repos) and produces four audience-specific summaries: Executive, Security, Manager, Engineer.

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
- `Summarize this repo for stakeholders: ~/Projects/setup-your-mac`
- `$monocle just the engineer view of ./scripts/enroll.zsh` (Codex)

All four views are produced by default. To get a subset, ask for it: "just the executive and manager views".

Fetching from GitHub works best with an authenticated [`gh`](https://cli.github.com) CLI, which also covers private repos. In Codex, fetching from GitHub needs network access in the sandbox; if network access is off, clone the repo locally and point Monocle at the path.
