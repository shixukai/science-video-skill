"""Synthetic local-repair scope contracts; never actual episode acceptance."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_episode import canonical_sha256, check_topic
from stage_checks import Checks, check_stage, local_repair_scope


class LocalRepairScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.anchor = {"version": "synthetic-original-v1", "title": "Synthetic whole-system comparison", "question": "Why do two regions differ?", "intent": "compare and explain", "required_scope": [{"id": "R1", "answer_requirement": "First region mechanism"}, {"id": "R2", "answer_requirement": "Second region mechanism"}, {"id": "R3", "answer_requirement": "Comparison limits"}]}
        (self.root / "topic-anchor.json").write_text(json.dumps(self.anchor))
        sha = canonical_sha256(self.anchor)
        self.data = {"topic": {"anchor_file": "topic-anchor.json", "anchor_sha256": sha, "current": copy.deepcopy(self.anchor), "current_sha256": sha, "origin_reference": "synthetic original request", "change_approval": {"status": "not_changed"}},
                     "scope": {"kind": "local_sample", "parent_episode_id": "synthetic-parent", "chapter_id": "synthetic-chapter", "purpose": "Repair a local mechanism", "delivery_context": "Middle excerpt of the unchanged parent question", "placement": "chapter_only", "publication_ready": False},
                     "shots": [{"id": "SH1"}, {"id": "SH2"}],
                     "brief": {"audience_start": {"assumed_knowledge": ["Synthetic prior observation"]}},
                     "topic_alignment": {"topic_sha256": sha, "main_scope_ids": ["R1"], "omitted_scope_ids": ["R2", "R3"],
                       "opening": {"intent": self.anchor["intent"], "scope_ids": ["R1"], "shot_ids": ["SH1"]},
                       "ending": {"intent": self.anchor["intent"], "scope_ids": ["R1"], "shot_ids": ["SH2"]},
                       "coverage": [{"scope_id": "R1", "shot_ids": ["SH1", "SH2"], "answer_evidence": "Synthetic actual local scope only", "causal_steps": [{"id": "STEP1", "before": "Synthetic earlier state", "change": "Synthetic local change", "after": "Synthetic later state", "handoff": "Continue the parent comparison later", "shot_ids": ["SH1", "SH2"], "requires_dynamic": True, "prerequisites": [{"source": "audience_prior", "knowledge": "Synthetic prior observation"}]}]}]},
                     "qa": {"visual_frames": {"status": "pending", "animation": {"next_action": "repair_sample"}, "failures": []}}}

    def tearDown(self):
        self.tmp.cleanup()

    def topic_errors(self, stage="plan"):
        return check_topic(self.data, self.root, stage, {s["id"]: s for s in self.data["shots"]})

    def scope_errors(self):
        checks = Checks(self.data, self.root)
        checks.causal()
        return checks.errors

    def test_honest_local_repair_keeps_full_anchor_without_invented_episode_opening(self):
        self.assertTrue(local_repair_scope(self.data))
        self.assertEqual(self.topic_errors(), [])
        self.assertEqual(self.scope_errors(), [])
        self.assertEqual(self.data["topic"]["current"], self.anchor)
        self.assertNotIn("spoken_question", self.data["topic_alignment"]["opening"])

    def test_optional_actual_local_title_or_excerpt_does_not_change_parent_question(self):
        self.data["topic_alignment"]["opening"].update(title="Synthetic local object label", voiceover="Synthetic excerpt continues the earlier sentence", spoken_question="", answer_route="")
        self.assertEqual(self.topic_errors(), [])
        self.assertEqual(self.scope_errors(), [])

    def test_each_local_scope_field_is_required(self):
        for key in ("parent_episode_id", "chapter_id", "purpose", "delivery_context"):
            original = self.data["scope"][key]
            for value in (None, "", "pending", "unknown", " 待审 ", "未验", "待验", "未审", "待核"):
                self.data["scope"][key] = value
                self.assertTrue(self.topic_errors(), (key, value))
                self.assertTrue(self.scope_errors(), (key, value))
            self.data["scope"][key] = original

    def test_episode_placement_or_publication_readiness_is_not_local_repair(self):
        for key, value in (("placement", "episode_opening"), ("placement", None), ("publication_ready", True), ("publication_ready", None), ("publication_ready", 0)):
            original = self.data["scope"][key]
            self.data["scope"][key] = value
            self.assertFalse(local_repair_scope(self.data))
            self.assertTrue(self.topic_errors())
            self.assertTrue(self.scope_errors())
            self.data["scope"][key] = original

    def test_local_expand_or_missing_action_cannot_use_scope_exception(self):
        for action in ("expand", "pending", "", None):
            self.data["qa"]["visual_frames"]["animation"]["next_action"] = action
            self.assertTrue(any("repair_sample" in e for e in self.topic_errors()))
            self.assertTrue(any("repair_sample" in e for e in self.scope_errors()))

    def test_nonlocal_episode_cannot_drop_opening_or_promised_scope(self):
        self.data["scope"]["kind"] = "episode"
        self.assertFalse(local_repair_scope(self.data))
        self.assertTrue(any("spoken_question" in e for e in self.topic_errors()))
        self.assertTrue(any("necessary answer scope missing" in e for e in self.topic_errors()))
        self.assertTrue(any("all promised explanation coverage incomplete" in e for e in self.scope_errors()))

    def test_chapter_does_not_gain_the_narrow_repair_exception(self):
        self.data["scope"]["kind"] = "chapter"
        self.assertFalse(local_repair_scope(self.data))
        self.assertTrue(any("spoken_question" in e for e in self.topic_errors()))
        self.assertTrue(any("all promised explanation coverage incomplete" in e for e in self.scope_errors()))

    def test_empty_local_coverage_is_not_an_exemption(self):
        self.data["topic_alignment"]["coverage"] = []
        self.data["topic_alignment"]["omitted_scope_ids"] = ["R1", "R2", "R3"]
        self.assertTrue(self.topic_errors())
        self.assertTrue(any("nonempty" in e for e in self.scope_errors()))

    def test_scope_outside_original_anchor_rejected(self):
        self.data["topic_alignment"]["coverage"][0]["scope_id"] = "R4"
        self.data["topic_alignment"]["main_scope_ids"] = ["R4"]
        self.assertTrue(self.topic_errors())
        self.assertTrue(self.scope_errors())

    def test_duplicate_coverage_rejected(self):
        self.data["topic_alignment"]["coverage"] *= 2
        self.assertTrue(self.topic_errors())
        self.assertTrue(self.scope_errors())

    def test_missing_extra_duplicate_unknown_or_malformed_omissions_rejected(self):
        for value in ([], ["R2"], ["R2", "R3", "R1"], ["R2", "R3", "R3"], ["R2", "unknown"], None, "R2,R3", [None]):
            self.data["topic_alignment"]["omitted_scope_ids"] = value
            self.assertTrue(self.topic_errors(), value)
            self.assertTrue(self.scope_errors(), value)

    def test_empty_duplicate_unknown_or_omitted_primary_selection_rejected(self):
        for value in ([], ["R1", "R1"], ["R2"], ["R1", "R2"], ["unknown"], None, "R1", [{}]):
            self.data["topic_alignment"]["main_scope_ids"] = value
            self.assertTrue(self.topic_errors(), value)
            self.assertTrue(self.scope_errors(), value)

    def test_supplied_wrong_intent_still_rejected(self):
        for section in ("opening", "ending"):
            self.data["topic_alignment"][section]["intent"] = "unrelated new question"
            self.assertTrue(any("question type differs" in e for e in self.topic_errors()))
            self.data["topic_alignment"][section]["intent"] = self.anchor["intent"]

    def test_boundary_cannot_map_an_omitted_scope(self):
        for section in ("opening", "ending"):
            self.data["topic_alignment"][section]["scope_ids"] = ["R2"]
            self.assertTrue(any("actual covered scope" in e for e in self.topic_errors()))
            self.data["topic_alignment"][section]["scope_ids"] = ["R1"]

    def test_missing_boundary_metadata_still_rejected(self):
        for section in ("opening", "ending"):
            original = self.data["topic_alignment"].pop(section)
            self.assertTrue(self.topic_errors())
            self.data["topic_alignment"][section] = original

    def test_actual_first_and_last_shot_mapping_still_required(self):
        for section, wrong in (("opening", "SH2"), ("ending", "SH1")):
            original = self.data["topic_alignment"][section]["shot_ids"]
            self.data["topic_alignment"][section]["shot_ids"] = [wrong]
            self.assertTrue(any("actual boundary shot" in e for e in self.topic_errors()))
            self.data["topic_alignment"][section]["shot_ids"] = original

    def test_anchor_hash_mismatch_still_rejected(self):
        self.data["topic"]["anchor_sha256"] = "0" * 64
        self.assertTrue(any("original anchor hash mismatch" in e for e in self.topic_errors()))

    def test_current_scope_cannot_be_shrunk_even_with_recalculated_hash(self):
        self.data["topic"]["current"]["required_scope"] = self.data["topic"]["current"]["required_scope"][:1]
        sha = canonical_sha256(self.data["topic"]["current"])
        self.data["topic"]["current_sha256"] = self.data["topic_alignment"]["topic_sha256"] = sha
        self.data["topic_alignment"]["omitted_scope_ids"] = []
        self.assertTrue(any("explicit user request" in e for e in self.topic_errors()))

    def test_complete_local_coverage_still_cannot_deliver_an_episode(self):
        for ident in ("R2", "R3"):
            row = copy.deepcopy(self.data["topic_alignment"]["coverage"][0])
            row["scope_id"] = ident
            row["causal_steps"][0]["id"] = "STEP-" + ident
            self.data["topic_alignment"]["coverage"].append(row)
        self.data["topic_alignment"]["omitted_scope_ids"] = []
        self.assertEqual(self.topic_errors(), [])
        self.assertEqual(self.scope_errors(), [])
        self.assertTrue(any("cannot pass complete-episode delivery" in e for e in self.topic_errors("delivery")))

    def test_local_sample_cannot_pass_g4_or_later_scope_check(self):
        for gate in ("G4", "G5", "G6", "G7"):
            errors = check_stage(self.data, self.root, gate)
            self.assertTrue(any("complete candidate/quality gates require episode scope" in e for e in errors), (gate, errors))

    def test_open_failure_allows_repair_scope_but_still_blocks_expansion(self):
        self.data["qa"]["visual_frames"]["failures"] = [{"id": "synthetic-failure", "scope": "segment", "status": "open", "severity": "P2", "note": "Synthetic known scene failure"}]
        checks = Checks(self.data, self.root)
        checks.expansion_failures(False)
        self.assertEqual(checks.errors, [])
        self.assertEqual(self.scope_errors(), [])
        self.data["qa"]["visual_frames"]["animation"]["next_action"] = "expand"
        checks.expansion_failures(True)
        self.assertTrue(any("blocks expansion" in e for e in checks.errors))
        self.assertTrue(any("repair_sample" in e for e in self.scope_errors()))

    def test_g3_route_still_checks_local_action_and_known_failure(self):
        self.data["qa"]["visual_frames"].update(status="fail", failures=[{"id": "synthetic-failure", "scope": "segment", "status": "open", "note": "Synthetic known failure"}])
        self.data["qa"]["visual_frames"]["animation"]["next_action"] = "expand"
        errors = check_stage(self.data, self.root, "G3")
        self.assertTrue(any("chapter-only repair_sample" in e for e in errors), errors)
        self.assertTrue(any("blocks expansion" in e for e in errors), errors)

    def test_local_repair_does_not_sign_pending_or_failed_stage_evidence(self):
        errors = check_stage(self.data, self.root, "G3")
        self.assertFalse(any("all promised explanation coverage incomplete" in e for e in errors), errors)
        self.assertTrue(any("not passed" in e or "actual motion review required" in e for e in errors), errors)
        self.assertTrue(errors)


class UnknownSpanDiagnosticsTests(unittest.TestCase):
    """Invalid observations stay blocked without being reclassified as stillness."""
    def setUp(self):
        import subject_motion
        self.motion = subject_motion
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        media = self.root / 'synthetic.bin'
        media.write_bytes(b'synthetic bytes, not real media')
        self.sha = self.motion.sha(media)
        self.viewing = {'file': media.name, 'sha256': self.sha}
        self.data = {'workflow_version': 2, 'qa': {'gates': {'G3': {'evidence': []}}}}
        self.policy = {'screen': {}, 'max_no_progress_seconds': 3, 'max_purposeful_read_seconds': 1.6}

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, kinds, unit_ranges=None, lows=None):
        from stage_checks import context_sha256
        duration = max(end for _, end, _ in kinds)
        report = {'duration': duration, 'regions': [], 'low_motion_ranges': lows or []}
        path = self.root / 'screen.json'
        path.write_text(json.dumps(report))
        evidence = {'file': path.name, 'sha256': self.motion.sha(path)}
        self.data['qa']['gates']['G3']['evidence'] = [evidence]
        rows = [{'start': start, 'end': end, 'kind': kind, 'subject': 'Synthetic subject', 'observation': 'Synthetic classifier declaration only', 'narration_relation': 'Synthetic semantic relation', 'evidence': 'Synthetic time range only'} for start, end, kind in kinds]
        units = [{'start': a, 'end': b, 'step_ids': ['S'], 'spoken_point': 'Synthetic point', 'progression_observed': 'Synthetic observation only', 'evidence': 'Synthetic times only'} for a, b in (unit_ranges or [(0, duration)])]
        record = {'status': 'pass', 'media_sha256': self.sha, 'context_sha256': context_sha256(self.data, 'G3'), 'roi_review': 'Synthetic ROI only', 'excluded_motion_review': {k: 'Synthetic exclusion only' for k in self.motion.IGNORED}, 'screen': evidence, 'spans': rows, 'semantic_units': units, 'longest_no_progress_seconds': None, 'screen_resolutions': []}
        return record, report

    def errors(self, record, report):
        from unittest.mock import patch
        checks = Checks(self.data, self.root)
        with patch.object(self.motion, 'screen', return_value=report), patch.object(self.motion, 'validate_pacing', create=True):
            self.motion.validate(checks, record, self.viewing, 'G3', self.policy, {'S'})
        return checks.errors

    def test_unknown_kind_is_invalid_and_never_passes_or_proves_slideshow(self):
        for kind in ('unknown', 'unreviewed', 'pending', None, 'made_up', [], {}):
            record, report = self.record([(0, 8, kind)])
            errors = self.errors(record, report)
            self.assertTrue(any('invalid observed span kind' in e for e in errors), errors)
            self.assertTrue(any('unreviewed span classification' in e for e in errors), errors)
            self.assertFalse(any('slideshow' in e or 'exceeds project limit' in e or 'longest interval declaration' in e for e in errors), errors)

    def test_partly_unknown_semantic_unit_is_not_a_proven_whole_unit_slideshow(self):
        record, report = self.record([(0, 1, 'no_progress'), (1, 4, 'unknown')])
        errors = self.errors(record, report)
        self.assertTrue(any('invalid observed span kind' in e for e in errors))
        self.assertFalse(any('slideshow' in e or 'exceeds project limit' in e for e in errors), errors)

    def test_submillisecond_unknown_span_still_prevents_a_proven_slideshow_claim(self):
        record, report = self.record([(0, .5, 'no_progress'), (.5, .5005, 'unknown'), (.5005, 2, 'no_progress')])
        errors = self.errors(record, report)
        self.assertTrue(any('invalid observed span kind' in e for e in errors), errors)
        self.assertTrue(any('unreviewed span classification' in e for e in errors), errors)
        self.assertFalse(any('slideshow' in e for e in errors), errors)

    def test_unknown_does_not_join_separate_known_still_intervals(self):
        record, report = self.record([(0, 2, 'no_progress'), (2, 4, 'unknown'), (4, 6, 'no_progress')])
        errors = self.errors(record, report)
        self.assertTrue(errors)
        self.assertFalse(any('exceeds project limit' in e or 'slideshow' in e for e in errors), errors)

    def test_unknown_cannot_hide_a_separately_observed_slideshow_or_long_still_interval(self):
        record, report = self.record([(0, 4, 'no_progress'), (4, 8, 'unknown')], [(0, 4), (4, 8)])
        errors = self.errors(record, report)
        self.assertTrue(any('invalid observed span kind' in e for e in errors), errors)
        self.assertTrue(any('slideshow' in e for e in errors), errors)
        self.assertTrue(any('observed no-progression interval exceeds' in e for e in errors), errors)

    def test_known_no_progress_retains_existing_static_blockers(self):
        record, report = self.record([(0, 8, 'no_progress')])
        record['longest_no_progress_seconds'] = 8
        errors = self.errors(record, report)
        self.assertTrue(any('slideshow' in e for e in errors), errors)
        self.assertTrue(any('longest interval without effective subject progression exceeds' in e for e in errors), errors)
        self.assertFalse(any('invalid observed span kind' in e for e in errors), errors)

    def test_unknown_low_motion_resolution_stays_blocked_without_false_contradiction(self):
        record, report = self.record([(0, 8, 'unknown')], lows=[[0, 8]])
        record['screen_resolutions'] = [{'range': [0, 8], 'result': 'effective_subject_progression', 'observation': 'Synthetic unsupported declaration', 'evidence': 'Synthetic times'}]
        errors = self.errors(record, report)
        self.assertTrue(any('screen resolution overlaps unreviewed spans' in e for e in errors), errors)
        self.assertFalse(any('contradicts observed no-progression' in e for e in errors), errors)

    def test_unknown_does_not_clear_explicit_failed_review_or_failure_history(self):
        record, report = self.record([(0, 8, 'unknown')])
        record['status'] = 'fail'
        self.data['qa']['visual_frames'] = {'status': 'fail', 'failures': [{'id': 'synthetic-known-failure', 'scope': 'segment', 'status': 'open', 'note': 'Actual prior failure retained in this synthetic example'}]}
        errors = self.errors(record, report)
        self.assertTrue(any('failed/unreviewed' in e for e in errors), errors)
        checks = Checks(self.data, self.root)
        checks.expansion_failures(True)
        self.assertTrue(any('blocks expansion' in e for e in checks.errors))

    def test_pending_empty_spans_keep_explicit_object_result_failure_visible(self):
        from stage_checks import context_sha256
        record, report = self.record([(0, 8, 'no_progress')])
        self.data['workflow_version'] = 3
        record.update(status='pending', spans=[], semantic_units=[], context_sha256=context_sha256(self.data, 'G3'), object_result_review={'status': 'fail', 'media_sha256': self.sha, 'units': []})
        errors = self.errors(record, report)
        self.assertTrue(any('failed/unreviewed diagnostic' in e for e in errors), errors)
        self.assertTrue(any('complete timeline required' in e for e in errors), errors)
        self.assertFalse(any('slideshow' in e for e in errors), errors)

    def test_missing_screen_cannot_hide_explicit_object_result_failure(self):
        record, report = self.record([(0, 8, 'no_progress')])
        record.update(screen={}, object_result_review={'status': 'fail', 'media_sha256': self.sha, 'units': []})
        errors = self.errors(record, report)
        self.assertTrue(any('failed/unreviewed diagnostic' in e for e in errors), errors)
        self.assertTrue(any('screen' in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
