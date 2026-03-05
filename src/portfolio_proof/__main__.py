from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .reporting import generate_report_markdown, write_report
from .checks import run_all_checks


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="portfolio_proof",
        description=(
            "Deterministic DevOps guardrails demo: validate inputs and generate a report "
            "mapping findings to IaC drift, delivery friction, and reliability/on-call readiness."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--inputs",
        type=Path,
        required=True,
        help="Path to an input bundle (e.g., examples/good).",
    )
    common.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository root (used to locate docs/runbooks). Default: current directory.",
    )

    p_report = sub.add_parser("report", parents=[common], help="Generate a markdown report.")
    p_report.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/report.md"),
        help="Where to write the report. Default: artifacts/report.md",
    )
    p_report.add_argument(
        "--also-scan",
        type=Path,
        default=None,
        help="Optional second input bundle to scan as a negative example (included in report only).",
    )

    sub.add_parser("validate", parents=[common], help="Validate inputs; exit non-zero on errors.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)

    inputs = ns.inputs
    repo_root = ns.repo_root

    if ns.cmd == "validate":
        findings = run_all_checks(inputs=inputs, repo_root=repo_root)
        errors = [f for f in findings if f.severity == "ERROR"]
        if errors:
            for f in errors:
                print(f"[ERROR] {f.id}: {f.title}")
                for ev in f.evidence:
                    print(f"  - {ev}")
            return 2
        return 0

    if ns.cmd == "report":
        findings_good = run_all_checks(inputs=inputs, repo_root=repo_root)
        findings_bad = None
        if ns.also_scan is not None:
            findings_bad = run_all_checks(inputs=ns.also_scan, repo_root=repo_root)

        report_md = generate_report_markdown(
            inputs=inputs,
            repo_root=repo_root,
            findings=findings_good,
            negative_example=(ns.also_scan, findings_bad) if findings_bad is not None else None,
        )
        write_report(ns.output, report_md)
        return 0

    raise RuntimeError(f"Unhandled command: {ns.cmd}")


if __name__ == "__main__":
    raise SystemExit(main())

