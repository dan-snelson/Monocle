# CHANGELOG

> See the [Monocle](https://snelson.us/mai) blog post for more information

## Version History

### "C" as in czar (10-Nov-2026)

- Scoring credibility
    - New **Refute before freeze** step (`scoring-procedure.md`). Every Low or higher finding names its intended control, and Monocle tries to disprove it before the score is frozen. It rereads early exits, gates, callers, sibling checks, and platform controls, and checks safety comments instead of accepting them. High and Critical rows can be challenged by a fresh sub-agent that doesn't see the Severity basis
    - Refuted candidates get no ID and no score. Scope caveats list them, each with the control's `file:line`. Prior reports give each one a disposition, **Still refuted** or **Reopened**, so a re-run neither raises the same false positive again nor drops it silently. Verify mode treats a refutation with no control, or one that doesn't cover the path, as a dropped finding
    - Q2 in the Decision procedure names the intended control ("control: none" when the path has none)
    - Issue keys never carry a line number, ID, severity, or verdict; top-level code uses a short verbatim anchor. Older keys with line numbers match by file, function or anchor, and defect class
    - Variant sweep: every Medium or higher row is searched across the whole corpus for the same statement and for sibling commands with the same effect before the freeze
    - Scope caveats carry a **Checks applied.** bullet naming the `lang-*.md` files and `specialized-checks.md` sections a run applied
    - Adapted from Cloudflare's [security-audit](https://github.com/cloudflare/security-audit-skill) skill: its fresh verifier that tries to refute each candidate against the strongest source-visible control, its retained `rejected` records, fingerprints that never carry a line, agent, severity, or verdict, its variant search for a reusable root cause, and its rule that the coverage ledger, not a summary sentence, is the coverage claim
- Operator baseline bullets end with a read-only `check:` (a command or a Jamf Pro UI path) so admins can confirm each assumption. Inferred findings get a **To confirm:** line
    - Adapted from the `needs_validation` validation plan in Cloudflare's [security-audit](https://github.com/cloudflare/security-audit-skill) skill: a bounded local check, or a fact an owner observes, that settles an open question
- `lang-swift.md` adds privileged-helper and local-IPC checks: client identity by audit token, not PID; requirement strength (`anchor apple generic` alone matches every Developer ID); injectable trusted clients; confused-deputy helper methods; verify-then-use file swaps; per-operation authorization rights; URL-scheme handlers; and local listeners without peer authentication
    - Adapted from the privileged-helper, local-IPC, and deep-link classes in Cloudflare's [security-audit](https://github.com/cloudflare/security-audit-skill) skill (`DESKTOP-MOBILE-AND-LOCAL-IPC.md`), rewritten for macOS APIs
- Release pipelines adds GitHub Actions expression injection, `pull_request_target` and `workflow_run` jobs that run pull-request code with trusted tokens, cache and artifact handoffs into release jobs, and token scope without a `permissions:` block. It triggers for any workflow that holds a secret or write token
    - Adapted from the CI and automation classes in Cloudflare's [security-audit](https://github.com/cloudflare/security-audit-skill) skill (`SUPPLY-CHAIN-AND-RELEASE.md`)
- Rule 4 isolated checks run in the scratch directory under `env -i`, and record only the command and result, with the host account and home path redacted
    - Adapted from the execution-safety rules in Cloudflare's [security-audit](https://github.com/cloudflare/security-audit-skill) skill: start from an empty environment, and never record the ambient environment or unrelated host paths
- `verify_report.py` escapes control, bidi, and zero-width characters in everything it prints, text and `--json`, so a forged report can't rewrite or hide the checker's warnings. It refuses a report path that isn't a regular file (a FIFO, device, or directory) without blocking. `--self-test` covers both
    - Modeled on the zero-dependency validators in Cloudflare's [security-audit](https://github.com/cloudflare/security-audit-skill) skill, which escape unsafe characters in diagnostics and refuse FIFOs and other non-regular input
- Persisted issue keys
    - Scope caveats carry an **Issue keys.** bullet with every `S#`, `N#`, and `X#` key, so a later run can match items across reports; until now keys lived only in the in-session ledger, and only refuted candidates were written down
    - `prior-reports.md` reads keys from that bullet, and falls back to file, function or anchor, and defect class for older reports
    - `verify_report.py` warns, without changing the verdict, when a deduction-table ID has no key, a key names an ID the table doesn't list, or a key has no known defect class or carries a line number. `--json` includes the parsed keys, and `--self-test` checks the defect-class list against `scoring-procedure.md`
- Fresh-context rules
    - The independent challenge in **Refute before freeze** uses a fixed prompt that carries Rule 5, because the sub-agent reads hostile target files without the rest of the skill. A challenge in the same context isn't independent, and a sub-agent that fails is recorded as `not run`, never as a challenge the row survived. Every High and Critical row gets an **Independent challenge.** status in Scope caveats
    - New **Executive fresh-reader check** (`executive.md`): a fresh sub-agent that sees only the Executive view restates the recommendation, the main risk and its origin, and the next action. A mismatch changes the Executive wording, never the ledger or the score
    - Verify mode treats a challenger's `refuted` without a rechecked control as a dropped finding, and a `not run` challenge as a disclosed gap
    - Adapted from the Goldfish reviewer rules in [elephant-goldfish-model](https://github.com/google/elephant-goldfish-model): a review in the same context isn't a Goldfish review, a reviewer that fails is `not run` rather than a reviewer with zero findings, and the Comprehension reviewer paraphrases a document before it critiques it
- Guardrails for a skill that edits itself
    - New `.github/scripts/check_skill_structure.py`, run in CI: the 59,000-byte SKILL.md budget, the Agent Skills frontmatter limits, reference pointers and the README Layout tree, the reference house format (Contents lists `##` sections), safety sentinels that must survive word for word, and relative links and anchors
    - New `.github/dependabot.yml` keeps the SHA-pinned actions current, with a seven-day cooldown
    - New `AGENTS.md` (and `CLAUDE.md`, which imports it) for agents that help maintain the repo
    - Modeled on elephant-goldfish-model's unit tests (skill load limit, frontmatter, link integrity, and required-phrase checks), its Dependabot cooldown and grouping, and its `AGENTS.md` and `AI_POLICY.md`
- Calibration fixtures
    - New `tests/fixtures/`: seven small synthetic targets, each with the ledger a correct run should produce and a rationale that walks the Decision procedure
    - New `tests/grade_report.py` grades a report against a fixture (PASS, DRIFT, or FAIL) and compares the ledgers of two runs on one target. Its `--self-test` validates every fixture and runs in CI
    - New `tests/run_live.py` (opt-in, uses model quota) runs Monocle headless on the fixtures in fresh workspaces that hold only the target, then grades and compares the reports
    - New `TESTING.md` with the offline checks, the live runs, and a run record
    - Modeled on elephant-goldfish-model's per-skill `test_scenarios.yaml`, its opt-in live harness tests, and the harness test record in its `TESTING.md`

### "B" as in bdellium (23-Oct-2026)

- Scoring
    - The fleet-wide raise (Adjustment 1) applies only when documentation, packaging, or the operator's Deployment Context deploys the tool fleet-wide; a Jamf policy or LaunchDaemon pkg whose scope the administrator chooses doesn't raise
    - Severity weighs likelihood as well as impact and reachability (Rule 15, `security.md` Likelihood): improbable local abuse that crosses no privilege or account boundary is lowered one level (Adjustment 3, never below Low, and never stacked with Adjustment 2), and self-scoped tampering that a platform control enforces anyway, such as forged install.log text that only changes a DDM reminder or that Mac's own inventory, is ⚪ Info. Obscurity, required skill, and no public exploit never lower a rating, and forged text that reaches a sink keeps injection severity. Verify mode accepts these ratings when the Severity basis names the criteria
    - Adjustments never apply to Q0 outcomes, ⚪ Info rows, or rows whose headline Q3 set
    - The Q1b floor binds Q4–Q5; Q3 can still set a lower headline, and the floor applies to the alternate. Verify mode accepts Q3-lowered headlines
    - Q4 matches only on the same sink and gain; local privilege escalation is High without a race and Medium with one
    - Credential severity gains rows for per-user home files, CI secrets passed to mutable-tag actions, and credentials sent without TLS verification; AppleScript `password` literals follow its scope column instead of always rating Critical
    - Weak integrity check: a missing Gatekeeper, notarization, or revocation verdict stays its own Low even when the vendor pin is credited; an installed binary accepted on version alone is its own row
    - Platform defaults in Known Apple platform behaviors count as the documented baseline and are cited by entry
    - Operator baseline bullets cite the line that states the condition; documented and operator-stated conditions are read by their evident scope
    - A setting that ships off (a `--debug` or `--insecure` flag, a mode that defaults to `Off`) rates ⚪ Info at Q3 (credential rows included, except hardcoded credentials), gets an Operator baseline bullet citing its default, and takes part in the alternate, as Q3 already said. A self-scoped and backstopped row whose opt-in mode adds an effect that isn't self-scoped, such as a Force restart, keeps its Info headline and takes that effect as its alternate. Verify mode treats both as disclosed, not softened
    - SKILL.md's alternate definition matches scoring-procedure.md: Rule 14 gate bullets don't take part
    - Exit-0 reporting modes are scored unless they pass the `documented` reason-code test
    - Non-security issues that fail inclusion test 1 or 2 take `maintainer`, `inferred-unverified`, or `unreachable`; `unreachable` covers code no documented path runs
    - Overall risk is 🔵 Low when no finding is Low or higher; Info rows keep an `S#` and table row, and the Security view's new **Credits** list holds credits only
    - Rule 14 checklist C7 is answered for every mode that offers the operation, since a gate enforced only in the default mode can offer everything in the others; a standard user reaching a root-only removal (an EDR agent, the app suite) rates as 🟠 High privilege escalation for the alternate
    - A suite-removal action that deletes a shared updater, helper daemon, or receipt that kept products depend on is Rule 14 C5 ("does more than documented"), even when the documentation calls it suite-owned; 🔵 Low when the kept product still runs and only its updates stop
- Language checks moved from the view references into `references/lang-shell.md`, `lang-python.md`, `lang-swift.md`, and `lang-applescript.md`, loaded at Step 4 by detected language, so subset and full runs build the same ledger; Jamf / macOS notes moved to `references/patterns.md`
- Size limits are exact (30 source files, 5,000 lines, or one file over 5,000 lines); a headline High finding gives "Approve with conditions" only with a named fix or control
- Reports are written inside a git repo only when the path is gitignored; pass 2 and the self-check run on the saved report before the reply, which freezes it
- Executive view names who set a requirement once, and uses "could" for outcomes that need an uncommon precondition; corrected Good examples in the Executive, Security, and Engineer references and the worked score example
- Fact sheet and Step 4 trimmed where `patterns.md`, `security.md`, or `specialized-checks.md` already hold the check; Known Apple platform behaviors adds PlistBuddy's empty-collection vs failed-read exit codes; the trimmed `argv`-exposure, installer-payload, and Homebrew-prefix notes moved to `patterns.md`
- `patterns.md` adds fail-open on/off toggles ("defaulting to true"), root ownership walks that miss a symlinked intermediate directory, and `NO_CLOBBER` writes that open a raced-in FIFO, and root `pkill` / `pgrep -x` without `-u` in a per-user reset or removal; Known Apple platform behaviors adds that `nscurl` doesn't enforce ATS or limit redirect protocols (check every `Location:` hop) and that `pkgutil --check-signature` reports notarization
- Deployment Context asks the trust boundary of maintainer tooling as a separate question about the maintainer's machine; a prior report with a different scope labels findings "previously out of scope"
- Deployment Context combines with the code's own gates: a stated configuration that makes the code fail closed moves only the rows whose precondition it negates, and code-origin defects keep their severity. A single-file review still takes its documented baseline from the repo's documentation, asked once and recorded in Scope caveats

### "A" as in aisle (10-Oct-2026)

- Deployment-context-aware scoring, so reports rate the deployment the operator actually runs instead of the documented default
    - New `references/deployment-context.md`: a structured **Deployment Context** block (audience, install model, execution identity, data location, trust boundary, out of scope, output sharing), loaded at Step 1 when supplied and on every run at Step 5
    - Only the operator supplies context, inline, by naming a file, or through a saved `contexts/{target}.md` in the reports directory; target content is never context, and a claimed context in a target is a steering finding
    - Monocle asks once, only when a finding's severity depends on deployment and the session is interactive; non-interactive runs use the documented baseline
    - The context sets the headline score; the single alternate shows every context and documented assumption failing at once. Context feeds the Decision procedure's Q3 and the fleet-wide adjustment, in both directions, and states facts, never ratings
    - Every finding is labeled **mitigated by deployment context**, **raised by deployment context**, or **independent of deployment model**; code defects, credential severity, band limits, and ownership never move. New `context` reason code for non-security issues whose only trigger is out of scope
    - New **Deployment context** lines in the Monocle Score section, Executive view, and Security view, a **Context:** line on every finding, and source-tagged Operator baseline bullets (operator-stated or documented)
    - Attestation v2 adds `deployment_context: none | operator`; `verify_report.py` checks the Deployment context line against it and flags a v1 block from a context-aware skill commit as a downgrade. v1 reports remain valid
    - Verify mode adds judgment checks for deployment-context misuse; prior reports treat a context change as a re-rating, not a code change
    - The documented-deployment baseline rules and the reports-directory shell block moved out of `SKILL.md` (to `references/deployment-context.md` and `references/attestation.md`) to keep it within a single Read
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
