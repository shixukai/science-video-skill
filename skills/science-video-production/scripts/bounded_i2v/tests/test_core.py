import unittest, tempfile, pathlib, importlib.util, ast, json, os, subprocess, time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
P=pathlib.Path(__file__).parent.parent
spec=importlib.util.spec_from_file_location('g',P/'i2v_core.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
class CoreTests(unittest.TestCase):
 def test_syntax(self):
  for p in P.glob('*.py'):ast.parse(p.read_text())
 def test_exclusive_partial_blocks(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'attempt';p.write_text('{')
   with self.assertRaises(FileExistsError):g.persist_new(p,{})
 def test_collector_failure_never_posts(self):
  with tempfile.TemporaryDirectory() as d:
   b={'submission_budget_seconds':600,'observation_budget_seconds':600,'authorization_evidence':{'sha256':'A'},'collector':{}}
   with patch.object(g,'preflight',return_value=(b,{})),patch.object(g,'collect_dynamic',side_effect=ValueError('identity denied')),patch.object(g,'request_local') as http:
    r=g.submit('B',pathlib.Path(d),c={'shot_id':'test','parent_prompt_id':None,'design_sha256':'D','scope_sha256':'S'});self.assertFalse(r['post_started']);self.assertEqual(r['state'],'known_no_post');http.assert_not_called()
    with self.assertRaises(FileExistsError):g.submit('B',pathlib.Path(d),c={'shot_id':'test','parent_prompt_id':None,'design_sha256':'D','scope_sha256':'S'})
 def test_network_allowlist(self):
  for m,p in [('POST','/interrupt'),('GET','/object_info'),('DELETE','/prompt'),('POST','http://other/prompt')]:
   with self.assertRaises(ValueError):g.request_local(m,p)
 def test_changed_graph_rejected(self):
  with self.assertRaises(ValueError):g.compare_graph({'3':{'inputs':{'seed':1}}},{'3':{'inputs':{'seed':2}}})
 def test_stale_dynamic_fails(self):
  with self.assertRaises(ValueError):g.freshness({'observed_at':'2000-01-01T00:00:00Z'})
class UtilizationTelemetryTests(unittest.TestCase):
 def fixture(self,root,value):
  now=datetime.now(timezone.utc).isoformat()
  minimum={'ram_available_bytes':17179869184,'vram_available_bytes':12884901888,'disk_available_bytes':2147483648}
  bindings={'executor_lock':{'holder_pid':123,'path':'synthetic-lock','holder_creation_time':now},'service_identity':{'synthetic_only':True},'worker_id':'one','output_root':str(root),'unique_executor_lock':'one-lock','minimum_resources':minimum,'gpu_load_policy':{'minimum_window_seconds':6,'minimum_sample_count':4}}
  resource={'collection_id':'synthetic','observed_at':now,'gpu_load':{'status':'measured' if value is not None else 'telemetry_unavailable','metric':'gpu_total_utilization_percent','observation_source':'synthetic-only','samples':[{'observed_at':(datetime.fromisoformat(now)-timedelta(seconds=n)).isoformat(),'utilization_percent':value} for n in (7,5,3,1)]},'lock_evidence':{'holder_pid':123,'path':'synthetic-lock','holder_creation_time':now,'collector_parent_pid':123,'byte_lock_held':True},'kind':'local_process_gpu_queue_inspection','endpoint':g.ENDPOINT,'service_ready':True,'queue_empty':True,'service_pid':456,'service_identity':bindings['service_identity'],'active_worker_ids':['one'],'gpu_process_pids':[456],'unattributed_gpu_process_pids':[456],'output_root':str(root),'inspection_source':'synthetic unit fixture','unique_executor_lock':'one-lock',**minimum}
  return resource,bindings
 def test_11_12_100_and_unavailable_utilization_do_not_refuse(self):
  with tempfile.TemporaryDirectory() as d:
   for value in (11,12,100,None):
    with self.subTest(utilization=value):
     resource,bindings=self.fixture(pathlib.Path(d),value)
     g.validate_dynamic(resource,bindings,'synthetic',time.time()-10,time.time()+10)
 def test_capacity_queue_worker_and_pid_guards_remain(self):
  with tempfile.TemporaryDirectory() as d:
   for field,value in [('ram_available_bytes',1),('vram_available_bytes',1),('disk_available_bytes',1),('queue_empty',False),('active_worker_ids',['one','other']),('gpu_process_pids',[456,456])]:
    with self.subTest(field=field):
     resource,bindings=self.fixture(pathlib.Path(d),12);resource[field]=value
     with self.assertRaises(ValueError):g.validate_dynamic(resource,bindings,'synthetic',time.time()-10,time.time()+10)
class EvidenceTests(unittest.TestCase):
 def test_telemetry_persisted_before_capacity_rejection(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);resource={'collection_id':'one','gpu_load':{'samples':[{'utilization_percent':37}]},'observed_at':'unchanged-source-time'}
   b={'collector':{'timeout_seconds':30},'executor_lock':{'holder_pid':os.getpid()},'service_identity':{'input_root':'input'},'worker_id':'worker','unique_executor_lock':'lock','output_root':'output','gpu_load_policy':{},'startup_record':{},'environment':{},'workspace_gpu_lock_path':'lock'}
   proc=subprocess.CompletedProcess([],0,json.dumps(resource),'')
   with patch.object(g,'check_collector',return_value=(root/'collector.py',root/'python')),patch.object(g.subprocess,'run',return_value=proc),patch.object(g,'validate_dynamic',side_effect=ValueError('insufficient checked resource: vram_available_bytes')):
    with self.assertRaises(ValueError):g.collect_dynamic(b,root,'one')
   self.assertEqual(json.loads((root/'dynamic-resource-one.json').read_text()),resource)
   self.assertEqual(json.loads((root/'resource-admission-failure-one.json').read_text())['state'],'NOT_ADMITTED_NO_POST')
   self.assertEqual(json.loads((root/'collector-invocation-one.json').read_text())['stdout'],json.dumps(resource))
 def test_failed_process_stderr_saved(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);b={'collector':{'timeout_seconds':30},'executor_lock':{'holder_pid':os.getpid()},'service_identity':{'input_root':'input'},'worker_id':'worker','unique_executor_lock':'lock','output_root':'output','gpu_load_policy':{},'startup_record':{},'environment':{},'workspace_gpu_lock_path':'lock'}
   with patch.object(g,'check_collector',return_value=(root/'collector.py',root/'python')),patch.object(g.subprocess,'run',return_value=subprocess.CompletedProcess([],1,'','actual query failure')):
    with self.assertRaises(ValueError):g.collect_dynamic(b,root,'two')
   self.assertEqual(json.loads((root/'collector-invocation-two.json').read_text())['stderr'],'actual query failure')
if __name__=='__main__':unittest.main()
