"""Resolve a moved final video for read-only episode checks."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

LOCAL_CONFIG = Path("config/video-storage.local.json")
STORAGE_FOLDERS = ("release-candidate", "archive")


def file_identity(path):
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


@dataclass(frozen=True)
class StoredVideo:
    episode_file: str
    path: Path
    sha256: str
    identity: tuple

    def unchanged(self):
        return file_identity(self.path) == self.identity


def bind_stored_video(data, episode_dir, supplied_path, *, config=None):
    """Allow a different location only for the same reviewed final deliverable."""
    try:
        episode_file = data["deliverables"]["video"]
        expected_hash = data["qa"]["reviewed_sha256"]["video"]
    except (KeyError, TypeError) as exc:
        raise ValueError("Stored video requires the episode deliverable and its reviewed SHA-256") from exc
    episode_dir = Path(episode_dir).resolve()
    if not isinstance(episode_file, str) or not episode_file.strip() or Path(episode_file).is_absolute():
        raise ValueError("Stored video requires an episode-relative deliverables.video")
    if not (episode_dir / episode_file).resolve().is_relative_to(episode_dir):
        raise ValueError("The original video path must stay inside the episode directory")
    if not isinstance(expected_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_hash):
        raise ValueError("Stored video requires the final reviewed SHA-256")

    if config is None:
        config = Path(__file__).resolve().parents[1] / LOCAL_CONFIG
    settings = json.loads(Path(config).read_text(encoding="utf-8"))
    root = Path(settings.get("archive_root", "")) if isinstance(settings, dict) else Path()
    if not root.is_absolute():
        raise ValueError("video-storage.local.json must provide an absolute archive_root")

    candidate = Path(supplied_path)
    folders = {root / name for name in STORAGE_FOLDERS}
    if not candidate.is_absolute() or ".." in candidate.parts or candidate.parent not in folders:
        raise ValueError("Stored video must be inside the configured release-candidate or archive folder")
    path = candidate.resolve(strict=True)
    if path.parent != root.resolve(strict=True) / candidate.parent.name or not path.is_file():
        raise ValueError("Stored video must resolve to a file in its configured folder")

    identity = file_identity(path)
    with path.open("rb") as handle:
        sha256 = hashlib.file_digest(handle, "sha256").hexdigest()
    if sha256 != expected_hash:
        raise ValueError("Stored video does not match the reviewed SHA-256")
    video = StoredVideo(episode_file, path, sha256, identity)
    if not video.unchanged():
        raise ValueError("Stored video changed while checking its SHA-256")
    return video
