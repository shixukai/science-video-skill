"""Stage-record regression fixtures, never real media quality evidence."""
import copy,json,subprocess,tempfile,unittest
from pathlib import Path
from stage_fixture import gates,upgrade,refresh
class CanonicalStageTests(unittest.TestCase):
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
 def test_g1_shot_order_change_invalidates_paper_review(s):
  s.d['shots'].reverse();s.rejects('stale context','G1')
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
 def test_benchmark_needs_no_people(s):s.d['brief']['production_class']='B';refresh(s.d);s.assertEqual(s.errors(),[])
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
  s.d['brief']['validation_triggers']=['new_complex_mechanism'];r=s.d['qa']['comprehension'];r['status']='audience_checked';r['audience_feedback_reference']='synthetic software fixture only'
  r['cold_view']={'status':'pass','shared_core_misconceptions':[],'group_id':'synthetic-five','sampling_plan_reference':'synthetic test plan, not real recruitment','actual_viewer_count':5,'passing_viewer_count':5,'media_sha256':s.d['qa']['reviewed_sha256']['video'],'viewers':[{'anonymous_id':'test-'+str(i),'real_person':True,'not_in_production':True,'no_relevant_training':True,'first_unprompted_normal_watch':True,'watched_current_version':True,'raw_answers':{k:'synthetic software fixture, not actual feedback' for k in ('topic','causal_chain','visualization_boundary','conclusion')},'scores':{'topic':1,'causal_chain':2,'visualization_boundary':0,'conclusion':1},'total':4,'scoring_evidence':'synthetic software fixture','core_misconceptions':[]} for i in range(5)]};r['optional_audience_feedback']=r['cold_view'];refresh(s.d)
 def test_optional_feedback_fixture(s):s.prepare_cold();s.assertEqual(s.errors(),[])
 def test_duplicate_people(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][1]['anonymous_id']='test-0';s.rejects('viewer ids missing/duplicate')
 def test_agents_not_people(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['real_person']=False;s.rejects('real_person required')
 def test_raw_answer_missing(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['raw_answers']['causal_chain']='';s.rejects('raw feedback answers')
 def test_optional_feedback_does_not_set_internal_quality_verdict(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers'][:2]:viewer['core_misconceptions']=['same-core-error']
  feedback=s.d['qa']['comprehension']['optional_audience_feedback'];feedback['shared_core_misconceptions']=['same-core-error'];feedback['misconception_review']={'status':'resolved','evidence':'synthetic specific error investigated against the current work; not a population verdict','media_sha256':s.d['qa']['reviewed_sha256']['video'],'context_sha256':gates.context_sha256(s.d,'G5'),'viewing':copy.deepcopy(s.d['qa']['explanation_review']['viewing'])}
  s.assertEqual(s.errors(),[])
 def test_optional_feedback_scores_are_not_a_gate(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers'][:2]:viewer['scores']={'topic':1,'causal_chain':1,'visualization_boundary':1,'conclusion':1}
  s.assertEqual(s.errors(),[])
 def test_optional_feedback_allows_four(s):s.prepare_cold();r=s.d['qa']['comprehension']['cold_view'];r['viewers'].pop();r['actual_viewer_count']=4;s.assertEqual(s.errors(),[])
 def test_overlap_cannot_hide_gap(s):s.d['qa']['shotbook']['viewing']['ranges']=[[0,.4],[0,.4],[.8,1]];s.rejects('range gap')
 def test_string_true_not_actual_watch(s):s.d['qa']['shotbook']['viewing']['watched']='true';s.rejects('actual viewing')
 def test_deprecated_asset(s):s.d['assets'][0]['catalog']['stage']='deprecated';refresh(s.d);s.rejects('catalog state blocks')
 def test_blocked_asset(s):s.d['assets'][0]['catalog']['stage']='blocked';refresh(s.d);s.rejects('catalog state blocks')
 def test_expired_rights(s):s.d['assets'][0]['catalog']['rights']['expires_on']='2000-01-01';refresh(s.d);s.rejects('rights expired')
 def test_source_script_stale(s):s.d['narration']['script_sha256']='0'*64;refresh(s.d);s.rejects('script evidence hash stale')
 def test_arbitrary_catalog_rule(s):s.d['assets'][1]['catalog']['rules']=['does-not-exist'];refresh(s.d);s.rejects('rules required/unknown')
 def test_calibration_needs_evidence(s):s.d['qa']['scorecard']['calibration']={};s.rejects('score calibration evidence file')
 def test_optional_feedback_does_not_require_score_rubric(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers']:viewer.pop('core_misconceptions')
  s.assertEqual(s.errors(),[])
 def test_declared_misconception_shape_checked_in_new_entry(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers']:viewer['core_misconceptions']={'shared':True}
  s.rejects('core_misconceptions must be an explicit text list')
 def test_unknown_trigger(s):s.d['brief']['validation_triggers']=['unclassified'];refresh(s.d);s.rejects('recognized values')
 def test_new_concept_needs_no_cold(s):s.d['brief']['validation_triggers']=['new_concept'];refresh(s.d);s.assertEqual(s.errors(),[])
 def test_routine_sample_needs_no_cold(s):s.d['brief']['validation_triggers']=['routine_sample'];refresh(s.d);s.assertEqual(s.errors(),[])
 def test_major_modification_needs_no_cold(s):s.d['brief']['validation_triggers']=['major_modification'];refresh(s.d);s.assertEqual(s.errors(),[])
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
 def test_optional_feedback_allows_any_actual_sample_size(s):
  s.prepare_cold();r=s.d['qa']['comprehension']['cold_view']
  for i in range(5):
   viewer=copy.deepcopy(r['viewers'][0]);viewer['anonymous_id']='extra-'+str(i);viewer['scores']={k:0 for k in viewer['scores']};viewer['total']=0;r['viewers'].append(viewer)
  r['viewers'][4]['scores']={k:0 for k in r['viewers'][4]['scores']};r['viewers'][4]['total']=0;r['actual_viewer_count']=10;r['passing_viewer_count']=4;s.assertEqual(s.errors(),[])
 def test_cold_count_summary_must_match(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['actual_viewer_count']=0;s.rejects('actual viewer count inconsistent')
 def test_legacy_passing_summary_not_a_gate(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['passing_viewer_count']=0;s.assertEqual(s.errors(),[])
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
 def test_declared_person_total_must_match(s):
  s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['total']=0;s.rejects('declared feedback person total inconsistent')
 def test_declared_summary_shape_checked_in_new_entry(s):
  s.prepare_cold();s.d['qa']['comprehension']['cold_view']['shared_core_misconceptions']={};s.rejects('summary must equal')
 def test_declared_summary_cannot_invent_shared_errors(s):
  s.prepare_cold();s.d['qa']['comprehension']['cold_view']['shared_core_misconceptions']=['invented'];s.rejects('summary must equal')

 def test_inherited_keyframe_dependency_bytes(s):
  a=copy.deepcopy(s.d['assets'][0]);a['id']='KEYFRAME_ONLY';a['file']='keyframe-only.mp4';path=s.root/a['file'];path.write_bytes((s.root/'v.mp4').read_bytes());a['sha256']=gates.file_digest(path);a['catalog']['rendered_file']=a['file'];a['catalog']['rendered_sha256']=a['sha256'];s.d['assets'].append(a);s.d['design']['keyframe_scales']['whole_scene']['asset_ids']=[a['id']];refresh(s.d)
  s.assertEqual(s.errors('G5'),[])
  try:
   path.write_bytes(path.read_bytes()+b'changed fixture');s.rejects('hash stale','G5')
  finally:path.unlink()


 def generalized(s,relation,fields):
  coverage=s.d['topic_alignment']['coverage'][0];old=coverage.pop('causal_steps')[0]
  coverage['explanation_steps']=[{'id':old['id'],'relation_type':relation,'prerequisites':[{'knowledge':'known test object','source':'audience_prior'}],'handoff':'next test relation','shot_ids':old['shot_ids'],'requires_dynamic':False,'still_reason':'a stable comparison reveals this test relationship','key_difficulty':True,'key_relation':'synthetic relation','derivation':'synthetic derivation','boundary':'synthetic scoped boundary','referent_mappings':{'object':'synthetic known object'},**{key:'synthetic '+key for key in gates.RELATION_FIELDS.get(relation,())},**fields}]
  s.d['qa']['visual_frames']['animation']['steps'][0].update(observed_relation='synthetic observed relation',derivation_observed='synthetic observed inference')
  refresh(s.d)
 def test_general_relationship_types(s):
  for relation,fields in gates.RELATION_FIELDS.items():
   with s.subTest(relation=relation):
    s.d=copy.deepcopy(s.base);s.generalized(relation,{key:'synthetic '+key for key in fields});s.assertEqual(s.errors(),[])
 def test_spatial_does_not_need_before_change_after(s):
  s.generalized('spatial',{'reference_frame':'front view','spatial_relation':'test object lies inside the enclosure'});s.assertEqual(s.errors(),[])
 def test_unknown_relation_rejected(s):s.generalized('magic',{});s.rejects('recognized relation_type')
 def test_relation_specific_information_required(s):s.generalized('spatial',{'reference_frame':'test view'});s.d['topic_alignment']['coverage'][0]['explanation_steps'][0].pop('spatial_relation');refresh(s.d);s.rejects('spatial_relation required')
 def test_general_structure_controls_sample_dependencies(s):
  s.generalized('evidence',{'evidence_basis':'test observation','inference':'test supported conclusion','limitations':'synthetic fixture only'});s.assertEqual(s.errors('G3'),[])
 def test_parallel_structures_rejected(s):
  c=s.d['topic_alignment']['coverage'][0];c['explanation_steps']=copy.deepcopy(c['causal_steps']);refresh(s.d);s.rejects('not two parallel structures')
 def test_key_difficulty_requires_card(s):s.d['topic_alignment']['expression_cards']=[];refresh(s.d);s.rejects('key difficulty lacks')
 def test_expression_action_missing(s):s.d['topic_alignment']['expression_cards'][0]['visual_action']='';refresh(s.d);s.rejects('visual_action required')
 def test_expression_prerequisites_explicit(s):s.d['topic_alignment']['expression_cards'][0].pop('prerequisites');refresh(s.d);s.rejects('prerequisites must be')
 def prepare_variants(s):
  c=s.d['topic_alignment']['expression_cards'][0];c['uncertain']=True;c['variants']=[{'id':v,'low_cost':True,'visual_action':'synthetic fixed-anchor comparison '+v,'explanation_effect':'synthetic relation becomes visible '+v} for v in ('A','B')];c['selection']={'variant_id':'B','rationale':'synthetic B keeps the reference visible','criteria':['relation_visibility','ambiguity']};refresh(s.d)
 def test_uncertain_variants_pass(s):s.prepare_variants();s.assertEqual(s.errors(),[])
 def test_uncertain_needs_two_variants(s):s.prepare_variants();s.d['topic_alignment']['expression_cards'][0]['variants'].pop();refresh(s.d);s.rejects('two low-cost expression variants')
 def test_uncertain_choice_cannot_use_prettiness(s):s.prepare_variants();s.d['topic_alignment']['expression_cards'][0]['selection']['criteria']=['prettiness'];refresh(s.d);s.rejects('compare explanation effects')
 def test_variant_needs_concrete_action(s):s.prepare_variants();s.d['topic_alignment']['expression_cards'][0]['variants'][0]['visual_action']='';refresh(s.d);s.rejects('variant visual_action required')
 def test_g1_logic_review_required(s):s.d['qa'].pop('explanation_logic');refresh(s.d);s.rejects('explanation_logic internal review missing','G1')
 def test_g1_can_precede_expression_cards(s):s.d['topic_alignment'].pop('expression_cards');refresh(s.d);s.assertEqual(s.errors('G1'),[])
 def test_g2_expression_plan_required(s):s.d['qa'].pop('expression_plan');refresh(s.d);s.rejects('expression_plan internal review missing','G2')
 def test_final_logic_review_uses_actual_work(s):s.d['qa']['explanation_review']['actual_information_only']=False;s.rejects('only information actually presented')
 def test_final_expression_review_independent(s):s.d['qa']['expression_review']['independent_of_generation_context']=False;s.rejects('independent review context required')
 def test_final_internal_review_binds_current_media(s):s.d['qa']['expression_review']['media_sha256']='0'*64;s.rejects('stale final media')
 def test_final_internal_review_covers_steps(s):s.d['qa']['explanation_review']['reviewed_step_ids']=[];s.rejects('complete explanation step review')
 def test_expression_review_covers_cards(s):s.d['qa']['expression_review']['expression_card_ids']=[];s.rejects('complete expression card review')
 def test_internal_review_context_not_self_referential(s):
  before=gates.context_sha256(s.d,'G5');s.d['qa']['explanation_review']['note']='another synthetic finding';s.assertEqual(before,gates.context_sha256(s.d,'G5'))
 def test_expression_card_change_invalidates_reviews(s):s.d['topic_alignment']['expression_cards'][0]['boundary']='changed';s.rejects('internal review stale context')
 def test_pending_optional_feedback_not_a_gate(s):s.d['qa']['comprehension']['cold_view']={'status':'pending'};s.assertEqual(s.errors(),[])
 def test_editorial_review_does_not_claim_audience_rate(s):s.d['qa']['comprehension']['status']='editor_reviewed';s.assertEqual(s.errors(),[])
 def test_new_optional_feedback_allows_four(s):
  s.prepare_cold();r=s.d['qa']['comprehension'];r['optional_audience_feedback']=r.pop('cold_view');r['optional_audience_feedback']['viewers'].pop();r['optional_audience_feedback']['actual_viewer_count']=4;s.assertEqual(s.errors(),[])
 def test_new_feedback_without_viewers_rejected(s):
  s.prepare_cold();r=s.d['qa']['comprehension'];r['optional_audience_feedback']=r.pop('cold_view');r['optional_audience_feedback']['viewers']=[];r['optional_audience_feedback']['actual_viewer_count']=0;s.rejects('needs actual viewer records')
 def test_audience_checked_without_feedback_rejected(s):
  s.prepare_cold();s.d['qa']['comprehension'].pop('cold_view');s.d['qa']['comprehension'].pop('optional_audience_feedback',None);s.rejects('completed actual optional feedback records')
 def test_new_pending_feedback_cannot_use_legacy_pass(s):
  s.prepare_cold();s.d['qa']['comprehension']['optional_audience_feedback']={'status':'not_run'};s.rejects('completed actual optional feedback records')
 def test_new_pending_feedback_allows_editorial_review(s):
  s.d['qa']['comprehension']['optional_audience_feedback']={'status':'not_run'};s.assertEqual(s.errors(),[])
 def test_new_feedback_still_requires_actual_raw_answers(s):
  s.prepare_cold();r=s.d['qa']['comprehension'];r['optional_audience_feedback']=r.pop('cold_view');r['optional_audience_feedback']['viewers'][0]['raw_answers']={};s.rejects('raw feedback answers')
 def test_brief_must_see_relation_supported(s):
  s.d['brief']['must_see_relation']=s.d['brief'].pop('must_see_change');refresh(s.d);s.assertEqual(s.errors('G1'),[])
 def test_brief_missing_visible_relation_rejected(s):
  s.d['brief'].pop('must_see_change');refresh(s.d);s.rejects('must_see_relation required','G1')


class DesignBoardEvidenceTests(unittest.TestCase):
 """Actual board bytes are required; the fixture is no claim of style acceptance."""
 setUpClass=classmethod(CanonicalStageTests.setUpClass.__func__)
 tearDownClass=classmethod(CanonicalStageTests.tearDownClass.__func__)
 setUp=CanonicalStageTests.setUp
 errors=CanonicalStageTests.errors
 rejects=CanonicalStageTests.rejects
 def test_current_local_board_passes(s):
  board=s.root/s.d['design']['board_reference']
  s.assertTrue(board.is_file());s.assertEqual(gates.file_digest(board),s.d['design']['board_sha256'])
  s.assertEqual(s.errors('G3'),[])
 def test_board_reference_required_from_g3(s):
  s.d['design'].pop('board_reference');refresh(s.d)
  s.assertEqual(s.errors('G2'),[]);s.rejects('G3 design board evidence file required','G3')
 def test_matching_declared_hashes_cannot_replace_missing_board(s):
  s.d['design']['board_reference']='missing-board.svg';refresh(s.d)
  s.rejects('G3 design board evidence path missing/unsafe','G3')
 def test_absolute_board_path_rejected(s):
  s.d['design']['board_reference']=str(s.root/s.d['design']['board_reference']);refresh(s.d)
  s.rejects('G3 design board evidence path missing/unsafe','G3')
 def test_board_outside_package_rejected(s):
  with tempfile.TemporaryDirectory(dir=s.root.parent) as outside:
   target=Path(outside)/'board.svg';target.write_bytes((s.root/s.d['design']['board_reference']).read_bytes())
   s.d['design']['board_reference']='../'+Path(outside).name+'/board.svg';refresh(s.d)
   s.rejects('G3 design board evidence path missing/unsafe','G3')
 def test_board_symlink_escape_rejected(s):
  with tempfile.TemporaryDirectory() as outside:
   target=Path(outside)/'board.svg';target.write_bytes((s.root/s.d['design']['board_reference']).read_bytes())
   link=s.root/'outside-board.svg';link.symlink_to(target);s.addCleanup(link.unlink)
   s.d['design']['board_reference']=link.name;refresh(s.d)
   s.rejects('G3 design board evidence path missing/unsafe','G3')
 def test_replaced_board_cannot_reuse_old_matching_hashes(s):
  board=s.root/s.d['design']['board_reference'];before=board.read_bytes();s.addCleanup(board.write_bytes,before)
  board.write_bytes(before.replace(b'#dceaf4',b'#204060'))
  s.rejects('G3 design board evidence hash stale','G3')
 def test_current_board_hash_does_not_extend_old_approval(s):
  board=s.root/s.d['design']['board_reference'];before=board.read_bytes();s.addCleanup(board.write_bytes,before)
  board.write_bytes(before.replace(b'#dceaf4',b'#204060'))
  s.d['design']['board_sha256']=gates.file_digest(board);refresh(s.d)
  s.rejects('design approval does not bind current board version','G3')


class EvidenceMediaIntegrityTests(unittest.TestCase):
 """Real media bytes test identity binding, without claiming perceptual approval."""
 @classmethod
 def setUpClass(c):
  CanonicalStageTests.setUpClass.__func__(c)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=green:s=48x64:r=2','-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(c.root/'replacement.mp4')],check=True)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(c.root/'v.mp4'),'-vn',str(c.root/'voice.wav')],check=True)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(c.root/'v.mp4'),'-an','-c:v','copy',str(c.root/'silent.mp4')],check=True)
 tearDownClass=classmethod(CanonicalStageTests.tearDownClass.__func__)
 setUp=CanonicalStageTests.setUp
 errors=CanonicalStageTests.errors
 rejects=CanonicalStageTests.rejects
 def review(s,gate):
  return s.d['qa']['shotbook'] if gate=='G2' else s.d['qa']['visual_frames']['animation']
 def replace_source(s,name):
  asset=next(a for a in s.d['assets'] if a['id']==s.d['narration']['asset_id'])
  asset.update(file=name,sha256=gates.file_digest(s.root/name))
  s.d['narration']['audio_sha256']=asset['sha256'];refresh(s.d)
 def test_replaced_review_media_invalidates_early_gate_receipts(s):
  for gate in ('G2','G3'):
   with s.subTest(gate=gate):
    s.d=copy.deepcopy(s.base);s.assertEqual(s.errors(gate),[])
    s.review(gate)['viewing'].update(file='replacement.mp4',sha256=gates.file_digest(s.root/'replacement.mp4'))
    s.rejects(gate+' stale stage context',gate)
    refresh(s.d);s.rejects('subject motion stale media',gate)
    # Re-signing a context cannot reuse old motion evidence on new pixels.
    import subject_motion
    policy=json.loads((Path(gates.__file__).resolve().parents[1]/'config/production-policy.json').read_text())['subject_motion']
    motion=s.review(gate)['subject_motion'];filename=gate+'-replacement-screen.json'
    (s.root/filename).write_text(json.dumps(subject_motion.screen(s.root/'replacement.mp4',[{'start':0,'end':1,'subject':'synthetic replacement fixture','isolation_note':'software test only','roi':[0,0,1,1],'masks':[]}],policy['screen'])))
    motion.update(media_sha256=gates.file_digest(s.root/'replacement.mp4'),screen={'file':filename,'sha256':gates.file_digest(s.root/filename)})
    s.d['qa']['presentation_text'][gate]['media_sha256']=s.review(gate)['viewing']['sha256']
    s.d['qa']['audio']['continuity'][gate]['media_sha256']=s.review(gate)['viewing']['sha256']
    refresh(s.d);s.assertEqual(s.errors(gate),[])
 def test_media_hash_change_at_same_path_invalidates_review_context(s):
  for gate in ('G2','G3'):
   with s.subTest(gate=gate):
    s.d=copy.deepcopy(s.base);before=gates.context_sha256(s.d,gate)
    s.review(gate)['viewing']['sha256']=gates.file_digest(s.root/'replacement.mp4')
    s.assertNotEqual(before,gates.context_sha256(s.d,gate))
 def test_review_findings_do_not_create_self_referential_context(s):
  for gate in ('G2','G3'):
   with s.subTest(gate=gate):
    before=gates.context_sha256(s.d,gate)
    s.review(gate)['viewing']['note']='updated finding about the same synthetic media'
    s.assertEqual(before,gates.context_sha256(s.d,gate))
 def test_real_audio_only_source_is_accepted(s):
  s.replace_source('voice.wav');s.assertEqual(s.errors('G2'),[])
 def test_text_cannot_satisfy_ready_narration(s):
  s.replace_source('script.txt');s.rejects('source narration','G2')
 def test_video_without_audio_cannot_satisfy_ready_narration(s):
  s.replace_source('silent.mp4');s.rejects('source narration has no audio','G2')


class CoverageStageTests(unittest.TestCase):
 @classmethod
 def setUpClass(c):
  c.tmp=tempfile.TemporaryDirectory();c.root=Path(c.tmp.name)
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','lavfi','-i','color=c=blue:s=48x64:r=2','-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(c.root/'v.mp4')],check=True)
  d=json.loads((Path(__file__).resolve().parents[1]/'examples/blue-sky/episode.json').read_text());d['deliverables']={k:'v.mp4' for k in ('video','cover_3_4','cover_4_3')}
  d['qa']={k:{'status':'pass','note':'synthetic only'} for k in ('science','rights','visual_frames','audio','narration','covers','shotbook','mobile_preview')};d['qa']['mobile_preview'].update(platform='synthetic',account='synthetic');d['qa']['comprehension']={'status':'editor_reviewed','note':'synthetic only'};d['qa']['reviewed_sha256']={k:gates.file_digest(c.root/'v.mp4') for k in d['deliverables']};c.base=upgrade(d,c.root,schema='coverage')
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
 def test_benchmark_no_people(s):s.d['brief']['production_class']='B';refresh(s.d);s.assertEqual(s.errors(),[])
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
  r['cold_view']={'status':'pass','population_rate_claimed':False,'shared_core_misconceptions':[],'group_id':'synthetic-five','sampling_plan_reference':'synthetic test plan, not real recruitment','actual_viewer_count':5,'passing_viewer_count':5,'media_sha256':s.d['qa']['reviewed_sha256']['video'],'viewers':[{'anonymous_id':'test-'+str(i),'real_person':True,'not_in_production':True,'no_relevant_training':True,'first_unprompted_normal_watch':True,'watched_current_version':True,'raw_answers':{k:'synthetic software fixture, not actual feedback' for k in ('topic','causal_chain','visualization_boundary','conclusion')},'scores':{'topic':1,'causal_chain':2,'visualization_boundary':0,'conclusion':1},'total':4,'scoring_evidence':'synthetic software fixture','core_misconceptions':[]} for i in range(5)]};refresh(s.d)
 def test_cold_fixture(s):s.prepare_cold();s.assertEqual(s.errors(),[])
 def test_duplicate_people(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][1]['anonymous_id']='test-0';s.rejects('ids missing/duplicate')
 def test_agents_not_people(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['real_person']=False;s.rejects('real_person required')
 def test_raw_answer_missing(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'][0]['raw_answers']['causal_chain']='';s.rejects('raw cold-test answer')
 def test_shared_misunderstanding(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers'][:2]:viewer['core_misconceptions']=['same-core-error']
  s.rejects('observed core misconception')
 def test_cause_incomplete_despite_total(s):
  s.prepare_cold()
  for viewer in s.d['qa']['comprehension']['cold_view']['viewers'][:2]:viewer['scores']={'topic':1,'causal_chain':1,'visualization_boundary':1,'conclusion':1}
  s.rejects('passing viewer count inconsistent')
 def test_not_five(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['viewers'].pop();s.rejects('actual viewer count inconsistent')
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
 def test_new_concept_no_people_allowed(s):s.d['brief']['validation_triggers']=['new_concept'];refresh(s.d);s.assertEqual(s.errors(),[])
 def test_sampled_routine_no_people_allowed(s):s.d['brief']['validation_triggers']=['routine_sample'];refresh(s.d);s.assertEqual(s.errors(),[])
 def test_major_modification_no_people_allowed(s):s.d['brief']['validation_triggers']=['major_modification'];refresh(s.d);s.assertEqual(s.errors(),[])
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
 def test_optional_feedback_no_fixed_sample_quota(s):
  s.prepare_cold();r=s.d['qa']['comprehension']['cold_view']
  for i in range(5):
   viewer=copy.deepcopy(r['viewers'][0]);viewer['anonymous_id']='extra-'+str(i);viewer['scores']={k:0 for k in viewer['scores']};r['viewers'].append(viewer)
  r['viewers'][4]['scores']={k:0 for k in r['viewers'][4]['scores']};r['actual_viewer_count']=10;r['passing_viewer_count']=4
  for viewer in r['viewers']:viewer['total']=sum(viewer['scores'].values())
  s.assertEqual(s.errors(),[])
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


 def typed(s,kind='spatial_constraint'):
  for coverage in s.d['topic_alignment']['coverage']:
   coverage['explanation_type']=kind;coverage['explanation_steps']=coverage.pop('causal_steps')
   for step in coverage['explanation_steps']:
    for k in ('before','change','after','handoff'):step.pop(k)
    step.update(prerequisites=[{'knowledge':'synthetic known premise','source':'audience_prior'}],key_relation='synthetic key relation',derivation='synthetic inference',boundary='synthetic limit',referent_mappings={'object':'synthetic on-screen object'},requires_dynamic=False,still_reason='stable relation permits inspection')
    step.update({key:'synthetic '+key for key in gates.EXPLANATION_TYPES[kind]})
  for entry in s.d['qa']['visual_frames']['animation']['steps']:
   entry.pop('observed_change');entry.pop('handoff_observed');entry.update(observed_relation='synthetic actual relation',derivation_observed='synthetic actual inference',representation='stable_spatial_diagram')
  s.d['brief']['must_make_understandable']=s.d['brief'].pop('must_see_change')
  s.d['brief'].update(difficult_step_ids=[],explanation_difficulties=[],no_special_design_reason='Synthetic simple stable relation; no separate difficult step identified')
  s.d['qa']['comprehension']['logic_review']={'status':'pass','basis':'paper_logic','reviewer':'synthetic','capability':'test only','evidence':'synthetic logic-only record'};refresh(s.d)
 def test_each_typed_relation_passes_without_fabricated_causal_states(s):
  for kind in gates.EXPLANATION_TYPES:
   with s.subTest(kind=kind):
    s.d=copy.deepcopy(s.base);s.typed(kind);s.assertEqual(s.errors(),[])
 def test_spatial_no_premise(s):s.typed();s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['prerequisites']=[];refresh(s.d);s.rejects('explicit prerequisites')
 def test_spatial_no_constraint(s):s.typed();s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['constraints']='';refresh(s.d);s.rejects('constraints required')
 def test_unknown_relation_type(s):s.typed();s.d['topic_alignment']['coverage'][0]['explanation_type']='anything';refresh(s.d);s.rejects('unknown or missing explanation_type')
 def test_parallel_legacy_cannot_mask_typed_missing(s):
  s.typed();c=s.d['topic_alignment']['coverage'][0];c['causal_steps']=copy.deepcopy(c['explanation_steps']);c['explanation_steps']=[];refresh(s.d);s.rejects('ambiguous parallel')
 def test_not_applicable_is_not_premise(s):s.typed();s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['prerequisites']=['not_applicable'];refresh(s.d);s.rejects('explicit prerequisites')
 def test_quantity_common_scale_required(s):s.typed('quantity');s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['common_scale']='';refresh(s.d);s.rejects('common_scale required')
 def test_probability_denominator_required(s):s.typed('probability');s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['denominator']='';refresh(s.d);s.rejects('denominator required')
 def test_evidence_inference_limits_required(s):s.typed('evidence_inference');s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['limits']='';refresh(s.d);s.rejects('limits required')
 def test_referent_mapping_missing(s):s.typed();s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['referent_mappings']={};refresh(s.d);s.rejects('referent mappings required')
 def test_actual_referent_missing(s):s.typed();s.d['qa']['comprehension']['internal_review']['steps'][0]['referent_evidence']={'other':'wrong object'};s.rejects('actual referent mapping incomplete')
 def test_actual_derivation_missing(s):s.typed();s.d['qa']['comprehension']['internal_review']['steps'][0]['derivation_observed']='';s.rejects('derivation_observed required')
 def test_unpresented_author_knowledge_blocks(s):s.d['qa']['comprehension']['internal_review']['steps'][0]['unpresented_assumptions']=['author privately knows the geometry'];s.rejects('unpresented assumptions block')
 def test_internal_review_missing_despite_no_viewer_requirement(s):s.d['qa']['comprehension'].pop('internal_review');s.rejects('actual internal explanation')
 def test_internal_review_missing_responsibility(s):s.d['qa']['comprehension']['internal_review']['responsibilities'].pop('expression');s.rejects('expression responsibility')
 def test_paper_logic_cannot_pass_final_media(s):s.d['qa']['comprehension']['internal_review']['viewing']['method']='paper_logic';s.rejects('normal-speed continuous playback')
 def test_no_actual_internal_watch(s):s.d['qa']['comprehension']['internal_review']['viewing']['watched']=False;s.rejects('actual viewing and listening')
 def test_no_actual_internal_listen(s):s.d['qa']['comprehension']['internal_review']['viewing']['heard']=False;s.rejects('actual viewing and listening')
 def test_incapable_agent_cannot_pass(s):s.d['qa']['comprehension']['internal_review']['visual_review_capable']=False;s.rejects('visual_review_capable required')
 def test_internal_old_context(s):s.d['qa']['comprehension']['internal_review']['context_sha256']='0'*64;s.rejects('internal review stale context')
 def test_internal_missing_transfer(s):s.d['qa']['comprehension']['internal_review']['understanding_goals']['transfer']['status']='pending';s.rejects('transfer understanding condition')
 def test_optional_pending_does_not_block(s):s.d['qa']['comprehension']['cold_view']={'status':'pending','viewers':[],'actual_viewer_count':0};s.assertEqual(s.errors(),[])
 def test_optional_population_rate_rejected(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['population_rate_claimed']=True;s.rejects('cannot establish population')
 def test_optional_stale_media_rejected(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['media_sha256']='0'*64;s.rejects('cold test stale media')
 def test_optional_low_scores_honestly_reported_do_not_prove_failure(s):
  s.prepare_cold();r=s.d['qa']['comprehension']['cold_view']
  for viewer in r['viewers']:viewer['scores']={k:0 for k in viewer['scores']};viewer['total']=0
  r['passing_viewer_count']=0;s.assertEqual(s.errors(),[])

 def test_difficult_steps_need_design(s):s.typed();s.d['brief']['difficult_step_ids']=['TEST0'];refresh(s.d);s.rejects('difficulties lack design cards','G1')
 def test_empty_difficulties_need_specific_reason(s):s.typed();s.d['brief']['no_special_design_reason']='not_applicable';refresh(s.d);s.rejects('no_special_design_reason','G1')
 def test_difficulty_card_four_fields(s):
  s.typed();s.d['brief']['difficult_step_ids']=['TEST0'];s.d['brief']['explanation_difficulties']=[{'step_ids':['TEST0'],'difficulty':'fixture','necessary_information':'fixture','expression_action':'fixture','derived_result':'','misleading_risk':'fixture'}];refresh(s.d);s.rejects('derived_result required','G1')
 def test_difficulty_card_can_cover_selected_subset(s):
  s.typed();s.d['brief']['difficult_step_ids']=['TEST0'];s.d['brief']['explanation_difficulties']=[{'step_ids':['TEST0'],'difficulty':'fixture','necessary_information':'fixture','expression_action':'fixture','derived_result':'fixture','misleading_risk':'fixture'}];refresh(s.d);s.assertEqual(s.errors(),[])
 def test_paper_logic_can_pass_g1_without_media_review(s):
  s.typed();s.d['qa']['comprehension']['internal_review']['status']='pending';s.assertEqual(s.errors('G1'),[]);s.rejects('actual internal explanation','G5')
 def test_g1_logic_review_missing(s):s.typed();s.d['qa']['comprehension'].pop('logic_review');s.rejects('separate paper logic review','G1')
 def test_g1_logic_stale(s):s.typed();s.d['qa']['comprehension']['logic_review']['context_sha256']='0'*64;s.rejects('logic review stale context','G1')
 def test_optional_bad_protocol(s):s.prepare_cold();s.d['qa']['comprehension']['cold_view']['protocol']={'item_max':{}};s.rejects('protocol item maxima invalid')
 def test_optional_unperformed_claimed_results(s):s.d['qa']['comprehension']['cold_view']={'status':'not_conducted','passing_viewer_count':5};s.rejects('unperformed feedback cannot claim')

 def test_auxiliary_promised_premise_required(s):
  s.typed();s.d['topic_alignment']['main_scope_ids']=[s.d['topic_alignment']['coverage'][0]['scope_id']];s.d['topic_alignment']['coverage'][1]['explanation_steps'][0]['prerequisites']=[];refresh(s.d);s.rejects('explicit prerequisites','G1')
 def test_auxiliary_actual_presentation_required(s):
  s.typed();s.d['topic_alignment']['main_scope_ids']=[s.d['topic_alignment']['coverage'][0]['scope_id']];s.d['qa']['comprehension']['internal_review']['steps'].pop();refresh(s.d);s.rejects('promised explanation coverage incomplete','G5')
 def test_auxiliary_does_not_require_first_representative_sample(s):
  s.typed();s.d['topic_alignment']['main_scope_ids']=[s.d['topic_alignment']['coverage'][0]['scope_id']];r=s.d['qa']['visual_frames']['animation'];r['step_ids']=['TEST0'];r['steps']=[r['steps'][0]];r['subject_motion']['semantic_units'][0]['step_ids']=['TEST0'];refresh(s.d);s.assertEqual(s.errors(),[])

 def test_legacy_structure_cannot_skip_design(s):s.d['brief'].pop('audience_start');refresh(s.d);s.rejects('explicit knowledge layer required','G1')
 def test_legacy_structure_cannot_skip_logic_review(s):s.d['qa']['comprehension'].pop('logic_review');s.rejects('separate paper logic review','G1')
 def test_legacy_structure_cannot_skip_learning_targets(s):s.d['brief'].pop('understanding_targets');refresh(s.d);s.rejects('planned understanding target required','G1')

class SchemaCompatibilityTests(unittest.TestCase):
 """Both public representations enforce one explanation responsibility and actual evidence."""
 setUpClass=classmethod(CanonicalStageTests.setUpClass.__func__)
 tearDownClass=classmethod(CanonicalStageTests.tearDownClass.__func__)
 setUp=CanonicalStageTests.setUp
 errors=CanonicalStageTests.errors
 rejects=CanonicalStageTests.rejects
 generalized=CanonicalStageTests.generalized
 def nested(s):s.d=upgrade(s.d,s.root,schema='coverage')
 def test_canonical_needs_no_parallel_nested_approvals(s):
  s.assertNotIn('internal_review',s.d['qa']['comprehension']);s.assertNotIn('logic_review',s.d['qa']['comprehension']);s.assertEqual(s.errors(),[])
 def test_nested_needs_no_parallel_top_level_approvals(s):
  s.nested()
  for name in ('explanation_logic','expression_plan','explanation_review','expression_review'):s.assertNotIn(name,s.d['qa'])
  s.assertEqual(s.errors(),[])
 def test_canonical_propagation_retains_carrier_path_transfer(s):
  s.generalized('propagation',{'carrier':'test field carries the signal','path':'test path through the medium','transfer':'test disturbance transfers energy'})
  s.assertEqual(s.errors(),[])
  s.d['topic_alignment']['coverage'][0]['explanation_steps'][0]['transfer']='';refresh(s.d);s.rejects('transfer required','G1')
 def test_canonical_spatial_requires_actual_constraint_and_positions(s):
  s.generalized('spatial',{})
  for key in ('objects_positions','constraints'):
   with s.subTest(key=key):
    original=s.d['topic_alignment']['coverage'][0]['explanation_steps'][0].pop(key);refresh(s.d);s.rejects(key+' required','G1');s.d['topic_alignment']['coverage'][0]['explanation_steps'][0][key]=original
 def test_canonical_quantity_requires_shared_scale_and_sample(s):
  s.generalized('quantitative',{})
  for key in ('common_scale','denominator','sample_scope','uncertainty'):
   with s.subTest(key=key):
    original=s.d['topic_alignment']['coverage'][0]['explanation_steps'][0].pop(key);refresh(s.d);s.rejects(key+' required','G1');s.d['topic_alignment']['coverage'][0]['explanation_steps'][0][key]=original
 def test_canonical_evidence_keeps_alternative_explanations(s):
  s.generalized('evidence',{});s.d['topic_alignment']['coverage'][0]['explanation_steps'][0].pop('alternative_explanations');refresh(s.d);s.rejects('alternative_explanations required','G1')
 def test_auxiliary_scope_cannot_skip_canonical_final_evidence(s):
  s.d['topic_alignment']['main_scope_ids']=[s.d['topic_alignment']['coverage'][0]['scope_id']]
  for name in ('explanation_review','expression_review'):s.d['qa'][name]['steps'].pop()
  refresh(s.d);s.rejects('promised explanation coverage incomplete','G5')
 def test_canonical_review_cannot_be_replaced_by_valid_alias(s):
  valid=copy.deepcopy(s.d['qa']['explanation_review']);s.d['qa']['comprehension']['internal_review']=valid;s.d['qa']['explanation_review']['status']='fail';s.rejects('explanation_review internal review missing')
 def test_canonical_review_requires_actual_step_derivation(s):
  s.d['qa']['explanation_review']['steps'][0]['derivation_observed']='';s.rejects('derivation_observed required')
 def test_nested_g2_requires_current_audio_and_roughcut(s):
  s.nested();s.d['qa']['shotbook']['viewing']['heard']=False;s.rejects('actual viewing and listening','G2')

class OptionalScoreDeclarationTests(unittest.TestCase):
 """Only actual volunteered score claims trigger consistency checks."""
 setUpClass=classmethod(CanonicalStageTests.setUpClass.__func__)
 tearDownClass=classmethod(CanonicalStageTests.tearDownClass.__func__)
 setUp=CanonicalStageTests.setUp
 errors=CanonicalStageTests.errors
 rejects=CanonicalStageTests.rejects
 prepare_cold=CanonicalStageTests.prepare_cold
 def unscored(s):
  s.prepare_cold();r=s.d['qa']['comprehension']['optional_audience_feedback']
  for viewer in r['viewers']:viewer['scores']=None;viewer['total']=None
  return r
 def test_unscored_feedback_requires_no_protocol(s):
  r=s.unscored();s.assertNotIn('protocol',r);s.assertEqual(s.errors(),[])
 def test_record_format_alone_never_enables_scoring(s):
  r=s.unscored();r['record_format']='legacy_scored';r['protocol']={'item_max':{}};s.assertEqual(s.errors(),[])
 def test_scores_alone_can_be_reported_without_a_total_or_protocol(s):
  r=s.unscored();r['viewers'][0]['scores']={'answer':0,'relationships':0};s.assertEqual(s.errors(),[])
 def test_honest_low_scores_do_not_block_internal_acceptance(s):
  r=s.unscored()
  for viewer in r['viewers']:viewer.update(scores={'answer':0,'relationships':0},total=0)
  s.assertEqual(s.errors(),[])
 def test_total_alone_cannot_be_verified(s):
  r=s.unscored();r['viewers'][0]['total']=3;s.rejects('score mapping')
 def test_declared_wrong_total_rejected_in_new_entry(s):
  s.prepare_cold();s.d['qa']['comprehension']['optional_audience_feedback']['viewers'][0]['total']=0;s.rejects('person total inconsistent')
 def test_declared_nonfinite_or_boolean_scores_rejected(s):
  for invalid in (True,float('inf'),float('nan'),-1,'one'):
   with s.subTest(invalid=invalid):
    s.d=copy.deepcopy(s.base);r=s.unscored();r['viewers'][0]['scores']={'answer':invalid};s.rejects('finite nonnegative score mapping')
 def test_declared_protocol_constrains_only_claimed_scores(s):
  r=s.unscored();r['viewers'][0].update(scores={'answer':2},total=2);r['protocol']={'item_max':{'answer':1}};s.rejects('scores conflict with submitted protocol')

class OptionalFeedbackTruthTests(unittest.TestCase):
 """Recorded errors require actual investigation; absent feedback stays optional."""
 setUpClass=classmethod(CanonicalStageTests.setUpClass.__func__)
 tearDownClass=classmethod(CanonicalStageTests.tearDownClass.__func__)
 setUp=CanonicalStageTests.setUp
 errors=CanonicalStageTests.errors
 rejects=CanonicalStageTests.rejects
 prepare_cold=CanonicalStageTests.prepare_cold
 def error_report(s):
  s.prepare_cold();r=s.d['qa']['comprehension']['optional_audience_feedback'];r['viewers'][0]['core_misconceptions']=['specific-error'];return r
 def resolve(s,r):
  r['misconception_review']={'status':'resolved','evidence':'synthetic recheck of specific recorded error against current media','media_sha256':s.d['qa']['reviewed_sha256']['video'],'context_sha256':gates.context_sha256(s.d,'G5'),'viewing':copy.deepcopy(s.d['qa']['explanation_review']['viewing'])}
 def test_actual_error_requires_internal_recheck(s):
  s.error_report();s.rejects('observed core misconception requires current internal recheck')
 def test_actual_recheck_can_accept_without_population_quality_inference(s):
  r=s.error_report();s.resolve(r);s.assertEqual(s.errors(),[])
 def test_recheck_requires_actual_continuous_watch_and_listen(s):
  for field,value in [('method','sampled_frames'),('watched',False),('heard',False)]:
   with s.subTest(field=field):
    s.d=copy.deepcopy(s.base);r=s.error_report();s.resolve(r);r['misconception_review']['viewing'][field]=value;s.assertTrue(s.errors())
 def test_recheck_must_bind_current_context_and_media(s):
  for key in ('context_sha256','media_sha256'):
   with s.subTest(key=key):
    s.d=copy.deepcopy(s.base);r=s.error_report();s.resolve(r);r['misconception_review'][key]='0'*64;s.assertTrue(s.errors())
 def test_shared_summary_must_come_from_distinct_actual_people(s):
  r=s.error_report();r['viewers'][0]['core_misconceptions']=['specific-error','specific-error'];r['shared_core_misconceptions']=['specific-error'];s.resolve(r);s.rejects('summary must equal')
 def test_supported_shared_summary_passes_after_actual_recheck(s):
  r=s.error_report();r['viewers'][1]['core_misconceptions']=['specific-error'];r['shared_core_misconceptions']=['specific-error'];s.resolve(r);s.assertEqual(s.errors(),[])
 def test_no_feedback_and_record_format_do_not_require_recheck(s):
  s.d['qa']['comprehension']['optional_audience_feedback']={'status':'not_run','viewers':[],'actual_viewer_count':0,'record_format':{'core_misconceptions':['format-example'],'misconception_review':{'status':'pending'}}};s.assertEqual(s.errors(),[])
 def test_empty_actual_misconceptions_do_not_require_recheck(s):
  s.prepare_cold();s.assertEqual(s.errors(),[])
 def test_not_performed_feedback_cannot_contain_actual_viewers(s):
  s.prepare_cold();r=s.d['qa']['comprehension'];r['status']='editor_reviewed';r['optional_audience_feedback'].update(status='not_run',actual_viewer_count=0);s.rejects('unperformed feedback cannot claim actual viewer records')
 def test_legacy_error_uses_same_actual_recheck(s):
  s.d=upgrade(s.d,s.root,schema='coverage');CoverageStageTests.prepare_cold(s);r=s.d['qa']['comprehension']['cold_view'];r['viewers'][0]['core_misconceptions']=['specific-error'];r['misconception_review']={'status':'resolved','evidence':'synthetic specific recheck','media_sha256':s.d['qa']['reviewed_sha256']['video'],'context_sha256':gates.context_sha256(s.d,'G5'),'viewing':copy.deepcopy(s.d['qa']['comprehension']['internal_review']['viewing'])};s.assertEqual(s.errors(),[]);r['misconception_review']['viewing']['heard']=False;s.rejects('actual viewing and listening')
