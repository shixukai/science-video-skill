"""Targeted offline capability delta tests. Not Windows/Blender execution."""
import copy, hashlib, ntpath, unittest
from pathlib import Path
import importlib.util
HERE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('reviewed_blender_static_test_helper',HERE/'test_blender_reuse.py')
_helper=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_helper)
check_static,fixture=_helper.check,_helper.fixture

def continuous():
    c=fixture(1);c['executor']='blender-local-bounded-reveal'
    c['argv'][8]=ntpath.join(c['candidate_root'],'package','run_bounded_reveal.py')
    c['expected_outputs']=[rf'output\frame_{i:04d}.png' for i in range(48)]
    c['scope'].update(FrameCount=48,States=[f'frame_{i:04d}' for i in range(48)],Animation=True,StartFrame=0,EndFrame=47,FPS=24)
    return c

def check(c):
    if c['executor']=='blender-local-three-keyframes': return check_static(c)
    if c['executor']!='blender-local-bounded-reveal': raise ValueError('profile')
    s=c['scope']
    if set(s)!=set(continuous()['scope']) or (s['FrameCount'],s['StartFrame'],s['EndFrame'],s['FPS'],s['Animation'])!=(48,0,47,24,True):raise ValueError('continuous scope')
    if c['expected_outputs']!=continuous()['expected_outputs'] or s['States']!=continuous()['scope']['States']:raise ValueError('continuous output sequence')
    if c['argv'][8]!=ntpath.join(c['candidate_root'],'package','run_bounded_reveal.py'):raise ValueError('continuous entry')
    # Reuse unchanged static validation for the common restricted envelope.
    common=copy.deepcopy(c);static=fixture(1)
    common['executor']=static['executor'];common['argv'][8]=ntpath.join(common['candidate_root'],'package','run_three_keyframes.py')
    common['expected_outputs']=static['expected_outputs']
    common['scope']={k:v for k,v in s.items() if k not in ('StartFrame','EndFrame','FPS')}
    common['scope'].update(FrameCount=3,States=static['scope']['States'],Animation=False)
    return check_static(common)

class ContinuousDelta(unittest.TestCase):
    def test_both_profiles_same_core(self):
        before=[hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('run-blender-local.ps1','blender-guardian.cs')]
        self.assertTrue(check(fixture(1)));self.assertTrue(check(continuous()))
        self.assertEqual(before,[hashlib.sha256((HERE/n).read_bytes()).hexdigest() for n in ('run-blender-local.ps1','blender-guardian.cs')])
    def test_out_of_scope(self):
        for key,value in [('FrameCount',49),('StartFrame',1),('EndFrame',48),('FPS',30),('Samples',64),('Width',1920),('Animation',False)]:
            c=continuous();c['scope'][key]=value
            with self.assertRaises(ValueError):check(c)
    def test_not_three_frames_repeated(self):
        c=continuous();c['scope']['States']=['frame_0000','frame_0033','frame_0047']*16
        with self.assertRaises(ValueError):check(c)
    def test_extra_missing_or_reordered_outputs(self):
        for outputs in (continuous()['expected_outputs']+['output\\frame_0048.png'],continuous()['expected_outputs'][:-1],list(reversed(continuous()['expected_outputs']))):
            c=continuous();c['expected_outputs']=outputs
            with self.assertRaises(ValueError):check(c)
    def test_argv_and_alternate_entry(self):
        c=continuous();c['argv']+=['--render-anim']
        with self.assertRaises(ValueError):check(c)
        c=continuous();c['argv'][8]=ntpath.join(c['candidate_root'],'package','other.py')
        with self.assertRaises(ValueError):check(c)
    def test_unknown_profile(self):
        c=continuous();c['executor']='full-video'
        with self.assertRaises(ValueError):check(c)
    def test_fixed_native_limits_and_unknown_inhibit(self):
        cs=(HERE/'blender-guardian.cs').read_text();ps=(HERE/'run-blender-local.ps1').read_text()
        for t in ('CutoffMilliseconds = 295000','MaximumMilliseconds = 300000','Interlocked.CompareExchange(ref InvocationClaimed','private_job_ACTIVE_PROCESS_ZERO_completion'):self.assertIn(t,cs)
        for t in ('local-gpu-execution-uncertain.json','$nativeResult.RootExited -and $nativeResult.TreeExitVerified','$ownedMarker.Nonce -cne $markerNonce','[IO.FileShare]::None'):self.assertIn(t,ps)
if __name__=='__main__':unittest.main()
