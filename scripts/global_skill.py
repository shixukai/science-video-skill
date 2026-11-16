"""Locate the single global installation and audit project copies without modifying files."""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import subprocess

PERSONAL_SKILLS_REMOTE = "https://chatgpt.com/backend-api/git-authed/skills"
MANAGED_PERSONAL_SKILLS = Path("/root/.codex/skills/remote-skills")

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


def _entries(folder):
    if not folder.is_dir():
        return []
    found = []
    for child in folder.iterdir():
        if child.is_dir() and is_science_skill(child / 'SKILL.md'):
            resolved = child.resolve()
            if resolved.parent != folder.resolve():
                raise ValueError('Global Skill entry must live in its installed skills directory: ' + str(child))
            found.append(resolved)
    return found


def _verify_personal_checkout(folder):
    """Recognize the host-managed checkout, never an arbitrary project copy."""
    if (folder.is_symlink()
            or getattr(folder.lstat(), 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT):
        raise ValueError('Personal Skill checkout root must not be a filesystem alias: ' + str(folder))
    try:
        def git(*args):
            return subprocess.run(['git', '-C', str(folder), *args], check=True,
                                  capture_output=True, text=True, timeout=10).stdout.strip()
        actual_root = Path(git('rev-parse', '--show-toplevel')).resolve()
        remote = git('remote', 'get-url', 'origin').rstrip('/')
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError('Cannot verify personal Skill checkout: ' + str(folder)) from exc
    if actual_root != folder.resolve() or remote != PERSONAL_SKILLS_REMOTE:
        raise ValueError('Personal Skill directory is not the official managed checkout: ' + str(folder))


def global_installation(codex_home=None):
    home = Path(codex_home) if codex_home is not None else Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex')
    folder = home / 'skills'
    found = _entries(folder)
    personal_roots = [(folder / 'remote-skills', False)]
    # The managed cloud host can keep its official personal checkout separate
    # from the read-only runtime home. An explicit home isolates callers/tests.
    if codex_home is None:
        personal_roots.append((MANAGED_PERSONAL_SKILLS, True))
    checked = set()
    for personal, optional in personal_roots:
        try:
            resolved = personal.resolve()
            if resolved in checked:
                continue
            checked.add(resolved)
            active = _entries(personal)
        except PermissionError:
            # A normal desktop user may not be allowed to inspect /root.
            # This optional host candidate must not break a valid local install.
            # Errors in the selected runtime home remain explicit failures.
            if optional:
                continue
            raise
        if active:
            _verify_personal_checkout(personal)
            found.extend(active)
    found = list(dict.fromkeys(found))
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
