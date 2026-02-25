# Database migration script for StoryBloom (PowerShell)

param(
    [Parameter(Position=0)]
    [string]$Command = "upgrade",
    
    [Parameter(Position=1)]
    [string]$Message = ""
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "StoryBloom Database Migration" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if alembic is available
$alembicExists = Get-Command alembic -ErrorAction SilentlyContinue
if (-not $alembicExists) {
    Write-Host "❌ Alembic is not installed!" -ForegroundColor Red
    Write-Host "Please activate your virtual environment and install dependencies:" -ForegroundColor Yellow
    Write-Host "  .venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host "  uv pip install -e ." -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "⚠️  Warning: .env file not found!" -ForegroundColor Yellow
    Write-Host "Using default DATABASE_URL from environment" -ForegroundColor Yellow
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: .\db_migrate.ps1 [command] [message]" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  upgrade      Apply all pending migrations (default)" -ForegroundColor Gray
    Write-Host "  downgrade    Rollback last migration" -ForegroundColor Gray
    Write-Host "  current      Show current migration version" -ForegroundColor Gray
    Write-Host "  history      Show migration history" -ForegroundColor Gray
    Write-Host "  create       Create a new migration (requires message)" -ForegroundColor Gray
    Write-Host "  reset        Reset database (downgrade all and upgrade)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor White
    Write-Host "  .\db_migrate.ps1 upgrade" -ForegroundColor Gray
    Write-Host "  .\db_migrate.ps1 create 'Add user table'" -ForegroundColor Gray
    Write-Host "  .\db_migrate.ps1 downgrade" -ForegroundColor Gray
    exit 1
}

# Process commands
switch ($Command.ToLower()) {
    "upgrade" {
        Write-Host "📦 Applying migrations..." -ForegroundColor Blue
        alembic upgrade head
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Migrations applied successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Migration failed!" -ForegroundColor Red
            exit 1
        }
    }
    
    "downgrade" {
        Write-Host "⏪ Rolling back last migration..." -ForegroundColor Blue
        alembic downgrade -1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Rollback completed!" -ForegroundColor Green
        } else {
            Write-Host "❌ Rollback failed!" -ForegroundColor Red
            exit 1
        }
    }
    
    "current" {
        Write-Host "📍 Current migration version:" -ForegroundColor Blue
        alembic current
    }
    
    "history" {
        Write-Host "📜 Migration history:" -ForegroundColor Blue
        alembic history
    }
    
    "create" {
        if ([string]::IsNullOrWhiteSpace($Message)) {
            Write-Host "❌ Error: Migration message required!" -ForegroundColor Red
            Write-Host "Usage: .\db_migrate.ps1 create 'Your migration message'" -ForegroundColor Yellow
            exit 1
        }
        Write-Host "✏️  Creating new migration: $Message" -ForegroundColor Blue
        alembic revision --autogenerate -m "$Message"
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Migration created!" -ForegroundColor Green
            Write-Host "⚠️  Please review the generated migration file before applying it." -ForegroundColor Yellow
        } else {
            Write-Host "❌ Migration creation failed!" -ForegroundColor Red
            exit 1
        }
    }
    
    "reset" {
        Write-Host "🔄 Resetting database..." -ForegroundColor Blue
        Write-Host "⚠️  This will rollback all migrations and reapply them." -ForegroundColor Yellow
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            alembic downgrade base
            if ($LASTEXITCODE -eq 0) {
                alembic upgrade head
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Database reset completed!" -ForegroundColor Green
                } else {
                    Write-Host "❌ Upgrade after reset failed!" -ForegroundColor Red
                    exit 1
                }
            } else {
                Write-Host "❌ Downgrade failed!" -ForegroundColor Red
                exit 1
            }
        } else {
            Write-Host "❌ Reset cancelled" -ForegroundColor Red
            exit 1
        }
    }
    
    { $_ -in "help", "--help", "-h" } {
        Show-Usage
    }
    
    default {
        Write-Host "❌ Error: Unknown command '$Command'" -ForegroundColor Red
        Write-Host ""
        Show-Usage
    }
}
