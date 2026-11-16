"""Synthetic editorial-input regressions; never proof of interest or actual selection."""
import copy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from topic_selection_fixture import attach_topic_selection_fixture, refresh_topic_selection_fixture
from topic_selection_guard import DISQUALIFIERS, selection_context_sha256, validate_topic_selection
from stage_checks import Checks, check_stage
import check_episode
import render_gate


class TopicSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.data = {}; attach_topic_selection_fixture(self.data)
        self.card = self.data['brief']['topic_selection']

    def tearDown(self):
        self.tmp.cleanup()

    def errors(self, refresh=True):
        if refresh: refresh_topic_selection_fixture(self.data)
        checks = Checks(self.data, self.root); validate_topic_selection(checks)
        return checks.errors

    def rejected(self, phrase, refresh=True):
        errors = self.errors(refresh); self.assertTrue(any(phrase in e for e in errors), errors)

    def test_editorial_hypothesis_needs_no_fabricated_feedback_or_popularity(self):
        self.assertEqual(self.card['audience_evidence'], [])
        self.assertEqual(self.errors(), [])
        self.assertNotIn('popularity', self.card)

    def test_missing_card_blocks(self):
        self.data['brief'].pop('topic_selection'); self.rejected('selection card', False)

    def test_child_audience_cannot_replace_adult_editorial_scope(self):
        self.card['audience_category'] = 'primary_school'; self.rejected('ordinary adult')

    def test_prior_knowledge_required(self):
        self.data['brief']['audience_start']['assumed_knowledge'] = []; self.rejected('prior knowledge')

    def test_specific_audience_required(self):
        self.data['brief']['audience'] = 'TODO'; self.rejected('specific adult')

    def test_answer_and_transfer_payoff_required(self):
        for obj, field in ((self.data['brief'], 'one_sentence_answer'), (self.data['brief']['understanding_targets'], 'transfer')):
            old = obj[field]; obj[field] = ''; self.rejected('payoff'); obj[field] = old

    def test_question_required(self):
        self.data['topic']['current']['question'] = '待定'; self.rejected('specific topic question')

    def test_each_core_card_field_required(self):
        for field in ('conflict_or_question', 'adult_relevance', 'knowledge_increment', 'causal_visualization'):
            old = self.card[field]; self.card[field] = '有趣'; self.rejected(field); self.card[field] = old

    def test_declared_unreviewed_placeholders_are_missing_not_editorial_content(self):
        for placeholder in ('待审', '未审', '待验', '未验', '待核', '不适用', '未核实', '未完成'):
            for field in ('conflict_or_question', 'adult_relevance', 'knowledge_increment', 'causal_visualization'):
                old = self.card[field]; self.card[field] = placeholder; self.rejected(field); self.card[field] = old
            for field in ('materials_and_rights_plan', 'method', 'constraints'):
                old = self.card['feasibility'][field]; self.card['feasibility'][field] = placeholder
                self.rejected('feasibility ' + field); self.card['feasibility'][field] = old
            for field in ('reviewer', 'reason'):
                old = self.card['review'][field]; self.card['review'][field] = placeholder
                self.rejected('actual editor'); self.card['review'][field] = old

    def test_feasible_plan_does_not_require_already_made_assets(self):
        self.assertNotIn('assets', self.data); self.assertEqual(self.errors(), [])

    def test_feasibility_plan_fields_required(self):
        for field in ('materials_and_rights_plan', 'method', 'constraints'):
            old = self.card['feasibility'][field]; self.card['feasibility'][field] = 'TODO'
            self.rejected('feasibility ' + field); self.card['feasibility'][field] = old

    def test_unresolved_feasibility_gap_blocks(self):
        self.card['feasibility']['blocking_gaps'] = ['No permitted way to show the claimed event']
        self.rejected('unresolved feasibility')

    def test_common_knowledge_title_repackaging_and_asset_led_reject_even_selected(self):
        for reason in DISQUALIFIERS:
            with self.subTest(reason=reason):
                self.card['disqualifiers'] = [reason]; self.rejected('disqualifiers')
        self.card['disqualifiers'] = ['another declared failure']; self.rejected('disqualifiers')

    def test_renaming_title_cannot_clear_declared_failure(self):
        self.card['disqualifiers'] = ['title_only_change']; self.data['title'] = 'A dramatic new headline'
        self.rejected('disqualifiers')

    def test_rejected_pending_or_revise_decision_blocks(self):
        for status in ('pending', 'revise', 'rejected', 'pass', None):
            self.card['review']['status'] = status; self.rejected('editorial decision')

    def test_editor_and_reason_cannot_be_empty_or_machine_score(self):
        for field in ('reviewer', 'reason'):
            old = self.card['review'][field]; self.card['review'][field] = 'pass'
            self.rejected('actual editor'); self.card['review'][field] = old

    def test_real_source_ids_required_unique_and_resolved(self):
        for refs in ([], ['missing'], [None], ['TOPIC_SELECTION_SYNTHETIC'] * 2, 'TOPIC_SELECTION_SYNTHETIC'):
            self.card['source_ids'] = refs; self.assertTrue(self.errors())

    def test_ambiguous_source_id_blocks(self):
        self.data['sources'].append(copy.deepcopy(self.data['sources'][0])); self.rejected('ambiguous')

    def test_source_url_malformed_or_nonweb_blocks_without_crash(self):
        for url in ('', 'file:///tmp/source', 'https://[bad', 'https:///no-host', 123):
            self.data['sources'][0]['url'] = url; self.rejected('traceable URL')

    def test_source_scope_publisher_title_required(self):
        for field in ('title', 'publisher', 'scope_note'):
            old = self.data['sources'][0][field]; self.data['sources'][0][field] = ''
            self.rejected('main source ' + field); self.data['sources'][0][field] = old

    def test_source_check_date_actual_and_not_future(self):
        for value in ('not-a-date', (date.today() + timedelta(days=1)).isoformat(), None):
            self.data['sources'][0]['accessed_on'] = value; self.rejected('date')

    def test_observed_interest_claim_requires_real_traceable_evidence(self):
        self.card['interest_basis'] = 'observed_audience_evidence'; self.rejected('real evidence')

    def add_evidence(self):
        (self.root/'audience.txt').write_text('Synthetic evidence bytes, no actual participant or audience claim.')
        self.card['audience_evidence'] = [{'file': 'audience.txt', 'sha256': hashlib.sha256((self.root/'audience.txt').read_bytes()).hexdigest(),
            'origin_reference': 'Synthetic local fixture only', 'observed_scope': 'Synthetic field test only', 'limitations': 'No real interest measured'}]
        self.card['interest_basis'] = 'observed_audience_evidence'

    def test_optional_evidence_hash_and_limitations_checked(self):
        self.add_evidence(); self.assertEqual(self.errors(), [])
        self.card['audience_evidence'][0]['limitations'] = ''; self.rejected('limitations')

    def test_claimed_audience_evidence_missing_or_stale_bytes_rejected(self):
        self.add_evidence(); (self.root/'audience.txt').write_text('changed')
        self.rejected('hash')
        (self.root/'audience.txt').unlink(); self.rejected('missing')

    def test_audience_evidence_outside_packet_rejected(self):
        self.add_evidence(); self.card['audience_evidence'][0]['file'] = '../outside.txt'; self.rejected('unsafe')

    def test_unknown_interest_basis_rejected(self):
        self.card['interest_basis'] = 'guaranteed_viral'; self.rejected('interest basis')

    def test_context_locks_topic_audience_payoff_and_sources(self):
        for obj, field in ((self.data['topic']['current'], 'question'), (self.data['brief'], 'audience'),
                           (self.data['brief']['understanding_targets'], 'transfer'), (self.data['sources'][0], 'scope_note'),
                           (self.card['feasibility'], 'method')):
            old = obj[field]; obj[field] += ' changed'; self.rejected('stale', False); obj[field] = old

    def test_review_metadata_only_does_not_change_design_context(self):
        before = selection_context_sha256(self.data)
        self.card['review']['reason'] = 'A clarified synthetic rationale'; self.card['review']['reviewer'] = 'Different synthetic editor'
        self.assertEqual(selection_context_sha256(self.data), before); self.assertEqual(self.errors(False), [])

    def test_topic_selection_context_changes_sample_design_context(self):
        before = render_gate.design_context(self.data, [])
        self.card['knowledge_increment'] += ' changed'; refresh_topic_selection_fixture(self.data)
        self.assertNotEqual(render_gate.design_context(self.data, []), before)

    def test_nonfinite_selection_input_reports_error(self):
        self.card['unexpected_number'] = float('nan'); self.rejected('finite JSON', False)

    def test_real_plan_and_direct_g1_require_card(self):
        self.data['brief'].pop('topic_selection')
        errors, _ = check_episode.check(self.data, self.root, 'plan')
        self.assertTrue(any('selection card' in e for e in errors))
        self.assertTrue(any('selection card' in e for e in check_stage(self.data, self.root, 'G1')))

    def test_sample_and_full_reject_before_any_adapter_subprocess(self):
        self.card['disqualifiers'] = ['common_knowledge_only']; refresh_topic_selection_fixture(self.data)
        (self.root/'adapter.py').write_text('raise RuntimeError("must never run")')
        self.data['execution'] = {'entrypoint': {'file': 'adapter.py', 'sha256': hashlib.sha256((self.root/'adapter.py').read_bytes()).hexdigest()}}
        (self.root/'episode.json').write_text(json.dumps(self.data))
        # Only unrelated lock/baseline are isolated; actual entry/hash and selection run.
        with patch.object(render_gate, 'check_lock'), patch.object(render_gate, 'check_baseline'), patch.object(render_gate.subprocess, 'run') as child:
            for phase in ('sample', 'full'):
                code, record = render_gate.run_render(self.root/'episode.json', phase, [], phase+'.mp4', phase+'.json')
                self.assertEqual(code, 1); self.assertEqual(record['result'], 'blocked')
                self.assertTrue(any('disqualifiers' in e for e in record['preflight_errors']))
            child.assert_not_called()

    def test_cover_only_does_not_invent_topic_selection_approval(self):
        errors, _ = check_episode.check({}, self.root, 'covers')
        self.assertFalse(any('topic selection' in e for e in errors)); self.assertTrue(errors)


    def test_editorial_selection_requires_a_real_alternative(self):
        for value in (None, [], 'another topic'):
            self.card['alternatives']=value
            self.rejected('alternative')

    def test_alternative_needs_a_question_and_specific_reason(self):
        for field in ('question','not_selected_reason'):
            self.card['alternatives']=[{'question':'A different synthetic question','not_selected_reason':'Synthetic comparative editorial rationale'}]
            self.card['alternatives'][0][field]='有趣'
            self.rejected('alternative')

    def test_selected_question_cannot_be_its_own_alternative(self):
        self.card['alternatives'][0]['question']=' SYNTHETIC TOPIC QUESTION?! '
        self.rejected('distinct question')

    def test_duplicate_alternative_questions_are_rejected(self):
        self.card['alternatives']*=2
        self.rejected('distinct question')

    def test_changed_comparison_requires_selection_review(self):
        self.card['alternatives'][0]['not_selected_reason']+=' changed'
        self.rejected('stale',False)

    def test_explicit_user_topic_does_not_require_fabricated_alternatives(self):
        (self.root/'request.txt').write_text('Synthetic explicit technical teaching request.',encoding='utf-8')
        self.card.update(selection_origin='user_requested',user_request_reference='synthetic request',
            user_request_evidence={'file':'request.txt','sha256':hashlib.sha256((self.root/'request.txt').read_bytes()).hexdigest()},
            scope_reason='Explain the requested technical foundation to its specified audience')
        self.card.pop('alternatives',None)
        self.card['disqualifiers']=['specialist_only_hook']
        self.assertEqual(self.errors(),[])


if __name__ == '__main__': unittest.main()
