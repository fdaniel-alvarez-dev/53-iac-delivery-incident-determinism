from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from portfolio_proof.checks import run_all_checks
from portfolio_proof.reporting import generate_report_markdown, write_report


class ReportTests(unittest.TestCase):
    def test_report_writes_markdown(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        inputs = repo_root / "examples" / "good"
        findings = run_all_checks(inputs=inputs, repo_root=repo_root)
        md = generate_report_markdown(inputs=inputs, repo_root=repo_root, findings=findings, negative_example=None)
        self.assertIn("# Deterministic Guardrails Report", md)
        self.assertIn("Pain Point 1", md)
        self.assertIn("Pain Point 2", md)
        self.assertIn("Pain Point 3", md)

        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.md"
            write_report(out, md)
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 100)

