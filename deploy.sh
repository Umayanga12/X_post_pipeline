#!/bin/bash

# Crypto News Pipe Deployment Script
# This script helps deploy the application to various cloud platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="crypto-news-pipe"
DOCKER_IMAGE="$APP_NAME"
PRODUCTION_COMPOSE="docker-compose.prod.yaml"
DEV_COMPOSE="docker-compose.yaml"

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    log_success "All dependencies are installed"
}

# Environment setup
setup_environment() {
    log_info "Setting up environment..."

    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warning "Created .env from .env.example. Please update with your actual values."
        else
            log_warning "No .env file found. Creating template..."
            cat > .env << EOF
# Twitter/X API Credentials
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_SECRET=your_access_secret_here

# Ollama Configuration
OLLAMA_MODEL=hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF

# Application Settings
LOG_LEVEL=INFO
POSTED_FILE=posted.json
IMAGE_FOLDER=image
EOF
        fi
        log_warning "Please edit .env file with your actual credentials before proceeding."
        exit 1
    fi

    log_success "Environment configured"
}

# Build Docker image
build_image() {
    local dockerfile=${1:-Dockerfile}
    log_info "Building Docker image using $dockerfile..."

    docker build -t $DOCKER_IMAGE -f $dockerfile .

    log_success "Docker image built successfully"
}

# Deploy locally for development
deploy_dev() {
    log_info "Deploying for development..."

    setup_environment
    check_dependencies

    # Build and start services
    docker compose -f $DEV_COMPOSE down --remove-orphans
    docker compose -f $DEV_COMPOSE build
    docker compose -f $DEV_COMPOSE up -d

    log_success "Development deployment complete"
    log_info "Services started:"
    docker compose -f $DEV_COMPOSE ps
}

# Deploy for production
deploy_prod() {
    log_info "Deploying for production..."

    setup_environment
    check_dependencies

    # Use production dockerfile and compose
    docker-compose -f $PRODUCTION_COMPOSE down --remove-orphans
    docker-compose -f $PRODUCTION_COMPOSE build
    docker-compose -f $PRODUCTION_COMPOSE up -d

    log_success "Production deployment complete"
    log_info "Services started:"
    docker-compose -f $PRODUCTION_COMPOSE ps
}

# Deploy to AWS ECS
deploy_aws() {
    log_info "Deploying to AWS ECS..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi

    # Build and push image to ECR
    AWS_REGION=${AWS_REGION:-us-east-1}
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$APP_NAME"

    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names $APP_NAME --region $AWS_REGION || \
    aws ecr create-repository --repository-name $APP_NAME --region $AWS_REGION

    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI

    # Build and push
    docker build -t $APP_NAME -f Dockerfile.prod --target production .
    docker tag $APP_NAME:latest $ECR_URI:latest
    docker push $ECR_URI:latest

    log_success "Image pushed to ECR: $ECR_URI:latest"
    log_info "You can now deploy this image to ECS using the AWS console or CLI"
}

# Deploy to Google Cloud Run
deploy_gcp() {
    log_info "Deploying to Google Cloud Run..."

    # Check gcloud CLI
    if ! command -v gcloud &> /dev/null; then
        log_error "Google Cloud CLI is not installed. Please install it first."
        exit 1
    fi

    PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
    REGION=${GCP_REGION:-us-central1}

    if [ -z "$PROJECT_ID" ]; then
        log_error "GCP_PROJECT_ID environment variable is not set and no default project configured"
        exit 1
    fi

    # Build and push to Container Registry
    IMAGE_URI="gcr.io/$PROJECT_ID/$APP_NAME"

    docker build -t $APP_NAME -f Dockerfile.prod --target production .
    docker tag $APP_NAME $IMAGE_URI
    docker push $IMAGE_URI

    # Deploy to Cloud Run
    gcloud run deploy $APP_NAME \
        --image $IMAGE_URI \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --set-env-vars="ENVIRONMENT=production" \
        --memory=2Gi \
        --cpu=1 \
        --timeout=3600 \
        --concurrency=1 \
        --max-instances=1

    log_success "Deployed to Google Cloud Run"
}

# Deploy to DigitalOcean App Platform
deploy_digitalocean() {
    log_info "Preparing for DigitalOcean App Platform deployment..."

    # Create app spec
    cat > app.yaml << EOF
name: crypto-news-pipe
services:
- name: crypto-news-pipe
  source_dir: /
  dockerfile_path: Dockerfile.prod
  build_command: ""
  environment_slug: docker
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: X_API_KEY
    scope: RUN_TIME
    value: \${X_API_KEY}
  - key: X_API_SECRET
    scope: RUN_TIME
    value: \${X_API_SECRET}
  - key: X_ACCESS_TOKEN
    scope: RUN_TIME
    value: \${X_ACCESS_TOKEN}
  - key: X_ACCESS_SECRET
    scope: RUN_TIME
    value: \${X_ACCESS_SECRET}
  - key: ENVIRONMENT
    scope: RUN_TIME
    value: production
EOF

    log_success "Created app.yaml for DigitalOcean App Platform"
    log_info "Upload your code to GitHub and create an app using the app.yaml spec"
}

# Stop services
stop() {
    log_info "Stopping services..."

    if [ -f "$PRODUCTION_COMPOSE" ]; then
        docker-compose -f $PRODUCTION_COMPOSE down
    fi

    if [ -f "$DEV_COMPOSE" ]; then
        docker-compose -f $DEV_COMPOSE down
    fi

    log_success "Services stopped"
}

# Clean up
cleanup() {
    log_info "Cleaning up..."

    stop

    # Remove images
    docker images | grep $APP_NAME | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true

    # Clean up unused containers and networks
    docker system prune -f

    log_success "Cleanup complete"
}

# Show logs
logs() {
    local compose_file=${1:-$DEV_COMPOSE}
    docker-compose -f $compose_file logs -f
}

# Show status
status() {
    log_info "Service Status:"

    if [ -f "$PRODUCTION_COMPOSE" ]; then
        echo -e "\n${YELLOW}Production Services:${NC}"
        docker-compose -f $PRODUCTION_COMPOSE ps
    fi

    if [ -f "$DEV_COMPOSE" ]; then
        echo -e "\n${YELLOW}Development Services:${NC}"
        docker-compose -f $DEV_COMPOSE ps
    fi
}

# Show usage
usage() {
    echo "Usage: $0 {dev|prod|aws|gcp|digitalocean|stop|cleanup|logs|status}"
    echo ""
    echo "Commands:"
    echo "  dev           Deploy for development (local)"
    echo "  prod          Deploy for production (local)"
    echo "  aws           Deploy to AWS ECS"
    echo "  gcp           Deploy to Google Cloud Run"
    echo "  digitalocean  Prepare for DigitalOcean App Platform"
    echo "  stop          Stop all services"
    echo "  cleanup       Clean up containers and images"
    echo "  logs          Show service logs"
    echo "  status        Show service status"
    echo ""
    echo "Environment Variables:"
    echo "  AWS_REGION         AWS region (default: us-east-1)"
    echo "  GCP_PROJECT_ID     GCP project ID"
    echo "  GCP_REGION         GCP region (default: us-central1)"
}

# Main script logic
case "${1}" in
    dev)
        deploy_dev
        ;;
    prod)
        deploy_prod
        ;;
    aws)
        deploy_aws
        ;;
    gcp)
        deploy_gcp
        ;;
    digitalocean)
        deploy_digitalocean
        ;;
    stop)
        stop
        ;;
    cleanup)
        cleanup
        ;;
    logs)
        logs ${2:-$DEV_COMPOSE}
        ;;
    status)
        status
        ;;
    *)
        usage
        exit 1
        ;;
esac
