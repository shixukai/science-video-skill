"""Synthetic declaration/media fixtures; tests never approve actual video."""
import copy
from pathlib import Path
import unittest

from stage_fixture import gates, refresh
import presentation_checks as presentation


class PresentationBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_stage_checks
        test_stage_checks.CanonicalStageTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.d = copy.deepcopy(self.base)

    def errors(self, stage="G5"):
        return gates.check_stage(self.d, self.root, stage)

    def rejects(self, fragment, stage="G5"):
        errors = self.errors(stage)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def accept_inventory_fixture(self):
        # Simulate fresh declarations only; not an actual-media review.
        items = self.d["presentation_text"]["items"]
        for r in self.d["qa"]["presentation_text"].values():
            r["inventory_sha256"] = gates.digest(self.d["presentation_text"])
            for surface, review in r["channel_reviews"].items():
                review["item_ids"] = [x["id"] for x in items if x["surface"] == surface]
        refresh(self.d)

    def add_item(self, surface, wording, purposes, notice=None):
        item = {"id": "added", "surface": surface, "text": wording, "purposes": purposes,
                "necessity": "Synthetic declared comprehension or rights purpose", "removal_loss": "Synthetic declared loss"}
        if notice:
            item["notice_id"] = notice["id"]
            self.d["presentation_text"]["required_notices"].append(notice)
        self.d["presentation_text"]["items"].append(item)
        self.d["presentation_text"]["channels"][surface]["status"] = "present"
        self.accept_inventory_fixture()

    def test_three_forbidden_purposes_block_every_audience_surface(self):
        for surface in presentation.SURFACES:
            for purpose in presentation.FORBIDDEN:
                with self.subTest(surface=surface, purpose=purpose):
                    self.d = copy.deepcopy(self.base)
                    self.add_item(surface, "这是为了我们的制作流程方便", [purpose])
                    self.rejects("material defects/internal QA/production excuses", "G1")

    def test_mixed_allowed_purpose_cannot_hide_production_excuse(self):
        self.add_item("frame", "暂且采用此种表现", ["mechanism", "production_excuse"])
        self.rejects("production excuses", "G1")

    def test_paraphrased_material_and_qa_excuses_are_screened_even_if_misclassified(self):
        for wording in ("原视频无音轨；不作飞行声音比较", "素材没有声音", "本片验收通过", "模型不支持这个表现", "制作受限只能这样展示"):
            with self.subTest(wording=wording):
                self.d = copy.deepcopy(self.base)
                self.add_item("frame", wording, ["mechanism"])
                self.rejects("production/material-defect cue", "G1")

    def test_protected_attribution_license_ai_and_scientific_conditions_are_allowed(self):
        examples = {"attribution": "Cheney 等 (2020) · CC BY 4.0", "license": "CC BY 4.0", "ai_simulation": "机制示意，非按比例", "scientific_condition": "条件：空气中、常温"}
        for purpose, wording in examples.items():
            with self.subTest(purpose=purpose):
                self.d = copy.deepcopy(self.base)
                notice = {"id": "N", "purpose": purpose, "text": wording, "basis": "Synthetic notice obligation only"}
                self.add_item("frame", wording, [purpose], notice)
                self.assertEqual(self.errors(), [])

    def test_scientific_model_limit_keeps_bound_scientific_basis(self):
        wording = "模型不支持超音速流动；适用范围：低速气流"
        notice = {"id": "N", "purpose": "scientific_condition", "text": wording, "basis": "科学模型的适用条件，不是制作工具限制"}
        self.add_item("frame", wording, ["scientific_condition"], notice)
        self.assertEqual(self.errors(), [])
        self.d = copy.deepcopy(self.base)
        wording = "模型不支持所以用此镜头"
        notice["text"] = wording
        self.add_item("frame", wording, ["scientific_condition"], notice)
        self.rejects("production/material-defect cue", "G1")

    def test_protected_label_does_not_exempt_material_or_internal_qa_text(self):
        for wording in ("原视频无音轨；不作飞行声音比较", "本片验收通过", "制作受限只能这样展示"):
            self.d = copy.deepcopy(self.base)
            notice = {"id": "N", "purpose": "scientific_condition", "text": wording, "basis": "Synthetic false scientific declaration"}
            self.add_item("frame", wording, ["scientific_condition"], notice)
            self.rejects("production/material-defect cue", "G1")

    def test_required_notice_cannot_be_removed_or_renamed(self):
        notice = {"id": "N", "purpose": "license", "text": "CC BY 4.0", "basis": "Synthetic known asset license"}
        self.add_item("frame", notice["text"], ["license"], notice)
        self.d["assets"][0]["required_notice_ids"] = ["N"]
        self.d["presentation_text"]["items"] = [x for x in self.d["presentation_text"]["items"] if x["id"] != "added"]
        self.accept_inventory_fixture(); self.rejects("required attribution/license/AI/scientific condition removed", "G1")
        self.d["presentation_text"]["required_notices"] = []
        self.accept_inventory_fixture(); self.rejects("used asset required notice unresolved", "G1")

    def test_formal_script_cannot_omit_unclassified_text(self):
        path = self.root/self.d["narration"]["script_file"]
        old = path.read_bytes()
        try:
            path.write_text("Synthetic test script only\nA second unclassified statement")
            self.d["narration"]["script_sha256"] = gates.file_digest(path)
            for r in self.d["qa"]["presentation_text"].values(): r["sources"]["voiceover"]["sha256"] = gates.file_digest(path)
            refresh(self.d); self.rejects("formal text is not completely classified")
        finally: path.write_bytes(old)

    def test_caption_metadata_is_not_audience_text(self):
        self.assertEqual(presentation.normalized(presentation.caption_body("1\n00:00:00,000 --> 00:00:01,000\n科学条件\n", ".srt")), "科学条件")
        self.assertEqual(presentation.caption_body("1\n00:00:00,000 --> 00:00:01,000\n2020\n", ".srt"), "2020")
        self.assertEqual(presentation.caption_body("WEBVTT\n\n1\n00:00:00.000 --> 00:00:01.000\n500\n", ".vtt"), "500")
        self.assertEqual(presentation.caption_body("2020\n500\n", ".txt"), "2020\n500\n")
        self.assertEqual(presentation.caption_body("[Events]\nDialogue: 0,0,1,Default,,0,0,0,,{\\b1}机制\\N示意", ".ass"), "机制\n示意")

    def test_actual_inspection_and_current_inventory_are_required(self):
        self.d["qa"]["presentation_text"]["G3"]["actual_media_inspected"] = False
        self.rejects("actual media text/voice inspection required", "G3")
        self.d = copy.deepcopy(self.base)
        self.d["qa"]["presentation_text"]["G5"]["inventory_sha256"] = "0"*64
        self.rejects("stale classified inventory")

    def test_caption_scientific_inequalities_survive_style_markup(self):
        condition = "条件：速度 v < 500 m/s；温度 T > 300 K"
        self.assertEqual(presentation.caption_body("1\n00:00:00,000 --> 00:00:01,000\n"+condition+"\n", ".srt"), condition)
        self.assertEqual(presentation.caption_body("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\n<v Speaker><b>条件：</b><c.unit>v &lt; 500</c> <00:00:00.500>T &gt; 300\n", ".vtt"), "条件：v < 500 T > 300")

    def test_frame_caption_voiceover_and_both_cover_checks_are_required(self):
        self.d["qa"]["presentation_text"]["G5"]["channel_reviews"].pop("cover")
        self.rejects("complete applicable surface review required")
        self.d = copy.deepcopy(self.base); self.d["qa"]["presentation_text"]["G5"]["cover_files"] = []
        self.rejects("both actual cover versions required")

    def test_same_serena_seed_and_asr_cannot_replace_continuous_listening(self):
        self.d["narration"]["speaker"] = "Serena"; self.d["narration"]["seed"] = 42
        refresh(self.d)
        r = self.d["qa"]["audio"]["continuity"]["G5"]
        r.update(actually_heard=False, method="ASR_and_decoding")
        self.rejects("same speaker/seed/ASR/decoding is insufficient")

    def test_tone_or_rate_failure_cannot_be_offset(self):
        for criterion in presentation.VOICE_CRITERIA:
            self.d = copy.deepcopy(self.base)
            self.d["qa"]["audio"]["continuity"]["G5"]["criteria"][criterion]["status"] = "fail"
            self.rejects(criterion+" failure cannot be offset")

    def test_complete_range_and_cross_shot_join_evidence_are_required(self):
        self.d["qa"]["audio"]["continuity"]["G2"]["ranges"] = [[0, .5]]
        self.rejects("complete reviewed clip/export", "G2")
        self.d = copy.deepcopy(self.base)
        self.d["qa"]["audio"]["continuity"]["G5"]["transitions"] = []
        self.rejects("cross-shot continuous listening coverage incomplete")
        self.d = copy.deepcopy(self.base)
        self.d["qa"]["audio"]["continuity"]["G3"]["transitions"][0]["listen_range"] = [.6, 1]
        self.rejects("must actually straddle", "G3")

    def test_self_reported_join_times_cannot_replace_actual_shot_boundaries(self):
        for gate in ("G2", "G3", "G5"):
            self.d = copy.deepcopy(self.base)
            for i, (start, end) in enumerate(((0, .2), (.2, .8), (.8, 1))):
                self.d["shots"][i]["shotbook"].update(start=start, end=end)
            self.d["qa"]["visual_frames"]["animation"]["shot_intervals"] = [{"shot_id":s["id"], "start":s["shotbook"]["start"], "end":s["shotbook"]["end"]} for s in self.d["shots"]]
            for row in self.d["qa"]["audio"]["continuity"][gate]["transitions"]:
                row.update(at=.5, listen_range=[.4, .6])
            refresh(self.d)
            self.rejects("must match actual current-media shot boundary", gate)

    def test_representative_clip_uses_its_own_bound_shot_timeline(self):
        self.d["qa"]["visual_frames"]["animation"]["shot_intervals"] = []
        refresh(self.d)
        self.rejects("shot timeline must cover complete", "G3")
        self.d = copy.deepcopy(self.base)
        self.d["qa"]["visual_frames"]["animation"]["shot_intervals"][0]["end"] = .1
        self.rejects("stale context", "G3")

    def test_unverified_segmentation_context_handoff_is_rejected(self):
        self.d["narration"]["delivery_plan"]["mode"] = "context_preserving_segments"
        refresh(self.d)
        self.rejects("segmentation capability_evidence required")

    def test_verified_segmentation_with_continuous_review_can_pass(self):
        plan = self.d["narration"]["delivery_plan"]
        plan.update(mode="context_preserving_segments", technical_limit="Synthetic verified length limit", verified_method="Synthetic existing method", capability_evidence="Synthetic run receipt only", context_handoff="Synthetic narrative chain")
        ref = {"file": "script.txt", "sha256": self.d["narration"]["script_sha256"]}
        audio = {"file": self.d["deliverables"]["video"], "sha256": self.d["narration"]["audio_sha256"]}
        plan["segments"] = [{"id": "A", "script": ref, "audio": audio, "context_before": "start", "context_after": "shared premise", "handoff_evidence": "Synthetic handoff receipt"}, {"id": "B", "script": ref, "audio": audio, "context_before": "shared premise", "context_after": "conclusion", "handoff_evidence": "Synthetic handoff receipt"}]
        refresh(self.d); self.assertEqual(self.errors(), [])
        plan["segments"][1]["context_before"] = "unrelated restart"
        refresh(self.d); self.rejects("segment narrative context handoff mismatch")

    def test_user_tone_feedback_stays_failed_until_full_current_review(self):
        self.d["qa"]["audio"]["status"] = "fail"
        self.d["qa"]["visual_frames"]["failures"] = [{"id": "VOICE", "scope": "audio", "note": "Synthetic tone discontinuity feedback, not actual user media", "status": "open"}]
        self.assertEqual(self.errors("G3"), [])
        self.rejects("known failure blocks full quality/release")
        self.d["qa"]["audio"]["status"] = "pass"
        self.rejects("unresolved failure cannot be overwritten")

    def test_unreviewed_and_malformed_voice_records_are_blocked(self):
        for value in (None, [], "pending", {"status": "pending"}):
            self.d = copy.deepcopy(self.base)
            self.d["qa"]["audio"]["continuity"]["G5"] = value
            self.rejects("voice continuity failed/unreviewed")

    def test_whole_audio_failure_cannot_be_resolved_by_local_sample(self):
        resolution = {"scope": "local_sample", "evidence": "Synthetic local sample only", "sha256": self.d["qa"]["reviewed_sha256"]["video"], "context_sha256": gates.context_sha256(self.d, "G5")}
        self.d["qa"]["visual_frames"]["failures"] = [{"id": "VOICE", "scope": "audio", "note": "Synthetic entire-episode discontinuity", "status": "resolved", "resolution": resolution}]
        self.rejects("local approval cannot resolve whole-episode failure")
        resolution["scope"] = "full_episode"
        self.assertEqual(self.errors(), [])
        self.d["qa"]["audio"]["continuity"]["G5"]["actually_heard"] = False
        self.rejects("actual complete continuous listening required")


if __name__ == "__main__":
    unittest.main()
