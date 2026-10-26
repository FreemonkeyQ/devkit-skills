#!/usr/bin/env python3
"""Run build-skill scenarios against a headless Claude Code session.

The harness copies a fixture to a temporary directory, runs the prompt with the
current devkit plugin loaded from this repository, records the trace and diff,
then applies deterministic checks and an optional LLM judge.

It never edits skill sources or fixture directories. Results are written under
evals/build-scenarios/results/<UTC timestamp>/.
"""
from __future__ import annotations

import argparse
import hashlib
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
ROOT = HERE.parents[1]
FIXTURES = HERE / "fixtures"
RESULTS = HERE / "results"
SCENARIOS = HERE / "scenarios.json"

sys.path.insert(0, str(ROOT / "evals" / "routing"))
from host_matrix import QODER_STRIP_ENV, qoder_cli_binary  # noqa: E402


def load_scenarios():
    return json.loads(SCENARIOS.read_text(encoding="utf-8"))


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
    )


def prepare_fixture(name: str) -> tuple[Path, Path]:
    tmp = Path(tempfile.mkdtemp(prefix=f"devkit-eval-{name}-"))
    dest = tmp / "repo"
    shutil.copytree(FIXTURES / name, dest)
    git(dest, "init", "-q")
    git(dest, "add", "-A")
    git(
        dest,
        "-c",
        "user.email=eval@local",
        "-c",
        "user.name=eval",
        "commit",
        "-qm",
        "fixture baseline",
    )
    return tmp, dest


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hash_manifests(dest: Path, paths: list[str]) -> dict[str, str]:
    return {path: sha256(dest / path) for path in paths if (dest / path).is_file()}


def run_claude(
    prompt: str,
    cwd: Path,
    permission: str,
    timeout: int,
    no_plugin: bool = False,
    model: str | None = None,
    host: str = "claude",
) -> subprocess.CompletedProcess:
    allowed = ["Read", "Glob", "Grep"]
    if permission != "plan":
        allowed += ["Write", "Edit", "Bash"]
    if host == "qoder":
        qoder_permission = "dont_ask" if permission == "plan" else "accept_edits"
        cmd = [str(qoder_cli_binary())]
        if no_plugin:
            cmd.extend(["--tools", *[t for t in allowed if t != "Skill"]])
        else:
            cmd.extend(["--plugin-dir", str(ROOT), "--tools", "Skill", *allowed])
        cmd.extend([
            "--permission-mode",
            qoder_permission,
            "--output-format",
            "stream-json",
            "--input-format",
            "stream-json",
            "--strict-mcp-config",
            "--settings",
            '{"disableAllHooks": true}',
        ])
        if model:
            cmd.extend(["-m", model])
        env = {
            key: value
            for key, value in os.environ.items()
            if key not in QODER_STRIP_ENV
        }
        payload = json.dumps(
            {
                "type": "user",
                "message": {
                    "role": "user",
                    "content": [{"type": "text", "text": prompt}],
                },
            },
            ensure_ascii=False,
        ) + "\n"
        return subprocess.run(
            cmd,
            cwd=cwd,
            input=payload,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    cmd = ["claude", "-p", prompt]
    if no_plugin:
        cmd.append("--disable-slash-commands")
    else:
        cmd.extend(["--plugin-dir", str(ROOT)])
    cmd.extend([
        "--permission-mode",
        permission,
        "--output-format",
        "stream-json",
        "--verbose",
        "--allowedTools",
        *allowed,
        "--disallowedTools",
        "WebFetch",
        "WebSearch",
        "--strict-mcp-config",
        "--settings",
        '{"disableAllHooks": true}',
    ])
    if model:
        cmd.extend(["--model", model])
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def parse_stream(stdout: str) -> tuple[str, list[dict], dict, dict]:
    text_parts: list[str] = []
    tool_calls: list[dict] = []
    usage: dict = {}
    models: dict = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    tool_calls.append(
                        {"name": block.get("name"), "input": block.get("input")}
                    )
        elif event.get("type") == "result":
            if event.get("result"):
                text_parts.append(str(event["result"]))
            usage = event.get("usage") or {}
            models = event.get("modelUsage") or {}
    return "\n".join(text_parts).strip(), tool_calls, usage, models


def collect_diff(dest: Path) -> tuple[str, list[str]]:
    git(dest, "add", "-A")
    diff = git(dest, "diff", "--cached", "--binary").stdout
    names = [
        line
        for line in git(dest, "diff", "--cached", "--name-only").stdout.splitlines()
        if line.strip()
    ]
    return diff, names


def check(name: str, passed: bool, detail: str = "") -> dict:
    return {"check": name, "pass": bool(passed), "detail": detail}


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
        if kind == "response_or_diff_contains":
            pattern = spec["pattern"]
            ok = re.search(pattern, haystack, re.IGNORECASE) is not None
            results.append(check(f"{kind}:{pattern}", ok))
        elif kind == "response_contains_any":
            patterns = spec["patterns"]
            ok = any(re.search(p, text, re.IGNORECASE) for p in patterns)
            results.append(check(f"{kind}:{patterns}", ok))
        elif kind == "response_not_contains":
            pattern = spec["pattern"]
            ok = re.search(pattern, text, re.IGNORECASE) is None
            results.append(check(f"{kind}:{pattern}", ok))
        elif kind == "diff_contains":
            pattern = spec["pattern"]
            ok = re.search(pattern, diff, re.IGNORECASE) is not None
            results.append(check(f"{kind}:{pattern}", ok))
        elif kind == "diff_not_contains":
            pattern = spec["pattern"]
            ok = re.search(pattern, diff, re.IGNORECASE) is None
            results.append(check(f"{kind}:{pattern}", ok))
        elif kind == "manifest_unchanged":
            paths = spec["paths"]
            after = hash_manifests(dest, paths)
            changed = [p for p in paths if before_hashes.get(p) != after.get(p)]
            results.append(
                check(
                    f"{kind}:{paths}",
                    not changed,
                    f"changed: {changed}" if changed else "",
                )
            )
        elif kind == "changed_files_max":
            limit = int(spec["value"])
            ok = len(changed_files) <= limit
            results.append(
                check(
                    f"{kind}:{limit}",
                    ok,
                    f"changed files: {len(changed_files)} {changed_files}",
                )
            )
        elif kind == "no_unverified_perf_claim":
            claim = re.search(r"性能(?:提升|改善|优化了|快了)", text)
            hedge = re.search(
                r"未验证|未实测|没有实测|未测|EXPLAIN|基准|需要实测|无法验证",
                text,
                re.IGNORECASE,
            )
            ok = claim is None or hedge is not None
            results.append(
                check(
                    kind,
                    ok,
                    "unverified performance claim" if not ok else "",
                )
            )
        else:
            results.append(check(f"{kind}:unknown", False, "unknown check type"))
    return results


def judge(
    scenario: dict, text: str, diff: str, timeout: int
) -> dict:
    prompt = f"""你是独立的代码评审员。只根据下面材料判定，不要臆测。
场景期望：
{json.dumps(scenario.get("expectations", []), ensure_ascii=False, indent=2)}

助手回复：
{text}

代码差异（可能为空）：
{diff[:12000]}

输出严格 JSON：{{"pass": true 或 false, "failed": ["未满足项"], "reasons": ["依据"]}}
只输出 JSON，不要 Markdown 代码块。"""
    cmd = [
        "claude",
        "-p",
        prompt,
        "--permission-mode",
        "plan",
        "--output-format",
        "json",
        "--allowedTools",
        "Read",
        "--strict-mcp-config",
        "--settings",
        '{"disableAllHooks": true}',
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        payload = json.loads(proc.stdout)
        raw = str(payload.get("result", "")).strip()
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
        verdict = json.loads(raw)
        if not isinstance(verdict, dict) or "pass" not in verdict:
            raise ValueError("judge returned unexpected JSON")
        return {"pass": bool(verdict["pass"]), **verdict}
    except Exception as exc:  # judge failure is recorded, not hidden
        return {"pass": None, "error": f"{type(exc).__name__}: {exc}"}


def write_run(
    out_dir: Path,
    prompt: str,
    response: str,
    stdout: str,
    stderr: str,
    diff: str,
    changed_files: list[str],
    checks: list[dict],
    judge_result: dict | None,
    skill_invocations: list[dict],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (out_dir / "response.txt").write_text(response, encoding="utf-8")
    (out_dir / "stdout.jsonl").write_text(stdout, encoding="utf-8")
    (out_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
    (out_dir / "diff.patch").write_text(diff, encoding="utf-8")
    (out_dir / "changed-files.txt").write_text(
        "\n".join(changed_files), encoding="utf-8"
    )
    (out_dir / "skill-invocations.json").write_text(
        json.dumps(skill_invocations, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "checks.json").write_text(
        json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if judge_result is not None:
        (out_dir / "judge.json").write_text(
            json.dumps(judge_result, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=420)
    parser.add_argument("--judge", action="store_true")
    parser.add_argument("--arm", default="baseline")
    parser.add_argument(
        "--explicit-skill",
        action="store_true",
        help="prepend 'use <expected skill>' so the skill body is exercised",
    )
    parser.add_argument(
        "--no-plugin",
        action="store_true",
        help="do not load this plugin and disable all skills (baseline arm)",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--model",
        default=None,
        help="pass --model to the host CLI (alias or full id)",
    )
    parser.add_argument(
        "--host",
        choices=["claude", "qoder"],
        default="claude",
        help="host CLI to drive: claude (Claude Code) or qoder (Qoder CLI CN)",
    )
    args = parser.parse_args()
    if args.no_plugin and args.explicit_skill:
        print("--no-plugin conflicts with --explicit-skill", file=sys.stderr)
        return 2

    data = load_scenarios()
    scenarios = data["scenarios"]
    if args.scenario:
        wanted = set(args.scenario)
        scenarios = [s for s in scenarios if s["id"] in wanted]
        missing = wanted - {s["id"] for s in scenarios}
        if missing:
            print(f"unknown scenario(s): {sorted(missing)}", file=sys.stderr)
            return 2

    if args.dry_run:
        for scenario in scenarios:
            print(f"{scenario['id']} ({scenario['fixture']}, {scenario['permission']})")
            print(f"  {scenario['prompt']}")
        return 0

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_root = RESULTS / f"{timestamp}-{args.arm}"
    out_root.mkdir(parents=True, exist_ok=True)

    if args.host == "qoder":
        host_name = "qoder-cli-cn"
        host_version = qoder_cli_binary().name
    else:
        host_name = "claude-code"
        host_version = subprocess.run(
            ["claude", "--version"], capture_output=True, text=True
        ).stdout.strip()
    try:
        repo_rev = subprocess.run(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    except Exception:
        repo_rev = "unknown"
    meta = {
        "arm": args.arm,
        "timestamp": timestamp,
        "host": host_name,
        "host_version": host_version,
        "model_arg": args.model,
        "repo_rev": repo_rev,
        "plugin_dir": str(ROOT),
        "runs_per_scenario": args.runs,
        "judge": args.judge,
        "explicit_skill": args.explicit_skill,
        "no_plugin": args.no_plugin,
        "hooks_disabled": True,
        "scenarios_file_sha256": sha256(SCENARIOS),
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
                tmp, dest = prepare_fixture(scenario["fixture"])
                before = hash_manifests(
                    dest,
                    [
                        path
                        for spec in scenario.get("checks", [])
                        if spec["type"] == "manifest_unchanged"
                        for path in spec["paths"]
                    ],
                )
                started = datetime.now(timezone.utc)
                sent_prompt = scenario["prompt"]
                if args.explicit_skill:
                    skill = (scenario.get("expected_skills") or ["dv-build"])[0]
                    sent_prompt = f"请使用 {skill} 技能完成以下任务：\n\n{sent_prompt}"
                proc = run_claude(
                    sent_prompt,
                    dest,
                    scenario["permission"],
                    args.timeout,
                    no_plugin=args.no_plugin,
                    model=args.model,
                    host=args.host,
                )
                elapsed = (datetime.now(timezone.utc) - started).total_seconds()
                response, tool_calls, usage, models = parse_stream(proc.stdout)
                skill_invocations = [
                    call["input"] for call in tool_calls if call["name"] == "Skill"
                ]
                diff, changed_files = collect_diff(dest)
                checks = run_checks(
                    scenario, response, diff, changed_files, before, dest
                )
                judge_result = (
                    judge(scenario, response, diff, args.timeout)
                    if args.judge
                    else None
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
                        "judge": judge_result,
                        "usage": usage,
                        "models": list(models.keys()),
                    }
                )
                write_run(
                    out_root / scenario["id"] / f"run-{run_index}",
                    sent_prompt,
                    response,
                    proc.stdout,
                    proc.stderr,
                    diff,
                    changed_files,
                    checks,
                    judge_result,
                    skill_invocations,
                )
                print(
                    f"   checks {record['checks_passed']}/{record['checks_total']}"
                    f", files {len(changed_files)}, tools {len(tool_calls)}"
                    f", skills {len(skill_invocations)}"
                    f", {record['duration_s']}s"
                    + (
                        f", judge {judge_result.get('pass')}"
                        if judge_result is not None
                        else ""
                    ),
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
        f"# Build scenario run {timestamp} ({args.arm})",
        "",
        f"- host: {meta['host']} {meta['host_version']}",
        f"- repo: {meta['repo_rev']}",
        f"- runs per scenario: {args.runs}",
        "",
        "| scenario | checks | judge | skills | files | tools | seconds | error |",
        "|---|---:|---|---:|---:|---:|---:|---|",
    ]
    for record in summary:
        lines.append(
            "| {scenario} | {checks_passed}/{checks_total} | {judge} | {skills} | {files} | {tools} | {duration} | {error} |".format(
                scenario=record.get("scenario"),
                checks_passed=record.get("checks_passed", 0),
                checks_total=record.get("checks_total", 0),
                judge=(
                    record.get("judge", {}).get("pass")
                    if record.get("judge")
                    else "-"
                ),
                skills=len(record.get("skill_invocations", [])),
                files=len(record.get("changed_files", [])),
                tools=record.get("tool_calls", 0),
                duration=record.get("duration_s", "-"),
                error=record.get("error") or "",
            )
        )
    (out_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nwrote {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
