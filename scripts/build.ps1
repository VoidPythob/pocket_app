$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$SpecFile = Join-Path $ScriptDir "pocket-app-win32.spec"
pyinstaller $SpecFile -y