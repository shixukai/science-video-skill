"""Regression tests for deterministic locked cover typography (scripts/compose_cover.py)."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import compose_cover  # noqa: E402


class ComposeCoverTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.spec = compose_cover.load_spec()

    def tearDown(self):
        self.tmp.cleanup()

    def _make_bg(self, name: str, size: tuple[int, int], rgb: tuple[int, int, int]) -> Path:
        p = self.dir / name
        Image.new("RGB", size, rgb).save(p, "PNG")
        return p

    def test_compose_3_4_daylight_terracotta_and_receipt_contract(self):
        raw = self._make_bg("raw_3_4.png", (1080, 1440), (235, 240, 244))
        out = self.dir / "cover-3x4.png"
        rep = self.dir / "cover-3x4.json"
        receipt = compose_cover.compose_cover(
            raw, "cover_3_4", "加油枪", "油一满，没电线的枪嘴\n怎么知道该停？", out, rep,
            palette="daylight_terracotta", lang="zh",
        )
        self.assertTrue(out.is_file())
        self.assertTrue((self.dir / "cover-3x4-background.png").is_file())
        self.assertTrue((self.dir / "cover-3x4-text-layer.png").is_file())
        self.assertTrue((self.dir / "cover-3x4-preview-270w.png").is_file())
        with Image.open(out) as im:
            self.assertEqual(im.size, (1080, 1440))
        with Image.open(self.dir / "cover-3x4-preview-270w.png") as pv:
            self.assertEqual(pv.size, (270, 360))
        typo = receipt["typography"]
        self.assertEqual(typo["font_family"], "Noto Sans SC")
        self.assertEqual(typo["main_weight"], 850)
        self.assertEqual(typo["subtitle_weight"], 740)
        self.assertEqual(typo["main_size_px"], 114)
        self.assertEqual(typo["subtitle_size_px"], 60)
        self.assertEqual(typo["palette"], "daylight_terracotta")
        self.assertEqual(typo["main_color_hex"], "#994B37")
        self.assertEqual(typo["subtitle_color_hex"], "#193E4B")
        self.assertFalse(typo["stroke_shadow_or_backing"])
        self.assertGreaterEqual(receipt["measurements"]["main_contrast_ratio"], 3.2)
        self.assertGreaterEqual(receipt["measurements"]["subtitle_contrast_ratio"], 4.5)
        # Reusing the same receipt path refuses overwrite
        with self.assertRaises(FileExistsError):
            compose_cover.compose_cover(
                raw, "cover_3_4", "加油枪", "油一满，没电线的枪嘴\n怎么知道该停？", out, rep,
                palette="daylight_terracotta", lang="zh",
            )

    def test_compose_4_3_dark_presets_and_16_9_english(self):
        raw_dark = self._make_bg("raw_4_3_dark.png", (1440, 1080), (14, 34, 48))
        out43 = self.dir / "cover-4x3.png"
        rep43 = self.dir / "cover-4x3.json"
        r43 = compose_cover.compose_cover(
            raw_dark, "cover_4_3", "深海无鱼区", "海沟深达一万一千米，\n为何鱼类止步八千四？", out43, rep43,
            palette="dark_ocean_gold", lang="zh",
        )
        self.assertEqual(r43["typography"]["main_size_px"], 110)
        self.assertEqual(r43["typography"]["subtitle_size_px"], 58)
        self.assertEqual(r43["typography"]["main_color_hex"], "#F2C14E")
        self.assertEqual(r43["typography"]["subtitle_color_hex"], "#E6F1F5")

        raw_169 = self._make_bg("raw_16_9.png", (1920, 1080), (242, 238, 228))
        out169 = self.dir / "cover-16x9-en.png"
        rep169 = self.dir / "cover-16x9-en.json"
        r169 = compose_cover.compose_cover(
            raw_169, "cover_16_9", "Fuel Nozzles", "Zero Wires Inside:\nHow Does It Click Off?", out169, rep169,
            palette="daylight_navy", lang="en",
        )
        self.assertEqual(r169["typography"]["main_size_px"], 108)
        self.assertEqual(r169["typography"]["subtitle_size_px"], 54)
        self.assertEqual(r169["typography"]["main_color_hex"], "#1E3246")
        self.assertEqual(r169["typography"]["subtitle_color_hex"], "#243F4D")

    def test_rejects_unregistered_palette_wrong_background_tone_and_overflow(self):
        raw_light = self._make_bg("light.png", (1080, 1440), (245, 245, 245))
        raw_dark = self._make_bg("dark.png", (1080, 1440), (15, 22, 30))

        # Unregistered palette rejected
        with self.assertRaisesRegex(ValueError, "color_presets"):
            compose_cover.compose_cover(
                raw_light, "cover_3_4", "加油枪", "第一行\n第二行", self.dir / "a.png", self.dir / "a.json",
                palette="freestyle_neon",
            )
        # Light palette on dark background rejected
        with self.assertRaisesRegex(ValueError, "dark upper-left"):
            compose_cover.compose_cover(
                raw_dark, "cover_3_4", "加油枪", "第一行\n第二行", self.dir / "b.png", self.dir / "b.json",
                palette="daylight_terracotta",
            )
        # Dark palette on bright background rejected
        with self.assertRaisesRegex(ValueError, "bright upper-left"):
            compose_cover.compose_cover(
                raw_light, "cover_3_4", "加油枪", "第一行\n第二行", self.dir / "c.png", self.dir / "c.json",
                palette="dark_terracotta",
            )
        # Wrong line counts rejected
        with self.assertRaisesRegex(ValueError, "single non-empty line"):
            compose_cover.compose_cover(
                raw_light, "cover_3_4", "第一行\n第二行", "问一\n问二", self.dir / "d.png", self.dir / "d.json",
            )
        with self.assertRaisesRegex(ValueError, "strictly 2"):
            compose_cover.compose_cover(
                raw_light, "cover_3_4", "加油枪", "只有一行没有换行", self.dir / "e.png", self.dir / "e.json",
            )
        # Overlong text rejected rather than silently shrunk (no_auto_shrink=true)
        with self.assertRaisesRegex(ValueError, "no_auto_shrink"):
            compose_cover.compose_cover(
                raw_light, "cover_3_4", "这是一段刻意超长用来触发宽度拦截的标题文字", "第一行\n第二行",
                self.dir / "f.png", self.dir / "f.json",
            )
        # Stretched mismatched aspect ratio rejected
        raw_wide = self._make_bg("wide.png", (1920, 1080), (245, 245, 245))
        with self.assertRaisesRegex(ValueError, "aspect ratio"):
            compose_cover.compose_cover(
                raw_wide, "cover_3_4", "加油枪", "第一行\n第二行", self.dir / "g.png", self.dir / "g.json",
            )

    def test_cli_list_palettes_works(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "compose_cover.py"), "list-palettes"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["default_palette"], "daylight_terracotta")
        self.assertEqual(payload["fonts"]["zh"]["family"], "Noto Sans SC")
        self.assertEqual(set(payload["color_presets"]), {
            "daylight_terracotta", "daylight_navy", "dark_terracotta", "dark_ocean_gold"
        })


if __name__ == "__main__":
    unittest.main()
