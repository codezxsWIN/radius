# Vendored Visual Dependencies

Runtime assets are embedded into the static build. No CDN request, telemetry or network fallback runs in the instrument. Versions and SHA-256 hashes are recorded by tools/vendor_ui.ps1 in manifest.json after downloading public distributable assets.

D3 and js-sha256 use permissive licences; jsPDF/svg2pdf and axe-core retain their upstream notices. Font Awesome Free SVG icons are CC-BY-4.0 and attributed in the instrument's source/evidence view. Atkinson Hyperlegible and IBM Plex Serif fonts are SIL Open Font License assets. Only original UI code is claimed Apache-2.0; upstream assets are not relicensed.
