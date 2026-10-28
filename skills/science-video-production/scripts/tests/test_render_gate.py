"""Real wrapper/child-process regressions with synthetic media; no actual art approval."""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from topic_selection_fixture import attach_topic_selection_fixture
import render_gate as gate
from stage_checks import Checks, check_stage


class RenderGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.media_tmp = tempfile.TemporaryDirectory()
        cls.media = Path(cls.media_tmp.name) / 'film.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=c=blue:s=48x64:d=0.5:r=10',
                        '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=mono', '-t', '0.5', '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(cls.media)], check=True)

        cls.silent_media = Path(cls.media_tmp.name) / 'silent-film.mp4'
        subprocess.run(['ffmpeg', '-v', 'error', '-i', str(cls.media), '-map', '0:v:0', '-c:v', 'copy', '-an', str(cls.silent_media)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.media_tmp.cleanup()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        (self.root / 'baseline.mp4').write_bytes(self.media.read_bytes())
        (self.root / 'approval.txt').write_text('Synthetic approval fixture, no real approval.')
        adapter = self.root / 'adapter.py'
        adapter.write_text('''import argparse, pathlib, shutil, json
p=argparse.ArgumentParser()
for arg in ('episode','phase','shot-ids','output'):p.add_argument('--'+arg,required=True)
a=p.parse_args()
pathlib.Path('invoked.json').write_text(json.dumps(vars(a)))
shutil.copyfile('baseline.mp4',a.output)
''')
        gate.make_lock(self.root / 'skill-lock.json')
        view = {**self.ref('baseline.mp4'), 'duration': .5, 'ranges': [[0,.5]],
                'method': 'continuous_playback', 'playback_speed': 1, 'watched': True, 'heard': True,
                'reviewer': 'synthetic baseline reviewer', 'capability': 'synthetic fixture, no perception',
                'reviewed_at': gate.now(), 'note': 'Synthetic observation only, no actual acceptance.', 'scope': 'approved_film'}
        self.data = {'episode_id': 'SYNTHETIC', 'brief': {'roles': {'producer': 'synthetic producer'}},
                     'shots': [{'id': 'SH1', 'shotbook': {key: 'synthetic concrete ' + key for key in
                          ('claim_support','subject','action','attention_target','viewer_takeaway')}}],
                     'execution': {'skill_lock': self.ref('skill-lock.json'), 'entrypoint': self.ref('adapter.py')},
                     'design': {'approved_film_reference': {'kind': 'approved_finished_film',
                         'approval_reference': 'synthetic approval reference', 'approval_evidence': self.ref('approval.txt'),
                         'approved_media_sha256': view['sha256'], 'applicable_style': 'synthetic same style test', 'viewing': view}},
                     'qa': {'visual_frames': {'status': 'pending', 'animation': {'next_action': 'repair_sample'}}}}
        self.data['shots'][0]['shotbook']['connections']={'applicable':False,'not_applicable_reason':'Synthetic shape has no connector.','links':[]}
        # Explicit synthetic non-realistic fixture exception; never a real approval.
        self.data['design']['visual_intent'] = {
            'target': 'scientific_realism', 'style_reference': self.ref('baseline.mp4'),
            'scientific_constraints': 'Synthetic fixture checks records only, not scientific truth.'}
        self.data['shots'][0]['shotbook']['realism'] = {
            'role': 'main', 'medium': 'pure_2d', 'renderer': 'raster_animation',
            'scientific_basis': 'Synthetic blue field, no real scientific claim.',
            'visible_motion': 'Synthetic fixture with no actual motion acceptance.',
            'exception': {'shot_id': 'SH1', 'scope': 'nonrealistic_full_frame_shot',
                          'reason': 'Explicit synthetic test-only exception, no production authorization.',
                          'user_evidence': self.ref('approval.txt')}}
        from origin_fixture import attach_origin_fixture
        attach_origin_fixture(self.data, self.root)
        attach_topic_selection_fixture(self.data)
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def ref(self, name):
        return {'file': name, 'sha256': gate.file_hash(self.root/name)}

    def save(self):
        (self.root/'episode.json').write_text(json.dumps(self.data))

    def run_sample(self, suffix='1'):
        self.save()
        return gate.run_render(self.root/'episode.json', 'sample', ['SH1'], 'sample'+suffix+'.mp4', 'run'+suffix+'.json')

    def final_data(self):
        self.prepared_sample()
        record = json.loads((self.root/'run1.json').read_text())
        # Fabricated full history solely for final-record validation, not a real full render.
        record['phase']='full'; (self.root/'full.json').write_text(json.dumps(record))
        self.data['execution']['full_receipt']=self.ref('full.json')
        self.data['deliverables']={'video':'sample1.mp4'}
        self.data['qa']['reviewed_sha256']={'video':record['output']['sha256']}
        review={**record['output'],'reviewer':'independent synthetic reviewer','reviewed_at':gate.now()}
        self.data['qa'].update(technical={'status':'pass'},audio={'status':'pass','listening':{'headphones':copy.deepcopy(review),'phone_speaker':copy.deepcopy(review)}})
        self.data['qa']['visual_frames'].update(status='pass',viewing=review)
        return record

    def final_errors(self):
        c=Checks(self.data,self.root);gate.validate_final_execution(c);return c.errors

    def visual_only_baseline(self):
        import struct, zlib
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
        png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b'\x00' + b'\x00\x00\xff' * 2 + b'\x00' + b'\x00\x00\xff' * 2)) + chunk(b'IEND', b'')
        (self.root/'frame.png').write_bytes(png)
        view = self.data['design']['approved_film_reference']['viewing']
        view.update(method='frame_samples', scope='approved_film_visual_reference', purpose='appearance_only',
                    heard=False, playback_speed=None, ranges=[], frames=[{'time': .2, 'source_sha256': view['sha256'],
                    'image': self.ref('frame.png'), 'actually_opened': True,
                    'observation': 'Synthetic blue field at this point; no motion or hearing claim.'}])
        return view

    def silent_visual_baseline(self):
        (self.root/'baseline.mp4').write_bytes(self.silent_media.read_bytes())
        baseline = self.data['design']['approved_film_reference']
        baseline['viewing'].update(self.ref('baseline.mp4'))
        baseline['approved_media_sha256'] = self.ref('baseline.mp4')['sha256']
        self.data['design']['visual_intent']['style_reference'] = self.ref('baseline.mp4')
        return self.visual_only_baseline()

    def test_actual_silent_film_is_valid_appearance_only_baseline(self):
        self.silent_visual_baseline()
        probe = Checks(self.data,self.root); probe.duration(self.root/'baseline.mp4')
        self.assertTrue(any('has no audio' in e for e in probe.errors))
        self.assertEqual(gate.preflight(self.data,self.root,'sample',['SH1']), [])

    def test_silent_baseline_scope_and_approved_hash_still_enforced(self):
        view = self.silent_visual_baseline(); view['scope'] = 'representative'
        checks = Checks(self.data,self.root); gate.check_baseline(checks)
        self.assertTrue(any('appearance-only scoped' in e for e in checks.errors))
        view['scope'] = 'approved_film_visual_reference'
        self.data['design']['approved_film_reference']['approved_media_sha256'] = '0'*64
        checks = Checks(self.data,self.root); gate.check_baseline(checks)
        self.assertTrue(checks.errors)

    def test_silent_baseline_cannot_be_continuous_audiovisual_reference(self):
        view = self.silent_visual_baseline()
        view.update(method='continuous_playback',scope='approved_film',heard=True,playback_speed=1,ranges=[[0,.5]])
        checks = Checks(self.data,self.root); gate.check_baseline(checks)
        self.assertTrue(any('has no audio' in e for e in checks.errors))

    def test_frame_samples_cannot_replace_audible_representative_review(self):
        view = self.visual_only_baseline()  # Actual fixture includes an audio track.
        view['scope'] = 'representative'
        checks = Checks(self.data,self.root); checks.viewing(view,'representative','representative')
        self.assertTrue(any('frame samples do not qualify' in e for e in checks.errors))
        self.assertTrue(any('actual viewing and listening required' in e for e in checks.errors))

    def test_finite_real_visual_reference_can_create_only_unreviewed_sample(self):
        self.visual_only_baseline(); code, record = self.run_sample()
        self.assertEqual(code, 0, record['preflight_errors']); self.assertEqual(record['result'], 'rendered_unreviewed')
        self.assertEqual(self.data['qa']['visual_frames']['status'], 'pending')
        self.assertIn('frame.png', record['input_files'])

    def test_visual_reference_missing_or_unopened_frames_block(self):
        view = self.visual_only_baseline(); view['frames'][0]['actually_opened'] = False
        self.assertEqual(self.run_sample('unopened')[0], 1)
        view['frames'] = []; self.assertEqual(self.run_sample('empty')[0], 1)
        self.assertFalse((self.root/'invoked.json').exists())

    def test_visual_reference_cannot_claim_listening_or_continuous_playback(self):
        view = self.visual_only_baseline(); view['heard'] = True
        self.assertEqual(self.run_sample('heard')[0], 1)
        view['heard'] = False; view['ranges'] = [[0,.5]]
        self.assertEqual(self.run_sample('continuous')[0], 1)

    def test_visual_reference_time_source_hash_and_actual_image_are_checked(self):
        for index, change in enumerate(({'time': .6}, {'time': float('nan')}, {'source_sha256': '0'*64}, {'image': {'file': 'missing.png', 'sha256': '0'*64}})):
            view = self.visual_only_baseline(); view['frames'][0].update(change)
            self.assertEqual(self.run_sample(str(index))[0], 1)
        self.assertFalse((self.root/'invoked.json').exists())

    def test_visual_reference_bytes_changed_block_before_renderer(self):
        self.visual_only_baseline(); (self.root/'frame.png').write_text('not the viewed image')
        self.assertEqual(self.run_sample()[0], 1); self.assertFalse((self.root/'invoked.json').exists())

    def test_visual_baseline_and_rendered_sample_do_not_replace_g3_listening(self):
        self.visual_only_baseline(); self.assertEqual(self.run_sample()[0], 0)
        self.data['execution']['sample_receipt'] = self.ref('run1.json')
        self.data['qa']['visual_frames']['animation']['next_action'] = 'expand'; self.save()
        actual_run = gate.subprocess.run
        with patch.object(gate.subprocess, 'run', wraps=actual_run) as calls:
            code, record = gate.run_render(self.root/'episode.json', 'full', ['SH1'], 'full.mp4', 'full.json')
        self.assertEqual(code, 1)
        self.assertFalse(any(str(self.root/'adapter.py') in call.args[0] for call in calls.call_args_list))
        self.assertTrue(any('G3' in e for e in record['preflight_errors']))

    def test_first_dynamic_sample_runs_without_future_g3(self):
        code,r=self.run_sample();self.assertEqual(code,0);self.assertEqual(r['result'],'rendered_unreviewed')
        self.assertTrue((self.root/'invoked.json').is_file())
        self.assertEqual(self.data['qa']['visual_frames']['status'],'pending')

    def test_real_cli_invokes_adapter_with_exact_scope(self):
        codex_home = self.root / 'isolated-test-home'
        installed = codex_home / 'skills/science-video-production-test'
        shutil.copytree(gate.SKILL_ROOT, installed, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        p=subprocess.run([sys.executable,str(installed/'scripts/render_gate.py'),'run',str(self.root/'episode.json'),
             '--phase','sample','--shot-ids','SH1','--output','cli.mp4','--receipt','cli.json'],capture_output=True,text=True,
             env=dict(os.environ, CODEX_HOME=str(codex_home)))
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        actual=json.loads((self.root/'invoked.json').read_text());self.assertEqual(actual['phase'],'sample');self.assertEqual(actual['shot_ids'],'SH1')

    def test_each_missing_design_field_prevents_actual_child(self):
        for index,key in enumerate(('claim_support','subject','action','attention_target','viewer_takeaway')):
            old=self.data['shots'][0]['shotbook'].pop(key)
            code,r=self.run_sample(str(index));self.assertEqual(code,1,key);self.assertFalse((self.root/'invoked.json').exists())
            self.data['shots'][0]['shotbook'][key]=old

    def test_repair_can_resume_after_missing_design_is_fixed(self):
        self.data['shots'][0]['shotbook']['action']='TODO';self.assertEqual(self.run_sample('bad')[0],1)
        self.data['shots'][0]['shotbook']['action']='The synthetic object changes visible state.'
        self.assertEqual(self.run_sample('fixed')[0],0)

    def test_current_failure_allows_repair_sample_but_not_expansion(self):
        self.data['qa']['visual_frames']['status']='fail';self.assertEqual(self.run_sample()[0],0)
        errors=gate.preflight(self.data,self.root,'full',['SH1']);self.assertTrue(any('failure blocks expansion' in e for e in errors))

    def test_full_without_g3_and_sample_does_not_execute(self):
        code,r=gate.run_render(self.root/'episode.json','full',['SH1'],'full.mp4','full.json')
        self.assertEqual(code,1);self.assertFalse((self.root/'invoked.json').exists());self.assertTrue(any('G3' in e for e in r['preflight_errors']))

    def test_changed_skill_bytes_block_even_same_version(self):
        actual=gate.skill_snapshot();actual['files']['SKILL.md']='0'*64;actual['tree_sha256']=gate.digest(actual['files'])
        with patch.object(gate,'skill_snapshot',return_value=actual):
            self.assertTrue(any('locked version/hash' in e for e in gate.preflight(self.data,self.root,'sample',['SH1'])))

    def test_missing_lock_blocks(self):
        self.data['execution'].pop('skill_lock');self.assertEqual(self.run_sample()[0],1)

    def test_lock_cannot_overwrite(self):
        with self.assertRaises(FileExistsError):gate.make_lock(self.root/'skill-lock.json')

    def test_renderer_hash_change_prevents_call(self):
        (self.root/'adapter.py').write_text('raise RuntimeError("must not run")')
        self.assertEqual(self.run_sample()[0],1);self.assertFalse((self.root/'invoked.json').exists())

    def test_still_image_cannot_replace_approved_film(self):
        (self.root/'baseline.mp4').write_text('not a film')
        view=self.data['design']['approved_film_reference']['viewing'];view.update(self.ref('baseline.mp4'))
        self.data['design']['approved_film_reference']['approved_media_sha256']=view['sha256']
        self.assertEqual(self.run_sample()[0],1)

    def test_baseline_cannot_be_unwatched_or_different_approval(self):
        base=self.data['design']['approved_film_reference'];base['viewing']['watched']=False
        self.assertEqual(self.run_sample('a')[0],1)
        base['viewing']['watched']=True;base['approved_media_sha256']='a'*64;self.assertEqual(self.run_sample('b')[0],1)

    def test_baseline_and_adapter_paths_cannot_escape(self):
        self.data['execution']['entrypoint']['file']='../adapter.py';self.assertEqual(self.run_sample()[0],1)

    def test_receipt_and_output_must_be_new_distinct_local_files(self):
        for out,rec in [('episode.json','x.json'),('../out.mp4','x.json'),('x.json','x.json')]:
            with self.assertRaises(ValueError):gate.run_render(self.root/'episode.json','sample',['SH1'],out,rec)

    def test_child_nonzero_is_failed_not_reviewed(self):
        (self.root/'adapter.py').write_text('raise SystemExit(7)');self.data['execution']['entrypoint']=self.ref('adapter.py')
        code,r=self.run_sample();self.assertEqual(code,2);self.assertEqual(r['returncode'],7);self.assertEqual(r['result'],'render_failed')

    def test_child_success_without_media_is_failed(self):
        (self.root/'adapter.py').write_text('pass');self.data['execution']['entrypoint']=self.ref('adapter.py')
        self.assertEqual(self.run_sample()[0],2)

    def test_pre_render_receipt_exists_when_adapter_starts(self):
        with (self.root/'adapter.py').open('a') as f:f.write('\nr=json.loads(pathlib.Path("run1.json").read_text());assert r["result"]=="started";assert r["completed_at"] is None\n')
        self.data['execution']['entrypoint']=self.ref('adapter.py');self.assertEqual(self.run_sample()[0],0)

    def test_final_independent_results_pass_structurally_only(self):
        self.final_data();self.assertEqual(self.final_errors(),[])

    def test_final_missing_receipt_blocks_g5_g6_g7(self):
        for stage in ('G5','G6','G7'):
            self.assertTrue(any('full render receipt' in e for e in check_stage(self.data,self.root,stage)),stage)

    def test_final_code_pass_cannot_replace_visual_or_hearing(self):
        self.final_data()
        for key in ('technical','visual_frames','audio'):
            self.data['qa'][key]['status']='pending';self.assertTrue(any('separate '+key in e for e in self.final_errors()));self.data['qa'][key]['status']='pass'

    def test_final_producer_cannot_self_review(self):
        self.final_data();self.data['qa']['visual_frames']['viewing']['reviewer']=' SYNTHETIC PRODUCER '
        self.assertTrue(any('differ from producer' in e for e in self.final_errors()))

    def test_post_render_design_changes_invalidate_receipt(self):
        self.final_data();self.data['shots'][0]['shotbook']['action']='Changed underlying action after rendering.'
        self.assertTrue(any('stale full design' in e for e in self.final_errors()))

    def test_backfilled_lock_or_future_review_rejected(self):
        self.final_data();self.data['qa']['visual_frames']['viewing']['reviewed_at']='2999-01-01T00:00:00Z'
        self.assertTrue(any('after rendering' in e for e in self.final_errors()))
        lock=json.loads((self.root/'skill-lock.json').read_text());lock['created_at']=gate.now();(self.root/'skill-lock.json').write_text(json.dumps(lock))
        self.data['execution']['skill_lock']=self.ref('skill-lock.json')
        self.assertTrue(any('must precede' in e for e in self.final_errors()))


    def test_unknown_api_phase_blocks(self):
        errors=gate.preflight(self.data,self.root,'typo-full',['SH1'])
        self.assertTrue(any('phase must' in e for e in errors))

    def test_missing_selected_asset_blocks_but_unused_candidate_does_not(self):
        self.data['assets']=[{'id':'A1','file':'missing.png','sha256':'a'*64}]
        self.data['shots'][0]['asset_ids']=['A1']
        self.assertEqual(self.run_sample('missing')[0],1)
        self.data['shots'][0]['asset_ids']=[]
        self.assertEqual(self.run_sample('unused')[0],0)

    def test_missing_script_and_changed_source_bytes_block(self):
        self.data['narration']={'script_file':'missing.txt','script_sha256':'a'*64}
        self.assertEqual(self.run_sample('missing')[0],1)
        self.data.pop('narration');(self.root/'asset.txt').write_text('before')
        self.data['assets']=[{'id':'A1',**self.ref('asset.txt')}];self.data['shots'][0]['asset_ids']=['A1']
        (self.root/'asset.txt').write_text('after')
        self.assertEqual(self.run_sample('changed')[0],1)

    def test_child_mutation_of_input_never_records_success(self):
        (self.root/'asset.txt').write_text('before')
        self.data['assets']=[{'id':'A1',**self.ref('asset.txt')}];self.data['shots'][0]['asset_ids']=['A1']
        with (self.root/'adapter.py').open('a') as f:f.write('\npathlib.Path("asset.txt").write_text("after")\n')
        self.data['execution']['entrypoint']=self.ref('adapter.py')
        from origin_fixture import attach_origin_fixture
        attach_origin_fixture(self.data, self.root)
        code,r=self.run_sample();self.assertEqual(code,2);self.assertTrue(any('input bytes changed' in e for e in r['output_checks']))

    def test_pure_g3_review_updates_do_not_change_render_design(self):
        self.data['design']['keyframe_scales']={'whole_scene':{'file':'baseline.mp4','sha256':self.ref('baseline.mp4')['sha256'],'status':'pending','note':''}}
        old=gate.design_context(self.data,['SH1'])
        self.data['design']['approval']={'status':'pass','actual_feedback_ref':'synthetic later review'}
        self.data['design']['keyframe_scales']['whole_scene'].update(status='pass',note='later real review declaration')
        self.assertEqual(old,gate.design_context(self.data,['SH1']))
        self.data['design']['keyframe_scales']['whole_scene']['sha256']='a'*64
        self.assertNotEqual(old,gate.design_context(self.data,['SH1']))

    def test_lock_cannot_be_created_inside_skill(self):
        with self.assertRaises(ValueError):gate.make_lock(Path(gate.SKILL_ROOT)/'must-not-create.json')


    def prepared_sample(self):
        self.assertEqual(self.run_sample()[0],0)
        self.data['execution']['sample_receipt']=self.ref('run1.json')
        animation=self.data['qa']['visual_frames']['animation']
        animation.update(next_action='expand',viewing={**copy.deepcopy(self.data['design']['approved_film_reference']['viewing']),
             **self.ref('sample1.mp4'), 'scope':'representative', 'reviewer':'independent synthetic reviewer', 'reviewed_at':gate.now()},
             independent_review_evidence=self.ref('approval.txt'),
             style_comparison={'status':'pass','actually_compared':True,'baseline_sha256':self.ref('baseline.mp4')['sha256'],
                 'sample_sha256':self.ref('sample1.mp4')['sha256'],'observation':'Synthetic same-style comparison, no actual perception.'})
        self.save()

    def test_full_invocation_after_sample_uses_same_adapter_and_all_shots(self):
        self.prepared_sample()
        # Isolate the new entry gate; existing G3 has its own full regression suite.
        with patch('stage_checks.check_stage',return_value=[]) as g3:
            code,r=gate.run_render(self.root/'episode.json','full',['SH1'],'full.mp4','full-run.json')
        self.assertEqual(code,0);self.assertEqual(r['phase'],'full')
        self.assertTrue(all(call.args[2]=='G3' for call in g3.call_args_list))
        self.assertEqual(json.loads((self.root/'invoked.json').read_text())['phase'],'full')

    def test_sample_comparison_pending_cannot_expand(self):
        self.prepared_sample();self.data['qa']['visual_frames']['animation']['style_comparison']['status']='pending'
        with patch('stage_checks.check_stage',return_value=[]):errors=gate.preflight(self.data,self.root,'full',['SH1'])
        self.assertTrue(any('same-style sample comparison' in e for e in errors))

    def test_sample_viewing_must_follow_actual_render(self):
        self.prepared_sample();self.data['qa']['visual_frames']['animation']['viewing']['reviewed_at']='2020-01-01T00:00:00Z'
        with patch('stage_checks.check_stage',return_value=[]):errors=gate.preflight(self.data,self.root,'full',['SH1'])
        self.assertTrue(any('viewed after its render' in e for e in errors))

    def test_known_audio_failure_cannot_expand_even_with_g3_declaration(self):
        self.prepared_sample();self.data['qa']['audio']={'status':'fail'}
        with patch('stage_checks.check_stage',return_value=[]):errors=gate.preflight(self.data,self.root,'full',['SH1'])
        self.assertTrue(any('known audio failure' in e for e in errors))

    def test_sample_selection_cannot_silently_be_full_missing_shots(self):
        self.data['shots'].append({'id':'SH2','shotbook':{}})
        self.assertEqual(self.run_sample()[0],0)
        with patch('stage_checks.check_stage',return_value=[]):errors=gate.preflight(self.data,self.root,'full',['SH1'])
        self.assertTrue(any('every designed shot' in e for e in errors))

    def test_unplanned_connector_blocks_real_adapter_before_any_output(self):
        self.data['shots'][0]['shotbook']['connections']={'applicable':True,'links':[]}
        code,r=self.run_sample();self.assertEqual(code,1);self.assertFalse((self.root/'invoked.json').exists())
        self.assertTrue(any('connection topology required' in e for e in r['preflight_errors']))


if __name__=='__main__':unittest.main()
