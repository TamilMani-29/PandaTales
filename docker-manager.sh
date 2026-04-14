#!/bin/bash

# ===========================================
# PandaTales Docker Management Scripts
# ===========================================
# 
# Bash script for common Docker operations
# Run: ./docker-manager.sh <command>
#

set -e

COMMAND="${1:-help}"
ARG="${2:-development}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_help() {
    echo -e "${CYAN}🐼 PandaTales Docker Manager${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
    echo -e "${YELLOW}Usage: ./docker-manager.sh <command> [environment]${NC}"
    echo ""
    echo -e "${GREEN}Commands:${NC}"
    echo "  start [env]       - Start all services (default: development)"
    echo "  stop              - Stop all services"
    echo "  restart [service] - Restart all or specific service"
    echo "  build             - Build all images"
    echo "  rebuild [service] - Rebuild specific service"
    echo "  logs [service]    - View logs (all or specific service)"
    echo "  ps                - List running containers"
    echo "  clean             - Stop and remove containers"
    echo "  purge             - Remove everything (containers, volumes, images)"
    echo "  migrate           - Run database migrations"
    echo "  shell <service>   - Open shell in service container"
    echo "  db                - Open PostgreSQL shell"
    echo "  status            - Show service status and health"
    echo "  help              - Show this help message"
    echo ""
    echo -e "${GREEN}Environments:${NC}"
    echo "  development       - Dev mode with hot-reload (default)"
    echo "  production        - Production mode with optimizations"
    echo ""
    echo -e "${YELLOW}Examples:${NC}"
    echo "  ./docker-manager.sh start"
    echo "  ./docker-manager.sh start production"
    echo "  ./docker-manager.sh logs backend"
    echo "  ./docker-manager.sh shell backend"
    echo "  ./docker-manager.sh rebuild frontend"
}

start_services() {
    local env=$1
    echo -e "${GREEN}🚀 Starting PandaTales services ($env mode)...${NC}"
    
    if [ "$env" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
    else
        docker-compose -f docker-compose.yml -f docker-compose.dev.yml --env-file .env.development up
    fi
}

stop_services() {
    echo -e "${YELLOW}⏸️  Stopping all services...${NC}"
    docker-compose down
}

restart_service() {
    local service=$1
    if [ -n "$service" ]; then
        echo -e "${CYAN}🔄 Restarting $service...${NC}"
        docker-compose restart "$service"
    else
        echo -e "${CYAN}🔄 Restarting all services...${NC}"
        docker-compose restart
    fi
}

build_images() {
    echo -e "${GREEN}🏗️  Building all images...${NC}"
    docker-compose build
}

rebuild_service() {
    local service=$1
    if [ -n "$service" ]; then
        echo -e "${GREEN}🏗️  Rebuilding $service...${NC}"
        docker-compose build --no-cache "$service"
        docker-compose up -d "$service"
    else
        echo -e "${RED}❌ Please specify a service name${NC}"
        echo -e "${YELLOW}Available services: frontend, backend, postgres, minio${NC}"
    fi
}

show_logs() {
    local service=$1
    if [ -n "$service" ]; then
        echo -e "${CYAN}📋 Showing logs for $service...${NC}"
        docker-compose logs -f "$service"
    else
        echo -e "${CYAN}📋 Showing all logs...${NC}"
        docker-compose logs -f
    fi
}

show_processes() {
    echo -e "${CYAN}📊 Container Status:${NC}"
    docker-compose ps
}

clean_environment() {
    echo -e "${YELLOW}🧹 Cleaning up containers...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

purge_environment() {
    echo -e "${RED}⚠️  WARNING: This will remove ALL containers, volumes, and images!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        echo -e "${RED}🗑️  Purging everything...${NC}"
        docker-compose down -v --rmi all --remove-orphans
        echo -e "${GREEN}✅ Purge complete${NC}"
    else
        echo -e "${YELLOW}❌ Purge cancelled${NC}"
    fi
}

run_migrations() {
    echo -e "${CYAN}🔄 Running database migrations...${NC}"
    docker-compose exec backend alembic upgrade head
}

open_shell() {
    local service=$1
    if [ -n "$service" ]; then
        echo -e "${CYAN}🐚 Opening shell in $service...${NC}"
        docker-compose exec "$service" sh
    else
        echo -e "${RED}❌ Please specify a service name${NC}"
        echo -e "${YELLOW}Available services: frontend, backend, postgres, minio${NC}"
    fi
}

open_database() {
    echo -e "${CYAN}🐘 Opening PostgreSQL shell...${NC}"
    docker-compose exec postgres psql -U pandatales -d pandatales
}

show_status() {
    echo -e "${CYAN}📊 PandaTales Service Status${NC}"
    echo -e "${CYAN}=============================${NC}"
    docker-compose ps
    echo ""
    echo -e "${GREEN}💾 Volume Usage:${NC}"
    docker volume ls | grep pandatales || echo "No volumes found"
    echo ""
    echo -e "${GREEN}🌐 Service URLs:${NC}"
    echo -e "${YELLOW}  Frontend:      http://localhost:3000${NC}"
    echo -e "${YELLOW}  Backend API:   http://localhost:8000${NC}"
    echo -e "${YELLOW}  API Docs:      http://localhost:8000/docs${NC}"
    echo -e "${YELLOW}  MinIO Console: http://localhost:9001${NC}"
}

# Main command router
case "$COMMAND" in
    start)
        start_services "$ARG"
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_service "$ARG"
        ;;
    build)
        build_images
        ;;
    rebuild)
        rebuild_service "$ARG"
        ;;
    logs)
        show_logs "$ARG"
        ;;
    ps)
        show_processes
        ;;
    clean)
        clean_environment
        ;;
    purge)
        purge_environment
        ;;
    migrate)
        run_migrations
        ;;
    shell)
        open_shell "$ARG"
        ;;
    db)
        open_database
        ;;
    status)
        show_status
        ;;
    help)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $COMMAND${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
