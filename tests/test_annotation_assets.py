"""Geometry regressions for the shipped annotation example, not media approval."""
import json
import math
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1] / 'skills/science-video-production'
NS = {'s': 'http://www.w3.org/2000/svg'}


class AnnotationAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.svg = ET.parse(ROOT / 'assets/style/leader-and-arrow.svg').getroot()
        cls.profile = json.loads((ROOT / 'assets/style/precision-annotations.tokens.json').read_text(encoding='utf-8'))
        cls.arrow = cls.svg.find('.//s:g[@id="arrow"]', NS)
        cls.body = cls.arrow.find('s:polygon', NS)
        cls.points = [tuple(map(float, pair.split(','))) for pair in cls.body.get('points').split()]

    def test_direction_arrow_has_one_unstroked_closed_outline(self):
        # No independent centerline can retain a round/square cap beyond the tip.
        self.assertEqual(len(list(self.arrow)), 1)
        self.assertEqual(self.body.tag, '{' + NS['s'] + '}polygon')
        self.assertEqual(self.arrow.get('stroke'), 'none')
        self.assertEqual(self.arrow.get('fill'), 'currentColor')
        self.assertIsNone(self.body.get('stroke'))
        self.assertFalse(any('marker-' in key for node in self.arrow.iter() for key in node.attrib))

    def test_tip_is_sharp_and_shaft_terminates_at_head_base(self):
        p = self.points
        self.assertEqual(len(p), 7)
        tip = p[3]
        base_x = p[2][0]
        self.assertEqual([i for i, xy in enumerate(p) if xy[0] == max(q[0] for q in p)], [3])
        self.assertEqual(p[1][0], base_x)
        self.assertEqual(p[5][0], base_x)
        self.assertLess(base_x, tip[0])
        self.assertEqual(p[2][1] + p[4][1], 2 * tip[1])
        self.assertEqual(p[1][1] + p[5][1], 2 * tip[1])
        self.assertLess(p[2][1], p[1][1])
        self.assertGreater(p[4][1], p[5][1])

    def test_example_dimensions_match_arrow_profile(self):
        p, a = self.points, self.profile['arrow']
        self.assertEqual(p[5][1] - p[1][1], a['shaft_width_px'])
        self.assertEqual(p[3][0] - p[2][0], a['head_length_px'])
        self.assertEqual(p[4][1] - p[2][1], a['head_width_px'])
        self.assertGreater(a['head_width_px'], a['shaft_width_px'])

    def test_rotation_and_scale_preserve_unique_forward_tip(self):
        for degrees in range(-180, 181, 45):
            for scale in [.1875, .5, 1, 2]:
                with self.subTest(degrees=degrees, scale=scale):
                    angle = math.radians(degrees)
                    cos, sin = math.cos(angle), math.sin(angle)
                    transformed = [(scale*(x*cos-y*sin), scale*(x*sin+y*cos)) for x, y in self.points]
                    forward = [x*cos+y*sin for x, y in transformed]
                    self.assertTrue(all(forward[3] > v + 1e-6 for i, v in enumerate(forward) if i != 3))
                    self.assertEqual(sum(abs(v-forward[3]) < 1e-6 for v in forward), 1)

    def test_shipped_themes_use_current_line_palette_and_same_shape(self):
        for name in ['light', 'dark']:
            example = self.svg.find('.//s:g[@id="' + name + '-example"]', NS)
            arrow_uses = [n for n in example.iter() if n.get('href') == '#arrow']
            self.assertEqual(len(arrow_uses), 1)
            self.assertEqual(arrow_uses[0].get('color'), self.profile['colors'][name]['line'])


if __name__ == '__main__':
    unittest.main()
