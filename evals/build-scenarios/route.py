#!/usr/bin/env python3
"""Lexical trigger-routing check for devkit skill descriptions.

This is a deterministic approximation: token-overlap TF-IDF over the 19
description strings. It cannot judge semantics. It only answers two questions:

1. Does a positive build prompt rank its expected skill top-1?
2. Does a negative prompt avoid pulling dv-build in?

Run: python3 evals/build-scenarios/route.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from lexical import catalog, cosine, fit_tfidf, tokenize  # noqa: E402


def main() -> int:
    data = json.loads((HERE / "scenarios.json").read_text(encoding="utf-8"))
    entries = list(catalog(ROOT))
    skills = []
    descriptions = []
    for path, name, description in entries:
        skills.append(name or path.parent.name)
        descriptions.append(description or "")

    positives = [
        {"id": scenario["id"], "prompt": scenario["prompt"],
         "expected": scenario["expected_skills"]}
        for scenario in data["scenarios"]
    ]
    negatives = data["negative_routes"]

    docs = [tokenize(text) for text in descriptions]
    query_docs = [tokenize(item["prompt"]) for item in positives + negatives]
    vectors = fit_tfidf(docs + query_docs)
    skill_vectors = vectors[: len(docs)]
    query_vectors = vectors[len(docs) :]

    def rank(query_vec):
        scored = [(name, cosine(query_vec, vec)) for name, vec in zip(skills, skill_vectors)]
        return sorted(scored, key=lambda item: (-item[1], item[0]))

    positive_rows = []
    for item, query_vec in zip(positives, query_vectors[: len(positives)]):
        ranked = rank(query_vec)
        names = [name for name, _ in ranked]
        expected = item["expected"]
        top1 = names[0]
        top2 = names[:2]
        positive_rows.append(
            {
                "id": item["id"],
                "expected": expected,
                "top1": top1,
                "top3": names[:3],
                "top1_ok": top1 in expected,
                "top2_ok": any(name in expected for name in top2),
                "scores": {name: round(score, 4) for name, score in ranked[:3]},
            }
        )

    negative_rows = []
    for item, query_vec in zip(negatives, query_vectors[len(positives):]):
        ranked = rank(query_vec)
        names = [name for name, _ in ranked]
        negative_rows.append(
            {
                "prompt": item["prompt"],
                "expected": item["skill"],
                "top1": names[0],
                "top3": names[:3],
                "top1_ok": names[0] == item["skill"],
                "build_leaked": names[0] == "dv-build",
            }
        )

    positive_top1 = sum(1 for row in positive_rows if row["top1_ok"])
    positive_top2 = sum(1 for row in positive_rows if row["top2_ok"])
    negative_top1 = sum(1 for row in negative_rows if row["top1_ok"])
    build_leaks = sum(1 for row in negative_rows if row["build_leaked"])

    result = {
        "skills": skills,
        "positive": {
            "total": len(positive_rows),
            "top1_ok": positive_top1,
            "top2_ok": positive_top2,
            "rows": positive_rows,
        },
        "negative": {
            "total": len(negative_rows),
            "top1_ok": negative_top1,
            "build_leaked": build_leaks,
            "rows": negative_rows,
        },
    }

    print("POSITIVE (expected skill in top-1 / top-2)")
    for row in positive_rows:
        mark = "PASS" if row["top1_ok"] else ("TOP2" if row["top2_ok"] else "FAIL")
        print(
            f"  {mark:4} {row['id']:<28} expected={row['expected']} "
            f"top3={row['top3']}"
        )
    print(
        f"  => top-1 {positive_top1}/{len(positive_rows)}, "
        f"top-2 {positive_top2}/{len(positive_rows)}"
    )

    print("NEGATIVE (expected skill must be top-1; dv-build must not leak)")
    for row in negative_rows:
        mark = "PASS" if row["top1_ok"] else "FAIL"
        print(
            f"  {mark:4} {row['prompt']:<20} expected={row['expected']} "
            f"top3={row['top3']}"
        )
    print(
        f"  => top-1 {negative_top1}/{len(negative_rows)}, "
        f"dv-build leaked {build_leaks}/{len(negative_rows)}"
    )

    out = HERE / "results" / "routing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
