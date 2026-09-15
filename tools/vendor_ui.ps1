$ErrorActionPreference = 'Stop'
$Project = Split-Path $PSScriptRoot -Parent
$Vendor = Join-Path $Project 'ui\vendor'
$Assets = @(
    @{name='d3.min.js';version='7.9.0';license='ISC';url='https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js'},
    @{name='sha256.min.js';version='0.11.0';license='MIT';url='https://cdn.jsdelivr.net/npm/js-sha256@0.11.0/build/sha256.min.js'},
    @{name='jspdf.umd.min.js';version='2.5.2';license='MIT';url='https://cdn.jsdelivr.net/npm/jspdf@2.5.2/dist/jspdf.umd.min.js'},
    @{name='svg2pdf.umd.min.js';version='2.3.0';license='MIT';url='https://cdn.jsdelivr.net/npm/svg2pdf.js@2.3.0/dist/svg2pdf.umd.min.js'},
    @{name='axe.min.js';version='4.10.3';license='MPL-2.0';url='https://cdn.jsdelivr.net/npm/axe-core@4.10.3/axe.min.js'},
    @{name='AtkinsonHyperlegible-Regular.ttf';version='Google Fonts main snapshot';license='OFL-1.1';url='https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Regular.ttf'},
    @{name='IBMPlexSerif-Regular.ttf';version='Google Fonts main snapshot';license='OFL-1.1';url='https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexserif/IBMPlexSerif-Regular.ttf'},
    @{name='Atkinson-OFL.txt';version='Google Fonts main snapshot';license='OFL-1.1';url='https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/OFL.txt'},
    @{name='Plex-OFL.txt';version='Google Fonts main snapshot';license='OFL-1.1';url='https://raw.githubusercontent.com/google/fonts/main/ofl/ibmplexserif/OFL.txt'},
    @{name='FontAwesome-LICENSE.txt';version='6.7.2';license='CC-BY-4.0 SVG; MIT code; OFL fonts';url='https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.7.2/LICENSE.txt'}
)
$Icons = @('user','server','shield-halved','cubes','robot','key','certificate','ticket','fingerprint','link','mobile-screen','user-check','network-wired','clock','unlock-keyhole','play','pause','forward-step','backward-step','download','file-code','file-pdf','image','rotate-left','plus','minus','magnifying-glass','circle-info','eye','eye-slash','sun','moon','table','code','expand','check','xmark','bars','diagram-project','chart-simple','flask','shield','sliders','arrow-right','arrow-left','copy','folder-open')
foreach ($Icon in $Icons) { $Assets += @{name="icons/$Icon.svg";version='6.7.2';license='CC-BY-4.0';url="https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.7.2/svgs/solid/$Icon.svg"} }
$Manifest = @()
foreach ($Asset in $Assets) {
    $Target = Join-Path $Vendor $Asset.name
    New-Item -ItemType Directory -Path (Split-Path $Target -Parent) -Force | Out-Null
    if (-not (Test-Path -LiteralPath $Target)) { Invoke-WebRequest -Uri $Asset.url -OutFile $Target }
    $Manifest += [ordered]@{name=$Asset.name;version=$Asset.version;license=$Asset.license;source=$Asset.url;sha256=(Get-FileHash $Target -Algorithm SHA256).Hash.ToLower();bytes=(Get-Item $Target).Length}
}
[IO.File]::WriteAllText((Join-Path $Vendor 'manifest.json'), ($Manifest | ConvertTo-Json -Depth 4) + "`n", [Text.UTF8Encoding]::new($false))
Write-Output "Vendored $($Manifest.Count) assets; no runtime CDN required."