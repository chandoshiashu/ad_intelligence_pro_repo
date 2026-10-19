$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path 'package.json')) { throw 'package.json is missing. Re-extract the complete project ZIP.' }
if (-not (Test-Path '.env.local')) { Copy-Item '.env.local.example' '.env.local' }
if (-not (Test-Path 'node_modules')) { npm install }
npm run dev
