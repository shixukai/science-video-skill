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
 print(f'{count} checks passed; all media fixtures were generated only in the temporary directory')
