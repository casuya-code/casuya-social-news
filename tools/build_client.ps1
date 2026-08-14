# Build script — Casuya Social News Godot client (Windows + Web).
#
# Prereqs:
#   1. Godot 4.7.1 (console) binary at client-godot/.godot-bin/Godot_v4.7.1-stable_win64_console.exe
#   2. Export templates installed to %APPDATA%\Godot\export_templates\4.7.1.stable\
#      (download: https://github.com/godotengine/godot/releases/download/4.7.1-stable/
#       Godot_v4.7.1-stable_export_templates.tpz, extract `templates/` there)
#
# Outputs (gitignored):
#   client-godot/build/casuya-social-news.exe (+ .pck)  — Windows desktop
#   client-godot/build/web/                             — web (wasm) build

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$project = Join-Path $root "client-godot"
$godot = Join-Path $project ".godot-bin\Godot_v4.7.1-stable_win64_console.exe"
$build = Join-Path $project "build"

if (-not (Test-Path $godot)) {
    throw "Godot binary not found: $godot"
}

foreach ($dir in @($build, (Join-Path $build "web"))) {
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
}

Write-Host "== Importing project =="
& $godot --headless --path $project --import
if ($LASTEXITCODE -ne 0) { throw "Import failed (exit $LASTEXITCODE)" }

Write-Host "== Exporting Windows Desktop =="
& $godot --headless --path $project --export-release "Windows Desktop"
if ($LASTEXITCODE -ne 0) { throw "Windows export failed (exit $LASTEXITCODE)" }

Write-Host "== Exporting Web =="
& $godot --headless --path $project --export-release "Web"
if ($LASTEXITCODE -ne 0) { throw "Web export failed (exit $LASTEXITCODE)" }

Write-Host ""
Write-Host "Done. Artifacts:"
Get-ChildItem $build -Recurse -File | ForEach-Object { "  $($_.FullName.Replace($root + '\', ''))  ($([math]::Round($_.Length / 1MB, 2)) MB)" }