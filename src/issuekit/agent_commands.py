"""将 issuekit 命令文件安装到目标 AI 助手的命令目录。"""

from importlib import resources
from pathlib import Path

from issuekit.agents.registry import AgentConfig

COMMAND_FILES = [
    "issuekit.require.md",
    "issuekit.design.md",
    "issuekit.coding.md",
    "issuekit.test.md",
    "issuekit.release.md",
    "issuekit.review.md",
    "issuekit.change.md",
]


def install_agent_commands(commands_dir: Path, agent_config: AgentConfig) -> int:
    """安装所有 issuekit 命令文件，返回安装的文件数。"""
    bundled = resources.files("issuekit") / "bundled_commands"
    count = 0

    for filename in COMMAND_FILES:
        source = bundled / filename
        if not source.is_file():
            continue

        content = source.read_text(encoding="utf-8")

        if not agent_config.command_frontmatter:
            content = _strip_frontmatter(content)

        if not agent_config.supports_handoffs:
            content = _strip_handoffs(content)

        dest = commands_dir / f"{Path(filename).stem}{agent_config.command_ext}"
        dest.write_text(content, encoding="utf-8")
        count += 1

    return count


def _strip_frontmatter(content: str) -> str:
    """移除 YAML frontmatter（--- ... ---）。"""
    if content.startswith("---"):
        end = content.find("---", 3)
        if end != -1:
            return content[end + 3:].lstrip("\n")
    return content


def _strip_handoffs(content: str) -> str:
    """移除 YAML frontmatter 中的 handoffs 部分（用于不支持 handoffs 的 AI 助手）。"""
    if not content.startswith("---"):
        return content

    end = content.find("---", 3)
    if end == -1:
        return content

    frontmatter = content[3:end]
    body = content[end + 3:]

    lines = frontmatter.split("\n")
    filtered = []
    skip = False
    for line in lines:
        if line.strip().startswith("handoffs:"):
            skip = True
            continue
        if skip and (line.startswith("  ") or line.startswith("\t")):
            continue
        skip = False
        filtered.append(line)

    new_frontmatter = "\n".join(filtered).strip()
    if new_frontmatter:
        return f"---\n{new_frontmatter}\n---{body}"
    return body.lstrip("\n")
