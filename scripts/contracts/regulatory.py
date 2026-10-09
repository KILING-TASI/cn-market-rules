# SPDX-License-Identifier: MIT
"""Declared regulatory event types; never infer fraud or a penalty from a signal."""
import copy
from datetime import date

KINDS={
 'inquiry':{'issuer_notice','original_inquiry_letter'},
 'administrative_penalty':{'original_penalty_decision','official_notice_citing_decision','issuer_notice_citing_decision'},
 'supervisory_measure':{'original_supervisory_decision','issuer_notice_citing_measure'},
 'audit_opinion':{'audit_report','embedded_audit_report'},
 'correction':{'issuer_correction_notice'},
}
STAGES={'inquiry':{'received','issued'},'administrative_penalty':{'decision_issued','decision_cited','received'},'supervisory_measure':{'measure_issued','measure_cited'},'audit_opinion':{'opinion_issued'},'correction':{'title_correction','financial_correction','other_correction'}}

def nonempty(value,label):
 if not isinstance(value,str) or not value.strip():raise ValueError(label+': required text')
 return value

def validate_regulatory(record,sources,as_of,selected=None):
 block=record.get('regulatory_event')
 if not isinstance(block,dict):raise ValueError('regulatory_event: object required for typed event')
 kind=record['event_type']
 if block.get('evidence_kind') not in KINDS[kind]:raise ValueError('evidence kind cannot certify this regulatory event type')
 if block.get('process_stage') not in STAGES[kind]:raise ValueError('process stage does not match event type')
 def binding(value):
  if not isinstance(value,dict) or value.get('source_id') not in sources:raise ValueError('regulatory evidence source missing')
  nonempty(value.get('locator'),'regulatory locator')
  return sources[value['source_id']]
 proof=binding(block.get('evidence'))
 if proof['original_verification']!='verified':raise ValueError('typed regulatory event requires checked original evidence container')
 evidence_kind=block['evidence_kind']
 if evidence_kind in {'original_penalty_decision','original_supervisory_decision'} and proof['source_type']!='regulatory_decision':raise ValueError('original decision requires regulator decision source')
 if evidence_kind=='original_inquiry_letter' and proof['source_type']!='regulatory_letter':raise ValueError('original inquiry requires letter source')
 if evidence_kind in {'issuer_notice','issuer_notice_citing_decision','issuer_notice_citing_measure','issuer_correction_notice','embedded_audit_report','official_notice_citing_decision'} and proof['source_type']!='company_notice':raise ValueError('notice/container source type mismatch')
 if evidence_kind=='audit_report' and proof['source_type']!='audit_report':raise ValueError('audit report source required')
 expected='not_obtained' if 'citing_' in evidence_kind else ('embedded' if evidence_kind=='embedded_audit_report' else 'obtained')
 if block.get('original_document_status')!=expected:raise ValueError('cited decision must not be upgraded to obtained original')
 publication=block.get('publication')
 if not isinstance(publication,dict) or 'date' not in publication or 'first_public_at' not in publication:raise ValueError('publication date/time must be explicit')
 public_source=binding(publication.get('evidence'))
 public_date=publication['date']
 if public_date is None:
  if publication.get('precision')!='unknown' or publication['first_public_at'] is not None:raise ValueError('unknown publication cannot contain a timestamp')
  nonempty(publication.get('reason'),'unknown publication reason')
 else:
  if not isinstance(public_date,str):raise ValueError('publication ISO date required')
  public_day=date.fromisoformat(public_date)
  if public_day>as_of or public_day>date.fromisoformat(record['observation_date']):raise ValueError('publication after snapshot/observation')
  if public_source['published_at']!=public_date:raise ValueError('publication date must match bound source public date')
  # First batch records day precision only; no fabricated midnight availability.
  if publication.get('precision')!='day' or publication['first_public_at'] is not None:raise ValueError('day-precision sample cannot certify exact first-public time')
  nonempty(publication.get('reason'),'publication precision reason')
 effect=block.get('legal_effect')
 if not isinstance(effect,dict) or effect.get('status') not in {'unknown','not_applicable','documented'} or 'date' not in effect:raise ValueError('legal effect must be explicit')
 if effect['status']!='documented':
  if effect['date'] is not None:raise ValueError('unknown/not-applicable legal effect must be null')
  nonempty(effect.get('reason'),'legal effect reason')
 else:
  if effect['date'] is None:raise ValueError('documented effect needs date')
  date.fromisoformat(effect['date']);binding(effect.get('evidence'))
  if block['original_document_status']=='not_obtained':raise ValueError('cited-only decision cannot certify legal effect')
  if kind=='audit_opinion':raise ValueError('audit opinion cannot certify administrative legal effect')
 application=block.get('rule_application')
 if not isinstance(application,dict) or application.get('status') not in {'selected','authority_cited','not_checked'}:raise ValueError('rule application status invalid')
 for key in ('version_id','effective_from','effective_until'):
  if key not in application:raise ValueError('rule version/effective interval must be explicit')
 if application.get('relation') not in {'disclosure_obligation','downstream_listing_reference','audit_standard_not_checked','correction_obligation_not_checked','penalty_basis_not_checked','supervisory_basis_not_checked'}:raise ValueError('rule relation invalid')
 if application['status']=='selected':
  if not selected or selected['status']!='selected':raise ValueError('selected regulatory rule requires existing selector result')
  for key,other in [('version_id','rule_version_id'),('effective_from','effective_from'),('effective_until','effective_until')]:
   if application[key]!=selected[other]:raise ValueError('regulatory rule version/interval differs from selector')
 else:
  if any(application[k] is not None for k in ('version_id','effective_from','effective_until')):raise ValueError('unchecked rule cannot invent effective interval/version ID')
  nonempty(application.get('reason'),'rule gap reason')
  if application['status']=='authority_cited':
   binding(application.get('evidence'));nonempty(application.get('reported_version_name'),'reported version name')
 if kind=='audit_opinion':
  if block.get('audit_domain') not in {'financial_statements','internal_control'}:raise ValueError('audit domain must be explicit')
  if block.get('audit_opinion') not in {'unmodified','unmodified_emphasis','qualified','adverse','disclaimer','unknown'}:raise ValueError('audit opinion invalid')
  if record.get('record_role')!='audit_observation':raise ValueError('audit opinion role mismatch')
  labels={'标准的无保留意见':'unmodified','标准无保留意见':'unmodified','无保留意见':'unmodified','保留意见':'qualified','否定意见':'adverse','无法表示意见':'disclaimer','带强调事项段的无保留意见':'unmodified_emphasis'}
  known=next((f for f in record['facts'] if f['key']=='audit_opinion_label' and f['status'] in {'original','reported'}),None)
  if known and known['value'] in labels and labels[known['value']]!=block['audit_opinion']:raise ValueError('audit opinion enum differs from supplied source label')
 if block.get('classification_scope')!='no_fraud_inference':raise ValueError('no fraud classification derived from regulatory signals')
 result=copy.deepcopy(block)
 result.update(record_id=record['record_id'],event_type=kind,public_date=public_date,verification_status='evidence_checked_rule_selected' if application['status']=='selected' else 'evidence_checked_rule_gap',validation='declared_structure_only')
 return result
