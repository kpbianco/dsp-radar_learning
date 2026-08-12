from __future__ import annotations

import copy
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def validate_implementation_frontier(modules: list[dict]) -> list[str]:
    statuses = [module.get("status") for module in modules]
    errors: list[str] = []
    unsupported = sorted(
        {str(status) for status in statuses if status not in {"implemented", "scaffolded"}}
    )
    if unsupported:
        errors.append(f"unsupported module statuses: {unsupported}")

    implemented_count = statuses.count("implemented")
    expected = ["implemented"] * implemented_count + ["scaffolded"] * (
        len(statuses) - implemented_count
    )
    if statuses != expected:
        errors.append("implemented modules must form a contiguous canonical prefix")
    return errors


def historical_module_test_policy_errors(source: str) -> list[str]:
    forbidden = (
        (r"(?i)latest implemented lesson overall", "permanent latest-module wording"),
        (
            r"(?i)current implementation frontier is P\d{2}",
            "hard-coded implementation frontier",
        ),
        (r"(?i)\bremains? scaffolded\b", "permanent future-scaffold wording"),
        (r"\bstatuses\s*\[\s*\d+\s*:\s*\]", "future status-tail assertion"),
        (r"\[\s*[\"']scaffolded[\"']\s*\]\s*\*", "exact scaffolded-tail snapshot"),
        (
            r"\bimplemented\s*=\s*\[[^\n]*\bfor\b[^\n]*\bstatus\b",
            "exact global implemented-list snapshot",
        ),
    )
    return [message for pattern, message in forbidden if re.search(pattern, source)]


class CurriculumTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "curriculum/modules.json").read_text())

    def test_has_exactly_84_ordered_modules(self):
        self.assertEqual(self.data["module_count"], 84)
        self.assertEqual([m["number"] for m in self.data["modules"]], list(range(1, 85)))

    def test_module_identity_and_core_files(self):
        for m in self.data["modules"]:
            self.assertEqual(m["id"], f"P{m['number']:02d}")
            folder = ROOT / m["folder"]
            for name in ("README.md",):
                self.assertTrue((folder / name).is_file(), f"{m['id']} missing {name}")

    def test_implemented_modules_follow_approved_batch_order(self):
        modules = self.data["modules"]
        self.assertEqual(validate_implementation_frontier(modules), [])
        implemented = [m["id"] for m in modules if m["status"] == "implemented"]
        expected = [f"P{number:02d}" for number in range(1, len(implemented) + 1)]
        self.assertEqual(implemented, expected)

        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        module_index = (ROOT / "modules" / "README.md").read_text(encoding="utf-8")
        frontier = implemented[-1]
        self.assertIn(f"current implementation frontier is {frontier}.", root_readme)
        self.assertRegex(module_index, rf"\| \[{frontier}\].*\| implemented \|")

        normalized_readme = " ".join(root_readme.split())
        implemented_count = len(implemented)
        self.assertIn(
            f"Projects 1–{implemented_count} have completed their separate governed "
            "implementation batches.",
            normalized_readme,
        )
        if implemented_count < self.data["module_count"]:
            self.assertIn(
                f"Projects {implemented_count + 1}–{self.data['module_count']} wait for their own "
                "MATLAB experiment, lesson, walkthrough, checks, validation, and evidence.",
                normalized_readme,
            )

    def test_future_module_transition_preserves_frontier_contract(self):
        implemented_count = sum(
            module["status"] == "implemented" for module in self.data["modules"]
        )
        future_modules = copy.deepcopy(self.data["modules"])
        if implemented_count < len(future_modules):
            future_modules[implemented_count]["status"] = "implemented"
        self.assertEqual(validate_implementation_frontier(future_modules), [])

        if implemented_count + 1 < len(future_modules):
            invalid_gap = copy.deepcopy(self.data["modules"])
            invalid_gap[implemented_count + 1]["status"] = "implemented"
            self.assertEqual(
                validate_implementation_frontier(invalid_gap),
                ["implemented modules must form a contiguous canonical prefix"],
            )

    def test_historical_module_tests_do_not_freeze_the_frontier(self):
        for path in sorted((ROOT / "tests").glob("test_p[0-9][0-9]_module.py")):
            with self.subTest(test_file=path.name):
                source = path.read_text(encoding="utf-8")
                self.assertEqual(historical_module_test_policy_errors(source), [])

    def test_historical_module_test_policy_rejects_time_relative_examples(self):
        examples = (
            'self.assertIn("Project 10 is the latest implemented lesson overall", readme)',
            'self.assertIn("current implementation frontier is P10.", readme)',
            'self.assertIn("Projects 11–84 remain scaffolded", readme)',
            'self.assertEqual(statuses[10:], ["scaffolded"] * 74)',
            'implemented = [entry["id"] for entry in modules if entry["status"] == "implemented"]',
        )
        for source in examples:
            with self.subTest(source=source):
                self.assertTrue(historical_module_test_policy_errors(source))


if __name__ == "__main__":
    unittest.main()
