Param(
  [switch]$RecreateVenv = $false,
  [int]$Port = 5001
)

$ErrorActionPreference = 'Stop'

# Move to repository root (directory containing this script is scripts/)
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
Set-Location $repoRoot

Write-Host "Repo root: $repoRoot"

# Ensure venv exists (or recreate when requested)
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
if ($RecreateVenv -and (Test-Path $venvPython)) {
  Write-Host "Removing existing venv..." -ForegroundColor Yellow
  Remove-Item -Recurse -Force (Join-Path $repoRoot ".venv")
}

if (-not (Test-Path $venvPython)) {
  Write-Host "Creating virtual environment (.venv) with system python..." -ForegroundColor Yellow
  $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
  if (-not $pythonCmd) {
    throw "'python' not found on PATH. Please install Python 3.11+ and ensure it's on PATH."
  }
  & $pythonCmd.Path -m venv .venv
  if (-not (Test-Path $venvPython)) {
    throw "Failed to create .venv. Verify that Python 3.11+ is installed."
  }
}

# Upgrade pip and install dependencies
Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $venvPython -m pip install -U pip

Write-Host "Installing project requirements..." -ForegroundColor Cyan
& $venvPython -m pip install -r (Join-Path $repoRoot 'requirements.txt')

# Start server
Write-Host "Starting R2R Financial Close API server on port $Port..." -ForegroundColor Green
# Open health endpoint shortly after start in the default browser
Start-Job -ScriptBlock {
  param($p)
  Start-Sleep -Seconds 1
  Start-Process "http://localhost:$p/api/health"
} -ArgumentList $Port | Out-Null

# Run the Flask server (this keeps the console open)
& $venvPython (Join-Path $repoRoot 'api\server.py')
