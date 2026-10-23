#!/usr/bin/env python3
"""Read-only doc contract check. Exit 1 = violations. Never rewrites files."""
import argparse
import json
import re
import sys
from pathlib import Path

from config import load_config

SLUG = r'[a-z0-9]+(?:-[a-z0-9]+)*'
DATE = r'\d{4}-\d{2}-\d{2}'

PATTERNS = {
    'specs': re.compile(rf'^(?:\d{{3}}-{SLUG}\.md|\d{{3}}-{SLUG})$'),
    'issues': re.compile(rf'^\d{{3}}-{SLUG}\.md$'),
    'adr': re.compile(rf'^\d{{4}}-{SLUG}\.md$'),
    'changes': re.compile(rf'^{DATE}-{SLUG}$'),
    'research': re.compile(rf'^{DATE}-{SLUG}\.md$'),
    'reviews': re.compile(rf'^{DATE}-{SLUG}\.md$'),
    'audits': re.compile(rf'^{DATE}-{SLUG}\.md$'),
    'design': re.compile(rf'^{SLUG}\.md$'),
}

STATUS = {
    'specs': re.compile(r'^(草稿|定稿|弃用)$'),
    'issues': re.compile(r'^(待实施|实施中|已验证|阻塞|已放弃)$'),
    'adr': re.compile(r'^(提议|采纳|弃用|被 \d{4} 取代)$'),
    'changes': re.compile(r'^(提案|已应用|已归档)$'),
}

SECTIONS = {
    'specs': ['背景与目标', '范围', '非目标', '用户故事', '实施决策', '测试决策', '未决与阻塞', '验收标准'],
    'issues': ['依据', '范围与非目标', '依赖', '交付', '验证', '证据'],
    'adr': ['背景', '选项', '决定', '后果', '确认方式', '相关'],
    'changes': ['动机', '范围', '非目标', '受影响规格', '验证与回滚'],
}

ID_FIELDS = {'specs': 3, 'issues': 3, 'adr': 4}
H2 = re.compile(r'^##\s+(.+?)\s*$', re.M)
STATUS_LINE = re.compile(r'^\s*-?\s*状态[:：]\s*(.+?)\s*$', re.M)
LINKED = re.compile(r'`([^`<>\n]+(?:\.md|/))`')
MD_LINK = re.compile(r'\]\(([^)\s]+)\)')


def read(p):
    try:
        return p.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return ''


def md_files(base, kind):
    if not base.is_dir():
        return []
    if kind == 'specs':
        return sorted(p for p in base.iterdir()
                      if (p.is_dir() or p.suffix == '.md') and p.name != 'archive')
    if kind == 'changes':
        return sorted(p for p in base.iterdir() if p.is_dir() and p.name != 'archive')
    return sorted(base.glob('*.md'))


def body_file(kind, path):
    if kind == 'specs' and path.is_dir():
        return path / 'spec.md'
    if kind == 'changes':
        return path / 'proposal.md'
    return path


def check(project):
    errors, warnings = [], []
    project = Path(project).resolve()
    try:
        cfg = load_config(project)
    except Exception as exc:
        return [f'C1 config invalid: {exc}'], []
    profile = cfg['docs']['profile']
    if profile == 'off':
        return [], ['profile=off: only C1 (path containment) enforced']
    paths = cfg['paths']

    seen = {}
    artifacts = {}
    for kind in PATTERNS:
        base = project / paths[kind]
        for entry in md_files(base, kind):
            rel = entry.relative_to(project).as_posix()
            if kind == 'changes' and entry.name == 'archive':
                continue
            if not PATTERNS[kind].match(entry.name):
                errors.append(f'C2 {rel}: name does not match {kind} pattern')
                continue
            artifacts.setdefault(kind, []).append(entry)
            target = body_file(kind, entry)
            if not target.is_file():
                errors.append(f'C2 {rel}: missing {target.name}')
                continue
            text = read(target)
            rel_body = target.relative_to(project).as_posix()

            if kind in ID_FIELDS:
                width = ID_FIELDS[kind]
                ident = entry.name[:width]
                key = (kind, ident)
                if key in seen:
                    errors.append(f'C3 {rel_body}: duplicate {kind} id {ident} (also {seen[key]})')
                else:
                    seen[key] = rel_body

            if kind in STATUS:
                match = STATUS_LINE.search(text[:1200])
                if not match:
                    errors.append(f'C4 {rel_body}: missing status line')
                elif not STATUS[kind].match(match.group(1)):
                    errors.append(f'C4 {rel_body}: status "{match.group(1)}" not in enum')

            if profile == 'strict':
                heads = [h.strip() for h in H2.findall(text)]
                for want in SECTIONS.get(kind, []):
                    if not any(want in h for h in heads):
                        errors.append(f'C5 {rel_body}: missing section {want}')

            for link in LINKED.findall(text):
                if link.startswith('/') or link.startswith('..'):
                    continue
                if any(token in link for token in ('NNN', 'NNNN', '<', '>', '*', 'YYYY')):
                    continue
                candidates = [target.parent / link, project / link]
                if not any(c.exists() for c in candidates):
                    errors.append(f'C6 {rel_body}: reference not found: {link}')

            if kind == 'adr':
                match = STATUS_LINE.search(text[:1200])
                if match:
                    sup = re.match(r'^被 (\d{4}) 取代$', match.group(1))
                    if sup and not any((project / paths['adr']).glob(f'{sup.group(1)}-*.md')):
                        errors.append(f'C7 {rel_body}: superseded by missing ADR {sup.group(1)}')

    index = project / paths['index']
    if artifacts:
        if not index.is_file():
            errors.append(f'C8 {paths["index"]}: missing index; run gen-docs-index.py')
        else:
            text = read(index)
            linked = set(MD_LINK.findall(text))
            for link in sorted(linked):
                if link.startswith(('http://', 'https://', '#', 'mailto:')):
                    continue
                if not (project / link).exists():
                    errors.append(f'C8 {paths["index"]}: stale link {link}')
            for kind, entries in artifacts.items():
                for entry in entries:
                    rel = entry.relative_to(project).as_posix()
                    if rel not in linked:
                        errors.append(f'C8 {paths["index"]}: missing {kind} entry {rel}')
    return errors, warnings


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', default='.')
    p.add_argument('--json', action='store_true')
    args = p.parse_args()
    errors, warnings = check(args.project)
    if args.json:
        print(json.dumps({'errors': errors, 'warnings': warnings}, ensure_ascii=False, indent=2))
    else:
        for e in errors:
            print('ERROR', e)
        for w in warnings:
            print('WARN', w)
        print(f'{len(errors)} errors, {len(warnings)} warnings')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
