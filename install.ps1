param(
    [switch]$NonInteractive,
    [switch]$RunInit,
    [string]$RepoZipUrl = "https://github.com/AlanJs26/dots/archive/refs/heads/main.zip"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "[dots-bootstrap] $Message" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Refresh-SessionPath {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $sessionPath = @($machinePath, $userPath) -join ";"

    foreach ($extra in @(
        "$env:USERPROFILE\\.local\\bin",
        "$env:USERPROFILE\\AppData\\Roaming\\Python\\Python314\\Scripts",
        "$env:USERPROFILE\\AppData\\Local\\Programs\\Python\\Python314\\Scripts"
    )) {
        if (Test-Path $extra) {
            $sessionPath = "$extra;$sessionPath"
        }
    }

    $env:Path = $sessionPath
}

function Install-Uv {
    if (Test-Command "uv") {
        Write-Step "uv already available."
        return
    }

    Write-Step "Installing uv..."
    Invoke-Expression (Invoke-RestMethod -Uri "https://astral.sh/uv/install.ps1")
    Refresh-SessionPath

    if (-not (Test-Command "uv")) {
        throw "uv could not be installed automatically."
    }
}

function Ensure-Git {
    if (Test-Command "git") {
        Write-Step "git already available."
        return
    }

    Write-Step "RunInit requested, installing git..."

    if (Test-Command "winget") {
        & winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements --disable-interactivity
        Refresh-SessionPath
    }

    if (-not (Test-Command "git")) {
        throw "git is required for 'dots init' and could not be installed automatically. Install git and run 'dots init' again."
    }
}

function Install-Dots {
    Write-Step "Downloading project source archive..."

    $tempRoot = Join-Path $env:TEMP ("dots-bootstrap-" + [Guid]::NewGuid().ToString("N"))
    $zipPath = "$tempRoot.zip"
    $extractPath = Join-Path $tempRoot "src"

    Invoke-WebRequest -Uri $RepoZipUrl -OutFile $zipPath
    New-Item -ItemType Directory -Path $extractPath -Force | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

    $projectDir = Get-ChildItem -Path $extractPath -Directory | Select-Object -First 1
    if ($null -eq $projectDir) {
        throw "Could not find extracted project directory."
    }

    Write-Step "Installing dots via uv tool..."
    & uv tool install --python 3.14 --force $projectDir.FullName
    Refresh-SessionPath

    Write-Step "Validating dots command..."
    & uv tool run dots --help | Out-Null
}

function Maybe-RunInit {
    if (-not $RunInit) {
        Write-Step "Skipping dots init. Use 'dots init' when you are ready."
        return
    }

    Ensure-Git

    Write-Step "Running dots init..."
    if (Test-Command "dots") {
        & dots init
    } else {
        & uv tool run dots init
    }
}

Write-Step "Starting zero-dependency bootstrap for dots..."
Install-Uv
Install-Dots
Maybe-RunInit

Write-Host ""
Write-Host "dots is installed." -ForegroundColor Green
if (Test-Command "dots") {
    Write-Host "Try: dots --help"
} else {
    Write-Host "If dots is not found in this shell, open a new terminal and run: dots --help"
    Write-Host "Fallback in current shell: uv tool run dots --help"
}
