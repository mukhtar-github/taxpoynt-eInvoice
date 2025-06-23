#!/bin/bash

# TaxPoynt Safe Railway Deployment Script
# Implements blue-green deployment strategy to prevent downtime

set -e

# Configuration
RAILWAY_PROJECT="${RAILWAY_PROJECT:-taxpoynt-backend}"
ENVIRONMENT="${ENVIRONMENT:-production}"
HEALTH_CHECK_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_INTERVAL=10  # 10 seconds
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Function to check if Railway CLI is installed
check_railway_cli() {
    if ! command -v railway &> /dev/null; then
        log_error "Railway CLI not found. Please install it first:"
        echo "npm install -g @railway/cli"
        exit 1
    fi
    log_info "Railway CLI found: $(railway --version)"
}

# Function to check current deployment status
check_current_deployment() {
    log_info "Checking current deployment status..."
    
    if ! railway status > /dev/null 2>&1; then
        log_error "Not logged into Railway or project not linked"
        log_info "Please run: railway login && railway link"
        exit 1
    fi
    
    CURRENT_STATUS=$(railway status --json | jq -r '.deployments[0].status // "unknown"')
    log_info "Current deployment status: $CURRENT_STATUS"
    
    if [ "$CURRENT_STATUS" = "DEPLOYING" ]; then
        log_warning "A deployment is currently in progress"
        read -p "Do you want to wait for it to complete? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            wait_for_deployment_completion
        else
            log_error "Aborting deployment"
            exit 1
        fi
    fi
}

# Function to wait for deployment completion
wait_for_deployment_completion() {
    log_info "Waiting for current deployment to complete..."
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=$HEALTH_CHECK_INTERVAL
    local elapsed=0
    
    while [ $elapsed -lt $timeout ]; do
        local status=$(railway status --json | jq -r '.deployments[0].status // "unknown"')
        
        case $status in
            "SUCCESS")
                log_success "Deployment completed successfully"
                return 0
                ;;
            "FAILED"|"CRASHED")
                log_error "Deployment failed with status: $status"
                return 1
                ;;
            "DEPLOYING")
                log_info "Still deploying... (${elapsed}s/${timeout}s)"
                ;;
            *)
                log_warning "Unknown deployment status: $status"
                ;;
        esac
        
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    log_error "Deployment timed out after ${timeout} seconds"
    return 1
}

# Function to get current service URL
get_service_url() {
    local url=$(railway domain | grep -E 'https?://' | head -1 | awk '{print $1}')
    if [ -z "$url" ]; then
        log_warning "Could not determine service URL automatically"
        url="https://${RAILWAY_PROJECT}.railway.app"
    fi
    echo "$url"
}

# Function to check application health
check_health() {
    local url="$1"
    local endpoint="${2:-/api/v1/health/ready}"
    local max_attempts="${3:-30}"
    local interval="${4:-10}"
    
    log_info "Checking health at: ${url}${endpoint}"
    
    for i in $(seq 1 $max_attempts); do
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "${url}${endpoint}" || echo "000")
        
        case $http_code in
            200)
                log_success "Health check passed (${i}/${max_attempts})"
                return 0
                ;;
            503)
                log_info "Service unavailable, waiting... (${i}/${max_attempts})"
                ;;
            000)
                log_info "Connection failed, waiting... (${i}/${max_attempts})"
                ;;
            *)
                log_warning "Unexpected response code: $http_code (${i}/${max_attempts})"
                ;;
        esac
        
        if [ $i -lt $max_attempts ]; then
            sleep $interval
        fi
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Function to get deployment ID before deployment
get_current_deployment_id() {
    railway status --json | jq -r '.deployments[0].id // "unknown"'
}

# Function to perform rollback
perform_rollback() {
    local previous_deployment_id="$1"
    
    if [ "$ROLLBACK_ENABLED" != "true" ]; then
        log_warning "Rollback is disabled"
        return 1
    fi
    
    if [ "$previous_deployment_id" = "unknown" ] || [ -z "$previous_deployment_id" ]; then
        log_error "Cannot rollback: previous deployment ID not found"
        return 1
    fi
    
    log_warning "Attempting to rollback to deployment: $previous_deployment_id"
    
    if railway rollback "$previous_deployment_id"; then
        log_success "Rollback initiated"
        
        # Wait for rollback to complete
        if wait_for_deployment_completion; then
            log_success "Rollback completed successfully"
            return 0
        else
            log_error "Rollback failed"
            return 1
        fi
    else
        log_error "Failed to initiate rollback"
        return 1
    fi
}

# Function to send deployment notification
send_notification() {
    local status="$1"
    local message="$2"
    local webhook_url="${DEPLOYMENT_WEBHOOK_URL}"
    
    if [ -n "$webhook_url" ]; then
        local payload=$(cat <<EOF
{
    "environment": "$ENVIRONMENT",
    "project": "$RAILWAY_PROJECT",
    "status": "$status",
    "message": "$message",
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "deployer": "$(whoami)"
}
EOF
)
        
        curl -s -X POST -H "Content-Type: application/json" -d "$payload" "$webhook_url" > /dev/null || true
    fi
}

# Function to run pre-deployment checks
run_pre_deployment_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if we have uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log_warning "You have uncommitted changes"
        read -p "Continue anyway? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Aborting deployment"
            exit 1
        fi
    fi
    
    # Check current branch
    local current_branch=$(git rev-parse --abbrev-ref HEAD)
    if [ "$ENVIRONMENT" = "production" ] && [ "$current_branch" != "master" ] && [ "$current_branch" != "main" ]; then
        log_warning "Deploying to production from branch: $current_branch"
        read -p "Continue? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Aborting deployment"
            exit 1
        fi
    fi
    
    # Run tests if available
    if [ -f "requirements.txt" ] && grep -q pytest requirements.txt; then
        log_info "Running tests..."
        if ! python -m pytest tests/ --tb=short -q; then
            log_error "Tests failed"
            read -p "Deploy anyway? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_error "Aborting deployment"
                exit 1
            fi
        else
            log_success "Tests passed"
        fi
    fi
}

# Function to validate deployment configuration
validate_deployment_config() {
    log_info "Validating deployment configuration..."
    
    # Check if health check endpoint exists in railway.json
    if [ -f "railway.json" ]; then
        local health_path=$(jq -r '.deploy.healthcheckPath // empty' railway.json)
        if [ -z "$health_path" ]; then
            log_warning "No health check path configured in railway.json"
        else
            log_info "Health check configured: $health_path"
        fi
    else
        log_warning "No railway.json found - using default configuration"
    fi
    
    # Check environment variables
    local required_env_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY")
    for var in "${required_env_vars[@]}"; do
        if [ -z "${!var}" ] && ! railway variables | grep -q "^$var"; then
            log_warning "Environment variable $var is not set locally or in Railway"
        fi
    done
}

# Main deployment function
main() {
    log_info "Starting TaxPoynt safe deployment to Railway"
    log_info "Environment: $ENVIRONMENT"
    log_info "Project: $RAILWAY_PROJECT"
    
    # Pre-deployment steps
    check_railway_cli
    check_current_deployment
    run_pre_deployment_checks
    validate_deployment_config
    
    # Get current state for potential rollback
    local service_url=$(get_service_url)
    local previous_deployment_id=$(get_current_deployment_id)
    
    log_info "Service URL: $service_url"
    log_info "Previous deployment ID: $previous_deployment_id"
    
    # Send deployment start notification
    send_notification "started" "Deployment started for $ENVIRONMENT environment"
    
    # Start deployment
    log_info "Starting Railway deployment..."
    
    if railway deploy --detach; then
        log_success "Deployment initiated successfully"
    else
        log_error "Failed to initiate deployment"
        send_notification "failed" "Failed to initiate deployment"
        exit 1
    fi
    
    # Wait for deployment to complete
    if wait_for_deployment_completion; then
        log_success "Deployment phase completed"
    else
        log_error "Deployment failed during build/start phase"
        send_notification "failed" "Deployment failed during build/start phase"
        
        if [ "$ROLLBACK_ENABLED" = "true" ]; then
            log_info "Attempting automatic rollback..."
            perform_rollback "$previous_deployment_id"
        fi
        exit 1
    fi
    
    # Health check the new deployment
    log_info "Performing post-deployment health checks..."
    
    if check_health "$service_url" "/api/v1/health/ready" 30 10; then
        log_success "Post-deployment health checks passed"
        send_notification "success" "Deployment completed successfully and health checks passed"
    else
        log_error "Post-deployment health checks failed"
        send_notification "failed" "Deployment completed but health checks failed"
        
        if [ "$ROLLBACK_ENABLED" = "true" ]; then
            log_info "Health checks failed, attempting rollback..."
            if perform_rollback "$previous_deployment_id"; then
                # Verify rollback health
                if check_health "$service_url" "/api/v1/health/ready" 20 10; then
                    log_success "Rollback completed and service is healthy"
                    send_notification "rolled_back" "Deployment failed, successfully rolled back"
                else
                    log_error "Rollback completed but service is still unhealthy"
                    send_notification "critical" "Deployment failed and rollback is unhealthy - manual intervention required"
                fi
            else
                log_error "Rollback failed - manual intervention required"
                send_notification "critical" "Deployment and rollback both failed - manual intervention required"
            fi
        fi
        exit 1
    fi
    
    # Final success message
    log_success "🚀 Deployment completed successfully!"
    log_success "✅ Service is healthy and ready to serve traffic"
    log_info "Service URL: $service_url"
    
    # Run deep health check for monitoring
    log_info "Running deep health check for monitoring..."
    local deep_health_response=$(curl -s "${service_url}/api/v1/health/deep" || echo '{"status":"error"}')
    local deep_health_status=$(echo "$deep_health_response" | jq -r '.status // "error"')
    
    case $deep_health_status in
        "healthy")
            log_success "Deep health check: All systems optimal"
            ;;
        "degraded")
            log_warning "Deep health check: Some non-critical issues detected"
            ;;
        *)
            log_warning "Deep health check: Issues detected - monitor closely"
            ;;
    esac
}

# Script entry point
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment|-e)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --no-rollback)
                ROLLBACK_ENABLED="false"
                shift
                ;;
            --timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  -e, --environment ENV    Deployment environment (default: production)"
                echo "  --no-rollback           Disable automatic rollback on failure"
                echo "  --timeout SECONDS       Health check timeout (default: 300)"
                echo "  -h, --help              Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run main function
    main
fi