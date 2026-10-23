"""Validate evaluation materials, not skill execution or model behavior."""
import json
from collections import Counter
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DepthEvaluationTests(unittest.TestCase):
    def test_cases_have_unique_ids_and_known_skills(self):
        data = json.loads((ROOT / 'evals/depth-scenarios.json').read_text(encoding='utf-8'))
        self.assertEqual(data['version'], 1)
        cases = data['cases']
        self.assertEqual(len(cases), 6)
        ids = [case['id'] for case in cases]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(isinstance(value, str) and value.strip() for value in ids))
        self.assertEqual(Counter(case['skill'] for case in cases),
                         {'dv-review': 2, 'dv-debug': 2, 'dv-test': 2})
        for case in cases:
            with self.subTest(case=case['id']):
                self.assertTrue((ROOT / 'skills' / case['skill'] / 'SKILL.md').is_file())

    def test_inputs_and_rubrics_are_separate_and_complete(self):
        data = json.loads((ROOT / 'evals/depth-scenarios.json').read_text(encoding='utf-8'))
        for case in data['cases']:
            with self.subTest(case=case['id']):
                self.assertIsInstance(case['prompt'], str)
                self.assertTrue(case['prompt'].strip())
                fixture = case['fixture']
                self.assertEqual(set(fixture), {'contract', 'files', 'observations'})
                self.assertTrue(isinstance(fixture['contract'], str) and fixture['contract'].strip())
                self.assertIsInstance(fixture['files'], dict)
                for name, source in fixture['files'].items():
                    path = Path(name)
                    self.assertFalse(path.is_absolute())
                    self.assertNotIn('..', path.parts)
                    self.assertTrue(name)
                    self.assertIsInstance(source, str)
                    self.assertTrue(source.strip())
                self.assertIsInstance(fixture['observations'], list)
                self.assertTrue(all(isinstance(item, str) and item.strip()
                                    for item in fixture['observations']))
                self.assertIsInstance(case['forbid'], list)
                self.assertTrue(case['forbid'])
                self.assertTrue(all(isinstance(item, str) and item.strip()
                                    for item in case['forbid']))
                self.assertEqual(set(case['rubric']), {'task', 'boundary', 'evidence'})
                for items in case['rubric'].values():
                    self.assertIsInstance(items, list)
                    self.assertTrue(items)
                    self.assertTrue(all(isinstance(item, str) and item.strip() for item in items))


if __name__ == '__main__':
    unittest.main()
