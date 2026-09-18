# Managed by NWarila/python-template — do not edit manually.
# Source: https://github.com/NWarila/python-template
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $PSCommandPath

# Walk up from ScriptDir to find the repo root (where pyproject.toml lives).
# This works whether the script is at scripts/ or .github/scripts/.
if ($env:PROJECT_ROOT) {
    $ProjectRoot = $env:PROJECT_ROOT
} else {
    $SearchDir = $ScriptDir
    $ProjectRoot = $null
    while ($SearchDir -and $SearchDir -ne (Split-Path -Parent $SearchDir)) {
        if (Test-Path (Join-Path $SearchDir 'pyproject.toml')) {
            $ProjectRoot = $SearchDir
            break
        }
        $SearchDir = Split-Path -Parent $SearchDir
    }
    if (-not $ProjectRoot) {
        Write-Error "Could not find pyproject.toml above $ScriptDir"
        exit 1
    }
}

Write-Host "Project root: $ProjectRoot"
Set-Location $ProjectRoot

# ---------------------------------------------------------------------------
# Detect toolchain
# ---------------------------------------------------------------------------
if (Test-Path 'uv.lock') {
    Write-Host ''
    Write-Host 'Detected uv.lock — using uv toolchain.'
    Write-Host ''

    & uv venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'uv venv failed.' }

    & uv sync
    if ($LASTEXITCODE -ne 0) { throw 'uv sync failed.' }

    Write-Host ''
    Write-Host 'Setup complete (uv).'
    Write-Host '  Activate: .venv\Scripts\Activate.ps1'
}
else {
    Write-Host ''
    Write-Host 'No uv.lock found — using pip + venv toolchain.'
    Write-Host ''

    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Failed to create virtual environment.' }

    $VenvPython = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Failed to upgrade pip.' }

    # Check for [project.optional-dependencies] dev in pyproject.toml
    $HasDevExtras = $false
    $PyprojectPath = Join-Path $ProjectRoot 'pyproject.toml'

    if (Test-Path $PyprojectPath) {
        $InSection = $false
        foreach ($Line in (Get-Content $PyprojectPath)) {
            $Trimmed = $Line.Trim()
            if ($Trimmed -eq '[project.optional-dependencies]') {
                $InSection = $true
                continue
            }
            if ($InSection -and $Trimmed -match '^\[') {
                $InSection = $false
            }
            if ($InSection -and $Trimmed -match '^dev\s*=') {
                $HasDevExtras = $true
                break
            }
        }
    }

    if ($HasDevExtras) {
        Write-Host 'Installing package with dev extras...'
        & $VenvPython -m pip install -e '.[dev]'
        if ($LASTEXITCODE -ne 0) { throw 'Failed to install package with dev extras.' }
    }
    else {
        Write-Host 'Installing package (no dev extras detected)...'
        & $VenvPython -m pip install -e .
        if ($LASTEXITCODE -ne 0) { throw 'Failed to install package.' }
    }

    Write-Host ''
    Write-Host 'Setup complete (pip + venv).'
    Write-Host "  Activate: .venv\Scripts\Activate.ps1"
}
