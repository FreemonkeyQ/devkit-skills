"""Validate build-scenario evaluation materials, not skill execution."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals" / "build-scenarios"))
import compare  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evals" / "build-scenarios"
SCENARIOS = BASE / "scenarios.json"
FIXTURES = BASE / "fixtures"
SKILLS = ROOT / "skills"

CHECK_TYPES = {
    "response_or_diff_contains",
    "response_contains_any",
    "response_not_contains",
    "diff_contains",
    "diff_not_contains",
    "manifest_unchanged",
    "changed_files_max",
    "changed_files_prefix",
    "hidden_tests",
    "no_unverified_perf_claim",
}
PERMISSIONS = {"plan", "acceptEdits"}
PATTERN_CHECKS = {
    "response_or_diff_contains",
    "response_not_contains",
    "diff_contains",
    "diff_not_contains",
}


class BuildEvaluationMaterialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
        cls.scenarios = cls.data["scenarios"]

    def test_scenarios_are_well_formed(self):
        self.assertEqual(self.data["version"], 1)
        self.assertEqual(len(self.scenarios), 12)
        ids = [scenario["id"] for scenario in self.scenarios]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario["prompt"].strip())
                self.assertIn(scenario["permission"], PERMISSIONS)
                self.assertTrue(scenario["expectations"])
                self.assertTrue(scenario["expected_skills"])
                for skill in scenario["expected_skills"]:
                    self.assertTrue((SKILLS / skill / "SKILL.md").is_file(), skill)
                fixture = FIXTURES / scenario["fixture"]
                self.assertTrue(fixture.is_dir(), fixture)
                self.assertTrue(any(path.is_file() for path in fixture.rglob("*")), fixture)

    def test_checks_are_known_and_reference_fixtures(self):
        for scenario in self.scenarios:
            fixture = FIXTURES / scenario["fixture"]
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario["checks"])
                for check in scenario["checks"]:
                    kind = check["type"]
                    self.assertIn(kind, CHECK_TYPES)
                    if kind == "manifest_unchanged":
                        self.assertTrue(check["paths"])
                        for path in check["paths"]:
                            self.assertTrue(
                                (fixture / path).is_file(),
                                f"{scenario['id']}: {path}",
                            )
                    elif kind == "changed_files_max":
                        self.assertIsInstance(check["value"], int)
                        self.assertGreaterEqual(check["value"], 0)
                    elif kind == "changed_files_prefix":
                        self.assertTrue(check["prefixes"])
                        self.assertTrue(
                            all(isinstance(item, str) and item.strip()
                                for item in check["prefixes"])
                        )
                    elif kind == "hidden_tests":
                        suite = BASE / "hidden" / check["suite"]
                        self.assertTrue(suite.is_dir(), suite)
                        self.assertTrue(
                            any(path.is_file() for path in suite.rglob("*")), suite
                        )
                        copy_to = Path(check["copy_to"])
                        self.assertFalse(copy_to.is_absolute(), copy_to)
                        self.assertNotIn("..", copy_to.parts, copy_to)
                        self.assertTrue(check["command"])
                        self.assertTrue(
                            all(isinstance(item, str) and item.strip()
                                for item in check["command"])
                        )
                        self.assertIsInstance(check.get("timeout", 120), int)
                    elif kind == "response_contains_any":
                        self.assertTrue(check["patterns"])
                        self.assertTrue(
                            all(isinstance(item, str) and item.strip()
                                for item in check["patterns"])
                        )
                    elif kind in PATTERN_CHECKS:
                        self.assertTrue(
                            isinstance(check.get("pattern"), str)
                            and check["pattern"].strip()
                        )

    def test_negative_routes_reference_known_skills(self):
        negatives = self.data["negative_routes"]
        self.assertEqual(len(negatives), 10)
        for entry in negatives:
            with self.subTest(prompt=entry["prompt"]):
                self.assertTrue(entry["prompt"].strip())
                self.assertTrue(
                    (SKILLS / entry["skill"] / "SKILL.md").is_file(),
                    entry["skill"],
                )

    def test_runner_and_routing_scripts_exist(self):
        self.assertTrue((BASE / "run.py").is_file())
        self.assertTrue((BASE / "route.py").is_file())
        self.assertTrue((BASE / "compare.py").is_file())
        self.assertTrue((BASE / "README.md").is_file())

    def test_no_plugin_arm_flags(self):
        runner = BASE / "run.py"
        conflict = subprocess.run(
            [sys.executable, str(runner), "--no-plugin", "--explicit-skill", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(conflict.returncode, 2)
        chain_conflict = subprocess.run(
            [sys.executable, str(runner), "--chain", "--no-plugin", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(chain_conflict.returncode, 2)
        skills_conflict = subprocess.run(
            [sys.executable, str(runner), "--skills", "dv-build,dv-test", "--no-plugin", "--dry-run"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(skills_conflict.returncode, 2)
        dry = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--no-plugin",
                "--scenario",
                "S1-reuse-csv-export",
                "--dry-run",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("S1-reuse-csv-export", dry.stdout)

    def test_compare_does_not_treat_timeout_as_pass(self):
        rows = compare.aggregate([
            {
                "arm": "a", "scenario": "x", "checks_passed": 0, "checks_total": 0,
                "changed_files": [], "tool_calls": 0, "duration_s": 0,
                "usage": {}, "skill_invocations": [], "error": "TimeoutExpired",
            }
        ])
        self.assertEqual(rows[0]["task_pass"], 0)

    def test_compare_counts_hidden_files_checks(self):
        rows = compare.aggregate([
            {
                "arm": "a", "scenario": "x", "checks_passed": 1, "checks_total": 1,
                "changed_files": [], "tool_calls": 0, "duration_s": 0,
                "usage": {}, "skill_invocations": [], "error": None,
                "checks": [{"check": "hidden_files:[...]", "pass": True}],
            }
        ])
        self.assertEqual((rows[0]["hidden_pass"], rows[0]["hidden_total"]), (1, 1))

    def test_results_are_gitignored(self):
        if not (ROOT / ".git").is_dir():
            self.skipTest("not a git checkout")
        proc = subprocess.run(
            ["git", "check-ignore", "-q", "evals/build-scenarios/results/example.json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, "results/ must stay untracked")


if __name__ == "__main__":
    unittest.main()
