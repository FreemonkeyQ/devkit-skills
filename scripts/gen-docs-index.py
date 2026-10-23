#!/usr/bin/env python3
"""Generate docs/INDEX.md from configured artifact dirs. --check never writes."""
import argparse
import re
import sys
from pathlib import Path

from config import load_config

LABELS = [
    ('specs', '规格'),
    ('changes', '变更提案'),
    ('issues', '工单'),
    ('adr', '决策'),
    ('research', '调研'),
    ('reviews', '评审'),
    ('audits', '审计'),
    ('design', '设计'),
]
STATUS_LINE = re.compile(r'^\s*-?\s*状态[:：]\s*(.+?)\s*$', re.M)
H1 = re.compile(r'^#\s+(.+?)\s*$', re.M)


def entries(base, kind):
    if not base.is_dir():
        return []
    if kind == 'specs':
        return sorted((p for p in base.iterdir()
                       if (p.is_dir() or p.suffix == '.md') and p.name != 'archive'),
                      key=lambda p: p.name)
    if kind == 'changes':
        return sorted((p for p in base.iterdir() if p.is_dir() and p.name != 'archive'),
                      key=lambda p: p.name)
    return sorted(base.glob('*.md'), key=lambda p: p.name)


def body(kind, path):
    if kind == 'specs' and path.is_dir():
        return path / 'spec.md'
    if kind == 'changes':
        return path / 'proposal.md'
    return path


def read(p):
    try:
        return p.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return ''


def build(project):
    project = Path(project).resolve()
    cfg = load_config(project)
    paths = cfg['paths']
    rows = ['# 研发产物索引', '',
            '> 由 scripts/gen-docs-index.py 生成，请勿手改。先读本索引，再按需打开具体文件。', '']
    total = 0
    for kind, label in LABELS:
        base = project / paths[kind]
        found = entries(base, kind)
        if not found:
            continue
        rows.append(f'## {label}（`{paths[kind]}`）')
        rows.append('')
        for entry in found:
            target = body(kind, entry)
            text = read(target)
            title = H1.search(text)
            status = STATUS_LINE.search(text[:1200])
            name = entry.name if kind != 'specs' or not entry.is_dir() else f'{entry.name}/'
            display = title.group(1) if title else name
            suffix = f' — {status.group(1)}' if status else ''
            rows.append(f'- [{display}]({target.relative_to(project).as_posix()}) `{name}`{suffix}')
            total += 1
        rows.append('')
    if not total:
        rows.append('_暂无产物。_')
        rows.append('')
    return '\n'.join(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', default='.')
    p.add_argument('--check', action='store_true')
    args = p.parse_args()
    project = Path(args.project).resolve()
    try:
        cfg = load_config(project)
    except Exception as exc:
        print('ERROR config invalid:', exc)
        return 1
    out = project / cfg['paths']['index']
    content = build(project)
    if args.check:
        if not out.is_file() or out.read_text(encoding='utf-8') != content:
            print('ERROR index drift; run scripts/gen-docs-index.py')
            return 1
        print('OK index matches artifacts')
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding='utf-8')
    print('Generated', out.relative_to(project))
    return 0


if __name__ == '__main__':
    sys.exit(main())
