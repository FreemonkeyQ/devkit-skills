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
import math
import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

ASCII_RE = re.compile(r"[a-z0-9_]+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def read_skill(path: Path) -> tuple[str, str]:
    """Read name/description without requiring PyYAML.

    Only the subset used by this repository is supported: a plain scalar or a
    single-quoted scalar continued over indented lines.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"missing frontmatter: {path}")
    end = next(i for i, line in enumerate(lines[1:], 1) if line.strip() == "---")
    name = ""
    description = ""
    i = 1
    while i < end:
        line = lines[i]
        if line.startswith("name:"):
            name = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("description:"):
            value = line.split(":", 1)[1].strip()
            if value[:1] in {"'", '"'}:
                quote = value[0]
                parts = [value[1:]]
                while not parts[-1].rstrip().endswith(quote) and i + 1 < end:
                    i += 1
                    parts.append(lines[i].strip())
                joined = " ".join(parts)
                description = joined.rstrip().rstrip(quote)
            else:
                description = value
        i += 1
    return name, description


def catalog(root: Path):
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        name, description = read_skill(path)
        yield path, name, description


def tokenize(text: str) -> list[str]:
    text = text.lower()
    tokens = ASCII_RE.findall(text)
    for run in CJK_RE.findall(text):
        tokens.extend(run)
        tokens.extend(run[i : i + 2] for i in range(len(run) - 1))
    return tokens


def fit_tfidf(docs: list[list[str]]) -> list[dict[str, float]]:
    tfs = [Counter(doc) for doc in docs]
    df: Counter[str] = Counter()
    for tf in tfs:
        df.update(tf.keys())
    n = len(docs)
    idf = {term: math.log((1 + n) / (1 + count)) + 1 for term, count in df.items()}
    vectors = []
    for tf, doc in zip(tfs, docs):
        if not doc:
            vectors.append({})
            continue
        vec = {term: (count / len(doc)) * idf[term] for term, count in tf.items()}
        norm = math.sqrt(sum(value * value for value in vec.values())) or 1.0
        vectors.append({term: value / norm for term, value in vec.items()})
    return vectors


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(term, 0.0) for term, value in left.items())


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
