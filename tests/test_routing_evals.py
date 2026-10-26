"""Validate routing-matrix materials and deterministic lexical evaluation."""
import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals" / "routing"
sys.path.insert(0, str(BASE))

import host_matrix  # noqa: E402
import matrix  # noqa: E402


class RoutingMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.skills, cls.descriptions = matrix.load(ROOT)
        cls.cases = cls.data["cases"]

    def test_data_is_valid(self):
        self.assertEqual(matrix.validate(self.data, self.skills), [])
        self.assertEqual(len(self.skills), 19)

    def test_case_type_counts(self):
        counts = Counter(case["type"] for case in self.cases)
        self.assertEqual(counts, {"positive": 57, "negative": 18, "hard-negative": 12})

    def test_each_skill_has_three_positives(self):
        counts = Counter(
            case["primary"] for case in self.cases if case["type"] == "positive"
        )
        self.assertEqual(set(counts), set(self.skills))
        for skill, count in counts.items():
            with self.subTest(skill=skill):
                self.assertEqual(count, 3)

    def test_prompts_are_not_verbatim_description_snippets(self):
        for case in self.cases:
            description = self.descriptions[self.skills.index(case["primary"])]
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["prompt"].strip(), description)

    def test_evaluate_covers_every_skill_and_is_deterministic(self):
        first = matrix.evaluate(self.data, self.skills, self.descriptions)
        second = matrix.evaluate(self.data, self.skills, self.descriptions)
        self.assertEqual(first, second)
        self.assertEqual(set(first["per_skill"]), set(self.skills))
        self.assertEqual(first["overall"]["total"], len(self.cases))
        self.assertEqual(
            sum(stats["positives"] for stats in first["per_skill"].values()), 57
        )
        for row in first["rows"]:
            self.assertIn(row["top1"], self.skills)
            self.assertEqual(len(row["top3"]), 3)

    def test_host_arm_selects_one_positive_per_skill_plus_hard_negatives(self):
        cases = host_matrix.select_cases(self.data, None, None)
        counts = Counter(case["type"] for case in cases)
        self.assertEqual(counts, {"positive": 19, "hard-negative": 12})
        self.assertEqual(len(cases), 31)
        self.assertEqual(
            {case["primary"] for case in cases if case["type"] == "positive"},
            set(self.skills),
        )

    def test_skill_name_extraction(self):
        self.assertEqual(
            host_matrix.skill_names({"skill": "dv-build", "args": "x"}), ["dv-build"]
        )
        self.assertEqual(
            host_matrix.skill_names({"skill": "devkit-skills:dv-build"}), ["dv-build"]
        )
        self.assertEqual(host_matrix.skill_names({"command": "/dv-arch"}), ["dv-arch"])
        self.assertEqual(host_matrix.skill_names({"skill": "not-a-skill"}), [])
        self.assertEqual(host_matrix.skill_names({"skill": "dv-build", "x": "dv-review"}),
                         ["dv-build"])
        self.assertEqual(
            host_matrix.external_skill_names({"skill": "skill-creator"}),
            ["skill-creator"],
        )
        self.assertEqual(
            host_matrix.external_skill_names({"skill": "devkit-skills:dv-build"}), []
        )

    def test_results_are_gitignored(self):
        if not (ROOT / ".git").is_dir():
            self.skipTest("not a git checkout")
        proc = subprocess.run(
            ["git", "check-ignore", "-q", "evals/routing/results/example.json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, "results/ must stay untracked")


if __name__ == "__main__":
    unittest.main()
