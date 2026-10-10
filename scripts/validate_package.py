# SPDX-License-Identifier: MIT
"""Validate local Markdown references, source IDs, UTF-8 and runnable examples."""
import json
import re
import hashlib
from pathlib import Path
from scenarios import run,load_calendar,apply_calendar
from evidence_interface import validate as validate_evidence
from rule_versions import load_catalog,select
from contracts.common import to_common,from_common
from audit_distribution import audit as audit_distribution,files as distribution_files

ROOT=Path(__file__).resolve().parents[1]
errors=[]
mds=[path for path in distribution_files(ROOT).values() if path.suffix=='.md']
for path in mds:
    text=path.read_text(encoding='utf-8')
    if '\ufffd' in text: errors.append(f'{path}: replacement character')
    for link in re.findall(r'\]\(([^)]+)\)',text):
        if link.startswith(('http://','https://','#','mailto:')): continue
        if not (path.parent/link.split('#')[0]).is_file(): errors.append(f'{path}: missing {link}')
sources=(ROOT/'references/sources.md').read_text(encoding='utf-8')
source_ids=set(re.findall(r'^\| ([A-Z][A-Z0-9-]+) \|',sources,re.M))
for path in mds:
    text=path.read_text(encoding='utf-8')
    for group in re.findall(r'\[([^\]]+)\]\([^)]*sources\.md\)',text):
        for source_id in re.findall(r'\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)+\b|\bREPO\b|\bTAKEOVER\b',group):
            if source_id not in source_ids: errors.append(f'{path}: unresolved source {source_id}')
for path in (ROOT/'examples').glob('*.json'):
    try:
        document=json.loads(path.read_text(encoding='utf-8'))
        if 'validation_calendar' in document:
            calendar_path=(path.parent/document['validation_calendar']).resolve()
            if not calendar_path.is_relative_to(ROOT):raise ValueError('validation calendar outside package')
            document=apply_calendar(document,load_calendar(calendar_path))
        run(document)
    except (ValueError,KeyError,TypeError) as e: errors.append(f'{path}: {e}')
for path in (ROOT/'interfaces/examples').glob('*.json'):
    try:
        document=json.loads(path.read_text(encoding='utf-8'))
        validate_evidence(document)
        if from_common(to_common(document))!=document:raise ValueError('common conversion not equivalent')
        if any(s['source_id'] not in source_ids for s in document['sources']):raise ValueError('interface source ID not registered')
    except (ValueError,KeyError,TypeError) as e:errors.append(f'{path}: {e}')
for path in (ROOT/'interfaces/common-inputs').glob('*.json'):
    try:
        document=json.loads(path.read_text(encoding='utf-8'))
        projected=to_common(document)
        saved=json.loads((ROOT/'interfaces/common-examples'/path.name).read_text(encoding='utf-8'))
        if projected!=saved:raise ValueError('saved common conversion differs from current contract')
        if from_common(saved)!=document:raise ValueError('common reverse differs from same input')
        if any(s['source_id'] not in source_ids for s in document['sources']):raise ValueError('common input source ID not registered')
    except (ValueError,KeyError,TypeError) as e:errors.append(f'{path}: {e}')
try:
    catalog=load_catalog()
    for version in catalog['versions']:
        bindings=[version['publication_evidence'],version['interval_evidence']]+[topic['evidence'] for topic in version['topics'].values()]
        if any(b['source_id'] not in source_ids for b in bindings):raise ValueError('catalog source ID not registered')
    select(catalog,json.loads((ROOT/'rules/example-query.json').read_text(encoding='utf-8')))
except (ValueError,KeyError,TypeError) as e:errors.append(f'rule catalog: {e}')
for path in (ROOT/'calendars').glob('*.json'):
    try:
        document=json.loads(path.read_text(encoding='utf-8'))
        load_calendar(path)
        if document['source_id'] not in source_ids:raise ValueError('calendar source ID not registered')
    except (ValueError,KeyError,TypeError) as e:errors.append(f'{path}: {e}')
preview=ROOT/'docs/preview'
if preview.exists():
    try:
        manifest=json.loads((preview/'screenshot-manifest.json').read_text(encoding='utf-8'))
        if manifest['report_sha256']!=hashlib.sha256((preview/'index.html').read_bytes()).hexdigest():raise ValueError('screenshot report bytes changed; recapture/review required')
        for shot in manifest['screenshots']:
            path=(preview/shot['path']).resolve()
            if not path.is_relative_to(preview.resolve()):raise ValueError('screenshot path outside preview')
            if shot['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('screenshot hash mismatch')
        report=json.loads((preview/'report-manifest.json').read_text(encoding='utf-8'))
        for item in report['inputs']:
            path=(ROOT/item['path']).resolve()
            if not path.is_relative_to(ROOT):raise ValueError('preview input outside package')
            if item['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('preview input changed; regenerate/review required')
    except (ValueError,KeyError,TypeError,OSError) as e:errors.append(f'preview: {e}')
preview_assets={preview/'index.html',preview/'overview.jpg',preview/'cash.jpg',preview/'fullpage.jpg'}
reader_preview=ROOT/'docs/regulatory-preview'
preview_assets|={reader_preview/'index.html',reader_preview/'regulatory-reader.js',reader_preview/'overview.jpg',reader_preview/'penalty-filter.jpg',ROOT/'assets/regulatory-reader.js'}
if reader_preview.exists():
    try:
        manifest=json.loads((reader_preview/'report-manifest.json').read_text(encoding='utf-8'))
        document=json.loads((reader_preview/'input.json').read_text(encoding='utf-8'))
        if manifest['input_sha256']!=hashlib.sha256((reader_preview/'input.json').read_bytes()).hexdigest():raise ValueError('reader input hash mismatch')
        if json.loads((reader_preview/'result.json').read_text(encoding='utf-8'))!=validate_evidence(document):raise ValueError('reader saved result differs')
        if from_common(json.loads((reader_preview/'common-handoff.json').read_text(encoding='utf-8')))!=document:raise ValueError('reader common conversion differs')
        if (reader_preview/'regulatory-reader.js').read_bytes()!=(ROOT/'assets/regulatory-reader.js').read_bytes():raise ValueError('reader script/version differs')
        from contracts.reader_state import filtered,METHOD_VERSION
        session=json.loads((reader_preview/'reader-session.json').read_text(encoding='utf-8'))
        if session['method_version']!=METHOD_VERSION or session['input_snapshot']!=document or session['results']!=filtered(validate_evidence(document)['regulatory_events'],session['parameters']):raise ValueError('reader session differs from saved input/method')
        if (reader_preview/'screenshot-manifest.json').exists():
            shots=json.loads((reader_preview/'screenshot-manifest.json').read_text(encoding='utf-8'))
            for name,key in [('index.html','report_sha256'),('regulatory-reader.js','script_sha256')]:
                if shots[key]!=hashlib.sha256((reader_preview/name).read_bytes()).hexdigest():raise ValueError('reader screenshot/source changed; recapture/review required')
            for shot in shots['screenshots']:
                path=(reader_preview/shot['path']).resolve()
                if not path.is_relative_to(reader_preview.resolve()) or shot['sha256']!=hashlib.sha256(path.read_bytes()).hexdigest():raise ValueError('reader screenshot hash/path mismatch')
    except (ValueError,KeyError,TypeError,OSError) as e:errors.append(f'regulatory reader: {e}')
for path in distribution_files(ROOT).values():
    if path.suffix.lower() not in {'.md','.json','.py','.yml','.yaml','.gitignore'} and path.name not in {'.gitignore','.gitattributes'} and path not in preview_assets and path not in {ROOT/'LICENSE',ROOT/'pyproject.toml',ROOT/'MANIFEST.in'}:
        errors.append(f'unexpected distribution file: {path}')
if (ROOT/'LICENSE_SCOPE.json').exists():
    try:audit_distribution(ROOT)
    except (ValueError,KeyError,TypeError,OSError) as e:errors.append(f'distribution scope: {e}')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print(f'Validated {len(mds)} Markdown files, {len(source_ids)} source IDs and all example inputs.')
