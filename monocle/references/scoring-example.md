# Monocle Score Worked Example

## Purpose

A fully worked Monocle Score calculation for SKILL.md Step 5. Load it when a score depends on deployment (headline vs alternate), when a band clamp applies, or when an admin-gated capability needs rating under Rule 14.

---

**Worked example.** Suppose a Jamf Self Service tool repairs, resets, or removes an office suite. It offers about 20 actions, including removing the EDR agent, and a Jamf parameter supplies an allowlist of actions. Under these rules:

- **Findings at the baseline.**

  | ID | Finding | Rating | Points |
  |---|---|---|---|
  | S1 | Root installs packages from `/Users/Shared` with a name-only signature check | High (Code defect) | 20 |
  | S2 | EDR removal and full-suite removal are offered when the allowlist parameter is blank | Low: an intended, documented, admin-gated capability with an unsafe default, so a secure-default gap (Rule 14) | 3 |
  | S3 | A tracked self-extracting wrapper | Info, because the documentation deploys the main script | 0 |
  | S4 | — | Medium | 8 |
  | S5 | Root runs `/usr/local/bin/dialog` | Low, assuming a root-owned `/usr/local/bin` | 3 |
  | S6–S8 | — | Low | 9 |
  | S9 | — | Info | 0 |

  Security total: 43.
- **Non-security.** 9 endpoint issues cost 18. Issues in a local release helper and a repo sync script are maintainer tooling: not scored.
- **Headline:** 100 − 61 = **39/100 (Poor)**. The High range (25–69) doesn't bind.
- **Alternate:** suppose any interactive policy leaves the allowlist blank, the wrapper is deployed, and `/usr/local/bin` is user-owned. Then S2 is High, S3 Medium, and S5 Medium: 100 − (73 + 18) = 9, **floored at 25 → 25/100 (Poor)**.
- **Operator baseline:**
  - Every interactive policy sets an allowlist that excludes EDR removal (S2 → High if not).
  - Every policy runs the main script, not the wrapper (S3 → Medium if not).
  - `/usr/local/bin` is root-owned on every Mac in scope (S5 → Medium if not).
