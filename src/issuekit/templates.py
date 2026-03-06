"""模板管理 — 将内置模板复制到项目目录。"""

from importlib import resources
from pathlib import Path


def copy_templates(target_dir: Path) -> int:
    """将所有内置模板复制到目标目录，返回复制的文件数。"""
    bundled = resources.files("issuekit") / "bundled_templates"
    count = 0
    for item in bundled.iterdir():
        if item.name.endswith(".md"):
            content = item.read_text(encoding="utf-8")
            dest = target_dir / item.name
            dest.write_text(content, encoding="utf-8")
            count += 1
    return count
