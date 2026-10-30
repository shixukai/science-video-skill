#!/usr/bin/env python3
"""Reusable local Blender image-sequence jobs. Outputs are always unreviewed.

The job contains scene inputs, not approvals. Use the existing episode gate when
assembling audiovisual samples or final media. No installation or device fallback.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import time
import uuid
import zlib


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def file_hash(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write(path, value):
    path = Path(path)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write("\n")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def resolve(root, path):
    if not isinstance(path, str) or not path.strip():
        raise ValueError("A nonempty file/directory path is required")
    return (Path(root) / path).resolve()


def parse_frames(value):
    """Blender frame numbers; preserve gaps for patches, reject duplicates."""
    if isinstance(value, str):
        frames = []
        for part in value.split(","):
            match = re.fullmatch(r"\s*(-?\d+)(?:\s*:\s*(-?\d+))?\s*", part)
            if not match:
                raise ValueError("Frames use comma-separated integers or inclusive start:end")
            first = int(match[1]); last = int(match[2]) if match[2] is not None else first
            if last < first:
                raise ValueError("Descending frame range")
            frames.extend(range(first, last + 1))
    else:
        frames = value
    if (not isinstance(frames, list) or not frames or
            any(type(frame) is not int for frame in frames) or len(set(frames)) != len(frames)):
        raise ValueError("Frames must be a nonempty unique integer list")
    return sorted(frames)


RENDER_KEYS = frozenset((
    "engine", "width", "height", "fps", "fps_base", "format", "color_mode", "threads",
    "device", "samples", "persistent_data", "denoise", "denoiser", "max_bounces",
    "noise_threshold", "backend", "device_name", "device_id", "color_management",
))
COLOR_MANAGEMENT_KEYS = ("display_device", "view_transform", "look", "exposure", "gamma")


def validate_render_settings(render):
    """Job settings are explicit; scene-specific settings stay in the scene/driver."""
    if not isinstance(render, dict):
        raise ValueError("render must be an object")
    unknown = set(render) - RENDER_KEYS
    if unknown:
        raise ValueError("Unsupported job render setting(s): " +
                         ", ".join("render." + str(key) for key in sorted(unknown, key=str)) +
                         ". Supported job render keys: " + ", ".join(sorted(RENDER_KEYS)) +
                         ". Color settings belong in render.color_management; other scene, "
                         "material and light settings belong in the driver or baked blend")
    if "color_management" not in render:
        return
    color = render["color_management"]
    if not isinstance(color, dict):
        raise ValueError("render.color_management must be an object")
    unknown = set(color) - set(COLOR_MANAGEMENT_KEYS)
    if unknown:
        raise ValueError("Unsupported render.color_management setting(s): " +
                         ", ".join(str(key) for key in sorted(unknown, key=str)) +
                         ". Supported color keys: " + ", ".join(COLOR_MANAGEMENT_KEYS))
    for key, value in color.items():
        if key in ("display_device", "view_transform", "look"):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("render.color_management." + key + " must be a nonempty string")
        else:
            try:
                finite = type(value) in (int, float) and math.isfinite(value)
            except OverflowError:
                finite = False
            if not finite or (key == "gamma" and value <= 0):
                raise ValueError("render.color_management." + key + " must be finite" +
                                 (" and positive" if key == "gamma" else ""))


def validate_spec(spec):
    if spec.get("schema_version") != 1 or not re.fullmatch(r"[A-Za-z0-9_.-]+", spec.get("job_id", "")):
        raise ValueError("schema_version=1 and a simple job_id are required")
    if spec.get("purpose") not in ("motion_preview", "lookdev", "shot_frames", "patch"):
        raise ValueError("Unknown intermediate-asset purpose")
    if bool(spec.get("blend")) == bool(spec.get("driver")):
        raise ValueError("Choose exactly one baked blend or Python driver")
    if not spec.get("blender_executable"):
        raise ValueError("Pin the existing Blender executable in the job spec")
    frames = parse_frames(spec.get("frames"))
    if spec["purpose"] == "motion_preview" and frames != list(range(frames[0], frames[-1] + 1)):
        raise ValueError("Motion previews require every native frame; use lookdev for sparse stills")
    render = spec.get("render", {})
    validate_render_settings(render)
    for key in ("width", "height", "fps"):
        if type(render.get(key)) is not int or render[key] <= 0:
            raise ValueError("Positive integer render." + key + " required")
    if not isinstance(render.get("fps_base", 1), (int, float)) or not math.isfinite(render.get("fps_base", 1)) or render.get("fps_base", 1) <= 0:
        raise ValueError("fps_base must be finite and positive")
    if render.get("engine") not in ("CYCLES", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        raise ValueError("Unsupported engine; validate a new engine before extending this executor")
    if render.get("format", "PNG") not in ("PNG", "OPEN_EXR"):
        raise ValueError("Use PNG or OPEN_EXR image sequences")
    if render["engine"] == "CYCLES":
        if render.get("device") not in ("CPU", "GPU"):
            raise ValueError("Select CPU or GPU explicitly")
        if render["device"] == "GPU" and (not render.get("backend") or not render.get("device_name")):
            raise ValueError("GPU requires the actual backend and exact enumerated device_name")
        if render["device"] == "CPU" and render.get("denoiser") == "OPTIX" and render.get("denoise", True):
            raise ValueError("CPU-only rendering requires a CPU-capable denoiser")
        if type(render.get("samples")) is not int or render["samples"] <= 0:
            raise ValueError("Positive Cycles samples required")
    for key in ("threads", "max_bounces"):
        if key in render and (type(render[key]) is not int or render[key] < (1 if key == "threads" else 0)):
            raise ValueError("Invalid render." + key)
    return frames


def prepare(spec_path, job_path):
    spec_path = Path(spec_path).resolve(); root = spec_path.parent
    spec = read(spec_path); spec["frames"] = validate_spec(spec)
    spec["output_dir"] = str(resolve(root, spec["output_dir"]))
    output = Path(spec["output_dir"])
    if output.is_relative_to(Path(__file__).resolve().parents[1]):
        raise ValueError("Outputs belong in the private project, outside the global Skill")
    files = list(spec.get("inputs", []))
    for key in ("blend", "driver", "blender_executable"):
        if spec.get(key):
            spec[key] = str(resolve(root, spec[key])); files.append(spec[key])
    if spec.get("resource_check"):
        # An existing project check, not a new utilization/VRAM threshold.
        spec["resource_check"] = str(resolve(root, spec["resource_check"]))
        files.append(spec["resource_check"])
    inputs = {}
    for item in files:
        path = resolve(root, item)
        if not path.is_file() or path.is_relative_to(output):
            raise ValueError("Input must be an existing file outside this job's output: " + str(path))
        inputs[str(path)] = file_hash(path)
    spec["inputs"] = inputs
    spec["executor_sha256"] = file_hash(__file__)
    job = {"kind": "blender_sequence_job", "created_at": now(), "spec": spec, "signature": digest(spec)}
    path = Path(job_path)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(job, stream, ensure_ascii=False, indent=2); stream.write("\n")
    return job


def verify(job):
    spec = job["spec"]
    validate_spec(spec)
    if job.get("kind") != "blender_sequence_job" or digest(spec) != job.get("signature"):
        raise ValueError("Job modified; prepare a new version")
    if file_hash(__file__) != spec["executor_sha256"]:
        raise ValueError("Executor changed; explicitly migrate this job")
    for path, expected in spec["inputs"].items():
        if file_hash(path) != expected:
            raise ValueError("Input changed: " + path)


@contextmanager
def job_lock(output):
    """OS lock is held by Blender itself, including if its launcher disappears."""
    output.mkdir(parents=True, exist_ok=True)
    path = output / ".render.lock"
    with path.open("a+b") as stream:
        stream.seek(0, 2)
        if stream.tell() == 0:
            stream.write(b"0"); stream.flush()
        stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("This output job is already running; inspect it, do not resubmit") from error
        try:
            yield
        finally:
            stream.seek(0)
            if os.name == "nt":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def frame_paths(output, frame, spec):
    stem = "frame_" + str(frame).zfill(6)
    return output / (stem + (".png" if spec["render"].get("format", "PNG") == "PNG" else ".exr")), output / (stem + ".json")


def check_image(path, render):
    width, height = render["width"], render["height"]
    if render.get("format", "PNG") == "PNG":
        raw = path.read_bytes(); offset = 8; compressed = bytearray(); ihdr = None; ended = False
        if raw[:8] != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Invalid PNG signature: " + str(path))
        while offset + 12 <= len(raw):
            length = struct.unpack(">I", raw[offset:offset+4])[0]
            end = offset + length + 12
            if end > len(raw): break
            kind = raw[offset+4:offset+8]; payload = raw[offset+8:end-4]
            crc = struct.unpack(">I", raw[end-4:end])[0]
            if zlib.crc32(kind + payload) != crc:
                raise ValueError("PNG chunk checksum failed: " + str(path))
            if ihdr is None and kind != b"IHDR":
                raise ValueError("PNG must begin with IHDR")
            if kind == b"IHDR":
                if ihdr is not None or length != 13: raise ValueError("Invalid PNG IHDR")
                ihdr = struct.unpack(">IIBBBBB", payload)
            elif kind == b"IDAT": compressed.extend(payload)
            elif kind == b"IEND":
                ended = length == 0 and end == len(raw); break
            offset = end
        if not ended or not ihdr or ihdr[:2] != (width, height) or not compressed:
            raise ValueError("Incomplete PNG or wrong dimensions: " + str(path))
        _, _, depth, color, compression, filtering, interlace = ihdr
        channels = {0:1, 2:3, 3:1, 4:2, 6:4}.get(color)
        if not channels or depth not in (1, 2, 4, 8, 16) or (compression, filtering, interlace) != (0, 0, 0):
            raise ValueError("Unsupported PNG encoding; expected non-interlaced Blender output")
        stride = (width * channels * depth + 7) // 8 + 1
        expected = stride * height; decoder = zlib.decompressobj()
        try:
            pixels = decoder.decompress(compressed, expected + 1)
        except zlib.error as error:
            raise ValueError("PNG pixel stream cannot be decoded") from error
        if len(pixels) != expected or not decoder.eof or decoder.unused_data or any(pixels[i] > 4 for i in range(0, expected, stride)):
            raise ValueError("Incomplete/invalid PNG pixel stream")
    else:
        with path.open("rb") as stream: header = stream.read(24)
        if len(header) < 24 or header[:4] != b"\x76\x2f\x31\x01" or path.stat().st_size <= 24:
            raise ValueError("Invalid EXR file: " + str(path))
        try:
            import bpy
        except ImportError as error:
            raise ValueError("EXR verification requires the actual Blender worker decoder") from error
        image = None
        try:
            image = bpy.data.images.load(str(path), check_existing=False)
            if tuple(image.size) != (width, height) or not image.has_data or len(image.pixels[:]) != width * height * image.channels:
                raise ValueError("EXR pixels cannot be decoded at the expected dimensions")
        except RuntimeError as error:
            raise ValueError("EXR decoder rejected image") from error
        finally:
            if image is not None: bpy.data.images.remove(image)


def valid_frame(job, frame):
    spec = job["spec"]; image, receipt = frame_paths(Path(spec["output_dir"]), frame, spec)
    try:
        record = read(receipt)
        if record.get("signature") != job["signature"] or record.get("frame") != frame or record.get("sha256") != file_hash(image):
            return False
        check_image(image, spec["render"])
        return True
    except (OSError, ValueError, KeyError):
        return False


def archive_invalid(output, paths):
    """Preserve only conflicting files within this already-owned output folder."""
    existing = [p for p in paths if p.exists()]
    if not existing:
        return
    destination = output / "invalid" / uuid.uuid4().hex
    destination.mkdir(parents=True)
    for path in existing:
        if not path.resolve().is_relative_to(output.resolve()) or not path.is_file():
            raise ValueError("Unexpected output path: " + str(path))
        path.replace(destination / path.name)


@contextmanager
def declared_source_imports(spec):
    """Execute declared project .py bytes, never timestamp-valid stale bytecode."""
    sources = {str(Path(path).resolve()): sha for path, sha in spec["inputs"].items()
               if Path(path).suffix == ".py"}

    class SourceLoader(importlib.machinery.SourceFileLoader):
        def get_code(self, fullname):
            data = Path(self.path).read_bytes()
            if hashlib.sha256(data).hexdigest() != sources[str(Path(self.path).resolve())]:
                raise ValueError("Imported source changed: " + self.path)
            return self.source_to_code(data, self.path)

    class SourceFinder:
        def find_spec(self, fullname, path=None, target=None):
            found = importlib.machinery.PathFinder.find_spec(fullname, path, target)
            if (found and found.origin and
                    isinstance(found.loader, importlib.machinery.SourceFileLoader) and
                    str(Path(found.origin).resolve()) in sources):
                found.loader = SourceLoader(fullname, found.origin)
                return found
            return None

    def declared(module):
        origin = getattr(module, "__file__", None)
        return bool(origin and str(Path(origin).resolve()) in sources)

    previous = {name: module for name, module in list(sys.modules.items()) if declared(module)}
    for name in previous:
        del sys.modules[name]
    original_path = list(sys.path)
    finder = SourceFinder(); sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        sys.path[:] = original_path
        for name, module in list(sys.modules.items()):
            if declared(module):
                del sys.modules[name]
        sys.modules.update(previous)


def load_module(path, name):
    sys.path.insert(0, str(Path(path).parent))
    module_spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(module_spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        # Direct entry modules also bypass .pyc and support normal dataclasses.
        exec(compile(Path(path).read_bytes(), str(path), "exec"), module.__dict__)
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module



def image_file_paths(image, abspath):
    """External file/tile paths; evaluated ImageUser adds sequence frames below."""
    raw = getattr(image, "filepath", "")
    if not raw or raw.startswith("<") or getattr(image, "packed_file", None):
        return []
    if getattr(image, "source", "FILE") == "TILED":
        if "<UDIM>" not in raw and "<UVTILE>" not in raw:
            raise ValueError("UDIM image needs an explicit <UDIM> or <UVTILE> file pattern")
        names = []
        for tile in image.tiles:
            number = tile.number; u = (number - 1001) % 10 + 1; v = (number - 1001) // 10 + 1
            names.append(raw.replace("<UDIM>", str(number)).replace("<UVTILE>", f"u{u}_v{v}"))
    else:
        names = [raw]
    return [Path(abspath(name, library=getattr(image, "library", None))).resolve() for name in names]


def check_external_path(path, spec):
    path = Path(path).resolve()
    if not path.is_file() or str(path) not in spec["inputs"]:
        raise ValueError("Declare actual external Blender dependency in inputs: " + str(path))


def audit_blender_inputs(spec, bpy, evaluated=False):
    # Recheck after state changes: an adapter can load a different image/library.
    for collection in (bpy.data.libraries, bpy.data.images, bpy.data.fonts):
        for block in collection:
            for path in image_file_paths(block, bpy.path.abspath):
                check_external_path(path, spec)
    if not evaluated:
        return
    graph = bpy.context.evaluated_depsgraph_get(); graph.update()

    def check_user(owner):
        image = getattr(owner, "image", None); user = getattr(owner, "image_user", None)
        if (image is not None and user is not None and image.source == "SEQUENCE" and
                not getattr(image, "packed_file", None)):
            # Original image_user.frame_current can stay at 0 until rendering.
            # The evaluated datablock carries Blender's real offset/cyclic mapping.
            check_external_path(image.filepath_from_user(image_user=user), spec)

    visited = set()
    def check_tree(tree):
        if tree is None or tree.as_pointer() in visited:
            return
        visited.add(tree.as_pointer())
        for node in tree.nodes:
            check_user(node)
            check_tree(getattr(node, "node_tree", None))

    # A saved fake-user material can have users=1 yet not participate in this
    # scene's dependency graph. Its unevaluated frame_current=0 is not evidence
    # of a missing texture. Inspect actual evaluated IDs and their node trees.
    for block in graph.ids:
        check_tree(block if isinstance(block, bpy.types.NodeTree) else getattr(block, "node_tree", None))
        check_user(block)
        if isinstance(block, bpy.types.Object) and block.type == "EMPTY" and isinstance(block.data, bpy.types.Image):
            if block.data.source == "SEQUENCE":
                check_external_path(block.data.filepath_from_user(image_user=block.image_user), spec)
        if isinstance(block, bpy.types.Camera):
            for background in block.background_images:
                check_user(background)



def apply_color_management(scene, color):
    # Display changes can affect transforms, and transforms can affect looks.
    # Omitted properties are inherited from the authored scene, with no style preset.
    for key in COLOR_MANAGEMENT_KEYS:
        if key not in color:
            continue
        owner = scene.display_settings if key == "display_device" else scene.view_settings
        value = color[key]
        try:
            setattr(owner, key, value)
            actual = getattr(owner, key)
        except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
            raise ValueError(f"Cannot apply render.color_management.{key}={value!r} "
                             f"in this Blender/OCIO configuration: {error}") from error
        matches = (math.isclose(actual, value, rel_tol=1e-6, abs_tol=0.0)
                   if key in ("exposure", "gamma") else actual == value)
        if not matches:
            raise ValueError(f"render.color_management.{key}={value!r} was not applied "
                             f"by this Blender/OCIO configuration (actual {actual!r})")


def configure(scene, render, bpy, refresh_devices=False):
    validate_render_settings(render)
    scene.render.engine = render["engine"]
    scene.render.resolution_x = render["width"]; scene.render.resolution_y = render["height"]
    scene.render.resolution_percentage = 100
    scene.render.fps = render["fps"]; scene.render.fps_base = render.get("fps_base", 1)
    scene.render.image_settings.file_format = render.get("format", "PNG")
    scene.render.image_settings.color_mode = render.get("color_mode", "RGBA")
    scene.render.use_file_extension = True
    if "threads" in render:
        scene.render.threads_mode = "FIXED"; scene.render.threads = render["threads"]
    apply_color_management(scene, render.get("color_management", {}))
    devices = []
    if scene.render.engine == "CYCLES":
        scene.cycles.device = render["device"]; scene.cycles.samples = render["samples"]
        scene.render.use_persistent_data = render.get("persistent_data", True)
        scene.cycles.use_denoising = render.get("denoise", True)
        scene.cycles.denoising_use_gpu = render["device"] == "GPU"
        if render["device"] == "CPU":
            scene.cycles.denoiser = render.get("denoiser", "OPENIMAGEDENOISE")
        elif "denoiser" in render:
            scene.cycles.denoiser = render["denoiser"]
        if "max_bounces" in render:
            scene.cycles.max_bounces = render["max_bounces"]
        if "noise_threshold" in render:
            scene.cycles.use_adaptive_sampling = True
            scene.cycles.adaptive_threshold = render["noise_threshold"]
        if render["device"] == "GPU":
            prefs = bpy.context.preferences.addons["cycles"].preferences
            if refresh_devices or prefs.compute_device_type != render["backend"]:
                prefs.compute_device_type = render["backend"]; prefs.refresh_devices()
            selected = [d for d in prefs.devices if d.type == render["backend"] and d.name == render["device_name"] and
                        ("device_id" not in render or d.id == render["device_id"])]
            if len(selected) != 1:
                raise RuntimeError("Requested GPU is unavailable/ambiguous; no CPU fallback")
            for device in prefs.devices:
                device.use = device == selected[0]
            devices = [{"name": d.name, "id": d.id, "type": d.type, "use": d.use} for d in prefs.devices]
    return {"engine": scene.render.engine, "width": scene.render.resolution_x,
            "height": scene.render.resolution_y, "fps": scene.render.fps,
            "fps_base": scene.render.fps_base, "devices": devices,
            "device": scene.cycles.device if scene.render.engine == "CYCLES" else None,
            "samples": scene.cycles.samples if scene.render.engine == "CYCLES" else None,
            "format": scene.render.image_settings.file_format,
            "color_mode": scene.render.image_settings.color_mode,
            "motion_blur": scene.render.use_motion_blur,
            "view_transform": scene.view_settings.view_transform,
            "look": scene.view_settings.look,
            "exposure": scene.view_settings.exposure,
            "gamma": scene.view_settings.gamma,
            "display_device": scene.display_settings.display_device,
            "persistent_data": scene.render.use_persistent_data,
            "cycles": {key: getattr(scene.cycles, key) for key in
                       ("use_denoising", "denoiser", "denoising_use_gpu", "denoising_input_passes",
                        "denoising_prefilter", "denoising_quality", "use_adaptive_sampling",
                        "adaptive_threshold", "adaptive_min_samples", "max_bounces", "diffuse_bounces",
                        "glossy_bounces", "transmission_bounces", "volume_bounces", "transparent_max_bounces",
                        "sample_clamp_direct", "sample_clamp_indirect", "blur_glossy",
                        "caustics_reflective", "caustics_refractive", "seed", "use_animated_seed")
                       if hasattr(scene.cycles, key)}
                      if scene.render.engine == "CYCLES" else None}


def execute(job, renderer, resume=False, selected=None):
    """renderer builds once and renders frames; also used by offline tests."""
    verify(job)
    spec = job["spec"]; output = Path(spec["output_dir"])
    frames = parse_frames(selected) if selected is not None else spec["frames"]
    if not set(frames) <= set(spec["frames"]):
        raise ValueError("Selected frames are outside this job")
    with job_lock(output), declared_source_imports(spec):
        owner = output / "job.json"
        if owner.exists():
            if not resume or read(owner).get("signature") != job["signature"]:
                raise ValueError("Existing output needs matching job and --resume")
        else:
            if any(p.name != ".render.lock" for p in output.iterdir()):
                raise ValueError("Output directory is not empty and has no matching owner")
            write(owner, job)
        state_path = output / "state.json"
        if state_path.exists() and read(state_path).get("status") == "inputs_changed":
            raise ValueError("Inputs changed during a prior attempt; keep outputs untrusted and prepare a new job")
        verify(job)
        todo = [frame for frame in frames if not valid_frame(job, frame)]
        attempt = {"kind": "blender_sequence_attempt", "signature": job["signature"], "started_at": now(),
                   "pid": os.getpid(), "status": "running", "selected_frames": frames,
                   "reused_frames": len(frames) - len(todo), "rendered_frames": 0,
                   "resource_check_seconds": 0.0, "build_seconds": 0.0,
                   "frame_state_seconds": 0.0, "render_write_seconds": 0.0}
        attempts = output / "attempts"; attempts.mkdir(exist_ok=True)
        attempt_path = attempts / (uuid.uuid4().hex + ".json")
        write(attempt_path, attempt); write(state_path, attempt)
        started = time.monotonic()
        try:
            if todo:
                if spec.get("resource_check"):
                    tic = time.monotonic()
                    result = load_module(spec["resource_check"], "project_resource_check").check(spec)
                    attempt["resource_check"] = result
                    write(attempt_path, attempt)
                    if not isinstance(result, dict) or result.get("ok") is not True:
                        raise RuntimeError("Existing project resource check did not pass; see attempt record")
                    attempt["resource_check_seconds"] = time.monotonic() - tic
                tic = time.monotonic()
                renderer.build(spec)
                attempt["build_seconds"] = time.monotonic() - tic
            for frame in todo:
                image, receipt = frame_paths(output, frame, spec)
                archive_invalid(output, (image, receipt))
                tic = time.monotonic(); metadata, actual = renderer.set_frame(frame, spec)
                state_seconds = time.monotonic() - tic
                tic = time.monotonic(); renderer.render(image)
                render_seconds = time.monotonic() - tic
                check_image(image, spec["render"])
                write(receipt, {"frame": frame, "signature": job["signature"], "sha256": file_hash(image),
                                "actual_render": actual, "metadata": metadata, "state_seconds": state_seconds,
                                "render_write_seconds": render_seconds, "completed_at": now()})
                attempt["rendered_frames"] += 1
                attempt["frame_state_seconds"] += state_seconds
                attempt["render_write_seconds"] += render_seconds
                write(state_path, attempt)
                print(json.dumps({"frame": frame, "rendered": attempt["rendered_frames"], "remaining": len(todo)-attempt["rendered_frames"]}), flush=True)
            verify(job)
            attempt["valid_frames"] = sum(valid_frame(job, frame) for frame in spec["frames"])
            attempt["status"] = "complete_unreviewed" if attempt["valid_frames"] == len(spec["frames"]) else "partial_unreviewed"
        except Exception as error:
            attempt.update(status="failed", error=str(error))
            try:
                verify(job)
            except (OSError, ValueError):
                attempt["status"] = "inputs_changed"
            raise
        finally:
            attempt.update(finished_at=now(), batch_seconds=time.monotonic()-started)
            write(attempt_path, attempt); write(state_path, attempt)
        return attempt


class BlenderRenderer:
    def build(self, spec):
        import bpy
        self.bpy = bpy; self.driver = None
        if Path(bpy.app.binary_path).resolve() != Path(spec["blender_executable"]).resolve():
            raise ValueError("Worker Blender binary differs from the prepared job")
        if spec.get("blend"):
            bpy.ops.wm.open_mainfile(filepath=spec["blend"])
            self.scene = bpy.context.scene
        else:
            self.driver = load_module(spec["driver"], "scene_driver")
            self.scene = self.driver.build(spec)
            if self.scene is None:
                raise ValueError("driver.build(spec) must return its scene")
        bpy.context.window.scene = self.scene
        configure(self.scene, spec["render"], bpy, refresh_devices=True)
        audit_blender_inputs(spec, bpy)
        if spec.get("driver"):
            parent = Path(spec["driver"]).parent
            for module in list(sys.modules.values()):
                raw = getattr(module, "__file__", None)
                if raw:
                    path = Path(raw).resolve()
                    if path.is_file() and path.suffix == ".py" and path.is_relative_to(parent) and str(path) not in spec["inputs"]:
                        raise ValueError("Declare imported project helper in inputs: " + str(path))

    def set_frame(self, frame, spec):
        self.scene.frame_set(frame)
        metadata = self.driver.set_frame(self.scene, frame, spec) if self.driver else {}
        self.bpy.context.view_layer.update()
        actual = configure(self.scene, spec["render"], self.bpy)
        audit_blender_inputs(spec, self.bpy, evaluated=True)
        actual['blender_version'] = self.bpy.app.version_string
        actual['blender_build_hash'] = self.bpy.app.build_hash.decode('ascii')
        return metadata, actual

    def render(self, path):
        self.scene.render.filepath = str(path)
        self.bpy.ops.render.render(write_still=True, scene=self.scene.name)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("spec"); prepare_parser.add_argument("job")
    for name in ("run", "worker"):
        p = sub.add_parser(name); p.add_argument("job"); p.add_argument("--resume", action="store_true")
        p.add_argument("--frames")
        if name == "run": p.add_argument("--blender", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        result = prepare(args.spec, args.job)
        print(json.dumps({"job": str(Path(args.job).resolve()), "signature": result["signature"]})); return 0
    job = read(args.job); verify(job)
    if args.command == "worker":
        print(json.dumps(execute(job, BlenderRenderer(), args.resume, args.frames))); return 0
    if Path(args.blender).resolve() != Path(job['spec']['blender_executable']).resolve():
        raise ValueError("Launch executable differs from the prepared job; prepare a new version")
    command = [str(Path(args.blender).resolve()), "--background", "--factory-startup", "--disable-autoexec",
               "--python-exit-code", "1", "--python", str(Path(__file__).resolve()), "--", "worker", str(Path(args.job).resolve())]
    if args.resume: command.append("--resume")
    if args.frames: command.extend(("--frames", args.frames))
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    try:
        arguments = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else None
        raise SystemExit(main(arguments))
    except (OSError, ValueError, RuntimeError) as error:
        print(str(error), file=sys.stderr); raise SystemExit(1)
