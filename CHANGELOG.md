# CHANGELOG

> See the [Monocle](https://snelson.us/mai) blog post for more information

## Version History

### "Initial Commit" (04-Oct-2026)

- Initial release of Monocle, an [Agent Skill](https://agentskills.io) for Claude Code and Codex that inspects scripts, small repos (local or on GitHub), and diagnostic/support bundles
- Four audience-specific views: 👔 Executive, 🔒 Security, 📋 Manager, and 🛠️ Engineer (all four by default; any subset on request)
- `0`–`100` **Monocle Score** with per-severity deductions, a capped non-security deduction, and severity-based floors and caps so one serious finding can't hide in an otherwise clean report (#1, #5)
- Every Security finding carries an origin: Code, Platform, Deployment, or a mix (#1)
- Rule 14, "Rate defects, not capabilities" (#1)
- Prior-report check: an earlier report on the same target serves as a checklist, never as current evidence, and counting corrections are called out in the **Score change** line (#1, #6)
- Reports saved to `$MONOCLE_REPORTS_DIR`, this repo's git-ignored `reports/`, or `~/monocle-reports`, with an inline fallback when the directory isn't writable
- On-demand reference files: GitHub input handling, large-target reading plans, risky Jamf / macOS / Python patterns, Semgrep scan and triage, specialized checks (including bundle intake), worked scoring example, `post-chat-refine`, and `binge-and-purge` (#2)
- Contents sections for every reference file over 100 lines; post-DOR review learnings (#3)
- Readability-focused report updates, plus Rule 13, "Known Apple platform behaviors" (#5)
- New specialized checks for root `chown -R` over user-writable trees (hard-link ownership takeover) and for fixes applied to one root operation but not its siblings (#6)
- Known Apple platform behaviors list moved from `SKILL.md` to `references/patterns.md` (#6)
- Report attestation block and "verify this Monocle report" mode, backed by `monocle/scripts/verify_report.py` (standard-library Python) (#6)
- Security Scan workflow: Semgrep, Gitleaks, syntax checks and ShellCheck for documented commands, hidden-Unicode and HTML-comment blocking, and a report-checker self-test that catches scoring drift (#2, #6)
- `CONTRIBUTING.md`, `SECURITY.md`, and GitHub issue templates for bug reports, documentation, and feature requests (#2)
- Scoring consistency: `references/scoring-procedure.md` (issue ledger, distinct-issue test, Rule 14 checklist, non-security inclusion test with reason codes, mechanical Operator baseline), a Decision procedure in `references/security.md`, and prior reports as a disposition checklist
