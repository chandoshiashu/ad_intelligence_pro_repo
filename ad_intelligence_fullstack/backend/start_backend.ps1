$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
  py -3 -m venv .venv
}
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
& $python -m pip install --retries 10 --timeout 180 -r requirements.txt
& $python -m uvicorn app.main:app --reload --port 8000
