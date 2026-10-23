#!/usr/bin/env python3
"""Read project config safely; paths cannot escape repo or follow external symlinks."""
import copy
import json
from pathlib import Path
import jsonschema

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATHS = {'specs':'.devkit/specs','issues':'.devkit/issues','status':'.devkit/STATUS.md',
                 'state':'.devkit/state.json','handoff':'.devkit/handoff','context':'CONTEXT.md',
                 'adr':'docs/adr','research':'docs/research','reviews':'docs/reviews',
                 'audits':'docs/audits','design':'docs/design','changes':'docs/changes',
                 'index':'docs/INDEX.md'}
DEFAULT_DOCS = {'profile':'light'}


def resolve_path(project, value):
    base = Path(project).resolve()
    if not isinstance(value,str) or not value or Path(value).is_absolute():
        raise ValueError('path must be nonempty and repo-relative')
    path = (base/value).resolve()
    if path == base or base not in path.parents:
        raise ValueError('path escapes repository or points to root')
    return path


def load_config(project):
    p = Path(project)/'.devkit/config.json'
    cfg = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'version':1}
    schema = json.loads((ROOT/'.devkit/config.schema.json').read_text(encoding='utf-8'))
    jsonschema.validate(cfg,schema)
    result = copy.deepcopy(cfg)
    result['paths'] = {**DEFAULT_PATHS, **cfg.get('paths',{})}
    result['docs'] = {**DEFAULT_DOCS, **cfg.get('docs',{})}
    for value in result['paths'].values(): resolve_path(project,value)
    return result


def load_state(project):
    cfg = load_config(project)
    path = resolve_path(project,cfg['paths']['state'])
    if not path.exists(): return None
    state = json.loads(path.read_text(encoding='utf-8'))
    schema = json.loads((ROOT/'.devkit/state.schema.json').read_text(encoding='utf-8'))
    jsonschema.validate(state,schema)
    return state
