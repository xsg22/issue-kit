#!/usr/bin/env python3
"""校验 IssueKit 测试 Fixture 批次计划的最低初始化条件。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 Fixture 批次计划")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        data = yaml.safe_load(args.path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        print(f"无法读取 Fixture 计划：{exc}", file=sys.stderr)
        return 2

    batch = data.get("fixture_batch")
    if not isinstance(batch, dict):
        print("缺少 fixture_batch")
        return 1

    required = ("batch_id", "test_run_id", "environment", "code_source",
                "database_profile", "write_authorization", "fixtures")
    errors = [f"缺少 {key}" for key in required if not batch.get(key)]
    fixtures = batch.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        errors.append("fixtures 不能为空")
    else:
        for index, fixture in enumerate(fixtures):
            if not isinstance(fixture, dict):
                errors.append(f"fixtures[{index}] 不是对象")
                continue
            for key in ("fixture_id", "case_ids", "actor", "target_state", "setup", "verification"):
                if key not in fixture:
                    errors.append(f"fixtures[{index}] 缺少 {key}")
            actor = fixture.get("actor") or {}
            if not actor.get("id") and not actor.get("tenant_id"):
                errors.append(f"fixtures[{index}] 缺少 actor.id 或 actor.tenant_id")
            setup = fixture.get("setup") or {}
            if not setup.get("mode"):
                errors.append(f"fixtures[{index}] 缺少 setup.mode")
            verification = fixture.get("verification") or {}
            if not verification.get("query") or "expected" not in verification:
                errors.append(f"fixtures[{index}] 缺少 verification.query/expected")

    if errors:
        print("Fixture 计划未通过校验：")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Fixture 计划通过最低校验；执行前仍需完成环境、权限和回读验证")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
