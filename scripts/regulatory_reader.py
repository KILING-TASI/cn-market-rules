# SPDX-License-Identifier: MIT
"""Generate a new read-only regulatory evidence page and versioned snapshots."""
import argparse
import hashlib
import html
import json
import shutil
from datetime import datetime,timezone,timedelta
from pathlib import Path
from evidence_interface import validate
from contracts.common import to_common
from contracts.reader_state import METHOD_VERSION,parameters,filtered

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_INPUT=ROOT/'interfaces/examples/regulatory-events.json'

def generate(output_dir,input_path=DEFAULT_INPUT,settings=None):
    output=Path(output_dir).resolve()
    if output.exists():raise ValueError('output directory exists; choose new output (no overwrite)')
    input_path=Path(input_path);raw=input_path.read_bytes();document=json.loads(raw.decode('utf-8-sig'))
    if document.get('schema_version')!='1.3':raise ValueError('reader requires explicit regulatory interface 1.3')
    result=validate(document)
    if not result.get('regulatory_events'):raise ValueError('no typed regulatory records')
    if len(result['regulatory_events'])!=len(document['records']):raise ValueError('separate non-regulatory records from this typed reader input')
    common=to_common(document)
    if isinstance(settings,dict) and 'method_version' in settings:
        if settings['method_version']!=METHOD_VERSION or settings.get('input_schema_version')!=document['schema_version'] or settings.get('common_contract_version')!=common['contract_version']:raise ValueError('saved reader method/interface version mismatch')
        if settings.get('input_sha256')!=hashlib.sha256(raw).hexdigest():raise ValueError('saved input hash differs; do not silently reuse changed input')
        canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,allow_nan=False)
        if canonical(settings.get('input_snapshot'))!=canonical(document):raise ValueError('saved input snapshot differs from current input')
        options=parameters(settings.get('parameters'))
    else:options=parameters(settings)
    config=dict(method_version=METHOD_VERSION,input_schema_version=document['schema_version'],common_contract_version=common['contract_version'],input_sha256=hashlib.sha256(raw).hexdigest(),generated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),parameters=options,input=document,results=result)
    payload=json.dumps(config,ensure_ascii=False,allow_nan=False).replace('<','\\u003c')
    selectors=[('event_type','类型',[('all','全部类型'),('inquiry','问询'),('administrative_penalty','行政处罚关联'),('audit_opinion','审计意见'),('correction','更正')]),('evidence_status','证据容器',[('all','全部'),('obtained','原公告取得'),('not_obtained','引用决定，原件未得'),('embedded','内嵌审计报告')]),('rule_status','关联核对',[('all','全部'),('selected','证据已核、版本已选'),('gap','关联版本仍有缺口')]),('sort','公开日排序',[('public_date_desc','最新在前'),('public_date_asc','最早在前')])]
    controls=''.join(f'<label>{label}<select id="{key}">'+''.join(f'<option value="{value}">{name}</option>' for value,name in choices)+'</select></label>' for key,label,choices in selectors)
    page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>规则核对示例</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf3ef;color:#19312e;font:15px/1.75 "Microsoft YaHei",sans-serif}}main{{max-width:1120px;margin:auto;padding:30px 24px}}h1{{font-size:30px;margin:8px 0}}h2{{font-size:18px;margin:8px 0}}p{{margin:8px 0}}.meta,.small{{font-size:12px;color:#647772}}.controls{{display:flex;gap:16px;flex-wrap:wrap;padding:18px 0}}label{{font-size:13px}}select{{display:block;margin-top:5px;padding:8px;border:1px solid #ccdcd2;border-radius:6px;background:white;font:inherit}}button{{padding:10px 16px;background:#137761;color:white;border:0;border-radius:6px;font:inherit;cursor:pointer}}#event-list{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:20px}}.card{{background:white;padding:22px;border:1px solid #dce6df;border-radius:12px}}.tag{{font-size:12px;color:#137761;background:#e8f3ee;padding:3px 7px;border-radius:4px}}.note{{font-size:12px;color:#775123;background:#fff5e6;border-left:3px solid #ccad76;padding:10px}}.version,a{{color:#137761}}a{{text-underline-offset:3px}}ul{{padding-left:18px}}@media(max-width:760px){{#event-list{{grid-template-columns:1fr}}main{{padding:20px 16px}}}}footer{{font-size:12px;color:#647772;margin:20px 0}}
</style></head><body><main><header><div class="meta">CN-MARKET-RULES · 制度版本 · 条款核对 · 有限个案示例</div><h1>核对适用规则与原文缺口</h1><p>本库主线是制度、有效版本、条款核对与给定条件情景计算。公司事件时间轴、关联检索与研究解释由 research-workbench 承接；本页仅保留有限的规则适用与证据缺口示例，不扩展为全量事件库、采集器或评分平台。</p><p class="meta">v2.1.0 候选，PR #1 待审 · 资料核验截至 {html.escape(document['as_of'])}<br>生成 {config['generated_at']} · 方法 {METHOD_VERSION} · 接口 1.3／交接 1.1</p></header><p class="note">{len(result['regulatory_events'])} 条源材料摘取记录，只核公开文件日期，首次上网精确时刻未知。引用处罚决定的记录保留原件缺口；审计领域及意见类型分别登记，不代表所有类型已核。问询／整改不升级为处罚，审计非标不升级为造假。</p><div class="controls">{controls}</div><button id="save">另存当前筛选结果与输入</button><span id="saved" class="small" role="status"></span><p id="count" aria-live="polite"></p><section id="event-list"></section><footer><a href="input.json">原始样本输入</a> · <a href="result.json">完整核对结果</a> · <a href="reader-session.json">生成时筛选快照</a> · <a href="https://github.com/KILING-TASI/research-workbench/blob/main/references/practical-entry.md">主工作台问题入口</a><p>筛选仅改变阅读视图，新结果下载不修改冻结报告。原创界面采用 MIT；第三方材料／数据／名称权利独立。不附原文全文、账户或付费资料，不构成交易指令或个案法律判断。</p></footer></main><script id="reader-data" type="application/json">{payload}</script><script src="regulatory-reader.js"></script></body></html>'''
    output.mkdir(parents=True,exist_ok=False)
    (output/'input.json').write_bytes(raw)
    def save(name,value):(output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8',newline='\n')
    save('result.json',result);save('common-handoff.json',common)
    save('reader-session.json',dict(method_version=METHOD_VERSION,input_schema_version=document['schema_version'],common_contract_version=common['contract_version'],input_sha256=config['input_sha256'],generated_at=config['generated_at'],parameters=options,input_snapshot=document,results=filtered(result['regulatory_events'],options)))
    save('report-manifest.json',dict(method_version=METHOD_VERSION,input_schema_version=document['schema_version'],common_contract_version=common['contract_version'],input_sha256=config['input_sha256'],as_of=document['as_of'],generated_at=config['generated_at'],parameters=options,data_class='declared public event excerpts; no exact first-public timestamps',no_overwrite=True))
    (output/'index.html').write_text(page,encoding='utf-8',newline='\n');shutil.copyfile(ROOT/'assets/regulatory-reader.js',output/'regulatory-reader.js')
    return config

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,default=DEFAULT_INPUT);parser.add_argument('--output-dir',type=Path,required=True);parser.add_argument('--settings',type=Path);args=parser.parse_args()
    try:generate(args.output_dir,args.input,json.loads(args.settings.read_text(encoding='utf-8')) if args.settings else None)
    except (ValueError,TypeError,KeyError,OSError) as error:parser.exit(2,f'Reader error: {error}\n下一步：已有输出目录请换新名字；输入或保存会话错误请核对文件路径、schema与方法版本，勿修改冻结快照来绕过核验。\n')
    print(f'cn-market-rules｜已生成有限规则核对阅读页与输入／方法快照。\n结果目录：{args.output_dir.resolve()}\n打开报告：{(args.output_dir / "index.html").resolve()}\n仅展示已提供的证据与缺口，不认证完整原文或项目资格。')
if __name__=='__main__':main()
