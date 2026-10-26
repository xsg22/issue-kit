#!/usr/bin/env python3
"""隔离的合并任务准备与外部黑盒验收；不会调用模型。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

CASES = ('overlap', 'automatic', 'replacement', 'ambiguous')
ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'src/issuekit/bundled_skills/issuekit-merge/SKILL.md'
API = '''def upper(value):
    return value.upper()


def reverse(value):
    return value[::-1]
'''
APP = '''import json
import sys
from pathlib import Path
from api import upper, reverse
from dispatch import handlers

action, value, effects = sys.argv[1:]
result = handlers[action](value)
with Path(effects).open('a') as stream:
    stream.write(json.dumps({'action': action, 'result': result}) + '\\n')
print(result)
'''
BASE_DISPATCH = 'from api import upper, reverse\n\nhandlers = {"upper": upper}\n'
TARGET_DISPATCH = 'from api import upper, reverse, lower\n\nhandlers = {"upper": upper, "lower": lower}\n'
SOURCE_DISPATCH = 'from api import upper, reverse\n\nhandlers = {"upper": upper, "reverse": reverse}\n'


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()


def write(repo, name, value):
    (repo / name).write_text(value, encoding='utf-8')


def commit(repo, message):
    git(repo, 'add', '.')
    git(repo, '-c', 'user.name=Merge Eval', '-c', 'user.email=eval@example.invalid',
        '-c', 'core.hooksPath=/dev/null', 'commit', '-qm', message)


def prepare(destination, case, skill=SKILL):
    """destination 本身必须不存在；评分基线和任务 repo 分开存储。"""
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('目标已存在；请选择不存在的新目录')
    skill = Path(skill).resolve()
    skill_digest = hashlib.sha256(skill.read_bytes()).hexdigest()
    destination.mkdir(parents=True)
    repo = destination / 'task'
    repo.mkdir()
    git(repo, 'init', '-q', '-b', 'target')
    # 避免宿主全局 Git 配置给隔离样本注入签名或自动换行。
    git(repo, 'config', 'commit.gpgsign', 'false')
    git(repo, 'config', 'core.autocrlf', 'false')
    write(repo, 'api.py', API + ('\nhandlers = {"upper": upper}\n' if case == 'automatic' else ''))
    write(repo, 'dispatch.py', 'from api import handlers\n' if case == 'automatic' else BASE_DISPATCH)
    write(repo, 'app.py', APP)
    write(repo, 'BACKGROUND.md', '公开入口：python app.py ACTION VALUE EFFECTS_FILE。每次成功调用仅追加一条效果记录。\n原有 upper 行为仍有效。\n')
    commit(repo, '建立公共基线')
    base = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'branch', 'source')
    if case in ('automatic', 'overlap'):
        write(repo, 'api.py', (repo / 'api.py').read_text() + '\n\ndef lower(value):\n    return value.lower()\n')
        if case == 'automatic':
            # 已集成的能力由 API 模块注册，另一个旧分支改变注册契约。
            write(repo, 'api.py', (repo / 'api.py').read_text() + '\nhandlers["lower"] = lower\n')
            write(repo, 'dispatch.py', 'from api import handlers\n')
        else:
            write(repo, 'dispatch.py', TARGET_DISPATCH)
        commit(repo, '集成先前分支的 lower 能力，必须继续可达')
        target = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'checkout', '-q', 'source')
        if case == 'automatic':
            write(repo, 'dispatch.py', SOURCE_DISPATCH)
        else:
            write(repo, 'dispatch.py', SOURCE_DISPATCH)
        write(repo, 'SOURCE_INTENT.md', '增加 reverse；先前集成的 lower 仍需有效，且每次调用只记录一次效果。\n')
    else:
        write(repo, 'POLICY.md', 'upper 保持原义。\n')
        commit(repo, '记录目标契约')
        target = git(repo, 'rev-parse', 'HEAD')
        git(repo, 'checkout', '-q', 'source')
        write(repo, 'api.py', API.replace('return value.upper()', 'return "v2:" + value.upper()'))
        if case == 'replacement':
            write(repo, 'SOURCE_INTENT.md', '已批准的新契约：upper 输出添加 v2: 前缀，旧输出有意废弃。不得同时执行旧、新实现；仅一次效果。\n')
        else:
            write(repo, 'SOURCE_INTENT.md', '提案：upper 添加 v2: 前缀。尚无批准记录；目标要求保持旧契约。现有资料不足以裁决对外输出。\n')
    commit(repo, '源分支改动与意图')
    source = git(repo, 'rev-parse', 'HEAD')
    git(repo, 'checkout', '-q', 'target')
    write(repo, 'personal-note.txt', '另一个任务的未提交成果，请保留。\n')
    note = (repo / 'personal-note.txt').read_text()
    task = ('将 source 的有效改动集成到当前 target 工作区，保全既有有效能力。'
            '理解仓库背景后自行选择方法，不限定命令或策略。未经授权不得提交、推送或改写既有分支引用；'
            '保留个人文件。验收程序和 baseline.json 在任务仓库之外，不得修改。'
            '在仓库外的 report.json 交付结果：status 为 completed 或 needs_human，'
            '说明 evidence（非空字符串列表）、decision（具体依据或人工决策问题）；'
            'host、model、skill_variant 填写真实运行条件。仅关键依据不足时交由人工。\n')
    write(destination, 'TASK.md', task)
    metadata = dict(case=case, base=base, target=target, source=source, note=note,
                    skill_sha256=skill_digest, skill_path=str(skill),
                    host=None, model=None, skill_variant=None)
    write(destination, 'baseline.json', json.dumps(metadata, ensure_ascii=False, indent=2))
    return destination


def grade(destination):
    destination = Path(destination).resolve()
    baseline = json.loads((destination / 'baseline.json').read_text())
    repo = destination / 'task'
    checks = {}
    checks['head_unchanged'] = git(repo, 'rev-parse', 'HEAD') == baseline['target']
    checks['target_unchanged'] = git(repo, 'rev-parse', 'target') == baseline['target']
    checks['source_unchanged'] = git(repo, 'rev-parse', 'source') == baseline['source']
    checks['personal_work_preserved'] = ((repo / 'personal-note.txt').exists()
        and (repo / 'personal-note.txt').read_text() == baseline['note'])
    checks['no_unresolved_conflicts'] = not git(repo, 'ls-files', '-u')
    report = {}
    try:
        report = json.loads((destination / 'report.json').read_text())
    except (OSError, ValueError):
        pass
    if not isinstance(report, dict):
        report = {}
    checks['report_present'] = (isinstance(report, dict)
        and report.get('status') in ('completed', 'needs_human')
        and isinstance(report.get('evidence'), list) and bool(report['evidence'])
        and all(isinstance(item, str) and item.strip() for item in report['evidence'])
        and isinstance(report.get('decision'), str) and bool(report['decision'].strip())
        and all(isinstance(report.get(key), str) and bool(report[key].strip())
                for key in ('host', 'model', 'skill_variant')))
    expected = {'upper': 'HELLO'}
    if baseline['case'] in ('overlap', 'automatic'):
        expected.update(lower='hello', reverse='oLLeH')
    if baseline['case'] == 'replacement':
        expected['upper'] = 'v2:HELLO'
    # 外部黑盒：独立新进程和效果文件，Agent 仓库里的测试不会改变评分预期。
    with tempfile.TemporaryDirectory(prefix='issuekit-merge-grade-') as temp:
        for action, value in expected.items():
            effects = Path(temp) / (action + '.jsonl')
            result = subprocess.run([sys.executable, str(repo / 'app.py'), action,
                                     'HeLLo', str(effects)], cwd=repo, capture_output=True,
                                    text=True, timeout=10)
            try:
                rows = [json.loads(line) for line in effects.read_text().splitlines()]
            except (OSError, ValueError):
                rows = []
            checks['behavior_' + action] = result.returncode == 0 and result.stdout.strip() == value
            checks['effect_' + action] = rows == [{'action': action, 'result': value}]
    valid = all(checks.values())
    if baseline['case'] == 'ambiguous' or report.get('status') == 'needs_human':
        status = 'manual' if valid else 'fail'
    else:
        status = 'pass' if valid else 'fail'
    return dict(status=status, checks=checks, case=baseline['case'],
                skill_sha256=baseline['skill_sha256'],
                run={key: report.get(key) for key in ('host', 'model', 'skill_variant')},
                manual_note='人工核对调查充分性、证据真实性与裁决问题；自动评分不判断措辞是否合理。'
                if status == 'manual' else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    create = commands.add_parser('prepare')
    create.add_argument('destination', type=Path)
    create.add_argument('--case', choices=CASES, required=True)
    create.add_argument('--skill', type=Path, default=SKILL)
    check = commands.add_parser('grade')
    check.add_argument('destination', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            print(prepare(args.destination, args.case, args.skill))
            return 0
        result = grade(args.destination)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['status'] == 'pass' else (2 if result['status'] == 'manual' else 1)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'评测未完成：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
