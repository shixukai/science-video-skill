# Pure fixture evaluates the ACTUAL admission condition AST; no GPU/process/service calls.
param([Parameter(Mandatory=$true)][string]$CorePath,[string]$ReportPath)
$ErrorActionPreference='Stop';Set-StrictMode -Version Latest
$source=[IO.File]::ReadAllText($CorePath);$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$errors)
if (@($errors).Count) {throw 'Core parse error'}
$nodes=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.IfStatementAst] -and $n.Extent.Text.Contains('$g.Count -ne 6')},$true))
if ($nodes.Count -ne 1 -or $nodes[0].Clauses.Count -ne 1) {throw 'Unique actual resource condition missing'}
$condition=$nodes[0].Clauses[0].Item1.Extent.Text
if ($condition -match '\$g\[5\]|utilization|heavy_load') {throw 'Utilization still influences resource admission'}
$evaluate=[scriptblock]::Create($condition)
$tests=[Collections.Generic.List[string]]::new()
foreach ($util in @(0,11,12,100,'N/A')) {
 $g=@('NVIDIA GeForce RTX 5060 Ti','synthetic-driver','16384','12288','4096',"$util")
 $osInfo=[pscustomobject]@{FreePhysicalMemory=20*1024*1024}
 $disks=@([pscustomobject]@{DeviceID='C:';FreeSpace=20GB})
 if (& $evaluate) {throw "Utilization-only fixture rejected: $util"}
 $tests.Add("admit-utilization-only-$util")
}
foreach ($failure in @('vram','ram','disk','gpu-name','sample-shape')) {
 $g=@('NVIDIA GeForce RTX 5060 Ti','synthetic-driver','16384','12288','4096','12')
 $osInfo=[pscustomobject]@{FreePhysicalMemory=20*1024*1024};$disks=@([pscustomobject]@{DeviceID='C:';FreeSpace=20GB})
 switch ($failure) {
  'vram' {$g[3]='10239'}
  'ram' {$osInfo.FreePhysicalMemory=1024}
  'disk' {$disks[0].FreeSpace=1GB}
  'gpu-name' {$g[0]='wrong-device'}
  'sample-shape' {$g=@('short')}
 }
 if (-not (& $evaluate)) {throw "Required capacity/shape refusal lost: $failure"}
 $tests.Add("reject-$failure")
}
if (-not $source.Contains('utilization.gpu') -or -not $source.Contains("`$rawResources.GPU = `$gpu")) {throw 'Raw utilization telemetry was lost'}
$result=[ordered]@{status='actual_condition_fixture_pass';core_sha256=(Get-FileHash -LiteralPath $CorePath -Algorithm SHA256).Hash.ToLowerInvariant();tests=$tests;utilization_is_telemetry_only=$true;native_or_gpu_invoked=$false}
if ($ReportPath) {
 $stream=[IO.File]::Open($ReportPath,[IO.FileMode]::CreateNew)
 try {$bytes=[Text.UTF8Encoding]::new($false).GetBytes(($result|ConvertTo-Json -Depth 5));$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
}
$result|ConvertTo-Json -Depth 5
