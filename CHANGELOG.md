# CHANGELOG

> See the [Monocle](https://snelson.us/mai) blog post for more information

## Version History

### "A" as in aisle (05-Oct-2026)

- Scoring consistency, so re-runs on the same code give the same Monocle Score
    - New `references/scoring-procedure.md`, loaded on every run before any view is written: an issue ledger with stable IDs (`S#`, `N#`, `X#`) and issue keys, a distinct-issue test, a Rule 14 checklist, a non-security inclusion test with reason codes, and a mechanical Operator baseline with a single alternate
    - Severity Decision procedure in `references/security.md`, recorded in a new **Severity basis** line on every finding. A security-relevant gap with a concrete fix is at least Low, the fleet-wide raise never reaches Critical, and Overall risk always equals the highest headline severity
    - Step 5 "Rate and freeze": the score comes from the frozen ledger, not from view prose. Every Low or higher finding gets its own row; the roll-up holds credits and Info only
    - Visible ledger tags: Manager and Engineer bullets end in `(N#)`, `(see S#)`, or `(not scored: …)`, and the Not scored row lists reason codes
    - Targets within the size limits are read in full, with no pattern-scanning. New fact-sheet details cover log-file modes, exit paths, who can write executed files, and where the console user is resolved
    - Inferred findings are kept, labeled, and rated, never dropped
    - Prior reports are now a disposition checklist: every earlier item is Confirmed, Re-rated, Closed, or Rejected
    - Verify mode adds ledger checks for parked Lows, roll-up Lows, missing reason codes, and missing tags
    - The refactor-snippet check moved from `SKILL.md` to `references/engineer.md`

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
