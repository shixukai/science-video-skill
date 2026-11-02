"""Original-visual provenance structure only, never an authorship detector."""
from datetime import date
from pathlib import Path
from realism_guard import obj, meaningful

LICENSED_3D = 'licensed_3d_model'
PRODUCTION_CATEGORIES = ('self_generated', 'self_rendered', 'self_designed', 'user_capture', LICENSED_3D)
MODEL_SUFFIXES = {'.blend', '.glb', '.gltf', '.fbx', '.obj', '.stl', '.ply', '.dae',
                  '.usd', '.usda', '.usdc', '.usdz', '.abc'}
MODEL_DEPENDENCY_SUFFIXES = MODEL_SUFFIXES | {'.bin', '.mtl', '.png', '.jpg', '.jpeg', '.webp',
                                             '.tif', '.tiff', '.exr', '.hdr', '.ktx', '.ktx2'}


def model_file(asset):
    return isinstance(asset.get('file'), str) and Path(asset['file']).suffix.lower() in MODEL_SUFFIXES


def reference_conflicts(asset, assets):
    """Retain research history while admitting an explicitly licensed native model."""
    return [a for a in assets if meaningful(asset.get('sha256'))
            and a.get('sha256') == asset.get('sha256')
            and obj(a.get('origin')).get('category') == 'third_party_reference'
            and not (obj(asset.get('origin')).get('category') == LICENSED_3D
                     and asset.get('kind') == a.get('kind') == 'model_3d'
                     and model_file(asset) and model_file(a))]


def validate_licensed_model(checks, asset, actual=False):
    """Bind a licensed model input; does not determine license or geometry truth."""
    origin = obj(asset.get('origin')); rights = obj(asset.get('rights'))
    label = 'origin licensed 3D ' + str(asset.get('id'))
    checks.need(asset.get('kind') == 'model_3d' and model_file(asset),
                label + ' must be native model_3d source, not finished footage/stills')
    checks.need(meaningful(asset.get('source')) and meaningful(asset.get('creator')),
                label + ' original model page and creator required')
    checks.need(rights.get('status') == 'cleared' and meaningful(rights.get('license_name'))
                and meaningful(rights.get('scope')),
                label + ' applicable model/bundled-dependency license and use scope must be cleared')
    catalog = obj(asset.get('catalog'))
    blocked = {'fail', 'failed', 'blocked', 'needs_changes', 'denied', 'revoked', 'expired', 'deprecated'}
    checks.need(asset.get('catalog_state') not in blocked and catalog.get('stage') not in blocked,
                label + ' blocked/deprecated model cannot be adopted')
    for record in (obj(asset.get('science')), obj(asset.get('approval')), obj(asset.get('scientific_review')),
                   obj(catalog.get('scientific_review')), obj(catalog.get('approval')), obj(catalog.get('rights'))):
        checks.need(record.get('status') not in blocked,
                    label + ' explicit science/approval/rights failure blocks model use')
    for record in (rights, obj(catalog.get('rights'))):
        if record.get('expires_on'):
            try:
                checks.need(date.fromisoformat(record['expires_on']) >= date.today(), label + ' rights expired')
            except (TypeError, ValueError):
                checks.need(False, label + ' rights expiry invalid')
    checks.evidence(origin.get('license_evidence'), label + ' actual license evidence')
    dependencies = origin.get('dependencies')
    checks.need(isinstance(dependencies, list), label + ' explicit bundled dependency inventory required')
    for raw in seq(dependencies):
        dependency = obj(raw)
        checks.need(isinstance(dependency.get('file'), str)
                    and Path(dependency['file']).suffix.lower() in MODEL_DEPENDENCY_SUFFIXES,
                    label + ' dependency must be model data/material/texture, not finished media')
        native = isinstance(dependency.get('file'), str) and Path(dependency['file']).suffix.lower() in MODEL_SUFFIXES
        declared = {**dependency, 'kind': 'model_3d' if native else 'model_dependency',
                    'origin': {'category': LICENSED_3D}}
        checks.need(not reference_conflicts(declared, [obj(a) for a in seq(checks.data.get('assets'))]),
                    label + ' bundled dependency is known third-party reference media; cannot launder it as a texture')
    if actual:
        science = obj(asset.get('scientific_review'))
        checks.need(science.get('status') == 'pass' or
                    (science.get('status') == 'not_applicable' and meaningful(science.get('reason'))),
                    label + ' actual geometry/use-fit review or justified applicability required')



def seq(value):
    return value if isinstance(value, list) else []


def selected_asset_ids(data, shot_ids, final=False, representative=False):
    from render_gate import input_asset_ids
    from stage_checks import used_asset_ids
    ids = set(used_asset_ids(data) if final else input_asset_ids(data, shot_ids))
    # G3's declared three-scale visual dependencies live in the design record.
    # They must not evade provenance simply because they are outside shot.asset_ids.
    if representative and not final:
        for frame in obj(obj(data.get('design')).get('keyframe_scales')).values():
            ids.update(i for i in seq(obj(frame).get('asset_ids')) if isinstance(i, str))
    return ids


def selected_assets(data, shot_ids, final=False, representative=False):
    ids = selected_asset_ids(data, shot_ids, final, representative)
    # Follow all declared visual parents. Unknown IDs are rejected by validate_origin.
    assets = [obj(a) for a in seq(data.get('assets'))]
    pending = set(ids)
    while pending:
        current = pending.pop()
        for asset in assets:
            if asset.get('id') != current:
                continue
            for item in seq(obj(asset.get('origin')).get('inputs')):
                parent = obj(item).get('asset_id')
                if isinstance(parent, str) and parent not in ids:
                    ids.add(parent); pending.add(parent)
    return [a for a in assets if a.get('id') in ids]


def validate_origin_plan(checks, shot_ids, final=False, representative=True):
    """Validate declared creation intent, without pretending future media exists.

    This is the G1 contract only. Actual audiovisual gates and render entrypoints
    still call validate_origin for output bytes, frame evidence and authorization.
    Scientific literature URLs and unselected research assets are not visual inputs.
    """
    data = checks.data
    allowed = PRODUCTION_CATEGORIES
    methods = {'ai_realistic': 'self_generated', 'three_d': 'self_rendered',
               'authentic_recording': 'user_capture', 'pure_2d': 'self_rendered',
               'static_pan': 'self_rendered', 'infographic': 'self_rendered'}
    checks.need(obj(data.get('origin_contract')).get('mode') == 'self_created_visuals',
                'origin explicit self_created_visuals contract required; no legacy bypass')
    for raw in seq(data.get('shots')):
        shot = obj(raw)
        if shot.get('id') not in shot_ids:
            continue
        book = obj(shot.get('shotbook')); origin = obj(book.get('origin'))
        label = 'origin shot ' + str(shot.get('id'))
        method = origin.get('planned_method')
        checks.need(isinstance(method, str) and method in ('self_generated', 'self_rendered', 'user_capture'),
                    label + ' self-created planned method required')
        checks.need(meaningful(origin.get('entry_version')), label + ' entry version required')
        medium = obj(book.get('realism')).get('medium')
        checks.need(isinstance(medium, str) and method == methods.get(medium),
                    label + ' origin method conflicts with actual medium')

    assets = [obj(a) for a in seq(data.get('assets'))]
    pending = list(selected_asset_ids(data, shot_ids, final, representative))
    seen, graph = set(), {}
    while pending:
        ident = pending.pop()
        if ident in seen:
            continue
        seen.add(ident)
        matches = [a for a in assets if a.get('id') == ident]
        checks.need(meaningful(ident) and len(matches) == 1,
                    'origin visual dependency ' + str(ident) + ' needs unique upstream asset_id')
        for asset in matches:
            if asset.get('kind') in ('audio', 'font'):
                continue
            origin = obj(asset.get('origin')); category = origin.get('category')
            if category == LICENSED_3D:
                validate_licensed_model(checks, asset)
            label = 'origin asset ' + str(ident)
            checks.need(isinstance(category, str) and category in allowed,
                        label + ' third-party/CC/reference media is not self-created production visual')
            checks.need(meaningful(origin.get('method')) and meaningful(origin.get('entry_version')),
                        label + ' creation method and entry version required')
            checks.need(isinstance(origin.get('inputs'), list),
                        label + ' explicit input inventory required (empty only for no external inputs)')
            conflicts = reference_conflicts(asset, assets)
            checks.need(not conflicts,
                        label + ' bytes also declared third-party reference; cannot relabel as original')
            expected = {'ai_generated': 'self_generated', 'simulation': 'self_rendered',
                        'real_capture': 'user_capture', 'real_observation': 'user_capture'}
            if isinstance(asset.get('kind'), str) and asset.get('kind') in expected:
                checks.need(category == expected[asset.get('kind')],
                            label + ' creation category conflicts with media kind')
            if category == 'user_capture':
                checks.need(asset.get('kind') in ('real_capture', 'real_observation'),
                            label + ' capture category conflicts with media kind')
            parents = graph.setdefault(ident, set())
            for raw_input in seq(origin.get('inputs')):
                item = obj(raw_input); parent_id = item.get('asset_id')
                valid_id = meaningful(parent_id)
                checks.need(valid_id and parent_id != ident,
                            label + ' visual input needs unique upstream asset_id, not self-reference')
                if not valid_id:
                    continue
                parents.add(parent_id); pending.append(parent_id)
                upstream = [a for a in assets if a.get('id') == parent_id]
                parent = upstream[0] if len(upstream) == 1 else {}
                parent_category = obj(parent.get('origin')).get('category')
                checks.need(len(upstream) == 1,
                            label + ' visual input needs unique upstream asset_id')
                checks.need(parent_category in allowed,
                            label + ' third-party or unclassified visual input cannot become original by rendering')
                # Plans need no future file/hash, but supplied provenance cannot
                # contradict an upstream record. Actual validation requires both.
                checks.need(all(item[k] == parent.get(k) for k in ('file', 'sha256') if k in item)
                            and ('origin_category' not in item or item['origin_category'] == parent_category),
                            label + ' visual input contradicts upstream asset provenance')

    # Iterative traversal also handles arbitrarily long declared ancestor chains.
    visited, active = set(), set()
    cyclic = False
    for root in graph:
        stack = [(root, False)]
        while stack:
            node, leaving = stack.pop()
            if leaving:
                active.discard(node); visited.add(node)
            elif node in active:
                cyclic = True
            elif node not in visited:
                active.add(node); stack.append((node, True))
                stack.extend((parent, False) for parent in graph.get(node, ()))
    checks.need(not cyclic, 'origin cyclic provenance cannot establish a creation root')


def context_assets(data, shot_ids, final=False, representative=False):
    """Freeze provenance, not later catalog/rights review conclusions."""
    return [{k: a.get(k) for k in (('id', 'kind', 'file', 'sha256', 'origin', 'disclosure',
                                     'source', 'creator', 'rights', 'scientific_review')
                                    if obj(a.get('origin')).get('category') == LICENSED_3D else
                                    ('id', 'kind', 'file', 'sha256', 'origin', 'disclosure'))}
            for a in selected_assets(data, shot_ids, final, representative)]


def references(data, shot_ids, final=False, representative=False):
    for shot in seq(data.get('shots')):
        if obj(shot).get('id') in shot_ids:
            origin = obj(obj(obj(shot).get('shotbook')).get('origin'))
            for key in ('design', 'entrypoint'):
                yield origin.get(key), 'origin shot ' + str(shot.get('id')) + ' ' + key
    for asset in selected_assets(data, shot_ids, final, representative):
        if asset.get('kind') in ('audio', 'font'):
            continue
        origin = obj(asset.get('origin'))
        if origin.get('category') == LICENSED_3D:
            yield {k: asset.get(k) for k in ('file', 'sha256')}, 'origin licensed model source'
            for key in ('license_evidence', 'review'):
                yield origin.get(key), 'origin licensed model ' + key
            for dependency in seq(origin.get('dependencies')):
                yield dependency, 'origin licensed model dependency'
            for dependency in seq(origin.get('inputs')):
                yield dependency, 'origin licensed model input'
            continue
        for key in ('entrypoint', 'design', 'output', 'review'):
            yield origin.get(key), 'origin asset ' + str(asset.get('id')) + ' ' + key
        for key in ('inputs', 'frames'):
            for ref in seq(origin.get(key)):
                yield ref, 'origin asset ' + str(asset.get('id')) + ' ' + key
        if origin.get('category') == 'user_capture':
            yield origin.get('user_authorization'), 'origin user capture authorization'


def validate_origin(checks, shot_ids, final=False, representative=False):
    validate_origin_plan(checks, shot_ids, final, representative)
    data = checks.data
    checks.need(obj(data.get('origin_contract')).get('mode') == 'self_created_visuals',
                'origin explicit self_created_visuals contract required; no legacy bypass')
    for shot in seq(data.get('shots')):
        if obj(shot).get('id') not in shot_ids:
            continue
        origin = obj(obj(shot.get('shotbook')).get('origin'))
        label = 'origin shot ' + str(shot.get('id'))
        method = origin.get('planned_method')
        checks.need(isinstance(method, str) and method in ('self_generated', 'self_rendered', 'user_capture'),
                    label + ' self-created planned method required')
        checks.need(meaningful(origin.get('entry_version')), label + ' entry version required')
        medium = obj(obj(shot.get('shotbook')).get('realism')).get('medium')
        allowed = {'ai_realistic': 'self_generated', 'three_d': 'self_rendered',
                   'authentic_recording': 'user_capture', 'pure_2d': 'self_rendered',
                   'static_pan': 'self_rendered', 'infographic': 'self_rendered'}
        checks.need(isinstance(medium, str) and method == allowed.get(medium),
                    label + ' origin method conflicts with actual medium')
    for asset in selected_assets(data, shot_ids, final, representative):
        if asset.get('kind') in ('audio', 'font'):
            continue
        origin = obj(asset.get('origin')); label = 'origin asset ' + str(asset.get('id'))
        category = origin.get('category')
        conflicts = reference_conflicts(asset, [obj(a) for a in seq(data.get('assets'))])
        checks.need(not conflicts, label + ' bytes also declared third-party reference; cannot relabel as original')
        checks.need(isinstance(category, str) and category in PRODUCTION_CATEGORIES,
                    label + ' third-party/CC/reference media is not self-created production visual')
        checks.need(meaningful(origin.get('method')) and meaningful(origin.get('entry_version')),
                    label + ' creation method and entry version required')
        checks.need(isinstance(origin.get('inputs'), list), label + ' explicit input inventory required (empty only for no external inputs)')
        for item in seq(origin.get('inputs')):
            item = obj(item)
            parents = [obj(a) for a in seq(data.get('assets')) if obj(a).get('id') == item.get('asset_id')]
            parent = parents[0] if len(parents) == 1 else {}
            checks.need(meaningful(item.get('asset_id')) and len(parents) == 1 and item.get('asset_id') != asset.get('id'),
                        label + ' visual input needs unique upstream asset_id, not self-reference')
            checks.need(all(item.get(k) == parent.get(k) for k in ('file', 'sha256'))
                        and item.get('origin_category') == obj(parent.get('origin')).get('category'),
                        label + ' visual input contradicts upstream asset provenance')
            checks.need(obj(item).get('origin_category') in PRODUCTION_CATEGORIES,
                        label + ' third-party or unclassified visual input cannot become original by rendering')
        if category == LICENSED_3D:
            validate_licensed_model(checks, asset, actual=True)
            continue
        checks.need(bool(seq(origin.get('frames'))), label + ' actual frame evidence required')
        checks.need(obj(origin.get('output')) == {k: asset.get(k) for k in ('file', 'sha256')},
                    label + ' original output must bind exact used asset bytes')
        if asset.get('kind') == 'ai_generated':
            checks.need(category == 'self_generated', label + ' AI asset requires own generation evidence')
        if asset.get('kind') == 'simulation':
            checks.need(category == 'self_rendered', label + ' simulation requires own render evidence')
        if asset.get('kind') in ('real_capture', 'real_observation'):
            checks.need(category == 'user_capture', label + ' real footage must be verified user capture, not CC footage')
        if category == 'user_capture':
            checks.need(asset.get('kind') in ('real_capture', 'real_observation'), label + ' capture category conflicts with media kind')
        if category in ('self_generated', 'self_rendered'):
            checks.need(meaningful(asset.get('disclosure')), label + ' generated/rendered visual requires non-live disclosure')
    for ref, label in references(data, shot_ids, final, representative):
        checks.evidence(ref, label)


def validate_cover_origins(checks):
    """Cover-only delivery uses the same source rules without requiring video shots."""
    from stage_checks import Checks
    data = checks.data
    mapping = obj(data.get('deliverable_asset_ids'))
    from task_scope import cover_keys
    cover_mapping = {key: mapping.get(key) for key in cover_keys(data)}
    for key, ids in cover_mapping.items():
        checks.need(isinstance(ids, list) and bool(ids) and all(meaningful(i) for i in seq(ids)),
                    'origin ' + key + ' nonempty visual asset ID list required')
        for ident in seq(ids):
            checks.need(sum(obj(a).get('id') == ident for a in seq(data.get('assets'))) == 1,
                        'origin ' + key + ' visual dependency missing or ambiguous')
        checks.need(len(seq(ids)) == len(set(i for i in seq(ids) if isinstance(i, str))),
                    'origin ' + key + ' visual dependency IDs must be unique')
        assets = [a for a in seq(data.get('assets')) if obj(a).get('id') in seq(ids)]
        checks.need(bool(assets) and any(obj(a).get('file') == obj(data.get('deliverables')).get(key) for a in assets),
                    'origin ' + key + ' must link its actual original output asset')
    scoped = {'origin_contract': data.get('origin_contract'), 'assets': data.get('assets'),
              'deliverable_asset_ids': cover_mapping, 'shots': []}
    local = Checks(scoped, checks.root)
    validate_origin(local, [], final=True)
    checks.errors.extend(local.errors)
