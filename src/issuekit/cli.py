"""IssueKit 命令行入口。"""

import os
import sys

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import typer

from issuekit.commands.init import init as init_cmd
from issuekit.agents import AGENT_REGISTRY

SUPPORTED_AI = ", ".join(AGENT_REGISTRY.keys())

INIT_USAGE = (
    "\n用法示例:\n"
    "  issuekit init --ai cursor\n"
    "  issuekit init --ai claude\n"
    "  issuekit init --ai cursor --force\n"
)


class ChineseErrorGroup(typer.core.TyperGroup):
    """拦截 Click 层的参数解析错误，替换为中文提示。"""

    def parse_args(self, ctx, args):
        try:
            return super().parse_args(ctx, args)
        except SystemExit:
            raise


app = typer.Typer(
    name="issuekit",
    help="AI 辅助开发的 Issue 全生命周期工具。",
    no_args_is_help=True,
)


@app.command("init")
def init(
    ai: str = typer.Option(
        None,
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
    """在项目中初始化 IssueKit。

    安装文档模板、AI 助手命令和知识库配置。

    用法示例:
        issuekit init --ai cursor
        issuekit init --ai cursor --issues-dir doc/issues
        issuekit init --ai cursor --force
    """
    if not ai:
        from rich.console import Console
        console = Console()
        console.print(
            f"[red]错误:[/red] 缺少必需参数 --ai\n"
            f"[dim]支持的选项:[/dim] {SUPPORTED_AI}"
            f"{INIT_USAGE}"
        )
        raise typer.Exit(2)
    init_cmd(ai=ai, issues_dir=issues_dir, here=here, force=force)


@app.command("version")
def version():
    """显示 IssueKit 版本号。"""
    from issuekit import __version__
    typer.echo(f"issuekit {__version__}")


def main():
    app()
