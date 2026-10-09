#!/usr/bin/env python3
"""Optional local Qwen adapter for an explicitly confirmed execution target."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import random
import re
import sys
import tempfile
import threading
from datetime import datetime, timezone


MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
HUB_ENDPOINT = "https://huggingface.co"
DEFAULT_PROFILE = Path(__file__).resolve().parents[1] / "config/series-profile.json"
COMMIT = re.compile(r"[0-9a-f]{40}")
RESERVED_GENERATION_KEYS = {"text", "speaker", "language", "instruct"}
_SYNTHESIS_LOCK = threading.Lock()


class SynthesisError(RuntimeError):
    """An actionable failure without exposing the narration text."""


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def load_runtime():
    # Import only when synthesis is requested; --help and validation need no model.
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    try:
        import numpy as np
        import torch
        import soundfile as sf
        from huggingface_hub import snapshot_download
        from qwen_tts import Qwen3TTSModel
    except ImportError as exc:
        raise SynthesisError(
            "Missing local Qwen dependencies. Use the isolated Python 3.12 "
            "installation commands in references/voice-reference.md."
        ) from exc
    return np, torch, sf, snapshot_download, Qwen3TTSModel


def package_versions():
    versions = {}
    for name in ("qwen-tts", "torch", "transformers", "accelerate", "numpy",
                 "soundfile", "huggingface-hub"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    return versions


def read_settings(profile_path, revision=None, device=None, dtype=None):
    profile_path = Path(profile_path).resolve()
    profile_bytes = profile_path.read_bytes()
    try:
        settings = json.loads(profile_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SynthesisError("The profile must contain valid JSON text.") from exc
    if not isinstance(settings, dict):
        raise SynthesisError("The profile must be an object.")
    audio = settings.get("audio")
    if not isinstance(audio, dict):
        raise SynthesisError("The profile audio must be an object.")
    if audio.get("backend") not in ("local_qwen", "confirm_at_invocation") or audio.get("provider") != "Qwen":
        raise SynthesisError("Only a confirmed local_qwen adapter with the Qwen provider is supported.")
    model_id = audio.get("model_id")
    if model_id != MODEL_ID or audio.get("model") != MODEL_ID.split("/", 1)[1]:
        raise SynthesisError("This backend requires the configured official 1.7B CustomVoice model.")
    adapter_example = audio.get("local_adapter_example", {})
    if not isinstance(adapter_example, dict):
        raise SynthesisError("local_adapter_example must be an object when this optional adapter is selected.")
    selected_revision = (revision if revision is not None else
                         audio.get("model_revision", adapter_example.get("model_revision")))
    if not isinstance(selected_revision, str) or not selected_revision.strip():
        raise SynthesisError("Configure model_revision or supply --revision; revisions are never guessed.")
    for key in ("speaker", "language", "instruct"):
        if not isinstance(audio.get(key), str) or not audio[key].strip():
            raise SynthesisError("The profile must explicitly set speaker, language and instruct.")
    runtime = audio.get("runtime", adapter_example.get("runtime", {}))
    if not isinstance(runtime, dict):
        raise SynthesisError("The profile runtime must be an object.")
    runtime = dict(runtime)
    if device is not None:
        runtime["device"] = device
    if dtype is not None:
        runtime["dtype"] = dtype
    if runtime.get("device") not in ("cpu", "mps") and not re.fullmatch(r"cuda:\d+", str(runtime.get("device"))):
        raise SynthesisError("Set an explicit cpu, mps or cuda:N device; automatic fallback is disabled.")
    if runtime.get("dtype") not in ("float32", "float16", "bfloat16"):
        raise SynthesisError("Set an explicit float32, float16 or bfloat16 dtype.")
    if runtime.get("attn_implementation") not in ("eager", "sdpa", "flash_attention_2"):
        raise SynthesisError("Set an explicit eager, sdpa or flash_attention_2 attention implementation.")
    requested = audio.get("generation_params", adapter_example.get("generation_params"))
    if not isinstance(requested, dict) or RESERVED_GENERATION_KEYS.intersection(requested):
        raise SynthesisError("generation_params must be an object and must not override text or voice identity.")
    if not isinstance(requested.get("non_streaming_mode", True), bool):
        raise SynthesisError("non_streaming_mode must be a boolean.")
    # Check serializability and reject NaN/Infinity before loading a model.
    try:
        json_bytes(requested)
    except (TypeError, ValueError) as exc:
        raise SynthesisError("generation_params must contain finite JSON values.") from exc
    return audio, runtime, requested, selected_revision, hashlib.sha256(profile_bytes).hexdigest()


def snapshot_manifest(snapshot):
    snapshot = Path(snapshot)
    if snapshot.parent.name != "snapshots" or not COMMIT.fullmatch(snapshot.name):
        raise SynthesisError("The Hub did not return a snapshot with a resolved 40-character commit.")
    expected_repo = "models--" + MODEL_ID.replace("/", "--")
    if snapshot.parent.parent.name != expected_repo:
        raise SynthesisError("The returned snapshot does not identify the configured official model repository.")
    try:
        config = json.loads((snapshot / "config.json").read_text(encoding="utf-8"))
        correct_model = (config.get("model_type") == "qwen3_tts" and
                         config.get("tts_model_type") == "custom_voice" and
                         config.get("tts_model_size") == "1b7")
        if not correct_model:
            raise SynthesisError("The cached model configuration is not the required 1.7B CustomVoice model.")
        for needed in ("speech_tokenizer/config.json", "generation_config.json"):
            if not (snapshot / needed).is_file():
                raise SynthesisError("The cached model snapshot is incomplete; download the fixed revision explicitly.")
        if not any(snapshot.glob("*.safetensors")):
            raise SynthesisError("The cached snapshot has no main model safetensors weights.")
    except (OSError, json.JSONDecodeError) as exc:
        raise SynthesisError("The cached model configuration is missing or unreadable.") from exc
    files = []
    for item in sorted(snapshot.rglob("*")):
        relative = item.relative_to(snapshot)
        if item.is_file() and not any(part.startswith(".") for part in relative.parts):
            files.append({"file": relative.as_posix(), "bytes": item.stat().st_size,
                          "sha256": file_sha256(item)})
    return files, hashlib.sha256(json_bytes(files)).hexdigest()


def check_device(torch, runtime):
    device = runtime["device"]
    if device == "mps" and not torch.backends.mps.is_available():
        raise SynthesisError("The requested MPS device is unavailable; no CPU fallback was attempted.")
    if device.startswith("cuda:") and (not torch.cuda.is_available() or
                                      int(device.split(":")[1]) >= torch.cuda.device_count()):
        raise SynthesisError("The requested CUDA device is unavailable; no other device was attempted.")
    if runtime["attn_implementation"] == "flash_attention_2" and not device.startswith("cuda:"):
        raise SynthesisError("This workflow only enables FlashAttention 2 on an explicitly selected CUDA device.")


def publish_pair(wav_temp, record_temp, output, record):
    """Publish complete new artifacts, exclusively; never overwrite accepted media."""
    linked_output = False
    try:
        os.link(wav_temp, output)
        linked_output = True
        os.link(record_temp, record)
    except OSError:
        if linked_output and Path(output).exists() and os.path.samefile(output, wav_temp):
            Path(output).unlink()
        raise


def confirmed_execution(execution_reference, project_dir, cache_dir):
    """Validate the explicit target before any runtime import or output creation."""
    if not isinstance(execution_reference, str) or not execution_reference.strip():
        raise SynthesisError("An explicit execution_reference to the user's local Qwen confirmation is required.")
    targets = {}
    for name, value in (("project_dir", project_dir), ("model_cache_dir", cache_dir)):
        if value is None or not str(value).strip():
            raise SynthesisError("An explicit " + name + " is required; no execution path is selected automatically.")
        path = Path(value).resolve()
        if not path.is_dir():
            raise SynthesisError("The confirmed " + name + " must be an existing directory.")
        targets[name] = str(path)
    return {
        "status": "confirmed", "mode": "local_project", "adapter": "local_qwen",
        "location": targets["project_dir"], "confirmation_reference": execution_reference.strip(),
        "model_cache_dir": targets["model_cache_dir"], "python_executable": sys.executable,
    }


def _synthesize(profile, text_file, output, record, *, revision=None, cache_dir=None,
                allow_model_download=False, seed=None, device=None, dtype=None,
                execution=None):
    for destination in (Path(output), Path(record)):
        if destination.exists() or destination.is_symlink():
            raise SynthesisError("Output or record already exists; choose new versioned filenames.")
    profile, text_file, output, record = map(lambda p: Path(p).resolve(),
                                           (profile, text_file, output, record))
    if output.suffix.lower() != ".wav":
        raise SynthesisError("The source output must be a WAV; postprocess as a separate version.")
    if len({profile, text_file, output, record}) != 4:
        raise SynthesisError("Profile, text, WAV and record must be distinct files.")
    for destination in (output, record):
        if destination.exists() or destination.is_symlink():
            raise SynthesisError("Output or record already exists; choose new versioned filenames.")
    text_bytes = text_file.read_bytes()
    try:
        narration_text = text_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SynthesisError("The narration text must be a UTF-8 text file.") from exc
    if not narration_text.strip():
        raise SynthesisError("The narration text is empty.")
    audio, runtime, requested, requested_revision, profile_hash = read_settings(
        profile, revision, device, dtype)
    if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32):
        raise SynthesisError("Seed must be an integer from 0 to 2^32-1.")
    np, torch, sf, snapshot_download, model_class = load_runtime()
    check_device(torch, runtime)
    try:
        snapshot = Path(snapshot_download(
            repo_id=MODEL_ID, revision=requested_revision,
            cache_dir=str(Path(cache_dir).resolve()) if cache_dir else None,
            endpoint=HUB_ENDPOINT, token=False,
            local_files_only=not allow_model_download,
        ))
    except Exception as exc:
        raise SynthesisError(
            "The requested official model snapshot is unavailable. Offline mode is the default; "
            "prepare the fixed revision in the configured cache or explicitly allow its download."
        ) from exc
    model_files, manifest_hash = snapshot_manifest(snapshot)
    if COMMIT.fullmatch(requested_revision) and requested_revision != snapshot.name:
        raise SynthesisError("The resolved snapshot does not match the explicitly requested commit.")
    # With a complete local path, all model and tokenizer loads remain local.
    load_parameters = {"device_map": runtime["device"], "dtype": runtime["dtype"],
                       "attn_implementation": runtime["attn_implementation"],
                       "local_files_only": True, "use_safetensors": True}
    try:
        model = model_class.from_pretrained(
            str(snapshot), **{**load_parameters, "dtype": getattr(torch, runtime["dtype"])})
        actual_device = str(model.device)
        expected_device = runtime["device"]
        if actual_device != expected_device and not (expected_device in ("cpu", "mps") and
                                                     actual_device == expected_device + ":0"):
            raise SynthesisError("The loaded model is on a different device; implicit device fallback is rejected.")
        speakers = model.get_supported_speakers()
        languages = model.get_supported_languages()
        if not speakers or audio["speaker"].lower() not in {str(s).lower() for s in speakers}:
            raise SynthesisError("The loaded model does not support the configured speaker.")
        if not languages or audio["language"].lower() not in {str(s).lower() for s in languages}:
            raise SynthesisError("The loaded model does not support the configured language.")
        # Resolve using the same helper used by the official wrapper, then pass
        # those values explicitly. Missing helper means incompatible runtime.
        merge = getattr(model, "_merge_generate_kwargs", None)
        if not callable(merge):
            raise SynthesisError("The installed Qwen wrapper cannot expose effective generation parameters.")
        params = dict(requested)
        non_streaming_mode = params.pop("non_streaming_mode", True)
        effective = merge(**params)
        json_bytes(effective)
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
        wavs, sample_rate = model.generate_custom_voice(
            text=narration_text, speaker=audio["speaker"], language=audio["language"],
            instruct=audio["instruct"], non_streaming_mode=non_streaming_mode, **effective)
    except SynthesisError:
        raise
    except Exception as exc:
        raise SynthesisError(
            "Local Qwen loading or generation failed (" + type(exc).__name__ + "). "
            "No alternate model, device or service was attempted."
        ) from exc
    if not isinstance(wavs, (list, tuple)) or len(wavs) != 1:
        raise SynthesisError("Expected exactly one source waveform for this complete text input.")
    waveform = np.asarray(wavs[0], dtype=np.float32)
    if waveform.ndim != 1 or waveform.size == 0 or not np.isfinite(waveform).all():
        raise SynthesisError("The returned waveform is empty, non-mono or contains non-finite samples.")
    if not isinstance(sample_rate, int) or isinstance(sample_rate, bool) or sample_rate <= 0:
        raise SynthesisError("The returned sample rate is invalid.")
    peak = float(np.abs(waveform).max())
    if peak == 0:
        raise SynthesisError("The returned waveform is entirely silent.")
    output.parent.mkdir(parents=True, exist_ok=True)
    record.parent.mkdir(parents=True, exist_ok=True)
    temporary = []
    try:
        for parent, suffix in ((output.parent, ".wav"), (record.parent, ".json")):
            handle = tempfile.NamedTemporaryFile(prefix=".qwen-", suffix=suffix, dir=parent, delete=False)
            handle.close()
            temporary.append(Path(handle.name))
        wav_temp, record_temp = temporary
        # FLOAT preserves source values; do not silently normalize, clip or resample.
        sf.write(str(wav_temp), waveform, sample_rate, format="WAV", subtype="FLOAT")
        info = sf.info(str(wav_temp))
        if info.frames != waveform.size or info.samplerate != sample_rate or info.channels != 1:
            raise SynthesisError("The written WAV does not match the generated waveform.")
        provenance = {
            "schema_version": 1, "status": "generated", "backend": "local_qwen", "provider": "Qwen",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model_id": MODEL_ID, "requested_revision": requested_revision,
            "resolved_model_revision": snapshot.name, "model_snapshot": str(snapshot),
            "model_manifest_sha256": manifest_hash, "model_files": model_files,
            "model_download": {"allowed": allow_model_download, "endpoint": HUB_ENDPOINT,
                               "text_sent_to_remote_service": False},
            "execution": {**execution, "working_directory": str(Path.cwd())},
            "voice": {key: audio[key] for key in ("speaker", "language", "instruct")},
            "load_parameters": load_parameters,
            "actual_device": actual_device,
            "requested_generation_params": requested,
            "effective_generation_params": {"non_streaming_mode": non_streaming_mode, **effective},
            "seed": seed, "reproducibility": "Parameters and artifacts are recorded; bitwise identity is not guaranteed.",
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "package_versions": package_versions()},
            "implementation": {"file": str(Path(__file__).resolve()), "sha256": file_sha256(__file__)},
            "profile": {"file": str(profile), "sha256": profile_hash},
            "input": {"file": str(text_file), "sha256": hashlib.sha256(text_bytes).hexdigest(),
                      "encoding": "utf-8", "text_transformation": "none"},
            "output": {"file": str(output), "sha256": file_sha256(wav_temp), "format": "WAV",
                       "subtype": "FLOAT", "sample_rate": sample_rate, "channels": 1,
                       "frames": int(waveform.size), "duration_seconds": waveform.size / sample_rate,
                       "peak_sample": peak, "postprocess": "none"},
            "listening": {"status": "pending", "scope": "source_voice_track", "heard": False},
        }
        record_temp.write_bytes(json_bytes(provenance))
        publish_pair(wav_temp, record_temp, output, record)
        return provenance
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def synthesize(profile, text_file, output, record, *, execution_reference=None,
               project_dir=None, cache_dir=None, **options):
    # cwd and RNG state are process-wide. Concurrent calls to this adapter must
    # wait until the previous invocation has restored and removed its workspace.
    with _SYNTHESIS_LOCK:
        return _synthesize_serialized(
            profile, text_file, output, record, execution_reference=execution_reference,
            project_dir=project_dir, cache_dir=cache_dir, **options)


def _synthesize_serialized(profile, text_file, output, record, *, execution_reference,
                          project_dir, cache_dir, **options):
    execution = confirmed_execution(execution_reference, project_dir, cache_dir)
    # Native dependency initialization can create relative session files. Keep
    # those side effects in disposable private storage, outside a repository.
    for destination in (Path(output), Path(record)):
        if destination.exists() or destination.is_symlink():
            raise SynthesisError("Output or record already exists; choose new versioned filenames.")
    paths = [Path(path).resolve() for path in (profile, text_file, output, record)]
    options["cache_dir"] = Path(execution["model_cache_dir"])
    paths[2].parent.mkdir(parents=True, exist_ok=True)
    previous_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix=".qwen-runtime-", dir=paths[2].parent) as private_work:
        try:
            os.chdir(private_work)
            return _synthesize(*paths, execution=execution, **options)
        finally:
            os.chdir(previous_cwd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--text-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New source .wav file; never overwrites")
    parser.add_argument("--record", type=Path, required=True, help="New private generation .json record")
    parser.add_argument("--revision", help="Explicit model revision override, resolved to a full commit")
    parser.add_argument("--execution-reference", required=True,
                        help="Reference to the user's explicit confirmation of this local target")
    parser.add_argument("--project-dir", type=Path, required=True,
                        help="Existing Qwen project directory explicitly selected for this invocation")
    parser.add_argument("--cache-dir", type=Path, required=True,
                        help="Existing model cache explicitly selected for this invocation")
    parser.add_argument("--allow-model-download", action="store_true", help="Allow official public weights download; text stays local")
    parser.add_argument("--device", help="Explicit profile override: cpu, mps or cuda:N")
    parser.add_argument("--dtype", choices=("float32", "float16", "bfloat16"))
    parser.add_argument("--seed", type=int)
    args = parser.parse_args(argv)
    try:
        result = synthesize(args.profile, args.text_file, args.output, args.record,
                            execution_reference=args.execution_reference, project_dir=args.project_dir,
                            revision=args.revision, cache_dir=args.cache_dir,
                            allow_model_download=args.allow_model_download,
                            seed=args.seed, device=args.device, dtype=args.dtype)
    except Exception as exc:
        # Never print library exceptions that might echo the private input text.
        message = str(exc) if isinstance(exc, SynthesisError) else type(exc).__name__
        print(json.dumps({"status": "failed", "error": message}, ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps({"status": result["status"], "output": result["output"]["file"],
                      "record": str(args.record.resolve()), "listening": "pending"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
