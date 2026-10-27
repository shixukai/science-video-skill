"""Behavioral regressions using explicitly synthetic records; no media approval."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_episode
import render_gate
import stage_checks
import task_scope
import test_render_gate as render_fixture
import test_opening_alignment_guard as opening_fixture
import test_topic_selection_guard as topic_fixture
import test_local_repair_scope as motion_fixture
import test_label_permission_guard as label_fixture
from cover_fixture import png, ref, attach_cover_fixture, save_cover_fixture
from cover_guard import validate_cover_review
from opening_alignment_guard import check_opening_plan, opening_context_sha256


class BootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        render_fixture.RenderGateTests.setUpClass()

    @classmethod
    def tearDownClass(cls):
        render_fixture.RenderGateTests.tearDownClass()

    def setUp(self):
        self.f=render_fixture.RenderGateTests(); self.f.setUp()
        self.addCleanup(self.f.tearDown)
        png(self.f.root/'initial.png',48,64)
        self.f.data['design']['approved_film_reference']={
            'kind':'initial_style_reference', 'reference':ref(self.f.root,'initial.png'),
            'selection_reason':'Synthetic first-sample design choice', 'applicable_style':'Synthetic shape reference',
            'actually_opened':True,'observation':'Synthetic observation, not real perception',
            'reviewer':'synthetic editor','reviewed_at':render_gate.now()}

    def test_first_sample_runs_without_fabricated_approved_film(self):
        code,record=self.f.run_sample()
        self.assertEqual(code,0,record)
        self.assertEqual(record['result'],'rendered_unreviewed')
        self.assertEqual(self.f.data['qa']['visual_frames']['status'],'pending')

    def test_first_sample_does_not_waive_actual_reference_observation(self):
        self.f.data['design']['approved_film_reference']['actually_opened']=False
        code,record=self.f.run_sample()
        self.assertEqual(code,1)
        self.assertFalse((self.f.root/'invoked.json').exists())

    def test_first_sample_rejects_changed_reference_bytes(self):
        png(self.f.root/'initial.png',48,64,(10,20,30))
        code,_=self.f.run_sample()
        self.assertEqual(code,1)

    def test_initial_reference_never_bypasses_full_g3_gate(self):
        errors=render_gate.preflight(self.f.data,self.f.root,'full',['SH1'])
        self.assertTrue(any('G3' in e for e in errors),errors)

    def test_roughcut_can_precede_g3_without_art_baseline(self):
        self.f.data['design'].pop('approved_film_reference')
        self.f.data['design'].pop('visual_intent')
        # Roughcut placeholders still declare their actual medium and source;
        # they do not require a final art direction or realism approval.
        self.f.data['shots'][0]['shotbook']['realism']={'medium':'infographic'}
        self.f.save()
        with patch.object(stage_checks,'check_stage',return_value=[]) as stages:
            code,record=render_gate.run_render(self.f.root/'episode.json','roughcut',['SH1'],'rough.mp4','rough.json')
        self.assertEqual(code,0,record)
        self.assertEqual({c.args[2] for c in stages.call_args_list},{'G1'})
        self.assertEqual(record['result'],'rendered_unreviewed')

    def test_roughcut_never_waives_original_visual_sources(self):
        self.f.data['origin_contract']['mode']='third_party_filler'
        self.f.save()
        with patch.object(stage_checks,'check_stage',return_value=[]):
            code,record=render_gate.run_render(self.f.root/'episode.json','roughcut',['SH1'],'rough.mp4','rough.json')
        self.assertEqual(code,1)
        self.assertTrue(any('origin explicit' in e for e in record['preflight_errors']))
        self.assertFalse((self.f.root/'invoked.json').exists())

    def test_roughcut_does_not_ignore_failed_g1(self):
        self.f.save()
        with patch.object(stage_checks,'check_stage',return_value=['G1 failed']):
            code,_=render_gate.run_render(self.f.root/'episode.json','roughcut',['SH1'],'rough.mp4','rough.json')
        self.assertEqual(code,1)
        self.assertFalse((self.f.root/'invoked.json').exists())

    def prepare_roughcut(self):
        self.f.data['execution']['contract_version']=2
        self.f.save()
        with patch.object(stage_checks,'check_stage',return_value=[]):
            code,record=render_gate.run_render(self.f.root/'episode.json','roughcut',['SH1'],'rough.mp4','rough.json')
        self.assertEqual(code,0,record)
        self.f.data['execution']['roughcut_receipt']=self.f.ref('rough.json')
        self.f.data['qa']['shotbook']={'viewing':{**record['output'],'reviewed_at':render_gate.now()}}

    def roughcut_errors(self):
        c=stage_checks.Checks(self.f.data,self.f.root)
        render_gate.validate_roughcut_execution(c)
        return c.errors

    def test_g2_actual_receipt_survives_only_later_art_refinement(self):
        self.prepare_roughcut()
        self.f.data['design']['board_sha256']='f'*64
        self.f.data['shots'][0]['shotbook'].update(status='reviewed',render_file='refined.mp4',render_sha256='a'*64,
            keyframe_review={'status':'pass','file':'refined.png'})
        self.assertEqual(self.roughcut_errors(),[])
        self.f.data['shots'][0]['shotbook']['action']='Changed explanation sequence'
        self.assertTrue(any('G2 plan changed' in e for e in self.roughcut_errors()))

    def test_g2_cannot_review_a_different_file_or_claim_viewing_before_render(self):
        self.prepare_roughcut()
        self.f.data['qa']['shotbook']['viewing']['file']='baseline.mp4'
        self.assertTrue(any('actual roughcut output' in e for e in self.roughcut_errors()))
        self.f.data['qa']['shotbook']['viewing'].update(file='rough.mp4',reviewed_at='2000-01-01T00:00:00Z')
        self.assertTrue(any('reviewed after actual execution' in e for e in self.roughcut_errors()))

    def test_new_contract_requires_roughcut_receipt_without_backfilling_legacy(self):
        self.f.data['execution']['contract_version']=2
        self.assertTrue(self.roughcut_errors())
        self.f.data['execution'].pop('contract_version')
        self.assertEqual(self.roughcut_errors(),[])


class OutputScopeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def test_requested_video_scope_cannot_contain_active_cover_outputs(self):
        data={'delivery_scope':'video_only','delivery_scope_note':'User requested video alone','deliverables':{'cover_3_4':'old.png'}}
        c=stage_checks.Checks(data,self.root);task_scope.validate_scope(c)
        self.assertTrue(c.errors)

    def test_delivery_and_publish_ready_have_different_stage_dependencies(self):
        root=Path(check_episode.__file__).resolve().parents[1]
        data=json.loads((root/'assets/episode-template.json').read_text())
        data.update(delivery_scope='video_only',delivery_scope_note='Synthetic video-only commission')
        for requested,expected in [('delivery','G5'),('publish_ready','G6')]:
            with patch.object(check_episode,'check_stage',return_value=[]) as stage:
                errors,_=check_episode.check(data,self.root,requested)
            self.assertEqual([c.args[2] for c in stage.call_args_list],[expected])
            if requested=='delivery':
                self.assertFalse(any('qa.mobile_preview' in e or 'cover_3_4: file' in e or 'qa.covers' in e for e in errors),errors)
            else:
                self.assertTrue(any('qa.mobile_preview' in e for e in errors))

    def test_first_cover_reference_does_not_require_invented_prior_approval(self):
        data={};review=attach_cover_fixture(data,self.root)
        review['baseline']['kind']='initial_style_reference'
        review['baseline']['selection_reason']='Synthetic first cover reference'
        for key in ('approval_evidence','approval_reference','approved_image_sha256'):review['baseline'].pop(key)
        save_cover_fixture(data,self.root,review)
        c=stage_checks.Checks(data,self.root);validate_cover_review(c)
        self.assertEqual(c.errors,[])
        review['baseline']['actually_opened']=False;save_cover_fixture(data,self.root,review)
        c=stage_checks.Checks(data,self.root);validate_cover_review(c)
        self.assertTrue(c.errors)

    def test_single_requested_cover_is_not_forced_to_two(self):
        data={'requested_cover_keys':['cover_4_3'],'delivery_scope_note':'Synthetic landscape cover-only request'}
        review=attach_cover_fixture(data,self.root)
        del review['variants']['cover_3_4']
        save_cover_fixture(data,self.root,review)
        c=stage_checks.Checks(data,self.root);validate_cover_review(c)
        self.assertEqual(c.errors,[])

    def test_invalid_cover_scope_does_not_silently_remove_required_work(self):
        for keys in ([],['unknown'],['cover_4_3','cover_4_3'],{},[{}]):
            c=stage_checks.Checks({'requested_cover_keys':keys,'delivery_scope_note':'Synthetic scope'},self.root)
            task_scope.validate_scope(c);self.assertTrue(c.errors)

    def test_label_position_keeps_g1_but_invalidates_media_stage(self):
        data={'presentation_text':{'items':[{'text':'温度','purposes':['mechanism'],'position':'left','time_range':[0,1]}]}}
        before={g:stage_checks.context_sha256(data,g) for g in ('G1','G2','G3','G5')}
        data['presentation_text']['items'][0]['position']='right'
        self.assertEqual(before['G1'],stage_checks.context_sha256(data,'G1'))
        for g in ('G2','G3','G5'):self.assertNotEqual(before[g],stage_checks.context_sha256(data,g))
        data['presentation_text']['items'][0]['text']='压力'
        self.assertNotEqual(before['G1'],stage_checks.context_sha256(data,'G1'))

    def test_video_opening_can_be_reviewed_without_cover_question(self):
        f=opening_fixture.OpeningAlignmentTests();f.setUp();self.addCleanup(f.tearDown)
        f.data.update(delivery_scope='video_only',delivery_scope_note='Synthetic no-cover request')
        for key in ('cover_3_4','cover_4_3'):
            f.data['deliverables'].pop(key);f.data['qa']['reviewed_sha256'].pop(key)
        f.data['topic_alignment']['opening'].pop('cover_question')
        f.review['covers']={}
        for source in f.review['sources']:
            source['reviewed_items']=[k for k in source['reviewed_items'] if k!='cover_question']
        f.review['sources']=[s for s in f.review['sources'] if s['reviewed_items']]
        f.review['context_sha256']=opening_context_sha256(f.data);f.save()
        self.assertEqual(check_opening_plan(f.data),[])
        self.assertEqual(f.errors(),[])
        f.review['question_relation']='different_question';f.save()
        self.assertTrue(f.errors())


class UserTopicTests(unittest.TestCase):
    def setUp(self):
        self.f=topic_fixture.TopicSelectionTests();self.f.setUp();self.addCleanup(self.f.tearDown)
        (self.f.root/'request.txt').write_text('Synthetic user chose this basic topic for a beginner.',encoding='utf-8')
        self.f.card.update(selection_origin='user_requested',user_request_reference='synthetic request',
            user_request_evidence=ref(self.f.root,'request.txt'),scope_reason='Explain the requested foundation accurately')

    def test_user_requested_basic_topic_retains_editorial_risk_without_veto(self):
        self.f.card['disqualifiers']=['common_knowledge_only','definition_only']
        self.assertEqual(self.f.errors(),[])

    def test_user_requested_audience_can_override_default(self):
        self.f.card['audience_category']='beginner_students'
        self.assertEqual(self.f.errors(),[])

    def test_user_scope_never_exempts_unsupported_scientific_hook(self):
        self.f.card['disqualifiers']=['unsupported_hook']
        self.assertTrue(self.f.errors())

    def test_user_origin_flag_without_original_request_is_insufficient(self):
        self.f.card.pop('user_request_evidence')
        self.assertTrue(self.f.errors())


class PurposefulHoldTests(unittest.TestCase):
    def setUp(self):
        self.f=motion_fixture.UnknownSpanDiagnosticsTests();self.f.setUp();self.addCleanup(self.f.tearDown)
        self.f.policy['timing_mode']='review_triggers'
        self.review={'status':'pass','reviewer':'synthetic reviewer','observation':'Synthetic observation of a bounded comparison task','evidence':'synthetic time-range evidence'}

    def test_long_observation_requires_actual_declared_review(self):
        record,report=self.f.record([(0,5,'purposeful_read')],lows=[[0,5]])
        record['longest_no_progress_seconds']=5
        record['spans'][0].update(purpose='Compare two fixed structures',resume_evidence='Returns to synthesis',hold_review=self.review)
        record['semantic_units'][0].update(task_type='observation',hold_review=self.review)
        record['screen_resolutions']=[{'range':[0,5],'result':'purposeful_observation','observation':'Synthetic comparison', 'evidence':'Synthetic times','hold_review':self.review}]
        self.assertEqual(self.f.errors(record,report),[])
        del record['spans'][0]['hold_review']
        self.assertTrue(self.f.errors(record,report))

    def test_read_hold_cannot_replace_unshown_process(self):
        record,report=self.f.record([(0,5,'purposeful_read')])
        record['longest_no_progress_seconds']=5
        record['spans'][0].update(purpose='Synthetic process',resume_evidence='Synthetic resumption',hold_review=self.review)
        self.assertTrue(any('slideshow' in e for e in self.f.errors(record,report)))


class LabelScopeTests(unittest.TestCase):
    def setUp(self):
        self.f=label_fixture.LabelPermissionTests();self.f.setUp();self.addCleanup(self.f.doCleanups)

    def test_explicit_disclosure_with_protected_notice_and_consent_can_pass(self):
        self.f.item.update(text='AI生成画面，非实拍',purposes=['ai_simulation'],notice_id='AI')
        label_fixture.consent_item(self.f.item,self.f.root)
        self.f.data['presentation_text']['required_notices']=[{'id':'AI','purpose':'ai_simulation',
            'text':self.f.item['text'],'basis':'Synthetic actual disclosure requirement','placement':'audience',
            'placement_basis':'Synthetic specifically requested on-frame disclosure'}]
        self.assertEqual(self.f.plan(),[])
        self.f.item.pop('user_approval');self.assertTrue(self.f.plan())

    def test_watermark_needs_specific_consent(self):
        self.f.item.update(text='Creator watermark',purposes=['watermark'])
        self.assertTrue(self.f.plan())
        label_fixture.consent_item(self.f.item,self.f.root)
        self.assertEqual(self.f.plan(),[])

    def test_scientific_ai_topic_has_reviewed_semantic_path(self):
        self.f.item.update(text='AI模拟大气环流用于预测天气',purposes=['mechanism'])
        self.assertTrue(self.f.plan())
        (self.f.root/'semantic.txt').write_text('Synthetic semantic review only',encoding='utf-8')
        self.f.data['claims']=[{'id':'C1'}]
        self.f.item['cue_review']={'status':'pass','interpretation':'scientific_subject','reviewer':'synthetic reviewer',
            'scientific_basis':'Synthetic source-bound scientific method','audience_task':'Understand prediction method',
            'note':'Describes scientific method, not production disclosure','claim_ids':['C1'],
            'text_sha256':hashlib.sha256(self.f.item['text'].encode()).hexdigest(),'evidence':ref(self.f.root,'semantic.txt')}
        self.assertEqual(self.f.plan(),[])
        self.f.item['text']='本片AI生成画面'
        self.assertTrue(self.f.plan())

    def test_scientific_subject_cannot_reference_missing_claim(self):
        self.test_scientific_ai_topic_has_reviewed_semantic_path()
        self.f.item['text']='AI模拟大气环流用于预测天气'
        self.f.data['claims']=[]
        self.assertTrue(self.f.plan())


if __name__=='__main__':unittest.main()
