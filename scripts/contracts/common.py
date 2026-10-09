"""Lossless common rule/evidence view, preserving the original envelope."""
import copy
import json
from evidence_interface import validate
from .identity import identity
from .units import unit_view

CONTRACT_VERSION='cn-market-rules.rule-handoff/1.0'

def to_common(document):
    validation=validate(document)
    source_index={s['source_id']:s for s in document['sources']}
    source_views=[]
    for source in document['sources']:
        metadata=('source_tier','access_requirement','acquisition_status','original_verification','retrieved_at','verified_at')
        missing=[k for k in metadata if k not in source]
        source_views.append(dict(source_id=source['source_id'],source_type=source['source_type'],title=source['title'],publisher=source['publisher'],url=source['url'],source_version=source['version'],rule_version_id=source.get('rule_version_id'),source_tier=source.get('source_tier'),access_requirement=source.get('access_requirement'),dates=dict(published_at=source['published_at'],retrieved_at=source.get('retrieved_at'),verified_at=source.get('verified_at'),date_timezone='+08:00'),verification=dict(acquisition_status=source.get('acquisition_status'),original_verification=source.get('original_verification'),missing_metadata=missing)))
    selections={s['record_id']:s for s in validation.get('rule_selections',[])}
    records=[]
    for record in document['records']:
        records.append(dict(record_id=record['record_id'],entity_name=record['entity_name'],security_identity=identity(record,source_index),dates=dict(event_date=record['event_date'],observation_date=record['observation_date'],backtest_cutoff=record.get('backtest_cutoff'),date_timezone='+08:00'),facts=copy.deepcopy(record['facts']),unit_semantics=[unit_view(f) for f in record['facts']],rules=copy.deepcopy(record['rules']),rule_selection=copy.deepcopy(selections.get(record['record_id'])),record_type=record.get('event_type',document['kind']),record_role=record.get('record_role'),workbench_inputs=copy.deepcopy(record.get('workbench_inputs'))))
    result=dict(contract_version=CONTRACT_VERSION,origin_interface_version=document['schema_version'],kind=document['kind'],as_of=document['as_of'],sources=source_views,records=records,validation=copy.deepcopy(validation),legacy_payload=copy.deepcopy(document),computation_status='not_migrated; use existing scenario input contract')
    # Reject non-JSON numeric special values; no silent coercion or rounding.
    json.dumps(result,ensure_ascii=False,allow_nan=False)
    return result

def from_common(document):
    if not isinstance(document,dict) or document.get('contract_version')!=CONTRACT_VERSION:raise ValueError('unsupported common contract version')
    original=document.get('legacy_payload')
    expected=to_common(original)
    canonical=lambda obj:json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False,separators=(',',':'))
    if canonical(document)!=canonical(expected):raise ValueError('common view differs from original/versioned payload; do not silently reconcile')
    return copy.deepcopy(original)
