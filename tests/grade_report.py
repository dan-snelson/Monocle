#!/usr/bin/env python3
"""Grade a Monocle report against a calibration fixture, or compare two reports on one target.

Fixtures live in tests/fixtures/<case>/: a small synthetic target in target/, and the
ledger a correct run should produce in expected.json (see tests/fixtures/README.md).
The grader matches the report's Security findings to the expected rows by the issue
keys in the report's Scope caveats (file and defect class), then checks severities,
alternates, Not scored reason codes, the score range, the band, and Overall risk.

The report is untrusted input: it is parsed with monocle/scripts/verify_report.py, and
nothing in it reaches a shell. Everything printed passes through that script's
safe_text(), so report text can't rewrite the output.

Usage:
    grade_report.py grade REPORT EXPECTED [--json]
    grade_report.py compare REPORT_A REPORT_B [--json]
    grade_report.py --self-test

Exit status: 0 for PASS (or identical ledgers), 1 for DRIFT, FAIL, or different ledgers,
2 for errors.
"""

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
VERIFIER = ROOT / "monocle" / "scripts" / "verify_report.py"


def load_verifier():
    spec = importlib.util.spec_from_file_location("verify_report", VERIFIER)
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_report"] = module  # dataclasses look their module up here
    spec.loader.exec_module(module)
    return module


vr = load_verifier()

# The Non-security inclusion test's reason codes, in references/scoring-procedure.md.
REASON_CODES = (
    "maintainer", "documented", "ownership", "docs", "dependency-handled", "config", "malformed-config",
    "unreachable", "immaterial", "capability", "inferred-unverified", "context",
)
RANK = {sev: index for index, sev in enumerate(vr.SEVERITIES)}  # Critical 0 … Info 4
ALTERNATE_RE = re.compile(r"\b(S\d+)\s*→\s*(?:[🔴🟠🟡🔵⚪]\s*)?(Critical|High|Medium|Low|Info)\b")
ALT_SCORE_RE = re.compile(r",\s*or\s+(\d+)/100")
HINT_RE = re.compile(r"fixture|expected\.json|monocle", re.IGNORECASE)

TOP_FIELDS = {"description": str, "deployment_context": (str, type(None)), "prompt_suffix": str,
              "expect": dict, "rationale": str}
EXPECT_FIELDS = {"score_range", "bands", "alternate_score_range", "overall_risk", "no_other_findings",
                 "findings", "not_scored", "refuted", "must_not_flag"}
ROW_FIELDS = {
    "findings": ({"class", "file", "severity", "rationale"}, {"function", "alternate"}),
    "not_scored": ({"reason", "rationale"}, {"class"}),
    "refuted": ({"class", "file", "rationale"}, set()),
    "must_not_flag": ({"class", "file", "rationale"}, {"min_severity"}),
}


class GradeError(Exception):
    """Bad input: an unreadable report or a malformed expectation file."""


def as_list(value):
    return list(value) if isinstance(value, (list, tuple)) else [value]


def same_file(reported, expected):
    return Path(reported).name == Path(expected).name


def split_key(key):
    """Return (file, function or anchor, defect class) for a key, or Nones when it doesn't parse."""
    match = vr.KEY_RE.match(key or "")
    if not match or ":" not in match.group(1):
        return None, None, None
    file_part, where = match.group(1).split(":", 1)
    return file_part.strip(), where.strip(), match.group(2)


# ---------------------------------------------------------------- report facts


def nested_bullets(lines, label):
    start = next((i for i, line in enumerate(lines) if line.startswith(label)), None)
    if start is None:
        return []
    found = []
    for line in lines[start + 1:]:
        if not line.strip() or not line.startswith((" ", "\t")):
            break
        found.append(line.strip()[2:].strip() if line.strip().startswith("- ") else line.strip())
    return found


def facts(report_text):
    """Everything the grader compares, read from one report."""
    report = vr.Report(report_text)
    audit = vr.run_checks(report)
    rules = vr.parse_rules((ROOT / "monocle" / "SKILL.md").read_text(encoding="utf-8"))
    vr.check_score(audit, report, rules)
    keys = audit.issue_keys or {}

    rows = {}
    for row in report.table("Security View", ("id", "severity")) or []:
        sev = vr.word_in(row[1], vr.SEVERITIES) if len(row) > 1 else None
        if sev and re.fullmatch(r"S\d+", row[0].strip()):
            rows[row[0].strip()] = {"id": row[0].strip(), "severity": sev}
    for ident in vr.ledger_ids(report):
        rows.setdefault(ident, {"id": ident, "severity": None})
    for ident, row in rows.items():
        row["key"] = keys.get(ident)
        row["file"], row["where"], row["class"] = split_key(row["key"])

    score_body = report.body("Monocle Score")
    alternates = {}
    for line in score_body:
        for ident, sev in ALTERNATE_RE.findall(line):
            alternates.setdefault(ident, sev)
    risk_line = next((line for line in score_body if line.startswith("**Overall risk:**")), "")
    score_line = next((line for line in score_body if line.startswith("**Score:**")), "")
    alt_score = ALT_SCORE_RE.search(score_line)

    reasons = {}
    for row in report.table("Monocle Score", ("source", "ids", "count", "each", "deduction")) or []:
        if len(row) > 1 and row[0].lower().startswith("not scored"):
            for segment in re.split(r"[,;]", row[1]):
                codes = [code for code in REASON_CODES if re.search(rf"(?<![\w-]){re.escape(code)}(?![\w-])", segment)]
                for ident in vr.expand_ids(segment, "X"):
                    reasons[ident] = codes[0] if codes else None

    refuted = []
    for entry in nested_bullets(report.body("Scope"), "- **Refuted candidates.**"):
        key = re.split(r"\s+—\s+", entry, maxsplit=1)[0].strip("` ")
        file_part, _, cls = split_key(key)
        refuted.append({"key": key, "file": file_part, "class": cls})

    failed = [f"{c.group}: {c.name} — {c.detail}" for c in audit.checks
              if c.status == "fail" and c.group in ("structure", "rules", "arithmetic")]
    return {
        "rows": rows, "alternates": alternates, "reasons": reasons, "refuted": refuted,
        "final": audit.reported_final, "band": audit.reported_band,
        "alternate_score": int(alt_score.group(1)) if alt_score else None,
        "overall_risk": vr.word_in(risk_line, vr.SEVERITIES), "keys_present": audit.issue_keys is not None,
        "report_failures": failed,
    }


# ---------------------------------------------------------------- grading


def distance(severity, wanted):
    if severity not in RANK:
        return None
    return min(abs(RANK[severity] - RANK[sev]) for sev in as_list(wanted))


def grade(report_text, expected):
    report = facts(report_text)
    expect = expected["expect"]
    results = []  # (status, detail); status is one of exact, adjacent, ok, extra, note, miss, off, false-positive, fail

    def add(status, detail):
        results.append((status, detail))

    for failure in report["report_failures"]:
        add("fail", f"report check failed — {failure}")
    if not report["keys_present"] and report["rows"]:
        add("note", "the report has no Issue keys bullet, so findings can't be matched by file and class")

    security = [row for row in report["rows"].values() if row["id"].startswith("S")]
    matched = set()
    for number, want in enumerate(expect.get("findings", []), 1):
        label = f"finding {number} ({'/'.join(as_list(want['class']))} in {want['file']}, {'/'.join(as_list(want['severity']))})"
        candidates = [row for row in security if row["id"] not in matched and row["class"] in as_list(want["class"])
                      and row["file"] and same_file(row["file"], want["file"])
                      and (not want.get("function") or want["function"] in (row["where"] or ""))]
        if not candidates:
            add("miss", f"{label}: no matching row")
            continue
        best = min(candidates, key=lambda row: (distance(row["severity"], want["severity"]) is None,
                                                distance(row["severity"], want["severity"]) or 0))
        matched.add(best["id"])
        gap = distance(best["severity"], want["severity"])
        status = "exact" if gap == 0 else "adjacent" if gap == 1 else "off"
        add(status, f"{label}: {best['id']} is {best['severity']} (`{best['key']}`)")
        if "alternate" in want:
            alt = report["alternates"].get(best["id"])
            alt_gap = distance(alt, want["alternate"]) if alt else None
            if alt is None:
                add("miss", f"{label}: no Operator baseline alternate for {best['id']}; expected {want['alternate']}")
            else:
                add("exact" if alt_gap == 0 else "adjacent" if alt_gap == 1 else "off",
                    f"{label}: {best['id']} alternate is {alt}; expected {want['alternate']}")

    flagged = set()
    for want in expect.get("must_not_flag", []):
        floor = RANK[want.get("min_severity", "Low")]
        for row in security:
            if (row["class"] in as_list(want["class"]) and row["file"] and same_file(row["file"], want["file"])
                    and row["severity"] in RANK and RANK[row["severity"]] <= floor):
                flagged.add(row["id"])
                add("false-positive", f"{row['id']} is {row['severity']} (`{row['key']}`); "
                                      f"{want['class']} in {want['file']} must not be flagged")

    for row in security:
        if row["id"] in matched or row["id"] in flagged:
            continue
        if row["severity"] in RANK and RANK[row["severity"]] <= RANK["Low"]:
            add("fail" if expect.get("no_other_findings") else "extra",
                f"{row['id']} is {row['severity']} (`{row['key']}`) and no expectation covers it")

    for want in expect.get("not_scored", []):
        hits = [ident for ident, reason in report["reasons"].items() if reason == want["reason"]
                and (not want.get("class") or report["rows"].get(ident, {}).get("class") in as_list(want["class"]))]
        add("ok" if hits else "miss", f"Not scored with reason code {want['reason']}: "
                                      f"{', '.join(hits) if hits else 'no matching X# row'}")

    for want in expect.get("refuted", []):
        hit = any(entry["class"] in as_list(want["class"]) and entry["file"] and same_file(entry["file"], want["file"])
                  for entry in report["refuted"])
        add("note", f"refuted candidate {want['class']} in {want['file']}: {'recorded' if hit else 'not recorded'}")

    low, high = expect["score_range"]
    final = report["final"]
    add("ok" if final is not None and low <= final <= high else "fail",
        f"score {final if final is not None else 'missing'}; expected {low}–{high}")
    add("ok" if report["band"] in expect["bands"] else "fail",
        f"band {report['band']}; expected {' or '.join(expect['bands'])}")
    risks = as_list(expect["overall_risk"])
    add("ok" if report["overall_risk"] in risks else "fail",
        f"Overall risk {report['overall_risk']}; expected {' or '.join(risks)}")
    if "alternate_score_range" in expect:
        alt_low, alt_high = expect["alternate_score_range"]
        alt = report["alternate_score"]
        add("ok" if alt is not None and alt_low <= alt <= alt_high else "fail",
            f"alternate score {alt if alt is not None else 'missing'}; expected {alt_low}–{alt_high}")

    statuses = [status for status, _ in results]
    if any(status in ("miss", "off", "false-positive", "fail") for status in statuses):
        verdict = "FAIL"
    elif any(status in ("adjacent", "extra") for status in statuses):
        verdict = "DRIFT"
    else:
        verdict = "PASS"
    counts = {status: statuses.count(status) for status in
              ("exact", "adjacent", "off", "miss", "false-positive", "extra", "fail")}
    return {"verdict": verdict, "final": final, "band": report["band"], "counts": counts,
            "results": [{"status": status, "detail": detail} for status, detail in results]}


def compare(text_a, text_b):
    a, b = facts(text_a), facts(text_b)
    differences = []

    def identity(row):
        return row["key"] or row["id"]

    rows_b = dict(b["rows"])
    for ident, row in a["rows"].items():
        twin = next((other for other in rows_b.values() if row["key"] and other["key"] == row["key"]), None)
        if twin is None:
            twin = next((other for other in rows_b.values() if row["class"] and other["class"] == row["class"]
                         and other["file"] and row["file"] and same_file(other["file"], row["file"])
                         and other["id"][0] == ident[0]), None)
        if twin is None:
            differences.append(f"only in A: {ident} {row['severity'] or ''} `{identity(row)}`".replace("  ", " "))
            continue
        rows_b.pop(twin["id"])
        if twin["severity"] != row["severity"]:
            differences.append(f"severity: `{identity(row)}` is {row['severity']} in A ({ident}), "
                               f"{twin['severity']} in B ({twin['id']})")
        alt_a, alt_b = a["alternates"].get(ident), b["alternates"].get(twin["id"])
        if alt_a != alt_b:
            differences.append(f"alternate: `{identity(row)}` is {alt_a or 'none'} in A, {alt_b or 'none'} in B")
    for ident, row in rows_b.items():
        differences.append(f"only in B: {ident} {row['severity'] or ''} `{identity(row)}`".replace("  ", " "))
    for field_name, label_text in (("final", "score"), ("band", "band"), ("alternate_score", "alternate score"),
                                   ("overall_risk", "Overall risk")):
        if a[field_name] != b[field_name]:
            differences.append(f"{label_text}: {a[field_name]} in A, {b[field_name]} in B")
    return {"identical": not differences, "score_a": a["final"], "score_b": b["final"], "differences": differences}


# ---------------------------------------------------------------- fixtures


def validate_fixture(case_dir):
    """Return a list of problems with one fixture directory."""
    problems = []
    name = case_dir.name
    target = case_dir / "target"
    files = sorted(path for path in target.rglob("*") if path.is_file()) if target.is_dir() else []
    if not files:
        problems.append(f"{name}: target/ is missing or empty")
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if HINT_RE.search(text):
            problems.append(f"{name}: {path.relative_to(case_dir)} hints that it is a test; the graded run "
                            "must see only the target")
        if path.stat().st_mode & 0o111:
            problems.append(f"{name}: {path.relative_to(case_dir)} is executable; fixtures stay mode 0644")
    try:
        data = json.loads((case_dir / "expected.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return problems + [f"{name}: expected.json doesn't load: {error}"]

    for field_name, kind in TOP_FIELDS.items():
        if not isinstance(data.get(field_name, ...), kind):
            problems.append(f"{name}: {field_name} is missing or has the wrong type")
    problems += [f"{name}: unknown top-level field {key!r}" for key in data if key not in TOP_FIELDS]
    expect = data.get("expect") if isinstance(data.get("expect"), dict) else {}
    problems += [f"{name}: unknown expect field {key!r}" for key in expect if key not in EXPECT_FIELDS]

    def score_range(key, required):
        value = expect.get(key)
        if value is None:
            if required:
                problems.append(f"{name}: expect.{key} is required")
            return
        if not (isinstance(value, list) and len(value) == 2 and all(isinstance(n, int) for n in value)
                and 0 <= value[0] <= value[1] <= 100):
            problems.append(f"{name}: expect.{key} must be [low, high] within 0–100")

    score_range("score_range", True)
    score_range("alternate_score_range", False)
    bands = expect.get("bands")
    if not (isinstance(bands, list) and bands and set(bands) <= set(vr.BANDS)):
        problems.append(f"{name}: expect.bands must list band names from {vr.BANDS}")
    if not set(as_list(expect.get("overall_risk"))) <= set(vr.SEVERITIES[:4]):
        problems.append(f"{name}: expect.overall_risk must be Critical, High, Medium, or Low")
    if not isinstance(expect.get("no_other_findings"), bool):
        problems.append(f"{name}: expect.no_other_findings must be true or false")

    shipped = {path.name for path in files}
    for section, (required, optional) in ROW_FIELDS.items():
        rows = expect.get(section)
        if not isinstance(rows, list):
            problems.append(f"{name}: expect.{section} must be a list")
            continue
        for number, row in enumerate(rows, 1):
            where = f"{name}: expect.{section}[{number}]"
            if not isinstance(row, dict):
                problems.append(f"{where} must be an object")
                continue
            problems += [f"{where} is missing {key}" for key in sorted(required - set(row))]
            problems += [f"{where} has unknown field {key!r}" for key in sorted(set(row) - required - optional)]
            if "class" in row and not set(as_list(row["class"])) <= set(vr.DEFECT_CLASSES):
                problems.append(f"{where}: class must come from the defect classes in scoring-procedure.md")
            for key in ("severity", "alternate", "min_severity"):
                if key in row and not set(as_list(row[key])) <= set(vr.SEVERITIES):
                    problems.append(f"{where}: {key} must be a severity name")
            if "reason" in row and row["reason"] not in REASON_CODES:
                problems.append(f"{where}: reason must be a reason code from scoring-procedure.md")
            if "file" in row and row["file"] not in shipped:
                problems.append(f"{where}: {row['file']} isn't in target/")
            if not str(row.get("rationale", "")).strip():
                problems.append(f"{where}: rationale must say why, citing the Decision procedure")
    return problems


def self_test():
    problems = []
    cases = sorted(path for path in FIXTURES.iterdir() if path.is_dir()) if FIXTURES.is_dir() else []
    if not cases:
        problems.append("no fixtures under tests/fixtures/")
    for case_dir in cases:
        problems += validate_fixture(case_dir)

    # The reason codes the grader accepts are the ones scoring-procedure.md's table lists.
    scoring_text = (ROOT / "monocle" / vr.SCORING_REFERENCE).read_text(encoding="utf-8")
    listed_codes = tuple(re.findall(r"^\| `([a-z-]+)` \|", scoring_text, re.MULTILINE))
    if listed_codes != REASON_CODES:
        problems.append(f"reason codes: {vr.SCORING_REFERENCE} lists {listed_codes}; grade_report.py has {REASON_CODES}")

    rules =vr.parse_rules((ROOT / "monocle" / "SKILL.md").read_text(encoding="utf-8"))
    one_high = dict(high=1, medium=0, low=0, info=0, nonsec=0)
    base = vr.synthetic_report(rules, **one_high, keys={"S1": "prep.zsh:summary · shared-path"})

    def expectation(**overrides):
        expect = {"score_range": [25, 69], "bands": ["Fair", "Poor"], "overall_risk": "High",
                  "no_other_findings": False, "findings": [{"class": "shared-path", "file": "prep.zsh",
                                                            "severity": "High", "rationale": "r"}],
                  "not_scored": [], "refuted": [], "must_not_flag": []}
        expect.update(overrides)
        return {"expect": expect}

    with_x = base.replace("| Not scored | — | 0 | 0 | 0 |", "| Not scored | X1 removal gate (capability) | 1 | 0 | 0 |").replace(
        "  - `S1` — `prep.zsh:summary · shared-path`",
        "  - `S1` — `prep.zsh:summary · shared-path`\n  - `X1` — `prep.zsh:remove · gate`")
    with_refuted = base.replace("- **Issue keys.**", "- **Refuted candidates.**\n  - prep.zsh:work · shared-path — root"
                                " write — refuted by mktemp -d at `prep.zsh:3`\n- **Issue keys.**")
    low_gate = vr.synthetic_report(rules, high=0, medium=0, low=1, info=0, nonsec=0,
                                   keys={"S1": "apps.zsh:main · gate"}).replace(
        "**Operator baseline:** None — the score doesn't depend on deployment.",
        "**Operator baseline:**\n\n- Parameter 4 is set (README.md:5) (S1 → 🟠 High if not); check: none available")
    extra_low = vr.synthetic_report(rules, high=1, medium=0, low=1, info=0, nonsec=0,
                                    keys={"S1": "prep.zsh:summary · shared-path", "S2": "prep.zsh:log · disclosure"})
    grade_cases = (
        ("matching report", base, expectation(), "PASS"),
        ("missed finding", base, expectation(findings=[{"class": "injection", "file": "prep.zsh",
                                                         "severity": "High", "rationale": "r"}]), "FAIL"),
        ("adjacent severity", base, expectation(findings=[{"class": "shared-path", "file": "prep.zsh",
                                                            "severity": "Medium", "rationale": "r"}]), "DRIFT"),
        ("false positive", base, expectation(findings=[], must_not_flag=[{"class": "shared-path", "file": "prep.zsh",
                                                                          "rationale": "r"}]), "FAIL"),
        ("score out of range", base, expectation(score_range=[70, 100]), "FAIL"),
        ("extra finding allowed", extra_low, expectation(), "DRIFT"),
        ("extra finding on a clean fixture", extra_low, expectation(no_other_findings=True), "FAIL"),
        ("reason code found", with_x, expectation(not_scored=[{"reason": "capability", "class": "gate",
                                                                "rationale": "r"}]), "PASS"),
        ("reason code missing", base, expectation(not_scored=[{"reason": "capability", "rationale": "r"}]), "FAIL"),
        ("alternate matches", low_gate, expectation(score_range=[70, 100], bands=["Excellent", "Good"],
                                                    overall_risk="Low",
                                                    findings=[{"class": "gate", "file": "apps.zsh", "severity": "Low",
                                                               "alternate": "High", "rationale": "r"}]), "PASS"),
        ("alternate differs", low_gate, expectation(score_range=[70, 100], bands=["Excellent", "Good"],
                                                    overall_risk="Low",
                                                    findings=[{"class": "gate", "file": "apps.zsh", "severity": "Low",
                                                               "alternate": "Low", "rationale": "r"}]), "FAIL"),
    )
    for name, text, expected, wanted in grade_cases:
        verdict = grade(text, expected)["verdict"]
        if verdict != wanted:
            problems.append(f"grade, {name}: expected {wanted}, got {verdict}")
    refuted = grade(with_refuted, expectation(refuted=[{"class": "shared-path", "file": "prep.zsh", "rationale": "r"}]))
    if not any("recorded" in r["detail"] and "not recorded" not in r["detail"] for r in refuted["results"]):
        problems.append("grade, refuted candidate: the Refuted candidates entry wasn't read")

    if not compare(base, base)["identical"]:
        problems.append("compare: a report differs from itself")
    medium = vr.synthetic_report(rules, high=0, medium=1, low=0, info=0, nonsec=0,
                                 keys={"S1": "prep.zsh:summary · shared-path"})
    changed = compare(base, medium)
    if changed["identical"] or not any(d.startswith("severity:") for d in changed["differences"]):
        problems.append(f"compare: a severity change wasn't reported ({changed['differences']})")

    for problem in problems:
        print(vr.safe_text(f"FAIL {problem}"))
    print(f"self-test: {len(cases)} fixtures validated, {len(grade_cases) + 1} grading cases, 2 compare cases — "
          f"{'all passed' if not problems else f'{len(problems)} problem(s)'}")
    return 1 if problems else 0


# ---------------------------------------------------------------- command line


def render_grade(result, report_path, expected_path):
    lines = [f"Report: {report_path}", f"Fixture: {Path(expected_path).parent.name}",
             f"Verdict: {result['verdict']}", ""]
    lines += [f"[{item['status']}] {item['detail']}" for item in result["results"]]
    counts = result["counts"]
    lines += ["", "Summary: " + ", ".join(f"{n} {status}" for status, n in counts.items() if n) or "Summary: no rows"]
    return "\n".join(vr.safe_text(line) for line in lines)


def read_text(path):
    try:
        return vr.read_report(path)
    except (vr.VerifyError, OSError) as error:
        raise GradeError(f"{path}: {error}") from error


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--self-test", action="store_true", help="validate every fixture and test the grader")
    commands = parser.add_subparsers(dest="command")
    grade_cmd = commands.add_parser("grade", help="grade REPORT against EXPECTED")
    grade_cmd.add_argument("report")
    grade_cmd.add_argument("expected")
    grade_cmd.add_argument("--json", action="store_true")
    compare_cmd = commands.add_parser("compare", help="compare the ledgers of two reports on one target")
    compare_cmd.add_argument("report_a")
    compare_cmd.add_argument("report_b")
    compare_cmd.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return self_test()
        if args.command == "grade":
            try:
                expected = json.loads(Path(args.expected).read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                raise GradeError(f"{args.expected}: {error}") from error
            result = grade(read_text(args.report), expected)
            print(json.dumps(vr.sanitize(result), indent=2, ensure_ascii=False) if args.json
                  else render_grade(result, args.report, args.expected))
            return 0 if result["verdict"] == "PASS" else 1
        if args.command == "compare":
            result = compare(read_text(args.report_a), read_text(args.report_b))
            if args.json:
                print(json.dumps(vr.sanitize(result), indent=2, ensure_ascii=False))
            else:
                lines = [f"Scores: {result['score_a']} (A), {result['score_b']} (B)",
                         "Ledgers identical" if result["identical"] else "Differences:"]
                lines += [f"- {difference}" for difference in result["differences"]]
                print("\n".join(vr.safe_text(line) for line in lines))
            return 0 if result["identical"] else 1
        parser.error("choose grade, compare, or --self-test")
    except (GradeError, vr.VerifyError) as error:
        print(f"grade_report.py: {vr.safe_text(error)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
