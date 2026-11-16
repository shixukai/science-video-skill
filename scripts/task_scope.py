"""Requested outputs, independent of authority to upload or publish."""


def scope(data):
    return data.get('delivery_scope', 'release_package')


def cover_keys(data):
    if scope(data) == 'video_only':
        return ()
    selected = data.get('requested_cover_keys', ('cover_3_4', 'cover_4_3'))
    if not isinstance(selected, (list, tuple)):
        return ('cover_3_4', 'cover_4_3')
    return tuple(k for k in selected if isinstance(k, str) and k in ('cover_3_4', 'cover_4_3'))


def validate_scope(checks):
    selected = scope(checks.data)
    checks.need(selected in ('video_only', 'release_package'), 'delivery_scope must be video_only or release_package')
    if 'requested_cover_keys' in checks.data:
        keys = checks.data['requested_cover_keys']
        checks.need(isinstance(keys, list) and bool(keys) and all(isinstance(k, str) and k in ('cover_3_4', 'cover_4_3') for k in keys)
                    and len(set(k for k in keys if isinstance(k, str))) == len(keys), 'requested_cover_keys must be a nonempty unique list of supported ratios')
        checks.need(selected != 'video_only', 'video_only cannot request covers')
        checks.need(bool(str(checks.data.get('delivery_scope_note', '')).strip()), 'custom cover selection requires requested scope note')
    if selected == 'video_only':
        note = checks.data.get('delivery_scope_note')
        checks.need(isinstance(note, str) and bool(note.strip()), 'video_only requires the actual requested scope note')
        # An explicit scope cannot conceal still-requested deliverables.
        outputs = checks.data.get('deliverables', {})
        if isinstance(outputs, dict):
            checks.need(not any(outputs.get(k) for k in ('cover_3_4', 'cover_4_3')), 'video_only conflicts with cover deliverables; keep them in release_package')
