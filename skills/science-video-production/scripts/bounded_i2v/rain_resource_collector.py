"""Windows-only fixed read-only resource collector, never inference or service control.
Extracted/adapted from supplied actual Windows sampling excerpts, not the old orchestrator.
Stdlib only; run using -I -S -B -X utf8. Outer parent owns task lock throughout submit.
"""
import argparse
import ctypes
from datetime import datetime, timezone
import errno
import hashlib
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ENDPOINT = 'http://127.0.0.1:8199'


def require(ok, message):
    if not ok: raise ValueError(message)


def now(): return datetime.now(timezone.utc).isoformat()


def instant(value):
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(d.utcoffset() is not None, 'timezone missing')
    return d.timestamp()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):h.update(block)
    return h.hexdigest()


def checked_tool(path, expected):
    p = Path(path)
    require(p.is_absolute() and p.is_file() and not p.is_symlink() and
            not any(x.is_symlink() for x in p.parents), 'tool file missing or redirected')
    require(file_sha(p) == expected, 'fixed existing tool bytes changed: '+str(p))


TRACE=None
def trace(kind,data):
    if TRACE is not None:
        with TRACE.open('a',encoding='utf-8') as f:
            f.write(json.dumps({'at':now(),'kind':kind,'data':data},ensure_ascii=False,allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())

def run(argv):
    # Call sites supply only the fixed audited PS query or fixed NVIDIA argv below.
    try:p = subprocess.run(argv, capture_output=True, text=True, encoding='utf-8', timeout=10, shell=False)
    except subprocess.TimeoutExpired as e:
        text=lambda v:v.decode('utf-8',errors='replace') if isinstance(v,bytes) else v
        trace('command_timeout',{'tool':argv[0],'stdout':text(e.stdout),'stderr':text(e.stderr),'error':str(e)});raise
    trace('command_result',{'tool':argv[0],'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    require(p.returncode == 0, 'fixed read-only command failed: '+str(argv[0]))
    require(len(p.stdout.encode('utf-8')) <= 1024*1024, 'read response too large')
    return p.stdout


def get(path):
    require(path in ('/queue','/system_stats'), 'only existing service health/queue reads allowed')
    c = http.client.HTTPConnection('127.0.0.1',8199,timeout=3)
    try:
        c.request('GET',path);r=c.getresponse();raw=r.read(4*1024*1024+1)
        trace('http_result',{'path':path,'status':r.status,'body':raw.decode('utf-8',errors='replace')})
        require(r.status == 200 and len(raw) <= 4*1024*1024, 'health read rejected')
        return json.loads(raw)
    finally:c.close()


class MemoryStatus(ctypes.Structure):
    _fields_=[('dwLength',ctypes.c_ulong),('dwMemoryLoad',ctypes.c_ulong),
        ('ullTotalPhys',ctypes.c_ulonglong),('ullAvailPhys',ctypes.c_ulonglong),
        ('ullTotalPageFile',ctypes.c_ulonglong),('ullAvailPageFile',ctypes.c_ulonglong),
        ('ullTotalVirtual',ctypes.c_ulonglong),('ullAvailVirtual',ctypes.c_ulonglong),
        ('ullAvailExtendedVirtual',ctypes.c_ulonglong)]


def ram():
    s=MemoryStatus();s.dwLength=ctypes.sizeof(s)
    if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s)):raise ctypes.WinError()
    return int(s.ullAvailPhys)


def inspect_lock(request):
    import msvcrt
    lock=request['executor_lock'];holder=lock['holder_pid']
    require(type(holder) is int and holder > 0 and holder == os.getppid(), 'collector parent must be actual outer lock holder')
    p=Path(lock['path'])
    require(p.is_absolute() and p.name == 'rain-single-candidate-executor.lock' and p.is_file()
            and not p.is_symlink() and not any(x.is_symlink() for x in p.parents), 'fixed existing task lock path required')
    # Original reviewed writer emits canonical JSON object at offset0 and locks byte0.
    # Do not read that locked byte: preserve the remaining actual bytes; reconstruct only
    # its known object opener. This does not claim a whole-file SHA or rewrite the lock.
    with p.open('r+b',buffering=0) as f:
        f.seek(1);tail=f.read(1024*1024)
        require(len(tail) < 1024*1024, 'lock metadata oversized')
        metadata=json.loads(b'{'+tail)
        require(metadata['pid'] == holder and metadata['worker_id'] == request['worker_id'] and
                metadata['lock_id'] == request['unique_executor_lock'], 'actual lock owner metadata differs')
        f.seek(0)
        try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as exc:
            require(exc.errno in (errno.EACCES,errno.EAGAIN,errno.EDEADLK), 'unexpected lock probe failure')
        else:
            msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            raise ValueError('task byte lock not held; stale marker is not ownership')
    return metadata


def collect(request):
    env=request['environment'];tools=env['tools']
    PYTHON=tools['python']['path'];PYTHON_SHA=tools['python']['sha256']
    BASE=tools['base_python']['path'];BASE_SHA=tools['base_python']['sha256']
    NV=tools['nvidia_smi']['path'];NV_SHA=tools['nvidia_smi']['sha256']
    PS=tools['powershell']['path'];PS_SHA=tools['powershell']['sha256']
    SERVICE_EXECUTABLES=env['service_executables']
    require(os.name == 'nt', 'this reviewed collector only supports the specified Windows environment')
    require(request['protocol'] == 'rain-resource-collector-v1' and request['endpoint'] == ENDPOINT, 'wrong request protocol/endpoint')
    require(Path(sys.executable).resolve() == Path(PYTHON).resolve() and
            Path(sys._base_executable).resolve() == Path(BASE).resolve(), 'actual direct base interpreter differs')
    for p,h in ((PYTHON,PYTHON_SHA),(BASE,BASE_SHA),(NV,NV_SHA),(PS,PS_SHA)):checked_tool(p,h)
    startup = request['service_identity']
    reference = request['startup_record']; path = Path(reference['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'actual startup record required')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == reference['sha256'] and json.loads(path.read_text(encoding='utf-8')) == startup, 'startup record changed')
    require(startup['endpoint'] == ENDPOINT and startup['comfy_root'] == env['comfy_root'] and startup['executable_path'] in SERVICE_EXECUTABLES, 'unapproved service installation')
    require(all(type(startup[k]) is int and startup[k] > 0 for k in ('service_pid','parent_pid')), 'invalid startup PID')
    checked_tool(startup['executable_path'], SERVICE_EXECUTABLES[startup['executable_path']])
    require(request['input_root'] == startup['input_root'] and Path(request['input_root']).is_absolute() and Path(request['input_root']).is_dir(), 'actual case3 service input root differs')
    service_pid = startup['service_pid']; service_parent = startup['parent_pid']; service_created = startup['created_at']
    # New cross-renderer protocol: same workspace lock as 3D guardian; never write/delete it.
    from ctypes import wintypes
    shared=Path(request['workspace_gpu_lock_path'])
    require(shared.is_file() and not shared.is_symlink() and not any(x.is_symlink() for x in shared.parents), 'workspace lock missing/redirected')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.CreateFileW.argtypes=[wintypes.LPCWSTR,wintypes.DWORD,wintypes.DWORD,ctypes.c_void_p,wintypes.DWORD,wintypes.DWORD,wintypes.HANDLE];k.CreateFileW.restype=wintypes.HANDLE
    k.CloseHandle.argtypes=[wintypes.HANDLE];k.CloseHandle.restype=wintypes.BOOL
    test=k.CreateFileW(str(shared),0xC0000000,0,None,3,0x80,None)
    if test not in (None,ctypes.c_void_p(-1).value):
        k.CloseHandle(test);raise ValueError('workspace GPU lock not held')
    require(ctypes.get_last_error()==32,'workspace lock failure is not verified sharing violation')
    lock=inspect_lock(request);holder=lock['pid']
    query = "$ErrorActionPreference='Stop'; $p=Get-CimInstance Win32_Process -Filter 'ProcessId="+str(service_pid)+"' -Property ProcessId,ParentProcessId,ExecutablePath,CreationDate; $l=@(Get-NetTCPConnection -LocalPort 8199 -State Listen|Select-Object LocalAddress,LocalPort,OwningProcess); $h=Get-CimInstance Win32_Process -Filter 'ProcessId="+str(holder)+"' -Property ProcessId,CreationDate; [ordered]@{process=$p|Select-Object ProcessId,ParentProcessId,ExecutablePath,CreationDate;listeners=$l;holder=$h|Select-Object ProcessId,CreationDate}|ConvertTo-Json -Depth 5 -Compress"
    identity=json.loads(run([PS,'-NoProfile','-NonInteractive','-Command',query]))
    proc=identity['process'];listeners=identity['listeners']
    require(proc['ProcessId'] == service_pid and proc['ParentProcessId'] == service_parent and proc['ExecutablePath'].casefold() == startup['executable_path'].casefold() and
            abs(instant(proc['CreationDate'])-instant(service_created)) <= .001 and
            isinstance(listeners, list) and len(listeners)==1 and all(x['LocalAddress']=='127.0.0.1' and x['LocalPort']==8199 and x['OwningProcess']==service_pid for x in listeners),
            'owned service identity/listener changed')
    chain=startup['identity_processes']
    require(len(chain)==2 and chain[1]['ProcessId']==service_pid and chain[1]['ParentProcessId']==chain[0]['ProcessId'], 'frozen parent chain invalid')
    parent_query="$ErrorActionPreference='Stop'; Get-CimInstance Win32_Process -Filter 'ProcessId="+str(service_parent)+"' -Property ProcessId,ParentProcessId,ExecutablePath,CreationDate|Select-Object ProcessId,ParentProcessId,ExecutablePath,CreationDate|ConvertTo-Json -Compress"
    parent=json.loads(run([PS,'-NoProfile','-NonInteractive','-Command',parent_query]))
    expected=chain[0]
    require(parent['ProcessId']==expected['ProcessId'] and parent['ParentProcessId']==expected['ParentProcessId'] and parent['ExecutablePath'].casefold()==expected['ExecutablePath'].casefold() and abs(instant(parent['CreationDate'])-instant(expected['CreationDate']))<=.001,'actual launcher identity changed')
    owner=identity['holder']
    require(owner['ProcessId'] == holder and
            abs(instant(owner['CreationDate'])-instant(request['executor_lock']['holder_creation_time'])) <= .001,
            'actual parent holder lifetime differs from static binding')
    health=get('/system_stats');before=get('/queue')
    require(before.get('queue_running') == [] and before.get('queue_pending') == [], 'queue occupied before sampling')
    pids=sorted(set(int(x.strip()) for x in run([NV,'--query-compute-apps=pid','--format=csv,noheader,nounits']).splitlines() if x.strip()))
    samples=[]
    for i in range(4):
        rows=run([NV,'--query-gpu=index,memory.free,utilization.gpu','--format=csv,noheader,nounits']).splitlines()
        require(len(rows) == 1, 'unexpected GPU count')
        index,free,util=[int(x.strip()) for x in rows[0].split(',')]
        samples.append({'observed_at':now(),'utilization_percent':util,'gpu_index':index,
                        'vram_available_bytes':free*1024*1024,'ram_available_bytes':ram()})
        trace('gpu_sample',samples[-1])
        if i < 3:time.sleep(2)
    after=get('/queue');require(after.get('queue_running') == [] and after.get('queue_pending') == [], 'queue occupied after sampling')
    require(inspect_lock(request) == lock, 'lock ownership metadata changed during sampling')
    output=Path(request['output_root']);require(output.is_absolute() and output.is_dir(), 'actual existing output directory required')
    return {'kind':'local_process_gpu_queue_inspection','collection_id':request['collection_id'],'observed_at':now(),
        'endpoint':ENDPOINT,'service_ready':True,'queue_empty':True,'service_pid':service_pid,
        'service_identity':request['service_identity'],'active_worker_ids':[lock['worker_id']],
        'gpu_process_pids':pids,'unattributed_gpu_process_pids':pids,'output_root':str(output),
        'inspection_source':str(Path(__file__).resolve())+'; fixed actual PS listener/parent identity, HTTP200 queue, NVIDIA short-window measurements, GlobalMemoryStatusEx and disk_usage',
        'unique_executor_lock':lock['lock_id'],'ram_available_bytes':min(x['ram_available_bytes'] for x in samples),
        'vram_available_bytes':min(x['vram_available_bytes'] for x in samples),'disk_available_bytes':shutil.disk_usage(output).free,
        'heavy_load_assessment':'not_observed_in_sample_window' if all(x['utilization_percent'] <= request['gpu_load_policy']['max_utilization_percent'] for x in samples) else 'observed_above_budget',
        'gpu_load':{'status':'measured','metric':'gpu_total_utilization_percent',
            'observation_source':'fixed nvidia-smi actual utilization.gpu; no per-PID idle inference',
            'samples':[{'observed_at':x['observed_at'],'utilization_percent':x['utilization_percent']} for x in samples]},
        'lock_evidence':{'path':request['executor_lock']['path'],'holder_pid':holder,
            'holder_creation_time':owner['CreationDate'],'collector_parent_pid':os.getppid(),'byte_lock_held':True,
            'metadata_read':'offset1 with reviewed canonical object opener; no lock-file rewrite'},
        'raw_observation':{'identity':identity,'system':health.get('system',{}),'samples':samples,
            'queue_before':before,'queue_after':after,'gpu_process_pids':pids,
            'per_pid_utilization':'unknown_WDDM_not_measured','lock_owner_metadata':lock}}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request-json',required=True);a=p.parse_args()
    path=Path(a.request_json);require(path.is_absolute() and path.is_file(), 'new absolute gate request file required')
    request=json.loads(path.read_text(encoding='utf-8'))
    global TRACE
    TRACE=path.parent/('collector-raw-'+request['collection_id']+'.jsonl')
    with TRACE.open('x',encoding='utf-8') as f:f.flush();os.fsync(f.fileno())
    try:print(json.dumps(collect(request),ensure_ascii=False,allow_nan=False))
    except Exception as exc:
        trace('failure',{'error':str(exc),'type':type(exc).__name__});raise


if __name__=='__main__':main()
