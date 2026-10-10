"""Evidence/transition validation only. No perceptual, legal or authorization verdicts."""
import hashlib
from datetime import date
import json
import math
import re
from pathlib import Path
import shutil
import subprocess
from subject_motion import validate as validate_subject_motion
from presentation_checks import validate_text_plan, validate_text_review, validate_voice_continuity

GATES = tuple(f'G{i}' for i in range(1, 8))
REQUIRED_REVIEWS = {
 'G1': ('science', 'explanation_logic'), 'G2': ('shotbook', 'expression_plan'),
 'G3': ('visual_frames.animation',), 'G4': (),
 'G5': ('science', 'science.visual_mechanism', 'rights', 'topic_alignment', 'visual_frames', 'visual_frames.art', 'visual_frames.motion', 'audio', 'narration', 'covers', 'captions', 'flicker', 'comprehension', 'explanation_review', 'expression_review'),
 'G6': ('mobile_preview', 'release'), 'G7': ('publication',)}

RELATION_FIELDS = {
 'causal': ('before', 'change', 'after'),
 'spatial': ('objects_positions', 'constraints', 'reference_frame', 'spatial_relation'),
 'structure_function': ('components', 'organization', 'structure', 'function', 'mechanism_link'),
 'comparison': ('compared_cases', 'controlled_conditions', 'difference', 'inference'),
 'quantitative': ('quantities', 'relationship', 'conditions', 'common_scale', 'denominator', 'sample_scope', 'uncertainty'),
 'probability': ('outcomes', 'distribution', 'interpretation', 'uncertainty', 'common_scale', 'denominator', 'sample_scope'),
 'evidence': ('evidence_basis', 'inference', 'limitations', 'alternative_explanations', 'inference_rule'),
 'propagation': ('carrier', 'path', 'transfer'),
}
VALIDATION_TRIGGERS = {'new_style', 'benchmark', 'new_complex_mechanism', 'major_restructure', 'new_concept', 'major_change', 'routine_sample', 'major_modification'}
EXPRESSION_CRITERIA = {'missing_prerequisites', 'reasoning_gaps', 'relation_visibility', 'ambiguity'}

def obj(x):
 return x if isinstance(x, dict) else {}

def seq(x):
 return x if isinstance(x, list) else []

def text(x):
 return isinstance(x, str) and bool(x.strip())

def number(x):
 try:
  return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
 except OverflowError:
  return False


EXPLANATION_TYPES = {
 'causal_process': ('before','change','after','handoff'),
 'spatial_constraint': ('objects_positions','constraints','observer_frame'),
 'structure_function': ('components','organization','function_link'),
 'propagation': ('carrier','path','transfer'),
 'quantity': ('common_scale','denominator','sample_scope','uncertainty'),
 'probability': ('common_scale','denominator','sample_scope','uncertainty','outcomes'),
 'evidence_inference': ('observations','inference_rule','alternative_explanations','limits'),
}
UNDERSTANDING_GOALS = ('answer','relationships','transfer','boundaries')

def relation_steps(coverage):
 """New typed records and legacy causal records share IDs and dependency mapping."""
 coverage=obj(coverage)
 return seq(coverage.get('explanation_steps') if 'explanation_steps' in coverage else coverage.get('causal_steps'))

explanation_steps = relation_steps

def substantive(value):
 return text(value) and value.strip().lower() not in ('n/a','na','none','not_applicable','not applicable','pending','todo','tbd','不适用','无')

def digest(x):
 return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def file_digest(path):
 with path.open('rb') as f:
  return hashlib.file_digest(f,'sha256').hexdigest()


def content_scope(data):
 return {k:v for k,v in obj(data.get('scope')).items() if k!='publication_ready'}

def dependencies(data, representative=False):
 """One typed dependency resolver for evidence checks and immutable context binding."""
 errors=[];known={obj(a).get('id') for a in seq(data.get('assets')) if text(obj(a).get('id'))}
 def refs(value,label,present=True):
  if not present:return set()
  if not isinstance(value,list) or not all(text(i) for i in value):
   errors.append(label+' must be an asset-ID list');return set()
  if len(set(value))!=len(value):errors.append(label+' contains duplicate asset IDs')
  if not set(value)<=known:errors.append(label+' dependency cannot be resolved')
  return set(value)
 design=obj(data.get('design'));animation=obj(obj(obj(data.get('qa')).get('visual_frames')).get('animation'))
 selected={x for x in seq(animation.get('step_ids')) if text(x)}
 selected_shots={i for coverage in seq(obj(data.get('topic_alignment')).get('coverage')) for step in relation_steps(coverage) if text(obj(step).get('id')) and obj(step).get('id') in selected for i in seq(obj(step).get('shot_ids')) if text(i)}
 used=set()
 for shot in seq(data.get('shots')):
  shot=obj(shot);ids=refs(shot.get('asset_ids'),'shot '+str(shot.get('id')))
  if not representative or shot.get('id') in selected_shots:used.update(ids)
 voice=obj(data.get('narration')).get('asset_id')
 if text(voice):
  if voice not in known:errors.append('narration dependency cannot be resolved')
  used.add(voice)
 common=refs(design.get('render_asset_ids'),'design.render_asset_ids','render_asset_ids' in design);used.update(common)
 font=design.get('font_asset_id')
 if font is not None:
  if not text(font):errors.append('design.font_asset_id must be a nonempty asset ID')
  elif font not in known:errors.append('design font dependency cannot be resolved')
  else:used.add(font)
 output=data.get('deliverable_asset_ids',{})
 if not isinstance(output,dict):errors.append('deliverable_asset_ids must be an object');output={}
 for key,value in output.items():
  ids=refs(value,'deliverable_asset_ids.'+str(key))
  if not representative or key in ('captions','design'):used.update(ids)
 for scale,frame in obj(design.get('keyframe_scales')).items():
  frame=obj(frame);ids=refs(frame.get('asset_ids'),'three-scale '+scale,'asset_ids' in frame)
  if representative:used.update(ids)
 sample_captions=obj(animation.get('captions'))
 sample_ids=refs(sample_captions.get('asset_ids'),'representative caption assets','asset_ids' in sample_captions)
 if representative:used.update(sample_ids)
 return used,selected_shots,errors

def used_asset_ids(data):
 return dependencies(data)[0]


def context_sha256(data, gate):
 """Version binding at the relevant production scope, not evidence of review."""
 keys=['topic','topic_alignment','sources','claims','brief','scope','series_profile','presentation_text']
 if gate!='G1': keys += ['shots','narration']
 if gate not in ('G1','G2'): keys += ['assets','design']
 if gate in ('G4','G5','G6','G7'): keys += ['deliverables','production_statement']
 if gate in ('G6','G7'): keys += ['title','description','tags']
 result={k:data.get(k) for k in keys}
 # Freeze the media actually reviewed at each early audiovisual gate. Review
 # conclusions stay outside the digest so recording them cannot hash itself.
 if gate=='G2':
  viewing=obj(obj(obj(data.get('qa')).get('shotbook')).get('viewing'))
  result['roughcut_media']={k:viewing.get(k) for k in ('file','sha256')}
 if gate=='G3':
  viewing=obj(obj(obj(obj(data.get('qa')).get('visual_frames')).get('animation')).get('viewing'))
  result['representative_media']={k:viewing.get(k) for k in ('file','sha256')}
 if gate not in ('G6','G7'):result['scope']=content_scope(data)
 if gate in ('G4','G5','G6','G7'):result['deliverable_asset_ids']=data.get('deliverable_asset_ids')
 if gate in ('G4','G5','G6','G7'):result['assets']=[a for a in seq(data.get('assets')) if obj(a).get('id') in used_asset_ids(data)]
 if gate=='G3':
  used,shot_ids,_=dependencies(data,True)
  result['shots']=[shot for shot in seq(data.get('shots')) if obj(shot).get('id') in shot_ids]
  result['assets']=[a for a in seq(data.get('assets')) if obj(a).get('id') in used]
  result['representative_step_ids']=obj(obj(obj(data.get('qa')).get('visual_frames')).get('animation')).get('step_ids')
  result['representative_shot_intervals']=obj(obj(obj(data.get('qa')).get('visual_frames')).get('animation')).get('shot_intervals')
 if gate not in ('G1','G2'):
  result['representative_captions']=obj(obj(obj(data.get('qa')).get('visual_frames')).get('animation')).get('captions')
 if gate in ('G4','G5','G6','G7'):
  result['media_hashes']=obj(data.get('qa')).get('reviewed_sha256')
 if gate in ('G6','G7'):
  result['platform']=obj(data.get('qa')).get('mobile_preview')
 return digest(result)

class Checks:
 def __init__(self,data,root):
  self.data=data;self.root=Path(root).resolve();self.qa=obj(data.get('qa'));self.errors=[];self.cache={}
 def need(self,ok,msg):
  if not ok:self.errors.append('stage: '+msg)
  return bool(ok)
 def record(self,path):
  x=self.qa
  for part in path.split('.'):x=obj(x).get(part)
  if path not in ('explanation_logic','expression_plan','explanation_review','expression_review') or path in self.qa:return obj(x)
  # Existing nested records are aliases of these responsibilities, not extra approvals.
  nested=obj(self.record('comprehension').get('logic_review' if path in ('explanation_logic','expression_plan') else 'internal_review'))
  if not nested:return {}
  result=dict(nested)
  role='expression' if path.startswith('expression') else 'explanation'
  responsibility=obj(obj(nested.get('responsibilities')).get(role))
  result.setdefault('note',responsibility.get('evidence',nested.get('evidence')))
  result.setdefault('evidence',responsibility.get('evidence'))
  return result
 def evidence(self,r,label):
  r=obj(r);name=r.get('file')
  if not self.need(text(name),label+' evidence file required'):return None
  p=(self.root/name).resolve()
  if not self.need(not Path(name).is_absolute() and p.is_relative_to(self.root) and p.is_file(),label+' evidence path missing/unsafe'):return None
  self.need(r.get('sha256')==file_digest(p),label+' evidence hash stale')
  return p
 def duration(self,path,require_audio=True,require_video=True,label='viewing media'):
  cache_key=(path,require_audio,require_video)
  if cache_key in self.cache:return self.cache[cache_key]
  value=None;probe=shutil.which('ffprobe')
  if not self.need(bool(probe),'ffprobe required for actual viewing interval bounds'):return None
  try:
   p=subprocess.run([probe,'-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,timeout=60)
   meta=obj(json.loads(p.stdout));value=float(obj(meta.get('format')).get('duration',0))
   self.need(p.returncode==0 and math.isfinite(value) and value>0,label+' duration invalid')
   if require_video:self.need(any(obj(s).get('codec_type')=='video' for s in seq(meta.get('streams'))),label+' has no video')
   if require_audio:self.need(any(obj(s).get('codec_type')=='audio' for s in seq(meta.get('streams'))),label+' has no audio')
  except (OSError,ValueError,TypeError,OverflowError,subprocess.TimeoutExpired):self.need(False,label+' unreadable')
  self.cache[cache_key]=value
  return value
 def viewing(self,r,label,scope,final=False,listening_only=False):
  r=obj(r);p=self.evidence(r,label)
  for k in ('reviewer','capability','reviewed_at','note'):self.need(text(r.get(k)),label+' '+k+' required')
  self.need(r.get('scope')==scope,label+' scope mismatch')
  self.need(r.get('method')=='continuous_playback' and r.get('playback_speed')==1 and not isinstance(r.get('playback_speed'),bool),label+' normal-speed continuous playback required; frame samples do not qualify')
  self.need(r.get('heard') is True and (listening_only or r.get('watched') is True),label+' actual viewing and listening required' if not listening_only else label+' actual listening required')
  if listening_only and 'watched' in r:self.need(isinstance(r['watched'],bool),label+' optional watched declaration must be boolean')
  if final:self.need(r.get('file')==obj(self.data.get('deliverables')).get('video'),label+' must bind final deliverable')
  dur=self.duration(p) if p else None
  self.need(number(r.get('duration')) and number(dur) and abs(r['duration']-dur)<0.05,label+' duration must match actual file')
  ranges=r.get('ranges');cursor=0
  if self.need(isinstance(ranges,list) and bool(ranges),label+' continuous ranges required'):
   for span in ranges:
    valid=isinstance(span,list) and len(span)==2 and all(number(v) for v in span)
    if self.need(valid,label+' range must contain finite start/end'):
     a,b=span;self.need(0<=a<=cursor+0.001 and a<b and number(dur) and b<=dur+0.05,label+' range gap/invalid interval');cursor=max(cursor,b)
   self.need(number(dur) and cursor>=dur-0.05,label+' full evidence clip must actually be covered')
  return r
 def causal(self):
  """Validate every promised scope; per-step types and coverage types share IDs."""
  a=obj(self.data.get('topic_alignment'));required={r.get('id') for r in seq(obj(obj(self.data.get('topic')).get('current')).get('required_scope')) if isinstance(r,dict) and text(r.get('id'))}
  mains=a.get('main_scope_ids');valid=isinstance(mains,list) and bool(mains) and all(text(x) for x in mains)
  self.need(valid and len(set(mains))==len(mains) and set(mains)<=required,'primary question main_scope_ids missing/invalid')
  covered=set();steps={};all_ids=[]
  shots={s.get('id') for s in seq(self.data.get('shots')) if isinstance(s,dict) and text(s.get('id'))}
  for c in seq(a.get('coverage')):
   c=obj(c);typed='explanation_steps' in c or 'explanation_type' in c;legacy_type=c.get('explanation_type')
   self.need(not (typed and 'causal_steps' in c),'ambiguous parallel explanation and causal records; use explanation_steps or legacy causal_steps, not two parallel structures')
   if 'explanation_type' in c:self.need(legacy_type in EXPLANATION_TYPES,'unknown or missing explanation_type')
   chain=relation_steps(c);all_ids.extend(obj(step).get('id') for step in chain if text(obj(step).get('id')))
   if not self.need(c.get('scope_id') in required,'explanation scope must match a promised scope'):continue
   if not self.need(bool(chain),'primary explanation structure missing (legacy primary causal chain missing)'):continue
   self.need(c.get('scope_id') not in covered,'duplicate promised explanation scope');covered.add(c['scope_id'])
   for row in chain:
    step=dict(obj(row));ident=step.get('id')
    if not self.need(text(ident) and ident not in steps,'explanation step id missing/duplicate'):continue
    canonical=typed and 'relation_type' in step
    relation=step.get('relation_type') if canonical else 'causal'
    if canonical:
     if self.need(relation in RELATION_FIELDS,ident+' recognized relation_type required'):
      for key in RELATION_FIELDS[relation]:self.need(substantive(step.get(key)),ident+' '+key+' required for '+relation)
     self.need(substantive(step.get('handoff')),ident+' handoff required')
     self.need(isinstance(step.get('key_difficulty'),bool),ident+' key_difficulty declaration required')
    else:
     kind=legacy_type if typed else 'causal_process'
     self.need(kind in EXPLANATION_TYPES,'unknown or missing explanation_type')
     for key in EXPLANATION_TYPES.get(kind,()):self.need(substantive(step.get(key)),ident+' '+key+' required')
    if typed:
     pre=step.get('prerequisites');self.need(isinstance(pre,list) and bool(pre) and all(substantive(x) for x in pre),ident+' explicit prerequisites required')
     for key in ('key_relation','derivation','boundary'):self.need(substantive(step.get(key)),ident+' '+key+' required')
     mappings=step.get('referent_mappings');self.need(isinstance(mappings,dict) and bool(mappings) and all(substantive(k) and substantive(v) for k,v in mappings.items()),ident+' referent mappings required')
    step.update(_typed=typed,_canonical=canonical,_explanation_type=legacy_type,relation_type=relation,key_difficulty=step.get('key_difficulty',not typed))
    steps[ident]=step
    ids=step.get('shot_ids');self.need(isinstance(ids,list) and bool(ids) and all(text(i) and i in shots and i in seq(c.get('shot_ids')) for i in ids),ident+' shot coverage missing')
    self.need(isinstance(step.get('requires_dynamic'),bool),ident+' requires_dynamic declaration required')
    if step.get('requires_dynamic') is False:self.need(substantive(step.get('still_reason')),ident+' static observation reason required')
  self.need(len(all_ids)==len(set(all_ids)),'explanation/causal step ids must be unique across primary and auxiliary scopes')
  self.need(covered==required and bool(steps),'all promised explanation coverage incomplete')
  return steps
 def explanation_design(self,steps):
  brief=obj(self.data.get('brief'));start=obj(brief.get('audience_start'))
  for key in ('assumed_knowledge','new_knowledge','deferred_knowledge'):
   values=start.get(key);self.need(isinstance(values,list) and all(substantive(v) for v in values) and (key!='new_knowledge' or bool(values)),'audience_start '+key+' explicit knowledge layer required')
  for goal in UNDERSTANDING_GOALS:self.need(substantive(obj(brief.get('understanding_targets')).get(goal)),goal+' planned understanding target required')
  # A canonical expression design may start at G2; coverage-style aliases retain G1 design.
  if 'expression_cards' not in obj(self.data.get('topic_alignment')) and 'explanation_difficulties' in brief:
   self.expression_cards(steps)
 def expression_cards(self,steps):
  alignment=obj(self.data.get('topic_alignment'));brief=obj(self.data.get('brief'));canonical='expression_cards' in alignment
  cards=alignment.get('expression_cards') if canonical else brief.get('explanation_difficulties')
  if not canonical:
   difficult=brief.get('difficult_step_ids');valid=isinstance(difficult,list) and all(text(i) and i in steps for i in difficult)
   self.need(valid and len(set(difficult))==len(difficult),'explicit difficult_step_ids must be unique known promised steps')
   difficult=set(difficult) if valid else set()
   if not difficult:self.need(substantive(brief.get('no_special_design_reason')),'no difficult steps requires specific no_special_design_reason')
   cards=[dict(obj(card),id=obj(card).get('id','DIFFICULTY'+str(i)),prerequisites=[obj(card).get('necessary_information')],visual_action=obj(card).get('expression_action'),inferable_outcome=obj(card).get('derived_result'),misconception=obj(card).get('misleading_risk'),boundary=obj(card).get('boundary',obj(card).get('misleading_risk')),uncertain=obj(card).get('uncertain',False)) for i,card in enumerate(seq(cards))] if isinstance(cards,list) else cards
  if not self.need(isinstance(cards,list),'expression_cards must explicitly record key difficulties'):return {}
  result={};covered=set()
  for card in cards:
   card=obj(card);ident=card.get('id')
   if not self.need(text(ident) and ident not in result,'expression card id missing/duplicate'):continue
   result[ident]=card
   for key in ('difficulty','visual_action','inferable_outcome','misconception','boundary'):
    self.need(substantive(card.get(key)),ident+' '+key+' required'+(' (derived_result required)' if key=='inferable_outcome' else ''))
   pre=card.get('prerequisites');self.need(isinstance(pre,list) and all(substantive(x) for x in pre),ident+' prerequisites must be an explicit text list')
   ids=card.get('step_ids');valid=isinstance(ids,list) and bool(ids) and all(text(i) and i in steps for i in ids)
   self.need(valid and len(set(ids))==len(ids),ident+' explanation step references missing/invalid')
   if valid:covered.update(ids)
   uncertain=card.get('uncertain');self.need(isinstance(uncertain,bool),ident+' uncertain declaration required')
   if uncertain is True:
    variants=card.get('variants');self.need(isinstance(variants,list) and len(variants)>=2,ident+' uncertain difficulty needs two low-cost expression variants')
    variant_ids=set()
    for variant in seq(variants):
     variant=obj(variant);v=variant.get('id');self.need(text(v) and v not in variant_ids,ident+' variant id missing/duplicate')
     if text(v):variant_ids.add(v)
     self.need(variant.get('low_cost') is True,ident+' variants must be low-cost expression studies')
     for key in ('visual_action','explanation_effect'):self.need(text(variant.get(key)),ident+' variant '+key+' required')
    selection=obj(card.get('selection'))
    self.need(text(selection.get('variant_id')) and selection.get('variant_id') in variant_ids,ident+' selected expression variant missing/invalid')
    self.need(text(selection.get('rationale')),ident+' expression-effect selection rationale required')
    criteria=selection.get('criteria');self.need(isinstance(criteria,list) and bool(criteria) and all(text(x) and x in EXPRESSION_CRITERIA for x in criteria),ident+' selection must compare explanation effects, not decorative preference')
  critical={ident for ident,step in steps.items() if step.get('key_difficulty') is True} if canonical else difficult
  if not canonical:self.need(covered==critical,'identified explanation difficulties lack design cards')
  self.need(critical<=covered,'key difficulty lacks a concrete expression card')
  if canonical and not critical:self.need(substantive(alignment.get('no_key_difficulty_reason')),'no key difficulty needs a reviewed applicability reason')
  return result
 def animation(self,steps):
  r=self.record('visual_frames.animation');v=self.viewing(r.get('viewing'),'G3 motion','representative')
  self.need(r.get('status')=='pass','G3 actual motion review required')
  self.evidence(r.get('captions'),'G3 representative captions')
  for k in ('reference','reference_viewing_note','scope_note'):self.need(text(r.get(k)),'G3 '+k+' required')
  self.need(r.get('context_sha256')==context_sha256(self.data,'G3'),'stale animation plan/audio/assets context')
  # Planned representative selection must cover at least one entire primary causal chain.
  selected=r.get('step_ids');valid=isinstance(selected,list) and bool(selected) and all(text(i) and i in steps for i in selected)
  self.need(valid and len(set(selected))==len(selected),'representative step selection invalid')
  mains={x for x in seq(obj(self.data.get('topic_alignment')).get('main_scope_ids')) if text(x)}
  chains=[{obj(s).get('id') for s in relation_steps(c) if text(obj(s).get('id'))} for c in seq(obj(self.data.get('topic_alignment')).get('coverage')) if obj(c).get('scope_id') in mains]
  self.need(valid and any(chain and chain<=set(selected) for chain in chains),'representative sample must cover a complete primary explanation chain (legacy complete primary causal chain)')
  found=set()
  for e in seq(r.get('steps')):
   e=obj(e);ident=e.get('step_id')
   if not self.need(text(ident) and ident in steps and ident not in found,'unknown/duplicate motion evidence step'):continue
   found.add(ident)
   self.need(e.get('status')=='pass',ident+' motion failed or unreviewed')
   for key in (('observed_relation','derivation_observed') if steps[ident].get('_typed') else ('observed_change','handoff_observed')):self.need(substantive(e.get(key)),ident+' '+key+' required')
   start,end=e.get('start'),e.get('end');self.need(number(start) and number(end) and number(v.get('duration')) and 0<=start<end<=v['duration']+0.05,ident+' motion interval invalid')
   if steps[ident].get('requires_dynamic') is True:self.need(e.get('representation') in ('object_state_or_interaction','relation_demonstration'),ident+' static board/overlay cannot replace required dynamic process')
  self.need(valid and found==set(selected),'selected primary process lacks continuous evidence')
 def failures(self,final):
  visual=self.record('visual_frames');history=visual.get('failures')
  self.need(isinstance(history,list),'visual failure history must be explicit')
  for item in seq(history):
   item=obj(item)
   for key in ('id','scope','note'):self.need(text(item.get(key)),'failure history '+key+' required')
   self.need(item.get('scope') in ('whole_episode','segment','audio','caption','series_style'),'unknown failure scope')
   state=item.get('status');self.need(state in ('open','resolved'),'unknown failure status')
   if state=='open':
    self.need(not final,'known failure blocks full quality/release')
    if item.get('scope') in ('whole_episode','series_style','segment'):
     self.need(visual.get('status')!='pass','local approval cannot overwrite unresolved overall failure')
    elif item.get('scope') in ('audio','caption'):
     affected=self.record('audio' if item['scope']=='audio' else 'captions')
     self.need(affected.get('status')!='pass','unresolved failure cannot be overwritten in its affected dimension')
   if state=='resolved':
    r=obj(item.get('resolution'));self.need(text(r.get('evidence')),'failure resolution evidence required')
    self.need(r.get('context_sha256')==context_sha256(self.data,'G5') and r.get('sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),'failure resolution stale media/context')
    if item.get('scope') in ('whole_episode','series_style','audio'):
     self.need(r.get('scope')=='full_episode','local approval cannot resolve whole-episode failure')
     if item.get('scope')=='audio':
      for env in ('headphones','phone_speaker'):
       self.viewing(obj(self.record('audio.listening')).get(env),'audio failure resolution '+env,'full_episode',final=True,listening_only=True)
      validate_voice_continuity(self,'G5',obj(obj(self.record('audio.listening')).get('headphones')))
     else:self.viewing(visual.get('viewing'),'failure resolution','full_episode',final=True)
 def asset_catalog(self,steps,representative):
  schema=json.loads((Path(__file__).resolve().parents[1]/'assets/production-asset.schema.json').read_text())
  owners=json.loads((Path(__file__).resolve().parents[1]/'indexes/rule-owners.json').read_text())
  known={rule for owner in owners['owners'] for rule in owner['owns']}
  used,_,dependency_errors=dependencies(self.data,representative)
  for error in dependency_errors:self.need(False,error)
  seen=set()
  for asset in seq(self.data.get('assets')):
   asset=obj(asset)
   if asset.get('id') not in used:continue
   label='asset '+str(asset.get('id'));record=obj(asset.get('catalog'))
   # Never let a second positive record erase an explicit legacy failure.
   self.need(asset.get('catalog_state') not in ('blocked','deprecated','needs_changes'),label+' legacy asset state blocks use')
   for legacy in ('science','approval'):
    if obj(asset.get(legacy)).get('status') is not None and record:
     inner='scientific_review' if legacy=='science' else 'approval'
     self.need(obj(asset[legacy]).get('status')==obj(record.get(inner)).get('status'),label+' conflicting legacy '+legacy+' state')
    self.need(obj(asset.get(legacy)).get('status') not in ('fail','needs_changes','blocked'),label+' legacy '+legacy+' failure conflicts with approval')
   if record:
    for outer,inner in (('catalog_state','stage'),('editable_source','source_file'),('view_box','viewBox')):
     if outer in asset:self.need(asset[outer]==record.get(inner),label+' conflicting legacy '+outer)
   self.evidence({'file':asset.get('file'),'sha256':asset.get('sha256')},label+' render')
   rights=obj(asset.get('rights'));self.need(rights.get('status')=='cleared',label+' rights not cleared')
   for rr in (rights,obj(record.get('rights'))):
    if rr.get('expires_on'):
     try:self.need(date.fromisoformat(rr['expires_on'])>=date.today(),label+' rights expired')
     except (TypeError,ValueError):self.need(False,label+' rights expiry invalid')
   if record:
    self.need(record.get('stage') not in ('blocked','deprecated','needs_changes'),label+' catalog state blocks use')
    for field in ('scientific_review','approval','rights'):
     status=obj(record.get(field)).get('status')
     self.need(status not in ('fail','needs_changes','blocked','denied','revoked','expired'),label+' explicit catalog '+field+' failure blocks use')
    if obj(record.get('rights')).get('status') is not None:
     self.need(obj(record['rights']).get('status')==rights.get('status'),label+' catalog/asset rights conflict')
   if asset.get('kind') in ('audio','font'):continue
   if asset.get('kind') in ('real_capture','real_observation','screen_recording'):
    path=self.evidence({'file':asset.get('file'),'sha256':asset.get('sha256')},label+' source footage')
    duration=self.duration(path,require_audio=False) if path else None
    observation=obj(asset.get('observation'))
    self.need(text(observation.get('viewing_reference')),label+' actual source footage viewing required')
    span=observation.get('source_interval')
    self.need(isinstance(span,list) and len(span)==2 and all(number(t) for t in span) and number(duration) and 0<=span[0]<span[1]<=duration+.05,label+' actual footage interval required')
    continue
   if not record:
    self.need(asset.get('usage')=='episode_original',label+' specify original production or reusable catalog')
    self.evidence({'file':asset.get('source_file'),'sha256':asset.get('source_sha256')},label+' editable original source')
    science=obj(asset.get('scientific_review'))
    self.need(science.get('status')=='pass' or (science.get('status')=='not_applicable' and text(science.get('reason'))),label+' science review or justified applicability required')
    continue
   ident=record.get('id');self.need(all(k in record for k in schema['required']),label+' catalog fields missing')
   valid=text(ident) and bool(re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',ident));self.need(valid and ident not in seen,label+' stable catalog id missing/duplicate')
   if valid:seen.add(ident)
   for key in ('name','category','version','purpose','not_for'):self.need(text(record.get(key)),label+' '+key+' required')
   self.need(record.get('stage')=='approved',label+' candidate/blocked/deprecated asset cannot be production-approved')
   box=record.get('viewBox');self.need(isinstance(box,list) and len(box)==4 and all(number(v) for v in box) and box[2]>0 and box[3]>0,label+' valid design coordinates required')
   rules=record.get('rules');self.need(isinstance(rules,list) and bool(rules) and all(text(v) and v in known for v in rules),label+' rules required/unknown')
   self.evidence({'file':record.get('source_file'),'sha256':record.get('sha256')},label+' source')
   self.need(record.get('rendered_file')==asset.get('file') and record.get('rendered_sha256')==asset.get('sha256'),label+' rendered asset version mismatch')
   science=obj(record.get('scientific_review'))
   self.need(science.get('status')=='pass' or (science.get('status')=='not_applicable' and text(science.get('reason'))),label+' science review or justified applicability required')
   self.need(obj(record.get('rights')).get('status')=='cleared',label+' catalog rights not cleared')
   approval=obj(record.get('approval'));self.need(approval.get('status')=='pass' and approval.get('asset_sha256')==record.get('sha256'),label+' approval stale/missing')
   for key in ('evidence_ref','scope','reviewer','reviewed_at'):self.need(text(approval.get(key)),label+' approval '+key+' required')
 def scores(self,policy):
  r=self.record('scorecard');benchmark=obj(self.data.get('brief')).get('production_class')=='B';q=dict(policy['quality'])
  if 'calibration' in r:
   calibration=obj(r.get('calibration'));self.evidence(calibration,'score calibration')
   for key in ('reviewer','rationale','scope'):self.need(text(calibration.get(key)),'score calibration '+key+' required')
   total_key='benchmark_total_min' if benchmark else 'routine_total_min';mins_key='benchmark_min_scores' if benchmark else 'routine_min_scores'
   value=calibration.get(total_key);valid=number(value) and 0<value<=100
   self.need(valid,'score calibration total invalid')
   if valid:q[total_key]=value
   minima=calibration.get(mins_key);valid=isinstance(minima,dict) and set(minima)==set(q['weights']) and all(number(v) and 0<v<=5 for v in minima.values())
   self.need(valid,'score calibration dimension minima invalid')
   if valid:q[mins_key]=minima
  mins=q['benchmark_min_scores' if benchmark else 'routine_min_scores'];total=0
  for key,weight in q['weights'].items():
   e=obj(obj(r.get('scores')).get(key));v=e.get('score')
   ok=number(v) and 0<=v<=5 and v*2==int(v*2)
   self.need(ok,'score '+key+' must be 0..5 in half points')
   if ok:total+=v/5*weight;self.need(v>=mins[key],'score '+key+' below adopted starting threshold')
   self.need(text(e.get('evidence')),'score '+key+' actual evidence required')
  self.need(total>=q['benchmark_total_min' if benchmark else 'routine_total_min'],'weighted score below adopted starting threshold')
  self.need(number(r.get('total')) and abs(r['total']-total)<1e-6,'weighted score total inconsistent')
  self.need(r.get('media_sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),'scorecard stale media')
 def presented_steps(self,r,steps,viewing):
  records=r.get('steps');seen=set()
  for entry in seq(records):
   entry=obj(entry);ident=entry.get('step_id')
   if not self.need(text(ident) and ident in steps and ident not in seen,'internal review unknown/duplicate step'):continue
   seen.add(ident);step=steps[ident]
   self.need(entry.get('status')=='pass',ident+' internal explanation failed/unreviewed')
   start,end=entry.get('start'),entry.get('end')
   self.need(number(start) and number(end) and number(viewing.get('duration')) and 0<=start<end<=viewing['duration']+.05,ident+' internal actual presentation interval required')
   ids=entry.get('shot_ids');self.need(isinstance(ids,list) and bool(ids) and all(text(i) for i in ids) and set(ids)==set(seq(step.get('shot_ids'))),ident+' internal shot mapping mismatch')
   for key in ('prerequisites_observed','relation_observed','derivation_observed','boundary_observed','visual_evidence','narration_evidence','audio_visual_coherence'):
    self.need(substantive(entry.get(key)),ident+' '+key+' required from actual presentation')
   self.need(entry.get('unpresented_assumptions')==[],ident+' unpresented assumptions block explanation acceptance')
   mapping=entry.get('referent_evidence');self.need(isinstance(mapping,dict) and bool(mapping) and all(substantive(k) and substantive(v) for k,v in mapping.items()),ident+' actual referent evidence required')
   if step.get('_typed'):self.need(set(obj(mapping))==set(obj(step.get('referent_mappings'))),ident+' actual referent mapping incomplete')
  self.need(seen==set(steps),'internal review promised explanation coverage incomplete')
 def internal_review(self,name,gate,steps,cards,final=False):
  canonical=name in self.qa;r=self.record(name);label=name+' internal review'
  self.need(r.get('status')=='pass',label+' missing/failed'+(' (actual internal explanation and expression review required)' if final else ' (separate paper logic review required)'))
  if not canonical:
   if not final:
    self.need(r.get('basis')=='paper_logic','G1 separate paper logic review required; it is not media acceptance')
    for key in ('reviewer','capability','evidence'):self.need(substantive(r.get(key)),'G1 logic review '+key+' required')
    self.need(r.get('context_sha256')==context_sha256(self.data,'G1'),'G1 logic review stale context')
    return
   self.need(r.get('basis')=='presented_work_only','internal review must use presented work only, not author knowledge or design notes')
   self.need(r.get('context_sha256')==context_sha256(self.data,'G5'),'internal review stale context')
   for role in ('explanation','expression'):
    role_record=obj(obj(r.get('responsibilities')).get(role))
    self.need(role_record.get('status')=='pass',role+' responsibility review missing/failed')
    for key in ('reviewer','capability','evidence'):self.need(substantive(role_record.get(key)),role+' '+key+' required')
  else:
   for key in ('reviewer','reviewed_at','note','evidence'):self.need(substantive(r.get(key)),label+' '+key+' required')
   self.need(r.get('context_sha256')==context_sha256(self.data,gate),label+' stale context')
   ids=r.get('reviewed_step_ids');self.need(isinstance(ids,list) and all(text(i) for i in ids) and len(set(ids))==len(ids) and set(ids)==set(steps),label+' complete explanation step review required')
   if name in ('expression_plan','expression_review'):
    ids=r.get('expression_card_ids');self.need(isinstance(ids,list) and all(text(i) for i in ids) and len(set(ids))==len(ids) and set(ids)==set(cards),label+' complete expression card review required')
   if final:
    self.need(r.get('review_scope')=='final_export' and r.get('scope')=='full_episode',label+' current actual full-episode export required')
    self.need(r.get('media_sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),label+' stale final media')
    self.need(r.get('independent_of_generation_context') is True,label+' independent review context required')
    self.need(r.get('actual_information_only') is True,label+' must use only information actually presented by the work')
   else:
    self.need(r.get('review_scope')=='plan',label+' plan review scope required')
    return
  self.need(r.get('reviewer_kind') in ('human','agent'),'internal reviewer kind must be human or capable agent')
  for key in ('visual_review_capable','audio_review_capable'):self.need(r.get(key) is True,'internal '+key+' required')
  viewing=self.viewing(r.get('viewing'),'internal explanation review','full_episode',final=True)
  for goal in UNDERSTANDING_GOALS:
   check=obj(obj(r.get('understanding_goals')).get(goal))
   self.need(check.get('status')=='pass' and substantive(check.get('evidence')),goal+' understanding condition missing/failed')
  self.presented_steps(r,steps,viewing)
 def declared_feedback_score(self,viewer,protocol):
  """Check volunteered score claims; absence of scores never creates a rubric gate."""
  scores=viewer.get('scores');total=viewer.get('total')
  if scores is None and total is None:return
  valid=isinstance(scores,dict) and bool(scores) and all(substantive(k) and number(v) and v>=0 for k,v in scores.items())
  self.need(valid,'declared feedback scores must be a nonempty finite nonnegative score mapping')
  if not valid:return
  computed=sum(scores.values());self.need(number(computed),'declared feedback score total must be finite')
  if total is not None:self.need(number(total) and number(computed) and abs(total-computed)<1e-6,'declared feedback person total inconsistent')
  # A volunteered protocol constrains its own score claims, without establishing pass quotas.
  maxima=obj(protocol).get('item_max')
  if maxima is not None:
   valid=isinstance(maxima,dict) and bool(maxima) and all(substantive(k) and number(v) and v>0 for k,v in maxima.items())
   self.need(valid,'declared feedback protocol item maxima invalid')
   if valid:self.need(set(scores)==set(maxima) and all(v<=maxima.get(k,-1) for k,v in scores.items()),'declared feedback scores conflict with submitted protocol')
 def declared_feedback_misconceptions(self,feedback,viewers):
  """Investigate actual reported errors without inferring a population quality verdict."""
  counts={}
  for person in seq(viewers):
   declared=obj(person).get('core_misconceptions')
   if declared is None:continue
   valid=isinstance(declared,list) and all(substantive(ident) for ident in declared)
   self.need(valid,'actual feedback core_misconceptions must be an explicit text list')
   if valid:
    for ident in set(declared):counts[ident]=counts.get(ident,0)+1
  summary=feedback.get('shared_core_misconceptions')
  if summary is not None:
   expected={ident for ident,count in counts.items() if count>=2}
   valid=isinstance(summary,list) and all(substantive(ident) for ident in summary)
   self.need(valid and len(set(summary))==len(summary) and set(summary)==expected,'shared misconception summary must equal derived repeated IDs')
  if not counts:return
  resolution=obj(feedback.get('misconception_review'))
  self.need(resolution.get('status')=='resolved' and substantive(resolution.get('evidence')) and resolution.get('media_sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),'observed core misconception requires current internal recheck; removing audience thresholds cannot erase known failures')
  self.need(resolution.get('context_sha256')==context_sha256(self.data,'G5'),'observed misconception recheck stale context')
  self.viewing(resolution.get('viewing'),'observed misconception recheck','full_episode',final=True)
 def optional_feedback(self):
  """Feedback may be recorded; no viewer count, score or sampling gate is required."""
  flags=obj(self.data.get('brief')).get('validation_triggers')
  self.need(isinstance(flags,list) and all(text(x) and x in VALIDATION_TRIGGERS for x in flags),'validation triggers must be explicit recognized values')
  r=self.record('comprehension')
  feedback=obj(r.get('optional_audience_feedback') if 'optional_audience_feedback' in r else r.get('cold_view'))
  if r.get('status')=='audience_checked':
   self.need(text(r.get('audience_feedback_reference')),'audience_checked needs an actual audience feedback reference')
   self.need(feedback.get('status')=='pass','audience_checked needs completed actual optional feedback records')
  if 'viewers' in feedback:self.need(isinstance(feedback.get('viewers'),list),'optional feedback viewers must be a list')
  if feedback.get('status')!='pass':
   self.need(not seq(feedback.get('viewers')),'unperformed feedback cannot claim actual viewer records')
   self.need(feedback.get('actual_viewer_count') in (None,0) and feedback.get('population_understanding_rate') is None and feedback.get('population_rate_claimed') in (None,False),'unperformed feedback cannot claim participants or population rate')
   return
  self.need(r.get('status')=='audience_checked','optional actual feedback must be recorded honestly as audience_checked')
  self.need(feedback.get('media_sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),'optional feedback stale media')
  self.need(feedback.get('population_rate_claimed') in (None,False) and feedback.get('population_understanding_rate') is None,'formative feedback cannot establish population understanding rate')
  viewers=feedback.get('viewers');self.need(isinstance(viewers,list) and bool(viewers),'claimed optional feedback needs actual viewer records')
  ids=set()
  for viewer in seq(viewers):
   viewer=obj(viewer);ident=viewer.get('anonymous_id')
   self.need(text(ident) and ident not in ids,'actual feedback viewer ids missing/duplicate')
   if text(ident):ids.add(ident)
   self.need(viewer.get('real_person') is True,'actual feedback real_person required; agents are not viewers')
   self.need(viewer.get('watched_current_version') is True,'actual feedback must concern the recorded current version')
   answers=viewer.get('raw_answers')
   self.need(isinstance(answers,dict) and bool(answers) and all(text(answer) for answer in answers.values()),'actual raw feedback answers required')
   self.declared_feedback_score(viewer,feedback.get('protocol'))
  self.declared_feedback_misconceptions(feedback,viewers)
  if 'actual_viewer_count' in feedback:
   self.need(type(feedback['actual_viewer_count']) is int and feedback['actual_viewer_count']==len(seq(viewers)),'optional actual viewer count inconsistent')
 def cold_view(self,policy):
  if 'optional_audience_feedback' in self.record('comprehension') or ('cold_view' not in self.record('comprehension') and self.record('comprehension').get('status')=='audience_checked'):
   self.optional_feedback();return
  brief=obj(self.data.get('brief'));flags=brief.get('validation_triggers')
  self.need(isinstance(flags,list) and all(text(x) and x in policy['review_triggers'] for x in flags),'validation triggers must be explicit recognized values')
  r=self.record('comprehension');test=obj(r.get('cold_view'));viewers=seq(test.get('viewers'))
  self.need('viewers' not in test or isinstance(test.get('viewers'),list),'optional feedback viewers must be a list')
  submitted=bool(viewers) or test.get('status') in ('pass','completed','fail') or r.get('status')=='audience_checked'
  if not submitted:
   self.need(test.get('status') in (None,'not_conducted','not_requested','pending'),'optional feedback status invalid')
   self.need(test.get('actual_viewer_count') in (None,0) and test.get('passing_viewer_count') in (None,0) and test.get('population_understanding_rate') is None and test.get('population_rate_claimed') in (None,False),'unperformed feedback cannot claim participants or population rate')
   return
  self.need(test.get('status') in ('pass','completed','fail'),'submitted actual feedback completion status required')
  self.need(test.get('population_rate_claimed') is False and test.get('population_understanding_rate') is None,'formative feedback cannot establish population understanding rate')
  self.need(test.get('media_sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),'cold test stale media')
  for key in ('group_id','sampling_plan_reference'):self.need(text(test.get(key)),'cold-test declared group/plan required')
  viewers=seq(test.get('viewers'));self.need(bool(viewers),'submitted feedback requires actual viewers')
  self.need(type(test.get('actual_viewer_count')) is int and test['actual_viewer_count']==len(viewers),'cold-test actual viewer count inconsistent')
  protocol=obj(test.get('protocol'));item_max=protocol.get('item_max',obj(policy.get('cold_view')).get('legacy_item_max',{'topic':1,'causal_chain':2,'visualization_boundary':1,'conclusion':1}))
  valid_protocol=isinstance(item_max,dict) and bool(item_max) and all(substantive(k) and number(v) and v>0 for k,v in item_max.items())
  self.need(valid_protocol,'cold-test protocol item maxima invalid')
  item_max=item_max if valid_protocol else {}
  minimum=protocol.get('individual_min',4);required=protocol.get('required_item','causal_chain');required_score=protocol.get('required_score',2)
  self.need(number(minimum) and 0<=minimum<=sum(item_max.values()) and text(required) and required in item_max and number(required_score) and 0<=required_score<=item_max.get(required,-1),'cold-test protocol invalid')
  ids=set();passing=0;mis={}
  for person in viewers:
   person=obj(person);ident=person.get('anonymous_id')
   self.need(text(ident) and ident not in ids,'real-viewer anonymous ids missing/duplicate')
   if text(ident):ids.add(ident)
   for key in ('real_person','not_in_production','no_relevant_training','first_unprompted_normal_watch','watched_current_version'):self.need(person.get(key) is True,'cold viewer '+key+' required')
   score=obj(person.get('scores'));total=0
   for key,maximum in item_max.items():
    n=score.get(key);valid=number(n) and 0<=n<=maximum
    self.need(valid,'cold-test score invalid')
    if valid:total+=n
    self.need(text(obj(person.get('raw_answers')).get(key)),'actual raw cold-test answer required')
   self.need(number(person.get('total')) and abs(person['total']-total)<1e-6,'cold-test person total inconsistent')
   self.need(text(person.get('scoring_evidence')),'cold-test scoring basis required')
   self.need(number(minimum) and number(required_score) and required in score,'cold-test protocol invalid')
   if number(minimum) and number(required_score) and total>=minimum and number(score.get(required)) and score[required]>=required_score:passing+=1
   misconceptions=person.get('core_misconceptions')
   valid=isinstance(misconceptions,list) and all(text(i) for i in misconceptions)
   self.need(valid,'explicit core_misconceptions list required, empty only when none observed')
   if valid:
    for misconception in set(misconceptions):mis[misconception]=mis.get(misconception,0)+1
  self.need(type(test.get('passing_viewer_count')) is int and test['passing_viewer_count']==passing,'cold-test passing viewer count inconsistent')
  self.need('shared_core_misconceptions' in test,'shared misconception summary must equal derived repeated IDs')
  self.declared_feedback_misconceptions(test,viewers)
 def caption_and_flicker(self,policy):
  caption=self.record('captions')
  self.need(caption.get('file')==obj(self.data.get('deliverables')).get('captions') and caption.get('sha256')==obj(self.qa.get('reviewed_sha256')).get('captions'),'final caption QA must bind current caption file/hash')
  self.evidence(caption,'final caption QA')
  self.need(text(caption.get('formal_script_sha256')) and caption.get('formal_script_sha256')==obj(self.data.get('narration')).get('script_sha256'),'caption formal script hash stale/missing')
  for key in ('note','evidence'):self.need(text(caption.get(key)),'caption actual '+key+' required')
  checks=caption.get('actual_contrast_checks')
  self.need(isinstance(checks,list) and bool(checks),'actual contrast measurements required')
  for measurement in seq(checks):
   m=obj(measurement);ratio=m.get('ratio')
   self.need(number(ratio) and 1<=ratio<=21 and m.get('unrounded') is True,'unrounded actual contrast measurement required')
   for key in ('foreground','actual_background','method','worst_case_review'):self.need(text(m.get(key)),'contrast '+key+' required')
   self.evidence(m.get('evidence'),'contrast measurement')
   if number(ratio) and ratio<policy['defaults']['text_contrast_min']:
    self.need(text(m.get('calibration_reason')),'contrast below starting target needs actual calibration rationale')
  static=obj(caption.get('static_checks'))
  self.need(static.get('status')=='pass' and text(static.get('evidence')),'caption checks unresolved or missing evidence')
  self.need(static.get('method') in ('automated','manual'),'caption checking method must be actual')
  self.need({'bounds','empty_captions','overlap','formal_text'}<=set(x for x in seq(static.get('covered_checks')) if text(x)),'caption checking coverage incomplete')
  flicker=self.record('flicker')
  for key in ('note','evidence','continuous_review_reference'):self.need(text(flicker.get(key)),'flicker '+key+' required')
  self.need(flicker.get('designed_flash_limit_checked') is True,'flash design limit not checked')
  self.need(isinstance(flicker.get('complex_sequence'),bool),'complex flash applicability required')
  if flicker.get('complex_sequence') is True:self.need(text(flicker.get('complex_sequence_assessment')),'complex flash assessment required')
  else:self.need(text(flicker.get('complex_sequence_reason')),'noncomplex flash applicability reason required')
  events=flicker.get('designed_events');self.need(isinstance(events,list) and all(number(t) and t>=0 for t in events),'designed flash events must be explicit')
  if isinstance(events,list) and all(number(t) for t in events):
   events=sorted(events)
   self.need(all(events[i+3]-events[i]>1 for i in range(max(0,len(events)-3))),'designed flashes exceed three within a second; count alone never proves safety')
 def platform_and_disclosure(self):
  preview=self.record('mobile_preview');phone=obj(preview.get('phone'))
  self.need(phone.get('status')=='pass' and phone.get('surface')=='actual_device','actual phone readability preview required')
  for key in ('device','app_version','checked_at'):self.need(text(phone.get(key)),'phone '+key+' required')
  self.need(phone.get('video_sha256')==obj(self.qa.get('reviewed_sha256')).get('video'),'phone preview stale video')
  for key in ('main_content_visible','captions_visible','audio_checked'):self.need(phone.get(key) is True,'phone '+key+' must actually be checked')
  geometry=phone.get('actual_overlay_geometry');self.need(isinstance(geometry,list) and bool(geometry),'actual platform overlay geometry required')
  self.need(phone.get('overlay_coordinate_space') in ('video_pixels','screenshot_pixels'),'phone overlay coordinate space required')
  canvas=phone.get('canvas');valid_canvas=isinstance(canvas,list) and len(canvas)==2 and all(number(v) and v>0 for v in canvas)
  self.need(valid_canvas,'phone overlay canvas required')
  for area in seq(geometry):
   area=obj(area);values=[area.get(k) for k in ('x','y','width','height')]
   valid=all(number(v) for v in values)
   self.need(valid,'phone overlay requires finite rectangle geometry')
   if valid:
    x,y,w,h=values;self.need(x>=0 and y>=0 and w>0 and h>0 and valid_canvas and x+w<=canvas[0] and y+h<=canvas[1],'phone overlay rectangle outside declared canvas')
  self.evidence(phone.get('screenshot'),'phone preview screenshot')
  declaration=obj(self.record('release').get('ai_disclosure'))
  self.need(declaration.get('status')=='pass' and isinstance(declaration.get('contains_generated_content'),bool),'AI disclosure applicability/status required')
  generated=obj(self.data.get('narration')).get('voice_type')=='synthetic' or any(obj(a).get('kind')=='ai_generated' and obj(a).get('id') in used_asset_ids(self.data) for a in seq(self.data.get('assets')))
  if generated:self.need(declaration.get('contains_generated_content') is True,'known generated content cannot be marked absent')
  if declaration.get('contains_generated_content') is True:
   for key in ('applicable_platform_controls_checked','platform_declaration_used','required_provenance_preserved'):self.need(declaration.get(key) is True,'AI disclosure '+key+' not checked')
   for key in ('current_rule_reference','declaration_evidence'):self.need(text(declaration.get(key)),'AI disclosure '+key+' required')
  else:self.need(text(declaration.get('not_applicable_reason')),'AI disclosure non-applicability reason required')
 def real_anchor_required(self):
  default=json.loads((Path(__file__).resolve().parents[1]/'config/series-profile.json').read_text())
  profile=default
  if 'series_profile' in self.data:
   ref=obj(self.data.get('series_profile'));path=self.evidence(ref,'project series profile')
   self.need(text(ref.get('scope_reference')),'project profile needs actual project-scope reference')
   if path:
    profile=obj(json.loads(path.read_text()))
    self.need(text(profile.get('id')),'project profile id required')
    if profile.get('id')==default['id']:
     self.need(obj(profile.get('medium')).get('real_anchor')==default['medium']['real_anchor'],'current series real-video requirement cannot be silently removed')
  mode=obj(profile.get('medium')).get('real_anchor')
  self.need(mode in ('authentic_continuous_video','not_required'),'explicit project real-anchor policy required')
  return mode!='not_required'
 def run(self,target,policy):
  n=GATES.index(target);gates=obj(self.qa.get('gates'));steps=self.causal();self.explanation_design(steps)
  text_items=validate_text_plan(self)
  cards=self.expression_cards(steps) if n>=1 else {}
  self.internal_review('explanation_logic','G1',steps,cards)
  if n>=1:self.internal_review('expression_plan','G2',steps,cards)
  brief=obj(self.data.get('brief'))
  for k in ('audience','one_sentence_answer'):self.need(text(brief.get(k)),'brief '+k+' required')
  self.need(substantive(brief.get('must_see_relation',brief.get('must_make_understandable',brief.get('must_see_change')))),'brief must_see_relation required (must_make_understandable and legacy must_see_change accepted)')
  for k in ('out_of_scope','forbidden_misrepresentations'):self.need(isinstance(brief.get(k),list),'brief '+k+' required')
  self.need(brief.get('production_class') in ('R','N','B'),'production class R/N/B required')
  for role in ('producer','science_editor','director','art_animation','audio_caption','reviewer','publisher'):self.need(text(obj(brief.get('roles')).get(role)),'responsible '+role+' required')
  for gate in GATES[:n+1]:
   r=obj(gates.get(gate));self.need(r.get('status')=='passed',gate+' not passed; no automatic promotion')
   for k in ('reviewer','reviewed_at','scope'):self.need(text(r.get(k)),gate+' '+k+' required')
   self.need(r.get('context_sha256')==context_sha256(self.data,gate),gate+' stale stage context')
   refs=r.get('review_refs');expected={ref for ref in REQUIRED_REVIEWS[gate] if ref not in ('explanation_logic','expression_plan','explanation_review','expression_review') or ref in self.qa}
   self.need(isinstance(refs,list) and expected<=set(x for x in seq(refs) if text(x)),gate+' required QA references missing')
   for ref in seq(refs):
    if not text(ref):self.need(False,gate+' invalid QA reference');continue
    record=self.record(ref);allowed=('editor_reviewed','audience_checked') if ref=='comprehension' else ('pass',)
    self.need(record.get('status') in allowed,gate+' referenced review not passed: '+ref)
    if ref not in ('release','publication','visual_frames.animation'):
     self.need(text(record.get('note')) and (text(record.get('evidence')) or ref in ('shotbook','science','rights','audio','narration','covers','mobile_preview','comprehension','topic_alignment','visual_frames')),gate+' review note/evidence missing: '+ref)
   evidence=r.get('evidence');self.need(isinstance(evidence,list) and bool(evidence),gate+' evidence required')
   for e in seq(evidence):self.evidence(e,gate)
  if n>=1:
   self.viewing(self.record('shotbook').get('viewing'),'G2 roughcut','full_roughcut')
   validate_subject_motion(self,self.record('shotbook').get('subject_motion'),obj(self.record('shotbook').get('viewing')),'G2',policy['subject_motion'],set(steps))
   validate_text_review(self,'G2',obj(self.record('shotbook').get('viewing')),text_items)
   validate_voice_continuity(self,'G2',obj(self.record('shotbook').get('viewing')))
   narration=obj(self.data.get('narration'))
   self.evidence({'file':narration.get('script_file'),'sha256':narration.get('script_sha256')},'narration script')
   self.need(narration.get('status')=='ready' and isinstance(narration.get('language'),str) and narration['language'].lower().split('-')[0]=='zh','actual ready Chinese working narration required')
   audio=next((a for a in seq(self.data.get('assets')) if isinstance(a,dict) and a.get('id')==narration.get('asset_id')), {})
   self.need(audio.get('kind')=='audio','source narration must be an audio asset')
   audio_path=self.evidence({'file':audio.get('file'),'sha256':narration.get('audio_sha256')},'source narration')
   if audio_path:self.duration(audio_path,require_video=False,label='source narration')
  if n>=2:
   self.animation(steps);self.failures(final=n>=4);self.asset_catalog(steps,representative=True)
   animation=self.record('visual_frames.animation')
   validate_subject_motion(self,animation.get('subject_motion'),obj(animation.get('viewing')),'G3',policy['subject_motion'],set(x for x in seq(animation.get('step_ids')) if text(x)))
   validate_text_review(self,'G3',obj(animation.get('viewing')),text_items)
   validate_voice_continuity(self,'G3',obj(animation.get('viewing')))
   if n>=3:self.asset_catalog(steps,representative=False)
   design=obj(self.data.get('design'));approval=obj(design.get('approval'))
   self.need(approval.get('status')=='pass','actual design approval missing/failed')
   self.need(obj(approval.get('scope')).get('visual_style') is True,'design approval does not cover visual style')
   self.need(text(approval.get('actual_feedback_ref')) and text(approval.get('reviewer')),'actual style feedback reference and reviewer required')
   board=design.get('board_sha256')
   self.need(text(board) and bool(re.fullmatch('[0-9a-f]{64}',board)) and approval.get('approved_board_sha256')==board,'design approval does not bind current board version')
   self.evidence({'file':design.get('board_reference'),'sha256':board},'G3 design board')
   for scale in ('whole_scene','object_midshot','mechanism_closeup'):
    frame=obj(obj(design.get('keyframe_scales')).get(scale))
    self.need(frame.get('status')=='pass' and text(frame.get('note')), 'G3 '+scale+' actual art review required')
    self.evidence(frame,'G3 '+scale)
   if 'new_style' in seq(brief.get('validation_triggers')):
    variants=seq(design.get('comparison_variants'))
    self.need(len(variants)>=2,'new style needs two comparable variants')
    for variant in variants:
     variant=obj(variant)
     self.evidence(variant,'style comparison')
     self.need(text(variant.get('comparison_note')) and variant.get('same_fact_voice_chain') is True,'style variants need same fact/voice/chain comparison')
  if n>=3:
   self.need(obj(self.data.get('scope')).get('kind')=='episode','complete candidate/quality gates require episode scope')
   for key in ('video','captions','editable_project','audio_stems','source_manifest'):
    self.evidence({'file':obj(self.data.get('deliverables')).get(key),'sha256':obj(self.qa.get('reviewed_sha256')).get(key)},'G4 '+key)
  if n>=4:
   self.viewing(self.record('visual_frames').get('viewing'),'G5 complete viewing','full_episode',final=True)
   validate_subject_motion(self,self.record('visual_frames').get('subject_motion'),obj(self.record('visual_frames').get('viewing')),'G5',policy['subject_motion'],set(steps))
   validate_text_review(self,'G5',obj(self.record('visual_frames').get('viewing')),text_items)
   validate_voice_continuity(self,'G5',obj(self.record('visual_frames').get('viewing')))
   self.need(self.record('visual_frames').get('independent_of_generation_context') is True,'independent review context required; not proof of human perception')
   audio=self.record('audio');self.need(set(policy['listening']['required_environments'])<=set(x for x in seq(audio.get('environments')) if text(x)),'headphones and phone-speaker actual listening required')
   for env in policy['listening']['required_environments']:
    self.viewing(obj(audio.get('listening')).get(env),'G5 '+env,'full_episode',final=True,listening_only=True)
   full_steps=self.record('visual_frames').get('process_steps')
   seen=set()
   for e in seq(full_steps):
    e=obj(e);ident=e.get('step_id')
    self.need(text(ident) and ident in steps and ident not in seen,'G5 invalid/duplicate process step')
    if text(ident):seen.add(ident)
    self.need(e.get('status')=='pass' and text(e.get('evidence')),'G5 actual process evidence required')
   self.need(seen==set(steps),'G5 full primary explanation evidence incomplete (legacy full primary causal chain evidence incomplete)')
   real_ids={obj(a).get('id') for a in seq(self.data.get('assets')) if obj(a).get('kind') in ('real_capture','real_observation')}
   shot_used={i for shot in seq(self.data.get('shots')) for i in seq(obj(shot).get('asset_ids')) if text(i)}
   if self.real_anchor_required():
    self.need(bool(real_ids & shot_used),'current series requires an actually used real continuous-video anchor; declarations do not prove authenticity')
   self.caption_and_flicker(policy);self.scores(policy);self.internal_review('explanation_review','G5',steps,cards,final=True);self.internal_review('expression_review','G5',steps,cards,final=True);self.cold_view(policy)
  if n>=5:
   self.need(obj(self.data.get('scope')).get('kind')=='episode' and obj(self.data.get('scope')).get('publication_ready') is True,'release requires a complete episode explicitly ready for publication')
   self.platform_and_disclosure()
   self.evidence({'file':obj(self.data.get('deliverables')).get('post_copy'),'sha256':obj(self.qa.get('reviewed_sha256')).get('post_copy')},'release independent post copy')
   r=self.record('release');self.need(r.get('authorization_status')=='pass','release authorization status must be independently verified')
   self.need(r.get('bundle_sha256')==digest({'deliverables':self.data.get('deliverables'),'hashes':self.qa.get('reviewed_sha256'),'title':self.data.get('title'),'description':self.data.get('description'),'tags':self.data.get('tags'),'platform':self.record('mobile_preview')}),'release approval stale bundle')
   for key in ('authorization_reference','authorization_scope','ai_disclosure_evidence','rights_evidence'):self.need(text(r.get(key)),'release '+key+' required')
   self.need(r.get('covers_exact_bundle') is True,'release authorization does not cover exact bundle')
  if n>=6:
   p=self.record('publication');self.need(p.get('state')=='published' and p.get('readback_matches_bundle') is True,'publication not confirmed by matching readback')
   self.need(text(p.get('work_id')) or text(p.get('url')),'publication work ID or permalink required')
   for key in ('actual_published_at','readback_reference'):self.need(text(p.get(key)),'publication '+key+' required')
   self.need(p.get('bundle_sha256')==self.record('release').get('bundle_sha256'),'publication readback bundle mismatch')
   for key in ('platform','account'):self.need(text(p.get(key)) and p.get(key)==self.record('mobile_preview').get(key),'publication readback destination mismatch')
  return self.errors

def check_stage(data,root,target):
 try:
  policy=json.loads((Path(__file__).resolve().parents[1]/'config/production-policy.json').read_text())
  return Checks(data,root).run(target,policy)
 except (KeyError, TypeError, ValueError, OSError) as exc:
  return ['stage: malformed or missing required evidence/policy: '+str(exc)]

def semantic_warnings(data):
 """Timing offsets trigger review, never an automatic artistic/semantic failure."""
 warnings=[]
 for shot in seq(data.get('shots')):
  for event in seq(obj(obj(shot).get('shotbook')).get('semantic_events')):
   event=obj(event);a=event.get('audio_time_ms');v=event.get('visual_time_ms')
   if number(a) and number(v) and abs(a-v)>150:
    warnings.append('Semantic offset >150ms: '+str(obj(shot).get('id'))+' / '+str(event.get('label'))+'; review actual scene and record any intentional anticipation/reaction')
 return warnings
