"""验证 Skill 资源、安装基线、本地修改保护及失败恢复。"""

from contextlib import contextmanager
from hashlib import sha256
from importlib import resources
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from typer.testing import CliRunner

from issuekit import __version__
from issuekit.agent_skills import (
    MANIFEST_NAME, SKILL_DIRS, SkillInstallError, install_agent_skills,
)
from issuekit.agents import AGENT_REGISTRY
from issuekit.cli import app


@contextmanager
def working_directory(path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class InstallAgentSkillsTest(unittest.TestCase):
    def test_installs_complete_resources_and_preserves_unrelated_files(self):
        bundled = resources.files("issuekit") / "bundled_skills"
        self.assertEqual(set(SKILL_DIRS), {p.name for p in bundled.iterdir() if p.is_dir()})
        for assistant in AGENT_REGISTRY:
            for command in ("init", "upgrade"):
                with self.subTest(assistant=assistant, command=command), TemporaryDirectory() as temp:
                    destination = Path(temp)
                    config = AGENT_REGISTRY[assistant]
                    skills = destination / config.skills_dir
                    note = skills / "issuekit-merge" / "local-note.md"
                    note.parent.mkdir(parents=True)
                    note.write_text("保留项目自有文件", encoding="utf-8")
                    with working_directory(destination):
                        result = CliRunner().invoke(app, ["init", "--ai", assistant])
                        self.assertEqual(result.exit_code, 0, result.output)
                        if command == "upgrade":
                            result = CliRunner().invoke(app, [command, "--ai", assistant])
                            self.assertEqual(result.exit_code, 0, result.output)
                    self.assertEqual(note.read_text(encoding="utf-8"), "保留项目自有文件")
                    manifest = json.loads((skills / MANIFEST_NAME).read_text())
                    self.assertEqual(manifest["version"], __version__)
                    for name in SKILL_DIRS:
                        self._assert_resources(bundled / name, skills / name, config.has_openai_yaml)
                    for name, digest in manifest["files"].items():
                        self.assertEqual(digest, sha256((skills / name).read_bytes()).hexdigest())

    def _assert_resources(self, source, destination, include_metadata):
        for item in source.iterdir():
            if item.name in {"__pycache__", ".DS_Store"} or item.name.endswith(".pyc"):
                self.assertFalse((destination / item.name).exists())
                continue
            if item.name == "agents" and not include_metadata:
                self.assertFalse((destination / item.name).exists())
                continue
            target = destination / item.name
            if item.is_dir():
                self._assert_resources(item, target, include_metadata)
            else:
                self.assertEqual(target.read_bytes(), item.read_bytes(), str(target))


class SafeUpgradeTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.package = root / "package"
        self.source = self.package / "bundled_skills"
        self.project = root / "project"
        self.project.mkdir()
        self.skills = self.project / ".agents" / "skills"
        self.resource = "issuekit-one/references/details.md"
        self.entry = "issuekit-one/SKILL.md"
        for name in (self.entry, self.resource, "issuekit-two/SKILL.md", "issuekit-one/agents/openai.yaml"):
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("旧版 " + name)
        self.addCleanup(patch.stopall)
        patch("issuekit.agent_skills.resources.files", return_value=self.package).start()
        patch("issuekit.agent_skills.SKILL_DIRS", ["issuekit-one", "issuekit-two"]).start()

    def install(self, **kwargs):
        return install_agent_skills(self.skills, **kwargs)

    def snapshot(self):
        return {str(p.relative_to(self.skills)): p.read_bytes()
                for p in self.skills.rglob("*") if p.is_file()}

    def test_unchanged_files_upgrade_and_record_new_version(self):
        self.assertEqual(self.install(), 2)
        (self.source / self.entry).write_text("新版")
        with patch("issuekit.agent_skills.__version__", "9.0.0"):
            self.install()
        self.assertEqual((self.skills / self.entry).read_text(), "新版")
        self.assertEqual(json.loads((self.skills / MANIFEST_NAME).read_text())["version"], "9.0.0")

    def test_generated_cache_is_not_distributed(self):
        cache = self.source / "issuekit-one/scripts/__pycache__"
        cache.mkdir(parents=True)
        (cache / "helper.cpython-312.pyc").write_bytes(b"local cache")
        (self.source / "issuekit-one/scripts/.DS_Store").write_bytes(b"desktop metadata")
        self.install()
        manifest = json.loads((self.skills / MANIFEST_NAME).read_text())
        self.assertFalse((self.skills / "issuekit-one/scripts/__pycache__").exists())
        self.assertFalse((self.skills / "issuekit-one/scripts/.DS_Store").exists())
        self.assertFalse(any("__pycache__" in name or ".DS_Store" in name for name in manifest["files"]))

    def test_local_change_blocks_entire_batch(self):
        self.install()
        (self.skills / self.resource).write_text("本地定制")
        (self.source / self.entry).write_text("新版")
        before = self.snapshot()
        with self.assertRaises(SkillInstallError) as raised:
            self.install()
        self.assertIn(self.resource, str(raised.exception.details))
        self.assertEqual(self.snapshot(), before)

    def test_no_baseline_different_existing_file_blocks_install(self):
        entry = self.skills / self.entry
        entry.parent.mkdir(parents=True)
        entry.write_text("未知来源的本地内容")
        before = self.snapshot()
        with self.assertRaises(SkillInstallError) as raised:
            self.install()
        self.assertIn("无旧安装基线", str(raised.exception.details))
        self.assertEqual(self.snapshot(), before)

    def test_local_content_matching_new_release_converges_with_or_without_baseline(self):
        for baseline in (False, True):
            with self.subTest(baseline=baseline):
                if baseline:
                    self.install()
                target = self.skills / self.entry
                target.parent.mkdir(parents=True, exist_ok=True)
                new_content = f"新版内容 {baseline}"
                (self.source / self.entry).write_text(new_content)
                target.write_text(new_content)
                self.install()
                manifest = json.loads((self.skills / MANIFEST_NAME).read_text())
                self.assertEqual(manifest["files"][self.entry], sha256(new_content.encode()).hexdigest())

    def test_local_deletion_is_not_silently_restored(self):
        self.install()
        (self.skills / self.resource).unlink()
        before = self.snapshot()
        with self.assertRaises(SkillInstallError) as raised:
            self.install()
        self.assertIn("本地已删除", str(raised.exception.details))
        self.assertEqual(self.snapshot(), before)

    def test_removed_release_resource_is_cleaned_up_and_reported(self):
        self.install()
        note = self.skills / "issuekit-one/references/project-note.md"
        note.write_text("自有文件")
        (self.source / self.resource).unlink()
        messages = []
        self.install(report=messages.append)
        self.assertFalse((self.skills / self.resource).exists())
        self.assertEqual(note.read_text(), "自有文件")
        self.assertIn(self.resource, messages[0])
        manifest = json.loads((self.skills / MANIFEST_NAME).read_text())
        self.assertNotIn(self.resource, manifest["files"])

    def test_removed_release_resource_modified_locally_blocks_cleanup(self):
        self.install()
        (self.source / self.resource).unlink()
        (self.skills / self.resource).write_text("本地定制")
        before = self.snapshot()
        with self.assertRaises(SkillInstallError):
            self.install()
        self.assertEqual(self.snapshot(), before)

    def test_already_absent_removed_resource_is_accepted(self):
        self.install()
        (self.source / self.resource).unlink()
        (self.skills / self.resource).unlink()
        self.install()
        self.assertNotIn(self.resource, json.loads((self.skills / MANIFEST_NAME).read_text())["files"])

    def test_other_host_preserves_codex_metadata_and_its_baseline(self):
        self.install(include_openai_yaml=True)
        metadata = self.skills / "issuekit-one/agents/openai.yaml"
        before = metadata.read_bytes()
        metadata.write_text("本地元数据")
        (self.source / "issuekit-one/agents/openai.yaml").unlink()
        self.install(include_openai_yaml=False)
        self.assertEqual(metadata.read_text(), "本地元数据")
        manifest = json.loads((self.skills / MANIFEST_NAME).read_text())
        self.assertEqual(manifest["files"]["issuekit-one/agents/openai.yaml"], sha256(before).hexdigest())

    def test_interrupted_write_keeps_baseline_and_retry_recovers(self):
        self.install()
        baseline = (self.skills / MANIFEST_NAME).read_bytes()
        (self.source / self.entry).write_text("新版入口")
        (self.source / self.resource).unlink()
        from issuekit.agent_skills import _atomic_write
        for fail_at in (2, 1):
            # 首次在基线提交时失败；第二次在重试的基线提交时再失败。
            calls = 0
            def interrupt(path, content):
                nonlocal calls
                calls += 1
                if calls == fail_at:
                    raise OSError("模拟磁盘写入失败")
                return _atomic_write(path, content)
            with patch("issuekit.agent_skills._atomic_write", side_effect=interrupt):
                with self.assertRaises(SkillInstallError) as raised:
                    self.install()
            self.assertIn("写入中断", str(raised.exception))
            self.assertEqual((self.skills / MANIFEST_NAME).read_bytes(), baseline)
        self.install()
        self.assertEqual((self.skills / self.entry).read_text(), "新版入口")
        self.assertFalse((self.skills / self.resource).exists())
        self.assertNotEqual((self.skills / MANIFEST_NAME).read_bytes(), baseline)

    def test_interrupted_initial_install_can_retry_without_a_baseline(self):
        from issuekit.agent_skills import _atomic_write
        calls = 0
        def interrupt(path, content):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("模拟写入中断")
            return _atomic_write(path, content)
        with patch("issuekit.agent_skills._atomic_write", side_effect=interrupt):
            with self.assertRaises(SkillInstallError):
                self.install()
        self.assertFalse((self.skills / MANIFEST_NAME).exists())
        self.assertEqual(self.install(), 2)
        self.assertTrue((self.skills / MANIFEST_NAME).exists())

    def test_concurrent_manifest_change_is_not_overwritten(self):
        self.install()
        (self.source / self.entry).write_text("新版入口")
        baseline_path = self.skills / MANIFEST_NAME
        original = json.loads(baseline_path.read_text())
        concurrent = dict(original, version="并发安装版本")
        from issuekit.agent_skills import _atomic_write
        def concurrent_install(path, content):
            _atomic_write(path, content)
            baseline_path.write_text(json.dumps(concurrent))
        with patch("issuekit.agent_skills._atomic_write", side_effect=concurrent_install):
            with self.assertRaises(SkillInstallError) as raised:
                self.install()
        self.assertIn("基线在预检后发生变化", str(raised.exception.details))
        self.assertEqual(json.loads(baseline_path.read_text()), concurrent)

    def test_invalid_manifest_or_path_is_rejected_without_changes(self):
        self.install()
        for name in ("../outside", "/absolute", "issuekit-one/references/../../outside"):
            with self.subTest(name=name):
                (self.skills / MANIFEST_NAME).write_text(json.dumps({
                    "schema_version": 1, "version": "0.1.6", "files": {name: "0" * 64},
                }))
                before = self.snapshot()
                with self.assertRaises(SkillInstallError):
                    self.install()
                self.assertEqual(self.snapshot(), before)
        (self.skills / MANIFEST_NAME).write_text("{broken")
        with self.assertRaises(SkillInstallError):
            self.install()

    def test_symbolic_link_is_not_followed(self):
        self.install()
        outside = self.project / "outside"
        outside.write_text("外部内容")
        target = self.skills / self.entry
        target.unlink()
        target.symlink_to(outside)
        with self.assertRaises(SkillInstallError):
            self.install()
        self.assertEqual(outside.read_text(), "外部内容")

    def test_internal_directory_link_is_not_followed(self):
        outside = self.project / "outside"
        outside.mkdir()
        skill = self.skills / "issuekit-one"
        skill.mkdir(parents=True)
        (skill / "references").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(SkillInstallError):
            self.install()
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((skill / "SKILL.md").exists())

    def test_atomic_replace_failure_preserves_existing_file_and_cleans_temporary(self):
        self.install()
        before = self.snapshot()
        (self.source / self.entry).write_text("新版")
        with patch("issuekit.agent_skills.os.replace", side_effect=OSError("替换失败")):
            with self.assertRaises(SkillInstallError):
                self.install()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(list(self.skills.rglob(".issuekit-*")), [self.skills / MANIFEST_NAME])

    def test_cli_conflict_is_nonzero_and_preserves_templates_and_config(self):
        self.install()
        (self.skills / self.resource).write_text("本地定制")
        issuekit = self.project / ".issuekit"
        (issuekit / "templates").mkdir(parents=True)
        template = issuekit / "templates/requirement.md"
        template.write_text("本地模板")
        config = issuekit / "config.yaml"
        config.write_text("原配置")
        with working_directory(self.project):
            for command in (["upgrade", "--ai", "codex"], ["init", "--ai", "codex", "--force"]):
                result = CliRunner().invoke(app, command)
                self.assertEqual(result.exit_code, 1, result.output)
                self.assertIn("同步未完成", result.output)
                self.assertNotIn("初始化完成", result.output)
                self.assertEqual(template.read_text(), "本地模板")
                self.assertEqual(config.read_text(), "原配置")
