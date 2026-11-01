"""Synthetic record regressions; no media was heard and no quality pass is asserted."""
import copy
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

LOCAL_SCRIPTS = Path(__file__).resolve().parents[1]
BASE = (LOCAL_SCRIPTS.parent if (LOCAL_SCRIPTS / 'stage_checks.py').is_file()
        else Path(os.environ['SCIENCE_SKILL_TEST_BASE']))
sys.path.insert(0, str(BASE / 'scripts'))
sys.path.insert(0, os.environ.get('SCIENCE_SKILL_TEST_CANDIDATE', str(LOCAL_SCRIPTS)))

from presentation_checks import VOICE_CRITERIA, validate_voice_continuity
from stage_checks import Checks, context_sha256, digest


class VoiceContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('SCIENCE_SKILL_TEST_TMP'))
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        media = self.root / 'synthetic-record-fixture.bin'
        media.write_bytes(b'Synthetic record fixture only: no audiovisual media or review')
        self.viewing = {'file': media.name, 'sha256': hashlib.sha256(media.read_bytes()).hexdigest(),
                        'duration': 10, 'ranges': [[0, 10]]}
        self.data = {'narration': {'audio_sha256': 'a' * 64, 'delivery_plan': {
            'mode': 'continuous_first', 'target': {
                'tone': 'One stable natural speaker with meaningful emphasis',
                'rhythm': 'Continuous semantic phrasing with concise endings',
                'speech_rate': 'Clear intelligible terms and purposeful observation pauses',
                'loudness': 'Consistent voice level with headroom'}}},
            'shots': [{'id': ident, 'asset_ids': [], 'shotbook': {'start': a, 'end': b}}
                      for ident, a, b in [('SH1', 0, 4), ('SH2', 4, 7), ('SH3', 7, 10)]],
            'qa': {'audio': {'continuity': {}}, 'visual_frames': {'animation': {
                'step_ids': ['EX1'], 'shot_intervals': [
                    {'shot_id': ident, 'start': a, 'end': b}
                    for ident, a, b in [('SH1', 0, 4), ('SH2', 4, 7), ('SH3', 7, 10)]]}}},
            'topic_alignment': {'coverage': [{'explanation_steps': [
                {'id': 'EX1', 'shot_ids': ['SH1', 'SH2', 'SH3']}]}]}}

    def review(self, gate='G5'):
        result = {'status': 'pass', 'context_sha256': context_sha256(self.data, gate),
                  'media_sha256': self.viewing['sha256'],
                  'audio_sha256': self.data['narration']['audio_sha256'],
                  'plan_sha256': digest(self.data['narration']['delivery_plan']),
                  'method': 'normal_speed_continuous_listening', 'actually_heard': True,
                  'reviewer': 'Synthetic record reviewer',
                  'capability': 'Synthetic declared normal speed listening capability',
                  'evidence': 'Synthetic declared observation; no listening occurred in this test',
                  'ranges': copy.deepcopy(self.viewing['ranges']),
                  'criteria': {key: {'status': 'pass',
                      'observation': 'Synthetic record observation for ' + key,
                      'evidence': 'Synthetic declared observation evidence for ' + key}
                      for key in VOICE_CRITERIA}, 'transitions': []}
        self.data['qa']['audio']['continuity'][gate] = result
        return result

    def row(self, left='SH1', right='SH2', at=4):
        return {'from_shot': left, 'to_shot': right, 'at': at,
                'listen_range': [at - 1, at + 1], 'status': 'pass',
                'observation': 'Synthetic continuous utterance across the observed picture cut',
                'evidence': 'Synthetic record evidence at the actual current-media boundary'}

    def errors(self, gate='G5'):
        checks = Checks(self.data, self.root)
        validate_voice_continuity(checks, gate, self.viewing)
        return checks.errors

    def blocked(self, errors, fragment):
        self.assertTrue(any(fragment in error for error in errors), errors)

    def test_continuous_track_needs_no_row_for_each_picture_cut_at_all_stages(self):
        for gate in ('G2', 'G3', 'G5'):
            with self.subTest(gate=gate):
                self.review(gate)
                self.assertEqual(self.errors(gate), [])

    def test_omitted_optional_transition_ledger_is_valid(self):
        r = self.review()
        del r['transitions']
        self.assertEqual(self.errors(), [])

    def test_targeted_subset_and_legacy_complete_cut_rows_stay_valid(self):
        r = self.review()
        r['transitions'] = [self.row()]
        self.assertEqual(self.errors(), [])
        r['transitions'].append(self.row('SH2', 'SH3', 7))
        self.assertEqual(self.errors(), [])

    def test_supplied_ledger_must_be_list(self):
        r = self.review()
        for value in (None, {}, 'unreviewed'):
            with self.subTest(value=value):
                r['transitions'] = value
                self.blocked(self.errors(), 'transition observations must be a list')

    def test_supplied_bad_rows_fail(self):
        changes = [({'from_shot': 'SH3', 'to_shot': 'SH1'}, 'missing/duplicate/irrelevant'),
                   ({'from_shot': None}, 'shot IDs invalid'),
                   ({'at': 4.25}, 'time must match'),
                   ({'at': float('nan')}, 'straddle'),
                   ({'listen_range': [4, 5]}, 'straddle'),
                   ({'listen_range': [3, 11]}, 'straddle'),
                   ({'listen_range': [3, 4]}, 'straddle'),
                   ({'status': 'fail'}, 'failed/unreviewed'),
                   ({'status': 'pending'}, 'failed/unreviewed'),
                   ({'observation': ''}, 'failed/unreviewed'),
                   ({'evidence': 'pending'}, 'failed/unreviewed')]
        r = self.review()
        for updates, message in changes:
            with self.subTest(updates=updates):
                row = self.row()
                row.update(updates)
                r['transitions'] = [row]
                self.blocked(self.errors(), message)

    def test_duplicate_supplied_rows_fail(self):
        r = self.review()
        r['transitions'] = [self.row(), self.row()]
        self.blocked(self.errors(), 'missing/duplicate/irrelevant')

    def test_missing_record_and_failed_review_remain_blocked(self):
        self.blocked(self.errors(), 'failed/unreviewed')
        r = self.review()
        r['status'] = 'fail'
        self.blocked(self.errors(), 'failed/unreviewed')

    def test_unheard_noncontinuous_or_missing_capability_remain_blocked(self):
        changes = [('actually_heard', False), ('method', 'frame_samples'),
                   ('reviewer', ''), ('capability', 'pending'), ('evidence', '')]
        for key, value in changes:
            with self.subTest(key=key):
                r = self.review()
                r[key] = value
                self.blocked(self.errors(), 'actual complete continuous listening required')

    def test_current_media_audio_plan_and_context_hashes_remain_required(self):
        for key in ('media_sha256', 'audio_sha256', 'plan_sha256', 'context_sha256'):
            with self.subTest(key=key):
                r = self.review()
                r[key] = 'f' * 64
                self.blocked(self.errors(), 'stale media/audio/target plan')

    def test_changed_plan_or_audio_cannot_reuse_old_cut_observation(self):
        r = self.review()
        r['transitions'] = [self.row()]
        self.data['narration']['delivery_plan']['target']['tone'] = 'Changed stable speaker direction'
        self.blocked(self.errors(), 'stale media/audio/target plan')
        self.review()['transitions'] = [self.row()]
        self.data['narration']['audio_sha256'] = 'b' * 64
        self.blocked(self.errors(), 'stale media/audio/target plan')

    def test_incomplete_listening_ranges_fail(self):
        r = self.review()
        r['ranges'] = [[0, 4]]
        self.blocked(self.errors(), 'listening must cover complete reviewed clip/export')

    def test_incomplete_viewing_range_cannot_become_complete_listening(self):
        # Exercise the existing caller's complete-range check with a synthetic
        # duration stub. No FFmpeg, media generation, or perception is invoked.
        self.viewing.update(ranges=[[0, 4]], scope='final', method='continuous_playback',
                            playback_speed=1, heard=True, watched=True,
                            reviewer='Synthetic reviewer', capability='Synthetic declared capability',
                            reviewed_at='2026-11-01', note='Synthetic record only')
        self.data['deliverables'] = {'video': self.viewing['file']}
        self.review()
        checks = Checks(self.data, self.root)
        with patch.object(checks, 'duration', return_value=10):
            viewing = checks.viewing(self.viewing, 'synthetic final viewing', 'final', final=True)
        validate_voice_continuity(checks, 'G5', viewing)
        self.blocked(checks.errors, 'full evidence clip must actually be covered')

    def test_failed_joins_or_voice_drift_cannot_be_offset_by_empty_ledger(self):
        for criterion in VOICE_CRITERIA:
            for field, value in [('status', 'fail'), ('observation', ''), ('evidence', 'pending')]:
                with self.subTest(criterion=criterion, field=field):
                    r = self.review()
                    r['criteria'][criterion][field] = value
                    self.blocked(self.errors(), criterion + ' failure cannot be offset')

    def test_missing_criteria_fail(self):
        r = self.review()
        del r['criteria']['joins']
        self.blocked(self.errors(), 'tone/rhythm/rate/loudness/joins criteria required')

    def test_incomplete_or_gapped_full_media_shot_timeline_still_fails(self):
        for edits in ('missing', 'gap', 'overlap'):
            original = copy.deepcopy(self.data['shots'])
            with self.subTest(edits=edits):
                if edits == 'missing':
                    self.data['shots'].pop()
                else:
                    self.data['shots'][1]['shotbook']['start'] = 5 if edits == 'gap' else 3
                self.review()
                self.blocked(self.errors(), 'current-media shot timeline')
                self.data['shots'] = original

    def test_g3_subset_uses_complete_sample_local_timeline(self):
        animation = self.data['qa']['visual_frames']['animation']
        self.data['topic_alignment']['coverage'][0]['explanation_steps'][0]['shot_ids'] = ['SH2', 'SH3']
        animation['shot_intervals'] = [{'shot_id': 'SH2', 'start': 0, 'end': 3},
                                      {'shot_id': 'SH3', 'start': 3, 'end': 6}]
        self.viewing.update(duration=6, ranges=[[0, 6]])
        r = self.review('G3')
        self.assertEqual(self.errors('G3'), [])
        r['transitions'] = [self.row('SH2', 'SH3', 7)]
        self.blocked(self.errors('G3'), 'time must match actual current-media shot boundary')
        r['transitions'] = [self.row('SH2', 'SH3', 3)]
        self.assertEqual(self.errors('G3'), [])
        animation['shot_intervals'].pop()
        self.blocked(self.errors('G3'), 'complete reviewed media and selected shots')

    def test_contextual_segment_plan_and_handoff_checks_unchanged(self):
        refs = []
        for index in (1, 2):
            path = self.root / ('segment' + str(index) + '.txt')
            path.write_text('Synthetic segment source fixture', encoding='utf-8')
            refs.append({'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        plan = self.data['narration']['delivery_plan']
        plan.update(mode='context_preserving_segments', technical_limit='Synthetic verified interface limit',
                    verified_method='Synthetic complete semantic segments before expansion',
                    capability_evidence='Synthetic real backend method evidence fixture',
                    context_handoff='Synthetic matching semantic unit handoff', segments=[
                        {'id': 'S1', 'script': refs[0], 'audio': refs[0],
                         'context_before': 'Opening question', 'context_after': 'Cause established',
                         'handoff_evidence': 'Synthetic adjacent-unit listening evidence'},
                        {'id': 'S2', 'script': refs[1], 'audio': refs[1],
                         'context_before': 'Cause established', 'context_after': 'Result explained',
                         'handoff_evidence': 'Synthetic adjacent-unit listening evidence'}])
        self.review()
        self.assertEqual(self.errors(), [])
        plan['segments'][1]['context_before'] = 'Different unsupported handoff'
        self.review()
        self.blocked(self.errors(), 'segment narrative context handoff mismatch')
        plan['segments'][1]['context_before'] = 'Cause established'
        plan['segments'][1]['audio']['sha256'] = 'c' * 64
        self.review()
        self.blocked(self.errors(), 'segment audio evidence hash stale')


if __name__ == '__main__':
    unittest.main(verbosity=2)
