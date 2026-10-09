# SPDX-License-Identifier: MIT
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from rule_versions import load_catalog,select,validate_catalog
from evidence_interface import validate

class VersionTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog()
        self.query=json.loads((ROOT/'rules/example-query.json').read_text(encoding='utf-8'))
    def query_on(self,day,**changes):
        q=dict(self.query,applicability_date=day,knowledge_date=day);q.update(changes)
        return select(self.catalog,q)
    def test_day_before_replacement(self):
        self.assertEqual(self.query_on('2025-12-30')['rule_version_id'],'SSE-REITS-EXP-2022')
    def test_replacement_day(self):
        result=self.query_on('2025-12-31')
        self.assertEqual(result['rule_version_id'],'SSE-REITS-EXP-2025')
        self.assertEqual(result['supersedes'],['SSE-REITS-EXP-2022'])
    def test_old_not_commercial(self):self.assertEqual(self.query_on('2025-12-30',asset_type='commercial')['status'],'gap')
    def test_new_commercial(self):self.assertEqual(self.query_on('2025-12-31',asset_type='commercial')['status'],'selected')
    def test_not_cross_market(self):self.assertEqual(self.query_on('2026-08-10',market='SZSE')['rule_version_id'],'SZSE-REITS-EXP-2025')
    def test_uncovered_old_sz(self):self.assertEqual(self.query_on('2025-12-30',market='SZSE')['status'],'gap')
    def test_subject_scope(self):self.assertEqual(self.query_on('2026-08-10',subject='listed_company')['status'],'gap')
    def test_board_scope(self):self.assertEqual(self.query_on('2026-08-10',board='MAIN')['status'],'gap')
    def test_future_not_extrapolated(self):self.assertEqual(self.query_on('2026-10-10')['status'],'gap')
    def trade_query(self,day,topic='risk_warning_price_band'):
        return self.query_on(day,topic=topic,board='MAIN',subject='market_participant',asset_type='stock')
    def test_publication_not_implementation(self):self.assertEqual(self.trade_query('2026-04-24')['status'],'gap')
    def test_before_delayed_effective(self):self.assertEqual(self.trade_query('2026-07-05')['status'],'gap')
    def test_effective_day(self):self.assertEqual(self.trade_query('2026-07-06')['status'],'selected')
    def test_deferred_exception(self):
        result=self.trade_query('2026-07-06','block_trade_late_session')
        self.assertEqual(result['status'],'deferred');self.assertEqual(result['evidence']['source_id'],'TRADE-SH-DEFER')
    def test_unknown_effective_not_guessed(self):
        result=self.query_on('2026-08-10',topic='st_delisting',market='BSE',board='BSE',subject='listed_company',asset_type='stock')
        self.assertEqual(result['status'],'gap')
    def test_future_application_not_historical(self):
        with self.assertRaises(ValueError):select(self.catalog,dict(self.query,knowledge_date='2025-12-30'))
    def test_overlap_not_latest_wins(self):
        item=copy.deepcopy(self.catalog['versions'][1]);item.update(version_id='SYNTHETIC-OVERLAP',supersedes=[],replaced_by=[])
        self.catalog['versions'].append(item)
        self.assertEqual(self.query_on('2026-08-10')['status'],'ambiguous')
    def test_boundary_contradiction(self):
        self.catalog['versions'][0]['effective_until']='2026-01-01'
        with self.assertRaises(ValueError):validate_catalog(self.catalog)
    def test_unknown_publication_not_verified(self):
        self.catalog['versions'][1]['published_at']=None
        with self.assertRaises(ValueError):validate_catalog(self.catalog)
    def test_event_handoff_version(self):
        doc=json.loads((ROOT/'interfaces/examples/inquiry-correction.json').read_text(encoding='utf-8'))
        result=validate(doc)
        self.assertEqual(result['rule_selections'][0]['rule_version_id'],'SZSE-REITS-EXP-2025')
        self.assertEqual(result['unknown_field_count'],6)
    def test_wrong_recorded_version(self):
        doc=json.loads((ROOT/'interfaces/examples/reits-terms.json').read_text(encoding='utf-8'));doc['records'][0]['rule_version_id']='SSE-REITS-EXP-2022'
        with self.assertRaises(ValueError):validate(doc)
    def test_wrong_source_version(self):
        doc=json.loads((ROOT/'interfaces/examples/reits-terms.json').read_text(encoding='utf-8'));doc['sources'][0]['rule_version_id']='SSE-REITS-EXP-2022'
        with self.assertRaisesRegex(ValueError,'source rule_version_id'):validate(doc)
    def test_old_envelope_does_not_reinterpret_extension(self):
        doc=json.loads((ROOT/'interfaces/examples/risk-events.json').read_text(encoding='utf-8'))
        for version in ('1.0','1.1'):
            doc['schema_version']=version;doc['records'][0]['rule_query']='legacy opaque extension'
            self.assertNotIn('rule_selections',validate(doc))
    def test_backtest_rejects_later_rule_knowledge(self):
        doc=json.loads((ROOT/'interfaces/examples/inquiry-correction.json').read_text(encoding='utf-8'));doc['records'][0]['backtest_cutoff']='2026-08-10T16:00:00+08:00'
        with self.assertRaisesRegex(ValueError,'later rule knowledge'):validate(doc)
    def test_real_correction_not_old_public_fact(self):
        doc=json.loads((ROOT/'interfaces/examples/inquiry-correction.json').read_text(encoding='utf-8'));doc['records']=[doc['records'][1]]
        rec=doc['records'][0];rec['backtest_cutoff']='2026-08-26T23:59:59+08:00'
        for fact in rec['facts']:
            if fact['status']!='unknown':fact['available_at']='2026-08-27T00:00:00+08:00'
        with self.assertRaisesRegex(ValueError,'later information'):validate(doc)

if __name__=='__main__':unittest.main()
