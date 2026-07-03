<#
.SYNOPSIS
Installs (or updates) the claude-base-kit into a host project's .claude/ directory.

.DESCRIPTION
Copies core/ content into the target repo. NEVER overwrites an existing file — on a name
collision the host's file wins and the kit file is skipped (reported). Idempotent: re-run
to pick up new kit files after pulling this repo.

.EXAMPLE
.\install.ps1 -Target C:\path\to\your-project
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$Target
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $Target -PathType Container)) {
    Write-Error "Target directory not found: $Target"
    exit 1
}

$kitRoot   = Split-Path -Parent $PSScriptRoot   # repo root (install/ -> root)
$claudeDir = Join-Path $Target '.claude'

$installed = @()
$skipped   = @()

function Copy-KitFiles {
    param([string]$SourceSubdir, [string]$DestSubdir)

    $src = Join-Path $kitRoot $SourceSubdir
    $dst = Join-Path $claudeDir $DestSubdir
    New-Item -ItemType Directory -Force -Path $dst | Out-Null

    foreach ($file in Get-ChildItem $src -Filter '*.md' -File) {
        $destFile = Join-Path $dst $file.Name
        if (Test-Path $destFile) {
            $script:skipped += ".claude\$DestSubdir\$($file.Name)"
        } else {
            Copy-Item $file.FullName $destFile
            $script:installed += ".claude\$DestSubdir\$($file.Name)"
        }
    }
}

Copy-KitFiles 'core\agents'     'agents'
Copy-KitFiles 'core\principles' 'principles'
Copy-KitFiles 'core\pipelines'  'pipelines'
Copy-KitFiles 'core\templates'  'templates'

# Seed the stack contract into rules/ if the host doesn't have one yet
$rulesDir = Join-Path $claudeDir 'rules'
New-Item -ItemType Directory -Force -Path $rulesDir | Out-Null
$contract = Join-Path $rulesDir 'stack-contract.md'
if (Test-Path $contract) {
    $skipped += '.claude\rules\stack-contract.md'
} else {
    Copy-Item (Join-Path $kitRoot 'core\templates\stack-contract.md') $contract
    $installed += '.claude\rules\stack-contract.md  (fill this in!)'
}

# Local knowledge capture directory
$lessonsDir = Join-Path $claudeDir 'lessons'
if (-not (Test-Path $lessonsDir)) {
    New-Item -ItemType Directory -Force -Path $lessonsDir | Out-Null
    New-Item -ItemType File -Path (Join-Path $lessonsDir '.gitkeep') | Out-Null
    $installed += '.claude\lessons\'
}

Write-Host ''
Write-Host "claude-base-kit install -> $Target" -ForegroundColor Cyan
Write-Host ("  Installed: {0}" -f $installed.Count) -ForegroundColor Green
$installed | ForEach-Object { Write-Host "    + $_" -ForegroundColor Green }
Write-Host ("  Skipped (host file wins): {0}" -f $skipped.Count) -ForegroundColor Yellow
$skipped | ForEach-Object { Write-Host "    = $_" -ForegroundColor Yellow }
Write-Host ''
Write-Host 'Next steps:' -ForegroundColor Cyan
Write-Host '  1. Fill .claude/rules/stack-contract.md (agents BLOCK without it).'
Write-Host '  2. No CLAUDE.md in the host? Start from .claude/templates/CLAUDE.skeleton.md.'
Write-Host '  3. Feature-sized work: run the sdlc-feature pipeline (.claude/pipelines/).'
