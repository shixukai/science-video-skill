"""Stage-record regression fixtures, never real media quality evidence."""
import copy,json,subprocess,tempfile,unittest
from pathlib import Path
from stage_fixture import gates,upgrade,refresh
class StageTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.tmp=tempfile.TemporaryDirectory();c.root=Path(c.tmp.name)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=blue:s=48x64:r=2','-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(c.root/'v.mp4')],check=True)
  d=json.loads((Path(__file__).resolve().parents[1]/'examples/blue-sky/episode.json').read_text());d['deliverables']={k:'v.mp4' for k in ('video','cover_3_4','cover_4_3')}
  d['qa']={k:{'status':'pass','note':'synthetic only'} for k in ('science','rights','visual_frames','audio','narration','covers','shotbook','mobile_preview')};d['qa']['mobile_preview'].update(platform='synthetic',account='synthetic');d['qa']['comprehension']={'status':'editor_reviewed','note':'synthetic only'};d['qa']['reviewed_sha256']={k:gates.file_digest(c.root/'v.mp4') for k in d['deliverables']};c.base=upgrade(d,c.root)
 @classmethod
 def tearDownClass(c):c.tmp.cleanup()
 def setUp(s):s.d=copy.deepcopy(s.base)
 def errors(s,stage='G6'):return gates.check_stage(s.d,s.root,stage)
 def rejects(s,part,stage='G6'):s.assertTrue(any(part in e for e in s.errors(stage)),s.errors(stage))
 def test_valid(s):s.assertEqual(s.errors(),[])
 def test_no_g2(s):s.d['qa']['gates']['G2']['status']='not_reviewed';s.rejects('G2 not passed','G3')
 def test_missing_chain(s):s.d['topic_alignment']['coverage'][0].pop('causal_steps');refresh(s.d);s.rejects('primary causal chain missing')
 def test_missing_shot(s):s.d['topic_alignment']['coverage'][0]['causal_steps'][0]['shot_ids']=['missing'];refresh(s.d);s.rejects('shot coverage missing')
 def test_missing_cause(s):s.d['topic_alignment']['coverage'][0]['causal_steps'][0]['change']='';refresh(s.d);s.rejects('change required')
 def test_static_board(s):s.d['qa']['visual_frames']['animation']['steps'][0]['representation']='static_board';s.rejects('static board/overlay')
 def test_overlay(s):s.d['qa']['visual_frames']['animation']['steps'][0]['representation']='overlay_only';s.rejects('static board/overlay')
 def test_sampled_frames(s):s.d['qa']['visual_frames']['animation']['viewing']['method']='sampled_frames';s.rejects('frame samples')
 def test_not_heard(s):s.d['qa']['shotbook']['viewing']['heard']=False;s.rejects('actual viewing and listening')
 def test_range_gap(s):s.d['qa']['visual_frames']['animation']['viewing']['ranges']=[[.2,1]];s.rejects('range gap')
 def test_partial(s):s.d['qa']['visual_frames']['animation']['viewing']['ranges']=[[0,.5]];s.rejects('full evidence clip')
 def test_old_media(s):s.d['qa']['visual_frames']['animation']['viewing']['sha256']='0'*64;s.rejects('hash stale')
 def test_plan_changed(s):s.d['shots'][0]['visual_note']='changed';s.rejects('stale stage context')
 def test_audio_changed(s):s.d['narration']['audio_sha256']='0'*64;s.rejects('stale animation')
 def test_step_missing(s):s.d['qa']['visual_frames']['animation']['steps'].pop();s.rejects('lacks continuous evidence')
 def test_local_cannot_clear(s):s.d['qa']['visual_frames']['failures']=[{'id':'F','scope':'whole_episode','note':'known','status':'open'}];s.rejects('local approval cannot overwrite')
 def test_repair_not_deadlocked(s):
  s.d['qa']['visual_frames']['status']='fail';s.d['qa']['visual_frames']['failures']=[{'id':'F','scope':'whole_episode','note':'known','status':'open'}];s.assertEqual(s.errors('G3'),[]);s.rejects('known failure blocks')
 def test_local_resolution(s):
  s.d['qa']['visual_frames']['failures']=[{'id':'F','scope':'whole_episode','note':'known','status':'resolved','resolution':{'scope':'local_sample','evidence':'test','sha256':s.d['qa']['reviewed_sha256']['video'],'context_sha256':gates.context_sha256(s.d,'G5')}}];s.rejects('local approval cannot resolve')
 def test_missing_phone(s):s.d['qa']['audio']['environments']=['headphones'];s.rejects('phone-speaker')
 def test_fake_score(s):s.d['qa']['scorecard']['total']=100;s.rejects('total inconsistent')
 def test_score_not_override(s):s.d['qa']['visual_frames']['status']='fail';s.rejects('referenced review not passed')
 def test_benchmark_no_people(s):s.d['brief']['production_class']='B';refresh(s.d);s.rejects('cold test missing')
 def test_new_video_old_review(s):s.d['deliverables']['video']='changed.mp4';refresh(s.d);s.rejects('must bind final deliverable')
 def test_unsafe_path(s):s.d['qa']['gates']['G1']['evidence'][0]['file']='../outside';s.rejects('path missing/unsafe')
 def test_bad_duration(s):s.d['qa']['visual_frames']['animation']['viewing']['duration']='one';s.rejects('duration must match')
 def test_bad_status(s):s.d['qa']['gates']['G3']['status']='approved';s.rejects('G3 not passed')
 def test_not_published(s):s.d['qa']['publication']['state']='submitted_unknown';s.rejects('publication not confirmed','G7')
 def test_changed_bundle(s):s.d['title']='changed';s.rejects('release approval stale')
 def test_bad_ids(s):s.d['topic_alignment']['main_scope_ids']=[{}];s.rejects('main_scope_ids')
 def test_history_missing(s):s.d['qa']['visual_frames'].pop('failures');s.rejects('failure history')
 def test_offset_warns_not_fails(s):
  s.d['shots'][0].setdefault('shotbook',{})['semantic_events']=[{'label':'test','audio_time_ms':0,'visual_time_ms':151}];refresh(s.d)
  s.assertEqual(len(gates.semantic_warnings(s.d)),1);s.assertEqual(s.errors(),[])
 def test_offset_at_threshold_not_warning(s):
  s.d['shots'][0].setdefault('shotbook',{})['semantic_events']=[{'label':'test','audio_time_ms':0,'visual_time_ms':150}];s.assertEqual(gates.semantic_warnings(s.d),[])
 def test_missing_scale_art(s):
  s.d['design']['keyframe_scales'].pop('mechanism_closeup');refresh(s.d);s.rejects('mechanism_closeup actual art review')
 def test_full_chain_review_missing(s):
  s.d['qa']['visual_frames']['process_steps'].pop();s.rejects('full primary causal chain evidence incomplete')
 def prepare_cold(s):
  s.d['brief']['validation_triggers']=['new_complex_mechanism'];r=s.d['qa']['comprehension'];r['status']='audience_checked'
  r['cold_view']={'status':'pass','shared_core_misconceptions':[],'group_id':'synthetic-five','sampling_plan_reference':'synthetic test plan, not real recruitment','actual_viewer_count':5,'passing_viewer_count':5,'media_sha256':s.d['qa']['reviewed_sha256']['video'],'viewers':[{'anonymous_id':'test-'+str(i),'real_person':True,'not_in_production':True,'no_relevant_training':True,'first_unprompted_normal_watch':True,'watched_current_version':True,'raw_answers':{k:'synthetic software fixture, not actual feedback' for k in ('topic','causal_chain','visualization_boundary','conclusion')},'scores':{'topic':1,'causal_chain':2,'visualization_boundary':0,'conclusion':1},'total':4,'scoring_evidence':'synthetic software fixture','core_misconceptions':[]} for i in range(5)]};refresh(s.d)
 def test_cold_fixture(s):s.prepare_cold();s.assertEqual(s.errors(),[])
 def test_duplicate_people(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][1]['anonymous_id']='test-0';s.rejects('ids missing/duplicate')
 def test_agents_not_people(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['real_person']=False;s.rejects('real_person required')
 def test_raw_answer_missing(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['raw_answers']['causal_chain']='';s.rejects('raw cold-test answer')
 def test_shared_misunderstanding(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers'][:2]:viewer['core_misconceptions']=['same-core-error']
  s.rejects('shared core misconception')
 def test_cause_incomplete_despite_total(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers'][:2]:viewer['scores']={'topic':1,'causal_chain':1,'visualization_boundary':1,'conclusion':1}
  s.rejects('four viewers')
 def test_not_five(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'].pop();s.rejects('five actual viewers')
 def test_overlap_cannot_hide_gap(s):s.d['qa']['shotbook']['viewing']['ranges']=[[0,.4],[0,.4],[.8,1]];s.rejects('range gap')
 def test_string_true_not_actual_watch(s):s.d['qa']['shotbook']['viewing']['watched']='true';s.rejects('actual viewing')
 def test_deprecated_asset(s):s.d['assets'][0]['catalog']['stage']='deprecated';refresh(s.d);s.rejects('catalog state blocks')
 def test_blocked_asset(s):s.d['assets'][0]['catalog']['stage']='blocked';refresh(s.d);s.rejects('catalog state blocks')
 def test_expired_rights(s):s.d['assets'][0]['catalog']['rights']['expires_on']='2000-01-01';refresh(s.d);s.rejects('rights expired')
 def test_source_script_stale(s):s.d['narration']['script_sha256']='0'*64;refresh(s.d);s.rejects('script evidence hash stale')
 def test_arbitrary_catalog_rule(s):s.d['assets'][1]['catalog']['rules']=['does-not-exist'];refresh(s.d);s.rejects('rules required/unknown')
 def test_calibration_needs_evidence(s):s.d['qa']['scorecard']['calibration']={};s.rejects('score calibration evidence file')
 def test_missing_misconception_record(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers']:viewer.pop('core_misconceptions')
  s.rejects('explicit core_misconceptions list')
 def test_malformed_misconception_record(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers']:viewer['core_misconceptions']={'shared':True}
  s.rejects('explicit core_misconceptions list')
 def test_unknown_trigger(s):s.d['brief']['validation_triggers']=['unclassified'];refresh(s.d);s.rejects('recognized values')
 def test_new_concept_requires_cold(s):s.d['brief']['validation_triggers']=['new_concept'];refresh(s.d);s.rejects('cold test missing')
 def test_sampled_routine_requires_cold(s):s.d['brief']['validation_triggers']=['routine_sample'];refresh(s.d);s.rejects('cold test missing')
 def test_major_modification_requires_cold(s):s.d['brief']['validation_triggers']=['major_modification'];refresh(s.d);s.rejects('cold test missing')
 def test_unselected_future_asset_allowed(s):
  asset=copy.deepcopy(s.d['assets'][0]);asset['id']='UNSELECTED';asset['catalog']['stage']='candidate';s.d['assets'].append(asset);s.assertEqual(s.errors('G3'),[])
 def test_real_video_not_svg(s):s.d['assets'][0]['catalog'].pop('viewBox');refresh(s.d);s.assertEqual(s.errors('G3'),[])
 def test_g4_does_not_require_release_covers(s):
  for key in ('cover_3_4','cover_4_3'):s.d['deliverables'].pop(key);s.d['qa']['reviewed_sha256'].pop(key)
  refresh(s.d);s.assertEqual(s.errors('G4'),[])
 def test_existing_style_benchmark_no_new_two_variants(s):s.d['brief']['production_class']='B';refresh(s.d);s.assertEqual(s.errors('G3'),[])
 def test_audio_failure_not_visual_failure(s):
  s.d['qa']['audio']['status']='fail';s.d['qa']['visual_frames']['failures']=[{'id':'F','scope':'audio','note':'sound only','status':'open'}];s.assertEqual(s.errors('G3'),[]);s.rejects('known failure blocks')
 def test_legacy_asset_failure_not_hidden(s):s.d['assets'][1]['science']={'status':'fail'};refresh(s.d);s.rejects('legacy science')
 def test_legacy_block_not_hidden(s):s.d['assets'][1]['catalog_state']='blocked';refresh(s.d);s.rejects('legacy asset state')
 def test_g3_caption_source_changed(s):
  file=s.root/s.d['qa']['visual_frames']['animation']['captions']['file'];original=file.read_bytes()
  try:file.write_text('changed');s.rejects('G3 representative captions evidence hash stale','G3')
  finally:file.write_bytes(original)
 def test_auxiliary_step_cannot_complete_primary(s):
  a=s.d['topic_alignment'];a['main_scope_ids']=[a['coverage'][0]['scope_id']];step=copy.deepcopy(a['coverage'][0]['causal_steps'][0]);step['id']='MAIN-LAST';a['coverage'][0]['causal_steps'].append(step);a['coverage'][1]['causal_steps']=[copy.deepcopy(a['coverage'][0]['causal_steps'][0])];r=s.d['qa']['visual_frames']['animation'];r['step_ids']=[r['step_ids'][0]];r['steps']=[r['steps'][0]];refresh(s.d);s.rejects('complete primary causal chain','G3')
 def test_phone_preview_required(s):s.d['qa']['mobile_preview']['phone']['status']='pending';refresh(s.d);s.rejects('actual phone readability')
 def test_ai_declaration_control_required(s):s.d['qa']['release']['ai_disclosure']['platform_declaration_used']=False;s.rejects('platform_declaration_used')
 def test_contrast_record_required(s):s.d['qa']['captions']['actual_contrast_checks']=[];s.rejects('contrast measurements required')
 def test_caption_checks_required(s):s.d['qa']['captions']['static_checks']={};s.rejects('caption checks unresolved')
 def test_flash_limit_false_blocks(s):s.d['qa']['flicker']['designed_flash_limit_checked']=False;s.rejects('flash design limit not checked')
 def test_real_capture_inner_failure(s):
  s.d['assets'][0]['catalog']['scientific_review']['status']='fail';refresh(s.d);s.rejects('explicit catalog scientific_review failure','G3')
 def test_real_capture_inner_approval_failure(s):
  s.d['assets'][0]['catalog']['approval']['status']='needs_changes';refresh(s.d);s.rejects('explicit catalog approval failure','G3')
 def test_real_capture_inner_denied_rights(s):
  s.d['assets'][0]['catalog']['rights']['status']='denied';refresh(s.d);s.rejects('explicit catalog rights failure','G3')
 def test_unknown_three_scale_dependency(s):
  s.d['design']['keyframe_scales']['whole_scene']['asset_ids']=['NO_SUCH_ASSET'];refresh(s.d);s.rejects('dependency cannot be resolved','G3')
 def test_final_caption_qa_wrong_file(s):s.d['qa']['captions'].update(file='missing.srt',sha256='0'*64);s.rejects('final caption QA must bind')
 def test_phone_null_geometry(s):s.d['qa']['mobile_preview']['phone']['actual_overlay_geometry']=[None];refresh(s.d);s.rejects('finite rectangle')
 def test_phone_outside_geometry(s):s.d['qa']['mobile_preview']['phone']['actual_overlay_geometry']=[{'x':0,'y':0,'width':1000,'height':1000}];refresh(s.d);s.rejects('outside declared canvas')
 def test_ready_transition_not_upstream_change(s):
  before={g:gates.context_sha256(s.d,g) for g in gates.GATES[:5]};s.d['scope']['publication_ready']=False
  s.assertEqual(before,{g:gates.context_sha256(s.d,g) for g in gates.GATES[:5]})
  s.assertEqual(s.errors('G5'),[])
  s.d['scope']['publication_ready']=True;s.assertEqual(s.errors('G6'),[])
 def test_chinese_language_alias(s):s.d['narration']['language']='zh-Hans';refresh(s.d);s.assertEqual(s.errors('G3'),[])
 def test_invalid_contrast_domain(s):s.d['qa']['captions']['actual_contrast_checks'][0]['ratio']=100;s.rejects('contrast measurement required')
 def test_style_rejection_blocks(s):s.d['design']['approval']['status']='fail';refresh(s.d);s.rejects('design approval missing/failed','G3')
 def test_style_scope_not_expanded(s):s.d['design']['approval']['scope']['visual_style']=False;refresh(s.d);s.rejects('does not cover visual style','G3')
 def test_style_feedback_not_board_path(s):s.d['design']['approval']['actual_feedback_ref']='';refresh(s.d);s.rejects('actual style feedback reference','G3')
 def test_ten_viewers_not_fixed_four_success(s):
  s.prepare_cold();r=s.d['qa']['comprehension']['cold_view']
  for i in range(5):
   viewer=copy.deepcopy(r['viewers'][0]);viewer['anonymous_id']='extra-'+str(i);viewer['scores']={k:0 for k in viewer['scores']};r['viewers'].append(viewer)
  r['viewers'][4]['scores']={k:0 for k in r['viewers'][4]['scores']};r['actual_viewer_count']=10;r['passing_viewer_count']=4;s.rejects('exactly five')
 def test_cold_count_summary_must_match(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['actual_viewer_count']=0;s.rejects('actual viewer count inconsistent')
 def test_cold_passing_summary_must_match(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['passing_viewer_count']=0;s.rejects('passing viewer count inconsistent')
 def test_unused_ai_not_current_content(s):
  s.d['narration']['voice_type']='human';s.d['qa']['release']['ai_disclosure'].update(contains_generated_content=False,not_applicable_reason='synthetic ordinary-content test')
  for asset in s.d['assets']:
   if asset['kind']=='ai_generated':asset['kind']='graphic'
  asset=copy.deepcopy(s.d['assets'][0]);asset.update(id='UNUSED_AI',kind='ai_generated');s.d['assets'].append(asset);refresh(s.d);s.assertEqual(s.errors(),[])
 def test_anchor_inventory_not_used(s):
  for shot in s.d['shots']:shot['asset_ids']=[i for i in shot['asset_ids'] if i!='A1']
  refresh(s.d);s.rejects('actually used real continuous-video anchor')
 def test_used_real_anchor_needs_viewing(s):s.d['assets'][0]['observation']['viewing_reference']='';refresh(s.d);s.rejects('source footage viewing required')
 def test_used_real_anchor_needs_interval(s):s.d['assets'][0]['observation']['source_interval']=[];refresh(s.d);s.rejects('actual footage interval required')


 def test_common_font_blocks_g3(s):
  a=next(a for a in s.d['assets'] if a['kind']=='font');s.d['design']['font_asset_id']=a['id'];refresh(s.d);s.assertEqual(s.errors('G3'),[]);a['rights']['status']='denied';s.rejects('stale stage context','G3');refresh(s.d);s.assertTrue(s.errors('G3'))
 def test_common_render_dependency_blocks_g3(s):
  a=s.d['assets'][0];s.d['design']['render_asset_ids']=[a['id']];refresh(s.d);a['rights']['status']='denied';refresh(s.d);s.assertTrue(s.errors('G3'))
 def test_dependency_mixed_types(s):
  for key,value in [('render_asset_ids',False),('font_asset_id',False)]:
   with s.subTest(key=key):
    s.d=copy.deepcopy(s.base);s.d['design'][key]=value;refresh(s.d);s.assertTrue(s.errors('G3'))
 def test_deliverable_dependency_string(s):
  s.d['deliverable_asset_ids']={'captions':'FONT'};refresh(s.d);s.rejects('must be an asset-ID list','G3')
 def test_listening_not_second_watch(s):
  for x in s.d['qa']['audio']['listening'].values():x['watched']=False
  s.assertEqual(s.errors('G5'),[])
 def test_listening_still_requires_heard(s):
  s.d['qa']['audio']['listening']['headphones']['heard']=False;s.rejects('actual listening required','G5')
 def test_cold_person_total(s):
  s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['total']=0;s.rejects('person total inconsistent')
 def test_cold_summary_shape(s):
  s.prepare_cold();s.d['qa']['comprehension']['cold_view']['shared_core_misconceptions']={};s.rejects('summary must equal')
 def test_cold_summary_consistency(s):
  s.prepare_cold();s.d['qa']['comprehension']['cold_view']['shared_core_misconceptions']=['invented'];s.rejects('summary must equal')

 def test_inherited_keyframe_dependency_bytes(s):
  a=copy.deepcopy(s.d['assets'][0]);a['id']='KEYFRAME_ONLY';a['file']='keyframe-only.mp4';path=s.root/a['file'];path.write_bytes((s.root/'v.mp4').read_bytes());a['sha256']=gates.file_digest(path);a['catalog']['rendered_file']=a['file'];a['catalog']['rendered_sha256']=a['sha256'];s.d['assets'].append(a);s.d['design']['keyframe_scales']['whole_scene']['asset_ids']=[a['id']];refresh(s.d)
  s.assertEqual(s.errors('G5'),[])
  try:
   path.write_bytes(path.read_bytes()+b'changed fixture');s.rejects('hash stale','G5')
  finally:path.unlink()
