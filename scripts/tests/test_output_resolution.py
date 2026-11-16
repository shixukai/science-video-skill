"""Offline synthetic ffprobe/adapter tests; never visual or listening approval."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_episode
import render_gate as gate
from stage_checks import Checks, output_target, validate_output_dimensions
import test_render_gate as fixtures


class OutputResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.RenderGateTests.setUpClass()
        cls.media_tmp = tempfile.TemporaryDirectory()
        cls.media_root = Path(cls.media_tmp.name)
        cls.media = {}
        for name, size in (('low', '1280x720'), ('hd', '1920x1080'),
                           ('large', '3840x2160'), ('square', '1080x1080'),
                           ('four_three', '1440x1080')):
            target = cls.media_root / (name + '.mp4')
            subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                            'color=c=blue:s=' + size + ':d=0.5:r=10',
                            '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono',
                            '-t', '0.5', '-c:v', 'libx264', '-preset', 'ultrafast',
                            '-threads', '2', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(target)], check=True)
            cls.media[name] = target
        cls.audio = cls.media_root / 'audio.wav'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                        'anullsrc=r=48000:cl=mono', '-t', '0.5', str(cls.audio)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.media_tmp.cleanup()
        fixtures.RenderGateTests.tearDownClass()

    def setUp(self):
        self.f = fixtures.RenderGateTests('test_first_dynamic_sample_runs_without_future_g3')
        self.f.setUp()

    def tearDown(self):
        self.f.tearDown()

    def probe_errors(self, name, target=None, **kwargs):
        data = {} if target is None else {'design': {'output': target}}
        checks = Checks(data, self.media_root)
        duration = checks.duration(self.media[name], formal_output=True, **kwargs)
        self.assertAlmostEqual(duration, .5, places=2)
        return checks.errors

    def adapter(self, name, phase=None):
        (self.f.root / 'candidate.mp4').write_bytes(self.media[name].read_bytes())
        with (self.f.root / 'adapter.py').open('a') as handle:
            if phase:
                handle.write('\nif a.phase == ' + repr(phase) + ': shutil.copyfile("candidate.mp4",a.output)\n')
            else:
                handle.write('\nshutil.copyfile("candidate.mp4",a.output)\n')
        self.f.data['execution']['entrypoint'] = self.f.ref('adapter.py')
        self.f.save()

    def test_formal_sample_rejects_actual_low_resolution_without_success_receipt(self):
        self.adapter('low')
        code, record = self.f.run_sample()
        self.assertEqual(code, 2, record)
        self.assertEqual(record['result'], 'render_failed')
        self.assertNotIn('output', record)
        self.assertTrue(any('actual 1280x720' in error for error in record['output_checks']))

    def test_roughcut_adapter_allows_low_resolution_even_with_final_target(self):
        self.adapter('low')
        self.f.data['design']['output'] = {'width': 1920, 'height': 1080}
        self.f.save()
        with patch('stage_checks.check_stage', return_value=[]):
            code, record = gate.run_render(self.f.root/'episode.json', 'roughcut', ['SH1'], 'roughcut.mp4', 'roughcut-run.json')
        self.assertEqual(code, 0, record)
        self.assertEqual(record['result'], 'rendered_unreviewed')

    def test_formal_full_rejects_low_resolution_after_valid_sample(self):
        self.adapter('low', phase='full')
        self.f.prepared_sample()
        with patch('stage_checks.check_stage', return_value=[]):
            code, record = gate.run_render(self.f.root/'episode.json', 'full', ['SH1'], 'full.mp4', 'full-run.json')
        self.assertEqual(code, 2, record)
        self.assertEqual(record['result'], 'render_failed')
        self.assertTrue(any('actual 1280x720' in error for error in record['output_checks']))

    def test_actual_hd_and_explicit_target_pass_at_existing_fps(self):
        self.assertEqual(self.probe_errors('hd'), [])
        self.assertEqual(self.probe_errors('hd', {'width': 1920, 'height': 1080}), [])
        self.adapter('hd')
        self.f.data['design']['output'] = {'width': 1920, 'height': 1080}
        code, record = self.f.run_sample()
        self.assertEqual(code, 0, record)
        self.assertEqual(record['result'], 'rendered_unreviewed')

    def test_declared_larger_output_requires_actual_exact_dimensions(self):
        target = {'width': 3840, 'height': 2160}
        self.assertTrue(any('match design.output 3840x2160 exactly' in e for e in self.probe_errors('hd', target)))
        self.assertEqual(self.probe_errors('large', target), [])

    def test_portrait_layout_is_preserved_and_landscape_cannot_substitute(self):
        checks = Checks({'design': {'output': {'width': 1080, 'height': 1920}}}, self.f.root)
        checks.duration(self.f.root/'baseline.mp4', formal_output=True)
        self.assertEqual(checks.errors, [])
        self.assertTrue(any('match design.output 1080x1920 exactly' in e
                            for e in self.probe_errors('hd', {'width': 1080, 'height': 1920})))

    def test_declared_square_and_four_three_canvas_preserve_layout(self):
        for name, width, height in (('square', 1080, 1080), ('four_three', 1440, 1080)):
            with self.subTest(name=name):
                self.assertEqual(self.probe_errors(name, {'width': width, 'height': height}), [])

    def test_invalid_target_blocks_formal_preflight_before_child(self):
        for index, target in enumerate((None, {}, {'width': 1920},
                {'width': True, 'height': 1080}, {'width': '1920', 'height': 1080},
                {'width': 1920.0, 'height': 1080}, {'width': 0, 'height': 1080},
                {'width': 1280, 'height': 720})):
            with self.subTest(target=target):
                self.f.data['design']['output'] = target
                code, record = self.f.run_sample(str(index))
                self.assertEqual(code, 1, record)
                self.assertTrue(any('design.output' in error for error in record['preflight_errors']))
                self.assertFalse((self.f.root/'invoked.json').exists())

    def test_unknown_or_malformed_probe_dimensions_fail_usefully(self):
        for dimensions in ({}, {'width': 1920}, {'width': '1920', 'height': 1080},
                           {'width': True, 'height': 1080}, {'width': 1920, 'height': None}):
            with self.subTest(dimensions=dimensions):
                checks = Checks({}, self.f.root)
                validate_output_dimensions({}, dimensions, checks.need)
                self.assertTrue(any('dimensions missing/invalid' in error for error in checks.errors))

    def test_actual_audio_only_duration_and_reference_media_are_exempt(self):
        checks = Checks({'design': {'output': {'width': 3840, 'height': 2160}}}, self.media_root)
        checks.duration(self.audio, require_video=False, formal_output=True)
        checks.duration(self.media['low'])
        self.assertEqual(checks.errors, [])

    def test_duration_cache_does_not_let_reference_probe_bypass_formal_check(self):
        checks = Checks({}, self.media_root)
        checks.duration(self.media['low'])
        self.assertEqual(checks.errors, [])
        checks.duration(self.media['low'], formal_output=True)
        self.assertTrue(any('actual 1280x720' in error for error in checks.errors))

    def test_g3_viewing_actual_clip_enforces_floor_but_roughcut_is_exempt(self):
        (self.f.root/'low.mp4').write_bytes(self.media['low'].read_bytes())
        viewing = copy.deepcopy(self.f.data['design']['approved_film_reference']['viewing'])
        viewing.update(self.f.ref('low.mp4'), scope='representative')
        checks = Checks(self.f.data, self.f.root)
        checks.viewing(viewing, 'G3 motion', 'representative')
        self.assertTrue(any('actual 1280x720' in error for error in checks.errors))
        viewing['scope'] = 'full_roughcut'
        checks = Checks(self.f.data, self.f.root)
        checks.viewing(viewing, 'G2 roughcut', 'full_roughcut')
        self.assertEqual(checks.errors, [])

    def test_final_viewing_requires_declared_resolution(self):
        (self.f.root/'final.mp4').write_bytes(self.media['hd'].read_bytes())
        self.f.data['design']['output'] = {'width': 3840, 'height': 2160}
        self.f.data['deliverables'] = {'video': 'final.mp4'}
        viewing = copy.deepcopy(self.f.data['design']['approved_film_reference']['viewing'])
        viewing.update(self.f.ref('final.mp4'), scope='full_episode')
        checks = Checks(self.f.data, self.f.root)
        checks.viewing(viewing, 'G5 complete viewing', 'full_episode', final=True)
        self.assertTrue(any('match design.output 3840x2160 exactly' in error for error in checks.errors))

    def test_delivery_and_g5_probe_actual_low_resolution(self):
        (self.f.root/'final.mp4').write_bytes(self.media['low'].read_bytes())
        self.f.data['deliverables'] = {'video': 'final.mp4'}
        self.f.data['qa']['reviewed_sha256'] = {'video': self.f.ref('final.mp4')['sha256']}
        for stage in ('G5', 'delivery'):
            with self.subTest(stage=stage):
                errors, notes = check_episode.check(self.f.data, self.f.root, stage)
                # Incomplete fixture intentionally has unrelated review failures.
                # This assertion checks the public entry point's real ffprobe result.
                self.assertTrue(any(error.startswith('video: actual 1280x720') for error in errors), errors)

    def test_cover_path_does_not_apply_video_floor(self):
        with patch.object(check_episode, 'validate_cover_review') as cover_check:
            errors, notes = check_episode.check({'design': {'output': None}}, self.f.root, 'covers')
        self.assertEqual(errors, [])
        cover_check.assert_called_once()


if __name__ == '__main__':
    unittest.main()
