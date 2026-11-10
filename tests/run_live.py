#!/usr/bin/env python3
"""Run Monocle on the calibration fixtures with a real agent, then grade every report.

Opt-in: this uses model quota, so it refuses to run unless MONOCLE_LIVE=1.

Each run gets a fresh workspace from mktemp that holds only a copy of the fixture's
target/ directory. The agent never sees expected.json or the fixture's name: the test
is a fresh reader too. The skill comes from this checkout, so the report's attestation
records this checkout's commit and whether monocle/ has local edits.

Personal state stays out: Claude Code loads only the workspace's project settings (no
user CLAUDE.md, hooks, plugins, or MCP servers), and the run refuses to start while
$HOME/monocle-reports holds a report or saved context for the target name every fixture
uses, since the skill reads that folder too. A run that exits non-zero, times out, or
ends with an error result is FAIL, even when the report it left behind grades PASS.

Reports are copied to the gitignored reports/fixtures/ directory, graded with
tests/grade_report.py, compared across repeats, and summarized as a row to paste into
the run record in TESTING.md.

Usage:
    MONOCLE_LIVE=1 run_live.py [--agent claude|codex] [--fixture NAME ...] [--repeat N]
                               [--timeout SECONDS] [--model MODEL] [--max-budget-usd N] [--keep]
"""

import argparse
import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "monocle"
FIXTURES = ROOT / "tests" / "fixtures"
SAVED = ROOT / "reports" / "fixtures"
# Where each agent looks for personal skills, and where a project-scoped skill goes in the workspace.
SKILL_HOMES = {"claude": Path.home() / ".claude" / "skills", "codex": Path.home() / ".agents" / "skills"}
PROJECT_SKILLS = {"claude": Path(".claude") / "skills", "codex": Path(".agents") / "skills"}
# Claude Code tools Monocle needs; dontAsk denies everything else without prompting.
CLAUDE_TOOLS = "Bash,Read,Write,Edit,Glob,Grep"
# Every fixture is reviewed as ./target, so the skill's {target} name is the same for all of them.
TARGET_NAME = "target"
# Older Monocle versions saved here, and SKILL.md Step 5 still checks it for prior reports and contexts.
LEGACY_REPORTS = Path.home() / "monocle-reports"


def load_grader():
    spec = importlib.util.spec_from_file_location("grade_report", ROOT / "tests" / "grade_report.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules["grade_report"] = module
    spec.loader.exec_module(module)
    return module


def git(*args):
    proc = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def agent_version(agent):
    try:
        proc = subprocess.run([agent, "--version"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    return (proc.stdout or proc.stderr).strip().splitlines()[0] if (proc.stdout or proc.stderr).strip() else "unknown"


def skill_source(agent):
    """Return the workspace-relative skills directory to link the skill into, or None when no link is needed.

    Claude Code runs load only project settings, so the skill is always linked into the workspace.
    Codex reads the personal install, so it is linked only when there is none.
    """
    personal = SKILL_HOMES[agent] / "monocle"
    if personal.exists() or personal.is_symlink():
        if personal.resolve() != SKILL_DIR.resolve():
            raise SystemExit(f"run_live.py: {personal} is a different Monocle ({personal.resolve()}), and it would "
                             f"answer instead of this checkout. Move it aside, or replace it with a symlink to {SKILL_DIR}.")
        if agent != "claude":
            return None
    return PROJECT_SKILLS[agent]


def personal_state():
    """Return files in the legacy reports folder that the skill would read on a fixture run."""
    found = sorted(LEGACY_REPORTS.glob(f"monocle-{TARGET_NAME}-*.md"))
    context = LEGACY_REPORTS / "contexts" / f"{TARGET_NAME}.md"
    return found + ([context] if context.exists() else [])


def claude_result_problem(stdout):
    """Return why a Claude Code JSON result shows an unfinished run, or None when it finished."""
    try:
        result = json.loads(stdout)
    except ValueError:
        return "agent output isn't a JSON result"
    if isinstance(result, list):  # some versions print every message; the result is the last one
        result = next((item for item in reversed(result) if isinstance(item, dict) and item.get("type") == "result"),
                      None)
    if not isinstance(result, dict):
        return "agent output has no JSON result"
    if result.get("is_error") or result.get("subtype", "success") != "success":
        return f"agent result: {result.get('subtype') or 'no subtype'}, is_error {bool(result.get('is_error'))}"
    return None


def add_note(outcome, text):
    outcome["note"] = f"{outcome['note']}; {text}" if outcome["note"] else text


def build_prompt(agent, expected):
    prompt = ("/monocle" if agent == "claude" else "$monocle") + f" ./{TARGET_NAME}"
    if expected.get("deployment_context"):
        prompt += "\n\nDeployment context:\n" + expected["deployment_context"]
    return prompt + (expected.get("prompt_suffix") or "")


def run_one(agent, link, case_dir, expected, number, args, grader, stamp):
    workspace = Path(tempfile.mkdtemp(prefix="monocle-live-"))
    shutil.copytree(case_dir / "target", workspace / TARGET_NAME)
    reports = workspace / "reports"
    reports.mkdir()
    if link:
        (workspace / link).mkdir(parents=True)
        (workspace / link / "monocle").symlink_to(SKILL_DIR)

    prompt = build_prompt(agent, expected)
    if agent == "claude":
        # Project settings only: no user CLAUDE.md, hooks, plugins, or skills, and no MCP servers.
        command = ["claude", "-p", prompt, "--permission-mode", "dontAsk", "--allowedTools", CLAUDE_TOOLS,
                   "--setting-sources", "project", "--strict-mcp-config",
                   "--no-session-persistence", "--output-format", "json"]
        if args.max_budget_usd:
            command += ["--max-budget-usd", str(args.max_budget_usd)]
    else:
        command = ["codex", "exec", "-C", str(workspace), "-s", "workspace-write", "--skip-git-repo-check",
                   "--ephemeral", "-o", str(workspace / "last-message.txt"), prompt]
    if args.model:
        command += ["--model", args.model] if agent == "claude" else ["-m", args.model]

    env = dict(os.environ, MONOCLE_REPORTS_DIR=str(reports))
    outcome = {"case": case_dir.name, "run": number, "workspace": str(workspace), "report": None,
               "verdict": "FAIL", "final": None, "note": ""}
    completed = False
    try:
        proc = subprocess.run(command, cwd=workspace, env=env, capture_output=True, text=True, timeout=args.timeout)
        (workspace / "agent-stdout.txt").write_text(proc.stdout, encoding="utf-8")
        (workspace / "agent-stderr.txt").write_text(proc.stderr, encoding="utf-8")
        problem = (f"agent exited {proc.returncode}" if proc.returncode
                   else claude_result_problem(proc.stdout) if agent == "claude" else None)
        completed = problem is None
        if problem:
            add_note(outcome, problem)
    except subprocess.TimeoutExpired:
        add_note(outcome, f"timed out after {args.timeout}s")

    written = sorted(reports.glob("monocle-*.md"), key=lambda path: path.stat().st_mtime)
    if not written:
        add_note(outcome, "no report written")
        return outcome
    SAVED.mkdir(parents=True, exist_ok=True)
    saved = SAVED / f"{agent}-{case_dir.name}-{stamp}-{number}.md"
    shutil.copyfile(written[-1], saved)
    outcome["report"] = str(saved)
    result = grader.grade(saved.read_text(encoding="utf-8"), expected)
    outcome.update(verdict=result["verdict"], final=result["final"])
    print(grader.render_grade(result, saved, case_dir / "expected.json"))
    if not completed:
        # TESTING.md: an unfinished run is not a pass, whatever the report it left behind grades.
        outcome["verdict"] = "FAIL"
        add_note(outcome, f"report graded {result['verdict']}, but the run didn't finish")
        print(f"Verdict for this run: FAIL ({outcome['note']})")
    print()
    return outcome


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--agent", choices=("claude", "codex"), default="claude")
    parser.add_argument("--fixture", action="append", help="fixture name (repeatable; default: every fixture)")
    parser.add_argument("--repeat", type=int, default=1, help="runs per fixture, to measure rerun agreement")
    parser.add_argument("--timeout", type=int, default=1800, help="seconds per run")
    parser.add_argument("--model", help="model to pass to the agent")
    parser.add_argument("--max-budget-usd", type=float, help="Claude Code spending cap per run")
    parser.add_argument("--keep", action="store_true", help="keep every workspace, not only failed ones")
    args = parser.parse_args(argv)

    if os.environ.get("MONOCLE_LIVE") != "1":
        parser.error("live runs use model quota; set MONOCLE_LIVE=1 to run them")
    if shutil.which(args.agent) is None:
        parser.error(f"{args.agent} isn't on PATH")
    if subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", "reports/fixtures/probe.md"]).returncode != 0:
        parser.error("reports/ isn't gitignored in this checkout; refusing to save reports there")
    cases = sorted(path for path in FIXTURES.iterdir() if (path / "expected.json").is_file())
    if args.fixture:
        unknown = set(args.fixture) - {path.name for path in cases}
        if unknown:
            parser.error(f"unknown fixture(s): {', '.join(sorted(unknown))}")
        cases = [path for path in cases if path.name in args.fixture]

    grader = load_grader()
    problems = [problem for case_dir in cases for problem in grader.validate_fixture(case_dir)]
    if problems:
        parser.error("fix the fixtures first:\n" + "\n".join(problems))
    link = skill_source(args.agent)
    leaks = personal_state()
    if leaks:
        parser.error(f"{LEGACY_REPORTS} holds files the skill would read for ./{TARGET_NAME}, so the runs wouldn't be "
                     "independent. Move them aside first:\n" + "\n".join(str(path) for path in leaks))

    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
    version = agent_version(args.agent)
    commit = git("rev-parse", "--short", "HEAD") or "unknown"
    dirty = " (dirty)" if git("status", "--porcelain", "--", "monocle") else ""
    rows, all_passed = [], True
    for case_dir in cases:
        expected = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
        outcomes = [run_one(args.agent, link, case_dir, expected, n, args, grader, stamp)
                    for n in range(1, args.repeat + 1)]
        all_passed = all_passed and all(o["verdict"] == "PASS" and o["report"] for o in outcomes)
        agreement = "n/a"
        saved = [outcome["report"] for outcome in outcomes if outcome["report"]]
        if len(saved) > 1:
            first = Path(saved[0]).read_text(encoding="utf-8")
            diffs = [grader.compare(first, Path(other).read_text(encoding="utf-8")) for other in saved[1:]]
            agreement = "identical" if all(d["identical"] for d in diffs) else "differs"
            for other, diff in zip(saved[1:], diffs):
                if not diff["identical"]:
                    print(f"Rerun differences, run 1 vs {Path(other).name}:")
                    print("\n".join(f"- {line}" for line in diff["differences"]))
        for outcome in outcomes:
            failed = outcome["verdict"] != "PASS" or not outcome["report"]
            if args.keep or failed:
                print(f"Workspace kept: {outcome['workspace']}")
            else:
                shutil.rmtree(outcome["workspace"], ignore_errors=True)
        scores = ", ".join(str(o["final"]) if o["final"] is not None else "none" for o in outcomes)
        verdicts = ", ".join(o["verdict"] for o in outcomes)
        notes = "; ".join(o["note"] for o in outcomes if o["note"]) or (f"reruns {agreement}" if args.repeat > 1 else "")
        rows.append(f"| {datetime.date.today().isoformat()} | {args.agent} {version} | {args.model or 'default'} | "
                    f"`{commit}`{dirty} | {case_dir.name} | {args.repeat} | {scores} | {verdicts} | {notes} |")

    print("Run record rows for TESTING.md:")
    print("\n".join(rows))
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
