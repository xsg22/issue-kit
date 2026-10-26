"""验证 Skill 安装完整性与升级边界。"""

from importlib import resources
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from issuekit.agent_skills import SKILL_DIRS, install_agent_skills


class InstallAgentSkillsTest(unittest.TestCase):
    def test_installs_complete_resources_and_preserves_unrelated_files(self):
        bundled = resources.files("issuekit") / "bundled_skills"
        self.assertEqual(set(SKILL_DIRS), {p.name for p in bundled.iterdir() if p.is_dir()})
        for include_metadata in (False, True):
            with self.subTest(include_metadata=include_metadata), TemporaryDirectory() as temp:
                destination = Path(temp)
                note = destination / "issuekit-merge" / "local-note.md"
                note.parent.mkdir()
                note.write_text("保留项目自有文件", encoding="utf-8")
                entry = note.parent / "SKILL.md"
                entry.write_text("旧版入口", encoding="utf-8")

                count = install_agent_skills(destination, include_openai_yaml=include_metadata)

                self.assertEqual(count, 11)
                self.assertEqual(note.read_text(encoding="utf-8"), "保留项目自有文件")
                for name in SKILL_DIRS:
                    source = bundled / name
                    self._assert_resources(source, destination / name, include_metadata)

    def _assert_resources(self, source, destination, include_metadata):
        for item in source.iterdir():
            if item.name == "agents" and not include_metadata:
                self.assertFalse((destination / item.name).exists())
                continue
            target = destination / item.name
            if item.is_dir():
                self._assert_resources(item, target, include_metadata)
            else:
                self.assertEqual(target.read_bytes(), item.read_bytes(), str(target))
