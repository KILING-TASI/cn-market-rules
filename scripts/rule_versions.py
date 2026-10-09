"""Select a source-backed rule version within explicitly verified coverage."""
import argparse
import json
from datetime import date
from pathlib import Path

DEFAULT_CATALOG=Path(__file__).resolve().parents[1]/'rules/version-catalog.json'

def day(value,label,nullable=False):
    if nullable and value is None:return None
    if not isinstance(value,str):raise ValueError(f'{label}: ISO date required')
    try:return date.fromisoformat(value)
    except ValueError:raise ValueError(f'{label}: invalid date') from None

def nonempty(value,label):
    if not isinstance(value,str) or not value.strip():raise ValueError(f'{label}: required text')
    return value

def evidence(value):
    if not isinstance(value,dict):raise ValueError('rule evidence must be object')
    for key in ('source_id','locator'):nonempty(value.get(key),key)

def validate_catalog(catalog):
    if not isinstance(catalog,dict) or catalog.get('schema_version')!='1.0':raise ValueError('rule catalog schema_version 1.0 required')
    checked=day(catalog.get('verified_as_of'),'verified_as_of')
    versions=catalog.get('versions')
    if not isinstance(versions,list) or not versions:raise ValueError('versions required')
    index={}
    for item in versions:
        if not isinstance(item,dict):raise ValueError('version must be object')
        vid=nonempty(item.get('version_id'),'version_id')
        if vid in index:raise ValueError('duplicate version_id')
        index[vid]=item
        for key in ('title','document_version','market','board'):nonempty(item.get(key),key)
        if item['market'] not in {'SSE','SZSE','BSE'}:raise ValueError('market invalid')
        for key in ('subjects','asset_types'):
            if not isinstance(item.get(key),list) or not item[key]:raise ValueError(f'{key}: nonempty list required')
            for value in item[key]:nonempty(value,key)
        if item.get('verification_status') not in {'verified','pending'}:raise ValueError('verification_status invalid')
        dates={}
        for key in ('published_at','effective_from','effective_until'):
            if key not in item:raise ValueError(f'{key}: explicit date/null required')
            dates[key]=day(item[key],key,True)
        if dates['published_at'] and dates['published_at']>checked:raise ValueError('publication beyond verified coverage')
        if item['verification_status']=='verified' and (not dates['published_at'] or not dates['effective_from']):raise ValueError('verified rule requires known publication and effective date')
        if dates['effective_until'] and (not dates['effective_from'] or dates['effective_until']<=dates['effective_from']):raise ValueError('invalid effective interval')
        evidence(item.get('publication_evidence'));evidence(item.get('interval_evidence'))
        for key in ('supersedes','replaced_by'):
            if not isinstance(item.get(key),list):raise ValueError(f'{key}: explicit list required')
            for value in item[key]:nonempty(value,key)
        if not isinstance(item.get('topics'),dict) or not item['topics']:raise ValueError('topics required')
        for topic,terms in item['topics'].items():
            nonempty(topic,'topic')
            if not isinstance(terms,dict) or terms.get('activation') not in {'active','deferred','conditional','unknown'}:raise ValueError('topic activation invalid')
            evidence(terms.get('evidence'));nonempty(terms.get('scope'),'scope')
            if terms['activation']!='active':nonempty(terms.get('reason'),'activation reason')
    for item in versions:
        for old_id in item['supersedes']:
            if old_id not in index:raise ValueError('unresolved superseded version')
            old=index[old_id]
            if item['version_id'] not in old['replaced_by']:raise ValueError('replacement relation must be reciprocal')
            if old['market']!=item['market'] or old['board']!=item['board']:raise ValueError('replacement scope mismatch')
            if old['effective_until']!=item['effective_from']:raise ValueError('replacement boundary mismatch')
        for new_id in item['replaced_by']:
            if new_id not in index or item['version_id'] not in index[new_id]['supersedes']:raise ValueError('replacement relation unresolved')
    def walk(vid,path):
        if vid in path:raise ValueError('replacement cycle')
        for nxt in index[vid]['replaced_by']:walk(nxt,path|{vid})
    for vid in index:walk(vid,set())
    return catalog

def load_catalog(path=DEFAULT_CATALOG):
    return validate_catalog(json.loads(Path(path).read_text(encoding='utf-8-sig')))

def select(catalog,query):
    validate_catalog(catalog)
    if not isinstance(query,dict):raise ValueError('rule query must be object')
    for key in ('topic','market','board','subject','asset_type'):nonempty(query.get(key),key)
    when=day(query.get('applicability_date'),'applicability_date')
    known=day(query.get('knowledge_date'),'knowledge_date')
    checked=day(catalog['verified_as_of'],'verified_as_of')
    if when>known:raise ValueError('future applicability cannot be treated as historical knowledge')
    base=dict(query=dict(query),catalog_version=catalog['schema_version'],catalog_verified_as_of=catalog['verified_as_of'],rule_version_id=None)
    if known>checked or when>checked:return dict(base,status='gap',reason='outside verified coverage; do not extrapolate')
    candidates=[]
    for item in catalog['versions']:
        if item['market']!=query['market'] or item['board']!=query['board'] or query['subject'] not in item['subjects'] or query['asset_type'] not in item['asset_types'] or query['topic'] not in item['topics']:continue
        if item['verification_status']!='verified':continue
        pub=day(item['published_at'],'published_at');start=day(item['effective_from'],'effective_from');end=day(item['effective_until'],'effective_until',True)
        if pub<=known and start<=when and (end is None or when<end):candidates.append(item)
    if not candidates:return dict(base,status='gap',reason='no verified version for supplied scope/date; missing dates are not guessed')
    if len(candidates)>1:return dict(base,status='ambiguous',reason='overlapping applicable versions; manual resolution required',candidate_version_ids=[v['version_id'] for v in candidates])
    item=candidates[0];terms=item['topics'][query['topic']]
    return dict(base,status='selected' if terms['activation']=='active' else terms['activation'],rule_version_id=item['version_id'],document_version=item['document_version'],published_at=item['published_at'],effective_from=item['effective_from'],effective_until=item['effective_until'],supersedes=item['supersedes'],replaced_by=item['replaced_by'],evidence=terms['evidence'],interval_evidence=item['interval_evidence'],scope=terms['scope'],reason=terms.get('reason','version selection only; not legal eligibility certification'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog',type=Path,default=DEFAULT_CATALOG);parser.add_argument('--input',type=Path,required=True);args=parser.parse_args()
    try:result=select(load_catalog(args.catalog),json.loads(args.input.read_text(encoding='utf-8-sig')))
    except (ValueError,TypeError,OSError) as e:parser.exit(2,f'Invalid rule selection: {e}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
