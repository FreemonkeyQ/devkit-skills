#!/usr/bin/env python3
"""Create and drive a deterministic devkit run with a shared context and gates."""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from devkit_context import load_adapter  # noqa: E402

PLAN_SCHEMA = ROOT / ".devkit" / "plan.schema.json"
CONTEXT_SCHEMA = ROOT / ".devkit" / "context.schema.json"
ACCEPTANCE_SCHEMA = ROOT / ".devkit" / "acceptance.schema.json"

HIGH_RISK = re.compile(
    r"安全|security|迁移|migration|schema|数据库|并发|concurrency|权限|auth|"
    r"发布|deploy|删除|force|支付|计费|审计",
    re.IGNORECASE,
)
TRIVIAL = re.compile(r"文案|typo|注释|配置|重命名|rename", re.IGNORECASE)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:32] or "run"


def resolve_run(root: Path, name: str) -> Path:
    path = Path(name)
    if path.is_absolute():
        return path
    if str(path).startswith(".devkit"):
        return root / path
    return root / ".devkit" / "runs" / path


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate(data: dict, schema_path: Path) -> None:
    jsonschema.validate(data, json.loads(schema_path.read_text(encoding="utf-8")))


def choose_risk(goal: str, scope: list[str], requested: str) -> str:
    if requested != "auto":
        return requested
    if len(scope) > 4 or HIGH_RISK.search(goal):
        return "high"
    if len(scope) <= 1 and TRIVIAL.search(goal):
        return "trivial"
    return "standard"


def steps_for(risk: str, endpoint: str, adapter: dict) -> list[dict]:
    required = [gate["id"] for gate in adapter["gates"] if gate["required"]]
    test_gates = [gate["id"] for gate in adapter["gates"] if gate["required"] and gate["kind"] == "test"]
    if risk == "trivial":
        plan = [
            {"skill": "dv-build", "status": "pending", "gates": [], "evidence": [], "note": "快速路径"},
            {"skill": "dv-done", "status": "pending", "gates": [], "evidence": [], "note": "快速路径，只做针对性验证"},
        ]
    else:
        plan = [
            {"skill": "dv-build", "status": "pending", "gates": [], "evidence": [], "note": ""},
            {"skill": "dv-test", "status": "pending", "gates": test_gates, "evidence": [], "note": ""},
            {"skill": "dv-review", "status": "pending", "gates": [], "evidence": [], "note": "含验收闭合"},
            {"skill": "dv-done", "status": "pending", "gates": required, "evidence": [], "note": ""},
        ]
    if endpoint in ("commit", "push"):
        plan.append({"skill": "dv-commit", "status": "pending", "gates": [], "evidence": [], "note": ""})
    if endpoint == "push":
        plan.append({"skill": "dv-push", "status": "pending", "gates": [], "evidence": [], "note": ""})
    return plan


def ensure_runs_excluded(root: Path) -> None:
    """Keep run artifacts out of Git without changing a tracked .gitignore."""
    git_dir = root / ".git"
    if git_dir.is_file():
        text = git_dir.read_text(encoding="utf-8").strip()
        if text.startswith("gitdir:"):
            git_dir = (root / text.split(":", 1)[1].strip()).resolve()
    if not git_dir.is_dir():
        return
    exclude = git_dir / "info" / "exclude"
    line = ".devkit/runs/"
    existing = exclude.read_text(encoding="utf-8") if exclude.is_file() else ""
    if line in existing.splitlines():
        return
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(f"{line}\n")


def init_run(args) -> int:
    root = args.root.resolve()
    adapter = load_adapter(root)
    ensure_runs_excluded(root)
    scope = [
        part.strip()
        for item in (args.scope or [])
        for part in item.split(",")
        if part.strip()
    ]
    risk = choose_risk(args.goal, scope, args.risk)
    endpoint = args.endpoint
    run_id = args.run_id or f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slug(args.goal)}"
    directory = resolve_run(root, run_id)
    if directory.exists() and not args.force:
        print(f"{directory} exists; pass --force to replace")
        return 2
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "evidence").mkdir(exist_ok=True)
    plan = {
        "version": 1,
        "run_id": run_id,
        "goal": args.goal,
        "risk": risk,
        "endpoint": endpoint,
        "scope": scope or ["."],
        "authorization": {
            "businessCode": True,
            "tests": True,
            "docs": risk != "trivial",
            "commit": endpoint in ("commit", "push"),
            "push": endpoint == "push",
            "deploy": False,
        },
        "gates": [gate["id"] for gate in adapter["gates"] if gate["required"]],
        "gate_results": {},
        "steps": steps_for(risk, endpoint, adapter),
        "state": "running",
        "createdAt": now(),
        "updatedAt": now(),
    }
    context = {
        "version": 1,
        "run_id": run_id,
        "goal": args.goal,
        "scope_files": scope,
        "reused": [],
        "decisions": [],
        "evidence": [],
        "updatedAt": now(),
    }
    acceptance = {
        "version": 1,
        "run_id": run_id,
        "items": [{"requirement": args.goal, "status": "pending", "evidence": ""}],
        "updatedAt": now(),
    }
    validate(plan, PLAN_SCHEMA)
    validate(context, CONTEXT_SCHEMA)
    validate(acceptance, ACCEPTANCE_SCHEMA)
    write_json(directory / "plan.json", plan)
    write_json(directory / "context.json", context)
    write_json(directory / "acceptance.json", acceptance)
    (directory / "report.md").write_text(
        f"# {args.goal}\n\n- run: `{run_id}`\n- risk: `{risk}`\n- endpoint: `{endpoint}`\n"
        f"- scope: {', '.join(plan['scope'])}\n- gates: {', '.join(plan['gates']) or 'none'}\n",
        encoding="utf-8",
    )
    print(directory)
    return 0


def load_run(root: Path, name: str) -> tuple[Path, dict, dict, dict]:
    directory = resolve_run(root, name)
    plan = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
    context = json.loads((directory / "context.json").read_text(encoding="utf-8"))
    acceptance = json.loads((directory / "acceptance.json").read_text(encoding="utf-8"))
    validate(plan, PLAN_SCHEMA)
    validate(context, CONTEXT_SCHEMA)
    validate(acceptance, ACCEPTANCE_SCHEMA)
    return directory, plan, context, acceptance


def next_step(plan: dict) -> dict | None:
    for step in plan["steps"]:
        if step["status"] == "pending":
            return step
    return None


def skill_prompt(directory: Path, plan: dict, step: dict) -> str:
    gates = ", ".join(step.get("gates") or []) or "none"
    return (
        f"请使用 {step['skill']} 技能继续当前 devkit 运行。\n\n"
        f"目标：{plan['goal']}\n"
        f"风险：{plan['risk']}；终点：{plan['endpoint']}\n"
        f"范围：{', '.join(plan['scope'])}\n"
        f"本步骤门禁：{gates}\n"
        f"计划：{directory / 'plan.json'}\n"
        f"上下文：{directory / 'context.json'}\n"
        f"验收矩阵：{directory / 'acceptance.json'}\n\n"
        "先读这三个文件，不重复已完成侦察；只做本步骤授权内的事。"
        "完成后调用：\n"
        f"python3 {ROOT / 'scripts/devkit_run.py'} --root {directory.parents[2]} "
        f"--run {directory.name} record --skill {step['skill']} --status pass "
        "--evidence \"<命令/结果/证据路径>\"\n"
        "若失败或命中停车闸门，用 --status blocked。不要自行 commit/push，"
        "除非 plan.authorization 明确允许且本步骤是 dv-commit/dv-push。"
    )


def record_step(directory: Path, plan: dict, context: dict, acceptance: dict,
                skill: str, status: str, evidence: str, notes: list[str],
                accepts: list[str]) -> int:
    step = next((item for item in plan["steps"] if item["skill"] == skill), None)
    if step is None:
        print(f"unknown step: {skill}")
        return 2
    # Gates may have been recorded after this caller loaded the plan.
    on_disk = json.loads((directory / "plan.json").read_text(encoding="utf-8"))
    plan["gate_results"] = on_disk.get("gate_results", plan.get("gate_results", {}))
    step["status"] = status
    if evidence:
        step["evidence"].append(evidence)
    context["evidence"].append({"skill": skill, "kind": status, "detail": evidence, "at": now()})
    for item in notes:
        context["decisions"].append(item)
    for raw in accepts:
        parts = raw.split("|")
        if len(parts) < 2:
            print(f"invalid --accept: {raw} (use requirement|evidence[|status])")
            return 2
        requirement = parts[0]
        existing = next(
            (item for item in acceptance["items"] if item["requirement"] == requirement),
            None,
        )
        item = {
            "requirement": requirement,
            "evidence": parts[1],
            "status": parts[2] if len(parts) > 2 else "pass",
        }
        if existing is not None:
            existing.update(item)
        else:
            acceptance["items"].append(item)
    if status == "pass" and step.get("gates"):
        missing_step_gates = [
            gate for gate in step["gates"]
            if plan.get("gate_results", {}).get(gate, {}).get("status") != "pass"
        ]
        if missing_step_gates:
            step["status"] = "blocked"
            plan["state"] = "blocked"
            print("step blocked; missing gates: " + ", ".join(missing_step_gates))
            write_json(directory / "plan.json", plan)
            write_json(directory / "context.json", context)
            write_json(directory / "acceptance.json", acceptance)
            return 1
    if skill == "dv-done" and status == "pass":
        required = list(step.get("gates", []))
        missing = [gate for gate in required if plan.get("gate_results", {}).get(gate, {}).get("status") != "pass"]
        pending = [item["requirement"] for item in acceptance["items"] if item["status"] in ("pending", "fail")]
        if missing or pending:
            step["status"] = "blocked"
            plan["state"] = "blocked"
            print("done blocked")
            if missing:
                print("  missing gates: " + ", ".join(missing))
            if pending:
                print("  pending acceptance: " + "; ".join(pending))
            write_json(directory / "plan.json", plan)
            write_json(directory / "context.json", context)
            write_json(directory / "acceptance.json", acceptance)
            return 1
    if status in ("fail", "blocked"):
        plan["state"] = "blocked"
    elif all(item["status"] in ("pass", "skipped") for item in plan["steps"]):
        plan["state"] = "complete"
    plan["updatedAt"] = now()
    context["updatedAt"] = now()
    acceptance["updatedAt"] = now()
    write_json(directory / "plan.json", plan)
    write_json(directory / "context.json", context)
    write_json(directory / "acceptance.json", acceptance)
    print(f"{skill}: {step['status']} ({plan['state']})")
    return 0


def note_context(directory: Path, context: dict, skill: str, kind: str, detail: str) -> int:
    context["evidence"].append({"skill": skill, "kind": kind, "detail": detail, "at": now()})
    context["updatedAt"] = now()
    write_json(directory / "context.json", context)
    print(f"{skill}: noted {kind}")
    return 0


def status(directory: Path, plan: dict, acceptance: dict) -> None:
    print(f"run {plan['run_id']} state={plan['state']} risk={plan['risk']} endpoint={plan['endpoint']}")
    for step in plan["steps"]:
        print(f"  {step['skill']:<12} {step['status']}")
    print("gates:")
    for gate in plan.get("gates", []):
        result = plan.get("gate_results", {}).get(gate, {})
        print(f"  {gate:<12} {result.get('status', 'missing')}")
    print("acceptance:")
    for item in acceptance["items"]:
        print(f"  [{item['status']}] {item['requirement']} :: {item['evidence'] or '-'}")


def drive(root: Path, name: str, command: str, max_steps: int, dry_run: bool) -> int:
    directory, plan, context, acceptance = load_run(root, name)
    for _ in range(max_steps):
        step = next_step(plan)
        if step is None:
            print(f"run {plan['run_id']} has no pending steps (state={plan['state']})")
            return 0 if plan["state"] == "complete" else 1
        prompt = skill_prompt(directory, plan, step)
        env = {
            **os.environ,
            "DEVKIT_PROMPT": prompt,
            "DEVKIT_SKILL": step["skill"],
            "DEVKIT_RUN": str(directory),
            "DEVKIT_ROOT": str(root),
        }
        if dry_run:
            print(f"[{step['skill']}] {command}")
            print(prompt)
            return 0
        proc = subprocess.run(command, cwd=root, shell=True, env=env)
        evidence = f"driver: {command} exit {proc.returncode}"
        # The host process may have updated acceptance/plan/context.
        directory, plan, context, acceptance = load_run(root, name)
        code = record_step(
            directory, plan, context, acceptance, step["skill"],
            "pass" if proc.returncode == 0 else "blocked", evidence, [], [],
        )
        if code != 0 or proc.returncode != 0:
            return 1
    print(f"stopped after {max_steps} steps")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--run")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--goal", required=True)
    init.add_argument("--risk", choices=["auto", "trivial", "standard", "high"], default="auto")
    init.add_argument("--endpoint", choices=["done", "commit", "push"], default="done")
    init.add_argument("--scope", action="append", default=[])
    init.add_argument("--run-id")
    init.add_argument("--force", action="store_true")
    sub.add_parser("next")
    sub.add_parser("status")
    note = sub.add_parser("note")
    note.add_argument("--skill", required=True)
    note.add_argument("--kind", default="note")
    note.add_argument("--detail", required=True)
    record = sub.add_parser("record")
    record.add_argument("--skill", required=True)
    record.add_argument("--status", choices=["pass", "fail", "blocked"], required=True)
    record.add_argument("--evidence", default="")
    record.add_argument("--note", action="append", default=[])
    record.add_argument("--accept", action="append", default=[])
    drive_parser = sub.add_parser("drive")
    drive_parser.add_argument(
        "--command",
        dest="host_command",
        default='claude -p "$DEVKIT_PROMPT" --permission-mode acceptEdits',
    )
    drive_parser.add_argument("--max-steps", type=int, default=20)
    drive_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "init":
        return init_run(args)
    if not args.run:
        parser.error("--run is required for this command")
    directory, plan, context, acceptance = load_run(root, args.run)
    if args.command == "next":
        step = next_step(plan)
        if step is None:
            print(json.dumps({"done": True, "state": plan["state"]}, ensure_ascii=False))
            return 0
        print(json.dumps({
            "skill": step["skill"],
            "gates": step.get("gates", []),
            "prompt": skill_prompt(directory, plan, step),
            "plan": str(directory / "plan.json"),
        }, ensure_ascii=False, indent=2))
        return 0
    if args.command == "status":
        status(directory, plan, acceptance)
        return 0
    if args.command == "note":
        return note_context(directory, context, args.skill, args.kind, args.detail)
    if args.command == "record":
        return record_step(
            directory, plan, context, acceptance, args.skill, args.status,
            args.evidence, args.note, args.accept,
        )
    if args.command == "drive":
        return drive(root, args.run, args.host_command, args.max_steps, args.dry_run)
    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
