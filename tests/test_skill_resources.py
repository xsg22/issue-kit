"""检查发行内容的发现信息和包内引用，不以文案匹配冒充行为评测。"""

from importlib import resources
from pathlib import PurePosixPath
import re
import unittest

import yaml

from issuekit.agent_skills import SKILL_DIRS


class SkillResourcesTest(unittest.TestCase):
    def test_metadata_and_bundled_links_are_valid(self):
        bundled = resources.files("issuekit") / "bundled_skills"
        for name in SKILL_DIRS:
            with self.subTest(skill=name):
                root = bundled / name
                content = (root / "SKILL.md").read_text(encoding="utf-8")
                match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", content, re.S)
                self.assertIsNotNone(match, name)
                metadata = yaml.safe_load(match.group(1))
                self.assertEqual(metadata["name"], name)
                self.assertIsInstance(metadata["description"], str)
                self.assertTrue(metadata["description"].strip())
                interface = yaml.safe_load(
                    (root / "agents" / "openai.yaml").read_text(encoding="utf-8")
                )["interface"]
                self.assertTrue(interface["display_name"].strip())
                self.assertTrue(interface["short_description"].strip())
                self._check_links(root, root)

    def _check_links(self, root, directory, prefix=""):
        for item in directory.iterdir():
            relative = prefix + item.name
            if item.is_dir():
                self._check_links(root, item, relative + "/")
            elif item.name.endswith(".md"):
                content = item.read_text(encoding="utf-8")
                # 只检查包内资源，不把用户项目路径、模板占位符或外部链接当作发行文件。
                for target in re.findall(r"\]\(([^)]+)\)", content):
                    target = target.split("#", 1)[0]
                    if not target or ":" in target or "{" in target:
                        continue
                    parts = list(PurePosixPath(relative).parent.parts)
                    for part in PurePosixPath(target).parts:
                        if part == "..":
                            if parts:
                                parts.pop()
                            else:
                                parts = [".."]
                                break
                        elif part != ".":
                            parts.append(part)
                    if parts and parts[0] in ("references", "scripts", "assets"):
                        resolved = root.joinpath(*parts)
                        self.assertTrue(resolved.is_file(), f"{relative}: {target}")
