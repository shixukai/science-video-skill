"""Regression tests for the 3-skill split (Topic Selection / Production / Publishing)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sync_companion_skills.py"
spec = importlib.util.spec_from_file_location("sync_companion_skills", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class CompanionSkillsContractTests(unittest.TestCase):
    def test_companion_skills_are_self_contained_and_route_clean(self):
        for name in sync.SKILL_NAMES:
            with self.subTest(skill=name):
                files = sync.validate_companion_source(ROOT / "skills", name)
                self.assertTrue(any(rel.as_posix() == "SKILL.md" for rel, _ in files))
                for rel, path in files:
                    if path.suffix.lower() != ".md":
                        continue
                    text = path.read_text(encoding="utf-8")
                    self.assertNotIn("MoneyPrinterTurbo", text)
                    self.assertNotRegex(text, r"(?i)\bvork\b")
                    self.assertNotIn("google-flow-production.md", text)

    def test_topic_positioning_config_matches_series_profile(self):
        series = json.loads((ROOT / "config/series-profile.json").read_text(encoding="utf-8"))
        topic_cfg = json.loads(
            (ROOT / "skills/science-video-topic-selection/config/topic-positioning.json").read_text(encoding="utf-8")
        )
        for key in ("id", "preserves_user_commissioned_topics", "core_proposition",
                    "content_mix_guidance", "question_framing", "scope_discipline"):
            self.assertEqual(topic_cfg[key], series["editorial_positioning"][key], key)

    def test_publishing_profile_matches_series_operations(self):
        series = json.loads((ROOT / "config/series-profile.json").read_text(encoding="utf-8"))
        pub_cfg = json.loads(
            (ROOT / "skills/science-video-publishing/config/publishing-profile.json").read_text(encoding="utf-8")
        )
        ops = series["operations"]
        self.assertEqual(pub_cfg["timezone"], ops["timezone"])
        self.assertEqual(pub_cfg["youtube_made_for_kids"], ops["youtube_made_for_kids"])
        self.assertEqual(pub_cfg["required_publication_tag"], ops["required_publication_tag"])
        self.assertEqual(pub_cfg["optional_ai_creation"], ops["optional_ai_creation"])
        self.assertEqual(pub_cfg["publication_spacing"]["recommended_min_gap_hours"],
                         ops["publication_spacing"]["recommended_min_gap_hours"])
        self.assertEqual(pub_cfg["video_download"]["allow_download"], ops["video_download"]["allow_download"])
        self.assertEqual(
            [c["title"] for c in pub_cfg["douyin_collections"]["collections"]],
            [c["title"] for c in ops["douyin_collections"]["collections"]],
        )
        self.assertEqual(pub_cfg["copy_limits"]["title_max_codepoints"],
                         series["delivery"]["title_max_codepoints"])
        self.assertEqual(pub_cfg["copy_limits"]["description_and_tags_max_codepoints"],
                         series["delivery"]["description_and_tags_max_codepoints"])
        policy = json.loads((ROOT / "config/production-policy.json").read_text(encoding="utf-8"))
        self.assertEqual(policy["feed_package"]["destinations"], ["douyin_composer_group"])
        self.assertIn("xiaohongshu", policy["feed_package"]["master_destinations"])
        pub_md = (ROOT / "skills/science-video-publishing/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Xiaohongshu (user-operated composer handoff, 16:9 landscape video)", pub_md)
        self.assertIn("NOT `-feed916.mp4`", pub_md)

    def test_sync_install_check_and_backup_in_temp_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "codex"
            (home / "skills/unrelated-skill").mkdir(parents=True)
            (home / "skills/unrelated-skill/SKILL.md").write_text("---\nname: unrelated-skill\n---\n", encoding="utf-8")
            plan = sync.plan_sync(ROOT / "skills", home)
            self.assertTrue(all(r["status"] == "missing" for r in plan))
            sync.install(plan)
            checked = sync.plan_sync(ROOT / "skills", home)
            self.assertTrue(all(r["status"] == "current" for r in checked))
            target_md = home / "skills/science-video-publishing/SKILL.md"
            original = target_md.read_bytes()
            target_md.write_bytes(original + b"\n# local tweak\n")
            diff_plan = sync.plan_sync(ROOT / "skills", home)
            with self.assertRaises(ValueError):
                sync.install(diff_plan, replace_existing=False)
            sync.install(diff_plan, replace_existing=True)
            self.assertEqual(target_md.read_bytes(), original)
            self.assertTrue((home / "skills/.science-video-skill-backups/science-video-publishing").is_dir())
            self.assertTrue((home / "skills/unrelated-skill/SKILL.md").is_file())

    def test_escaping_link_in_companion_skill_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "skills"
            bad = src / "science-video-topic-selection"
            bad.mkdir(parents=True)
            (bad / "SKILL.md").write_text(
                "---\nname: science-video-topic-selection\n---\n[escape](../../config/series-profile.json)\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "escapes"):
                sync.validate_companion_source(src, "science-video-topic-selection")


if __name__ == "__main__":
    unittest.main()
