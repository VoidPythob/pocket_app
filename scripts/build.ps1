$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
$ResourcesDir = Join-Path $ProjectRoot "resources"
$ReleaseConfig = Join-Path $ResourcesDir "config-release.json"
$BuildConfig = Join-Path $ResourcesDir "config.json"
$SpecFile = Join-Path $ScriptDir "pocket-app-win64.spec"

Copy-Item $ReleaseConfig $BuildConfig -Force
try {
    Push-Location $ProjectRoot
    pyinstaller $SpecFile -y
}
finally {
    Pop-Location
    if (Test-Path $BuildConfig) {
        Remove-Item $BuildConfig -Force
    }
}
