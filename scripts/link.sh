#!/usr/bin/env bash
# Local Claude/Qoder links; no remote or global config mutations.
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/link.py" "$@"
