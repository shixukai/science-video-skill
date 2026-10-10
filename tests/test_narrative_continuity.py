"""Structural continuity regressions; no assertion of actual audience understanding."""
import copy
from pathlib import Path
import tempfile
import unittest

from stage_fixture import gates


class NarrativeContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = {
            'brief': {'audience_start': {'assumed_knowledge': ['recognizes the object']}},
            'shots': [{'id': 'S1'}, {'id': 'S2'}, {'id': 'S3'}],
        }
        self.steps = {
            'A': {'shot_ids': ['S1'], 'prerequisites': [
                {'knowledge': 'recognizes the object', 'source': 'audience_prior'}]},
            'B': {'shot_ids': ['S2'], 'prerequisites': [
                {'knowledge': 'the state established in A', 'source': 'step', 'step_id': 'A'}]},
            'C': {'shot_ids': ['S3'], 'prerequisites': [
                {'knowledge': 'the relation established in B', 'source': 'step', 'step_id': 'B'}]},
        }

    def tearDown(self):
        self.temp.cleanup()

    def errors(self):
        checks = gates.Checks(self.data, self.root)
        checks.prerequisites(self.steps)
        return checks.errors

    def test_established_premises_pass(self):
        self.assertEqual(self.errors(), [])

    def test_unknown_self_and_invalid_references_fail_without_crash(self):
        for target in ('missing', 'B', {}, [], None):
            with self.subTest(target=target):
                self.steps['B']['prerequisites'][0]['step_id'] = target
                self.assertTrue(any('different known step' in e for e in self.errors()))

    def test_future_dependency_fails(self):
        self.steps['B']['prerequisites'][0]['step_id'] = 'C'
        self.assertTrue(any('before use' in e for e in self.errors()))

    def test_cycle_fails(self):
        self.steps['A']['prerequisites'] = [
            {'knowledge': 'a circular premise', 'source': 'step', 'step_id': 'C'}]
        self.assertTrue(any('before use' in e for e in self.errors()))

    def test_premise_must_finish_before_consumer(self):
        self.steps['A']['shot_ids'] = ['S1', 'S3']
        self.assertTrue(any('before use' in e for e in self.errors()))

    def test_same_shot_uses_declared_step_order(self):
        self.steps['B']['shot_ids'] = ['S1']
        self.assertEqual(self.errors(), [])
        self.steps = {'B': self.steps['B'], 'A': self.steps['A'], 'C': self.steps['C']}
        self.assertTrue(any('before use' in e for e in self.errors()))

    def test_coverage_grouping_does_not_override_actual_shot_order(self):
        self.steps = {'C': self.steps['C'], 'A': self.steps['A'], 'B': self.steps['B']}
        self.assertEqual(self.errors(), [])
        self.data['shots'].reverse()
        self.assertTrue(any('before use' in e for e in self.errors()))

    def test_audience_claim_must_be_declared(self):
        self.steps['A']['prerequisites'][0]['knowledge'] = 'unestablished technical mechanism'
        self.assertTrue(any('declared assumed_knowledge' in e for e in self.errors()))

    def test_missing_text_only_or_placeholder_premises_fail(self):
        for refs in (None, [], ['a free-form assertion'], [{}], [{'knowledge': 'pending', 'source': 'audience_prior'}]):
            with self.subTest(refs=refs):
                self.steps['A']['prerequisites'] = refs
                self.assertTrue(any('explicit prerequisites' in e for e in self.errors()))

    def test_source_is_explicit_and_audience_source_cannot_hide_step(self):
        self.steps['A']['prerequisites'][0]['step_id'] = 'C'
        self.assertTrue(any('without a step_id' in e for e in self.errors()))
        self.steps['A']['prerequisites'][0]['source'] = {}
        self.assertTrue(any('source must be' in e for e in self.errors()))

    def causal_errors(self):
        data = copy.deepcopy(self.data)
        data['topic'] = {'current': {'required_scope': [{'id': key} for key in self.steps]}}
        coverage = []
        for ident, step in self.steps.items():
            row = dict(step, id=ident, before='initial object', change='supported change',
                       after='observed result', handoff='use the result', requires_dynamic=True)
            coverage.append({'scope_id': ident, 'shot_ids': step['shot_ids'], 'causal_steps': [row]})
        data['topic_alignment'] = {'main_scope_ids': list(self.steps), 'coverage': coverage}
        checks = gates.Checks(data, self.root)
        checks.causal()
        return checks.errors

    def test_legacy_causal_records_cannot_omit_premise_sources(self):
        self.assertEqual(self.causal_errors(), [])
        self.steps['B'].pop('prerequisites')
        self.assertTrue(any('explicit prerequisites' in e for e in self.causal_errors()))

    def test_cross_scope_same_shot_dependency_is_integrated(self):
        self.steps['B']['shot_ids'] = ['S1']
        self.assertEqual(self.causal_errors(), [])
        self.steps = {'B': self.steps['B'], 'A': self.steps['A'], 'C': self.steps['C']}
        self.assertTrue(any('before use' in e for e in self.causal_errors()))

    def narration_errors(self, excerpts, master='先看对象。再看变化。最后回答。'):
        path = self.root / 'script.txt'
        path.write_text(master, encoding='utf-8')
        data = copy.deepcopy(self.data)
        for shot, excerpt in zip(data['shots'], excerpts):
            shot['shotbook'] = {'narration_exact_text': excerpt}
        checks = gates.Checks(data, self.root)
        checks.narration_sequence(path)
        return checks.errors

    def test_contiguous_excerpts_and_layout_whitespace_pass(self):
        self.assertEqual(self.narration_errors(['先看对象。\n', '再看变化。', '最后回答。']), [])
        self.assertEqual(self.narration_errors(['先看对象。再看变化。', '', '最后回答。']), [])

    def test_reordered_rewritten_omitted_or_repeated_excerpts_fail(self):
        for excerpts in (
            ['再看变化。', '先看对象。', '最后回答。'],
            ['大家好，先看对象。', '再看变化。', '最后回答。'],
            ['先看对象。', '', '最后回答。'],
            ['先看对象。', '再看变化。', '再看变化。最后回答。'],
        ):
            with self.subTest(excerpts=excerpts):
                self.assertTrue(any('continuous master script' in e for e in self.narration_errors(excerpts)))

    def test_silent_shot_must_be_explicit_and_empty_master_fails(self):
        self.assertTrue(any('narration_exact_text required' in e for e in self.narration_errors(['先看对象。再看变化。最后回答。'])))
        self.assertTrue(any('continuous master script' in e for e in self.narration_errors(['', '', ''], '\n')))


if __name__ == '__main__':
    unittest.main()
