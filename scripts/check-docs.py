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

PATTERN_HINT = {
    'specs': 'NNN-<slug>.md or NNN-<slug>/',
    'issues': 'NNN-<slug>.md',
    'adr': 'NNNN-<slug>.md',
    'changes': 'YYYY-MM-DD-<slug>/',
    'research': 'YYYY-MM-DD-<slug>.md',
    'reviews': 'YYYY-MM-DD-<slug>.md',
    'audits': 'YYYY-MM-DD-<slug>.md',
    'design': '<slug>.md',
}

SCHEMA = Path(__file__).with_name('docs.schema.json')
ID_FIELDS = {'specs': 3, 'issues': 3, 'adr': 4}
H2 = re.compile(r'^##\s+(.+?)\s*$')
STATUS_LINE = re.compile(r'^\s*-?\s*状态[:：]\s*(.+?)\s*$', re.M)
LINKED = re.compile(r'`([^`<>\n]+(?:\.md|/))`')
BACKTICK = re.compile(r'`([^`<>\n]+)`')
MD_LINK = re.compile(r'\]\(([^)\s]+)\)')
PLACEHOLDER = ('NNN', 'YYYY')


def schema():
    """Load scripts/docs.schema.json: the single source for enums and sections."""
    try:
        data = json.loads(SCHEMA.read_text(encoding='utf-8'))
        status, allowed = {}, {}
        for kind, spec in data['status'].items():
            values = list(spec['values'])
            pattern = [re.escape(v) for v in values]
            if spec.get('supersede'):
                values.append('被 NNNN 取代')
                pattern.append(r'被 \d{4} 取代')
            allowed[kind] = values
            status[kind] = re.compile('^(?:' + '|'.join(pattern) + ')$')
        return {
            'status': status,
            'allowed': allowed,
            'sections': data['sections'],
            'evidence': data['evidence']['sections'],
            'extensions': {e.lower() for e in data['evidence']['extensions']},
        }
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ValueError(f'cannot load {SCHEMA.name}: {exc}')


def h2_bodies(text):
    """Map each H2 heading to its body without compiling file-wide regexes."""
    result, current = [], None
    for line in text.splitlines():
        match = H2.match(line)
        if match:
            current = []
            result.append((match.group(1).strip(), current))
        elif current is not None:
            current.append(line)
    return [(heading, '\n'.join(lines)) for heading, lines in result]


def cited_paths(text, extensions):
    """Backticked repo-relative code/config paths; logs, globs and placeholders excluded."""
    for token in BACKTICK.findall(text):
        token = token.strip()
        if not token or ' ' in token or token.startswith(('/', '..')):
            continue
        if any(char in token for char in '<>*?`'):
            continue
        if any(mark in token for mark in PLACEHOLDER):
            continue
        path = re.sub(r'(?::\d+(?:-\d+)?)+$|#L\d+$', '', token)
        name = path.rsplit('/', 1)[-1]
        if '.' not in name:
            continue
        if name.rsplit('.', 1)[1].lower() not in extensions:
            continue
        yield path


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
    try:
        spec = schema()
    except ValueError as exc:
        return [f'C1 {exc}'], []
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
                errors.append(f'C2 {rel}: name does not match {kind} pattern (expected {PATTERN_HINT[kind]})')
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

            if kind in spec['status']:
                match = STATUS_LINE.search(text[:1200])
                if not match:
                    errors.append(f'C4 {rel_body}: missing status line (expected "- 状态：<value>")')
                elif not spec['status'][kind].match(match.group(1)):
                    allowed = ' | '.join(spec['allowed'][kind])
                    errors.append(f'C4 {rel_body}: status "{match.group(1)}" not in enum (allowed: {allowed})')

            sections = spec['sections'].get(kind, [])
            if profile == 'strict':
                heads = [heading for heading, _ in h2_bodies(text)]
                for want in sections:
                    if not any(want in h for h in heads):
                        errors.append(f'C5 {rel_body}: missing section {want} (required: {" / ".join(sections)})')

            for link in LINKED.findall(text):
                if link.startswith('/') or link.startswith('..'):
                    continue
                if any(token in link for token in ('NNN', 'NNNN', '<', '>', '*', 'YYYY')):
                    continue
                candidates = [target.parent / link, project / link]
                if not any(c.exists() for c in candidates):
                    errors.append(f'C6 {rel_body}: reference not found: {link} (checked relative to the document and the project root)')

            evidence_headings = spec['evidence'].get(kind, [])
            if evidence_headings:
                bodies = [body for heading, body in h2_bodies(text)
                          if any(want in heading for want in evidence_headings)]
                cited = set()
                for body in bodies:
                    for path in cited_paths(body, spec['extensions']):
                        if path in cited:
                            continue
                        cited.add(path)
                        if (target.parent / path).exists() or (project / path).exists():
                            continue
                        errors.append(f'C9 {rel_body}: evidence path not found: {path} '
                                      '(expected existing repo-relative code/config path; '
                                      'logs and external artifacts stay outside this check)')

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
