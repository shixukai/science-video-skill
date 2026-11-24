#!/usr/bin/env python3
"""Safe non-interactive Google Colab CLI (`google-colab-cli`) helper for science-video-production.

Provides:
- `preflight`: read-only detection of `colab` CLI (native or WSL2), version and optional auth/usage checks.
- `sessions` / `status` / `usage` / `url` / `stop`: non-TTY session inspection and explicit teardown.
- `audit-blend`: local offline headless-Blender preflight audit against the `high_poly_industrial_v1` modeling standard
  (evaluated triangle density, non-uniform scales, flat-shaded curved meshes, bevel/modifier coverage, unbaked rigidbody
  world for strided shards, unpacked images and node-based materials) before spending Colab GPU units.
- `run-ephemeral`: bounded GPU Python job runner with minimal upload/download, SHA-256 receipts and guaranteed `colab stop`.
- `blender-stills`: headless Linux Blender Cycles GPU render of selected sparse hero/lookdev frames (`--frames`)
  from a packed `.blend` across strided GPU shards, bundled into a single tar download and unpacked into `--out-dir`
  so even 1080p lookdev stills run on Colab GPU instead of a slow local machine.
- `blender-render`: headless Linux Blender Cycles GPU offload using packed `.blend`, automatic OPTIX/CUDA selection,
  OIDN `RGB_ALBEDO_NORMAL` + `0.015` adaptive threshold for machined bevel fidelity, embedded modeling audit telemetry,
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
import tarfile
import tempfile
import time
from typing import Any

SOURCE_ID = "google-colab-cli"
SUPPORTED_GPUS = ("T4", "L4", "G4", "A100", "H100")
NON_RT_DATACENTER_GPUS = {"A100", "H100", "T4"}
DEFAULT_BLENDER_LINUX_URL = "https://download.blender.org/release/Blender4.5/blender-4.5.10-linux-x64.tar.xz"
MODELING_PROFILE_HIGH_POLY = "high_poly_industrial_v1"
MODELING_PROFILES = ("high_poly_industrial", "custom")
DEFAULT_MIN_SCENE_TRIANGLES = 25000
DEFAULT_ADAPTIVE_THRESHOLD = 0.015
DEFAULT_DENOISING_INPUT_PASSES = "RGB_ALBEDO_NORMAL"
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


def normalize_modeling_profile(profile: str) -> str:
    val = profile.strip().lower()
    if val in ("high_poly_industrial", "high_poly_industrial_v1"):
        return MODELING_PROFILE_HIGH_POLY
    if val == "custom":
        return "custom"
    raise ValueError(f"Unsupported --modeling-profile {profile!r}; expected high_poly_industrial or custom")


_INDUSTRIAL_AUDIT_BLENDER_CODE = r'''
import argparse, json, pathlib, sys, bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--out-json", required=True)
p.add_argument("--frame", type=int, default=None)
a = p.parse_args(argv)

scene = bpy.context.scene
if a.frame is not None:
    scene.frame_set(a.frame)

depsgraph = bpy.context.evaluated_depsgraph_get()
mesh_rows = []
total_polys = 0
total_tris = 0
non_uniform_scale = []
unapplied_uniform_scale = []
viewport_only_mats = []

for obj in scene.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    try:
        poly_count = len(mesh.polygons)
        tri_count = sum(max(1, len(poly.loop_indices) - 2) for poly in mesh.polygons)
        smooth_count = sum(1 for poly in mesh.polygons if poly.use_smooth)
        smooth_ratio = round(smooth_count / poly_count, 4) if poly_count else 1.0
    finally:
        obj_eval.to_mesh_clear()

    total_polys += poly_count
    total_tris += tri_count
    sx, sy, sz = (abs(float(v)) for v in obj.scale)
    is_non_uniform = max(abs(sx - sy), abs(sy - sz), abs(sx - sz)) > 1e-3
    is_unapplied_uniform = (not is_non_uniform) and (abs(sx - 1.0) > 1e-3)
    if is_non_uniform:
        non_uniform_scale.append({"name": obj.name, "scale": [round(sx, 4), round(sy, 4), round(sz, 4)]})
    elif is_unapplied_uniform:
        unapplied_uniform_scale.append({"name": obj.name, "scale": [round(sx, 4), round(sy, 4), round(sz, 4)]})

    mods = [m.type for m in obj.modifiers]
    mats = [slot.material for slot in obj.material_slots if slot.material is not None]
    has_node_mat = bool(mats) and all(bool(getattr(m, "use_nodes", False)) for m in mats)
    if not has_node_mat:
        viewport_only_mats.append(obj.name)

    mesh_rows.append({
        "name": obj.name,
        "polygon_count": poly_count,
        "triangle_count": tri_count,
        "smooth_face_ratio": smooth_ratio,
        "modifiers": mods,
        "has_bevel": "BEVEL" in mods,
        "has_subsurf": "SUBSURF" in mods,
        "has_weighted_normal": ("WEIGHTED_NORMAL" in mods) or ("EDGE_SPLIT" in mods),
        "has_solidify": "SOLIDIFY" in mods,
        "has_node_material": has_node_mat,
    })

mesh_rows.sort(key=lambda r: r["triangle_count"], reverse=True)
rbw = scene.rigidbody_world
has_active_rbw = bool(
    rbw is not None
    and bool(getattr(rbw, "enabled", True))
    and rbw.collection is not None
    and len(rbw.collection.objects) > 0
)
unpacked_images = [
    img.name
    for img in bpy.data.images
    if getattr(img, "source", "") in ("FILE", "SEQUENCE")
    and img.packed_file is None
    and bool(getattr(img, "filepath", "").strip())
]
missing_libs = [
    lib.filepath
    for lib in bpy.data.libraries
    if not pathlib.Path(bpy.path.abspath(lib.filepath)).exists()
]

vs = scene.view_settings
ds = scene.display_settings
cyc = getattr(scene, "cycles", None)

import math
from mathutils import Vector as _Vec
orig_frame = int(scene.frame_current)
f_start = int(scene.frame_start)
f_end = int(scene.frame_end)
fps_val = float(getattr(scene.render, "fps", 30) or 30) / float(getattr(scene.render, "fps_base", 1.0) or 1.0)
dur_s = max(0.0, (f_end - f_start + 1) / fps_val) if f_end >= f_start else 0.0
cam_cuts = []
prev_cam = None
prev_loc = None
prev_dir = None
prev_fr = f_start
step = max(1, int(round(fps_val / 6.0))) if dur_s > 0 else 1
sample_frames = list(range(f_start, f_end + 1, step))
if sample_frames and sample_frames[-1] != f_end:
    sample_frames.append(f_end)
for fr in sample_frames:
    scene.frame_set(fr)
    cam_obj = scene.camera
    if cam_obj is None:
        continue
    mw = cam_obj.matrix_world
    loc = mw.translation.copy()
    fwd = (mw.to_3x3() @ _Vec((0.0, 0.0, -1.0))).normalized()
    if prev_cam is not None:
        dt_s = max(1e-6, (fr - prev_fr) / fps_val)
        loc_jump = (loc - prev_loc).length
        dot = max(-1.0, min(1.0, prev_dir.dot(fwd)))
        ang_deg = math.degrees(math.acos(dot))
        if (cam_obj.name != prev_cam) or (loc_jump >= 0.35 and (loc_jump / dt_s) >= 2.0) or (ang_deg >= 22.0 and (ang_deg / dt_s) >= 120.0):
            cam_cuts.append(round((fr - f_start) / fps_val, 2))
    prev_cam, prev_loc, prev_dir, prev_fr = cam_obj.name, loc, fwd, fr
scene.frame_set(orig_frame)
cut_edges = [0.0] + cam_cuts + [round(dur_s, 2)]
longest_shot_s = round(max((b - a for a, b in zip(cut_edges, cut_edges[1:])), default=dur_s), 2)
camera_staging = {
    "fps": round(fps_val, 3),
    "frame_start": f_start,
    "frame_end": f_end,
    "duration_s": round(dur_s, 2),
    "hard_cut_count": len(cam_cuts),
    "hard_cut_times_s": cam_cuts,
    "longest_unbroken_shot_s": longest_shot_s,
}

stats = {
    "frame": orig_frame,
    "mesh_object_count": len(mesh_rows),
    "evaluated_polygon_count": total_polys,
    "evaluated_triangle_count": total_tris,
    "meshes": mesh_rows,
    "non_uniform_scale_objects": non_uniform_scale,
    "unapplied_uniform_scale_objects": unapplied_uniform_scale,
    "viewport_only_material_objects": viewport_only_mats,
    "has_active_rigidbody_world": has_active_rbw,
    "unpacked_external_images": unpacked_images,
    "missing_libraries": missing_libs,
    "camera_staging": camera_staging,
    "color_management": {
        "display_device": getattr(ds, "display_device", None),
        "view_transform": getattr(vs, "view_transform", None),
        "look": getattr(vs, "look", None),
        "exposure": round(float(getattr(vs, "exposure", 0.0)), 4),
        "gamma": round(float(getattr(vs, "gamma", 1.0)), 4),
    },
    "cycles_bounces": {
        "max_bounces": int(getattr(cyc, "max_bounces", 0)) if cyc else None,
        "glossy_bounces": int(getattr(cyc, "glossy_bounces", 0)) if cyc else None,
        "transmission_bounces": int(getattr(cyc, "transmission_bounces", 0)) if cyc else None,
        "diffuse_bounces": int(getattr(cyc, "diffuse_bounces", 0)) if cyc else None,
    },
}

out_path = pathlib.Path(a.out_json)
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
print("INDUSTRIAL_AUDIT_STATS=" + json.dumps(stats, ensure_ascii=False))
'''


def evaluate_industrial_audit(
    stats: dict[str, Any],
    *,
    modeling_profile: str = MODELING_PROFILE_HIGH_POLY,
    min_scene_triangles: int = DEFAULT_MIN_SCENE_TRIANGLES,
    shards: int = 1,
    require_packed: bool = True,
) -> dict[str, Any]:
    """Evaluate collected Blender scene stats against high_poly_industrial_v1 screening rules.

    Technical screening only; passing never certifies artistic, scientific, or motion quality.
    """
    profile = normalize_modeling_profile(modeling_profile)
    meshes = list(stats.get("meshes") or [])
    mesh_count = int(stats.get("mesh_object_count", len(meshes)))
    total_polys = int(stats.get("evaluated_polygon_count", sum(int(m.get("polygon_count", 0)) for m in meshes)))
    total_tris = int(stats.get("evaluated_triangle_count", sum(int(m.get("triangle_count", 0)) for m in meshes)))
    non_uniform = list(stats.get("non_uniform_scale_objects") or [])
    unapplied_uniform = list(stats.get("unapplied_uniform_scale_objects") or [])
    viewport_only = list(stats.get("viewport_only_material_objects") or [])
    has_rbw = bool(stats.get("has_active_rigidbody_world", False))
    unpacked_imgs = list(stats.get("unpacked_external_images") or [])
    missing_libs = list(stats.get("missing_libraries") or [])

    blocking: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    if mesh_count == 0:
        blocking.append({
            "code": "no_visible_meshes",
            "severity": "blocking",
            "message": "Scene contains zero render-visible mesh objects.",
        })
    if shards > 1 and has_rbw:
        blocking.append({
            "code": "unbaked_rigidbody_world",
            "severity": "blocking",
            "message": (
                f"Active rigidbody_world detected with shards={shards}; bake physics to quaternion F-curves "
                "and remove rigidbody_world before strided Colab multi-shard rendering to prevent frame divergence."
            ),
        })
    if require_packed and unpacked_imgs:
        blocking.append({
            "code": "unpacked_external_images",
            "severity": "blocking",
            "message": f"{len(unpacked_imgs)} external image(s) are not packed into the .blend (run bpy.ops.file.pack_all()).",
            "items": unpacked_imgs[:20],
        })
    if missing_libs:
        blocking.append({
            "code": "missing_linked_libraries",
            "severity": "blocking",
            "message": f"{len(missing_libs)} linked .blend library path(s) are missing.",
            "items": missing_libs[:20],
        })
    if viewport_only:
        blocking.append({
            "code": "viewport_only_materials",
            "severity": "blocking",
            "message": f"{len(viewport_only)} visible mesh object(s) lack active node-based materials.",
            "items": viewport_only[:20],
        })
    if non_uniform:
        blocking.append({
            "code": "non_uniform_scale",
            "severity": "blocking",
            "message": (
                f"{len(non_uniform)} visible mesh object(s) have unapplied non-uniform scale "
                "(skews chamfers, brushed anisotropy, normals and mechanical linkages)."
            ),
            "items": non_uniform[:20],
        })

    if unapplied_uniform:
        warnings.append({
            "code": "unapplied_uniform_scale",
            "severity": "warning",
            "message": f"{len(unapplied_uniform)} visible mesh object(s) have unapplied uniform scale != (1, 1, 1).",
            "items": unapplied_uniform[:20],
        })

    if profile == MODELING_PROFILE_HIGH_POLY:
        if total_tris < min_scene_triangles:
            warnings.append({
                "code": "low_poly_scene",
                "severity": "warning",
                "message": (
                    f"Visible evaluated triangle count ({total_tris}) is below the high-poly industrial screening floor "
                    f"({min_scene_triangles}); verify hero curved segments (>=64), machined bevels and multi-part detail."
                ),
            })
        flat_curved = [
            m["name"]
            for m in meshes
            if int(m.get("polygon_count", 0)) >= 24 and float(m.get("smooth_face_ratio", 1.0)) == 0.0
        ]
        if flat_curved:
            warnings.append({
                "code": "flat_shaded_curved_meshes",
                "severity": "warning",
                "message": (
                    f"{len(flat_curved)} visible mesh object(s) with >=24 faces are 100% flat-shaded "
                    "(use smooth shading paired with WeightedNormal or angle-controlled EdgeSplit)."
                ),
                "items": flat_curved[:20],
            })
        unbeveled_low = [
            m["name"]
            for m in meshes
            if int(m.get("polygon_count", 0)) >= 6
            and not bool(m.get("has_bevel", False))
            and not bool(m.get("has_subsurf", False))
            and int(m.get("triangle_count", 0)) < 2000
        ]
        if unbeveled_low:
            warnings.append({
                "code": "unbeveled_low_detail_meshes",
                "severity": "warning",
                "message": (
                    f"{len(unbeveled_low)} visible hard-surface mesh(es) lack Bevel/Subsurf modifiers and have <2000 triangles "
                    "(verify real physical chamfers/fillets rather than razor-sharp 90-degree primitives)."
                ),
                "items": unbeveled_low[:20],
            })
        missing_wn = [
            m["name"]
            for m in meshes
            if bool(m.get("has_bevel", False))
            and not bool(m.get("has_weighted_normal", False))
            and int(m.get("polygon_count", 0)) >= 12
        ]
        if missing_wn:
            warnings.append({
                "code": "beveled_without_weighted_normal",
                "severity": "warning",
                "message": (
                    f"{len(missing_wn)} beveled mesh(es) have no WeightedNormal or EdgeSplit modifier "
                    "(inspect flat CNC faces for pillow-shading distortion)."
                ),
                "items": missing_wn[:20],
            })

    cam_stage = stats.get("camera_staging") if isinstance(stats.get("camera_staging"), dict) else None
    if cam_stage is not None:
        cam_dur = float(cam_stage.get("duration_s") or 0.0)
        cam_cuts = int(cam_stage.get("hard_cut_count") or 0)
        cam_longest = float(cam_stage.get("longest_unbroken_shot_s") or 0.0)
        if cam_dur >= 25.0 and (cam_cuts < 3 or cam_longest > 14.0):
            warnings.append({
                "code": "hollow_single_stage_glide",
                "severity": "warning",
                "message": (
                    f"Timeline spans {cam_dur:.1f}s with only {cam_cuts} discrete camera cut(s) and a "
                    f"{cam_longest:.1f}s unbroken camera shot; avoid 'high-poly emptiness' from a 20-40s single-workbench "
                    "Bezier glide by staging >=3 distinct visual arenas/scales/comparisons with discrete hard cuts."
                ),
            })

    summary_out = {
        "frame": stats.get("frame"),
        "mesh_object_count": mesh_count,
        "evaluated_polygon_count": total_polys,
        "evaluated_triangle_count": total_tris,
        "has_active_rigidbody_world": has_rbw,
        "unpacked_external_image_count": len(unpacked_imgs),
        "missing_library_count": len(missing_libs),
        "color_management": stats.get("color_management"),
        "cycles_bounces": stats.get("cycles_bounces"),
        "top_meshes": [
            {
                "name": m.get("name"),
                "triangle_count": m.get("triangle_count"),
                "polygon_count": m.get("polygon_count"),
                "smooth_face_ratio": m.get("smooth_face_ratio"),
                "modifiers": m.get("modifiers", []),
            }
            for m in sorted(meshes, key=lambda r: int(r.get("triangle_count", 0)), reverse=True)[:10]
        ],
    }
    if cam_stage is not None:
        summary_out["camera_staging"] = cam_stage

    return {
        "schema_version": 1,
        "profile": profile,
        "review_status": "technical_screening_only_not_visual_acceptance",
        "passed": len(blocking) == 0,
        "strict_passed": len(blocking) == 0 and len(warnings) == 0,
        "thresholds": {
            "min_scene_triangles": min_scene_triangles,
            "shards": shards,
            "require_packed": require_packed,
        },
        "summary": summary_out,
        "blocking_issues": blocking,
        "warnings": warnings,
    }


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
    adaptive_threshold: float = DEFAULT_ADAPTIVE_THRESHOLD,
    modeling_profile: str = MODELING_PROFILE_HIGH_POLY,
    min_scene_triangles: int = DEFAULT_MIN_SCENE_TRIANGLES,
    strict_modeling_audit: bool = False,
) -> str:
    profile = normalize_modeling_profile(modeling_profile)
    cfg = {
        "remote_blend": remote_blend,
        "remote_mp4": remote_mp4,
        "remote_meta": remote_meta,
        "frame_start": frame_start,
        "frame_end": frame_end,
        "samples": samples,
        "adaptive_threshold": float(adaptive_threshold),
        "denoising_input_passes": DEFAULT_DENOISING_INPUT_PASSES,
        "width": width,
        "height": height,
        "fps": fps,
        "crf": crf,
        "shards": shards,
        "backend": backend,
        "blender_url": blender_url,
        "modeling_profile": profile,
        "min_scene_triangles": int(min_scene_triangles),
        "strict_modeling_audit": bool(strict_modeling_audit),
    }
    return f"""#!/usr/bin/env python3
import json, pathlib, shutil, subprocess, sys, time

CFG = {json.dumps(cfg, ensure_ascii=False)}
BLENDER_DIR = pathlib.Path("/content/blender")
BLENDER_BIN = BLENDER_DIR / "blender"
WORK_DIR = pathlib.Path("/content/_sv_blender_work")
FRAMES_DIR = WORK_DIR / "frames"
DRIVER_PY = WORK_DIR / "_cycles_shard.py"
AUDIT_PY = WORK_DIR / "_industrial_audit.py"
AUDIT_JSON = WORK_DIR / "_industrial_audit_stats.json"
AUDIT_CODE = {repr(_INDUSTRIAL_AUDIT_BLENDER_CODE)}

SHARD_CODE = r'''
import argparse, pathlib, sys, bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--out-dir", required=True)
p.add_argument("--frame-start", type=int, required=True)
p.add_argument("--frame-end", type=int, required=True)
p.add_argument("--frame-step", type=int, default=1)
p.add_argument("--samples", type=int, required=True)
p.add_argument("--adaptive-threshold", type=float, default=0.015)
p.add_argument("--width", type=int, required=True)
p.add_argument("--height", type=int, required=True)
p.add_argument("--backend", required=True)
a = p.parse_args(argv)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.use_persistent_data = True
scene.cycles.samples = a.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = a.adaptive_threshold
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
if hasattr(scene.cycles, "denoising_input_passes"):
    scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
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
print(f"[CYCLES] backend={{selected}} frames={{a.frame_start}}..{{a.frame_end}} step={{a.frame_step}} samples={{a.samples}} adaptive={{a.adaptive_threshold}} oidn=RGB_ALBEDO_NORMAL", flush=True)

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


def _eval_remote_audit(stats, profile, min_tris, n_shards):
    meshes = list(stats.get("meshes") or [])
    mesh_count = int(stats.get("mesh_object_count", len(meshes)))
    total_polys = int(stats.get("evaluated_polygon_count", 0))
    total_tris = int(stats.get("evaluated_triangle_count", 0))
    non_uniform = list(stats.get("non_uniform_scale_objects") or [])
    unapplied_uniform = list(stats.get("unapplied_uniform_scale_objects") or [])
    viewport_only = list(stats.get("viewport_only_material_objects") or [])
    has_rbw = bool(stats.get("has_active_rigidbody_world", False))
    unpacked_imgs = list(stats.get("unpacked_external_images") or [])
    missing_libs = list(stats.get("missing_libraries") or [])
    blocking = []
    warnings = []
    if mesh_count == 0:
        blocking.append({{"code": "no_visible_meshes", "severity": "blocking", "message": "No render-visible mesh objects."}})
    if n_shards > 1 and has_rbw:
        blocking.append({{"code": "unbaked_rigidbody_world", "severity": "blocking", "message": f"Active rigidbody_world with shards={{n_shards}}; bake to quaternion F-curves first."}})
    if unpacked_imgs:
        blocking.append({{"code": "unpacked_external_images", "severity": "blocking", "message": f"{{len(unpacked_imgs)}} unpacked external image(s).", "items": unpacked_imgs[:20]}})
    if missing_libs:
        blocking.append({{"code": "missing_linked_libraries", "severity": "blocking", "message": f"{{len(missing_libs)}} missing linked library path(s).", "items": missing_libs[:20]}})
    if viewport_only:
        blocking.append({{"code": "viewport_only_materials", "severity": "blocking", "message": f"{{len(viewport_only)}} visible mesh(es) lack active node materials.", "items": viewport_only[:20]}})
    if non_uniform:
        blocking.append({{"code": "non_uniform_scale", "severity": "blocking", "message": f"{{len(non_uniform)}} visible mesh(es) have non-uniform scale.", "items": non_uniform[:20]}})
    if unapplied_uniform:
        warnings.append({{"code": "unapplied_uniform_scale", "severity": "warning", "message": f"{{len(unapplied_uniform)}} visible mesh(es) have unapplied uniform scale.", "items": unapplied_uniform[:20]}})
    if profile == "high_poly_industrial_v1":
        if total_tris < min_tris:
            warnings.append({{"code": "low_poly_scene", "severity": "warning", "message": f"Evaluated triangles ({{total_tris}}) below screening floor ({{min_tris}})."}})
        flat_curved = [m["name"] for m in meshes if int(m.get("polygon_count", 0)) >= 24 and float(m.get("smooth_face_ratio", 1.0)) == 0.0]
        if flat_curved:
            warnings.append({{"code": "flat_shaded_curved_meshes", "severity": "warning", "message": f"{{len(flat_curved)}} curved/multi-face mesh(es) are 100% flat-shaded.", "items": flat_curved[:20]}})
        unbeveled = [m["name"] for m in meshes if int(m.get("polygon_count", 0)) >= 6 and not m.get("has_bevel") and not m.get("has_subsurf") and int(m.get("triangle_count", 0)) < 2000]
        if unbeveled:
            warnings.append({{"code": "unbeveled_low_detail_meshes", "severity": "warning", "message": f"{{len(unbeveled)}} hard-surface mesh(es) lack Bevel/Subsurf and have <2000 triangles.", "items": unbeveled[:20]}})
        missing_wn = [m["name"] for m in meshes if m.get("has_bevel") and not m.get("has_weighted_normal") and int(m.get("polygon_count", 0)) >= 12]
        if missing_wn:
            warnings.append({{"code": "beveled_without_weighted_normal", "severity": "warning", "message": f"{{len(missing_wn)}} beveled mesh(es) lack WeightedNormal/EdgeSplit.", "items": missing_wn[:20]}})
    cam_stage = stats.get("camera_staging") if isinstance(stats.get("camera_staging"), dict) else None
    if cam_stage is not None:
        cam_dur = float(cam_stage.get("duration_s") or 0.0)
        cam_cuts = int(cam_stage.get("hard_cut_count") or 0)
        cam_longest = float(cam_stage.get("longest_unbroken_shot_s") or 0.0)
        if cam_dur >= 25.0 and (cam_cuts < 3 or cam_longest > 14.0):
            warnings.append({{"code": "hollow_single_stage_glide", "severity": "warning", "message": f"Timeline spans {{cam_dur:.1f}}s with {{cam_cuts}} hard cut(s) and {{cam_longest:.1f}}s longest shot; avoid hollow single-workbench Bezier glides."}})
    return {{
        "schema_version": 1,
        "profile": profile,
        "review_status": "technical_screening_only_not_visual_acceptance",
        "passed": len(blocking) == 0,
        "strict_passed": len(blocking) == 0 and len(warnings) == 0,
        "summary": {{
            "frame": stats.get("frame"),
            "mesh_object_count": mesh_count,
            "evaluated_polygon_count": total_polys,
            "evaluated_triangle_count": total_tris,
            "has_active_rigidbody_world": has_rbw,
            "unpacked_external_image_count": len(unpacked_imgs),
            "missing_library_count": len(missing_libs),
            "color_management": stats.get("color_management"),
            "cycles_bounces": stats.get("cycles_bounces"),
        }},
        "blocking_issues": blocking,
        "warnings": warnings,
    }}


t0 = time.monotonic()
gpu_info = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
    capture_output=True, text=True, check=False,
).stdout.strip()

if not BLENDER_BIN.is_file():
    print("[COLAB-BLENDER] Downloading Blender Linux runtime ...", flush=True)
    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-fsSL", CFG["blender_url"], "-o", "/tmp/blender.tar.xz"], check=True)
    subprocess.run(["tar", "-xf", "/tmp/blender.tar.xz", "-C", str(BLENDER_DIR), "--strip-components=1"], check=True)
    pathlib.Path("/tmp/blender.tar.xz").unlink(missing_ok=True)

if shutil.which("ffmpeg") is None:
    print("[COLAB-BLENDER] Installing ffmpeg ...", flush=True)
    subprocess.run(["apt-get", "-qq", "update"], check=True)
    subprocess.run(["apt-get", "-qq", "install", "-y", "ffmpeg"], check=True)

blender_version = subprocess.check_output([str(BLENDER_BIN), "--version"], text=True).splitlines()[0].strip()
print(f"[COLAB-BLENDER] GPU={{gpu_info}} | {{blender_version}} | profile={{CFG['modeling_profile']}} | frames={{CFG['frame_start']}}..{{CFG['frame_end']}} | shards={{CFG['shards']}} | samples={{CFG['samples']}}", flush=True)

if FRAMES_DIR.exists():
    shutil.rmtree(FRAMES_DIR, ignore_errors=True)
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
DRIVER_PY.write_text(SHARD_CODE, encoding="utf-8")
AUDIT_PY.write_text(AUDIT_CODE, encoding="utf-8")

f0, f1 = int(CFG["frame_start"]), int(CFG["frame_end"])
total_frames = f1 - f0 + 1
n_shards = max(1, min(int(CFG["shards"]), total_frames))

industrial_audit = None
audit_proc = subprocess.run(
    [str(BLENDER_BIN), "-b", CFG["remote_blend"], "-P", str(AUDIT_PY), "--", "--out-json", str(AUDIT_JSON), "--frame", str(f0)],
    capture_output=True, text=True, check=False,
)
if audit_proc.returncode == 0 and AUDIT_JSON.is_file():
    raw_stats = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    industrial_audit = _eval_remote_audit(raw_stats, CFG["modeling_profile"], int(CFG["min_scene_triangles"]), n_shards)
    print(
        f"[COLAB-AUDIT] profile={{industrial_audit['profile']}} meshes={{industrial_audit['summary']['mesh_object_count']}} "
        f"tris={{industrial_audit['summary']['evaluated_triangle_count']}} "
        f"blocking={{len(industrial_audit['blocking_issues'])}} warnings={{len(industrial_audit['warnings'])}}",
        flush=True,
    )
    if CFG["strict_modeling_audit"] and not industrial_audit["strict_passed"]:
        raise RuntimeError("Strict industrial modeling audit failed before render: " + json.dumps(industrial_audit, ensure_ascii=False))
else:
    industrial_audit = {{"status": "audit_error", "returncode": audit_proc.returncode, "stderr_tail": (audit_proc.stderr or "")[-400:]}}
    if CFG["strict_modeling_audit"]:
        raise RuntimeError("Strict industrial modeling audit script failed: " + json.dumps(industrial_audit, ensure_ascii=False))

procs = []
log_files = []
for si in range(n_shards):
    log_p = WORK_DIR / f"shard_{{si}}.log"
    lf = log_p.open("w", encoding="utf-8", errors="replace")
    log_files.append((si, log_p, lf))
    cmd = [
        str(BLENDER_BIN), "-b", CFG["remote_blend"], "-P", str(DRIVER_PY), "--",
        "--out-dir", str(FRAMES_DIR),
        "--frame-start", str(f0 + si),
        "--frame-end", str(f1),
        "--frame-step", str(n_shards),
        "--samples", str(CFG["samples"]),
        "--adaptive-threshold", str(CFG["adaptive_threshold"]),
        "--width", str(CFG["width"]),
        "--height", str(CFG["height"]),
        "--backend", CFG["backend"],
    ]
    procs.append(subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT))

last_beat = 0.0
while any(p.poll() is None for p in procs):
    now = time.monotonic()
    if now - last_beat >= 10.0:
        rendered = sum(1 for p in FRAMES_DIR.glob("frame_*.png") if p.stat().st_size > 1024)
        elapsed = now - t0
        pct = 100.0 * rendered / max(1, total_frames)
        print(f"[PROGRESS] {{rendered}}/{{total_frames}} ({{pct:.1f}}%) elapsed={{elapsed:.0f}}s", flush=True)
        last_beat = now
    time.sleep(2.0)

rcs = [p.wait() for p in procs]
for _, _, lf in log_files:
    lf.close()
rendered = sum(1 for p in FRAMES_DIR.glob("frame_*.png") if p.stat().st_size > 1024)
if any(rc != 0 for rc in rcs) or rendered != total_frames:
    tails = []
    for si, log_p, _ in log_files:
        if rcs[si] != 0 and log_p.is_file():
            tails.append(f"shard_{{si}} rc={{rcs[si]}}: " + log_p.read_text(encoding="utf-8", errors="replace")[-400:])
    raise RuntimeError(f"Blender render failed: returncodes={{rcs}}, rendered={{rendered}}/{{total_frames}}; " + " | ".join(tails))

print(f"[COLAB-BLENDER] Encoding {{total_frames}} frames to Rec.709 MP4 ...", flush=True)

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
    "modeling_profile": CFG["modeling_profile"],
    "frame_start": f0,
    "frame_end": f1,
    "total_frames": total_frames,
    "width": CFG["width"],
    "height": CFG["height"],
    "fps": CFG["fps"],
    "samples": CFG["samples"],
    "adaptive_threshold": CFG["adaptive_threshold"],
    "denoising_input_passes": CFG["denoising_input_passes"],
    "shards": n_shards,
    "industrial_modeling_audit": industrial_audit,
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

    exec_args = ["exec", "-s", session, "--timeout", "0", "-f", _host_path_for_cli(script_resolved, tname)]
    for pair in env_pairs:
        exec_args += ["--env", pair]

    planned_steps: list[list[str]] = []
    if not reuse_session:
        planned_steps.append(build_colab_cmd(info, new_args, **common))
    for local_p, remote_p in uploads:
        planned_steps.append(build_colab_cmd(info, ["upload", "-s", session, _host_path_for_cli(local_p, tname), remote_p], **common))
    # Redact --env values in plan summary
    safe_exec_args = ["exec", "-s", session, "--timeout", "0", "-f", _host_path_for_cli(script_resolved, tname)]
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


def cmd_audit_blend(args: argparse.Namespace, *, runner=subprocess.run) -> int:
    try:
        profile = normalize_modeling_profile(args.modeling_profile)
        if args.min_scene_triangles < 0:
            raise ValueError("--min-scene-triangles must be >= 0")
        if args.shards < 1:
            raise ValueError("--shards must be >= 1")
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    blend_path = Path(args.blend).resolve()
    if not blend_path.is_file():
        print(f"Input error: .blend file not found: {blend_path}", file=sys.stderr)
        return 2

    report_path = Path(args.report).resolve() if args.report else None
    if report_path is not None and report_path.exists() and not args.overwrite_report:
        print(f"Input error: Report file already exists (use a new report filename): {report_path}", file=sys.stderr)
        return 2

    blender_exe = args.blender or shutil.which("blender")
    if not blender_exe or (not Path(blender_exe).is_file() and shutil.which(blender_exe) is None):
        print(
            json.dumps({
                "status": "blender_not_found",
                "reason": "Local Blender executable not found; pass --blender <path-to-blender>.",
            }, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2

    with tempfile.TemporaryDirectory(prefix="sv-colab-audit-") as tmp_dir:
        audit_py = Path(tmp_dir) / "industrial_audit.py"
        stats_json = Path(tmp_dir) / "industrial_stats.json"
        audit_py.write_text(_INDUSTRIAL_AUDIT_BLENDER_CODE, encoding="utf-8")
        cmd = [str(blender_exe), "-b", str(blend_path), "-P", str(audit_py), "--", "--out-json", str(stats_json)]
        if args.frame is not None:
            cmd += ["--frame", str(args.frame)]
        res = _run_cli(cmd, timeout=args.timeout, runner=runner)
        if res["returncode"] != 0:
            print(
                json.dumps({
                    "status": "blender_error",
                    "returncode": res["returncode"],
                    "stderr_tail": res["stderr"][-800:],
                    "stdout_tail": res["stdout"][-400:],
                }, ensure_ascii=False, indent=2),
                file=sys.stderr,
            )
            return 2

        stats: dict[str, Any] | None = None
        if stats_json.is_file():
            stats = json.loads(stats_json.read_text(encoding="utf-8"))
        else:
            for line in res["stdout"].splitlines():
                if line.startswith("INDUSTRIAL_AUDIT_STATS="):
                    stats = json.loads(line.split("=", 1)[1])
                    break
        if stats is None:
            print("Blender completed without emitting industrial audit stats.", file=sys.stderr)
            return 2

    audit = evaluate_industrial_audit(
        stats,
        modeling_profile=profile,
        min_scene_triangles=args.min_scene_triangles,
        shards=args.shards,
        require_packed=not args.allow_unpacked,
    )
    payload = {
        "checked_at": _now_iso(),
        "blend": {
            "path": str(blend_path),
            "bytes": blend_path.stat().st_size,
            "sha256": sha256_file(blend_path),
        },
        "blender_executable": str(blender_exe),
        "strict": bool(args.strict),
        **audit,
    }
    _write_receipt(report_path, payload, overwrite=args.overwrite_report)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    ok = audit["strict_passed"] if args.strict else audit["passed"]
    return 0 if ok else 1


def parse_still_frames_spec(spec: str) -> list[tuple[str, int]]:
    """Parse `--frames` spec (`16,84,200` or `01_hook:16,02_shatter:84`) into validated `(filename_stem, frame_int)` pairs."""
    items: list[tuple[str, int]] = []
    seen_stems: set[str] = set()
    for raw_tok in (spec or "").split(","):
        tok = raw_tok.strip()
        if not tok:
            continue
        if ":" in tok:
            label_part, frame_part = tok.rsplit(":", 1)
            label = re.sub(r"[^A-Za-z0-9._-]+", "_", label_part.strip()).strip("._-")
            if not label:
                raise ValueError(f"Invalid frame label in {tok!r}")
            try:
                fnum = int(frame_part.strip())
            except ValueError as exc:
                raise ValueError(f"Invalid frame integer in {tok!r}") from exc
            stem = f"{label}_f{fnum:04d}"
        else:
            try:
                fnum = int(tok)
            except ValueError as exc:
                raise ValueError(f"Invalid frame integer {tok!r}") from exc
            stem = f"frame_{fnum:04d}"
        if fnum < 0:
            raise ValueError(f"Frame number must be >= 0 (got {fnum})")
        if stem in seen_stems:
            continue
        seen_stems.add(stem)
        items.append((stem, fnum))
    if not items:
        raise ValueError("--frames must specify at least one frame integer (e.g. '16,84,200' or 'hook:16,peak:84')")
    return items


def _build_remote_blender_stills_driver(
    *,
    remote_blend: str,
    remote_tar: str,
    remote_meta: str,
    frame_items: list[tuple[str, int]],
    samples: int,
    width: int,
    height: int,
    shards: int,
    backend: str,
    blender_url: str,
    adaptive_threshold: float = DEFAULT_ADAPTIVE_THRESHOLD,
) -> str:
    cfg = {
        "remote_blend": remote_blend,
        "remote_tar": remote_tar,
        "remote_meta": remote_meta,
        "frame_items": [[stem, fnum] for stem, fnum in frame_items],
        "samples": samples,
        "adaptive_threshold": float(adaptive_threshold),
        "denoising_input_passes": DEFAULT_DENOISING_INPUT_PASSES,
        "width": width,
        "height": height,
        "shards": shards,
        "backend": backend,
        "blender_url": blender_url,
    }
    return f"""#!/usr/bin/env python3
import json, pathlib, shutil, subprocess, sys, tarfile, time

CFG = {json.dumps(cfg, ensure_ascii=False)}
BLENDER_DIR = pathlib.Path("/content/blender")
BLENDER_BIN = BLENDER_DIR / "blender"
WORK_DIR = pathlib.Path("/content/_sv_blender_stills_work")
STILLS_DIR = WORK_DIR / "stills"
DRIVER_PY = WORK_DIR / "_cycles_stills_shard.py"

SHARD_CODE = r'''
import argparse, json, pathlib, sys, bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
p = argparse.ArgumentParser()
p.add_argument("--out-dir", required=True)
p.add_argument("--items-json", required=True)
p.add_argument("--samples", type=int, required=True)
p.add_argument("--adaptive-threshold", type=float, default=0.015)
p.add_argument("--width", type=int, required=True)
p.add_argument("--height", type=int, required=True)
p.add_argument("--backend", required=True)
a = p.parse_args(argv)

items = json.loads(pathlib.Path(a.items_json).read_text(encoding="utf-8"))
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.render.use_persistent_data = True
scene.cycles.samples = a.samples
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = a.adaptive_threshold
scene.cycles.use_denoising = True
scene.cycles.denoiser = "OPENIMAGEDENOISE"
if hasattr(scene.cycles, "denoising_input_passes"):
    scene.cycles.denoising_input_passes = "RGB_ALBEDO_NORMAL"
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
print(f"[CYCLES-STILLS] backend={{selected}} count={{len(items)}} samples={{a.samples}} adaptive={{a.adaptive_threshold}}", flush=True)

out_dir = pathlib.Path(a.out_dir)
out_dir.mkdir(parents=True, exist_ok=True)
for stem, fnum in items:
    dst = out_dir / f"{{stem}}.png"
    scene.frame_set(int(fnum))
    cam_name = scene.camera.name if scene.camera else "NONE"
    scene.render.filepath = str(dst)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError as exc:
        if selected == "OPTIX":
            print(f"[CYCLES-STILLS] OPTIX failed ({{exc}}); switching to CUDA", flush=True)
            prefs.compute_device_type = "CUDA"
            prefs.get_devices()
            for dev in prefs.devices:
                dev.use = (dev.type == "CUDA")
            selected = "CUDA"
            bpy.ops.render.render(write_still=True)
        else:
            raise
    print(f"[STILL OK] {{dst.name}} frame={{fnum}} cam={{cam_name}}", flush=True)
'''

t0 = time.monotonic()
gpu_info = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
    capture_output=True, text=True, check=False,
).stdout.strip()

if not BLENDER_BIN.is_file():
    print("[COLAB-STILLS] Downloading Blender Linux runtime ...", flush=True)
    BLENDER_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(["curl", "-fsSL", CFG["blender_url"], "-o", "/tmp/blender.tar.xz"], check=True)
    subprocess.run(["tar", "-xf", "/tmp/blender.tar.xz", "-C", str(BLENDER_DIR), "--strip-components=1"], check=True)
    pathlib.Path("/tmp/blender.tar.xz").unlink(missing_ok=True)

blender_version = subprocess.check_output([str(BLENDER_BIN), "--version"], text=True).splitlines()[0].strip()
all_items = CFG["frame_items"]
n_shards = max(1, min(int(CFG["shards"]), len(all_items)))
print(f"[COLAB-STILLS] GPU={{gpu_info}} | {{blender_version}} | stills={{len(all_items)}} | shards={{n_shards}} | samples={{CFG['samples']}}", flush=True)

if STILLS_DIR.exists():
    shutil.rmtree(STILLS_DIR, ignore_errors=True)
STILLS_DIR.mkdir(parents=True, exist_ok=True)
DRIVER_PY.write_text(SHARD_CODE, encoding="utf-8")

procs = []
log_files = []
for si in range(n_shards):
    shard_items = all_items[si::n_shards]
    items_json = WORK_DIR / f"shard_{{si}}_items.json"
    items_json.write_text(json.dumps(shard_items), encoding="utf-8")
    log_p = WORK_DIR / f"stills_shard_{{si}}.log"
    lf = log_p.open("w", encoding="utf-8", errors="replace")
    log_files.append((si, log_p, lf))
    cmd = [
        str(BLENDER_BIN), "-b", CFG["remote_blend"], "-P", str(DRIVER_PY), "--",
        "--out-dir", str(STILLS_DIR),
        "--items-json", str(items_json),
        "--samples", str(CFG["samples"]),
        "--adaptive-threshold", str(CFG["adaptive_threshold"]),
        "--width", str(CFG["width"]),
        "--height", str(CFG["height"]),
        "--backend", CFG["backend"],
    ]
    procs.append(subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT))

rcs = [p.wait() for p in procs]
for _, _, lf in log_files:
    lf.close()

rendered_files = sorted(STILLS_DIR.glob("*.png"))
if any(rc != 0 for rc in rcs) or len(rendered_files) != len(all_items):
    tails = []
    for si, log_p, _ in log_files:
        if rcs[si] != 0 and log_p.is_file():
            tails.append(f"shard_{{si}} rc={{rcs[si]}}: " + log_p.read_text(encoding="utf-8", errors="replace")[-500:])
    raise RuntimeError(f"Blender stills render failed: rcs={{rcs}}, rendered={{len(rendered_files)}}/{{len(all_items)}}; " + " | ".join(tails))

tar_path = pathlib.Path(CFG["remote_tar"])
tar_path.parent.mkdir(parents=True, exist_ok=True)
with tarfile.open(tar_path, "w") as tf:
    for png in rendered_files:
        tf.add(png, arcname=png.name)

meta = {{
    "gpu": gpu_info,
    "blender_version": blender_version,
    "requested_backend": CFG["backend"],
    "stills_count": len(rendered_files),
    "files": [p.name for p in rendered_files],
    "width": CFG["width"],
    "height": CFG["height"],
    "samples": CFG["samples"],
    "adaptive_threshold": CFG["adaptive_threshold"],
    "denoising_input_passes": CFG["denoising_input_passes"],
    "shards": n_shards,
    "tar_bytes": tar_path.stat().st_size,
    "remote_elapsed_s": round(time.monotonic() - t0, 2),
}}
pathlib.Path(CFG["remote_meta"]).write_text(json.dumps(meta, indent=2), encoding="utf-8")
print("COLAB_BLENDER_STILLS_META=" + json.dumps(meta, ensure_ascii=False))
"""


def cmd_blender_stills(args: argparse.Namespace, *, runner=subprocess.run) -> int:
    try:
        session = validate_session_name(args.session)
        gpu = normalize_gpu(args.gpu)
        assert gpu is not None
        backend = choose_cycles_backend(gpu, args.backend)
        frame_items = parse_still_frames_spec(args.frames)
        if not (0 < args.adaptive_threshold < 1):
            raise ValueError(f"--adaptive-threshold ({args.adaptive_threshold}) must be between 0 and 1")
        if min(args.width, args.height) < 1080 and not args.allow_proxy:
            raise ValueError(
                f"Formal still dimensions {args.width}x{args.height} have short edge < 1080; "
                "pass --allow-proxy only for explicitly internal low-res diagnostics."
            )
    except ValueError as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2

    blend_path = Path(args.blend).resolve()
    if not blend_path.is_file():
        print(f"Input error: packed .blend not found: {blend_path}", file=sys.stderr)
        return 2
    out_dir = Path(args.out_dir).resolve()
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
    remote_tar = f"/content/{session}_stills.tar"
    remote_meta = f"/content/{session}_stills_meta.json"

    driver_src = _build_remote_blender_stills_driver(
        remote_blend=remote_blend,
        remote_tar=remote_tar,
        remote_meta=remote_meta,
        frame_items=frame_items,
        samples=args.samples,
        width=args.width,
        height=args.height,
        shards=args.shards,
        backend=backend,
        blender_url=args.blender_url,
        adaptive_threshold=args.adaptive_threshold,
    )

    with tempfile.TemporaryDirectory(prefix="sv-colab-stills-") as tmp_dir:
        driver_file = Path(tmp_dir) / f"{session}_stills_driver.py"
        driver_file.write_text(driver_src, encoding="utf-8")
        meta_local = Path(tmp_dir) / f"{session}_stills_meta.json"
        if not args.dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
        # Download each PNG individually (<3 MB each) to avoid >4 MB Jupyter Contents API download stalls!
        per_still_downloads = [
            (f"/content/_sv_blender_stills_work/stills/{stem}.png", out_dir / f"{stem}.png")
            for stem, _ in frame_items
        ]
        per_still_downloads.append((remote_meta, meta_local))
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
                downloads=per_still_downloads,
                env_pairs=[],
                exec_timeout=args.timeout,
                dry_run=args.dry_run,
                receipt_path=None,
                overwrite_receipt=args.overwrite_receipt,
                extra_meta={
                    "blender_stills": {
                        "blend": str(blend_path),
                        "out_dir": str(out_dir),
                        "frames": [[stem, fnum] for stem, fnum in frame_items],
                        "width": args.width,
                        "height": args.height,
                        "samples": args.samples,
                        "adaptive_threshold": args.adaptive_threshold,
                        "denoising_input_passes": DEFAULT_DENOISING_INPUT_PASSES,
                        "shards": args.shards,
                        "selected_backend": backend,
                        "proxy_mode": bool(args.allow_proxy),
                    }
                },
                runner=runner,
            )
            extracted: list[dict[str, Any]] = []
            if rc == 0 and not args.dry_run:
                for stem, _ in frame_items:
                    dest = out_dir / f"{stem}.png"
                    if dest.is_file():
                        extracted.append({"file": str(dest), "bytes": dest.stat().st_size, "sha256": sha256_file(dest)})
                receipt["extracted_stills"] = extracted
            if meta_local.is_file():
                try:
                    receipt["remote_stills_meta"] = json.loads(meta_local.read_text(encoding="utf-8"))
                except ValueError:
                    pass
            _write_receipt(receipt_path, receipt, overwrite=args.overwrite_receipt)
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
        modeling_profile = normalize_modeling_profile(args.modeling_profile)
        if args.frame_start > args.frame_end:
            raise ValueError(f"--frame-start ({args.frame_start}) must be <= --frame-end ({args.frame_end})")
        if not (0 < args.adaptive_threshold < 1):
            raise ValueError(f"--adaptive-threshold ({args.adaptive_threshold}) must be between 0 and 1")
        if args.min_scene_triangles < 0:
            raise ValueError("--min-scene-triangles must be >= 0")
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
        adaptive_threshold=args.adaptive_threshold,
        modeling_profile=modeling_profile,
        min_scene_triangles=args.min_scene_triangles,
        strict_modeling_audit=args.strict_modeling_audit,
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
                        "modeling_profile": modeling_profile,
                        "min_scene_triangles": args.min_scene_triangles,
                        "strict_modeling_audit": bool(args.strict_modeling_audit),
                        "frame_start": args.frame_start,
                        "frame_end": args.frame_end,
                        "width": args.width,
                        "height": args.height,
                        "fps": args.fps,
                        "samples": args.samples,
                        "adaptive_threshold": args.adaptive_threshold,
                        "denoising_input_passes": DEFAULT_DENOISING_INPUT_PASSES,
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

    p_aud = sub.add_parser("audit-blend", help="Run local offline headless-Blender preflight against high_poly_industrial_v1")
    p_aud.add_argument("--blend", required=True, help="Local packed .blend scene to inspect")
    p_aud.add_argument("--blender", help="Explicit local Blender executable path (default: blender on PATH)")
    p_aud.add_argument("--frame", type=int, help="Optional frame number to evaluate before inspecting meshes")
    p_aud.add_argument("--modeling-profile", choices=MODELING_PROFILES, default="high_poly_industrial", help="Modeling audit profile (default: high_poly_industrial)")
    p_aud.add_argument("--min-scene-triangles", type=int, default=DEFAULT_MIN_SCENE_TRIANGLES, help=f"Visible evaluated triangle screening floor (default {DEFAULT_MIN_SCENE_TRIANGLES})")
    p_aud.add_argument("--shards", type=int, default=2, help="Planned Colab shard count for strided physics check (default 2)")
    p_aud.add_argument("--allow-unpacked", action="store_true", help="Do not block on unpacked external image files (for local-only draft inspection)")
    p_aud.add_argument("--strict", action="store_true", help="Treat high-poly industrial advisory warnings as non-zero failures")
    p_aud.add_argument("--timeout", type=int, default=180, help="Local Blender audit timeout in seconds")
    p_aud.add_argument("--report", help="Write hash-bound JSON audit report to a new file")
    p_aud.add_argument("--overwrite-report", action="store_true", help="Allow overwriting an existing audit report file")
    p_aud.set_defaults(func=cmd_audit_blend)

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

    p_st = sub.add_parser("blender-stills", help="Headless packed-.blend Cycles GPU render of selected lookdev stills + tar download + teardown")
    p_st.add_argument("-s", "--session", required=True, help="Explicit unique session name")
    p_st.add_argument("--blend", required=True, help="Self-contained packed .blend file to upload")
    p_st.add_argument("--frames", required=True, help="Comma-separated frame ints or label:frame pairs (e.g. '16,84,200' or 'hook:16,shatter:84')")
    p_st.add_argument("--out-dir", required=True, help="Local destination directory for unpacked PNG stills")
    p_st.add_argument("--gpu", default="A100", help="Colab GPU accelerator (T4, L4, G4, A100, H100)")
    p_st.add_argument("--high-mem", action="store_true", help="Request high-RAM machine shape where supported")
    p_st.add_argument("--backend", choices=("auto", "OPTIX", "CUDA"), default="auto", help="Cycles GPU backend (auto picks CUDA on A100/H100/T4, OPTIX on G4/L4)")
    p_st.add_argument("--samples", type=int, default=64, help="Cycles samples per frame")
    p_st.add_argument("--adaptive-threshold", type=float, default=DEFAULT_ADAPTIVE_THRESHOLD, help=f"Cycles adaptive noise threshold (default {DEFAULT_ADAPTIVE_THRESHOLD})")
    p_st.add_argument("--width", type=int, default=1920, help="Render width (default 1920)")
    p_st.add_argument("--height", type=int, default=1080, help="Render height (default 1080)")
    p_st.add_argument("--shards", type=int, default=4, help="Concurrent Blender GPU shards (default 4)")
    p_st.add_argument("--blender-url", default=DEFAULT_BLENDER_LINUX_URL, help="Official Linux Blender tarball URL")
    p_st.add_argument("--allow-proxy", action="store_true", help="Allow short edge < 1080 for internal low-res diagnostics only")
    p_st.add_argument("--reuse-session", action="store_true", help="Attach to an existing session without new/stop")
    p_st.add_argument("--keep", action="store_true", help="Keep newly allocated session alive after completion")
    p_st.add_argument("--timeout", type=int, default=1800, help="Execution timeout in seconds")
    p_st.add_argument("--dry-run", action="store_true", help="Validate inputs and print plan without allocating a Colab VM")
    p_st.add_argument("--receipt", help="Write hash-bound JSON execution receipt to a new file")
    p_st.add_argument("--overwrite-receipt", action="store_true", help="Allow overwriting an existing receipt file")
    p_st.set_defaults(func=cmd_blender_stills)

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
    p_bl.add_argument("--adaptive-threshold", type=float, default=DEFAULT_ADAPTIVE_THRESHOLD, help=f"Cycles adaptive noise threshold (default {DEFAULT_ADAPTIVE_THRESHOLD} for crisp bevels/metals)")
    p_bl.add_argument("--modeling-profile", choices=MODELING_PROFILES, default="high_poly_industrial", help="Modeling audit profile recorded in remote receipt (default: high_poly_industrial)")
    p_bl.add_argument("--min-scene-triangles", type=int, default=DEFAULT_MIN_SCENE_TRIANGLES, help=f"Visible evaluated triangle screening floor (default {DEFAULT_MIN_SCENE_TRIANGLES})")
    p_bl.add_argument("--strict-modeling-audit", action="store_true", help="Abort on Colab before rendering if high-poly industrial modeling audit reports blocking issues or warnings")
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
