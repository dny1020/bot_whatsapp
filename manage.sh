#!/bin/bash
# Management script for WhatsApp Chatbot Platform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_usage() {
    echo "WhatsApp Chatbot Platform - Management Script"
    echo ""
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Commands:"
    echo "  start       - Start all services"
    echo "  stop        - Stop all services"
    echo "  restart     - Restart all services"
    echo "  status      - Show service status"
    echo "  logs        - Show logs (follow mode)"
    echo "  logs-tail   - Show last 100 lines of logs"
    echo "  build       - Rebuild Docker images"
    echo "  clean       - Stop and remove all containers and volumes"
    echo "  shell       - Open bash shell in backend container"
    echo "  db-shell    - Open PostgreSQL shell"
    echo "  test        - Run tests"
    echo "  backup      - Backup database"
    echo ""
}

start_services() {
    echo -e "${GREEN}Starting services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ Services started${NC}"
    show_status
}

stop_services() {
    echo -e "${YELLOW}Stopping services...${NC}"
    docker-compose down
    echo -e "${GREEN}✅ Services stopped${NC}"
}

restart_services() {
    echo -e "${YELLOW}Restarting services...${NC}"
    docker-compose restart
    echo -e "${GREEN}✅ Services restarted${NC}"
    show_status
}

show_status() {
    echo -e "\n${GREEN}Service Status:${NC}"
    docker-compose ps
}

show_logs() {
    echo -e "${GREEN}Following logs (Ctrl+C to exit)...${NC}"
    docker-compose logs -f
}

show_logs_tail() {
    echo -e "${GREEN}Last 100 log lines:${NC}"
    docker-compose logs --tail=100
}

build_images() {
    echo -e "${GREEN}Building Docker images...${NC}"
    docker-compose build --no-cache
    echo -e "${GREEN}✅ Images built${NC}"
}

clean_all() {
    echo -e "${RED}⚠️  This will remove all containers, volumes, and data!${NC}"
    read -p "Are you sure? (yes/no): " -r
    if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        echo -e "${YELLOW}Cleaning up...${NC}"
        docker-compose down -v
        echo -e "${GREEN}✅ Cleanup complete${NC}"
    else
        echo "Cancelled"
    fi
}

open_shell() {
    echo -e "${GREEN}Opening bash shell in backend container...${NC}"
    docker-compose exec backend /bin/bash
}

open_db_shell() {
    echo -e "${GREEN}Opening PostgreSQL shell...${NC}"
    docker-compose exec postgres psql -U chatbot -d chatbot_db
}

run_tests() {
    echo -e "${GREEN}Running tests...${NC}"
    docker-compose exec backend python -m pytest tests/ -v
}

backup_db() {
    BACKUP_DIR="backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/chatbot_db_$TIMESTAMP.sql"
    
    echo -e "${GREEN}Creating database backup...${NC}"
    docker-compose exec -T postgres pg_dump -U chatbot chatbot_db > "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
}

# Main
case "${1:-}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-tail)
        show_logs_tail
        ;;
    build)
        build_images
        ;;
    clean)
        clean_all
        ;;
    shell)
        open_shell
        ;;
    db-shell)
        open_db_shell
        ;;
    test)
        run_tests
        ;;
    backup)
        backup_db
        ;;
    *)
        print_usage
        exit 1
        ;;
esac
