"""Synthetic opening evidence tests; no regex-based semantics or real review claim."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opening_alignment_guard import check_opening_plan, validate_opening_review, opening_context_sha256
_fixture_spec = importlib.util.spec_from_file_location('bundled_opening_fixture', Path(__file__).with_name('opening_fixture.py'))
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
attach_opening_fixture = _fixture_module.attach_opening_fixture
from stage_checks import Checks, check_stage, file_digest


class OpeningAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data = {"scope": {"kind": "episode"}, "topic": {"current": {"question": "白天天空为什么蓝？"}},
                     "topic_alignment": {"opening": {"title": "天空的蓝色", "voiceover": "晴天抬头看到的那片蓝色，从哪里来？先看阳光如何被空气散射。",
                     "spoken_question": "晴天抬头看到的那片蓝色，从哪里来？", "answer_route": "先看阳光如何被空气散射。",
                     "cover_question": "白天天空为什么蓝？", "question_relation": "specific_equivalent",
                     "question_comparison": "同问白天天空蓝色的来源；口播是自然改述，未换成泛泛天空变化。",
                     "visual_handoff": "从封面天空进入同一观察对象，再有动机地转入散射示意。"}},
                     "shots": [{"id": "S1"}], "deliverables": {"video": "video.bin", "cover_3_4": "portrait.bin", "cover_4_3": "landscape.bin"},
                     "qa": {"reviewed_sha256": {}, "topic_alignment": {"opening_voiceover": {
                         "heard_question": "晴天抬头看到的那片蓝色，从哪里来？", "heard_answer_route": "先看阳光如何被空气散射。"}}}}
        for key, name in self.data["deliverables"].items():
            (self.root / name).write_bytes(("synthetic bytes, not actual media: " + key).encode())
            self.data["qa"]["reviewed_sha256"][key] = file_digest(self.root / name)
        self.review = attach_opening_fixture(self.data, self.root, duration=12)
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        path = self.root / "review.json"
        path.write_text(json.dumps(self.review, ensure_ascii=False))
        self.data["qa"]["topic_alignment"]["opening_alignment"] = {"status": "pass", "evidence": {"file": path.name, "sha256": file_digest(path)}}

    def errors(self, real_probe=False):
        checks = Checks(self.data, self.root)
        if not real_probe:
            checks.duration = lambda *args, **kwargs: 12.0
        validate_opening_review(checks)
        return checks.errors

    def rejects(self, text):
        self.assertTrue(any(text in e for e in self.errors()), self.errors())

    def test_natural_equivalent_question_and_motivated_transition(self):
        self.assertNotEqual(self.data['topic_alignment']['opening']['spoken_question'], self.data['topic']['current']['question'])
        self.assertEqual(check_opening_plan(self.data), [])
        self.assertEqual(self.errors(), [])

    def test_continuous_subject_is_also_valid(self):
        self.review['visual_handoff']['mode'] = 'continuous_subject'; self.save()
        self.assertEqual(self.errors(), [])

    def test_plan_needs_no_final_media(self):
        self.data.pop('deliverables'); self.data.pop('qa')
        self.assertEqual(check_opening_plan(self.data), [])

    def interest_plan(self):
        data = copy.deepcopy(self.data)
        data['shots'] = [{'id': 'S1'}, {'id': 'S2'}, {'id': 'S3'}]
        data['topic_alignment']['coverage'] = [
            dict(scope_id='R1', shot_ids=['S1', 'S2']),
            dict(scope_id='R2', shot_ids=['S3'])]
        data['topic_alignment']['opening'].update(
            curiosity_gap='太阳光看起来近白，晴朗天空却蓝；具体观察差异，不预设人人误解。',
            viewer_payoff='说明散射光如何从天空方向进入眼睛。',
            payoff_steps=[dict(scope_id='R1', shot_ids=['S2'], contribution='定位光、空气与眼睛，展示散射的关系。'),
                          dict(scope_id='R2', shot_ids=['S3'], contribution='回到真实观察回答原题及晴朗白天的条件。')])
        return data

    def test_interest_plan_accepts_observation_question_without_media_or_timing_formula(self):
        data = self.interest_plan()
        data.pop('deliverables'); data.pop('qa')
        self.assertEqual(check_opening_plan(data), [])

    def test_accurate_conclusion_can_be_topic_entry_without_question_mark(self):
        opening = self.data['topic_alignment']['opening']
        entry = '晴朗白天天空的蓝色来自被空气散向眼睛的阳光。'
        route = '先定位阳光、空气和眼睛，再比较散射的颜色。'
        opening.update(spoken_question=entry, answer_route=route, voiceover=entry + route,
                       question_comparison='结论式主题陈述明确回答同一晴朗白天蓝色来源，再说明解释任务。')
        self.data['qa']['topic_alignment']['opening_voiceover'].update(heard_question=entry, heard_answer_route=route)
        self.review['context_sha256'] = opening_context_sha256(self.data)
        self.review['question_comparison'] = opening['question_comparison']
        self.save()
        self.assertEqual(check_opening_plan(self.data), [])
        self.assertEqual(self.errors(), [])  # Synthetic declarations, not scientific or listening acceptance.

    def test_partial_interest_design_and_placeholder_content_rejected(self):
        for key in ('curiosity_gap', 'viewer_payoff', 'payoff_steps'):
            for value in (None, '', 'pending', [], {}):
                data = self.interest_plan(); data['topic_alignment']['opening'][key] = value
                self.assertTrue(check_opening_plan(data), (key, value))
            data = self.interest_plan(); del data['topic_alignment']['opening'][key]
            self.assertTrue(check_opening_plan(data), key)
        data = copy.deepcopy(self.data)
        data['topic_alignment']['opening']['viewer_payoff'] = '说明可见的具体关系。'
        self.assertTrue(check_opening_plan(data))

    def test_payoff_references_must_belong_to_existing_answer_evidence(self):
        for key, value in [('scope_id', 'missing'), ('scope_id', {}), ('shot_ids', ['missing']),
                           ('shot_ids', ['S3']), ('shot_ids', ['S2', 'S2']), ('shot_ids', [{}]),
                           ('shot_ids', []), ('contribution', 'pass')]:
            data = self.interest_plan(); data['topic_alignment']['opening']['payoff_steps'][0][key] = value
            self.assertTrue(check_opening_plan(data), (key, value))

    def test_payoff_order_follows_shots_and_allows_sequential_same_shot_progress(self):
        data = self.interest_plan()
        steps = data['topic_alignment']['opening']['payoff_steps']
        steps.reverse()
        self.assertTrue(any('actual shot order' in e for e in check_opening_plan(data)))
        data = self.interest_plan()
        data['topic_alignment']['opening']['payoff_steps'][0]['shot_ids'] = ['S2', 'S1']
        self.assertTrue(any('actual shot order' in e for e in check_opening_plan(data)))
        data = self.interest_plan()
        data['topic_alignment']['coverage'][1]['shot_ids'] = ['S2', 'S3']
        data['topic_alignment']['opening']['payoff_steps'][1]['shot_ids'] = ['S2', 'S3']
        self.assertEqual(check_opening_plan(data), [])

    def test_interest_design_does_not_force_episode_opening_on_local_or_chapter(self):
        for kind in ('local_sample', 'chapter'):
            data = self.interest_plan(); data['scope']['kind'] = kind
            data['topic_alignment']['opening'] = {'viewer_payoff': ''}
            self.assertEqual(check_opening_plan(data), [])

    def test_g1_direct_path_checks_new_interest_design(self):
        data = self.interest_plan(); data['topic_alignment']['opening'].pop('viewer_payoff')
        self.assertTrue(any('opening.viewer_payoff' in e for e in check_stage(data, self.root, 'G1')))

    def test_interest_change_invalidates_existing_actual_review_context(self):
        self.data = self.interest_plan()
        self.review['context_sha256'] = opening_context_sha256(self.data); self.save()
        self.assertEqual(self.errors(), [])
        self.data['topic_alignment']['opening']['payoff_steps'][0]['contribution'] += ' changed evidence task'
        self.save(); self.rejects('stale topic/opening/transcript context')

    def test_plan_missing_empty_or_placeholder_details_rejected(self):
        for key in ('spoken_question', 'answer_route', 'cover_question', 'question_comparison', 'visual_handoff'):
            for value in (None, '', 'pending', 'pass'):
                data = copy.deepcopy(self.data); data['topic_alignment']['opening'][key] = value
                self.assertTrue(check_opening_plan(data), (key, value))

    def test_plan_declared_generic_or_different_question_rejected(self):
        for relation in ('generic_only', 'different_question', 'pending'):
            self.data['topic_alignment']['opening']['question_relation'] = relation
            self.assertTrue(check_opening_plan(self.data))

    def test_g1_direct_stage_path_checks_plan(self):
        self.data['topic_alignment']['opening'].pop('cover_question')
        self.assertTrue(any('opening.cover_question' in e for e in check_stage(self.data, self.root, 'G1')))

    def test_schema_version_requires_integer_one(self):
        for value in (True, False, 1.0, '1', None):
            self.review['schema_version'] = value; self.save()
            self.rejects('schema_version must be integer 1')

    def test_fixture_without_release_covers_never_fabricates_final_pass(self):
        self.data['deliverables'].pop('cover_3_4')
        self.data['qa']['reviewed_sha256'].pop('cover_3_4')
        self.assertIsNone(attach_opening_fixture(self.data, self.root))
        self.assertEqual(self.data['qa']['topic_alignment']['opening_alignment']['status'], 'pending')
        self.rejects('actual scoped review required')

    def test_missing_or_empty_review_cannot_pass(self):
        self.data['qa']['topic_alignment'].pop('opening_alignment'); self.rejects('actual scoped review')
        self.review = {}; self.save(); self.rejects('schema_version')

    def test_declared_generic_hook_is_insufficient_under_overall_pass(self):
        self.data['qa']['topic_alignment']['opening_voiceover']['heard_question'] = '看看天空，它怎么变成这样？'
        self.review['question_relation'] = 'generic_only'
        self.review['context_sha256'] = opening_context_sha256(self.data); self.save()
        self.rejects('actual question generic_only')

    def test_empty_observations_and_nested_pending_cannot_hide_under_pass(self):
        for section, key, value in [('visual_handoff', 'status', 'pending'), ('visual_handoff', 'status', 'fail'),
                                    ('answer_route_review', 'status', 'pending'), ('answer_route_review', 'observation', '')]:
            with self.subTest(section=section, key=key, value=value):
                saved = copy.deepcopy(self.review)
                self.review[section][key] = value; self.save(); self.assertTrue(self.errors())
                self.review = saved

    def test_unwatched_unheard_or_noncontinuous_review_rejected(self):
        for key, value in [('actually_watched', False), ('actually_heard', False), ('method', 'frame_samples')]:
            old = self.review['sources'][0][key]; self.review['sources'][0][key] = value; self.save(); self.assertTrue(self.errors()); self.review['sources'][0][key] = old

    def test_cover_mismatch_pending_and_empty_title_rejected(self):
        for key, value in [('status', 'pending'), ('status', 'fail'), ('question_relation', 'different_question'), ('question_relation', 'pending'), ('observed_title', '')]:
            old = self.review['covers']['cover_3_4'][key]
            self.review['covers']['cover_3_4'][key] = value; self.save(); self.assertTrue(self.errors())
            self.review['covers']['cover_3_4'][key] = old

    def test_changed_actual_cover_bytes_rejected_even_with_same_declared_hashes(self):
        (self.root / 'portrait.bin').write_bytes(b'changed actual cover')
        self.rejects('evidence hash stale')

    def test_changed_actual_final_export_bytes_rejected(self):
        (self.root / 'video.bin').write_bytes(b'changed actual final export')
        self.rejects('evidence hash stale')

    def test_new_cover_and_outer_hash_cannot_reuse_old_proof(self):
        self.data['deliverables']['cover_3_4'] = 'new-cover.bin'
        (self.root / 'new-cover.bin').write_bytes(b'new cover bytes')
        self.data['qa']['reviewed_sha256']['cover_3_4'] = file_digest(self.root / 'new-cover.bin')
        self.save(); self.rejects('stale topic/opening/transcript context'); self.rejects('deliverable path mismatch')

    def test_rehashing_outer_evidence_cannot_refresh_old_context(self):
        self.data['topic_alignment']['opening']['spoken_question'] += ' 新改述'
        self.save(); self.rejects('stale topic/opening/transcript context')

    def test_actual_heard_transcript_change_invalidates_proof(self):
        self.data['qa']['topic_alignment']['opening_voiceover']['heard_question'] += ' 改动'
        self.rejects('stale topic/opening/transcript context')

    def test_proof_mutation_without_hash_refresh_rejected(self):
        (self.root / 'review.json').write_text('{}')
        self.rejects('evidence hash stale')

    def test_review_ranges_must_cover_entry_and_order_question_before_route(self):
        for key, value in [('viewed_range_s', [1, 12]), ('question_range_s', [0, 13]), ('answer_route_range_s', [0, 1])]:
            old = self.review[key]; self.review[key] = value; self.save(); self.assertTrue(self.errors()); self.review[key] = old
        self.review['visual_handoff']['range_s'] = [1, 2]; self.save(); self.rejects('include actual opening entry')

    def test_scoped_user_review_does_not_claim_assistant_listening(self):
        self.review['sources'][0].update(kind='user', reviewer='synthetic user')
        self.data['qa']['assistant_listening'] = {'status': 'unknown'}
        self.save(); self.assertEqual(self.errors(), [])
        self.assertEqual(self.data['qa']['assistant_listening']['status'], 'unknown')

    def test_general_praise_with_no_specific_coverage_is_insufficient(self):
        self.review['sources'][0].update(kind='user', statement='不错', reviewed_items=[])
        path = self.root / 'praise.txt'; path.write_text('不错')
        self.review['sources'][0]['evidence'] = dict(file=path.name, sha256=file_digest(path))
        self.save(); self.rejects('explicitly cover all opening items')

    def test_topic_review_allows_truthful_user_reviewer_role(self):
        from check_episode import check_topic, canonical_sha256, topic_review_sha256
        anchor = dict(version='1', title='天空的蓝色', question='白天天空为什么蓝？',
                      intent='explain_mechanism', required_scope=[dict(id='R1', answer_requirement='说明蓝色来源')])
        (self.root / 'topic-anchor.json').write_text(json.dumps(anchor))
        sha = canonical_sha256(anchor)
        self.data['topic'] = dict(current=anchor, anchor_file='topic-anchor.json', anchor_sha256=sha,
                                  current_sha256=sha, origin_reference='synthetic request source')
        alignment = self.data['topic_alignment']; alignment['topic_sha256'] = sha
        alignment['opening'].update(intent='explain_mechanism', scope_ids=['R1'], shot_ids=['S1'])
        alignment['ending'] = dict(answer='说明蓝色来源', intent='explain_mechanism', scope_ids=['R1'], shot_ids=['S1'])
        alignment['coverage'] = [dict(scope_id='R1', shot_ids=['S1'], answer_evidence='synthetic specific evidence')]
        alignment['omitted_scope_ids'] = []
        qa = self.data['qa']['topic_alignment']; qa.update(status='pass', reviewer_role='user')
        for item in ('opening_title', 'opening_voiceover', 'coverage', 'ending'):
            qa.setdefault(item, {}).update(status='pass', note='synthetic scoped user statement', evidence='synthetic source')
        qa['opening_voiceover']['review_scope'] = 'final_export'
        qa['reviewed_sha256'] = topic_review_sha256(self.data)
        self.assertEqual(check_topic(self.data, self.root, 'delivery', {'S1': self.data['shots'][0]}), [])

    def test_source_statement_must_exist_in_bound_original(self):
        self.review['sources'][0]['statement'] = 'An invented claim of listening'; self.save()
        self.rejects('statement missing from bound original')

    def test_missing_source_and_stale_source_rejected(self):
        self.review['sources'][0]['reference'] = ''; self.save(); self.rejects('reference required')
        (self.root / 'synthetic-opening-source.txt').write_text('changed source')
        self.rejects('evidence hash stale')

    def test_sources_can_combine_real_item_scopes(self):
        visual = self.review['sources'][0]
        cover = copy.deepcopy(visual)
        cover.update(reviewed_items=['cover_question'], actually_heard=False, method='actual_cover_inspection', range_s=[])
        visual.update(kind='user', reviewed_items=['spoken_question', 'answer_route', 'visual_handoff'])
        self.review['sources'] = [cover, visual]; self.save()
        self.assertEqual(self.errors(), [])

    def test_source_pending_or_unheard_is_not_hidden_by_other_source(self):
        old = copy.deepcopy(self.review['sources'][0])
        for field, value in [('status', 'pending'), ('actually_heard', False), ('actually_watched', False)]:
            self.review['sources'] = [copy.deepcopy(old), copy.deepcopy(old)]
            self.review['sources'][1][field] = value; self.save()
            self.assertTrue(self.errors())

    def test_each_source_range_must_cover_its_claimed_items(self):
        self.review['sources'][0]['range_s'] = [0, 2]; self.save()
        self.rejects('actual range does not cover')

    def test_handoff_must_fit_reviewed_opening(self):
        self.review['visual_handoff']['range_s'] = [0, 13]; self.save()
        self.rejects('visual handoff must be a nonempty bounded time range')

    def test_huge_integer_and_nonfinite_ranges_reject_without_crash(self):
        for value in (10 ** 1000, float('inf'), float('nan'), True):
            self.review['question_range_s'] = [0, value]; self.save()
            self.rejects('spoken question must be a nonempty bounded time range')

    def test_real_probe_does_not_accept_synthetic_bytes_as_media(self):
        self.assertTrue(self.errors(real_probe=True))

    def test_stage_g5_g6_g7_require_final_opening_evidence(self):
        self.data['qa']['topic_alignment'].pop('opening_alignment')
        for stage in ('G5', 'G6', 'G7'):
            errors = check_stage(self.data, self.root, stage)
            self.assertTrue(any('opening alignment: actual scoped review' in e for e in errors), errors)


if __name__ == '__main__':
    unittest.main()
