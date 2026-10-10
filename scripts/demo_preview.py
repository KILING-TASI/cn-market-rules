# SPDX-License-Identifier: MIT
"""Build a readable offline preview from existing verified/sample inputs."""
import argparse
import hashlib
import html
import json
import subprocess
from datetime import datetime,timezone,timedelta
from decimal import Decimal
from pathlib import Path
from evidence_interface import validate
from rule_versions import load_catalog,select
from scenarios import run

ROOT=Path(__file__).resolve().parents[1]
VERSION='2.1.0 candidate (PR #1, unreleased)'
INPUTS={'rule':'rules/example-query.json','events':'interfaces/examples/inquiry-correction.json','cash':'examples/cash-ledger.json'}
WORKBENCH='https://github.com/KILING-TASI/research-workbench/blob/main/references/practical-entry.md'
DATE_LABELS={'inquiry_received_date':'收到问询','notice_document_date':'公告落款','public_notice_date':'公开刊登'}

def read(path):return json.loads(path.read_text(encoding='utf-8'),parse_float=Decimal)
def escape(value):return html.escape(str(value),quote=True)
def money(value):return format(Decimal(str(value)),',.2f')
def write_json(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

def make_html(rule,event_input,event_result,cash,manifest,cash_input):
    balance_statement='现金未出现负余额' if Decimal(cash['minimum_balance'])>=0 else '现金出现负余额'
    buffer_statement='低于' if Decimal(cash['maximum_buffer_gap'])>0 else '未低于'
    cash_note=f'{balance_statement}，但最低 {money(cash["minimum_balance"])} 元{buffer_statement}预设 {money(cash_input["minimum_buffer"])} 元缓冲。退款只有已确认可用才进入本账本；不能用待退款或持仓市值补上午资金。'
    erows=[]
    for record in event_input['records']:
        known=[f for f in record['facts'] if f['status']!='unknown']
        unknown=[f for f in record['facts'] if f['status']=='unknown']
        dates=[f for f in known if f['unit']=='date']
        proof=' · '.join(f'{escape(DATE_LABELS.get(f["key"],f["key"]))}：{escape(f["value"])}' for f in dates)
        gaps='；'.join(escape(f['reason']) for f in unknown)
        binding=next((s for s in event_result.get('rule_selections',[]) if s['record_id']==record['record_id']),None)
        version=escape(binding['rule_version_id']) if binding else '未绑定规则版本，保留个案证据'
        erows.append(f'<article class="event"><h3>{escape(record["entity_name"])}</h3><p>{proof}</p><p class="version">{version}</p><p class="note">未知：{gaps}</p></article>')
    cash_rows=''.join(f'<tr class="{"stress" if Decimal(row["buffer_gap"])>0 else ""}"><td>{escape(row["at"].replace("T"," "))}</td><td>{escape(row["name"])}</td><td class="num">{money(row["balance"])}</td><td class="num">{money(row["buffer_gap"])}</td></tr>' for row in cash['trajectory'])
    source_rows=''.join(f'<li><a href="{escape(s["url"])}">{escape(s["source_id"])}</a> · {escape(s["version"])} · 原文核验 {escape(s["original_verification"])}，取得 {escape(s["retrieved_at"])}{(" · 公开日期未知" if s["published_at"] is None else " · 公布 "+escape(s["published_at"]))}</li>' for s in event_input['sources'])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>规则与现金核对｜cn-market-rules 演示</title>
<style>
:root{{--ink:#19312e;--muted:#647772;--green:#137761;--bg:#edf3ef;--line:#dce6df;--amber:#986019}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "Microsoft YaHei","PingFang SC",sans-serif}}main{{max-width:1120px;margin:auto;padding:32px 28px 48px}}h1{{font-size:32px;line-height:1.3;margin:8px 0 14px}}h2{{font-size:20px;margin:0 0 16px}}h3{{font-size:15px;margin:0 0 7px}}p{{margin:8px 0}}a{{color:var(--green);text-underline-offset:3px;overflow-wrap:anywhere}}.eyebrow{{font-size:12px;letter-spacing:1px;color:var(--green);font-weight:700}}.meta{{font-size:12px;color:var(--muted)}}.hero{{padding-bottom:22px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.card{{background:white;border:1px solid var(--line);border-radius:14px;padding:24px}}.tag{{display:inline-block;font-size:12px;padding:3px 10px;border-radius:5px;background:#e8f3ee;color:var(--green);margin-bottom:12px}}.tag.amber{{color:var(--amber);background:#fff1df}}.value{{font-size:22px;font-weight:700;overflow-wrap:anywhere;line-height:1.45}}.small{{font-size:12px;color:var(--muted)}}dl{{display:grid;grid-template-columns:82px 1fr;gap:8px 12px;margin:16px 0}}dt{{color:var(--muted)}}dd{{margin:0;overflow-wrap:anywhere}}.note{{border-left:3px solid #ccad76;background:#fff8ec;padding:9px 12px;font-size:12px;color:#775123}}.event{{padding:12px 0;border-top:1px solid var(--line)}}.event p{{font-size:12px}}.version{{color:var(--green)}}.section{{margin-top:20px}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:20px 0}}.metric{{background:#f3f7f4;padding:16px;border-radius:8px}}.metric strong{{display:block;font-size:26px;color:var(--green)}}.metric.warn strong{{color:#a3561d}}table{{width:100%;border-collapse:collapse;font-size:13px}}th,td{{padding:12px 10px;border-bottom:1px solid var(--line);text-align:left}}th{{color:var(--muted);font-weight:500}}.num{{text-align:right;font-variant-numeric:tabular-nums}}.stress{{background:#fff3e3}}ul{{padding-left:20px}}li{{margin:7px 0}}.footer{{font-size:12px;color:var(--muted);margin-top:20px}}.downloads{{display:flex;gap:15px;flex-wrap:wrap;font-size:13px}}@media(max-width:760px){{main{{padding:20px 16px}}.grid{{grid-template-columns:1fr}}.card{{padding:18px}}.metrics{{grid-template-columns:1fr}}.table-wrap{{overflow-x:auto}}h1{{font-size:27px}}}}
</style></head><body><main>
<header class="hero"><div class="eyebrow">CN-MARKET-RULES · 可复核的规则与个案</div><h1>核对规则版本与现金占用</h1><p>先确认适用版本，再记录事实、未知项与资金时点。</p><div class="meta">v2.1.0 候选 · PR #1 待审，main 已发布 v2.0.0<br>规则核验截至 {escape(manifest['verified_as_of'])} · 生成 {escape(manifest['generated_at'])} · 基线 {escape((manifest['base_commit'] or '无 Git 信息')[:8])}</div></header>
<div class="grid"><section class="card"><span class="tag">规则查询演示 · 已核规则</span><h2>切换当日采用哪个版本？</h2><div class="value">{escape(rule['rule_version_id'])}</div><dl><dt>选择状态</dt><dd>适用版本已选取 · 仅版本选取</dd><dt>适用范围</dt><dd>沪市 REITs · 基金管理人 · 基础设施</dd><dt>判断日期</dt><dd>{escape(rule['query']['applicability_date'])}</dd><dt>生效区间</dt><dd>{escape(rule['effective_from'])} 起；终止日未登记，仅截至 {escape(rule['catalog_verified_as_of'])} 覆盖</dd><dt>替代旧版</dt><dd>{escape(', '.join(rule['supersedes']))}</dd><dt>原文定位</dt><dd>{escape(rule['evidence']['source_id'])} · {escape(rule['evidence']['locator'])}</dd></dl><p class="note">新通知公布与生效均为 2025-12-31。选中版本不代表项目审批、账户资格或定价已通过；暂缓条文需另查实施通知。</p><a href="rule-selection.json">完整结果与更替依据 →</a></section>
<section class="card"><span class="tag">真实公告摘取 · 非实时全市场库</span><h2>问询与更正：日期各有含义</h2><p class="small">{event_result['record_count']} 条原文例证 · {event_result['unknown_field_count']} 个未知字段 · 结构检查通过</p>{''.join(erows)}<a href="event-evidence.json">字段、来源与未知理由 →</a></section></div>
<section class="card section" id="cash"><span class="tag amber">教学现金情景 · 全部金额／支付与退款时点均为假设</span><h2>下午退款不覆盖上午的缓冲需求</h2><p class="small">v2.1.0 候选 · 生成 {escape(manifest['generated_at'])}<br>金额：人民币元。按原现金事件账本计算，不是收益、损失预测或真实账户余额。</p><div class="metrics"><div class="metric"><span>期末可用现金</span><strong>{money(cash['final_cash'])}</strong></div><div class="metric"><span>过程中最低余额</span><strong>{money(cash['minimum_balance'])}</strong></div><div class="metric warn"><span>最大缓冲缺口</span><strong>{money(cash['maximum_buffer_gap'])}</strong></div></div><div class="table-wrap"><table><thead><tr><th>时点（Asia/Shanghai）</th><th>事件</th><th class="num">可用余额</th><th class="num">缓冲缺口</th></tr></thead><tbody>{cash_rows}</tbody></table></div><p class="note">{escape(cash_note)}</p><a href="cash-scenario.json">原计算结果 →</a></section>
<section class="card section"><h2>来源、输入与继续研究</h2><ul>{source_rows}</ul><div class="downloads"><a href="inputs/rule-query.json">规则查询输入</a><a href="inputs/event-evidence.json">事件输入</a><a href="inputs/cash-ledger.json">教学现金输入</a><a href="report-manifest.json">输入哈希与生成说明</a></div><p><a href="{WORKBENCH}">进入主工作台：按研究问题选择入口 →</a></p><p class="small">本页只复制自编条款摘取和教学输入，不附原公告全文、账户或付费资料。旧更正原版本、精确首发时刻与问询实际实施时刻尚未取得。</p></section>
<footer class="footer">仅供规则核对、公开信息研究与教学，不构成交易指令、法律税务意见或收益保证。JSON 与原命令入口继续独立可用。</footer></main></body></html>'''

def generate(output_dir):
    output=Path(output_dir).resolve()
    if output.exists():raise ValueError('output directory already exists; choose a new directory (no overwrite)')
    documents={key:read(ROOT/path) for key,path in INPUTS.items()}
    catalog=load_catalog();rule=select(catalog,documents['rule']);events=validate(documents['events']);cash=run(documents['cash'])
    if rule['status']!='selected':raise ValueError('built-in rule sample is not selectable')
    try:
        git_root=subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip()
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip() if Path(git_root).resolve()==ROOT else None
    except (OSError,subprocess.CalledProcessError):commit=None
    manifest=dict(preview_version='1.0',package_version=VERSION,verified_as_of=catalog['verified_as_of'],generated_at=datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),base_commit=commit,inputs=[dict(role=k,path=p,sha256=hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),data_class='teaching assumptions' if k=='cash' else 'source-backed rule query or public notice excerpts') for k,p in INPUTS.items()],outputs=['index.html','rule-selection.json','event-evidence.json','cash-scenario.json'],scope='read-only derived preview; no original full text, account data, live retrieval or trading')
    rendered=make_html(rule,documents['events'],events,cash,manifest,documents['cash'])
    output.mkdir(parents=True,exist_ok=False);(output/'inputs').mkdir()
    for key,name in [('rule','rule-query.json'),('events','event-evidence.json'),('cash','cash-ledger.json')]:
        (output/'inputs'/name).write_bytes((ROOT/INPUTS[key]).read_bytes())
    for name,value in [('rule-selection.json',rule),('event-evidence.json',events),('cash-scenario.json',cash),('report-manifest.json',manifest)]:write_json(output/name,value)
    (output/'index.html').write_text(rendered,encoding='utf-8',newline='\n')
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output-dir',required=True,type=Path);args=parser.parse_args()
    try:generate(args.output_dir)
    except (ValueError,TypeError,OSError,KeyError) as e:parser.exit(2,f'Preview error: {e}\n下一步：输出目录已存在时换一个新名字；其他错误请核对包内输入文件是否完整、字段是否符合示例。\n')
    print(f'cn-market-rules｜已生成规则核对与教学现金报告、JSON结果及输入快照。\n结果目录：{args.output_dir.resolve()}\n打开报告：{(args.output_dir / "index.html").resolve()}\n现金参数为教学假设；本次离线生成，不认证实际收益或资格。')
if __name__=='__main__':main()
