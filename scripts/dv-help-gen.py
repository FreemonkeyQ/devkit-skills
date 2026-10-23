#!/usr/bin/env python3
"""Generate help from source metadata; --check never writes."""
import sys
from pathlib import Path
from skillmeta import ROOT, catalog

OUT = ROOT/'skills/dv-help/references/_generated.md'


def build(root=ROOT):
    records = catalog(root)
    rows = [f'<!-- GENERATED: scripts/dv-help-gen.py -->\n\n共 {len(records)} 个技能。自然语言可选技能，副作用由当次授权控制。\n',
            '| 技能 | 作用 | 能力范围 | 需明确意图的动作 | 可选关联 |',
            '|---|---|---|---|---|']
    for path, fm, body in records:
        m = fm['metadata']
        rows.append('| '+ ' | '.join([fm['name'],m['summary'], ', '.join(m['effects']) or '只读说明',
                                     ', '.join(m['explicit-actions']) or '依任务范围', ', '.join(m['next']) or '—'])+' |')
    return '\n'.join(rows)+'\n'


def main():
    content = build()
    if '--check' in sys.argv:
        if not OUT.is_file() or OUT.read_text(encoding='utf-8') != content:
            print('ERROR help drift; run scripts/dv-help-gen.py')
            return 1
        print('OK help matches source')
    else:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(content,encoding='utf-8')
        print('Generated', OUT.relative_to(ROOT))
    return 0

if __name__ == '__main__':
    sys.exit(main())
