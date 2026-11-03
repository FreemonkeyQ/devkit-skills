#!/usr/bin/env python3
"""Install the /dv entry command into a host's user command directory.

Dry-run by default. --apply copies the command with a timestamped backup of any
existing file. It does not edit host settings or install plugins.
"""
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "commands" / "dv.md"
TARGETS = {
    "claude": Path(".claude") / "commands" / "dv.md",
    "qoder": Path(".qoder-cn") / "commands" / "dv.md",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=sorted(TARGETS), required=True)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    target = args.home / TARGETS[args.host]
    print(f"source: {SOURCE}")
    print(f"target: {target}")
    if not args.apply:
        print("dry-run; pass --apply to install")
        return 0
    if target.exists() and not args.force:
        print("target exists; pass --force to replace (a backup is kept)")
        return 2
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = target.with_name(f"{target.name}.bak-{stamp}")
        shutil.copy2(target, backup)
        print(f"backup: {backup}")
    text = SOURCE.read_text(encoding="utf-8").replace("{{DEVKIT_ROOT}}", str(ROOT)).replace("${CLAUDE_PLUGIN_ROOT}", str(ROOT))
    target.write_text(text, encoding="utf-8")
    print(f"installed: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
