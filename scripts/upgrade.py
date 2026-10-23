#!/usr/bin/env python3
"""Upgrade devkit-skills in Claude Code and Qoder CN; verify content, backup before sync."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

PLUGIN = 'devkit-skills'
MARKET = 'devkit-skills'
PLUGIN_ID = 'devkit-skills@devkit-skills'
SKIP = {'.git', '__pycache__', '.DS_Store'}
PROBLEM = {
    'install_missing', 'marketplace_missing', 'downgrade_blocked', 'cli_missing',
    'marketplace_update_failed', 'plugin_update_failed', 'update_incomplete',
    'sync_failed', 'pull_failed', 'dirty', 'no_upstream', 'error',
}
NEEDS_ACTION = {'update_available', 'sync_needed', 'duplicate'} | PROBLEM


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def version_at(root, host):
    names = ['.claude-plugin/plugin.json'] if host == 'claude' else ['.qoder-plugin/plugin.json']
    for name in names + ['.claude-plugin/plugin.json', '.qoder-plugin/plugin.json']:
        data = load_json(Path(root) / name)
        if data and data.get('version'):
            return str(data['version'])
    return None


def version_tuple(value):
    parts = []
    for item in str(value or '').split('.'):
        match = re.match(r'\d+', item)
        parts.append(int(match.group()) if match else 0)
    return tuple(parts)


def compare_versions(left, right):
    a, b = version_tuple(left), version_tuple(right)
    return (a > b) - (a < b)


def tree_digest(root):
    digest = hashlib.sha256()
    for sub in ('skills', 'scripts'):
        base = Path(root) / sub
        if not base.is_dir():
            continue
        for path in sorted(base.rglob('*')):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(root)
            if any(part in SKIP for part in rel.parts):
                continue
            digest.update(rel.as_posix().encode())
            digest.update(b'\0')
            try:
                digest.update(path.read_bytes())
            except OSError:
                return 'unreadable'
    return digest.hexdigest()[:16]


def run(cmd, timeout, env=None):
    try:
        done = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return {'cmd': cmd, 'code': done.returncode, 'out': (done.stdout + done.stderr).strip()}
    except FileNotFoundError:
        return {'cmd': cmd, 'code': 127, 'out': 'command not found'}
    except subprocess.TimeoutExpired:
        return {'cmd': cmd, 'code': 124, 'out': f'timeout after {timeout}s'}


def host_root(host):
    if host == 'claude':
        return Path(os.environ.get('CLAUDE_CONFIG_DIR') or Path.home() / '.claude')
    return Path(os.environ.get('QODER_CONFIG_DIR') or Path.home() / '.qoder-cn')


def find_cli(host, root):
    if host == 'claude':
        override = os.environ.get('CLAUDE_CLI')
        if override:
            return override
        found = shutil.which('claude')
        if found:
            return found
        for path in (Path.home() / '.local/bin/claude', Path('/opt/homebrew/bin/claude'),
                     Path('/usr/local/bin/claude')):
            if path.is_file() and os.access(path, os.X_OK):
                return str(path)
        return None
    override = os.environ.get('QODERCLI')
    if override:
        return override
    found = shutil.which('qoderclicn')
    if found:
        return found
    folder = Path(root) / 'bin' / 'qoderclicn'
    version_file = folder / 'version.txt'
    if version_file.is_file():
        path = folder / f'qoderclicn-{version_file.read_text(encoding="utf-8").strip()}'
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    candidates = [p for p in folder.glob('qoderclicn-*')
                  if p.is_file() and os.access(p, os.X_OK)]
    return str(sorted(candidates, key=lambda p: version_tuple(p.name.split('-')[-1]))[-1]) if candidates else None


def registry_record(host, root):
    name = 'installed_plugins.json' if host == 'claude' else 'installed_plugins_v2.json'
    data = load_json(Path(root) / 'plugins' / name)
    entry = ((data or {}).get('plugins') or {}).get(PLUGIN_ID)
    if isinstance(entry, list):
        return entry[0] if entry else None
    return entry if isinstance(entry, dict) else None


def marketplace_root(root):
    return Path(root) / 'plugins' / 'marketplaces' / MARKET


def link_records(root):
    folder = Path(root) / 'skills'
    records = []
    if not folder.is_dir():
        return records
    for link in sorted(folder.glob('dv-*')):
        if not link.is_symlink():
            continue
        try:
            target = link.resolve()
        except OSError:
            continue
        records.append({'link': str(link), 'target': str(target),
                        'repo': str(target.parent.parent)})
    return records


def marketplace_update(host, root, cli, timeout):
    if host == 'claude':
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(root))
        return run([cli, 'plugin', 'marketplace', 'update', MARKET], timeout, env)
    return run([cli, '--config-dir', str(root), 'plugins', 'marketplace', 'update', MARKET], timeout)


def plugin_update(host, root, cli, timeout):
    if host == 'claude':
        env = dict(os.environ, CLAUDE_CONFIG_DIR=str(root))
        return run([cli, 'plugin', 'update', PLUGIN_ID, '--scope', 'user', '-y'], timeout, env)
    return run([cli, '--config-dir', str(root), 'plugins', 'update', PLUGIN_ID,
                '--scope', 'user'], timeout)


def atomic_copy_tree(source, target):
    source, target = Path(source), Path(target)
    for src in sorted(source.rglob('*')):
        rel = src.relative_to(source)
        if any(part in SKIP for part in rel.parts) or src.is_symlink():
            continue
        dst = target / rel
        if src.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            tmp = dst.with_name(dst.name + '.upgrade-tmp')
            shutil.copy2(src, tmp)
            os.replace(tmp, dst)
    src_skills, dst_skills = source / 'skills', target / 'skills'
    if src_skills.is_dir() and dst_skills.is_dir():
        wanted = {p.relative_to(src_skills) for p in src_skills.rglob('*') if p.is_file()}
        for path in sorted(dst_skills.rglob('*'), key=lambda p: len(p.parts), reverse=True):
            if path.is_file() and path.relative_to(dst_skills) not in wanted:
                try:
                    path.unlink()
                except OSError:
                    pass
            elif path.is_dir() and not any(path.iterdir()):
                try:
                    path.rmdir()
                except OSError:
                    pass


def backup_and_sync(source, target, root):
    source, target = Path(source), Path(target)
    if source.resolve() == target.resolve():
        raise ValueError('source and target are the same directory')
    if target.is_symlink() or not target.is_dir():
        raise ValueError(f'target is not a real install directory: {target}')
    cache = (Path(root) / 'plugins' / 'cache').resolve()
    try:
        target.resolve().relative_to(cache)
    except ValueError as exc:
        raise ValueError(f'target outside devkit cache: {target}') from exc
    stamp = time.strftime('%Y%m%d%H%M%S')
    backup_dir = target.parent.parent / 'backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f'{target.name}-{stamp}'
    counter = 1
    while backup.exists():
        backup = backup_dir / f'{target.name}-{stamp}-{counter}'
        counter += 1
    shutil.copytree(target, backup, symlinks=True)
    atomic_copy_tree(source, target)
    return backup


def git(path, *args, timeout=60):
    return run(['git', '-C', str(path), *args], timeout)


def git_head(path, timeout=60):
    result = git(path, 'rev-parse', '--short', 'HEAD', timeout=timeout)
    return result['out'].strip() if result['code'] == 0 else None


def update_repo(repo, apply, timeout):
    result = {'repo': str(repo)}
    checked = git(repo, 'rev-parse', '--is-inside-work-tree', timeout=timeout)
    if checked['code'] != 0:
        result['status'] = 'not_git'
        return result
    status = git(repo, 'status', '--porcelain', timeout=timeout)
    if status['code'] != 0:
        result['status'] = 'error'
        result['out'] = status['out']
        return result
    if status['out'].strip():
        result['status'] = 'dirty'
        result['out'] = status['out'].strip()
        return result
    upstream = git(repo, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}',
                   timeout=timeout)
    if upstream['code'] != 0:
        result['status'] = 'no_upstream'
        return result
    result['upstream'] = upstream['out'].strip()
    if apply:
        fetched = git(repo, 'fetch', '--quiet', timeout=timeout)
        if fetched['code'] != 0:
            result['status'] = 'pull_failed'
            result['out'] = fetched['out']
            return result
        pulled = git(repo, 'pull', '--ff-only', '--quiet', timeout=timeout)
        if pulled['code'] != 0:
            result['status'] = 'pull_failed'
            result['out'] = pulled['out']
            return result
    head = git(repo, 'rev-parse', '--short', 'HEAD', timeout=timeout)
    result['head'] = head['out'].strip() if head['code'] == 0 else None
    result['status'] = 'updated' if apply else 'checked'
    return result


def ensure_links(repo, links_folder, apply):
    source = Path(repo) / 'skills'
    if not source.is_dir():
        return {'added': [], 'missing': []}
    added, missing = [], []
    for skill in sorted(source.glob('dv-*')):
        target = Path(links_folder) / skill.name
        if target.exists() or target.is_symlink():
            continue
        if apply:
            Path(links_folder).mkdir(parents=True, exist_ok=True)
            target.symlink_to(skill.resolve(), target_is_directory=True)
            added.append(skill.name)
        else:
            missing.append(skill.name)
    return {'added': added, 'missing': missing}


def upgrade_host(host, apply, sync, timeout):
    root = host_root(host)
    result = {
        'host': host, 'root': str(root), 'cli': find_cli(host, root),
        'status': 'unknown', 'steps': [], 'duplicate': False,
    }
    record = registry_record(host, root)
    result['record'] = record
    result['links'] = link_records(root)
    result['duplicate'] = bool(record and result['links'])

    source = marketplace_root(root)
    result['source'] = str(source)
    if source.is_dir():
        result['source_version'] = version_at(source, host)
        result['source_sha'] = git_head(source, timeout)

    if record:
        installed = Path(record.get('installPath', ''))
        result['installed'] = str(installed)
        if record.get('gitCommitSha'):
            result['installed_sha'] = str(record['gitCommitSha'])[:7]
        if not installed.is_dir():
            result['status'] = 'install_missing'
        elif not source.is_dir():
            result['status'] = 'marketplace_missing'
        else:
            installed_version = record.get('version') or version_at(installed, host)
            source_version = result.get('source_version')
            result['installed_version'] = installed_version
            source_digest = tree_digest(source)
            installed_digest = tree_digest(installed)
            result['source_digest'] = source_digest
            result['installed_digest'] = installed_digest
            relation = (compare_versions(source_version, installed_version)
                        if source_version and installed_version else 0)
            if relation < 0:
                result['status'] = 'downgrade_blocked'
            elif source_digest == installed_digest:
                result['status'] = 'up_to_date'
            elif not apply:
                result['status'] = 'update_available' if relation > 0 else 'sync_needed'
            elif not result['cli']:
                result['status'] = 'cli_missing'
            else:
                step = marketplace_update(host, root, result['cli'], timeout)
                result['steps'].append(step)
                if step['code'] != 0:
                    result['status'] = 'marketplace_update_failed'
                else:
                    step = plugin_update(host, root, result['cli'], timeout)
                    result['steps'].append(step)
                    current = registry_record(host, root) or record
                    updated_path = Path(current.get('installPath', installed))
                    updated_version = current.get('version') or version_at(updated_path, host)
                    result['installed_after'] = str(updated_path)
                    result['installed_version_after'] = updated_version
                    result['source_version_after'] = version_at(source, host)
                    result['source_digest_after'] = tree_digest(source)
                    result['installed_digest_after'] = tree_digest(updated_path)
                    if (updated_path.is_dir()
                            and result['source_digest_after'] == result['installed_digest_after']):
                        result['status'] = 'updated'
                    elif step['code'] != 0:
                        result['status'] = 'plugin_update_failed'
                    elif (sync and compare_versions(result['source_version_after'],
                                                    updated_version) == 0):
                        try:
                            backup = backup_and_sync(source, updated_path, root)
                            result['backup'] = str(backup)
                            result['installed_digest_after'] = tree_digest(updated_path)
                            result['status'] = ('synced'
                                                if tree_digest(source) == tree_digest(updated_path)
                                                else 'sync_failed')
                        except (OSError, ValueError) as exc:
                            result['status'] = 'sync_failed'
                            result['error'] = str(exc)
                    else:
                        result['status'] = 'update_incomplete'
    elif result['links']:
        result['status'] = 'linked'
    else:
        result['status'] = 'not_installed'

    repos = {}
    for item in result['links']:
        repos.setdefault(item['repo'], None)
    if repos:
        result['repos'] = []
        for repo in sorted(repos):
            info = update_repo(repo, apply, timeout)
            info['links'] = ensure_links(repo, Path(root) / 'skills', apply)
            result['repos'].append(info)

    return result


def render(results, as_json=False):
    if as_json:
        print(json.dumps({'hosts': results}, ensure_ascii=False, indent=2))
        return
    for item in results:
        print(f"== {item.get('host', '?')} ==")
        print(f"root: {item.get('root', '?')}")
        print(f"status: {item.get('status', 'unknown')}")
        if item.get('cli'):
            print(f"cli: {item['cli']}")
        if item.get('installed_version') or item.get('source_version'):
            print(f"version: {item.get('installed_version')} -> {item.get('source_version')}")
        if item.get('installed_sha') or item.get('source_sha'):
            print(f"sha: {item.get('installed_sha') or '?'} -> {item.get('source_sha') or '?'}")
        if item.get('source_digest') or item.get('installed_digest'):
            print(f"digest: {item.get('installed_digest')} -> {item.get('source_digest')}")
        if item.get('backup'):
            print(f"backup: {item['backup']}")
        if item.get('duplicate'):
            print('duplicate: plugin and bare links are both installed')
        for step in item.get('steps', []):
            print(f"cmd[{step['code']}]: {' '.join(step['cmd'])}")
            if step.get('out'):
                print(f"  {step['out']}")
        for repo in item.get('repos', []):
            print(f"repo: {repo['repo']} ({repo['status']})")
            if repo.get('links', {}).get('added'):
                print(f"  added links: {', '.join(repo['links']['added'])}")
            if repo.get('links', {}).get('missing'):
                print(f"  missing links: {', '.join(repo['links']['missing'])}")
        if item.get('error'):
            print(f"error: {item['error']}")
        print()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true', help='read-only status (default)')
    group.add_argument('--apply', action='store_true', help='perform upgrades')
    parser.add_argument('--host', choices=['claude', 'qoder', 'both'], default='both')
    parser.add_argument('--no-sync', action='store_true',
                        help='do not sync same-version content in place')
    parser.add_argument('--json', action='store_true', help='machine-readable output')
    parser.add_argument('--timeout', type=int, default=180, help='per-command timeout in seconds')
    args = parser.parse_args(argv)
    apply = args.apply
    hosts = ['claude', 'qoder'] if args.host == 'both' else [args.host]
    results = []
    for host in hosts:
        try:
            results.append(upgrade_host(host, apply, not args.no_sync, args.timeout))
        except Exception as exc:  # keep the other host running
            try:
                root_text = str(host_root(host))
            except Exception:
                root_text = '?'
            results.append({'host': host, 'root': root_text, 'status': 'error',
                            'error': str(exc), 'steps': []})
    render(results, args.json)
    if apply:
        return 1 if any(item.get('status') in PROBLEM for item in results) else 0
    return 1 if any(item.get('status') in NEEDS_ACTION for item in results) else 0


if __name__ == '__main__':
    sys.exit(main())
