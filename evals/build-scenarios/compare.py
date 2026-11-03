#!/usr/bin/env python3
"""Aggregate build-scenario runs. Read-only; never calls a model."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_runs(paths: list[str]) -> list[dict]:
    rows = []
    for raw in paths:
        root = Path(raw)
        summary = root / "summary.json"
        if not summary.is_file():
            raise SystemExit(f"missing {summary}")
        meta_path = root / "meta.json"
        arm = root.name
        if meta_path.is_file():
            arm = json.loads(meta_path.read_text(encoding="utf-8")).get("arm", arm)
        for record in json.loads(summary.read_text(encoding="utf-8")):
            record["arm"] = arm
            rows.append(record)
    return rows


def aggregate(rows: list[dict]) -> list[dict]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(row["arm"], row["scenario"])].append(row)
    result = []
    for (arm, scenario), items in sorted(groups.items()):
        runs = len(items)
        hidden = [
            check
            for item in items
            for check in item.get("checks", [])
            if check["check"].startswith(("hidden_tests:", "hidden_files:"))
        ]
        result.append(
            {
                "arm": arm,
                "scenario": scenario,
                "runs": runs,
                "task_pass": sum(
                    item.get("checks_total", 0) > 0
                    and not item.get("error")
                    and item.get("checks_passed", 0) == item.get("checks_total", 0)
                    for item in items
                ),
                "hidden_pass": sum(check["pass"] for check in hidden),
                "hidden_total": len(hidden),
                "avg_files": sum(len(item.get("changed_files", [])) for item in items) / runs,
                "avg_tools": sum(item.get("tool_calls", 0) for item in items) / runs,
                "avg_seconds": sum(item.get("duration_s", 0) for item in items) / runs,
                "avg_output_tokens": sum(
                    (item.get("usage") or {}).get("output_tokens", 0) for item in items
                )
                / runs,
                "skill_calls": sum(
                    len(item.get("skill_invocations", [])) for item in items
                ),
                "errors": sum(bool(item.get("error")) for item in items),
            }
        )
    return result


def render(rows: list[dict]) -> str:
    lines = [
        "| arm | scenario | runs | task pass | hidden | files | tools | seconds | out tokens | skill calls | errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {arm} | {scenario} | {runs} | {task_pass} | {hidden_pass}/{hidden_total} | "
            "{avg_files:.1f} | {avg_tools:.1f} | {avg_seconds:.1f} | "
            "{avg_output_tokens:.0f} | {skill_calls} | {errors} |".format(**row)
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arms", nargs="+", help="result directories")
    args = parser.parse_args()
    rows = aggregate(load_runs(args.arms))
    print(render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
