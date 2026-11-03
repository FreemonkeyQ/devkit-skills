#!/usr/bin/env python3
"""Detect a repository's real test/lint/build gates into .devkit/project.json.

This is a read-only detector until --write is passed. It never installs tools or
runs the detected commands.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / ".devkit" / "project.schema.json"


def _add_gate(gates: list[dict], gate_id: str, kind: str, command: str,
              required: bool = True, timeout: int = 600) -> None:
    if not command or any(gate["id"] == gate_id for gate in gates):
        return
    gates.append({
        "id": gate_id,
        "kind": kind,
        "command": command,
        "required": required,
        "timeout": timeout,
    })


def _node_scripts(root: Path) -> dict[str, str]:
    path = root / "package.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    scripts = data.get("scripts") or {}
    return {key: value for key, value in scripts.items() if isinstance(value, str)}


def _hard_constraints(root: Path) -> list[str]:
    path = root / "AGENTS.md"
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    active = False
    items: list[str] = []
    for line in lines:
        if line.startswith("## "):
            active = "硬约束" in line
            continue
        if not active:
            continue
        match = re.match(r"^- \*\*(.+?)\*\*", line)
        if match:
            items.append(match.group(1).strip())
    return items[:20]


def detect(root: Path) -> dict:
    root = root.resolve()
    gates: list[dict] = []
    commands: dict[str, str] = {}
    languages: set[str] = set()

    if (root / "go.mod").is_file():
        languages.add("go")
        commands["test"] = "go test ./... -count=1"
        commands["lint"] = "go vet ./..."
        commands["build"] = "go build ./..."
        _add_gate(gates, "unit", "test", commands["test"])
        _add_gate(gates, "lint", "lint", commands["lint"])
        _add_gate(gates, "build", "build", commands["build"], required=False)

    scripts = _node_scripts(root)
    if scripts:
        languages.add("node")
        for key in ("test", "lint", "build"):
            if key in scripts:
                commands[key] = f"npm run {key}"
                _add_gate(gates, key, key, commands[key], required=key != "build")

    if (root / "pyproject.toml").is_file() or (root / "tests").is_dir():
        languages.add("python")
        if (root / "tests").is_dir():
            commands["test"] = "python3 -m unittest discover -s tests -v"
            _add_gate(gates, "unit", "test", commands["test"])
        if (root / "scripts/lint.py").is_file():
            commands["lint"] = "python3 scripts/lint.py"
            _add_gate(gates, "lint", "lint", commands["lint"])
        if (root / "scripts/dv-help-gen.py").is_file():
            _add_gate(gates, "help", "custom", "python3 scripts/dv-help-gen.py --check")
        if (root / "scripts/cost.py").is_file():
            _add_gate(gates, "cost", "custom", "python3 scripts/cost.py", required=False)

    if (root / "tools/check-manual.py").is_file():
        _add_gate(gates, "manual", "manual", "python3 tools/check-manual.py")
    if (root / "docs/check-docs.py").is_file():
        _add_gate(gates, "docs", "docs", "python3 docs/check-docs.py")
    elif (root / "scripts/check-docs.py").is_file():
        _add_gate(gates, "docs", "docs", "python3 scripts/check-docs.py")
    if (root / "tools/check-releases.py").is_file():
        _add_gate(gates, "release", "release", "python3 tools/check-releases.py")
    if (root / "tools/check-migration-ui.py").is_file():
        node_modules = (root / "web/node_modules").is_dir()
        _add_gate(
            gates,
            "i18n",
            "i18n",
            "python3 tools/check-migration-ui.py",
            required=node_modules,
        )

    rules = [name for name in ("AGENTS.md", "CLAUDE.md") if (root / name).is_file()]
    hints = [name for name in ("internal", "cmd", "web", "skills", "tests", "docs") if (root / name).is_dir()]
    return {
        "version": 1,
        "root": ".",
        "language": "mixed" if len(languages) > 1 else (next(iter(languages), "unknown")),
        "rulesFiles": rules,
        "scopeHints": hints,
        "invariants": _hard_constraints(root),
        "commands": commands,
        "gates": gates,
    }


def load_adapter(root: Path) -> dict:
    path = root / ".devkit" / "project.json"
    if not path.is_file():
        return detect(root)
    data = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(data, json.loads(SCHEMA.read_text(encoding="utf-8")))
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    adapter = detect(root)
    jsonschema.validate(adapter, json.loads(SCHEMA.read_text(encoding="utf-8")))
    if args.write:
        path = root / ".devkit" / "project.json"
        if path.exists() and not args.force:
            print(f"{path} exists; pass --force to refresh")
            return 2
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(adapter, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    if args.json:
        print(json.dumps(adapter, ensure_ascii=False, indent=2))
    else:
        print(f"language={adapter['language']} gates={[g['id'] for g in adapter['gates']]}")
        for gate in adapter["gates"]:
            state = "required" if gate["required"] else "optional"
            print(f"  {gate['id']} ({gate['kind']}, {state}): {gate['command']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
