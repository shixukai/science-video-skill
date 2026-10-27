import unittest,sys,json,copy,hashlib,tempfile,subprocess,importlib.util
from pathlib import Path
from unittest.mock import patch
R=Path(__file__).parent.parent
spec=importlib.util.spec_from_file_location('runner',R/'runner.py');r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
g=r.load_core()
def cfg():return json.loads((R/'tests/fixtures/candidate_a.json').read_text())
class Tests(unittest.TestCase):
 def test_two_configs_same_core_actual_cli(self):
  before=r.core_hashes();results=[]
  for n in ('a','b'):
   p=R/'tests/fixtures'/('candidate_'+n+'.json');proc=subprocess.run([sys.executable,'-I','-S','-B',str(R/'runner.py'),'--dry-run','--config',str(p),'--config-sha256',r.sha(p)],capture_output=True,text=True)
   self.assertEqual(proc.returncode,0,proc.stderr);results.append(json.loads(proc.stdout))
  self.assertEqual(results[0]['core_sha256'],results[1]['core_sha256']);self.assertEqual(before,r.core_hashes());self.assertNotEqual(results[0]['config_sha256'],results[1]['config_sha256'])
 def test_two_graphs_within_capability(self):
  for n in ('a','b'):r.validate_graph(json.loads((R/f'tests/fixtures/graph_{n}.json').read_text()),json.loads((R/f'tests/fixtures/candidate_{n}.json').read_text()))
 def test_supported_skill_patch_versions(self):
  for version in ('1.6.5','1.6.6','1.6.7','1.6.8','1.6.9'):
   c=cfg();c['skill_version']=version;r.validate_config(c)
  for version in ('1.6.10','latest',''):
   c=cfg();c['skill_version']=version
   with self.assertRaises(ValueError):r.validate_config(c)
 def test_utilization_admission_ceiling_cannot_be_reintroduced(self):
  for ceiling in (10,11,12,100):
   c=cfg();c['bindings']['gpu_load_policy']['max_utilization_percent']=ceiling
   with self.assertRaises(ValueError):r.validate_config(c)
 def test_capacity_thresholds_still_fixed(self):
  c=cfg();c['bindings']['minimum_resources']['vram_available_bytes']=1
  with self.assertRaises(ValueError):r.validate_config(c)
 def test_different_root_rejected(self):
  c=cfg();c['candidate_root']+='-clone'
  with self.assertRaises(ValueError):r.validate_config(c)
 def test_stale_holder_in_config_rejected(self):
  c=cfg();c['bindings']['executor_lock']={}
  with self.assertRaises(ValueError):r.validate_config(c)
 def test_service_chain_drift_rejected(self):
  c=cfg();c['bindings']['service_identity']['identity_processes'][1]['ParentProcessId']=999
  with self.assertRaises(ValueError):r.validate_config(c)
 def test_config_drift_review_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'c.json';q=Path(d)/'review.json';p.write_text(json.dumps(cfg()));q.write_text(json.dumps({'status':'pass','independent_of_executor':True,'config_sha256':'f'*64,'core_sha256':r.core_hashes()}))
   with self.assertRaises(ValueError):r.review_config(p,r.sha(p),q,r.sha(q))
 def test_unknown_post_never_reposts(self):
  with tempfile.TemporaryDirectory() as d:
   b={'submission_budget_seconds':600,'observation_budget_seconds':600,'authorization_evidence':{'sha256':'A'},'collector':{},'executor_lock':{'holder_pid':g.os.getpid()},'config_sha256':'C'};c={'shot_id':'synthetic','parent_prompt_id':None,'design_sha256':'D','scope_sha256':'S'}
   def http(method,path,*a):
    if method=='GET':return {'queue_running':[],'queue_pending':[]}
    raise TimeoutError('accepted state unknown')
   with patch.object(g,'preflight',return_value=(b,{})),patch.object(g,'collect_dynamic',return_value=({'lock_evidence':{}},{'collection_started_unix':0,'collection_finished_unix':1})),patch.object(g,'validate_dynamic'),patch.object(g,'check_condition_image'),patch.object(g,'request_local',side_effect=http) as req:
    out=g.submit('B',Path(d),c=c);self.assertTrue(out['post_started']);self.assertEqual(out['state'],'unknown_do_not_retry')
    with self.assertRaises(FileExistsError):g.submit('B',Path(d),c=c)
    self.assertEqual(sum(x.args[0]=='POST' for x in req.call_args_list),1)
 def test_known_no_post_recovery_does_not_accept_unknown(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'o';p.write_text(json.dumps({'post_started':True,'state':'unknown_do_not_retry'}));q=Path(d)/'r';q.write_text(json.dumps({'state':'runner_work_completed_locks_released','locks_released':True,'holder_pid':123,'post_started':False}));c=cfg();c['lineage']={'kind':'known_no_post_recovery','evidence':{'outcome':{'path':str(p),'sha256':r.sha(p)},'runner_completion':{'path':str(q),'sha256':r.sha(q)}}}
   with self.assertRaises(ValueError):r.check_lineage(c)
 def test_save_matching_recovers_partial_archive_without_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'receipt';r.save_matching(p,{'state':'same'});before=p.read_bytes();r.save_matching(p,{'state':'same'});self.assertEqual(before,p.read_bytes())
   with self.assertRaises(ValueError):r.save_matching(p,{'state':'changed'})
 def test_extra_sampler_and_rewired_decode_rejected(self):
  c=cfg();graph=json.loads((R/'tests/fixtures/graph_a.json').read_text());graph['99']=copy.deepcopy(graph['3']);graph['99']['inputs']['steps']=9999;graph['8']['inputs']['samples']=['99',0];c['bindings']['derived_graph_sha256']=hashlib.sha256(r.canon(graph)).hexdigest()
  with self.assertRaises(ValueError):r.validate_graph(graph,c)
 def test_loader_and_edge_and_dimension_drift_rejected(self):
  for node,key,value in [('37','unet_name','different.safetensors'),('8','samples',['55',0]),('55','width',2048)]:
   c=cfg();graph=json.loads((R/'tests/fixtures/graph_a.json').read_text());graph[node]['inputs'][key]=value;c['bindings']['derived_graph_sha256']=hashlib.sha256(r.canon(graph)).hexdigest()
   with self.assertRaises(ValueError):r.validate_graph(graph,c)
 def test_unknown_or_foreign_persistent_gpu_marker_never_cleared(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'local-gpu-execution-uncertain.json';x={'owner_nonce':'one'};r.claim_gpu_marker(p,x)
   with self.assertRaises(ValueError):r.claim_gpu_marker(p,{'owner_nonce':'new-engine'})
   with self.assertRaises(ValueError):r.clear_owned_marker(p,x,False)
   self.assertTrue(p.exists())
   with self.assertRaises(ValueError):r.clear_owned_marker(p,{'owner_nonce':'other'},True)
   self.assertTrue(p.exists());r.clear_owned_marker(p,x,True);self.assertFalse(p.exists())
 def test_generic_code_has_no_profile_home_or_instance_literals(self):
  for n in r.CORE_FILES:
   source=(R/n).read_text()
   self.assertNotIn('C:'+chr(92)+'Users'+chr(92),source)
if __name__=='__main__':unittest.main()
