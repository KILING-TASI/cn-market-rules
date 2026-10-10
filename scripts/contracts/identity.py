# SPDX-License-Identifier: MIT
"""Explicit security identity. Never infer a venue from a code prefix."""
import copy

FIELDS=('code','market','board','security_type','name')
BOARDS={'SSE':{'MAIN','STAR','REITS','FUND'},'SZSE':{'MAIN','GEM','REITS','FUND'},'BSE':{'BSE'}}

def identity(record,sources):
    supplied=record.get('security_identity')
    if supplied is None:
        return dict(status='unknown',**{k:None for k in FIELDS},reason='explicit security identity not supplied; issuer name and code prefix are not substitutes',evidence=None)
    if not isinstance(supplied,dict) or supplied.get('status') not in {'partial','original','unknown'}:raise ValueError('security_identity status invalid')
    result=copy.deepcopy(supplied)
    for key in FIELDS:
        if key not in result:raise ValueError(f'security_identity {key}: explicit text/null required')
        if result[key] is not None and (not isinstance(result[key],str) or not result[key].strip()):raise ValueError('identity values must be nonempty text/null; preserve code as text')
    if result['market'] is not None and result['market'] not in BOARDS:raise ValueError('identity market invalid')
    if result['board'] is not None and result['board'] not in set().union(*BOARDS.values()):raise ValueError('identity board invalid')
    if result['market'] and result['board'] and result['board'] not in BOARDS[result['market']]:raise ValueError('identity market/board mismatch')
    if result['security_type'] is not None and result['security_type'] not in {'stock','convertible_bond','reit','fund','other'}:raise ValueError('identity security_type invalid')
    known=[key for key in FIELDS if result[key] is not None]
    if result['status']=='unknown' and known:raise ValueError('unknown identity cannot contain known values')
    if result['status']=='original' and len(known)!=len(FIELDS):raise ValueError('original identity requires all fields')
    if result['status']=='partial' and not known:raise ValueError('partial identity requires at least one known field')
    if result['status']!='original' and (not isinstance(result.get('reason'),str) or not result['reason'].strip()):raise ValueError('partial/unknown identity needs reason')
    if known:
        evidence=result.get('evidence')
        if not isinstance(evidence,dict) or evidence.get('source_id') not in sources or not isinstance(evidence.get('locator'),str) or not evidence['locator'].strip():raise ValueError('known identity requires source and locator')
        if result['status']=='original' and sources[evidence['source_id']].get('original_verification')!='verified':raise ValueError('original identity needs verified original source')
    else:result['evidence']=None
    return result
