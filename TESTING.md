# Testing Monocle

Monocle is a set of instructions that rewrites itself, through `post-chat-refine` and `binge-and-purge`. Two kinds of checks protect it:

- **Offline checks** run in CI on every push and pull request. They cost nothing and need no model.
- **Live fixture runs** run Monocle with a real agent against synthetic targets, and grade the reports. They use model quota, so they run only on request.

The README promises that re-runs of the same code give the same score. The live runs are how that promise gets tested.

---

## Offline checks

Run these before opening a pull request. They need only `python3` (3.9 or newer, standard library only).

```bash
python3 monocle/scripts/verify_report.py --self-test
python3 .github/scripts/check_skill_structure.py
python3 tests/grade_report.py --self-test
git diff --check
```

- `verify_report.py --self-test` covers the report checker: verdict cases, issue keys, output escaping, and scoring text kept in sync across `SKILL.md`, `README.md`, and `security.md`.
- `check_skill_structure.py` covers the skill's shape:
  - the `SKILL.md` byte budget and frontmatter limits;
  - every reference file named and present, and the README Layout tree;
  - the house format of reference files;
  - the safety sentinels;
  - relative links and anchors.
- `grade_report.py --self-test` validates every fixture's `expected.json`, rejects targets that hint they are tests, and checks the grader on synthetic reports.

---

## Live fixture runs

```bash
MONOCLE_LIVE=1 python3 tests/run_live.py --agent claude --fixture shared-tmp-chown --repeat 2
MONOCLE_LIVE=1 python3 tests/run_live.py --agent claude --repeat 2        # every fixture
```

What a run does:

1. It creates a fresh `mktemp` workspace holding only a copy of the fixture's `target/`. The agent never sees `expected.json`.
2. It loads the skill from this checkout. A personal install that points somewhere else stops the run, so the right Monocle is under test.
3. It runs the agent headless, with `MONOCLE_REPORTS_DIR` inside the workspace.
4. It saves the report to the gitignored `reports/fixtures/`, grades it, and compares reports across repeats.
5. It prints rows for the run record below.

Options: `--agent claude|codex`, `--fixture NAME` (repeatable), `--repeat N`, `--timeout SECONDS`, `--model MODEL`, and `--max-budget-usd N` (Claude Code only). A run keeps its workspace when it fails, and always with `--keep`.

Grade or compare saved reports by hand:

```bash
python3 tests/grade_report.py grade reports/fixtures/claude-shared-tmp-chown-20261110-0900-1.md tests/fixtures/shared-tmp-chown/expected.json
python3 tests/grade_report.py compare reports/fixtures/claude-shared-tmp-chown-20261110-0900-1.md reports/fixtures/claude-shared-tmp-chown-20261110-0900-2.md
```

**Verdicts:**

- **PASS:** every expected row matched at its severity, nothing was flagged that must not be, and the score, band, and Overall risk are in range.
- **DRIFT:** a severity is one level off, or there is an extra finding no expectation covers. Read the report: either the run drifted, or the fixture needs a new expectation.
- **FAIL:** a missed row, a severity two or more levels off, a false positive, an out-of-range score, or a report that fails `verify_report.py`'s structure or arithmetic checks.

`compare` reports rows found in only one run, severity and alternate changes, and score changes. Identical ledgers across repeats are the evidence for the README's consistency promise.

### When a rule change moves a rating

Update the case's `expected.json` in the same change, and rewrite its `rationale` to cite the new rule. Never edit an expectation only to make a run pass. If a run disagrees with a fixture, find out which one is wrong.

### Codex

`--agent codex` links the skill into the workspace's `.agents/skills/` and runs `codex exec` in a `workspace-write` sandbox. This path has not been verified end to end yet. Record the first run's result here, including a failure.

---

## Run record

Add a row for every live run, including failed and unfinished ones. An unfinished run is not a pass. Raw reports stay in `reports/fixtures/` and are never committed.

| Date | Agent and version | Model | Skill commit | Fixture | Runs | Scores | Verdicts | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
