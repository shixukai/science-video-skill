#!/usr/bin/env python3
"""Check or install the two companion top-level Codex skills from this repo.

Syncs ``skills/science-video-topic-selection`` and ``skills/science-video-publishing``
into ``${CODEX_HOME}/skills/<name>`` (default ``~/.codex/skills/<name>``) while
keeping ``science-video-production`` as the single source Git working tree.
Never modifies unrelated skills or ``science-video-production``.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys

SKILL_NAMES = ("science-video-topic-selection", "science-video-publishing")
BACKUP_DIR_NAME = ".science-video-skill-backups"
SKIP_PARTS = {".git", "__pycache__"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_frontmatter_name(path):
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"Missing YAML frontmatter in {path}")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Malformed YAML frontmatter in {path}")
    match = re.search(r"(?m)^name:\s*[\"']?([A-Za-z0-9_-]+)[\"']?\s*$", parts[1])
    if not match:
        raise ValueError(f"Missing frontmatter name in {path}")
    return match.group(1)


def _iter_source_files(skill_dir):
    files = []
    for p in sorted(skill_dir.rglob("*")):
        rel = p.relative_to(skill_dir)
        if any(part in SKIP_PARTS for part in rel.parts):
            continue
        if p.is_file():
            files.append((rel, p))
    return files


def validate_companion_source(source_root, name):
    skill_dir = Path(source_root) / name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise ValueError(f"Companion skill missing SKILL.md: {skill_dir}")
    declared = parse_frontmatter_name(skill_md)
    if declared != name:
        raise ValueError(f"Frontmatter name mismatch in {skill_md}: {declared!r} != {name!r}")
    files = _iter_source_files(skill_dir)
    for rel, path in files:
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for link in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in link or link.startswith("mailto:") or link.startswith("#"):
                continue
            target_part = link.split("#", 1)[0]
            if not target_part:
                continue
            resolved = (path.parent / target_part).resolve()
            if not resolved.is_relative_to(skill_dir.resolve()):
                raise ValueError(f"Self-contained skill link escapes {name}: {rel.as_posix()} -> {link}")
            if not resolved.exists():
                raise ValueError(f"Broken local link in {name}: {rel.as_posix()} -> {link}")
    return files


def _is_reparse(path):
    try:
        st = path.lstat()
    except OSError:
        return False
    return path.is_symlink() or bool(getattr(st, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def plan_sync(source_root, codex_home):
    source_root = Path(source_root).resolve()
    skills_dir = Path(codex_home).resolve() / "skills"
    rows = []
    for name in SKILL_NAMES:
        files = validate_companion_source(source_root, name)
        target_dir = skills_dir / name
        if _is_reparse(target_dir):
            raise ValueError(f"Refusing to sync over symlink/junction: {target_dir}")
        if target_dir.exists() and not target_dir.is_dir():
            raise ValueError(f"Target skill path is not a directory: {target_dir}")
        target_md = target_dir / "SKILL.md"
        if target_md.is_file():
            existing_name = parse_frontmatter_name(target_md)
            if existing_name != name:
                raise ValueError(f"Destination {target_dir} is owned by another skill: {existing_name!r}")
        file_plan = []
        status = "current"
        if not target_dir.exists():
            status = "missing"
        for rel, src in files:
            src_bytes = src.read_bytes()
            dst = target_dir / rel
            if dst.is_file():
                dst_bytes = dst.read_bytes()
                fstatus = "current" if dst_bytes == src_bytes else "differs"
                if fstatus == "differs" and status == "current":
                    status = "differs"
            else:
                dst_bytes = None
                fstatus = "missing"
                if status == "current":
                    status = "differs" if target_dir.exists() else "missing"
            file_plan.append({
                "rel": rel.as_posix(),
                "source": str(src),
                "target": str(dst),
                "source_sha256": sha(src_bytes),
                "target_sha256": sha(dst_bytes) if dst_bytes is not None else None,
                "status": fstatus,
            })
        rows.append({
            "name": name,
            "target_dir": str(target_dir),
            "status": status,
            "files": file_plan,
        })
    return rows


def install(plan, replace_existing=False):
    for row in plan:
        if row["status"] == "differs" and not replace_existing:
            raise ValueError(
                f"Existing companion skill differs: {row['target_dir']}; rerun with --replace-existing"
            )
    results = []
    for row in plan:
        target_dir = Path(row["target_dir"])
        skills_dir = target_dir.parent
        backup_root = skills_dir / BACKUP_DIR_NAME / row["name"]
        updated_files = []
        for item in row["files"]:
            src = Path(item["source"])
            dst = Path(item["target"])
            src_bytes = src.read_bytes()
            if item["status"] == "current":
                updated_files.append({**item, "action": "unchanged"})
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            backup_path = None
            if dst.is_file():
                existing_bytes = dst.read_bytes()
                if sha(existing_bytes) != item["target_sha256"]:
                    raise ValueError(f"Concurrent modification detected at {dst}")
                backup_root.mkdir(parents=True, exist_ok=True)
                safe_rel = item["rel"].replace("/", "__")
                backup_path = backup_root / f"{safe_rel}-{sha(existing_bytes)[:16]}.bak"
                if not backup_path.exists():
                    backup_path.write_bytes(existing_bytes)
            dst.write_bytes(src_bytes)
            updated_files.append({
                **item,
                "action": "installed",
                "target_sha256": sha(src_bytes),
                "backup": str(backup_path) if backup_path else None,
            })
        results.append({
            "name": row["name"],
            "target_dir": row["target_dir"],
            "status": "current" if row["status"] == "current" else "installed",
            "files": updated_files,
        })
    return results


def default_codex_home():
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="read-only check of companion skill installs")
    group.add_argument("--install", action="store_true", help="install or update companion skills")
    parser.add_argument("--replace-existing", action="store_true", help="overwrite differing files with backup")
    parser.add_argument("--codex-home", type=Path, default=default_codex_home())
    parser.add_argument("--source", type=Path, default=Path(__file__).resolve().parents[1] / "skills")
    args = parser.parse_args(argv)
    try:
        plan = plan_sync(args.source, args.codex_home)
        if args.check:
            out = {"mode": "check", "codex_home": str(args.codex_home), "skills": plan}
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0 if all(r["status"] == "current" for r in plan) else 1
        res = install(plan, replace_existing=args.replace_existing)
        out = {"mode": "install", "codex_home": str(args.codex_home), "skills": res}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
