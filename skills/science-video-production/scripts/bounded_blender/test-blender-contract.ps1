# Synthetic scratch-only contract validation. Never invokes Guardian.Run, GPU, CIM,
# HTTP, Blender, or the full launcher. Add-Type only compiles the C# type in memory.
param([string]$ReportPath)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.Major -lt 7) { throw 'PowerShell 7 required' }
$runnerPath = Join-Path $PSScriptRoot 'run-blender-local.ps1'
$guardianPath = Join-Path $PSScriptRoot 'blender-guardian.cs'
$source = [IO.File]::ReadAllText($runnerPath)
$tokens = $null; $parseErrors = $null
$ast = [Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count) { throw "Launcher parse errors: $parseErrors" }
$boundary = $source.IndexOf('$queueLock = $null',[StringComparison]::Ordinal)
if ($boundary -lt 0) { throw 'Validation boundary absent' }
$validationSource = $source.Substring(0,$boundary)
$serviceAst = $ast.Find({param($a) $a -is [Management.Automation.Language.FunctionDefinitionAst] -and $a.Name -eq 'Assert-ExactIdleComfyService'},$true)
if ($null -eq $serviceAst) { throw 'Service function missing' }
. ([ScriptBlock]::Create($serviceAst.Extent.Text))
Add-Type -TypeDefinition ([IO.File]::ReadAllText($guardianPath)) -Language CSharp -ErrorAction Stop
$beforeRunner = (Get-FileHash $runnerPath -Algorithm SHA256).Hash
$beforeGuardian = (Get-FileHash $guardianPath -Algorithm SHA256).Hash
$temp = Join-Path ([IO.Path]::GetTempPath()) ('blender-contract-'+[Guid]::NewGuid().ToString('N'))
[void][IO.Directory]::CreateDirectory($temp)
# A real scratch .ps1 gives the unchanged prefix its normal PSScriptRoot semantics.
$validation = Join-Path $temp 'validation-prefix.ps1'
[IO.File]::WriteAllText($validation,$validationSource,[Text.UTF8Encoding]::new($false))
function Write-Fixture($path,$obj) { [IO.File]::WriteAllText($path,($obj|ConvertTo-Json -Depth 20),[Text.UTF8Encoding]::new($false)) }
function Hash($path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() }
$tests = [Collections.Generic.List[string]]::new()
# This is deliberately fake test data, not a live service observation or approval.
$service = [pscustomobject]@{schema_version=1;startup_verified=$true;workers=@(
    [pscustomobject]@{PID=41001;Parent=41000;Exe=(Join-Path $temp 'service-a\python.exe');Created='2000-01-01T00:00:00Z';SHA=('a'*64)},
    [pscustomobject]@{PID=41002;Parent=41001;Exe=(Join-Path $temp 'service-b\python.exe');Created='2000-01-01T00:00:01Z';SHA=('b'*64)}
);listener=[pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=8199;OwningProcess=41002}}
foreach ($n in 1,2,3) {
    $root = Join-Path $temp "candidate-$n"
    [void][IO.Directory]::CreateDirectory($root)
    [IO.File]::WriteAllText((Join-Path $root 'blender.exe'),'SYNTHETIC NON EXECUTABLE')
    [IO.File]::WriteAllText((Join-Path $root 'skill-lock.json'),'{}')
    Write-Fixture (Join-Path $root 'service.json') $service
    $c = [ordered]@{schema_version=1;executor='blender-local-three-keyframes';candidate_id="synthetic-$n";candidate_root=$root;input_manifest=@{path='inputs.json';sha256=('d'*64)};skill_lock=@{path='skill-lock.json';sha256=(Hash (Join-Path $root 'skill-lock.json'))};skill_root=(Join-Path $temp 'skill');blender=@{path=(Join-Path $root 'blender.exe');sha256=(Hash (Join-Path $root 'blender.exe'))};service_evidence=@{path='service.json';sha256=(Hash (Join-Path $root 'service.json'))};expected_outputs=@('output\frame_0000.png','output\frame_0033.png','output\frame_0047.png');prerequisite_receipts=@();scope=@{FrameCount=3;Width=960;Height=540;Samples=256;Device='RTX5060Ti OptiX';States=@('frame_0000','frame_0033','frame_0047');Animation=$false}}
    $c.argv=@('--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',(Join-Path $root 'package\run_three_keyframes.py'),'--','--skill-root',$c.skill_root,'--skill-lock',(Join-Path $root 'skill-lock.json'))
    $cp = Join-Path $root 'config.json'; Write-Fixture $cp $c
    & $validation -ConfigPath $cp -ReviewedConfigSHA256 (Hash $cp)
    $tests.Add("synthetic-candidate-$n-prefix-validation")
    $c.argv += '--render-anim';Write-Fixture $cp $c
    $rejected = $false
    try { & $validation -ConfigPath $cp -ReviewedConfigSHA256 (Hash $cp) } catch { $rejected = $true }
    if (-not $rejected) { throw 'Forbidden argv was accepted' }
    $tests.Add("candidate-$n-forbidden-argv-rejected")
}
$workers=@($service.workers | ForEach-Object { [pscustomobject]@{ProcessId=$_.PID;ParentProcessId=$_.Parent;Name='python.exe';ExecutablePath=$_.Exe;CreationDate=[datetime]$_.Created} })
$hashes=@{};foreach($e in $service.workers){$hashes[$e.Exe]=$e.SHA}
$snapshot=[pscustomobject]@{ReadSucceeded=$true;Workers=$workers;Listeners=@($service.listener);Queue=[pscustomobject]@{queue_running=@();queue_pending=@()};BinaryHashes=$hashes}
Assert-ExactIdleComfyService $snapshot
$tests.Add('synthetic-idle-service-admitted')
$snapshot.Workers[0].CreationDate=$snapshot.Workers[0].CreationDate.AddSeconds(1)
$rejected=$false;try { Assert-ExactIdleComfyService $snapshot } catch {$rejected=$true}
if(-not $rejected){throw 'PID reuse/lifetime mismatch accepted'}
$tests.Add('synthetic-lifetime-mismatch-rejected')
if ((Get-FileHash $runnerPath -Algorithm SHA256).Hash -cne $beforeRunner -or (Get-FileHash $guardianPath -Algorithm SHA256).Hash -cne $beforeGuardian) { throw 'Core changed during tests' }
$result=[ordered]@{status='synthetic_contract_and_compile_pass';tests=$tests;runner_sha256=$beforeRunner.ToLowerInvariant();guardian_sha256=$beforeGuardian.ToLowerInvariant();powershell=$PSVersionTable.PSVersion.ToString();guardian_compiled=$true;guardian_invoked=$false;windows_job_execution_tested=$false;rendering_executed=$false;performance_improvement_measured=$false;synthetic_scratch=$temp}
if ($ReportPath) {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 10))
    $stream=[IO.File]::Open($ReportPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try {$stream.Write($bytes,0,$bytes.Length)} finally {$stream.Dispose()}
}
$result|ConvertTo-Json -Depth 10
