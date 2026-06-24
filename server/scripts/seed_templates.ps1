#!/usr/bin/env pwsh
# Seed Story Book Templates - PowerShell Script

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   Story Book Template Seeder" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the server directory
if (-not (Test-Path "app")) {
    Write-Host "❌ Error: Please run this script from the server/ directory" -ForegroundColor Red
    exit 1
}

# Check if venv exists
if (-not (Test-Path ".venv")) {
    Write-Host "❌ Error: Virtual environment (.venv) not found" -ForegroundColor Red
    Write-Host "   Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& .\.venv\Scripts\Activate.ps1

# Check if JSON file exists
if (-not (Test-Path "data\story_book_templates.json")) {
    Write-Host "❌ Error: data\story_book_templates.json not found" -ForegroundColor Red
    exit 1
}

# Check if config exists
if (-not (Test-Path "data\seed_config.json")) {
    Write-Host "⚠️  Warning: data\seed_config.json not found" -ForegroundColor Yellow
    Write-Host "   Using default database URL or DATABASE_URL environment variable" -ForegroundColor Yellow
}

Write-Host ""

# Run the seeder
Write-Host "🌱 Starting seeder..." -ForegroundColor Green
Write-Host ""

python scripts\seed_story_templates.py $args

$exitCode = $LASTEXITCODE

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ Seeding completed successfully!" -ForegroundColor Green
} else {
    Write-Host "❌ Seeding failed with exit code $exitCode" -ForegroundColor Red
}

exit $exitCode
