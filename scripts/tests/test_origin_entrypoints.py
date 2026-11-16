"""Synthetic provenance admission checks; no authorship or media-quality verdict."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_render_gate as fixtures
import render_gate
from stage_checks import Checks, check_stage


class OriginEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixtures.RenderGateTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        fixtures.RenderGateTests.tearDownClass()

    def setUp(self):
        name=next(n for n in dir(fixtures.RenderGateTests) if n.startswith('test_'))
        self.f=fixtures.RenderGateTests(name);self.f.setUp()
        self.data=self.f.data

    def tearDown(self):
        self.f.tearDown()

    def add_paper(self):
        (self.f.root/'paper.mp4').write_bytes(self.f.media.read_bytes())
        self.data.setdefault('assets',[]).append({'id':'PAPER','kind':'real_capture',**self.f.ref('paper.mp4'),
            'rights':{'status':'cleared','scope':'synthetic permitted reuse'},
            'origin':{'category':'third_party_reference','method':'crop; reorder; Chinese dubbing'}})
        self.data['shots'][0]['asset_ids']=['PAPER']

    def test_sample_rejects_cropped_dubbed_paper_before_child(self):
        self.add_paper()
        code,record=self.f.run_sample('paper-rejected')
        self.assertEqual(code,1)
        self.assertTrue(any('origin' in x for x in record['preflight_errors']))
        self.assertFalse((self.f.root/'invoked.json').exists())

    def test_roughcut_cannot_waive_paper_sources(self):
        self.add_paper()
        with patch('stage_checks.check_stage',return_value=[]):
            errors=render_gate.preflight(self.data,self.f.root,'roughcut',['SH1'])
        self.assertTrue(any('origin' in x for x in errors))

    def test_absent_contract_blocks_sample(self):
        self.data.pop('origin_contract',None)
        errors=render_gate.preflight(self.data,self.f.root,'sample',['SH1'])
        self.assertTrue(any('origin explicit' in x for x in errors))

    def test_missing_selected_root_cannot_disappear_from_actual_validation(self):
        from origin_guard import validate_origin
        self.data['shots'][0]['asset_ids']=['MISSING']
        c=Checks(self.data,self.f.root)
        validate_origin(c,['SH1'])
        self.assertTrue(any('MISSING' in x and 'origin' in x for x in c.errors))

    def test_sample_does_not_require_future_g3_keyframe_output(self):
        self.data.setdefault('assets',[]).append({'id':'FUTURE','kind':'ai_generated',
            'origin':{'category':'self_generated','method':'planned own generation','entry_version':'planned-v1','inputs':[]}})
        self.data['design']['keyframe_scales']={'whole_scene':{'asset_ids':['FUTURE']}}
        self.assertEqual(render_gate.preflight(self.data,self.f.root,'sample',['SH1']),[])

    def test_g1_rejects_declared_third_party_plan(self):
        self.add_paper()
        errors=check_stage(self.data,self.f.root,'G1')
        self.assertTrue(any('origin' in x for x in errors))

    def test_g2_does_not_use_legacy_execution_to_skip_actual_origin(self):
        self.data['execution']['contract_version']=1
        self.add_paper()
        errors=check_stage(self.data,self.f.root,'G2')
        self.assertTrue(any('origin' in x for x in errors))

    def test_g3_staged_origin_call_precedes_other_review_checks(self):
        class Reached(Exception):pass
        with patch('origin_guard.validate_origin',side_effect=Reached):
            with self.assertRaises(Reached):check_stage(self.data,self.f.root,'G3')

    def test_g4_staged_origin_checks_full_scope(self):
        class Reached(Exception):pass
        with patch('origin_guard.validate_origin',side_effect=Reached) as called:
            with self.assertRaises(Reached):check_stage(self.data,self.f.root,'G4')
        self.assertTrue(called.call_args.kwargs['final'])

    def test_final_execution_checks_origin_even_without_receipt(self):
        self.add_paper();c=Checks(self.data,self.f.root)
        render_gate.validate_final_execution(c)
        self.assertTrue(any('origin' in x for x in c.errors))


if __name__=='__main__':unittest.main()
