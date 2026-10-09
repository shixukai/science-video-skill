"""Synthetic export regressions, never user media or real film acceptance."""
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from stage_fixture import gates
import subject_motion as motion


POLICY = json.loads((Path(gates.__file__).resolve().parents[1]/"config/production-policy.json").read_text())["subject_motion"]


class SubjectMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="synthetic-subject-motion-")
        cls.root = Path(cls.tmp.name)
        # All video and audio bytes are made here; no private footage is read.
        filters = {
            "static_voice": "color=c=white:s=128x128:r=4,drawbox=x=32:y=32:w=64:h=64:color=blue:t=fill",
            "captions_only": "color=c=white:s=128x128:r=4,drawbox=x=32:y=32:w=64:h=64:color=blue:t=fill,drawbox=x=0:y=112:w=128:h=16:color=black:t=fill:enable='lt(mod(t,2),1)'",
            "decoration_only": "color=c=white:s=128x128:r=4,drawbox=x=32:y=32:w=64:h=64:color=blue:t=fill,drawbox=x=0:y=0:w=16:h=16:color=red:t=fill:enable='lt(mod(t,2),1)'",
            "ken_burns": "color=c=white:s=128x128:r=4,drawgrid=w=24:h=24:t=4:c=blue,zoompan=z='1+on/60':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=128x128:fps=4",
            "hard_cuts": "color=c=white:s=128x128:r=4,drawbox=x=16:y=32:w=64:h=64:color=blue:t=fill:enable='lt(mod(t,2),1)',drawbox=x=48:y=32:w=64:h=64:color=blue:t=fill:enable='gte(mod(t,2),1)'",
            "dynamic": "nullsrc=s=128x128:r=4,geq=lum='if(between(X,16+8*T,40+8*T)*between(Y,32,96),200,30)':cb=128:cr=128",
            "mechanism": "nullsrc=s=128x128:r=4,geq=lum='if(between(X,16+8*T,40+8*T)*between(Y,32,96),200,if(between(X,100,120)*between(Y,32,96),100,30))':cb=128:cr=128",
            "short_read": "nullsrc=s=128x128:r=4,geq=lum='if(between(X,16+8*max(T-1,0),40+8*max(T-1,0))*between(Y,32,96),200,30)':cb=128:cr=128",
        }
        cls.reports = {}
        for name, filterspec in filters.items():
            path = cls.root/(name+".mp4")
            subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", filterspec,
                            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-t", "10",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", str(path)], check=True)
            masks = []
            if name == "captions_only":
                masks = [{"kind": "captions", "rect": [0, .875, 1, .125]}]
            if name == "decoration_only":
                masks = [{"kind": "decoration", "rect": [0, 0, .125, .125]}]
            regions = [{"start": 0, "end": 10, "subject": "synthetic mechanism rectangle",
                        "isolation_note": "Complete synthetic subject; exclude known generated overlay boxes.",
                        "roi": [0, 0, 1, 1], "masks": masks}]
            cls.reports[name] = motion.screen(path, regions, POLICY["screen"])

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def record(self, name, kind="subject_change"):
        report = copy.deepcopy(self.reports[name])
        reportfile = self.root/(name+"-screen.json")
        reportfile.write_text(json.dumps(report))
        data = {"qa": {"gates": {"G3": {"evidence": []}}}}
        viewing = {"file": name+".mp4", "sha256": report["media_sha256"]}
        record = {
            "status": "pass", "media_sha256": viewing["sha256"],
            "context_sha256": gates.context_sha256(data, "G3"),
            "roi_review": "Synthetic fixture observation: ROI includes the entire rectangle relation.",
            "excluded_motion_review": {k: "Synthetic fixture: separately inspected "+k for k in motion.IGNORED},
            "screen": {"file": reportfile.name, "sha256": motion.sha(reportfile)},
            "spans": [{"start": 0, "end": 10, "kind": kind, "subject": "test rectangle",
                       "observation": "Synthetic observed state progression" if kind in motion.ACTIVE else "Only excluded changes; subject has no progression.",
                       "narration_relation": "Synthetic spoken explanation fixture", "evidence": "synthetic.mp4 0–10s"}],
            "semantic_units": [{"start": 0, "end": 10, "step_ids": ["S"], "spoken_point": "Synthetic complete spoken point",
                                "progression_observed": "Fixture comparison only", "evidence": "synthetic.mp4 0–10s"}],
            "longest_no_progress_seconds": 0 if kind in motion.ACTIVE else 10,
            "screen_resolutions": [],
        }
        data["qa"]["gates"]["G3"]["evidence"] = [record["screen"]]
        return data, viewing, record

    def errors(self, data, viewing, record):
        checks = gates.Checks(data, self.root)
        motion.validate(checks, record, viewing, "G3", POLICY, {"S"})
        return checks.errors

    def test_ten_seconds_static_with_audio_is_rejected(self):
        self.assertEqual(self.reports["static_voice"]["longest_low_motion_seconds"], 10)
        d, v, r = self.record("static_voice", "no_progress")
        errors = self.errors(d, v, r)
        self.assertTrue(any("exceeds project limit" in e for e in errors), errors)
        self.assertTrue(any("complete spoken semantic unit is a slideshow" in e for e in errors), errors)
        self.assertTrue(any("unresolved low-motion" in e for e in errors), errors)

    def test_subtitles_and_decoration_cannot_hide_static_subject(self):
        for name in ("captions_only", "decoration_only"):
            with self.subTest(name=name):
                self.assertEqual(self.reports[name]["longest_low_motion_seconds"], 10)
                d, v, r = self.record(name, "no_progress")
                self.assertTrue(self.errors(d, v, r))

    def test_ken_burns_and_frequent_hard_cuts_fail_semantic_review(self):
        # Pixel differences can pass while the subject never demonstrates a process.
        for name in ("ken_burns", "hard_cuts"):
            with self.subTest(name=name):
                self.assertLess(self.reports[name]["longest_low_motion_seconds"], 3)
                d, v, r = self.record(name, "no_progress")
                self.assertTrue(any("slideshow" in e for e in self.errors(d, v, r)))

    def test_dynamic_source_and_mechanism_progression_can_pass(self):
        # Authenticity/rights are separate existing checks, not established here.
        for name, kind in (("dynamic", "authentic_motion"), ("mechanism", "subject_change")):
            with self.subTest(name=name):
                d, v, r = self.record(name, kind)
                self.assertEqual(self.errors(d, v, r), [])

    def test_purposeful_short_read_then_progression_can_pass(self):
        d, v, r = self.record("short_read")
        pause = copy.deepcopy(r["spans"][0])
        pause.update(end=1, kind="purposeful_read", purpose="Locate initial rectangle before it moves.",
                     resume_evidence="Same subject begins its relation demonstration at 1s.")
        r["spans"][0]["start"] = 1
        r["spans"].insert(0, pause)
        r["longest_no_progress_seconds"] = 1
        self.assertEqual(self.errors(d, v, r), [])

    def test_short_read_cannot_exempt_whole_semantic_unit(self):
        d, v, r = self.record("short_read")
        pause = copy.deepcopy(r["spans"][0])
        pause.update(end=1, kind="purposeful_read", purpose="Synthetic read", resume_evidence="Synthetic resumption")
        r["spans"][0]["start"] = 1
        r["spans"].insert(0, pause)
        r["longest_no_progress_seconds"] = 1
        first = copy.deepcopy(r["semantic_units"][0]); first["end"] = 1
        r["semantic_units"][0]["start"] = 1
        r["semantic_units"].insert(0, first)
        self.assertTrue(any("slideshow" in e for e in self.errors(d, v, r)))

    def test_split_static_spans_do_not_reset_clock(self):
        d, v, r = self.record("hard_cuts", "no_progress")
        span = r["spans"][0]
        r["spans"] = [dict(span, start=i, end=i+1) for i in range(10)]
        self.assertTrue(any("exceeds project limit" in e for e in self.errors(d, v, r)))

    def test_roi_region_changes_do_not_reset_static_screen(self):
        p = self.root/"static_voice.mp4"
        original = self.reports["static_voice"]["regions"][0]
        # Frequent region selection changes must not bypass the candidate limit.
        report = motion.screen(p, [dict(original, start=i, end=i+1) for i in range(10)], POLICY["screen"])
        self.assertEqual(report["low_motion_ranges"], [[0, 10]])

    def test_read_pause_limit_and_accumulated_pause_limit(self):
        d, v, r = self.record("dynamic")
        active = r["spans"][0]
        pause = dict(active, kind="purposeful_read", start=0, end=2, purpose="Read", resume_evidence="Resume")
        r["spans"] = [pause, dict(active, start=2)]
        r["longest_no_progress_seconds"] = 2
        self.assertTrue(any("read too long" in e for e in self.errors(d, v, r)))
        r["spans"] = [dict(pause, start=i, end=i+1) for i in range(4)]+[dict(active, start=4)]
        r["longest_no_progress_seconds"] = 4
        self.assertTrue(any("exceeds project limit" in e for e in self.errors(d, v, r)))

    def test_tampered_screen_missing_gate_evidence_and_stale_context_fail(self):
        d, v, r = self.record("dynamic")
        reportfile = self.root/r["screen"]["file"]
        report = json.loads(reportfile.read_text()); report["duration"] = 9
        reportfile.write_text(json.dumps(report)); r["screen"]["sha256"] = motion.sha(reportfile)
        self.assertTrue(any("screen stale/tampered" in e for e in self.errors(d, v, r)))
        d, v, r = self.record("dynamic"); d["qa"]["gates"]["G3"]["evidence"] = []
        self.assertTrue(any("bound in gate evidence" in e for e in self.errors(d, v, r)))
        d, v, r = self.record("dynamic"); r["context_sha256"] = "0"*64
        self.assertTrue(any("stale context" in e for e in self.errors(d, v, r)))

    def test_screen_resolution_cannot_clear_static_observation(self):
        d, v, r = self.record("static_voice", "no_progress")
        r["screen_resolutions"] = [{"range": [0, 10], "result": "effective_subject_progression",
                                    "observation": "False fixture assertion", "evidence": "Fixture"}]
        self.assertTrue(any("contradicts" in e for e in self.errors(d, v, r)))

    def test_timeline_gap_and_nonfinite_values_fail(self):
        for value in (.5, float("nan"), True, 10**1000):
            d, v, r = self.record("dynamic"); r["spans"][0]["start"] = value
            self.assertTrue(self.errors(d, v, r))

    def test_padded_unreviewed_placeholders_cannot_clear_static_screen(self):
        for placeholder in (" pending ", " TODO ", " n/a ", " 待审 "):
            with self.subTest(placeholder=placeholder):
                d, v, r = self.record("static_voice")
                r["roi_review"] = placeholder
                r["excluded_motion_review"] = dict.fromkeys(motion.IGNORED, placeholder)
                for span in r["spans"]:
                    for key in ("subject", "observation", "narration_relation", "evidence"):
                        span[key] = placeholder
                for unit in r["semantic_units"]:
                    for key in ("spoken_point", "progression_observed", "evidence"):
                        unit[key] = placeholder
                r["screen_resolutions"] = [{"range": [0, 10], "result": "effective_subject_progression",
                                            "observation": placeholder, "evidence": placeholder}]
                self.assertTrue(any("low-motion candidate needs actual" in e for e in self.errors(d, v, r)))


class MotionGateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import test_stage_checks
        test_stage_checks.CanonicalStageTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_g2_g3_g5_each_require_their_actual_motion_evidence(self):
        for gate, route in (("G2", ("shotbook",)), ("G3", ("visual_frames", "animation")), ("G5", ("visual_frames",))):
            with self.subTest(gate=gate):
                data = copy.deepcopy(self.base)
                self.assertEqual(gates.check_stage(data, self.root, gate), [])
                parent = data["qa"]
                for key in route:
                    parent = parent[key]
                parent.pop("subject_motion")
                errors = gates.check_stage(data, self.root, gate)
                self.assertTrue(any(gate+" subject motion review required" in e for e in errors), errors)

    def test_whole_semantic_static_unit_fails_below_long_interval_limit(self):
        data = copy.deepcopy(self.base)
        record = data["qa"]["visual_frames"]["animation"]["subject_motion"]
        record["spans"][0]["kind"] = "no_progress"
        record["longest_no_progress_seconds"] = 1
        errors = gates.check_stage(data, self.root, "G3")
        self.assertTrue(any("complete spoken semantic unit is a slideshow" in e for e in errors), errors)

    def test_forged_low_motion_clearance_does_not_override_no_progression(self):
        data = copy.deepcopy(self.base)
        record = data["qa"]["shotbook"]["subject_motion"]
        record["excluded_motion_review"].pop("camera_transform")
        errors = gates.check_stage(data, self.root, "G2")
        self.assertTrue(any("bypasses must be reviewed" in e for e in errors), errors)

    def test_malformed_gate_records_are_blocked_without_exception(self):
        for value in (None, [], "pending", {"evidence": None}):
            with self.subTest(value=value):
                data = copy.deepcopy(self.base)
                data["qa"]["gates"]["G2"] = value
                errors = gates.check_stage(data, self.root, "G2")
                self.assertTrue(any("screen must be bound in gate evidence" in e for e in errors), errors)


if __name__ == "__main__":
    unittest.main()
