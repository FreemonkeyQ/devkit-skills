#!/usr/bin/env python3
"""估算技能元数据的常驻 token 成本。

两种口径：
  desc   —— Claude Code 等端只把 name + description 放进上下文（保守估 3 字符/token）
  full   —— 部分端会加载完整 frontmatter（含 metadata）
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"


def split(text: str) -> tuple[int, int]:
    if not text.startswith("---\n"):
        return 0, 0
    end = text.find("\n---\n", 4)
    if end < 0:
        return 0, 0
    raw = text[4:end]
    full = len(raw)
    m = re.search(r"^description:\s*(.*)$", raw, re.M)
    desc = len(m.group(1)) if m else 0
    m2 = re.search(r"^name:\s*(.*)$", raw, re.M)
    desc += len(m2.group(1)) if m2 else 0
    return desc, full


def main() -> int:
    rows = []
    tot_d = tot_f = 0
    for p in sorted(SKILLS.iterdir()):
        sm = p / "SKILL.md"
        if not sm.is_file():
            continue
        d, f = split(sm.read_text(encoding="utf-8"))
        rows.append((round(d / 3), round(f / 3), p.name))
        tot_d += round(d / 3)
        tot_f += round(f / 3)
    rows.sort(reverse=True)
    print(f"{'skill':<16}{'desc tok':>10}{'full tok':>10}")
    for d, f, name in rows:
        print(f"{name:<16}{d:>10}{f:>10}")
    print(f"{'TOTAL':<16}{tot_d:>10}{tot_f:>10}")
    print(f"\n常驻约 {tot_d} token（仅描述）；最坏 {tot_f} token（完整 frontmatter）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
