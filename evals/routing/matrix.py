#!/usr/bin/env python3
"""Deterministic routing matrix over every devkit skill.

This is a lexical TF-IDF approximation, not a model or host run. It answers:
which skill ranks first for realistic prompts, where do adjacent skills
collide, and which negatives leak into the wrong skill. Real-host invocation
logs remain the authoritative evidence for triggering.

Run: python3 evals/routing/matrix.py
Check data only: python3 evals/routing/matrix.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "results"
SCENARIOS = HERE / "scenarios.json"
sys.path.insert(0, str(HERE.parent))

from lexical import catalog, cosine, fit_idf, tokenize, vectorize  # noqa: E402

TYPES = {"positive", "negative", "hard-negative"}


def load(root: Path = ROOT) -> tuple[dict, list[str], list[str]]:
    data = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    entries = list(catalog(root))
    skills = [name or path.parent.name for path, name, _ in entries]
    descriptions = [description for _, _, description in entries]
    return data, skills, descriptions


def validate(data: dict, skills: list[str]) -> list[str]:
    errors: list[str] = []
    if data.get("version") != 1:
        errors.append("version must be 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return errors + ["cases must be a non-empty list"]

    known = set(skills)
    ids = [case.get("id") for case in cases]
    prompts = [case.get("prompt") for case in cases]
    duplicates = {value for value, count in Counter(ids).items() if count > 1}
    if duplicates:
        errors.append(f"duplicate ids: {sorted(duplicates)}")
    duplicate_prompts = {
        value for value, count in Counter(prompts).items() if count > 1
    }
    if duplicate_prompts:
        errors.append(f"duplicate prompts: {sorted(duplicate_prompts)}")

    for case in cases:
        case_id = case.get("id", "<missing>")
        if not isinstance(case.get("id"), str) or not case["id"].strip():
            errors.append(f"{case_id}: id is required")
        if case.get("type") not in TYPES:
            errors.append(f"{case_id}: unknown type {case.get('type')!r}")
        prompt = case.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"{case_id}: prompt is required")
        want = case.get("want")
        if not isinstance(want, list) or not want:
            errors.append(f"{case_id}: want must be a non-empty list")
            continue
        unknown = [skill for skill in want if skill not in known]
        if unknown:
            errors.append(f"{case_id}: unknown skills in want {unknown}")
        primary = case.get("primary")
        if primary not in known:
            errors.append(f"{case_id}: primary {primary!r} is not a skill")
        elif primary not in want:
            errors.append(f"{case_id}: primary must be included in want")
        trap = case.get("trap")
        if trap is not None:
            if trap not in known:
                errors.append(f"{case_id}: unknown trap {trap!r}")
            elif trap in want:
                errors.append(f"{case_id}: trap must not be a wanted skill")

    positive_counts = Counter(
        case["primary"] for case in cases if case.get("type") == "positive"
    )
    for skill in skills:
        count = positive_counts.get(skill, 0)
        if count < 3:
            errors.append(f"{skill}: needs at least 3 positive prompts, found {count}")
    return errors


def rank(
    query: dict[str, float], skills: list[str], vectors: list[dict[str, float]]
) -> list[tuple[str, float]]:
    scored = [
        (name, cosine(query, vector)) for name, vector in zip(skills, vectors)
    ]
    return sorted(scored, key=lambda item: (-item[1], item[0]))


def evaluate(data: dict, skills: list[str], descriptions: list[str]) -> dict:
    docs = [tokenize(text) for text in descriptions]
    idf = fit_idf(docs)
    skill_vectors = [vectorize(doc, idf) for doc in docs]

    rows = []
    for case in data["cases"]:
        ranked = rank(vectorize(tokenize(case["prompt"]), idf), skills, skill_vectors)
        names = [name for name, _ in ranked]
        top1 = names[0]
        top3 = names[:3]
        trap = case.get("trap")
        rows.append(
            {
                "id": case["id"],
                "type": case["type"],
                "primary": case["primary"],
                "want": case["want"],
                "trap": trap,
                "prompt": case["prompt"],
                "top1": top1,
                "top3": top3,
                "top1_ok": top1 in case["want"],
                "top3_ok": any(name in case["want"] for name in top3),
                "trap_leaked_top1": trap is not None and top1 == trap,
                "trap_leaked_top3": trap is not None and trap in top3,
                "scores": {name: round(score, 4) for name, score in ranked[:3]},
            }
        )

    by_type = {}
    for kind in sorted(TYPES):
        subset = [row for row in rows if row["type"] == kind]
        by_type[kind] = {
            "total": len(subset),
            "top1_ok": sum(row["top1_ok"] for row in subset),
            "top3_ok": sum(row["top3_ok"] for row in subset),
            "trap_leaked_top1": sum(row["trap_leaked_top1"] for row in subset),
        }

    per_skill = {}
    for skill in skills:
        subset = [
            row
            for row in rows
            if row["type"] == "positive" and row["primary"] == skill
        ]
        per_skill[skill] = {
            "positives": len(subset),
            "top1_ok": sum(row["top1_ok"] for row in subset),
            "top3_ok": sum(row["top3_ok"] for row in subset),
            "misses": [
                {"id": row["id"], "top1": row["top1"], "top3": row["top3"]}
                for row in subset
                if not row["top1_ok"]
            ],
        }

    confusion = Counter(
        (row["primary"], row["top1"]) for row in rows if not row["top1_ok"]
    )
    build_leak = [
        row
        for row in rows
        if "dv-build" not in row["want"] and row["top1"] == "dv-build"
    ]
    trap_leaks = [row for row in rows if row["trap_leaked_top1"]]

    return {
        "scenarios_sha256": hashlib.sha256(SCENARIOS.read_bytes()).hexdigest(),
        "skills": skills,
        "overall": {
            "total": len(rows),
            "top1_ok": sum(row["top1_ok"] for row in rows),
            "top3_ok": sum(row["top3_ok"] for row in rows),
        },
        "by_type": by_type,
        "per_skill": per_skill,
        "confusion": [
            {"expected": expected, "predicted": predicted, "count": count}
            for (expected, predicted), count in confusion.most_common()
        ],
        "dv_build_leaks": [
            {"id": row["id"], "prompt": row["prompt"]} for row in build_leak
        ],
        "trap_leaks": [
            {
                "id": row["id"],
                "prompt": row["prompt"],
                "trap": row["trap"],
                "top3": row["top3"],
            }
            for row in trap_leaks
        ],
        "rows": rows,
    }


def render_markdown(result: dict) -> str:
    overall = result["overall"]
    total = overall["total"]
    lines = [
        "# Routing matrix (lexical baseline)",
        "",
        "Deterministic TF-IDF approximation over skill descriptions. "
        "Not a model or host run; use real invocation logs for authoritative evidence.",
        "",
        f"- scenarios sha256: `{result['scenarios_sha256']}`",
        f"- skills: {len(result['skills'])}; cases: {total}",
        f"- overall top-1: {overall['top1_ok']}/{total} "
        f"({overall['top1_ok'] / total:.1%}); "
        f"top-3: {overall['top3_ok']}/{total} "
        f"({overall['top3_ok'] / total:.1%})",
        "",
        "## By case type",
        "",
        "| type | cases | top-1 | top-3 | trap leaked top-1 |",
        "|---|---:|---:|---:|---:|",
    ]
    for kind, stats in result["by_type"].items():
        lines.append(
            f"| {kind} | {stats['total']} | {stats['top1_ok']} | "
            f"{stats['top3_ok']} | {stats['trap_leaked_top1']} |"
        )

    lines += [
        "",
        "## Per-skill positives",
        "",
        "| skill | prompts | top-1 | top-3 | misses |",
        "|---|---:|---:|---:|---|",
    ]
    for skill in result["skills"]:
        stats = result["per_skill"][skill]
        misses = ", ".join(row["id"] for row in stats["misses"]) or "-"
        lines.append(
            f"| {skill} | {stats['positives']} | {stats['top1_ok']} | "
            f"{stats['top3_ok']} | {misses} |"
        )

    lines += ["", "## Confusion pairs", "", "| expected | predicted | count |", "|---|---|---:|"]
    if result["confusion"]:
        for item in result["confusion"]:
            lines.append(
                f"| {item['expected']} | {item['predicted']} | {item['count']} |"
            )
    else:
        lines.append("| - | - | 0 |")

    lines += ["", "## Trap leaks (wrong skill ranked first)", ""]
    if result["trap_leaks"]:
        for item in result["trap_leaks"]:
            lines.append(
                f"- `{item['id']}`: {item['prompt']} -> {item['trap']} "
                f"(top3: {', '.join(item['top3'])})"
            )
    else:
        lines.append("- none")

    lines += ["", "## dv-build false positives", ""]
    if result["dv_build_leaks"]:
        for item in result["dv_build_leaks"]:
            lines.append(f"- `{item['id']}`: {item['prompt']}")
    else:
        lines.append("- none")

    lines += ["", "## All misses", "", "| id | type | expected | top-1 | top-3 |", "|---|---|---|---|---|"]
    for row in result["rows"]:
        if not row["top1_ok"]:
            lines.append(
                f"| {row['id']} | {row['type']} | {', '.join(row['want'])} | "
                f"{row['top1']} | {', '.join(row['top3'])} |"
            )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate data only")
    parser.add_argument(
        "--min-top1",
        type=float,
        default=None,
        help="fail when overall top-1 accuracy is below this fraction",
    )
    parser.add_argument("--json", type=Path, default=RESULTS / "routing-matrix.json")
    parser.add_argument("--md", type=Path, default=RESULTS / "routing-matrix.md")
    args = parser.parse_args()

    data, skills, descriptions = load()
    errors = validate(data, skills)
    if errors:
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        return 2
    if args.check:
        print(f"OK {len(data['cases'])} cases cover {len(skills)} skills")
        return 0

    result = evaluate(data, skills, descriptions)
    report = render_markdown(result)
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.md.write_text(report, encoding="utf-8")

    overall = result["overall"]
    print(report)
    print(f"wrote {args.json}")
    print(f"wrote {args.md}")
    if args.min_top1 is not None:
        ratio = overall["top1_ok"] / overall["total"]
        if ratio < args.min_top1:
            print(
                f"FAIL top-1 {ratio:.1%} below {args.min_top1:.1%}",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
