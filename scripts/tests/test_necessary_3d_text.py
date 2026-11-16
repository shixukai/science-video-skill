"""Offline synthetic regressions; no rendered-media or perceptual pass asserted."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

LOCAL_SCRIPTS = Path(__file__).resolve().parents[1]
GLOBAL = (LOCAL_SCRIPTS.parent if (LOCAL_SCRIPTS / 'stage_checks.py').is_file()
          else Path(os.environ['SCIENCE_SKILL_TEST_BASE']))
sys.path.insert(0, str(GLOBAL / 'scripts'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import label_permission_guard as guard
from presentation_checks import validate_text_plan, validate_text_review, prohibited_cue
from stage_checks import Checks, context_sha256, digest


class NecessaryTextTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.item = {'id': 'T1', 'surface': 'frame', 'text': '出口压力 2 MPa',
                     'purposes': ['mechanism'], 'necessity': 'Identify the pressure at the observed outlet',
                     'removal_loss': 'The audience cannot attach the compared quantity to the outlet'}
        self.data = {'presentation_text': {'channels': {s: {'status': 'present' if s == 'frame' else 'absent',
                    'note': 'Synthetic explicit inventory'} for s in guard.VISUAL_SURFACES | {'voiceover'}},
                    'items': [self.item], 'required_notices': []}, 'delivery_scope': 'video_only'}
        self.view = {'sha256': 'a' * 64, 'duration': 1}
        self.review_extra = {}
        source = self.write('synthetic-renderer.py', 'pass\n')
        self.manifest = {'schema_version': 1, 'status': 'pass', 'stage': 'G2',
            'media_sha256': self.view['sha256'], 'inventory_sha256': '', 'time_range': [0, 1],
            'method': 'actual_output_and_sources', 'actual_output_inspected': True,
            'reviewer': 'synthetic reviewer', 'observation': 'Synthetic declared inspection only',
            'zones': sorted(guard.ZONES), 'unknown_overlays': [],
            'sources': [{'id': 'SRC', 'kind': 'renderer', **source}], 'observed': []}

    def write(self, name, content):
        path = self.root / name
        path.write_text(content, encoding='utf-8')
        return {'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

    def plan(self):
        checks = Checks(self.data, self.root)
        validate_text_plan(checks)
        return checks.errors

    def blocked(self, errors, fragment):
        self.assertTrue(any(fragment in e for e in errors), errors)

    def science_review(self, interpretation='scientific_condition'):
        self.data['claims'] = [{'id': 'C1'}]
        self.item['cue_review'] = {'status': 'pass', 'interpretation': interpretation,
            'reviewer': 'synthetic semantic reviewer', 'scientific_basis': 'Synthetic source-bound scientific basis',
            'audience_task': 'Avoid a mistaken geometric inference', 'note': 'Necessary scientific meaning, not renderer commentary',
            'claim_ids': ['C1'], 'text_sha256': hashlib.sha256(self.item['text'].encode()).hexdigest(),
            'evidence': self.write('semantic-review.txt', 'Synthetic semantic review fixture only')}
        if interpretation == 'scientific_condition':
            self.item.update(purposes=['scientific_condition'], notice_id='N1')
            self.data['presentation_text']['required_notices'] = [{'id': 'N1',
                'purpose': 'scientific_condition', 'text': self.item['text'],
                'basis': self.item['cue_review']['scientific_basis'], 'placement': 'audience',
                'placement_basis': 'Synthetic actual comparison needs this scale condition'}]

    def three_d(self):
        self.data['shots'] = [{'id': 'SH1', 'modality': 'controlled_3d', 'asset_ids': []}]
        self.item.update(kind='auxiliary_text', shot_ids=['SH1'], representation='spatial_3d', text='A')

    def surface(self, name):
        self.item['surface'] = name
        for key, channel in self.data['presentation_text']['channels'].items():
            channel['status'] = 'present' if key == name else 'absent'

    def observe(self):
        row = {'item_id': 'T1', 'source_ids': ['SRC'], 'text': self.item['text'],
               'surface': self.item['surface'], 'position': 'beside outlet', 'time_range': [0, 1]}
        for key in ('kind', 'shot_ids', 'representation', 'source_asset_id', 'caption_role'):
            if key in self.item:
                row[key] = copy.deepcopy(self.item[key])
        if guard.spatial_auxiliary(self.item, self.data):
            row['spatial_review'] = {'status': 'pass',
                'observation': 'Synthetic assertion: depth/perspective fit the outlet, composed tastefully, readable at intended size'}
        self.manifest['observed'] = [row]
        return row

    def overlay_ref(self):
        self.manifest['inventory_sha256'] = digest(self.data['presentation_text'])
        return self.write('overlay.json', json.dumps(self.manifest, ensure_ascii=False))

    def overlay(self):
        checks = Checks(self.data, self.root)
        review = {'overlay_evidence': self.overlay_ref(), **self.review_extra}
        guard.validate_overlay_review(checks, 'G2', self.view,
            review, {'T1': self.item}, {'T1'})
        return checks.errors

    def ordinary_caption(self, role='spoken_sync'):
        if self.item['text'] == 'A':
            self.item['text'] = '出口压力升至 2 MPa'
        self.item.update(surface='caption', caption_role=role, representation='screen_2d')
        self.item.pop('kind', None)
        for key, value in self.data['presentation_text']['channels'].items():
            value['status'] = 'present' if key == 'caption' else 'absent'
        formal = self.write('captions.srt', '1\n00:00:00,000 --> 00:00:01,000\n' + self.item['text'] + '\n')
        narration = self.write('narration.txt', '出口的压力升高到了两兆帕。')
        self.manifest['sources'].append({'id': 'CAP', 'kind': 'caption', **formal})
        self.review_extra = {'sources': {'caption': formal, 'voiceover': narration},
            'channel_reviews': {'caption': {'caption_correspondence': {'status': 'pass', 'item_ids': ['T1'],
                'observation': 'Synthetic observation: condensed captions follow actual spoken meaning or necessary audible sound; no detached auxiliary annotation'}}}}
        row = self.observe()
        row['source_ids'] = ['CAP']
        return row

    def test_generic_view_meta_default_fails_under_all_allowed_scientific_labels(self):
        self.three_d()
        for purpose in ('topic', 'mechanism', 'accessibility', 'scientific_condition'):
            self.item.update(text='观察角度说明·非比例', purposes=[purpose])
            self.blocked(self.plan(), 'production/material-defect cue')

    def test_bounded_scene_description_cues_fail_anywhere_in_frame(self):
        self.three_d()
        for text in ('局部布局示意', '一般机构结构说明', '场景说明', '模型示意', '本画面仅供示意',
                     '观 察 角 度 说 明·非比例', '观\u200b察角度说明·非比例'):
            for position in ('top left', 'center', 'bottom right', 'in scene'):
                self.item.update(text=text, position=position)
                self.blocked(self.plan(), 'production/material-defect cue')

    def test_decorating_or_physical_reclassification_does_not_rescue_meta_prose(self):
        self.three_d()
        self.item.update(text='观察角度说明·非比例')
        self.blocked(self.plan(), 'production/material-defect cue')
        self.item.update(kind='physical_lettering')
        self.blocked(self.plan(), 'production/material-defect cue')

    def test_body_caption_or_voiceover_classification_cannot_rescue_meta_prose(self):
        self.three_d()
        for surface in ('caption', 'voiceover'):
            self.item.update(surface=surface, text='一般机构结构说明')
            for key, value in self.data['presentation_text']['channels'].items():
                value['status'] = 'present' if key == surface else 'absent'
            self.blocked(self.plan(), 'production/material-defect cue')

    def test_not_a_blanket_demonstration_or_scientific_condition_ban(self):
        for text, purpose in [('结构示意', 'mechanism'), ('机制示意', 'mechanism'),
                              ('折射光线示意', 'mechanism'), ('时间放慢10倍', 'scientific_condition'),
                              ('不按实际比例绘制', 'scientific_condition'), ('在相同温度下比较', 'scientific_condition'),
                              ('出口压力 2 MPa', 'mechanism'), ('纸币水印的明暗来自纸张厚度差', 'mechanism')]:
            self.item.update(text=text, purposes=[purpose])
            self.assertEqual(self.plan(), [], text)

    def test_current_scientific_review_cannot_waive_single_letter_restriction(self):
        self.three_d()
        self.item['text'] = '观察角度说明·非比例'
        self.science_review()
        self.blocked(self.plan(), 'only single-letter markers')
        self.observe()
        self.blocked(self.overlay(), 'only single-letter markers')
        self.assertNotIn('user_approval', self.item)

    def test_scale_exception_rejects_changed_text_claim_basis_or_stale_evidence(self):
        self.three_d()
        self.item['text'] = '观察角度说明·非比例'
        self.science_review()
        self.surface('voiceover')
        self.assertEqual(self.plan(), [])
        original = copy.deepcopy(self.data)
        cases = [('text', '局部布局示意', 'production/material-defect cue'),
                 ('claim_ids', ['missing'], 'actual claim IDs'),
                 ('scientific_basis', 'Different basis', 'production/material-defect cue'),
                 ('sha256', '0' * 64, 'hash stale'),
                 ('status', 'fail', 'production/material-defect cue')]
        for key, value, error in cases:
            self.data = copy.deepcopy(original)
            self.item = self.data['presentation_text']['items'][0]
            if key == 'text': self.item[key] = value
            elif key == 'sha256': self.item['cue_review']['evidence'][key] = value
            else: self.item['cue_review'][key] = value
            self.blocked(self.plan(), error)

    def test_model_limits_preserve_science_with_current_traceable_review(self):
        self.three_d()
        self.item['text'] = '气体模型受限于低压条件'
        self.science_review()
        self.surface('voiceover')
        self.assertEqual(self.plan(), [])
        self.item['cue_review'].pop('text_sha256')
        self.blocked(self.plan(), 'production/material-defect cue')

    def test_scientific_subject_keeps_semantic_path_in_genuine_synchronized_captions(self):
        self.three_d()
        for text in ('AI模拟大气环流用于预测天气', '神经网络模型示意'):
            self.item['text'] = text
            self.science_review('scientific_subject')
            self.manifest['sources'] = [s for s in self.manifest['sources'] if s['id'] != 'CAP']
            self.ordinary_caption()
            self.assertEqual(self.plan(), [])
            self.assertEqual(self.overlay(), [])

    def test_scoped_three_d_auxiliary_accepts_only_spatial_representation(self):
        self.three_d()
        self.assertEqual(self.plan(), [])
        for value in (None, '', 'unknown', 'screen_2d', 'billboard_2d', {}, ['spatial_3d']):
            self.item['representation'] = value
            self.blocked(self.plan(), 'requires spatial_3d')

    def test_missing_or_unknown_shot_binding_cannot_silently_opt_out(self):
        self.three_d()
        for value in (None, [], ['missing'], ['SH1', 'SH1'], [[]]):
            self.item['shot_ids'] = value
            self.blocked(self.plan(), 'actual shot_ids required')

    def test_arbitrary_kind_cannot_rename_frame_auxiliary_as_caption(self):
        self.three_d()
        self.item.update(kind='caption', representation='screen_2d')
        self.blocked(self.plan(), 'kind must identify')
        self.blocked(self.plan(), 'requires spatial_3d')

    def test_realism_medium_also_scopes_3d_without_modality(self):
        self.three_d()
        self.data['shots'][0] = {'id': 'SH1', 'shotbook': {'realism': {'medium': 'three_d'}}}
        self.item['representation'] = 'screen_2d'
        self.blocked(self.plan(), 'requires spatial_3d')

    def test_ordinary_caption_cover_voiceover_remain_outside_spatial_scope(self):
        self.three_d()
        for surface in ('caption', 'cover', 'voiceover'):
            self.item.update(surface=surface, representation='screen_2d')
            if surface == 'caption':
                self.item['caption_role'] = 'spoken_sync'
                self.item.pop('kind', None)
            for key, value in self.data['presentation_text']['channels'].items():
                value['status'] = 'present' if key == surface else 'absent'
            self.assertEqual(self.plan(), [], surface)

    def test_mixed_realistic_shot_binding_is_exempt_without_exempting_three_d(self):
        self.three_d()
        self.data['shots'].append({'id': 'SH2', 'modality': 'ai_generated'})
        self.item.update(shot_ids=['SH2'], representation='screen_2d')
        self.assertEqual(self.plan(), [])
        self.item['shot_ids'] = ['SH1', 'SH2']
        self.blocked(self.plan(), 'requires spatial_3d')

    def test_other_routes_and_legacy_inventory_without_three_d_stay_exempt(self):
        self.item['representation'] = 'screen_2d'
        for modality in ('real_footage', 'ai_generated', 'pure_2d'):
            self.data['shots'] = [{'id': 'SH1', 'modality': modality}]
            self.assertEqual(self.plan(), [])

    def test_new_view_meta_combinations_do_not_change_realistic_or_two_d_routes(self):
        self.item.update(text='观察角度说明·非比例', representation='screen_2d', shot_ids=['SH1'])
        for modality in ('real_footage', 'ai_generated', 'pure_2d'):
            self.data['shots'] = [{'id': 'SH1', 'modality': modality}]
            self.assertEqual(self.plan(), [], modality)
            self.observe()
            self.assertEqual(self.overlay(), [], modality)
        self.data.pop('shots')
        self.item.pop('shot_ids')
        self.assertEqual(self.plan(), [])

    def test_new_body_meta_combinations_do_not_change_independent_cover(self):
        self.three_d()
        self.item.update(surface='cover', text='一般机构结构说明', representation='screen_2d')
        for key, value in self.data['presentation_text']['channels'].items():
            value['status'] = 'present' if key == 'cover' else 'absent'
        self.assertEqual(self.plan(), [])

    def test_mixed_explicit_non_three_d_bindings_narrow_new_body_and_caption_rules(self):
        self.three_d()
        self.data['shots'].append({'id': 'SH2', 'modality': 'ai_generated'})
        self.item.update(shot_ids=['SH2'], representation='screen_2d', text='一般机构结构说明')
        self.item.pop('kind')
        for surface in ('frame', 'caption', 'voiceover'):
            self.item['surface'] = surface
            for key, value in self.data['presentation_text']['channels'].items():
                value['status'] = 'present' if key == surface else 'absent'
            self.assertEqual(self.plan(), [], surface)
            if surface != 'voiceover':
                self.observe()
                self.assertEqual(self.overlay(), [], surface)
        self.item.update(surface='frame', shot_ids=['SH1'])
        self.blocked(self.plan(), 'production/material-defect cue')

    def test_mixed_unbound_or_invalid_binding_does_not_opt_out_of_new_cue_scope(self):
        self.three_d()
        self.data['shots'].append({'id': 'SH2', 'modality': 'ai_generated'})
        self.item['text'] = '局部布局示意'
        for ids in (None, [], ['missing'], [[]]):
            self.item['shot_ids'] = ids
            self.blocked(self.plan(), 'production/material-defect cue')

    def test_preexisting_generic_qa_and_production_excuse_rules_keep_all_route_scope(self):
        self.item.update(text='本片测试通过', purposes=['mechanism'])
        for modality in ('real_footage', 'ai_generated', 'pure_2d', 'controlled_3d'):
            self.data['shots'] = [{'id': 'SH1', 'modality': modality}]
            self.blocked(self.plan(), 'production/material-defect cue')

    def test_legacy_scientific_model_exception_outside_three_d_is_unchanged(self):
        self.item['text'] = '气体模型受限于低压条件'
        self.science_review()
        for key in ('reviewer', 'claim_ids', 'text_sha256', 'evidence'):
            self.item['cue_review'].pop(key)
        self.data.pop('claims')
        for modality in ('real_footage', 'ai_generated', 'pure_2d'):
            self.data['shots'] = [{'id': 'SH1', 'modality': modality}]
            self.assertEqual(self.plan(), [], modality)
        self.three_d()
        self.item['text'] = '气体模型受限于低压条件'
        self.blocked(self.plan(), 'production/material-defect cue')

    def test_physical_lettering_source_strengthening_does_not_touch_non_three_d(self):
        self.item.update(kind='physical_lettering', representation='physical_surface', shot_ids=['SH1'])
        self.data['shots'] = [{'id': 'SH1', 'modality': 'real_footage'}]
        self.assertEqual(self.plan(), [])
        self.observe()
        self.assertEqual(self.overlay(), [])

    def test_non_three_d_actual_scientific_subject_cue_keeps_preexisting_guard_behavior(self):
        self.item['text'] = 'AI模拟大气环流用于预测天气'
        self.science_review('scientific_subject')
        for modality in ('real_footage', 'ai_generated', 'pure_2d'):
            self.data['shots'] = [{'id': 'SH1', 'modality': modality}]
            self.assertEqual(self.plan(), [])
            self.observe()
            # Preserve the pre-existing conservative actual-overlay result;
            # this 3D-only change does not also repair another route's guard.
            self.blocked(self.overlay(), 'visible marking misclassified')

    def test_actual_clear_2d_caption_stays_exempt_in_three_d_video(self):
        self.three_d()
        self.item['text'] = '出口压力升至 2 MPa'
        row = self.ordinary_caption()
        self.assertNotIn('spatial_review', row)
        self.assertEqual(self.overlay(), [])

    def test_full_current_source_review_allows_condensation_and_unit_spelling(self):
        self.three_d()
        self.item['text'] = '出口压力升至 2 MPa'
        self.ordinary_caption()
        spoken = {'id': 'V1', 'surface': 'voiceover', 'text': '出口的压力升高到了两兆帕。',
                  'purposes': ['mechanism'], 'necessity': 'Explain the observed pressure rise',
                  'removal_loss': 'The audience loses the causal statement'}
        self.data['presentation_text']['items'].append(spoken)
        self.data['presentation_text']['channels']['voiceover']['status'] = 'present'
        r = {'status': 'pass', 'media_sha256': self.view['sha256'],
             'inventory_sha256': digest(self.data['presentation_text']), 'actual_media_inspected': True,
             'evidence': 'Synthetic actual inspection fixture only', 'overlay_evidence': self.overlay_ref(),
             'channel_reviews': {s: {'status': 'pass', 'item_ids': ['T1'] if s == 'caption' else ['V1'] if s == 'voiceover' else [],
                 'observation': 'Synthetic current purpose/deletion and speech correspondence observation',
                 'evidence': 'Synthetic bounded observation'} for s in ('frame', 'caption', 'voiceover')},
             'sources': self.review_extra['sources'],
             'protected_notices_review': 'Synthetic preservation review', 'companion_notices': []}
        r['channel_reviews']['caption'].update(self.review_extra['channel_reviews']['caption'])
        self.data['qa'] = {'presentation_text': {'G2': r}}
        r['context_sha256'] = context_sha256(self.data, 'G2')
        self.assertEqual(self.plan(), [])
        checks = Checks(self.data, self.root)
        validate_text_review(checks, 'G2', self.view, {'T1': self.item, 'V1': spoken})
        self.assertEqual(checks.errors, [])
        r['sources']['voiceover']['sha256'] = '0' * 64
        checks = Checks(self.data, self.root)
        validate_text_review(checks, 'G2', self.view, {'T1': self.item, 'V1': spoken})
        self.blocked(checks.errors, 'voiceover evidence hash stale')

    def test_sound_accessibility_caption_stays_2d_with_actual_audible_correspondence(self):
        self.three_d()
        self.item.update(text='[阀门关闭声]', purposes=['accessibility'])
        self.ordinary_caption('sound_accessibility')
        self.assertEqual(self.plan(), [])
        self.assertEqual(self.overlay(), [])

    def test_reclassifying_detached_auxiliary_as_caption_is_not_enough(self):
        self.three_d()
        self.item.update(surface='caption', representation='screen_2d')
        self.observe()
        self.blocked(self.plan(), 'ordinary synchronized role required')
        self.blocked(self.overlay(), 'correspondence review')
        for role in ('auxiliary_text', None, 'unknown', {}, ['spoken_sync']):
            self.item['caption_role'] = role
            self.blocked(self.plan(), 'ordinary synchronized role required')
        self.item['caption_role'] = 'spoken_sync'
        self.blocked(self.overlay(), 'ordinary caption source must bind')

    def test_caption_correspondence_failure_missing_coverage_or_detachment_blocks(self):
        self.three_d()
        self.ordinary_caption()
        correspondence = self.review_extra['channel_reviews']['caption']['caption_correspondence']
        for field, value in (('status', 'fail'), ('status', 'unknown'), ('item_ids', []),
                             ('item_ids', ['missing']), ('item_ids', [[]]), ('observation', '')):
            old = copy.deepcopy(correspondence)
            correspondence[field] = value
            self.blocked(self.overlay(), 'correspondence review')
            correspondence.clear(); correspondence.update(old)

    def test_ordinary_caption_requires_exact_current_formal_source_not_arbitrary_renderer(self):
        self.three_d()
        row = self.ordinary_caption()
        row['source_ids'] = ['SRC']
        self.blocked(self.overlay(), 'ordinary caption source must bind')
        row['source_ids'] = ['CAP']
        self.review_extra['sources']['caption']['sha256'] = '0' * 64
        self.blocked(self.overlay(), 'ordinary caption source must bind')

    def test_actual_caption_role_cannot_disagree_with_reviewed_inventory(self):
        self.three_d()
        row = self.ordinary_caption()
        row['caption_role'] = 'auxiliary_text'
        self.blocked(self.overlay(), 'caption role must match')

    def test_actual_spatial_review_and_representation_must_match(self):
        self.three_d()
        row = self.observe()
        self.assertEqual(self.overlay(), [])
        for value in (None, 'unknown', 'screen_2d'):
            row['representation'] = value
            self.blocked(self.overlay(), 'spatial representation missing/mismatched')
        row['representation'] = 'spatial_3d'
        for value in ({}, {'status': 'fail', 'observation': 'Flat overlay detached from target'},
                      {'status': 'unknown', 'observation': 'Unverified'}, {'status': 'pass', 'observation': ''}):
            row['spatial_review'] = value
            self.blocked(self.overlay(), 'return for repair')

    def test_actual_frame_binding_cannot_switch_shots_or_kind(self):
        self.three_d()
        row = self.observe()
        row['shot_ids'] = ['SH2']
        self.blocked(self.overlay(), 'shot/kind binding differs')
        row['shot_ids'] = ['SH1']
        row['kind'] = 'physical_lettering'
        self.blocked(self.overlay(), 'shot/kind binding differs')

    def test_physical_lettering_requires_bound_actual_asset_and_observation(self):
        self.three_d()
        self.item.update(kind='physical_lettering', representation='physical_surface', source_asset_id='A1')
        self.blocked(self.plan(), 'actual object/source asset')
        asset = {'id': 'A1', **self.write('functional-object.blend', 'Synthetic functional object source')}
        self.data['assets'] = [asset]
        self.data['shots'][0]['asset_ids'] = ['A1']
        self.assertEqual(self.plan(), [])
        row = self.observe()
        row['observation'] = 'Synthetic observation: original single-letter marker A belongs to the actual instrument face'
        self.blocked(self.overlay(), 'same object/asset file')
        self.manifest['sources'].append({'id': 'OBJ', 'kind': 'renderer', 'asset_id': 'A1',
                                        'file': asset['file'], 'sha256': asset['sha256']})
        row['source_ids'].append('OBJ')
        self.assertEqual(self.overlay(), [])
        row['observation'] = ''
        self.blocked(self.overlay(), 'physical lettering and object binding')

    def test_failed_actual_output_review_blocks_even_when_declaration_says_spatial(self):
        self.three_d()
        self.observe()
        self.manifest['status'] = 'fail'
        self.blocked(self.overlay(), 'unreviewed/failed evidence')

    def test_existing_channel_and_overall_actual_review_failure_still_blocks(self):
        self.three_d()
        self.observe()
        r = {'status': 'pass', 'media_sha256': self.view['sha256'],
             'inventory_sha256': digest(self.data['presentation_text']), 'actual_media_inspected': True,
             'evidence': 'Synthetic actual inspection fixture only', 'overlay_evidence': self.overlay_ref(),
             'channel_reviews': {s: {'status': 'pass', 'item_ids': ['T1'] if s == 'frame' else [],
                 'observation': 'Synthetic purpose and deletion review', 'evidence': 'Synthetic bounded observation'}
                 for s in ('frame', 'caption', 'voiceover')},
             'sources': {s: self.write(s + '.txt', '') for s in ('caption', 'voiceover')},
             'protected_notices_review': 'Synthetic preservation review', 'companion_notices': []}
        self.data['qa'] = {'presentation_text': {'G2': r}}
        r['context_sha256'] = context_sha256(self.data, 'G2')
        checks = Checks(self.data, self.root)
        validate_text_review(checks, 'G2', self.view, {'T1': self.item})
        self.assertEqual(checks.errors, [])
        r['channel_reviews']['frame']['status'] = 'fail'
        checks = Checks(self.data, self.root)
        validate_text_review(checks, 'G2', self.view, {'T1': self.item})
        self.blocked(checks.errors, 'actual purpose/deletion review required')
        r['status'] = 'fail'
        checks = Checks(self.data, self.root)
        validate_text_review(checks, 'G2', self.view, {'T1': self.item})
        self.blocked(checks.errors, 'actual review failed/unreviewed')


    def test_3d_picture_rejects_all_explanatory_content_even_when_spatial(self):
        self.three_d()
        for wording in ('阀门流向说明', '出口压力', '局部排列', 'Pressure', 'EUV', '2 MPa',
                        '100', 'A1', 'A B', 'AB', 'A\nB', 'A=2', '字', '2', '→', 'A\u200b'):
            self.item['text'] = wording
            self.blocked(self.plan(), 'only single-letter markers')
            self.observe()
            self.blocked(self.overlay(), 'only single-letter markers')

    def test_single_latin_or_greek_markers_keep_spatial_binding_and_actual_review(self):
        self.three_d()
        for letter in ('A', 'B', 'z', 'α', 'Δ'):
            self.item['text'] = letter
            self.assertEqual(self.plan(), [], letter)
            self.observe()
            self.assertEqual(self.overlay(), [], letter)

    def test_physical_or_consented_marking_classification_cannot_waive_letters_only(self):
        self.three_d()
        for kind in ('auxiliary_text', 'physical_lettering', 'marking'):
            self.item.update(kind=kind, text='Pressure')
            self.item['user_approval'] = {'scope': guard.scope(self.item), 'user_quote': 'Synthetic obsolete approval'}
            self.blocked(self.plan(), 'only single-letter markers')
            self.observe()
            self.blocked(self.overlay(), 'only single-letter markers')

    def test_actual_words_fail_even_when_inventory_declares_a_letter(self):
        self.three_d()
        self.observe()['text'] = 'Pressure'
        self.blocked(self.overlay(), 'only single-letter markers')
        self.blocked(self.overlay(), 'differs from classified content')

    def test_marking_caption_needs_real_synchronized_role_and_correspondence_too(self):
        self.three_d()
        self.surface('caption')
        self.item.update(kind='marking', text='Pressure')
        self.observe()
        self.blocked(self.plan(), 'ordinary synchronized role required')
        self.blocked(self.overlay(), 'correspondence review')

    def test_preflight_content_check_is_bound_to_selected_three_d_shots(self):
        self.three_d()
        self.data['shots'].extend([{'id': 'SH2', 'modality': 'ai_generated'},
                                   {'id': 'SH3', 'modality': 'controlled_3d'}])
        self.item.update(text='Pressure', shot_ids=['SH1'])
        for selected, blocked in ((['SH1'], True), (['SH2'], False), (['SH3'], False),
                                  (['SH1', 'SH2'], True)):
            checks = Checks(self.data, self.root)
            guard.validate_three_d_frame_text(checks, self.item, selected)
            self.assertEqual(bool(checks.errors), blocked, selected)
        self.item['shot_ids'] = ['missing']
        checks = Checks(self.data, self.root)
        guard.validate_three_d_frame_text(checks, self.item, ['SH1'])
        self.blocked(checks.errors, 'only single-letter markers')

    def test_render_preflight_rejects_declared_3d_explanation_before_execution(self):
        import render_gate
        self.three_d()
        self.item['text'] = 'Pressure'
        for phase in ('roughcut', 'sample', 'full'):
            errors = render_gate.preflight(self.data, self.root, phase, ['SH1'])
            self.blocked(errors, 'only single-letter markers')

    def test_mixed_frame_binding_cannot_register_actual_3d_words_as_non_3d(self):
        self.three_d()
        self.data['shots'].append({'id': 'REAL', 'modality': 'real_footage'})
        self.item.update(shot_ids=['REAL'], text='OUTLET', representation='screen_2d')
        self.assertEqual(self.plan(), [])
        row = self.observe()
        self.assertEqual(self.overlay(), [])
        row['shot_ids'] = ['SH1']
        self.blocked(self.overlay(), 'only single-letter markers')
        self.blocked(self.overlay(), 'shot/kind binding differs')

    def test_mixed_caption_cannot_switch_actual_shot_to_bypass_synchronized_role(self):
        self.three_d()
        self.data['shots'].append({'id': 'REAL', 'modality': 'real_footage'})
        self.surface('caption')
        self.item.update(shot_ids=['REAL'], text='OUTLET', representation='screen_2d')
        self.assertEqual(self.plan(), [])
        row = self.observe()
        self.assertEqual(self.overlay(), [])
        row['shot_ids'] = ['SH1']
        self.blocked(self.overlay(), 'shot/kind binding differs')
        self.blocked(self.overlay(), 'caption role must match')

    def test_prior_consent_does_not_exempt_single_letter_from_spatial_checks(self):
        self.three_d()
        self.item.update(kind='marking', representation='screen_2d', position='beside outlet', time_range=[0, 1])
        quote = 'Synthetic historical consent fixture for letter A; not actual user consent.'
        self.item['user_approval'] = {'scope': guard.scope(self.item), 'user_message_ref': 'synthetic-consent-only',
            'user_quote': quote, 'evidence': self.write('synthetic-consent.txt', quote)}
        self.blocked(self.plan(), 'requires spatial_3d')
        row = self.observe()
        self.blocked(self.overlay(), 'spatial representation missing/mismatched')
        self.item['representation'] = 'spatial_3d'
        row['representation'] = 'spatial_3d'
        self.assertEqual(self.plan(), [])
        row.pop('spatial_review')
        self.blocked(self.overlay(), 'return for repair')
        self.observe()
        self.assertEqual(self.overlay(), [])


if __name__ == '__main__':
    unittest.main()
