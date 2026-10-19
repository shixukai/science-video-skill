"""Fabricated software fixtures, NEVER evidence of actual authorship/review."""
from pathlib import Path
import hashlib


def attach_origin_fixture(data, root):
    root = Path(root)
    note = root / 'synthetic-origin.txt'
    note.write_text('FABRICATED SOFTWARE TEST ONLY: no actual creation, frame review or user authorization.')
    ref = {'file': note.name, 'sha256': hashlib.sha256(note.read_bytes()).hexdigest()}
    data['origin_contract'] = {'mode': 'self_created_visuals'}
    for shot in data.get('shots', []):
        medium = shot.get('shotbook', {}).get('realism', {}).get('medium')
        method = {'ai_realistic':'self_generated', 'authentic_recording':'user_capture'}.get(medium, 'self_rendered')
        shot.setdefault('shotbook', {})['origin'] = {'planned_method':method,
            'entry_version':'synthetic-test-v1', 'design':dict(ref), 'entrypoint':dict(ref)}
    for asset in data.get('assets', []):
        if asset.get('kind') in ('audio', 'font'): continue
        category = 'user_capture' if asset.get('kind') in ('real_capture','real_observation') else {'ai_generated':'self_generated', 'simulation':'self_rendered'}.get(asset.get('kind'), 'self_designed')
        asset['origin'] = {'category':category, 'method':'fabricated test declaration only',
            'entry_version':'synthetic-test-v1', 'design':dict(ref), 'entrypoint':dict(ref),
            'inputs':[], 'output':{k:asset.get(k) for k in ('file','sha256')},
            'frames':[dict(ref)], 'review':dict(ref)}
        if category in ('self_generated','self_rendered'):
            asset.setdefault('disclosure', 'Synthetic software fixture, not a real recording.')
        if category == 'user_capture': asset['origin']['user_authorization'] = dict(ref)
