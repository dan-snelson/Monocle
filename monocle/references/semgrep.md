# Automated Scan (Semgrep)

## Purpose

Rulesets, skip accounting, and triage for the semgrep run in SKILL.md Step 4. Load this file when `command -v semgrep` succeeds, before running the scan; the command is under **Run**. The scan supplements the manual Step 4 checks; it never replaces them.

---

### Run

Run it once on the local copy (the clone, or fetched files saved to the scratch directory) before the manual checks:

```bash
semgrep scan --metrics=off --disable-version-check \
  --config p/r2c-security-audit --config p/secrets --config p/ci \
  --verbose --json --output "$scratch/semgrep.json" "$target" 2>"$scratch/semgrep.err"
jq -r '.results[] | "\(.extra.severity)\t\(.check_id)\t\(.path):\(.start.line)"' "$scratch/semgrep.json"
jq -r '.errors[] | "\(.path // "-")\t\(.message[0:120])"' "$scratch/semgrep.json"
jq -r '.paths.skipped[]? | "\(.reason)\t\(.path)"' "$scratch/semgrep.json"
```

### Rulesets, skips, and triage

- **Rulesets.** Add a language pack when the target uses that language, for example `p/python`, `p/javascript`, `p/swift`, or `p/dockerfile`. For a bundle (SKILL.md Step 1 E), run `p/secrets` over the extracted data too. `p/bash` doesn't exist and returns an HTTP 404 that fails the whole run. Always pass `--config` explicitly so a config file shipped in the target repo is never used.
- **Registry rules need network access.** If the download fails, note that in the Scope table's **Automated scan** row and carry on with the manual checks.
- **Check what the scan skipped.** In a git repo, Semgrep scans tracked files plus untracked files that `.gitignore` doesn't exclude. It also skips files over 1 MB and honors a `.semgrepignore` in the target. When the target ships no `.semgrepignore`, Semgrep applies its built-in default ignore list, which includes `tests/`. Those skips also show up as `semgrepignore_patterns_match`; report them as, for example, "9 under `tests/` by semgrep's default ignore list". List any exclusions and parse errors (`.errors[]`) under Scope caveats.
  - `--verbose` populates `.paths.skipped` with each size skip (`exceeded_size_limit`) and `.semgrepignore` match (`semgrepignore_patterns_match`); without it the array is empty. As a cross-check, the `semgrep.err` summary reports "Files larger than 1.0 MB: N", and `find "$target" -path '*/.git' -prune -o -type f -size +1000k -print` names them. When a skipped file matters (a large script or log), rescan it alone with `--max-target-bytes 0` and report that run separately.
  - Gitignored files don't appear in `.paths.skipped`, even with `--verbose`. Take them from `git status --short --ignored` (SKILL.md Step 1 D).
  - Parse errors from `p/ci` on the embedded bash in GitHub Actions `run:` blocks are common and are the scanner's limitation, not a defect in the target. Count them and move on.
- **Run it in the background.** A full-repo scan takes minutes. Start it before mapping the structure, and triage its results when it finishes.
- **Triage every result.** Confirm each one in the code before it becomes a finding. Cite confirmed results in the Security view with the rule ID, for example `(semgrep: bash.curl.security.curl-pipe-bash)`. Drop false positives silently, but count them in the Scope table's **Automated scan** row.
  - Common Python false positives: `use-defused-xml` fires on `from xml.sax.saxutils import escape`, which only escapes and parses nothing. `dynamic-urllib-use-detected` fires when the URL comes from the user's own config file. Check the actual sink before dropping either one.
