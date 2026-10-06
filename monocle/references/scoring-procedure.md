# 🧮 Scoring Procedure

## Contents
- Purpose
- Issue ledger
- Defect classes
- Distinct-issue test
- Rule 14 checklist
- Non-security inclusion test
- Operator baseline and alternate
- Freeze check

## Purpose

The fixed procedure that turns the fact sheet into scored issues, for SKILL.md Step 5 item 1. Load it on every run after Step 4 and before writing any view, together with the Decision procedure in `security.md`. Verify mode (`verify-report.md`, Step 2) uses it too.

Two runs on the same code and documentation should produce the same ledger. Each rule here removes a judgment call that used to move scores between runs. The procedure decides how issues are counted, never what you look for: Step 4 stays open-ended, and anything you notice gets a ledger row.

---

## Issue ledger

Extend the fact sheet with one row per candidate issue: every Step 4 hit, and every Security finding, Manager fragility hotspot, Engineer footgun, and unhandled edge case you might write.

| Field | Content |
|---|---|
| ID | `S#` for a Security finding, `N#` for a scored non-security issue, `X#` for an issue that is not scored |
| Key | `{file}:{function or first line} · {defect class}` (classes below) |
| Location | Every `file:line`, checked in SKILL.md Step 5 item 7, pass 1 |
| Evidence | Observed, or inferred with its basis (SKILL.md Rule 3) |
| Severity basis | The path through the Decision procedure in `security.md`, or the inclusion-test result |
| Disposition | Scored at its weight, or not scored with exactly one reason code |

- **No ledger row, no score.** A view mentions only issues that have a row. If writing a view turns up a new issue, add a row, rate it with this procedure, update any views already written, and recompute the score. Never count a bullet that has no row.
- **Number in a fixed order.** Number `S#` by severity, then by first `file:line`. Number `N#` and `X#` by first `file:line`. Use new sequential IDs, never suffixes such as `S2a`.
- **Views render the ledger.**
  - The Security findings table lists exactly the `S#` rows.
  - Each Manager fragility hotspot, Engineer footgun, and edge case ends with `(N#)`, `(see S#)`, or `(not scored: {reason code})`.
- **The deduction table is a projection of the ledger.**
  - The Non-security row lists the `N#` IDs and short names.
  - The Not scored row lists each `X#` with a short name and its reason code, maintainer tooling included.

## Defect classes

Use exactly one class per key, so keys match across runs:

- `privilege-escalation`
- `injection`
- `trust-check`: ownership, path, or signer checks
- `integrity`: download or install verification
- `secret-exposure`
- `disclosure`: non-secret data
- `shared-path`: symlink, hard link, or race in a shared directory
- `gate`: Rule 14 gates and mode parsing
- `exit-status`: wrong success or failure reported
- `wrong-target`: wrong user, path, or process
- `state`: caches, persistence, partial runs
- `dependency`
- `platform-variant`: architecture, OS, shell, or prefix
- `docs`

## Distinct-issue test

Ask these in order. The first yes decides.

1. **Same control?** All gaps in one check, gate, or guard are one issue, rated at its most severe gap. List each gap in the finding. Example: a trust check that skips parent directories and also runs only once, before a long wait.
2. **Same pattern, same severity?** One defective statement or pattern repeated at several sites is one issue that lists every site. Split out only the sites that rate at a different severity.
3. **Same root cause in several views?** It is one issue, at its highest weight. Security outranks non-security.
4. **Does one enable the other?** A compounding chain isn't a new issue. Rate each link on its own, and explain the chain in Cross-cutting notes.
5. **Tie-break.** Two observations are one issue only if one minimal edit closes both. The same consequence from different triggers is two issues.
6. Otherwise, the observations are distinct issues.

## Rule 14 checklist

Run the checklist for each high-impact operation in the fact sheet's Privileged operations row:

- deleting or uninstalling;
- removing or disabling security tooling;
- changing accounts, credentials, or encryption;
- restarting or logging out;
- installing or executing software chosen by configuration;
- changing security settings.

The checklist decides only whether the operation *being available* is scored. Defects in how the code performs the operation (path trust, integrity, races, injection) skip it and go straight to the Decision procedure.

| # | Question | Record |
|---|---|---|
| C1 | Is it the tool's stated purpose? | README or header line |
| C2 | Is it documented under its real effect? | Doc line |
| C3 | Does it sit behind an admin gate (a Jamf parameter, policy scope, an in-script allowlist or item array, an operation mode)? | Code line |
| C4 | Can a non-admin reach or set the gate (a user-writable config, a policy whose gate the user controls)? | Yes/No + line |
| C5 | Does it do more than documented (for example, "remove the app suite" also deleting data that sibling products keep in the same vendor folder)? | Yes/No + line |
| C6 | Does the code defeat the gate (a wrapper that drops `"$@"`, a gate read after the action)? | Yes/No + line |
| C7 | With the gate blank or unset, does it offer nothing or a safe minimum, or everything? | Safe / Everything + line |
| C8 | With a non-blank invalid value (typo, wrong case, unknown word), is it rejected, or does it fall through to a high-impact branch? | Rejected / Falls through + line |

| Answers | Disposition |
|---|---|
| C1–C3 yes; C4–C6 no; C7 safe; C8 rejected | Not scored (reason code `capability`). Add one Operator baseline bullet per distinct admin gate, marked "(Rule 14 gate; not scored)" |
| As above, but C7 is "everything" | 🔵 Low secure-default gap (Origin: Code + Deployment). For the alternate, rate the operation with the Decision procedure, Q2–Q5, with this precondition met: "the gate is blank in a policy the documented audience can run" |
| As above, but C8 falls through | The same as C7 "everything" when only an admin sets the value. Full severity from Q2–Q5 when a non-admin can influence it |
| C1, C2, or C3 no; or C4, C5, or C6 yes | Not a capability. Rate it with the Decision procedure, Q1–Q5, on its real exposure |

A confirmation dialog shown to the end user gates only operations limited to that user's own session or data, such as a restart or logout. It gets no Operator baseline bullet.

## Non-security inclusion test

Apply the reason codes first: any match makes the issue an `X#`, not scored. Otherwise it is an `N#` and scores 2 points when all three of these hold:

1. It is observed, with a `file:line`, in code that ships to or runs on endpoints.
2. Its trigger is reachable in a supported configuration: a documented platform, mode, or deploy path.
3. Its consequence is one of these:
   - a wrong result is reported: an exit code, policy status, or inventory value, or the code's own message misstates what it did;
   - an action is applied to the wrong user, path, or process;
   - data is lost, or something changes persistently that shouldn't;
   - the run aborts or hangs where it should continue;
   - intended work is silently skipped;
   - a documented feature doesn't work on a supported platform.

| Reason code | Meaning |
|---|---|
| `maintainer` | Maintainer-only tooling: release and deploy helpers, sync or parity scripts, and CI that doesn't sign or deploy. Its Security findings are still scored |
| `documented` | Deliberate behavior that is both documented and shown, through UI the end user sees or a non-zero exit for unattended runs. A log line alone doesn't count as shown |
| `ownership` | Bus factor, a single maintainer, missing tests or CI |
| `docs` | Documentation drift with no effect on endpoints. Give it a Manager action item |
| `dependency-handled` | A missing dependency stops the run with a logged error and a non-zero exit |
| `config` | Organization-specific constants an adopter is expected to edit |
| `malformed-config` | Needs a value the documented format forbids, for example a delimiter inside a field |
| `unreachable` | Dead code with no current caller |
| `immaterial` | None of the listed consequences, including slow growth bounded by user-started runs |
| `capability` | An intended capability that passes the Rule 14 checklist |
| `inferred-unverified` | Depends on unverified third-party behavior along a code path you didn't trace |

## Operator baseline and alternate

Build both mechanically from the ledger:

- **One bullet per scored finding whose headline depends on a deployment condition:** `{condition, as the documentation states it} ({doc file:line}) (S# → {severity} if not)`. If no documentation line exists, the control is undocumented, and the headline takes the unsafe rating (SKILL.md Step 5, "Undocumented controls get no credit").
- **Then one bullet per distinct admin gate** from the Rule 14 checklist, marked "(Rule 14 gate; not scored)".
- **Order:** finding bullets by ID, then gate bullets. If both lists are empty, write "None — the score doesn't depend on deployment."
- **One alternate only.** Assume every finding bullet's condition fails at once; the Rule 14 gate bullets don't take part. The alternate's condition text is the negation of those finding bullets. Recompute from the same ledger with the alternate severities, and clamp the result the same way.
- **Read operator instructions by their evident scope.** An instruction to secure or validate a path covers every directory on that path.
- **Host evidence never sets a severity.** The reviewer's Mac can confirm an Apple platform default (SKILL.md Rule 13). It can't establish a deployment state, or what another tool's installer did.

## Freeze check

Before writing any view, confirm:

- Every Step 4 hit, and every bullet you plan to write, has a ledger row.
- Every `S#` has a Severity basis. Every Info row passes the Info test in Q2. No Low is folded into the roll-up.
- Every `X#` has exactly one reason code.
- The distinct-issue test was applied, and IDs are numbered in the fixed order.
- The Operator baseline and the single alternate were built as described above.
- The score was computed from the ledger.
