param(
    [Parameter(Mandatory=$true)][string]$ConfigPath,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-f0-9]{64}$')][string]$ReviewedConfigSHA256
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
function Digest([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() }
function ExactFields($Object,[string[]]$Fields) {
    $actual = @($Object.PSObject.Properties.Name | Sort-Object)
    if (($actual -join '|') -cne (($Fields | Sort-Object) -join '|')) { throw 'Unknown or missing configuration fields' }
}
function RelativeFile([string]$Root,[string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative) -or $Relative -match '(^|[\\/])\.\.?([\\/]|$)' -or $Relative -match ':') { throw 'Unsafe relative path' }
    $full = [IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if (-not $full.StartsWith($Root.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Path escaped root' }
    $p = $full
    while ($p) {
        if ((Test-Path -LiteralPath $p) -and ((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Reparse points not permitted' }
        $p = Split-Path -Parent $p
    }
    return $full
}
if ((Digest $ConfigPath) -cne $ReviewedConfigSHA256) { throw 'Independent reviewed configuration hash mismatch' }
$c = [IO.File]::ReadAllText($ConfigPath) | ConvertFrom-Json
ExactFields $c @('schema_version','executor','candidate_id','candidate_root','input_manifest','skill_lock','skill_root','blender','service_evidence','expected_outputs','argv','prerequisite_receipts','scope')
if ($c.schema_version -ne 1 -or $c.executor -cne 'blender-local-three-keyframes' -or $c.candidate_id -notmatch '^[A-Za-z0-9_-]{1,80}$') { throw 'Unsupported configuration profile' }
$taskRoot = [IO.Path]::GetFullPath($c.candidate_root)
if ($c.candidate_root -notmatch '^[A-Za-z]:\\' -or -not [IO.Path]::IsPathFullyQualified($c.candidate_root) -or -not (Test-Path -LiteralPath $taskRoot -PathType Container)) { throw 'Existing absolute candidate root required' }
$workspace = Split-Path -Parent $taskRoot
$package = RelativeFile $taskRoot 'package'
ExactFields $c.blender @('path','sha256')
$exe = $c.blender.path
$exeSHA = $c.blender.sha256
if ($exe -notmatch '^[A-Za-z]:\\' -or -not [IO.Path]::IsPathFullyQualified($exe) -or [IO.Path]::GetFileName($exe) -cne 'blender.exe' -or $exeSHA -notmatch '^[a-f0-9]{64}$') { throw 'Only reviewed Blender binary permitted' }
$controller = Join-Path $PSScriptRoot 'blender-guardian.cs'
$controllerSHA = '07fe9fd30f257960939edd08a0740e8cf75a989cfe9f40a451c22c4e687882be'
ExactFields $c.skill_lock @('path','sha256')
$skillLockPath = RelativeFile $taskRoot $c.skill_lock.path
if ((Digest $skillLockPath) -cne $c.skill_lock.sha256 -or $c.skill_root -notmatch '^[A-Za-z]:\\' -or -not [IO.Path]::IsPathFullyQualified($c.skill_root)) { throw 'Actual Skill lock mismatch' }
$arguments = @('--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',(Join-Path $package 'run_three_keyframes.py'),'--','--skill-root',$c.skill_root,'--skill-lock',$skillLockPath)
if (@($c.argv).Count -ne $arguments.Count) { throw 'Only fixed diagnostic argv profile permitted' }
for ($i=0;$i -lt $arguments.Count;$i++) { if ($c.argv[$i] -cne $arguments[$i]) { throw 'Argument outside fixed allowlist' } }
$expectedNames = @('output\frame_0000.png','output\frame_0033.png','output\frame_0047.png')
if (@($c.expected_outputs).Count -ne 3) { throw 'Exactly three fixed diagnostic outputs required' }
$outputPNGs = @()
for ($i=0;$i -lt 3;$i++) { if ($c.expected_outputs[$i] -cne $expectedNames[$i]) { throw 'Unexpected diagnostic output' }; $outputPNGs += RelativeFile $package $c.expected_outputs[$i] }
ExactFields $c.scope @('FrameCount','Width','Height','Samples','Device','States','Animation')
if ($c.scope.FrameCount -ne 3 -or $c.scope.Width -ne 960 -or $c.scope.Height -ne 540 -or $c.scope.Samples -ne 256 -or $c.scope.Device -cne 'RTX5060Ti OptiX' -or $c.scope.Animation -cne $false -or (@($c.scope.States) -join '|') -cne 'frame_0000|frame_0033|frame_0047') { throw 'Scope is outside fixed diagnostic profile' }
ExactFields $c.service_evidence @('path','sha256')
$servicePath = RelativeFile $taskRoot $c.service_evidence.path
if ((Digest $servicePath) -cne $c.service_evidence.sha256) { throw 'Reviewed startup evidence changed' }
$service = [IO.File]::ReadAllText($servicePath) | ConvertFrom-Json
ExactFields $service @('schema_version','startup_verified','workers','listener')
if ($service.schema_version -ne 1 -or $service.startup_verified -cne $true -or @($service.workers).Count -ne 2) { throw 'Verified two-process service startup evidence required' }
foreach ($e in $service.workers) {
    ExactFields $e @('PID','Parent','Exe','Created','SHA')
    if ($e.PID -le 0 -or $e.Parent -le 0 -or $e.Exe -notmatch '^[A-Za-z]:\\' -or -not [IO.Path]::IsPathFullyQualified($e.Exe) -or [IO.Path]::GetFileName($e.Exe) -cne 'python.exe' -or $e.SHA -notmatch '^[a-f0-9]{64}$') { throw 'Invalid service identity' }
    [void][DateTimeOffset]::Parse($e.Created)
}
ExactFields $service.listener @('LocalAddress','LocalPort','OwningProcess')
if ($service.listener.LocalAddress -cne '127.0.0.1' -or $service.listener.LocalPort -ne 8199 -or $service.listener.OwningProcess -ne $service.workers[1].PID -or $service.workers[1].Parent -ne $service.workers[0].PID -or $service.workers[0].PID -eq $service.workers[1].PID) { throw 'Invalid service topology' }
$queueLock = $null
$claimOwned = $false
$nativeResult = $null
$guardianCalled = $false
$outcomeWritten = $false
$bytecodeCaptured = $false
$uncertainMarkerOwned = $false
$markerNonce = [Guid]::NewGuid().ToString('N')
$uncertainPath = Join-Path $workspace 'local-gpu-execution-uncertain.json'
$wrapperExitCode = 1

function Write-NewJson([string]$Path, $Value) {
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes(($Value | ConvertTo-Json -Depth 18)+[Environment]::NewLine)
    $stream = [IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try { $stream.Write($bytes,0,$bytes.Length); $stream.Flush($true) } finally { $stream.Dispose() }
}
function Assert-ExactIdleComfyService($Snapshot) {
    # Only the reviewed startup identities, verified live below, may remain.
    if ($Snapshot.ReadSucceeded -cne $true) { throw 'Incomplete service observation' }
    $expected = @($service.workers)
    if (@($Snapshot.Workers).Count -ne 2) { throw 'Unexpected or missing inference/render/encoder worker' }
    foreach ($e in $expected) {
        $matches = @($Snapshot.Workers | Where-Object { $_.ProcessId -eq $e.PID })
        if ($matches.Count -ne 1) { throw 'Known service PID missing or duplicated' }
        $w = $matches[0]
        if ($w.ParentProcessId -ne $e.Parent -or $w.Name -ine 'python.exe' -or $w.ExecutablePath -cne $e.Exe -or $w.CreationDate -isnot [datetime]) { throw 'Service identity missing or changed' }
        if ($w.CreationDate.ToUniversalTime().Ticks -ne ([DateTimeOffset]::Parse($e.Created)).UtcTicks) { throw 'Service lifetime changed; possible PID reuse' }
        if ($Snapshot.BinaryHashes[$e.Exe] -cne $e.SHA) { throw 'Service binary changed' }
    }
    $listeners = @($Snapshot.Listeners)
    if ($listeners.Count -ne 1 -or $listeners[0].LocalAddress -cne '127.0.0.1' -or $listeners[0].LocalPort -ne 8199 -or $listeners[0].OwningProcess -ne $service.listener.OwningProcess) { throw 'Service listener identity differs' }
    if ($null -eq $Snapshot.Queue -or $Snapshot.Queue.queue_running -isnot [array] -or $Snapshot.Queue.queue_pending -isnot [array]) { throw 'Service queue structure missing or invalid' }
    if ($Snapshot.Queue.queue_running.Count -ne 0 -or $Snapshot.Queue.queue_pending.Count -ne 0) { throw 'Known service is busy; no Blender started' }
}

try {
    foreach ($name in @('preflight-resource-observation.json','idle-service-admission-observation.json','render-launch-claim.json','render-intent.json','render-process.json','render-native-outcome.json','render-job-close.json','render-outcome.json','preflight-resources.json','postflight-resources.json','postflight-error.json','render-stdout.log','render-stderr.log')) {
        if (Test-Path -LiteralPath (Join-Path $taskRoot $name)) { throw 'Prior execution evidence exists; reconcile without repeating' }
    }
    if (Test-Path -LiteralPath (Join-Path $package 'output')) { throw 'Output directory exists; no overwrite or automatic retry' }
    # CreateNew atomically claims this invocation. A losing concurrent invocation
    # cannot write execution records belonging to the winning invocation.
    Write-NewJson (Join-Path $taskRoot 'render-launch-claim.json') ([ordered]@{Status='parent_wrapper_claimed_not_started';CreatedUTC=[DateTime]::UtcNow.ToString('o');ParentLauncherPID=$PID;WrapperPath=$PSCommandPath;WrapperSHA256=(Digest $PSCommandPath);ConfigSHA256=$ReviewedConfigSHA256;CandidateID=$c.candidate_id;AutomaticRetry=$false})
    $claimOwned = $true
    if ((Digest $controller) -ne $controllerSHA) { throw 'Reviewed native guardian source changed' }
    if ((Digest $exe) -ne $exeSHA) { throw 'Fixed Blender executable mismatch' }
    ExactFields $c.input_manifest @('path','sha256')
    $frozenPath = RelativeFile $taskRoot $c.input_manifest.path
    if ((Digest $frozenPath) -cne $c.input_manifest.sha256) { throw 'Pinned input manifest changed' }
    $frozen = [IO.File]::ReadAllText($frozenPath) | ConvertFrom-Json
    ExactFields $frozen @('schema_version','files')
    if ($frozen.schema_version -ne 1 -or @($frozen.files).Count -lt 2) { throw 'Frozen inputs missing' }
    $seen = @{}
    foreach ($item in $frozen.files) {
        ExactFields $item @('path','bytes','sha256')
        $member = RelativeFile $package $item.path
        if ($seen.ContainsKey($member.ToLowerInvariant()) -or $item.path -match '(^|[\\/])output([\\/]|$)') { throw 'Duplicate or output input path' }
        $seen[$member.ToLowerInvariant()] = $true
        if ($item.sha256 -notmatch '^[a-f0-9]{64}$' -or (Get-Item -LiteralPath $member).Length -ne $item.bytes -or (Digest $member) -cne $item.sha256) { throw 'Frozen package member changed' }
    }
    foreach ($required in @('run_three_keyframes.py','manifest.json')) { if (-not $seen.ContainsKey((RelativeFile $package $required).ToLowerInvariant())) { throw 'Required entry/manifest not frozen' } }
    $actualFiles = @(Get-ChildItem -LiteralPath $package -Recurse -File -Force)
    if ($actualFiles.Count -ne $seen.Count) { throw 'Unfrozen package files present' }
    foreach ($file in $actualFiles) { if (-not $seen.ContainsKey($file.FullName.ToLowerInvariant())) { throw 'Unfrozen package member' } }
    $voiceProof = @()
    foreach ($spec in $c.prerequisite_receipts) {
        ExactFields $spec @('path','sha256','count')
        $p = RelativeFile $workspace $spec.path
        if ((Digest $p) -cne $spec.sha256 -or $spec.count -le 0) { throw 'Prerequisite receipt mismatch' }
        $receipt = [IO.File]::ReadAllText($p) | ConvertFrom-Json
        if (@($receipt.files).Count -ne $spec.count) { throw 'Prerequisite saved-file count incomplete' }
        foreach ($file in $receipt.files) { if ($file.status -ne 'succeeded' -or -not $file.native_identity_readback -or -not $file.file_bytes_unchanged -or -not $file.library_file_id) { throw 'Prerequisite delivery incomplete' } }
        $voiceProof += [ordered]@{Path=$p;SHA256=(Digest $p);ConfirmedFiles=@($receipt.files).Count}
    }
    # PowerShell 7 Add-Type compiles in this process, with no output assembly.
    # Merely compiling the type does not invoke its native Run entry.
    if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 is required for in-process Add-Type; no compiler fallback' }
    Add-Type -TypeDefinition ([IO.File]::ReadAllText($controller)) -Language CSharp -ErrorAction Stop
    $lockPath = Join-Path $workspace 'local-gpu-execution.lock'
    $queueLock = [IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
    if (Test-Path -LiteralPath $uncertainPath) { throw 'Shared GPU execution is unresolved; read-only reconciliation required, no new launch' }
    # Snapshot raw observations before deciding; exceptions are not empty/idle proof.
    $idleService = [ordered]@{CheckedUTC=[DateTime]::UtcNow.ToString('o');ReadSucceeded=$false;Workers=$null;Listeners=$null;Queue=$null;BinaryHashes=@{};Error=$null;Admitted=$false}
    try {
        $workers = @(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe' OR Name='blender.exe' OR Name='ffmpeg.exe' OR Name='llama-server.exe' OR Name='llama-cli.exe'" -ErrorAction Stop | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CreationDate)
        $idleService.Workers = $workers
        $idleService.Listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8199 -ErrorAction Stop | Select-Object LocalAddress,LocalPort,OwningProcess)
        $idleService.Queue = Invoke-RestMethod -Uri 'http://127.0.0.1:8199/queue' -Method Get -TimeoutSec 10 -MaximumRedirection 0 -NoProxy -ErrorAction Stop
        foreach ($binary in @($service.workers.Exe)) { $idleService.BinaryHashes[$binary] = Digest $binary }
        $idleService.ReadSucceeded = $true
    } catch {
        $idleService.Error = $_.Exception.Message
        Write-NewJson (Join-Path $taskRoot 'idle-service-admission-observation.json') $idleService
        throw
    }
    Write-NewJson (Join-Path $taskRoot 'idle-service-admission-observation.json') $idleService
    Assert-ExactIdleComfyService $idleService
    # Only the exact two verified idle service processes are excluded, not a PID list.
    $otherWorkerCount = $workers.Count - 2
    $rawResources = [ordered]@{CheckedUTC=[DateTime]::UtcNow.ToString('o');ReadSucceeded=$false;OS=$null;Disks=$null;GPU=$null;Error=$null}
    try {
        $osInfo = Get-CimInstance Win32_OperatingSystem -ErrorAction Stop
        $rawResources.OS = $osInfo | Select-Object FreePhysicalMemory
        $disks = @(Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:' OR DeviceID='D:'" -ErrorAction Stop | Select-Object DeviceID,Size,FreeSpace)
        $rawResources.Disks = $disks
        $gpu = @(& 'C:\Windows\System32\nvidia-smi.exe' -i 0 --query-gpu=name,driver_version,memory.total,memory.free,memory.used,utilization.gpu --format=csv,noheader,nounits)
        $rawResources.GPU = $gpu
        if ($LASTEXITCODE -ne 0 -or $gpu.Count -ne 1) { throw 'GPU query failed' }
        $rawResources.ReadSucceeded = $true
    } catch { $rawResources.Error = $_.Exception.Message; throw }
    finally { Write-NewJson (Join-Path $taskRoot 'preflight-resource-observation.json') $rawResources }
    $g = $gpu[0].Split(',') | ForEach-Object Trim
    $resources = [ordered]@{CheckedUTC=[DateTime]::UtcNow.ToString('o');GPUFields='name,driver_version,totalMiB,freeMiB,usedMiB,utilizationPercent';GPU=$gpu;FreeRAMBytes=[long]$osInfo.FreePhysicalMemory*1024;Disks=$disks;OtherInferenceRenderEncoderWorkers=$otherWorkerCount;VerifiedIdleComfyServiceWorkers=$workers;IdleServiceObservationSHA256=(Digest (Join-Path $taskRoot 'idle-service-admission-observation.json'));OwnedGPUQueueLock=$lockPath;PendingOwnedGPUJobs='only the reviewed three static diagnostic frames in one process; configured prerequisites verified'}
    Write-NewJson (Join-Path $taskRoot 'preflight-resources.json') $resources
    if ($g.Count -ne 6 -or $g[0] -ne 'NVIDIA GeForce RTX 5060 Ti' -or [int]$g[3] -lt 10240 -or [int]$g[5] -gt 10 -or ([long]$osInfo.FreePhysicalMemory*1024) -lt 12GB -or ($disks | Where-Object DeviceID -eq 'C:').FreeSpace -lt 2GB) { throw 'GPU/RAM/disk busy or insufficient; no Blender started' }
    $intent = [ordered]@{
        Status='frozen_not_started';CreatedUTC=[DateTime]::UtcNow.ToString('o');Executable=$exe;ExecutableSHA256=$exeSHA;Arguments=$arguments;WorkingDirectory=$package;InputDirectory=$package;OutputDirectory=(Join-Path $package 'output');OutputPNGs=$outputPNGs
        ManifestSHA256=(Digest (Join-Path $package 'manifest.json'));WrapperPath=$PSCommandPath;WrapperSHA256=(Digest $PSCommandPath);ControllerPath=$controller;ControllerSHA256=$controllerSHA
        Scope=$c.scope;MaximumSeconds=300;WatchdogSeconds=295;CleanupReserveSeconds=5
        Job=[ordered]@{Anonymous=$true;AtomicJobListAssignment=$true;CreateSuspended=$true;KillOnLastHandleClose=$true;JobHandleInherited=$false;InheritedHandles='only NUL/stdout/stderr';CloseAttemptsMaximum=1;NoBreakaway=$true;NoPIDOrNameKill=$true;TreeExitEvidence='private completion port ACTIVE_PROCESS_ZERO; missing notification means unknown'}
        VoiceASRDeliveries=$voiceProof;Resources=$resources;UserSceneOpened=$false;PreferencesSaved=$false;AutomaticRetry=$false
    }
    Write-NewJson (Join-Path $taskRoot 'render-intent.json') $intent
    $oldBytecode = [Environment]::GetEnvironmentVariable('PYTHONDONTWRITEBYTECODE','Process')
    $bytecodeCaptured = $true
    [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE','1','Process')
    Write-NewJson $uncertainPath ([ordered]@{State='launch_may_start_or_be_active';Nonce=$markerNonce;CandidateID=$c.candidate_id;TaskRoot=$taskRoot;ConfigSHA256=$ReviewedConfigSHA256;CreatedUTC=[DateTime]::UtcNow.ToString('o');AutomaticRetry=$false})
    $uncertainMarkerOwned = $true
    $guardianCalled = $true
    $nativeResult = [ReviewedBlenderLocal.Guardian]::Run($taskRoot,$exe,[string[]]$arguments,$package,$PID,$exeSHA,$c.skill_root,$skillLockPath)
    $unchanged = $true
    $verificationErrors = @()
    foreach ($item in $frozen.files) {
        try { if ((Digest (Join-Path $package $item.path)) -ne $item.sha256) { $unchanged=$false; $verificationErrors += "Changed frozen member: $($item.path)" } }
        catch { $unchanged=$false; $verificationErrors += "Frozen member check failed: $($item.path): $($_.Exception.Message)" }
    }
    $outcome = [ordered]@{
        Status=$nativeResult.Status;FinishedUTC=$nativeResult.FinishedUTC;ElapsedSeconds=$nativeResult.ElapsedSeconds;PID=$nativeResult.PID;CreationTimeUTC=$nativeResult.CreationTimeUTC;ExitCode=$nativeResult.ExitCode;MaximumSeconds=300
        Cleanup=@([ordered]@{Scope='only newly created private job';Attempted=$nativeResult.CleanupAttempted;CloseAttempted=$nativeResult.JobCloseAttempted;CloseCompleted=$nativeResult.JobCloseCompleted;CloseSucceeded=$nativeResult.JobCloseSucceeded;CloseAttemptsMaximum=1;Reason=$nativeResult.JobCloseReason;AtSeconds=$nativeResult.JobCloseAtSeconds;Win32Error=$nativeResult.JobCloseWin32Error;ReceiptPending=$nativeResult.JobCloseReceiptPending})
        Error=$nativeResult.Error;VerificationErrors=$verificationErrors;FrozenInputsUnchanged=$unchanged;OutputPNGs=$outputPNGs;PNGsExist=(@($outputPNGs | Where-Object {-not (Test-Path -LiteralPath $_ -PathType Leaf)}).Count -eq 0);IndependentPNGVerificationPending=$true;VisualAccepted=$false;FullVideoAuthorized=$false
        ControllerSHA256=$controllerSHA;ProcessCreated=$nativeResult.ProcessCreated;IdentityVerified=$nativeResult.IdentityVerified;Resumed=$nativeResult.Resumed;RootExited=$nativeResult.RootExited;TreeExitVerified=$nativeResult.TreeExitVerified;TreeExitEvidence=$nativeResult.TreeExitEvidence;TimedOut=$nativeResult.TimedOut;LimitBreach=$nativeResult.LimitBreach;NativeOutcomeWriteError=$nativeResult.NativeOutcomeWriteError
    }
    Write-NewJson (Join-Path $taskRoot 'render-outcome.json') $outcome
    $outcomeWritten = $true
    if ($nativeResult.ProcessCreated -and (-not $nativeResult.RootExited -or -not $nativeResult.TreeExitVerified)) {
        Write-NewJson (Join-Path $taskRoot 'postflight-resources.json') ([ordered]@{Status='skipped_unknown_owned_job_state';CheckedUTC=[DateTime]::UtcNow.ToString('o');ProcessHasExited=$nativeResult.RootExited;TreeExitVerified=$nativeResult.TreeExitVerified;RequiresReconciliation=$true;AutomaticRetry=$false})
    } else {
        try {
            $postGPU = @(& 'C:\Windows\System32\nvidia-smi.exe' -i 0 --query-gpu=name,driver_version,memory.total,memory.free,memory.used,utilization.gpu --format=csv,noheader,nounits)
            if ($LASTEXITCODE -ne 0) { throw 'Postflight GPU query failed' }
            Write-NewJson (Join-Path $taskRoot 'postflight-resources.json') ([ordered]@{CheckedUTC=[DateTime]::UtcNow.ToString('o');GPU=$postGPU;FreeRAMBytes=[long](Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory*1024;Disks=@(Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='C:' OR DeviceID='D:'"|Select-Object DeviceID,Size,FreeSpace);ProcessHasExited=$nativeResult.RootExited;TreeExitVerified=$nativeResult.TreeExitVerified})
        } catch {
            Write-NewJson (Join-Path $taskRoot 'postflight-error.json') ([ordered]@{Status='resource_observation_failed_after_native_outcome';UTC=[DateTime]::UtcNow.ToString('o');Error=$_.Exception.Message;AutomaticRetry=$false})
        }
    }
    $outcome | ConvertTo-Json -Depth 10
    if ($nativeResult.Status -eq 'exited_zero_unverified' -and $unchanged -and $outcome.PNGsExist -and -not $nativeResult.NativeOutcomeWriteError) { $wrapperExitCode = 0 }
} catch {
    $message = $_.Exception.Message
    if ($claimOwned -and -not $outcomeWritten -and -not (Test-Path -LiteralPath (Join-Path $taskRoot 'render-outcome.json'))) {
        $failure = [ordered]@{Status=if($guardianCalled){'unknown_requires_reconciliation'}else{'preflight_failed_no_process_created'};FinishedUTC=[DateTime]::UtcNow.ToString('o');Error=$message;GuardianCalled=$guardianCalled;PID=if($nativeResult){$nativeResult.PID}else{$null};MaximumSeconds=300;AutomaticRetry=$false;VisualAccepted=$false;FullVideoAuthorized=$false;IndependentPNGVerificationPending=$true}
        try { Write-NewJson (Join-Path $taskRoot 'render-outcome.json') $failure; $outcomeWritten=$true } catch { Write-Error -ErrorAction Continue ('Could not persist wrapper failure: '+$_.Exception.Message) }
    }
    Write-Error -ErrorAction Continue $message
} finally {
    if ($bytecodeCaptured) { [Environment]::SetEnvironmentVariable('PYTHONDONTWRITEBYTECODE',$oldBytecode,'Process') }
    # Release the OS lock, but never clear the shared durable inhibit on unknown state.
    # If the wrapper crashes, the marker also survives. Reconciliation is read-only first.
    if ($uncertainMarkerOwned -and $null -ne $nativeResult -and ((-not $nativeResult.ProcessCreated) -or ($nativeResult.RootExited -and $nativeResult.TreeExitVerified))) {
        $ownedMarker = [IO.File]::ReadAllText($uncertainPath) | ConvertFrom-Json
        if ($ownedMarker.Nonce -cne $markerNonce -or $ownedMarker.ConfigSHA256 -cne $ReviewedConfigSHA256 -or $ownedMarker.TaskRoot -cne $taskRoot) { throw 'Shared inhibit marker identity changed; preserve for reconciliation' }
        Remove-Item -LiteralPath $uncertainPath -ErrorAction Stop
    }
    if ($null -ne $queueLock) { $queueLock.Dispose() }
}
exit $wrapperExitCode
