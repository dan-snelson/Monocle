# Prior Reports

## Purpose

How to use an earlier Monocle report on the same target, for SKILL.md Step 5. Load this file when the reports directory (or `$HOME/monocle-reports`) already holds a report on the target. A prior report is a checklist and draft aid, never current evidence.

---

- If a prior report has the same target and ref/SHA, treat it as a checklist and draft aid only. Do not treat it as current evidence until you have re-run the input classification, git status, ignored/local-file check, automated scan or its documented failure path, and citation verification against the current checkout.
- If the target ref/SHA or working tree status differs, treat the prior report as historical context only. Rebuild the fact sheet from the current target.
- If the new report would differ only by timestamp, tell the user that the previous report already covers the same clean ref and give its path instead of creating a duplicate, unless they explicitly asked for a fresh timestamped rerun. If they did ask for a rerun, state in the header that it is a rerun of the same ref and summarize what was revalidated.
- Never copy a previous report into a new file without a fresh citation pass. A copied report with only the Date changed is stale evidence.
- When a prior report covers a different ref of the same target, give the score change in the new report's **Monocle Score** header line, for example "up from 48 at `abc1234`". Recompute the prior score with the current weights if the prior report predates the Monocle Score or used different weights, and say so.
- When a prior report covers an earlier ref, add a **Score change** line under the score's Total. It lists which prior findings are closed, which persist, and which findings are new. For each new finding, check the prior ref (`git show <prior-sha>:<file> | grep -nF 'snippet'`). If the code was already there, say the prior report missed it; don't credit or blame the new release for it.
- When a target's CHANGELOG claims fixes from an earlier review (for example, "based on a Monocle review"), verify each claimed fix against the code (SKILL.md Step 4, Secrets: "Verify the target's own security claims"), and credit the verified ones in the Low/Info roll-up.
