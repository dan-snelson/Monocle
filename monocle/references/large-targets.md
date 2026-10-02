# Large Targets

## Purpose

How to cover a target that is over the SKILL.md Step 2 limits, or a single file too large to read top to bottom. Load this file when Step 2 says the target is oversized. Never skip an oversized file, and never imply full coverage.

---

### Oversized single files

One script can blow the limit on its own (for example, a 9,000-line zsh file). Don't read it top to bottom, and don't skip it. Instead:

1. Count lines with `wc -l`, then map the structure with a pattern for the detected language:
   - Shell: `grep -nE '^(function )?[A-Za-z_][A-Za-z0-9_]*\s*\(\)\s*\{|^####' file`
   - Python: `grep -nE '^(class|def|async def) [A-Za-z_][A-Za-z0-9_]*|^if __name__ == .__main__.' file`
   - Swift: `grep -nE '^\s*(class|struct|enum|actor|protocol|extension|func|init)\b|@main|UIApplicationMain' file`
   - AppleScript: `grep -nE '^on [A-Za-z_][A-Za-z0-9_]*|^script |^property ' file`
   - Markdown or mixed instruction files: `grep -nE '^#{1,6} ' file`
   If the pattern returns nothing, use a parser or language-aware search before choosing regions.
2. Read these regions in full, in this order:
   1. Globals and parameter parsing.
   2. Pre-flight checks and early exits.
   3. The main program, usually at the bottom.
   4. Helpers that write files, change ownership, run as another user, install persistence, or call the network.
   5. Quit and cleanup.
3. Pattern-scan the rest for the SKILL.md Step 2 item 6 commands, plus `eval`, `rm -rf`, `mktemp`, `/tmp/`, `/var/tmp/`, `chown`, `chmod`, and `> "`. Read the surrounding function wherever a scan hits.
4. In **Scope caveats**, list the exact line ranges you read, estimate the direct-read coverage percentage, and name the functions you only scanned. Keep a running list of the ranges while you read, then compute coverage by summing them. Don't estimate it afterwards. Merge adjacent or overlapping ranges before summing (for example, 5918–6283 and 6284–6999 become 5918–6999), because reads split across tool calls double-count easily.

For long runs like this, post a one-line progress note between phases (fetch, read, analysis, writing), and at least every 5 or so tool calls within a phase. A 10,000-line review takes dozens of calls, and long silent stretches make users think the work has stalled. The manual reading in SKILL.md Step 4 is where silence builds up most, so keep up the notes there too.
