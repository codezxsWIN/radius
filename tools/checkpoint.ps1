param(
    [Parameter(Mandatory = $true)][string]$Label,
    [string]$Destination = "$env:OneDrive\Blast-Radius-Build\2026-09-09"
)
$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
$Checkpoint = Join-Path $Destination $Label
New-Item -ItemType Directory -Path $Checkpoint -Force | Out-Null
Add-Type -AssemblyName System.IO.Compression
$ZipPath = Join-Path $Checkpoint 'blast-radius-v0.1.zip'
$Archive = [System.IO.Compression.ZipFile]::Open($ZipPath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($File in Get-ChildItem -LiteralPath $Project -Recurse -File) {
        $Relative = [System.IO.Path]::GetRelativePath($Project, $File.FullName).Replace('\', '/')
        if ($Relative -match '(^|/)(\.venv|\.git|__pycache__|\.pytest_cache|dist|build|exports-live|[^/]+\.egg-info)(/|$)' -or $Relative -match '\.(key|pem|pfx)$|(^|/)\.env|(^|/)\.coverage$') { continue }
        [System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($Archive, $File.FullName, "blast-radius-v0.1/$Relative", [System.IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
} finally { $Archive.Dispose() }
foreach ($Relative in @('README.md', 'HANDOVER.md', 'TEST_REPORT.md', 'demo/index.html')) {
    $Source = Join-Path $Project $Relative
    if (Test-Path -LiteralPath $Source) {
        $Target = Join-Path $Checkpoint $Relative
        New-Item -ItemType Directory -Path (Split-Path $Target -Parent) -Force | Out-Null
        Copy-Item -LiteralPath $Source -Destination $Target
    }
}
$Latest = Join-Path $Destination 'latest'
New-Item -ItemType Directory -Path $Latest -Force | Out-Null
Copy-Item -Path "$Checkpoint\*" -Destination $Latest -Recurse -Force
$Receipt = [ordered]@{ checkpoint=$Label; local_onedrive_path=$Checkpoint; saved_at=(Get-Date -Format o); zip_sha256=(Get-FileHash $ZipPath -Algorithm SHA256).Hash; bytes=(Get-Item $ZipPath).Length; cloud_sync_verified=$false }
$ReceiptJson = $Receipt | ConvertTo-Json
[IO.File]::WriteAllText((Join-Path $Checkpoint 'SAVE_RECEIPT.json'), $ReceiptJson + "`n", [Text.UTF8Encoding]::new($false))
Copy-Item -LiteralPath (Join-Path $Checkpoint 'SAVE_RECEIPT.json') -Destination (Join-Path $Latest 'SAVE_RECEIPT.json') -Force
$ReceiptJson
