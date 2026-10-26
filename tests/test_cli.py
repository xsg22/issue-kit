"""验证真实 CLI 的安装、升级与项目知识保护。"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from issuekit.agents import AGENT_REGISTRY
from issuekit.cli import app


@pytest.mark.parametrize("agent", list(AGENT_REGISTRY))
def test_init_and_upgrade_preserve_project_knowledge(tmp_path, monkeypatch, agent):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ["init", "--ai", agent])
    assert result.exit_code == 0, result.output
    config = tmp_path / ".issuekit/config.yaml"
    original = config.read_bytes()
    knowledge = tmp_path / ".issuekit/knowledge/project-overview.md"
    knowledge.write_text("项目已有知识，必须保留。", encoding="utf-8")
    result = runner.invoke(app, ["upgrade", "--ai", agent])
    assert result.exit_code == 0, result.output
    assert config.read_bytes() == original
    assert knowledge.read_text(encoding="utf-8") == "项目已有知识，必须保留。"
    skills = tmp_path / AGENT_REGISTRY[agent].skills_dir
    assert (skills / "issuekit-merge/SKILL.md").is_file()
    assert (skills / "issuekit-business-test/references/case-maintenance.md").is_file()
    assert (skills / "issuekit-business-test/scripts/validate_fixture_plan.py").is_file()
    assert (skills / "issuekit-merge/agents/openai.yaml").is_file() == (agent == "codex")


def test_skill_conflict_blocks_template_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    assert runner.invoke(app, ["init", "--ai", "codex"]).exit_code == 0
    skill = Path(".agents/skills/issuekit-merge/SKILL.md")
    skill.write_text("项目定制规则", encoding="utf-8")
    template = Path(".issuekit/templates/test-plan.md")
    template.write_text("项目定制模板", encoding="utf-8")
    result = runner.invoke(app, ["upgrade", "--ai", "codex"])
    assert result.exit_code != 0
    assert skill.read_text(encoding="utf-8") == "项目定制规则"
    assert template.read_text(encoding="utf-8") == "项目定制模板"
