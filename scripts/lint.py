#!/usr/bin/env python3
"""devkit-skills 结构校验。12 条规则，任一失败退出码 1。"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
L0 = {"dv-route", "dv-research", "dv-debug", "dv-review"}  # 允许模型自动触发
MAX_DESC = 200
MAX_BODY = 120

errors: list[str] = []
warnings: list[str] = []


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    data: dict = {}
    cur_key = None
    cur_indent = 0
    for line in raw.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = re.match(r"^(\s*)([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not m:
            continue
        indent, key, val = len(m.group(1)), m.group(2), m.group(3).strip()
        if indent == 0:
            cur_key, cur_indent = key, 0
            if val == "":
                data[key] = {}
            else:
                data[key] = val.strip('"').strip("'")
        elif cur_key:
            if isinstance(data.get(cur_key), dict):
                if val.startswith("[") and val.endswith("]"):
                    items = [x.strip().strip('"').strip("'") for x in val[1:-1].split(",") if x.strip()]
                    data[cur_key][key] = items
                else:
                    data[cur_key][key] = val.strip('"').strip("'")
    return data, body


def check() -> None:
    if not SKILLS.is_dir():
        errors.append("[1] skills/ 目录不存在")
        return

    entries = sorted(p for p in SKILLS.iterdir() if p.is_dir())
    names = {p.name for p in entries}

    for p in entries:
        skill_md = p / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"[1] {p.name}/ 缺少 SKILL.md")
            continue
        rel = skill_md.relative_to(SKILLS)
        if len(rel.parts) != 2:
            errors.append(f"[1] 技能必须一层平铺：{rel}")

    next_map: dict[str, list[str]] = {}

    for p in entries:
        skill_md = p / "SKILL.md"
        if not skill_md.exists():
            continue
        name = p.name
        text = skill_md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        meta = fm.get("metadata") or {}

        # 2 / 3
        if fm.get("name") != name:
            errors.append(f"[2] {name}: name 字段({fm.get('name')}) 与目录名不一致")
        if not name.startswith("dv-") or not re.fullmatch(r"dv-[a-z0-9]+(-[a-z0-9]+)*", name):
            errors.append(f"[3] {name}: 必须以 dv- 开头且全小写连字符")

        # 4 / 5
        desc = str(fm.get("description") or "")
        if len(desc) > MAX_DESC:
            errors.append(f"[4] {name}: description {len(desc)} 字，超过 {MAX_DESC}")
        if re.search(r"(先|然后|接着|步骤\s*\d|step\s*\d|first,|then,)", desc, re.I):
            errors.append(f"[5] {name}: description 含流程描述词")

        # 6 / 7
        if name not in L0:
            if fm.get("disable-model-invocation") != "true":
                errors.append(f"[6] {name}: L2 技能缺少 disable-model-invocation: true")
            if fm.get("user-invocable") != "true":
                errors.append(f"[6] {name}: L2 技能缺少 user-invocable: true")
            oy = p / "agents" / "openai.yaml"
            if not oy.exists():
                errors.append(f"[7] {name}: L2 技能缺少 agents/openai.yaml")
            elif "allow_implicit_invocation: false" not in oy.read_text(encoding="utf-8"):
                errors.append(f"[7] {name}: openai.yaml 未设置 allow_implicit_invocation: false")

        # 8
        for k in ("stage", "edits-code", "next"):
            if k not in meta:
                errors.append(f"[8] {name}: metadata 缺少 {k}")
        stage = str(meta.get("stage") or "")
        if stage and stage not in {"meta", "discover", "build", "verify", "ship"}:
            errors.append(f"[8] {name}: stage 非法值 {stage}")
        ec = str(meta.get("edits-code") or "")
        if ec and ec not in {"true", "false"}:
            errors.append(f"[8] {name}: edits-code 必须是 true/false")

        # 9
        nxt = meta.get("next")
        if isinstance(nxt, list):
            next_map[name] = nxt
            for t in nxt:
                if t not in names:
                    errors.append(f"[9] {name}: next 指向不存在的技能 {t}")
            if not nxt and stage != "ship" and stage != "meta":
                errors.append(f"[9] {name}: 非终点技能 next 不得为空")

        # 11
        lines = [l for l in body.strip().splitlines() if l.strip()]
        if len(lines) > MAX_BODY:
            errors.append(f"[11] {name}: 正文 {len(lines)} 行，超过 {MAX_BODY}")

        # 12
        for kw in ("不适用", "反合理化"):
            if kw not in body:
                errors.append(f"[12] {name}: 正文缺少「{kw}」小节")

    # 10 环检测
    color: dict[str, int] = {}

    def dfs(n: str, stack: list[str]) -> None:
        color[n] = 1
        for t in next_map.get(n, []):
            if color.get(t) == 1:
                cyc = " → ".join(stack + [n, t])
                if not ({"dv-plan", "dv-build"} <= {n, t}):
                    errors.append(f"[10] next 图存在环：{cyc}")
            elif color.get(t, 0) == 0:
                dfs(t, stack + [n])
        color[n] = 2

    for n in next_map:
        if color.get(n, 0) == 0:
            dfs(n, [])

    # 12b 互斥句（仅对易混技能）
    for name in ("dv-route", "dv-help"):
        p = SKILLS / name / "SKILL.md"
        if p.exists():
            body = p.read_text(encoding="utf-8")
            other = "/dv-help" if name == "dv-route" else "/dv-route"
            if other not in body:
                errors.append(f"[12] {name}: 缺少指向 {other} 的互斥句")

    # 13 dv-help 首屏里的数字与名单必须与实际一致
    help_md = SKILLS / "dv-help" / "SKILL.md"
    if help_md.exists():
        body = help_md.read_text(encoding="utf-8")
        total = len(names)
        for m in re.finditer(r"(\d+)\s*个技能", body):
            if int(m.group(1)) != total:
                errors.append(
                    f"[13] dv-help: 首屏写「{m.group(1)} 个技能」，实际 {total} 个"
                )
        l0_m = re.search(r"自己会来（([^）]*)）", body)
        if l0_m:
            listed = {x.strip() for x in l0_m.group(1).split("/") if x.strip()}
            expect = {n.replace("dv-", "") for n in L0}
            if listed != expect:
                errors.append(
                    f"[13] dv-help: 自动触发名单 {sorted(listed)} 与 L0 {sorted(expect)} 不一致"
                )
        for m in re.finditer(r"其余\s*(\d+)\s*个", body):
            rest = int(m.group(1))
            if rest != total - 3:
                errors.append(
                    f"[13] dv-help: 写「其余 {rest} 个」，应为总数 {total} − 入口 3 = {total - 3}"
                )
            seasonal = re.search(r"(\d+)\s*个季节型", body)
            if seasonal:
                s = int(seasonal.group(1))
                if rest != len(listed) + s:
                    errors.append(
                        f"[13] dv-help: 其余 {rest} ≠ 自动 {len(listed)} + 季节 {s}"
                    )
                if s != total - 3 - len(L0):
                    errors.append(
                        f"[13] dv-help: 季节型写 {s} 个，应为 {total - 3 - len(L0)} 个"
                    )


def main() -> int:
    check()
    if warnings:
        for w in warnings:
            print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"\n{len(errors)} errors, {len(warnings)} warnings, {len(list(SKILLS.glob('*/SKILL.md')))} skills")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
