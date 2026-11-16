"""Synthetic evidence regression, not platform or audiovisual validation."""
import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from platform_evidence import align_observed_times, summarize_comments


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


if __name__ == "__main__": unittest.main()
