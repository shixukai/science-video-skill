"""Synthetic PCM/provenance fixtures; no speech or actual listening is claimed."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
import wave

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE if (HERE / 'check_episode.py').is_file() else HERE.parent
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('master_binding_checks', SCRIPTS / 'check_episode.py')
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


@unittest.skipUnless(shutil.which('ffprobe'), 'ffprobe required for synthetic PCM fixtures')
class VoiceMasterBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='voice-master-binding-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.execution = {'status':'confirmed', 'mode':'local_project', 'location':'/synthetic/qwen',
                          'confirmation_reference':'Synthetic fixture, not production authorization'}
        (self.root / 'reason.txt').write_text('Synthetic interface-limit evidence only.')
        (self.root / 'listening.txt').write_text('Synthetic listening declarations only; no person listened.')
        texts = ['Synthetic first section.\n', 'Synthetic second section.\n']
        (self.root / 'script.txt').write_text(''.join(texts), encoding='utf-8')
        self.manifest = {'schema_version':1, 'mode':'ordered_full_segments',
                         'reason':{'kind':'interface_limit','note':'Synthetic recorded interface limit',
                                   'evidence':self.ref('reason.txt')},
                         'script':self.ref('script.txt'), 'segments':[]}
        for i, text in enumerate(texts, 1):
            ident = 'S' + str(i)
            (self.root / (ident+'.txt')).write_text(text,encoding='utf-8')
            self.pcm(ident+'.wav',1600,8000)
            item = {'id':ident,'input':self.ref(ident+'.txt'),'output':self.ref(ident+'.wav')}
            generation = {'schema_version':1,'status':'generated','backend':'local_qwen','provider':'Qwen',
                'model_id':'synthetic-fixture-model','model_version_reference':'Synthetic pinned fixture version',
                'execution':copy.deepcopy(self.execution),
                'voice':{'speaker':'Serena','language':'Chinese','instruct':'Synthetic consistent direction'},
                'effective_generation_params':{'temperature':0.9},'load_parameters':{'device':'cpu'},
                'input':{**item['input'],'text_transformation':'none'},'output':item['output']}
            item['generation_record'] = self.json(ident+'.json',generation)
            self.manifest['segments'].append(item)
        self.pcm('assembled.wav',3200,8000)
        self.concat = {'schema_version':1,'status':'processed','mode':'concatenate_full_segments',
            'sources':[{'segment_id':s['id'],**s['output']} for s in self.manifest['segments']],
            'output':self.ref('assembled.wav'),
            'steps':[{'tool':'synthetic PCM assembly','version':'fixture',
                      'parameters':{'action':'concatenate complete PCM sections'}}]}
        self.floating('master.wav',19200,48000)
        self.master = {'schema_version':1,'status':'processed','mode':'whole_track_linear_gain',
            'upstream_record':self.json('concat.json',self.concat),'source':self.ref('assembled.wav'),
            'output':self.ref('master.wav'),
            'steps':[{'tool':'FFmpeg synthetic fixture','version':'fixture',
                'parameters':{'processing_mode':'whole_track_linear_gain','gain_db':2.0,
                    'output_sample_rate_hz':48000,'codec':'pcm_f32le','channels':'preserve',
                    'speed_factor':1,'pitch_shift_semitones':0,'dynamic_compression':False,
                    'per_shot_normalization':False}}]}
        self.narration = {'status':'ready','execution':copy.deepcopy(self.execution),
            'script_file':'script.txt','script_sha256':self.ref('script.txt')['sha256'],
            'audio_sha256':self.ref('master.wav')['sha256'],
            'generation_manifest':self.json('manifest.json',self.manifest),
            'source_listen_review':{'status':'pass','scope':'assembled_voice_track',**self.ref('master.wav'),
                'heard':True,'method':'continuous_playback','playback_speed':1,
                'reviewer':'synthetic fixture reviewer','capability':'synthetic declarations only',
                'environment':'synthetic device','reviewed_at':'2026-11-05T00:00:00Z',
                'boundaries':[{'left_segment_id':'S1','right_segment_id':'S2','at_seconds':0.2,
                    'range':[0.1,0.3],'note':'Synthetic continuity observation',
                    'evidence':self.ref('listening.txt')}]}}
        self.save()

    def ref(self,name):
        return {'file':name,'sha256':checks.file_sha256(self.root/name)}

    def json(self,name,data):
        (self.root/name).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
        return self.ref(name)

    def pcm(self,name,frames,rate,channels=1):
        with wave.open(str(self.root/name),'wb') as output:
            output.setparams((channels,2,rate,0,'NONE','not compressed'))
            output.writeframes(struct.pack('<h',1000)*frames*channels)

    def floating(self,name,frames,rate,channels=1):
        samples = b''.join(struct.pack('<f',0.05*math.sin(2*math.pi*200*i/rate))
                           for i in range(frames) for _ in range(channels))
        fmt = struct.pack('<HHIIHH',3,channels,rate,rate*channels*4,channels*4,32)
        chunks = b'fmt '+struct.pack('<I',len(fmt))+fmt+b'data'+struct.pack('<I',len(samples))+samples
        (self.root/name).write_bytes(b'RIFF'+struct.pack('<I',len(chunks)+4)+b'WAVE'+chunks)

    def save(self):
        self.narration['postprocess_record'] = self.json('master.json',self.master)

    def errors(self):
        return checks.check_voice_segments(self.narration,self.root)

    def rejects(self,phrase):
        errors=self.errors()
        self.assertTrue(any(phrase in e for e in errors),errors)

    def test_native_concat_then_float_resample_gain_preserves_source_chain(self):
        self.assertEqual(self.errors(),[])

    def test_legacy_concat_path_retains_original_behavior(self):
        self.narration['postprocess_record']=self.json('concat.json',self.concat)
        self.narration['audio_sha256']=self.ref('assembled.wav')['sha256']
        self.narration['source_listen_review'].update(self.ref('assembled.wav'))
        self.assertEqual(self.errors(),[])

    def test_incidental_reference_metadata_does_not_break_identity(self):
        self.concat['output']['bytes']=(self.root/'assembled.wav').stat().st_size
        self.master['upstream_record']=self.json('concat.json',self.concat)
        self.save()
        self.assertEqual(self.errors(),[])

    def test_stale_upstream_record_or_assembly_audio_is_rejected(self):
        for name in ('concat.json','assembled.wav'):
            with self.subTest(name=name):
                path=self.root/name;raw=path.read_bytes();path.write_bytes(raw+b'stale')
                self.rejects('hash stale/missing');path.write_bytes(raw)

    def test_master_source_must_match_original_assembly(self):
        self.master['source']=self.ref('S1.wav');self.save()
        self.rejects('exactly bind upstream assembled output')

    def test_final_hash_and_current_listening_cannot_reuse_old_assembly(self):
        self.narration['source_listen_review'].update(self.ref('assembled.wav'))
        self.rejects('bind current assembled audio')
        self.narration['audio_sha256']='0'*64
        self.rejects('output must bind current narration')

    def test_unknown_transform_or_extra_steps_are_rejected(self):
        original=copy.deepcopy(self.master)
        for field,value in [('processing_mode','crop'),('speed_factor',1.1),
                            ('pitch_shift_semitones',1),('dynamic_compression',True),
                            ('per_shot_normalization',True),('gain_db',float('nan')),
                            ('speed_factor',True),('output_sample_rate_hz',True)]:
            with self.subTest(field=field):
                self.master=copy.deepcopy(original)
                self.master['steps'][0]['parameters'][field]=value;self.save()
                self.rejects('permits only declared constant gain')
        self.master=copy.deepcopy(original)
        self.master['steps'].append({'tool':'other','version':'fixture','parameters':{'crop':True}})
        self.save();self.rejects('requires one actual gain/resample step')

    def test_missing_step_metadata_is_rejected(self):
        self.master['steps'][0].pop('version');self.save()
        self.rejects('requires one actual gain/resample step')

    def test_processed_pcm_format_rate_channels_and_duration_are_checked(self):
        for kind in ('codec','rate','channels','duration'):
            with self.subTest(kind=kind):
                if kind=='codec':self.pcm('master.wav',19200,48000)
                elif kind=='rate':self.floating('master.wav',17640,44100)
                elif kind=='channels':self.floating('master.wav',19200,48000,2)
                else:self.floating('master.wav',14400,48000)
                self.master['output']=self.ref('master.wav')
                self.narration['audio_sha256']=self.master['output']['sha256']
                self.narration['source_listen_review'].update(self.master['output']);self.save()
                self.rejects({'codec':'PCM codec/rate','rate':'PCM codec/rate',
                              'channels':'preserve assembled channels','duration':'preserve complete assembled duration'}[kind])

    def test_original_segment_order_and_voice_config_still_checked_after_mastering(self):
        self.concat['sources'].reverse()
        self.master['upstream_record']=self.json('concat.json',self.concat);self.save()
        self.rejects('all ordered segment outputs')
        generation=json.loads((self.root/'S2.json').read_text(encoding='utf-8'))
        generation['voice']['instruct']='Unrelated new style'
        self.manifest['segments'][1]['generation_record']=self.json('S2.json',generation)
        self.narration['generation_manifest']=self.json('manifest.json',self.manifest)
        self.rejects('parameters drift')

    def test_nested_or_self_referencing_upstream_does_not_create_a_chain_bypass(self):
        original=copy.deepcopy(self.master)
        self.master['upstream_record']=self.ref('master.json');self.save()
        self.rejects('hash stale/missing')
        self.master=original
        self.concat['upstream_record']=self.ref('concat.json')
        self.master['upstream_record']=self.json('concat.json',self.concat);self.save()
        self.rejects('must concatenate complete segments')

    def test_missing_current_boundary_listening_remains_unreviewed(self):
        self.narration['source_listen_review']['heard']=False
        self.rejects('requires actual normal-speed boundary listening')
        self.narration['source_listen_review']['heard']=True
        self.narration['source_listen_review']['boundaries'][0]['at_seconds']=0.1
        self.rejects('time must match actual source durations')


if __name__=='__main__':
    unittest.main()
