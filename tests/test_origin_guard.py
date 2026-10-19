"""Provenance structural regressions. Synthetic fixtures do not prove authorship."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('origin_render_fixture', SCRIPTS/'tests/test_render_gate.py')
fixture = importlib.util.module_from_spec(spec); spec.loader.exec_module(fixture)
from origin_guard import validate_origin
from stage_checks import Checks
from origin_fixture import attach_origin_fixture
import render_gate

class OriginTests(unittest.TestCase):
    setUpClass = classmethod(fixture.RenderGateTests.setUpClass.__func__)
    tearDownClass = classmethod(fixture.RenderGateTests.tearDownClass.__func__)
    tearDown = fixture.RenderGateTests.tearDown
    ref = fixture.RenderGateTests.ref
    save = fixture.RenderGateTests.save
    run_sample = fixture.RenderGateTests.run_sample
    def setUp(self):
        fixture.RenderGateTests.setUp(self)
        self.data['assets'] = [{'id':'VIS', 'kind':'diagram', **self.ref('baseline.mp4')}]
        self.data['shots'][0]['asset_ids'] = ['VIS']
        attach_origin_fixture(self.data, self.root)
    def errors(self, final=False):
        c = Checks(self.data, self.root); validate_origin(c, ['SH1'], final); return c.errors
    def test_structural_only_pass(self):
        self.assertEqual(self.errors(), [])
    def test_missing_origin_blocks_actual_child(self):
        self.data['assets'][0].pop('origin')
        code, receipt = self.run_sample()
        self.assertEqual(code, 1)
        self.assertTrue(any('origin' in e for e in receipt['preflight_errors']))
        self.assertFalse((self.root/'invoked.json').exists())
    def test_cc_rights_not_original(self):
        a = self.data['assets'][0]; a['rights']={'status':'cleared','license':'CC BY 4.0'}
        a['origin']['category']='third_party_reference'
        self.assertTrue(any('third-party/CC' in e for e in self.errors()))
    def test_real_footage_cannot_relabel_self_created(self):
        self.data['assets'][0]['kind']='real_capture'
        self.assertTrue(any('verified user capture' in e for e in self.errors()))
    def test_capture_requires_authorization(self):
        a=self.data['assets'][0]; a['kind']='real_capture'; a['origin']['category']='user_capture'
        self.assertTrue(any('capture authorization' in e for e in self.errors()))
    def test_stale_origin_evidence_blocks(self):
        (self.root/'synthetic-origin.txt').write_text('Changed provenance')
        self.assertTrue(any('hash stale' in e for e in self.errors()))
    def test_output_hash_cannot_refer_to_other_original(self):
        self.data['assets'][0]['origin']['output']['sha256']='0'*64
        self.assertTrue(any('exact used asset' in e for e in self.errors()))
    def test_third_party_input_cannot_be_laundered(self):
        self.data['assets'][0]['origin']['inputs']=[{**self.ref('baseline.mp4'), 'origin_category':'third_party_reference'}]
        self.assertTrue(any('cannot become original' in e for e in self.errors()))
    def test_relabelled_cc_input_contradiction_rejected(self):
        a=copy.deepcopy(self.data['assets'][0]); a['id']='CC_INPUT'; a['origin']['category']='third_party_reference'
        self.data['assets'].append(a)
        self.data['assets'][0]['origin']['inputs']=[{**self.ref('baseline.mp4'), 'asset_id':'CC_INPUT', 'origin_category':'self_designed'}]
        self.assertTrue(any('contradicts upstream' in e for e in self.errors()))
        self.assertTrue(any('third-party/CC' in e for e in self.errors()))
    def test_missing_frames_review_and_entry_block(self):
        for key in ('frames','review','entrypoint','design','inputs','entry_version'):
            with self.subTest(key=key):
                data=copy.deepcopy(self.data); self.data['assets'][0]['origin'].pop(key)
                self.assertTrue(self.errors()); self.data=data
    def test_cover_dependency_is_checked_at_final(self):
        (self.root/'cover-source.txt').write_text('Distinct synthetic cover input')
        a=copy.deepcopy(self.data['assets'][0]); a.update(id='COVER', **self.ref('cover-source.txt')); a['origin']['output']=self.ref('cover-source.txt'); a['origin']['category']='third_party_reference'
        self.data['assets'].append(a); self.data['deliverable_asset_ids']={'cover_3_4':['COVER']}
        self.assertEqual(self.errors(), [])
        self.assertTrue(self.errors(final=True))
    def test_contract_change_invalidates_frozen_design(self):
        before=render_gate.design_context(self.data,['SH1'])
        self.data['origin_contract']['mode']='licensed_footage'
        self.assertNotEqual(before,render_gate.design_context(self.data,['SH1']))
        self.assertTrue(self.errors())
    def test_upstream_provenance_changes_invalidate_contexts(self):
        from stage_checks import context_sha256
        (self.root/'parent.txt').write_text('Distinct synthetic upstream creation')
        a=copy.deepcopy(self.data['assets'][0]); a.update(id='UP', **self.ref('parent.txt')); a['origin']['output']=self.ref('parent.txt')
        self.data['assets'].append(a)
        self.data['assets'][0]['origin']['inputs']=[{**self.ref('parent.txt'), 'asset_id':'UP', 'origin_category':'self_designed'}]
        stage_before=context_sha256(self.data,'G5'); render_before=render_gate.design_context(self.data,['SH1'])
        a['origin']['method']='Different documented synthetic method'
        self.assertNotEqual(stage_before,context_sha256(self.data,'G5'))
        self.assertNotEqual(render_before,render_gate.design_context(self.data,['SH1']))
    def test_cycle_fails_closed(self):
        a=copy.deepcopy(self.data['assets'][0]); a['id']='PARENT'
        self.data['assets'].append(a)
        self.data['assets'][0]['origin']['inputs']=[{**self.ref('baseline.mp4'), 'asset_id':'PARENT', 'origin_category':'self_designed'}]
        a['origin']['inputs']=[{**self.ref('baseline.mp4'), 'asset_id':'VIS', 'origin_category':'self_designed'}]
        self.assertTrue(any('cyclic provenance' in e for e in self.errors()))
    def test_unknown_malformed_category_fails_without_crash(self):
        for v in (None, [], {}, 7):
            self.data['assets'][0]['origin']['category']=v
            self.assertTrue(self.errors())

if __name__ == '__main__': unittest.main()
