from __future__ import annotations
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
        implemented = [m["id"] for m in self.data["modules"] if m["status"] == "implemented"]
        self.assertEqual(implemented, ["P01", "P02", "P03", "P04", "P05"])

if __name__ == "__main__":
    unittest.main()
