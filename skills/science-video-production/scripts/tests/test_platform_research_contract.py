"""Blank template integrity only; no real platform data, causal or interest validation."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_reference_system import check_platform_record_formats


class PlatformResearchContractTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.data = json.loads((root/'assets/project-ledger-template.json').read_text())
        self.snapshot = self.data['record_formats']['platform_snapshot']

    def test_empty_honest_research_template_passes_without_audience_results(self):
        self.assertEqual(check_platform_record_formats(self.data), [])
        self.assertEqual(self.data['platform_snapshots'], [])
        self.assertEqual(self.data['platform_research'], [])

    def test_missing_container_or_record_format_rejected(self):
        for value in (None, [], {}, {'record_formats': []}):
            self.assertTrue(check_platform_record_formats(value))

    def test_required_snapshot_traceability_fields_cannot_disappear(self):
        for field in ('collected_at', 'denominators', 'hours_since_publication', 'duration_s', 'traffic_and_audience', 'source_url', 'window_note', 'data_updated_display', 'update_status', 'published_display',
                      'publication_timezone', 'age_basis', 'sample_note', 'field_definitions', 'raw_display_values',
                      'field_states', 'inconsistency_note', 'page_filters', 'evidence'):
            data = copy.deepcopy(self.data); data['record_formats']['platform_snapshot'].pop(field)
            self.assertTrue(check_platform_record_formats(data), field)

    def test_default_freshness_or_zero_age_cannot_be_invented(self):
        for key, value in (('update_status', 'updated'), ('hours_since_publication', 0), ('duration_s', 0)):
            data = copy.deepcopy(self.data); data['record_formats']['platform_snapshot'][key] = value
            self.assertTrue(any('freshness or work age' in e for e in check_platform_record_formats(data)))

    def test_template_contains_no_fake_observed_values_or_definitions(self):
        for key in ('raw_display_values', 'field_states', 'field_definitions', 'field_names_as_platform_shows', 'denominators', 'traffic_and_audience'):
            data = copy.deepcopy(self.data); data['record_formats']['platform_snapshot'][key] = {'synthetic field': 0}
            self.assertTrue(any('invent observed fields' in e for e in check_platform_record_formats(data)))

    def test_blank_template_must_not_include_research_findings(self):
        self.data['platform_research'] = [{'synthetic claim': 'audience interested'}]
        self.assertTrue(any('invent research findings' in e for e in check_platform_record_formats(self.data)))

    def test_blank_template_must_not_prepopulate_platform_observations(self):
        self.data['platform_snapshots'] = [{'synthetic observation': 0}]
        self.assertTrue(any('invent observations' in e for e in check_platform_record_formats(self.data)))

    def test_blank_experiment_cannot_claim_improvement_or_measurement(self):
        for field, value in (('observation_status', 'improved'), ('observation_status', 'measured'),
                             ('result', 'synthetic retention improved'), ('result', 0)):
            data = copy.deepcopy(self.data); data['record_formats']['experiment'][field] = value
            self.assertTrue(any('unmeasured status' in e for e in check_platform_record_formats(data)))

    def test_research_has_separate_sources_ai_activity_and_hypothesis_fields(self):
        for field in ('snapshot_references', 'availability_note', 'candidate_hypotheses', 'ai_suggestions', 'activity_constraints', 'next_check'):
            data = copy.deepcopy(self.data); data['record_formats']['platform_research'].pop(field)
            self.assertTrue(check_platform_record_formats(data), field)

    def test_experiment_retains_one_variable_versions_window_metrics_limits(self):
        for field in ('primary_variable', 'baseline_version', 'candidate_version', 'comparison_window', 'metrics_to_check',
                      'traffic_and_sample_limits', 'observation_status', 'result', 'limits'):
            data = copy.deepcopy(self.data); data['record_formats']['experiment'].pop(field)
            self.assertTrue(check_platform_record_formats(data), field)

    def test_no_media_or_platform_approval_is_encoded_in_empty_template(self):
        self.assertEqual(self.data['record_formats']['experiment']['observation_status'], 'not_measured')
        self.assertIsNone(self.snapshot['hours_since_publication'])
        self.assertIsNone(self.snapshot['publication_timezone'])
        self.assertEqual(self.snapshot['update_status'], 'unknown')


if __name__ == '__main__': unittest.main()
