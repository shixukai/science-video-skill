"""Offline data/source tests, NOT PowerShell or Windows execution certification."""
import copy, hashlib, json, ntpath, re, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def relative(s):
    if not isinstance(s,str) or not s or ntpath.isabs(s) or ':' in s or any(p in ('.','..','') for p in re.split(r'[\\/]',s)): raise ValueError('relative path')
    return s

def check(c):
    required={'schema_version','executor','candidate_id','candidate_root','input_manifest','skill_lock','skill_root','blender','service_evidence','expected_outputs','argv','prerequisite_receipts','scope'}
    if set(c)!=required or c['schema_version']!=1 or c['executor']!='blender-local-three-keyframes': raise ValueError('schema')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',c['candidate_id']): raise ValueError('candidate')
    root=c['candidate_root']
    if not ntpath.isabs(root) or not ntpath.isabs(c['skill_root']): raise ValueError('absolute root')
    for key in ('input_manifest','skill_lock','service_evidence'):
        if set(c[key])!={'path','sha256'} or not re.fullmatch('[a-f0-9]{64}',c[key]['sha256']): raise ValueError('binding')
        relative(c[key]['path'])
    if set(c['blender'])!={'path','sha256'} or ntpath.basename(c['blender']['path'])!='blender.exe' or not re.fullmatch('[a-f0-9]{64}',c['blender']['sha256']): raise ValueError('binary')
    expected=['--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',ntpath.join(root,'package','run_three_keyframes.py'),'--','--skill-root',c['skill_root'],'--skill-lock',ntpath.join(root,c['skill_lock']['path'])]
    if c['argv']!=expected: raise ValueError('argv')
    if c['expected_outputs']!=[rf'output\frame_{n:04}.png' for n in (0,33,47)]: raise ValueError('outputs')
    s=c['scope']
    if set(s)!={'FrameCount','Width','Height','Samples','Device','States','Animation'} or (s['FrameCount'],s['Width'],s['Height'],s['Samples'],s['Device'],s['Animation'],s['States'])!=(3,960,540,256,'RTX5060Ti OptiX',False,['frame_0000','frame_0033','frame_0047']): raise ValueError('scope')
    return True

def fixture(n):
    root=rf'C:\Synthetic\candidate-{n}'
    c={'schema_version':1,'executor':'blender-local-three-keyframes','candidate_id':f'synthetic-{n}','candidate_root':root,'input_manifest':{'path':'inputs.json','sha256':str(n)*64},'skill_lock':{'path':'skill-lock.json','sha256':'a'*64},'skill_root':r'C:\Synthetic\skill','blender':{'path':r'C:\Synthetic\Blender\blender.exe','sha256':'b'*64},'service_evidence':{'path':'service-start.json','sha256':'c'*64},'expected_outputs':[rf'output\frame_{i:04}.png' for i in (0,33,47)],'prerequisite_receipts':[],'scope':{'FrameCount':3,'Width':960,'Height':540,'Samples':256,'Device':'RTX5060Ti OptiX','States':['frame_0000','frame_0033','frame_0047'],'Animation':False}}
    c['argv']=['--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',ntpath.join(root,'package','run_three_keyframes.py'),'--','--skill-root',c['skill_root'],'--skill-lock',ntpath.join(root,'skill-lock.json')]
    return c

class OfflineReuse(unittest.TestCase):
    def test_three_data_configs_one_core(self):
        before={p.name:digest(p) for p in (HERE/'blender-guardian.cs',HERE/'run-blender-local.ps1')}
        for n in (1,2,3): self.assertTrue(check(fixture(n)))
        self.assertEqual(before,{p.name:digest(p) for p in (HERE/'blender-guardian.cs',HERE/'run-blender-local.ps1')})
    def test_reject_arbitrary_argv(self):
        for extra in ('--python-expr','--render-anim','--python-console','-b'):
            c=fixture(1); c['argv']+=[extra]
            with self.assertRaises(ValueError): check(c)
    def test_reject_changed_entry(self):
        c=fixture(1); c['argv'][9]=r'C:\Synthetic\evil.py'
        with self.assertRaises(ValueError): check(c)
    def test_reject_paths_and_fields(self):
        for path in ('../input.json',r'..\input.json','C:\\other.json','a:stream',r'foo\..\x'):
            c=fixture(1); c['input_manifest']['path']=path
            with self.assertRaises(ValueError): check(c)
        c=fixture(1);c['command']='anything'
        with self.assertRaises(ValueError): check(c)
    def test_reject_scope_and_outputs(self):
        for key,value in [('Samples',1024),('Animation',True),('FrameCount',100)]:
            c=fixture(1);c['scope'][key]=value
            with self.assertRaises(ValueError):check(c)
        c=fixture(1);c['expected_outputs'][0]='output\\movie.mp4'
        with self.assertRaises(ValueError): check(c)
    def test_required_safety_code_retained(self):
        ps=(HERE/'run-blender-local.ps1').read_text();cs=(HERE/'blender-guardian.cs').read_text()
        for token in ('[IO.FileMode]::CreateNew','[IO.FileShare]::None','Get-CimInstance Win32_Process','Get-NetTCPConnection','Invoke-RestMethod','queue_running.Count -ne 0','CreationDate.ToUniversalTime().Ticks','preflight-resources.json','TreeExitVerified','AutomaticRetry=$false','--factory-startup','--disable-autoexec','ReparsePoint','ReviewedConfigSHA256'):
            self.assertIn(token,ps)
        for token in ('CutoffMilliseconds = 295000','MaximumMilliseconds = 300000','JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE','CREATE_SUSPENDED','Interlocked.CompareExchange(ref CloseClaimed','private_job_ACTIVE_PROCESS_ZERO_completion','InvocationClaimed','unknown_requires_reconciliation'):
            self.assertIn(token,cs)
    def test_failed_observation_saved_before_decision(self):
        ps=(HERE/'run-blender-local.ps1').read_text()
        self.assertLess(ps.index("'preflight-resources.json') $resources"),ps.index("if ($g.Count -ne 6"))
        self.assertIn("finally { Write-NewJson (Join-Path $taskRoot 'preflight-resource-observation.json')",ps)
    def test_durable_unknown_inhibit(self):
        ps=(HERE/'run-blender-local.ps1').read_text()
        self.assertIn("Join-Path $workspace 'local-gpu-execution-uncertain.json'",ps)
        self.assertLess(ps.index("Test-Path -LiteralPath $uncertainPath"),ps.index("$guardianCalled = $true"))
        self.assertIn("$nativeResult.RootExited -and $nativeResult.TreeExitVerified",ps)
        self.assertIn("$ownedMarker.Nonce -cne $markerNonce",ps)
    def test_guardian_hash_pin(self): self.assertIn(digest(HERE/'blender-guardian.cs'),(HERE/'run-blender-local.ps1').read_text())
if __name__=='__main__':unittest.main()
