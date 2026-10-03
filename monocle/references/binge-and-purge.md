# Binge and Purge

## Contents
- Purpose
- Budget
- Phase 1: Analyze and propose (no edits)
- Phase 2: Implement (after approval)
- Phase 3: Verify
- Guardrails

## Purpose

A maintenance pass that keeps `monocle/SKILL.md` lean. `post-chat-refine.md` "binges": each run folds new lessons into the skill, and SKILL.md grows. This file "purges": it moves conditional content out of SKILL.md into `references/`, without changing meaning, until the file fits comfortably in a single Read.

Load this file only when:

- the user asks to slim, restructure, or purge SKILL.md; or
- a post-chat-refine run leaves SKILL.md over about 59,000 bytes (less than 3,000 tokens of headroom). In that case offer this pass in one line; don't run it unasked.

This pass edits the skill, not a target. No Monocle report is written, and the Step 1–5 workflow does not run.

---

## Budget

- SKILL.md loads on every run and must fit in one Read call. The Read cap is 25,000 tokens; past it, Read returns a truncated "PARTIAL view" and the agent works from an incomplete skill.
- Estimate about 2.7 bytes per token for this file (`wc -c monocle/SKILL.md`). Aim for at least 3,000 tokens under the cap, so about 59,000 bytes at most.
- The estimate is a guide. The real test is a full Read (no offset or limit) that comes back without the truncation notice.
- **Measure before proposing.** If the file already meets the headroom goal, say so with the numbers, then offer only the moves that are clearly worth it. Don't manufacture a restructure.

## Phase 1: Analyze and propose (no edits)

1. Read `README.md`, all of `monocle/SKILL.md`, and every file in `monocle/references/`.
2. Measure each section:

   ```bash
   awk '/^##+ /{if(h)printf "%6d  %4d-%-4d %s\n",b,s,NR-1,h; h=$0; s=NR; b=0} {b+=length($0)+1} END{printf "%6d  %4d-%-4d %s\n",b,s,NR,h}' monocle/SKILL.md | sort -rn
   ```

   Measure candidate blocks at line level too (`sed -n "${n}p" monocle/SKILL.md | wc -c`). Sections hide conditional bullets.
3. Classify every section and every large bullet:
   - **Move it** when only some runs need it (a particular input type, tool, language, target shape, or prior state) **and** SKILL.md can name a clear trigger for loading it ("when the input is a GitHub URL", "when `command -v semgrep` succeeds", "when a credential arrives through `$4`–`$11`").
   - **Trim it** when it repeats something a reference file already says. Replace it with a one-line pointer, or delete it when an existing pointer already covers it.
   - **Keep it** when every run needs it: the step skeleton and input classification, the fact sheet, the core high-risk checks most targets hit, the Monocle Score rules, the output template, citation verification, the report path, the Rules, and Failure modes.
4. Choose destinations:
   - Prefer merging into an existing reference file, or a new section of one, over creating a file. Create a file only when nothing existing fits the trigger.
   - Analysis-time checks go to a step or trigger reference (for example `specialized-checks.md`), never to a view reference. View files load only while that view is written, after the analysis is done.
   - A trimmed duplicate can hold a detail found nowhere else (a severity rule, a flag variant, a "label it inferred" caveat). Plan to merge that detail into the destination.
5. Present a table ranked by tokens saved: block, line range, approximate tokens saved, trigger, destination. Add the stub each move leaves behind, the pointer updates, and a short "Not moved, and why" list.
6. Give the SKILL.md size before and after, in bytes and estimated tokens, then **stop and wait for approval**. In plan mode, write the plan and exit plan mode for approval.

## Phase 2: Implement (after approval)

1. Back up first: copy `monocle/SKILL.md` to the scratch directory as `SKILL.before.md`, and copy `references/` and `README.md` too, so every touched file can be diffed.
2. **Move the text verbatim.** Change only cross-references that break in the new location: inside a reference file, "Step 2" becomes "SKILL.md Step 2", "Rule 5" becomes "SKILL.md Rule 5", `references/security.md` becomes `security.md`, and a pointer to the destination itself becomes "below" or "above".
3. **House format** for every reference file: `# Title`, `## Contents` (only for files over 100 lines: a plain bullet list of every `##` and `###` section, Purpose first), `## Purpose` (what it covers and exactly when to load it), `---`, then the sections. When a file gains sections, update its Purpose trigger list and, if it has one, its Contents list. Add a Contents list when a file grows past 100 lines. Begin a moved section with one line naming what it extends ("Extends SKILL.md Step 4, Secrets.").
4. **Leave a stub of one to three lines.** It names the trigger and the destination, and keeps inline any rule that must never be missed even if the reference is skipped. Examples: "never paste URL text into a command", "never run anything inside the bundle", "zero scan findings never means clean", "rate it with Credential severity, High only while a policy populates the parameter".
5. **Place stubs where they read naturally.** Never put a stub between an intro line such as "Check for each of these:" and its list. Put it at the end of the section instead.
6. **Merge stubs** when several pointers target the same reference file: add the triggers to that file's single triggered list in SKILL.md (for example Step 4 **Specialized checks**), in the same order as the reference's sections.
7. **Keep cited headings stable.** When another file cites a SKILL.md heading by name, keep that heading even if part of its content moves.
8. **Update every pointer:**
   - the reference list near the top of SKILL.md: every on-trigger file, in step order, with no hardcoded count and no hardcoded list of section names that will drift;
   - the `## Layout` tree in `README.md`;
   - any SKILL.md or reference text that cites a moved section by name.
9. **Apply everything with one script** that validates before it writes:
   - Pull moved text from SKILL.md itself, so it is verbatim by construction.
   - Check each anchor line by expected prefix **and** byte length, and each substitution by an exact match count of 1.
   - Collect every mismatch and abort with nothing written if any exist.
   - Apply SKILL.md replacements from the bottom of the file up, so line numbers stay valid.

   ```python
   ANCHORS = [(163, "Semgrep does static analysis only", 295), ...]  # (line, prefix, bytes incl. newline)
   for n, prefix, size in ANCHORS:
       line = skill[n - 1]
       if not line.startswith(prefix) or len(line.encode()) != size:
           errors.append(f"SKILL.md:{n} anchor mismatch")
   def sub(text, old, new, where):
       if text.count(old) != 1:
           errors.append(f"{where}: {text.count(old)} matches")
           return text
       return text.replace(old, new)
   # ... build moved blocks and replacements ...
   if errors: print("\n".join(errors)); sys.exit(1)
   for a, b, repl in sorted(EDITS, reverse=True):
       skill[a - 1:b] = repl
   ```

## Phase 3: Verify

1. Do a full Read of `monocle/SKILL.md` with no offset or limit, and confirm there is no truncation notice. While reading, check that each stub reads naturally in place.
2. Confirm nothing was lost:

   ```bash
   cat monocle/references/*.md monocle/SKILL.md > "$scratch/all.txt"
   diff "$scratch/SKILL.before.md" monocle/SKILL.md | grep '^< ' | sed 's/^< //' |
   while IFS= read -r line; do
     [[ -z "${line// }" ]] && continue
     grep -qxF -- "$line" "$scratch/all.txt" || printf 'CHANGED: %s\n' "${line:0:110}"
   done
   ```

   Each CHANGED line must be an intended stub, trim, or cross-reference rewrite. Explain every one.
3. Confirm the pointer set matches the files on disk, and check the README layout block against the same list:

   ```bash
   grep -ohE 'references/[a-z-]+\.md' monocle/SKILL.md | sort -u
   ls monocle/references
   sed -n '/^## Layout/,/^## Install/p' README.md | grep -oE '[a-z-]+\.md' | sort
   ```

4. Grep SKILL.md and `references/` for the name of each moved section and bullet, and fix any reference that points to text no longer in SKILL.md.
5. Grep the moved sections for bare `Rule N` or `Step N` that should now read `SKILL.md Rule N` or `SKILL.md Step N`.
6. Review `diff -u` of each touched reference file against its backup.

## Guardrails

- **Restructure, don't rewrite.** Meaning stays the same. Don't add advice; that is post-chat-refine's job, under its own criteria.
- **Keep it generic.** Moved text is existing skill content. Don't introduce any target, organization, or person name while writing stubs or Purpose lines.
- **Don't commit.** List new untracked files so the user can `git add` them. Note any unrelated uncommitted changes that `git diff --stat` shows, so they aren't mistaken for this pass.
- **Report back with:**
  - before and after byte counts and estimated tokens;
  - the files created or changed;
  - every CHANGED line and why it changed;
  - what you chose not to move, and why.
