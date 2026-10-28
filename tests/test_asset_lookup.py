"""Portable generic library lookup; metadata must never become media approval."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'skills/science-video-production/scripts/find_3d_assets.py'
spec = importlib.util.spec_from_file_location('finder', path)
finder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(finder)

class AssetLookupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def bundle(self, name, **records):
        root = self.root / name
        root.mkdir()
        (root / 'model.blend').write_bytes(b'Not a Blender file; lookup must not open or execute models.')
        (root / 'asset-index.json').write_text(json.dumps({'schema_version': 1, 'revision': name, **records}), encoding='utf-8')
        return root

    def lookup(self, *args):
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            code = finder.main(['--root', str(self.root), *args])
        return code, json.loads(stream.getvalue())

    def test_generic_current_asset_and_exact_category(self):
        self.bundle('chip', kind='chip-manufacturing', current_asset={'file': 'model.blend', 'name': '晶圆工位'})
        code, result = self.lookup('--kind', 'chip-manufacturing', '--query', '晶圆')
        self.assertEqual(code, 0)
        self.assertEqual(result['results'][0]['file_status'], 'present')
        self.assertFalse(result['results'][0]['file_sha256_verified'])
        self.assertEqual(result['results'][0]['quality_status'], 'not_evaluated')
        self.assertEqual(self.lookup('--kind', 'engine')[1]['status'], 'no_matches')

    def test_environment_material_and_lighting_keywords(self):
        self.bundle('studio', assets=[{'id': kind, 'kind': kind, 'file': 'model.blend', 'keywords': ['厂房', '可复用']} for kind in ('environment', 'material', 'lighting')])
        result = self.lookup('--kind', 'environment', '--query', '厂房 可复用')[1]
        self.assertEqual([r['asset_id'] for r in result['results']], ['environment'])

    def test_legacy_index_still_works(self):
        self.bundle('legacy', current_engine={'file': 'model.blend'}, cooled_blade={'files': ['model.blend']})
        self.assertEqual([r['kind'] for r in self.lookup('--kind', 'engine')[1]['results']], ['engine'])

    def test_failed_and_historical_are_explicit_nondefault(self):
        self.bundle('old', assets=[{'kind': 'model', 'file': 'model.blend', 'status': status} for status in ('failed', 'historical')])
        self.assertEqual(self.lookup()[1]['status'], 'no_matches')
        rows = self.lookup('--include-supporting')[1]['results']
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(r['non_default'] for r in rows))
        self.assertEqual({r['recorded_status'] for r in rows}, {'failed', 'historical'})

    def test_generic_parent_path_is_rejected(self):
        self.bundle('bad', current_asset={'kind': 'model', 'file': '../outside.blend'})
        code, result = self.lookup()
        self.assertEqual(code, 1)
        self.assertFalse(result['results'])
        self.assertTrue(result['errors'])

    def test_malformed_generic_array_is_reported(self):
        self.bundle('bad', assets={'file': 'model.blend'})
        self.assertEqual(self.lookup()[0], 1)

    def test_multiple_versions_do_not_promote_global_current(self):
        for name in ('one', 'two'):
            self.bundle(name, current_asset={'file': 'model.blend', 'kind': 'environment'})
        result = self.lookup()[1]
        self.assertEqual(len(result['results']), 2)
        self.assertTrue(result['multiple_indexes_require_selection'])
        self.assertTrue(all(r['current_scope'] == 'within_index' for r in result['results']))

    def test_unavailable_library_is_not_an_empty_catalog(self):
        self.root = self.root / 'missing'
        code, result = self.lookup()
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], 'library_unavailable_or_not_visible')

if __name__ == '__main__':
    unittest.main()
