# SPDX-License-Identifier: MIT
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from contracts.common import to_common,from_common,CONTRACT_VERSION
from evidence_interface import validate

class CommonTests(unittest.TestCase):
    def setUp(self):self.doc=json.loads((ROOT/'interfaces/examples/risk-events.json').read_text(encoding='utf-8'))
    def test_all_actual_envelopes_roundtrip(self):
        for path in (ROOT/'interfaces/examples').glob('*.json'):
            with self.subTest(path=path.name):
                source=json.loads(path.read_text(encoding='utf-8'))
                restored=from_common(to_common(source))
                self.assertEqual(json.dumps(restored,sort_keys=True),json.dumps(source,sort_keys=True))
                self.assertEqual(validate(restored),validate(source))
    def test_does_not_mutate_input(self):
        before=copy.deepcopy(self.doc);common=to_common(self.doc);common['records'][0]['facts'][0]['value']=0
        self.assertEqual(self.doc,before)
    def test_unknown_identity_not_code_prefix_guess(self):
        result=to_common(self.doc)['records'][1]['security_identity']
        self.assertEqual(result['status'],'unknown');self.assertIsNone(result['market']);self.assertIsNone(result['code'])
    def explicit_identity(self):
        record=self.doc['records'][1]
        record['security_identity']=dict(status='partial',code='002015',market=None,board=None,security_type='stock',name='协鑫能科',reason='证券代码及简称来自公告；市场板块尚未绑定独立身份证据',evidence=dict(source_id='PLEDGE-GCL',locator='PDF第1页页首'))
        return record['security_identity']
    def test_explicit_code_keeps_leading_zero(self):
        self.explicit_identity();result=to_common(self.doc)['records'][1]['security_identity']
        self.assertEqual(result['code'],'002015');self.assertIsNone(result['market'])
    def test_numeric_code_rejected(self):
        self.explicit_identity()['code']=2015
        with self.assertRaises(ValueError):to_common(self.doc)
    def test_scope_mismatch_rejected(self):
        self.explicit_identity().update(market='SZSE',board='STAR')
        with self.assertRaises(ValueError):to_common(self.doc)
    def test_original_identity_cannot_be_partial(self):
        self.explicit_identity()['status']='original'
        with self.assertRaises(ValueError):to_common(self.doc)
    def test_identity_needs_source(self):
        self.explicit_identity()['evidence']['source_id']='UNBOUND'
        with self.assertRaises(ValueError):to_common(self.doc)
    def test_old_source_metadata_not_guessed(self):
        self.doc['schema_version']='1.0'
        for source in self.doc['sources']:
            for key in ('source_tier','access_requirement','acquisition_status','original_verification','retrieved_at','verified_at'):source.pop(key,None)
        result=to_common(self.doc)
        self.assertIsNone(result['sources'][0]['verification']['acquisition_status'])
        self.assertIn('source_tier',result['sources'][0]['verification']['missing_metadata'])
        self.assertEqual(from_common(result),self.doc)
    def test_ratio_not_rescaled_or_rounded(self):
        self.doc['records'][1]['facts'][3]['value']='0.5096000000000000'
        result=to_common(self.doc)['records'][1]
        self.assertEqual(result['facts'][3]['value'],'0.5096000000000000')
        self.assertEqual(result['unit_semantics'][3]['unit_family'],'fraction')
    def test_zero_not_changed_to_unknown(self):
        self.doc['records'][1]['facts'][1]['value']=0
        fact=to_common(self.doc)['records'][1]['facts'][1]
        self.assertEqual(fact['value'],0);self.assertEqual(fact['status'],'original')
    def test_unknown_null_and_reason_preserved(self):
        fact=to_common(self.doc)['records'][1]['facts'][-1]
        self.assertIsNone(fact['value']);self.assertEqual(fact,self.doc['records'][1]['facts'][-1])
    def test_fee_opaque_decimal_string_preserved(self):
        self.doc['records'][1]['facts'].append(dict(key='test_fee',value='0.1234567890123456789',unit='CNY',status='hypothesis',reason='合成测试输入，非实际费率'))
        self.assertEqual(from_common(to_common(self.doc))['records'][1]['facts'][-1],self.doc['records'][1]['facts'][-1])
    def test_native_unmapped_unit_not_guessed(self):
        self.doc['records'][1]['facts'][1]['unit']='万股'
        view=to_common(self.doc)['records'][1]
        self.assertEqual(view['facts'][1]['value'],30000000)
        self.assertEqual(view['unit_semantics'][1]['native_unit'],'万股');self.assertEqual(view['unit_semantics'][1]['unit_family'],'unmapped')
    def test_rule_version_preserved(self):
        doc=json.loads((ROOT/'interfaces/examples/reits-terms.json').read_text(encoding='utf-8'));result=to_common(doc)
        self.assertEqual(result['records'][0]['rule_selection'],validate(doc)['rule_selections'][0])
    def test_view_changes_do_not_silently_override_original(self):
        result=to_common(self.doc);result['records'][0]['facts'][0]['value']=0
        with self.assertRaises(ValueError):from_common(result)
    def test_numeric_type_change_rejected(self):
        result=to_common(self.doc);result['records'][0]['facts'][0]['value']=float(result['records'][0]['facts'][0]['value'])
        with self.assertRaises(ValueError):from_common(result)
    def test_unknown_contract_rejected(self):
        result=to_common(self.doc);result['contract_version']='unknown'
        with self.assertRaises(ValueError):from_common(result)
    def test_result_declares_no_computation_migration(self):
        self.assertEqual(to_common(self.doc)['contract_version'],CONTRACT_VERSION)
        self.assertIn('not_migrated',to_common(self.doc)['computation_status'])

if __name__=='__main__':unittest.main()
