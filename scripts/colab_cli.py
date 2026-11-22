#!/usr/bin/env python3
"""Safe non-interactive Google Colab CLI (`google-colab-cli`) helper for science-video-production.

Provides:
- `preflight`: read-only detection of `colab` CLI (native or WSL2), version and optional auth/usage checks.
- `sessions` / `status` / `usage` / `url` / `stop`: non-TTY session inspection and explicit teardown.
- `run-ephemeral`: bounded GPU Python job runner with minimal upload/download, SHA-256 receipts and guaranteed `colab stop`.
- `blender-render`: headless Linux Blender Cycles GPU offload using packed `.blend`, automatic OPTIX/CUDA selection,
  on-VM Rec.709 MP4 encoding (keeping raw PNG sequences off the wire), local SHA-256 verification and guaranteed teardown.

Never calls interactive subcommands (`repl`, bare `ssh`, `auth`, `drivemount`) and never prints or stores credentials.
Remote execution completion is technical evidence only (`complete_unreviewed`), never visual or scientific acceptance.
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
import tempfile
import time
from typing import Any

SOURCE_ID = "google-colab-cli"
SUPPORTED_GPUS = ("T4", "L4", "G4", "A100", "H100")
NON_RT_DATACENTER_GPUS = {"A100", "H100", "T4"}
DEFAULT_BLENDER_LINUX_URL = "https://download.blender.org/release/Blender4.5/blender-4.5.10-linux-x64.tar.xz"
SESSION_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SECRET_PATTERNS = (
    re.compile(r"(Bearer\s+)[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"\bya29\.[A-Za-z0-9._-]{16,}\b"),
    re.compile(r"\b1//[A-Za-z0-9._-]{16,}\b"),
    re.compile(r"([?&](?:access_token|token|code)=)[^&\s]+", re.IGNORECASE),
)


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


def windows_to_wsl_path(raw: str | Path) -> str:
    text = str(Path(raw).resolve())
    m = re.match(r"^([A-Za-z]):[\\/](.*)$", text)
    if not m:
        return text.replace("\\", "/")
    drive = m.group(1).lower()
    rest = m.group(2).replace("\\", "/")
    return f"/mnt/{drive}/{rest}"


def validate_session_name(name: str) -> str:
    cleaned = name.strip()
    if not SESSION_NAME_RE.fullmatch(cleaned):
        raise ValueError(
            f"Invalid session name {name!r}: use 1-64 ASCII letters, digits, '.', '_' or '-' starting with alphanumeric."
        )
    return cleaned


def normalize_gpu(gpu: str | None) -> str | None:
    if gpu is None:
        return None
    val = gpu.strip().upper()
    if val not in SUPPORTED_GPUS:
        raise ValueError(f"Unsupported GPU {gpu!r}; expected one of: {', '.join(SUPPORTED_GPUS)}")
    return val


def choose_cycles_backend(gpu: str, requested: str) -> str:
    mode = requested.strip().upper()
    if mode in ("OPTIX", "CUDA"):
        return mode
    if mode != "AUTO":
        raise ValueError(f"Unsupported Cycles backend {requested!r}; expected auto, OPTIX or CUDA")
    return "CUDA" if gpu.upper() in NON_RT_DATACENTER_GPUS else "OPTIX"


def parse_transfer_spec(spec: str, *, direction: str) -> tuple[str, str]:
    """Parse LOCAL:REMOTE (upload) or REMOTE:LOCAL (download), preserving Windows drive letters."""
    if direction == "upload":
        # Windows local path may start with "C:\" or "C:/"; split on the last ":" before remote POSIX path.
        m = re.match(r"^([A-Za-z]:[\\/][^:]+|[^:]+):(\/.+|[^:]+)$", spec.strip())
    else:
        # Remote POSIX path first, then local path (which may have Windows drive letter).
        m = re.match(r"^([^:]+):([A-Za-z]:[\\/].+|.+)$", spec.strip())
    if not m:
        example = "local.blend:/content/local.blend" if direction == "upload" else "/content/out.mp4:./out.mp4"
        raise ValueError(f"Invalid --{direction} spec {spec!r}; expected format like {example!r}")
    return m.group(1).strip(), m.group(2).strip()


def resolve_transport(
    *,
    transport: str = "auto",
    colab_bin: str | None = None,
    wsl_distro: str | None = None,
    runner=subprocess.run,
) -> dict[str, Any]:
    """Locate an executable `colab` CLI natively or inside WSL2 without modifying host state."""
    mode = transport.strip().lower()
    if mode not in ("auto", "native", "wsl"):
        raise ValueError(f"Invalid --transport {transport!r}; expected auto, native or wsl")

    is_windows = platform.system().lower() == "windows"
    candidates: list[str] = []
    if colab_bin:
        candidates.append(colab_bin)
    else:
        found = shutil.which("colab")
        if found:
            candidates.append(found)
        for rel in (".local/bin/colab.exe", ".local/bin/colab"):
            p = Path.home() / rel
            if p.is_file():
                candidates.append(str(p))

    if mode in ("auto", "native"):
        for cand in candidates:
            if Path(cand).is_file() or shutil.which(cand):
                return {
                    "available": True,
                    "transport": "native",
                    "prefix": [cand],
                    "host_os": platform.system(),
                    "wsl_distro": None,
                }
        if mode == "native":
            return {
                "available": False,
                "transport": "unavailable",
                "prefix": [],
                "host_os": platform.system(),
                "wsl_distro": None,
                "reason": "colab binary not found on native PATH",
            }

    if mode in ("auto", "wsl") and is_windows:
        wsl_exe = shutil.which("wsl")
        if wsl_exe:
            probe_cmd = [wsl_exe]
            if wsl_distro:
                probe_cmd += ["-d", wsl_distro]
            probe_cmd += ["--", "sh", "-lc", "command -v colab"]
            try:
                proc = runner(
                    probe_cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=10,
                    check=False,
                )
            except (OSError, subprocess.SubprocessError) as exc:
                return {
                    "available": False,
                    "transport": "unavailable",
                    "prefix": [],
                    "host_os": platform.system(),
                    "wsl_distro": wsl_distro,
                    "reason": f"WSL probe failed: {exc}",
                }
            raw_out = proc.stdout or b""
            if isinstance(raw_out, bytes):
                decoded = raw_out.decode("utf-8", errors="replace").replace("\x00", "")
            else:
                decoded = str(raw_out).replace("\x00", "")
            remote_bin = [line.strip() for line in decoded.splitlines() if line.strip()]
            if proc.returncode == 0 and remote_bin:
                prefix = [wsl_exe] + (["-d", wsl_distro] if wsl_distro else []) + ["--", remote_bin[0].strip()]
                return {
                    "available": True,
                    "transport": "wsl",
                    "prefix": prefix,
                    "host_os": platform.system(),
                    "wsl_distro": wsl_distro,
                }
            return {
                "available": False,
                "transport": "unavailable",
                "prefix": [],
                "host_os": platform.system(),
                "wsl_distro": wsl_distro,
                "reason": "colab binary not installed in WSL (or WSL distro not installed)",
            }

    return {
        "available": False,
        "transport": "unavailable",
        "prefix": [],
        "host_os": platform.system(),
        "wsl_distro": wsl_distro,
        "reason": "colab CLI not found natively and WSL unavailable",
    }


def _host_path_for_cli(path: str | Path, transport_name: str) -> str:
    if transport_name == "wsl":
        return windows_to_wsl_path(path)
    return str(Path(path).resolve())


def build_colab_cmd(
    transport_info: dict[str, Any],
    subargs: list[str],
    *,
    auth: str | None = None,
    config_path: str | None = None,
    client_oauth_config: str | None = None,
) -> list[str]:
    if not transport_info.get("available"):
        raise RuntimeError(transport_info.get("reason") or "colab CLI is unavailable")
    cmd = list(transport_info["prefix"])
    tname = transport_info["transport"]
    if auth:
        cmd.append(f"--auth={auth}")
    if config_path:
        cmd += ["--config", _host_path_for_cli(config_path, tname)]
    if client_oauth_config:
        cmd += ["--client-oauth-config", _host_path_for_cli(client_oauth_config, tname)]
    cmd.extend(subargs)
    return cmd


def _run_cli(
    cmd: list[str],
    *,
    timeout: int = 300,
    runner=subprocess.run,
) -> dict[str, Any]:
    t0 = time.monotonic()
    try:
        proc = runner(
            cmd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
        return {
            "returncode": proc.returncode,
            "stdout": redact_secrets(proc.stdout or ""),
            "stderr": redact_secrets(proc.stderr or ""),
            "elapsed_s": round(time.monotonic() - t0, 3),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "returncode": 124,
            "stdout": redact_secrets((exc.stdout or "") if isinstance(exc.stdout, str) else ""),
            "stderr": f"Command timed out after {timeout}s",
            "elapsed_s": round(time.monotonic() - t0, 3),
        }
    except OSError as exc:
        return {
            "returncode": 127,
            "stdout": "",
            "stderr": redact_secrets(str(exc)),
            "elapsed_s": round(time.monotonic() - t0, 3),
        }


def _write_receipt(path: Path | None, payload: dict[str, Any], *, overwrite: bool = False) -> None:
    if path is None:
        return
    if path.exists() and not overwrite:
        raise FileExistsError(f"Receipt file already exists (use a new receipt filename): {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _extract_common(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "auth": getattr(args, "auth", None),
        "config_path": getattr(args, "config", None),
        "client_oauth_config": getattr(args, "client_oauth_config", None),
    }


def cmd_preflight(args: argparse.Namespace, *, runner=subprocess.run) -> int:
    info = resolve_transport(
        transport=args.transport,
        colab_bin=args.colab_bin,
        wsl_distro=args.wsl_distro,
        runner=runner,
    )
    common = _extract_common(args)
    result: dict[str, Any] = {
        "schema_version": 1,
        "source_id": SOURCE_ID,
        "checked_at": _now_iso(),
        "host_os": info["host_os"],
        "available": info["available"],
        "transport": info["transport"],
        "wsl_distro": info.get("wsl_distro"),
        "platform_note": (
            "Upstream google-colab-cli README officially declares Linux and macOS support "
            "(colab update --install is Linux/macOS-only); verify native Windows or WSL2 execution "
            "before production routing, or fall back to authenticated HTTPS tunnel / local GPU."
        ),
        "version": None,
        "auth_strategy": common["auth"] or "default(oauth2)",
        "auth_checked": False,
        "auth_ok": None,
        "sessions_output": None,
        "usage_output": None,
        "fallback_modes": ["https_tunnel", "local_gpu"],
        "status": "unavailable",
        "reason": info.get("reason"),
    }

    if not info["available"]:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    ver_cmd = build_colab_cmd(info, ["version"], **common)
    ver_res = _run_cli(ver_cmd, timeout=20, runner=runner)
    if ver_res["returncode"] != 0:
        result["status"] = "cli_error"
        result["reason"] = (ver_res["stderr"] or ver_res["stdout"]).strip() or f"exit {ver_res['returncode']}"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    result["version"] = ver_res["stdout"].strip()

    if not args.check_auth:
        result["status"] = "cli_installed_auth_unchecked"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    result["auth_checked"] = True
    sess_cmd = build_colab_cmd(info, ["sessions"], **common)
    sess_res = _run_cli(sess_cmd, timeout=30, runner=runner)
    result["sessions_output"] = sess_res["stdout"].strip()
    if sess_res["returncode"] != 0:
        result["auth_ok"] = False
        result["status"] = "auth_failed"
        result["reason"] = (
            (sess_res["stderr"] or sess_res["stdout"]).strip()
            or "colab sessions failed; verify --auth=adc scopes or cached oauth2 keyring credentials via `colab whoami`"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1

    usage_cmd = build_colab_cmd(info, ["usage"], **common)
    usage_res = _run_cli(usage_cmd, timeout=30, runner=runner)
    result["usage_output"] = usage_res["stdout"].strip() if usage_res["returncode"] == 0 else None
    result["auth_ok"] = True
    result["status"] = "ready"
    result["reason"] = None
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_simple_action(args: argparse.Namespace, *, runner=subprocess.run) -> int:
    info = resolve_transport(
        transport=args.transport,
        colab_bin=args.colab_bin,
        wsl_distro=args.wsl_distro,
        runner=runner,
    )
    if not info["available"]:
        print(json.dumps({"status": "unavailable", "reason": info.get("reason")}, ensure_ascii=False), file=sys.stderr)
        return 1

    action = args.cmd
    subargs = [action]
    if action in ("status", "url", "stop"):
        if args.session:
            subargs += ["-s", validate_session_name(args.session)]
        elif action == "stop":
            print("`stop` requires explicit `-s <session>` to avoid terminating unrelated runtimes.", file=sys.stderr)
            return 2

    cmd = build_colab_cmd(info, subargs, **_extract_common(args))
    res = _run_cli(cmd, timeout=60, runner=runner)
    if res["stdout"]:
        sys.stdout.write(res["stdout"])
    if res["stderr"]:
        sys.stderr.write(res["stderr"])
    return 0 if res["returncode"] == 0 else 1


def _build_remote_blender_driver(
    *,
    remote_blend: str,
    remote_mp4: str,
    remote_meta: str,
    frame_start: int,
    frame_end: int,
    samples: int,
    width: int,
    height: int,
    fps: int,
    crf: int,
    shards: int,
    backend: str,
    blender_url: str,
) -> str:
    cfg = {
        "remote_blend": remote_blend,
        "remote_mp4": remote_mp4,
        "remote_meta": remote_meta,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "samples": samples,
        "width": width,
        "height": height,
        "fps": fps,
        "crf": crf,
        "shards": shards,
        "backend": backend,
        "blender_url": blender_url,
    }
    return f"""#!/usr/bin/env python3
import json, pathlib, shutil, subprocess, sys, time

CFG = {json.dumps(cfg, ensure_ascii=False)}
BLENDER_DIR = pathlib.Path("/content/blender")
BLENDER_BIN = BLENDER_DIR / "blender"
WORK_DIR = pathlib.Path("/content/_sv_blender_work")
FRAMES_DIR = WORK_DIR / "frames"
DRIVER_PY = WORK_DIR / "_cycles_shard.py"

SHARD_CODE = r'''
import argparse, pathlib, sys, bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--out-dir", required=True)
p.add_argument("--frame-start", type=int, required=True)
p.add_argument("--frame-end", type=int, required=True)
p.add_argument("--frame-step", type=int, default=1)
p.add_argument("--samples", type=int, required=True)
p.add_argument("--width", type=int, required=True)
p.add_argument("--height", type=int, required=True)
p.add_argument("--backend", required=True)
a = p.parse_args(argv)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.use_persistent_data = True
scene.cycles.samples = a.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.025
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
if hasattr(scene.cycles, "denoising_use_gpu"):
    scene.cycles.denoising_use_gpu = True
scene.render.resolution_x = a.width
scene.render.resolution_y = a.height
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "8"

prefs = bpy.context.preferences.addons["cycles"].preferences
order = ("OPTIX", "CUDA") if a.backend == "OPTIX" else ("CUDA",)
selected = "CPU"
for candidate in order:
    try:
        prefs.compute_device_type = candidate
        prefs.get_devices()
        found = False
        for dev in prefs.devices:
            if dev.type == candidate:
                dev.use = True
                found = True
            else:
                dev.use = False
        if found:
            selected = candidate
            break
    except Exception:
        continue
if selected == "CPU":
    raise RuntimeError("No CUDA/OPTIX Cycles GPU device found on Colab runtime")
scene.cycles.device = "GPU"
print(f"[CYCLES] backend={{selected}} frames={{a.frame_start}}..{{a.frame_end}} step={{a.frame_step}} samples={{a.samples}}", flush=True)

out_dir = pathlib.Path(a.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)
for fnum in range(a.frame_start, a.frame_end + 1, max(1, a.frame_step)):
    dst = out_dir / f"frame_{{fnum:04d}}.png"
    scene.frame_set(fnum)
    scene.render.filepath = str(dst)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError as exc:
        if selected == "OPTIX":
            print(f"[CYCLES] OPTIX failed ({{exc}}); switching to CUDA", flush=True)
            prefs.compute_device_type = "CUDA"
            prefs.get_devices()
            for dev in prefs.devices:
                dev.use = (dev.type == "CUDA")
            selected = "CUDA"
            bpy.ops.render.render(write_still=True)
        else:
            raise
'''

t0 = time.monotonic()
gpu_info = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
    capture_output=True, text=True, check=False,
).stdout.strip()

if not BLENDER_BIN.is_file():
    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-fsSL", CFG["blender_url"], "-o", "/tmp/blender.tar.xz"], check=True)
    subprocess.run(["tar", "-xf", "/tmp/blender.tar.xz", "-C", str(BLENDER_DIR), "--strip-components=1"], check=True)
    pathlib.Path("/tmp/blender.tar.xz").unlink(missing_ok=True)

if shutil.which("ffmpeg") is None:
    subprocess.run(["apt-get", "-qq", "update"], check=True)
    subprocess.run(["apt-get", "-qq", "install", "-y", "ffmpeg"], check=True)

blender_version = subprocess.check_output([str(BLENDER_BIN), "--version"], text=True).splitlines()[0].strip()

if FRAMES_DIR.exists():
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
DRIVER_PY.write_text(SHARD_CODE, encoding="utf-8")

f0, f1 = int(CFG["frame_start"]), int(CFG["frame_end"])
total_frames = f1 - f0 + 1
n_shards = max(1, min(int(CFG["shards"]), total_frames))

procs = []
for si in range(n_shards):
    cmd = [
        str(BLENDER_BIN), "-b", CFG["remote_blend"], "-P", str(DRIVER_PY), "--",
        "--out-dir", str(FRAMES_DIR),
        "--frame-start", str(f0 + si),
        "--frame-end", str(f1),
        "--frame-step", str(n_shards),
        "--samples", str(CFG["samples"]),
        "--width", str(CFG["width"]),
        "--height", str(CFG["height"]),
        "--backend", CFG["backend"],
    ]
    procs.append(subprocess.Popen(cmd))

rcs = [p.wait() for p in procs]
rendered = sum(1 for p in FRAMES_DIR.glob("frame_*.png") if p.stat().st_size > 1024)
if any(rc != 0 for rc in rcs) or rendered != total_frames:
    raise RuntimeError(f"Blender render failed: returncodes={{rcs}}, rendered={{rendered}}/{{total_frames}}")

mp4_path = pathlib.Path(CFG["remote_mp4"])
mp4_path.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(
    [
        "ffmpeg", "-y",
        "-framerate", str(CFG["fps"]),
        "-start_number", str(f0),
        "-i", str(FRAMES_DIR / "frame_%04d.png"),
        "-frames:v", str(total_frames),
        "-r", str(CFG["fps"]),
        "-c:v", "libx264", "-preset", "fast", "-crf", str(CFG["crf"]),
        "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-movflags", "+faststart",
        str(mp4_path),
    ],
    check=True,
)
shutil.rmtree(FRAMES_DIR, ignore_errors=True)
meta = {{
    "gpu": gpu_info,
    "blender_version": blender_version,
    "requested_backend": CFG["backend"],
    "frame_start": f0,
    "frame_end": f1,
    "total_frames": total_frames,
    "width": CFG["width"],
    "height": CFG["height"],
    "fps": CFG["fps"],
    "samples": CFG["samples"],
    "shards": n_shards,
    "mp4_bytes": mp4_path.stat().st_size,
    "remote_elapsed_s": round(time.monotonic() - t0, 2),
}}
pathlib.Path(CFG["remote_meta"]).write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("COLAB_BLENDER_META=" + json.dumps(meta, ensure_ascii=False))
"""


def _execute_ephemeral_workflow(
    *,
    info: dict[str, Any],
    common: dict[str, Any],
    session: str,
    gpu: str | None,
    high_mem: bool,
    reuse_session: bool,
    keep_session: bool,
    uploads: list[tuple[Path, str]],
    script_path: Path,
    downloads: list[tuple[str, Path]],
    env_pairs: list[str],
    exec_timeout: int,
    dry_run: bool,
    receipt_path: Path | None,
    overwrite_receipt: bool,
    extra_meta: dict[str, Any] | None = None,
    runner=subprocess.run,
) -> tuple[int, dict[str, Any]]:
    if receipt_path is not None and receipt_path.exists() and not overwrite_receipt:
        raise FileExistsError(f"Receipt file already exists (use a new receipt filename): {receipt_path}")

    script_resolved = script_path.resolve()
    if not script_resolved.is_file():
        raise FileNotFoundError(f"Script file not found: {script_resolved}")

    upload_records: list[dict[str, Any]] = []
    total_upload_bytes = script_resolved.stat().st_size
    for local_p, remote_p in uploads:
        resolved = local_p.resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Upload input not found: {resolved}")
        sz = resolved.stat().st_size
        total_upload_bytes += sz
        upload_records.append({
            "local": str(resolved),
            "remote": remote_p,
            "bytes": sz,
            "sha256": sha256_file(resolved),
        })

    env_keys: list[str] = []
    for pair in env_pairs:
        if "=" not in pair or not pair.split("=", 1)[0].strip():
            raise ValueError(f"Invalid --env value (expected KEY=VALUE): {pair.split('=', 1)[0]!r}")
        env_keys.append(pair.split("=", 1)[0].strip())

    tname = info["transport"]
    new_args = ["new", "-s", session]
    if gpu:
        new_args += ["--gpu", gpu]
    if high_mem:
        new_args.append("--high-mem")

    exec_args = ["exec", "-s", session, "-f", _host_path_for_cli(script_resolved, tname)]
    for pair in env_pairs:
        exec_args += ["--env", pair]

    planned_steps: list[list[str]] = []
    if not reuse_session:
        planned_steps.append(build_colab_cmd(info, new_args, **common))
    for local_p, remote_p in uploads:
        planned_steps.append(build_colab_cmd(info, ["upload", "-s", session, _host_path_for_cli(local_p, tname), remote_p], **common))
    # Redact --env values in plan summary
    safe_exec_args = ["exec", "-s", session, "-f", _host_path_for_cli(script_resolved, tname)]
    for k in env_keys:
        safe_exec_args += ["--env", f"{k}=[REDACTED]"]
    planned_steps.append(build_colab_cmd(info, safe_exec_args, **common))
    for remote_p, local_p in downloads:
        planned_steps.append(build_colab_cmd(info, ["download", "-s", session, remote_p, _host_path_for_cli(local_p, tname)], **common))
    if not keep_session and not reuse_session:
        planned_steps.append(build_colab_cmd(info, ["stop", "-s", session], **common))

    receipt: dict[str, Any] = {
        "schema_version": 1,
        "source_id": SOURCE_ID,
        "usage_mode": "runtime",
        "recorded_at": _now_iso(),
        "dry_run": dry_run,
        "compute_node": {
            "selected": "colab_cli",
            "access_mode": "google_colab_cli",
            "transport": tname,
            "session": session,
            "requested_gpu": gpu or "CPU",
            "high_mem": high_mem,
            "reuse_session": reuse_session,
            "keep_session": keep_session,
        },
        "script": {
            "local": str(script_resolved),
            "bytes": script_resolved.stat().st_size,
            "sha256": sha256_file(script_resolved),
        },
        "env_keys": env_keys,
        "uploads": upload_records,
        "total_upload_bytes": total_upload_bytes,
        "downloads": [],
        "total_download_bytes": 0,
        "planned_commands": planned_steps,
        "timings_s": {},
        "teardown_attempted": False,
        "teardown_ok": None,
        "status": "dry_run" if dry_run else "pending",
        "review_status": "complete_unreviewed",
        "error": None,
    }
    if extra_meta:
        receipt.update(extra_meta)

    if dry_run:
        _write_receipt(receipt_path, receipt, overwrite=overwrite_receipt)
        return 0, receipt

    t_total = time.monotonic()
    allocated_by_us = False
    exit_code = 0
    try:
        if not reuse_session:
            prov_res = _run_cli(build_colab_cmd(info, new_args, **common), timeout=300, runner=runner)
            receipt["timings_s"]["provision"] = prov_res["elapsed_s"]
            if prov_res["returncode"] != 0:
                receipt["status"] = "provision_failed"
                receipt["error"] = (prov_res["stderr"] or prov_res["stdout"]).strip() or f"colab new exited {prov_res['returncode']}"
                exit_code = 1
                return exit_code, receipt
            allocated_by_us = True

        t_up = 0.0
        for local_p, remote_p in uploads:
            up_cmd = build_colab_cmd(info, ["upload", "-s", session, _host_path_for_cli(local_p, tname), remote_p], **common)
            up_res = _run_cli(up_cmd, timeout=600, runner=runner)
            t_up += up_res["elapsed_s"]
            if up_res["returncode"] != 0:
                receipt["timings_s"]["upload"] = round(t_up, 3)
                receipt["status"] = "upload_failed"
                receipt["error"] = (up_res["stderr"] or up_res["stdout"]).strip() or f"colab upload failed for {local_p}"
                exit_code = 1
                return exit_code, receipt
        receipt["timings_s"]["upload"] = round(t_up, 3)

        exec_cmd = build_colab_cmd(info, exec_args, **common)
        exec_res = _run_cli(exec_cmd, timeout=exec_timeout, runner=runner)
        receipt["timings_s"]["execute"] = exec_res["elapsed_s"]
        receipt["exec_returncode"] = exec_res["returncode"]
        receipt["exec_stdout_tail"] = exec_res["stdout"][-2000:]
        receipt["exec_stderr_tail"] = exec_res["stderr"][-1000:]
        if exec_res["returncode"] != 0:
            receipt["status"] = "exec_failed"
            receipt["error"] = (exec_res["stderr"] or exec_res["stdout"]).strip()[-500:] or f"colab exec exited {exec_res['returncode']}"
            exit_code = 1
            return exit_code, receipt

        t_dl = 0.0
        dl_records: list[dict[str, Any]] = []
        total_dl_bytes = 0
        for remote_p, local_p in downloads:
            local_resolved = local_p.resolve()
            local_resolved.parent.mkdir(parents=True, exist_ok=True)
            dl_cmd = build_colab_cmd(info, ["download", "-s", session, remote_p, _host_path_for_cli(local_resolved, tname)], **common)
            dl_res = _run_cli(dl_cmd, timeout=600, runner=runner)
            t_dl += dl_res["elapsed_s"]
            if dl_res["returncode"] != 0 or not local_resolved.is_file():
                receipt["timings_s"]["download"] = round(t_dl, 3)
                receipt["status"] = "download_failed"
                receipt["error"] = (dl_res["stderr"] or dl_res["stdout"]).strip() or f"colab download failed for {remote_p}"
                exit_code = 1
                return exit_code, receipt
            sz = local_resolved.stat().st_size
            total_dl_bytes += sz
            dl_records.append({
                "remote": remote_p,
                "local": str(local_resolved),
                "bytes": sz,
                "sha256": sha256_file(local_resolved),
            })
        receipt["timings_s"]["download"] = round(t_dl, 3)
        receipt["downloads"] = dl_records
        receipt["total_download_bytes"] = total_dl_bytes
        receipt["status"] = "completed"
        return 0, receipt
    finally:
        if allocated_by_us and not keep_session:
            receipt["teardown_attempted"] = True
            stop_cmd = build_colab_cmd(info, ["stop", "-s", session], **common)
            stop_res = _run_cli(stop_cmd, timeout=60, runner=runner)
            receipt["timings_s"]["teardown"] = stop_res["elapsed_s"]
            receipt["teardown_ok"] = stop_res["returncode"] == 0
            if not receipt["teardown_ok"]:
                receipt["teardown_error"] = (stop_res["stderr"] or stop_res["stdout"]).strip()
        receipt["timings_s"]["total"] = round(time.monotonic() - t_total, 3)
        _write_receipt(receipt_path, receipt, overwrite=overwrite_receipt)


def cmd_run_ephemeral(args: argparse.Namespace, *, runner=subprocess.run) -> int:
    try:
        session = validate_session_name(args.session)
        gpu = None if args.cpu else normalize_gpu(args.gpu)
        uploads = [(Path(loc), rem) for loc, rem in (parse_transfer_spec(s, direction="upload") for s in (args.upload or []))]
        downloads = [(rem, Path(loc)) for rem, loc in (parse_transfer_spec(s, direction="download") for s in (args.download or []))]
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    info = resolve_transport(
        transport=args.transport,
        colab_bin=args.colab_bin,
        wsl_distro=args.wsl_distro,
        runner=runner,
    )
    if not info["available"]:
        if args.dry_run:
            info = {"available": True, "transport": "dry_run_placeholder", "prefix": ["colab"], "host_os": platform.system()}
        else:
            print(json.dumps({"status": "unavailable", "reason": info.get("reason")}, ensure_ascii=False), file=sys.stderr)
            return 1

    try:
        rc, receipt = _execute_ephemeral_workflow(
            info=info,
            common=_extract_common(args),
            session=session,
            gpu=gpu,
            high_mem=args.high_mem,
            reuse_session=args.reuse_session,
            keep_session=args.keep,
            uploads=uploads,
            script_path=Path(args.script),
            downloads=downloads,
            env_pairs=list(args.env or []),
            exec_timeout=args.timeout,
            dry_run=args.dry_run,
            receipt_path=Path(args.receipt) if args.receipt else None,
            overwrite_receipt=args.overwrite_receipt,
            runner=runner,
        )
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return rc


def cmd_blender_render(args: argparse.Namespace, *, runner=subprocess.run) -> int:
    try:
        session = validate_session_name(args.session)
        gpu = normalize_gpu(args.gpu)
        assert gpu is not None
        backend = choose_cycles_backend(gpu, args.backend)
        if args.frame_start > args.frame_end:
            raise ValueError(f"--frame-start ({args.frame_start}) must be <= --frame-end ({args.frame_end})")
        if min(args.width, args.height) < 1080 and not args.allow_proxy:
            raise ValueError(
                f"Formal render dimensions {args.width}x{args.height} have short edge < 1080; "
                "pass --allow-proxy only for explicitly internal motion previews."
            )
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    blend_path = Path(args.blend).resolve()
    if not blend_path.is_file():
        print(f"Input error: packed .blend not found: {blend_path}", file=sys.stderr)
        return 2
    receipt_path = Path(args.receipt).resolve() if args.receipt else None
    if receipt_path is not None and receipt_path.exists() and not args.overwrite_receipt:
        print(f"Input error: Receipt file already exists (use a new receipt filename): {receipt_path}", file=sys.stderr)
        return 2

    info = resolve_transport(
        transport=args.transport,
        colab_bin=args.colab_bin,
        wsl_distro=args.wsl_distro,
        runner=runner,
    )
    if not info["available"]:
        if args.dry_run:
            info = {"available": True, "transport": "dry_run_placeholder", "prefix": ["colab"], "host_os": platform.system()}
        else:
            print(json.dumps({"status": "unavailable", "reason": info.get("reason")}, ensure_ascii=False), file=sys.stderr)
            return 1

    remote_blend = f"/content/{blend_path.name}"
    remote_mp4 = f"/content/{session}_render.mp4"
    remote_meta = f"/content/{session}_meta.json"
    output_mp4 = Path(args.output).resolve()

    driver_src = _build_remote_blender_driver(
        remote_blend=remote_blend,
        remote_mp4=remote_mp4,
        remote_meta=remote_meta,
        frame_start=args.frame_start,
        frame_end=args.frame_end,
        samples=args.samples,
        width=args.width,
        height=args.height,
        fps=args.fps,
        crf=args.crf,
        shards=args.shards,
        backend=backend,
        blender_url=args.blender_url,
    )

    with tempfile.TemporaryDirectory(prefix="sv-colab-blender-") as tmp_dir:
        driver_file = Path(tmp_dir) / f"{session}_driver.py"
        driver_file.write_text(driver_src, encoding="utf-8")
        meta_local = Path(tmp_dir) / f"{session}_meta.json"
        try:
            rc, receipt = _execute_ephemeral_workflow(
                info=info,
                common=_extract_common(args),
                session=session,
                gpu=gpu,
                high_mem=args.high_mem,
                reuse_session=args.reuse_session,
                keep_session=args.keep,
                uploads=[(blend_path, remote_blend)],
                script_path=driver_file,
                downloads=[(remote_mp4, output_mp4), (remote_meta, meta_local)],
                env_pairs=[],
                exec_timeout=args.timeout,
                dry_run=args.dry_run,
                receipt_path=None,
                overwrite_receipt=args.overwrite_receipt,
                extra_meta={
                    "blender_render": {
                        "blend": str(blend_path),
                        "frame_start": args.frame_start,
                        "frame_end": args.frame_end,
                        "width": args.width,
                        "height": args.height,
                        "fps": args.fps,
                        "samples": args.samples,
                        "shards": args.shards,
                        "selected_backend": backend,
                        "proxy_mode": bool(args.allow_proxy),
                    }
                },
                runner=runner,
            )
            if meta_local.is_file():
                try:
                    receipt["remote_blender_meta"] = json.loads(meta_local.read_text(encoding="utf-8"))
                except ValueError:
                    pass
            _write_receipt(
                Path(args.receipt) if args.receipt else None,
                receipt,
                overwrite=args.overwrite_receipt,
            )
        except (FileNotFoundError, FileExistsError, ValueError) as exc:
            print(f"Input error: {exc}", file=sys.stderr)
            return 2

    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--transport", choices=("auto", "native", "wsl"), default="auto", help="CLI transport mode")
    ap.add_argument("--colab-bin", help="Explicit path to colab binary")
    ap.add_argument("--wsl-distro", help="Optional WSL distro name on Windows")
    ap.add_argument("--auth", choices=("oauth2", "adc"), help="Colab CLI global --auth provider")
    ap.add_argument("--config", help="Isolated session state JSON path passed to colab --config")
    ap.add_argument("--client-oauth-config", help="Custom OAuth client config JSON path")

    sub = ap.add_subparsers(dest="cmd", required=True)

    p_pre = sub.add_parser("preflight", help="Check colab CLI availability, version and optional auth/usage")
    p_pre.add_argument("--check-auth", action="store_true", help="Also run read-only `colab sessions` and `colab usage`")
    p_pre.set_defaults(func=cmd_preflight)

    for simple_cmd, help_text in (
        ("sessions", "List active backend Colab sessions"),
        ("status", "Show status for tracked Colab sessions"),
        ("usage", "Show account compute-unit balance and burn rate"),
        ("url", "Print browser URL attached to an existing CLI session"),
        ("stop", "Stop and release an active Colab VM session"),
    ):
        p = sub.add_parser(simple_cmd, help=help_text)
        if simple_cmd in ("status", "url", "stop"):
            p.add_argument("-s", "--session", help="Explicit Colab session name")
        p.set_defaults(func=cmd_simple_action)

    p_run = sub.add_parser("run-ephemeral", help="Provision, upload minimal inputs, execute script, download outputs and stop VM")
    p_run.add_argument("-s", "--session", required=True, help="Explicit unique session name")
    p_run.add_argument("--script", required=True, help="Local Python script (.py) or notebook (.ipynb) to run")
    p_run.add_argument("--gpu", default="A100", help="Colab GPU accelerator (T4, L4, G4, A100, H100)")
    p_run.add_argument("--cpu", action="store_true", help="Allocate CPU-only runtime instead of GPU")
    p_run.add_argument("--high-mem", action="store_true", help="Request high-RAM machine shape where supported")
    p_run.add_argument("--upload", action="append", default=[], help="Repeatable LOCAL:REMOTE file upload")
    p_run.add_argument("--download", action="append", default=[], help="Repeatable REMOTE:LOCAL file download")
    p_run.add_argument("--env", action="append", default=[], help="Repeatable KEY=VALUE passed to colab exec")
    p_run.add_argument("--reuse-session", action="store_true", help="Run on an existing session without new/stop")
    p_run.add_argument("--keep", action="store_true", help="Keep newly allocated session alive after completion")
    p_run.add_argument("--timeout", type=int, default=3600, help="Execution timeout in seconds")
    p_run.add_argument("--dry-run", action="store_true", help="Validate inputs, compute hashes and print command plan without calling colab")
    p_run.add_argument("--receipt", help="Write hash-bound JSON execution receipt to a new file")
    p_run.add_argument("--overwrite-receipt", action="store_true", help="Allow overwriting an existing receipt file")
    p_run.set_defaults(func=cmd_run_ephemeral)

    p_bl = sub.add_parser("blender-render", help="Headless packed-.blend Cycles GPU render + on-VM MP4 encode + teardown")
    p_bl.add_argument("-s", "--session", required=True, help="Explicit unique session name")
    p_bl.add_argument("--blend", required=True, help="Self-contained packed .blend file to upload")
    p_bl.add_argument("--frame-start", type=int, required=True, help="First native Blender frame (inclusive)")
    p_bl.add_argument("--frame-end", type=int, required=True, help="Last native Blender frame (inclusive)")
    p_bl.add_argument("--output", required=True, help="Local destination .mp4 path")
    p_bl.add_argument("--gpu", default="A100", help="Colab GPU accelerator (T4, L4, G4, A100, H100)")
    p_bl.add_argument("--high-mem", action="store_true", help="Request high-RAM machine shape where supported")
    p_bl.add_argument("--backend", choices=("auto", "OPTIX", "CUDA"), default="auto", help="Cycles GPU backend (auto picks CUDA on A100/H100/T4, OPTIX on G4/L4)")
    p_bl.add_argument("--samples", type=int, default=64, help="Cycles samples per frame")
    p_bl.add_argument("--width", type=int, default=1920, help="Render width (default 1920)")
    p_bl.add_argument("--height", type=int, default=1080, help="Render height (default 1080)")
    p_bl.add_argument("--fps", type=int, default=30, help="Target CFR framerate")
    p_bl.add_argument("--crf", type=int, default=14, help="x264 CRF for intermediate transfer clip")
    p_bl.add_argument("--shards", type=int, default=2, help="Concurrent strided Blender GPU shards")
    p_bl.add_argument("--blender-url", default=DEFAULT_BLENDER_LINUX_URL, help="Official Linux Blender tarball URL")
    p_bl.add_argument("--allow-proxy", action="store_true", help="Allow short edge < 1080 for internal motion previews only")
    p_bl.add_argument("--reuse-session", action="store_true", help="Attach to an existing session without new/stop")
    p_bl.add_argument("--keep", action="store_true", help="Keep newly allocated session alive after completion")
    p_bl.add_argument("--timeout", type=int, default=7200, help="Execution timeout in seconds")
    p_bl.add_argument("--dry-run", action="store_true", help="Validate inputs and print plan without allocating a Colab VM")
    p_bl.add_argument("--receipt", help="Write hash-bound JSON execution receipt to a new file")
    p_bl.add_argument("--overwrite-receipt", action="store_true", help="Allow overwriting an existing receipt file")
    p_bl.set_defaults(func=cmd_blender_render)

    return ap


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
