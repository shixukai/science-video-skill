#!/usr/bin/env python3
"""Regression checks; generated media are synthetic software fixtures, never an episode."""
import copy, hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[1]
p=PROJECT/'skills/science-video-production/scripts/check_episode.py'
spec=importlib.util.spec_from_file_location('checks',p); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
plan=json.loads((PROJECT/'examples/blue-sky/episode.json').read_text())
count=0
def test(label, data, root, stage, expected=None):
 global count
 errors,notes=mod.check(data,root,stage)
 assert (not errors) if expected is None else any(expected in e for e in errors),(label,errors)
 count+=1;print('PASS',label)
with tempfile.TemporaryDirectory(prefix='science-video-checks-') as tmp:
 root=Path(tmp)
 (root/"topic-anchor.json").write_text((PROJECT/"examples/blue-sky/topic-anchor.json").read_text())
 test('plan accepts pending capture honestly',plan,root,'plan')
 for kind,label in [('graphic','2D illustration'),('simulation','2D mechanism animation')]:
  x=copy.deepcopy(plan)
  for asset in x['assets']:
   if asset['id']=='A2':
    asset.update({'kind':kind,'source':f'Planned original {label} linked to the planned real observation','creator':'test plan author','disclosure':'教学示意，非实拍'})
    asset['rights']['evidence']='Planned original work; rights remain pending until created and checked'
  for shot in x['shots']:
   if 'A2' in shot['asset_ids']:shot['visual_note']=f'Planned original {label} explaining the real observation'
  test(f'accept {label} with a planned real-material anchor',x,root,'plan')
 x=copy.deepcopy(plan);x['sources'][0]['accessed_on']='not-a-date';test('reject malformed source date',x,root,'plan','source check date')
 x=copy.deepcopy(plan);x['assets'][0]['rights']['status']='cleared'
 errors,notes=mod.check(x,root,'plan')
 assert not errors and any('A1: media not acquired' in n for n in notes)
 count+=1;print('PASS distinguish rights from asset acquisition')
 for field,value,substring in [('title','中'*31,'title:'),('description','中'*1001,'exceeds 1000')]:
  x=copy.deepcopy(plan);x[field]=value;test('reject '+field+' length',x,root,'plan',substring)
 x=copy.deepcopy(plan);x['description']='@好友';test('reject mentions',x,root,'plan','mentions')
 x=copy.deepcopy(plan);x['claims'][0]['source_ids']=['missing'];test('reject broken scientific source',x,root,'plan','source_ids')
 x=copy.deepcopy(plan);x['assets'][1]['disclosure']='';test('require simulation disclosure',x,root,'plan','disclosure required')
 test('pending plan cannot pass delivery',plan,root,'delivery','rights not cleared')
 def ff(args):
  subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*args],check=True)
 ff(['-f','lavfi','-i','color=c=blue:s=48x64:r=2','-f','lavfi','-i','anullsrc=r=48000:cl=mono','-t','1','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(root/'v.mp4')])
 for name,size in [('p.png','48x64'),('l.png','64x48')]:
  ff(['-f','lavfi','-i',f'color=c=blue:s={size}','-frames:v','1','-threads','1',str(root/name)])
 x=copy.deepcopy(plan)
 x['assets']=[{'id':'A1','kind':'simulation','source':'original synthetic software test fixture','creator':'test harness','file':'v.mp4','rights':{'status':'cleared','evidence':'generated in this isolated test; not an episode','scope':'local software tests only'},'disclosure':'synthetic test fixture, not real footage'}]
 x['assets'].append({'id':'VOICE','kind':'audio','source':'synthetic audio-stream fixture, not recorded speech','creator':'test harness','file':'v.mp4','rights':{'status':'cleared','evidence':'generated in this isolated test','scope':'local software tests only'}})
 x['narration']={'language':'zh-CN','status':'ready','voice_type':'synthetic','asset_id':'VOICE','disclosure':'Synthetic test declaration only; not actual spoken narration','series_sample_reference':'software fixture only; no sample was shared'}
 x['shots']=[{'id':'SH1','claim_ids':['C1'],'asset_ids':['A1'],'visual_note':'software fixture only'}]
 x['deliverables']={'video':'v.mp4','cover_3_4':'p.png','cover_4_3':'l.png'}
 x['qa']={k:{'status':'pass','note':'test fixture value; no human visual/science approval claimed'} for k in mod.REVIEW_KEYS}
 x['qa']['narration']['review_scope']='final_export'
 x['qa']['comprehension']={'status':'editor_reviewed','note':'software fixture declaration only; no real audience understanding verified','audience_feedback_reference':''}
 x['qa']['mobile_preview'].update({'review_scope':'target_platform','surface':'desktop_platform_preview','platform':'synthetic test fixture','account':'no real account or platform accessed'})
 x['qa']['mobile_preview']['reviewed_metadata_sha256']=mod.platform_metadata_sha256(x,x['qa']['mobile_preview'])
 x['qa']['reviewed_sha256']={k:hashlib.sha256((root/f).read_bytes()).hexdigest() for k,f in x['deliverables'].items()}
 for asset in x['assets']:asset['sha256']=hashlib.sha256((root/asset['file']).read_bytes()).hexdigest()
 x['narration']['audio_sha256']=hashlib.sha256((root/'v.mp4').read_bytes()).hexdigest()
 x['shots'][0]['shotbook']={'start':0,'end':1,'subject':'test shape','action':'hold','framing':'wide','claim_support':'fixture only','motion_purpose':'static comparison; no decorative motion','beats':[{'at':0,'trigger_words':'fixture','attention_subject':'test shape','action':'hold'}],'candidates':[{'source':'synthetic fixture','viewing_note':'fixture declaration only','decision_reason':'isolated test input','selected':True,'asset_id':'A1','source_interval':'full'}],'alternatives_note':'one generated fixture for deterministic tests','keyframe_review':{'status':'pass','file':'p.png','sha256':hashlib.sha256((root/'p.png').read_bytes()).hexdigest(),'note':'fixture only, no human review'}}
 x['shots'][0]['shotbook']['visual_logic']={'review_scope':'final_export','orientation':{'applicable':False,'reason':'synthetic solid shape; no handedness or functional structure'},'graphics':[],'no_graphics_reason':'synthetic solid color contains no arrows or leaders'}
 x['qa']['shotbook']={'status':'pass','reviewed_sha256':mod.shotbook_sha256(x),'note':'software fixture declaration only, no actual audiovisual review'}
 for key in ('opening','ending'):x['topic_alignment'][key]['shot_ids']=['SH1']
 for record in x['topic_alignment']['coverage']:record['shot_ids']=['SH1']
 x['qa']['topic_alignment']={'status':'pass','reviewer_role':'independent',**{key:{'status':'pass','note':'synthetic fixture declaration; no media review claimed','evidence':'synthetic fixture only'} for key in ('opening_title','opening_voiceover','coverage','ending')}}
 x['qa']['topic_alignment']['opening_voiceover'].update(review_scope='final_export',heard_question='synthetic question declaration only',heard_answer_route='synthetic answer declaration only')
 x['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(x)
 test('valid technical fixture dimensions and full decode',x,root,'delivery')
 for status in ['fail','pending','pass']:
  y=copy.deepcopy(x);y['qa']['comprehension']['status']=status;test(f'comprehension {status} cannot be treated as reviewed delivery',y,root,'delivery','qa.comprehension')
 y=copy.deepcopy(x);y['qa']['comprehension']['status']='audience_checked';test('audience-checked claim needs actual feedback reference',y,root,'delivery','actual audience feedback reference required')
 y=copy.deepcopy(x);y['qa']['visual_frames']['status']='fail';test('known visual failure blocks delivery despite prior technical success',y,root,'delivery','qa.visual_frames')
 y=copy.deepcopy(x);y['qa']['visual_frames']['status']='pending';test('reopened visual review blocks delivery after prior technical success',y,root,'delivery','qa.visual_frames')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['review_scope']='local_player';test('local player review cannot approve target-platform fit',y,root,'delivery','actual target_platform review required')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['surface']='bare_player';test('bare player is not an actual platform surface',y,root,'delivery','surface must distinguish')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['surface']='thumbnail_proxy';test('proxy thumbnail cannot stand in for platform preview',y,root,'delivery','surface must distinguish')
 for key,value in [('title','新的标题'),('description','后来填入的完整简介'),('tags',['#新的相关标签'])]:
  y=copy.deepcopy(x);y[key]=value;test(f'changed {key} invalidates previous preview context',y,root,'delivery','missing/stale preview context hash')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['account']='different test account';test('changed account invalidates previous preview context',y,root,'delivery','missing/stale preview context hash')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['platform']='';test('require actual platform identity in review record',y,root,'delivery','actual platform and account required')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['surface']='actual_device';y['qa']['mobile_preview']['reviewed_metadata_sha256']=mod.platform_metadata_sha256(y,y['qa']['mobile_preview']);test('accept distinct actual-device metadata fixture',y,root,'delivery')
 y=copy.deepcopy(x);y['qa']['narration']['review_scope']='short_sample';test('approved short sample cannot approve a full episode',y,root,'delivery','final_export listening scope required')
 y=copy.deepcopy(x);y['qa']['narration']['review_scope']='pending';test('pending full-export listening cannot pass delivery',y,root,'delivery','final_export listening scope required')
 y=copy.deepcopy(x);y['qa']['narration'].pop('review_scope');test('missing listening scope cannot pass delivery',y,root,'delivery','final_export listening scope required')
 y=copy.deepcopy(x);y.pop('narration');test('audio stream alone cannot satisfy narration records',y,root,'delivery','ready Chinese voiceover required')
 y=copy.deepcopy(x);y['narration']['status']='pending';test('captions/music pending voiceover cannot be complete',y,root,'delivery','ready Chinese voiceover required')
 y=copy.deepcopy(x);y['narration']['language']='en';test('require Chinese narration',y,root,'delivery','Chinese language')
 y=copy.deepcopy(x);y['narration']['asset_id']='A1';test('require a voiceover audio asset',y,root,'delivery','reference an audio asset')
 y=copy.deepcopy(x);y['narration']['disclosure']='';test('require synthetic voice disclosure',y,root,'delivery','synthetic voice disclosure')
 y=copy.deepcopy(x);y['narration']['series_sample_reference']='';test('require first series voice sample reference',y,root,'delivery','series voice sample reference')
 y=copy.deepcopy(x);y['qa']['narration']['status']='pending';test('unheard narration cannot pass delivery',y,root,'delivery','qa.narration')
 y=copy.deepcopy(x);y['deliverables']['cover_3_4']='l.png';y['qa']['reviewed_sha256']['cover_3_4']=y['qa']['reviewed_sha256']['cover_4_3'];test('reject wrong cover aspect',y,root,'delivery','incorrect aspect ratio')
 y=copy.deepcopy(x);y['qa']['reviewed_sha256']['video']='0'*64;test('reject stale review hash',y,root,'delivery','missing/stale')
 y=copy.deepcopy(x);y['qa']['mobile_preview']['status']='pending';test('require mobile review',y,root,'delivery','qa.mobile_preview')
 y=copy.deepcopy(x);y['deliverables']['video']='../outside.mp4';test('reject traversal path',y,root,'delivery','path must stay inside')
 y=copy.deepcopy(x);(root/'bad.mp4').write_bytes(b'not a media file');y['deliverables']['video']='bad.mp4';test('reject corrupt video',y,root,'delivery','ffprobe failed')
 y=copy.deepcopy(x);y['deliverables']['video']='p.png';test('reject missing audio/duration',y,root,'delivery','audio stream missing')
 for field in ['subject','action','framing','claim_support','motion_purpose']:
  y=copy.deepcopy(x);y['shots'][0]['shotbook'][field]='';test('require shotbook '+field,y,root,'delivery','shotbook.'+field)
 for end in [0,-1,float('nan'),float('inf'),True,'1',10**1000]:
  y=copy.deepcopy(x);y['shots'][0]['shotbook']['end']=end;test('reject invalid timing '+str(end),y,root,'delivery','finite start < end')
 y=copy.deepcopy(x);y['shots'][0].pop('shotbook');test('delivery requires shotbook',y,root,'delivery','shotbook required')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['beats'][0]['at']=2;test('reject beat outside shot',y,root,'delivery','beat outside shot')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['beats'][0]['trigger_words']='';test('require semantic trigger',y,root,'delivery','beat.trigger_words')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['candidates'][0]['viewing_note']='';test('require actual candidate viewing record',y,root,'delivery','candidate.viewing_note')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['candidates'][0]['source_interval']='';test('require selected source interval',y,root,'delivery','source_interval required')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['candidates'][0]['selected']=False;test('require one selected primary',y,root,'delivery','exactly one selected')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['alternatives_note']='';test('single candidate needs explanation',y,root,'delivery','explain unavailable alternatives')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['keyframe_review']['status']='pending';test('motion does not approve unfinished keyframe',y,root,'delivery','finished keyframe review')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['keyframe_review']['sha256']='0'*64;test('keyframe replacement invalidates review',y,root,'delivery','stale keyframe')
 y=copy.deepcopy(x);y['narration']['audio_sha256']='0'*64;test('audio change needs realignment',y,root,'delivery','audio changed or unbound')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['beats'][0]['action']='changed';test('beat changes invalidate audiovisual approval',y,root,'delivery','stale audio/shotbook')
 y=copy.deepcopy(x);y['qa']['shotbook']['status']='pending';test('unseen audiovisual sample cannot pass',y,root,'delivery','actual representative audiovisual review')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['beats']=[];test('silent shot needs purpose',y,root,'delivery','silence_reason')
 y['shots'][0]['shotbook']['silence_reason']='hold for visual observation';y['qa']['shotbook']['reviewed_sha256']=mod.shotbook_sha256(y);y['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(y);test('accept documented silent observation',y,root,'delivery')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['end']=2;y['qa']['shotbook']['reviewed_sha256']=mod.shotbook_sha256(y);test('reject shot beyond actual export',y,root,'delivery','exceeds actual video duration')
 y=copy.deepcopy(x);y['assets'][0]['source']='changed source';test('source changes invalidate audiovisual review',y,root,'delivery','stale audio/shotbook')
 y=copy.deepcopy(x);y['assets'][0]['file']='p.png';test('asset file changes invalidate its content approval',y,root,'delivery','stale/missing asset sha256')
 y=copy.deepcopy(x);y['assets'][0]['sha256']='0'*64;test('missing or stale asset hash blocks delivery',y,root,'delivery','stale/missing asset sha256')
 for key in ('topic','scope','topic_alignment'):
  y=copy.deepcopy(x);y.pop(key);test('missing '+key+' blocks complete episode',y,root,'delivery','topic:')
 y=copy.deepcopy(x);y['topic']['current']['question']='How does this one component work?';y['topic']['current_sha256']=mod.canonical_sha256(y['topic']['current']);test('local subject cannot replace episode without permission',y,root,'delivery','explicit user request')
 y=copy.deepcopy(x);y['topic']['anchor_sha256']='0'*64;test('reject overwritten anchor hash',y,root,'delivery','original anchor hash')
 y=copy.deepcopy(x);y['topic']['anchor_file']='../outside.json';test('anchor cannot escape packet',y,root,'delivery','anchor path')
 y=copy.deepcopy(x);y['scope']={'kind':'local_sample','parent_episode_id':'synthetic-parent','chapter_id':'chapter-2','purpose':'color review','delivery_context':'One chapter of the complete question','placement':'chapter_only','publication_ready':False};test('local sample cannot pass full delivery',y,root,'delivery','cannot pass complete-episode')
 y['scope']['placement']='episode_opening';test('local sample cannot silently become opening',y,root,'plan','cannot substitute')
 y['scope']['placement']='chapter_only';y['scope']['publication_ready']=True;test('local sample cannot claim publication readiness',y,root,'plan','publication ready')
 y=copy.deepcopy(x);y['topic_alignment']['coverage'].pop();test('partial coverage cannot satisfy episode',y,root,'delivery','necessary answer scope missing')
 y=copy.deepcopy(x);y['topic_alignment']['opening']['intent']='describe_function';test('different opening question type rejected',y,root,'delivery','question type differs')
 y=copy.deepcopy(x);y['topic_alignment']['ending']['shot_ids']=['unknown'];test('conclusion must map to actual shot',y,root,'delivery','existing shot_ids')
 for key in ('opening_title','opening_voiceover','coverage','ending'):
  y=copy.deepcopy(x);y['qa']['topic_alignment'][key]['status']='fail';test('semantic review failure '+key+' blocks despite hashes',y,root,'delivery',key+' recheck failed')
 y=copy.deepcopy(x);y['qa']['reviewed_sha256']['video']='0'*64;test('replaced export invalidates topic review',y,root,'delivery','stale topic/media')
 y=copy.deepcopy(x);y['narration']['audio_sha256']='0'*64;test('changed narration invalidates topic review',y,root,'delivery','stale topic/media')
 # Generic construction topic: a function explanation is not a manufacturing answer.
 manufacturing={'version':'1','title':'How a ceramic cup is made','question':'How is a ceramic cup manufactured?','intent':'explain_manufacture','required_scope':[{'id':'M1','answer_requirement':'material preparation and forming'},{'id':'M2','answer_requirement':'firing and inspection'}]}
 (root/'manufacturing-anchor.json').write_text(json.dumps(manufacturing))
 y=copy.deepcopy(x);h=mod.canonical_sha256(manufacturing);y['topic'].update(anchor_file='manufacturing-anchor.json',anchor_sha256=h,current=manufacturing,current_sha256=h);y['topic_alignment']['topic_sha256']=h
 for key in ('opening','ending'):y['topic_alignment'][key].update(intent='describe_function',scope_ids=['M1','M2'])
 y['topic_alignment']['coverage']=[{'scope_id':'M1','shot_ids':['SH1'],'answer_evidence':'explains what the handle does'}]
 test('function-only substitute misses manufacturing scope',y,root,'delivery','necessary answer scope missing')
 y=copy.deepcopy(x);y['scope']={'kind':'local_sample','parent_episode_id':'synthetic-parent','chapter_id':'chapter-2','purpose':'illustration review','delivery_context':'Local mechanism chapter of the sky episode','placement':'chapter_only','publication_ready':False};y['topic_alignment']['coverage']=y['topic_alignment']['coverage'][:1];y['topic_alignment']['omitted_scope_ids']=['R2'];test('honest local sample plan keeps original anchor',y,root,'plan')
 y=copy.deepcopy(x);y['topic'].pop('origin_reference');test('missing original request provenance blocks delivery',y,root,'delivery','original request reference')
 y=copy.deepcopy(x);y['topic']['current']['version']='2';new_hash=mod.canonical_sha256(y['topic']['current']);old_hash=y['topic']['anchor_sha256'];y['topic']['current_sha256']=new_hash;y['topic']['change_approval']={'status':'explicit_user_request','request_reference':'synthetic explicit version change fixture','from_sha256':old_hash,'to_sha256':new_hash};y['topic_alignment']['topic_sha256']=new_hash;y['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(y);test('accept version-bound explicit change declaration',y,root,'delivery')
 y['topic']['change_approval']['to_sha256']='0'*64;test('approval for other version cannot authorize change',y,root,'delivery','explicit user request')
 y=copy.deepcopy(x);y['topic_alignment']['coverage'][0]['answer_evidence']='function-only text with matching keywords';y['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(y);y['qa']['topic_alignment']['coverage']['status']='fail';test('matching labels cannot override semantic review failure',y,root,'delivery','coverage recheck failed')
 y=copy.deepcopy(plan);y['topic_alignment']['opening']['shot_ids']=['SH2'];test('later shot cannot stand in for actual opening',y,root,'plan','actual boundary shot')
 y=copy.deepcopy(plan);y['topic_alignment']['ending']['shot_ids']=['SH2'];test('middle shot cannot stand in for actual ending',y,root,'plan','actual boundary shot')
 for omitted in [['R2'],None,'']:
  y=copy.deepcopy(x);y['topic_alignment']['omitted_scope_ids']=omitted;y['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(y);test('complete episode cannot declare omitted scope '+str(omitted),y,root,'delivery','must declare no omitted scope')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['visual_logic']['orientation']['status']='fail';test('inapplicability cannot hide known orientation failure',y,root,'delivery','known orientation failure')
 # Visual logic fixtures assert record handling only, never human image approval.
 for key in ('spoken_question','answer_route'):
  y=copy.deepcopy(x);y['topic_alignment']['opening'][key]='';test('opening requires '+key,y,root,'delivery',key+' required')
 for key in ('heard_question','heard_answer_route'):
  y=copy.deepcopy(x);y['qa']['topic_alignment']['opening_voiceover'][key]='';test('actual opening audio requires '+key,y,root,'delivery',key+' required')
 y=copy.deepcopy(x);y['qa']['topic_alignment']['opening_voiceover']['review_scope']='script';test('script text cannot prove heard opening',y,root,'delivery','actual final_export listening')
 y=copy.deepcopy(x);y['shots'][0]['shotbook'].pop('visual_logic');test('missing per-shot visual logic blocks delivery',y,root,'delivery','visual_logic:')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['visual_logic']['review_scope']='short_sample';test('short sample cannot approve final visual logic',y,root,'delivery','current final_export review')
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['visual_logic']['orientation']['reason']='';test('non-applicability needs actual reason',y,root,'delivery','non-applicability needs reason')
 orientation={'applicable':True,'status':'pass','reference':'synthetic diagram reference','frame_mapping':'fixture object left maps to screen right in front view','structures':'fixture connection checked','transforms':'fixture front/back mapping; no reflection applied','evidence':'synthetic frame 0, fixture only'}
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['visual_logic']['orientation']=orientation
 assert not mod.check_visual_logic({'SH1':y['shots'][0]},{a['id']:a for a in y['assets']})
 count+=1;print('PASS complete orientation record fixture')
 for field in ('reference','frame_mapping','structures','transforms','evidence'):
  z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['orientation'][field]='';test('require orientation '+field,z,root,'delivery','orientation.'+field)
 for status in ('fail','pending'):
  z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['orientation']['status']=status;test('reject orientation '+status,z,root,'delivery','orientation failed')
 z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['orientation']['applicable']='false';test('no truthy-string applicability',z,root,'delivery','must be boolean')
 graphic={'id':'G1','kind':'arrow','asset_id':'A1','component_reference':'original synthetic fixture v1','license_evidence':'original test code; local fixture only','checks':{key:{'status':'pass','note':'synthetic fixture declaration only','evidence':'fixture frame 0, not actual review'} for key in ('tip','shaft_join','visibility','direction','endpoints','motion_extrema')}}
 y=copy.deepcopy(x);y['shots'][0]['shotbook']['visual_logic']['graphics']=[graphic]
 y['qa']['shotbook']['reviewed_sha256']=mod.shotbook_sha256(y);y['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(y)
 test('complete arrow record fixture',y,root,'delivery')
 for key in graphic['checks']:
  z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics'][0]['checks'][key]['status']='fail';test('known arrow '+key+' failure blocks',z,root,'delivery','graphic '+key+' failed')
  z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics'][0]['checks'][key]['evidence']='';test('arrow '+key+' needs evidence',z,root,'delivery','graphic '+key+' failed')
 for key in ('component_reference','license_evidence'):
  z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics'][0][key]='';test('require graphic '+key,z,root,'delivery','graphic.'+key)
 z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics'][0]['asset_id']='VOICE';test('arrow asset must belong to shot',z,root,'delivery','asset must belong')
 z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics'].append(copy.deepcopy(graphic));test('reject duplicate graphic ids',z,root,'delivery','id missing/duplicate')
 z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics']=[None];test('malformed graphic record returns errors',z,root,'delivery','graphic id')
 z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics']='arrow';test('malformed graphics inventory returns errors',z,root,'delivery','inventory required')
 z=copy.deepcopy(x);z['shots'][0]['shotbook']['visual_logic']['no_graphics_reason']='';test('empty graphics inventory needs reason',z,root,'delivery','empty graphics inventory')
 z=copy.deepcopy(y);g=z['shots'][0]['shotbook']['visual_logic']['graphics'][0];g['kind']='leader'
 for key in ('tip','shaft_join','direction'):g['checks'].pop(key)
 z['qa']['shotbook']['reviewed_sha256']=mod.shotbook_sha256(z);z['qa']['topic_alignment']['reviewed_sha256']=mod.topic_review_sha256(z)
 test('undirected leader does not require arrowhead',z,root,'delivery')
 for key in ('tip','shaft_join','direction'):
  failed=copy.deepcopy(z);failed['shots'][0]['shotbook']['visual_logic']['graphics'][0]['checks'][key]={'status':'fail','note':'known failure before reclassification','evidence':'fixture only'};test('leader cannot hide known '+key+' failure',failed,root,'delivery','known graphic failure')
 z=copy.deepcopy(y);z['shots'][0]['shotbook']['visual_logic']['graphics'][0]['checks']['tip']['note']='changed observation';test('edited visual review invalidates prior context',z,root,'delivery','stale audio/shotbook')
 print(f'{count} checks passed; all media fixtures were generated only in the temporary directory')
