import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import devkit_context  # noqa: E402
import devkit_gates  # noqa: E402
import devkit_run  # noqa: E402


class AdapterTests(unittest.TestCase):
    def test_detects_python_gates(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "tests").mkdir()
            (root / "tests/test_x.py").write_text("")
            (root / "scripts").mkdir()
            (root / "scripts/lint.py").write_text("")
            adapter = devkit_context.detect(root)
            ids = {gate["id"] for gate in adapter["gates"]}
            self.assertIn("unit", ids)
            self.assertIn("lint", ids)
            self.assertEqual(adapter["language"], "python")

    def test_detects_go_and_node(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "go.mod").write_text("module example\n")
            (root / "package.json").write_text(json.dumps({"scripts": {"test": "node --test", "lint": "lint"}}))
            adapter = devkit_context.detect(root)
            ids = {gate["id"] for gate in adapter["gates"]}
            self.assertTrue({"unit", "lint", "test"}.issubset(ids))
            self.assertEqual(adapter["language"], "mixed")

    def test_detects_hard_constraints(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            (root / "AGENTS.md").write_text("## 硬约束\n- **不改 schema**\n- 其他\n")
            adapter = devkit_context.detect(root)
            self.assertIn("不改 schema", adapter["invariants"])


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".devkit").mkdir()
        (self.root / ".devkit/project.json").write_text(json.dumps({
            "version": 1,
            "gates": [{
                "id": "unit", "kind": "test", "command": "python3 -c \"print('ok')\"",
                "required": True, "timeout": 20,
            }],
        }))

    def tearDown(self):
        self.tmp.cleanup()

    def init(self, goal="加筛选", risk="standard", endpoint="done", run_id="r1", scope=None):
        args = type("Args", (), {
            "root": self.root, "goal": goal, "risk": risk, "endpoint": endpoint,
            "scope": scope or [], "run_id": run_id, "force": True,
        })()
        self.assertEqual(devkit_run.init_run(args), 0)
        return self.root / ".devkit/runs" / run_id

    def test_standard_plan_and_completion(self):
        directory = self.init()
        plan = json.loads((directory / "plan.json").read_text())
        self.assertEqual([step["skill"] for step in plan["steps"]], ["dv-build", "dv-test", "dv-review", "dv-done"])
        self.assertEqual(plan["gates"], ["unit"])
        devkit_gates.run_gates(self.root, devkit_context.load_adapter(self.root), directory)
        self.assertEqual(devkit_gates.check(self.root, devkit_context.load_adapter(self.root), directory), [])
        for skill in ("dv-build", "dv-test", "dv-review"):
            devkit_run.record_step(directory, plan, *self._contexts(directory), skill, "pass", skill, [], [])
            plan = json.loads((directory / "plan.json").read_text())
        self.assertEqual(devkit_run.record_step(
            directory, plan, *self._contexts(directory), "dv-done", "pass", "done",
            [], ["加筛选|unit pass|pass"],
        ), 0)
        final = json.loads((directory / "plan.json").read_text())
        self.assertEqual(final["state"], "complete")

    def _contexts(self, directory):
        context = json.loads((directory / "context.json").read_text())
        acceptance = json.loads((directory / "acceptance.json").read_text())
        return context, acceptance

    def test_done_blocked_without_gates_or_acceptance(self):
        directory = self.init()
        plan = json.loads((directory / "plan.json").read_text())
        context, acceptance = self._contexts(directory)
        code = devkit_run.record_step(
            directory, plan, context, acceptance, "dv-done", "pass", "done", [], [],
        )
        self.assertEqual(code, 1)
        final = json.loads((directory / "plan.json").read_text())
        self.assertEqual(final["state"], "blocked")
        self.assertEqual(final["steps"][-1]["status"], "blocked")

    def test_trivial_fast_path_and_high_risk(self):
        directory = self.init(goal="改文案", risk="auto", run_id="r2")
        plan = json.loads((directory / "plan.json").read_text())
        self.assertEqual(plan["risk"], "trivial")
        self.assertEqual([step["skill"] for step in plan["steps"]], ["dv-build", "dv-done"])
        directory = self.init(goal="改权限 schema 迁移", risk="auto", run_id="r3")
        plan = json.loads((directory / "plan.json").read_text())
        self.assertEqual(plan["risk"], "high")

    def test_endpoint_adds_git_steps(self):
        directory = self.init(endpoint="push", run_id="r4")
        plan = json.loads((directory / "plan.json").read_text())
        self.assertEqual([step["skill"] for step in plan["steps"]][-2:], ["dv-commit", "dv-push"])
        self.assertTrue(plan["authorization"]["commit"])
        self.assertTrue(plan["authorization"]["push"])

    def test_init_excludes_run_artifacts_in_git(self):
        (self.root / ".git/info").mkdir(parents=True)
        self.init(run_id="r8")
        exclude = (self.root / ".git/info/exclude").read_text()
        self.assertIn(".devkit/runs/", exclude.splitlines())
        devkit_run.ensure_runs_excluded(self.root)
        self.assertEqual(
            (self.root / ".git/info/exclude").read_text().count(".devkit/runs/"), 1
        )

    def test_note_appends_context(self):
        directory = self.init(run_id="r7")
        context = json.loads((directory / "context.json").read_text())
        self.assertEqual(devkit_run.note_context(directory, context, "dv-build", "reuse", "reused Page"), 0)
        saved = json.loads((directory / "context.json").read_text())
        self.assertEqual(saved["evidence"][-1]["detail"], "reused Page")

    def test_driver_runs_steps_and_reloads_acceptance(self):
        directory = self.init(goal="改文案", risk="trivial", run_id="r6")
        script = self.root / "host.sh"
        script.write_text(
            "#!/bin/sh\n"
            "if [ \"$DEVKIT_SKILL\" = \"dv-done\" ]; then\n"
            "python3 - \"$DEVKIT_RUN\" <<'PY'\n"
            "import json,sys\n"
            "p=sys.argv[1]+'/acceptance.json'\n"
            "d=json.load(open(p)); d['items'][0]['status']='pass'; d['items'][0]['evidence']='driver'; json.dump(d,open(p,'w'))\n"
            "PY\n"
            "fi\n"
            "exit 0\n"
        )
        code = devkit_run.drive(self.root, "r6", f"sh {script}", 5, False)
        self.assertEqual(code, 0)
        plan = json.loads((directory / "plan.json").read_text())
        self.assertEqual(plan["state"], "complete")

    def test_gate_failure_blocks_check(self):
        (self.root / ".devkit/project.json").write_text(json.dumps({
            "version": 1,
            "gates": [{"id": "unit", "kind": "test", "command": "python3 -c \"exit(1)\"",
                       "required": True, "timeout": 20}],
        }))
        directory = self.init(run_id="r5")
        adapter = devkit_context.load_adapter(self.root)
        results = devkit_gates.run_gates(self.root, adapter, directory)
        self.assertEqual(results[0]["status"], "fail")
        self.assertTrue(devkit_gates.check(self.root, adapter, directory))


class EntryTests(unittest.TestCase):
    def test_install_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as t:
            home = Path(t)
            cmd = [sys.executable, str(ROOT / "scripts/install_entry.py"),
                   "--host", "claude", "--home", str(home)]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertFalse((home / ".claude/commands/dv.md").exists())
            proc = subprocess.run(cmd + ["--apply"], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            text = (home / ".claude/commands/dv.md").read_text()
            self.assertIn(str(ROOT), text)
            self.assertNotIn("{{DEVKIT_ROOT}}", text)
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", text)


if __name__ == "__main__":
    unittest.main()
