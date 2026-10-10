# SPDX-License-Identifier: MIT
"""Run bounded CLI scenarios with independently recorded expectations."""
import argparse
import copy
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def at(value,path):
    for key in path.split('/'):
        value=value[int(key)] if isinstance(value,list) else value[key]
    return value


def run(destination):
    destination=destination.resolve()
    destination.mkdir(parents=True,exist_ok=False)
    index=json.loads((ROOT/'references/scenario-index.json').read_text(encoding='utf-8'))
    env={k:v for k,v in os.environ.items() if not any(token in k.upper() for token in ('PYTHONPATH','RESEARCH_WORKBENCH','COMPONENT','DATA_PATH','SKILL_PATH'))}
    receipts=[]
    for case in index['cases']:
        folder=destination/case['id'];folder.mkdir()
        (folder/'expected.json').write_text(json.dumps(case,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        args=[sys.executable,'-s','-E','-B','-X','utf8',str(ROOT/'scripts'/case['script'])]
        if case['script']=='demo_preview.py':
            args+=['--output-dir',str(folder/'report')]
        else:
            document=copy.deepcopy(case.get('input'))
            if 'reuse' in case:
                document=json.loads((ROOT/case['reuse']).read_text(encoding='utf-8'))
                if 'case_index' in case:document=document['cases'][case['case_index']]
            document.update(case.get('changes',{}))
            (folder/'input.json').write_text(json.dumps(document,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            args+=['--input',str(folder/'input.json')]
        sentinel=folder/'protected-result.json'
        if case.get('protect_output'):
            sentinel.write_text('frozen prior result\n',encoding='utf-8')
            args+=['--output',str(sentinel)]
        process=subprocess.run(args,cwd=folder,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
        actual={'command':args,'exit_code':process.returncode,'stdout':process.stdout,'stderr':process.stderr}
        (folder/'actual.json').write_text(json.dumps(actual,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if process.returncode!=case.get('exit_code',0):raise ValueError(case['id']+': unexpected exit')
        if 'error_contains' in case and case['error_contains'] not in process.stderr:raise ValueError(case['id']+': expected error missing')
        if case.get('protect_output') and sentinel.read_text(encoding='utf-8')!='frozen prior result\n':raise ValueError('failed input overwrote result')
        if process.returncode==0:
            if case['script']=='demo_preview.py':
                value={name:json.loads((folder/'report'/filename).read_text(encoding='utf-8')) for name,filename in [('cash','cash-scenario.json'),('rules','rule-selection.json'),('events','event-evidence.json')]}
            else:value=json.loads(process.stdout)
            for path,expected in case.get('equals',{}).items():
                if at(value,path)!=expected:raise ValueError(case['id']+': '+path+' differs from independent expectation')
            (folder/'result.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        receipts.append(dict(id=case['id'],status='passed',basis=case['basis'],input_kind=case['input_kind']))
    result=dict(method_version=index['method_version'],status='bounded_cli_scenarios_passed',cases=receipts,limits=index['limits'])
    (destination/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    try: result=run(args.output_dir)
    except (ValueError,KeyError,TypeError,OSError) as error:
        parser.exit(2,f'Scenario acceptance refused: {error}\n')
    print(json.dumps(result,ensure_ascii=False,indent=2))
