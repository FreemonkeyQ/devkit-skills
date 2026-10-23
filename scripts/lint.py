#!/usr/bin/env python3
"""Validate source contracts, references and host metadata; not model behavior."""
import re
import sys
from pathlib import Path
import yaml
from skillmeta import ROOT, EFFECTS, ACTIONS, frontmatter


def check(root=ROOT):
    root = Path(root)
    errors, warnings = [], []
    files = sorted((root/'skills').rglob('SKILL.md'))
    records = []
    for path in files:
        name = path.parent.name
        if len(path.relative_to(root/'skills').parts) != 2:
            errors.append(f'{path}: skills must be flat')
        try:
            fm, body = frontmatter(path.read_text(encoding='utf-8'))
        except (ValueError, yaml.YAMLError) as exc:
            errors.append(f'{path}: invalid YAML: {exc}')
            continue
        records.append((name, fm))
        if fm.get('name') != name or not re.fullmatch(r'dv-[a-z0-9]+(?:-[a-z0-9]+)*', name):
            errors.append(f'{name}: invalid/mismatched name')
        desc = fm.get('description')
        if not isinstance(desc, str) or not desc.strip():
            errors.append(f'{name}: missing description')
        elif len(desc) > 200:
            warnings.append(f'{name}: description exceeds 200-character budget')
        if len(body.splitlines()) > 120:
            warnings.append(f'{name}: body exceeds 120-line budget')
        for word in ('适用', '不适用', '自检'):
            if word not in body:
                errors.append(f'{name}: missing {word}')
        meta = fm.get('metadata')
        if not isinstance(meta, dict):
            errors.append(f'{name}: metadata must be object')
            continue
        if meta.get('stage') not in {'meta', 'discover', 'build', 'verify', 'ship'}:
            errors.append(f'{name}: invalid stage')
        if not isinstance(meta.get('summary'), str) or not meta['summary']:
            errors.append(f'{name}: missing summary')
        for key, allowed in [('effects', EFFECTS), ('explicit-actions', ACTIONS)]:
            value = meta.get(key)
            if not isinstance(value, list) or any(v not in allowed for v in value):
                errors.append(f'{name}: invalid {key}')
        if not isinstance(meta.get('next'), list) or any(not isinstance(v,str) for v in meta['next']):
            errors.append(f'{name}: next must be list of skill names')
        oy = path.parent/'agents/openai.yaml'
        try:
            policy = yaml.safe_load(oy.read_text(encoding='utf-8'))
            if policy.get('policy', {}).get('allow_implicit_invocation') is not True:
                errors.append(f'{name}: Codex implicit invocation must match source policy')
        except (OSError, yaml.YAMLError, AttributeError):
            errors.append(f'{name}: invalid/missing Codex metadata')
        if fm.get('disable-model-invocation', False):
            errors.append(f'{name}: disabled invocation breaks natural-language composition')
        for ref in re.findall(r'references/[\w./-]+\.md', body):
            if not (path.parent/ref).is_file():
                errors.append(f'{name}: missing reference {ref}')
    names = {name for name,_ in records}
    for name, fm in records:
        nxt = fm.get('metadata', {}).get('next', [])
        if isinstance(nxt, list):
            for target in nxt:
                if isinstance(target, str) and target not in names:
                    errors.append(f'{name}: missing next target {target}')
    return errors, warnings


def main():
    errors, warnings = check()
    for e in errors: print('ERROR', e)
    for w in warnings: print('WARN', w)
    print(f'{len(errors)} errors, {len(warnings)} warnings')
    return bool(errors)

if __name__ == '__main__':
    sys.exit(main())
