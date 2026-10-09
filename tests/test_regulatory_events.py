# SPDX-License-Identifier: MIT
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evidence_interface import validate
from contracts.common import to_common,from_common

class RegulatoryTests(unittest.TestCase):
 def setUp(self):self.doc=json.loads((ROOT/'interfaces/examples/regulatory-events.json').read_text(encoding='utf-8'))
 def rejected(self):
  with self.assertRaises(ValueError):validate(self.doc)
 def test_actual_types_and_gaps(self):
  result=validate(self.doc);self.assertEqual(result['record_count'],4);self.assertEqual(result['unknown_field_count'],9)
  self.assertEqual({r['event_type'] for r in result['regulatory_events']},{'inquiry','administrative_penalty','audit_opinion','correction'})
  self.assertEqual(result['regulatory_events'][2]['original_document_status'],'not_obtained')
 def test_inquiry_cannot_be_relabelled_penalty(self):
  self.doc['records'][0]['event_type']='administrative_penalty';self.rejected()
 def test_cited_decision_not_original(self):
  self.doc['records'][2]['regulatory_event']['original_document_status']='obtained';self.rejected()
 def test_unknown_effect_not_decision_date(self):
  self.doc['records'][2]['regulatory_event']['legal_effect']['date']='2024-02-05';self.rejected()
 def test_cited_only_effect_cannot_be_certified(self):
  self.doc['records'][2]['regulatory_event']['legal_effect']=dict(status='documented',date='2024-02-05',evidence=dict(source_id='XINHAI-PENALTY-CITE',locator='第一段'));self.rejected()
 def test_cited_rule_not_current_version_interval(self):
  self.doc['records'][2]['regulatory_event']['rule_application']['effective_from']='2026-04-24';self.rejected()
 def test_selected_version_must_match_existing_selector(self):
  self.doc['records'][0]['regulatory_event']['rule_application']['version_id']='SSE-REITS-EXP-2025';self.rejected()
 def test_source_day_must_match(self):
  self.doc['records'][3]['regulatory_event']['publication']['date']='2026-04-22';self.rejected()
 def test_no_fabricated_midnight(self):
  self.doc['records'][1]['regulatory_event']['publication']['first_public_at']='2026-08-27T00:00:00+08:00';self.rejected()
 def test_same_day_precision_not_intraday_available(self):
  self.doc['records']=[self.doc['records'][1]];self.doc['records'][0]['backtest_cutoff']='2026-08-27T15:00:00+08:00';self.rejected()
 def test_audit_domain_required(self):
  self.doc['records'][3]['regulatory_event'].pop('audit_domain');self.rejected()
 def test_qualified_opinion_does_not_infer_fraud(self):
  self.doc['records'][3]['regulatory_event']['audit_opinion']='qualified'
  next(f for f in self.doc['records'][3]['facts'] if f['key']=='audit_opinion_label')['value']='保留意见'
  self.assertEqual(validate(self.doc)['regulatory_events'][3]['classification_scope'],'no_fraud_inference')
  self.doc['records'][3]['regulatory_event']['classification_scope']='fraud_inferred';self.rejected()
 def test_audit_label_and_enum_cannot_disagree(self):
  self.doc['records'][3]['regulatory_event']['audit_opinion']='qualified';self.rejected()
 def test_older_interfaces_unchanged(self):
  old=json.loads((ROOT/'interfaces/examples/inquiry-correction.json').read_text(encoding='utf-8'))
  self.assertNotIn('regulatory_events',validate(old));self.assertEqual(to_common(old)['contract_version'],'cn-market-rules.rule-handoff/1.0')
 def test_new_common_roundtrip_preserves_all_dates_and_types(self):
  common=to_common(self.doc);self.assertEqual(common['contract_version'],'cn-market-rules.rule-handoff/1.1')
  self.assertEqual(common['records'][3]['regulatory_event'],self.doc['records'][3]['regulatory_event'])
  self.assertEqual(from_common(common),self.doc)

if __name__=='__main__':unittest.main()
