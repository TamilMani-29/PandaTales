# ===========================================
# PandaTales Docker Management Scripts
# ===========================================
# 
# PowerShell scripts for common Docker operations
# Run: .\docker-manager.ps1 <command>
#

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Environment = "development"
)

function Show-Help {
    Write-Host "🐼 PandaTales Docker Manager" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\docker-manager.ps1 <command> [environment]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor Green
    Write-Host "  start [env]       - Start all services (default: development)"
    Write-Host "  stop              - Stop all services"
    Write-Host "  restart [service] - Restart all or specific service"
    Write-Host "  build             - Build all images"
    Write-Host "  rebuild [service] - Rebuild specific service"
    Write-Host "  logs [service]    - View logs (all or specific service)"
    Write-Host "  ps                - List running containers"
    Write-Host "  clean             - Stop and remove containers"
    Write-Host "  purge             - Remove everything (containers, volumes, images)"
    Write-Host "  migrate           - Run database migrations"
    Write-Host "  shell <service>   - Open shell in service container"
    Write-Host "  db                - Open PostgreSQL shell"
    Write-Host "  status            - Show service status and health"
    Write-Host "  help              - Show this help message"
    Write-Host ""
    Write-Host "Environments:" -ForegroundColor Green
    Write-Host "  development       - Dev mode with hot-reload (default)"
    Write-Host "  production        - Production mode with optimizations"
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\docker-manager.ps1 start"
    Write-Host "  .\docker-manager.ps1 start production"
    Write-Host "  .\docker-manager.ps1 logs backend"
    Write-Host "  .\docker-manager.ps1 shell backend"
    Write-Host "  .\docker-manager.ps1 rebuild frontend"
}

function Start-Services {
    param([string]$Env)
    
    Write-Host "🚀 Starting PandaTales services ($Env mode)..." -ForegroundColor Green
    
    if ($Env -eq "production") {
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
    } else {
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.development up
    }
}

function Stop-Services {
    Write-Host "⏸️  Stopping all services..." -ForegroundColor Yellow
    docker-compose down
}

function Restart-Service {
    param([string]$ServiceName)
    
    if ($ServiceName) {
        Write-Host "🔄 Restarting $ServiceName..." -ForegroundColor Cyan
        docker-compose restart $ServiceName
    } else {
        Write-Host "🔄 Restarting all services..." -ForegroundColor Cyan
        docker-compose restart
    }
}

function Build-Images {
    Write-Host "🏗️  Building all images..." -ForegroundColor Green
    docker-compose build
}

function Rebuild-Service {
    param([string]$ServiceName)
    
    if ($ServiceName) {
        Write-Host "🏗️  Rebuilding $ServiceName..." -ForegroundColor Green
        docker-compose build --no-cache $ServiceName
        docker-compose up -d $ServiceName
    } else {
        Write-Host "❌ Please specify a service name" -ForegroundColor Red
        Write-Host "Available services: frontend, backend, postgres, minio" -ForegroundColor Yellow
    }
}

function Show-Logs {
    param([string]$ServiceName)
    
    if ($ServiceName) {
        Write-Host "📋 Showing logs for $ServiceName..." -ForegroundColor Cyan
        docker-compose logs -f $ServiceName
    } else {
        Write-Host "📋 Showing all logs..." -ForegroundColor Cyan
        docker-compose logs -f
    }
}

function Show-Processes {
    Write-Host "📊 Container Status:" -ForegroundColor Cyan
    docker-compose ps
}

function Clean-Environment {
    Write-Host "🧹 Cleaning up containers..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Cleanup complete" -ForegroundColor Green
}

function Purge-Environment {
    Write-Host "⚠️  WARNING: This will remove ALL containers, volumes, and images!" -ForegroundColor Red
    $confirm = Read-Host "Are you sure? (yes/no)"
    
    if ($confirm -eq "yes") {
        Write-Host "🗑️  Purging everything..." -ForegroundColor Red
        docker-compose down -v --rmi all --remove-orphans
        Write-Host "✅ Purge complete" -ForegroundColor Green
    } else {
        Write-Host "❌ Purge cancelled" -ForegroundColor Yellow
    }
}

function Run-Migrations {
    Write-Host "🔄 Running database migrations..." -ForegroundColor Cyan
    docker-compose exec backend alembic upgrade head
}

function Open-Shell {
    param([string]$ServiceName)
    
    if ($ServiceName) {
        Write-Host "🐚 Opening shell in $ServiceName..." -ForegroundColor Cyan
        docker-compose exec $ServiceName sh
    } else {
        Write-Host "❌ Please specify a service name" -ForegroundColor Red
        Write-Host "Available services: frontend, backend, postgres, minio" -ForegroundColor Yellow
    }
}

function Open-Database {
    Write-Host "🐘 Opening PostgreSQL shell..." -ForegroundColor Cyan
    docker-compose exec postgres psql -U pandatales -d pandatales
}

function Show-Status {
    Write-Host "📊 PandaTales Service Status" -ForegroundColor Cyan
    Write-Host "=============================" -ForegroundColor Cyan
    docker-compose ps
    Write-Host ""
    Write-Host "💾 Volume Usage:" -ForegroundColor Green
    docker volume ls | Select-String "pandatales"
    Write-Host ""
    Write-Host "🌐 Service URLs:" -ForegroundColor Green
    Write-Host "  Frontend:     http://localhost:3000" -ForegroundColor Yellow
    Write-Host "  Backend API:  http://localhost:8000" -ForegroundColor Yellow
    Write-Host "  API Docs:     http://localhost:8000/docs" -ForegroundColor Yellow
    Write-Host "  MinIO Console: http://localhost:9001" -ForegroundColor Yellow
}

# Main command router
switch ($Command.ToLower()) {
    "start" { Start-Services -Env $Environment }
    "stop" { Stop-Services }
    "restart" { Restart-Service -ServiceName $Environment }
    "build" { Build-Images }
    "rebuild" { Rebuild-Service -ServiceName $Environment }
    "logs" { Show-Logs -ServiceName $Environment }
    "ps" { Show-Processes }
    "clean" { Clean-Environment }
    "purge" { Purge-Environment }
    "migrate" { Run-Migrations }
    "shell" { Open-Shell -ServiceName $Environment }
    "db" { Open-Database }
    "status" { Show-Status }
    "help" { Show-Help }
    default { 
        Write-Host "❌ Unknown command: $Command" -ForegroundColor Red
        Write-Host ""
        Show-Help
    }
}
