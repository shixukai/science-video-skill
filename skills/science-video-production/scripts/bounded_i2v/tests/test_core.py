import unittest, tempfile, pathlib, importlib.util, ast, json, os, subprocess
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
class EvidenceTests(unittest.TestCase):
 def test_high_load_observation_persisted_before_rejection(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);resource={'collection_id':'one','gpu_load':{'samples':[{'utilization_percent':37}]},'observed_at':'unchanged-source-time'}
   b={'collector':{'timeout_seconds':30},'executor_lock':{'holder_pid':os.getpid()},'service_identity':{'input_root':'input'},'worker_id':'worker','unique_executor_lock':'lock','output_root':'output','gpu_load_policy':{'max_utilization_percent':10},'startup_record':{},'environment':{},'workspace_gpu_lock_path':'lock'}
   proc=subprocess.CompletedProcess([],0,json.dumps(resource),'')
   with patch.object(g,'check_collector',return_value=(root/'collector.py',root/'python')),patch.object(g.subprocess,'run',return_value=proc),patch.object(g,'validate_dynamic',side_effect=ValueError('observed or unknown heavy load blocks this attempt')):
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
