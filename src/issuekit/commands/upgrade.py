"""issuekit upgrade — 同步 bundled 文档模板与 Skills。"""

from pathlib import Path

import typer
from rich.console import Console

from issuekit.agent_skills import install_agent_skills
from issuekit.agents import AGENT_REGISTRY, get_agent_config
from issuekit.templates import copy_templates

console = Console()
OK = "[green]+[/green]"
SUPPORTED_AI = ", ".join(AGENT_REGISTRY.keys())
ISSUEKIT_DIR = ".issuekit"


def run_upgrade(*, ai: str) -> None:
    agent_config = get_agent_config(ai)
    if not agent_config:
        console.print(
            f"[red]错误:[/red] 不支持的 AI 助手 '{ai}'\n"
            f"[dim]支持的选项:[/dim] {SUPPORTED_AI}"
        )
        raise typer.Exit(1)

    project_path = Path.cwd()
    issuekit_path = project_path / ISSUEKIT_DIR
    if not issuekit_path.is_dir():
        console.print(
            f"[red]错误:[/red] 当前目录下没有 {ISSUEKIT_DIR}/，请先在本项目执行 "
            f"[cyan]issuekit init --ai {ai}[/cyan]"
        )
        raise typer.Exit(1)

    templates_path = issuekit_path / "templates"
    templates_path.mkdir(parents=True, exist_ok=True)
    console.print(
        "[yellow]注意:[/yellow] 将覆盖 [cyan].issuekit/templates/[/cyan] 中与内置同名的 .md 模板。"
    )
    tpl_count = copy_templates(templates_path)
    console.print(
        f"{OK} 已从当前 issuekit 安装包同步 {tpl_count} 个模板到 "
        f"[cyan]{ISSUEKIT_DIR}/templates/[/cyan]"
    )

    skills_dir = project_path / agent_config.skills_dir
    skills_dir.mkdir(parents=True, exist_ok=True)

    install_count = install_agent_skills(
        skills_dir,
        include_openai_yaml=agent_config.has_openai_yaml,
    )
    console.print(
        f"{OK} 已从当前 issuekit 安装包同步 {install_count} 个 Skill 到 "
        f"[cyan]{agent_config.skills_dir}/[/cyan]"
    )
