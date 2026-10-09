# SPDX-License-Identifier: MIT
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from contracts.reader_state import parameters,filtered,METHOD_VERSION
from evidence_interface import validate
from regulatory_reader import generate

class ReaderTests(unittest.TestCase):
 def setUp(self):
  self.doc=json.loads((ROOT/'interfaces/examples/regulatory-events.json').read_text(encoding='utf-8'));self.rows=validate(self.doc)['regulatory_events']
 def test_filters_distinguish_container_and_rule_gap(self):
  self.assertEqual(len(filtered(self.rows,{'rule_status':'selected'})),1)
  self.assertEqual(filtered(self.rows,{'evidence_status':'not_obtained'})[0]['event_type'],'administrative_penalty')
  self.assertEqual(filtered(self.rows,{'event_type':'supervisory_measure'}),[])
 def test_unknown_public_date_last_and_input_not_mutated(self):
  rows=copy.deepcopy(self.rows);rows[0]['public_date']=None;before=copy.deepcopy(rows)
  result=filtered(rows,{'sort':'public_date_asc'});self.assertIsNone(result[-1]['public_date'])
  result[-1]['legal_effect']['reason']='changed view';self.assertEqual(rows,before)
 def test_unknown_parameters_rejected(self):
  with self.assertRaises(ValueError):parameters({'fraud_score':1})
 def test_snapshots_and_restore_same_input(self):
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/'one';generate(output)
   saved=json.loads((output/'reader-session.json').read_text(encoding='utf-8'));saved['parameters']['event_type']='administrative_penalty'
   restored=Path(directory)/'two';generate(restored,settings=saved)
   session=json.loads((restored/'reader-session.json').read_text(encoding='utf-8'))
   self.assertEqual(len(session['results']),1);self.assertEqual(session['input_snapshot'],self.doc)
   self.assertEqual(session['method_version'],METHOD_VERSION)
   self.assertEqual((output/'input.json').read_bytes(),(ROOT/'interfaces/examples/regulatory-events.json').read_bytes())
   saved['method_version']='unknown-version'
   with self.assertRaisesRegex(ValueError,'version mismatch'):generate(Path(directory)/'three',settings=saved)
 def test_restore_changed_input_hash_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/'one';generate(output);saved=json.loads((output/'reader-session.json').read_text(encoding='utf-8'));saved['input_sha256']='changed'
   with self.assertRaisesRegex(ValueError,'input hash differs'):generate(Path(directory)/'two',settings=saved)
 def test_existing_output_not_overwritten(self):
  with tempfile.TemporaryDirectory() as directory:
   with self.assertRaisesRegex(ValueError,'no overwrite'):generate(Path(directory))
 @unittest.skipUnless(shutil.which('node'),'Node only needed for optional JS/Python filter parity test')
 def test_browser_filter_logic_matches_python(self):
  settings=[{},dict(event_type='administrative_penalty'),dict(evidence_status='embedded'),dict(rule_status='gap',sort='public_date_asc')]
  script="const fs=require('fs'),api=require(process.argv[1]),v=JSON.parse(fs.readFileSync(0,'utf8'));console.log(JSON.stringify(v.settings.map(p=>api.filtered(v.rows,p))));"
  result=subprocess.run(['node','-e',script,str(ROOT/'assets/regulatory-reader.js')],input=json.dumps(dict(rows=self.rows,settings=settings)),capture_output=True,text=True,encoding='utf-8',check=True)
  self.assertEqual(json.loads(result.stdout),[filtered(self.rows,p) for p in settings])

if __name__=='__main__':unittest.main()
