"""Validate local Markdown references, source IDs, UTF-8 and runnable examples."""
import json
import re
from pathlib import Path
from scenarios import run,load_calendar,apply_calendar

ROOT=Path(__file__).resolve().parents[1]
errors=[]
mds=list(ROOT.rglob('*.md'))
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
for path in (ROOT/'calendars').glob('*.json'):
    try:
        document=json.loads(path.read_text(encoding='utf-8'))
        load_calendar(path)
        if document['source_id'] not in source_ids:raise ValueError('calendar source ID not registered')
    except (ValueError,KeyError,TypeError) as e:errors.append(f'{path}: {e}')
for path in ROOT.rglob('*'):
    if path.is_file() and path.suffix.lower() not in {'.md','.json','.py','.yml','.yaml','.gitignore'} and path.name!='.gitignore' and '.git' not in path.parts and '__pycache__' not in path.parts:
        errors.append(f'unexpected distribution file: {path}')
if errors:
    print('\n'.join(errors))
    raise SystemExit(1)
print(f'Validated {len(mds)} Markdown files, {len(source_ids)} source IDs and all example inputs.')
