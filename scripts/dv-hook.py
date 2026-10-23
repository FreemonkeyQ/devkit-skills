#!/usr/bin/env python3
"""Read-only recovery hint. Never treats state as authorization."""
import os
import sys
from pathlib import Path
from config import load_state


def hint(project):
    state = load_state(project)
    if not state or state['stage'] in ('idle','completed'): return ''
    parts = ['[devkit hint]', 'stage='+state['stage']]
    if state.get('ticket'): parts.append('ticket='+state['ticket'])
    if state['next']: parts.append('optional-next='+','.join(state['next']))
    parts.append('current request/repo evidence override this hint; no action authorization')
    return ' '.join(parts).replace('\n',' ').replace('\r',' ')


def main():
    project = os.environ.get('CLAUDE_PROJECT_DIR') or os.environ.get('QODER_PROJECT_DIR') or os.getcwd()
    try:
        line = hint(Path(project))
    except Exception:
        # Invalid config is not fabricated as a valid stage; do not block host prompt.
        line = ''
    if line: print(line)
    return 0

if __name__ == '__main__': sys.exit(main())
