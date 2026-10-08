"""Synthetic declaration fixtures only; they never assert real media acceptance."""
from pathlib import Path
import copy
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/science-video-production/scripts'))
import stage_checks as gates

def upgrade(data,root,schema='canonical'):
 d=copy.deepcopy(data);root=Path(root)
 d['scope']={'kind':'episode','publication_ready':True}
 d['narration']['status']='ready';d['narration']['language']='zh-CN'
 d['brief']={'audience':'synthetic fixture','one_sentence_answer':'fixture only','must_see_change':'fixture declaration only','out_of_scope':[],'forbidden_misrepresentations':[],'production_class':'R','validation_triggers':[], 'roles':{r:'synthetic software fixture, not an actual reviewer' for r in ('producer','science_editor','director','art_animation','audio_caption','reviewer','publisher')}}
 d['brief'].update(audience_start={'assumed_knowledge':[],'new_knowledge':['synthetic new premise'],'deferred_knowledge':[]},understanding_targets={goal:'synthetic '+goal for goal in gates.UNDERSTANDING_GOALS},)
 (root/'script.txt').write_text('Synthetic test script only')
 d['narration']['script_file']='script.txt';d['narration']['script_sha256']=gates.file_digest(root/'script.txt')
 for asset in d.get('assets',[]):
  if asset.get('kind') in ('audio','font'):
   if not asset.get('file'):asset['file']=d['deliverables']['video']
   asset.setdefault('rights',{})['status']='cleared'
   asset['sha256']=gates.file_digest(root/asset['file'])
 audio=next((a for a in d.get('assets',[]) if a.get('id')==d['narration'].get('asset_id')),None)
 if audio:
  d['narration']['audio_sha256']=gates.file_digest(root/audio['file'])
  d['narration']['reuse_record']={'status':'previously_accepted','reference':'synthetic test declaration only, not real acceptance','audio_sha256':d['narration']['audio_sha256']}
 alignment=d['topic_alignment'];alignment['main_scope_ids']=[x['id'] for x in d['topic']['current']['required_scope']]
 steps=[]
 for n,c in enumerate(alignment['coverage']):
  for old in ('explanation_steps','explanation_type'):c.pop(old,None)
  ident='TEST'+str(n);c['causal_steps']=[{'id':ident,'before':'test initial declaration','change':'test change declaration','after':'test final declaration','handoff':'test declared handoff','shot_ids':c['shot_ids'],'requires_dynamic':True}];steps.append(ident)
 alignment['expression_cards']=[{'id':'CARD'+str(i),'step_ids':[ident],'difficulty':'synthetic relationship difficulty','prerequisites':['synthetic premise already established'],'visual_action':'hold the synthetic anchor and show its connected state change','inferable_outcome':'synthetic test conclusion','misconception':'synthetic possible confusion','boundary':'synthetic simplified model only','uncertain':False} for i,ident in enumerate(steps)]
 qa=d['qa'];sha=qa['reviewed_sha256']['video'];video=d['deliverables']['video']
 if not any(a.get('kind') in ('real_capture','real_observation') for a in d.get('assets',[])):
  d['assets'].append({'id':'REAL_FIXTURE','kind':'real_capture','source':'synthetic software declaration, not actual footage','creator':'test harness','file':video,'sha256':sha,'rights':{'status':'cleared','evidence':'synthetic test only','scope':'software test only'},'observation':{'source_interval':[0,1],'viewing_reference':'synthetic, not an actual observation'}})
  d['shots'][0]['asset_ids'].append('REAL_FIXTURE')
 d['design']={'keyframe_scales':{scale:{'file':video,'sha256':sha,'status':'pass','note':'synthetic shape fixture only'} for scale in ('whole_scene','object_midshot','mechanism_closeup')},'comparison_variants':[],'board_sha256':sha,'approval':{'status':'pass','reviewer':'synthetic fixture','actual_feedback_ref':'synthetic data, not actual approval','approved_board_sha256':sha,'scope':{'visual_style':True,'named_motion':False,'full_episode':False,'platform_release':False}}}
 for i,asset in enumerate(d.get('assets',[])):
  if asset.get('kind') in ('audio','font'):continue
  if not asset.get('file'):asset['file']=video
  asset['sha256']=gates.file_digest(root/asset['file'])
  asset.setdefault('rights',{})['status']='cleared'
  asset['observation']={'source_interval':[0,1],'viewing_reference':'synthetic only'}
  asset['catalog']={'id':'fixture-'+str(i),'name':'synthetic test asset','category':'fixture','version':'1','stage':'approved','source_file':asset['file'],'sha256':asset['sha256'],'rendered_file':asset['file'],'rendered_sha256':asset['sha256'],'viewBox':[0,0,48,64],'rules':['motion-quality'],'purpose':'software fixture','not_for':'actual publication','scientific_review':{'status':'pass'},'rights':{'status':'cleared'},'approval':{'status':'pass','asset_sha256':asset['sha256'],'evidence_ref':'synthetic only','scope':'test only','reviewer':'fixture','reviewed_at':'2026-01-01'}}

 for name in ('captions','editable_project','audio_stems','source_manifest','post_copy'):
  (root/(name+'.txt')).write_text('Synthetic software fixture only')
  d['deliverables'][name]=name+'.txt';qa['reviewed_sha256'][name]=gates.file_digest(root/(name+'.txt'))
 def viewing(scope):return {'file':video,'sha256':sha,'duration':1.0,'ranges':[[0,1.0]],'method':'continuous_playback','playback_speed':1,'watched':True,'heard':True,'reviewer':'synthetic fixture','capability':'synthetic declarations, no actual perception','reviewed_at':'2026-01-01T00:00:00Z','note':'test only, not actual viewing','scope':scope}
 qa['shotbook']['viewing']=viewing('full_roughcut')
 qa['visual_frames'].update({'failures':[],'viewing':viewing('full_episode'),'independent_of_generation_context':True,'animation':{'status':'pass','reference':'synthetic reference declaration','reference_viewing_note':'test only','scope_note':'test primary chain','viewing':viewing('representative'),'step_ids':steps,'steps':[{'step_id':s,'status':'pass','observed_change':'synthetic declaration','handoff_observed':'synthetic declaration','start':0,'end':1,'representation':'object_state_or_interaction'} for s in steps]}})
 qa['visual_frames']['process_steps']=[{'step_id':s,'status':'pass','evidence':'synthetic current full-episode declaration'} for s in steps]
 qa['visual_frames']['animation']['captions']={'file':d['deliverables']['captions'],'sha256':qa['reviewed_sha256']['captions'],'version':'fixture'}
 qa['visual_frames']['art']={'status':'pass','note':'synthetic only','evidence':'fixture'}
 qa['visual_frames']['motion']={'status':'pass','note':'synthetic only','evidence':'fixture'}
 qa['visual_frames']['finesse']={'status':'pass','target_level':'L3','reference':'fixture scoped reference','reference_note':'software fixture only','media_sha256':sha}
 for dimension,prefix,count in (('static','A',10),('motion','D',8),('integration','I',5)):
  qa['visual_frames']['finesse'][dimension]={'level':'L3','note':'synthetic software fixture only','evidence':'synthetic fixture declaration','criteria':[{'id':prefix+str(i).zfill(2),'status':'pass','note':'synthetic fixture only','evidence':'synthetic fixture declaration'} for i in range(1,count+1)]}
 qa['science']['visual_mechanism']={'status':'pass','note':'synthetic only','evidence':'fixture'}
 qa.setdefault('topic_alignment',{'status':'pass','note':'synthetic only','evidence':'fixture'})
 qa['topic_alignment'].setdefault('note','synthetic only')
 qa['audio'].update({'environments':['headphones','phone_speaker'],'listening':{e:viewing('full_episode') for e in ('headphones','phone_speaker')}})
 for k in ('captions','flicker'):qa[k]={'status':'pass','note':'synthetic declaration','evidence':'test fixture'}
 qa['captions'].update(file=d['deliverables']['captions'],sha256=qa['reviewed_sha256']['captions'],formal_script_sha256=d['narration']['script_sha256'],actual_contrast_checks=[{'time':0,'ratio':4.5,'unrounded':True,'foreground':'fixture white','actual_background':'fixture blue','method':'synthetic measurement only','worst_case_review':'fixture','evidence':{'file':video,'sha256':sha}}],static_checks={'status':'pass','method':'manual','evidence':'synthetic only','covered_checks':['bounds','empty_captions','overlap','formal_text']})
 qa['flicker'].update(designed_flash_limit_checked=True,continuous_review_reference='synthetic only',complex_sequence=False,complex_sequence_reason='synthetic no flash',designed_events=[])
 qa['mobile_preview'].update(phone={'status':'pass','surface':'actual_device','device':'synthetic fixture','app_version':'fixture','checked_at':'2026-01-01','video_sha256':sha,'canvas':[48,64],'overlay_coordinate_space':'video_pixels','actual_overlay_geometry':[{'x':0,'y':0,'width':1,'height':1}],'main_content_visible':True,'captions_visible':True,'audio_checked':True,'screenshot':{'file':video,'sha256':sha}})
 qa['comprehension']['independent_review_reference']='synthetic software declaration'
 for name,gate in (('explanation_logic','G1'),('expression_plan','G2'),('explanation_review','G5'),('expression_review','G5')):
  final=gate=='G5'
  qa[name]={'status':'pass','reviewer':'synthetic software fixture, not an actual reviewer','reviewed_at':'2026-01-01T00:00:00Z','note':'synthetic declared internal review only','evidence':'synthetic script/media fixture','reviewed_step_ids':steps[:],'review_scope':'final_export' if final else 'plan'}
  if name.startswith('expression'):qa[name]['expression_card_ids']=[card['id'] for card in alignment['expression_cards']]
  if final:qa[name].update(scope='full_episode',media_sha256=sha,independent_of_generation_context=True,actual_information_only=True)
 presented={'status':'pass','basis':'presented_work_only','reviewer_kind':'agent','visual_review_capable':True,'audio_review_capable':True,'viewing':viewing('full_episode'),'responsibilities':{role:{'status':'pass','reviewer':'synthetic test','capability':'synthetic, no actual perception','evidence':'test only'} for role in ('explanation','expression')},'understanding_goals':{goal:{'status':'pass','evidence':'synthetic condition evidence'} for goal in gates.UNDERSTANDING_GOALS},'steps':[{'step_id':step['id'],'status':'pass','start':0,'end':1,'shot_ids':step['shot_ids'],'prerequisites_observed':'synthetic premise','relation_observed':'synthetic relation','derivation_observed':'synthetic derivation','boundary_observed':'synthetic boundary','visual_evidence':'synthetic observation','narration_evidence':'synthetic spoken inference','audio_visual_coherence':'synthetic coherent relation','unpresented_assumptions':[],'referent_evidence':{'object':'synthetic visual mapping'}} for coverage in alignment['coverage'] for step in gates.relation_steps(coverage)]}
 for name in ('explanation_review','expression_review'):
  qa[name].update(copy.deepcopy(presented))
  qa[name].pop('responsibilities',None)
 if schema=='coverage':
  qa['comprehension']['logic_review']={'status':'pass','basis':'paper_logic','reviewer':'synthetic','capability':'test only','evidence':'synthetic paper logic'}
  qa['comprehension']['internal_review']=presented
  for name in ('explanation_logic','expression_plan','explanation_review','expression_review'):qa.pop(name)
  alignment.pop('expression_cards')
  d['brief'].update(difficult_step_ids=[],explanation_difficulties=[],no_special_design_reason='synthetic fixture has no specially difficult relation')
 qa['scorecard']={'scores':{k:{'score':4.5,'evidence':'synthetic test only'} for k in ('understanding','art','motion','sound','packaging')},'total':90,'media_sha256':sha}
 qa['release']={'status':'pass','authorization_reference':'synthetic authorization declaration only','authorization_scope':'no actual platform','ai_disclosure_evidence':'test','rights_evidence':'test','covers_exact_bundle':True}
 qa['release']['authorization_status']='pass'
 qa['release']['ai_disclosure']={'status':'pass','contains_generated_content':True,'applicable_platform_controls_checked':True,'platform_declaration_used':True,'required_provenance_preserved':True,'current_rule_reference':'synthetic fixture','declaration_evidence':'synthetic fixture'}
 qa['publication']={'status':'pass','state':'published','readback_matches_bundle':True,'work_id':'synthetic_not_real','actual_published_at':'2026-01-01T00:00:00Z','readback_reference':'synthetic not actual publication'}
 refresh(d)
 return d

def refresh(d):
 if isinstance(d.get('narration',{}).get('reuse_record'),dict):d['narration']['reuse_record']['audio_sha256']=d['narration'].get('audio_sha256')
 qa=d['qa']
 for name,gate in (('logic_review','G1'),('internal_review','G5')):
  if isinstance(qa['comprehension'].get(name),dict):qa['comprehension'][name]['context_sha256']=gates.context_sha256(d,gate)
 qa['visual_frames']['animation']['context_sha256']=gates.context_sha256(d,'G3')
 if isinstance(qa['visual_frames'].get('finesse'),dict):qa['visual_frames']['finesse'].update(context_sha256=gates.context_sha256(d,'G5'),media_sha256=qa['reviewed_sha256']['video'])
 for name,gate in (('explanation_logic','G1'),('expression_plan','G2'),('explanation_review','G5'),('expression_review','G5')):
  if isinstance(qa.get(name),dict):qa[name]['context_sha256']=gates.context_sha256(d,gate)
 qa['gates']={g:{'status':'passed','reviewer':'synthetic fixture','reviewed_at':'2026-01-01T00:00:00Z','scope':'software test only','context_sha256':gates.context_sha256(d,g),'review_refs':list(gates.REQUIRED_REVIEWS[g]),'evidence':[{'file':d['deliverables']['video'],'sha256':qa['reviewed_sha256']['video']}]} for g in gates.GATES}
 if 'explanation_logic' not in qa:
  for record in qa['gates'].values():record['review_refs']=[ref for ref in record['review_refs'] if ref not in ('explanation_logic','expression_plan','explanation_review','expression_review')]
 qa['release']['bundle_sha256']=gates.digest({'deliverables':d['deliverables'],'hashes':qa['reviewed_sha256'],'title':d.get('title'),'description':d.get('description'),'tags':d.get('tags'),'platform':qa['mobile_preview']})
 qa['publication'].update(bundle_sha256=qa['release']['bundle_sha256'],platform=qa['mobile_preview'].get('platform','fixture'),account=qa['mobile_preview'].get('account','fixture'))
