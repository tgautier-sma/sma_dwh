#!/bin/bash

# SMA DWH - Docker Deployment Script
# Description: Build and deploy the application with Docker Compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""
}

# Check if .env file exists
check_env_file() {
    if [ ! -f .env ]; then
        print_warning ".env file not found"
        if [ -f .env.example ]; then
            print_info "Copying .env.example to .env"
            cp .env.example .env
            print_warning "Please update .env with your configuration"
            exit 1
        else
            print_error ".env.example file not found"
            exit 1
        fi
    fi
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if Docker Compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null 2>&1; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Determine which command to use
    if docker compose version &> /dev/null 2>&1; then
        COMPOSE_CMD="docker compose"
    else
        COMPOSE_CMD="docker-compose"
    fi
    print_success "Docker Compose is available: $COMPOSE_CMD"
}

# Build the Docker image
build_image() {
    print_header "Building Docker Image"
    print_info "Building application image..."
    
    $COMPOSE_CMD build --no-cache
    
    print_success "Docker image built successfully"
}

# Start the services
start_services() {
    print_header "Starting Services"
    print_info "Starting containers..."
    
    $COMPOSE_CMD up -d
    
    print_success "Services started successfully"
}

# Stop the services
stop_services() {
    print_header "Stopping Services"
    print_info "Stopping containers..."
    
    $COMPOSE_CMD down
    
    print_success "Services stopped successfully"
}

# View logs
view_logs() {
    print_header "Viewing Logs"
    print_info "Showing logs (Ctrl+C to exit)..."
    
    $COMPOSE_CMD logs -f
}

# Check service health
check_health() {
    print_header "Checking Service Health"
    
    # Wait for services to be ready
    print_info "Waiting for services to start (max 60s)..."
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Application is healthy"
            
            # Show service URLs
            echo ""
            print_info "Service URLs:"
            echo "  📱 Application: http://localhost:8000"
            echo "  📚 API Documentation: http://localhost:8000/docs"
            echo "  🔍 API Redoc: http://localhost:8000/redoc"
            echo ""
            
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 1
    done
    
    print_error "Application health check failed after ${max_attempts}s"
    print_info "Check logs with: ./deploy.sh logs"
    return 1
}

# Show service status
show_status() {
    print_header "Service Status"
    $COMPOSE_CMD ps
}

# Clean up (remove containers, volumes, images)
cleanup() {
    print_header "Cleaning Up"
    print_warning "This will remove all containers, volumes, and images"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" == "yes" ]; then
        print_info "Stopping and removing containers..."
        $COMPOSE_CMD down -v --remove-orphans
        
        print_info "Removing images..."
        docker rmi $(docker images "sma_dwh*" -q) 2>/dev/null || true
        
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Main script
main() {
    print_header "SMA DWH - Docker Deployment"
    
    # Parse command line arguments
    case "${1:-deploy}" in
        build)
            check_docker
            check_docker_compose
            build_image
            ;;
        start)
            check_docker
            check_docker_compose
            start_services
            check_health
            ;;
        stop)
            check_docker
            check_docker_compose
            stop_services
            ;;
        restart)
            check_docker
            check_docker_compose
            stop_services
            start_services
            check_health
            ;;
        deploy)
            check_env_file
            check_docker
            check_docker_compose
            build_image
            start_services
            check_health
            ;;
        logs)
            check_docker
            check_docker_compose
            view_logs
            ;;
        status)
            check_docker
            check_docker_compose
            show_status
            ;;
        clean)
            check_docker
            check_docker_compose
            cleanup
            ;;
        *)
            echo "Usage: $0 {build|start|stop|restart|deploy|logs|status|clean}"
            echo ""
            echo "Commands:"
            echo "  build    - Build Docker image"
            echo "  start    - Start services"
            echo "  stop     - Stop services"
            echo "  restart  - Restart services"
            echo "  deploy   - Build and deploy (default)"
            echo "  logs     - View service logs"
            echo "  status   - Show service status"
            echo "  clean    - Remove all containers, volumes, and images"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
