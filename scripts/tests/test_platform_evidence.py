"""Synthetic evidence regression, not platform or audiovisual validation."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_evidence import align_observed_times, summarize_comments, summarize_media_observations


class PlatformEvidenceTests(unittest.TestCase):
    def test_unequal_grids_use_times_not_rows(self):
        rows = align_observed_times({"short": [{"time_s": 1, "value": 80}, {"time_s": 2, "value": 70}],
                                     "long": [{"time_s": 2, "value": 60}, {"time_s": 4, "value": 40}]})
        self.assertEqual([r["time_s"] for r in rows], [1, 2, 4])
        self.assertIsNone(rows[0]["values"]["long"])
        self.assertEqual(rows[1]["values"], {"short": 70, "long": 60})
        self.assertFalse(rows[0]["observed"]["long"])

    def test_observed_null_is_not_absent_or_zero(self):
        row = align_observed_times({"a": [{"time_s": 2, "value": None}], "b": []})[0]
        self.assertEqual(row["values"], {"a": None, "b": None})
        self.assertEqual(row["observed"], {"a": True, "b": False})

    def test_ambiguous_or_invalid_times_rejected(self):
        for value in (-1, True, float("nan"), float("inf"), "2"):
            with self.assertRaises(ValueError): align_observed_times({"a": [{"time_s": value, "value": 1}]})
        with self.assertRaises(ValueError):
            align_observed_times({"a": [{"time_s": 2, "value": 1}, {"time_s": 2, "value": 2}]})

    def test_comments_are_not_independent_votes(self):
        comments = [{"id": "root", "parent_id": None, "author_id": "viewer"},
                    {"id": "r1", "parent_id": "root", "author_id": "owner"},
                    {"id": "r2", "parent_id": "root", "author_id": "viewer"}]
        report = summarize_comments(comments + comments[:1], "owner")
        self.assertEqual(report["retrieved_unique_comments"], 3)
        self.assertEqual(report["retrieved_root_threads"], 1)
        self.assertEqual(report["retrieved_replies"], 2)
        self.assertEqual(report["distinct_non_owner_commenters"], 1)
        self.assertEqual(report["owner_reply_count"], 1)
        self.assertEqual(report["coverage"], "partial_or_unknown")
        self.assertEqual(report["audience_consensus"], "not_inferred")

    def test_unknown_owner_and_author_remain_unknown(self):
        report = summarize_comments([{"id": "a"}])
        self.assertIsNone(report["distinct_non_owner_commenters"])
        self.assertIsNone(report["owner_reply_count"])
        self.assertEqual(report["unknown_author_records"], 1)

    def test_conflicting_comment_snapshot_rejected(self):
        with self.assertRaises(ValueError): summarize_comments([{"id": "a", "author_id": "x"}, {"id": "a", "author_id": "y"}])
        with self.assertRaises(ValueError): summarize_comments([{}])

    def test_missing_or_empty_parent_is_unknown_not_a_root_or_reply(self):
        result = summarize_comments([{"id": "a"}, {"id": "b", "parent_id": ""}])
        self.assertEqual(result["unknown_relationship_records"], 2)
        self.assertEqual(result["retrieved_root_threads"], 0)
        self.assertEqual(result["retrieved_replies"], 0)
        with self.assertRaises(ValueError):
            summarize_comments([{"id": "a"}, {"id": "a", "parent_id": None}])
        with self.assertRaises(ValueError): summarize_comments([{"id": "a", "parent_id": False}])
        with self.assertRaises(ValueError): summarize_comments([{"id": "a", "author_id": []}])

    def test_empty_observations_not_fabricated(self):
        self.assertEqual(align_observed_times({}), [])
        self.assertEqual(summarize_comments([], complete="yes")["coverage"], "partial_or_unknown")


    def test_description_correction_does_not_verify_media(self):
        result = summarize_media_observations("edit-b", [
            {"version": "edit-b", "surface": "publication_text", "observation": "description changed"},
            {"version": "edit-b", "surface": "captions", "observation": "earlier wording visible", "start_s": 4, "end_s": 4}])
        self.assertEqual(result["surfaces"]["narration"]["coverage"], "unknown")
        self.assertEqual(result["scientific_correctness"], "not_assessed")
        self.assertEqual(result["correction_verification"], "not_assessed")
        self.assertEqual(len(result["surfaces"]["captions"]["observations"]), 1)

    def test_visible_caption_without_native_track_is_still_observation(self):
        result = summarize_media_observations("v1", [{"version": "v1", "surface": "captions",
            "observation": "burned-in subtitle visible; native track list empty", "start_s": 3, "end_s": 3}])
        self.assertEqual(result["surfaces"]["captions"]["coverage"], "observed_intervals_only")
        self.assertEqual(result["surfaces"]["narration"]["coverage"], "unknown")

    def test_sampled_frames_never_become_continuous_review(self):
        rows = [{"version": "v1", "surface": "captions", "observation": "sample text",
                 "start_s": t, "end_s": t} for t in (1, 4, 9)]
        result = summarize_media_observations("v1", rows)
        self.assertEqual(result["continuous_audiovisual_review"], "not_assessed")
        self.assertEqual([r["start_s"] for r in result["surfaces"]["captions"]["observations"]], [1, 4, 9])

    def test_other_versions_cannot_supply_current_evidence(self):
        rows = [{"version": "old", "surface": s, "observation": "reviewed", "start_s": 0, "end_s": 10}
                for s in ("publication_text", "captions", "narration")]
        result = summarize_media_observations("new", rows)
        self.assertEqual(result["other_version_records"], 3)
        self.assertTrue(all(r["coverage"] == "unknown" for r in result["surfaces"].values()))

    def test_observation_identity_and_intervals_required(self):
        with self.assertRaises(ValueError): summarize_media_observations("", [])
        base = {"version": "v", "surface": "captions", "observation": "text", "start_s": 1, "end_s": 2}
        for field, value in (("version", ""), ("surface", "native_tracks"), ("observation", ""),
                             ("start_s", True), ("end_s", float("nan")), ("end_s", 0)):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                summarize_media_observations("v", [dict(base, **{field: value})])


if __name__ == "__main__": unittest.main()
