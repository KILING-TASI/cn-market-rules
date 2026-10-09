"""Offline validation of field-level evidence. No valuation or risk inference."""
import argparse
import json
from datetime import date
from decimal import Decimal,InvalidOperation
from pathlib import Path

def text(obj,key):
    value=obj.get(key)
    if not isinstance(value,str) or not value.strip():raise ValueError(f'{key}: required text')
    return value

def day(value,label,nullable=False):
    if nullable and value is None:return None
    if not isinstance(value,str):raise ValueError(f'{label}: ISO date required')
    try:return date.fromisoformat(value)
    except ValueError:raise ValueError(f'{label}: invalid date') from None

def validate(document):
    if not isinstance(document,dict) or document.get('schema_version')!='1.0':raise ValueError('schema_version: 1.0 required')
    kind=text(document,'kind')
    if kind not in {'risk_events','reits_expansion_terms'}:raise ValueError('unsupported interface kind')
    as_of=day(document.get('as_of'),'as_of')
    sources={}
    if not isinstance(document.get('sources'),list):raise ValueError('sources: list required')
    for source in document['sources']:
        if not isinstance(source,dict):raise ValueError('source: object required')
        sid=text(source,'source_id')
        if sid in sources:raise ValueError('duplicate source ID')
        for key in ('title','publisher','version'):text(source,key)
        if source.get('source_type') not in {'rule','company_notice','official_summary','regulatory_decision'}:raise ValueError('source_type invalid')
        if not text(source,'url').startswith(('https://','http://')):raise ValueError('source URL required')
        if 'published_at' not in source:raise ValueError('published_at: explicit date or null required')
        pub=day(source['published_at'],'published_at',True)
        if pub and pub>as_of:raise ValueError('source publication after as_of')
        sources[sid]=source
    records=document.get('records')
    if not isinstance(records,list) or not records:raise ValueError('records: nonempty list required')
    ids=set();unknown=0
    def binding(evidence):
        if not isinstance(evidence,dict):raise ValueError('field evidence required')
        sid=text(evidence,'source_id');text(evidence,'locator')
        if sid not in sources:raise ValueError('unresolved source ID')
        return sources[sid]
    for record in records:
        if not isinstance(record,dict):raise ValueError('record: object required')
        rid=text(record,'record_id')
        if rid in ids:raise ValueError('duplicate record ID')
        ids.add(rid);text(record,'entity_name')
        observed=day(record.get('observation_date'),'observation_date')
        if observed>as_of:raise ValueError('observation after as_of')
        if 'event_date' not in record:raise ValueError('event_date must be explicit date/null')
        day(record['event_date'],'event_date',True)
        if kind=='risk_events':
            if record.get('event_type') not in {'unlock','pledge','goodwill'}:raise ValueError('event_type invalid')
            if record.get('record_role') not in {'company_event','regulatory_observation'}:raise ValueError('record_role invalid')
        else:
            if record.get('market') not in {'SSE','SZSE'}:raise ValueError('market invalid')
            if record.get('offering_method') not in {'holders','public','targeted'}:raise ValueError('offering_method invalid')
            if record.get('rule_check_status') not in {'unknown','partial','verified'}:raise ValueError('rule_check_status invalid')
            inputs=record.get('workbench_inputs')
            if not isinstance(inputs,list) or not inputs or any(not isinstance(v,str) or not v for v in inputs):raise ValueError('workbench_inputs: required data names')
        rules=record.get('rules')
        if not isinstance(rules,list):raise ValueError('rules must be explicit list')
        for rule in rules:
            if binding(rule)['source_type']!='rule':raise ValueError('company event cannot serve as rule source')
            text(rule,'scope')
        facts=record.get('facts');keys=set();original_keys=set();record_unknown=0
        if not isinstance(facts,list) or not facts:raise ValueError('facts required')
        for fact in facts:
            if not isinstance(fact,dict):raise ValueError('fact must be object')
            key=text(fact,'key')
            if key in keys:raise ValueError('duplicate fact key')
            keys.add(key);status=text(fact,'status');text(fact,'unit')
            if status not in {'original','summary','reported','hypothesis','unknown'}:raise ValueError('fact status invalid')
            if 'value' not in fact:raise ValueError('fact value required')
            if status=='unknown':
                if fact['value'] is not None:raise ValueError('unknown must be null, never zero')
                text(fact,'reason');unknown+=1;record_unknown+=1
                continue
            if fact['value'] is None:raise ValueError('known/hypothesis fact cannot be null')
            if status=='hypothesis':text(fact,'reason')
            else:
                source=binding(fact.get('evidence'))
                if status in {'original','reported'} and source['source_type']=='official_summary':raise ValueError('summary cannot certify full original fact')
                if status=='summary' and source['source_type']!='official_summary':raise ValueError('summary requires official_summary source')
                if source['published_at'] and day(source['published_at'],'published_at')>observed:raise ValueError('evidence publication after observation')
                if status=='original' and source['source_type']=='company_notice':original_keys.add(key)
            if fact['unit']=='ratio':
                if isinstance(fact['value'],bool):raise ValueError('ratio must be numeric')
                try:value=Decimal(str(fact['value']))
                except InvalidOperation:raise ValueError('ratio invalid') from None
                if not value.is_finite() or not 0<=value<=1:raise ValueError('ratio outside 0..1')
                text(fact,'denominator');day(fact.get('denominator_date'),'denominator_date')
        if kind=='reits_expansion_terms' and record['rule_check_status']=='verified':
            if record_unknown or not rules or not {'expansion_price','approved_units','offering_method'}.issubset(original_keys):
                raise ValueError('verified requires original project price/units/route, rules and no unknowns')
    return {'kind':kind,'record_count':len(records),'unknown_field_count':unknown,
            'status':'structure_valid_only','scope':'no source authenticity certification, liquidation price, fraud classification, valuation or execution'}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);args=parser.parse_args()
    try:result=validate(json.loads(args.input.read_text(encoding='utf-8-sig')))
    except (ValueError,TypeError,OSError) as e:parser.exit(2,f'Invalid evidence: {e}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
