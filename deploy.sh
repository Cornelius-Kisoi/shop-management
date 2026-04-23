#!/bin/bash

# Production Deployment Script for EXTREME TECH Shop Management System
# This script handles the complete deployment process

set -e

echo "🚀 Starting EXTREME TECH Production Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="extreme-tech-shop"
BACKUP_DIR="./backups"
ENV_FILE=".env.production"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    # Check if .env.production exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Production environment file ($ENV_FILE) not found."
        log_info "Please copy .env.example to .env.production and configure your settings."
        exit 1
    fi

    log_info "Requirements check passed!"
}

create_backup() {
    log_info "Creating database backup..."

    if [ -d "$BACKUP_DIR" ]; then
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="$BACKUP_DIR/pre_deployment_backup_$TIMESTAMP.sql"

        # If using Docker, backup from container
        if docker ps | grep -q "${PROJECT_NAME}_db"; then
            log_info "Backing up database from Docker container..."
            docker exec ${PROJECT_NAME}_db pg_dump -U $DB_USER -d $DB_NAME > $BACKUP_FILE
        else
            log_warn "Database container not running. Skipping backup."
        fi
    else
        log_warn "Backup directory not found. Skipping backup."
    fi
}

deploy() {
    log_info "Starting deployment..."

    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' $ENV_FILE | xargs)
    fi

    # Stop existing containers
    log_info "Stopping existing containers..."
    docker-compose down || true

    # Remove old images (optional, for clean deployment)
    log_info "Cleaning up old Docker images..."
    docker image prune -f || true

    # Build and start services
    log_info "Building and starting services..."
    docker-compose up -d --build

    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30

    # Run database migrations
    log_info "Running database migrations..."
    docker-compose exec -T web python manage.py migrate

    # Collect static files
    log_info "Collecting static files..."
    docker-compose exec -T web python manage.py collectstatic --noinput

    # Create superuser if it doesn't exist (optional)
    log_info "Checking for superuser..."
    docker-compose exec -T web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

    log_info "Deployment completed successfully!"
}

health_check() {
    log_info "Performing health checks..."

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        log_info "Services are running"
    else
        log_error "Services are not running properly"
        exit 1
    fi

    # Check health endpoint
    if curl -f http://localhost/health/ &> /dev/null; then
        log_info "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
}

rollback() {
    log_error "Deployment failed. Rolling back..."

    # Stop current deployment
    docker-compose down

    # Restore from backup if available
    if [ -f "$BACKUP_DIR/latest_backup.sql" ]; then
        log_info "Restoring from backup..."
        docker-compose up -d db
        sleep 10
        docker exec -i ${PROJECT_NAME}_db psql -U $DB_USER -d $DB_NAME < $BACKUP_DIR/latest_backup.sql
    fi

    log_info "Rollback completed"
}

# Main deployment process
main() {
    log_info "EXTREME TECH Shop Management System - Production Deployment"
    echo "========================================================"

    check_requirements

    # Create backup before deployment
    create_backup

    # Attempt deployment
    if deploy; then
        health_check
        log_info "🎉 Deployment successful!"
        log_info "Application is now running at: http://localhost"
        log_info "Admin panel: http://localhost/admin/"
        log_info "Health check: http://localhost/health/"
    else
        rollback
        exit 1
    fi
}

# Run main function
main "$@"