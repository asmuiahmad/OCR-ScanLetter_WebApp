#!/bin/bash

# Environment Switcher Script
# Usage: ./switch_env.sh [dev|prod|test]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Environment Switcher for OCR Application"
    echo "========================================"
    echo ""
    echo "Usage: $0 [environment]"
    echo ""
    echo "Available environments:"
    echo "  dev     - Development environment"
    echo "  prod    - Production environment"
    echo "  test    - Testing environment"
    echo ""
    echo "Examples:"
    echo "  $0 dev      # Switch to development"
    echo "  $0 prod     # Switch to production"
    echo "  $0 test     # Switch to testing"
    echo ""
    echo "Current environment files:"
    for env in dev prod test; do
        if [ -f ".env.$env" ]; then
            print_status ".env.$env exists"
        else
            print_warning ".env.$env missing"
        fi
    done
}

# Function to backup current .env
backup_env() {
    if [ -f ".env" ]; then
        timestamp=$(date +"%Y%m%d_%H%M%S")
        mkdir -p env_backups
        cp .env "env_backups/.env.backup.$timestamp"
        print_status "Backed up current .env to env_backups/.env.backup.$timestamp"
    fi
}

# Function to switch environment
switch_environment() {
    local env=$1
    local env_file=".env.$env"
    
    # Check if environment file exists
    if [ ! -f "$env_file" ]; then
        print_error "Environment file '$env_file' not found!"
        echo ""
        print_info "Available environment files:"
        ls -la .env.* 2>/dev/null || echo "No environment files found"
        exit 1
    fi
    
    # Backup current .env if it exists
    backup_env
    
    # Copy environment file
    cp "$env_file" ".env"
    print_status "Switched to $env environment"
    print_info "Active environment: $env_file -> .env"
    
    # Show some key settings
    echo ""
    print_info "Key settings:"
    grep -E "^(DEBUG|FLASK_ENV|DB_ENGINE|OCR_ENGINE)" .env | while read line; do
        echo "  $line"
    done
}

# Main script
main() {
    # Check if no arguments provided
    if [ $# -eq 0 ]; then
        show_usage
        exit 0
    fi
    
    # Get environment argument
    env=$1
    
    # Validate environment
    case $env in
        dev|development)
            switch_environment "dev"
            ;;
        prod|production)
            switch_environment "prod"
            ;;
        test|testing)
            switch_environment "test"
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            print_error "Unknown environment: $env"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"