$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$specPath = Join-Path $projectRoot "main.spec"
$venvPyInstaller = Join-Path $projectRoot ".venv\\Scripts\\pyinstaller.exe"
$buildStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$distRoot = Join-Path $projectRoot "dist\\pyinstaller\\$buildStamp"
$workRoot = Join-Path $projectRoot "build\\pyinstaller\\$buildStamp"

New-Item -ItemType Directory -Force -Path $distRoot | Out-Null
New-Item -ItemType Directory -Force -Path $workRoot | Out-Null

if (Test-Path $venvPyInstaller) {
    & $venvPyInstaller --clean --noconfirm --distpath $distRoot --workpath $workRoot $specPath
    exit $LASTEXITCODE
}

pyinstaller --clean --noconfirm --distpath $distRoot --workpath $workRoot $specPath
