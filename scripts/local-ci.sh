#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$PROJECT_ROOT/app"

FRONTEND_STATUS=0
PYTHON_STATUS=0

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ Error: '$1' command not found"
        exit 1
    fi
}

print_header() {
    echo ""
    echo "=========================================="
    echo "  $1"
    echo "=========================================="
    echo ""
}

run_frontend_verify() {
    print_header "Frontend Verification"
    
    cd "$APP_DIR"
    
    echo "🔍 Running TypeScript type check..."
    yarn typecheck
    local ts_exit_code=$?
    
    if [ $ts_exit_code -ne 0 ]; then
        echo "❌ TypeScript type check failed (exit code: $ts_exit_code)"
        FRONTEND_STATUS=$ts_exit_code
        return $ts_exit_code
    fi
    echo "✅ TypeScript type check passed"
    echo ""
    
    echo "🧪 Running frontend verification scripts..."
    yarn verify:all
    local verify_exit_code=$?
    
    if [ $verify_exit_code -ne 0 ]; then
        echo "❌ Frontend verification scripts failed (exit code: $verify_exit_code)"
        echo ""
        echo "📋 Frontend verification summary:"
        
        cd "$APP_DIR" && yarn verify:data-pipeline > /dev/null 2>&1
        echo "   - verify:data-pipeline: $([ $? -eq 0 ] && echo "✅" || echo "❌")"
        
        cd "$APP_DIR" && yarn verify:export-config > /dev/null 2>&1
        echo "   - verify:export-config: $([ $? -eq 0 ] && echo "✅" || echo "❌")"
        
        cd "$APP_DIR" && yarn verify:export-refactor > /dev/null 2>&1
        echo "   - verify:export-refactor: $([ $? -eq 0 ] && echo "✅" || echo "❌")"
        
        cd "$APP_DIR" && yarn verify:recommendation > /dev/null 2>&1
        echo "   - verify:recommendation: $([ $? -eq 0 ] && echo "✅" || echo "❌")"
        
        FRONTEND_STATUS=$verify_exit_code
        return $verify_exit_code
    fi
    echo "✅ Frontend verification passed"
    
    return 0
}

run_python_verify() {
    local test_group="${1:-core}"
    
    print_header "Python Verification (Group: $test_group)"
    
    cd "$PROJECT_ROOT"
    
    echo "🧪 Running Python tests..."
    python scripts/run_pytest_groups.py --group "$test_group"
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo "❌ Python tests failed (group: $test_group, exit code: $exit_code)"
        PYTHON_STATUS=$exit_code
        return $exit_code
    fi
    echo "✅ Python tests passed (group: $test_group)"
    
    return 0
}

print_final_summary() {
    print_header "Final Summary"
    
    echo "Frontend: $([ $FRONTEND_STATUS -eq 0 ] && echo "✅ Success" || echo "❌ Failed (exit code: $FRONTEND_STATUS)")"
    echo "Python:   $([ $PYTHON_STATUS -eq 0 ] && echo "✅ Success" || echo "❌ Failed (exit code: $PYTHON_STATUS)")"
    
    if [ $FRONTEND_STATUS -ne 0 ] || [ $PYTHON_STATUS -ne 0 ]; then
        echo ""
        echo "❌ Local CI failed"
        if [ $FRONTEND_STATUS -ne 0 ]; then
            echo "   - Frontend verification failed"
        fi
        if [ $PYTHON_STATUS -ne 0 ]; then
            echo "   - Python tests failed"
        fi
        echo ""
        exit 1
    fi
    
    echo ""
    echo "✅ Local CI completed successfully!"
}

run_quick() {
    print_header "PyGWalker Local CI (Quick Mode)"
    
    echo "📋 Checking prerequisites..."
    check_command python3
    check_command node
    check_command yarn
    echo "✅ All prerequisites found"
    
    cd "$APP_DIR"
    echo "🔧 Building frontend..."
    yarn build
    echo "✅ Frontend build completed"
    
    run_frontend_verify || true
    run_python_verify "core" || true
    
    print_final_summary
}

run_full() {
    print_header "PyGWalker Local CI (Full Mode)"
    
    echo "📋 Checking prerequisites..."
    check_command python3
    check_command node
    check_command yarn
    echo "✅ All prerequisites found"
    echo ""
    
    print_header "Step 1: Frontend Setup"
    
    cd "$APP_DIR"
    echo "📦 Installing frontend dependencies..."
    yarn install --frozen-lockfile
    echo "✅ Frontend dependencies installed"
    echo ""
    
    echo "🔧 Building frontend..."
    yarn build
    echo "✅ Frontend build completed"
    echo ""
    
    print_header "Step 2: Python Setup"
    
    cd "$PROJECT_ROOT"
    
    if [ ! -d "venv" ]; then
        echo "🐍 Creating virtual environment..."
        python3 -m venv venv
        echo "✅ Virtual environment created"
    fi
    
    source venv/bin/activate
    echo "📦 Installing Python package..."
    pip install -e ".[export]"
    echo "✅ Python package installed"
    echo ""
    
    print_header "Step 3: Verification"
    
    run_frontend_verify || true
    run_python_verify "core" || true
    
    print_final_summary
}

print_usage() {
    echo "Usage: $0 [--quick|--full|--help]"
    echo ""
    echo "Options:"
    echo "  --quick    Quick mode: Skip install/build, run verification only"
    echo "  --full     Full mode: Install deps, build, and verify (default)"
    echo "  --help     Show this help message"
    echo ""
}

main() {
    local mode="${1:-full}"
    
    case "$mode" in
        --quick|-q)
            run_quick
            ;;
        --full|-f)
            run_full
            ;;
        --help|-h)
            print_usage
            ;;
        *)
            echo "Unknown option: $mode"
            echo ""
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
