param(
  [string]$RepoRoot = (Get-Location).Path
)

$errors = @()
$warnings = @()

function Test-PathRequired($path, $label) {
  if (-not (Test-Path $path)) {
    $errors += "$label not found: $path"
  }
}

function Test-PathWarn($path, $label) {
  if (-not (Test-Path $path)) {
    $warnings += "$label not found: $path"
  }
}

# Basic paths
$backendEnv = Join-Path $RepoRoot "backend_env"
$backendEnvActivate = Join-Path $backendEnv "Scripts\activate"
$backendDist = Join-Path $RepoRoot "src\backend\dist\origin_backend"
$backendEnvFile = Join-Path $RepoRoot "src\backend\.env"

# Checks
Test-PathRequired $backendEnv "backend_env directory"
Test-PathRequired $backendEnvActivate "backend_env activation script"
Test-PathWarn $backendEnvFile "backend .env"
Test-PathWarn $backendDist "backend build output (run PyInstaller first)"

# Tooling checks
try {
  $node = node --version 2>$null
  if (-not $node) { $warnings += "node not found in PATH" }
} catch { $warnings += "node not found in PATH" }

try {
  $python = python --version 2>$null
  if (-not $python) { $warnings += "python not found in PATH" }
} catch { $warnings += "python not found in PATH" }

# Output
if ($errors.Count -gt 0) {
  Write-Host "FAIL" -ForegroundColor Red
  $errors | ForEach-Object { Write-Host $_ -ForegroundColor Red }
} else {
  Write-Host "OK" -ForegroundColor Green
}

if ($warnings.Count -gt 0) {
  Write-Host "WARN" -ForegroundColor Yellow
  $warnings | ForEach-Object { Write-Host $_ -ForegroundColor Yellow }
}

if ($errors.Count -gt 0) { exit 1 }
