# Saved/synthetic timestamps only. No CIM, HTTP, GPU, compiler or Guardian invocation.
param([string]$ReportPath)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$path=Join-Path $PSScriptRoot 'run-blender-local.ps1'
$source=[IO.File]::ReadAllText($path);$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if (@($errors).Count) {throw "Parse error: $errors"}
foreach($name in @('Get-ExactUtcTicks','Assert-ExactIdleComfyService')) {
 $fn=$ast.Find({param($a) $a -is [Management.Automation.Language.FunctionDefinitionAst] -and $a.Name -eq $name},$true)
 if($null -eq $fn){throw "Missing actual function: $name"}
 . ([ScriptBlock]::Create($fn.Extent.Text))
}
$tests=[Collections.Generic.List[string]]::new()
$rows=@()
# Synthetic timestamp pairs reproducing typed JSON, timezone and subsecond precision.
foreach($pair in @(
 @('2000-01-02T06:37:38.766978+00:00','2000-01-02T14:37:38.766978+08:00'),
 @('2000-01-02T06:37:38.795503+00:00','2000-01-02T14:37:38.795503+08:00')
)) {
 $raw=$pair[0];$observedRaw=$pair[1]
 $parsed=(('{"Created":"'+$raw+'"}')|ConvertFrom-Json).Created
 if($parsed -isnot [DateTime]){throw 'Expected real PowerShell ConvertFrom-Json DateTime type'}
 $dto=[DateTimeOffset]::Parse($raw,[Globalization.CultureInfo]::InvariantCulture)
 $observed=[DateTimeOffset]::Parse($observedRaw,[Globalization.CultureInfo]::InvariantCulture).LocalDateTime
 $want=$dto.UtcTicks
 foreach($value in @($raw,$parsed,$dto,$observed,$dto.UtcDateTime)) {
  if((Get-ExactUtcTicks $value) -ne $want){throw 'Exact subsecond ticks were lost'}
 }
 $rows += @{Raw=$raw;DefaultJsonType=$parsed.GetType().FullName;ObservedType=$observed.GetType().FullName;ExpectedUtcTicks=$want;ActualUtcTicks=(Get-ExactUtcTicks $parsed);LegacyImplicitStringUtcTicks=([DateTimeOffset]::Parse($parsed)).UtcTicks}
 $tests.Add('synthetic-typed-and-string-ticks-preserved')
}
$base=[DateTimeOffset]::Parse('2000-01-02T06:37:38.7669780+00:00',[Globalization.CultureInfo]::InvariantCulture)
$service=[pscustomobject]@{workers=@(
 [pscustomobject]@{PID=41001;Parent=41000;Exe='C:\Synthetic\a\python.exe';Created=$base.LocalDateTime;SHA=('a'*64)},
 [pscustomobject]@{PID=41002;Parent=41001;Exe='C:\Synthetic\b\python.exe';Created=$base.AddTicks(1).UtcDateTime;SHA=('b'*64)}
);listener=[pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=8199;OwningProcess=41002}}
# Exercise the real JSON conversion path before the actual admission function.
$service = ($service | ConvertTo-Json -Depth 10) | ConvertFrom-Json
if ($service.workers[0].Created -isnot [DateTime] -or $service.workers[1].Created -isnot [DateTime]) { throw 'JSON fixture did not exercise DateTime conversion' }
function Snapshot {
 $hashes=@{};foreach($e in $service.workers){$hashes[$e.Exe]=$e.SHA}
 [pscustomobject]@{ReadSucceeded=$true;Workers=@($service.workers|ForEach-Object{[pscustomobject]@{ProcessId=$_.PID;ParentProcessId=$_.Parent;Name='python.exe';ExecutablePath=$_.Exe;CreationDate=$_.Created.ToUniversalTime()}});Listeners=@($service.listener);Queue=[pscustomobject]@{queue_running=@();queue_pending=@()};BinaryHashes=$hashes}
}
Assert-ExactIdleComfyService (Snapshot);$tests.Add('actual-admission-matching-datetime-lifetimes')
foreach($mutation in @('one-tick','one-microsecond','pid','parent','exe','hash','listener','busy','missing-worker')) {
 $s=Snapshot
 switch($mutation){
  'one-tick' {$s.Workers[0].CreationDate=$s.Workers[0].CreationDate.AddTicks(1)}
  'one-microsecond' {$s.Workers[0].CreationDate=$s.Workers[0].CreationDate.AddTicks(10)}
  'pid' {$s.Workers[0].ProcessId=42001}
  'parent' {$s.Workers[0].ParentProcessId=42000}
  'exe' {$s.Workers[0].ExecutablePath='C:\Synthetic\other\python.exe'}
  'hash' {$s.BinaryHashes[$service.workers[0].Exe]='c'*64}
  'listener' {$s.Listeners=@([pscustomobject]@{LocalAddress='127.0.0.1';LocalPort=8199;OwningProcess=42002})}
  'busy' {$s.Queue.queue_running=@('synthetic-job')}
  'missing-worker' {$s.Workers=@($s.Workers[0])}
 }
 $rejected=$false;try{Assert-ExactIdleComfyService $s}catch{$rejected=$true}
 if(-not $rejected){throw "Identity mismatch accepted: $mutation"}
 $tests.Add('rejected-'+$mutation)
}
foreach($value in @([DateTime]::SpecifyKind($base.DateTime,[DateTimeKind]::Unspecified),'2000-01-02T06:37:38.766978',123)) {
 $rejected=$false;try{Get-ExactUtcTicks $value|Out-Null}catch{$rejected=$true}
 if(-not $rejected){throw 'Ambiguous/non-timestamp accepted'}
 $tests.Add('rejected-ambiguous-timestamp')
}
# Seventh fractional digit is retained, and equivalent timezone offsets compare exactly.
if((Get-ExactUtcTicks '2000-01-02T06:37:38.7669781Z') -ne $base.AddTicks(1).UtcTicks){throw 'Seventh digit lost'}
if((Get-ExactUtcTicks '2000-01-02T14:37:38.7669781+08:00') -ne $base.AddTicks(1).UtcTicks){throw 'Offset conversion changed ticks'}
$tests.Add('seven-digit-fraction-and-offset-exact')
$result=[ordered]@{status='exact_lifetime_precision_delta_pass';tests=$tests;rows=$rows;wrapper_sha256=(Get-FileHash $path -Algorithm SHA256).Hash.ToLowerInvariant();powershell=$PSVersionTable.PSVersion.ToString();cim_or_processes_queried=$false;rendering_executed=$false;guardian_invoked=$false;precision_tolerance_ticks=0}
if($ReportPath){$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 10));$f=[IO.File]::Open($ReportPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);try{$f.Write($bytes,0,$bytes.Length)}finally{$f.Dispose()}}
$result|ConvertTo-Json -Depth 10
