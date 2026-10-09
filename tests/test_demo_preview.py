import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from demo_preview import generate,INPUTS
from scenarios import run
from evidence_interface import validate
from rule_versions import load_catalog,select

class DemoTests(unittest.TestCase):
    def test_report_reuses_same_inputs_and_results(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary)/'new-report';manifest=generate(output)
            read=lambda p:json.loads(p.read_text(encoding='utf-8'))
            self.assertEqual(read(output/'cash-scenario.json'),run(read(ROOT/INPUTS['cash'])))
            self.assertEqual(read(output/'event-evidence.json'),validate(read(ROOT/INPUTS['events'])))
            self.assertEqual(read(output/'rule-selection.json'),select(load_catalog(),read(ROOT/INPUTS['rule'])))
            for entry in manifest['inputs']:
                self.assertEqual(entry['sha256'],hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest())
            self.assertIn('teaching assumptions',{entry['data_class'] for entry in manifest['inputs']})
            page=(output/'index.html').read_text(encoding='utf-8')
            for marker in ('教学现金情景','85,000.00','5,000.00','15,000.00','未知','2025-12-31','PR #1 待审','SSE-REITS-EXP-2025'):self.assertIn(marker,page)
    def test_existing_directory_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);sentinel=output/'keep.txt';sentinel.write_text('keep',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'no overwrite'):generate(output)
            self.assertEqual(sentinel.read_text(encoding='utf-8'),'keep')
    def test_saved_cash_snapshots_are_byte_identical(self):
        self.assertEqual((ROOT/'docs/preview/inputs/cash-ledger.json').read_bytes(),(ROOT/INPUTS['cash']).read_bytes())

if __name__=='__main__':unittest.main()
