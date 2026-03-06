"""知识库引擎 — 项目上下文总结命令的安装。"""

from pathlib import Path
from importlib import resources
from issuekit.agents.registry import AgentConfig


def copy_knowledge_commands(commands_dir: Path, agent_config: AgentConfig) -> int:
    """复制知识库相关的 Agent 命令文件，返回安装的文件数。"""
    bundled = resources.files("issuekit") / "bundled_commands"
    knowledge_file = bundled / "issuekit.knowledge.md"

    if not knowledge_file.is_file():
        return 0

    content = knowledge_file.read_text(encoding="utf-8")

    if not agent_config.command_frontmatter:
        content = _strip_frontmatter(content)

    dest = commands_dir / f"issuekit.knowledge{agent_config.command_ext}"
    dest.write_text(content, encoding="utf-8")
    return 1


def _strip_frontmatter(content: str) -> str:
    """移除 Markdown 内容中的 YAML frontmatter。"""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content
