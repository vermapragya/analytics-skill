"""
Static SQL anti-pattern scanner.

Regex-based first pass over a SQL file. Flags mechanical anti-patterns with
line numbers and severity. Output is a list of LEADS for a human/agent review,
not verdicts — every hit needs confirmation in context.

Usage:
    python antipattern_scan.py path/to/query.sql
    cat query.sql | python antipattern_scan.py -

Exit codes: 0 = no blockers, 1 = at least one blocker-severity lead.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass


@dataclass
class Rule:
    pattern: re.Pattern
    severity: str  # blocker | major | minor
    title: str
    advice: str


RULES = [
    Rule(
        re.compile(r"\bnot\s+in\s*\(\s*select\b", re.I),
        "blocker",
        "NOT IN with subquery",
        "Returns zero rows if the subquery yields any NULL. Use NOT EXISTS.",
    ),
    Rule(
        re.compile(r"\bselect\s+distinct\b", re.I),
        "major",
        "SELECT DISTINCT",
        "If this dedups join output, it may be masking a fanout. Verify the join grain (sql-correctness-review).",
    ),
    Rule(
        re.compile(r"\bselect\s+\*", re.I),
        "minor",
        "SELECT *",
        "Project only needed columns; columnar warehouses charge I/O per column.",
    ),
    Rule(
        re.compile(r"\b(date|to_date|to_char|year|month|trunc|date_trunc|lower|upper|cast)\s*\(\s*\w+(\.\w+)?\s*[^)]*\)\s*(=|>=|<=|<|>|between)", re.I),
        "major",
        "Function-wrapped filter column",
        "Function on the filtered column defeats partition pruning. Rewrite as a range predicate on the raw column.",
    ),
    Rule(
        re.compile(r"\bon\b[^;]{0,200}?\bor\b", re.I),
        "major",
        "OR in join condition",
        "OR-joins prevent hash joins. Split into two joins + COALESCE, or UNION ALL of clean joins. (Verify the OR is in the ON clause, not a later WHERE.)",
    ),
    Rule(
        re.compile(r"\bunion\b(?!\s+all)", re.I),
        "major",
        "UNION without ALL",
        "UNION dedups the full row (expensive sort). Use UNION ALL unless dedup is intended.",
    ),
    Rule(
        re.compile(r"\brange\s+between\b", re.I),
        "minor",
        "RANGE window frame",
        "RANGE requires value-based sort; prefer ROWS BETWEEN unless tie semantics require RANGE.",
    ),
    Rule(
        re.compile(r"\bcross\s+join\b", re.I),
        "major",
        "CROSS JOIN",
        "Verify the Cartesian product is intentional (e.g., date spine) and both sides are small.",
    ),
    Rule(
        re.compile(r"\bjoin\b\s+\w+(\s+(as\s+)?\w+)?\s*(?!.*\bon\b)\s*$", re.I),
        "blocker",
        "JOIN possibly missing ON",
        "JOIN with no ON on the same line — confirm the join condition exists (next lines) or this is a Cartesian product.",
    ),
]


def scan(sql: str) -> list[tuple[int, Rule]]:
    findings: list[tuple[int, Rule]] = []
    # Strip comments so commented-out SQL doesn't trigger hits
    no_block_comments = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), sql, flags=re.S)
    lines = no_block_comments.splitlines()
    for i, raw_line in enumerate(lines, start=1):
        line = raw_line.split("--", 1)[0]
        if not line.strip():
            continue
        for rule in RULES:
            if rule.pattern.search(line):
                findings.append((i, rule))
    return findings


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    source = sys.argv[1]
    sql = sys.stdin.read() if source == "-" else open(source).read()

    findings = scan(sql)
    if not findings:
        print("No mechanical anti-patterns found. (This is a first pass, not a full review.)")
        return 0

    order = {"blocker": 0, "major": 1, "minor": 2}
    findings.sort(key=lambda f: (order[f[1].severity], f[0]))

    print(f"{len(findings)} lead(s) found:\n")
    for line_no, rule in findings:
        print(f"  [{rule.severity.upper():7s}] line {line_no:>4}  {rule.title}")
        print(f"            {rule.advice}\n")

    print("Note: these are leads, not verdicts. Confirm each in context.")
    return 1 if any(r.severity == "blocker" for _, r in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
