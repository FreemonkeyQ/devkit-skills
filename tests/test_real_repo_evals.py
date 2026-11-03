"""Validate real-repository evaluation materials, not agent execution."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOS = {
    "leju-robot-ota": {
        "root": ROOT / "evals" / "real-repos" / "leju-robot-ota",
        "target_prefix": "internal/audit/",
        "source_suffix": "leju-robot-ota",
    },
    "leju-let-platform": {
        "root": ROOT / "evals" / "real-repos" / "leju-let-platform",
        "target_prefix": "projects/backend/kuavodatahubserver/src/test/java/",
        "source_suffix": "Leju-LET-Platform",
    },
}
SKILLS = ROOT / "skills"
CHECK_TYPES = {
    "manifest_unchanged",
    "changed_files_max",
    "changed_files_prefix",
    "hidden_files",
    "command",
    "response_or_diff_contains",
}


class RealRepoEvaluationMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {}
        for name, spec in REPOS.items():
            data = json.loads((spec["root"] / "scenarios.json").read_text(encoding="utf-8"))
            cls.data[name] = data

    def test_metadata_and_scenarios_are_well_formed(self):
        for name, spec in REPOS.items():
            data = self.data[name]
            with self.subTest(repo=name):
                self.assertEqual(data["version"], 1)
                self.assertTrue(data["source"].endswith(spec["source_suffix"]))
                self.assertRegex(data["base_rev"], r"^[0-9a-f]{40}$")
                ids = [scenario["id"] for scenario in data["scenarios"]]
                self.assertEqual(len(ids), len(set(ids)))
                for scenario in data["scenarios"]:
                    self.assertTrue(scenario["prompt"].strip())
                    self.assertTrue(scenario["expectations"])
                    self.assertTrue(scenario["expected_skills"])
                    for skill in scenario["expected_skills"]:
                        self.assertTrue((SKILLS / skill / "SKILL.md").is_file(), skill)
                    self.assertTrue(scenario["checks"])

    def test_checks_reference_existing_hidden_files(self):
        for name, spec in REPOS.items():
            base = spec["root"]
            for scenario in self.data[name]["scenarios"]:
                with self.subTest(repo=name, scenario=scenario["id"]):
                    for check in scenario["checks"]:
                        kind = check["type"]
                        self.assertIn(kind, CHECK_TYPES)
                        if kind == "manifest_unchanged":
                            self.assertTrue(check["paths"])
                        elif kind == "changed_files_max":
                            self.assertIsInstance(check["value"], int)
                        elif kind == "changed_files_prefix":
                            self.assertTrue(check["prefixes"])
                        elif kind == "hidden_files":
                            self.assertTrue(check["files"])
                            for item in check["files"]:
                                source = base / "hidden" / item["source"]
                                self.assertTrue(source.is_file(), source)
                                self.assertTrue(
                                    item["target"].startswith(spec["target_prefix"]),
                                    item["target"],
                                )
                            self.assertTrue(check["command"])
                        elif kind == "command":
                            self.assertTrue(check["command"])
                        elif kind == "response_or_diff_contains":
                            self.assertTrue(check["pattern"].strip())

    def test_runners_and_ignore_files_exist(self):
        for name, spec in REPOS.items():
            base = spec["root"]
            with self.subTest(repo=name):
                self.assertTrue((base / "run.py").is_file())
                self.assertTrue((base / "README.md").is_file())
                self.assertIn("results/", (base / ".gitignore").read_text(encoding="utf-8"))
                compile((base / "run.py").read_text(encoding="utf-8"), str(base / "run.py"), "exec")

    def test_hidden_files_use_expected_package(self):
        ota = REPOS["leju-robot-ota"]["root"]
        for path in (ota / "hidden").rglob("*.go"):
            with self.subTest(path=path):
                self.assertIn("package audit", path.read_text(encoding="utf-8"))
        let = REPOS["leju-let-platform"]["root"]
        for path in (let / "hidden").rglob("*.java"):
            with self.subTest(path=path):
                self.assertIn(
                    "package com.kuavo.datahub.common.tool;",
                    path.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
