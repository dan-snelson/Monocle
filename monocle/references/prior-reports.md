# Prior Reports

## Purpose

How to use an earlier Monocle report on the same target, for SKILL.md Step 5. Load this file when the reports directory (or `$HOME/monocle-reports`) already holds a report on the target. A prior report is a checklist of items that each need a disposition, never current evidence.

---

- **Same target and ref:** before rating anything, give every prior `S#`, `N#`, and Not scored item exactly one disposition in the issue ledger (`scoring-procedure.md`):
  - **Confirmed:** same rating.
  - **Re-rated:** name the Decision procedure step (`security.md`) that differs.
  - **Closed:** the code changed; cite the change.
  - **Rejected:** the prior report was wrong; cite the evidence.

  Never drop a prior item silently. Prior items are checks to run, not ratings to copy: re-derive each one with the current procedure. Don't treat the prior report as current evidence until you have re-run the input classification, git status, ignored/local-file check, automated scan or its documented failure path, and citation verification against the current checkout.
- **Match prior items by issue key** (`scoring-procedure.md`, Issue ledger). For reports written before keys existed, match by file, function, and defect class.
- **Same ref and same skill commit, different score:** the **Score change** line lists every Re-rated and Rejected disposition, and every new issue, as a counting correction.
- If the target ref/SHA or working tree status differs, treat the prior report as historical context only. Rebuild the fact sheet from the current target.
- If the new report would differ only by timestamp, tell the user that the previous report already covers the same clean ref and give its path instead of creating a duplicate, unless they explicitly asked for a fresh timestamped rerun. If they did ask for a rerun, state in the Scope section that it is a rerun of the same ref and summarize what was revalidated.
- Never copy a previous report into a new file without a fresh citation pass. A copied report with only the Date changed is stale evidence.
- When a prior report covers a different ref of the same target, give the score change in the new report's **Score:** line in the Monocle Score section, for example "up from 48 at `abc1234`". Recompute the prior score with the current weights if the prior report predates the Monocle Score or used different weights, and say so.
- When a prior report covers an earlier ref, add a **Score change** line under the score's Total. It lists which prior findings are closed, which persist, and which findings are new. For each new finding, check the prior ref (`git show <prior-sha>:<file> | grep -nF 'snippet'`). If the code was already there, say the prior report missed it; don't credit or blame the new release for it.
- If the prior report listed an issue in a view but left it out of the score (for example, an Engineer edge case), apply the inclusion test (`scoring-procedure.md`) now: count it, or give its reason code. Call either result a counting correction in the **Score change** line, so the change isn't credited to or blamed on the code.
- When a target's CHANGELOG claims fixes from an earlier review (for example, "based on a Monocle review"), verify each claimed fix against the code (SKILL.md Step 4, Secrets: "Verify the target's own security claims"), and credit the verified ones in the Low/Info roll-up.
