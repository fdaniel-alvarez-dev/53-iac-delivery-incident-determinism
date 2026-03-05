from __future__ import annotations

import unittest
from pathlib import Path

from portfolio_proof.checks import run_all_checks


class ValidateTests(unittest.TestCase):
    def test_good_examples_have_no_errors(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        inputs = repo_root / "examples" / "good"
        findings = run_all_checks(inputs=inputs, repo_root=repo_root)
        errors = [f for f in findings if f.severity == "ERROR"]
        self.assertEqual(errors, [], f"Unexpected errors: {errors}")

    def test_bad_examples_have_errors(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        inputs = repo_root / "examples" / "bad"
        findings = run_all_checks(inputs=inputs, repo_root=repo_root)
        errors = [f for f in findings if f.severity == "ERROR"]
        self.assertGreaterEqual(len(errors), 3)

