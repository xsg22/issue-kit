"""安装发行版 Skill，并以内容摘要保护项目内的本地修改。"""

from hashlib import sha256
from importlib import resources
import json
import os
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Callable

from issuekit import __version__

SKILL_DIRS = [
    "issuekit-require",
    "issuekit-design",
    "issuekit-coding",
    "issuekit-test",
    "issuekit-business-test",
    "issuekit-release",
    "issuekit-review",
    "issuekit-merge",
    "issuekit-cleanup",
    "issuekit-change",
    "issuekit-knowledge",
]
MANIFEST_NAME = ".issuekit-manifest.json"


class SkillInstallError(Exception):
    """冲突或部分写入失败；调用方不能把本次安装报告为完成。"""

    def __init__(self, message: str, *, details: list[str]):
        super().__init__(message)
        self.details = details


def _digest(content: bytes) -> str:
    return sha256(content).hexdigest()


def _read_baseline(content: bytes | None) -> dict[str, str]:
    if content is None:
        return {}
    try:
        manifest = json.loads(content)
        files = manifest["files"]
        if manifest["schema_version"] != 1 or not isinstance(manifest["version"], str):
            raise ValueError("不支持的基线格式")
        if not isinstance(files, dict):
            raise ValueError("文件摘要不是对象")
        for name, digest in files.items():
            parts = PurePosixPath(name).parts
            valid_resource = (
                len(parts) == 2 and parts[1] == "SKILL.md"
                or len(parts) >= 3 and parts[1] in {"references", "scripts", "assets"}
                or len(parts) == 3 and parts[1:] == ("agents", "openai.yaml")
            )
            if (
                not parts or not parts[0].startswith("issuekit-")
                or PurePosixPath(name).is_absolute() or ".." in parts
                or PurePosixPath(name).as_posix() != name or "\\" in name
                or not valid_resource or not isinstance(digest, str)
                or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest)
            ):
                raise ValueError(f"无效的受管理资源: {name}")
        return files
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SkillInstallError("安装基线无法读取，未修改 Skill；请先核对或恢复基线。", details=[str(exc)]) from exc


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".issuekit-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _check_path(path: Path, root: Path) -> None:
    # 入口目录可位于系统链接下；入口内部资源不得通过链接逃逸。
    current = path
    while True:
        if current.is_symlink():
            raise ValueError(f"路径包含符号链接: {path}")
        if current != path and current.exists() and not current.is_dir():
            raise ValueError(f"资源父路径不是目录: {current}")
        if current == root:
            break
        current = current.parent
    if path.exists() and not path.is_file():
        raise ValueError(f"资源路径不是普通文件: {path}")


def install_agent_skills(
    skills_dir: Path,
    *,
    include_openai_yaml: bool = False,
    report: Callable[[str], None] | None = None,
) -> int:
    """安装全部 Skill，返回数量；冲突全批停止，写入失败保留旧基线供重试。

    每个宿主 skills 目录独立记录发行版本与已安装资源摘要。无旧基线时，
    仅接纳缺失资源或与新版相同的内容；本地定制需先自行核对和迁移。
    文件逐个原子替换，基线最后更新；这不是跨文件事务。
    """
    skills_dir = skills_dir.resolve()
    bundled = resources.files("issuekit") / "bundled_skills"
    desired: dict[str, bytes] = {}

    def collect(source, prefix: str) -> None:
        for item in source.iterdir():
            if item.name in {"__pycache__", ".DS_Store"} or item.name.endswith(".pyc"):
                continue
            name = f"{prefix}/{item.name}"
            if item.is_dir():
                collect(item, name)
            else:
                desired[name] = item.read_bytes()

    # 先读取完整发行资源，缺失入口不得静默跳过并谎报安装成功。
    for skill_name in SKILL_DIRS:
        source = bundled / skill_name
        desired[f"{skill_name}/SKILL.md"] = (source / "SKILL.md").read_bytes()
        for name in ("references", "scripts", "assets"):
            if (source / name).is_dir():
                collect(source / name, f"{skill_name}/{name}")
        metadata = source / "agents" / "openai.yaml"
        if include_openai_yaml and metadata.is_file():
            desired[f"{skill_name}/agents/openai.yaml"] = metadata.read_bytes()

    manifest_path = skills_dir / MANIFEST_NAME
    try:
        _check_path(manifest_path, skills_dir)
    except ValueError as exc:
        raise SkillInstallError("安装路径不安全，未修改 Skill。", details=[str(exc)]) from exc
    original_manifest = manifest_path.read_bytes() if manifest_path.exists() else None
    baseline = _read_baseline(original_manifest)
    # 其他宿主不管理 Codex 元数据，保留其文件及原基线。
    ignored = {name: digest for name, digest in baseline.items()
               if not include_openai_yaml and name.endswith("/agents/openai.yaml")}
    hashes = {name: _digest(content) for name, content in desired.items()}
    writes: list[str] = []
    removals: list[str] = []
    conflicts: list[str] = []
    observed: dict[str, str | None] = {}
    for name in sorted((baseline.keys() | desired.keys()) - ignored.keys()):
        path = skills_dir / name
        try:
            _check_path(path, skills_dir)
            current = _digest(path.read_bytes()) if path.exists() else None
        except (OSError, ValueError) as exc:
            conflicts.append(f"{name}: {exc}")
            continue
        observed[name] = current
        previous = baseline.get(name)
        if name in desired:
            if current == hashes[name]:
                continue
            if current == previous and (current is not None or name not in baseline):
                writes.append(name)
            else:
                reason = "本地已删除" if current is None else "本地内容与新版不同"
                if name not in baseline:
                    reason += "，无旧安装基线"
                conflicts.append(f"{name}: {reason}")
        elif current is not None:
            if current == previous:
                removals.append(name)
            else:
                conflicts.append(f"{name}: 新版已移除，但本地已修改")
    if conflicts:
        raise SkillInstallError(
            "Skill 同步未完成：发现本地修改或无基线冲突，全部 Skill 保持原样。请核对并迁移本地定制后重试。",
            details=conflicts,
        )

    changed: list[str] = []
    try:
        for name in writes + removals:
            path = skills_dir / name
            _check_path(path, skills_dir)
            current = _digest(path.read_bytes()) if path.exists() else None
            if current != observed[name]:
                raise ValueError(f"预检后文件发生变化: {name}")
            if name in desired:
                _atomic_write(path, desired[name])
                changed.append(f"已写入 {name}")
            else:
                path.unlink()
                changed.append(f"已移除 {name}")
        manifest = {"schema_version": 1, "version": __version__, "files": hashes | ignored}
        _check_path(manifest_path, skills_dir)
        if (manifest_path.read_bytes() if manifest_path.exists() else None) != original_manifest:
            raise ValueError("安装基线在预检后发生变化，请核对并发安装")
        _atomic_write(manifest_path, (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode())
    except (OSError, ValueError) as exc:
        raise SkillInstallError(
            "Skill 同步未完成：写入中断，本次未更新安装基线；已写文件未回滚，可核对后重试。",
            details=changed + [str(exc)],
        ) from exc
    if report:
        for name in removals:
            report(f"已移除发行版不再提供且未经本地修改的资源: {name}")
    return len(SKILL_DIRS)
