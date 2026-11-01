"""Focused candidate-only gate regressions. Synthetic bytes are never media approval.

The real check_stage, check_episode.check and render_gate.preflight execute.
Only deterministic probing/decoding/ROI measurements are mocked. All admission,
current byte hashes, feedback, viewing, stage and receipt validation execute.
No subprocess executes.
"""
from pathlib import Path
import copy, hashlib, importlib.util, json, sys, tempfile, unittest
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import patch

# This test belongs in the maintained repository's tests/ directory and reuses
# its public synthetic stage fixture. No installed Skill or user media is edited.
sys.path.insert(0,str(Path(__file__).resolve().parent))
import stage_fixture
from stage_fixture import gates as stage
import check_episode as check
import render_gate, subject_motion, origin_fixture
from feedback_guard import feedback_context_sha256
TEST_TMP_ROOT=Path(tempfile.gettempdir()).resolve()

def fake_screen(path,regions,settings):
 return {'schema_version':1,'kind':'subject_roi_screen_only','media_sha256':stage.file_digest(Path(path)),
         'duration':1.,'settings':settings,'regions':regions,'low_motion_ranges':[], 'longest_low_motion_seconds':0}

def probe(args,**kwargs):
 exe=Path(str(args[0])).stem
 if exe=='ffprobe':
  path=Path(args[-1]);size=(1920,1080)
  if path.suffix=='.png':
   from PIL import Image
   with Image.open(path) as im:size=im.size
  if path.suffix=='.png':
   return SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'1','format_name':'png_pipe'},'streams':[{'codec_type':'video','width':size[0],'height':size[1],'codec_name':'png','nb_read_frames':'1'}]}),stderr='')
  return SimpleNamespace(returncode=0,stdout=json.dumps({'format':{'duration':'1'},'streams':[
   {'codec_type':'video','width':size[0],'height':size[1],'sample_aspect_ratio':'1:1','r_frame_rate':'25/1'}, {'codec_type':'audio'}]}),stderr='')
 if exe=='ffmpeg' and '-f' in args and 'null' in args:
  return SimpleNamespace(returncode=0,stdout='',stderr='')
 raise AssertionError('Forbidden subprocess: '+str(args))

class GatesRegression(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=TEST_TMP_ROOT);self.root=Path(self.tmp.name)
  assert self.root.resolve().is_relative_to(TEST_TMP_ROOT.resolve())
  self.addCleanup(self.tmp.cleanup)
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  self.stack.enter_context(patch('subprocess.run',side_effect=probe))
  self.stack.enter_context(patch('shutil.which',side_effect=lambda name: name if name in ('ffprobe','ffmpeg') else None))
  self.stack.enter_context(patch.object(subject_motion,'screen',side_effect=fake_screen))
  # Actual current byte hashing, viewing coverage, feedback and receipts remain real.
  (self.root/'synthetic.bin').write_bytes(b'SYNTHETIC DETERMINISTIC BYTES; NOT ACTUAL MEDIA')
  (self.root/'audio.bin').write_bytes(b'SYNTHETIC AUDIO SOURCE BYTES; NOT ACTUAL AUDIO')
  from cover_fixture import png
  png(self.root/'p.png',48,64);png(self.root/'l.png',64,48)
  project=Path(stage_fixture.__file__).resolve().parents[1]
  (self.root/'topic-anchor.json').write_bytes((project/'examples/blue-sky/topic-anchor.json').read_bytes())
  d=json.loads((project/'examples/blue-sky/episode.json').read_text())
  d['assets']=[{'id':'A1','kind':'simulation','source':'original synthetic software fixture','creator':'test harness','file':'synthetic.bin','rights':{'status':'cleared','evidence':'test only','scope':'local software tests'},'disclosure':'synthetic software fixture'},
   {'id':'VOICE','kind':'audio','source':'synthetic source','creator':'test harness','file':'audio.bin','rights':{'status':'cleared','evidence':'test only','scope':'local tests'},'disclosure':'synthetic voice software fixture'}]
  d['narration'].update(asset_id='VOICE',status='ready',language='zh-CN',voice_type='synthetic',disclosure='synthetic test voice',series_sample_reference='synthetic test sample declaration only')
  d['shots']=[{'id':'SH1','modality':'pure_2d','claim_ids':['C1'],'asset_ids':['A1'],'visual_note':'software fixture only','shotbook':{
   'start':0,'end':1,'subject':'test shape','action':'state changes','framing':'wide','claim_support':'fixture only','motion_purpose':'test relation',
   'beats':[{'at':0,'trigger_words':'fixture','attention_subject':'test shape','action':'state changes'}],
   'candidates':[{'source':'synthetic fixture','viewing_note':'test only','decision_reason':'isolated test input','selected':True,'asset_id':'A1','source_interval':'full'}],
   'alternatives_note':'one deterministic fixture', 'keyframe_review':{'status':'pass','file':'p.png','sha256':stage.file_digest(self.root/'p.png'),'note':'fixture only'},
   'visual_logic':{'review_scope':'final_export','orientation':{'applicable':False,'reason':'synthetic solid shape'},'graphics':[],'no_graphics_reason':'no arrows'}}}]
  d['deliverables']={'video':'synthetic.bin','cover_3_4':'p.png','cover_4_3':'l.png'}
  d['qa']={k:{'status':'pass','note':'SYNTHETIC SOFTWARE DECLARATION ONLY'} for k in check.REVIEW_KEYS}
  d['qa']['narration']['review_scope']='final_export';d['qa']['shotbook']={'status':'pass','note':'synthetic audiovisual declaration only'}
  d['qa']['comprehension']={'status':'editor_reviewed','note':'synthetic declaration only','audience_feedback_reference':''}
  d['qa']['mobile_preview'].update(review_scope='target_platform',surface='desktop_platform_preview',platform='synthetic',account='synthetic')
  d['qa']['mobile_preview']['reviewed_metadata_sha256']=check.platform_metadata_sha256(d,d['qa']['mobile_preview'])
  d['qa']['reviewed_sha256']={k:stage.file_digest(self.root/v) for k,v in d['deliverables'].items()}
  for key in ('opening','ending'):d['topic_alignment'][key]['shot_ids']=['SH1']
  for c in d['topic_alignment']['coverage']:c['shot_ids']=['SH1']
  d['qa']['topic_alignment']={'status':'pass','reviewer_role':'independent',**{key:{'status':'pass','note':'synthetic declaration','evidence':'fixture only'} for key in ('opening_title','opening_voiceover','coverage','ending')}}
  d['qa']['topic_alignment']['opening_voiceover'].update(review_scope='final_export',heard_question='synthetic question',heard_answer_route='synthetic answer')
  self.d=stage_fixture.upgrade(d,self.root)
  self.d['design']['approved_film_reference']={'kind':'initial_style_reference','reference':{'file':'p.png','sha256':stage.file_digest(self.root/'p.png')},'actually_opened':True,'selection_reason':'synthetic test reference only','applicable_style':'synthetic test shape','observation':'synthetic declaration, no perception','reviewer':'synthetic fixture','reviewed_at':'2026-01-01T00:00:00Z'}
  origin_fixture.attach_origin_fixture(self.d,self.root)
  stage_fixture.refresh(self.d)
  self.d['qa']['shotbook']['reviewed_sha256']=check.shotbook_sha256(self.d)
  self.d['qa']['topic_alignment']['reviewed_sha256']=check.topic_review_sha256(self.d)

 def ref(self,name):return {'file':name,'sha256':stage.file_digest(self.root/name)}
 def write(self,name,value):
  (self.root/name).write_text(json.dumps(value),encoding='utf-8');return self.ref(name)
 def errors(self,target='G3'):return stage.check_stage(self.d,self.root,target)
 def complete(self,target='delivery'):return check.check(self.d,self.root,target)[0]
 def assert_reject(self,needle,target='G3'):
  errors=self.errors(target);self.assertTrue(any(needle in e for e in errors),errors)
 def rebind_later(self):
  # Deliberately leave the original G2 evidence, digest and receipt untouched.
  saved=copy.deepcopy({k:self.d['qa'][k] for k in ('shotbook','expression_plan')});g2=copy.deepcopy(self.d['qa']['gates']['G2'])
  extra={k:copy.deepcopy(self.d['qa'][k]['G2']) for k in ('presentation_text',)}
  continuity=copy.deepcopy(self.d['qa']['audio']['continuity']['G2'])
  stage_fixture.refresh(self.d)
  for k,v in saved.items():self.d['qa'][k]=v
  self.d['qa']['gates']['G2']=g2
  for k,v in extra.items():self.d['qa'][k]['G2']=v
  self.d['qa']['audio']['continuity']['G2']=continuity
  self.d['qa']['topic_alignment']['reviewed_sha256']=check.topic_review_sha256(self.d)
 def migrate_g2(self):
  self.d['execution']['contract_version']=2
  # Explicit synthetic receipt, shaped exactly as validator requires; no render
  # or perceptual claim is made. Real validations bind bytes/plan/output/timing.
  record={'kind':'guarded_render_receipt','schema_version':1,'phase':'roughcut','result':'rendered_unreviewed','returncode':0,'preflight_errors':[],
   'shot_ids':['SH1'],'roughcut_plan_sha256':render_gate.roughcut_plan_context(self.d),
   'skill_tree_sha256':render_gate.skill_snapshot()['tree_sha256'],
   'started_at':'2025-12-31T00:00:01Z','completed_at':'2025-12-31T00:00:02Z','output':self.ref('synthetic.bin')}
  self.d['execution']['roughcut_receipt']=self.write('roughcut-receipt.json',record)
  self.d['qa']['shotbook']['review_binding_version']=2
  stage_fixture.refresh(self.d)
  self.d['qa']['shotbook']['reviewed_sha256']=check.shotbook_sha256(self.d)
  self.d['qa']['topic_alignment']['reviewed_sha256']=check.topic_review_sha256(self.d)
 def bridge(self,scope='whole_episode'):
  oldsha='a'*64;sha=self.d['qa']['visual_frames']['animation']['viewing']['sha256']
  change=self.write('change.json',{'synthetic':'rule fix only'})
  regression=self.write('regression.json',{'rule_id':'repair-bridge','rule_version':'candidate','change_sha256':change['sha256'],'command':'synthetic test fixture','executed':True,'exit_code':0,'result':'tests_pass'})
  row={'contract_version':1,'feedback_id':'F1','origin':'user','source_ref':'synthetic-source','received_at':'2026-01-01','original_feedback':'synthetic broad visual failure',
   'media_version':'synthetic-old','media_sha256':oldsha,'scope':'full original stated failure scope','scope_kind':scope,'time_range_s':[],
   'applies_to_gates':['G3'],'dimensions':{'art':{'status':'fail','note':'synthetic failure'}},'what_changes':'complete repair including transition joins','status':'resolved','repair_time_range_s':[0,1],
   'skill_update':{'disposition':'execution_fix','proposed_change':'synthetic correction','status':'implemented','rule_id':'repair-bridge','rule_version':'candidate','change_evidence':change,'regression_evidence':[regression]},
   'repair_artifacts':[self.ref('synthetic.bin')]}
  review={'feedback_id':'F1','feedback_context_sha256':feedback_context_sha256(row),'media_sha256':sha,'status':'pass','scope_kind':scope,'source_time_range_s':[],
   'scope_mapping':'original broad failure rechecked on complete current repair and its joins; final film still requires full retest','ranges':[[0,.5],[.5,1]],'scope':'complete current representative repair and joins',
   'reviewer':'synthetic-checker','actual_viewed':True,'observation':'synthetic complete cycle + entry and exit joins','normal_speed_continuous_av':True,'dimension_results':{'art':{'status':'pass','observation':'synthetic repair declaration'}}}
  row['retest_evidence']=[self.write('retest.json',review)]
  self.d['qa']['feedback']=[row];self.d['qa']['feedback_expected_ids']=['F1']
  failure={'id':'legacy-F1','scope':scope,'note':'original legacy failure retained','status':'resolved','feedback_id':'F1'}
  failure['resolution']={'binding_version':2,'feedback_id':'F1','legacy_failure_sha256':stage.legacy_failure_sha256(failure),
   'scope':'representative_repair','evidence':'linked retest.json','context_sha256':stage.context_sha256(self.d,'G3'),'sha256':sha}
  self.d['qa']['visual_frames']['failures']=[failure]
  return row,review,failure
 def save_review(self,row,review):row['retest_evidence']=[self.write('retest.json',review)]

 def full_preflight(self):
  animation=self.d['qa']['visual_frames']['animation']
  sample={'kind':'guarded_render_receipt','schema_version':1,'phase':'sample','result':'rendered_unreviewed','returncode':0,'preflight_errors':[],
   'shot_ids':['SH1'],'design_sha256':render_gate.design_context(self.d,['SH1']),'skill_tree_sha256':render_gate.skill_snapshot()['tree_sha256'],
   'started_at':'2025-12-31T00:00:01Z','completed_at':'2025-12-31T00:00:02Z','output':{k:animation['viewing'][k] for k in ('file','sha256')}}
  self.d['execution']['sample_receipt']=self.write('sample-receipt.json',sample)
  animation['style_comparison']={'status':'pass','baseline_sha256':self.ref('p.png')['sha256'],'sample_sha256':animation['viewing']['sha256'],'actually_compared':True,'observation':'synthetic comparison'}
  return render_gate.preflight(self.d,self.root,'full',['SH1'])
 def risk_relation_fixture(self):
  alignment=self.d['topic_alignment'];coverage=alignment['coverage'][0];old=coverage['causal_steps'][0]['id']
  original=copy.deepcopy(coverage['causal_steps'][0]);chain=[]
  for index in range(1,5):
   step=copy.deepcopy(original);step.update(id='MAIN'+str(index),key_difficulty=index in (2,3));chain.append(step)
  chain[1].update(before='established entry condition',change='actuator starts complete action',after='response begins',handoff='continuous join to response/result')
  chain[2].update(before='observed response begins',change='response reaches full visible result',after='stable explained result',handoff='exit join into later production context')
  coverage['causal_steps']=chain
  oldcard=next(card for card in alignment['expression_cards'] if old in card['step_ids'])
  oldcard.update(id='RISK',step_ids=['MAIN2','MAIN3'],difficulty='Actuator response and complete result are the actual new implementation risk',
   prerequisites=['Established entry condition and object identity from MAIN1'],visual_action='complete actuator action through response and stable result with entry/exit joins',inferable_outcome='the connected action produces the complete visible result')
  all_steps=[step['id'] for c in alignment['coverage'] for step in c['causal_steps']]
  cards=[card['id'] for card in alignment['expression_cards']]
  animation=self.d['qa']['visual_frames']['animation'];animation.update(selection_mode='risk_relation',expression_card_ids=['RISK'],step_ids=['MAIN2','MAIN3'],
   scope_note='MAIN1 establishes prerequisite and entry condition; this sample shows complete action, response and result of MAIN2/MAIN3, including entry and exit joins; MAIN4 remains full-film scope')
  observed=copy.deepcopy(animation['steps'][0]);animation['steps']=[dict(copy.deepcopy(observed),step_id=i,observed_change='complete action through response and stable result',handoff_observed='entry/exit joins observed continuously') for i in animation['step_ids']]
  self.d['qa']['visual_frames']['process_steps']=[{'step_id':i,'status':'pass','evidence':'synthetic full-film step observation'} for i in all_steps]
  for name in ('explanation_logic','expression_plan','explanation_review','expression_review'):
   record=self.d['qa'][name];record['reviewed_step_ids']=all_steps[:]
   if name.startswith('expression'):record['expression_card_ids']=cards[:]
   if 'steps' in record:
    observed=copy.deepcopy(record['steps'][0]);record['steps']=[dict(copy.deepcopy(observed),step_id=i) for i in all_steps]
  for gate,parent in (('G2',self.d['qa']['shotbook']),('G3',animation),('G5',self.d['qa']['visual_frames'])):
   record=parent['subject_motion'];ids=animation['step_ids'] if gate=='G3' else all_steps
   for unit in record['semantic_units']:unit['step_ids']=ids[:]
   for unit in record['object_result_review']['units']:unit['step_ids']=ids[:]
  stage_fixture.refresh(self.d)
  self.d['qa']['shotbook']['reviewed_sha256']=check.shotbook_sha256(self.d)
  self.d['qa']['topic_alignment']['reviewed_sha256']=check.topic_review_sha256(self.d)
  return all_steps
 def test_risk_relation_complete_middle_group_can_pass_actual_g3(self):
  all_steps=self.risk_relation_fixture();self.assertGreater(len(all_steps),2)
  self.assertEqual(self.errors(),[])
  self.assertEqual(self.complete(),[])
  self.d['deliverables'].pop('video');self.d['qa']['reviewed_sha256'].pop('video')
  self.assertEqual(self.full_preflight(),[])
 def test_risk_relation_may_be_one_complete_causal_step(self):
  self.risk_relation_fixture();animation=self.d['qa']['visual_frames']['animation']
  self.d['topic_alignment']['coverage'][0]['causal_steps'][1].update(change='complete actuator action, response and stable result',after='stable result with connected identity')
  self.d['topic_alignment']['coverage'][0]['causal_steps'][2]['key_difficulty']=False
  self.d['topic_alignment']['expression_cards'][0]['step_ids']=['MAIN2']
  animation['step_ids']=['MAIN2'];animation['steps']=animation['steps'][:1]
  for unit in animation['subject_motion']['semantic_units']:unit['step_ids']=['MAIN2']
  for unit in animation['subject_motion']['object_result_review']['units']:unit['step_ids']=['MAIN2']
  stage_fixture.refresh(self.d);self.assertEqual(self.errors(),[])
 def test_risk_relation_card_can_bridge_adjacent_primary_scope_partitions(self):
  self.risk_relation_fixture();alignment=self.d['topic_alignment'];moved=alignment['coverage'][0]['causal_steps'].pop(2)
  alignment['coverage'][1]['causal_steps'].insert(0,moved)
  stage_fixture.refresh(self.d);self.assertEqual(self.errors(),[])
 def test_risk_relation_explicit_no_prerequisites_is_valid(self):
  self.risk_relation_fixture();self.d['topic_alignment']['expression_cards'][0]['prerequisites']=[]
  self.d['qa']['visual_frames']['animation']['scope_note']='No external prerequisites: entry object identity is established inside this complete action, response, result and exit-join sample'
  stage_fixture.refresh(self.d);self.assertEqual(self.errors(),[])
 def test_legacy_selection_still_requires_complete_primary_chain(self):
  self.risk_relation_fixture();animation=self.d['qa']['visual_frames']['animation'];animation.pop('selection_mode');animation.pop('expression_card_ids')
  stage_fixture.refresh(self.d);self.assert_reject('complete primary explanation chain')
 def test_risk_relation_partial_unknown_missing_scope_and_wrongmedia_fail(self):
  self.risk_relation_fixture();baseline=copy.deepcopy(self.d)
  for label,mutation,needle in (
   ('partial_card',lambda:animation.update(step_ids=['MAIN2']),'exactly cover complete'),
   ('unknown_card',lambda:animation.update(expression_card_ids=['UNKNOWN']),'existing expression_card_ids'),
   ('missing_cards',lambda:animation.pop('expression_card_ids'),'existing expression_card_ids'),
   ('missing_scope',lambda:animation.pop('scope_note'),'scope_note'),
   ('boolean_scope',lambda:animation.update(scope_note=True),'scope_note'),
   ('wrong_media',lambda:animation['viewing'].update(sha256='0'*64),'hash stale'),
   ('unknown_mode',lambda:animation.update(selection_mode='arbitrary_subset'),'unknown representative'),
   ('not_primary',lambda:self.d['topic_alignment'].update(main_scope_ids=[self.d['topic_alignment']['coverage'][1]['scope_id']]),'primary explanation scope')):
   with self.subTest(label=label):
    self.d=copy.deepcopy(baseline);animation=self.d['qa']['visual_frames']['animation'];mutation();self.assert_reject(needle)
 def test_risk_relation_does_not_clear_false_or_open_failure_history(self):
  self.risk_relation_fixture();self.d['qa']['visual_frames']['status']='fail'
  self.d['qa']['visual_frames']['failures']=[{'id':'original','scope':'whole_episode','note':'unresolved implementation failure','status':'open'}]
  self.assert_reject('blocks expansion')
 def test_risk_relation_selection_contract_is_context_bound(self):
  self.risk_relation_fixture();original=stage.context_sha256(self.d,'G3')
  for key,value in (('selection_mode','full_chain'),('expression_card_ids',[]),('scope_note','changed reviewed relation boundary')):
   animation=self.d['qa']['visual_frames']['animation'];saved=animation[key];animation[key]=value
   self.assertNotEqual(original,stage.context_sha256(self.d,'G3'));animation[key]=saved
 def test_risk_relation_never_relaxes_g2_or_g5_full_scope(self):
  self.risk_relation_fixture();self.d['qa']['expression_plan']['reviewed_step_ids']=['MAIN2','MAIN3']
  self.assert_reject('complete explanation step review','G2')
  self.d['qa']['expression_plan']['reviewed_step_ids']=[step['id'] for c in self.d['topic_alignment']['coverage'] for step in c['causal_steps']]
  self.d['qa']['visual_frames']['process_steps']=[row for row in self.d['qa']['visual_frames']['process_steps'] if row['step_id'] in ('MAIN2','MAIN3')]
  self.assert_reject('full primary explanation evidence incomplete','G5')
 def test_fixture_valid_complete_path(self):self.assertEqual(self.complete(),[])
 def test_bridge_all_visual_scopes_unblocks_real_g3_and_full_preflight(self):
  for scope in ('whole_episode','series_style','segment'):
   self.bridge(scope)
   self.d['deliverables'].pop('video',None);self.d['qa']['reviewed_sha256'].pop('video',None)
   self.assertEqual(self.errors(),[])
   # The full preflight, including G3 and the sample receipt, executes unchanged.
   self.assertEqual(self.full_preflight(),[])
 def test_bridge_g4_no_g5_binding(self):
  self.bridge();self.assertEqual(self.errors('G4'),[])
 def test_bridge_negative_scope_open_unreviewed_wrongmedia_and_gap(self):
  row,review,failure=self.bridge();baseline=copy.deepcopy(self.d)
  for label,mutation,needle in (
   ('open',lambda:failure.update(status='open'),'blocks expansion'),
   ('wrongscope',lambda:row.update(scope_kind='segment'),'preserve original'),
   ('unreviewed',lambda:review.update(actual_viewed=False),'actual viewing'),
   ('wrongmedia',lambda:review.update(media_sha256='b'*64),'repaired media'),
   ('gap',lambda:review.update(ranges=[[0,.4],[.6,1]]),'does not cover'),
   ('partial',lambda:row.update(repair_time_range_s=[.2,1]),'partial repair'),
   ('wrong_sample',lambda:failure['resolution'].update(sha256='b'*64),'stale media'),
   ('original_changed',lambda:failure.update(note='altered original'),'retained original'),
   ('missingmigration',lambda:failure['resolution'].pop('binding_version'),'stale media')):
   with self.subTest(label=label):
    self.d=copy.deepcopy(baseline);row=self.d['qa']['feedback'][0];failure=self.d['qa']['visual_frames']['failures'][0];review=json.loads((self.root/'retest.json').read_text())
    # Restore same baseline retest before mutation.
    review.update(actual_viewed=True,media_sha256=self.ref('synthetic.bin')['sha256'],ranges=[[0,.5],[.5,1]])
    mutation();self.save_review(row,review);self.assert_reject(needle)
 def test_nonexpanding_repair_still_cannot_claim_stale_current_closure(self):
  row,review,failure=self.bridge();self.d['qa']['visual_frames']['animation']['next_action']='repair_sample'
  (self.root/'older-repair.bin').write_bytes(b'OLDER SYNTHETIC REPAIR')
  older=self.ref('older-repair.bin');row['repair_artifacts']=[older];review['media_sha256']=older['sha256'];self.save_review(row,review)
  self.assert_reject('current repair media')
 def test_sample_repair_never_approves_g5_new_final(self):
  row,review,failure=self.bridge()
  self.assert_reject('stale media/context','G5')
  (self.root/'new-final.bin').write_bytes(b'NEW SYNTHETIC FINAL; NO REAL MEDIA')
  self.d['deliverables']['video']='new-final.bin';self.d['qa']['reviewed_sha256']['video']=stage.file_digest(self.root/'new-final.bin')
  stage_fixture.refresh(self.d)
  failure['resolution'].update(context_sha256=stage.context_sha256(self.d,'G5'),sha256=self.d['qa']['reviewed_sha256']['video'],scope='full_episode')
  self.assert_reject('stale retest','G5')
 def test_explicit_final_retest_and_binding_valid(self):
  row,review,failure=self.bridge()
  failure['resolution'].update(context_sha256=stage.context_sha256(self.d,'G5'),scope='full_episode')
  self.assert_reject('full-film retest','G5')
  review['scope']='full_episode';self.save_review(row,review)
  self.assertEqual(self.errors('G5'),[])
 def test_incomplete_cycle_and_join_evidence_still_block_expansion(self):
  self.bridge();baseline=copy.deepcopy(self.d)
  self.d['qa']['visual_frames']['animation']['steps'][0]['handoff_observed']=''
  self.assert_reject('handoff_observed')
  self.d=copy.deepcopy(baseline)
  self.d['qa']['visual_frames']['animation']['viewing']['ranges']=[[0,.8]]
  self.assert_reject('full evidence clip')
 def test_linked_passing_feedback_cannot_erase_original_failed_history(self):
  row,review,failure=self.bridge();row['dimensions']['art']['status']='pass'
  review['feedback_context_sha256']=feedback_context_sha256(row);self.save_review(row,review)
  self.assert_reject('original failed dimensions')
 def test_v2_bookkeeping_keeps_original_g2_through_complete_delivery_and_g5(self):
  self.migrate_g2();original=copy.deepcopy(self.d['qa']['shotbook']);g2=copy.deepcopy(self.d['qa']['gates']['G2'])
  self.d['shots'][0]['shotbook'].update(status='refined',render_file='later.bin',render_sha256='c'*64,keyframe_review={'status':'pass','file':'p.png','sha256':stage.file_digest(self.root/'p.png'),'note':'later art'})
  self.rebind_later()
  self.assertEqual(self.d['qa']['shotbook'],original);self.assertEqual(self.d['qa']['gates']['G2'],g2)
  for target in ('delivery','G5'):self.assertEqual(self.complete(target),[])
 def test_v2_semantic_timing_audio_declaration_rejected_full_path(self):
  self.migrate_g2();baseline=copy.deepcopy(self.d)
  for label,mutation in (
   ('action',lambda:self.d['shots'][0]['shotbook'].update(action='different explanation')),
   ('timing',lambda:self.d['shots'][0]['shotbook'].update(end=.9)),
   ('narration',lambda:self.d['narration'].update(audio_sha256='0'*64))):
   with self.subTest(label=label):
    self.d=copy.deepcopy(baseline);mutation();errors=self.complete();self.assertTrue(any('G2' in e or 'shotbook: stale' in e for e in errors),errors)
 def test_v2_actual_audio_bytes_rejected_full_path(self):
  self.migrate_g2();(self.root/'audio.bin').write_bytes(b'CHANGED AUDIO SOURCE BYTES')
  errors=self.complete();self.assertTrue(any('source narration evidence hash stale' in e or 'audio changed' in e for e in errors),errors)
 def test_v2_actual_roughcut_bytes_rejected_full_path(self):
  self.migrate_g2();(self.root/'synthetic.bin').write_bytes(b'CHANGED ROUGHCUT BYTES; AUDIO UNCHANGED')
  errors=self.complete();self.assertTrue(any('roughcut output evidence hash stale' in e or 'G2 roughcut evidence hash stale' in e for e in errors),errors)
 def test_v2_actual_narration_script_bytes_rejected_full_path(self):
  self.migrate_g2();(self.root/'script.txt').write_text('CHANGED NARRATION WORDS')
  errors=self.complete();self.assertTrue(any('narration script evidence hash stale' in e for e in errors),errors)
 def test_v2_roughcut_declaration_change_rejected(self):
  self.migrate_g2();self.d['qa']['shotbook']['viewing']['sha256']='0'*64
  errors=self.complete();self.assertTrue(any('G2' in e or 'actual roughcut output' in e for e in errors),errors)
 def test_legacy_digest_and_migration_boundary_preserved(self):
  original=self.d['qa']['shotbook']['reviewed_sha256'];raw=hashlib.sha256(json.dumps({'audio_sha256':self.d['narration'].get('audio_sha256'),'shots':self.d.get('shots'),'assets':self.d.get('assets')},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  self.assertEqual(original,raw)
  self.d['shots'][0]['shotbook']['status']='later bookkeeping';self.rebind_later()
  self.assertTrue(any('qa.shotbook: stale' in e for e in self.complete()))
  self.d['qa']['shotbook']['review_binding_version']=2
  self.assertTrue(any('requires explicit execution' in e for e in self.complete()))
 def test_fresh_shotbook_hash_alone_cannot_approve_changed_semantics(self):
  self.migrate_g2();self.d['shots'][0]['shotbook']['action']='changed actual explanation'
  self.d['qa']['shotbook']['reviewed_sha256']=check.shotbook_sha256(self.d)
  errors=self.complete()
  self.assertTrue(any('roughcut G2 plan changed' in e for e in errors),errors)
  self.assertTrue(any('G2 stale stage context' in e for e in errors),errors)
 def test_contract_v2_alone_does_not_reinterpret_old_hash(self):
  original=self.d['qa']['shotbook']['reviewed_sha256'];self.d['execution']['contract_version']=2
  self.assertEqual(check.shotbook_sha256(self.d),original)
 def test_scorecard_absent_and_null_scaffold_passes_g5(self):
  self.d['qa'].pop('scorecard');self.assertEqual(self.complete(),[])
  self.d['qa']['scorecard']={'scores':{k:{'score':None,'evidence':''} for k in ('understanding','art','motion','sound','packaging')},'total':None,'media_sha256':''}
  self.assertEqual(self.complete(),[])
 def test_diagnostic_all_four_total_eighty_passes(self):
  r=self.d['qa']['scorecard'];r['total']=80
  for e in r['scores'].values():e['score']=4
  self.assertEqual(self.complete(),[])
 def test_malformed_or_stale_diagnostic_rejected(self):
  baseline=copy.deepcopy(self.d)
  for value in (float('nan'),True,-1,5.5,4.2,'4'):
   self.d=copy.deepcopy(baseline);self.d['qa']['scorecard']['scores']['art']['score']=value
   self.assertTrue(any('score art' in e for e in self.complete()))
  self.d=copy.deepcopy(baseline);self.d['qa']['scorecard']['media_sha256']='0'*64
  self.assertTrue(any('scorecard stale' in e for e in self.complete()))
  self.d=copy.deepcopy(baseline);self.d['qa']['scorecard']['total']=100
  self.assertTrue(any('total inconsistent' in e for e in self.complete()))
 def test_high_score_cannot_bypass_real_quality_failure(self):
  r=self.d['qa']['scorecard'];r['total']=100
  for e in r['scores'].values():e['score']=5
  self.d['qa']['visual_frames']['animation']['steps'][0]['status']='fail'
  self.assertTrue(any('motion failed or unreviewed' in e for e in self.complete()))

if __name__=='__main__':unittest.main(verbosity=2)
