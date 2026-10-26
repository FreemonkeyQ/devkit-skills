"""Shared lexical helpers for deterministic routing approximations.

This cannot judge semantics. It only provides a reproducible baseline for
trigger routing; real-host invocation logs remain the authoritative evidence.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

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


def fit_idf(docs: list[list[str]]) -> dict[str, float]:
    df: Counter[str] = Counter()
    for doc in docs:
        df.update(set(doc))
    n = len(docs)
    return {term: math.log((1 + n) / (1 + count)) + 1 for term, count in df.items()}


def vectorize(doc: list[str], idf: dict[str, float]) -> dict[str, float]:
    if not doc:
        return {}
    fallback = max(idf.values(), default=1.0)
    tf = Counter(doc)
    vec = {
        term: (count / len(doc)) * idf.get(term, fallback)
        for term, count in tf.items()
    }
    norm = math.sqrt(sum(value * value for value in vec.values())) or 1.0
    return {term: value / norm for term, value in vec.items()}


def fit_tfidf(docs: list[list[str]]) -> list[dict[str, float]]:
    idf = fit_idf(docs)
    return [vectorize(doc, idf) for doc in docs]


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * right.get(term, 0.0) for term, value in left.items())
