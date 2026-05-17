$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    & $VenvPython -m teleeu_bot
    exit $LASTEXITCODE
}

$env:PYTHONPATH = Join-Path $ProjectRoot "src"
python -m teleeu_bot
