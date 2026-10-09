# SPDX-License-Identifier: MIT
"""Versioned read-only filters for the regulatory evidence sample."""
import copy

METHOD_VERSION='regulatory-reader/1.0'
DEFAULT=dict(event_type='all',evidence_status='all',rule_status='all',sort='public_date_desc')
OPTIONS=dict(event_type={'all','inquiry','administrative_penalty','supervisory_measure','audit_opinion','correction'},evidence_status={'all','obtained','not_obtained','embedded'},rule_status={'all','selected','gap'},sort={'public_date_desc','public_date_asc'})

def parameters(value=None):
    result=dict(DEFAULT)
    if value is not None:
        if not isinstance(value,dict) or set(value)-set(DEFAULT):raise ValueError('unknown reader parameter')
        result.update(value)
    for key,allowed in OPTIONS.items():
        if result[key] not in allowed:raise ValueError('unsupported reader parameter: '+key)
    return result

def filtered(rows,value=None):
    options=parameters(value);result=[]
    for row in rows:
        if options['event_type']!='all' and row['event_type']!=options['event_type']:continue
        if options['evidence_status']!='all' and row['original_document_status']!=options['evidence_status']:continue
        selected=row['rule_application']['status']=='selected'
        if options['rule_status']=='selected' and not selected:continue
        if options['rule_status']=='gap' and selected:continue
        result.append(copy.deepcopy(row))
    known=[r for r in result if r['public_date'] is not None];unknown=[r for r in result if r['public_date'] is None]
    known.sort(key=lambda r:r['record_id']);known.sort(key=lambda r:r['public_date'],reverse=options['sort']=='public_date_desc')
    unknown.sort(key=lambda r:r['record_id'])
    return known+unknown
