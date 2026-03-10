"""issuekit init 命令 — 在项目中初始化 Issue 驱动的开发环境。"""

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from issuekit.agents import AGENT_REGISTRY, get_agent_config
from issuekit.templates import copy_templates

console = Console()

OK = "[green]+[/green]"

ISSUEKIT_DIR = ".issuekit"

SUPPORTED_AI = ", ".join(AGENT_REGISTRY.keys())

USAGE_EXAMPLES = (
    "\n[dim]用法示例:[/dim]\n"
    "  issuekit init --ai cursor\n"
    "  issuekit init --ai codex\n"
    "  issuekit init --ai claude\n"
    "  issuekit init --ai cursor --force"
)

SKILL_NAMES = [
    "issuekit-require", "issuekit-design", "issuekit-coding",
    "issuekit-test", "issuekit-release", "issuekit-review",
    "issuekit-change", "issuekit-knowledge",
]


def init(
    ai: str = typer.Option(
        ...,
        help=f"指定 AI 助手：{SUPPORTED_AI}",
    ),
    issues_dir: str = typer.Option(
        "issues",
        "--issues-dir",
        help="Issue 文档存放目录（相对项目根目录，默认：issues）",
    ),
    here: bool = typer.Option(
        True,
        "--here/--no-here",
        help="在当前目录初始化（默认：是）",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="如果 .issuekit/ 已存在，强制覆盖",
    ),
):
    """在项目中初始化 IssueKit。"""
    agent_config = get_agent_config(ai)
    if not agent_config:
        console.print(
            f"[red]错误:[/red] 不支持的 AI 助手 '{ai}'\n"
            f"[dim]支持的选项:[/dim] {SUPPORTED_AI}"
            f"{USAGE_EXAMPLES}"
        )
        raise typer.Exit(1)

    project_path = Path.cwd()
    issuekit_path = project_path / ISSUEKIT_DIR

    if issuekit_path.exists() and not force:
        console.print(
            f"[yellow]提示:[/yellow] {ISSUEKIT_DIR}/ 目录已存在，"
            "如需覆盖请添加 --force 参数。"
            f"{USAGE_EXAMPLES}"
        )
        raise typer.Exit(1)

    console.print()
    console.print(
        Panel(
            f"[cyan]IssueKit 初始化[/cyan]\n\n"
            f"{'项目':<10} [green]{project_path.name}[/green]\n"
            f"{'AI 助手':<9} [green]{agent_config.name}[/green]\n"
            f"{'Issues':<10} [green]{issues_dir}[/green]\n"
            f"{'路径':<10} [dim]{project_path}[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # 第 1 步：创建 .issuekit/ 目录结构
    console.print(f"\n[cyan]创建 {ISSUEKIT_DIR}/ 目录...[/cyan]")

    templates_path = issuekit_path / "templates"
    knowledge_path = issuekit_path / "knowledge"

    if issuekit_path.exists():
        shutil.rmtree(issuekit_path)

    templates_path.mkdir(parents=True)
    knowledge_path.mkdir(parents=True)

    template_count = copy_templates(templates_path)
    console.print(f"  {OK} 已复制 {template_count} 个模板到 {ISSUEKIT_DIR}/templates/")

    # 第 2 步：创建项目配置和知识库配置
    console.print(f"\n[cyan]创建项目配置...[/cyan]")
    write_project_config(issuekit_path, issues_dir=issues_dir)
    console.print(f"  {OK} 项目配置已创建：{ISSUEKIT_DIR}/config.yaml")

    console.print(f"\n[cyan]配置知识库引擎...[/cyan]")
    write_knowledge_config(knowledge_path)
    console.print(f"  {OK} 知识库配置已创建：{ISSUEKIT_DIR}/knowledge/")

    # 第 3 步：安装 Skills
    skills_dir = project_path / agent_config.skills_dir
    skills_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"\n[cyan]安装 {agent_config.name} Skills...[/cyan]")
    from issuekit.agent_skills import install_agent_skills
    install_count = install_agent_skills(
        skills_dir, include_openai_yaml=agent_config.has_openai_yaml,
    )
    console.print(f"  {OK} 已安装 {install_count} 个 Skill 到 {agent_config.skills_dir}/")

    # 第 4 步：展示结果
    console.print()
    tree = Tree(f"[bold]{project_path.name}[/bold]")

    issuekit_tree = tree.add(f"[cyan]{ISSUEKIT_DIR}/[/cyan]")
    issuekit_tree.add("config.yaml")
    tpl_tree = issuekit_tree.add("[cyan]templates/[/cyan]")
    tpl_tree.add("requirement.md")
    tpl_tree.add("technical-design.md")
    tpl_tree.add("test-plan.md")
    tpl_tree.add("release-note.md")
    tpl_tree.add("code-review.md")
    kn_tree = issuekit_tree.add("[cyan]knowledge/[/cyan]")
    kn_tree.add("config.yaml")

    skills_tree = tree.add(f"[cyan]{agent_config.skills_dir}/[/cyan]")
    for name in SKILL_NAMES:
        skill_subtree = skills_tree.add(f"[cyan]{name}/[/cyan]")
        skill_subtree.add("SKILL.md")
        if agent_config.has_openai_yaml:
            agents_subtree = skill_subtree.add("[cyan]agents/[/cyan]")
            agents_subtree.add("openai.yaml")

    console.print(tree)

    console.print(
        f"\n[green]IssueKit 初始化完成！[/green]\n\n"
        f"下一步：\n"
        f"  1. [cyan]$issuekit-knowledge[/cyan]  构建项目知识摘要（推荐）\n"
        f"  2. [cyan]$issuekit-require[/cyan]    创建第一个 Issue\n"
    )


def write_project_config(issuekit_path: Path, *, issues_dir: str = "issues"):
    """写入 IssueKit 项目级配置文件。"""
    config = issuekit_path / "config.yaml"
    config.write_text(
        "# IssueKit 项目配置\n"
        "\n"
        "# Issue 文档存放目录（相对项目根目录）\n"
        f"issues_dir: {issues_dir}\n",
        encoding="utf-8",
    )


def write_knowledge_config(knowledge_path: Path):
    """写入知识库引擎的默认配置文件。"""
    config = knowledge_path / "config.yaml"
    config.write_text(
        "# IssueKit 知识库配置\n"
        "# 项目上下文摘要自动生成到此目录\n"
        "\n"
        "# 摘要输出目录\n"
        "output_dir: .issuekit/knowledge\n"
        "\n"
        "# 生成的摘要章节\n"
        "sections:\n"
        "  - project-overview    # 目录结构、技术栈、依赖\n"
        "  - architecture        # 分层架构、设计模式\n"
        "  - api-surface         # API 端点、请求/响应约定\n"
        "  - data-model          # 数据库表、ORM 实体、关系\n"
        "  - integrations        # 外部服务、SDK、消息队列\n"
        "  - conventions         # 编码规范、命名约定、错误处理\n",
        encoding="utf-8",
    )
