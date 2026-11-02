"""Synthetic provenance bindings only; no actual license, import or visual pass."""
import copy
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]
BASE = Path(os.environ.get('SCIENCE_SKILL_TEST_BASE', str(SCRIPTS.parent)))
sys.path.insert(0, str(BASE / 'scripts'))
sys.path.insert(0, str(SCRIPTS))
import origin_guard as guard
from stage_checks import Checks, digest


class LicensedModelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.note = self.ref('software-fixture.txt', 'SYNTHETIC SOFTWARE TEST. No real license/import/review asserted.')
        native = self.ref('triangle.obj', 'v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
        self.model = {'id': 'MODEL', 'kind': 'model_3d', **native,
            'source': 'https://example.invalid/models/synthetic-triangle', 'creator': 'Synthetic fixture author',
            'rights': {'status': 'cleared', 'license_name': 'Synthetic software-test terms',
                       'scope': 'Software test declaration only; not real permission.'},
            'usage': 'licensed_model_reuse', 'scientific_review': {'status': 'not_applicable', 'reason': 'Software triangle, no scientific claim.'},
            'origin': {'category': 'licensed_3d_model', 'method': 'Import fixture model data',
                       'entry_version': 'synthetic-model-v1', 'inputs': [], 'license_evidence': dict(self.note),
                       'dependencies': [], 'review': dict(self.note)}}
        self.output = {'id': 'OUT', 'kind': 'simulation', **self.ref('render-output.txt', 'Synthetic render declaration only.'),
            'rights': {'status': 'cleared'}, 'disclosure': 'Synthetic test, not an actual render.',
            'origin': {'category': 'self_rendered', 'method': 'Synthetic local scene/render evidence', 'entry_version': 'fixture-v1',
                       'design': dict(self.note), 'entrypoint': dict(self.note), 'review': dict(self.note),
                       'frames': [dict(self.note)], 'inputs': [self.parent_ref()]}}
        self.output['origin']['output'] = {k: self.output[k] for k in ('file', 'sha256')}
        self.output.update(usage='episode_original', source_file=self.note['file'], source_sha256=self.note['sha256'],
                           scientific_review={'status': 'not_applicable', 'reason': 'Synthetic render fixture, no scientific claim.'})
        self.data = {'origin_contract': {'mode': 'self_created_visuals'},
            'shots': [{'id': 'SH1', 'asset_ids': ['OUT'], 'shotbook': {'realism': {'medium': 'three_d'},
                'origin': {'planned_method': 'self_rendered', 'entry_version': 'fixture-v1',
                           'design': dict(self.note), 'entrypoint': dict(self.note)}}}],
            'assets': [self.output, self.model]}

    def ref(self, name, text):
        p = self.root / name; p.write_text(text, encoding='utf-8')
        return {'file': name, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}

    def parent_ref(self):
        return {'asset_id': 'MODEL', **{k: self.model[k] for k in ('file', 'sha256')},
                'origin_category': 'licensed_3d_model'}

    def errors(self, actual=True, final=False):
        checks = Checks(self.data, self.root)
        if actual: guard.validate_origin(checks, ['SH1'], final=final)
        else: guard.validate_origin_plan(checks, ['SH1'], final=final, representative=False)
        return checks.errors

    def blocked(self, fragment, actual=True):
        errors = self.errors(actual=actual)
        self.assertTrue(any(fragment in e for e in errors), errors)

    def test_native_model_can_feed_own_render_without_fake_self_creation_fields(self):
        self.assertEqual(self.errors(), [])
        self.assertNotIn('entrypoint', self.model['origin'])
        self.assertNotIn('output', self.model['origin'])
        self.assertNotIn('frames', self.model['origin'])

    def test_plan_does_not_require_future_render_output(self):
        for field in ('design', 'entrypoint', 'output', 'frames', 'review'):
            self.output['origin'].pop(field, None)
        self.assertEqual(self.errors(actual=False), [])
        self.blocked('actual frame evidence required')

    def test_missing_license_source_creator_or_scope_blocks(self):
        original = copy.deepcopy(self.model)
        for field in ('source', 'creator', 'license_name', 'scope', 'status', 'license_evidence'):
            with self.subTest(field=field):
                self.model.clear(); self.model.update(copy.deepcopy(original))
                if field in ('source', 'creator'): self.model[field] = ''
                elif field == 'license_evidence': self.model['origin'].pop(field)
                else: self.model['rights'][field] = 'pending' if field == 'status' else ''
                self.assertTrue(self.errors(actual=False))

    def test_license_bytes_and_actual_model_bytes_are_verified(self):
        (self.root / self.note['file']).write_text('Changed evidence', encoding='utf-8')
        self.blocked('hash stale')
        self.note = self.ref('software-fixture.txt', 'SYNTHETIC SOFTWARE TEST. No real license/import/review asserted.')
        (self.root / self.model['file']).write_text('Changed native geometry', encoding='utf-8')
        self.blocked('hash stale')

    def test_model_and_dependency_formats_cannot_be_finished_video_or_stills(self):
        for suffix in ('.mp4', '.mov', '.png', '.jpg', '.html', '.zip'):
            with self.subTest(suffix=suffix):
                self.model.update(self.ref('wrong' + suffix, 'Synthetic wrong type'))
                self.output['origin']['inputs'] = [self.parent_ref()]
                self.blocked('native model_3d source')

    def test_upstream_model_blocked_expired_or_failed_states_block_video_and_cover(self):
        original = copy.deepcopy(self.model)
        for field, value, fragment in (
                ('catalog', {'stage': 'blocked'}, 'blocked/deprecated model'),
                ('rights', {**self.model['rights'], 'expires_on': '2000-01-01'}, 'rights expired'),
                ('science', {'status': 'fail'}, 'explicit science/approval/rights failure')):
            with self.subTest(field=field):
                self.model.clear(); self.model.update(copy.deepcopy(original)); self.model[field] = value
                self.blocked(fragment)
                checks = Checks(self.data, self.root); checks.asset_catalog([], False)
                self.assertTrue(any('MODEL' in e for e in checks.errors), checks.errors)
                cover = copy.deepcopy(self.data)
                cover.update(delivery_scope='release_package', requested_cover_keys=['cover_3_4'],
                             deliverables={'cover_3_4': self.output['file']}, deliverable_asset_ids={'cover_3_4': ['OUT']})
                checks = Checks(cover, self.root); guard.validate_cover_origins(checks)
                self.assertTrue(any(fragment in e for e in checks.errors), checks.errors)

    def test_known_research_photo_cannot_enter_as_bundled_material_map(self):
        image = self.ref('research-photo.png', 'Synthetic known reference photo bytes')
        self.data['assets'].append({'id': 'PHOTO', 'kind': 'real_observation', **image,
                                    'origin': {'category': 'third_party_reference'}})
        self.model['origin']['dependencies'] = [image]
        self.blocked('cannot launder it as a texture')
        self.data.update(delivery_scope='release_package', requested_cover_keys=['cover_3_4'],
                         deliverables={'cover_3_4': self.output['file']}, deliverable_asset_ids={'cover_3_4': ['OUT']})
        checks = Checks(self.data, self.root); guard.validate_cover_origins(checks)
        self.assertTrue(any('cannot launder it as a texture' in e for e in checks.errors), checks.errors)

    def test_bundled_dependency_must_be_declared_current_data_or_material(self):
        texture = self.ref('material.png', 'Synthetic dependency bytes only; no image review.')
        self.model['origin']['dependencies'] = [texture]
        self.assertEqual(self.errors(), [])
        (self.root / texture['file']).write_text('Changed dependency', encoding='utf-8')
        self.blocked('hash stale')
        self.model['origin']['dependencies'] = [self.ref('promotional.mp4', 'Synthetic prohibited dependency')]
        self.blocked('dependency must be model data/material/texture')
        self.model['origin'].pop('dependencies')
        self.blocked('explicit bundled dependency inventory')

    def test_known_footage_bytes_cannot_be_relabelled_as_native_model(self):
        known = {'id': 'KNOWN', 'kind': 'real_observation', **self.model,
                 'file': 'old-video.mp4', 'origin': {'category': 'third_party_reference'}}
        known.update(id='KNOWN', kind='real_observation')
        self.data['assets'].append(known)
        self.blocked('bytes also declared third-party reference')

    def test_native_model_research_history_is_preserved_on_permitted_adoption(self):
        history = copy.deepcopy(self.model)
        history.update(id='RESEARCH'); history['origin'] = {'category': 'third_party_reference'}
        self.data['assets'].append(history)
        self.assertEqual(self.errors(), [])
        self.assertEqual(history['origin']['category'], 'third_party_reference')

    def test_license_or_model_input_labels_do_not_admit_third_party_footage_ancestors(self):
        paper = {'id': 'PAPER', 'kind': 'real_observation', **self.ref('paper.mp4', 'Synthetic prohibited footage'),
                 'origin': {'category': 'third_party_reference', 'method': 'Existing external film', 'entry_version': 'fixture', 'inputs': []}}
        self.data['assets'].append(paper)
        self.model['origin']['inputs'] = [{'asset_id': 'PAPER', 'file': paper['file'], 'sha256': paper['sha256'],
                                         'origin_category': 'third_party_reference'}]
        self.blocked('third-party or unclassified visual input')

    def test_model_use_fit_and_actual_review_cannot_be_fabricated_by_category(self):
        self.model['scientific_review']['status'] = 'pending'
        self.blocked('geometry/use-fit review')
        self.model['scientific_review']['status'] = 'not_applicable'
        self.model['origin'].pop('review')
        self.blocked('model review')

    def test_model_license_creator_and_dependency_context_is_frozen(self):
        initial = digest(guard.context_assets(self.data, ['SH1']))
        self.model['rights']['scope'] = 'Changed license use scope'
        self.assertNotEqual(initial, digest(guard.context_assets(self.data, ['SH1'])))
        initial = digest(guard.context_assets(self.data, ['SH1']))
        self.model['creator'] = 'Different claimed creator'
        self.assertNotEqual(initial, digest(guard.context_assets(self.data, ['SH1'])))

    def test_model_ancestors_are_checked_for_final_and_cover_outputs(self):
        self.data['deliverable_asset_ids'] = {'video': ['OUT']}
        self.assertEqual(self.errors(final=True), [])
        self.data.update(delivery_scope='release_package', requested_cover_keys=['cover_3_4'],
                         deliverables={'cover_3_4': self.output['file']}, deliverable_asset_ids={'cover_3_4': ['OUT']})
        checks = Checks(self.data, self.root); guard.validate_cover_origins(checks)
        self.assertEqual(checks.errors, [])

    def test_single_use_native_model_does_not_require_fake_original_or_catalog_record(self):
        data = copy.deepcopy(self.data); data['shots'][0]['asset_ids'] = ['MODEL']
        data['assets'] = [copy.deepcopy(self.model)]
        checks = Checks(data, self.root); checks.asset_catalog([], False)
        self.assertEqual(checks.errors, [])
        data['assets'][0]['usage'] = 'episode_original'
        checks = Checks(data, self.root); checks.asset_catalog([], False)
        self.assertTrue(any('licensed model reuse scope required' in e for e in checks.errors), checks.errors)

    def test_execution_snapshot_contains_native_model_license_and_bundled_inputs(self):
        import render_gate
        texture = self.ref('material.png', 'Synthetic dependency only')
        self.model['origin']['dependencies'] = [texture]
        checks = Checks(self.data, self.root)
        snapshot = render_gate.input_snapshot(checks, ['SH1'])
        # The wrapper hashes these file paths in addition to ordinary outputs.
        encoded = str(snapshot)
        for ref in (self.model, self.note, texture):
            self.assertIn(ref['file'], encoded)


if __name__ == '__main__': unittest.main()
