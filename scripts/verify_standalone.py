# SPDX-License-Identifier: MIT
"""Verify a source Skill archive in a fresh directory/venv, not a fresh OS."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

LAUNCHER = '''import json,runpy,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
receipt=Path(sys.argv[2])
sys.path.insert(0,str(root/'scripts'))
sys.argv=[str(root/'scripts/demo_preview.py'),'--output-dir',sys.argv[3]]
try:
 runpy.run_path(sys.argv[0],run_name='__main__')
finally:
 origins={name:str(Path(module.__file__).resolve()) for name,module in sys.modules.copy().items() if getattr(module,'__file__',None)}
 receipt.write_text(json.dumps(dict(sys_path=sys.path,module_origins=origins,executable=sys.executable,prefix=sys.prefix,base_prefix=sys.base_prefix),indent=2),encoding='utf-8')
'''


def verify(archive, destination):
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=False)
    package = destination / 'skill'
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            path = (package / info.filename).resolve()
            if not path.is_relative_to(package.resolve()):
                raise ValueError('archive path escapes package')
            if any(part in {'.git', '.venv', '__pycache__', 'local-data', 'work'} for part in Path(info.filename).parts):
                raise ValueError('archive contains private/runtime directory')
        bundle.extractall(package)
    if not (package / 'SKILL.md').is_file():
        raise ValueError('expected root-level Skill archive')
    venv.EnvBuilder(with_pip=False, system_site_packages=False).create(destination / 'venv')
    python = destination / 'venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    empty = destination / 'empty-user'
    empty.mkdir()
    env = {k:v for k,v in os.environ.items() if not any(token in k.upper() for token in ('PYTHON', 'RESEARCH_WORKBENCH', 'CODEX', 'AKSHARE', 'TUSHARE', 'DATA_PATH', 'COMPONENT', 'SKILL_PATH'))}
    # Child-only variables: never mutate the user's process or actual caches.
    for key in ('HOME', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME'):
        env[key] = str(empty)
    launcher = destination / 'run_demo.py'
    launcher.write_text(LAUNCHER, encoding='utf-8')
    report = destination / 'report'
    commands = []
    def run(args, expected, direct=False):
        flags = ['-s', '-E'] if direct else ['-I']
        process = subprocess.run([str(python), *flags, '-B', '-X', 'utf8', *map(str,args)], cwd=destination, env=env, capture_output=True, text=True, encoding='utf-8', timeout=60)
        commands.append(dict(argv=process.args, returncode=process.returncode, stdout=process.stdout, stderr=process.stderr))
        if process.returncode != expected:
            raise ValueError(f'command exit {process.returncode}, expected {expected}: {process.stderr}')
        return process
    run([launcher, package, destination/'origins.json', report], 0)
    # Exact README entry with Python isolation flags, without a runpy wrapper.
    direct_report = destination/'readme-report'
    run([package/'scripts/demo_preview.py', '--output-dir', direct_report], 0, direct=True)
    for name in ('cash-scenario.json','rule-selection.json','event-evidence.json'):
        if (direct_report/name).read_bytes() != (report/name).read_bytes():
            raise ValueError('direct README entry differs from instrumented entry')
    run(['-c', "import importlib.util; assert importlib.util.find_spec('pypdf') is None; assert importlib.util.find_spec('pdfplumber') is None; print('Optional PDF libraries absent; demo still completed')"], 0)
    run([package/'scripts/announcement_consumer.py', '--sidecar', package/'interfaces/announcement-samples/sidecar-920188.json', '--review', package/'interfaces/announcement-samples/review-920188.json', '--original', destination/'missing-original.pdf'], 2, direct=True)
    run([package/'scripts/run_scenario_acceptance.py', '--output-dir', destination/'scenarios'], 0, direct=True)
    origins = json.loads((destination/'origins.json').read_text(encoding='utf-8'))
    allowed = [destination, Path(origins['base_prefix']).resolve()]
    for path in origins['sys_path'] + list(origins['module_origins'].values()):
        if not any(Path(path).resolve().is_relative_to(root) for root in allowed):
            raise ValueError('module/search path outside isolated package and base Python: '+path)
    for module in ('evidence_interface', 'rule_versions', 'scenarios'):
        if not Path(origins['module_origins'][module]).is_relative_to(package):
            raise ValueError('professional module loaded outside archive')
    cash = json.loads((report/'cash-scenario.json').read_text(encoding='utf-8'))
    for key, expected in {'final_cash':'85000.00','minimum_balance':'5000.00','maximum_buffer_gap':'15000.00'}.items():
        if cash[key] != expected: raise ValueError('teaching result mismatch: '+key)
    rules = json.loads((report/'rule-selection.json').read_text(encoding='utf-8'))
    if rules['rule_version_id'] != 'SSE-REITS-EXP-2025' or rules['status'] != 'selected':
        raise ValueError('rule version mismatch')
    events = json.loads((report/'event-evidence.json').read_text(encoding='utf-8'))
    if events['unknown_field_count'] <= 0: raise ValueError('expected evidence unknowns')
    html = (report/'index.html').read_text(encoding='utf-8')
    if '教学' not in html or '未知' not in html: raise ValueError('report scope labels missing')
    for href in re.findall(r'href="([^"]+)"', html):
        if not href.startswith(('https://','http://','#')) and not (report/href).is_file():
            raise ValueError('report file link missing: '+href)
    for name in ('LICENSE','LICENSE_SCOPE.json','THIRD_PARTY_NOTICES.md','licenses/README.md'):
        if not (package/name).is_file(): raise ValueError('license file missing: '+name)
    # Original package verifier runs through isolated Python with its own script directory.
    check = destination/'check_package.py'
    check.write_text("import runpy,sys\nfrom pathlib import Path\nr=Path(sys.argv[1]);sys.path.insert(0,str(r/'scripts'));sys.argv=[str(r/'scripts/validate_package.py')];runpy.run_path(sys.argv[0],run_name='__main__')\n", encoding='utf-8')
    run([check, package], 0)
    before = hashlib.sha256((report/'index.html').read_bytes()).hexdigest()
    run([launcher, package, destination/'failure-origins.json', report], 2)
    if before != hashlib.sha256((report/'index.html').read_bytes()).hexdigest():
        raise ValueError('existing report overwritten')
    result = dict(status='independent_source_skill_demo_passed', archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), python_version=sys.version, isolation='fresh directory and venv; same host/base Python, not fresh OS', dependencies='standard library only; venv without pip/system site packages', removed_environment_keys=[k for k in os.environ if k not in env], module_origins=origins, commands=commands, report_checks=dict(teaching_cash=cash['final_cash'],minimum_balance=cash['minimum_balance'],buffer_gap=cash['maximum_buffer_gap'],rule_version=rules['rule_version_id'],unknown_count=events['unknown_field_count'],local_links='resolved',existing_output='exit 2; unchanged'), limitations=['No natural-language Skill discovery/activation or browser visual certification','No live acquisition or real investor qualification','Optional external PDF not needed for README shortest demo','Released v2.0.0 not tested by this runner'])
    (destination/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    result=verify(args.archive.resolve(),args.output_dir)
    print(json.dumps({k:result[k] for k in ('status','archive_sha256','isolation','dependencies')},ensure_ascii=False))


if __name__=='__main__': main()
