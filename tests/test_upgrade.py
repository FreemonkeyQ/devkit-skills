import importlib.util
import json
import os
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('upgrade', ROOT / 'scripts' / 'upgrade.py')
upgrade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upgrade)


class UpgradeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def make_plugin(self, base, version='0.2.0', content='old'):
        base = Path(base)
        (base / '.claude-plugin').mkdir(parents=True, exist_ok=True)
        (base / '.claude-plugin' / 'plugin.json').write_text(
            json.dumps({'name': 'devkit-skills', 'version': version}))
        (base / 'skills' / 'dv-review').mkdir(parents=True, exist_ok=True)
        (base / 'skills' / 'dv-review' / 'SKILL.md').write_text(content)
        return base

    def make_install(self, root, version='0.2.0', content='old'):
        target = root / 'plugins' / 'cache' / 'devkit-skills' / 'devkit-skills' / version
        self.make_plugin(target, version, content)
        registry = {'version': 2, 'plugins': {'devkit-skills@devkit-skills': [
            {'scope': 'user', 'installPath': str(target), 'version': version}]}}
        (root / 'plugins').mkdir(parents=True, exist_ok=True)
        (root / 'plugins' / 'installed_plugins.json').write_text(json.dumps(registry))
        return target

    def fake_cli(self, log):
        path = self.root / 'fake-claude'
        path.write_text(
            '#!/usr/bin/env python3\n'
            'import sys\n'
            f'open({str(log)!r}, "a", encoding="utf-8").write(" ".join(sys.argv[1:]) + "\\n")\n'
            'raise SystemExit(0)\n')
        path.chmod(0o755)
        return path

    def test_versions_and_digest(self):
        self.assertGreater(upgrade.version_tuple('0.10.0'), upgrade.version_tuple('0.9.0'))
        left = self.make_plugin(self.root / 'left', content='a')
        right = self.make_plugin(self.root / 'right', content='b')
        self.assertNotEqual(upgrade.tree_digest(left), upgrade.tree_digest(right))
        (right / 'skills/dv-review/SKILL.md').write_text('a')
        self.assertEqual(upgrade.tree_digest(left), upgrade.tree_digest(right))

    def test_check_is_readonly(self):
        root = self.root / 'claude'
        source = self.make_plugin(root / 'plugins/marketplaces/devkit-skills', content='new')
        target = self.make_install(root, content='old')
        with unittest.mock.patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(root)}, clear=False):
            result = upgrade.upgrade_host('claude', False, True, 5)
        self.assertEqual(result['status'], 'sync_needed')
        self.assertEqual(result['steps'], [])
        self.assertEqual((target / 'skills/dv-review/SKILL.md').read_text(), 'old')
        self.assertEqual(upgrade.tree_digest(source), result['source_digest'])

    def test_apply_refreshes_marketplace_before_deciding(self):
        root = self.root / 'claude'
        self.make_plugin(root / 'plugins/marketplaces/devkit-skills', content='same')
        self.make_install(root, content='same')
        log = self.root / 'cli.log'
        cli = self.fake_cli(log)
        env = {'CLAUDE_CONFIG_DIR': str(root), 'CLAUDE_CLI': str(cli)}
        with unittest.mock.patch.dict(os.environ, env, clear=False):
            result = upgrade.upgrade_host('claude', True, True, 5)
        self.assertEqual(result['status'], 'up_to_date')
        self.assertEqual(len(result['steps']), 1)
        self.assertIn('plugin marketplace update', log.read_text())

    def test_same_version_sync_fallback(self):
        root = self.root / 'claude'
        self.make_plugin(root / 'plugins/marketplaces/devkit-skills', content='new')
        target = self.make_install(root, content='old')
        (target / 'skills' / 'stale.md').write_text('stale')
        log = self.root / 'cli.log'
        cli = self.fake_cli(log)
        env = {'CLAUDE_CONFIG_DIR': str(root), 'CLAUDE_CLI': str(cli)}
        with unittest.mock.patch.dict(os.environ, env, clear=False):
            result = upgrade.upgrade_host('claude', True, True, 5)
        self.assertEqual(result['status'], 'synced')
        self.assertEqual((target / 'skills/dv-review/SKILL.md').read_text(), 'new')
        self.assertFalse((target / 'skills/stale.md').exists())
        self.assertTrue(Path(result['backup']).is_dir())
        self.assertEqual((Path(result['backup']) / 'skills/dv-review/SKILL.md').read_text(), 'old')
        self.assertEqual(len(result['steps']), 2)
        self.assertTrue(log.read_text().strip())

    def test_ensure_links_only_adds_missing(self):
        repo = self.root / 'repo'
        (repo / 'skills' / 'dv-review').mkdir(parents=True)
        (repo / 'skills' / 'dv-upgrade').mkdir()
        links = self.root / 'skills'
        checked = upgrade.ensure_links(repo, links, False)
        self.assertIn('dv-upgrade', checked['missing'])
        applied = upgrade.ensure_links(repo, links, True)
        self.assertIn('dv-upgrade', applied['added'])
        self.assertTrue((links / 'dv-upgrade').is_symlink())


if __name__ == '__main__':
    unittest.main()
