"""Synthetic evidence-contract regression; never actual artwork/media approval.

The duration probe is stubbed except the explicit non-media rejection test. Files
are disposable synthetic bytes, not user media or a real audiovisual review.
"""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from feedback_guard import validate_feedback, feedback_context_sha256
from stage_checks import Checks, check_stage


class FeedbackContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.artifact = self.write('synthetic-media.bin', b'synthetic repair bytes, not actual media')
        self.change = self.write('change.txt', b'synthetic rule delta')
        self.regression = self.json('regression.json', {'rule_id': 'feedback-retest', 'rule_version': '1.4.2', 'change_sha256': self.change['sha256'], 'command': 'python -m unittest synthetic', 'executed': True, 'exit_code': 0, 'result': 'tests_pass'})
        self.row = {'contract_version': 1, 'feedback_id': 'f1', 'origin': 'user',
                    'source_ref': 'synthetic-source-1', 'received_at': '2026-01-01',
                    'original_feedback': 'The relation is clear; the enlarged control and flat dark backdrop are visually rough.',
                    'media_version': 'synthetic-old', 'media_sha256': 'a' * 64,
                    'scope': 'representative mechanism segment', 'scope_kind': 'segment', 'time_range_s': [0, 24],
                    'applies_to_gates': ['G3'], 'dimensions': {
                        'comprehension': {'status': 'pass', 'note': 'Old segment relation recognized only'},
                        'art': {'status': 'fail', 'note': 'Enlarged UI lacks fine scene integration'}},
                    'what_changes': 'Candidate: visible state change in a coherent natural scene',
                    'status': 'candidate', 'repair_time_range_s': [0, 24],
                    'skill_update': {'disposition': 'rule_change', 'proposed_change': 'Keep art independent of understanding', 'status': 'pending'}}
        self.data = {'qa': {'feedback_expected_ids': ['f1'], 'feedback': [self.row],
                           'visual_frames': {'status': 'pending', 'art': {'status': 'fail'},
                                             'animation': {'viewing': dict(self.artifact)}},
                           'comprehension': {'status': 'audience_checked'},
                           'reviewed_sha256': {'video': self.artifact['sha256']}}}

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, contents):
        (self.root / name).write_bytes(contents)
        return {'file': name, 'sha256': hashlib.sha256(contents).hexdigest()}

    def json(self, name, record):
        return self.write(name, json.dumps(record).encode())

    def check(self, target='G3', expanding=False, real_probe=False):
        checks = Checks(self.data, self.root)
        if not real_probe:
            checks.duration = lambda *args, **kwargs: 24.0
        validate_feedback(checks, target, expanding)
        return checks.errors

    def resolve(self):
        self.regression = self.json('regression.json', {'rule_id': 'feedback-retest', 'rule_version': '1.4.2', 'change_sha256': self.change['sha256'], 'command': 'python -m unittest synthetic', 'executed': True, 'exit_code': 0, 'result': 'tests_pass'})
        self.row['status'] = 'resolved'
        self.row['repair_artifacts'] = [self.artifact]
        self.row['skill_update'].update(status='implemented', rule_id='feedback-retest', rule_version='1.4.2',
                                       change_evidence=self.change, regression_evidence=[self.regression],
                                       deployment_status='not_deployed', sample_validation='pending')
        self.review = {'feedback_id': 'f1', 'feedback_context_sha256': feedback_context_sha256(self.row),
                       'media_sha256': self.artifact['sha256'], 'status': 'pass',
                       'source_time_range_s': [0, 24], 'scope_mapping': 'same duration, revised scene',
                       'ranges': [[0, 12], [12, 24]], 'scope': 'complete representative segment', 'scope_kind': 'segment',
                       'reviewer': 'synthetic-checker', 'actual_viewed': True,
                       'observation': 'Synthetic example only: current art and relation reviewed independently',
                       'normal_speed_continuous_av': True,
                       'dimension_results': {'art': {'status': 'pass', 'observation': 'Synthetic fine scene observation'},
                                             'comprehension': {'status': 'pass', 'observation': 'Synthetic current relation recheck'}}}
        self.save_review()
        self.data['qa']['visual_frames']['art']['status'] = 'pass'

    def save_review(self):
        self.row['retest_evidence'] = [self.json('review.json', self.review)]

    def test_old_empty_packet_needs_no_migration(self):
        self.data = {'qa': {}}
        self.assertEqual(self.check(expanding=True), [])

    def test_untouched_nonuser_archive_compatible(self):
        self.data = {'qa': {'feedback': [{'origin': 'editor', 'note': 'legacy archive'}]}}
        self.assertEqual(self.check(), [])

    def test_repair_allowed_while_art_failed_and_skill_pending(self):
        self.assertEqual(self.check(), [])

    def test_understanding_pass_cannot_cancel_art_failure(self):
        self.assertTrue(any('unresolved' in e for e in self.check(expanding=True)))

    def test_overall_pass_rejected_even_in_repair(self):
        self.data['qa']['visual_frames']['status'] = 'pass'
        self.assertTrue(any('overall visual pass' in e for e in self.check()))

    def test_art_pass_cannot_erase_registered_failure(self):
        self.data['qa']['visual_frames']['art']['status'] = 'pass'
        self.assertTrue(any('overwritten' in e for e in self.check()))

    def test_missing_feedback_id_is_blocked(self):
        self.data['qa']['feedback'] = []
        self.assertTrue(any('omitted' in e for e in self.check()))

    def test_stripping_contract_does_not_bypass_expected_record(self):
        self.row.pop('origin'); self.row.pop('contract_version')
        self.assertTrue(any('contract_version' in e for e in self.check()))

    def test_failure_reference_also_prevents_legacy_bypass(self):
        self.data['qa']['feedback_expected_ids'] = []
        self.data['qa']['visual_frames']['failures'] = [{'feedback_id': 'f1'}]
        self.row.pop('origin'); self.row.pop('contract_version')
        self.assertTrue(self.check())

    def test_unique_ids_required(self):
        self.data['qa']['feedback'].append(copy.deepcopy(self.row))
        self.assertTrue(any('unique' in e for e in self.check()))

    def test_before_first_affected_gate_remains_available(self):
        self.assertEqual(self.check('G2', True), [])

    def test_failed_g3_feedback_blocks_all_later_gates(self):
        for gate in ('G3', 'G4', 'G5', 'G6', 'G7'):
            self.assertTrue(self.check(gate, True), gate)

    def test_resolved_synthetic_contract_does_not_require_deployment(self):
        self.resolve()
        self.assertEqual(self.check(expanding=True), [])

    def test_g4_candidate_can_follow_reviewed_sample_without_early_g5(self):
        self.resolve(); self.data['qa']['reviewed_sha256']['video'] = 'b' * 64
        self.assertEqual(self.check('G4', True), [])

    def test_new_sample_does_not_auto_approve_new_final(self):
        self.resolve(); self.data['qa']['reviewed_sha256']['video'] = 'b' * 64
        self.assertTrue(any('stale retest' in e for e in self.check('G5', True)))

    def test_old_understanding_pass_requires_new_retest(self):
        self.resolve(); self.review['dimension_results'].pop('comprehension'); self.save_review()
        self.assertTrue(any('comprehension' in e for e in self.check(expanding=True)))

    def test_top_level_failed_review_cannot_hide_behind_dimensions(self):
        self.resolve(); self.review['status'] = 'fail'; self.save_review()
        self.assertTrue(self.check(expanding=True))

    def test_failed_art_retest_cannot_be_averaged(self):
        self.resolve(); self.review['dimension_results']['art']['status'] = 'fail'; self.save_review()
        self.assertTrue(self.check(expanding=True))

    def test_unwatched_or_static_only_review_not_a_sample_pass(self):
        for key in ('actual_viewed', 'normal_speed_continuous_av'):
            self.resolve(); self.review[key] = False; self.save_review()
            self.assertTrue(self.check(expanding=True), key)

    def test_partial_and_gapped_retests_blocked(self):
        for ranges in ([[0, 1]], [[0, 10], [12, 24]], [[0, 25]]):
            self.resolve(); self.review['ranges'] = ranges; self.save_review()
            self.assertTrue(self.check(expanding=True), str(ranges))

    def test_original_range_mapping_required(self):
        self.resolve(); self.review['source_time_range_s'] = [0, 1]; self.save_review()
        self.assertTrue(self.check(expanding=True))

    def test_changing_feedback_scope_or_adjustment_invalidates_retest(self):
        for key in ('scope', 'source_ref', 'what_changes'):
            self.resolve(); self.row[key] += ' changed'
            self.assertTrue(any('stale feedback' in e for e in self.check(expanding=True)))

    def test_same_failed_media_is_not_its_own_repair(self):
        self.resolve(); self.row['media_sha256'] = self.artifact['sha256']
        self.review['feedback_context_sha256'] = feedback_context_sha256(self.row); self.save_review()
        self.assertTrue(any('old failed media' in e for e in self.check(expanding=True)))

    def test_missing_and_stale_repair_artifacts_block(self):
        self.resolve(); self.row['repair_artifacts'][0] = dict(self.artifact, sha256='b' * 64)
        self.assertTrue(self.check(expanding=True))

    def test_technical_file_is_not_actual_video(self):
        self.resolve()
        self.assertTrue(self.check(expanding=True, real_probe=True))

    def test_failed_or_unrun_regression_cannot_close_skill_action(self):
        for field, value in (('exit_code', 1), ('result', 'failed'), ('executed', False)):
            self.resolve()
            record = {'rule_id': 'feedback-retest', 'rule_version': '1.4.2', 'change_sha256': self.change['sha256'], 'command': 'python test.py', 'executed': True, 'exit_code': 0, 'result': 'pass'}
            record[field] = value
            self.row['skill_update']['regression_evidence'] = [self.json('regression.json', record)]
            self.assertTrue(self.check(expanding=True))

    def test_skill_change_alone_cannot_close_media_feedback(self):
        self.resolve(); self.row['retest_evidence'] = []
        self.assertTrue(self.check(expanding=True))

    def test_new_static_direction_approval_does_not_close_old_dynamic_failure(self):
        approved = copy.deepcopy(self.row)
        approved.update(feedback_id='f2', media_sha256='c' * 64, media_version='new-static-direction',
                        scope='static artwork direction only', scope_kind='static_direction', time_range_s=[], status='recorded',
                        dimensions={'static_art': {'status': 'pass', 'note': 'Only this direction image approved'}})
        self.data['qa']['feedback'].append(approved)
        self.data['qa']['feedback_expected_ids'].append('f2')
        self.assertEqual(self.check(expanding=False), [])
        self.assertTrue(any('unresolved' in error for error in self.check(expanding=True)))
        self.assertEqual(self.data['qa']['feedback'][0]['dimensions']['art']['status'], 'fail')

    def test_static_art_pass_with_pending_animation_cannot_claim_resolved(self):
        self.resolve()
        self.review['dimension_results'] = {'static_art': {'status': 'pass', 'observation': 'Direction only'},
                                            'motion': {'status': 'pending', 'observation': 'No continuous sample'}}
        self.save_review()
        self.assertTrue(self.check(expanding=True))

    def test_local_or_static_review_cannot_close_whole_episode_feedback(self):
        self.row['scope_kind'] = 'whole_episode'
        self.resolve()
        for kind in ('segment', 'static_direction'):
            self.review['scope_kind'] = kind; self.save_review()
            self.assertTrue(self.check(expanding=True))

    def test_whole_scope_cannot_be_closed_with_one_second(self):
        self.row['scope_kind'] = 'whole_episode'; self.row['repair_time_range_s'] = [0, 1]
        self.resolve(); self.review['scope_kind'] = 'whole_episode'; self.review['ranges'] = [[0, 1]]; self.save_review()
        self.assertTrue(any('partial repair range' in error for error in self.check(expanding=True)))

    def test_huge_nan_bool_and_malformed_time_ranges_fail_without_crash(self):
        for value in ([0, 10**400], [0, float('nan')], [False, 1], 'whole'):
            self.row['time_range_s'] = value
            self.assertTrue(self.check())

    def test_regression_cannot_be_reused_for_another_rule_or_change(self):
        for key, value in (('rule_id', 'another-rule'), ('rule_version', '1.4.3')):
            self.resolve(); self.row['skill_update'][key] = value
            self.assertTrue(any('stale regression' in error for error in self.check(expanding=True)))
        self.resolve(); self.row['skill_update']['change_evidence'] = self.write('new-change.txt', b'new rule delta')
        self.assertTrue(any('stale regression' in error for error in self.check(expanding=True)))

    def resolve_static(self):
        from PIL import Image
        Image.new('RGB', (2, 2), 'white').save(self.root / 'synthetic-still.png')
        self.artifact = self.write('synthetic-still.png', (self.root / 'synthetic-still.png').read_bytes())
        self.row.update(scope_kind='static_direction', scope='static direction only', time_range_s=[], repair_time_range_s=[],
                        dimensions={'art': {'status': 'fail', 'note': 'This static direction lacks detail'}})
        self.resolve()
        self.review.update(scope_kind='static_direction', scope='static direction only', source_time_range_s=[], ranges=[],
                           normal_speed_continuous_av=False,
                           dimension_results={'art': {'status': 'pass', 'observation': 'Synthetic still independently reviewed'}})
        self.save_review()

    def test_real_still_can_close_only_its_static_feedback(self):
        self.resolve_static()
        self.assertEqual(self.check(expanding=True, real_probe=True), [])

    def test_static_repair_does_not_close_another_dynamic_feedback(self):
        dynamic = copy.deepcopy(self.row); dynamic['feedback_id'] = 'dynamic'
        self.resolve_static()
        self.data['qa']['feedback'].append(dynamic); self.data['qa']['feedback_expected_ids'].append('dynamic')
        self.assertTrue(self.check(expanding=True))

    def test_fake_static_file_not_accepted(self):
        self.resolve_static(); (self.root / 'synthetic-still.png').write_bytes(b'not an image')
        self.assertTrue(self.check(expanding=True))

    def test_static_feedback_cannot_approve_understanding_or_motion(self):
        self.resolve_static(); self.row['dimensions']['motion'] = {'status': 'pass', 'note': 'unsupported motion claim'}
        self.review['feedback_context_sha256'] = feedback_context_sha256(self.row); self.save_review()
        self.assertTrue(self.check(expanding=True))

    def test_recorded_static_praise_cannot_claim_motion_understanding_or_audio(self):
        for dimension in ('motion', 'comprehension', 'audio', 'animation', 'whole_episode', 'publication', 'voice', 'unknown_dimension'):
            self.row.update(scope_kind='static_direction', time_range_s=[], status='recorded',
                            dimensions={dimension: {'status': 'pass', 'note': 'Only static direction approval exists'}})
            self.assertTrue(any('audiovisual dimensions' in error for error in self.check(expanding=True)))

    def test_static_whitelist_preserves_actual_still_dimensions(self):
        for dimension in ('art', 'static_art', 'layout', 'composition', 'color', 'lighting', 'material', 'detail', 'style'):
            self.row.update(scope_kind='static_direction', time_range_s=[], status='recorded',
                            dimensions={dimension: {'status': 'pass', 'note': 'Only this visible still property approved'}})
            self.assertEqual(self.check(expanding=True), [], dimension)

    def test_static_retest_cannot_sneak_extra_dynamic_alias_results(self):
        for dimension in ('animation', 'whole_episode', 'publication', 'voice'):
            self.resolve_static()
            self.review['dimension_results'][dimension] = {'status': 'pass', 'observation': 'Unsupported extra result'}
            self.save_review()
            self.assertTrue(any('static retest dimensions' in error for error in self.check(expanding=True)))

    def operations_profile(self):
        profile = json.loads((Path(__file__).resolve().parents[2] / 'config/series-profile.json').read_text())
        return profile

    def test_current_daily_targets_are_ten_and_independent(self):
        from check_reference_system import check_operations
        profile = self.operations_profile()
        self.assertEqual(profile['version'], '1.4.5')
        self.assertEqual(check_operations(profile['operations']), [])
        self.assertEqual(profile['operations']['daily_completed_unique_target'], 10)
        self.assertEqual(profile['operations']['daily_actual_unique_target'], 10)
        self.assertTrue(profile['operations']['daily_counting']['counters_independent'])
        self.assertTrue(profile['operations']['no_schedule_change_from_adoption'])

    def test_daily_target_regression_rejects_old_five_or_combined_counter(self):
        from check_reference_system import check_operations
        for field in ('daily_completed_unique_target', 'daily_actual_unique_target'):
            for value in (5, '10', True, None):
                operations = copy.deepcopy(self.operations_profile()['operations'])
                operations[field] = value
                self.assertTrue(check_operations(operations), (field, value))
        operations = copy.deepcopy(self.operations_profile()['operations'])
        operations['daily_counting']['counters_independent'] = False
        self.assertTrue(check_operations(operations))

    def test_daily_counts_cannot_credit_failures_samples_or_old_results(self):
        from check_reference_system import check_operations
        original = self.operations_profile()['operations']
        for excluded in original['daily_counting']['excluded_credits']:
            operations = copy.deepcopy(original)
            operations['daily_counting']['excluded_credits'].remove(excluded)
            self.assertTrue(check_operations(operations), excluded)
        for field in ('completion_basis', 'publication_basis', 'new_work_eligibility', 'unpublished_inventory'):
            operations = copy.deepcopy(original)
            operations['daily_counting'][field] = 'attempts_or_old_files'
            self.assertTrue(check_operations(operations), field)

    def test_daily_template_keeps_two_unknown_actual_counters(self):
        ledger = json.loads((Path(__file__).resolve().parents[2] / 'assets/project-ledger-template.json').read_text())
        self.assertEqual(ledger['production_ledger']['daily_target'], 10)
        self.assertEqual(ledger['publication_ledger']['daily_target'], 10)
        self.assertIsNone(ledger['production_ledger']['actual_unique_completed'])
        self.assertIsNone(ledger['publication_ledger']['actual_unique'])
        self.assertIsNone(ledger['production_ledger']['gap'])
        self.assertIsNone(ledger['publication_ledger']['gap'])
        self.assertEqual(ledger['record_formats']['episode']['new_work_eligibility']['status'], 'pending')
        self.assertEqual(ledger['record_formats']['episode']['quality_evidence'], [])
        self.assertEqual(ledger['record_formats']['episode']['publication_readback_evidence'], [])
        policy = json.loads((Path(__file__).resolve().parents[2] / 'config/production-policy.json').read_text())
        self.assertEqual(policy['capacity']['routine_batch_start'], 5)

    def test_daily_target_update_cannot_grant_schedule_authority(self):
        from check_reference_system import check_operations
        operations = copy.deepcopy(self.operations_profile()['operations'])
        operations['no_schedule_change_from_adoption'] = False
        self.assertTrue(check_operations(operations))

    def test_actual_stage_checker_calls_feedback_guard(self):
        for stage in ('G1', 'G3', 'G5'):
            errors = check_stage({'qa': {'feedback_expected_ids': ['omitted']}}, self.root, stage)
            self.assertTrue(any('explicit feedback omitted' in error for error in errors), stage)


if __name__ == '__main__':
    unittest.main()
