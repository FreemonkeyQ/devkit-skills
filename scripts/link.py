#!/usr/bin/env python3
"""Local links only; check is read-only; foreign links/files are never replaced."""
import argparse
import os
from pathlib import Path
from skillmeta import ROOT


def sync(root, targets, mode):
    issues = 0
    sources = sorted((Path(root)/'skills').glob('*/SKILL.md'))
    for target in targets:
        target = Path(target)
        if not target.is_dir():
            print('Missing target directory:',target)
            if mode == 'check': issues += 1
            elif mode == 'apply': target.mkdir(parents=True,exist_ok=True)
            else: continue
        for file in sources:
            src = file.parent.resolve()
            dst = target/src.name
            owned = dst.is_symlink() and os.readlink(dst) == str(src)
            if mode == 'uninstall':
                if owned: dst.unlink(); print('Removed owned link',dst)
                continue
            if owned: continue
            if dst.exists() or dst.is_symlink():
                issues += 1; print('Conflict preserved:',dst); continue
            if mode == 'check':
                issues += 1; print('Missing:',dst)
            else:
                dst.symlink_to(src,target_is_directory=True); print('Linked:',dst)
        # Remove stale links only when exact canonical target is a removed skill of this repo.
        if mode == 'uninstall':
            for dst in target.glob('dv-*'):
                if dst.is_symlink():
                    raw = Path(os.readlink(dst))
                    if raw.is_absolute() and raw.parent == (Path(root)/'skills').resolve(): dst.unlink()
    return 1 if issues else 0


def main():
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group()
    g.add_argument('--check',action='store_true');g.add_argument('--apply',action='store_true');g.add_argument('--uninstall',action='store_true')
    p.add_argument('--target',action='append',help='Explicit target for isolated tests or supported local skills directory')
    args=p.parse_args()
    mode='apply' if args.apply else 'uninstall' if args.uninstall else 'check'
    targets=args.target or [Path.home()/'.claude/skills',Path.home()/'.qoder-cn/skills']
    return sync(ROOT,targets,mode)

if __name__ == '__main__': raise SystemExit(main())
