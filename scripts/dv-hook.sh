#!/usr/bin/env bash
# Optional UserPromptSubmit adapter; no global registration is performed.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/dv-hook.py" 2>/dev/null || true
