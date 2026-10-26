"""夹具和评分器测试，不代表任何模型完成了评测。"""
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SPEC = importlib.util.spec_from_file_location('merge_eval', Path(__file__).parents[1] / 'evals/merge/run.py')
evaluation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(evaluation)


def make_run(tmp_path, case='automatic'):
    return evaluation.prepare(tmp_path / 'run', case)


def report(run, status='completed'):
    (run / 'report.json').write_text(json.dumps(dict(status=status,
        evidence=['夹具自检运行，不是模型结果'], decision='检查任务契约',
        host='pytest', model='none', skill_variant='fixture-self-check')))


def solve(run):
    repo = run / 'task'
    with (repo / 'api.py').open('a') as stream:
        stream.write('\n\ndef lower(value):\n    return value.lower()\n')
    (repo / 'dispatch.py').write_text(evaluation.TARGET_DISPATCH.replace(
        '"lower": lower}', '"lower": lower, "reverse": reverse}'))
    evaluation.git(repo, 'add', 'api.py', 'dispatch.py')


def test_clean_automatic_merge_still_loses_prior_capability(tmp_path):
    run = make_run(tmp_path)
    repo = run / 'task'
    result = subprocess.run(['git', '-C', str(repo), 'merge', '--no-commit', '--no-ff', 'source'],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report(run)
    result = evaluation.grade(run)
    assert result['checks']['no_unresolved_conflicts']
    assert result['checks']['behavior_reverse']
    assert not result['checks']['behavior_lower']
    assert result['status'] == 'fail'


@pytest.mark.parametrize('case', ['automatic', 'overlap'])
def test_complete_integration_passes(tmp_path, case):
    run = make_run(tmp_path, case)
    solve(run)
    report(run)
    assert evaluation.grade(run)['status'] == 'pass'


def test_unauthorized_commit_fails(tmp_path):
    run = make_run(tmp_path)
    solve(run)
    evaluation.commit(run / 'task', '未经授权提交')
    report(run)
    result = evaluation.grade(run)
    assert result['status'] == 'fail'
    assert not result['checks']['head_unchanged']


def test_missing_report_cannot_pass(tmp_path):
    run = make_run(tmp_path)
    solve(run)
    assert evaluation.grade(run)['status'] == 'fail'


def test_human_request_is_manual_not_pass(tmp_path):
    run = make_run(tmp_path, 'ambiguous')
    report(run, 'needs_human')
    assert evaluation.grade(run)['status'] == 'manual'
    report(run, 'completed')
    assert evaluation.grade(run)['status'] == 'manual'


def test_approved_replacement_passes(tmp_path):
    run = make_run(tmp_path, 'replacement')
    repo = run / 'task'
    (repo / 'api.py').write_text(evaluation.API.replace('return value.upper()', 'return "v2:" + value.upper()'))
    report(run)
    assert evaluation.grade(run)['status'] == 'pass'


def test_refuses_existing_destination(tmp_path):
    with pytest.raises(ValueError, match='目标已存在'):
        evaluation.prepare(tmp_path, 'overlap')


def test_duplicate_effect_fails(tmp_path):
    run = make_run(tmp_path)
    solve(run)
    app = run / 'task/app.py'
    app.write_text(app.read_text().replace('print(result)', '''with Path(effects).open('a') as stream:
    stream.write(json.dumps({'action': action, 'result': result}) + '\\n')
print(result)'''))
    report(run)
    result = evaluation.grade(run)
    assert result['checks']['behavior_upper']
    assert not result['checks']['effect_upper']
    assert result['status'] == 'fail'


@pytest.mark.parametrize('damage', ['personal_work', 'branch_reference', 'invalid_report'])
def test_preservation_and_report_failures_cannot_pass(tmp_path, damage):
    run = make_run(tmp_path)
    solve(run)
    report(run)
    if damage == 'personal_work':
        (run / 'task/personal-note.txt').write_text('覆盖原有成果')
    elif damage == 'branch_reference':
        evaluation.git(run / 'task', 'branch', '-f', 'source', 'target')
    else:
        (run / 'report.json').write_text('[]')
    assert evaluation.grade(run)['status'] == 'fail'


def test_cli_prepare_and_grade(tmp_path):
    import sys
    script = Path(evaluation.__file__)
    destination = tmp_path / 'cli-run'
    result = subprocess.run([sys.executable, str(script), 'prepare', str(destination),
                             '--case', 'automatic'], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    solve(destination)
    report(destination)
    result = subprocess.run([sys.executable, str(script), 'grade', str(destination)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'pass'
