"""AI 助手配置注册表。

每个助手定义了命令文件的存放位置和格式要求。
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """AI 助手配置项。"""
    name: str
    commands_dir: str
    rules_dir: Optional[str]
    command_ext: str
    command_frontmatter: bool
    supports_handoffs: bool

    def format_description(self) -> str:
        return f"{self.name} ({self.commands_dir})"


AGENT_REGISTRY: dict[str, AgentConfig] = {
    "cursor": AgentConfig(
        name="Cursor",
        commands_dir=".cursor/commands",
        rules_dir=".cursor/rules",
        command_ext=".md",
        command_frontmatter=True,
        supports_handoffs=True,
    ),
    "claude": AgentConfig(
        name="Claude Code",
        commands_dir=".claude/commands",
        rules_dir=None,
        command_ext=".md",
        command_frontmatter=False,
        supports_handoffs=False,
    ),
    "codex": AgentConfig(
        name="Codex",
        commands_dir=".codex/commands",
        rules_dir=None,
        command_ext=".md",
        command_frontmatter=False,
        supports_handoffs=False,
    ),
    "copilot": AgentConfig(
        name="GitHub Copilot",
        commands_dir=".github/agents",
        rules_dir=None,
        command_ext=".md",
        command_frontmatter=False,
        supports_handoffs=False,
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
