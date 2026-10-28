#!/usr/bin/env python3
"""Read version-scoped 3D asset indexes. Never open models or modify the library."""
import argparse
from collections import deque
import json
import os
from pathlib import Path, PureWindowsPath
import stat
import sys

PRIMARY = {
    'current_engine': ('engine', '发动机 整机 engine turbofan'),
    'cooled_blade': ('cooled-blade', '冷却 叶片 空心 cooled blade HPT'),
    'spatial_bridge': ('bridge', '过桥 定位 衔接 bridge transition'),
}
SUPPORTING = {
    'baseline_engine_sources': ('baseline_engine_source', '原片 基础 来源 baseline'),
    'rebuild_only_intermediate_blends': ('rebuild_dependency', '重建 依赖 中间 rebuild dependency'),
    'cover_camera_layouts': ('cover_layout', '封面 机位 cover layout'),
}
GENERIC = ('current_asset', 'assets')
NON_DEFAULT_STATUSES = {'failed', 'rejected', 'superseded', 'historical', 'archived_unreviewed'}


def read_json(path):
    with path.open(encoding='utf-8-sig') as stream:
        return json.load(stream)


def reparse(path):
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 1024)


def safe_path(base, relative):
    """Index paths are local to their bundle, even when running on POSIX."""
    if not isinstance(relative, str) or not relative.strip():
        raise ValueError('nonempty relative file path required')
    parts = relative.replace('\\', '/').split('/')
    win = PureWindowsPath(relative)
    if win.drive or win.root or relative.startswith('/') or any(p == '..' or ':' in p or (p not in ('', '.') and not p.rstrip(' .')) for p in parts):
        raise ValueError('absolute, drive, UNC, parent or alternate-stream path rejected')
    path = base
    for part in parts:
        if part in ('', '.'):
            continue
        path = path / part
        try:
            if reparse(path):
                raise ValueError('symbolic link or reparse-point path rejected')
        except FileNotFoundError:
            pass
    if not path.resolve().is_relative_to(base.resolve()):
        raise ValueError('path escapes index directory')
    return path


def reference(base, relative):
    path = safe_path(base, relative)
    try:
        info = path.stat()
        state = 'present' if stat.S_ISREG(info.st_mode) else 'not_a_file'
    except FileNotFoundError:
        state = 'missing'
    except OSError:
        state = 'unavailable_or_not_visible'
    return {'file': str(path), 'file_status': state}


def scan(root, max_depth, errors):
    queue = deque([(root, 0)])
    indexes = []
    limited = False
    while queue:
        directory, depth = queue.popleft()
        try:
            entries = list(os.scandir(directory))
        except OSError as error:
            if directory == root:
                raise
            errors.append({'path': str(directory), 'error': str(error)})
            continue
        try:
            index = next((Path(e.path) for e in entries if e.name == 'asset-index.json'), None)
            if index is not None:
                if reparse(index):
                    raise ValueError('index is a symbolic link or reparse point')
                data = read_json(index)
                if not isinstance(data, dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1 or not any(k in data for k in (*PRIMARY, *GENERIC)):
                    raise ValueError('unsupported asset-index schema or roles')
                indexes.append((index, data))
                continue  # A version bundle is a leaf; do not traverse models/previews.
            for entry in sorted(entries, key=lambda e: e.name.casefold()):
                path = Path(entry.path)
                if entry.is_dir(follow_symlinks=False) and not reparse(path):
                    if depth < max_depth:
                        queue.append((path, depth + 1))
                    else:
                        limited = True
        except (OSError, ValueError) as error:
            errors.append({'path': str(directory), 'error': str(error)})
    return indexes, limited


def manifest_hashes(base):
    path = safe_path(base, 'manifest.json')
    try:
        data = read_json(path)
    except FileNotFoundError:
        return {}
    if not isinstance(data, dict) or not isinstance(data.get('files'), list):
        raise ValueError('manifest must contain a files list')
    return {r['file'].replace('\\', '/'): r.get('sha256') for r in data['files']
            if isinstance(r, dict) and isinstance(r.get('file'), str)}


def candidates(index, data, args, errors):
    base = index.parent
    try:
        hashes = manifest_hashes(base)
    except (OSError, ValueError) as error:
        errors.append({'path': str(base / 'manifest.json'), 'error': str(error)})
        hashes = {}
    kinds = dict(PRIMARY)
    if args.include_supporting:
        kinds.update(SUPPORTING)
    records = [(role, kind, aliases, data.get(role)) for role, (kind, aliases) in kinds.items()]
    if 'current_asset' in data:
        records.append(('current_asset', None, '', data['current_asset']))
    if 'assets' in data:
        if isinstance(data['assets'], list):
            records.extend(('asset', None, '', record) for record in data['assets'])
        else:
            errors.append({'path': str(index), 'error': 'assets must be a list'})
    results = []
    for role, kind, aliases, record in records:
        if record is None:
            continue
        try:
            if not isinstance(record, dict):
                raise ValueError('role record must be an object: ' + role)
            generic = role in ('current_asset', 'asset')
            if generic:
                kind = record.get('kind', data.get('kind', 'model'))
                if not isinstance(kind, str) or not kind.strip():
                    raise ValueError('asset kind must be a nonempty string')
                keywords = record.get('keywords', [])
                if not isinstance(keywords, list) or any(not isinstance(word, str) for word in keywords):
                    raise ValueError('keywords must be a list of strings')
                aliases = ' '.join([str(record.get('id', '')), str(record.get('name', '')), kind, *keywords])
            if (role in PRIMARY or generic) and args.kind not in ('all', kind):
                continue
            if not isinstance(record.get('non_default', False), bool):
                raise ValueError('non_default must be a boolean')
            non_default = (role in SUPPORTING or record.get('non_default', False)
                           or record.get('status') in NON_DEFAULT_STATUSES
                           or record.get('review_status') in NON_DEFAULT_STATUSES)
            if non_default and not args.include_supporting:
                continue
            files = [record['file']] if 'file' in record else record.get('files', [])
            if not isinstance(files, list):
                raise ValueError('role files must be a list: ' + role)
            if any(not isinstance(record.get(key, []), list) for key in ('previews', 'additional_sources')):
                raise ValueError('previews and additional_sources must be lists: ' + role)
            for relative in files:
                info = reference(base, relative)
                haystack = f"{aliases} {relative} {data.get('revision', '')}".casefold()
                if args.query and not all(word in haystack for word in args.query.casefold().split()):
                    continue
                refs = ['blender-dependencies.json', 'provenance.json', 'scientific-reference.json']
                refs += [record[k] for k in ('builder', 'scientific_reference', 'review') if k in record]
                refs += record.get('additional_sources', [])
                results.append({
                    'index': str(index), 'revision': data.get('revision'), 'role': role,
                    'kind': kind, 'non_default': non_default,
                    'asset_id': record.get('id'), 'name': record.get('name'),
                    'recorded_status': record.get('status'),
                    'recorded_review_status': record.get('review_status'),
                    'current_scope': 'within_index' if role in ('current_engine', 'current_asset') else None,
                    **info,
                    'recorded_sha256': record.get('sha256') or hashes.get(relative.replace('\\', '/')),
                    'file_sha256_verified': False, 'quality_status': 'not_evaluated',
                    'source_version': record.get('source_version'), 'role_note': record.get('role'),
                    'previews': [reference(base, p) for p in record.get('previews', [])],
                    'metadata_refs': [reference(base, p) for p in dict.fromkeys(refs)],
                    'limits': data.get('limits'),
                })
        except (OSError, ValueError, TypeError, KeyError) as error:
            errors.append({'path': str(index), 'role': role, 'error': str(error)})
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', help='Library root or version directory; default: series-profile shared_3d_library.root')
    parser.add_argument('--kind', default='all', help='Exact indexed category, e.g. engine, environment, material, lighting, chip-manufacturing; default all')
    parser.add_argument('--query', default='')
    parser.add_argument('--include-supporting', action='store_true', help='Also list explicitly non-default, historical, failed, baseline, rebuild and cover assets')
    parser.add_argument('--max-depth', type=int, default=6)
    args = parser.parse_args(argv)
    if args.max_depth < 0:
        parser.error('--max-depth must be nonnegative')
    output = {'status': None, 'root': args.root, 'indexes_read': 0, 'results': [], 'errors': [],
              'scan_depth_limit': args.max_depth, 'scan_depth_limited': False,
              'global_current': 'not_defined_by_supported_schema',
              'limits': 'Metadata lookup only. Current roles are current within one index, not globally latest or quality-approved. Recorded reviews remain scoped source claims. Models are never opened, executed or hashed.'}
    try:
        if args.root is None:
            profile = read_json(Path(__file__).resolve().parents[1] / 'config/series-profile.json')
            args.root = profile['shared_3d_library']['root']
        root = Path(args.root)
        output['root'] = str(root)
        if not root.is_absolute() or reparse(root) or not stat.S_ISDIR(root.stat().st_mode):
            raise OSError('library root must be an accessible absolute directory without a reparse point')
        indexes, limited = scan(root, args.max_depth, output['errors'])
        output['indexes_read'] = len(indexes)
        output['scan_depth_limited'] = limited
        for index, data in indexes:
            output['results'].extend(candidates(index, data, args, output['errors']))
        output['multiple_indexes_require_selection'] = len({r['index'] for r in output['results']}) > 1
        if output['errors']:
            output['status'] = 'partial_results' if indexes else 'errors'
        else:
            output['status'] = 'ok' if output['results'] else ('no_matches' if indexes else 'no_indexes_found')
    except (OSError, ValueError, KeyError, TypeError) as error:
        output['status'] = 'library_unavailable_or_not_visible'
        output['errors'].append({'path': output['root'], 'error': str(error)})
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 1 if output['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
