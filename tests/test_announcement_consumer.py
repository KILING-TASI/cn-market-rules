# SPDX-License-Identifier: MIT
import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from announcement_consumer import consume


class AnnouncementConsumerTests(unittest.TestCase):
    def test_binding_preservation_and_rejections(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / 'original.bin'
            original.write_bytes(b'synthetic original; not a real PDF')
            digest = hashlib.sha256(original.read_bytes()).hexdigest()
            field = dict(value='0.0003', unit='fraction', source_id='result', professional_extension={'denominator': 'subscribed shares'})
            source = dict(sha256=digest, url='https://example.invalid/source', announcement_number='test-1')
            sidecar = dict(schema='bjx-announcement-sidecar.v1', document_id='BSE:920188:test-1', sha256=digest, official_url=source['url'], publisher='test issuer', source_version={'announcement_number': 'test-1'}, times={key: dict(value=None, precision=None, reason='not obtained') for key in ('published_at', 'historical_available_at')}, native_payload=dict(security='920188', issuer_name='test issuer', documents={'result': source}, fields={'allocation': field}, other_extension=[0, None]))
            review = dict(schema='cn-market-rules.announcement-review/1', source_sha256=digest, source_version='test-1', document_id=sidecar['document_id'], reviewed_native_fields={'allocation': field}, rule_version_id=None, qualification={'value': None, 'reason': 'not checked'})
            frozen = copy.deepcopy(sidecar)
            result = consume(sidecar, review, original)
            self.assertEqual(result['source_attachment'], frozen)
            self.assertEqual(sidecar, frozen)
            self.assertIsNone(result['historical_available_at']['value'])
            for change in ('digest', 'version', 'field', 'qualification', 'review_digest', 'prospective'):
                changed, checked = copy.deepcopy(sidecar), copy.deepcopy(review)
                if change == 'digest': changed['sha256'] = '0' * 64
                if change == 'version': changed['source_version']['announcement_number'] = 'test-2'
                if change == 'field': checked['reviewed_native_fields']['allocation']['value'] = 0
                if change == 'qualification': checked['qualification']['value'] = True
                if change == 'review_digest': checked['source_sha256'] = '0' * 64
                with self.subTest(case=change), self.assertRaises(ValueError):
                    consume(changed, checked, original, change == 'prospective')


if __name__ == '__main__':
    unittest.main()
