# 📈 Monocle Score Worked Example

## Purpose

A fully worked Monocle Score calculation for SKILL.md Step 5. It shows the issue ledger (`scoring-procedure.md`) turned into a score, a Severity basis for each finding (`security.md`, Decision procedure), reason codes for what isn't scored, a headline with a single alternate, and a band floor. Load it when a score depends on deployment (headline vs alternate), when a band clamp applies, when an admin-gated capability needs rating under Rule 14, or when an operator supplies a Deployment Context (`deployment-context.md`).

---

**Worked example.** Suppose a Jamf Self Service helpdesk toolkit repairs, resets, or removes managed apps. It offers about 15 actions, including removing the EDR agent, and a Jamf parameter supplies an allowlist of actions. Under these rules:

- **Findings at the baseline.** IDs are numbered by severity, then by first location.

  | ID | Finding | Severity basis | Rating | Points |
  |---|---|---|---|---|
  | S1 | Root installs packages from a user-writable staging directory with a name-only signature check, and re-reads the directory after a long download | Q2: a local user gets root code execution; nothing in the deployment closes it; Q5 High. Both gaps belong to one trust check (distinct-issue test 1) | 🟠 High (Code defect) | 20 |
  | S2 | — | — | 🟡 Medium | 8 |
  | S3 | EDR removal and full app removal are offered when the allowlist parameter is blank | Q0, Rule 14 checklist: C1–C6 pass, C7 offers everything → secure-default gap | 🔵 Low | 3 |
  | S4 | Root runs `/usr/local/bin/dialog` | Q2: root code execution if the directory is user-owned; Q3: the platform default (root-owned on Apple silicon) closes the precondition | 🔵 Low | 3 |
  | S5–S7 | — | — | 🔵 Low | 9 |
  | S8 | A tracked self-extracting wrapper | Q3: the documentation deploys the main script, never the wrapper | ⚪ Info | 0 |
  | S9 | — | — | ⚪ Info | 0 |

  Security total: 43. The other actions (repair, reset) pass the Rule 14 checklist and aren't scored. Their gate is the same allowlist, which the S3 bullet already lists, so they get no separate Operator baseline bullet.
- **Non-security.** Nine endpoint issues (N1–N9) pass the inclusion test and cost 18. Not scored:
  - X1, a local release helper (`maintainer`)
  - X2, a repo sync script (`maintainer`)
  - X3, README drift (`docs`)
  - X4, a restart deferred to the next login, which the README and the completion dialog state (`documented`)
- **Headline:** 100 − 61 = **39/100 (🟠 Poor)**. The High range (25–69) doesn't bind.
- **Alternate:** every Operator baseline condition that flips a finding fails at once: some interactive policy leaves the allowlist blank, `/usr/local/bin` is user-owned, and the wrapper is deployed. Then S3 is High, S4 Medium, and S8 Medium: 100 − (73 + 18) = 9, **floored at 25 → 25/100 (🟠 Poor)**.
- **Operator baseline:**
  - Every interactive policy sets an allowlist that excludes EDR removal (S3 → High if not).
  - `/usr/local/bin` is root-owned on every Mac in scope (S4 → Medium if not).
  - Every policy runs the main script, not the wrapper (S8 → Medium if not).

---

**Deployment context variant.** Suppose instead a console-user zsh tool that builds support bundles. Its documentation describes an optional shared staging folder that only the support team may write. Seven non-security issues pass the inclusion test; one of them (N7, retention ordering by modification times that sync clients rewrite) occurs only in shared staging. The operator supplies this context: one admin Mac, no other local accounts, a local staging folder only, shared staging out of scope.

| Finding | Documented baseline | With the operator's context | Alternate |
|---|---|---|---|
| The staging folder takes the default umask, so other local accounts can read bundles (Code + Deployment) | 🟡 Medium | 🔵 Low: Q3, the path runs but no other local account exists (mitigated) | 🟡 Medium |
| The shared-staging config file chooses the upload destination (Code + Deployment) | 🔵 Low: Q3, the documentation limits writes to the team | ⚪ Info: Q3, shared staging is out of scope (mitigated) | 🟡 Medium |
| Bundle redaction misses quoted-JSON secrets (Code) | 🔵 Low | 🔵 Low (independent) | 🔵 Low |
| N7 | 2 | Not scored, `context` | 2 |
| N1–N6 | 12 | 12 | 12 |
| **Score** | 100 − 28 = **72/100 (🔵 Good)**; Overall risk 🟡 Medium | 100 − 18 = **82/100 (🔵 Good)**; Overall risk 🔵 Low | 100 − 33 = **67/100 (🟡 Fair)** |

- **Headline:** 82/100 (🔵 Good), at the operator-stated deployment context. The Low range (70–100) doesn't bind.
- **Alternate:** every Operator baseline condition fails at once (another local account exists, and shared staging is writable beyond the team): 67/100 (🟡 Fair), inside the Medium range (50–89). The documented baseline (72) isn't shown as a third score; the Deployment context lines say what the context changed.
- **Operator baseline:**
  - No other local accounts on the Mac (operator-stated) (umask finding → Medium if not).
  - Staging stays local; shared staging is out of scope (operator-stated) (config finding → Medium, N7 scored, if not).
- **The redaction gap is independent of deployment model.** No context item negates its precondition, so it keeps its rating in all three columns.
- **Context can also raise.** Had the operator said the tool ships in the enrollment prestage to every Mac, Adjustment 1 would raise each finding one level, and the headline would fall below the documented baseline.
