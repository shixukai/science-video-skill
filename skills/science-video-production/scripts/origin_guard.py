"""Original-visual provenance structure only, never an authorship detector."""
from realism_guard import obj, meaningful


def seq(value):
    return value if isinstance(value, list) else []


def selected_assets(data, shot_ids, final=False):
    from render_gate import input_asset_ids
    from stage_checks import used_asset_ids
    ids = used_asset_ids(data) if final else input_asset_ids(data, shot_ids)
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


def context_assets(data, shot_ids, final=False):
    """Freeze provenance, not later catalog/rights review conclusions."""
    return [{k: a.get(k) for k in ('id', 'kind', 'file', 'sha256', 'origin', 'disclosure')}
            for a in selected_assets(data, shot_ids, final)]


def references(data, shot_ids, final=False):
    for shot in seq(data.get('shots')):
        if obj(shot).get('id') in shot_ids:
            origin = obj(obj(obj(shot).get('shotbook')).get('origin'))
            for key in ('design', 'entrypoint'):
                yield origin.get(key), 'origin shot ' + str(shot.get('id')) + ' ' + key
    for asset in selected_assets(data, shot_ids, final):
        if asset.get('kind') in ('audio', 'font'):
            continue
        origin = obj(asset.get('origin'))
        for key in ('entrypoint', 'design', 'output', 'review'):
            yield origin.get(key), 'origin asset ' + str(asset.get('id')) + ' ' + key
        for key in ('inputs', 'frames'):
            for ref in seq(origin.get(key)):
                yield ref, 'origin asset ' + str(asset.get('id')) + ' ' + key
        if origin.get('category') == 'user_capture':
            yield origin.get('user_authorization'), 'origin user capture authorization'


def validate_origin(checks, shot_ids, final=False):
    data = checks.data
    selected = selected_assets(data, shot_ids, final)
    graph = {a.get('id'): [obj(i).get('asset_id') for i in seq(obj(a.get('origin')).get('inputs'))
                         if isinstance(obj(i).get('asset_id'), str)] for a in selected if isinstance(a.get('id'), str)}
    visited, active = set(), set()
    def acyclic(node):
        if node in active: return False
        if node in visited: return True
        active.add(node)
        valid = all(acyclic(parent) for parent in graph.get(node, []))
        active.remove(node); visited.add(node)
        return valid
    checks.need(all(acyclic(node) for node in graph), 'origin cyclic provenance cannot establish a creation root')
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
    for asset in selected_assets(data, shot_ids, final):
        if asset.get('kind') in ('audio', 'font'):
            continue
        origin = obj(asset.get('origin')); label = 'origin asset ' + str(asset.get('id'))
        category = origin.get('category')
        conflicts = [a for a in seq(data.get('assets')) if obj(a).get('sha256') == asset.get('sha256')
                     and meaningful(asset.get('sha256'))
                     and obj(obj(a).get('origin')).get('category') == 'third_party_reference']
        checks.need(not conflicts, label + ' bytes also declared third-party reference; cannot relabel as original')
        checks.need(isinstance(category, str) and category in ('self_generated', 'self_rendered', 'self_designed', 'user_capture'),
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
            checks.need(obj(item).get('origin_category') in ('self_generated', 'self_rendered', 'self_designed', 'user_capture'),
                        label + ' third-party or unclassified visual input cannot become original by rendering')
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
    for ref, label in references(data, shot_ids, final):
        checks.evidence(ref, label)


def validate_cover_origins(checks):
    """Cover-only delivery uses the same source rules without requiring video shots."""
    from stage_checks import Checks
    data = checks.data
    mapping = obj(data.get('deliverable_asset_ids'))
    cover_mapping = {key: mapping.get(key) for key in ('cover_3_4', 'cover_4_3')}
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
