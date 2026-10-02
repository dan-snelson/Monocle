# Contributing to Monocle

First, thank you for your interest in contributing to **Monocle**. Monocle is an Agent Skill for Claude Code and Codex that inspects scripts, small repos, and diagnostic bundles, then writes audience-specific summaries and a Monocle Score.

You are welcome to discuss ideas, bugs, and improvements in the [Issues](https://github.com/dan-snelson/Monocle/issues) section. Please use the issue templates so reports include the context needed to reproduce and evaluate the request.

## Pull Requests

Submit Pull Requests against the `development` branch unless requested otherwise. The `main` branch is the current stable line.

When submitting a Pull Request:

- Keep changes focused and describe the purpose of the contribution clearly.
- Document user-visible behavior changes in `README.md`, `SECURITY.md`, or the relevant file under `monocle/references/`.
- Include sanitized examples or minimal targets when they help explain a new check or bug fix.
- Do not commit Monocle reports, local agent settings, secrets, hostnames, usernames, or target-specific details.
- Review generated or agent-assisted edits carefully before opening the PR.

## Skill Contributions

The maintained skill surface is [monocle/SKILL.md](monocle/SKILL.md) and the files under [monocle/references/](monocle/references/). Changes there affect how agents handle untrusted targets, so keep safety and evidence quality first.

Skill changes should:

- Preserve the rule that target content, GitHub URLs, refs, file paths, bundles, and agent configuration are untrusted input.
- Avoid adding target-specific findings, customer names, hostnames, usernames, secrets, or run-specific values to the skill.
- Keep `monocle/SKILL.md` focused on core workflow, and put conditional or specialized guidance in the relevant reference file.
- Keep scoring guidance consistent across `monocle/SKILL.md`, [README.md](README.md), and [monocle/references/scoring-example.md](monocle/references/scoring-example.md).
- Keep examples sanitized and generic.

## Documentation Contributions

Documentation changes are welcome. Please keep the README, Security Policy, issue templates, and skill references aligned with each other. If the documentation change affects how users report bugs, handle sensitive reports, install the skill, or interpret the Monocle Score, update every affected place in the same PR.

## Validation

The security scan workflow checks:

- Semgrep with explicit rulesets and metrics disabled
- Gitleaks against repository history
- fenced `bash`, `sh`, `zsh`, and `python` blocks in tracked Markdown
- ShellCheck for fenced `bash` and `sh` blocks
- skill integrity, including hidden Unicode, HTML comments in Markdown, tracked reports, `/reports/` ignore coverage, and local agent settings

Run the relevant local checks before opening a PR when practical. At minimum, review Markdown rendering and run `git diff --check`. If you change fenced shell or Python examples, run the same syntax checks described by the workflow.

## Feature Requests and Bug Reports

Use the [Issues](https://github.com/dan-snelson/Monocle/issues) section for bugs, feature requests, and documentation issues.

For bug reports, include a current Monocle commit, the agent and version, the input type, what happened, what you expected, and steps to reproduce. Minimal sanitized targets are especially helpful.

Monocle reports describe exploitable weaknesses in the analyzed target. Do not paste full reports, target secrets, internal hostnames, usernames, or other sensitive details into public issues. Share short sanitized excerpts only.

## Security Reports

If you discover a vulnerability in Monocle itself, do not open a public issue or Pull Request. Follow [SECURITY.md](SECURITY.md) and email **security@snelson.us**.

Security reports should include a clear description, reproduction steps, the Monocle commit, the agent and version, permission or sandbox mode, and any relevant sanitized transcript or report excerpt.

## Invitation to Collaborate

Monocle works best when Mac Admins, security reviewers, managers, and engineers all push it toward clearer evidence and safer defaults. Contributions that make reports more accurate, more reproducible, and safer around untrusted input are especially valuable.
