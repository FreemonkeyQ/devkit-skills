#!/usr/bin/env bash
# devkit · 状态注入 hook
# 事件：UserPromptSubmit
# 输出：一行状态提示（约 30 token），失败时静默不阻断。
set -uo pipefail

ROOT="${CLAUDE_PROJECT_DIR:-${QODER_PROJECT_DIR:-$PWD}}"
STATE="$ROOT/.devkit/state.json"

[ -f "$STATE" ] || exit 0

line=$(python3 - "$STATE" <<'PY' 2>/dev/null
import json, sys, datetime, os
p = sys.argv[1]
try:
    d = json.load(open(p))
except Exception:
    sys.exit(0)
stage = d.get("stage") or "idle"
if stage == "idle":
    sys.exit(0)
parts = [f"stage={stage}"]
if d.get("ticket"):
    parts.append(f"ticket={d['ticket']}")
if d.get("next"):
    parts.append(f"next={d['next']}")
since = d.get("since")
if since:
    try:
        t = datetime.datetime.fromisoformat(since)
        mins = int((datetime.datetime.now(t.tzinfo) - t).total_seconds() // 60)
        if mins >= 60:
            parts.append(f"({mins // 60}h前)")
        elif mins > 0:
            parts.append(f"({mins}m前)")
    except Exception:
        pass
print("[devkit] " + " ".join(parts))
PY
)

[ -n "${line:-}" ] && printf '%s\n' "$line"
exit 0
