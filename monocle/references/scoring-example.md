# 📈 Monocle Score Worked Example

## Purpose

A fully worked Monocle Score calculation for SKILL.md Step 5. It shows the issue ledger (`scoring-procedure.md`) turned into a score, a Severity basis for each finding (`security.md`, Decision procedure), reason codes for what isn't scored, a headline with a single alternate, and a band floor. Load it when a score depends on deployment (headline vs alternate), when a band clamp applies, or when an admin-gated capability needs rating under Rule 14.

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
