#!/usr/bin/env python3
"""Run evaluation scenarios against a temporary clone of leju-robot-ota.

The source checkout is only read by git clone/checkout. The agent works in the
clone; hidden tests are copied in after the run and removed again. No commit,
push, deploy or dependency installation is performed.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD_EVAL = ROOT / "evals" / "build-scenarios"
HIDDEN = HERE / "hidden"
RESULTS = HERE / "results"
SCENARIOS = HERE / "scenarios.json"

sys.path.insert(0, str(BUILD_EVAL))
_SPEC = importlib.util.spec_from_file_location(
    "build_scenarios_run", BUILD_EVAL / "run.py"
)
build_run = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(build_run)


def load_scenarios() -> dict:
    return json.loads(SCENARIOS.read_text(encoding="utf-8"))


def prepare_repo(source: Path, rev: str) -> tuple[Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix="devkit-ota-eval-"))
    dest = tmp / "repo"
    subprocess.run(
        ["git", "clone", "--quiet", "--no-hardlinks", "--no-checkout", str(source), str(dest)],
        check=True,
        timeout=120,
    )
    subprocess.run(
        ["git", "-C", str(dest), "checkout", "--quiet", "--detach", rev],
        check=True,
        timeout=120,
    )
    return tmp, dest


def expand(command: list[str], dest: Path) -> list[str]:
    return [
        item.replace("{repo}", str(dest)).replace("{hidden}", str(HIDDEN))
        for item in command
    ]


def run_command(spec: dict, dest: Path) -> tuple[bool, str]:
    cwd = dest / spec.get("cwd", ".")
    try:
        proc = subprocess.run(
            expand(spec["command"], dest),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=int(spec.get("timeout", 180)),
        )
        return proc.returncode == 0, (proc.stdout + proc.stderr)[-2000:]
    except subprocess.TimeoutExpired:
        return False, f"timeout after {spec.get('timeout', 180)}s"
    except OSError as exc:
        return False, f"{type(exc).__name__}: {exc}"


def run_checks(
    scenario: dict,
    text: str,
    diff: str,
    changed_files: list[str],
    before_hashes: dict[str, str],
    dest: Path,
) -> list[dict]:
    results: list[dict] = []
    haystack = f"{text}\n{diff}"
    for spec in scenario.get("checks", []):
        kind = spec["type"]
        if kind == "manifest_unchanged":
            paths = spec["paths"]
            after = build_run.hash_manifests(dest, paths)
            changed = [p for p in paths if before_hashes.get(p) != after.get(p)]
            results.append(
                build_run.check(
                    f"{kind}:{paths}",
                    not changed,
                    f"changed: {changed}" if changed else "",
                )
            )
        elif kind == "changed_files_max":
            limit = int(spec["value"])
            results.append(
                build_run.check(
                    f"{kind}:{limit}",
                    len(changed_files) <= limit,
                    f"changed files: {len(changed_files)} {changed_files}",
                )
            )
        elif kind == "changed_files_prefix":
            prefixes = spec["prefixes"]
            outside = [
                path
                for path in changed_files
                if not any(path.startswith(prefix) for prefix in prefixes)
            ]
            results.append(
                build_run.check(
                    f"{kind}:{prefixes}",
                    not outside,
                    f"outside scope: {outside}" if outside else "",
                )
            )
        elif kind == "response_or_diff_contains":
            pattern = spec["pattern"]
            results.append(
                build_run.check(
                    f"{kind}:{pattern}",
                    re.search(pattern, haystack, re.IGNORECASE) is not None,
                )
            )
        elif kind == "command":
            ok, detail = run_command(spec, dest)
            results.append(build_run.check(f"{kind}:{spec['command']}", ok, detail))
        elif kind == "hidden_files":
            copied: list[Path] = []
            try:
                for item in spec["files"]:
                    source = HIDDEN / item["source"]
                    target = dest / item["target"]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
                    copied.append(target)
                ok, detail = run_command(spec, dest)
            finally:
                for target in copied:
                    target.unlink(missing_ok=True)
            results.append(
                build_run.check(f"{kind}:{spec['files']}", ok, detail)
            )
        else:
            results.append(
                build_run.check(f"{kind}:unknown", False, "unknown check type")
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--arm", default="baseline")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--base-rev")
    parser.add_argument("--explicit-skill", action="store_true")
    parser.add_argument("--chain", action="store_true")
    parser.add_argument("--skills", default="", help="comma-separated ablation skills")
    parser.add_argument("--no-plugin", action="store_true")
    parser.add_argument("--model", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    arm_flags = [args.no_plugin, args.explicit_skill, args.chain, bool(args.skills)]
    if sum(bool(flag) for flag in arm_flags) > 1:
        print(
            "choose only one of --no-plugin, --explicit-skill, --chain, --skills",
            file=sys.stderr,
        )
        return 2

    data = load_scenarios()
    source = args.source or Path(os.environ.get("LEJU_OTA_SOURCE", data["source"]))
    base_rev = args.base_rev or data["base_rev"]
    scenarios = data["scenarios"]
    if args.scenario:
        wanted = set(args.scenario)
        scenarios = [s for s in scenarios if s["id"] in wanted]
        missing = wanted - {s["id"] for s in scenarios}
        if missing:
            print(f"unknown scenario(s): {sorted(missing)}", file=sys.stderr)
            return 2
    if not (source / ".git").exists():
        print(f"not a git checkout: {source}", file=sys.stderr)
        return 2

    if args.dry_run:
        for scenario in scenarios:
            print(f"{scenario['id']} ({scenario['permission']})")
            print(f"  {scenario['prompt']}")
        print(f"source: {source}")
        print(f"base_rev: {base_rev}")
        return 0

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_root = RESULTS / f"{timestamp}-{args.arm}"
    out_root.mkdir(parents=True, exist_ok=True)
    host_version = subprocess.run(
        ["claude", "--version"], capture_output=True, text=True
    ).stdout.strip()
    meta = {
        "arm": args.arm,
        "timestamp": timestamp,
        "host": "claude-code",
        "host_version": host_version,
        "model_arg": args.model,
        "source": str(source),
        "base_rev": base_rev,
        "runs_per_scenario": args.runs,
        "explicit_skill": args.explicit_skill,
        "chain": args.chain,
        "skills_arg": args.skills,
        "no_plugin": args.no_plugin,
        "hooks_disabled": True,
        "scenarios_file_sha256": build_run.sha256(SCENARIOS),
    }
    (out_root / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    summary: list[dict] = []
    for scenario in scenarios:
        for run_index in range(1, args.runs + 1):
            print(f"== {scenario['id']} run {run_index}/{args.runs}", flush=True)
            record = {
                "scenario": scenario["id"],
                "run": run_index,
                "expected_skills": scenario.get("expected_skills", []),
                "error": None,
            }
            tmp = None
            try:
                tmp, dest = prepare_repo(source, base_rev)
                before = build_run.hash_manifests(
                    dest,
                    [
                        path
                        for spec in scenario.get("checks", [])
                        if spec["type"] == "manifest_unchanged"
                        for path in spec["paths"]
                    ],
                )
                sent_prompt = scenario["prompt"]
                if args.skills:
                    sent_prompt = (
                        f"请依次使用 {args.skills} 技能完成以下任务：\n\n"
                        f"{sent_prompt}"
                    )
                elif args.chain:
                    sent_prompt = (
                        "请根据 dv Skill(s) 链路执行：先用 dv-route 规划，"
                        "再用 dv-build 实现、dv-test 验证、dv-review 评审、"
                        "dv-done 收口。用户已确认按此计划连续执行，"
                        "不要停在计划确认；不要 commit 或 push。\n\n"
                        f"{sent_prompt}"
                    )
                elif args.explicit_skill:
                    skill = (scenario.get("expected_skills") or ["dv-build"])[0]
                    sent_prompt = f"请使用 {skill} 技能完成以下任务：\n\n{sent_prompt}"
                started = datetime.now(timezone.utc)
                proc = build_run.run_claude(
                    sent_prompt,
                    dest,
                    scenario["permission"],
                    args.timeout,
                    no_plugin=args.no_plugin,
                    model=args.model,
                    host="claude",
                )
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                response, tool_calls, usage, models = build_run.parse_stream(proc.stdout)
                skill_invocations = [
                    call["input"] for call in tool_calls if call["name"] == "Skill"
                ]
                diff, changed_files = build_run.collect_diff(dest)
                checks = run_checks(
                    scenario, response, diff, changed_files, before, dest
                )
                record.update(
                    {
                        "duration_s": round(elapsed, 1),
                        "exit_code": proc.returncode,
                        "response_chars": len(response),
                        "tool_calls": len(tool_calls),
                        "tool_names": sorted({c["name"] for c in tool_calls}),
                        "changed_files": changed_files,
                        "checks": checks,
                        "checks_passed": sum(1 for c in checks if c["pass"]),
                        "checks_total": len(checks),
                        "skill_invocations": skill_invocations,
                        "usage": usage,
                        "models": list(models.keys()),
                    }
                )
                build_run.write_run(
                    out_root / scenario["id"] / f"run-{run_index}",
                    sent_prompt,
                    response,
                    proc.stdout,
                    proc.stderr,
                    diff,
                    changed_files,
                    checks,
                    None,
                    skill_invocations,
                )
                print(
                    f"   checks {record['checks_passed']}/{record['checks_total']}"
                    f", files {len(changed_files)}, tools {len(tool_calls)}"
                    f", skills {len(skill_invocations)}, {record['duration_s']}s",
                    flush=True,
                )
            except Exception as exc:
                record["error"] = f"{type(exc).__name__}: {exc}"
                print(f"   ERROR: {record['error']}", file=sys.stderr, flush=True)
            finally:
                if tmp is not None:
                    shutil.rmtree(tmp, ignore_errors=True)
            summary.append(record)

    (out_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        f"# OTA real-repo run {timestamp} ({args.arm})",
        "",
        f"- host: {meta['host']} {meta['host_version']}",
        f"- source: {meta['source']} @ {meta['base_rev']}",
        "",
        "| scenario | checks | skills | files | tools | seconds | error |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for record in summary:
        lines.append(
            "| {scenario} | {passed}/{total} | {skills} | {files} | {tools} | {seconds} | {error} |".format(
                scenario=record.get("scenario"),
                passed=record.get("checks_passed", 0),
                total=record.get("checks_total", 0),
                skills=len(record.get("skill_invocations", [])),
                files=len(record.get("changed_files", [])),
                tools=record.get("tool_calls", 0),
                seconds=record.get("duration_s", "-"),
                error=record.get("error") or "",
            )
        )
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
