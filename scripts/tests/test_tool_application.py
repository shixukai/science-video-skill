"""Synthetic contract checks; never evidence of actual video quality."""
import copy,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from stage_checks import Checks,context_sha256
from check_reference_system import caption_baselines

class ToolApplicationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  (self.root/'record.txt').write_text('synthetic record only')
  self.e={'file':'record.txt','sha256':hashlib.sha256((self.root/'record.txt').read_bytes()).hexdigest()}
  self.d={'shots':[{'id':'A','shotbook':{'start':0,'end':1}},{'id':'B','shotbook':{'start':1,'end':2}}], 'qa':{'visual_frames':{'status':'fail','failures':[]}}}
  self.row={'need':'candidate selection','selection_reason':'actual scene needs evidence','source_id':'openmontage','usage_mode':'method','read_reference':{'version':'9327439db69021ab4b0e2776729bf3b58fdb5a87','files':['asset-director.md']},'shot_ids':['A'],'status':'applied','artifact_evidence':self.e}
 def tearDown(self):self.tmp.cleanup()
 def tools(self,expanding=False):
  c=Checks(self.d,self.root);c.tool_applications(expanding);return c.errors
 def test_unselected_tools_need_no_install(self):self.assertEqual(self.tools(True),[])
 def test_method_does_not_require_framework(self):self.d['tool_applications']=[self.row];self.assertEqual(self.tools(True),[])
 def test_runtime_requires_install_and_execution(self):
  self.row['usage_mode']='runtime';self.d['tool_applications']=[self.row];self.assertTrue(self.tools())
  self.row.update(installation_evidence=self.e,execution_evidence=self.e);self.assertEqual(self.tools(),[])
 def test_missing_artifact_not_applied(self):
  self.row.pop('artifact_evidence');self.d['tool_applications']=[self.row];self.assertTrue(self.tools())
 def test_planned_does_not_claim_applied(self):
  self.row['status']='planned';self.row.pop('artifact_evidence');self.d['tool_applications']=[self.row]
  self.assertEqual(self.tools(),[]);self.assertTrue(self.tools(True))
 def test_moving_read_version_rejected(self):
  self.row['read_reference']['version']='main';self.d['tool_applications']=[self.row];self.assertTrue(self.tools())
 def test_absent_shot_rejected(self):
  self.row['shot_ids']=['missing'];self.d['tool_applications']=[self.row];self.assertTrue(self.tools())
 def test_stale_artifact_rejected(self):
  self.row['artifact_evidence']=dict(self.e,sha256='0'*64);self.d['tool_applications']=[self.row];self.assertTrue(self.tools())
 def test_full_timing(self):
  c=Checks(self.d,self.root);c.whole_shot_coverage(2);self.assertEqual(c.errors,[])
  c.whole_shot_coverage(110);self.assertTrue(c.errors)
 def test_gap_and_overlap(self):
  for start in (.8,1.2):
   self.d['shots'][1]['shotbook']['start']=start;c=Checks(self.d,self.root);c.whole_shot_coverage(2);self.assertTrue(c.errors)
 def test_open_failure_allows_repair_but_not_expansion(self):
  self.d['qa']['visual_frames']['failures']=[{'scope':'whole_episode','status':'open'}]
  c=Checks(self.d,self.root);c.expansion_failures(False);self.assertEqual(c.errors,[]);c.expansion_failures(True);self.assertTrue(c.errors)
 def test_failed_overall_review_cannot_hide_behind_empty_history(self):
  c=Checks(self.d,self.root);c.expansion_failures(True);self.assertTrue(c.errors)
 def test_failed_art_cannot_hide_behind_pending_overall(self):
  for field in ('art','motion','finesse'):
   self.d['qa']['visual_frames']={'status':'not_reviewed','failures':[],field:{'status':'fail'}}
   c=Checks(self.d,self.root);c.expansion_failures(False);self.assertEqual(c.errors,[]);c.expansion_failures(True);self.assertTrue(c.errors)
 def test_failed_finesse_criterion_blocks_only_expansion(self):
  for dimension in ('static','motion','integration'):
   self.d['qa']['visual_frames']={'status':'not_reviewed','failures':[],'finesse':{'status':'pending',dimension:{'criteria':[{'status':'fail'}]}}}
   c=Checks(self.d,self.root);c.expansion_failures(False);self.assertEqual(c.errors,[]);c.expansion_failures(True);self.assertTrue(c.errors)
 def test_application_evidence_changes_context(self):
  before=context_sha256(self.d,'G4');self.d['tool_applications']=[self.row];self.assertNotEqual(before,context_sha256(self.d,'G4'))
 def test_execution_receipts_do_not_expire_paper_gates(self):
  self.d['tool_applications']=[dict(self.row,status='planned')];before=[context_sha256(self.d,g) for g in ('G1','G2')]
  self.d['tool_applications'][0]['status']='applied';self.assertEqual(before,[context_sha256(self.d,g) for g in ('G1','G2')])
 def test_empty_field_preserves_legacy_context(self):
  before=[context_sha256(self.d,g) for g in ('G1','G2','G3','G4','G5','G6','G7')];self.d['tool_applications']=[]
  self.assertEqual(before,[context_sha256(self.d,g) for g in ('G1','G2','G3','G4','G5','G6','G7')])
 def test_future_tool_does_not_block_representative_expansion(self):
  self.d['tool_applications']=[self.row,dict(self.row,status='planned',shot_ids=['B'])]
  c=Checks(self.d,self.root);c.tool_applications(True,{'A'});self.assertEqual(c.errors,[])
  c.tool_applications(True);self.assertTrue(c.errors)
 def test_unrelated_stale_application_does_not_block_representative(self):
  self.d['tool_applications']=[self.row,dict(self.row,shot_ids=['B'],artifact_evidence=dict(self.e,sha256='0'*64))]
  c=Checks(self.d,self.root);c.tool_applications(True,{'A'});self.assertEqual(c.errors,[])
  c.tool_applications(True);self.assertTrue(c.errors)
 def test_landscape_default_preserves_portrait_recovery(self):
  p=json.loads((Path(__file__).resolve().parents[2]/'config/series-profile.json').read_text())
  self.assertEqual(p['delivery']['canvas'],[1920,1080]);self.assertEqual(p['landscape_captions']['canvas'],[1920,1080]);self.assertIsNone(p['landscape_captions']['baselines'])
  self.assertEqual(caption_baselines(p,1080,1920),{'narration':1615,'real_footage':1690})
  with self.assertRaises(ValueError):caption_baselines(p,1920,1080)
if __name__=='__main__':unittest.main()
