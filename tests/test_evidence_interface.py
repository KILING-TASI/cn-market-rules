import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from evidence_interface import validate

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.events=json.loads((ROOT/'interfaces/examples/risk-events.json').read_text(encoding='utf-8'))
        self.reits=json.loads((ROOT/'interfaces/examples/reits-terms.json').read_text(encoding='utf-8'))
    def rejected(self,document):
        with self.assertRaises(ValueError):validate(document)
    def test_valid_events(self):
        result=validate(self.events)
        self.assertEqual(result['record_count'],3)
        self.assertEqual(result['unknown_field_count'],3)
        self.assertEqual(result['status'],'structure_valid_only')
    def test_valid_partial_handoff(self):self.assertEqual(validate(self.reits)['unknown_field_count'],2)
    def test_unknown_zero_rejected(self):
        self.events['records'][0]['facts'][-1]['value']=0;self.rejected(self.events)
    def test_summary_not_original(self):
        self.events['records'][0]['facts'][0]['status']='original';self.rejected(self.events)
    def test_company_notice_not_rule(self):
        self.events['records'][0]['rules'][0]['source_id']='PLEDGE-GCL';self.rejected(self.events)
    def test_version_required(self):
        self.events['sources'][0].pop('version');self.rejected(self.events)
    def test_unique_source(self):
        self.events['sources'].append(copy.deepcopy(self.events['sources'][0]));self.rejected(self.events)
    def test_observation_not_future(self):
        self.events['records'][0]['observation_date']='2026-10-10';self.rejected(self.events)
    def test_ratio_denominator_required(self):
        self.events['records'][1]['facts'][3].pop('denominator');self.rejected(self.events)
    def test_ratio_bounds(self):
        self.events['records'][1]['facts'][3]['value']='50.96';self.rejected(self.events)
    def test_source_not_yet_observable(self):
        self.events['records'][1]['observation_date']='2026-04-28';self.rejected(self.events)
    def test_verified_rejects_missing_project(self):
        self.reits['records'][0]['rule_check_status']='verified';self.rejected(self.reits)
    def test_rule_source_cannot_certify_project(self):
        rec=self.reits['records'][0];rec['rule_check_status']='verified'
        rec['facts']=[dict(key=k,value=v,unit='text',status='original',evidence=dict(source_id='REITS-EXP-SH',locator='示范')) for k,v in [('expansion_price',1),('approved_units',100),('offering_method','public')]]
        self.rejected(self.reits)
    def test_project_can_be_structurally_verified(self):
        doc=self.reits;rec=doc['records'][0];rec['rule_check_status']='verified'
        project=copy.deepcopy(doc['sources'][0]);project.update(source_id='SYNTHETIC',source_type='company_notice',title='合成测试，非真实公告')
        doc['sources'].append(project)
        rec['facts']=[dict(key=k,value=v,unit='text',status='original',evidence=dict(source_id='SYNTHETIC',locator='测试')) for k,v in [('expansion_price',1),('approved_units',100),('offering_method','public')]]
        self.assertEqual(validate(doc)['status'],'structure_valid_only')

if __name__=='__main__':unittest.main()
