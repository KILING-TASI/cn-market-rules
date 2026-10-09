# SPDX-License-Identifier: MIT
"""Check declared distribution scope; not an external rights certification."""
import ast
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','__pycache__','demo-output','local-data'}

def files(root):
    return {str(p.relative_to(root)).replace('\\','/'):p for p in root.rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(root).parts)}

def audit(root=ROOT):
    root=Path(root);manifest=json.loads((root/'LICENSE_SCOPE.json').read_text(encoding='utf-8'))
    if manifest.get('scope_version')!='1.0' or manifest.get('copyright_holder')!='KILING-TASI':raise ValueError('unknown declared scope/holder')
    entries=manifest['files'];inventory=files(root)
    if not {'LICENSE','LICENSE_SCOPE.json','THIRD_PARTY_NOTICES.md','licenses/README.md'}.issubset(inventory):raise ValueError('required license/notices missing')
    if set(entries)!=set(inventory):raise ValueError('unclassified or missing distribution files: '+str(sorted(set(entries)^set(inventory))))
    classes={'original_mit','mixed_source_data','excluded_pending_rights','license_text'}
    imports=set();internal={p.stem for p in inventory.values() if p.suffix=='.py'}|{'contracts'}
    for name,path in inventory.items():
        entry=entries[name]
        if entry.get('class') not in classes or not entry.get('basis'):raise ValueError('missing scope basis: '+name)
        if path.name in {'.env','.netrc','credentials.json','account-cache.json','token.json'}:raise ValueError('private configuration/cache must not be distributed: '+name)
        if path.suffix.lower() in {'.zip','.pdf','.docx','.xlsx','.csv','.db','.sqlite','.ttf','.otf','.woff','.woff2','.exe','.dll'}:raise ValueError('unapproved original/data/dependency file: '+name)
        if path.suffix=='.py':
            source=path.read_text(encoding='utf-8')
            if not source.startswith('# SPDX-License-Identifier: MIT\n'):raise ValueError('original code SPDX missing: '+name)
            if entry['class']!='original_mit':raise ValueError('code not classified original: '+name)
            for node in ast.walk(ast.parse(source)):
                if isinstance(node,ast.Import):imports.update(alias.name.split('.')[0] for alias in node.names)
                elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:imports.add(node.module.split('.')[0])
        if entry['class']=='excluded_pending_rights' and '不声明整文件 MIT' not in path.read_text(encoding='utf-8'):raise ValueError('unresolved file needs in-file notice: '+name)
        if path.suffix=='.json':
            def sensitive_keys(obj):
                if isinstance(obj,dict):
                    for key,value in obj.items():
                        if key.lower() in {'account_number','api_key','access_token','password','broker_credentials'} and value not in (None,'',[]):return True
                        if sensitive_keys(value):return True
                elif isinstance(obj,list):return any(sensitive_keys(value) for value in obj)
                return False
            if sensitive_keys(json.loads(path.read_text(encoding='utf-8'))):raise ValueError('nonempty private credential/account field: '+name)
    external=imports-set(sys.stdlib_module_names)-internal-{'__future__'}
    if external:raise ValueError('external code imports need separate license review: '+str(sorted(external)))
    license_text=(root/'LICENSE').read_text(encoding='utf-8')
    if 'MIT License' not in license_text or 'Copyright (c) 2026 KILING-TASI' not in license_text or '[year]' in license_text:raise ValueError('MIT text/holder not set')
    return dict(status='declared_distribution_scope_valid',file_count=len(inventory),class_counts={c:sum(e['class']==c for e in entries.values()) for c in sorted(classes)},external_code_imports=sorted(external),scope='no certification of all external material rights; MIT only declared original parts')

if __name__=='__main__':
    try:result=audit()
    except (ValueError,KeyError,TypeError,OSError) as error:raise SystemExit(f'Distribution audit failed: {error}')
    print(json.dumps(result,ensure_ascii=False,indent=2))
