# Security Policy

Thank you for helping keep **Monocle** secure.

Monocle is an [Agent Skill](https://agentskills.io) for Claude Code and Codex. It ships no compiled code, but its instructions direct an AI agent to read **untrusted targets** (scripts, repos, GitHub URLs, and diagnostic bundles), run local commands against them (`gh`, `curl`, `git clone`, `unzip`, `semgrep`), and write reports that contain **security findings**. On request, its **post-chat-refine** pass edits the skill's own files. The maintained attack surface is **`monocle/SKILL.md`** and everything under **`monocle/references/`**.

## Supported Versions

Monocle has no tagged releases yet. Only the current `main` branch receives security updates.

- Current stable: **`main`**
- Current prerelease line: **`development`**
- Older copies of the skill receive no security patches.

If you installed Monocle by copying the `monocle/` directory, copy it again from current `main` before requesting security support.

## Scope

Report a vulnerability when Monocle's instructions can lead an agent to:

- Execute target code, or shell syntax embedded in a target, a GitHub URL, a ref, or a file path
- Follow instructions embedded in target content (prompt injection) in a way that changes the analysis, hides findings, or runs commands
- Expose secrets from a target in a report, chat reply, or skill edit without redaction
- Write reports to an unintended location, overwrite existing files, or place reports in a git-tracked path without a warning
- Leak target-identifying details into `SKILL.md` or `references/` through post-chat-refine

Inaccurate findings, missed issues, and scoring disagreements are quality issues, not vulnerabilities. Open a regular issue for those.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, report it privately.

**Do not** open a public GitHub Issue or Pull Request that discloses the vulnerability.

Send reports to: **security@snelson.us**

Please include as much of the following as possible:

- A clear description of the issue and its potential impact
- Steps to reproduce it, including a minimal target (script, URL, or bundle) that triggers it
- The `main` commit SHA of the Monocle copy you used
- The agent and version (Claude Code or Codex), plus its permission or sandbox mode
- The relevant agent transcript excerpt, or the generated report, with secrets redacted
- Any suggested mitigation or fix
- Your name or handle, if you want attribution

You should receive an acknowledgment within **48 hours**. We will work with you to validate the report, develop a fix, and coordinate disclosure once the issue is resolved.

## Safe Use Guidance

- Install Monocle only from this repository, and review `monocle/` before installing it.
- Run Monocle with your agent's permission prompts or sandbox enabled. Monocle analyzes untrusted code, so review any command the agent proposes that isn't a read, fetch, or static scan.
- Treat every report as sensitive. Reports describe exploitable weaknesses in the target, so don't commit them or attach them to public issues.
- If you set `MONOCLE_REPORTS_DIR` inside a git repository, gitignore that path there.
- For bundles you intend to share publicly, use Monocle's verdict as one input and still review the bundle yourself before posting it.
- Review the diff after accepting **post-chat-refine** and before committing it. Confirm that no target names, hostnames, usernames, version strings, or secrets were added to the skill files.

## Code Security Practices

- This repository is scanned with **Semgrep** using the `p/r2c-security-audit`, `p/ci`, and `p/secrets` rulesets.
- **Gitleaks** scans repository history for potential credential or secret exposure, including any that post-chat-refine might copy from a target into the skill.
- Fenced `bash`, `sh`, `zsh`, and `python` blocks in tracked Markdown, which are the commands an agent runs, are syntax-checked with **`zsh -n`**, **`bash -n`**, **`sh -n`**, and Python's `ast.parse`. Fenced `bash` and `sh` blocks are also checked with **ShellCheck**.
- Skill-integrity checks block hidden or bidirectional Unicode in tracked files, HTML comments in tracked Markdown (invisible when rendered, but read by agents), tracked Monocle reports, and tracked `.claude/settings.local.json`.
- Monocle's rules forbid executing analyzed code (`SKILL.md` Rule 4) and require treating all target content, including agent configuration shipped in the target, as untrusted data (Rule 5).
- Secrets found in a target are redacted to their first 4 characters in every report (Rule 6).
- GitHub URL components are validated against allowlist patterns and passed to commands only as quoted variables (`references/github-input.md`, Safe URL handling).
- Semgrep scans use `--metrics=off` and explicit `--config` rulesets, so a config file shipped in the target repo is never used (`references/semgrep.md`).
- This repository's `.gitignore` excludes `/reports/`, and the skill checks that any reports directory inside a git repository is gitignored before writing.
- post-chat-refine strips identifiers and runs a fingerprint check over the lines it adds (`references/post-chat-refine.md`).
- Changes are reviewed with attention to shell quoting in documented commands, untrusted-input handling, report destinations, and what post-chat-refine may write.

## Disclosure Policy

- We follow coordinated disclosure.
- We will prioritize a fix before sharing public technical details.
- Security fixes will be committed to `main` as quickly as practical, with a commit message noting the fix.
- We will credit the reporter unless anonymity is requested.

## General Security Questions

For non-vulnerability questions or general usage concerns, open an issue on [GitHub](https://github.com/dan-snelson/Monocle/issues).

Last updated: October 2026
