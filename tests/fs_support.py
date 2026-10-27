"""Skip only unavailable native link privileges; never suppress validation failures."""


def symlink_or_skip(case, link, target, **kwargs):
    try:
        link.symlink_to(target, **kwargs)
    except OSError as error:
        if getattr(error, 'winerror', None) == 1314:
            case.skipTest('Windows does not grant symbolic-link creation privilege')
        raise
