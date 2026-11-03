#!/usr/bin/env python3
"""Run the cross-repo ablation matrix and write a consolidated report.

This orchestrates the existing runners; it does not implement another agent
loop. Each cell is one real host invocation per scenario. Outputs are ignored by
git; pass --dry-run to inspect commands first.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals" / "build-scenarios"))
import compare  # noqa: E402

TASKS = [
    {
        "name": "build-scenarios",
        "runner": ROOT / "evals" / "build-scenarios" / "run.py",
        "scenarios": ["S9-fullstack-backend-filter", "S11-saas-billing-backend"],
        "results": ROOT / "evals" / "build-scenarios" / "results",
    },
    {
        "name": "leju-robot-ota",
        "runner": ROOT / "evals" / "real-repos" / "leju-robot-ota" / "run.py",
        "scenarios": ["OTA2-audit-client-ip-filter"],
        "results": ROOT / "evals" / "real-repos" / "leju-robot-ota" / "results",
    },
    {
        "name": "leju-let-platform",
        "runner": ROOT / "evals" / "real-repos" / "leju-let-platform" / "run.py",
        "scenarios": ["LET1-dept-isolation-consistency"],
        "results": ROOT / "evals" / "real-repos" / "leju-let-platform" / "results",
    },
]
ARMS = [
    ("no-skill", ["--no-plugin"]),
    ("build", ["--skills", "dv-build"]),
    ("build-test", ["--skills", "dv-build,dv-test"]),
    ("build-test-review", ["--skills", "dv-build,dv-test,dv-review"]),
    ("chain", ["--chain"]),
]


def java_home() -> str:
    for key in ("JAVA17_HOME", "JAVA_HOME"):
        value = os.environ.get(key)
        if value and (Path(value) / "bin/java").is_file():
            return value
    try:
        return subprocess.check_output(
            ["/usr/libexec/java_home", "-v", "17"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return ""


def command(task: dict, arm: str, model: str, runs: int, timeout: int) -> list[str]:
    cmd = [
        sys.executable,
        str(task["runner"]),
        "--runs",
        str(runs),
        "--timeout",
        str(timeout),
        "--model",
        model,
        "--arm",
        f"matrix-{model}-{arm}",
    ]
    for scenario in task["scenarios"]:
        cmd.extend(["--scenario", scenario])
    cmd.extend(dict(ARMS)[arm])
    return cmd


def run_cell(task: dict, arm: str, model: str, runs: int, timeout: int,
             env: dict) -> tuple[str, str, str, int, str]:
    log_dir = ROOT / "evals" / "matrix-logs" / model / arm
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{task['name']}.log"
    cmd = command(task, arm, model, runs, timeout)
    with log_path.open("w", encoding="utf-8") as log:
        log.write("$ " + " ".join(cmd) + "\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    print(f"{model}/{arm}/{task['name']}: exit={proc.returncode} log={log_path}", flush=True)
    return model, arm, task["name"], proc.returncode, str(log_path)


def result_dirs() -> list[Path]:
    dirs: list[Path] = []
    for task in TASKS:
        if not task["results"].is_dir():
            continue
        for path in task["results"].iterdir():
            meta = path / "meta.json"
            if not meta.is_file() or not (path / "summary.json").is_file():
                continue
            try:
                arm = json.loads(meta.read_text(encoding="utf-8")).get("arm", "")
            except json.JSONDecodeError:
                continue
            if arm.startswith("matrix-"):
                dirs.append(path)
    return dirs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--models", default="fable,sonnet")
    parser.add_argument("--arms", default=",".join(name for name, _ in ARMS))
    parser.add_argument("--tasks", default=",".join(task["name"] for task in TASKS))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    models = [item.strip() for item in args.models.split(",") if item.strip()]
    arms = [item.strip() for item in args.arms.split(",") if item.strip()]
    tasks = [task for task in TASKS if task["name"] in set(args.tasks.split(","))]
    unknown = set(arms) - {name for name, _ in ARMS}
    if unknown:
        parser.error(f"unknown arm(s): {sorted(unknown)}")
    env = os.environ.copy()
    home = java_home()
    if home:
        env["JAVA_HOME"] = home
        env["PATH"] = str(Path(home) / "bin") + os.pathsep + env.get("PATH", "")
    cells = [(task, arm, model) for model in models for arm in arms for task in tasks]
    if args.dry_run:
        for task, arm, model in cells:
            print(" ".join(command(task, arm, model, args.runs, args.timeout)))
        return 0
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    results = []
    if not args.report_only:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [
                pool.submit(run_cell, task, arm, model, args.runs, args.timeout, env)
                for task, arm, model in cells
            ]
            results = [future.result() for future in as_completed(futures)]
    failures = [item for item in results if item[3] != 0]
    dirs = result_dirs()
    rows = compare.aggregate(compare.load_runs([str(path) for path in dirs]))
    report = [
        "# Cross-repo ablation matrix",
        "",
        f"- started: {started}",
        f"- models: {', '.join(models)}",
        f"- arms: {', '.join(arms)}",
        f"- tasks: {', '.join(task['name'] for task in tasks)}",
        f"- runs per cell: {args.runs}",
        f"- runner failures: {len(failures)}",
        "",
        compare.render(rows),
    ]
    if failures:
        report.extend(["", "## Runner failures", ""])
        for model, arm, task, code, log in sorted(failures):
            report.append(f"- {model}/{arm}/{task}: exit {code} ({log})")
    out = ROOT / "evals" / "matrix-report.md"
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    print(f"\nwrote {out}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
