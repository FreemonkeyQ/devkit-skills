"""Shared, strict YAML reader; metadata describes capabilities, not permissions."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
EFFECTS = {'docs', 'prototype', 'tests', 'business-code'}
ACTIONS = {'commit', 'push'}


def frontmatter(text):
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != '---':
        raise ValueError('missing YAML frontmatter')
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == '---'), None)
    if end is None:
        raise ValueError('missing closing frontmatter')
    data = yaml.safe_load(''.join(lines[1:end]))
    if not isinstance(data, dict):
        raise ValueError('frontmatter must be an object')
    return data, ''.join(lines[end+1:])


def catalog(root=ROOT):
    return [(path, *frontmatter(path.read_text(encoding='utf-8')))
            for path in sorted((Path(root)/'skills').glob('*/SKILL.md'))]
