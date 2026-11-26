#!/usr/bin/env python3
"""Safe non-interactive Gemini API CLI (`google-gemini/gemini-api-cli`) helper for the Google Flow route.

Provides:
- `preflight`: read-only detection of `gemini-api` on PATH or standard install dirs, version check,
  and masked `whoami` credential-source inspection (`--check-auth`, optional `--verify-live`).
- `models`: inspect offline curated model catalog or live API models (`--live`).
- `upload`: upload >14 MB local media conditioning inputs via `gemini-api files upload --wait`
  and return reusable `files/<id>` handles with SHA-256 receipts.
- `video`: generate/edit HD video clips (`gemini-omni-1.2-flash` default) with mandatory `>= 1080p`
  HD guard (`--resolution 1080p` default; `720p` blocked unless `--allow-proxy-720p` for internal
  proxies only), repeatable `-i/--input` frame/reference conditioning (auto-uploading >14 MB files),
  `--previous-interaction-id` continuation, `--dry-run`, `--async`, disk-backed prompt ledger
  persistence (`--ledger`), and automatic `ffprobe` stream verification.
- `resume`: safely resume polling an `--async` or timed-out video interaction via
  `gemini-api video --resume <id>` without blind resubmission.
- `image`: generate/edit text-free keyframes (`16:9`) or cover art backgrounds (`3:4`/`4:3`/`1:1`/`16:9`)
  via `gemini-api image` (`gemini-nano-banana-2.1` default, `--image-size 2K` default).
- `music`: generate optional ducked BGM stems via `gemini-api music` (`lyria-3.5` default).
- `tts`: optional cloud TTS via `gemini-api tts` (`gemini-3.8-flash-tts` default), emitting a
  `check_episode.py`-compatible generation record when `--receipt` is provided.

Never calls interactive subcommands (`configure --interactive`, `auth login`, `explore`), always
passes `--no-interactive`, redacts credentials from logs/receipts, refuses to overwrite existing
`--receipt`/`--report` files, and marks outputs `generated_unreviewed` (never audiovisual acceptance).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Any

SOURCE_ID = "google-gemini-api-cli"
DEFAULT_API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions"
DEFAULT_VIDEO_MODEL = "gemini-omni-1.2-flash"
DEFAULT_IMAGE_MODEL = "gemini-nano-banana-2.1"
DEFAULT_MUSIC_MODEL = "lyria-3.5"
DEFAULT_TTS_MODEL = "gemini-3.8-flash-tts"
DEFAULT_VIDEO_ASPECT_RATIO = "16:9"
DEFAULT_VIDEO_RESOLUTION = "1080p"
DEFAULT_IMAGE_ASPECT_RATIO = "16:9"
DEFAULT_IMAGE_SIZE = "2K"
EXPECTED_CLIP_FPS = 24.0
MIN_FORMAL_SHORT_EDGE_PX = 1080

# Upstream gemini-api-cli keeps inline requests under 20 MiB total (19 MiB payload after base64 ~ 14.25 MiB raw).
MAX_INLINE_RAW_BYTES = 14 * 1024 * 1024

ALLOWED_VIDEO_ASPECT_RATIOS = ("16:9", "9:16")
ALLOWED_VIDEO_RESOLUTIONS = ("360p", "720p", "1080p", "4k")
FORMAL_VIDEO_RESOLUTIONS = ("1080p", "4k")
ALLOWED_IMAGE_ASPECT_RATIOS = (
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4",
    "9:16", "16:9", "21:9", "1:8", "8:1", "1:4", "4:1",
)
ALLOWED_IMAGE_SIZES = ("512", "1K", "2K", "4K")

FILE_REF_RE = re.compile(r"^files/[a-z0-9](?:[a-z0-9-]{0,38}[a-z0-9])?$")
YOUTUBE_HOST_RE = re.compile(r"^(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)$", re.IGNORECASE)

SECRET_PATTERNS = (
    re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"(x-goog-api-key\s*[:=]\s*)[^\s\"',;]+", re.IGNORECASE),
    re.compile(r"(GEMINI_API_KEY\s*=\s*)[^\s\"',;]+", re.IGNORECASE),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bya29\.[A-Za-z0-9._-]{16,}\b"),
    re.compile(r"([?&](?:key|api_key|access_token|token)=)[^&\s]+", re.IGNORECASE),
)

INSTALL_HINTS = {
    "windows_powershell": "iwr -useb https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.ps1 | iex",
    "macos_linux": "curl -fsSL https://raw.githubusercontent.com/google-gemini/gemini-api-cli/main/scripts/install.sh | bash",
    "go_install": "go install github.com/google-gemini/gemini-api-cli/cmd/gemini-api@latest",
    "releases": "https://github.com/google-gemini/gemini-api-cli/releases",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def redact_secrets(text: str) -> str:
    cleaned = text
    for pat in SECRET_PATTERNS:
        cleaned = pat.sub(lambda m: (m.group(1) + "[REDACTED]") if m.lastindex else "[REDACTED]", cleaned)
    return cleaned


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_rate(rate_str: str | None) -> float | None:
    if not rate_str or rate_str in {"0/0", "N/A"}:
        return None
    if "/" in rate_str:
        num_s, den_s = rate_str.split("/", 1)
        try:
            num, den = float(num_s), float(den_s)
        except ValueError:
            return None
        return num / den if den != 0 else None
    try:
        return float(rate_str)
    except ValueError:
        return None


def ffprobe_media(path: Path, *, runner: Any = subprocess.run) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_format",
        "-show_streams",
        "-of",
        "json",
        str(path),
    ]
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {redact_secrets((proc.stderr or '').strip())}")
    raw = json.loads(proc.stdout or "{}")
    streams = raw.get("streams", [])
    fmt = raw.get("format", {})
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    avg_fps = parse_rate(v_stream.get("avg_frame_rate")) if v_stream else None
    r_fps = parse_rate(v_stream.get("r_frame_rate")) if v_stream else None
    dur = None
    for candidate in (
        v_stream.get("duration") if v_stream else None,
        fmt.get("duration"),
        a_stream.get("duration") if a_stream else None,
    ):
        if candidate is not None:
            try:
                dur = float(candidate)
                break
            except (TypeError, ValueError):
                pass
    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "has_video": v_stream is not None,
        "has_audio": a_stream is not None,
        "width": int(v_stream["width"]) if v_stream and v_stream.get("width") else None,
        "height": int(v_stream["height"]) if v_stream and v_stream.get("height") else None,
        "avg_fps": round(avg_fps, 4) if avg_fps is not None else None,
        "r_fps": round(r_fps, 4) if r_fps is not None else None,
        "duration_s": round(dur, 4) if dur is not None else None,
        "video_codec": v_stream.get("codec_name") if v_stream else None,
        "audio_codec": a_stream.get("codec_name") if a_stream else None,
        "audio_sample_rate": int(a_stream["sample_rate"]) if a_stream and a_stream.get("sample_rate") else None,
    }


def resolve_binary(explicit_binary: str | None = None) -> dict[str, Any]:
    host_os = platform.system() or "Unknown"
    if explicit_binary:
        p = Path(explicit_binary).expanduser()
        if p.is_file():
            return {"available": True, "binary": str(p.resolve()), "source": "flag", "host_os": host_os}
        found = shutil.which(explicit_binary)
        if found:
            return {"available": True, "binary": str(Path(found).resolve()), "source": "flag_path", "host_os": host_os}
        return {
            "available": False,
            "binary": None,
            "source": "flag",
            "host_os": host_os,
            "reason": f"Specified binary not found: {explicit_binary}",
        }

    found = shutil.which("gemini-api")
    if found:
        return {"available": True, "binary": str(Path(found).resolve()), "source": "PATH", "host_os": host_os}

    exe = "gemini-api.exe" if host_os.lower().startswith("win") else "gemini-api"
    home = Path.home()
    candidates = [
        home / ".local" / "bin" / exe,
        home / "go" / "bin" / exe,
    ]
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app:
        candidates.insert(0, Path(local_app) / "Programs" / "gemini-api" / exe)
        candidates.insert(1, Path(local_app) / "gemini-api" / exe)
    for cand in candidates:
        if cand.is_file():
            return {"available": True, "binary": str(cand.resolve()), "source": "standard_dir", "host_os": host_os}

    return {
        "available": False,
        "binary": None,
        "source": "not_found",
        "host_os": host_os,
        "reason": "gemini-api binary not found on PATH or standard install directories",
    }


def build_cli_cmd(
    binary: str,
    subargs: list[str],
    *,
    output_format: str | None = "json",
    dry_run: bool = False,
    api_version: str | None = None,
    timeout: str | None = None,
    no_keyring: bool = False,
) -> list[str]:
    cmd = [binary, "--no-interactive"]
    if output_format:
        cmd.extend(["--output-format", output_format])
    if dry_run:
        cmd.append("--dry-run")
    if api_version:
        cmd.extend(["--api-version", api_version])
    if timeout:
        cmd.extend(["--timeout", timeout])
    if no_keyring:
        cmd.append("--no-keyring")
    cmd.extend(subargs)
    return cmd


def _parse_json_stdout(stdout: str) -> Any:
    text = (stdout or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for ln in reversed(lines):
            try:
                return json.loads(ln)
            except json.JSONDecodeError:
                continue
        return None


def _ensure_new_output_path(raw: str | None, label: str) -> Path | None:
    if not raw:
        return None
    p = Path(raw).resolve()
    if p.exists():
        raise FileExistsError(f"Refusing to overwrite existing {label}: {p}")
    return p


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _load_or_init_ledger(path: Path) -> dict[str, Any]:
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data
        raise ValueError(f"Malformed prompt ledger JSON (expected object with 'entries' list): {path}")
    return {
        "schema_version": 1,
        "route": "google_flow",
        "backend": "gemini_api_cli",
        "source_id": SOURCE_ID,
        "updated_at": _now_iso(),
        "entries": [],
    }


def _upsert_ledger_entry(ledger_path: Path, entry: dict[str, Any]) -> None:
    ledger = _load_or_init_ledger(ledger_path)
    entries: list[dict[str, Any]] = ledger["entries"]
    key_shot = entry.get("shot_id")
    key_id = entry.get("entry_id")
    replaced = False
    for idx, existing in enumerate(entries):
        if key_id and existing.get("entry_id") == key_id:
            entries[idx] = entry
            replaced = True
            break
        if not key_id and key_shot and existing.get("shot_id") == key_shot and existing.get("kind") == entry.get("kind"):
            entries[idx] = entry
            replaced = True
            break
    if not replaced:
        entries.append(entry)
    ledger["updated_at"] = _now_iso()
    _write_json(ledger_path, ledger)


def _read_prompt_text(prompt_parts: list[str] | None, prompt_file: str | None) -> str | None:
    chunks: list[str] = []
    if prompt_file:
        pf = Path(prompt_file).resolve()
        if not pf.is_file():
            raise FileNotFoundError(f"Prompt file not found: {pf}")
        chunks.append(pf.read_text(encoding="utf-8").strip())
    if prompt_parts:
        joined = " ".join(prompt_parts).strip()
        if joined:
            chunks.append(joined)
    merged = "\n".join(c for c in chunks if c).strip()
    return merged or None


def _load_body_json(raw_body: str | None) -> dict[str, Any] | None:
    if not raw_body:
        return None
    text = raw_body.strip()
    if text.startswith("@"):
        p = Path(text[1:]).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Request body file not found: {p}")
        text = p.read_text(encoding="utf-8")
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("--body JSON must be an object")
    return obj


def _is_remote_input(ref: str) -> bool:
    s = ref.strip()
    if FILE_REF_RE.fullmatch(s):
        return True
    if s.startswith("https://generativelanguage.googleapis.com/"):
        return True
    if s.startswith(("http://", "https://")):
        return True
    return False


def _prepare_media_inputs(
    inputs: list[str] | None,
    *,
    binary: str,
    auto_upload: bool,
    dry_run: bool,
    api_version: str | None,
    timeout: str | None,
    no_keyring: bool,
    runner: Any,
) -> tuple[list[str], list[dict[str, Any]]]:
    resolved: list[str] = []
    uploads: list[dict[str, Any]] = []
    for raw in inputs or []:
        ref = raw.strip()
        if not ref:
            continue
        if _is_remote_input(ref):
            resolved.append(ref)
            continue
        p = Path(ref).resolve()
        if not p.is_file():
            raise FileNotFoundError(f"Conditioning input file not found: {p}")
        size = p.stat().st_size
        if size == 0:
            raise ValueError(f"Conditioning input file is empty: {p}")
        if size > MAX_INLINE_RAW_BYTES:
            if not auto_upload:
                raise ValueError(
                    f"Input {p.name} is {size} bytes (> {MAX_INLINE_RAW_BYTES} inline cap); "
                    "pass --auto-upload or run `scripts/gemini_api_cli.py upload` first."
                )
            if dry_run:
                uploads.append({
                    "local_path": str(p),
                    "size_bytes": size,
                    "status": "would_upload_files_api",
                })
                resolved.append("files/dry-run-placeholder")
                continue
            up_cmd = build_cli_cmd(
                binary,
                ["files", "upload", str(p), "--wait"],
                output_format="json",
                dry_run=False,
                api_version=api_version,
                timeout=timeout,
                no_keyring=no_keyring,
            )
            proc = runner(up_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
            if proc.returncode != 0:
                raise RuntimeError(
                    f"gemini-api files upload failed for {p}: {redact_secrets((proc.stderr or proc.stdout or '').strip())}"
                )
            parsed = _parse_json_stdout(proc.stdout)
            file_uri = None
            if isinstance(parsed, dict):
                file_uri = parsed.get("name") or (parsed.get("file", {}) or {}).get("name")
            if not isinstance(file_uri, str) or not file_uri.strip():
                plain = (proc.stdout or "").strip().splitlines()
                file_uri = plain[-1].strip() if plain else ""
            if not FILE_REF_RE.fullmatch(file_uri):
                raise RuntimeError(f"Unexpected files upload output for {p}: {redact_secrets(file_uri)}")
            uploads.append({
                "local_path": str(p),
                "sha256": sha256_file(p),
                "size_bytes": size,
                "file_ref": file_uri,
                "status": "uploaded",
            })
            resolved.append(file_uri)
        else:
            resolved.append(str(p))
    return resolved, uploads


def _extract_artifact_path(parsed: Any, stdout: str, requested_out: str | None) -> Path | None:
    if isinstance(parsed, dict) and isinstance(parsed.get("path"), str) and parsed["path"].strip():
        return Path(parsed["path"]).resolve()
    lines = [ln.strip() for ln in (stdout or "").splitlines() if ln.strip()]
    if lines:
        cand = Path(lines[-1])
        if cand.is_file():
            return cand.resolve()
    if requested_out:
        p = Path(requested_out).resolve()
        if p.is_file():
            return p
    return None


def _extract_response_id(parsed: Any, stdout: str) -> str | None:
    if isinstance(parsed, dict):
        for key in ("response_id", "id", "interaction_id"):
            val = parsed.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    lines = [ln.strip() for ln in (stdout or "").splitlines() if ln.strip()]
    if len(lines) == 1 and not lines[0].startswith("{") and " " not in lines[0] and not Path(lines[0]).exists():
        return lines[0]
    return None


def _check_video_compliance(probe: dict[str, Any], *, allow_proxy_720p: bool) -> list[dict[str, Any]]:
    flags: list[dict[str, Any]] = []
    w, h = probe.get("width"), probe.get("height")
    if not probe.get("has_video") or w is None or h is None:
        flags.append({"code": "missing_video_stream", "detail": "Generated file has no valid video stream"})
    else:
        short_edge = min(w, h)
        if short_edge < MIN_FORMAL_SHORT_EDGE_PX and not allow_proxy_720p:
            flags.append({
                "code": "low_res_generated_clip",
                "width": w,
                "height": h,
                "min_short_edge_px": MIN_FORMAL_SHORT_EDGE_PX,
                "detail": "Formal google_flow clips require short edge >= 1080 px (pass --resolution 1080p or 4k).",
            })
    avg_fps = probe.get("avg_fps")
    if avg_fps is not None and abs(avg_fps - EXPECTED_CLIP_FPS) > 0.25:
        flags.append({
            "code": "non_24fps_native_cadence",
            "measured_fps": avg_fps,
            "expected_flow_fps": EXPECTED_CLIP_FPS,
            "detail": "Clip fps differs from default 24 fps Flow cadence; verify timeline fps lock or pass --allow-fps-conversion intentionally.",
        })
    return flags


def cmd_preflight(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    report_path = _ensure_new_output_path(args.report, "report")
    bin_info = resolve_binary(args.binary)
    payload: dict[str, Any] = {
        "tool": "scripts/gemini_api_cli.py",
        "command": "preflight",
        "source_id": SOURCE_ID,
        "checked_at": _now_iso(),
        "host_os": bin_info["host_os"],
        "binary": bin_info["binary"],
        "binary_source": bin_info["source"],
        "default_models": {
            "video": DEFAULT_VIDEO_MODEL,
            "image": DEFAULT_IMAGE_MODEL,
            "music": DEFAULT_MUSIC_MODEL,
            "tts": DEFAULT_TTS_MODEL,
        },
        "fallback_modes": ["google_flow_web"],
        "install_hints": INSTALL_HINTS,
    }
    if not bin_info["available"]:
        payload["status"] = "unavailable"
        payload["reason"] = bin_info.get("reason")
        if report_path:
            _write_json(report_path, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    binary = bin_info["binary"]
    ver_cmd = build_cli_cmd(
        binary,
        ["version"],
        output_format="json",
        api_version=args.api_version,
        no_keyring=args.no_keyring,
    )
    ver_proc = runner(ver_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    ver_parsed = _parse_json_stdout(ver_proc.stdout)
    if isinstance(ver_parsed, dict) and ver_parsed.get("version"):
        payload["version"] = str(ver_parsed["version"])
    else:
        payload["version"] = (ver_proc.stdout or "").strip() or None

    who_cmd = build_cli_cmd(
        binary,
        ["whoami"],
        output_format="json",
        api_version=args.api_version,
        no_keyring=args.no_keyring,
    )
    who_proc = runner(who_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    who_parsed = _parse_json_stdout(who_proc.stdout)
    cred_sources: dict[str, str] = {}
    auth_configured = False
    if isinstance(who_parsed, dict):
        creds = who_parsed.get("credentials")
        if isinstance(creds, dict):
            for k, v in creds.items():
                src = str(v.get("source", "unset")) if isinstance(v, dict) else "unset"
                cred_sources[k] = src
                if src not in ("", "unset", "none"):
                    auth_configured = True
        params = who_parsed.get("global_parameters")
        if isinstance(params, dict):
            payload["global_parameters"] = {
                k: (v.get("value") if isinstance(v, dict) else v) for k, v in params.items()
            }
    payload["credential_sources"] = cred_sources
    payload["auth_configured"] = auth_configured

    if args.verify_live:
        if not auth_configured:
            payload["status"] = "unauthenticated"
            payload["live_models_checked"] = False
            payload["reason"] = "Cannot run --verify-live without configured GEMINI_API_KEY or access token"
            if report_path:
                _write_json(report_path, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        ml_cmd = build_cli_cmd(
            binary,
            ["models", "list"],
            output_format="json",
            api_version=args.api_version,
            timeout=args.timeout,
            no_keyring=args.no_keyring,
        )
        ml_proc = runner(ml_cmd, capture_output=True, text=True, encoding="utf-8", check=False)
        payload["live_models_checked"] = ml_proc.returncode == 0
        if ml_proc.returncode != 0:
            payload["status"] = "auth_or_network_error"
            payload["reason"] = redact_secrets((ml_proc.stderr or ml_proc.stdout or "").strip())
            if report_path:
                _write_json(report_path, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1

    if args.check_auth and not auth_configured:
        payload["status"] = "unauthenticated"
        payload["reason"] = (
            "gemini-api is installed but no API key or OAuth token is configured "
            "(set GEMINI_API_KEY or run `gemini-api configure --api-key ...`)."
        )
        rc = 1
    else:
        payload["status"] = "ready" if (auth_configured or not args.check_auth) else "unauthenticated"
        rc = 0

    if report_path:
        _write_json(report_path, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return rc


def cmd_models(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason"), "install_hints": INSTALL_HINTS}, ensure_ascii=False, indent=2))
        return 1
    subargs = ["models", "list", "--all"] if args.live else ["models"]
    cmd = build_cli_cmd(
        bin_info["binary"],
        subargs,
        output_format="json",
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    if proc.returncode != 0:
        print(redact_secrets((proc.stderr or proc.stdout or "").strip()), file=sys.stderr)
        return proc.returncode or 1
    print(proc.stdout.strip())
    return 0


def cmd_upload(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    receipt_path = _ensure_new_output_path(args.receipt, "receipt")
    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason")}, ensure_ascii=False, indent=2))
        return 1
    local_file = Path(args.file).resolve()
    if not local_file.is_file():
        raise FileNotFoundError(f"File to upload not found: {local_file}")
    subargs = ["files", "upload", str(local_file)]
    if args.wait:
        subargs.append("--wait")
    if args.display_name:
        subargs.extend(["--display-name", args.display_name])
    if args.mime_type:
        subargs.extend(["--mime-type", args.mime_type])
    cmd = build_cli_cmd(
        bin_info["binary"],
        subargs,
        output_format="json",
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    parsed = _parse_json_stdout(proc.stdout)
    file_ref = None
    if isinstance(parsed, dict):
        file_ref = parsed.get("name") or (parsed.get("file", {}) or {}).get("name")
    receipt = {
        "schema_version": 1,
        "tool": "scripts/gemini_api_cli.py",
        "command": "upload",
        "source_id": SOURCE_ID,
        "recorded_at": _now_iso(),
        "dry_run": bool(args.dry_run),
        "status": "dry_run" if args.dry_run and proc.returncode == 0 else ("uploaded" if proc.returncode == 0 else "failed"),
        "local_file": str(local_file),
        "local_sha256": sha256_file(local_file),
        "size_bytes": local_file.stat().st_size,
        "file_ref": file_ref,
        "response": parsed,
        "stderr": redact_secrets((proc.stderr or "").strip()) or None,
    }
    if receipt_path:
        _write_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else (proc.returncode or 1)


def cmd_video(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    receipt_path = _ensure_new_output_path(args.receipt, "receipt")
    aspect_ratio = args.aspect_ratio or DEFAULT_VIDEO_ASPECT_RATIO
    if aspect_ratio not in ALLOWED_VIDEO_ASPECT_RATIOS:
        raise ValueError(f"Unsupported video --aspect-ratio {aspect_ratio!r}; expected one of: {', '.join(ALLOWED_VIDEO_ASPECT_RATIOS)}")
    resolution = (args.resolution or DEFAULT_VIDEO_RESOLUTION).lower()
    if resolution not in ALLOWED_VIDEO_RESOLUTIONS:
        raise ValueError(f"Unsupported video --resolution {resolution!r}; expected one of: {', '.join(ALLOWED_VIDEO_RESOLUTIONS)}")
    if resolution not in FORMAL_VIDEO_RESOLUTIONS and not args.allow_proxy_720p:
        raise ValueError(
            f"Refusing formal google_flow video request at {resolution!r}: formal clips require >= 1080p "
            "(use --resolution 1080p or 4k, or pass --allow-proxy-720p strictly for internal screening proxies)."
        )

    prompt = _read_prompt_text(args.prompt, args.prompt_file)
    body_obj = _load_body_json(args.body)
    if not prompt and not body_obj:
        raise ValueError("A video prompt, --prompt-file, or --body JSON is required")

    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason"), "fallback_modes": ["google_flow_web"]}, ensure_ascii=False, indent=2))
        return 1
    binary = bin_info["binary"]

    resolved_inputs, uploads = _prepare_media_inputs(
        args.input,
        binary=binary,
        auto_upload=args.auto_upload,
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
        runner=runner,
    )

    model = args.model or DEFAULT_VIDEO_MODEL
    subargs: list[str] = ["video"]
    use_body = body_obj is not None or bool(args.duration)
    if use_body:
        payload = dict(body_obj or {})
        if payload.get("store") is False:
            raise ValueError(
                "gemini-api video runs with background=true and requires server-side storage (do not set store=false)."
            )
        payload.setdefault("model", model)
        rf = payload.get("response_format")
        rf = dict(rf) if isinstance(rf, dict) else {}
        rf["type"] = "video"
        rf.setdefault("aspect_ratio", aspect_ratio)
        rf.setdefault("resolution", resolution)
        if args.duration:
            rf["duration"] = args.duration
        payload["response_format"] = rf
        if args.previous_interaction_id and "previous_interaction_id" not in payload:
            payload["previous_interaction_id"] = args.previous_interaction_id
        subargs.extend(["--body", json.dumps(payload, ensure_ascii=False)])
        if prompt and "input" not in payload:
            subargs.append(prompt)
    else:
        subargs.append(prompt or "")
        subargs.extend(["--model", model, "--aspect-ratio", aspect_ratio, "--resolution", resolution])
        if args.previous_interaction_id:
            subargs.extend(["--previous-interaction-id", args.previous_interaction_id])

    for inp in resolved_inputs:
        subargs.extend(["-i", inp])
    if args.out:
        out_p = Path(args.out).resolve()
        if not args.dry_run and not str(args.out).endswith(("/", "\\")):
            out_p.parent.mkdir(parents=True, exist_ok=True)
        subargs.extend(["--out", str(out_p)])
    if args.async_mode:
        subargs.append("--async")
    if args.poll_interval:
        subargs.extend(["--poll-interval", args.poll_interval])
    if args.poll_timeout:
        subargs.extend(["--poll-timeout", args.poll_timeout])

    cmd = build_cli_cmd(
        binary,
        subargs,
        output_format="json",
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )

    entry_id = f"{args.shot_id or 'video'}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    ledger_path = Path(args.ledger).resolve() if args.ledger else None
    ledger_entry: dict[str, Any] = {
        "entry_id": entry_id,
        "kind": "video",
        "shot_id": args.shot_id,
        "backend": "gemini_api_cli",
        "model": model,
        "aspect_ratio": aspect_ratio,
        "resolution": resolution,
        "allow_proxy_720p": bool(args.allow_proxy_720p),
        "prompt": prompt,
        "inputs": resolved_inputs,
        "uploads": uploads,
        "previous_interaction_id": args.previous_interaction_id,
        "submitted_at": _now_iso(),
        "status": "dry_run_pending" if args.dry_run else "pending",
        "review_status": "generated_unreviewed",
    }
    if ledger_path and not args.dry_run:
        _upsert_ledger_entry(ledger_path, ledger_entry)

    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    parsed = _parse_json_stdout(proc.stdout)
    stderr_clean = redact_secrets((proc.stderr or "").strip())
    response_id = _extract_response_id(parsed, proc.stdout)

    flags: list[dict[str, Any]] = []
    probe: dict[str, Any] | None = None
    artifact_path: Path | None = None

    if proc.returncode != 0:
        status = "failed"
        rc = proc.returncode or 1
    elif args.dry_run:
        status = "dry_run"
        rc = 0
    elif args.async_mode:
        status = "submitted_async"
        rc = 0
    else:
        status = "completed"
        rc = 0
        artifact_path = _extract_artifact_path(parsed, proc.stdout, args.out)
        if artifact_path and artifact_path.is_file() and not args.skip_probe:
            probe = ffprobe_media(artifact_path, runner=runner)
            flags = _check_video_compliance(probe, allow_proxy_720p=bool(args.allow_proxy_720p))
            if any(f["code"] in ("low_res_generated_clip", "missing_video_stream") for f in flags):
                status = "flagged"
                rc = 1

    ledger_entry.update({
        "status": status,
        "completed_at": _now_iso(),
        "response_id": response_id,
        "resume_command": f"gemini-api video --resume {response_id}" if response_id else None,
        "output_path": str(artifact_path) if artifact_path else (str(Path(args.out).resolve()) if args.out else None),
        "sha256": probe["sha256"] if probe else (sha256_file(artifact_path) if artifact_path and artifact_path.is_file() else None),
        "probe": probe,
        "flags": flags,
        "stderr": stderr_clean or None,
    })
    if ledger_path and not args.dry_run:
        _upsert_ledger_entry(ledger_path, ledger_entry)

    receipt = {
        "schema_version": 1,
        "tool": "scripts/gemini_api_cli.py",
        "command": "video",
        "source_id": SOURCE_ID,
        "dry_run": bool(args.dry_run),
        "async": bool(args.async_mode),
        "command_argv": [redact_secrets(part) for part in cmd],
        "entry": ledger_entry,
        "cli_response": parsed if not args.dry_run else parsed,
        "review_status": "generated_unreviewed",
        "acceptance_note": "Technical generation completion only; inspect 1920x1080 Frame 0, contact sheets, 4-8s tails and run google_flow_audit.py before assembly.",
    }
    if receipt_path:
        _write_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return rc


def cmd_resume(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    receipt_path = _ensure_new_output_path(args.receipt, "receipt")
    interaction_id = args.interaction_id.strip()
    if not interaction_id:
        raise ValueError("Non-empty interaction_id is required for resume")
    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason")}, ensure_ascii=False, indent=2))
        return 1

    subargs = ["video", "--resume", interaction_id]
    if args.out:
        out_p = Path(args.out).resolve()
        if not args.dry_run and not str(args.out).endswith(("/", "\\")):
            out_p.parent.mkdir(parents=True, exist_ok=True)
        subargs.extend(["--out", str(out_p)])
    if args.poll_interval:
        subargs.extend(["--poll-interval", args.poll_interval])
    if args.poll_timeout:
        subargs.extend(["--poll-timeout", args.poll_timeout])

    cmd = build_cli_cmd(
        bin_info["binary"],
        subargs,
        output_format="json",
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    parsed = _parse_json_stdout(proc.stdout)
    stderr_clean = redact_secrets((proc.stderr or "").strip())

    probe: dict[str, Any] | None = None
    flags: list[dict[str, Any]] = []
    artifact_path: Path | None = None
    if proc.returncode != 0:
        status = "failed"
        rc = proc.returncode or 1
    elif args.dry_run:
        status = "dry_run"
        rc = 0
    else:
        status = "completed"
        rc = 0
        artifact_path = _extract_artifact_path(parsed, proc.stdout, args.out)
        if artifact_path and artifact_path.is_file() and not args.skip_probe:
            probe = ffprobe_media(artifact_path, runner=runner)
            flags = _check_video_compliance(probe, allow_proxy_720p=bool(args.allow_proxy_720p))
            if any(f["code"] in ("low_res_generated_clip", "missing_video_stream") for f in flags):
                status = "flagged"
                rc = 1

    entry = {
        "entry_id": f"{args.shot_id or 'resume'}-{interaction_id}",
        "kind": "video",
        "shot_id": args.shot_id,
        "backend": "gemini_api_cli",
        "response_id": interaction_id,
        "resumed_at": _now_iso(),
        "status": status,
        "output_path": str(artifact_path) if artifact_path else (str(Path(args.out).resolve()) if args.out else None),
        "sha256": probe["sha256"] if probe else (sha256_file(artifact_path) if artifact_path and artifact_path.is_file() else None),
        "probe": probe,
        "flags": flags,
        "stderr": stderr_clean or None,
        "review_status": "generated_unreviewed",
    }
    if args.ledger and not args.dry_run:
        _upsert_ledger_entry(Path(args.ledger).resolve(), entry)

    receipt = {
        "schema_version": 1,
        "tool": "scripts/gemini_api_cli.py",
        "command": "resume",
        "source_id": SOURCE_ID,
        "dry_run": bool(args.dry_run),
        "entry": entry,
        "cli_response": parsed,
        "review_status": "generated_unreviewed",
    }
    if receipt_path:
        _write_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return rc


def cmd_image(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    receipt_path = _ensure_new_output_path(args.receipt, "receipt")
    aspect_ratio = args.aspect_ratio or DEFAULT_IMAGE_ASPECT_RATIO
    if aspect_ratio not in ALLOWED_IMAGE_ASPECT_RATIOS:
        raise ValueError(f"Unsupported image --aspect-ratio {aspect_ratio!r}")
    image_size = args.image_size or DEFAULT_IMAGE_SIZE
    if image_size not in ALLOWED_IMAGE_SIZES:
        raise ValueError(f"Unsupported --image-size {image_size!r}; expected one of: {', '.join(ALLOWED_IMAGE_SIZES)}")

    prompt = _read_prompt_text(args.prompt, args.prompt_file)
    body_obj = _load_body_json(args.body)
    if not prompt and not body_obj:
        raise ValueError("An image prompt, --prompt-file, or --body JSON is required")

    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason")}, ensure_ascii=False, indent=2))
        return 1
    binary = bin_info["binary"]

    resolved_inputs, uploads = _prepare_media_inputs(
        args.input,
        binary=binary,
        auto_upload=args.auto_upload,
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
        runner=runner,
    )

    model = args.model or DEFAULT_IMAGE_MODEL
    subargs = ["image"]
    if body_obj is not None or args.no_store:
        payload = dict(body_obj or {})
        payload.setdefault("model", model)
        rf = payload.get("response_format")
        rf = dict(rf) if isinstance(rf, dict) else {}
        rf["type"] = "image"
        rf.setdefault("aspect_ratio", aspect_ratio)
        rf.setdefault("image_size", image_size)
        if args.output_mime_type:
            rf["mime_type"] = args.output_mime_type
        payload["response_format"] = rf
        if args.no_store:
            payload["store"] = False
        if args.previous_interaction_id and "previous_interaction_id" not in payload:
            payload["previous_interaction_id"] = args.previous_interaction_id
        subargs.extend(["--body", json.dumps(payload, ensure_ascii=False)])
        if prompt and "input" not in payload:
            subargs.append(prompt)
    else:
        subargs.append(prompt or "")
        subargs.extend(["--model", model, "--aspect-ratio", aspect_ratio, "--image-size", image_size])
        if args.output_mime_type:
            subargs.extend(["--output-mime-type", args.output_mime_type])
        if args.previous_interaction_id:
            subargs.extend(["--previous-interaction-id", args.previous_interaction_id])

    for inp in resolved_inputs:
        subargs.extend(["-i", inp])
    if args.out:
        out_p = Path(args.out).resolve()
        if not args.dry_run and not str(args.out).endswith(("/", "\\")):
            out_p.parent.mkdir(parents=True, exist_ok=True)
        subargs.extend(["--out", str(out_p)])

    cmd = build_cli_cmd(
        binary,
        subargs,
        output_format="json",
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    parsed = _parse_json_stdout(proc.stdout)
    artifact_path = _extract_artifact_path(parsed, proc.stdout, args.out) if proc.returncode == 0 and not args.dry_run else None
    response_id = _extract_response_id(parsed, proc.stdout)

    entry = {
        "entry_id": f"{args.shot_id or 'image'}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "kind": "image",
        "shot_id": args.shot_id,
        "backend": "gemini_api_cli",
        "model": model,
        "aspect_ratio": aspect_ratio,
        "image_size": image_size,
        "prompt": prompt,
        "inputs": resolved_inputs,
        "uploads": uploads,
        "previous_interaction_id": args.previous_interaction_id,
        "response_id": response_id,
        "status": "dry_run" if args.dry_run and proc.returncode == 0 else ("completed" if proc.returncode == 0 else "failed"),
        "output_path": str(artifact_path) if artifact_path else (str(Path(args.out).resolve()) if args.out else None),
        "sha256": sha256_file(artifact_path) if artifact_path and artifact_path.is_file() else None,
        "size_bytes": artifact_path.stat().st_size if artifact_path and artifact_path.is_file() else None,
        "stderr": redact_secrets((proc.stderr or "").strip()) or None,
        "review_status": "generated_unreviewed",
    }
    if args.ledger and not args.dry_run:
        _upsert_ledger_entry(Path(args.ledger).resolve(), entry)

    receipt = {
        "schema_version": 1,
        "tool": "scripts/gemini_api_cli.py",
        "command": "image",
        "source_id": SOURCE_ID,
        "dry_run": bool(args.dry_run),
        "entry": entry,
        "cli_response": parsed,
        "review_status": "generated_unreviewed",
        "acceptance_note": "For covers, pass text-free stills through scripts/compose_cover.py --lang zh|en and inspect full-res + phone thumbnails.",
    }
    if receipt_path:
        _write_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else (proc.returncode or 1)


def cmd_music(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    receipt_path = _ensure_new_output_path(args.receipt, "receipt")
    prompt = _read_prompt_text(args.prompt, args.prompt_file)
    body_obj = _load_body_json(args.body)
    if not prompt and not body_obj:
        raise ValueError("A music prompt, --prompt-file, or --body JSON is required")

    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason")}, ensure_ascii=False, indent=2))
        return 1
    model = args.model or DEFAULT_MUSIC_MODEL
    subargs = ["music"]
    if body_obj is not None:
        payload = dict(body_obj)
        payload.setdefault("model", model)
        subargs.extend(["--body", json.dumps(payload, ensure_ascii=False)])
        if prompt and "input" not in payload:
            subargs.append(prompt)
    else:
        subargs.extend([prompt or "", "--model", model])
    if args.out:
        out_p = Path(args.out).resolve()
        if not args.dry_run and not str(args.out).endswith(("/", "\\")):
            out_p.parent.mkdir(parents=True, exist_ok=True)
        subargs.extend(["--out", str(out_p)])

    cmd = build_cli_cmd(
        bin_info["binary"],
        subargs,
        output_format="json",
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    parsed = _parse_json_stdout(proc.stdout)
    artifact_path = _extract_artifact_path(parsed, proc.stdout, args.out) if proc.returncode == 0 and not args.dry_run else None
    probe = ffprobe_media(artifact_path, runner=runner) if artifact_path and artifact_path.is_file() and not args.skip_probe else None
    receipt = {
        "schema_version": 1,
        "tool": "scripts/gemini_api_cli.py",
        "command": "music",
        "source_id": SOURCE_ID,
        "dry_run": bool(args.dry_run),
        "model": model,
        "status": "dry_run" if args.dry_run and proc.returncode == 0 else ("completed" if proc.returncode == 0 else "failed"),
        "output_path": str(artifact_path) if artifact_path else (str(Path(args.out).resolve()) if args.out else None),
        "sha256": probe["sha256"] if probe else (sha256_file(artifact_path) if artifact_path and artifact_path.is_file() else None),
        "probe": probe,
        "cli_response": parsed,
        "stderr": redact_secrets((proc.stderr or "").strip()) or None,
        "review_status": "generated_unreviewed",
    }
    if receipt_path:
        _write_json(receipt_path, receipt)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else (proc.returncode or 1)


def _canonical_language_name(raw_lang: str | None) -> str:
    val = (raw_lang or "").strip().lower()
    if val.startswith("en"):
        return "English"
    if val.startswith("zh") or val in ("chinese", "mandarin", ""):
        return "Chinese"
    return raw_lang.strip() if raw_lang else "Chinese"


def cmd_tts(args: argparse.Namespace, *, runner: Any = subprocess.run) -> int:
    receipt_path = _ensure_new_output_path(args.receipt, "receipt")
    script_file = Path(args.script_file).resolve() if args.script_file else None
    if script_file and not script_file.is_file():
        raise FileNotFoundError(f"TTS script file not found: {script_file}")
    inline_text = " ".join(args.text or []).strip()
    if not script_file and not inline_text:
        raise ValueError("Provide --script-file or text arguments for tts")

    bin_info = resolve_binary(args.binary)
    if not bin_info["available"]:
        print(json.dumps({"status": "unavailable", "reason": bin_info.get("reason")}, ensure_ascii=False, indent=2))
        return 1

    model = args.model or DEFAULT_TTS_MODEL
    subargs = ["tts", "--model", model]
    if script_file:
        subargs.extend(["--file", str(script_file)])
    else:
        subargs.append(inline_text)
    if args.voice:
        subargs.extend(["--voice", args.voice])
    if args.style:
        subargs.extend(["--style", args.style])
    if args.language:
        subargs.extend(["--language", args.language])
    if args.out:
        out_p = Path(args.out).resolve()
        if not args.dry_run and not str(args.out).endswith(("/", "\\")):
            out_p.parent.mkdir(parents=True, exist_ok=True)
        subargs.extend(["--out", str(out_p)])

    cmd = build_cli_cmd(
        bin_info["binary"],
        subargs,
        output_format="json",
        dry_run=args.dry_run,
        api_version=args.api_version,
        timeout=args.timeout,
        no_keyring=args.no_keyring,
    )
    proc = runner(cmd, capture_output=True, text=True, encoding="utf-8", check=False)
    parsed = _parse_json_stdout(proc.stdout)
    artifact_path = _extract_artifact_path(parsed, proc.stdout, args.out) if proc.returncode == 0 and not args.dry_run else None
    probe = ffprobe_media(artifact_path, runner=runner) if artifact_path and artifact_path.is_file() and not args.skip_probe else None

    lang_name = _canonical_language_name(args.language)
    evidence_path: Path | None = None
    cloud_evidence: dict[str, str] | None = None
    if receipt_path and proc.returncode == 0 and not args.dry_run:
        evidence_path = receipt_path.with_name(f"{receipt_path.stem}.cloud-evidence.json")
        if evidence_path.exists():
            raise FileExistsError(f"Refusing to overwrite existing cloud evidence file: {evidence_path}")
        _write_json(evidence_path, {
            "tool": "scripts/gemini_api_cli.py",
            "source_id": SOURCE_ID,
            "recorded_at": _now_iso(),
            "endpoint": DEFAULT_API_ENDPOINT,
            "model_id": model,
            "cli_response": parsed,
        })
        ep_dir = Path(args.episode_dir).resolve() if args.episode_dir else receipt_path.parent
        try:
            ev_rel = evidence_path.resolve().relative_to(ep_dir).as_posix()
        except ValueError:
            ev_rel = evidence_path.name
        cloud_evidence = {
            "file": ev_rel,
            "sha256": sha256_file(evidence_path),
        }

    # Emit a check_episode.py / google_flow_audit.py compatible cloud generation record.
    record: dict[str, Any] = {
        "schema_version": 1,
        "status": "dry_run" if args.dry_run and proc.returncode == 0 else ("generated" if proc.returncode == 0 else "failed"),
        "provider": "Google",
        "backend": "gemini-api-cli",
        "model_id": model,
        "source_id": SOURCE_ID,
        "execution": {
            "status": "confirmed",
            "mode": "service",
            "location": DEFAULT_API_ENDPOINT,
            "confirmation_reference": args.confirmation_reference or "gemini-api-cli explicit tts invocation",
        },
        "voice": {
            "language": lang_name,
            "speaker": args.voice or "Kore",
            "language_code": args.language or ("en-US" if lang_name == "English" else "zh-CN"),
            "style": args.style or None,
        },
        "input": (
            {"file": str(script_file), "sha256": sha256_file(script_file)}
            if script_file
            else {"text_sha256": hashlib.sha256(inline_text.encode("utf-8")).hexdigest()}
        ),
        "output": (
            {
                "file": str(artifact_path),
                "sha256": probe["sha256"] if probe else sha256_file(artifact_path),
                "duration_s": probe.get("duration_s") if probe else None,
                "sample_rate": probe.get("audio_sample_rate") if probe else None,
            }
            if artifact_path and artifact_path.is_file()
            else {"file": str(Path(args.out).resolve()) if args.out else None, "sha256": None}
        ),
        "cloud_evidence": cloud_evidence,
        "cli_response": parsed,
        "stderr": redact_secrets((proc.stderr or "").strip()) or None,
        "review_status": "generated_unreviewed",
    }
    if receipt_path:
        _write_json(receipt_path, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0 if proc.returncode == 0 else (proc.returncode or 1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safe non-interactive Gemini API CLI (`gemini-api`) helper for the Google Flow production route."
    )
    parser.add_argument("--binary", help="Explicit path to gemini-api binary (defaults to PATH lookup).")
    parser.add_argument("--api-version", help="Override Gemini API version (passed to gemini-api --api-version).")
    parser.add_argument("--timeout", help="Override HTTP request timeout (e.g. 60s, 5m).")
    parser.add_argument("--no-keyring", action="store_true", help="Disable OS keyring access (forward --no-keyring).")

    sub = parser.add_subparsers(dest="command", required=True)

    p_pre = sub.add_parser("preflight", help="Check gemini-api binary availability, version, and credential sources.")
    p_pre.add_argument("--check-auth", action="store_true", help="Return exit code 1 if no API key or token is configured.")
    p_pre.add_argument("--verify-live", action="store_true", help="Query `gemini-api models list` to confirm live auth/connectivity.")
    p_pre.add_argument("--report", help="Write JSON preflight report to a new file path (refuses overwrite).")

    p_mod = sub.add_parser("models", help="Inspect curated offline models or live API models.")
    p_mod.add_argument("--live", action="store_true", help="Query live API models via `gemini-api models list --all`.")

    p_up = sub.add_parser("upload", help="Upload a >14 MB local file via Files API and return files/<id>.")
    p_up.add_argument("file", help="Local media file path to upload.")
    p_up.add_argument("--display-name", help="Human-readable display name.")
    p_up.add_argument("--mime-type", help="Override detected MIME type.")
    p_up.add_argument("--no-wait", dest="wait", action="store_false", default=True, help="Do not wait for ACTIVE state.")
    p_up.add_argument("--dry-run", action="store_true", help="Validate and preview HTTP request without uploading.")
    p_up.add_argument("--receipt", help="Write JSON upload receipt to a new file path (refuses overwrite).")

    p_vid = sub.add_parser("video", help="Generate or edit a video clip via `gemini-api video` with HD guard and ledger tracking.")
    p_vid.add_argument("prompt", nargs="*", help="Physical visual + literal foley prompt (no Mandarin voiceover).")
    p_vid.add_argument("--prompt-file", help="Read prompt text from a UTF-8 file.")
    p_vid.add_argument("--body", help="Advanced Interactions API JSON body string or @path/to/payload.json.")
    p_vid.add_argument("--model", "-m", default=DEFAULT_VIDEO_MODEL, help=f"Video model (default: {DEFAULT_VIDEO_MODEL}).")
    p_vid.add_argument("--aspect-ratio", default=DEFAULT_VIDEO_ASPECT_RATIO, help=f"Aspect ratio (default: {DEFAULT_VIDEO_ASPECT_RATIO}).")
    p_vid.add_argument("--resolution", default=DEFAULT_VIDEO_RESOLUTION, help=f"Output resolution (default: {DEFAULT_VIDEO_RESOLUTION}; formal clips require 1080p or 4k).")
    p_vid.add_argument("--allow-proxy-720p", action="store_true", help="Explicitly permit 360p/720p strictly for internal screening proxies.")
    p_vid.add_argument("-i", "--input", action="append", default=[], help="Conditioning frame/video/reference path or files/<id> (repeatable).")
    p_vid.add_argument("--no-auto-upload", dest="auto_upload", action="store_false", default=True, help="Disable auto-uploading >14 MB local inputs via Files API.")
    p_vid.add_argument("--previous-interaction-id", help="Continue/edit from a prior video interaction ID.")
    p_vid.add_argument("--duration", help="Optional response_format.duration override (e.g. 8s, 10s, 3s-15s for Omni 1.2 Flash) merged into --body.")
    p_vid.add_argument("--out", help="Output video path or directory.")
    p_vid.add_argument("--async", dest="async_mode", action="store_true", help="Return interaction handle immediately without polling.")
    p_vid.add_argument("--poll-interval", help="Override async initial poll interval (e.g. 5s).")
    p_vid.add_argument("--poll-timeout", help="Override async poll timeout (e.g. 15m).")
    p_vid.add_argument("--shot-id", help="Episode shot ID (e.g. SH01) recorded in ledger/receipt.")
    p_vid.add_argument("--ledger", help="Disk-backed JSON prompt ledger path (updated before and after submission).")
    p_vid.add_argument("--receipt", help="Write JSON receipt to a new file path (refuses overwrite).")
    p_vid.add_argument("--dry-run", action="store_true", help="Validate and preview HTTP request offline without network/spend.")
    p_vid.add_argument("--skip-probe", action="store_true", help="Skip ffprobe verification on generated clip.")

    p_res = sub.add_parser("resume", help="Resume polling an async or timed-out `gemini-api video` interaction by ID.")
    p_res.add_argument("interaction_id", help="Interaction handle returned by `video --async` or recorded in the ledger.")
    p_res.add_argument("--out", help="Output video path or directory.")
    p_res.add_argument("--poll-interval", help="Override initial poll interval.")
    p_res.add_argument("--poll-timeout", help="Override poll timeout.")
    p_res.add_argument("--allow-proxy-720p", action="store_true", help="Permit <1080p clip strictly as an internal proxy.")
    p_res.add_argument("--shot-id", help="Episode shot ID for ledger correlation.")
    p_res.add_argument("--ledger", help="Disk-backed JSON prompt ledger path to update.")
    p_res.add_argument("--receipt", help="Write JSON resume receipt to a new file path (refuses overwrite).")
    p_res.add_argument("--dry-run", action="store_true", help="Preview poll request without executing.")
    p_res.add_argument("--skip-probe", action="store_true", help="Skip ffprobe verification on downloaded clip.")

    p_img = sub.add_parser("image", help="Generate or edit text-free keyframes or cover art backgrounds via `gemini-api image`.")
    p_img.add_argument("prompt", nargs="*", help="Image prompt (keep text-free for covers and keyframes).")
    p_img.add_argument("--prompt-file", help="Read prompt text from a UTF-8 file.")
    p_img.add_argument("--body", help="Advanced Interactions API JSON body string or @path/to/payload.json.")
    p_img.add_argument("--model", "-m", default=DEFAULT_IMAGE_MODEL, help=f"Image model (default: {DEFAULT_IMAGE_MODEL}).")
    p_img.add_argument("--aspect-ratio", default=DEFAULT_IMAGE_ASPECT_RATIO, help=f"Aspect ratio (default: {DEFAULT_IMAGE_ASPECT_RATIO}; e.g. 3:4, 4:3, 1:1, 16:9).")
    p_img.add_argument("--image-size", default=DEFAULT_IMAGE_SIZE, help=f"Output image size (default: {DEFAULT_IMAGE_SIZE}; 512, 1K, 2K, 4K).")
    p_img.add_argument("--output-mime-type", help="Output MIME type (e.g. image/jpeg).")
    p_img.add_argument("-i", "--input", action="append", default=[], help="Reference image path or files/<id> (repeatable).")
    p_img.add_argument("--no-auto-upload", dest="auto_upload", action="store_false", default=True, help="Disable auto-uploading >14 MB local inputs.")
    p_img.add_argument("--previous-interaction-id", help="Edit a prior image interaction conversationally.")
    p_img.add_argument("--no-store", action="store_true", help="Set store=false in the request body.")
    p_img.add_argument("--out", help="Output image path or directory.")
    p_img.add_argument("--shot-id", help="Episode shot/cover ID for ledger tracking.")
    p_img.add_argument("--ledger", help="Disk-backed JSON prompt ledger path to update.")
    p_img.add_argument("--receipt", help="Write JSON image receipt to a new file path (refuses overwrite).")
    p_img.add_argument("--dry-run", action="store_true", help="Validate and preview HTTP request offline.")

    p_mus = sub.add_parser("music", help="Generate an optional ducked BGM stem via `gemini-api music`.")
    p_mus.add_argument("prompt", nargs="*", help="Music prompt.")
    p_mus.add_argument("--prompt-file", help="Read prompt text from a UTF-8 file.")
    p_mus.add_argument("--body", help="Advanced JSON body string or @path/to/payload.json.")
    p_mus.add_argument("--model", "-m", default=DEFAULT_MUSIC_MODEL, help=f"Music model (default: {DEFAULT_MUSIC_MODEL}).")
    p_mus.add_argument("--out", help="Output audio path or directory.")
    p_mus.add_argument("--receipt", help="Write JSON music receipt to a new file path (refuses overwrite).")
    p_mus.add_argument("--dry-run", action="store_true", help="Validate and preview HTTP request offline.")
    p_mus.add_argument("--skip-probe", action="store_true", help="Skip ffprobe inspection.")

    p_tts = sub.add_parser("tts", help="Optional cloud TTS synthesis via `gemini-api tts` with episode-compatible receipt.")
    p_tts.add_argument("text", nargs="*", help="Inline text to speak (prefer --script-file for continuous whole-episode narration).")
    p_tts.add_argument("--script-file", "-f", help="Path to full UTF-8 narration script file.")
    p_tts.add_argument("--model", "-m", default=DEFAULT_TTS_MODEL, help=f"TTS model (default: {DEFAULT_TTS_MODEL}).")
    p_tts.add_argument("--voice", "-v", help="Prebuilt voice name or custom voice_<id>.")
    p_tts.add_argument("--style", help="Delivery direction (text is spoken verbatim).")
    p_tts.add_argument("--language", help="BCP-47 language hint (e.g. zh-CN or en-US).")
    p_tts.add_argument("--confirmation-reference", help="Confirmation reference stored in execution metadata.")
    p_tts.add_argument("--episode-dir", help="Optional episode root directory for relative cloud_evidence paths.")
    p_tts.add_argument("--out", help="Output WAV path or directory.")
    p_tts.add_argument("--receipt", help="Write check_episode.py-compatible generation record JSON (refuses overwrite).")
    p_tts.add_argument("--dry-run", action="store_true", help="Validate and preview HTTP request offline.")
    p_tts.add_argument("--skip-probe", action="store_true", help="Skip ffprobe inspection.")

    return parser


def main(argv: list[str] | None = None, *, runner: Any = subprocess.run) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "preflight": cmd_preflight,
        "models": cmd_models,
        "upload": cmd_upload,
        "video": cmd_video,
        "resume": cmd_resume,
        "image": cmd_image,
        "music": cmd_music,
        "tts": cmd_tts,
    }
    try:
        return dispatch[args.command](args, runner=runner)
    except (FileExistsError, FileNotFoundError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"Error: {redact_secrets(str(exc))}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
