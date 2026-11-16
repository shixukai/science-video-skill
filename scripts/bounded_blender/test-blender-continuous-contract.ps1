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
foreach ($n in 1) {
    $root = Join-Path $temp "candidate-$n"
    [void][IO.Directory]::CreateDirectory($root)
    [IO.File]::WriteAllText((Join-Path $root 'blender.exe'),'SYNTHETIC NON EXECUTABLE')
    [IO.File]::WriteAllText((Join-Path $root 'skill-lock.json'),'{}')
    Write-Fixture (Join-Path $root 'service.json') $service
    $c = [ordered]@{schema_version=1;executor='blender-local-bounded-reveal';candidate_id="synthetic-$n";candidate_root=$root;input_manifest=@{path='inputs.json';sha256=('d'*64)};skill_lock=@{path='skill-lock.json';sha256=(Hash (Join-Path $root 'skill-lock.json'))};skill_root=(Join-Path $temp 'skill');blender=@{path=(Join-Path $root 'blender.exe');sha256=(Hash (Join-Path $root 'blender.exe'))};service_evidence=@{path='service.json';sha256=(Hash (Join-Path $root 'service.json'))};expected_outputs=@(0..47 | ForEach-Object { 'output\frame_{0:d4}.png' -f $_ });prerequisite_receipts=@();scope=@{FrameCount=48;Width=960;Height=540;Samples=256;Device='RTX5060Ti OptiX';States=@(0..47 | ForEach-Object { 'frame_{0:d4}' -f $_ });Animation=$true;StartFrame=0;EndFrame=47;FPS=24}}
    $c.argv=@('--background','--factory-startup','--disable-autoexec','--threads','2','--python-exit-code','1','--python',(Join-Path $root 'package\run_bounded_reveal.py'),'--','--skill-root',$c.skill_root,'--skill-lock',(Join-Path $root 'skill-lock.json'))
    $cp = Join-Path $root 'config.json'; Write-Fixture $cp $c
    & $validation -ConfigPath $cp -ReviewedConfigSHA256 (Hash $cp)
    $tests.Add('exact-48-frame-continuous-prefix-validation')
    $mutations = @('extra-argv','49th-output','missing-output','wrong-fps','wrong-samples','extra-frame','alternate-entry','repeated-three-states')
    foreach ($mutation in $mutations) {
        $bad = ($c | ConvertTo-Json -Depth 20) | ConvertFrom-Json
        switch ($mutation) {
            'extra-argv' { $bad.argv += '--render-anim' }
            '49th-output' { $bad.expected_outputs += 'output\frame_0048.png' }
            'missing-output' { $bad.expected_outputs = @($bad.expected_outputs[0..46]) }
            'wrong-fps' { $bad.scope.FPS = 30 }
            'wrong-samples' { $bad.scope.Samples = 64 }
            'extra-frame' { $bad.scope.EndFrame = 48; $bad.scope.FrameCount = 49 }
            'alternate-entry' { $bad.argv[8] = Join-Path $root 'package\anything.py' }
            'repeated-three-states' { $bad.scope.States = @('frame_0000','frame_0033','frame_0047') * 16 }
        }
        Write-Fixture $cp $bad
        $rejected = $false
        try { & $validation -ConfigPath $cp -ReviewedConfigSHA256 (Hash $cp) } catch { $rejected = $true }
        if (-not $rejected) { throw "Forbidden continuous mutation accepted: $mutation" }
        $tests.Add("rejected-$mutation")
    }
}
if ((Get-FileHash $runnerPath -Algorithm SHA256).Hash -cne $beforeRunner -or (Get-FileHash $guardianPath -Algorithm SHA256).Hash -cne $beforeGuardian) { throw 'Core changed during tests' }
$result=[ordered]@{status='continuous_profile_delta_contract_and_compile_pass';tests=$tests;runner_sha256=$beforeRunner.ToLowerInvariant();guardian_sha256=$beforeGuardian.ToLowerInvariant();powershell=$PSVersionTable.PSVersion.ToString();guardian_compiled=$true;guardian_invoked=$false;windows_job_execution_tested=$false;rendering_executed=$false;performance_improvement_measured=$false;synthetic_scratch=$temp}
if ($ReportPath) {
    $bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 10))
    $stream=[IO.File]::Open($ReportPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try {$stream.Write($bytes,0,$bytes.Length)} finally {$stream.Dispose()}
}
$result|ConvertTo-Json -Depth 10
