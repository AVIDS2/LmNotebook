$ErrorActionPreference = "Stop"

# Run dev mode with explicit UTF-8 environment to avoid Chinese mojibake.
chcp 65001 > $null
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:NODE_OPTIONS = "--max-old-space-size=4096"

Write-Host "[UTF8] Console + Python UTF-8 mode enabled." -ForegroundColor Green
Write-Host "[UTF8] Starting: npm run dev" -ForegroundColor Green

npm run dev
