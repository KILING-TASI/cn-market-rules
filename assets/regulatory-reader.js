// SPDX-License-Identifier: MIT
(function(root){
  'use strict';
  const defaults={event_type:'all',evidence_status:'all',rule_status:'all',sort:'public_date_desc'};
  const choices={event_type:['all','inquiry','administrative_penalty','supervisory_measure','audit_opinion','correction'],evidence_status:['all','obtained','not_obtained','embedded'],rule_status:['all','selected','gap'],sort:['public_date_desc','public_date_asc']};
  function parameters(input){
    if(input!==undefined&&input!==null&&(typeof input!=='object'||Array.isArray(input)))throw new Error('参数须为对象');
    const p={...defaults,...input};
    if(Object.keys(p).some(k=>!choices[k]||!choices[k].includes(p[k])))throw new Error('不支持的筛选参数');
    return p;
  }
  function filtered(rows,input){
    const p=parameters(input);
    return rows.filter(r=>(p.event_type==='all'||r.event_type===p.event_type)&&(p.evidence_status==='all'||r.original_document_status===p.evidence_status)&&(p.rule_status==='all'||(p.rule_status==='selected')===(r.rule_application.status==='selected'))).map(r=>JSON.parse(JSON.stringify(r))).sort((a,b)=>{
      if(!a.public_date&&!b.public_date)return a.record_id<b.record_id?-1:a.record_id>b.record_id?1:0;
      if(!a.public_date)return 1;if(!b.public_date)return -1;
      if(a.public_date===b.public_date)return a.record_id<b.record_id?-1:a.record_id>b.record_id?1:0;
      return (a.public_date<b.public_date?-1:1)*(p.sort==='public_date_desc'?-1:1);
    });
  }
  const api={method_version:'regulatory-reader/1.0',parameters,filtered};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  root.RegulatoryReader=api;
  if(typeof document==='undefined')return;
  const dataNode=document.getElementById('reader-data');if(!dataNode)return;
  const data=JSON.parse(dataNode.textContent),list=document.getElementById('event-list');
  const names={inquiry:'问询',administrative_penalty:'行政处罚关联',supervisory_measure:'监管措施',audit_opinion:'审计意见',correction:'更正'};
  const proofNames={issuer_notice:'收到问询公告',issuer_correction_notice:'原更正公告',official_notice_citing_decision:'交易所正式通知援引；处罚决定原件未得',embedded_audit_report:'年报内嵌财务审计报告'};
  function state(){const p={};for(const k of Object.keys(defaults))p[k]=document.getElementById(k).value;return parameters(p);}
  function text(tag,value,parent,cls){const e=document.createElement(tag);e.textContent=value;if(cls)e.className=cls;parent.appendChild(e);return e;}
  function render(){
    const rows=filtered(data.results.regulatory_events,state());list.replaceChildren();
    document.getElementById('count').textContent=`显示 ${rows.length} / ${data.results.record_count} 条；筛选只改变阅读视图，不改历史底稿。`;
    if(!rows.length){text('p','没有匹配记录。本样本不覆盖全部监管类型，不能据此判断不存在相关事件。',list,'note');return;}
    for(const r of rows){
      const original=data.input.records.find(x=>x.record_id===r.record_id),card=document.createElement('article');card.className='card';list.appendChild(card);
      text('span',names[r.event_type],card,'tag');text('h2',original.entity_name,card);
      text('p',`公开文件日：${r.public_date||'未知'}（精度：${r.publication.precision==='day'?'日':'未确认'}，首次上网时刻未核）`,card);
      text('p',`证据：${proofNames[r.evidence_kind]||r.evidence_kind}；${r.evidence.source_id} · ${r.evidence.locator}`,card,'small');
      const application=r.rule_application;
      const end=application.effective_until?`至 ${application.effective_until}（不含该日）`:`终止日未登记，仅截至 ${data.input.as_of} 覆盖`;
      text('p',application.status==='selected'?`关联版本：${application.version_id}；${application.effective_from} 起，${end}。`:`关联规则待核：${application.reported_version_name||'未独立核版本'}；生效区间未知。`,card,'version');
      if(application.reason)text('p',application.reason,card,'note');
      text('p',`个案法律生效：${r.legal_effect.status==='documented'?r.legal_effect.date:(r.legal_effect.status==='not_applicable'?'本记录不作行政生效判断':'未知')}。${r.legal_effect.reason||''}`,card,'small');
      if(r.audit_opinion)text('p',`${r.audit_domain==='internal_control'?'内部控制':'财务报表'}审计意见：${original.facts.find(f=>f.key==='audit_opinion_label')?.value||'未知'}。意见事实不等于退市或造假认定。`,card);
      const ul=document.createElement('ul');card.appendChild(ul);
      for(const f of original.facts.filter(f=>f.status==='unknown'))text('li',f.reason,ul,'small');
      const a=document.createElement('a');a.textContent='查看对应原发布者材料 →';a.href=data.input.sources.find(s=>s.source_id===r.evidence.source_id).url;a.target='_blank';a.rel='noopener';card.appendChild(a);
    }
  }
  for(const k of Object.keys(defaults)){document.getElementById(k).value=data.parameters[k];document.getElementById(k).addEventListener('change',render);}
  document.getElementById('save').addEventListener('click',()=>{
    const generated_at=new Date().toISOString(),p=state(),saved={method_version:api.method_version,input_schema_version:data.input.schema_version,common_contract_version:data.common_contract_version,input_sha256:data.input_sha256,generated_at,parameters:p,input_snapshot:data.input,results:filtered(data.results.regulatory_events,p),scope:'阅读视图快照；不评分、不推断造假、不覆盖历史结果'};
    const url=URL.createObjectURL(new Blob([JSON.stringify(saved,null,2)+'\n'],{type:'application/json;charset=utf-8'})),a=document.createElement('a');
    a.href=url;a.download='regulatory-reader-'+generated_at.replace(/[-:.]/g,'')+'.json';a.click();URL.revokeObjectURL(url);
    document.getElementById('saved').textContent='已创建新结果下载，内含原输入、筛选参数、方法版本与输入摘要；冻结报告未修改。';
  });
  render();
})(typeof globalThis!=='undefined'?globalThis:this);
