"""Validate real-repository evaluation materials, not agent execution."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals" / "real-repos" / "leju-robot-ota"
SCENARIOS = BASE / "scenarios.json"
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
        cls.data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        cls.scenarios = cls.data["scenarios"]

    def test_metadata_and_scenarios_are_well_formed(self):
        self.assertEqual(self.data["version"], 1)
        self.assertTrue(self.data["source"].endswith("leju-robot-ota"))
        self.assertRegex(self.data["base_rev"], r"^[0-9a-f]{40}$")
        ids = [scenario["id"] for scenario in self.scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario["prompt"].strip())
                self.assertTrue(scenario["expectations"])
                self.assertTrue(scenario["expected_skills"])
                for skill in scenario["expected_skills"]:
                    self.assertTrue((SKILLS / skill / "SKILL.md").is_file(), skill)
                self.assertTrue(scenario["checks"])

    def test_checks_reference_existing_hidden_files(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
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
                            source = BASE / item["source"]
                            self.assertTrue(source.is_file(), source)
                            self.assertTrue(item["target"].startswith("internal/audit/"))
                        self.assertTrue(check["command"])
                    elif kind == "command":
                        self.assertTrue(check["command"])
                    elif kind == "response_or_diff_contains":
                        self.assertTrue(check["pattern"].strip())

    def test_runner_and_ignore_file_exist(self):
        self.assertTrue((BASE / "run.py").is_file())
        self.assertTrue((BASE / "README.md").is_file())
        self.assertIn("results/", (BASE / ".gitignore").read_text(encoding="utf-8"))
        compile((BASE / "run.py").read_text(encoding="utf-8"), str(BASE / "run.py"), "exec")

    def test_hidden_go_files_declare_the_audit_package(self):
        for path in (BASE / "hidden").rglob("*.go"):
            with self.subTest(path=path):
                self.assertIn("package audit", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
