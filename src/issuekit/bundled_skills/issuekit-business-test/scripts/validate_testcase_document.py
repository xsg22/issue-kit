#!/usr/bin/env python3
"""校验 Case 定义或运行报告的最低结构，不证明业务预期或执行结果正确。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CASE_HEADER = re.compile(r"^(#{1,6})\s+.*?\b([A-Z][A-Z0-9]+-\d{2,})\b")
HEADING = re.compile(r"^(#{1,6})\s+")
DEFINITION_FIELDS = {
    "需求来源": ("需求来源", "需求基线"),
    "前置状态": ("前置状态", "上下文"),
    "数据准备": ("数据准备", "测试数据准备"),
    "操作步骤": ("操作步骤", "用户操作和接口步骤", "步骤"),
    "精确预期": ("预期结果", "精确预期"),
    "通过标准": ("通过标准",),
    "数据库验证或不适用说明": ("数据库断言", "预期数据库", "数据库"),
}
VAGUE_PHRASES = (
    "适量", "约几分钟", "正常测试", "测试一下", "视情况而定",
    "或明确失败", "按实现决定", "按代码定义", "符合需求", "合理处理",
    "不足或失败均可", "返回稳定错误", "等价幂等结果",
)
VERDICTS = {"PASS", "PASS_WITH_WARNINGS", "PARTIAL_PASS", "FAIL", "BLOCKED", "NOT_RUN"}


def markdown_lines(content: str) -> list[str]:
    """代码围栏中的示例标题不能充当实际 Case。"""
    lines = []
    fence = None
    for line in content.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            lines.append("")
        else:
            lines.append(line if fence is None else "")
    return lines


def field_value(lines: list[str], names: tuple[str, ...], raw_lines: list[str] | None = None) -> str:
    """接受“字段：值”或 Markdown 字段标题下的正文。"""
    alternatives = "|".join(re.escape(name) for name in names)
    pattern = re.compile(rf"^(?:#{{1,6}}\s+|[-*]\s+)?(?:{alternatives})(?:\s*[:：]\s*(.*)|\s*)$")
    for index, line in enumerate(lines):
        # 常见的粗体字段标签不改变字段语义。
        match = pattern.fullmatch(line.strip().replace("**", ""))
        if not match:
            continue
        if match.group(1):
            return match.group(1).strip()
        following = []
        for next_index in range(index + 1, len(lines)):
            next_line = lines[next_index]
            if HEADING.match(next_line) or re.match(r"^\s*[^:：]+[:：]", next_line):
                break
            value_line = raw_lines[next_index] if raw_lines is not None else next_line
            if not re.match(r"^\s*(`{3,}|~{3,})", value_line):
                following.append(value_line)
        if any(part.strip() for part in following):
            return "\n".join(following).strip()
    return ""


def validate_case_blocks(content: str, kind: str = "definition") -> list[str]:
    if kind not in {"definition", "report"}:
        raise ValueError(f"未知校验类型：{kind}")
    lines = markdown_lines(content)
    raw_lines = content.splitlines()
    headers = [(i, match) for i, line in enumerate(lines) if (match := CASE_HEADER.match(line))]
    if not headers:
        return ["未找到实际 Case 标题（例如 # CASE-001：名称）；旧混合文档需拆分定义与运行报告"]
    errors = []
    seen = set()
    for start, header in headers:
        case_id = header.group(2)
        if case_id in seen:
            errors.append(f"Case ID 重复：{case_id}")
        seen.add(case_id)
        end = next((i for i in range(start + 1, len(lines))
                    if (match := HEADING.match(lines[i])) and
                    (len(match.group(1)) <= len(header.group(1)) or CASE_HEADER.match(lines[i]))), len(lines))
        block = lines[start + 1:end]
        raw_block = raw_lines[start + 1:end]
        if kind == "definition":
            required = DEFINITION_FIELDS
        else:
            required = {"Case 修订引用": ("Case 引用", "Case reference"),
                        "实际结果": ("实际结果", "Actual"),
                        "证据索引": ("证据", "证据索引", "Evidence"),
                        "结论": ("结论", "Verdict")}
        for description, names in required.items():
            if not field_value(block, names, raw_block):
                errors.append(f"{case_id} 缺少{description}或内容为空")
        if kind == "definition":
            for phrase in VAGUE_PHRASES:
                if phrase in "\n".join(block):
                    errors.append(f"{case_id} 包含模糊描述“{phrase}”，需具体输入或判定条件")
        else:
            reference = field_value(block, ("Case 引用", "Case reference"), raw_block)
            if reference and not re.search(rf"\b{re.escape(case_id)}@(?:revision[=:])?[A-Za-z0-9][\w.-]*", reference):
                errors.append(f"{case_id} 引用须包含相同 Case ID@revision")
            verdict = field_value(block, ("结论", "Verdict"), raw_block)
            if verdict and verdict not in VERDICTS:
                errors.append(f"{case_id} 结论不是支持的结果等级")
            if verdict in {"FAIL", "BLOCKED", "NOT_RUN"} and not field_value(block, ("失败原因", "未执行原因", "Failure reason"), raw_block):
                errors.append(f"{case_id} 缺少失败或未执行原因")
            if verdict in {"PARTIAL_PASS", "PASS_WITH_WARNINGS"} and not field_value(block, ("限制", "Limitations"), raw_block):
                errors.append(f"{case_id} 缺少证据限制说明")
    return errors


def validate(path: Path, kind: str = "definition") -> list[str]:
    content = path.read_text(encoding="utf-8")
    lines = markdown_lines(content)
    # 批次事实仅从 Case 前的头部读取，不能借某一 Case 的字段覆盖其他 Case。
    first_case = next((i for i, line in enumerate(lines) if CASE_HEADER.match(line)), len(lines))
    context = lines[:first_case]
    common = {"环境或绑定方式": ("环境", "环境绑定", "environment"),
              "数据隔离或不适用说明": ("数据隔离标识", "数据隔离", "isolation")}
    if kind == "report":
        common.update({"运行标识": ("test_run_id",), "实际被测版本": ("被测版本", "部署版本", "version")})
    errors = [f"缺少{description}或内容为空" for description, names in common.items()
              if not field_value(context, names, content.splitlines()[:first_case])]
    errors.extend(validate_case_blocks(content, kind))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--kind", choices=("definition", "report"), default="definition")
    args = parser.parse_args()
    if not args.path.is_file():
        print(f"文件不存在：{args.path}", file=sys.stderr)
        return 2
    errors = validate(args.path, args.kind)
    if errors:
        print(f"{args.kind} 文档未通过最低结构校验：")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"{args.kind} 文档通过最低结构校验；不代表业务验证通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
