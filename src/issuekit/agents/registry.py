"""AI 助手配置注册表。

每个助手定义了 Skills 的安装位置。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """AI 助手配置项。"""
    name: str
    skills_dir: str
    """Skills 安装目录（每个 skill 一个子目录，含 SKILL.md）。"""
    has_openai_yaml: bool = False
    """是否安装 agents/openai.yaml 元数据（仅 Codex 需要）。"""

    def format_description(self) -> str:
        return f"{self.name} ({self.skills_dir})"


AGENT_REGISTRY: dict[str, AgentConfig] = {
    "cursor": AgentConfig(
        name="Cursor",
        skills_dir=".cursor/skills",
    ),
    "claude": AgentConfig(
        name="Claude Code",
        skills_dir=".claude/skills",
    ),
    "codex": AgentConfig(
        name="Codex",
        skills_dir=".agents/skills",
        has_openai_yaml=True,
    ),
    "copilot": AgentConfig(
        name="GitHub Copilot",
        skills_dir=".github/skills",
    ),
}

AGENT_ALIASES: dict[str, str] = {
    "cursor-agent": "cursor",
    "claude-code": "claude",
}


def get_agent_config(name: str) -> Optional[AgentConfig]:
    """根据名称获取 AI 助手配置，支持别名解析。"""
    resolved = AGENT_ALIASES.get(name, name)
    return AGENT_REGISTRY.get(resolved)
