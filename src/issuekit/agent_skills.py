"""将 issuekit skills 安装到目标目录。

每个 skill 是一个独立目录，包含 SKILL.md。
Codex 额外需要 agents/openai.yaml 元数据文件。
源模板在 bundled_skills/ 下，按 skill-name/{SKILL.md, agents/openai.yaml} 组织。
"""

from importlib import resources
from pathlib import Path

SKILL_DIRS = [
    "issuekit-require",
    "issuekit-design",
    "issuekit-coding",
    "issuekit-test",
    "issuekit-release",
    "issuekit-review",
    "issuekit-change",
    "issuekit-knowledge",
]


def install_agent_skills(skills_dir: Path, *, include_openai_yaml: bool = False) -> int:
    """将所有 bundled skills 安装到目标目录，返回安装数。

    Args:
        skills_dir: 目标 skills 目录。
        include_openai_yaml: 是否同时复制 agents/openai.yaml（仅 Codex 需要）。
    """
    bundled = resources.files("issuekit") / "bundled_skills"
    count = 0

    for skill_name in SKILL_DIRS:
        source_dir = bundled / skill_name
        skill_md = source_dir / "SKILL.md"
        if not skill_md.is_file():
            continue

        dest_dir = skills_dir / skill_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        content = skill_md.read_text(encoding="utf-8")
        (dest_dir / "SKILL.md").write_text(content, encoding="utf-8")

        if include_openai_yaml:
            openai_yaml = source_dir / "agents" / "openai.yaml"
            if openai_yaml.is_file():
                agents_dir = dest_dir / "agents"
                agents_dir.mkdir(parents=True, exist_ok=True)
                yaml_content = openai_yaml.read_text(encoding="utf-8")
                (agents_dir / "openai.yaml").write_text(yaml_content, encoding="utf-8")

        count += 1

    return count
