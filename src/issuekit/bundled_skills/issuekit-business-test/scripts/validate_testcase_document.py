#!/usr/bin/env python3
"""校验 IssueKit 真实业务测试文档是否具备最低落地信息。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_MARKERS = {
    "测试目标": "业务目标",
    "需求基线": "需求事实来源",
    "验收标准": "需求验收标准映射",
    "执行上下文": "执行上下文",
    "前置状态": "具体用户或业务状态",
    "状态转换": "状态转换",
    "测试数据准备": "数据准备说明",
    "用户操作和接口步骤": "真实操作和接口映射",
    "预期结果": "接口、数据库或副作用预期",
    "测试预言机": "测试预言机",
    "通过标准": "明确通过条件",
    "实际结果": "逐 Case 真实结果记录",
    "失败原因": "失败原因记录",
    "证据清单": "可回溯证据",
}

VAGUE_PHRASES = (
    "适量", "约几分钟", "正常测试", "测试一下", "视情况而定",
    "或明确失败", "按实现决定", "按代码定义", "符合需求", "合理处理",
    "不足或失败均可", "返回稳定错误", "等价幂等结果",
)
CASE_HEADER = re.compile(r"^(#{2,6})\s+.*?\b([A-Z][A-Z0-9]+-\d{2,})\b")


def validate_case_blocks(content: str) -> list[str]:
    lines = content.splitlines()
    section_start = next(
        (index for index, line in enumerate(lines) if re.match(r"^##\s+\d+\.\s+逐条执行 Case 记录", line)),
        None,
    )
    if section_start is None:
        return []

    headers = []
    for index in range(section_start + 1, len(lines)):
        match = CASE_HEADER.match(lines[index])
        if match:
            headers.append((index, match.group(1), match.group(2)))

    errors = []
    required_case_markers = {
        "上下文": "用户/实体/资源上下文",
        "步骤": "可执行操作步骤",
        "状态转换": "状态转换协议",
        "用户可见状态": "用户可见状态变化",
        "系统状态": "系统状态变化",
        "变体选择": "状态变体覆盖说明",
        "禁止变化": "禁止变化和不变量",
        "预期接口": "精确接口预期",
        "预期数据库": "字段级数据库预期",
        "实际结果": "逐 Case 实际结果",
        "失败原因": "逐 Case 失败原因栏",
        "结论": "逐 Case 结论",
    }
    for offset, (start, level, case_id) in enumerate(headers):
        end = len(lines)
        for next_start, next_level, _ in headers[offset + 1:]:
            if len(next_level) <= len(level):
                end = next_start
                break
        block = "\n".join(lines[start:end])
        for marker, description in required_case_markers.items():
            if marker not in block:
                errors.append(f"{case_id} 缺少{description}：{marker}")
    return errors


def validate(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    errors = []
    for marker, description in REQUIRED_MARKERS.items():
        if marker not in content:
            errors.append(f"缺少{description}章节：{marker}")
    if "环境" not in content and "environment" not in content:
        errors.append("未声明执行环境或环境绑定方式")
    if "数据库" not in content and "database" not in content:
        errors.append("未声明数据库验证或明确说明不适用")
    if "PASS" not in content or "BLOCKED" not in content:
        errors.append("未包含 PASS/BLOCKED 结果等级")
    if "覆盖标签" not in content:
        errors.append("未声明覆盖标签，无法确认边界/幂等/失败等场景覆盖")
    if "数据隔离标识" not in content:
        errors.append("未声明测试数据隔离标识，无法保证异步结果可归属")
    for phrase in VAGUE_PHRASES:
        if phrase in content:
            errors.append(f"包含模糊描述“{phrase}”，必须替换成具体输入或判定条件")
    errors.extend(validate_case_blocks(content))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 IssueKit 业务测试用例文档")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if not args.path.is_file():
        print(f"文件不存在：{args.path}", file=sys.stderr)
        return 2
    errors = validate(args.path)
    if errors:
        print("测试文档未通过最低落地校验：")
        for error in errors:
            print(f"- {error}")
        return 1
    print("测试文档通过最低落地校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
