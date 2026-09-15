param([Parameter(Mandatory=$true)][string]$Label)
$ErrorActionPreference='Stop'
$Project=Split-Path $PSScriptRoot -Parent
$Destination=Join-Path $env:OneDrive 'blast-radius\checkpoints\2026-09-09-visual'
& (Join-Path $PSScriptRoot 'checkpoint.ps1') -Label $Label -Destination $Destination
$Checkpoint=Join-Path $Destination $Label
$Latest=Join-Path $env:OneDrive 'blast-radius\latest'
foreach($Relative in @('HANDOVER.md','DECISIONS.md','UI_ROADMAP.md','UI_TEST_REPORT.md','ui\index.html','ui\tokens.json','spec\VISUAL_VOCABULARY_v0.1.md')) {
    $Source=Join-Path $Project $Relative
    if(Test-Path -LiteralPath $Source){foreach($TargetRoot in @($Checkpoint,$Latest)){$Target=Join-Path $TargetRoot $Relative;New-Item -ItemType Directory -Path (Split-Path $Target -Parent) -Force|Out-Null;Copy-Item -LiteralPath $Source -Destination $Target -Force}}
}
Copy-Item -LiteralPath (Join-Path $Checkpoint 'blast-radius-v0.1.zip') -Destination (Join-Path $Latest 'blast-radius-visual.zip') -Force
Write-Output "Visual checkpoint saved: $Checkpoint"