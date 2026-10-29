import importlib.util
import json
import os
import re
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
docscheck=module('docscheck','check-docs.py')
indexgen=module('indexgen','gen-docs-index.py')


class MetadataTests(unittest.TestCase):
    def test_catalog(self):
        records=catalog();self.assertEqual(len(records),19)
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


class DocContractTests(unittest.TestCase):
    def project(self,t,profile='light'):
        root=Path(t);(root/'.devkit').mkdir(parents=True)
        cfg={'version':1,'docs':{'profile':profile}}
        (root/'.devkit/config.json').write_text(json.dumps(cfg))
        return root
    def write(self,root,rel,text):
        p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text,encoding='utf-8');return p
    def test_clean_project_passes(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t)
            self.write(root,'.devkit/specs/001-user-auth.md','# 用户鉴权\n\n- 状态：草稿\n\n## 1. 背景与目标\n\nx\n')
            self.write(root,'docs/adr/0001-use-jwt.md','# 0001. 选 JWT\n\n- 状态：采纳\n')
            indexgen.main.__globals__['sys'].argv=['gen','--project',t]
            self.assertEqual(indexgen.main(),0)
            errors,warnings=docscheck.check(t)
            self.assertEqual(errors,[])
    def test_bad_name_duplicate_status_missing_section(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t,'strict')
            self.write(root,'.devkit/specs/spec1.md','# x\n\n- 状态：草稿\n')
            self.write(root,'.devkit/specs/001-a.md','# a\n\n- 状态：错误态\n\n## 1. 背景与目标\n')
            self.write(root,'.devkit/specs/001-b.md','# b\n\n- 状态：定稿\n')
            errors,_=docscheck.check(t)
            self.assertTrue(any('C2' in e for e in errors))
            self.assertTrue(any('C3' in e for e in errors))
            self.assertTrue(any('C4' in e for e in errors))
            self.assertTrue(any('C5' in e for e in errors))
    def test_broken_reference_and_supersede(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t)
            self.write(root,'docs/adr/0001-old.md','# 0001. 旧\n\n- 状态：被 0099 取代\n\n相关：`docs/specs/001-missing.md`\n')
            errors,_=docscheck.check(t)
            self.assertTrue(any('C6' in e for e in errors))
            self.assertTrue(any('C7' in e for e in errors))
    def test_index_required_and_stale(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t)
            self.write(root,'.devkit/specs/001-a.md','# a\n\n- 状态：草稿\n')
            errors,_=docscheck.check(t)
            self.assertTrue(any('C8' in e and 'missing index' in e for e in errors))
            self.write(root,'docs/INDEX.md','- [x](docs/specs/gone.md)\n')
            errors,_=docscheck.check(t)
            self.assertTrue(any('stale link' in e for e in errors))
    def test_profile_off_only_reports(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t,'off')
            self.write(root,'.devkit/specs/spec1.md','# x\n')
            errors,warnings=docscheck.check(t)
            self.assertEqual(errors,[])
            self.assertTrue(any('off' in w for w in warnings))
    def test_index_generation_idempotent(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t)
            self.write(root,'.devkit/specs/001-a.md','# 标题A\n\n- 状态：定稿\n')
            for _ in range(2):
                indexgen.main.__globals__['sys'].argv=['gen','--project',t]
                self.assertEqual(indexgen.main(),0)
            first=(root/'docs/INDEX.md').read_text()
            indexgen.main.__globals__['sys'].argv=['gen','--project',t,'--check']
            self.assertEqual(indexgen.main(),0)
            self.assertIn('[标题A]',first)
            self.assertIn('定稿',first)
    def test_strict_sections_present_pass(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t,'strict')
            body='# a\n\n- 状态：草稿\n\n'+''.join(f'## {s}\n\nx\n\n' for s in docscheck.schema()['sections']['specs'])
            self.write(root,'.devkit/specs/001-a.md',body)
            indexgen.main.__globals__['sys'].argv=['gen','--project',t]
            self.assertEqual(indexgen.main(),0)
            errors,warnings=docscheck.check(t)
            self.assertEqual([e for e in errors if 'C5' in e],[],errors)
    def test_ticket_evidence_paths(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t)
            (root/'src').mkdir();(root/'src/a.py').write_text('x')
            self.write(root,'.devkit/issues/001-a.md','# a\n\n- 状态：待实施\n\n## 依据\n\n`src/a.py` 与 `docs/specs/001-a.md`\n\n'
                '## 证据\n\n- `src/a.py` 退出码 0\n- `src/missing.py` 退出码 0\n'
                '- `logs/run.log`\n- `/tmp/out.json`\n- `src/NNN-x.py`\n')
            errors,_=docscheck.check(t)
            hits=[e for e in errors if 'C9' in e]
            self.assertEqual(len(hits),1,hits)
            self.assertIn('src/missing.py',hits[0])
    def test_review_axis_evidence(self):
        with tempfile.TemporaryDirectory() as t:
            root=self.project(t)
            (root/'src').mkdir();(root/'src/ok.ts').write_text('x')
            self.write(root,'docs/reviews/2026-10-29-x.md','# r\n\n## Correctness\n\n`src/gone.ts:12`\n\n'
                '## Standards\n\n`src/ok.ts:3`\n')
            errors,_=docscheck.check(t)
            hits=[e for e in errors if 'C9' in e]
            self.assertEqual(len(hits),1,hits)
            self.assertIn('src/gone.ts',hits[0])


class DocSchemaTests(unittest.TestCase):
    """ARTIFACTS.md must stay a readable mirror of scripts/docs.schema.json."""
    def section(self,text,title):
        start=text.index(title);end=text.find('\n## ',start+len(title))
        return text[start:end if end!=-1 else len(text)]
    def test_artifacts_match_schema(self):
        schema=json.loads((ROOT/'scripts/docs.schema.json').read_text(encoding='utf-8'))
        artifacts=(ROOT/'ARTIFACTS.md').read_text(encoding='utf-8')
        labels={'规格':'specs','工单':'issues','ADR':'adr','变更提案':'changes'}
        states=self.section(artifacts,'## 状态词表')
        for label,kind in labels.items():
            row=next(line for line in states.splitlines() if line.startswith(f'| {label} |'))
            expected=list(schema['status'][kind]['values'])
            if schema['status'][kind].get('supersede'):expected.append('被 NNNN 取代')
            self.assertEqual(set(re.findall(r'`([^`]+)`',row)),set(expected),label)
        required=self.section(artifacts,'## 必填小节')
        for label,kind in labels.items():
            line=next(line for line in required.splitlines() if line.startswith(f'- {label}：'))
            listed=[s.strip() for s in re.sub(r'（[^）]*）','',line.split('：',1)[1]).split('/')]
            self.assertEqual(listed,schema['sections'][kind],label)


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
    def test_parallel_contracts(self):
        records={fm['name']:(fm,body) for _,fm,body in catalog()}
        for name in ('dv-review','dv-audit','dv-research'):
            body=records[name][1]
            for word in ('并行执行','串行','不伪称已分发'):
                self.assertIn(word,body)
        self.assertIn('只读',records['dv-review'][1])
        for word in ('3 个','未确认停止前'):
            self.assertIn(word,records['dv-review'][1])
        self.assertIn('独立临时副本',records['dv-audit'][1])
        self.assertIn('一手证据',records['dv-research'][1])
    def test_upgrade_contract(self):
        records={fm['name']:(fm,body) for _,fm,body in catalog()}
        fm,body=records['dv-upgrade']
        self.assertEqual(fm['metadata']['stage'],'meta')
        self.assertEqual(fm['metadata']['effects'],['install'])
        self.assertEqual(fm['metadata']['explicit-actions'],['install'])
        for word in ('备份','不授权commit/push','重启','--check','--apply'):
            self.assertIn(word,body)
    def test_evaluation_fixtures(self):
        cases=json.loads((ROOT/'evals/scenarios.json').read_text())['cases']
        self.assertEqual(len(cases),10)
        for case in cases:self.assertTrue(case['forbid'])

if __name__=='__main__':unittest.main()
