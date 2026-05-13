$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SpecFile = Join-Path $ScriptDir "pocket-app-win64.spec"
pyinstaller $SpecFile -y