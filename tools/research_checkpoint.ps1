param([Parameter(Mandatory=$true)][string]$Label)
$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
$Destination = Join-Path $env:OneDrive 'blast-radius\checkpoints\2026-09-09-standards'
& (Join-Path $PSScriptRoot 'checkpoint.ps1') -Label $Label -Destination $Destination
$Checkpoint = Join-Path $Destination $Label
$Latest = Join-Path $env:OneDrive 'blast-radius\latest'
New-Item -ItemType Directory -Path $Latest -Force | Out-Null
foreach ($Relative in @('README.md','HANDOVER.md','TEST_REPORT.md','DECISIONS.md','DIRECTION.md','CONFORMANCE.md','STRUCTURAL_SUMMARY.md','PRIVACY_ANALYSIS.md','PREREGISTRATION.md','GOVERNANCE.md','NEUTRALITY.md','RECONSTRUCTION_METHOD.md','spec\METRIC_SPECIFICATION_v1.0-draft.md','paper\PAPER_1_DRAFT.md','demo\index.html')) {
    $Source = Join-Path $Project $Relative
    if (Test-Path -LiteralPath $Source) {
        foreach ($Root in @($Checkpoint,$Latest)) {
            $Target = Join-Path $Root $Relative
            New-Item -ItemType Directory -Path (Split-Path $Target -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $Source -Destination $Target -Force
        }
    }
}
Copy-Item -LiteralPath (Join-Path $Checkpoint 'blast-radius-v0.1.zip') -Destination (Join-Path $Latest 'blast-radius.zip') -Force
Copy-Item -LiteralPath (Join-Path $Checkpoint 'SAVE_RECEIPT.json') -Destination (Join-Path $Latest 'SAVE_RECEIPT.json') -Force
Write-Output "Standards checkpoint saved: $Checkpoint"
