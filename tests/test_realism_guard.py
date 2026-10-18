"""Synthetic records only: no fixture claims real visual/scientific acceptance."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('realism_gate_fixture', SCRIPTS / 'tests/test_render_gate.py')
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)
import render_gate as gate
from realism_guard import validate_realism
from stage_checks import Checks


class RealismGuardTests(fixture.RenderGateTests):
    # Inherit the real adapter fixture and existing gate regressions deliberately.
    def errors(self, phase='sample', shot_ids=None):
        checks = Checks(self.data, self.root)
        validate_realism(checks, shot_ids or ['SH1'], phase)
        return checks.errors

    def realistic(self, medium='ai_realistic', renderer='video_model'):
        r = self.data['shots'][0]['shotbook']['realism']
        r.update(medium=medium, renderer=renderer, motion_kind='subject_motion',
                 disclosure='Synthetic test declaration: generated illustration, not a real recording.')
        r.pop('exception', None)
        if medium == 'authentic_recording':
            r['source_asset_id'] = 'REAL1'
            self.data['shots'][0]['asset_ids'] = ['REAL1']
            self.data['assets'] = [{'id':'REAL1', 'kind':'real_capture', **self.ref('baseline.mp4'),
                'source':'Synthetic source fixture, not real footage.', 'creator':'Synthetic fixture',
                'rights':{'status':'cleared', 'evidence':'Synthetic test record only.', 'scope':'Synthetic tests only.'}}]
        return r

    def test_missing_contract_fails_closed_before_child(self):
        self.data['design'].pop('visual_intent')
        code, receipt = self.run_sample()
        self.assertEqual(code, 1)
        self.assertTrue(any('visual intent required' in e for e in receipt['preflight_errors']))
        self.assertFalse((self.root / 'invoked.json').exists())

    def test_all_realistic_kinds_distinct(self):
        for medium, renderer in [('authentic_recording', 'camera'), ('ai_realistic', 'video_model'), ('three_d', 'three_d_engine')]:
            self.realistic(medium, renderer)
            self.assertEqual(self.errors(), [], medium)

    def test_malformed_medium_fails_closed_without_exception(self):
        for value in ([], {}, None, 3):
            self.data['shots'][0]['shotbook']['realism']['medium'] = value
            self.assertTrue(self.errors())

    def test_ai_cannot_claim_vector_or_three_d_renderer(self):
        for renderer in ('vector_renderer', 'raster_animation', 'still_pan', 'three_d_engine'):
            self.realistic(renderer=renderer)
            self.assertTrue(any('renderer must match' in e for e in self.errors()), renderer)

    def test_vector_cannot_claim_video_model(self):
        r = self.data['shots'][0]['shotbook']['realism']; r['renderer'] = 'video_model'
        self.assertTrue(any('renderer must match' in e for e in self.errors()))

    def test_static_pan_never_realistic_subject_motion(self):
        r = self.realistic(); r['motion_kind'] = 'camera_pan_only'
        self.assertTrue(any('actual subject motion' in e for e in self.errors()))

    def test_synthetic_disclosure_is_required(self):
        for medium, renderer in [('ai_realistic', 'video_model'), ('three_d', 'three_d_engine')]:
            r = self.realistic(medium, renderer); r.pop('disclosure')
            self.assertTrue(any('disclosure' in e for e in self.errors()))

    def test_every_full_frame_nonrealistic_route_requires_scoped_exception(self):
        for role in ('main', 'explanation'):
            for medium, renderer in [('pure_2d','vector_renderer'), ('static_pan','still_pan'), ('infographic','raster_animation')]:
                r = self.data['shots'][0]['shotbook']['realism']
                r.update(role=role, medium=medium, renderer=renderer); r.pop('exception', None)
                self.assertTrue(any('per-shot user exception' in e for e in self.errors()), (role, medium))

    def test_wrong_shot_exception_or_changed_evidence_rejected(self):
        r = self.data['shots'][0]['shotbook']['realism']; r['exception']['shot_id'] = 'SH2'
        self.assertTrue(any('per-shot user exception' in e for e in self.errors()))
        r['exception']['shot_id'] = 'SH1'; (self.root/'approval.txt').write_text('changed')
        self.assertTrue(any('hash stale' in e for e in self.errors()))

    def test_auxiliary_role_is_not_full_frame_escape(self):
        r = self.data['shots'][0]['shotbook']['realism']; r.update(role='auxiliary'); r.pop('exception')
        self.assertTrue(any('explicit main/explanation role' in e for e in self.errors()))

    def test_style_reference_missing_or_changed_blocks_sample(self):
        intent = self.data['design']['visual_intent']; intent['style_reference']['sha256'] = '0'*64
        self.assertTrue(any('hash stale' in e for e in self.errors()))
        intent.pop('style_reference'); self.assertTrue(any('evidence file required' in e for e in self.errors()))

    def test_ordinary_subtitles_do_not_change_realism_contract(self):
        self.realistic('authentic_recording', 'camera')
        self.data['captions'] = {'mode':'ordinary_subtitles'}
        self.assertEqual(self.errors(), [])

    def test_authentic_source_missing_rights_or_wrong_kind_blocks(self):
        self.realistic('authentic_recording', 'camera')
        self.data['assets'][0]['kind'] = 'ai_generated'
        self.assertTrue(any('linked real source' in e for e in self.errors()))
        self.data['assets'][0]['kind'] = 'real_capture'
        self.data['assets'][0]['rights']['status'] = 'pending'
        self.assertTrue(any('cleared rights' in e for e in self.errors()))

    def test_modality_conflict_blocks(self):
        self.realistic(); self.data['shots'][0]['modality'] = 'pure_2d'
        self.assertTrue(any('modality conflicts' in e for e in self.errors()))

    def test_final_delivery_validation_cannot_omit_realism(self):
        self.final_data(); self.data['design'].pop('visual_intent')
        self.assertTrue(any('visual intent required' in e for e in self.final_errors()))

    def test_contract_changes_invalidate_design_binding(self):
        old = gate.design_context(self.data, ['SH1'])
        self.data['design']['visual_intent']['scientific_constraints'] = 'Changed constraint.'
        self.assertNotEqual(old, gate.design_context(self.data, ['SH1']))

    def test_full_continuous_review_rejects_technical_or_static_claims(self):
        self.prepared_sample(); animation = self.data['qa']['visual_frames']['animation']
        good = copy.deepcopy(animation['viewing'])
        for change in ({'method':'frame_samples'}, {'heard':False}, {'watched':False}, {'ranges':[]}, {'reviewer':'synthetic producer'}):
            animation['viewing'] = {**good, **change}
            self.assertTrue(self.errors('full'), change)
        animation['viewing'] = good
        animation.pop('independent_review_evidence')
        self.assertTrue(any('independent review evidence' in e for e in self.errors('full')))

    def test_full_probe_rejects_still_or_text_as_sample(self):
        self.prepared_sample(); animation = self.data['qa']['visual_frames']['animation']
        (self.root/'not-video.txt').write_text('Technical report, not continuous A/V.')
        animation['viewing'].update(self.ref('not-video.txt'))
        self.assertTrue(self.errors('full'))

    def test_valid_synthetic_review_structure_passes_only_structurally(self):
        self.prepared_sample()
        self.assertEqual(self.errors('full'), [])


if __name__ == '__main__':
    unittest.main()
