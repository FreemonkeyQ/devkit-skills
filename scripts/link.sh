#!/usr/bin/env bash
# devkit · 多端链接脚本（幂等，只建符号链接，永不 copy）
#
#   ./scripts/link.sh --check    只报告差异
#   ./scripts/link.sh --apply    增删链接
#   ./scripts/link.sh --uninstall 移除本仓创建的所有链接
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="${1:---check}"

CLAUDE_DIR="$HOME/.claude/skills"
QODER_DIR="$HOME/.qoder-cn/skills"

say() { printf '%s\n' "$*"; }

link_one() {
  local src="$1" dst="$2"
  if [ -L "$dst" ]; then
    if [ "$(readlink "$dst")" = "$src" ]; then
      say "  ok      $(basename "$dst")"
      return 0
    fi
    say "  drift   $(basename "$dst") -> $(readlink "$dst")"
    [ "$MODE" = "--apply" ] && rm "$dst" && ln -s "$src" "$dst" && say "          relinked"
    return 0
  fi
  if [ -e "$dst" ]; then
    say "  skip    $(basename "$dst") (已存在非链接，未改动)"
    return 0
  fi
  say "  missing $(basename "$dst")"
  [ "$MODE" = "--apply" ] && ln -s "$src" "$dst" && say "          linked"
}

sync_dir() {
  local target="$1"
  [ -d "$target" ] || { say "  (目录不存在，跳过) $target"; return 0; }
  for d in "$ROOT"/skills/*/; do
    name="$(basename "$d")"
    link_one "${d%/}" "$target/$name"
  done
}

case "$MODE" in
  --check|--apply)
    say "Claude Code: $CLAUDE_DIR"
    sync_dir "$CLAUDE_DIR"
    say "Qoder CN: $QODER_DIR"
    sync_dir "$QODER_DIR"
    ;;
  --uninstall)
    for target in "$CLAUDE_DIR" "$QODER_DIR"; do
      [ -d "$target" ] || continue
      for d in "$ROOT"/skills/*/; do
        name="$(basename "$d")"
        if [ -L "$target/$name" ] && [ "$(readlink "$target/$name")" = "${d%/}" ]; then
          rm "$target/$name" && say "removed $target/$name"
        fi
      done
    done
    ;;
  *)
    say "用法: $0 [--check|--apply|--uninstall]"
    exit 2
    ;;
esac

say ""
say "提示：安装为插件时无需本脚本；本脚本用于本地开发与不装插件的场景。"
