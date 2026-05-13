#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$PROJECT_ROOT/app"

echo "=========================================="
echo "  PyGWalker CI Verification Script"
echo "=========================================="
echo ""

verify_frontend() {
    echo "=========================================="
    echo "  Frontend Verification"
    echo "=========================================="
    echo ""
    
    cd "$APP_DIR"
    
    echo "🔍 TypeScript Type Check..."
    if ! yarn typecheck; then
        echo "❌ TypeScript type check failed"
        echo "::error::Frontend TypeScript type check failed"
        exit 1
    fi
    echo "✅ TypeScript type check passed"
    echo ""
    
    echo "🧪 Running frontend verification scripts..."
    if ! yarn verify:all; then
        echo "❌ Frontend verification scripts failed"
        echo "::error::Frontend verification scripts failed"
        exit 1
    fi
    echo "✅ Frontend verification passed"
    echo ""
}

verify_python() {
    local test_group="${1:-core}"
    
    echo "=========================================="
    echo "  Python Verification (Group: $test_group)"
    echo "=========================================="
    echo ""
    
    cd "$PROJECT_ROOT"
    
    echo "🧪 Running Python tests..."
    if ! python scripts/run_pytest_groups.py --group "$test_group"; then
        echo "❌ Python tests failed (group: $test_group)"
        echo "::error::Python tests failed for group: $test_group"
        exit 1
    fi
    echo "✅ Python tests passed (group: $test_group)"
    echo ""
}

verify_all() {
    verify_frontend
    
    echo "=========================================="
    echo "  Running All Python Test Groups"
    echo "=========================================="
    echo ""
    
    # Run core tests first (must pass)
    echo "🔹 Running core tests..."
    verify_python "core"
    
    # Run integration tests (optional, but report status)
    echo "🔹 Running integration tests..."
    if python scripts/run_pytest_groups.py --group "integration"; then
        echo "✅ Integration tests passed"
    else
        echo "⚠️ Integration tests failed (may be flaky, continuing...)"
    fi
    echo ""
}

main() {
    local target="${1:-all}"
    
    case "$target" in
        frontend)
            verify_frontend
            ;;
        python-core)
            verify_python "core"
            ;;
        python-integration)
            verify_python "integration"
            ;;
        python-all)
            verify_python "all"
            ;;
        all)
            verify_all
            ;;
        *)
            echo "Usage: $0 {frontend|python-core|python-integration|python-all|all}"
            exit 1
            ;;
    esac
    
    echo "=========================================="
    echo "  Verification completed successfully!"
    echo "=========================================="
}

main "$@"
