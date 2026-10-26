"""独立文档验证定义/运行分离及逐 Case 归属，不证明业务通过。"""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = (Path(__file__).parents[1] / 'src/issuekit/bundled_skills/'
          'issuekit-business-test/scripts/validate_testcase_document.py')
SPEC = importlib.util.spec_from_file_location('business_document_validator', SCRIPT)
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

CONTEXT = '''环境绑定：执行时绑定已确认环境，定义不绑定具体部署。
数据隔离：按 run 独立对象和幂等键。
'''
DEFINITION = '''# CASE-101：拒绝无权限修改
需求来源：任务讨论第 3 条确认只读用户不得编辑。
前置状态：用户 role=reader，文档 version=1。
数据准备：通过业务接口创建独立文档；不直接写数据库。
操作步骤：以 reader 调用 PATCH /documents/123，body={"title":"new"}。
预期结果：HTTP 403，title 保持 old，version 保持 1，不发送更新事件。
数据库断言：按文档 ID 查询，version=1，title=old。
通过标准：响应、持久化和事件禁止变化断言全部满足。
'''
REPORT_CONTEXT = '''环境：local，实际服务 127.0.0.1:8100，数据库 test_db。
数据隔离标识：run-isolated-23。
test_run_id：run-23。
被测版本：commit abc123。
'''
REPORT = '''## CASE-101：本轮结果
Case 引用：cases/access.md CASE-101@r2，冻结输入版本 abc123。
实际结果：HTTP 403，文档 version=1，title=old，无更新事件。
证据：runs/run-23/request.json、db.json、events.json。
结论：PASS
'''


def check(tmp_path, text, kind='definition'):
    path = tmp_path / 'test.md'
    path.write_text(text)
    return validator.validate(path, kind)


def test_definition_needs_no_runtime_result(tmp_path):
    assert check(tmp_path, CONTEXT + DEFINITION) == []


def test_definition_without_expected_behavior_is_rejected(tmp_path):
    text = '\n'.join(line for line in DEFINITION.splitlines() if not line.startswith('预期结果'))
    errors = check(tmp_path, CONTEXT + text)
    assert errors and any('CASE-101' in error and '预期' in error for error in errors)


def test_report_can_reference_definition_without_repeating_it(tmp_path):
    assert check(tmp_path, REPORT_CONTEXT + REPORT, 'report') == []


def test_report_needs_actual_even_with_reference_and_evidence(tmp_path):
    text = '\n'.join(line for line in REPORT.splitlines() if not line.startswith('实际结果'))
    assert any('实际结果' in error for error in check(tmp_path, REPORT_CONTEXT + text, 'report'))


def test_fields_cannot_be_borrowed_between_cases(tmp_path):
    second = DEFINITION.replace('CASE-101', 'CASE-102')
    first = '\n'.join(line for line in DEFINITION.splitlines() if not line.startswith('预期结果'))
    errors = check(tmp_path, CONTEXT + first + '\n' + second)
    assert any('CASE-101' in error and '预期' in error for error in errors)
    assert not any('CASE-102' in error for error in errors)


def test_report_results_cannot_be_borrowed_between_cases(tmp_path):
    second = REPORT.replace('CASE-101', 'CASE-102')
    first = '\n'.join(line for line in REPORT.splitlines() if not line.startswith('实际结果'))
    errors = check(tmp_path, REPORT_CONTEXT + first + '\n' + second, 'report')
    assert any('CASE-101' in error and '实际结果' in error for error in errors)
    assert not any('CASE-102' in error for error in errors)


@pytest.mark.parametrize('body', ['# 测试报告\n没有 Case。', '```markdown\n' + DEFINITION + '\n```', '# CASE-101：空 Case'])
def test_no_real_populated_case_cannot_pass(tmp_path, body):
    assert check(tmp_path, CONTEXT + body)


def test_empty_expected_heading_cannot_borrow_following_field(tmp_path):
    text = DEFINITION.replace('预期结果：HTTP 403，title 保持 old，version 保持 1，不发送更新事件。', '## 预期结果\n## 通过标准\n响应与持久化必须满足断言。')
    assert check(tmp_path, CONTEXT + text)


def test_mismatched_case_revision_reference_is_rejected(tmp_path):
    text = REPORT.replace('cases/access.md CASE-101@r2', 'cases/access.md CASE-999@r2')
    assert check(tmp_path, REPORT_CONTEXT + text, 'report')


def test_failed_report_requires_reason(tmp_path):
    text = REPORT.replace('结论：PASS', '结论：FAIL')
    assert check(tmp_path, REPORT_CONTEXT + text, 'report')
    assert check(tmp_path, REPORT_CONTEXT + text + '失败原因：实现错误允许了编辑。\n', 'report') == []


def test_cli_defaults_to_definition_and_report_is_explicit(tmp_path):
    definition = tmp_path / 'definition.md'
    definition.write_text(CONTEXT + DEFINITION)
    report = tmp_path / 'report.md'
    report.write_text(REPORT_CONTEXT + REPORT)
    assert subprocess.run([sys.executable, str(SCRIPT), str(definition)], capture_output=True).returncode == 0
    assert subprocess.run([sys.executable, str(SCRIPT), str(report)], capture_output=True).returncode == 1
    assert subprocess.run([sys.executable, str(SCRIPT), str(report), '--kind', 'report'], capture_output=True).returncode == 0


def test_expected_json_under_heading_is_a_value(tmp_path):
    text = DEFINITION.replace('预期结果：HTTP 403，title 保持 old，version 保持 1，不发送更新事件。',
                              '## 预期结果\n```json\n{"status": 403, "version": 1}\n```')
    assert check(tmp_path, CONTEXT + text) == []


def test_empty_fence_is_not_an_expected_value(tmp_path):
    text = DEFINITION.replace('预期结果：HTTP 403，title 保持 old，version 保持 1，不发送更新事件。',
                              '## 预期结果\n```json\n\n```')
    assert any('预期' in error for error in check(tmp_path, CONTEXT + text))


def test_fenced_field_cannot_satisfy_missing_structure(tmp_path):
    text = DEFINITION.replace('预期结果：HTTP 403，title 保持 old，version 保持 1，不发送更新事件。',
                              '```markdown\n预期结果：HTTP 403，version=1。\n```')
    assert any('预期' in error for error in check(tmp_path, CONTEXT + text))
