# SPDX-License-Identifier: MIT
"""Exercise the public CLI boundary from a foreign consumer working directory."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'scripts/common_interface.py'


class WorkbenchHandoffTests(unittest.TestCase):
    def invoke(self, input_path, cwd, reverse=False):
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        args = [sys.executable, '-B', '-X', 'utf8', str(CLI), '--input', str(input_path)]
        if reverse:
            args.append('--reverse')
        return subprocess.run(args, cwd=cwd, env=environment, capture_output=True,
                              text=True, encoding='utf-8', timeout=15)

    def test_foreign_cwd_export_reverse_preserves_selected_and_gap(self):
        for name, status, version in [('workbench-rule-selected', 'selected', 'SSE-REITS-EXP-2025'),
                                      ('workbench-rule-gap', 'gap', None)]:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as directory:
                source_path = ROOT / 'interfaces/common-inputs' / (name + '.json')
                original = json.loads(source_path.read_text(encoding='utf-8'))
                result = self.invoke(source_path, directory)
                self.assertEqual(result.returncode, 0, result.stderr)
                common = json.loads(result.stdout)
                expected = json.loads((ROOT / 'interfaces/common-examples' / (name + '.json')).read_text(encoding='utf-8'))
                self.assertEqual(common, expected)
                record = common['records'][0]
                self.assertEqual(record['rule_selection']['status'], status)
                self.assertEqual(record['rule_selection']['rule_version_id'], version)
                self.assertEqual(record['rule_selection']['query']['subject'], 'fund_manager')
                self.assertEqual(record['rule_selection']['query']['board'], 'REITS')
                self.assertEqual(common['sources'][0]['source_tier'], 'public_original')
                unknown = next(f for f in record['facts'] if f['key'] == 'settlement_available_at')
                self.assertIsNone(unknown['value'])
                self.assertEqual(unknown['status'], 'unknown')
                self.assertTrue(unknown['reason'])
                exported = Path(directory) / 'exported.json'
                exported.write_text(result.stdout, encoding='utf-8')
                reverse = self.invoke(exported, directory, reverse=True)
                self.assertEqual(reverse.returncode, 0, reverse.stderr)
                self.assertEqual(json.loads(reverse.stdout), original)

    def test_reverse_rejects_gap_promoted_to_selected(self):
        common = json.loads((ROOT / 'interfaces/common-examples/workbench-rule-gap.json').read_text(encoding='utf-8'))
        common['records'][0]['rule_selection']['status'] = 'selected'
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'promoted.json'
            path.write_text(json.dumps(common), encoding='utf-8')
            result = self.invoke(path, directory, reverse=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('differs from original', result.stderr)
            self.assertEqual(result.stdout, '')


if __name__ == '__main__':
    unittest.main()
