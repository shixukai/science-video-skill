"""Synthetic declarations only; these fabricated histories NEVER approve real work."""
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_gate as gate


def ref(root, path):
    return {'file': path, 'sha256': gate.file_hash(Path(root) / path)}


def attach_execution_fixture(data, root):
    root = Path(root)
    data.setdefault('execution', {})
    producer = data.setdefault('brief', {}).setdefault('roles', {}).get('producer')
    if producer == 'synthetic software fixture, not an actual reviewer':
        data['brief']['roles']['producer'] = 'synthetic producer identity, no real person'
    for shot in data.get('shots', []):
        book = shot.setdefault('shotbook', {})
        book.setdefault('connections', {'applicable': False, 'not_applicable_reason': 'Synthetic fixture has no inter-part connector.', 'links': []})
        for key in ('claim_support', 'subject', 'action', 'attention_target', 'viewer_takeaway'):
            if not book.get(key):
                book[key] = 'synthetic design ' + key + ', not actual production'
    adapter = root / 'synthetic-render-adapter.py'
    adapter.write_text('# Synthetic declaration fixture only; not an actual rendering entrypoint.\n')
    data['execution']['entrypoint'] = ref(root, adapter.name)
    refresh_execution_fixture(data, root)


def refresh_execution_fixture(data, root):
    root = Path(root)
    lock = {'schema_version': 1, 'kind': 'production_skill_lock',
            'created_at': '2025-12-31T00:00:00Z', **gate.skill_snapshot()}
    (root / 'synthetic-skill-lock.json').write_text(json.dumps(lock))
    data['execution']['skill_lock'] = ref(root, 'synthetic-skill-lock.json')
    ids = [s['id'] for s in data['shots']]
    output = {'file': data['deliverables']['video'], 'sha256': data['qa']['reviewed_sha256']['video']}
    record = {'schema_version': 1, 'kind': 'guarded_render_receipt', 'phase': 'full',
              'result': 'rendered_unreviewed', 'returncode': 0, 'preflight_errors': [],
              'shot_ids': ids, 'design_sha256': gate.design_context(data, ids),
              'skill_tree_sha256': lock['tree_sha256'], 'output': output,
              'started_at': '2025-12-31T00:00:01Z', 'completed_at': '2025-12-31T00:00:02Z',
              'fixture_only': 'FABRICATED SOFTWARE FIXTURE, NO REAL RENDER OR REVIEW'}
    name = 'synthetic-full-' + gate.digest(record) + '.json'
    (root / name).write_text(json.dumps(record))
    data['execution']['full_receipt'] = ref(root, name)
    data['qa'].setdefault('technical', {}).setdefault('status', 'pass')
