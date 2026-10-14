"""Synthetic connector-plan/review tests; no real apparatus or visual approval."""
import copy
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from connection_guard import plans, validate_connection_review, plan_sha256, OBSERVATIONS, VIEWS
from stage_checks import Checks, check_stage
spec=importlib.util.spec_from_file_location('connection_png_fixture',Path(__file__).with_name('cover_fixture.py'));fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)


class ConnectionGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        fixture.png(self.root/'view.png',48,64)
        self.link={'id':'LINK1','kind':'pipe','from':{'object_id':'source','port_id':'out','role':'synthetic outlet','role_basis':'Synthetic declared teaching model defines this port.'},
                   'to':{'object_id':'receiver','port_id':'in','role':'synthetic inlet','role_basis':'Synthetic declared teaching model defines this port.'},
                   **{k:'synthetic planned '+k for k in OBSERVATIONS[1:]}}
        self.data={'shots':[{'id':'S1','shotbook':{'connections':{'applicable':True,'links':[self.link]}}}],
                   'qa':{'visual_frames':{'animation':{'viewing':{'sha256':'a'*64,'reviewer':'synthetic reviewer'}}}}}
        self.review={'status':'pass','actually_inspected':True,'media_sha256':'a'*64,'plan_sha256':plan_sha256(self.data,['S1']),'reviewer':'synthetic reviewer',
                     'links':[{'shot_id':'S1','connection_id':'LINK1','from':copy.deepcopy(self.link['from']),'to':copy.deepcopy(self.link['to']),
                      'status':'pass','issues':[],'observations':{k:'synthetic observed '+k for k in OBSERVATIONS},
                      'views':[{'kind':k,**fixture.ref(self.root,'view.png'),'source_media_sha256':'a'*64,'actually_opened':True,'observation':'Synthetic view declaration only.'} for k in sorted(VIEWS)]}]}
        self.data['qa']['visual_frames']['animation']['connection_review']=self.review

    def tearDown(self):self.tmp.cleanup()

    def errors(self,stage='G3'):
        c=Checks(self.data,self.root);validate_connection_review(c,stage,['S1']);return c.errors

    def plan_errors(self,ids=('S1',)):
        c=Checks(self.data,self.root);plans(c,ids);return c.errors

    def test_complete_synthetic_review_passes_bindings_only(self):self.assertEqual(self.errors(),[])

    def test_real_na_needs_no_connector_reviews(self):
        self.data['shots'][0]['shotbook']['connections']={'applicable':False,'links':[],'not_applicable_reason':'One free particle with no physical connections.'}
        self.data['qa']={};self.assertEqual(self.errors(),[])

    def test_false_na_with_existing_link_rejected(self):
        self.data['shots'][0]['shotbook']['connections'].update(applicable=False,not_applicable_reason='no connectors')
        self.assertTrue(self.plan_errors())

    def test_unassessed_applicability_or_unexplained_na_rejected(self):
        plan=self.data['shots'][0]['shotbook']['connections'];plan.pop('applicable');self.assertTrue(self.plan_errors())
        plan.update(applicable=False,links=[]);self.assertTrue(self.plan_errors())

    def test_missing_geometry_diameter_occlusion_or_continuity_blocks_design(self):
        for key in OBSERVATIONS[1:]:
            old=self.link.pop(key);self.assertTrue(self.plan_errors(),key);self.link[key]=old

    def test_port_role_cannot_be_missing_or_unverified(self):
        self.link['from']['role']='';self.assertTrue(self.plan_errors())
        self.link['from']['role']='synthetic outlet';self.link['from']['role_basis']='unverified';self.assertTrue(self.plan_errors())

    def test_same_object_same_port_cannot_fake_two_ends(self):
        self.link['to']=copy.deepcopy(self.link['from']);self.assertTrue(self.plan_errors())

    def test_distinct_ports_on_same_object_allowed(self):
        self.link['to']['object_id']='source';self.assertEqual(self.plan_errors(),[])

    def test_reducer_and_different_section_are_allowed_when_designed(self):
        self.link['diameter_and_transition']='Large hose enters a modeled rigid reducer; the small outlet seats inside its collar.'
        self.assertEqual(self.plan_errors(),[])
        self.link['kind']='cable';self.link['diameter_and_transition']='Cable insulation and metal terminal differ in section, with a modeled strain relief.'
        self.assertEqual(self.plan_errors(),[])

    def test_wrong_observed_endpoint_or_role_is_rejected(self):
        row=self.review['links'][0]
        for key in ('object_id','port_id','role'):
            old=row['to'][key];row['to'][key]='wrong observed '+key
            self.assertTrue(any('observed topology' in e for e in self.errors()));row['to'][key]=old

    def test_reversed_camera_listing_preserves_physical_pair(self):
        row=self.review['links'][0];row['from'],row['to']=row['to'],row['from'];self.assertEqual(self.errors(),[])

    def test_unexplained_cross_shot_reconnection_is_rejected(self):
        second=copy.deepcopy(self.data['shots'][0]);second['id']='S2';second['shotbook']['connections']['links'][0]['to']['port_id']='other-port';self.data['shots'].append(second)
        self.assertTrue(any('across shots' in e for e in self.plan_errors(('S1','S2'))))
        second['shotbook']['connections']['links'][0]['topology_change_reason']='The scene explicitly shows unplugging and reconnecting as the experiment.'
        self.assertEqual(self.plan_errors(('S1','S2')),[])

    def test_failed_or_unreviewed_connector_never_passes(self):
        for status in ('fail','pending'):
            self.review['status']=status;self.assertTrue(self.errors())

    def test_actual_visual_inspection_required(self):
        self.review['actually_inspected']=False;self.assertTrue(self.errors())

    def test_floating_joint_or_abrupt_section_issue_blocks(self):
        for issue in ('floating gap','false visual bridge','wrong tangent','abrupt hose width','wrong occlusion order'):
            self.review['links'][0]['issues']=[issue];self.assertTrue(self.errors())

    def test_every_observation_and_view_required(self):
        row=self.review['links'][0]
        for key in OBSERVATIONS:
            old=row['observations'].pop(key);self.assertTrue(self.errors());row['observations'][key]=old
        for index in range(3):
            old=row['views'].pop(index);self.assertTrue(self.errors());row['views'].insert(index,old)

    def test_stale_plan_media_or_images_rejected(self):
        self.review['plan_sha256']='b'*64;self.assertTrue(self.errors())
        self.review['plan_sha256']=plan_sha256(self.data,['S1']);self.review['media_sha256']='b'*64;self.assertTrue(self.errors())
        self.review['media_sha256']='a'*64;self.review['links'][0]['views'][0]['sha256']='b'*64;self.assertTrue(self.errors())

    def test_view_must_be_actual_image_and_opened(self):
        view=self.review['links'][0]['views'][0];view['actually_opened']=False;self.assertTrue(self.errors())
        view['actually_opened']=True;(self.root/'bad.txt').write_text('not an image');view.update(fixture.ref(self.root,'bad.txt'));self.assertTrue(self.errors())

    def test_missing_link_and_duplicate_link_review_block(self):
        old=self.review['links'].pop();self.assertTrue(self.errors());self.review['links']=[old,copy.deepcopy(old)];self.assertTrue(self.errors())

    def test_final_uses_full_film_review_record(self):
        self.assertTrue(self.errors('G5'))
        self.data['qa']['visual_frames'].update(viewing={'sha256':'a'*64,'reviewer':'synthetic reviewer'},connection_review=self.review)
        self.assertEqual(self.errors('G5'),[])

    def test_stage_final_cannot_skip_applicable_connection_review(self):
        for stage in ('G5','G6','G7'):
            self.assertTrue(any('connections '+('G5') in e for e in check_stage(self.data,self.root,stage)))


if __name__=='__main__':unittest.main()
