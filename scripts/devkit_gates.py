#!/usr/bin/env python3
"""Run project gates and persist their evidence into a devkit run plan."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
sys_path = ROOT / "scripts"
import sys

sys.path.insert(0, str(sys_path))
from devkit_context import load_adapter  # noqa: E402

PLAN_SCHEMA = ROOT / ".devkit" / "plan.schema.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_dir(root: Path, name: str | None) -> Path | None:
    if not name:
        return None
    path = Path(name)
    if not path.is_absolute():
        path = root / ".devkit" / "runs" / name if not str(path).startswith(".devkit") else root / path
    return path


def read_plan(path: Path) -> dict:
    data = json.loads((path / "plan.json").read_text(encoding="utf-8"))
    jsonschema.validate(data, json.loads(PLAN_SCHEMA.read_text(encoding="utf-8")))
    return data


def write_plan(path: Path, plan: dict) -> None:
    plan["updatedAt"] = now()
    (path / "plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def run_gates(root: Path, adapter: dict, directory: Path | None,
              ids: set[str] | None = None, strict: bool = False) -> list[dict]:
    results = []
    evidence_dir = directory / "evidence" if directory else None
    if evidence_dir:
        evidence_dir.mkdir(parents=True, exist_ok=True)
    for gate in adapter["gates"]:
        if ids and gate["id"] not in ids:
            continue
        started = now()
        try:
            proc = subprocess.run(
                gate["command"],
                cwd=root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=int(gate.get("timeout", 600)),
            )
            output = (proc.stdout + proc.stderr)[-4000:]
            status = "pass" if proc.returncode == 0 else "fail"
            code = proc.returncode
        except subprocess.TimeoutExpired as exc:
            output = f"timeout after {gate.get('timeout', 600)}s: {exc}"
            status = "fail"
            code = None
        record = {
            "id": gate["id"],
            "kind": gate["kind"],
            "required": gate["required"],
            "status": status,
            "exit_code": code,
            "output": output,
            "at": started,
        }
        if evidence_dir:
            (evidence_dir / f"gate-{gate['id']}.log").write_text(
                output, encoding="utf-8"
            )
        results.append(record)
        print(
            f"{gate['id']}: {status}"
            f"{'' if gate['required'] else ' (optional)'}"
            f" exit={code}"
        )
    if directory:
        plan = read_plan(directory)
        plan.setdefault("gate_results", {})
        for result in results:
            plan["gate_results"][result["id"]] = {
                "status": result["status"],
                "exit_code": result["exit_code"],
                "log": f"evidence/gate-{result['id']}.log",
                "at": result["at"],
            }
        write_plan(directory, plan)
    return results


def check(root: Path, adapter: dict, directory: Path | None) -> list[str]:
    required = [gate["id"] for gate in adapter["gates"] if gate["required"]]
    results = {}
    if directory and (directory / "plan.json").is_file():
        results = read_plan(directory).get("gate_results", {})
    problems = []
    for gate_id in required:
        result = results.get(gate_id)
        if not result:
            problems.append(f"{gate_id}: no evidence")
        elif result.get("status") != "pass":
            problems.append(f"{gate_id}: {result.get('status')} exit={result.get('exit_code')}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--run", help="run id or .devkit/runs/<id> path")
    parser.add_argument("--gate", action="append", default=[], help="gate id (repeatable)")
    parser.add_argument("--strict", action="store_true", help="optional gate failures also fail")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run")
    sub.add_parser("check")
    sub.add_parser("list")
    args = parser.parse_args()
    root = args.root.resolve()
    adapter = load_adapter(root)
    directory = run_dir(root, args.run)
    if args.command == "list":
        print(json.dumps(adapter["gates"], ensure_ascii=False, indent=2))
        return 0
    if args.command == "check":
        problems = check(root, adapter, directory)
        if args.json:
            print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False))
        else:
            print("gates: ok" if not problems else "gates: FAIL")
            for problem in problems:
                print(f"  - {problem}")
        return 0 if not problems else 1
    ids = set(args.gate) or None
    results = run_gates(root, adapter, directory, ids=ids, strict=args.strict)
    failed = [
        result for result in results
        if result["status"] != "pass" and (result["required"] or args.strict)
    ]
    if args.json:
        print(json.dumps({"ok": not failed, "results": results}, ensure_ascii=False, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
