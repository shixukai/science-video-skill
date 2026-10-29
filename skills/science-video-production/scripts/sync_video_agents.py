#!/usr/bin/env python3
"""Check or sync this Skill's six personal Codex agent definitions (Python 3.11+)."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys
import tempfile
import tomllib


ROLE_NAMES = (
    "video_researcher", "video_visual_artist", "video_animator",
    "video_audio_editor", "video_producer_windows", "video_reviewer",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def validate_definition(data, name):
    definition = tomllib.loads(data.decode("utf-8-sig"))
    # This package intentionally inherits model, capabilities and permissions.
    if set(definition) != {"name", "description", "developer_instructions"}:
        raise ValueError(f"{name}: this package expects only name/description/developer_instructions")
    if definition["name"] != name:
        raise ValueError(f"{name}: filename and declared role name differ")
    if not all(isinstance(value, str) and value.strip() for value in definition.values()):
        raise ValueError(f"{name}: all fields must be nonempty strings")


def plan_sync(source, codex_home):
    source, codex_home = Path(source).resolve(), Path(codex_home).resolve()
    destination = codex_home / "agents"
    if destination.resolve().parent != codex_home:
        raise ValueError("agents directory must resolve inside the selected Codex home")
    records = []
    for name in ROLE_NAMES:
        source_file = source / f"{name}.toml"
        if source_file.resolve().parent != source:
            raise ValueError(f"{name}: source escapes the definitions directory")
        content = source_file.read_bytes()
        validate_definition(content, name)
        target = destination / source_file.name
        if target.resolve().parent != destination.resolve() or target.is_symlink():
            raise ValueError(f"{name}: destination must be a regular file in agents")
        if target.exists() and not target.is_file():
            raise ValueError(f"{name}: destination is not a file")
        before = target.read_bytes() if target.exists() else None
        if before is not None:
            # Do not overwrite a differently named role sharing this filename.
            old = tomllib.loads(before.decode("utf-8-sig"))
            if old.get("name") != name:
                raise ValueError(f"{name}: installed file belongs to another role")
        status = "missing" if before is None else "current" if before == content else "different"
        records.append({"name": name, "target": str(target), "status": status,
                        "before_sha256": sha(before) if before is not None else None,
                        "after_sha256": sha(content), "content": content, "before": before})
    return records


def install(records, replace_existing=False):
    if any(row["status"] == "different" for row in records) and not replace_existing:
        raise ValueError("Definitions differ: inspect them, then use --install --replace-existing to update")
    # Preflight the entire set before making any changes.
    for row in records:
        target = Path(row["target"])
        current = target.read_bytes() if target.exists() else None
        if current != row["before"]:
            raise ValueError(f"{row['name']}: destination changed since the sync plan")
        if row["status"] != "current" and row["before"] is not None:
            backup_dir = target.parent / ".science-video-backups"
            if (backup_dir.resolve().parent != target.parent.resolve()
                    or backup_dir.is_symlink()
                    or (backup_dir.exists() and not backup_dir.is_dir())):
                raise ValueError("Backup directory must be a regular directory inside agents")
            backup = backup_dir / f"{row['name']}-{row['before_sha256']}.bak"
            if (backup.resolve().parent != backup_dir.resolve() or backup.is_symlink()
                    or (backup.exists() and not backup.is_file())):
                raise ValueError(f"{row['name']}: backup must be a regular unlinked file")
            if backup.exists() and backup.read_bytes() != row["before"]:
                raise ValueError(f"{row['name']}: backup contents do not match")
            row["backup"] = str(backup)
    for row in records:
        if row["status"] == "current":
            continue
        target = Path(row["target"])
        target.parent.mkdir(parents=True, exist_ok=True)
        if row["before"] is not None:
            backup = Path(row["backup"])
            backup.parent.mkdir(exist_ok=True)
            if backup.exists():
                if backup.is_symlink() or backup.read_bytes() != row["before"]:
                    raise ValueError(f"{row['name']}: backup contents do not match")
            else:
                with backup.open("xb") as handle:
                    handle.write(row["before"])
        # Same-directory atomic replacement; no shell command or recursive move.
        fd, temporary = tempfile.mkstemp(prefix=".video-agent-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(row["content"])
            current = target.read_bytes() if target.exists() else None
            if current != row["before"]:
                raise ValueError(f"{row['name']}: destination changed before replacement")
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        if target.read_bytes() != row["content"]:
            raise ValueError(f"{row['name']}: installed contents do not match")
        row["status"] = "installed"
        if row.get("backup") and Path(row["backup"]).read_bytes() != row["before"]:
            raise ValueError(f"{row['name']}: retained backup no longer matches")


def public_records(records):
    return [{k: v for k, v in row.items() if k not in ("content", "before")} for row in records]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="Read-only comparison (default)")
    modes.add_argument("--install", action="store_true", help="Install missing definitions")
    parser.add_argument("--replace-existing", action="store_true", help="Update differing named roles, retaining backups")
    parser.add_argument("--codex-home", type=Path, help="Codex home; default CODEX_HOME or ~/.codex")
    args = parser.parse_args(argv)
    if args.replace_existing and not args.install:
        parser.error("--replace-existing requires --install")
    codex_home = args.codex_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
    records = []
    try:
        records = plan_sync(Path(__file__).resolve().parents[1] / "agents", codex_home)
        if args.install:
            install(records, args.replace_existing)
        print(json.dumps({"mode": "install" if args.install else "check",
                          "validation_scope": "definition_files_only",
                          "runtime_discovery": "not_checked_by_this_helper",
                          "runtime_invocation": "not_checked_by_this_helper",
                          "roles": public_records(records)}, ensure_ascii=False, indent=2))
        return 0 if all(row["status"] in ("current", "installed") for row in records) else 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc), "roles": public_records(records)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
