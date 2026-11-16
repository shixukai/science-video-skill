"""Fail-closed realism contracts. Structural checks are not visual/science approval."""


def obj(value):
    return value if isinstance(value, dict) else {}


def meaningful(value):
    return isinstance(value, str) and value.strip().casefold() not in {
        '', 'todo', 'tbd', 'pending', 'none', 'n/a', 'pass', 'ok', 'unknown', '待补', '待验', '无'}


RENDERERS = {
    'authentic_recording': {'camera'},
    'ai_realistic': {'video_model'},
    'three_d': {'three_d_engine'},
    'pure_2d': {'vector_renderer', 'raster_animation'},
    'static_pan': {'still_pan'},
    'infographic': {'vector_renderer', 'raster_animation'},
}
REALISTIC = {'authentic_recording', 'ai_realistic', 'three_d'}


def references(data, shot_ids):
    """Actual evidence dependencies frozen with the render inputs."""
    intent = obj(obj(data.get('design')).get('visual_intent'))
    yield intent.get('style_reference'), 'realism style reference'
    for raw in data.get('shots', []) if isinstance(data.get('shots'), list) else []:
        shot = obj(raw)
        if shot.get('id') not in shot_ids:
            continue
        realism = obj(obj(shot.get('shotbook')).get('realism'))
        exception = obj(realism.get('exception'))
        if exception:
            yield exception.get('user_evidence'), 'realism scoped user exception'


def validate_realism(checks, shot_ids, phase):
    data = checks.data
    intent = obj(obj(data.get('design')).get('visual_intent'))
    checks.need(intent.get('target') == 'scientific_realism',
                'realism explicit scientific_realism visual intent required; no legacy silent bypass')
    checks.need(meaningful(intent.get('scientific_constraints')),
                'realism scientific constraints must bind visual design')
    for reference, label in references(data, shot_ids):
        checks.evidence(reference, label)
    for raw in data.get('shots', []) if isinstance(data.get('shots'), list) else []:
        shot = obj(raw)
        if shot.get('id') not in shot_ids:
            continue
        label = 'realism shot ' + str(shot.get('id'))
        r = obj(obj(shot.get('shotbook')).get('realism'))
        medium, renderer = r.get('medium'), r.get('renderer')
        checks.need(r.get('role') in ('main', 'explanation'), label + ' explicit main/explanation role required')
        checks.need(isinstance(medium, str) and medium in RENDERERS, label + ' recognized medium required')
        checks.need(isinstance(medium, str) and isinstance(renderer, str)
                    and renderer in RENDERERS.get(medium, set()),
                    label + ' renderer must match actual medium; vector/still is not video_model')
        for field in ('scientific_basis', 'visible_motion'):
            checks.need(meaningful(r.get(field)), label + ' ' + field + ' required')
        expected_modality = {'authentic_recording':'real_footage', 'ai_realistic':'ai_generated',
                             'three_d':'controlled_3d', 'pure_2d':'pure_2d',
                             'static_pan':'pure_2d', 'infographic':'pure_2d'}
        if 'modality' in shot:
            checks.need(isinstance(medium, str) and shot['modality'] == expected_modality.get(medium),
                        label + ' modality conflicts with realism medium')
        if medium == 'authentic_recording':
            source_id = r.get('source_asset_id')
            assets = [obj(a) for a in data.get('assets', []) if isinstance(a, dict) and a.get('id') == source_id]
            asset = assets[0] if len(assets) == 1 else {}
            checks.need(meaningful(source_id) and source_id in (shot.get('asset_ids') or [])
                        and asset.get('kind') in ('real_capture', 'real_observation'),
                        label + ' authentic recording needs linked real source asset, not AI/simulation')
            checks.need(meaningful(asset.get('source')) and meaningful(asset.get('creator'))
                        and obj(asset.get('rights')).get('status') == 'cleared'
                        and all(meaningful(obj(asset.get('rights')).get(k)) for k in ('evidence', 'scope')),
                        label + ' authentic source provenance and cleared rights required')
            path = checks.evidence(asset, label + ' authentic source media')
            if path is not None:
                checks.duration(path, require_audio=False, label=label + ' authentic source media')
        if medium in ('ai_realistic', 'three_d'):
            checks.need(meaningful(r.get('disclosure')), label + ' synthetic media disclosure required; not real recording')
        if isinstance(medium, str) and medium in REALISTIC:
            checks.need(r.get('motion_kind') == 'subject_motion',
                        label + ' actual subject motion required; still pan/zoom is not realistic motion')
        if r.get('role') in ('main', 'explanation') and (not isinstance(medium, str) or medium not in REALISTIC):
            exception = obj(r.get('exception'))
            checks.need(exception.get('shot_id') == shot.get('id')
                        and exception.get('scope') == 'nonrealistic_full_frame_shot'
                        and meaningful(exception.get('reason')),
                        label + ' nonrealistic full-frame shot needs explicit per-shot user exception')
            checks.evidence(exception.get('user_evidence'), label + ' per-shot user authorization')
    if phase == 'full':
        from render_gate import stamp
        animation = checks.record('visual_frames.animation')
        view = checks.viewing(animation.get('viewing'), 'realism continuous sample', 'representative')
        producer = obj(obj(data.get('brief')).get('roles')).get('producer')
        reviewer = view.get('reviewer')
        checks.need(meaningful(producer) and meaningful(reviewer)
                    and reviewer.strip().casefold() != producer.strip().casefold(),
                    'realism sample independent watched/listened reviewer must differ from producer')
        checks.need(stamp(view.get('reviewed_at')) is not None, 'realism sample actual review timestamp required')
        checks.evidence(animation.get('independent_review_evidence'), 'realism sample independent review evidence')
