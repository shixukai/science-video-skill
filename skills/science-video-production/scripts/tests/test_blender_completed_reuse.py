"""Historical completed frame reuse integrity; never authorizes rerender."""
from pathlib import Path
import json, sys, unittest, tempfile, importlib.util
from unittest.mock import patch

here = Path(__file__).resolve().parent
source = here.parent / 'blender_batch.py'
sys.path.insert(0, str(source.parent))
import blender_batch as batch
sp = importlib.util.spec_from_file_location('existing_blender_batch_tests', here / 'test_blender_batch.py')
fixtures = importlib.util.module_from_spec(sp); sp.loader.exec_module(fixtures)

class CompletedReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.old_executor = 'a' * 64
        (self.root/'scene.py').write_text('# source\n', encoding='utf-8')
        (self.root/'asset.txt').write_text('asset', encoding='utf-8')
        (self.root/'blender.exe').write_bytes(b'fake executable')
        self.spec = {'schema_version':1,'job_id':'historic','purpose':'motion_preview',
            'driver':'scene.py','blender_executable':'blender.exe','inputs':['asset.txt'],
            'output_dir':'output','frames':'1:3',
            'render':{'engine':'CYCLES','device':'CPU','samples':2,'width':8,'height':6,'fps':25}}
        (self.root/'spec.json').write_text(json.dumps(self.spec),encoding='utf-8')
        original_hash = batch.file_hash
        def previous(path):
            return self.old_executor if Path(path).resolve() == source.resolve() else original_hash(path)
        with patch.object(batch, 'file_hash', side_effect=previous):
            self.job = batch.prepare(self.root/'spec.json', self.root/'job.json')
            batch.execute(self.job, fixtures.FakeRenderer())
        self.output = Path(self.job['spec']['output_dir'])
        self.prior = self.lock('prior.json', self.old_executor)
        self.current = self.lock('current.json', batch.file_hash(source))
        self.migration = {'schema_version':1,'kind':'blender_completed_job_reuse_migration',
            'prior_lock':self.ref(self.prior),'current_lock':self.ref(self.current),
            'jobs':[{'signature':self.job['signature'],
                     'signed_job_sha256':batch.file_hash(self.output/'job.json'),
                     'state_sha256':batch.file_hash(self.output/'state.json')}]}
        self.migration_path = self.root/'migration.json'; self.save_migration()

    def ref(self, path): return {'file':str(path), 'sha256':batch.file_hash(path)}
    def save_migration(self):
        self.migration_path.write_text(json.dumps(self.migration), encoding='utf-8')
        self.migration_sha = batch.file_hash(self.migration_path)
    def lock(self, name, exe_hash):
        files = {'scripts/blender_batch.py':exe_hash}
        path = self.root/name
        path.write_text(json.dumps({'kind':'production_skill_lock','schema_version':1,
                                    'files':files,'tree_sha256':batch.digest(files)}),encoding='utf-8')
        return path
    def reuse(self, frames=(1,2,3)):
        return batch.verify_completed_reuse(self.job,self.migration_path,self.migration_sha,frames)

    def test_archived_frames_read_only_verified_but_strict_execution_still_rejected(self):
        before = {p.name:batch.file_hash(p) for p in self.output.iterdir() if p.is_file()}
        self.assertEqual(self.reuse()['frames'],3)
        self.assertEqual(before,{p.name:batch.file_hash(p) for p in self.output.iterdir() if p.is_file()})
        with self.assertRaisesRegex(ValueError,'Executor changed'): batch.verify(self.job)
        with self.assertRaisesRegex(ValueError,'Executor changed'): batch.execute(self.job,fixtures.FakeRenderer(),resume=True)
    def test_bad_migration_hash_rejected(self):
        self.migration_path.write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'migration evidence changed'): self.reuse()
    def test_wrong_or_mutated_prior_lock_rejected(self):
        self.prior.write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Skill lock changed'): self.reuse()
    def test_wrong_current_executor_lock_rejected(self):
        self.current=self.lock('current2.json','b'*64)
        self.migration['current_lock']=self.ref(self.current); self.save_migration()
        with self.assertRaisesRegex(ValueError,'does not bind the executor'): self.reuse()
    def test_migration_must_bind_unique_job(self):
        self.migration['jobs']*=2; self.save_migration()
        with self.assertRaisesRegex(ValueError,'not uniquely bound'): self.reuse()
    def test_changed_source_rejected(self):
        (self.root/'asset.txt').write_text('tampered',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Input changed'): self.reuse()
    def test_changed_signed_job_rejected(self):
        (self.output/'job.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'output ownership'): self.reuse()
    def test_changed_state_rejected(self):
        (self.output/'state.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'output ownership'): self.reuse()
    def test_unfinished_state_cannot_be_authorized_by_new_migration(self):
        state = batch.read(self.output/'state.json'); state['status']='partial_unreviewed'
        batch.write(self.output/'state.json',state)
        self.migration['jobs'][0]['state_sha256']=batch.file_hash(self.output/'state.json');self.save_migration()
        with self.assertRaisesRegex(ValueError,'not complete'): self.reuse()
    def test_corrupted_frame_rejected(self):
        (self.output/'frame_000002.png').write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError,'Invalid historical image'): self.reuse()
    def test_corrupted_frame_receipt_rejected(self):
        (self.output/'frame_000002.json').write_text('{}',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Invalid historical image'): self.reuse()
    def test_previously_checked_frame_cannot_change_mid_scan(self):
        original = batch.FrameVerifier.valid_frame
        def mutate_after_frame_three(verifier, frame):
            result = original(verifier, frame)
            if frame == 3:
                (self.output/'frame_000001.png').write_bytes(b'changed during scan')
            return result
        with patch.object(batch.FrameVerifier, 'valid_frame', mutate_after_frame_three):
            with self.assertRaisesRegex(ValueError,'frame changed during verification'): self.reuse()
    def test_unsupported_and_duplicate_frames_rejected(self):
        for frames in ([],[1,1],[1,4],[True]):
            with self.subTest(frames=frames), self.assertRaisesRegex(ValueError,'frame selection'):
                self.reuse(frames)
    def test_tampered_job_signature_rejected(self):
        self.job['spec']['render']['samples']=3
        with self.assertRaisesRegex(ValueError,'Job modified'): self.reuse()

if __name__ == '__main__': unittest.main(verbosity=2)
