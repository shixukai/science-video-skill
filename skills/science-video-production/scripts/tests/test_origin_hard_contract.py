"""Synthetic provenance regressions only; no authorship or media approval.

The sibling candidate module can be tested privately before installation. After
installation this test also works from scripts/tests against scripts/origin_guard.
"""
import copy
import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SCRIPTS = Path(os.environ.get('SCIENCE_VIDEO_SCRIPTS', str(HERE.parent)))
sys.path.insert(0, str(SCRIPTS))
MODULE = HERE / 'origin_guard.py' if (HERE / 'origin_guard.py').is_file() else SCRIPTS / 'origin_guard.py'
SPEC = importlib.util.spec_from_file_location('origin_hard_candidate', MODULE)
origin_guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(origin_guard)
from stage_checks import Checks


def planned_asset(ident='V1', category='self_generated', kind='ai_generated'):
    return {'id': ident, 'kind': kind, 'origin': {
        'category': category, 'method': 'Planned original creation with local tools',
        'entry_version': 'synthetic-plan-v1', 'inputs': []}}


def planned_episode():
    return {'origin_contract': {'mode': 'self_created_visuals'},
            'shots': [{'id': 'SH1', 'asset_ids': ['V1'], 'shotbook': {
                'origin': {'planned_method': 'self_generated', 'entry_version': 'synthetic-plan-v1'},
                'realism': {'medium': 'ai_realistic'}}}],
            'assets': [planned_asset()]}


class OriginHardContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='origin-hard-synthetic-',
                                              dir=os.environ.get('SCIENCE_VIDEO_TEST_TMPDIR', str(HERE)))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = planned_episode()

    def plan_errors(self, data=None, final=False):
        checks = Checks(self.data if data is None else data, self.root)
        origin_guard.validate_origin_plan(checks, ['SH1'], final=final)
        return checks.errors

    def actual_errors(self, representative=False):
        checks = Checks(self.data, self.root)
        origin_guard.validate_origin(checks, ['SH1'], representative=representative)
        return checks.errors

    def assert_blocked(self, fragment, data=None, final=False):
        errors = self.plan_errors(data, final)
        self.assertTrue(any(fragment in error for error in errors), errors)

    def synthetic_ref(self):
        path = self.root / 'synthetic-software-fixture.txt'
        path.write_text('FABRICATED SOFTWARE TEST ONLY: no real creation, frame review or user authorization.',
                        encoding='utf-8')
        return {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def completed_structure(self):
        ref = self.synthetic_ref()
        origin = self.data['shots'][0]['shotbook']['origin']
        origin.update(design=dict(ref), entrypoint=dict(ref))
        asset = self.data['assets'][0]
        asset.update(ref)
        asset['disclosure'] = 'Synthetic generated software-test visual, not live footage.'
        asset['origin'].update(design=dict(ref), entrypoint=dict(ref),
                               output=dict(ref), frames=[dict(ref)], review=dict(ref))
        return ref

    def test_future_generation_plan_needs_no_fake_output_or_frames(self):
        asset = self.data['assets'][0]
        asset['file'] = 'future-generation.mp4'
        self.assertFalse((self.root / asset['file']).exists())
        self.assertNotIn('output', asset['origin'])
        self.assertNotIn('frames', asset['origin'])
        self.assertEqual(self.plan_errors(), [])

    def test_future_generation_is_not_completed_output(self):
        self.assertEqual(self.plan_errors(), [])
        errors = self.actual_errors()
        self.assertTrue(any('actual frame evidence required' in error for error in errors), errors)
        self.assertTrue(any('evidence file required' in error for error in errors), errors)

    def test_missing_disabled_or_changed_mode_never_bypasses_plan(self):
        for contract in (None, {}, {'enabled': False}, {'mode': 'third_party_filler'}, {'mode': ''}):
            with self.subTest(contract=contract):
                data = copy.deepcopy(self.data)
                if contract is None:
                    data.pop('origin_contract')
                else:
                    data['origin_contract'] = contract
                self.assert_blocked('explicit self_created_visuals contract required', data)

    def test_unknown_method_and_medium_mismatch_are_blocked(self):
        for method, medium in (('licensed_footage', 'authentic_recording'),
                               ('self_generated', 'three_d'), ('user_capture', 'ai_realistic'),
                               ('self_rendered', 'unknown_medium')):
            with self.subTest(method=method, medium=medium):
                data = copy.deepcopy(self.data)
                data['shots'][0]['shotbook']['origin']['planned_method'] = method
                data['shots'][0]['shotbook']['realism']['medium'] = medium
                self.assert_blocked('origin method conflicts', data)

    def test_supported_self_created_medium_plans(self):
        for medium, method in (('ai_realistic', 'self_generated'), ('three_d', 'self_rendered'),
                               ('pure_2d', 'self_rendered'), ('static_pan', 'self_rendered'),
                               ('infographic', 'self_rendered'), ('authentic_recording', 'user_capture')):
            with self.subTest(medium=medium):
                data = copy.deepcopy(self.data)
                data['shots'][0]['shotbook']['origin']['planned_method'] = method
                data['shots'][0]['shotbook']['realism']['medium'] = medium
                self.assertEqual(self.plan_errors(data), [])

    def test_paper_video_rights_crop_reorder_and_chinese_dub_do_not_make_original(self):
        asset = self.data['assets'][0]
        asset.update(kind='real_observation', source='https://example.invalid/paper/supplement.mp4',
                     rights={'status': 'approved', 'legal_rights': True, 'license': 'CC BY 4.0'},
                     processing=['crop', 'reorder', 'Chinese dubbing', 'AI redrawing'])
        asset['origin']['category'] = 'third_party_reference'
        self.assert_blocked('third-party/CC/reference media is not self-created')

    def test_generated_child_with_third_party_visual_ancestor_is_blocked(self):
        reference = planned_asset('PAPER', 'third_party_reference', 'real_observation')
        middle = planned_asset('INTERMEDIATE')
        middle['origin']['inputs'] = [{'asset_id': 'PAPER'}]
        self.data['assets'].extend([middle, reference])
        self.data['assets'][0]['origin']['inputs'] = [{'asset_id': 'INTERMEDIATE'}]
        self.assert_blocked('third-party or unclassified visual input cannot become original')

    def test_scientific_urls_and_unselected_research_reference_remain_allowed(self):
        self.data['sources'] = [{'id': 'SCI1', 'url': 'https://example.invalid/paper',
                                 'role': 'scientific_basis'}]
        self.data['assets'].append({'id': 'RESEARCH', 'kind': 'real_observation',
                                    'source': 'https://example.invalid/paper/supplement.mp4',
                                    'origin': {'category': 'third_party_reference'}})
        self.assertEqual(self.plan_errors(), [])

    def test_missing_selected_asset_is_blocked(self):
        self.data['shots'][0]['asset_ids'] = ['MISSING']
        self.assert_blocked('MISSING needs unique upstream asset_id')

    def test_missing_origin_or_explicit_input_inventory_is_blocked(self):
        for field in ('origin', 'inputs'):
            with self.subTest(field=field):
                data = copy.deepcopy(self.data)
                if field == 'origin':
                    data['assets'][0].pop('origin')
                else:
                    data['assets'][0]['origin'].pop('inputs')
                self.assertTrue(self.plan_errors(data))

    def test_missing_and_duplicate_upstream_ids_are_blocked(self):
        self.data['assets'][0]['origin']['inputs'] = [{'asset_id': 'PARENT'}]
        self.assert_blocked('unique upstream asset_id')
        self.data['assets'].extend([planned_asset('PARENT'), planned_asset('PARENT')])
        self.assert_blocked('unique upstream asset_id')

    def test_duplicate_selected_id_is_blocked(self):
        self.data['assets'].append(planned_asset())
        self.assert_blocked('V1 needs unique upstream asset_id')

    def test_invalid_input_id_and_cycles_are_blocked(self):
        for value in (None, '', {'id': 'V1'}):
            with self.subTest(value=value):
                data = copy.deepcopy(self.data)
                data['assets'][0]['origin']['inputs'] = [{'asset_id': value}]
                self.assert_blocked('visual input needs unique upstream asset_id', data)
        parent = planned_asset('PARENT')
        parent['origin']['inputs'] = [{'asset_id': 'V1'}]
        self.data['assets'].append(parent)
        self.data['assets'][0]['origin']['inputs'] = [{'asset_id': 'PARENT'}]
        self.assert_blocked('cyclic provenance')

    def test_contradictory_claimed_parent_provenance_is_blocked(self):
        self.data['assets'].append(planned_asset('PARENT'))
        self.data['assets'][0]['origin']['inputs'] = [
            {'asset_id': 'PARENT', 'origin_category': 'user_capture'}]
        self.assert_blocked('contradicts upstream asset provenance')

    def test_relabeling_known_third_party_bytes_is_blocked(self):
        self.data['assets'][0]['sha256'] = 'a' * 64
        research = planned_asset('RESEARCH', 'third_party_reference')
        research['sha256'] = 'a' * 64
        self.data['assets'].append(research)
        self.assert_blocked('bytes also declared third-party reference')

    def test_third_party_design_keyframe_dependency_is_blocked(self):
        self.data['design'] = {'keyframe_scales': {'mobile': {'asset_ids': ['KEYFRAME']}}}
        self.data['assets'].append(planned_asset('KEYFRAME', 'third_party_reference'))
        self.assert_blocked('third-party/CC/reference media is not self-created')
        selected = {asset['id'] for asset in origin_guard.selected_assets(self.data, ['SH1'], representative=True)}
        self.assertEqual(selected, {'V1', 'KEYFRAME'})
        self.assertTrue(any('KEYFRAME' in error and 'not self-created' in error
                            for error in self.actual_errors(representative=True)))

    def test_final_plan_includes_deliverable_visual_ancestors(self):
        self.data['deliverable_asset_ids'] = {'video': ['OUTPUT']}
        output = planned_asset('OUTPUT', 'self_rendered', 'simulation')
        output['origin']['inputs'] = [{'asset_id': 'PAPER'}]
        self.data['assets'].extend([output, planned_asset('PAPER', 'third_party_reference')])
        self.assert_blocked('third-party or unclassified visual input', final=True)

    def test_final_scope_excludes_unused_representative_keyframes(self):
        self.data['design'] = {'keyframe_scales': {'mobile': {'asset_ids': ['UNUSED_REFERENCE']}}}
        self.data['assets'].append(planned_asset('UNUSED_REFERENCE', 'third_party_reference'))
        self.assert_blocked('third-party/CC/reference media is not self-created')
        self.assertEqual(self.plan_errors(final=True), [])
        selected = {asset['id'] for asset in origin_guard.selected_assets(self.data, ['SH1'], final=True)}
        self.assertEqual(selected, {'V1'})

    def test_audio_and_font_selection_is_not_a_footage_ban(self):
        self.data['assets'].extend([{'id': 'VOICE', 'kind': 'audio'}, {'id': 'FONT', 'kind': 'font'}])
        self.data['narration'] = {'asset_id': 'VOICE'}
        self.data['design'] = {'font_asset_id': 'FONT'}
        self.assertEqual(self.plan_errors(), [])

    def test_actual_output_binding_and_evidence_hash_are_still_required(self):
        self.completed_structure()
        self.assertEqual(self.actual_errors(), [])
        self.data['assets'][0]['origin']['output']['sha256'] = 'f' * 64
        errors = self.actual_errors()
        self.assertTrue(any('bind exact used asset bytes' in error for error in errors), errors)
        self.assertTrue(any('evidence hash stale' in error for error in errors), errors)

    def test_actual_user_capture_requires_authorization_file_and_matching_hash(self):
        ref = self.completed_structure()
        self.data['shots'][0]['shotbook']['origin']['planned_method'] = 'user_capture'
        self.data['shots'][0]['shotbook']['realism']['medium'] = 'authentic_recording'
        self.data['assets'][0]['kind'] = 'real_capture'
        capture_origin = self.data['assets'][0]['origin']
        capture_origin['category'] = 'user_capture'
        self.assertEqual(self.plan_errors(), [])
        for authorization in (None, True, {'file': 'absent.txt', 'sha256': ref['sha256']},
                              {'file': ref['file'], 'sha256': 'f' * 64}):
            with self.subTest(authorization=authorization):
                capture_origin['user_authorization'] = authorization
                errors = self.actual_errors()
                self.assertTrue(any('capture authorization' in error for error in errors), errors)


if __name__ == '__main__':
    unittest.main()
