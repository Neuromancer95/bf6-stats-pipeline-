# Push bf6-stats-pipeline to https://github.com/Neuromancer95/bf6-stats-pipeline-
# Run from this folder. Requires Git installed and on PATH.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "Git not found. Install from https://git-scm.com/ and ensure it is on PATH." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path .git)) {
    git init
    git add .
    git commit -m "Initial commit: BF6 stats pipeline"
}

$remote = "https://github.com/Neuromancer95/bf6-stats-pipeline-.git"
$exists = git remote get-url origin 2>$null
if (-not $exists) {
    git remote add origin $remote
} elseif ($exists -ne $remote) {
    git remote set-url origin $remote
}

git branch -M main
git push -u origin main --force

Write-Host "Done. Repo: https://github.com/Neuromancer95/bf6-stats-pipeline-" -ForegroundColor Green
