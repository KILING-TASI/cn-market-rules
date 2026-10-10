# SPDX-License-Identifier: MIT
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_distribution import audit

class AuditTests(unittest.TestCase):
    def fixture(self,root,extra=None):
        files={'LICENSE':(ROOT/'LICENSE').read_text(encoding='utf-8'),'THIRD_PARTY_NOTICES.md':'Original only, third-party rights excluded.','licenses/README.md':'No bundled third-party code.','script.py':'# SPDX-License-Identifier: MIT\nimport json\n'}
        files.update(extra or {})
        for name,content in files.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8')
        entries={name:dict(**{'class':'license_text' if name=='LICENSE' else 'original_mit'},basis='synthetic audit fixture') for name in files}
        entries['LICENSE_SCOPE.json']=dict(**{'class':'original_mit'},basis='scope fixture')
        (root/'LICENSE_SCOPE.json').write_text(json.dumps(dict(scope_version='1.0',copyright_holder='KILING-TASI',files=entries)),encoding='utf-8')
    def test_current_inventory(self):self.assertEqual(audit()['external_code_imports'],[])
    def test_unknown_new_file_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root);(root/'unclassified.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'unclassified'):audit(root)
    def test_full_document_not_bundled_even_if_classified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root,{'full-source.pdf':'synthetic'});
            with self.assertRaisesRegex(ValueError,'unapproved'):audit(root)
    def test_vendor_import_requires_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root,{'script.py':'# SPDX-License-Identifier: MIT\nimport third_party_vendor\n'})
            with self.assertRaisesRegex(ValueError,'separate license review'):audit(root)
    def test_missing_original_code_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root,{'script.py':'import json\n'})
            with self.assertRaisesRegex(ValueError,'SPDX'):audit(root)
    def test_private_account_field_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);self.fixture(root,{'data.json':json.dumps({'account_number':'synthetic-private-field-test'})})
            with self.assertRaisesRegex(ValueError,'private credential/account'):audit(root)

if __name__=='__main__':unittest.main()
