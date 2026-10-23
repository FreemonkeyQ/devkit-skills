import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from skillmeta import frontmatter,catalog
from lint import check
from config import load_config,load_state,resolve_path
from link import sync


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

helpgen=module('helpgen','dv-help-gen.py')
hook=module('hook','dv-hook.py')


class MetadataTests(unittest.TestCase):
    def test_catalog(self):
        records=catalog();self.assertEqual(len(records),18)
        self.assertEqual(check()[0],[])
        for _,fm,_ in records:
            self.assertNotIn('disable-model-invocation',fm)
            self.assertIsInstance(fm['metadata']['next'],list)
    def test_yaml_multiline(self):
        fm,_=frontmatter('---\nname: dv-x\ndescription: >\n  hello: world\nmetadata:\n  next: []\n---\nbody')
        self.assertEqual(fm['description'].strip(),'hello: world')
    def test_bad_yaml(self):
        with self.assertRaises(yaml.YAMLError):frontmatter('---\na: [\n---\nbody')
    def test_bad_metadata_and_nesting(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'skills/group/dv-bad/SKILL.md';p.parent.mkdir(parents=True)
            p.write_text('---\nname: wrong\ndescription: x\nmetadata: {}\n---\nbody')
            errors,_=check(t)
            self.assertTrue(any('flat' in x for x in errors))
            self.assertTrue(any('name' in x for x in errors))
    def test_generated(self):
        p=ROOT/'skills/dv-help/references/_generated.md'
        self.assertEqual(p.read_text(),helpgen.build())
    def test_check_is_readonly(self):
        # missing OUT must stay missing; --check never creates it
        with tempfile.TemporaryDirectory() as t:
            saved=helpgen.OUT;args=sys.argv
            helpgen.OUT=Path(t)/'missing/out.md';sys.argv=['help','--check']
            try:self.assertEqual(helpgen.main(),1);self.assertFalse(helpgen.OUT.parent.exists())
            finally:helpgen.OUT=saved;sys.argv=args


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(load_config(t)['paths']['state'],'.devkit/state.json')
            self.assertIsNone(load_state(t))
    def test_escape(self):
        with tempfile.TemporaryDirectory() as t:
            for v in ('../escape','/tmp/escape','.'):
                with self.assertRaises(ValueError):resolve_path(t,v)
    def test_external_symlink(self):
        with tempfile.TemporaryDirectory() as t,tempfile.TemporaryDirectory() as other:
            (Path(t)/'external').symlink_to(other)
            with self.assertRaises(ValueError):resolve_path(t,'external/state.json')
    def test_custom_state_hook(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'.devkit').mkdir();(root/'runtime').mkdir()
            (root/'.devkit/config.json').write_text(json.dumps({'version':1,'paths':{'state':'runtime/state.json'}}))
            p=root/'runtime/state.json'
            p.write_text(json.dumps({'version':1,'stage':'verified','next':['dv-review'],'ticket':'7'}))
            self.assertIn('optional-next=dv-review',hook.hint(t))
            p.write_text(json.dumps({'version':1,'stage':'idle','next':[]}))
            self.assertEqual(hook.hint(t),'')
    def test_bad_state_type(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'.devkit/state.json';p.parent.mkdir()
            p.write_text('{"version":1,"stage":"building","next":"dv-push"}')
            import jsonschema
            with self.assertRaises(jsonschema.ValidationError):load_state(t)
    def test_bad_hook_nonblocking(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'.devkit/state.json';p.parent.mkdir();p.write_text('broken')
            result=subprocess.run(['bash',str(ROOT/'scripts/dv-hook.sh')],env={**os.environ,'CLAUDE_PROJECT_DIR':t},capture_output=True,text=True)
            self.assertEqual((result.returncode,result.stdout),(0,''))


class LinkTests(unittest.TestCase):
    def test_link_protection(self):
        with tempfile.TemporaryDirectory() as t:
            base=Path(t);src=base/'repo';(src/'skills/dv-x').mkdir(parents=True);(src/'skills/dv-x/SKILL.md').write_text('test')
            target=base/'target'
            self.assertEqual(sync(src,[target],'check'),1);self.assertFalse(target.exists())
            self.assertEqual(sync(src,[target],'apply'),0)
            self.assertTrue((target/'dv-x').is_symlink())
            self.assertEqual(sync(src,[target],'uninstall'),0)
            foreign=base/'foreign';foreign.mkdir();(target/'dv-x').symlink_to(foreign)
            self.assertEqual(sync(src,[target],'apply'),1)
            self.assertEqual((target/'dv-x').resolve(),foreign.resolve())
            sync(src,[target],'uninstall');self.assertTrue((target/'dv-x').is_symlink())


class GitFixtureTests(unittest.TestCase):
    def test_uncommitted_and_new_files(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)
            def git(*args):return subprocess.check_output(['git','-C',t,*args],stderr=subprocess.STDOUT)
            git('init','-q');git('config','user.name','fixture');git('config','user.email','fixture@example.invalid')
            (p/'tracked').write_text('before\n');git('add','tracked');git('commit','-qm','baseline')
            (p/'tracked').write_text('staged\n');git('add','tracked');(p/'tracked').write_text('unstaged\n')
            (p/'new').write_text('new\n');(p/'unrelated').write_text('preserve\n')
            self.assertEqual(git('diff','HEAD...HEAD'),b'')
            self.assertIn(b'unstaged',git('diff'));self.assertIn(b'staged',git('diff','--cached'))
            self.assertIn(b'new',git('ls-files','--others','--exclude-standard'))
            result=subprocess.run(['git','-C',t,'rev-parse','--abbrev-ref','@{upstream}'],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertEqual((p/'unrelated').read_text(),'preserve\n')


class SkillContractTests(unittest.TestCase):
    def test_commit_push_done_contracts(self):
        records={fm['name']:(fm,body) for _,fm,body in catalog()}
        self.assertEqual(records['dv-commit'][0]['metadata']['explicit-actions'],['commit'])
        self.assertEqual(records['dv-push'][0]['metadata']['explicit-actions'],['commit','push'])
        self.assertEqual(records['dv-done'][0]['metadata']['explicit-actions'],[])
        for word in ['只推已有提交','dv-commit','SHA','CI']:
            self.assertIn(word,records['dv-push'][1])
        for word in ['未提交','暂存','未跟踪']:
            self.assertIn(word,records['dv-review'][1])
    def test_evaluation_fixtures(self):
        cases=json.loads((ROOT/'evals/scenarios.json').read_text())['cases']
        self.assertEqual(len(cases),9)
        for case in cases:self.assertTrue(case['forbid'])

if __name__=='__main__':unittest.main()
