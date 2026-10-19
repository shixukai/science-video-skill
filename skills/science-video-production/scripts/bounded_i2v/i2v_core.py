"""Project-only one-shot raw visual test. Not a Skill gate or quality approval.

No service startup, installs, arbitrary commands, redirects, proxy, cancel or retry.
A 600s maximum observation budget is NOT a GPU execution timeout guarantee.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import http.client
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
from fractions import Fraction
import time
import uuid
ROOT = Path(__file__).resolve().parent
ENDPOINT = 'http://127.0.0.1:8199'
ATTEMPT = 'technical-test-one-shot-attempt.json'
OUTCOME = 'technical-test-one-shot-outcome.json'
LIMITS = 'AI generated, not real recording. Internal silent raw test only; not audiovisual, science, G3 or delivery approval. Observation expiry does not terminate GPU work.'

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def digest_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def sha(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()

def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()

def stamp(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(d.utcoffset() is not None, 'timezone required')
    return d.timestamp()

def now():
    return datetime.now(timezone.utc).isoformat()

def regular(path):
    p = Path(path)
    require(not p.is_symlink() and p.is_file(), 'missing/symlink file: ' + str(p))
    require(not any((x.is_symlink() for x in p.parents)), 'symlink parent forbidden')
    return p.resolve()

def read_pinned(path, expected):
    require(isinstance(expected, str) and re.fullmatch('[a-f0-9]{64}', expected), 'explicit expected SHA256 required')
    p = regular(path)
    raw = p.read_bytes()
    require(digest_bytes(raw) == expected, 'hash mismatch: ' + str(p))
    return json.loads(raw)

def absolute(value):
    require(isinstance(value, str) and Path(value).is_absolute(), 'explicit absolute local path required')
    p = Path(value)
    require(not p.is_symlink() and (not any((x.is_symlink() for x in p.parents))), 'symlink path forbidden')
    return p.resolve()


def evidence(root, ref):
    p = absolute(ref['path'])
    # Exact independently reviewed absolute references may reuse immutable shared evidence.
    return read_pinned(p, ref['sha256'])

def freshness(record, max_age=60):
    age = time.time() - stamp(record['observed_at'])
    require(0 <= age <= max_age, 'stale/future resource or service observation')

def check_gpu_observation(resource, policy):
    """Preserve WDDM PID evidence; low aggregate load is not per-PID attribution."""
    pids = resource['gpu_process_pids']
    require(isinstance(pids, list) and all((type(pid) is int and pid > 0 for pid in pids)) and (len(set(pids)) == len(pids)), 'complete GPU PID observation must be a unique integer list')
    unknown = resource.get('unattributed_gpu_process_pids', [])
    require(isinstance(unknown, list) and all((type(pid) is int and pid in pids for pid in unknown)), 'unattributed PIDs must remain within observed full list')
    load = resource['gpu_load']
    require(load['status'] == 'measured' and load['metric'] == 'gpu_total_utilization_percent' and isinstance(load['observation_source'], str) and load['observation_source'].strip(), 'actual short-window aggregate GPU observation required; unknown heavy load blocks')
    require(resource['heavy_load_assessment'] == 'not_observed_in_sample_window', 'observed or unknown heavy load blocks this attempt')
    number = lambda x: type(x) in (int, float) and x == x and (abs(x) != float('inf'))
    maximum = policy['max_utilization_percent']
    window = policy['minimum_window_seconds']
    count = policy['minimum_sample_count']
    require(number(maximum) and 0 <= maximum < 100 and number(window) and (0 < window <= 60) and (type(count) is int) and (2 <= count <= 60) and isinstance(policy['basis'], str) and policy['basis'].strip(), 'independently justified finite load threshold and short-window policy required')
    samples = load['samples']
    require(isinstance(samples, list) and count <= len(samples) <= 120, 'insufficient aggregate load samples')
    times = []
    for sample in samples:
        freshness(sample)
        value = sample['utilization_percent']
        require(number(value) and 0 <= value <= 100 and (value <= maximum), 'aggregate GPU load exceeds reviewed budget or is unknown')
        times.append(stamp(sample['observed_at']))
    require(all((a < b for a, b in zip(times, times[1:]))) and times[-1] - times[0] >= window and (times[-1] <= stamp(resource['observed_at'])), 'aggregate sample timestamps/window invalid')

def check_condition_image(bindings, *, c):
    row = bindings['condition_image']
    name = row['basename']
    require(isinstance(name, str) and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]*\\.png', name) and ('..' not in name), 'controlled plain PNG basename required; no URL/path/Comfy annotation')
    input_root = absolute(bindings['service_identity']['input_root'])
    require(input_root.is_dir(), 'actual service input root required')
    path = regular(absolute(row['path']))
    require(path == input_root / name and row['sha256'] == c['image_sha256'] and (sha(path) == c['image_sha256']), 'exact original PNG inside actual service input root required')
    with path.open('rb') as f:
        header = f.read(24)
    require(len(header) == 24 and header[:8] == b'\x89PNG\r\n\x1a\n' and (header[8:16] == b'\x00\x00\x00\rIHDR') and (int.from_bytes(header[16:20], 'big') == 832) and (int.from_bytes(header[20:24], 'big') == 480), 'reviewed adapted PNG IHDR must be832x480')
    return name

def case4_graph(bindings, root, source, *, c):
    require(str(root) == c['candidate_root'], 'fixed canonical glass candidate root required')
    require(bindings['case_id'] == c['shot_id'], 'wrong glass candidate')
    read_pinned(absolute(c['design_path']), c['design_sha256'])
    name = check_condition_image(bindings, c=c)
    graph = source.get('prompt', source)
    require(graph[c['image_node']] == {'class_type': 'LoadImage', 'inputs': {'image': name}}, 'exact reviewed image binding required')
    require(graph['55']['inputs']['start_image'] == [c['image_node'], 0], 'exact native input edge required')
    return graph

def startup_record(bindings, root, *, c):
    record = evidence(root, bindings['startup_record'])
    require(record['endpoint'] == ENDPOINT and record['comfy_root'] == c['environment']['comfy_root'] and (record['executable_path'] in c['environment']['service_executables']), 'startup must be fixed existing Comfy installation and endpoint')
    require(all((type(record[k]) is int and record[k] > 0 for k in ('service_pid', 'parent_pid'))), 'startup process IDs must be positive integers')
    require(sha(regular(absolute(record['executable_path']))) == c['environment']['service_executables'][record['executable_path']], 'actual service interpreter changed')
    stamp(record['created_at'])
    launch = evidence(root, bindings['launch_evidence'])
    observed = evidence(root, bindings['identity_evidence'])
    require(observed['source_tool_exit_code'] == 0 and observed['source_sandbox_permissions'] == 'require_escalated', 'formal identity evidence missing')
    require(observed['startup_record_sha256'] == bindings['launch_evidence']['sha256'], 'identity/launch linkage differs')
    require(launch['LauncherPID'] == record['parent_pid'], 'service parent differs from owned launcher')
    require(record['identity_processes'] == observed['processes'], 'exact observed process chain differs')
    require(observed['port8199_listeners'] == [{'LocalAddress': '127.0.0.1', 'LocalPort': 8199, 'OwningProcess': record['service_pid']}], 'observed listener differs')
    require(launch['Executable'] in c['environment']['service_executables'] and sha(regular(absolute(launch['Executable']))) == c['environment']['service_executables'][launch['Executable']], 'actual launcher interpreter changed')
    argv = launch['Arguments']
    require(c['environment']['comfy_entrypoint'] in argv and argv[argv.index('--models-directory') + 1] == c['environment']['models_directory'] and (argv[argv.index('--extra-model-paths-config') + 1] == c['environment']['extra_model_paths']), 'pinned launch model configuration differs')
    require(argv[argv.index('--input-directory') + 1] == record['input_root'] and argv[argv.index('--output-directory') + 1] == record['output_root'], 'startup root intent differs')
    require(record['entrypoint']['path'] == c['environment']['comfy_entrypoint'] and sha(regular(absolute(record['entrypoint']['path']))) == record['entrypoint']['sha256'], 'actual fixed Comfy entrypoint changed')
    require(record['output_root'] == bindings['output_root'], 'startup output root must match the unchanged reused service')
    require(bindings['service_identity'] == record, 'service identity must exactly equal pinned startup record')
    return record

def preflight(bindings_sha256, root=ROOT, *, c):
    root = Path(root).resolve()
    require(not (root / ATTEMPT).exists() and (not (root / OUTCOME).exists()), 'one-shot already reserved/attempted; uncertain outcomes must be read-only reconciled, never resubmitted')
    bindings = read_pinned(root / 'technical_test_bindings.json', bindings_sha256)
    require(bindings['kind'] == 'reviewed_one_shot_rain_test_bindings_v1', 'wrong binding scope')
    require(absolute(bindings['project_root']) == root, 'wrong project root')
    require(bindings['endpoint'] == ENDPOINT, 'only already-ready127.0.0.1:8199 allowed')
    require(bindings['config_sha256'] == c['config_sha256'], 'runtime bindings differ from reviewed config')
    spec_scope = read_pinned(absolute(c['scope_path']), c['scope_sha256'])
    require(spec_scope['shot_id'] == c['shot_id'] and spec_scope['intended_frames'] == 49 and (spec_scope['audio_tracks'] == 0), 'bounded silent stage differs')
    authorization = evidence(root, bindings['authorization_evidence'])
    require(authorization['shot_id'] == c['shot_id'] and authorization['action'] == 'one_bounded_silent_i2v_generation' and authorization['source_ref'] and authorization['verbatim_user_instruction'], 'explicit current generation authority missing')
    manifest = read_pinned(absolute(c['skill_manifest_path']), c['skill_manifest_sha256'])
    require(manifest['installed_version'] == c['skill_version'] and len(manifest['files']) == c['skill_file_count'], 'actual applicable stage Skill snapshot differs')
    for row in manifest['files']:
        p = regular(absolute(row['source_path']))
        require(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'actual installed stage Skill bytes changed')
    spec = {'models': {'diffusion': 'wan2.2_ti2v_5B_fp16.safetensors', 'vae': 'wan2.2_vae.safetensors', 'text_encoder': 'umt5_xxl_fp8_e4m3fn_scaled.safetensors'}}
    source_path = absolute(bindings['api_source_path'])
    source = read_pinned(source_path, c['api_sha256'])
    startup_record(bindings, root, c=c)
    graph = case4_graph(bindings, root, source, c=c)
    require(digest_bytes(canonical(graph)) == bindings['derived_graph_sha256'], 'derived graph does not match independently reviewed digest')
    save = [n for n in graph.values() if n['class_type'] == 'SaveVideo']
    require(len(save) == 1 and save[0]['inputs']['filename_prefix'] == c['output_prefix'], 'fixed relative output prefix required')
    output_root = absolute(bindings['output_root'])
    require(output_root.is_dir(), 'existing Comfy output root required')
    require(not list(output_root.rglob(c['output_prefix'] + '*')), 'existing candidate output found; reconcile instead of regenerating')
    require(set(bindings['models']) == set(spec['models']), 'exact three model roles required')
    provenance = evidence(root, bindings['model_provenance'])
    require(provenance['kind'] == 'existing_model_file_inspection' and provenance['no_download_or_install'] is True, 'existing actual model inspection source required')
    require(isinstance(provenance.get('inspection_source'), str) and provenance['inspection_source'].strip(), 'model inspection source missing')
    require(provenance['endpoint'] == ENDPOINT and provenance['service_identity'] == bindings['service_identity'], 'model loader resolution belongs to a different service')
    for role, name in spec['models'].items():
        row = bindings['models'][role]
        p = regular(absolute(row['path']))
        roots = [absolute(value) for value in row['loader_roots']]
        require(bool(roots) and all((r.is_dir() for r in roots)) and any((p.is_relative_to(r) for r in roots)) and (p.name == name), 'model role-specific loader root/path/name differs')
        config = row['configuration_source']
        require(sha(regular(absolute(config['path']))) == config['sha256'], 'actual loader configuration source changed')
        require(type(row['bytes']) is int and row['bytes'] > 0 and (p.stat().st_size == row['bytes']), 'model size mismatch')
        require(sha(p) == row['sha256'], 'actual model hash mismatch')
        require(provenance['models'][role] == row, 'model provenance differs from actual bindings')
        require(provenance['loader_resolution'][role] == {'configured_name': name, 'resolved_path': str(p), 'loader_roots': row['loader_roots'], 'configuration_source': row['configuration_source']}, 'actual Comfy loader resolution must identify this exact file')
    require('resource_evidence' not in bindings and 'submit_not_after' not in bindings, 'v3 static bindings must not contain expiring resource evidence or a pre-review submission deadline')
    check_collector(bindings['collector'], root)
    for key in ('worker_id', 'unique_executor_lock'):
        require(isinstance(bindings[key], str) and bindings[key].strip(), 'named task worker and executor lock required')
    for key in ('ram_available_bytes', 'vram_available_bytes', 'disk_available_bytes'):
        require(type(bindings['minimum_resources'][key]) is int and bindings['minimum_resources'][key] > 0, 'positive independently reviewed resource threshold required')
    require(type(bindings['observation_budget_seconds']) is int and 1 <= bindings['observation_budget_seconds'] <= 600, 'observation budget must be1..600 seconds')
    require(type(bindings['submission_budget_seconds']) is int and 1 <= bindings['submission_budget_seconds'] <= 600, 'runtime submission budget must be1..600 seconds')
    require(bindings['observation_timeout_is_not_gpu_termination'] is True, 'must acknowledge observation vs GPU timeout')
    return (bindings, graph)

def check_collector(collector, root):
    require(collector['protocol'] == 'rain-resource-collector-v1', 'fixed collector protocol required')
    path = regular(absolute(collector['path']))
    require(path.parent == Path(__file__).resolve().parent and path.name == 'rain_resource_collector.py', 'fixed local reviewed collector path required')
    interpreter = regular(absolute(collector['interpreter']['path']))
    require(interpreter.name.casefold() in ('python', 'python3', 'python.exe'), 'existing verified Python interpreter required')
    require(sha(path) == collector['sha256'] and sha(interpreter) == collector['interpreter']['sha256'], 'collector or interpreter hash changed')
    require(type(collector['timeout_seconds']) is int and 1 <= collector['timeout_seconds'] <= 30, 'collector timeout must be1..30 seconds')
    require(set(collector) == {'protocol', 'path', 'sha256', 'interpreter', 'timeout_seconds'}, 'no arbitrary collector commands, args or environment allowed')
    return (path, interpreter)

def validate_dynamic(resource, bindings, collection_id, started, finished):
    require(resource['collection_id'] == collection_id, 'resource snapshot belongs to another collection')
    require(started <= stamp(resource['observed_at']) <= finished, 'resource observation predates this collection or is future')
    for sample in resource['gpu_load']['samples']:
        require(started <= stamp(sample['observed_at']) <= finished, 'GPU sample predates this collection or is future')
    freshness(resource)
    require(resource['lock_evidence']['holder_pid'] == bindings['executor_lock']['holder_pid'] and resource['lock_evidence']['path'] == bindings['executor_lock']['path'] and (abs(stamp(resource['lock_evidence']['holder_creation_time']) - stamp(bindings['executor_lock']['holder_creation_time'])) <= 0.001) and (resource['lock_evidence']['collector_parent_pid'] == bindings['executor_lock']['holder_pid']) and (resource['lock_evidence']['byte_lock_held'] is True), 'actual parent lock-holder evidence required')
    require(resource['kind'] == 'local_process_gpu_queue_inspection', 'actual local resource inspection required')
    require(resource['endpoint'] == ENDPOINT and resource['service_ready'] is True and (resource['queue_empty'] is True), 'existing ready service and empty queue required')
    require(type(resource['service_pid']) is int and resource['service_pid'] > 0 and (resource['service_identity'] == bindings['service_identity']), 'existing service identity mismatch')
    require(resource['active_worker_ids'] == [bindings['worker_id']], 'unique task worker claim inconsistent')
    check_gpu_observation(resource, bindings['gpu_load_policy'])
    require(resource['output_root'] == str(absolute(bindings['output_root'])), 'service output path differs from frozen path')
    require(isinstance(bindings['worker_id'], str) and bindings['worker_id'].strip(), 'named unique executor required')
    require(isinstance(bindings['unique_executor_lock'], str) and bindings['unique_executor_lock'].strip(), 'external executor-lock identity required')
    require(resource['inspection_source'] and resource['unique_executor_lock'] == bindings['unique_executor_lock'], 'fresh externally established executor lock required')
    for key in ('ram_available_bytes', 'vram_available_bytes', 'disk_available_bytes'):
        require(type(resource[key]) is int and resource[key] >= bindings['minimum_resources'][key] > 0, 'insufficient checked resource: ' + key)

def collect_dynamic(bindings, root, collection_id):
    """Invoke only an independently reviewed, fixed read-only collector after hashing."""
    root = Path(root).resolve()
    collector = bindings['collector']
    path, interpreter = check_collector(collector, root)
    require(bindings['executor_lock']['holder_pid'] == os.getpid(), 'gate.submit must run inside the actual outer lock-holder process')
    request = {'protocol': 'rain-resource-collector-v1', 'collection_id': collection_id, 'endpoint': ENDPOINT, 'service_identity': bindings['service_identity'], 'input_root': bindings['service_identity']['input_root'], 'worker_id': bindings['worker_id'], 'unique_executor_lock': bindings['unique_executor_lock'], 'output_root': bindings['output_root'], 'gpu_load_policy': bindings['gpu_load_policy'], 'executor_lock': bindings['executor_lock'], 'startup_record': bindings['startup_record'], 'environment': bindings['environment'], 'workspace_gpu_lock_path': bindings['workspace_gpu_lock_path']}
    request_path = root / ('resource-request-' + collection_id + '.json')
    persist_new(request_path, request)
    started = time.time()
    invocation_path = root / ('collector-invocation-' + collection_id + '.json')
    try:
        result = subprocess.run([str(interpreter), '-I', '-S', '-B', '-X', 'utf8', str(path), '--request-json', str(request_path)], cwd=root, capture_output=True, text=True, timeout=collector['timeout_seconds'], shell=False)
    except subprocess.TimeoutExpired as exc:

        def text(value):
            return value.decode('utf-8', errors='replace') if isinstance(value, bytes) else value or ''
        persist_new(invocation_path, {'state': 'collector_timeout_NOT_ADMITTED', 'collection_id': collection_id, 'started_unix': started, 'finished_unix': time.time(), 'stdout': text(exc.stdout)[:4 * 1024 * 1024], 'stderr': text(exc.stderr)[:65536], 'output_may_be_truncated': True, 'error': str(exc)})
        raise
    finished = time.time()
    persist_new(invocation_path, {'state': 'collector_returned_NOT_YET_ADMITTED', 'collection_id': collection_id, 'started_unix': started, 'finished_unix': finished, 'returncode': result.returncode, 'stdout': result.stdout[:4 * 1024 * 1024], 'stderr': result.stderr[:65536], 'stdout_characters': len(result.stdout), 'stderr_characters': len(result.stderr), 'output_truncated': len(result.stdout) > 4 * 1024 * 1024 or len(result.stderr) > 65536})
    require(result.returncode == 0 and len(result.stdout.encode('utf-8')) <= 4 * 1024 * 1024, 'read-only collector failed or returned oversized data; no submission')
    check_collector(collector, root)
    resource = json.loads(result.stdout)
    snapshot_path = root / ('dynamic-resource-' + collection_id + '.json')
    persist_new(snapshot_path, resource)
    try:
        validate_dynamic(resource, bindings, collection_id, started, finished)
    except Exception as exc:
        persist_new(root / ('resource-admission-failure-' + collection_id + '.json'), {'state': 'NOT_ADMITTED_NO_POST', 'collection_id': collection_id, 'error': str(exc), 'resource_file': snapshot_path.name, 'resource_sha256': sha(snapshot_path), 'invocation_file': invocation_path.name, 'invocation_sha256': sha(invocation_path)})
        raise
    return (resource, {'file': snapshot_path.name, 'sha256': sha(snapshot_path), 'collection_id': collection_id, 'collection_started_unix': started, 'collection_finished_unix': finished})

def persist_new(path, record):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 384)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())

def request_local(method, path, payload=None, timeout=10):
    require(method == 'POST' and path == '/prompt' or (method == 'GET' and (path == '/queue' or re.fullmatch('/history/[a-f0-9-]{36}', path))), 'unapproved endpoint operation')
    require(isinstance(timeout, (int, float)) and 0 < timeout <= 10, 'HTTP timeout must be at most10s')
    conn = http.client.HTTPConnection('127.0.0.1', 8199, timeout=timeout)
    try:
        body = canonical(payload) if payload is not None else None
        conn.request(method, path, body=body, headers={'Content-Type': 'application/json'})
        response = conn.getresponse()
        raw = response.read(4 * 1024 * 1024 + 1)
        require(response.status == 200 and len(raw) <= 4 * 1024 * 1024, 'response rejected; outcome may be unknown')
        return json.loads(raw)
    finally:
        conn.close()

def submit(bindings_sha256, root=ROOT, *, c):
    runtime_start = time.monotonic()
    root = Path(root).resolve()
    bindings, graph = preflight(bindings_sha256, root, c=c)
    submission_deadline = runtime_start + bindings['submission_budget_seconds']
    require(time.monotonic() < submission_deadline, 'runtime hash/preflight exceeded submission budget')
    client_id = str(uuid.uuid4())
    attempt = {'case_id': c['shot_id'], 'parent_prompt_id': c['parent_prompt_id'], 'case_spec_sha256': c['design_sha256'], 'kind': 'one_shot_attempt', 'state': 'reserved_outcome_unknown_until_readback', 'created_at': now(), 'bindings_sha256': bindings_sha256, 'graph_sha256': digest_bytes(canonical(graph)), 'client_id': client_id, 'endpoint': ENDPOINT, 'spec_sha256': c['scope_sha256'], 'authorization_sha256': bindings['authorization_evidence']['sha256'], 'observation_budget_seconds': bindings['observation_budget_seconds'], 'collector': bindings['collector'], 'submission_budget_seconds': bindings['submission_budget_seconds'], 'limits': LIMITS}
    persist_new(root / ATTEMPT, attempt)
    post_started = False
    failure_stage = 'collector'
    snapshot = None
    try:
        resource, snapshot = collect_dynamic(bindings, root, client_id)
        failure_stage = 'live_queue'
        queue = request_local('GET', '/queue')
        require(isinstance(queue, dict) and queue.get('queue_running') == [] and (queue.get('queue_pending') == []), 'live queue must be structurally empty; stop without POST')
        failure_stage = 'final_dynamic_validation'
        check_condition_image(bindings, c=c)
        validate_dynamic(resource, bindings, client_id, snapshot['collection_started_unix'], snapshot['collection_finished_unix'])
        require(bindings['executor_lock']['holder_pid'] == os.getpid(), 'outer lock-holder identity changed')
        require(time.monotonic() < submission_deadline, 'runtime submission deadline reached before POST')
        persist_new(root / 'dynamic-admission.json', {'state': 'automated_independent_collector_validated', 'collection_id': client_id, 'holder': resource['lock_evidence'], 'resource': snapshot, 'config_sha256': bindings['config_sha256'], 'recorded_at': now()})
        failure_stage = 'post_response'
        post_started = True
        result = request_local('POST', '/prompt', {'prompt': graph, 'client_id': client_id})
        prompt_id = result.get('prompt_id')
        require(isinstance(prompt_id, str) and str(uuid.UUID(prompt_id)) == prompt_id and (not result.get('node_errors')), 'no unambiguous accepted prompt ID; do not retry')
        outcome = {'state': 'accepted_unreviewed', 'prompt_id': prompt_id, 'post_started': True, 'dynamic_resource': snapshot, 'recorded_at': now(), 'limits': LIMITS}
    except Exception as exc:
        outcome = {'state': 'unknown_do_not_retry' if post_started else 'known_no_post', 'post_started': post_started, 'failure_stage': failure_stage, 'dynamic_resource': snapshot, 'error': str(exc), 'recorded_at': now(), 'limits': LIMITS}
    persist_new(root / OUTCOME, outcome)
    return outcome

def observe(root=ROOT, *, c):
    """Read-only queue/history diagnostics. Never cancels or submits anything."""
    root = Path(root).resolve()
    attempt = json.loads(regular(root / ATTEMPT).read_text())
    outcome = json.loads(regular(root / OUTCOME).read_text())
    require(attempt['endpoint'] == ENDPOINT and attempt['spec_sha256'] == c['scope_sha256'], 'wrong attempt scope')
    require(outcome['state'] == 'accepted_unreviewed', 'unknown submission: inspect fixed service queue/history manually by client_id; never retry POST')
    prompt_id = outcome['prompt_id']
    require(str(uuid.UUID(prompt_id)) == prompt_id, 'invalid prompt ID')
    deadline = stamp(attempt['created_at']) + min(600, attempt['observation_budget_seconds'])
    saved = root / 'technical-test-history.json'
    if saved.exists():
        record = json.loads(regular(saved).read_text())
        require(record['prompt_id'] == prompt_id, 'saved history belongs to different prompt')
        return {'state': 'history_saved_requires_actual_output_verification', 'history': record['history'], 'limits': LIMITS}
    monotonic_deadline = time.monotonic() + max(0, min(600, deadline - time.time()))
    while time.monotonic() < monotonic_deadline:
        remaining = monotonic_deadline - time.monotonic()
        if remaining <= 0:
            break
        history = request_local('GET', '/history/' + prompt_id, timeout=min(10, remaining))
        if prompt_id in history:
            record = {'prompt_id': prompt_id, 'history': history[prompt_id], 'observed_at': now(), 'limits': LIMITS}
            persist_new(root / 'technical-test-history.json', record)
            return {'state': 'history_saved_requires_actual_output_verification', 'history': history[prompt_id], 'limits': LIMITS}
        time.sleep(min(10, max(0, monotonic_deadline - time.monotonic())))
    return {'state': 'observation_budget_expired_GPU_may_still_be_running', 'prompt_id': prompt_id, 'next_action': 'Do not resubmit or use global interrupt. Reconcile this exact prompt read-only; report to owner.', 'limits': LIMITS}
ALLOWED = {('57', 'inputs', 'fps'), ('3', 'inputs', 'denoise'), ('3', 'inputs', 'cfg'), ('48', 'inputs', 'shift')}

def compare_graph(expected, actual):
    differences = []

    def walk(a, b, path):
        if path in ALLOWED:
            require(type(a) in (int, float) and type(b) in (int, float), 'non-numeric/bool at ' + str(path))
            require((type(a) is int or math.isfinite(a)) and (type(b) is int or math.isfinite(b)), 'nonfinite at ' + str(path))
            require(Fraction(a) == Fraction(b), 'numeric value changed at ' + str(path))
            if type(a) is not type(b):
                differences.append({'path': '/' + '/'.join(path), 'expected_type': type(a).__name__, 'expected_value': a, 'server_type': type(b).__name__, 'server_value': b, 'reason': 'exact rational numeric equality at explicit schema field'})
            return
        require(type(a) is type(b), 'type changed at ' + str(path))
        if type(a) is dict:
            require(a.keys() == b.keys(), 'keys changed at ' + str(path))
            for key in a:
                walk(a[key], b[key], path + (key,))
        elif type(a) is list:
            require(len(a) == len(b), 'array length changed at ' + str(path))
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, path + (str(i),))
        else:
            require(not (type(a) is float and (not math.isfinite(a) or not math.isfinite(b))), 'nonfinite outside whitelist')
            require(a == b, 'value changed at ' + str(path))
    walk(expected, actual, ())
    return differences

def verify_output(bindings_sha256, root=ROOT, *, c):
    """Offline actual decode metadata check. No network, installs or quality verdict."""
    root = Path(root).resolve()
    bindings = read_pinned(root / 'technical_test_bindings.json', bindings_sha256)
    attempt = json.loads(regular(root / ATTEMPT).read_text())
    outcome = json.loads(regular(root / OUTCOME).read_text())
    record = json.loads(regular(root / 'technical-test-history.json').read_text())
    require(attempt['bindings_sha256'] == bindings_sha256 and attempt['spec_sha256'] == c['scope_sha256'] and (attempt['authorization_sha256'] == bindings['authorization_evidence']['sha256']) and (attempt['endpoint'] == ENDPOINT) and (outcome['state'] == 'accepted_unreviewed') and (record['prompt_id'] == outcome['prompt_id']), 'output history must bind this exact accepted attempt')
    history = record['history']
    require(history['status']['completed'] is True and history['status']['status_str'] == 'success', 'history is not successful completion')
    prompt = history['prompt']
    source = read_pinned(absolute(bindings['api_source_path']), c['api_sha256'])
    expected_graph = source.get('prompt', source)
    require(digest_bytes(canonical(expected_graph)) == attempt['graph_sha256'], 'pinned case4 graph differs from original attempt')
    require(isinstance(prompt, list) and len(prompt) >= 4, 'malformed history prompt')
    changes = compare_graph(expected_graph, prompt[2])
    require(isinstance(prompt, list) and len(prompt) >= 4 and (prompt[1] == outcome['prompt_id']) and (digest_bytes(canonical(expected_graph)) == attempt['graph_sha256']) and (prompt[3]['client_id'] == attempt['client_id']), 'history prompt/graph/client differs from actual attempt')
    outputs = []
    for node in history['outputs'].values():
        for key in ('images', 'videos', 'gifs'):
            outputs.extend(node.get(key, []))
    require(len(outputs) == 1, 'exactly one candidate video output required')
    output = outputs[0]
    name = output['filename']
    subfolder = output.get('subfolder', '')
    require(output['type'] == 'output' and isinstance(name, str) and re.fullmatch(re.escape(c['output_prefix']) + '_[0-9]+_?\\.(mp4|webm|mkv)', name), 'unexpected output filename/type')
    require(isinstance(subfolder, str) and (not Path(subfolder).is_absolute()) and ('..' not in Path(subfolder).parts) and (not any((x in subfolder for x in ('\\', ':')))), 'unsafe output subfolder')
    output_root = absolute(bindings['output_root'])
    path = regular(output_root / subfolder / name)
    require(path.is_relative_to(output_root), 'output path escapes Comfy output root')
    executable = regular(absolute(bindings['ffprobe']['path']))
    require(executable.name.casefold() in ('ffprobe', 'ffprobe.exe') and sha(executable) == bindings['ffprobe']['sha256'], 'only verified existing ffprobe executable permitted')
    before = sha(path)
    result = subprocess.run([str(executable), '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json', str(path)], capture_output=True, text=True, timeout=60, shell=False)
    require(result.returncode == 0, 'ffprobe failed; output not validated')
    metadata = json.loads(result.stdout)
    streams = metadata['streams']
    videos = [s for s in streams if s.get('codec_type') == 'video']
    require(len(videos) == 1 and (not any((s.get('codec_type') == 'audio' for s in streams))), 'exactly one video stream and no audio required')
    video = videos[0]
    require(video['width'] == 832 and video['height'] == 480 and (int(video['nb_read_frames']) == 49) and (Fraction(video['avg_frame_rate']) == 24), 'actual output dimensions/decoded frames/fps differ')
    require(abs(float(metadata['format']['duration']) - 49 / 24) <= 0.06, 'actual output duration differs')
    require(sha(path) == before, 'output mutated during verification')
    return {'state': 'technical_output_verified_visual_review_still_pending', 'file': str(path), 'sha256': before, 'bytes': path.stat().st_size, 'original_attempt_graph_sha256': attempt['graph_sha256'], 'server_history_graph_sha256': digest_bytes(canonical(prompt[2])), 'normalization_differences': changes, 'server_history_file_sha256': sha(root / 'technical-test-history.json'), 'frames': 49, 'fps': 24, 'audio': False, 'limits': LIMITS}
