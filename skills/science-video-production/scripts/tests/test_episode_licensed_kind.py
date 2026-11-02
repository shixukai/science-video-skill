"""Regression coverage for the episode checker and native model origin guard.

Run as a standalone test with SCIENCE_SKILL_TEST_BASE pointing at the one
installed global Skill, or place in scripts/tests of a maintenance checkout.
Synthetic triangle data and terms are not actual rights or media approval.
"""
import os
from pathlib import Path
import sys
import unittest

base = os.environ.get('SCIENCE_SKILL_TEST_BASE')
scripts = Path(base) / 'scripts' if base else Path(__file__).resolve().parents[1]
sys.path.insert(0, str(scripts))
sys.path.insert(0, str(scripts / 'tests'))
import check_episode
import test_licensed_3d_models as fixture


class EpisodeLicensedKindTests(fixture.LicensedModelTests):
    def test_base_checker_accepts_native_model_kind_and_guard_still_validates(self):
        errors, _ = check_episode.check(self.data, self.root, 'plan')
        self.assertNotIn('MODEL: unknown asset kind', errors)
        self.assertEqual(self.errors(actual=False), [])
        self.assertEqual(self.errors(actual=True), [])

    def test_missing_license_is_still_rejected(self):
        self.model['origin'].pop('license_evidence')
        self.blocked('license evidence', actual=False)

    def test_finished_video_cannot_be_laundered_as_native_model(self):
        self.model.update(self.ref('fake-model.mp4', 'Synthetic file; not real media.'))
        self.output['origin']['inputs'] = [self.parent_ref()]
        self.blocked('native model_3d source', actual=False)


if __name__ == '__main__':
    unittest.main()
