"""Locate the single global installation and audit project copies without modifying files."""
import argparse
import json
import os
from pathlib import Path
import re
import stat

NAME = 'science-video-production'
SKIP = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'site-packages'}


def is_science_skill(path):
    try:
        with Path(path).open(encoding='utf-8-sig') as stream:
            head = stream.read(8192)
    except (OSError, UnicodeError):
        return False
    if not head.startswith('---\n'):
        return False
    frontmatter = head.split('---', 2)[1]
    return re.search(r'(?m)^name:\s*[\"\x27]?science-video-production[\"\x27]?\s*$', frontmatter) is not None


def global_installation(codex_home=None):
    home = Path(codex_home) if codex_home is not None else Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    folder = home / 'skills'
    found = []
    if folder.is_dir():
        for child in folder.iterdir():
            if child.is_dir() and is_science_skill(child / 'SKILL.md'):
                resolved = child.resolve()
                # A global alias into a project is not a global installation.
                if resolved.parent != folder.resolve():
                    raise ValueError('Global Skill entry must live in the global skills directory: ' + str(child))
                if resolved not in found:
                    found.append(resolved)
    if len(found) != 1:
        raise ValueError('Expected one global science-video-production installation; found ' + str(len(found)))
    return found[0]


def require_global_runtime(root, codex_home=None):
    installed = global_installation(codex_home)
    if Path(root).resolve() != installed:
        raise ValueError('Project/repository Skill execution is disabled. Use global Skill: ' + str(installed))
    return installed


def audit_projects(roots, installed, source_roots=()):
    installed = Path(installed).resolve()
    sources = {Path(p).resolve() for p in source_roots}
    copies, aliases, errors = [], [], []
    for value in roots:
        root = Path(value)
        if not root.is_dir():
            errors.append(str(root) + ': missing/unreadable project root')
            continue
        def onerror(exc):
            errors.append(str(exc))
        for current, dirs, files in os.walk(root, followlinks=False, onerror=onerror):
            parent = Path(current)
            # Never follow compatibility junctions/symlinks into the global tree.
            retained = []
            for name in dirs:
                path = parent / name
                if name in SKIP:
                    continue
                if path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                    if path.resolve() == installed:
                        aliases.append(str(path))
                    continue
                retained.append(name)
            dirs[:] = retained
            if 'SKILL.md' in files and is_science_skill(parent / 'SKILL.md'):
                resolved = parent.resolve()
                if resolved == installed or resolved in sources:
                    continue
                copies.append(str(parent))
    return {'independent_project_copies': sorted(set(copies)),
            'global_aliases': sorted(set(aliases)), 'scan_errors': errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan', nargs='*', default=[], metavar='PROJECT_ROOT')
    parser.add_argument('--source-root', action='append', default=[], help='read-only maintenance source, never a runtime exemption')
    args = parser.parse_args()
    try:
        installed = global_installation()
        result = {'global_skill': str(installed), **audit_projects(args.scan, installed, args.source_root)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result['independent_project_copies'] or result['scan_errors'] else 0
    except (OSError, ValueError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
